# import serial
# import time
# import struct

# CLI_PORT = "/dev/ttyUSB0"
# DATA_PORT = "/dev/ttyUSB1"

# CLI_BAUD = 115200
# DATA_BAUD = 921600

# CFG_FILE = "config3.cfg"

# MAGIC_WORD = b'\x02\x01\x04\x03\x06\x05\x08\x07'
# HEADER_LEN = 40
# TLV_HDR_LEN = 8

# TLV_DETECTED_POINTS = 1


# def send_cfg(cli):
#     with open(CFG_FILE, 'r') as f:
#         for line in f:
#             line = line.strip()
#             if line and not line.startswith('%'):
#                 cli.write((line + '\n').encode())
#                 time.sleep(0.05)


# def read_packet(data_port):
#     buffer = b''

#     while True:
#         buffer += data_port.read(4096)

#         magic_index = buffer.find(MAGIC_WORD)
#         if magic_index == -1:
#             continue

#         if len(buffer) < magic_index + HEADER_LEN:
#             continue

#         header = buffer[magic_index:magic_index + HEADER_LEN]
#         total_packet_len = struct.unpack_from('I', header, 12)[0]

#         if len(buffer) < magic_index + total_packet_len:
#             continue

#         packet = buffer[magic_index:magic_index + total_packet_len]
#         buffer = buffer[magic_index + total_packet_len:]

#         return packet


# def parse_detected_points(tlv_data):
#     points = []
#     rec = 16  # 4 floats per point
#     n_full_points = len(tlv_data) // rec  # only full points

#     for i in range(n_full_points):
#         offset = i * rec
#         try:
#             x, y, z, v = struct.unpack_from('<ffff', tlv_data, offset)
#             points.append((x, y, z, v))
#         except struct.error:
#             # If somehow a point is incomplete, just stop parsing
#             break

#     return points


# def main():
#     print("[INFO] Opening ports...")

#     cli = serial.Serial(CLI_PORT, CLI_BAUD, timeout=1)
#     data = serial.Serial(DATA_PORT, DATA_BAUD, timeout=1)

#     time.sleep(1)

#     send_cfg(cli)
#     cli.write(b'sensorStart\n')

#     print("[INFO] Radar running...\n")

#     try:
#         while True:
#             packet = read_packet(data)

#             num_tlvs = struct.unpack_from('I', packet, 28)[0]
#             offset = HEADER_LEN

#             for _ in range(num_tlvs):
#                 tlv_type, tlv_len = struct.unpack_from('II', packet, offset)
#                 offset += TLV_HDR_LEN

#                 tlv_data = packet[offset:offset + max(0, tlv_len - TLV_HDR_LEN)]

#                 if tlv_type == TLV_DETECTED_POINTS:
#                     points = parse_detected_points(tlv_data)
#                     print(f"Detected {len(points)} objects")
#                     for p in points:
#                         print(f"  x={p[0]:.2f} y={p[1]:.2f} z={p[2]:.2f} v={p[3]:.2f}")

#                 offset += tlv_len - TLV_HDR_LEN

#     except KeyboardInterrupt:
#         print("\n[INFO] Stopping radar...")
#         cli.write(b'sensorStop\n')

#     finally:
#         cli.close()
#         data.close()
#         print("[INFO] Ports closed.")


# if __name__ == "__main__":
#     main()

"""
mmwave_run6_pi.py
-----------------
Simple mmWave parser for Raspberry Pi 3.
Streams detected points to the terminal safely.
Ignores plotting and extra TLVs for simplicity.
"""

import serial
import time
import struct

# ------------------ USER SETTINGS ------------------
CLI_PORT  = "/dev/ttyUSB0"
DATA_PORT = "/dev/ttyUSB1"

CLI_BAUD  = 115200
DATA_BAUD = 921600
CFG_FILE  = "config3.cfg"

MAGIC_WORD   = b'\x02\x01\x04\x03\x06\x05\x08\x07'
HEADER_LEN   = 40
TLV_HDR_LEN  = 8
TLV_DETECTED_POINTS = 1
# ---------------------------------------------------

def send_cfg(cli):
    """Send radar configuration to CLI port"""
    with open(CFG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('%'):
                cli.write((line + '\n').encode())
                time.sleep(0.05)

def read_packet(data_port):
    """Read a single full radar packet safely"""
    buffer = b''

    while True:
        chunk = data_port.read(4096)
        if not chunk:
            continue
        buffer += chunk

        magic_index = buffer.find(MAGIC_WORD)
        if magic_index == -1:
            # No magic word yet, keep buffering
            if len(buffer) > 65536:
                buffer = buffer[-4096:]  # trim old bytes
            continue

        if len(buffer) < magic_index + HEADER_LEN:
            continue  # incomplete header

        header = buffer[magic_index:magic_index + HEADER_LEN]
        total_packet_len = struct.unpack_from('<I', header, 12)[0]

        if total_packet_len < HEADER_LEN or total_packet_len > 65536:
            buffer = buffer[magic_index + 1:]  # skip invalid header
            continue

        if len(buffer) < magic_index + total_packet_len:
            continue  # full packet not yet received

        packet = buffer[magic_index:magic_index + total_packet_len]
        buffer = buffer[magic_index + total_packet_len:]
        return packet

def parse_detected_points(tlv_data):
    """Parse detected points from TLV data safely"""
    points = []
    rec = 16  # 4 floats per point
    n_full_points = len(tlv_data) // rec  # only full points

    for i in range(n_full_points):
        offset = i * rec
        try:
            x, y, z, v = struct.unpack_from('<ffff', tlv_data, offset)
            points.append((x, y, z, v))
        except struct.error:
            break  # stop if point incomplete
    return points

def main():
    print("[INFO] Opening ports...")
    cli = serial.Serial(CLI_PORT, CLI_BAUD, timeout=1)
    data = serial.Serial(DATA_PORT, DATA_BAUD, timeout=1)

    time.sleep(1)

    print("[INFO] Sending configuration...")
    send_cfg(cli)
    cli.write(b'sensorStart\n')

    print("[INFO] Radar running...\n")

    try:
        while True:
            packet = read_packet(data)

            if len(packet) < HEADER_LEN:
                continue  # skip tiny packets

            # Number of TLVs in this frame
            try:
                num_tlvs = struct.unpack_from('<I', packet, 28)[0]
            except struct.error:
                continue

            offset = HEADER_LEN

            for _ in range(num_tlvs):
                if offset + TLV_HDR_LEN > len(packet):
                    break  # malformed TLV

                tlv_type, tlv_len = struct.unpack_from('<II', packet, offset)

                # validate TLV length
                if tlv_len < TLV_HDR_LEN or offset + tlv_len > len(packet):
                    break

                tlv_data = packet[offset + TLV_HDR_LEN: offset + tlv_len]

                if tlv_type == TLV_DETECTED_POINTS:
                    points = parse_detected_points(tlv_data)
                    print(f"Detected {len(points)} objects")
                    for p in points:
                        print(f"  x={p[0]:.2f} y={p[1]:.2f} z={p[2]:.2f} v={p[3]:.2f}")

                offset += tlv_len

    except KeyboardInterrupt:
        print("\n[INFO] Stopping radar...")
        try:
            cli.write(b'sensorStop\n')
        except Exception:
            pass

    finally:
        cli.close()
        data.close()
        print("[INFO] Ports closed.")

if __name__ == "__main__":
    main()
