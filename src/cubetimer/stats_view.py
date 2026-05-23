"""
stats_view.py — full stats screen using pandas for rolling averages
Press s from the main timer to open; any key to return.
"""

import curses

from .common import RECORDS_FILE
from .utils import fmt_time


try:
    import pandas as pd

    _PANDAS = True
except ImportError:
    _PANDAS = False


def _load_df(puzzle_key: str):
    """Load CSV into a DataFrame filtered by puzzle, return None if unavailable."""
    if not _PANDAS or not RECORDS_FILE.exists():
        return None
    df = pd.read_csv(RECORDS_FILE, parse_dates=["timestamp"])
    df = df[df["puzzle"] == puzzle_key].copy()
    if df.empty:
        return None
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["time_s"] = df["time_ms"] / 1000

    def trimmed_avg(series):
        if len(series) < 3:
            return None
        s = sorted(series)
        return sum(s[1:-1]) / (len(s) - 2)

    for n in (5, 12, 50, 100):
        df[f"ao{n}"] = df["time_ms"].rolling(n).apply(trimmed_avg, raw=True)

    return df


def _draw_stats(stdscr, puzzle_key: str, puzzle_label: str) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    curses.curs_set(0)

    def put(row, col, text, attr=0):
        try:
            stdscr.addstr(row, col, text[: w - col], attr)
        except curses.error:
            pass

    def center(row, text, attr=0):
        put(row, max(0, (w - len(text)) // 2), text, attr)

    center(0, f"[ stats — {puzzle_label} ]", curses.A_BOLD)

    if not _PANDAS:
        center(2, "pandas not installed  →  pip install pandas")
        center(h - 1, "any key to return", curses.A_DIM)
        stdscr.refresh()
        return

    df = _load_df(puzzle_key)

    if df is None:
        center(2, "no solves recorded yet for this puzzle")
        center(h - 1, "any key to return", curses.A_DIM)
        stdscr.refresh()
        return

    row = 2

    # Summary line
    best = fmt_time(df["time_ms"].min())
    worst = fmt_time(df["time_ms"].max())
    mean = fmt_time(df["time_ms"].mean())
    count = len(df)
    center(row, f"solves: {count}   best: {best}   worst: {worst}   mean: {mean}")
    row += 2

    # Current rolling averages (last window)
    ao_labels = [(5, "ao5"), (12, "ao12"), (50, "ao50"), (100, "ao100")]
    ao_parts = []
    for n, col in ao_labels:
        val = df[col].dropna().iloc[-1] if not df[col].dropna().empty else None
        if val is not None:
            ao_parts.append(f"{col}: {fmt_time(val)}")
    if ao_parts:
        center(row, "  ".join(ao_parts))
        row += 2

    # Recent solves table
    col_w = min(w - 2, 72)
    left = max(0, (w - col_w) // 2)
    header = f"{'#':>4}  {'time':>8}  {'ao5':>8}  {'ao12':>9}  {'timestamp':<19}"
    put(row, left, header, curses.A_DIM)
    row += 1
    put(row, left, "─" * col_w, curses.A_DIM)
    row += 1

    # Show last N rows that fit on screen
    available_rows = h - row - 2
    tail = df.tail(available_rows)
    for i, (_, r) in enumerate(tail.iterrows()):
        idx = int(r.name) + 1
        t = fmt_time(r["time_ms"])
        ao5 = fmt_time(r["ao5"]) if pd.notna(r["ao5"]) else "—"
        ao12 = fmt_time(r["ao12"]) if pd.notna(r["ao12"]) else "—"
        ts = str(r["timestamp"])[:19]
        line = f"{idx:>4}  {t:>8}  {ao5:>8}  {ao12:>9}  {ts:<19}"
        put(row + i, left, line)

    center(h - 1, "any key to return", curses.A_DIM)
    stdscr.refresh()


def show_stats(stdscr, puzzle_key: str, puzzle_label: str) -> None:
    """Block until any key pressed, drawing the stats screen."""
    _draw_stats(stdscr, puzzle_key, puzzle_label)
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)
    stdscr.timeout(50)
