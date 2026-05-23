"""
training.py — training mode picker
Same scrollable pattern as the puzzle picker.
Returns a TrainingMode or None if cancelled.
"""

import curses

from .common import TRAINING_MODES
from .common import TrainingMode


def select_training(stdscr, current_key: str | None) -> TrainingMode | str | None:
    """
    Full-screen training mode picker.
    Returns chosen TrainingMode, or None if ESC pressed (clears training mode).
    """
    curses.curs_set(0)
    # "no training" is index 0, actual modes start at 1
    items: list[TrainingMode | None] = [None] + list(TRAINING_MODES)
    idx = 0
    if current_key:
        match = next((i for i, t in enumerate(items) if t and t.key == current_key), 0)
        idx = match

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        def center(row, text, attr=0):
            try:
                stdscr.addstr(row, max(0, (w - len(text)) // 2), text[:w], attr)
            except curses.error:
                pass

        center(0, "[ training mode ]", curses.A_BOLD)

        visible = h - 4
        start = max(0, idx - visible // 2)
        end = min(len(items), start + visible)
        start = max(0, end - visible)

        for i, item in enumerate(items[start:end]):
            selected = (start + i) == idx
            label = item.label if item else "— no training (full solve) —"
            if selected:
                label = "> " + label
            center(2 + i, label, curses.A_REVERSE if selected else 0)

        center(h - 1, "↑↓ / jk  navigate   ENTER  confirm   ESC  cancel", curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")) and idx > 0:
            idx -= 1
        elif key in (curses.KEY_DOWN, ord("j")) and idx < len(items) - 1:
            idx += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            return items[idx]
        elif key == 27:  # ESC — cancel without changing
            return "cancel"
