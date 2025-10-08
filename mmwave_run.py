"""
mmwave_run.py
-------------
Host controller for TI AWR6843ISK over UART.

What this script does:
  1) Opens two serial ports:
       - CLI (115200 bps): sends the .cfg and control commands (sensorStart/Stop)
       - DATA (921600 bps): receives binary TLV frames
  2) Sends your .cfg file line-by-line (stripping inline '%' comments)
  3) Reads frames from the DATA port, decodes the "Detected Points" TLV
  4) Emits each frame as NDJSON on STDOUT (one JSON per line) for your AI
     while logging device echoes and short human messages on STDERR

Notes:
  - Keep this script's STDOUT clean JSON if piping to an AI. We send all
    device echo and debug to STDERR to avoid mixing streams.
  - On Raspberry Pi, update CLI_PORT/DATA_PORT to /dev/ttyACM0/1.
"""

import os, sys, time, struct, json
import serial
from serial.tools import list_ports

# ========= USER SETTINGS =========
# On your laptop (Windows):
CLI_PORT  = "COM5"           # CLI @ 115200 bps  (lower-numbered COM usually)
DATA_PORT = "COM6"           # DATA @ 921600 bps (higher-numbered COM usually)
# On Raspberry Pi 3, change to:
# CLI_PORT  = "/dev/ttyACM0"
# DATA_PORT = "/dev/ttyACM1"

CFG_FILE  = "indoor_fall_detection.cfg"
CLI_BAUD  = 115200
DATA_BAUD = 921600
TIMEOUT   = 0.5              # read timeout (seconds) for both ports
# ================================

# "Magic word" that marks the start of each UART packet on the DATA stream
MAGIC = b"\x02\x01\x04\x03\x06\x05\x08\x07"

# Frame header format for SDK 3.x mmwDemo (40 bytes total)
# magic(8) + version(4) + totalLen(4) + platform(4) + frameNumber(4) +
# timeCpuCycles(4) + numDetectedObj(4) + numTLVs(4) + subFrameNumber(4)
FRAME_HDR_FMT = "<QIIIIIIII"
FRAME_HDR_LEN = struct.calcsize(FRAME_HDR_FMT)

# TLV header: type(4) + length(4)
TLV_HDR_FMT = "<II"
TLV_HDR_LEN = struct.calcsize(TLV_HDR_FMT)

# TLV types we parse (add more if needed)
TLV_DETECTED_POINTS = 1   # float32 x,y,z,velocity per point
TLV_SIDE_INFO       = 12  # optional int16 snr/noise per point

def send_cmd(cli: serial.Serial, cmd: str) -> bool:
    """
    Send a single CLI command and print the device's response to STDERR.
    Returns True if the response did NOT contain 'Error' or 'not recognized'.
    """
    cli.write((cmd + "\n").encode("utf-8"))
    time.sleep(0.10)
    resp = cli.read_all().decode(errors="ignore")
    if resp.strip():
        # Print CLI echoes to STDERR so STDOUT stays JSON-clean
        print(resp.strip(), file=sys.stderr, flush=True)
    ok = ("Error" not in resp) and ("not recognized" not in resp)
    return ok

def open_ports():
    """
    Open CLI and DATA serial ports with expected baud rates and a small delay.
    """
    cli  = serial.Serial(CLI_PORT,  CLI_BAUD,  timeout=TIMEOUT)
    data = serial.Serial(DATA_PORT, DATA_BAUD, timeout=TIMEOUT)
    # Clear any junk in buffers
    cli.reset_input_buffer();  cli.reset_output_buffer()
    data.reset_input_buffer(); data.reset_output_buffer()
    time.sleep(0.2)
    return cli, data

def send_cfg(cli: serial.Serial, cfg_path: str):
    """
    Stream the .cfg to the device.
    - Skips blank lines and full-line comments (% at start)
    - Strips inline comments (anything after a % on the same line)
    """
    if not os.path.exists(cfg_path):
        sys.exit(f"[ERROR] Config file not found: {cfg_path}")

    print(f"[INFO] Sending cfg: {cfg_path}", file=sys.stderr)

    # Clean start guarantees predictable behavior
    send_cmd(cli, "sensorStop")
    send_cmd(cli, "flushCfg")

    with open(cfg_path, "r", encoding="utf-8") as f:
        for raw in f:
            # Remove inline comments and whitespace
            line = raw.split("%", 1)[0].strip()
            if not line:
                continue
            send_cmd(cli, line)

def apply_cfar(cli: serial.Serial):
    """
    Your firmware requires CFAR to be configured with:
      cfarCfg <sfIdx> <procDir> <avgMode> <win> <guard> <noiseDiv> <cyclic> <thr_dB> <peakGroupEn>
    We use 20 dB thresholds (good indoor default) and enable peak grouping.
    If these lines already exist in the .cfg, this simply echoes 'Done' again.
    """
    print("[INFO] Ensuring CFAR (dB threshold + peak grouping)...", file=sys.stderr)
    ok1 = send_cmd(cli, "cfarCfg -1 0 2 8 4 3 0 20 1")  # Range direction
    ok2 = send_cmd(cli, "cfarCfg -1 1 2 4 4 3 0 20 1")  # Doppler direction
    if not (ok1 and ok2):
        # Show the firmware's help so you can adjust parameters if this ever changes
        send_cmd(cli, "help cfarCfg")
        raise RuntimeError("CFAR configuration was not accepted by the device.")
    print("[INFO] CFAR configured.", file=sys.stderr)

def get_packet(buf: bytearray, data_port: serial.Serial):
    """
    Accumulate bytes from DATA UART until a full packet is available.
    Returns: (header_dict, tlv_payload_bytes)
    """
    while True:
        chunk = data_port.read(4096)
        if chunk:
            buf.extend(chunk)

        # Search for the magic word
        idx = buf.find(MAGIC)
        if idx < 0:
            # Avoid unbounded buffer growth if we lose sync
            if len(buf) > 65536:
                del buf[:-4096]
            continue

        # Ensure the full header is present
        if len(buf) < idx + FRAME_HDR_LEN:
            continue

        # Unpack the fixed-size header (magic is part of it via '<Q')
        (magic, version, totalLen, platform, frameNumber,
         timeCpuCycles, numDetectedObj, numTLVs, subFrameNumber) = struct.unpack_from(
            FRAME_HDR_FMT, buf, idx
        )

        end = idx + totalLen
        if len(buf) < end:
            # Not all bytes have arrived yet
            continue

        # Slice out the packet, then consume it from the buffer
        packet = bytes(buf[idx:end])
        del buf[:end]

        header = {
            "version": version,
            "totalLen": totalLen,
            "platform": platform,
            "frameNumber": frameNumber,
            "timeCpuCycles": timeCpuCycles,
            "numDetectedObj": numDetectedObj,
            "numTLVs": numTLVs,
            "subFrameNumber": subFrameNumber,
        }
        payload = packet[FRAME_HDR_LEN:]  # TLVs follow the 40-byte header
        return header, payload

def parse_detected_points(tlv_data: bytes):
    """
    Parse TLV type 1: Detected Points
    Each point = 16 bytes: float32 x, float32 y, float32 z, float32 velocity.
    Returns a list of (x, y, z, v).
    """
    pts = []
    rec = 16
    n = len(tlv_data) // rec
    for i in range(n):
        x, y, z, v = struct.unpack_from("<ffff", tlv_data, i * rec)
        pts.append((x, y, z, v))
    return pts

def parse_side_info(tlv_data: bytes):
    """
    Parse TLV type 12: per-point side info (optional)
    Each record = int16 snr, int16 noise.
    """
    out = []
    rec = 4
    n = len(tlv_data) // rec
    for i in range(n):
        snr, noise = struct.unpack_from("<hh", tlv_data, i * rec)
        out.append((snr, noise))
    return out

def parse_tlvs(payload: bytes, num_tlvs: int):
    """
    Iterate over TLVs in the payload and dispatch parsers.
    Returns a dict with 'points' and optionally 'side_info'.
    """
    ofs = 0
    out = {"points": [], "side_info": []}
    for _ in range(num_tlvs):
        if ofs + TLV_HDR_LEN > len(payload):
            break
        tlv_type, tlv_len = struct.unpack_from(TLV_HDR_FMT, payload, ofs)
        ofs += TLV_HDR_LEN
        data = payload[ofs : ofs + (tlv_len - TLV_HDR_LEN)]
        ofs += len(data)

        if tlv_type == TLV_DETECTED_POINTS:
            out["points"] = parse_detected_points(data)
        elif tlv_type == TLV_SIDE_INFO:
            out["side_info"] = parse_side_info(data)
        # Add more TLV parsers here as needed (e.g., tracked objects)
    return out

def main():
    # Human status → STDERR (keeps STDOUT clean for NDJSON)
    print(f"[INFO] Opening ports: CLI={CLI_PORT} ({CLI_BAUD})  DATA={DATA_PORT} ({DATA_BAUD})",
          file=sys.stderr)
    cli, data = open_ports()
    try:
        # 1) Send configuration
        send_cfg(cli, CFG_FILE)

        # 2) Ensure CFAR is set per your firmware (dB + peakGroupingEn)
        apply_cfar(cli)

        # 3) Start the sensor
        send_cmd(cli, "sensorStart")

        print("[INFO] Reading frames... (Ctrl+C to stop)", file=sys.stderr)
        buf = bytearray()

        # 4) Main read/parse/emit loop
        while True:
            header, payload = get_packet(buf, data)
            parsed = parse_tlvs(payload, header["numTLVs"])
            pts = parsed["points"]

            # ---- NDJSON frame to STDOUT (for AI) ----
            frame_obj = {
                "ts": time.time(),  # producer timestamp
                "frame": int(header["frameNumber"]),
                "num_points": len(pts),
                "points": [{"x": float(x), "y": float(y), "z": float(z), "v": float(v)} for (x,y,z,v) in pts]
            }
            print(json.dumps(frame_obj), flush=True)

            # ---- minimal human log to STDERR ----
            print(f"[FRAME {header['frameNumber']}] points={len(pts)} "
                  f"(numDetectedObj={header['numDetectedObj']})",
                  file=sys.stderr, flush=True)

    except KeyboardInterrupt:
        print("\n[INFO] Stopping (Ctrl+C).", file=sys.stderr)
    finally:
        # Stop sensor on exit, then close ports
        try:
            send_cmd(cli, "sensorStop")
        except Exception:
            pass
        cli.close(); data.close()
        print("[INFO] Ports closed.", file=sys.stderr)

if __name__ == "__main__":
    main()
