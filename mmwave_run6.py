"""
mmwave_run6.py
--------------
Based on mmwave_run5_clustered.py, with one key improvement:

Step 2 (soft distance preference): when multiple clusters exist, prefer clusters
whose center-y is within a configurable "near" range, so we don't accidentally
select a back-wall / far clutter cluster when a nearer (likely-person) cluster
is present.

This is NOT a hard ROI. If no near clusters exist, we fall back to selecting
the best cluster from all clusters.

Env var added:
  MMW_PREF_Y_MAX (default 3.5)  # meters

All other behavior/output stays the same.
"""

import os
import sys
import time
import struct
import json
import statistics
from collections import deque

import serial
import numpy as np


# ========= USER SETTINGS =========
CLI_PORT  = "COM5"
DATA_PORT = "COM6"
CFG_FILE  = "config3.cfg"

CLI_BAUD  = 115200
DATA_BAUD = 921600
TIMEOUT   = 0.5
# =================================

# ---------- Logging (STDERR only) ----------
PRINT_CLI_ECHO = False
STATUS_LOGS    = True

def _elog(msg: str):
    if STATUS_LOGS:
        print(msg, file=sys.stderr, flush=True)


MAGIC = b"\x02\x01\x04\x03\x06\x05\x08\x07"

FRAME_HDR_FMT = "<QIIIIIIII"
FRAME_HDR_LEN = struct.calcsize(FRAME_HDR_FMT)

TLV_HDR_FMT = "<II"
TLV_HDR_LEN = struct.calcsize(TLV_HDR_FMT)

TLV_DETECTED_POINTS = 1
TLV_SIDE_INFO_TYPES = {7, 12}

# -----------------------------
# Tunables (environment overrides supported)
# -----------------------------
MAX_POINTS = int(os.environ.get("MMW_MAX_POINTS", "50"))

# Hard physical sanity bounds (broad, NOT ROI)
MAX_ABS_X = float(os.environ.get("MMW_MAX_ABS_X", "6.0"))
MIN_Y     = float(os.environ.get("MMW_MIN_Y", "1.0"))
MAX_Y     = float(os.environ.get("MMW_MAX_Y", "8.0"))
MAX_ABS_Z = float(os.environ.get("MMW_MAX_ABS_Z", "3.0"))
MAX_ABS_V = float(os.environ.get("MMW_MAX_ABS_V", "6.0"))

# If side-info is present, reject weak points (helps remove multipath/clutter)
MIN_SNR = int(os.environ.get("MMW_MIN_SNR", "70"))

# Cluster selection & gating
CLUSTER_EPS_M       = float(os.environ.get("MMW_CLUSTER_EPS", "0.7"))
CLUSTER_MIN_SAMPLES = int(os.environ.get("MMW_CLUSTER_MIN_SAMPLES", "3"))
MIN_PERSON_POINTS   = int(os.environ.get("MMW_MIN_PERSON_POINTS", "4"))
MAX_MEDIAN_RADIUS_M = float(os.environ.get("MMW_MAX_MEDIAN_RADIUS", "0.85"))

# Step 2: soft "near" preference to avoid back-wall clusters when a closer cluster exists
PREF_Y_MAX = float(os.environ.get("MMW_PREF_Y_MAX", "3.5"))

# Optional: softly reject mostly-static blobs (walls) without killing "standing still"
MIN_MEDIAN_SPEED_MPS = float(os.environ.get("MMW_MIN_MEDIAN_SPEED", "0.00"))


def send_cmd(cli: serial.Serial, cmd: str) -> bool:
    cli.write((cmd + "\n").encode("utf-8"))
    time.sleep(0.10)
    resp = cli.read_all().decode(errors="ignore")
    if PRINT_CLI_ECHO and resp.strip():
        print(resp.strip(), file=sys.stderr, flush=True)
    return ("Error" not in resp) and ("not recognized" not in resp)


def open_ports():
    cli  = serial.Serial(CLI_PORT,  CLI_BAUD,  timeout=TIMEOUT)
    data = serial.Serial(DATA_PORT, DATA_BAUD, timeout=TIMEOUT)
    cli.reset_input_buffer(); cli.reset_output_buffer()
    data.reset_input_buffer(); data.reset_output_buffer()
    time.sleep(0.2)
    return cli, data


def send_cfg(cli: serial.Serial, cfg_path: str):
    send_cmd(cli, "sensorStop")
    send_cmd(cli, "flushCfg")
    with open(cfg_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.split("%", 1)[0].strip()
            if line:
                send_cmd(cli, line)


def get_packet(buf: bytearray, data_port: serial.Serial):
    while True:
        chunk = data_port.read(4096)
        if chunk:
            buf.extend(chunk)

        idx = buf.find(MAGIC)
        if idx < 0:
            if len(buf) > 65536:
                del buf[:-4096]
            continue

        if idx > 0:
            del buf[:idx]

        if len(buf) < FRAME_HDR_LEN:
            continue

        header = struct.unpack_from(FRAME_HDR_FMT, buf, 0)
        totalLen = header[2]

        if totalLen < FRAME_HDR_LEN or totalLen > 65536:
            del buf[0:1]
            continue

        if len(buf) < totalLen:
            continue

        packet = bytes(buf[:totalLen])
        del buf[:totalLen]
        return header, packet[FRAME_HDR_LEN:]


def parse_detected_points(tlv_data: bytes):
    pts = []
    rec = 16
    n = len(tlv_data) // rec
    for i in range(n):
        x, y, z, v = struct.unpack_from("<ffff", tlv_data, i * rec)
        pts.append((x, y, z, v))
    return pts


def parse_side_info(tlv_data: bytes):
    out = []
    rec = 4
    n = len(tlv_data) // rec
    for i in range(n):
        snr, noise = struct.unpack_from("<hh", tlv_data, i * rec)
        out.append((int(snr), int(noise)))
    return out


def robust_center(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    vs = [p[3] for p in points]
    return (
        float(statistics.median(xs)),
        float(statistics.median(ys)),
        float(statistics.median(zs)),
        float(statistics.median(vs)),
    )


def median_radius(points, center):
    cx, cy, cz, _ = center
    dists = []
    for (x, y, z, _) in points:
        dx, dy, dz = x - cx, y - cy, z - cz
        dists.append((dx*dx + dy*dy + dz*dz) ** 0.5)
    return float(statistics.median(dists)) if dists else float("inf")


def cap_near_center(points, center, max_points: int):
    cx, cy, cz, _ = center
    def dist2(p):
        dx = p[0] - cx
        dy = p[1] - cy
        dz = p[2] - cz
        return dx*dx + dy*dy + dz*dz
    return sorted(points, key=dist2)[:max_points]


def dbscan_cluster_indices(xyz: np.ndarray, eps: float, min_samples: int):
    n = xyz.shape[0]
    if n == 0:
        return np.array([], dtype=int)

    eps2 = eps * eps
    labels = np.full(n, -1, dtype=int)
    visited = np.zeros(n, dtype=bool)

    neighbors = []
    for i in range(n):
        di = xyz - xyz[i]
        d2 = np.sum(di * di, axis=1)
        neighbors.append(np.where(d2 <= eps2)[0])

    cluster_id = 0
    for i in range(n):
        if visited[i]:
            continue
        visited[i] = True
        nbrs = neighbors[i]
        if nbrs.size < min_samples:
            labels[i] = -1
            continue

        labels[i] = cluster_id
        q = deque(nbrs.tolist())
        while q:
            j = q.popleft()
            if not visited[j]:
                visited[j] = True
                nbrs_j = neighbors[j]
                if nbrs_j.size >= min_samples:
                    q.extend(nbrs_j.tolist())
            if labels[j] == -1:
                labels[j] = cluster_id

        cluster_id += 1

    return labels


def pick_best_cluster(points, snrs, labels):
    """
    Step 2 implementation:
      - Build clusters from labels
      - Prefer "near" clusters (center_y <= PREF_Y_MAX) if any exist
      - Choose best cluster by a score (size, mean_snr, compactness, motion, and slight y bias)
    Returns list of point indices for the chosen cluster.
    """
    if labels.size == 0:
        return []

    # cluster_id -> indices
    clusters = {}
    for i, lab in enumerate(labels.tolist()):
        if lab < 0:
            continue
        clusters.setdefault(int(lab), []).append(int(i))

    if not clusters:
        return []

    def cluster_center_y(idxs):
        ys = [points[i][1] for i in idxs]
        ys.sort()
        return float(ys[len(ys)//2])

    # Prefer near clusters, but do NOT hard reject far clusters.
    near_clusters = {cid: idxs for cid, idxs in clusters.items() if cluster_center_y(idxs) <= PREF_Y_MAX}
    pool = near_clusters if near_clusters else clusters

    def score(idxs):
        n = len(idxs)
        cluster_pts = [points[i] for i in idxs]
        c = robust_center(cluster_pts)
        mr = median_radius(cluster_pts, c)
        mean_abs_v = float(sum(abs(points[i][3]) for i in idxs) / max(1, n))
        cy = cluster_center_y(idxs)

        if snrs is not None and len(snrs) == len(points):
            mean_snr = float(np.mean([snrs[i] for i in idxs]))
        else:
            mean_snr = 0.0

        # Higher is better.
        # - size dominates
        # - mean_snr helps when available
        # - compactness penalizes wall sheets
        # - motion gives a small boost
        # - small y penalty biases closer within the pool
        return (1.0*n) + (0.02*mean_snr) - (0.8*mr) + (0.4*mean_abs_v) - (0.05*cy)

    best_cid = max(pool.keys(), key=lambda cid: score(pool[cid]))
    return pool[best_cid]


def build_person_obj(best_pts):
    center = robust_center(best_pts)
    best_pts = cap_near_center(best_pts, center, MAX_POINTS)

    mr = median_radius(best_pts, center)
    med_speed = float(statistics.median([abs(p[3]) for p in best_pts])) if best_pts else 0.0

    conf_count = min(1.0, len(best_pts) / 20.0)
    conf_compact = max(0.0, 1.0 - (mr / max(1e-6, MAX_MEDIAN_RADIUS_M)))
    conf_motion = 1.0 if MIN_MEDIAN_SPEED_MPS <= 0 else min(1.0, med_speed / max(1e-6, MIN_MEDIAN_SPEED_MPS))

    confidence = 0.55 * conf_count + 0.40 * conf_compact + 0.05 * conf_motion
    confidence = float(max(0.0, min(1.0, confidence)))

    return {
        "present": True,
        "confidence": round(confidence, 3),
        "center": {
            "x": round(center[0], 3),
            "y": round(center[1], 3),
            "z": round(center[2], 3),
            "v": round(center[3], 3),
        },
        "num_points": int(len(best_pts)),
        "points": [
            {"x": round(p[0], 3), "y": round(p[1], 3), "z": round(p[2], 3), "v": round(p[3], 3)}
            for p in best_pts
        ],
    }


def main():
    _elog(f"[INFO] Opening ports: CLI={CLI_PORT} ({CLI_BAUD})  DATA={DATA_PORT} ({DATA_BAUD})")
    cli, data = open_ports()

    try:
        send_cfg(cli, CFG_FILE)
        send_cmd(cli, "sensorStart")
        _elog("[INFO] Running... (Ctrl+C to stop)")

        buf = bytearray()
        t0 = time.monotonic()

        while True:
            header, payload = get_packet(buf, data)

            numTLVs = header[7]
            ofs = 0
            pts = []
            side = None

            for _ in range(numTLVs):
                if ofs + TLV_HDR_LEN > len(payload):
                    break
                tlv_type, tlv_len = struct.unpack_from(TLV_HDR_FMT, payload, ofs)
                tlv_start = ofs + TLV_HDR_LEN
                tlv_end = tlv_start + tlv_len
                if tlv_end > len(payload):
                    break
                tlv_data = payload[tlv_start:tlv_end]

                if tlv_type == TLV_DETECTED_POINTS:
                    pts = parse_detected_points(tlv_data)
                elif tlv_type in TLV_SIDE_INFO_TYPES:
                    side = parse_side_info(tlv_data)

                ofs = tlv_end

            snrs = None
            if side is not None and len(side) == len(pts):
                snrs = [s[0] for s in side]

            # --- Step 1: bounds + (optional) SNR filtering ---
            cand_pts = []
            cand_snrs = [] if snrs is not None else None

            for i, (x, y, z, v) in enumerate(pts):
                if not (
                    abs(x) <= MAX_ABS_X and
                    MIN_Y <= y <= MAX_Y and
                    abs(z) <= MAX_ABS_Z and
                    abs(v) <= MAX_ABS_V
                ):
                    continue

                if snrs is not None and snrs[i] < MIN_SNR:
                    continue

                cand_pts.append((float(x), float(y), float(z), float(v)))
                if cand_snrs is not None:
                    cand_snrs.append(int(snrs[i]))

            # --- Step 2: densest cluster selection (now with near preference) ---
            if len(cand_pts) < MIN_PERSON_POINTS:
                person_obj = {"present": False}
            else:
                xyz = np.asarray([[p[0], p[1], p[2]] for p in cand_pts], dtype=float)
                labels = dbscan_cluster_indices(xyz, CLUSTER_EPS_M, CLUSTER_MIN_SAMPLES)
                best_idx = pick_best_cluster(cand_pts, cand_snrs, labels)
                best_pts = [cand_pts[i] for i in best_idx]

                if len(best_pts) < MIN_PERSON_POINTS:
                    person_obj = {"present": False}
                else:
                    c = robust_center(best_pts)
                    mr = median_radius(best_pts, c)
                    med_speed = float(statistics.median([abs(p[3]) for p in best_pts])) if best_pts else 0.0

                    if mr > MAX_MEDIAN_RADIUS_M:
                        person_obj = {"present": False}
                    elif MIN_MEDIAN_SPEED_MPS > 0 and med_speed < MIN_MEDIAN_SPEED_MPS:
                        person_obj = {"present": False}
                    else:
                        person_obj = build_person_obj(best_pts)

            # Always output capped filtered points (even if person.present is false)
            points_filt = cand_pts
            if len(points_filt) > MAX_POINTS:
                c_all = robust_center(points_filt)
                points_filt = cap_near_center(points_filt, c_all, MAX_POINTS)

            out = {
                "ts": round(time.monotonic() - t0, 3),
                "frame": int(header[4]),

                # NEW: always present for ML + debugging
                "num_points_filt": int(len(points_filt)),
                "points_filt": [
                    {"x": round(p[0], 3), "y": round(p[1], 3), "z": round(p[2], 3), "v": round(p[3], 3)}
                    for p in points_filt
                ],

                # Existing “best guess” person detection
                "person": person_obj,
            }
            print(json.dumps(out), flush=True)

    except KeyboardInterrupt:
        _elog("[INFO] Stopping (Ctrl+C).")
    finally:
        try:
            send_cmd(cli, "sensorStop")
        except Exception:
            pass
        try:
            cli.close()
        except Exception:
            pass
        try:
            data.close()
        except Exception:
            pass
        _elog("[INFO] Ports closed.")


if __name__ == "__main__":
    main()
