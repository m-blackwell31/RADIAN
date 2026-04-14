"""
fall_detector_rules.py
======================
Rule-based fall detector tuned to RADIAN radar data.

How it works
------------
Watches a short rolling buffer of frames and fires when ALL of these are true:

  1. V-SPIKE   — peak velocity in recent frames exceeds threshold
                 (pre-fall = ~0.04 m/s, fall = 0.15-0.57 m/s)
  2. NPTS-JUMP — average point count jumps above threshold
                 (pre-fall = ~5 pts, fall = ~10 pts)
  3. SUSTAINED — both conditions hold for at least N consecutive frames
                 (avoids single-frame noise spikes)

Usage
-----
    python3 fall_detector_rules.py \\
        --parser    mmwave_run6.py \\
        --cli-port  /dev/ttyUSB0 \\
        --data-port /dev/ttyUSB1 \\
        --cfg-file  config3.cfg \\
        --verbose
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

# ── GPIO buzzer ───────────────────────────────────────────────────────────────
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
# Per-frame helpers
# ═══════════════════════════════════════════════════════════════════════════════

def frame_vpeak(frame):
    pts = frame.get("points_filt", []) or []
    if not pts:
        return 0.0
    return float(max(abs(p["v"]) for p in pts))

def frame_npts(frame):
    return float(len(frame.get("points_filt", []) or []))


# ═══════════════════════════════════════════════════════════════════════════════
# Rule engine
# ═══════════════════════════════════════════════════════════════════════════════

class FallRuleEngine:
    """
    Watches a short rolling buffer and detects falls using:
      - v_spike_thresh  : peak velocity must exceed this (default 0.15 m/s)
      - npts_thresh     : avg point count must exceed this (default 7)
      - sustain_frames  : conditions must hold for this many frames (default 2)
      - cooldown        : seconds between alerts
    """

    def __init__(self, args):
        self.v_thresh    = args.v_spike
        self.npts_thresh = args.npts
        self.sustain     = args.sustain
        self.cooldown    = args.cooldown
        self._buffer     = collections.deque(maxlen=args.buffer)
        self._consec     = 0
        self._last_alert = 0.0

    def update(self, frame):
        self._buffer.append(frame)

    def check(self):
        if len(self._buffer) < 3:
            return False, 0.0, ""

        buf = list(self._buffer)
        vpeaks = [frame_vpeak(f) for f in buf]
        npts   = [frame_npts(f)  for f in buf]

        # Use recent window (last 5 frames) for spike detection
        recent = min(5, len(buf))
        v_recent    = max(vpeaks[-recent:])
        npts_recent = float(np.mean(npts[-recent:]))

        v_ok    = v_recent    >= self.v_thresh
        npts_ok = npts_recent >= self.npts_thresh

        score = min(1.0, (v_recent / self.v_thresh) * 0.6 +
                         (npts_recent / self.npts_thresh) * 0.4)

        if v_ok and npts_ok:
            self._consec += 1
        else:
            self._consec = 0

        reason = (
            f"v_peak={v_recent:.3f}({'✓' if v_ok else '✗'})  "
            f"npts={npts_recent:.1f}({'✓' if npts_ok else '✗'})  "
            f"consec={self._consec}  score={score:.2f}"
        )

        detected = (self._consec >= self.sustain)
        now = time.time()
        if detected and (now - self._last_alert) < self.cooldown:
            detected = False  # still in cooldown

        if detected:
            self._last_alert = now
            self._consec = 0  # reset after alert

        return detected, score, reason


# ═══════════════════════════════════════════════════════════════════════════════
# Alert helpers
# ═══════════════════════════════════════════════════════════════════════════════

def send_gotify(url, token, score, ts):
    if not HAS_REQUESTS:
        return
    try:
        requests.post(
            f"{url.rstrip('/')}/message",
            params={"token": token},
            json={
                "title"   : "⚠️ Fall Detected",
                "message" : f"Fall detected (score {score:.0%}) at {ts}",
                "priority": 8,
            },
            timeout=5,
        )
    except Exception as e:
        log.error(f"Gotify alert failed: {e}")


def buzz_fall():
    if not HAS_GPIO:
        return
    def _b():
        for _ in range(3):
            GPIO.output(27, GPIO.HIGH); time.sleep(0.3)
            GPIO.output(27, GPIO.LOW);  time.sleep(0.2)
    threading.Thread(target=_b, daemon=True).start()


def buzz_ready():
    if not HAS_GPIO:
        return
    def _b():
        for _ in range(2):
            GPIO.output(27, GPIO.HIGH); time.sleep(0.12)
            GPIO.output(27, GPIO.LOW);  time.sleep(0.10)
    threading.Thread(target=_b, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# CSV logger
# ═══════════════════════════════════════════════════════════════════════════════

class FallLogger:
    def __init__(self, path):
        self.path = path
        if not os.path.exists(path):
            with open(path, "w", newline="") as f:
                csv.writer(f).writerow(["timestamp", "detected", "score", "reason", "alert_sent"])

    def write(self, ts, detected, score, reason, alerted):
        with open(self.path, "a", newline="") as f:
            csv.writer(f).writerow([ts, int(detected), f"{score:.4f}", reason, int(alerted)])


# ═══════════════════════════════════════════════════════════════════════════════
# Main detector
# ═══════════════════════════════════════════════════════════════════════════════

class RuleDetector:
    def __init__(self, args):
        self.args         = args
        self.engine       = FallRuleEngine(args)
        self.logger       = FallLogger(args.log)
        self._frame_count = 0
        self._running     = False
        self._lock        = threading.Lock()
        self._proc        = None
        self.stats        = {
            "frames": 0, "checks": 0,
            "falls": 0, "alerts": 0, "parse_errors": 0,
        }

    def _reader_thread(self):
        parser_dir = os.path.dirname(os.path.abspath(self.args.parser))
        parser_abs = os.path.abspath(self.args.parser)
        cmd = [sys.executable, parser_abs]
        log.info(f"Starting parser: {self.args.parser}")
        log.info(f"  CLI  port : {self.args.cli_port}")
        log.info(f"  Data port : {self.args.data_port}")
        log.info(f"  Config    : {self.args.cfg_file}")
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, cwd=parser_dir,
                env={**os.environ, "PYTHONPATH": parser_dir},
            )
            self._proc = proc

            def _fwd():
                for line in proc.stderr:
                    line = line.rstrip()
                    if line: log.debug(f"[parser] {line}")
            threading.Thread(target=_fwd, daemon=True).start()

            for raw in proc.stdout:
                if not self._running: break
                raw = raw.strip()
                if not raw: continue
                try:
                    frame = json.loads(raw)
                except json.JSONDecodeError:
                    self.stats["parse_errors"] += 1
                    continue
                with self._lock:
                    self.engine.update(frame)
                self._frame_count += 1
                self.stats["frames"] += 1

            proc.wait()
            if proc.returncode:
                log.error(f"Parser exited with code {proc.returncode}")
        except Exception as e:
            log.error(f"Reader thread error: {e}")
        finally:
            self._running = False

    def run(self):
        self._running = True
        log.info(
            f"Rule detector starting — "
            f"v_spike={self.args.v_spike}m/s  "
            f"npts={self.args.npts}  "
            f"sustain={self.args.sustain}  "
            f"cooldown={self.args.cooldown}s"
        )

        reader = threading.Thread(target=self._reader_thread, daemon=True)
        reader.start()

        # Background scan
        bg_frames = self.args.bg_frames
        if bg_frames > 0:
            log.info(f"Background scan — stand CLEAR for ~{bg_frames // 10}s…")
            while self._frame_count < bg_frames and self._running:
                time.sleep(0.05)
            log.info("Background scan complete")

        # Warmup
        warmup = self.args.warmup
        log.info(f"Warmup — {warmup} frames…")
        while self._frame_count < bg_frames + warmup and self._running:
            time.sleep(0.05)
        log.info("Warmup complete — detection active")
        buzz_ready()
        if self.args.gotify_url and self.args.gotify_token:
            try:
                requests.post(
                    f"{self.args.gotify_url.rstrip('/')}/message",
                    params={"token": self.args.gotify_token},
                    json={"title": "✅ RADIAN Online",
                          "message": "Fall detection active.",
                          "priority": 4},
                    timeout=5,
                )
            except Exception: pass

        last_check = 0
        try:
            while self._running:
                current = self._frame_count
                if current - last_check >= 2:
                    last_check = current
                    with self._lock:
                        detected, score, reason = self.engine.check()
                    self.stats["checks"] += 1
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    alerted = False
                    if detected:
                        self.stats["falls"] += 1
                        self.stats["alerts"] += 1
                        alerted = True
                        log.warning(f"🚨 FALL DETECTED  score={score:.2f}  time={ts}")
                        buzz_fall()
                        if self.args.gotify_url and self.args.gotify_token:
                            send_gotify(self.args.gotify_url, self.args.gotify_token, score, ts)

                    self.logger.write(ts, detected, score, reason, alerted)

                    if self.args.verbose:
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
                except Exception: pass
            log.info(
                f"Session — frames={self.stats['frames']}  "
                f"checks={self.stats['checks']}  "
                f"falls={self.stats['falls']}  "
                f"alerts={self.stats['alerts']}  "
                f"parse_errors={self.stats['parse_errors']}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args():
    p = argparse.ArgumentParser(description="Rule-based fall detector for RADIAN")
    p.add_argument("--parser",       required=True)
    p.add_argument("--cli-port",     default="/dev/ttyUSB0")
    p.add_argument("--data-port",    default="/dev/ttyUSB1")
    p.add_argument("--cfg-file",     default="config3.cfg")
    p.add_argument("--gotify-url",   default=None)
    p.add_argument("--gotify-token", default=None)
    p.add_argument("--log",          default="fall_log_rules.csv")
    p.add_argument("--verbose",      action="store_true")

    # Tuning
    p.add_argument("--v-spike",  default=0.15, type=float,
                   help="Min peak velocity (m/s) to trigger  [default: 0.15]")
    p.add_argument("--npts",     default=7,    type=int,
                   help="Min avg points in recent frames     [default: 7]")
    p.add_argument("--sustain",  default=2,    type=int,
                   help="Consecutive detections before alert [default: 2]")
    p.add_argument("--buffer",   default=10,   type=int,
                   help="Rolling frame buffer size           [default: 10]")
    p.add_argument("--cooldown", default=15.0, type=float,
                   help="Seconds between alerts              [default: 15]")
    p.add_argument("--warmup",   default=30,   type=int,
                   help="Frames before detection starts      [default: 30]")
    p.add_argument("--bg-frames",default=50,   type=int,
                   help="Background scan frames (0=disable)  [default: 50]")
    return p.parse_args()


def main():
    args = parse_args()
    if not os.path.exists(args.parser):
        log.error(f"Parser not found: {args.parser}"); sys.exit(1)
    if not os.path.exists(args.cfg_file):
        log.error(f"Config not found: {args.cfg_file}"); sys.exit(1)
    RuleDetector(args).run()


if __name__ == "__main__":
    main()
