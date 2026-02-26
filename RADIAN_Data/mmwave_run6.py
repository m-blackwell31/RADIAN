"""
mmwave_run6_liveplot.py
Same logic as mmwave_run6.py
But outputs live radar visualization on Raspberry Pi instead of JSON.
"""

import os
import sys
import time
import struct
import statistics
from collections import deque
import matplotlib.pyplot as plt

import serial
import numpy as np


# ========= USER SETTINGS =========
CLI_PORT  = "/dev/ttyUSB0"   # CHANGE if needed
DATA_PORT = "/dev/ttyUSB1"   # CHANGE if needed
CFG_FILE  = "config3.cfg"

CLI_BAUD  = 115200
DATA_BAUD = 921600
TIMEOUT   = 0.5
# =================================

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

MAX_POINTS = int(os.environ.get("MMW_MAX_POINTS", "50"))
MAX_ABS_X = float(os.environ.get("MMW_MAX_ABS_X", "6.0"))
MIN_Y     = float(os.environ.get("MMW_MIN_Y", "1.0"))
MAX_Y     = float(os.environ.get("MMW_MAX_Y", "8.0"))
MAX_ABS_Z = float(os.environ.get("MMW_MAX_ABS_Z", "3.0"))
MAX_ABS_V = float(os.environ.get("MMW_MAX_ABS_V", "6.0"))
MIN_SNR = int(os.environ.get("MMW_MIN_SNR", "70"))

CLUSTER_EPS_M       = float(os.environ.get("MMW_CLUSTER_EPS", "0.7"))
CLUSTER_MIN_SAMPLES = int(os.environ.get("MMW_CLUSTER_MIN_SAMPLES", "3"))
MIN_PERSON_POINTS   = int(os.environ.get("MMW_MIN_PERSON_POINTS", "4"))
MAX_MEDIAN_RADIUS_M = float(os.environ.get("MMW_MAX_MEDIAN_RADIUS", "0.85"))
PREF_Y_MAX = float(os.environ.get("MMW_PREF_Y_MAX", "3.5"))
MIN_MEDIAN_SPEED_MPS = float(os.environ.get("MMW_MIN_MEDIAN_SPEED", "0.00"))


def send_cmd(cli, cmd):
    cli.write((cmd + "\n").encode())
    time.sleep(0.1)
    return True


def open_ports():
    cli  = serial.Serial(CLI_PORT,  CLI_BAUD,  timeout=TIMEOUT)
    data = serial.Serial(DATA_PORT, DATA_BAUD, timeout=TIMEOUT)
    time.sleep(0.2)
    return cli, data


def send_cfg(cli, path):
    send_cmd(cli, "sensorStop")
    send_cmd(cli, "flushCfg")
    with open(path) as f:
        for raw in f:
            line = raw.split("%", 1)[0].strip()
            if line:
                send_cmd(cli, line)


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
        totalLen = header[2]

        if len(buf) < totalLen:
            continue

        packet = bytes(buf[:totalLen])
        del buf[:totalLen]
        return header, packet[FRAME_HDR_LEN:]


def parse_detected_points(tlv_data):
    pts = []
    rec = 16
    for i in range(len(tlv_data)//rec):
        pts.append(struct.unpack_from("<ffff", tlv_data, i*rec))
    return pts


def robust_center(points):
    return (
        float(statistics.median([p[0] for p in points])),
        float(statistics.median([p[1] for p in points])),
        float(statistics.median([p[2] for p in points])),
        float(statistics.median([p[3] for p in points]))
    )


def main():
    _elog("[INFO] Opening ports...")
    cli, data = open_ports()
    send_cfg(cli, CFG_FILE)
    send_cmd(cli, "sensorStart")
    _elog("[INFO] Radar running")

    # -------- Plot Setup --------
    plt.ion()
    fig, ax = plt.subplots()
    scatter = ax.scatter([], [])
    center_marker = ax.scatter([], [], marker='x')

    ax.set_xlim(-4, 4)
    ax.set_ylim(0, 8)
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    plt.show()
    # ----------------------------

    buf = bytearray()
    t0 = time.monotonic()

    try:
        while True:
            header, payload = get_packet(buf, data)

            numTLVs = header[7]
            ofs = 0
            pts = []

            for _ in range(numTLVs):
                if ofs + TLV_HDR_LEN > len(payload):
                    break
                tlv_type, tlv_len = struct.unpack_from(TLV_HDR_FMT, payload, ofs)
                tlv_start = ofs + TLV_HDR_LEN
                tlv_end = tlv_start + tlv_len
                tlv_data = payload[tlv_start:tlv_end]

                if tlv_type == TLV_DETECTED_POINTS:
                    pts = parse_detected_points(tlv_data)

                ofs = tlv_end

            # Basic bounds filtering
            cand_pts = [
                (x,y,z,v) for (x,y,z,v) in pts
                if abs(x)<=MAX_ABS_X and MIN_Y<=y<=MAX_Y and abs(z)<=MAX_ABS_Z
            ]

            if cand_pts:
                xs = [p[0] for p in cand_pts]
                ys = [p[1] for p in cand_pts]
                scatter.set_offsets(list(zip(xs, ys)))
            else:
                scatter.set_offsets([])

            ax.set_title(f"Live Radar | Frame {header[4]} | Points: {len(cand_pts)}")
            plt.draw()
            plt.pause(0.01)

    except KeyboardInterrupt:
        _elog("[INFO] Stopping...")

    finally:
        send_cmd(cli, "sensorStop")
        cli.close()
        data.close()


if __name__ == "__main__":
    main()
