# RADIAN Radar — AWR6843ISK → UART → Point Cloud (NDJSON)

This repo has:
- `indoor_fall_detection.cfg` — configures the AWR6843ISK for indoor people tracking.
- `mmwave_run.py` — sends the cfg, reads UART TLVs, and outputs **one JSON object per frame** (NDJSON) on stdout.

> Device echoes + short logs go to **stderr** so stdout stays machine-readable.

---

## Quick start (Windows)
1. `pip install -r requirements.txt`
2. Set ports at the top of `mmwave_run.py`:
   ```python
   CLI_PORT = "COM5"
   DATA_PORT = "COM6"
   CFG_FILE  = "indoor_fall_detection.cfg"
3. Run `python mmwave_run.py`:
    You should see:
    {"ts": 1739055600.12, "frame": 1, "num_points": 23, "points":[{"x":0.23,"y":1.01,"z":0.40,"v":-0.08}]}

## Quick start (Raspberry Pi 3)
1. ```bash
    sudo apt-get update
    sudo apt-get install -y python3-pip
    python3 -m pip install -r requirements.txt
    sudo usermod -a -G dialout $USER   # re-log or reboot so serial perms apply
2. Edit ports in `mmwave_run.py`:
    ```python
    CLI_PORT = "/dev/ttyACM0"
    DATA_PORT = "/dev/ttyACM1"
3. Run:
    ```bash
    python3 mmwave_run.py

## Output format (NDJSON)
1. One JSON object per frame:
    ```json
    {
        "ts": 1739055600.123,
        "frame": 42,
        "num_points": 37,
        "points": [
            {"x": 0.24, "y": 1.02, "z": 0.41, "v": -0.10}
        ]
    }
2. Units: 
    meters (x,y,z)
    m/s (v)
    Rate: ~10 Hz with the provided cfg

## Configuration Notes
1. Point-cloud only (no heatmaps):
    ```nginx
    guiMonitor -1 1 1 1 0 0 1
2. CFAR required by firmware (dB + peak grouping) --> already in the cfg file:
    ```nginx
    cfarCfg -1 0 2 8 4 3 0 20 1
    cfarCfg -1 1 2 4 4 3 0 20 1
3. For minimal UART (points + stats only), set:
    ```nginx
    guiMonitor -1 1 0 0 0 0 1

## Troubleshooting
1. `sensorStart` fails --> confirm both cfarCfg lines show `Done`
2. Port busy / cannot open --> close other serial apps; verify COM or `/dev/ttyACM*`
3. Garbled / no frames --> CLI/DATA swapped; flip the two port strings
4. Always 0 points --> move in FOV; try 15 dB for more sensitivity:
    ```nginx
    cfarCfg -1 0 2 8 4 3 0 15 1
    cfarCfg -1 1 2 4 4 3 0 15 1





