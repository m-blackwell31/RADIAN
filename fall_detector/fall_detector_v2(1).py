"""
fall_detector.py
================
Live fall detection for Raspberry Pi 3B+.
Uses mmwave_run6.py as the radar parser — runs it as a subprocess and reads
its JSON output line by line.  No duplicate UART parsing here.

Architecture
------------
                    ┌─────────────────────┐
                    │   mmwave_run6.py     │  (subprocess)
                    │  CLI_PORT + DATA_PORT│
                    │  → JSON to stdout   │
                    └────────┬────────────┘
                             │ one JSON line per radar frame
                    ┌────────▼────────────┐
                    │  reader thread       │
                    │  deque(maxlen=WINDOW)│
                    └────────┬────────────┘
                             │ every STEP new frames
                    ┌────────▼────────────┐
                    │  inference thread    │
                    │  extract_features()  │
                    │  ET-30 model         │
                    └────────┬────────────┘
                             │ prob >= threshold
                    ┌────────▼────────────┐
                    │  Gotify alert        │
                    │  CSV log             │
                    └─────────────────────┘

Usage
-----
    python3 fall_detector.py \\
        --parser    mmwave_run6.py \\
        --model     best_model_pi_v3.pkl \\
        --cli-port  /dev/ttyUSB0 \\
        --data-port /dev/ttyUSB1 \\
        --cfg-file  config3.cfg \\
        --gotify-url  http://YOUR_SERVER:PORT \\
        --gotify-token YOUR_APP_TOKEN \\
        --verbose

Options
-------
  --parser        PATH   Path to mmwave_run6.py            [required]
  --model         PATH   Path to best_model_pi_v3.pkl      [required]
  --cli-port      PORT   Radar CLI/config UART port        [default: /dev/ttyUSB0]
  --data-port     PORT   Radar data UART port              [default: /dev/ttyUSB1]
  --cfg-file      PATH   Radar .cfg file                   [default: config3.cfg]
  --window        INT    Frames per inference window       [default: 32]
  --step          INT    New frames between inferences     [default: 6]
  --cooldown      FLOAT  Min seconds between alerts        [default: 15.0]
  --gotify-url    URL    Gotify server base URL            [default: None]
  --gotify-token  TOKEN  Gotify app token                  [default: None]
  --log           PATH   CSV log file path                 [default: fall_log.csv]
  --verbose              Print every inference result
"""

import argparse
import collections
import csv
import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime

import joblib
import numpy as np
import pandas as pd

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── optional debug dashboard ──────────────────────────────────────────────────
try:
    from debug_dashboard import Dashboard, DebugState
    HAS_DEBUG = True
except ImportError:
    HAS_DEBUG = False

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("fall_detector")

# ── constants ─────────────────────────────────────────────────────────────────
N_BUCKETS = 8


# ═══════════════════════════════════════════════════════════════════════════════
# Feature extraction — must stay byte-for-byte identical to train_fall_model_v3.py
# ═══════════════════════════════════════════════════════════════════════════════

def _longest_run(cond) -> int:
    best = cur = 0
    for c in cond:
        if c:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def _safe_stats(arr, prefix: str) -> dict:
    arr = np.asarray(arr, dtype=float)
    if len(arr) == 0:
        keys = ["mean", "std", "min", "max", "median",
                "q10", "q25", "q75", "q90", "range", "skew", "kurtosis"]
        return {f"{prefix}_{k}": 0.0 for k in keys}
    n   = len(arr)
    mu  = arr.mean()
    std = max(arr.std(ddof=0), 1e-12)
    skew = float(((arr - mu) ** 3).mean() / std ** 3) if n > 2 else 0.0
    kurt = float(((arr - mu) ** 4).mean() / std ** 4 - 3) if n > 3 else 0.0
    return {
        f"{prefix}_mean"    : float(mu),
        f"{prefix}_std"     : float(std),
        f"{prefix}_min"     : float(arr.min()),
        f"{prefix}_max"     : float(arr.max()),
        f"{prefix}_median"  : float(np.median(arr)),
        f"{prefix}_q10"     : float(np.quantile(arr, 0.10)),
        f"{prefix}_q25"     : float(np.quantile(arr, 0.25)),
        f"{prefix}_q75"     : float(np.quantile(arr, 0.75)),
        f"{prefix}_q90"     : float(np.quantile(arr, 0.90)),
        f"{prefix}_range"   : float(arr.max() - arr.min()),
        f"{prefix}_skew"    : skew,
        f"{prefix}_kurtosis": kurt,
    }


def _spectral(arr, prefix: str, n_freqs: int = 4) -> dict:
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
    p = fft ** 2 + 1e-12
    p /= p.sum()
    feats[f"{prefix}_spec_ent"] = float(-np.sum(p * np.log(p)))
    return feats


def _buckets(arr, prefix: str, n: int = N_BUCKETS) -> dict:
    arr    = np.asarray(arr, dtype=float)
    splits = np.array_split(arr, n) if len(arr) else [np.array([0.0])] * n
    return {
        f"{prefix}_b{i}": float(s.mean()) if len(s) else 0.0
        for i, s in enumerate(splits)
    }


def _smooth(arr, w: int = 5) -> np.ndarray:
    arr = np.asarray(arr, dtype=float)
    if   len(arr) >= w: return np.convolve(arr, np.ones(w) / w, mode="same")
    elif len(arr) >= 3: return np.convolve(arr, np.ones(3) / 3, mode="same")
    return arr.copy()


def extract_features(frames: list) -> dict:
    """
    frames  : list of dicts from mmwave_run6.py stdout, each containing:
                  ts, frame, num_points_filt, points_filt, person
    Returns : feature dict aligned with training feature_cols
    """
    zmean, zmed, zmin_, zmax_, ziqr = [], [], [], [], []
    vmean, vpeak, vmed              = [], [], []
    xspread, yspread, zspread       = [], [], []
    npts_arr, ppres                  = [], []
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

            zmean.append(za.mean());  zmed.append(np.median(za))
            zmin_.append(za.min());   zmax_.append(za.max())
            ziqr.append(np.quantile(za, 0.75) - np.quantile(za, 0.25))
            vmean.append(av.mean());  vpeak.append(av.max()); vmed.append(np.median(av))
            xspread.append(xa.std()); yspread.append(ya.std()); zspread.append(za.std())
            cx_arr.append(xa.mean()); cy_arr.append(ya.mean())
            bvol.append(
                (xa.max() - xa.min() + 1e-6)
                * (ya.max() - ya.min() + 1e-6)
                * (za.max() - za.min() + 1e-6)
            )
            vposfrac.append(float((va > 0).mean()))
        else:
            for lst in [zmean, zmed, zmin_, zmax_, ziqr,
                        vmean, vpeak, vmed, xspread, yspread, zspread,
                        cx_arr, cy_arr, bvol, vposfrac]:
                lst.append(0.0)

    z  = np.array(zmean); v = np.array(vmean)
    zs = _smooth(z, 5);   vs = _smooth(v, 5)
    dz  = np.diff(zs, prepend=zs[0])
    dv  = np.diff(vs, prepend=vs[0])
    ddz = np.diff(dz, prepend=dz[0])
    adz = np.abs(dz); adv = np.abs(dv)

    cx  = _smooth(np.array(cx_arr), 3)
    cy  = _smooth(np.array(cy_arr), 3)
    lat = np.sqrt(
        np.abs(np.diff(cx, prepend=cx[0])) ** 2
        + np.abs(np.diff(cy, prepend=cy[0])) ** 2
    )

    imin  = int(np.argmin(zs)) if len(zs) else 0
    imax  = int(np.argmax(vs)) if len(vs) else 0
    post  = min(len(zs), imin + 6)
    z_rec = float(zs[imin + 1 : post].mean() - zs[imin]) if post > imin + 1 else 0.0

    feats: dict = {}

    for arr, prefix in [
        (zmean,   "zmean"),  (zmed,    "zmed"),  (zmin_,   "zmin"),
        (zmax_,   "zmax"),   (ziqr,    "ziqr"),  (vmean,   "vmean"),
        (vpeak,   "vpeak"),  (vmed,    "vmed"),  (npts_arr,"npts"),
        (xspread, "xspread"),(yspread, "yspread"),(zspread,"zspread"),
        (adz,     "abs_dz"), (adv,     "abs_dv"), (ddz,    "jerk"),
        (bvol,    "bvol"),   (vposfrac,"vposfrac"),(lat,   "lat_motion"),
    ]:
        feats.update(_safe_stats(arr, prefix))

    feats.update(_spectral(zs,  "z"))
    feats.update(_spectral(vs,  "v"))
    feats.update(_spectral(adz, "dz"))

    feats.update(_buckets(zs,  "z"))
    feats.update(_buckets(vs,  "v"))
    feats.update(_buckets(adz, "dz"))
    feats.update(_buckets(dz,  "dz_signed"))

    feats["n_frames"]             = len(frames)
    feats["z_drop"]               = float(zs.max() - zs.min())       if len(zs) else 0.0
    feats["z_signed_drop"]        = float(zs[0]  - zs.min())          if len(zs) else 0.0
    feats["z_end_minus_start"]    = float(zs[-1]  - zs[0])            if len(zs) else 0.0
    feats["z_end_minus_min"]      = float(zs[-1]  - zs.min())          if len(zs) else 0.0
    feats["z_min_index_frac"]     = float(imin / max(1, len(zs) - 1))
    feats["v_peak_index_frac"]    = float(imax / max(1, len(vs) - 1))
    feats["v_peak"]               = float(vs.max())                    if len(vs) else 0.0
    feats["dz_peak"]              = float(adz.max())                   if len(adz) else 0.0
    feats["dv_peak"]              = float(adv.max())                   if len(adv) else 0.0
    feats["jerk_peak"]            = float(np.abs(ddz).max())           if len(ddz) else 0.0
    feats["impulse_score"]        = feats["z_signed_drop"] * feats["v_peak"]
    feats["impulse2"]             = feats["z_drop"]        * feats["v_peak"]
    feats["v_energy"]             = float((vs ** 2).sum())
    feats["z_recovery"]           = z_rec
    feats["v_leads_z_drop"]       = float(imax < imin)
    feats["v_z_lead_diff"]        = float(imin - imax) / max(1, len(zs))
    feats["high_v_run"]           = _longest_run(vs  > np.quantile(vs,  0.8)) if len(vs)  else 0
    feats["high_dz_run"]          = _longest_run(adz > np.quantile(adz, 0.8)) if len(adz) else 0
    feats["low_z_run"]            = _longest_run(zs  < np.quantile(zs,  0.2)) if len(zs)  else 0
    pp = np.array(ppres)
    feats["person_present_mean"]  = float(pp.mean())
    feats["person_present_change"]= float(np.abs(np.diff(pp)).sum())
    feats["z_curvature_mean"]     = float(np.abs(ddz).mean())          if len(ddz) else 0.0
    bv = np.array(bvol)
    feats["bvol_drop"]            = float(bv.max() - bv.min())         if len(bv) else 0.0
    feats["bvol_end_ratio"]       = float(bv[-1] / (bv.max() + 1e-6))  if len(bv) else 1.0
    feats["lat_vs_z_ratio"]       = float(lat.mean() / (adz.mean() + 1e-6))

    return feats


# ═══════════════════════════════════════════════════════════════════════════════
# Gotify alert
# ═══════════════════════════════════════════════════════════════════════════════

def send_gotify_alert(url: str, token: str, prob: float, ts: str):
    if not HAS_REQUESTS:
        log.warning("requests not installed — cannot send Gotify alert. Run: pip install requests")
        return
    try:
        resp = requests.post(
            f"{url.rstrip('/')}/message",
            params={"token": token},
            json={
                "title"   : "⚠️ Fall Detected",
                "message" : f"Fall detected ({prob:.0%} confidence) at {ts}",
                "priority": 8,
            },
            timeout=5,
        )
        if resp.status_code == 200:
            log.info(f"Gotify alert sent  ({prob:.0%})")
        else:
            log.warning(f"Gotify returned HTTP {resp.status_code}: {resp.text[:120]}")
    except Exception as e:
        log.error(f"Gotify alert failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# CSV logger
# ═══════════════════════════════════════════════════════════════════════════════

class FallLogger:
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            with open(path, "w", newline="") as f:
                csv.writer(f).writerow(
                    ["timestamp", "prediction", "probability", "alert_sent"]
                )

    def write(self, ts: str, pred: int, prob: float, alerted: bool):
        with open(self.path, "a", newline="") as f:
            csv.writer(f).writerow([ts, pred, f"{prob:.4f}", int(alerted)])


# ═══════════════════════════════════════════════════════════════════════════════
# Main detector
# ═══════════════════════════════════════════════════════════════════════════════

class FallDetector:
    def __init__(self, args):
        self.args = args

        # Load model bundle
        log.info(f"Loading model: {args.model}")
        bundle            = joblib.load(args.model)
        self.model        = bundle["model"]
        self.feature_cols = bundle["feature_cols"]
        self.threshold    = bundle["threshold"]
        log.info(
            f"Model ready — {len(self.feature_cols)} features, "
            f"threshold={self.threshold:.2f}"
        )

        # Sliding window buffer
        self.window = collections.deque(maxlen=args.window)
        self.logger = FallLogger(args.log)

        # State
        self._frame_count = 0
        self._last_infer  = 0
        self._last_alert  = 0.0
        self._running     = False
        self._lock        = threading.Lock()

        # Stats
        self.stats = {
            "frames": 0, "inferences": 0,
            "falls_flagged": 0, "alerts_sent": 0,
            "parse_errors": 0,
        }

        # Debug dashboard (only active when --debug is passed)
        self._debug_state = None
        self._dashboard   = None
        if getattr(args, "debug", False):
            if HAS_DEBUG:
                self._debug_state = DebugState(args.window)
                self._dashboard   = Dashboard(self._debug_state, self.threshold)
            else:
                log.warning("debug_dashboard.py not found — --debug has no effect")

    # ── inference ──────────────────────────────────────────────────────────────

    def _infer(self) -> tuple:
        with self._lock:
            window_snap = list(self.window)

        feats = extract_features(window_snap)
        X     = pd.DataFrame(
            [[feats.get(col, 0.0) for col in self.feature_cols]],
            columns=self.feature_cols,
        )
        prob = float(self.model.predict_proba(X)[0, 1])
        pred = int(prob >= self.threshold)
        return prob, pred

    # ── alert ──────────────────────────────────────────────────────────────────

    def _maybe_alert(self, prob: float, ts: str) -> bool:
        now = time.time()
        if now - self._last_alert < self.args.cooldown:
            return False
        self._last_alert = now
        log.warning(f"🚨 FALL DETECTED  confidence={prob:.1%}  time={ts}")
        if self.args.gotify_url and self.args.gotify_token:
            send_gotify_alert(
                self.args.gotify_url, self.args.gotify_token, prob, ts
            )
        self.stats["alerts_sent"] += 1
        return True

    # ── reader thread: launches mmwave_run6.py, reads its stdout ───────────────

    def _reader_thread(self):
        cmd = [
            sys.executable, self.args.parser,
        ]

        # Pass port/cfg overrides via environment variables that mmwave_run6.py
        # respects, then patch CLI_PORT / DATA_PORT / CFG_FILE at the top of
        # the script via a tiny wrapper approach.
        # Simpler: we just patch the three settings by rewriting them in the
        # subprocess environment isn't possible for hardcoded vars, so we
        # launch with a monkeypatch env trick via -c.

        patch = (
            f"import mmwave_run6 as m; "
            f"m.CLI_PORT='{self.args.cli_port}'; "
            f"m.DATA_PORT='{self.args.data_port}'; "
            f"m.CFG_FILE='{self.args.cfg_file}'; "
            f"m.main()"
        )
        cmd = [sys.executable, "-c", patch]

        # Make sure the directory containing mmwave_run6.py is on the path
        parser_dir = os.path.dirname(os.path.abspath(self.args.parser))

        log.info(f"Starting parser: {self.args.parser}")
        log.info(f"  CLI  port : {self.args.cli_port}")
        log.info(f"  Data port : {self.args.data_port}")
        log.info(f"  Config    : {self.args.cfg_file}")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,   # parser's status logs go here
                text=True,
                cwd=parser_dir,
                env={**os.environ, "PYTHONPATH": parser_dir},
            )
            self._proc = proc

            # Forward parser's stderr to our log at DEBUG level
            def _forward_stderr():
                for line in proc.stderr:
                    line = line.rstrip()
                    if line:
                        log.debug(f"[parser] {line}")
            threading.Thread(target=_forward_stderr, daemon=True).start()

            # Read JSON frames from parser stdout
            for raw_line in proc.stdout:
                if not self._running:
                    break
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    frame = json.loads(raw_line)
                except json.JSONDecodeError:
                    self.stats["parse_errors"] += 1
                    log.debug(f"JSON parse error: {raw_line[:80]}")
                    continue

                with self._lock:
                    self.window.append(frame)
                self._frame_count += 1
                self.stats["frames"] += 1

                # Feed debug dashboard
                if self._debug_state is not None:
                    self._debug_state.update_frame(frame)

            proc.wait()
            if proc.returncode and proc.returncode != 0:
                log.error(f"Parser exited with code {proc.returncode}")

        except Exception as e:
            log.error(f"Reader thread error: {e}")
        finally:
            self._running = False

    # ── main loop ──────────────────────────────────────────────────────────────

    def run(self):
        self._running = True
        self._proc    = None

        log.info(
            f"Fall detector starting — "
            f"window={self.args.window} frames  "
            f"step={self.args.step} frames  "
            f"cooldown={self.args.cooldown}s"
        )

        # Start debug dashboard if requested
        if self._dashboard is not None:
            self._dashboard.start()
            log.info("Debug dashboard active — press 'q' to quit, 'c' to clear history")

        reader = threading.Thread(target=self._reader_thread, daemon=True)
        reader.start()

        last_infer_at  = 0
        # Warmup: skip inference for the first N frames so the window fills
        # with stable baseline data before we start making predictions.
        # At ~10fps, default warmup=48 = ~4.8 seconds.
        warmup_frames  = getattr(self.args, "warmup", 48)
        warmup_done    = False
        try:
            while self._running:
                current = self._frame_count

                if not warmup_done:
                    if current >= warmup_frames:
                        warmup_done = True
                        log.info(f"Warmup complete ({warmup_frames} frames) — inference active")
                    else:
                        time.sleep(0.01)
                        continue

                if (
                    len(self.window) >= self.args.window
                    and current - last_infer_at >= self.args.step
                ):
                    last_infer_at = current
                    t0 = time.perf_counter()
                    prob, pred = self._infer()
                    elapsed_ms = (time.perf_counter() - t0) * 1000

                    self.stats["inferences"] += 1
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    alerted = False
                    if pred:
                        self.stats["falls_flagged"] += 1
                        alerted = self._maybe_alert(prob, ts)

                    self.logger.write(ts, pred, prob, alerted)

                    # Feed debug dashboard
                    if self._debug_state is not None:
                        self._debug_state.update_inference(prob, pred, alerted)

                    if self.args.verbose or pred:
                        tag = "FALL ⚠️ " if pred else "ok    "
                        log.info(
                            f"{tag} prob={prob:.3f}  "
                            f"frames={self.stats['frames']}  "
                            f"infer={elapsed_ms:.0f}ms  "
                            f"alerts={self.stats['alerts_sent']}"
                        )
                else:
                    time.sleep(0.01)

        except KeyboardInterrupt:
            log.info("Shutting down…")
        finally:
            self._running = False
            if self._dashboard is not None:
                self._dashboard.stop()
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
            log.info(
                f"Session summary — "
                f"frames={self.stats['frames']}  "
                f"inferences={self.stats['inferences']}  "
                f"falls={self.stats['falls_flagged']}  "
                f"alerts={self.stats['alerts_sent']}  "
                f"parse_errors={self.stats['parse_errors']}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args():
    p = argparse.ArgumentParser(
        description="Live fall detection — uses mmwave_run6.py as radar parser"
    )
    p.add_argument("--parser",       required=True,
                   help="Path to mmwave_run6.py")
    p.add_argument("--model",        required=True,
                   help="Path to best_model_pi_v3.pkl")
    p.add_argument("--cli-port",     default="/dev/ttyUSB0",
                   help="Radar CLI/config UART port  [default: /dev/ttyUSB0]")
    p.add_argument("--data-port",    default="/dev/ttyUSB1",
                   help="Radar data UART port        [default: /dev/ttyUSB1]")
    p.add_argument("--cfg-file",     default="config3.cfg",
                   help="Radar .cfg file             [default: config3.cfg]")
    p.add_argument("--window",       default=32,  type=int,
                   help="Sliding window size (frames) [default: 32]")
    p.add_argument("--step",         default=6,   type=int,
                   help="New frames between inferences [default: 6]")
    p.add_argument("--cooldown",     default=15.0, type=float,
                   help="Min seconds between alerts  [default: 15.0]")
    p.add_argument("--gotify-url",   default=None,
                   help="Gotify server base URL  e.g. http://192.168.1.10:8080")
    p.add_argument("--gotify-token", default=None,
                   help="Gotify app token")
    p.add_argument("--log",          default="fall_log.csv",
                   help="CSV log file path           [default: fall_log.csv]")
    p.add_argument("--verbose",      action="store_true",
                   help="Print every inference result")
    p.add_argument("--debug",        action="store_true",
                   help="Enable live terminal debug dashboard (requires debug_dashboard.py)")
    p.add_argument("--warmup",       default=48, type=int,
                   help="Frames to collect before first inference (~10fps so 48=~5s) [default: 48]")
    return p.parse_args()


def main():
    args = parse_args()

    # Sanity checks before starting
    if not os.path.exists(args.parser):
        log.error(f"Parser not found: {args.parser}")
        sys.exit(1)
    if not os.path.exists(args.model):
        log.error(f"Model not found: {args.model}")
        sys.exit(1)
    if not os.path.exists(args.cfg_file):
        log.error(f"Config file not found: {args.cfg_file}")
        sys.exit(1)
    if args.gotify_url and not args.gotify_token:
        log.warning("--gotify-url set but --gotify-token missing — alerts will not send")

    FallDetector(args).run()


if __name__ == "__main__":
    main()
