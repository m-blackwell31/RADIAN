"""
debug_dashboard.py
==================
Terminal debug dashboard for the RADIAN fall detector.
Uses Python's built-in curses — no extra dependencies.

Activated by passing --debug to fall_detector_v2.py.
Press 'q' to quit, 'c' to clear history.

Layout (fits in a standard 80×24 terminal, scales up with larger windows)
--------------------------------------------------------------------------
┌─────────────────────────────────────────────────────────────┐
│  RADIAN DEBUG  │  frames: 142  │  inferences: 18  │  HH:MM:SS │
├──────────────────────────┬──────────────────────────────────┤
│  POINT CLOUD  (top view) │  Z HEIGHT OVER TIME               │
│  x/y scatter, z as char  │  last WINDOW frames               │
│                          │                                   │
├──────────────────────────┼───────────────────────────────────┤
│  VELOCITY OVER TIME      │  PROBABILITY                      │
│  last WINDOW frames      │  bar + numeric + FALL/ok badge    │
└──────────────────────────┴───────────────────────────────────┘
"""

import collections
import curses
import math
import threading
import time
from datetime import datetime


# ── tunables ──────────────────────────────────────────────────────────────────
HISTORY   = 64    # frames kept for time-series plots
REFRESH   = 0.12  # seconds between screen redraws (~8fps, easy on Pi CPU)


# ── shared state written by detector, read by dashboard ───────────────────────

class DebugState:
    """Thread-safe store updated by FallDetector, consumed by Dashboard."""

    def __init__(self, window_size: int):
        self._lock       = threading.Lock()
        self.window_size = window_size

        # Rolling histories
        self.z_history    = collections.deque(maxlen=HISTORY)
        self.v_history    = collections.deque(maxlen=HISTORY)
        self.prob_history = collections.deque(maxlen=HISTORY)

        # Latest frame
        self.latest_pts   = []   # list of {x,y,z,v}
        self.latest_prob  = 0.0
        self.latest_pred  = 0
        self.latest_npts  = 0

        # Counters (mirrors FallDetector.stats)
        self.frames      = 0
        self.inferences  = 0
        self.alerts      = 0
        self.falls       = 0
        self.last_fall_ts = ""

    def update_frame(self, frame: dict):
        pts = frame.get("points_filt", []) or []
        if pts:
            import numpy as np
            z_mean = float(sum(p["z"] for p in pts) / len(pts))
            v_mean = float(sum(abs(p["v"]) for p in pts) / len(pts))
        else:
            z_mean = 0.0
            v_mean = 0.0

        with self._lock:
            self.z_history.append(z_mean)
            self.v_history.append(v_mean)
            self.latest_pts  = pts
            self.latest_npts = len(pts)
            self.frames     += 1

    def update_inference(self, prob: float, pred: int, alerted: bool):
        with self._lock:
            self.prob_history.append(prob)
            self.latest_prob = prob
            self.latest_pred = pred
            self.inferences += 1
            if pred:
                self.falls += 1
                self.last_fall_ts = datetime.now().strftime("%H:%M:%S")
            if alerted:
                self.alerts += 1

    def snapshot(self):
        with self._lock:
            return {
                "z"        : list(self.z_history),
                "v"        : list(self.v_history),
                "prob"     : list(self.prob_history),
                "pts"      : list(self.latest_pts),
                "npts"     : self.latest_npts,
                "cur_prob" : self.latest_prob,
                "cur_pred" : self.latest_pred,
                "frames"   : self.frames,
                "inferences": self.inferences,
                "alerts"   : self.alerts,
                "falls"    : self.falls,
                "fall_ts"  : self.last_fall_ts,
            }

    def clear_history(self):
        with self._lock:
            self.z_history.clear()
            self.v_history.clear()
            self.prob_history.clear()


# ── drawing helpers ───────────────────────────────────────────────────────────

def _sparkline(values, width, lo=None, hi=None):
    """Return a sparkline string of given width from a list of floats."""
    CHARS = " ▁▂▃▄▅▆▇█"
    if not values:
        return " " * width
    lo = lo if lo is not None else min(values)
    hi = hi if hi is not None else max(values)
    span = hi - lo if hi != lo else 1.0
    # Downsample or pad to width
    n = len(values)
    result = []
    for i in range(width):
        idx = int(i * n / width)
        idx = min(idx, n - 1)
        norm = (values[idx] - lo) / span
        ci   = int(norm * (len(CHARS) - 1))
        ci   = max(0, min(len(CHARS) - 1, ci))
        result.append(CHARS[ci])
    return "".join(result)


def _bar(value, width, lo=0.0, hi=1.0):
    """Horizontal filled bar."""
    norm  = max(0.0, min(1.0, (value - lo) / max(hi - lo, 1e-9)))
    filled = int(norm * width)
    return "█" * filled + "░" * (width - filled)


def _scatter_topview(pts, cols, rows):
    """
    Project points onto x/y plane (top-down view).
    Returns a list of `rows` strings each `cols` chars wide.
    Char brightness encodes z height: high=● mid=· low=,
    """
    grid = [[" "] * cols for _ in range(rows)]

    if not pts:
        # Draw axes
        mid_r = rows // 2
        mid_c = cols // 2
        for c in range(cols): grid[mid_r][c] = "─"
        for r in range(rows): grid[r][mid_c] = "│"
        grid[mid_r][mid_c] = "┼"
        return ["".join(row) for row in grid]

    xs = [p["x"] for p in pts]
    ys = [p["y"] for p in pts]
    zs = [p["z"] for p in pts]

    x_lo, x_hi = min(xs) - 0.1, max(xs) + 0.1
    y_lo, y_hi = min(ys) - 0.1, max(ys) + 0.1
    x_span = x_hi - x_lo or 1.0
    y_span = y_hi - y_lo or 1.0
    z_lo   = min(zs); z_hi = max(zs); z_span = z_hi - z_lo or 1.0

    for p in pts:
        c = int((p["x"] - x_lo) / x_span * (cols - 1))
        r = int((1 - (p["y"] - y_lo) / y_span) * (rows - 1))
        c = max(0, min(cols - 1, c))
        r = max(0, min(rows - 1, r))
        z_norm = (p["z"] - z_lo) / z_span
        ch = "●" if z_norm > 0.66 else ("·" if z_norm > 0.33 else ",")
        grid[r][c] = ch

    # Axis labels
    mid_r = rows // 2
    mid_c = cols // 2
    if grid[mid_r][mid_c] == " ": grid[mid_r][mid_c] = "─"
    if grid[0][mid_c]    == " ": grid[0][mid_c]    = "▲"
    if grid[rows-1][mid_c] == " ": grid[rows-1][mid_c] = "▼"

    return ["".join(row) for row in grid]


def _time_series(values, cols, rows, lo=None, hi=None, unit=""):
    """
    Simple time-series plot.
    Returns list of `rows` strings each `cols` chars wide.
    """
    lines = [[" "] * cols for _ in range(rows)]

    if not values:
        return ["".join(l) for l in lines]

    lo = lo if lo is not None else min(values)
    hi = hi if hi is not None else max(values)
    span = hi - lo if hi != lo else 1.0

    n = len(values)
    for ci in range(cols):
        idx   = int(ci * n / max(cols, 1))
        idx   = min(idx, n - 1)
        norm  = (values[idx] - lo) / span
        row_f = (1.0 - norm) * (rows - 1)
        ri    = max(0, min(rows - 1, int(round(row_f))))
        lines[ri][ci] = "●"

    # Y-axis labels (rightmost col)
    if cols > 6:
        top_label = f"{hi:+.2f}"[:cols-1]
        bot_label = f"{lo:+.2f}"[:cols-1]
        for i, ch in enumerate(top_label):
            lines[0][i] = ch
        for i, ch in enumerate(bot_label):
            lines[rows-1][i] = ch

    return ["".join(l) for l in lines]


# ── main dashboard class ──────────────────────────────────────────────────────

class Dashboard:
    def __init__(self, state: DebugState, threshold: float):
        self.state     = state
        self.threshold = threshold
        self._running  = False

    def start(self):
        self._running = True
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def stop(self):
        self._running = False

    def _run(self):
        try:
            curses.wrapper(self._loop)
        except Exception:
            pass  # silently die if terminal too small etc.

    def _loop(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        curses.start_color()
        curses.use_default_colors()

        # Colour pairs
        curses.init_pair(1, curses.COLOR_GREEN,  -1)   # ok
        curses.init_pair(2, curses.COLOR_RED,    -1)   # fall / danger
        curses.init_pair(3, curses.COLOR_CYAN,   -1)   # headers
        curses.init_pair(4, curses.COLOR_YELLOW, -1)   # values
        curses.init_pair(5, curses.COLOR_WHITE,  -1)   # normal
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_RED)    # fall badge

        GREEN  = curses.color_pair(1)
        RED    = curses.color_pair(2)
        CYAN   = curses.color_pair(3)
        YELLOW = curses.color_pair(4)
        NORMAL = curses.color_pair(5)
        BADGE  = curses.color_pair(6)
        BOLD   = curses.A_BOLD

        while self._running:
            key = stdscr.getch()
            if key == ord('q'):
                self._running = False
                break
            if key == ord('c'):
                self.state.clear_history()

            H, W = stdscr.getmaxyx()
            if H < 16 or W < 60:
                stdscr.clear()
                stdscr.addstr(0, 0, "Terminal too small — resize to at least 60×16")
                stdscr.refresh()
                time.sleep(REFRESH)
                continue

            snap = self.state.snapshot()
            stdscr.erase()

            # ── header bar ───────────────────────────────────────────────────
            ts_str = datetime.now().strftime("%H:%M:%S")
            header = (
                f" RADIAN DEBUG  │  frames: {snap['frames']}  │  "
                f"infer: {snap['inferences']}  │  alerts: {snap['alerts']}  │  {ts_str} "
            )
            header = header[:W-1].ljust(W-1)
            try:
                stdscr.addstr(0, 0, header, CYAN | BOLD)
            except curses.error:
                pass

            hint = " q=quit  c=clear "
            try:
                stdscr.addstr(0, W - len(hint) - 1, hint, NORMAL)
            except curses.error:
                pass

            # ── layout calculations ───────────────────────────────────────────
            content_h = H - 2          # rows available below header + above footer
            left_w    = W // 2 - 1
            right_w   = W - left_w - 3
            divider_c = left_w + 1

            top_h     = content_h // 2
            bot_h     = content_h - top_h

            # ── dividers ─────────────────────────────────────────────────────
            for r in range(1, H - 1):
                try: stdscr.addstr(r, divider_c, "│", NORMAL)
                except curses.error: pass
            try: stdscr.addstr(1 + top_h, 0, "─" * divider_c + "┼" + "─" * right_w, NORMAL)
            except curses.error: pass

            # ── panel titles ─────────────────────────────────────────────────
            panels = [
                (1,             0,            " POINT CLOUD (top view) "),
                (1,             divider_c+2,  " Z HEIGHT over time "),
                (1 + top_h + 1, 0,            " VELOCITY over time "),
                (1 + top_h + 1, divider_c+2,  " FALL PROBABILITY "),
            ]
            for (r, c, title) in panels:
                try: stdscr.addstr(r, c, title[:left_w], CYAN | BOLD)
                except curses.error: pass

            inner_top = 2           # first usable row inside a panel
            plot_rows_top = top_h - inner_top
            plot_rows_bot = bot_h - inner_top

            # ── Panel TL: point cloud ─────────────────────────────────────────
            pc_rows = max(1, plot_rows_top)
            pc_cols = max(1, left_w)
            cloud   = _scatter_topview(snap["pts"], pc_cols, pc_rows)
            for i, line in enumerate(cloud[:pc_rows]):
                try: stdscr.addstr(inner_top + i, 0, line[:pc_cols], NORMAL)
                except curses.error: pass

            # npts label
            npts_str = f" pts: {snap['npts']} "
            try: stdscr.addstr(inner_top, left_w - len(npts_str) - 1,
                               npts_str, YELLOW)
            except curses.error: pass

            # ── Panel TR: Z height ────────────────────────────────────────────
            z_vals = snap["z"]
            z_plot = _time_series(z_vals, right_w, max(1, plot_rows_top),
                                  lo=-2.0, hi=2.0)
            for i, line in enumerate(z_plot[:plot_rows_top]):
                try: stdscr.addstr(inner_top + i, divider_c + 2,
                                   line[:right_w], GREEN)
                except curses.error: pass

            if z_vals:
                cur_z = f" z={z_vals[-1]:+.2f}m "
                try: stdscr.addstr(inner_top, divider_c + 2, cur_z, YELLOW | BOLD)
                except curses.error: pass

            # ── Panel BL: velocity ────────────────────────────────────────────
            v_vals  = snap["v"]
            v_plot  = _time_series(v_vals, pc_cols, max(1, plot_rows_bot),
                                   lo=0.0, hi=1.0)
            base_bl = 1 + top_h + inner_top
            for i, line in enumerate(v_plot[:plot_rows_bot]):
                try: stdscr.addstr(base_bl + i, 0, line[:pc_cols], YELLOW)
                except curses.error: pass

            if v_vals:
                cur_v = f" v={v_vals[-1]:.2f}m/s "
                try: stdscr.addstr(base_bl, 0, cur_v, YELLOW | BOLD)
                except curses.error: pass

            # ── Panel BR: probability ─────────────────────────────────────────
            prob      = snap["cur_prob"]
            pred      = snap["cur_pred"]
            base_br   = 1 + top_h + inner_top
            bar_width = max(4, right_w - 8)

            # Big probability number
            prob_str = f" {prob:.1%} "
            color    = (RED | BOLD) if pred else (GREEN | BOLD)
            try: stdscr.addstr(base_br, divider_c + 2, prob_str, color)
            except curses.error: pass

            # FALL / ok badge
            badge     = " ⚠ FALL " if pred else "  ok  "
            badge_col = (BADGE | BOLD) if pred else (GREEN | BOLD)
            try: stdscr.addstr(base_br, divider_c + 2 + len(prob_str) + 1,
                               badge, badge_col)
            except curses.error: pass

            # Threshold marker line
            thresh_str = f" threshold: {self.threshold:.2f} "
            try: stdscr.addstr(base_br + 1, divider_c + 2, thresh_str, NORMAL)
            except curses.error: pass

            # Probability bar
            bar = _bar(prob, bar_width)
            bar_color = RED if pred else GREEN
            try: stdscr.addstr(base_br + 2, divider_c + 2,
                               f"[{bar}]", bar_color)
            except curses.error: pass

            # Mini sparkline history
            prob_spark = _sparkline(snap["prob"], bar_width + 2)
            try: stdscr.addstr(base_br + 3, divider_c + 2,
                               prob_spark[:right_w], NORMAL)
            except curses.error: pass

            # Last fall time
            if snap["fall_ts"]:
                ft = f" last fall: {snap['fall_ts']} "
                try: stdscr.addstr(base_br + 4, divider_c + 2, ft, RED)
                except curses.error: pass

            # Falls / inferences counter
            ratio_str = f" falls: {snap['falls']} / {snap['inferences']} inferences "
            try: stdscr.addstr(base_br + 5, divider_c + 2,
                               ratio_str[:right_w], NORMAL)
            except curses.error: pass

            # ── footer ────────────────────────────────────────────────────────
            footer = (
                f" window: {self.state.window_size} frames  │  "
                f"● high-z  · mid-z  , low-z  │  "
                f"green=z  yellow=v "
            )
            try:
                stdscr.addstr(H - 1, 0, footer[:W-1], CYAN)
            except curses.error:
                pass

            stdscr.refresh()
            time.sleep(REFRESH)
