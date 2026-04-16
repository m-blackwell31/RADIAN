"""
train_fall_model_v5.py
======================
Fall detection model training for RADIAN mmWave radar system.

Designed for use with mmwave_run6_simple.py parser output.

Key differences from v4
------------------------
- Window size = 10 frames (~5s at 2fps) to match live sliding window
- Multi-window augmentation for fall clips (step=2) to capture fall at any timing
- Smaller N_BUCKETS (4) and spectral bins (3) to match shorter window
- Shorter smoothing kernel (w=3) for 10-frame windows
- Trained exclusively on new environment data

Usage
-----
1. Record clips using mmwave_run6_simple.py via SSH:
       timeout 15 python3 mmwave_run6_simple.py > fall_01.ndjson
       timeout 15 python3 mmwave_run6_simple.py > standing_01.ndjson

2. Put all fall clips and standing clips in a zip file.
   Fall clips must start with 'fall', standing clips with 'standing'.

3. Run:
       python3 train_fall_model_v5.py --zip your_clips.zip

4. Copy the output model to the Pi:
       scp fall_model_v5_outputs/best_model_v5.pkl pi:~/RADIAN/fall_detector/

5. Run the fall detector:
       python3 fall_detector_v2.py \
           --parser mmwave_run6_simple.py \
           --model best_model_v5.pkl \
           --window 10 --step 1 --warmup 10 \
           --min-points 0 --bg-frames 0 \
           --verbose
"""

from __future__ import annotations

import argparse
import json
import os
import time
import warnings
import zipfile

import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import (
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict

warnings.filterwarnings("ignore")

# ── config ────────────────────────────────────────────────────────────────────
WINDOW    = 10      # frames per window — must match --window in fall_detector_v2.py
N_BUCKETS = 4       # temporal buckets (smaller for short window)
RANDOM    = 42
OUTDIR    = "fall_model_v5_outputs"


# ═══════════════════════════════════════════════════════════════════════════════
# Data loading
# ═══════════════════════════════════════════════════════════════════════════════

def get_label(name: str):
    n = os.path.basename(name).lower()
    if n.startswith("fall"):     return 1
    if n.startswith("standing"): return 0
    return None


def read_rows(zf: zipfile.ZipFile, name: str) -> list[dict]:
    data = zf.read(name)
    for enc in ("utf-16", "utf-8", "utf-8-sig", "latin1"):
        try:
            txt = data.decode(enc)
            if '"frame"' not in txt:
                continue
            rows = []
            for line in txt.splitlines():
                line = line.strip().replace("\x00", "")
                if line:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
            return rows
        except Exception:
            pass
    return []


def _empty_row(i: int) -> dict:
    return {"ts": 0.0, "frame": i, "num_points_filt": 0,
            "points_filt": [], "person": {"present": False}}


def _mean_z(r: dict) -> float:
    pts = r.get("points_filt", []) or []
    return float(np.mean([p["z"] for p in pts])) if pts else 0.0


def _mean_v(r: dict) -> float:
    pts = r.get("points_filt", []) or []
    return float(np.mean([abs(p["v"]) for p in pts])) if pts else 0.0


def pad_to_window(rows: list[dict], window: int = WINDOW) -> list[dict]:
    if len(rows) >= window:
        return rows[:window]
    out = list(rows)
    nf = int(rows[-1].get("frame", len(rows) - 1)) + 1 if rows else 0
    while len(out) < window:
        out.append(_empty_row(nf))
        nf += 1
    return out


def select_center_window(rows: list[dict], window: int = WINDOW) -> list[dict]:
    """Center crop for non-fall clips."""
    if len(rows) <= window:
        return pad_to_window(rows, window)
    start = max(0, (len(rows) - window) // 2)
    return rows[start: start + window]


def get_fall_windows(rows: list[dict], window: int = WINDOW, step: int = 2) -> list[list[dict]]:
    """
    Generate multiple overlapping windows from a fall clip.
    This way the model sees the fall at different positions in the window.
    """
    n = len(rows)
    if n <= window:
        return [pad_to_window(rows, window)]
    windows = []
    for start in range(0, n - window + 1, step):
        windows.append(rows[start: start + window])
    return windows


# ═══════════════════════════════════════════════════════════════════════════════
# Feature extraction
# ═══════════════════════════════════════════════════════════════════════════════

def _longest_run(cond) -> int:
    best = cur = 0
    for c in cond:
        if c:
            cur += 1; best = max(best, cur)
        else:
            cur = 0
    return best


def _safe_stats(arr, prefix: str) -> dict:
    arr = np.asarray(arr, dtype=float)
    if len(arr) == 0:
        return {f"{prefix}_{k}": 0.0 for k in
                ["mean", "std", "min", "max", "median",
                 "q10", "q25", "q75", "q90", "range", "skew", "kurtosis"]}
    n = len(arr); mu = arr.mean(); std = max(arr.std(ddof=0), 1e-12)
    skew = float(((arr - mu) ** 3).mean() / std ** 3) if n > 2 else 0.0
    kurt = float(((arr - mu) ** 4).mean() / std ** 4 - 3) if n > 3 else 0.0
    return {
        f"{prefix}_mean":     float(mu),
        f"{prefix}_std":      float(std),
        f"{prefix}_min":      float(arr.min()),
        f"{prefix}_max":      float(arr.max()),
        f"{prefix}_median":   float(np.median(arr)),
        f"{prefix}_q10":      float(np.quantile(arr, 0.10)),
        f"{prefix}_q25":      float(np.quantile(arr, 0.25)),
        f"{prefix}_q75":      float(np.quantile(arr, 0.75)),
        f"{prefix}_q90":      float(np.quantile(arr, 0.90)),
        f"{prefix}_range":    float(arr.max() - arr.min()),
        f"{prefix}_skew":     skew,
        f"{prefix}_kurtosis": kurt,
    }


def _spectral(arr, prefix: str, n_freqs: int = 3) -> dict:
    arr = np.asarray(arr, dtype=float)
    feats: dict = {}
    if len(arr) < 4:
        for i in range(n_freqs):
            feats[f"{prefix}_fft_{i}"] = 0.0
        feats[f"{prefix}_spec_ent"] = 0.0
        return feats
    fft = np.abs(np.fft.rfft(arr - arr.mean()))[:n_freqs]
    for i, val in enumerate(fft):
        feats[f"{prefix}_fft_{i}"] = float(val)
    p = fft ** 2 + 1e-12; p /= p.sum()
    feats[f"{prefix}_spec_ent"] = float(-np.sum(p * np.log(p)))
    return feats


def _buckets(arr, prefix: str, n: int = N_BUCKETS) -> dict:
    arr = np.asarray(arr, dtype=float)
    splits = np.array_split(arr, n) if len(arr) else [np.array([0.0])] * n
    return {f"{prefix}_b{i}": float(s.mean()) if len(s) else 0.0
            for i, s in enumerate(splits)}


def _smooth(arr, w: int = 3) -> np.ndarray:
    arr = np.asarray(arr, dtype=float)
    if len(arr) >= w:
        return np.convolve(arr, np.ones(w) / w, mode="same")
    return arr.copy()


def extract_features(frames: list[dict]) -> dict:
    zmean, zmed, zmin_, zmax_, ziqr = [], [], [], [], []
    vmean, vpeak, vmed              = [], [], []
    xspread, yspread, zspread       = [], [], []
    npts_arr, ppres                 = [], []
    bvol, vposfrac                  = [], []
    cx_arr, cy_arr                  = [], []

    for r in frames:
        pts = r.get("points_filt", []) or []
        npts_arr.append(float(r.get("num_points_filt", len(pts))))
        ppres.append(float(bool((r.get("person") or {}).get("present", False))))

        if pts:
            xa = np.array([p["x"] for p in pts], dtype=float)
            ya = np.array([p["y"] for p in pts], dtype=float)
            za = np.array([p["z"] for p in pts], dtype=float)
            va = np.array([p["v"] for p in pts], dtype=float)
            av = np.abs(va)

            zmean.append(za.mean());  zmed.append(float(np.median(za)))
            zmin_.append(za.min());   zmax_.append(za.max())
            ziqr.append(float(np.quantile(za, 0.75) - np.quantile(za, 0.25)))
            vmean.append(av.mean());  vpeak.append(av.max()); vmed.append(float(np.median(av)))
            xspread.append(xa.std()); yspread.append(ya.std()); zspread.append(za.std())
            cx_arr.append(xa.mean()); cy_arr.append(ya.mean())
            bvol.append(
                (xa.max() - xa.min() + 1e-6) *
                (ya.max() - ya.min() + 1e-6) *
                (za.max() - za.min() + 1e-6)
            )
            vposfrac.append(float((va > 0).mean()))
        else:
            for lst in [zmean, zmed, zmin_, zmax_, ziqr,
                        vmean, vpeak, vmed,
                        xspread, yspread, zspread,
                        cx_arr, cy_arr, bvol, vposfrac]:
                lst.append(0.0)

    z  = np.array(zmean); v = np.array(vmean)
    zs = _smooth(z, 3);   vs = _smooth(v, 3)
    dz  = np.diff(zs, prepend=zs[0])
    dv  = np.diff(vs, prepend=vs[0])
    ddz = np.diff(dz, prepend=dz[0])
    adz = np.abs(dz); adv = np.abs(dv)
    cx  = _smooth(np.array(cx_arr), 3)
    cy  = _smooth(np.array(cy_arr), 3)
    lat = np.sqrt(
        np.abs(np.diff(cx, prepend=cx[0])) ** 2 +
        np.abs(np.diff(cy, prepend=cy[0])) ** 2
    )

    imin = int(np.argmin(zs)) if len(zs) else 0
    imax = int(np.argmax(vs)) if len(vs) else 0
    post = min(len(zs), imin + 3)
    z_rec = float(zs[imin + 1:post].mean() - zs[imin]) if post > imin + 1 else 0.0

    feats: dict = {}
    for arr, prefix in [
        (zmean,   "zmean"),  (zmed,    "zmed"),
        (zmin_,   "zmin"),   (zmax_,   "zmax"),   (ziqr,   "ziqr"),
        (vmean,   "vmean"),  (vpeak,   "vpeak"),  (vmed,   "vmed"),
        (npts_arr,"npts"),
        (xspread, "xspread"),(yspread, "yspread"),(zspread,"zspread"),
        (adz,     "abs_dz"), (adv,     "abs_dv"), (ddz,    "jerk"),
        (bvol,    "bvol"),   (vposfrac,"vposfrac"),(lat,   "lat_motion"),
    ]:
        feats.update(_safe_stats(arr, prefix))

    feats.update(_spectral(zs, "z"))
    feats.update(_spectral(vs, "v"))
    feats.update(_spectral(adz, "dz"))
    feats.update(_buckets(zs, "z"))
    feats.update(_buckets(vs, "v"))
    feats.update(_buckets(adz, "dz"))
    feats.update(_buckets(dz, "dz_signed"))

    feats["z_drop"]           = float(zs.max() - zs.min()) if len(zs) else 0.0
    feats["z_signed_drop"]    = float(zs[0] - zs.min()) if len(zs) else 0.0
    feats["z_end_minus_start"]= float(zs[-1] - zs[0]) if len(zs) else 0.0
    feats["z_end_minus_min"]  = float(zs[-1] - zs.min()) if len(zs) else 0.0
    feats["z_min_index_frac"] = float(imin / max(1, len(zs) - 1))
    feats["v_peak_index_frac"]= float(imax / max(1, len(vs) - 1))
    feats["v_peak"]           = float(vs.max()) if len(vs) else 0.0
    feats["dz_peak"]          = float(adz.max()) if len(adz) else 0.0
    feats["dv_peak"]          = float(adv.max()) if len(adv) else 0.0
    feats["jerk_peak"]        = float(np.abs(ddz).max()) if len(ddz) else 0.0
    feats["impulse_score"]    = feats["z_signed_drop"] * feats["v_peak"]
    feats["impulse2"]         = feats["z_drop"] * feats["v_peak"]
    feats["v_energy"]         = float((vs ** 2).sum())
    feats["z_recovery"]       = z_rec
    feats["v_leads_z_drop"]   = float(imax < imin)
    feats["v_z_lead_diff"]    = float(imin - imax) / max(1, len(zs))
    feats["high_v_run"]       = _longest_run(vs > np.quantile(vs, 0.8)) if len(vs) else 0
    feats["high_dz_run"]      = _longest_run(adz > np.quantile(adz, 0.8)) if len(adz) else 0
    feats["low_z_run"]        = _longest_run(zs < np.quantile(zs, 0.2)) if len(zs) else 0
    pp = np.array(ppres)
    feats["person_present_mean"]  = float(pp.mean())
    feats["person_present_change"]= float(np.abs(np.diff(pp)).sum())
    feats["z_curvature_mean"]     = float(np.abs(ddz).mean()) if len(ddz) else 0.0
    bv = np.array(bvol)
    feats["bvol_drop"]      = float(bv.max() - bv.min()) if len(bv) else 0.0
    feats["bvol_end_ratio"] = float(bv[-1] / (bv.max() + 1e-6)) if len(bv) else 1.0
    feats["lat_vs_z_ratio"] = float(lat.mean() / (adz.mean() + 1e-6))
    return feats


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(description="Train RADIAN fall detection model v5")
    p.add_argument("--zip",     required=True,  help="Zip file containing .ndjson clips")
    p.add_argument("--outdir",  default=OUTDIR, help="Output directory")
    p.add_argument("--window",  default=WINDOW, type=int,
                   help=f"Frames per window (default: {WINDOW}) — must match --window in fall_detector_v2.py")
    p.add_argument("--step",    default=2, type=int,
                   help="Step size for fall window augmentation (default: 2)")
    args = p.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    np.random.seed(RANDOM)

    print("=" * 60)
    print("RADIAN Fall Detection Model Training v5")
    print("=" * 60)
    print(f"  Zip file : {args.zip}")
    print(f"  Window   : {args.window} frames")
    print(f"  Output   : {args.outdir}/")

    # ── Load data ─────────────────────────────────────────────────────────────
    print("\nLoading clips...")
    X_list, y_list = [], []

    with zipfile.ZipFile(args.zip) as zf:
        names = sorted([n for n in zf.namelist() if n.endswith(".ndjson")])
        fall_count = stand_count = 0

        for name in names:
            label = get_label(name)
            if label is None:
                print(f"  Skipping (unknown label): {name}")
                continue
            rows = read_rows(zf, name)
            if not rows:
                print(f"  Skipping (empty): {name}")
                continue

            if label == 1:
                # Fall: generate multiple windows
                windows = get_fall_windows(rows, args.window, args.step)
                for w in windows:
                    feats = extract_features(w)
                    X_list.append(list(feats.values()))
                    y_list.append(1)
                fall_count += 1
            else:
                # Non-fall: center crop
                w = select_center_window(rows, args.window)
                feats = extract_features(w)
                X_list.append(list(feats.values()))
                y_list.append(0)
                stand_count += 1

    feature_cols = list(feats.keys())
    X = np.array(X_list)
    y = np.array(y_list)

    print(f"\n  Fall clips    : {fall_count}  →  {y.sum()} windows after augmentation")
    print(f"  NonFall clips : {stand_count}  →  {(1-y).sum()} windows")
    print(f"  Features      : {len(feature_cols)}")

    # ── Cross-validation ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("5-Fold Cross Validation")
    print("=" * 60)

    cv = StratifiedKFold(5, shuffle=True, random_state=RANDOM)
    model = ExtraTreesClassifier(
        n_estimators=50, random_state=RANDOM,
        class_weight="balanced_subsample",
        min_samples_leaf=2, n_jobs=-1,
    )
    oof_proba = cross_val_predict(model, X, y, cv=cv, method="predict_proba", n_jobs=-1)[:, 1]

    best_t, best_j = 0.5, -1.0
    for t in np.arange(0.10, 0.91, 0.01):
        pred = (oof_proba >= t).astype(int)
        tp = ((pred == 1) & (y == 1)).sum()
        tn = ((pred == 0) & (y == 0)).sum()
        fp = ((pred == 1) & (y == 0)).sum()
        fn = ((pred == 0) & (y == 1)).sum()
        j = tp / (tp + fn + 1e-9) + tn / (tn + fp + 1e-9) - 1
        if j > best_j:
            best_j, best_t = j, t

    pred = (oof_proba >= best_t).astype(int)
    print(f"\n  Threshold : {best_t:.2f}  (Youden-J on OOF)")
    print()
    print(classification_report(y, pred, target_names=["NonFall", "Fall"], zero_division=0))
    try:
        auc = roc_auc_score(y, oof_proba)
        bal = balanced_accuracy_score(y, pred)
        print(f"  AUC     : {auc:.3f}")
        print(f"  BalAcc  : {bal:.3f}")
    except Exception:
        pass
    cm = confusion_matrix(y, pred)
    print(f"\n  Confusion matrix:")
    print(f"    TN={cm[0,0]}  FP={cm[0,1]}")
    print(f"    FN={cm[1,0]}  TP={cm[1,1]}")

    # ── Train final model ─────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Training final model on all data...")
    print("=" * 60)
    model.fit(X, y)

    # Inference timing
    t0 = time.perf_counter()
    for _ in range(100):
        model.predict_proba(X[:1])
    ms = (time.perf_counter() - t0) / 100 * 1000
    print(f"  Inference : {ms:.1f}ms local  →  ~{ms*20:.0f}ms on Pi 3B+")

    # Save
    bundle = {
        "model":        model,
        "feature_cols": feature_cols,
        "threshold":    float(best_t),
        "window":       args.window,
        "notes":        f"v5 — window={args.window}, multi-window fall aug, mmwave_run6_simple.py",
    }
    model_path = os.path.join(args.outdir, "best_model_v5.pkl")
    joblib.dump(bundle, model_path)
    sz = os.path.getsize(model_path) / 1e6

    print(f"\n  Saved: {model_path}  ({sz:.2f} MB)")
    print(f"\n  Run command for Pi:")
    print(f"    python3 fall_detector_v2.py \\")
    print(f"        --parser mmwave_run6_simple.py \\")
    print(f"        --model best_model_v5.pkl \\")
    print(f"        --window {args.window} --step 1 --warmup 10 \\")
    print(f"        --min-points 0 --bg-frames 0 \\")
    print(f"        --verbose")
    print("=" * 60)


if __name__ == "__main__":
    main()
