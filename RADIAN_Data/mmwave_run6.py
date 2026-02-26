"""
mmwave_run6_terminal.py
-----------------------

Readable terminal-streaming version of mmwave_run6.

Outputs clean human-readable lines like:

Frame 152 | Person @ x=0.42 y=2.31 v=0.18 | Points=17 | Conf=0.87
Frame 153 | No person | Points=3
"""

import os
import sys
import time
import struct
import statistics
from collections import deque

import serial
import numpy as np


# ================= USER SETTINGS =================
CLI_PORT  = "/dev/ttyUSB0"   # CHANGE if needed
DATA_PORT = "/dev/ttyUSB1"   # CHANGE if needed
CFG_FILE  = "config3.cfg"

CLI_BAUD  = 115200
DATA_BAUD = 921600
TIMEOUT   = 0.5
# =================================================


# ================= Tunables =================
MAX_POINTS = 50

MAX_ABS_X = 6.0
MIN_Y     = 1.0
MAX_Y     = 8.0
MAX_ABS_Z = 3.0
MAX_ABS_V = 6.0

MIN_SNR = 70

CLUSTER_EPS_M       = 0.7
CLUSTER_MIN_SAMPLES = 3
MIN_PERSON_POINTS   = 4
MAX_MEDIAN_RADIUS_M = 0.85
PREF_Y_MAX          = 3.5
# ============================================


MAGIC = b"\x02\x01\x04\x03\x06\x05\x08\x07"
FRAME_HDR_FMT = "<QIIIIIIII"
FRAME_HDR_LEN = struct.calcsize(FRAME_HDR_FMT)
TLV_HDR_FMT   = "<II"
TLV_HDR_LEN   = struct.calcsize(TLV_HDR_FMT)

TLV_DETECTED_POINTS = 1
TLV_SIDE_INFO_TYPES = {7, 12}


# ================= Serial Helpers =================

def send_cmd(cli, cmd):
    cli.write((cmd + "\n").encode())
    time.sleep(0.1)


def open_ports():
    cli  = serial.Serial(CLI_PORT,  CLI_BAUD,  timeout=TIMEOUT)
    data = serial.Serial(DATA_PORT, DATA_BAUD, timeout=TIMEOUT)
    time.sleep(0.2)
    return cli, data


def send_cfg(cli, cfg_path):
    send_cmd(cli, "sensorStop")
    send_cmd(cli, "flushCfg")

    with open(cfg_path) as f:
        for raw in f:
            line = raw.split("%", 1)[0].strip()
            if line:
                send_cmd(cli, line)


# ================= Packet Parsing =================

def get_packet(buf, data_port):
    while True:
        chunk = data_port.read(4096)
        if chunk:
            buf.extend(chunk)

        idx = buf.find(MAGIC)
        if idx < 0:
            continue

        if idx > 0:
            del buf[:idx]

        if len(buf) < FRAME_HDR_LEN:
            continue

        header = struct.unpack_from(FRAME_HDR_FMT, buf, 0)
        total_len = header[2]

        if len(buf) < total_len:
            continue

        packet = bytes(buf[:total_len])
        del buf[:total_len]

        return header, packet[FRAME_HDR_LEN:]


def parse_detected_points(tlv_data):
    pts = []
    for i in range(len(tlv_data)//16):
        pts.append(struct.unpack_from("<ffff", tlv_data, i*16))
    return pts


# ================= Clustering =================

def robust_center(points):
    return (
        statistics.median([p[0] for p in points]),
        statistics.median([p[1] for p in points]),
        statistics.median([p[2] for p in points]),
        statistics.median([p[3] for p in points]),
    )


def median_radius(points, center):
    cx, cy, cz, _ = center
    dists = []
    for (x,y,z,_) in points:
        dx, dy, dz = x-cx, y-cy, z-cz
        dists.append((dx*dx + dy*dy + dz*dz)**0.5)
    return statistics.median(dists) if dists else 999


def dbscan(xyz, eps, min_samples):
    n = xyz.shape[0]
    labels = np.full(n, -1)
    visited = np.zeros(n, dtype=bool)

    eps2 = eps * eps
    neighbors = []

    for i in range(n):
        d2 = np.sum((xyz - xyz[i])**2, axis=1)
        neighbors.append(np.where(d2 <= eps2)[0])

    cluster_id = 0

    for i in range(n):
        if visited[i]:
            continue
        visited[i] = True

        nbrs = neighbors[i]
        if len(nbrs) < min_samples:
            continue

        labels[i] = cluster_id
        q = deque(nbrs.tolist())

        while q:
            j = q.popleft()
            if not visited[j]:
                visited[j] = True
                nbrs_j = neighbors[j]
                if len(nbrs_j) >= min_samples:
                    q.extend(nbrs_j.tolist())
            if labels[j] == -1:
                labels[j] = cluster_id

        cluster_id += 1

    return labels


# ================= Main =================

def main():
    print("[INFO] Opening ports...")
    cli, data = open_ports()

    send_cfg(cli, CFG_FILE)
    send_cmd(cli, "sensorStart")
    print("[INFO] Radar running...\n")

    buf = bytearray()

    try:
        while True:
            header, payload = get_packet(buf, data)
            frame_num = header[4]

            numTLVs = header[7]
            ofs = 0
            pts = []

            for _ in range(numTLVs):
                tlv_type, tlv_len = struct.unpack_from(TLV_HDR_FMT, payload, ofs)
                tlv_start = ofs + TLV_HDR_LEN
                tlv_end = tlv_start + tlv_len
                tlv_data = payload[tlv_start:tlv_end]

                if tlv_type == TLV_DETECTED_POINTS:
                    pts = parse_detected_points(tlv_data)

                ofs = tlv_end

            # -------- Basic Filtering --------
            cand = []
            for (x,y,z,v) in pts:
                if abs(x)<=MAX_ABS_X and MIN_Y<=y<=MAX_Y and abs(z)<=MAX_ABS_Z:
                    cand.append((x,y,z,v))

            # -------- Person Detection --------
            if len(cand) < MIN_PERSON_POINTS:
                print(f"Frame {frame_num} | No person | Points={len(cand)}")
                continue

            xyz = np.array([[p[0],p[1],p[2]] for p in cand])
            labels = dbscan(xyz, CLUSTER_EPS_M, CLUSTER_MIN_SAMPLES)

            clusters = {}
            for i,lab in enumerate(labels):
                if lab >= 0:
                    clusters.setdefault(lab, []).append(cand[i])

            if not clusters:
                print(f"Frame {frame_num} | No person | Points={len(cand)}")
                continue

            # Prefer near clusters
            def center_y(cluster):
                return statistics.median([p[1] for p in cluster])

            near = [c for c in clusters.values() if center_y(c) <= PREF_Y_MAX]
            pool = near if near else list(clusters.values())

            best = max(pool, key=len)

            if len(best) < MIN_PERSON_POINTS:
                print(f"Frame {frame_num} | No person | Points={len(cand)}")
                continue

            center = robust_center(best)
            mr = median_radius(best, center)

            if mr > MAX_MEDIAN_RADIUS_M:
                print(f"Frame {frame_num} | No person | Points={len(cand)}")
                continue

            print(
                f"Frame {frame_num} | "
                f"Person @ x={center[0]:.2f} "
                f"y={center[1]:.2f} "
                f"v={center[3]:.2f} | "
                f"Points={len(best)}"
            )

    except KeyboardInterrupt:
        print("\n[INFO] Stopping...")

    finally:
        send_cmd(cli, "sensorStop")
        cli.close()
        data.close()
        print("[INFO] Ports closed.")


if __name__ == "__main__":
    main()
