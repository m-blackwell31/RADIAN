"""
fall_detector_rules.py
======================
Rule-based fall detector for Raspberry Pi 3B+.
No ML model required — uses physics-based rules on the radar point cloud.

How it works
------------
Every frame the radar outputs a point cloud. We keep a short rolling buffer
and look for the classic fall signature:

  1. Z-DROP   — the mean z height drops sharply (person falls to floor)
  2. V-SPIKE  — peak velocity spikes at the same time (fast movement)
  3. STAY-LOW — z stays low for several frames after (person on floor)

All three must fire together before an alert is sent.

Usage
-----
    python3 fall_detector_rules.py \\
        --parser    mmwave_run6.py \\
        --cli-port  /dev/ttyUSB0 \\
        --data-port /dev/ttyUSB1 \\
        --cfg-file  config3.cfg \\
        --gotify-url  http://YOUR_SERVER:PORT \\
        --gotify-token YOUR_APP_TOKEN \\
        --verbose

Tuning
------
  --z-drop       Minimum z drop in metres to trigger          [default: 0.6]
  --v-spike      Minimum peak velocity (m/s) during drop      [default: 0.25]
  --stay-low     Frames z must stay low after drop            [default: 4]
  --buffer       Rolling buffer size in frames                [default: 20]
  --warmup       Frames before detection starts               [default: 48]
  --cooldown     Seconds between alerts                       [default: 15]
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

import numpy as np

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── optional GPIO buzzer ──────────────────────────────────────────────────────
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(27, GPIO.OUT)
    GPIO.output(27, GPIO.LOW)
    HAS_GPIO = True
except Exception:
    HAS_GPIO = False

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("fall_rules")


# ═══════════════════════════════════════════════════════════════════════════════
# Rule engine
# ═══════════════════════════════════════════════════════════════════════════════

def _frame_zmean(frame: dict) -> float:
    """Mean z of all filtered points in a frame, or None if empty."""
    pts = frame.get("points_filt", []) or []
    if not pts:
        return None
    return float(np.mean([p["z"] for p in pts]))

def _frame_vpeak(frame: dict) -> float:
    """Peak absolute velocity in a frame, or 0 if empty."""
    pts = frame.get("points_filt", []) or []
    if not pts:
        return 0.0
    return float(max(abs(p["v"]) for p in pts))

def _smooth_z(buffer: list) -> list:
    """Return list of smoothed z means from the buffer (None → carry forward)."""
    zs = []
    last = 0.0
    for frame in buffer:
        z = _frame_zmean(frame)
        if z is None:
            zs.append(last)
        else:
            last = z
            zs.append(z)
    return zs

def check_fall(buffer: list, args) -> tuple:
    """
    Apply fall detection rules to the rolling buffer.

    Returns (detected: bool, score: float, reason: str)
    score is 0.0-1.0 (how strongly the rules fired)
    """
    if len(buffer) < args.buffer:
        return False, 0.0, "buffer not full"

    zs = _smooth_z(buffer)
    vs = [_frame_vpeak(f) for f in buffer]

    z_arr = np.array(zs)
    v_arr = np.array(vs)

    # ── Rule 1: Z-DROP ────────────────────────────────────────────────────────
    # Find the biggest drop between any two points in the buffer
    # We look at the first half vs the second half to enforce temporal order
    mid = len(z_arr) // 2
    z_start = float(z_arr[:mid].mean())
    z_end   = float(z_arr[mid:].mean())
    z_drop  = z_start - z_end          # positive = dropped

    # ── Rule 2: V-SPIKE ──────────────────────────────────────────────────────
    # Peak velocity anywhere in the buffer
    v_peak = float(v_arr.max())

    # ── Rule 3: STAY-LOW ─────────────────────────────────────────────────────
    # Last N frames should be below the pre-fall z level
    stay_low_frames = int(args.stay_low)
    if len(z_arr) >= stay_low_frames:
        z_tail = z_arr[-stay_low_frames:]
        stay_low = bool(z_tail.mean() < z_start - args.z_drop * 0.5)
    else:
        stay_low = False

    # ── Scoring ───────────────────────────────────────────────────────────────
    drop_score  = min(1.0, max(0.0, z_drop  / args.z_drop))
    spike_score = min(1.0, max(0.0, v_peak  / args.v_spike))
    low_score   = 1.0 if stay_low else 0.0

    score = (drop_score * 0.5 + spike_score * 0.3 + low_score * 0.2)

    drop_ok  = z_drop  >= args.z_drop
    spike_ok = v_peak  >= args.v_spike
    low_ok   = stay_low

    detected = drop_ok and spike_ok and low_ok

    reason = (
        f"z_drop={z_drop:.2f}({'✓' if drop_ok else '✗'})  "
        f"v_peak={v_peak:.2f}({'✓' if spike_ok else '✗'})  "
        f"stay_low={'✓' if low_ok else '✗'}  "
        f"score={score:.2f}"
    )

    return detected, score, reason


# ═══════════════════════════════════════════════════════════════════════════════
# Alert helpers
# ═══════════════════════════════════════════════════════════════════════════════

def send_gotify_alert(url: str, token: str, score: float, ts: str):
    if not HAS_REQUESTS:
        return
    try:
        resp = requests.post(
            f"{url.rstrip('/')}/message",
            params={"token": token},
            json={
                "title"   : "⚠️ Fall Detected",
                "message" : f"Fall detected (score {score:.0%}) at {ts}",
                "priority": 8,
            },
            timeout=5,
        )
        if resp.status_code != 200:
            log.error(f"Gotify HTTP {resp.status_code}")
    except Exception as e:
        log.error(f"Gotify alert failed: {e}")


def buzz():
    if not HAS_GPIO:
        return
    def _buzz():
        for _ in range(3):
            GPIO.output(27, GPIO.HIGH)
            time.sleep(0.3)
            GPIO.output(27, GPIO.LOW)
            time.sleep(0.2)
    threading.Thread(target=_buzz, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# CSV logger
# ═══════════════════════════════════════════════════════════════════════════════

class FallLogger:
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            with open(path, "w", newline="") as f:
                csv.writer(f).writerow(
                    ["timestamp", "detected", "score", "reason", "alert_sent"]
                )

    def write(self, ts, detected, score, reason, alerted):
        with open(self.path, "a", newline="") as f:
            csv.writer(f).writerow([ts, int(detected), f"{score:.4f}", reason, int(alerted)])


# ═══════════════════════════════════════════════════════════════════════════════
# Main detector
# ═══════════════════════════════════════════════════════════════════════════════

class RuleDetector:
    def __init__(self, args):
        self.args        = args
        self.buffer      = collections.deque(maxlen=args.buffer)
        self.logger      = FallLogger(args.log)
        self._frame_count = 0
        self._last_alert  = 0.0
        self._running     = False
        self._lock        = threading.Lock()
        self._proc        = None
        self._consecutive = 0

        self.stats = {
            "frames": 0, "checks": 0,
            "falls_flagged": 0, "alerts_sent": 0,
            "parse_errors": 0,
        }

    def _reader_thread(self):
        parser_dir = os.path.dirname(os.path.abspath(self.args.parser))
        patch = (
            f"import mmwave_run6 as m; "
            f"m.CLI_PORT='{self.args.cli_port}'; "
            f"m.DATA_PORT='{self.args.data_port}'; "
            f"m.CFG_FILE='{self.args.cfg_file}'; "
            f"m.main()"
        )
        cmd = [sys.executable, "-c", patch]

        log.info(f"Starting parser: {self.args.parser}")
        log.info(f"  CLI  port : {self.args.cli_port}")
        log.info(f"  Data port : {self.args.data_port}")
        log.info(f"  Config    : {self.args.cfg_file}")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=parser_dir,
                env={**os.environ, "PYTHONPATH": parser_dir},
            )
            self._proc = proc

            def _fwd_stderr():
                for line in proc.stderr:
                    line = line.rstrip()
                    if line:
                        log.debug(f"[parser] {line}")
            threading.Thread(target=_fwd_stderr, daemon=True).start()

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
                    continue

                with self._lock:
                    self.buffer.append(frame)
                self._frame_count += 1
                self.stats["frames"] += 1

            proc.wait()
        except Exception as e:
            log.error(f"Reader thread error: {e}")
        finally:
            self._running = False

    def _maybe_alert(self, score: float, ts: str) -> bool:
        now = time.time()
        if now - self._last_alert < self.args.cooldown:
            return False
        self._last_alert = now
        log.warning(f"🚨 FALL DETECTED  score={score:.2f}  time={ts}")
        buzz()
        if self.args.gotify_url and self.args.gotify_token:
            send_gotify_alert(self.args.gotify_url, self.args.gotify_token, score, ts)
        self.stats["alerts_sent"] += 1
        return True

    def run(self):
        self._running = True
        log.info(
            f"Rule detector starting — "
            f"buffer={self.args.buffer} frames  "
            f"z_drop={self.args.z_drop}m  "
            f"v_spike={self.args.v_spike}m/s  "
            f"stay_low={self.args.stay_low} frames  "
            f"cooldown={self.args.cooldown}s"
        )

        reader = threading.Thread(target=self._reader_thread, daemon=True)
        reader.start()

        warmup_done = False
        last_check_at = 0

        try:
            while self._running:
                current = self._frame_count

                # Warmup
                if not warmup_done:
                    if current >= self.args.warmup:
                        warmup_done = True
                        log.info(f"Warmup complete ({self.args.warmup} frames) — detection active")
                    else:
                        time.sleep(0.05)
                        continue

                # Check every 3 new frames
                if current - last_check_at >= 3:
                    last_check_at = current

                    with self._lock:
                        buf_snap = list(self.buffer)

                    detected, score, reason = check_fall(buf_snap, self.args)
                    self.stats["checks"] += 1
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    if detected:
                        self._consecutive += 1
                    else:
                        self._consecutive = 0

                    alerted = False
                    confirm = getattr(self.args, "confirm", 2)
                    if detected and self._consecutive >= confirm:
                        self.stats["falls_flagged"] += 1
                        alerted = self._maybe_alert(score, ts)

                    self.logger.write(ts, detected, score, reason, alerted)

                    if self.args.verbose or alerted:
                        tag = "FALL ⚠️ " if detected else "ok    "
                        log.info(f"{tag} {reason}  frames={self.stats['frames']}")
                else:
                    time.sleep(0.01)

        except KeyboardInterrupt:
            log.info("Shutting down…")
        finally:
            self._running = False
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
            if HAS_GPIO:
                try:
                    GPIO.output(27, GPIO.LOW)
                    GPIO.cleanup()
                except Exception:
                    pass
            log.info(
                f"Session summary — "
                f"frames={self.stats['frames']}  "
                f"checks={self.stats['checks']}  "
                f"falls={self.stats['falls_flagged']}  "
                f"alerts={self.stats['alerts_sent']}  "
                f"parse_errors={self.stats['parse_errors']}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args():
    p = argparse.ArgumentParser(
        description="Rule-based fall detector — no ML model required"
    )
    p.add_argument("--parser",       required=True,
                   help="Path to mmwave_run6.py")
    p.add_argument("--cli-port",     default="/dev/ttyUSB0")
    p.add_argument("--data-port",    default="/dev/ttyUSB1")
    p.add_argument("--cfg-file",     default="config3.cfg")
    p.add_argument("--gotify-url",   default=None)
    p.add_argument("--gotify-token", default=None)
    p.add_argument("--log",          default="fall_log_rules.csv")
    p.add_argument("--verbose",      action="store_true",
                   help="Print every check result")

    # Detection tuning
    p.add_argument("--z-drop",    default=0.6,  type=float,
                   help="Min z drop in metres to trigger            [default: 0.6]")
    p.add_argument("--v-spike",   default=0.25, type=float,
                   help="Min peak velocity m/s during drop          [default: 0.25]")
    p.add_argument("--stay-low",  default=4,    type=int,
                   help="Frames z must stay low after drop          [default: 4]")
    p.add_argument("--buffer",    default=20,   type=int,
                   help="Rolling buffer size in frames              [default: 20]")
    p.add_argument("--warmup",    default=48,   type=int,
                   help="Frames before detection starts             [default: 48]")
    p.add_argument("--cooldown",  default=15.0, type=float,
                   help="Seconds between alerts                     [default: 15]")
    p.add_argument("--confirm",   default=2,    type=int,
                   help="Consecutive detections before alert        [default: 2]")
    return p.parse_args()


def main():
    args = parse_args()
    if not os.path.exists(args.parser):
        log.error(f"Parser not found: {args.parser}")
        sys.exit(1)
    if not os.path.exists(args.cfg_file):
        log.error(f"Config file not found: {args.cfg_file}")
        sys.exit(1)
    if args.gotify_url and not args.gotify_token:
        log.warning("--gotify-url set but --gotify-token missing — alerts will not send")
    RuleDetector(args).run()


if __name__ == "__main__":
    main()
