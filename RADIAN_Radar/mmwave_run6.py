"""
mmwave_run6.py
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
MIN_Y     = float(os.environ.get("MMW_MIN_Y", "0.5"))
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

# soft "near" preference to avoid back-wall clusters when a closer cluster exists
PREF_Y_MAX = float(os.environ.get("MMW_PREF_Y_MAX", "3.5"))

# softly reject mostly-static blobs (walls) without killing "standing still"
MIN_MEDIAN_SPEED_MPS = float(os.environ.get("MMW_MIN_MEDIAN_SPEED", "0.00"))

# send one command to the radar CLI port and check for command errors
def send_cmd(cli: serial.Serial, cmd: str) -> bool:
    cli.write((cmd + "\n").encode("utf-8"))
    time.sleep(0.10)
    # read back the radar response
    resp = cli.read_all().decode(errors="ignore")
    # print the CLI response for debugging
    if PRINT_CLI_ECHO and resp.strip():
        print(resp.strip(), file=sys.stderr, flush=True)
    # return true is no error text was found in response
    return ("Error" not in resp) and ("not recognized" not in resp)

# open and inizialize CLI and DATA serial ports
def open_ports():
    # opening serial ports
    cli  = serial.Serial(CLI_PORT,  CLI_BAUD,  timeout=TIMEOUT)
    data = serial.Serial(DATA_PORT, DATA_BAUD, timeout=TIMEOUT)
    # clearing any leftover data in buffers
    cli.reset_input_buffer(); cli.reset_output_buffer()
    data.reset_input_buffer(); data.reset_output_buffer()
    # time delay to stabilize connection
    time.sleep(0.2)
    return cli, data

# send radar config file to the CLI port
def send_cfg(cli: serial.Serial, cfg_path: str):
    # stop sensor and clear previous config
    send_cmd(cli, "sensorStop")
    send_cmd(cli, "flushCfg")
    # read config file
    with open(cfg_path, "r", encoding="utf-8") as f:
        # read each line, strip comments/whitespace, and send valid commands
        for raw in f:
            line = raw.split("%", 1)[0].strip()
            if line:
                send_cmd(cli, line)

# continuously read DATA port and extract a radar frame
def get_packet(buf: bytearray, data_port: serial.Serial):
    while True:
        # read incoming chunck of bytes from the DATA serial port
        chunk = data_port.read(4096)
        if chunk:
            buf.extend(chunk)
        # find start of frame 
        idx = buf.find(MAGIC)
        if idx < 0:
            if len(buf) > 65536:
                del buf[:-4096]
            continue
        # align butter to frame start
        if idx > 0:
            del buf[:idx]
        # ensure full header is available
        if len(buf) < FRAME_HDR_LEN:
            continue
        # parse frame header
        header = struct.unpack_from(FRAME_HDR_FMT, buf, 0)
        totalLen = header[2]
        # validate packet length
        if totalLen < FRAME_HDR_LEN or totalLen > 65536:
            del buf[0:1]
            continue
        # wait until full packet is received
        if len(buf) < totalLen:
            continue
        # extract full packet and return
        packet = bytes(buf[:totalLen])
        del buf[:totalLen]
        return header, packet[FRAME_HDR_LEN:]

# parse TLV payload data into a list of detected tuples (x, y, z, v)
def parse_detected_points(tlv_data: bytes):
    # create output list and define bytes per point record
    pts = []
    rec = 16
    # determine how many full point records are in the TLV payload
    n = len(tlv_data) // rec
    # unpack each point record and append it to the list
    for i in range(n):
        x, y, z, v = struct.unpack_from("<ffff", tlv_data, i * rec)
        pts.append((x, y, z, v))
    # returned parsed points
    return pts

# parse TLV side info payload into a list of (snr, noise) tuples
def parse_side_info(tlv_data: bytes):
    # create output list and define bytes per side info record
    out = []
    rec = 4
    # determine how many full side info records are in the TLV payload
    n = len(tlv_data) // rec
    # unpack each side info record and append it to the list
    for i in range(n):
        snr, noise = struct.unpack_from("<hh", tlv_data, i * rec)
        out.append((int(snr), int(noise)))
    # return the parsed SNR/noise data
    return out

# compute the median based center of a group of points 
def robust_center(points):
    # separate x, y, z, and velocity values into individual lists
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    vs = [p[3] for p in points]
    # return the median x, y, z, and velocity as the cluster center
    return (
        float(statistics.median(xs)),
        float(statistics.median(ys)),
        float(statistics.median(zs)),
        float(statistics.median(vs)),
    )

# measure how spread out a point cluster is around its center
def median_radius(points, center):
    # extract the center coordinates and create distance list
    cx, cy, cz, _ = center
    # compute each point's 3d distance from the center
    dists = []
    for (x, y, z, _) in points:
        dx, dy, dz = x - cx, y - cy, z - cz
        dists.append((dx*dx + dy*dy + dz*dz) ** 0.5)
    # return the median distance, or infinity if no points exist
    return float(statistics.median(dists)) if dists else float("inf")

# keep only the points closest to the cluster center up to max_points
def cap_near_center(points, center, max_points: int):
    # extract center coordinates
    cx, cy, cz, _ = center
    # define a helper function for squared distance to the center
    def dist2(p):
        dx = p[0] - cx
        dy = p[1] - cy
        dz = p[2] - cz
        return dx*dx + dy*dy + dz*dz
    # sort points by dstance to center and return the nearest max_points
    return sorted(points, key=dist2)[:max_points]

# group neaby 3d points into clusters using a DBSCAN style algorithm
def dbscan_cluster_indices(xyz: np.ndarray, eps: float, min_samples: int):
    # get number of points and handle empty input
    n = xyz.shape[0]
    if n == 0:
        return np.array([], dtype=int)
    # inizialize clustering variables
    eps2 = eps * eps
    labels = np.full(n, -1, dtype=int)
    visited = np.zeros(n, dtype=bool)
    # precompute each point's neighbors within eps distance
    neighbors = []
    for i in range(n):
        di = xyz - xyz[i]
        d2 = np.sum(di * di, axis=1)
        neighbors.append(np.where(d2 <= eps2)[0])
    # visit each point and grow clusters from dense regions
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
    # return the cluster label assigned to each point
    return labels

# select the cluster most likely to represent a person based on size, compactness, motion, SNR, and distance
def pick_best_cluster(points, snrs, labels):
    # handle empty label input
    if labels.size == 0:
        return []
    # build a dictionary mapping cluster_id to point indices
    clusters = {}
    for i, lab in enumerate(labels.tolist()):
        if lab < 0:
            continue
        clusters.setdefault(int(lab), []).append(int(i))
    # return empty if no valid clusters were found 
    if not clusters:
        return []
    # define helper function to estimate a cluster's center y-position
    def cluster_center_y(idxs):
        ys = [points[i][1] for i in idxs]
        ys.sort()
        return float(ys[len(ys)//2])
    # prefer clusters closer to the radar, but not a hard reject for far clusters
    near_clusters = {cid: idxs for cid, idxs in clusters.items() if cluster_center_y(idxs) <= PREF_Y_MAX}
    pool = near_clusters if near_clusters else clusters
    # define a scoring function to rank each candidate cluster
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
        # combine cluster quality metrics into one score
        return (1.0*n) + (0.02*mean_snr) - (0.8*mr) + (0.4*mean_abs_v) - (0.05*cy)
    # select and return the highest scoreing cluster
    best_cid = max(pool.keys(), key=lambda cid: score(pool[cid]))
    return pool[best_cid]

# build the final person detection dictionary from the selected cluster
def build_person_obj(best_pts):
    # compute a robust center for the selected cluster
    center = robust_center(best_pts)
    # limit the number of points by keeping those closest to the center
    best_pts = cap_near_center(best_pts, center, MAX_POINTS)
    # compute cluster spread and median speed
    mr = median_radius(best_pts, center)
    med_speed = float(statistics.median([abs(p[3]) for p in best_pts])) if best_pts else 0.0
    # compute confidence components based on count, compactness, and motion
    conf_count = min(1.0, len(best_pts) / 20.0)
    conf_compact = max(0.0, 1.0 - (mr / max(1e-6, MAX_MEDIAN_RADIUS_M)))
    conf_motion = 1.0 if MIN_MEDIAN_SPEED_MPS <= 0 else min(1.0, med_speed / max(1e-6, MIN_MEDIAN_SPEED_MPS))
    # combine confidence components into a final bounded confidence score
    confidence = 0.55 * conf_count + 0.40 * conf_compact + 0.05 * conf_motion
    confidence = float(max(0.0, min(1.0, confidence)))
    # return the formatted person detected object
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

# run the full radar pipeline from serial setup to packet parsing and JSON output
def main():
    # open radar serial ports and log startup information
    _elog(f"[INFO] Opening ports: CLI={CLI_PORT} ({CLI_BAUD})  DATA={DATA_PORT} ({DATA_BAUD})")
    cli, data = open_ports()

    try:
        # send radar config and start the sensor
        send_cfg(cli, CFG_FILE)
        send_cmd(cli, "sensorStart")
        _elog("[INFO] Running... (Ctrl+C to stop)")
        # initialize packet buffer and time reference
        buf = bytearray()
        t0 = time.monotonic()

        while True:
            # read one complete radar packet
            header, payload = get_packet(buf, data)
            # parse all TLVs in the packet payload
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
            # extract SNR values if side info matches detected points
            snrs = None
            if side is not None and len(side) == len(pts):
                snrs = [s[0] for s in side]

            # apply physical bounds and optional SNR filtering to candidate points
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

            # cluster filtered points and decide whether a valid person is present
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

            # build capped filitered point output for ML/debugging
            points_filt = cand_pts
            if len(points_filt) > MAX_POINTS:
                c_all = robust_center(points_filt)
                points_filt = cap_near_center(points_filt, c_all, MAX_POINTS)
            # build final NDJSON output object
            out = {
                "ts": round(time.monotonic() - t0, 3),
                "frame": int(header[4]),

                "num_points_filt": int(len(points_filt)),
                "points_filt": [
                    {"x": round(p[0], 3), "y": round(p[1], 3), "z": round(p[2], 3), "v": round(p[3], 3)}
                    for p in points_filt
                ],
                "person": person_obj,
            }
            # print one JSON object per frame to STDOUT
            print(json.dumps(out), flush=True)

    except KeyboardInterrupt:
        # handle Ctrl+C 
        _elog("[INFO] Stopping (Ctrl+C).")
    finally:
        # stop sensor and close serial ports
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
        # log shutdown completion
        _elog("[INFO] Ports closed.")

if __name__ == "__main__":
    main()
