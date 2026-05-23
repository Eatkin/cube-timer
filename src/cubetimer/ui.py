"""
ui.py — curses TUI: timer loop and puzzle picker
"""

import curses
import time

from .common import DEFAULT_PUZZLE_KEY
from .common import PUZZLE_KEYS
from .common import PUZZLES
from .common import Puzzle
from .common import TrainingMode
from .records import compute_stats
from .records import delete_last_record
from .records import load_records
from .records import save_record
from .stats_view import show_stats
from .training import select_training
from .utils import fmt_time
from .utils import wrap_words


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _active_scramble_fn(puzzle: Puzzle, training: TrainingMode | None):
    return training.scramble_fn if training else puzzle.scramble_fn


def _csv_key(puzzle: Puzzle, training: TrainingMode | None) -> str:
    return f"{puzzle.key}:{training.key}" if training else puzzle.key


def _header(puzzle: Puzzle, training: TrainingMode | None) -> str:
    if training:
        return f"[ cubetimer — {puzzle.label} / {training.label} ]"
    return f"[ cubetimer — {puzzle.label} ]"


# ---------------------------------------------------------------------------
# Puzzle selector (scrollable list)
# ---------------------------------------------------------------------------


def select_puzzle(stdscr, current_key: str) -> str:
    """
    Full-screen puzzle picker. Returns the chosen puzzle key.
    Arrow keys / j/k to navigate, ENTER to confirm, ESC to cancel.
    """
    curses.curs_set(0)
    idx = next((i for i, p in enumerate(PUZZLES) if p.key == current_key), 0)

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        def center(row, text, attr=0):
            try:
                stdscr.addstr(row, max(0, (w - len(text)) // 2), text[:w], attr)
            except curses.error:
                pass

        center(0, "[ select puzzle ]", curses.A_BOLD)

        visible = h - 4
        start = max(0, idx - visible // 2)
        end = min(len(PUZZLES), start + visible)
        start = max(0, end - visible)

        for i, puzzle in enumerate(PUZZLES[start:end]):
            selected_idx = (start + i) == idx
            label = puzzle.label
            if selected_idx:
                label = "> " + label
            center(2 + i, label, curses.A_REVERSE if selected_idx else 0)

        center(h - 1, "↑↓ / jk  navigate   ENTER  confirm   ESC  cancel", curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")) and idx > 0:
            idx -= 1
        elif key in (curses.KEY_DOWN, ord("j")) and idx < len(PUZZLES) - 1:
            idx += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            return PUZZLES[idx].key
        elif key == 27:  # ESC
            return current_key


# ---------------------------------------------------------------------------
# Main timer loop
# ---------------------------------------------------------------------------


def _draw_timer(stdscr, state: dict) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    hidden: bool = state["timer_hidden"]

    def put(row, col, text, attr=0):
        try:
            stdscr.addstr(row, col, text[: w - col], attr)
        except curses.error:
            pass

    def center(row, text, attr=0):
        put(row, max(0, (w - len(text)) // 2), text, attr)

    puzzle: Puzzle = state["puzzle"]
    training: TrainingMode | None = state["training"]

    center(0, _header(puzzle, training), curses.A_BOLD)

    # Scramble
    lines = wrap_words(state["scramble"], w - 4)
    for i, line in enumerate(lines):
        center(2 + i, line)
    scramble_end_row = 2 + len(lines)

    # Timer
    timer_row = scramble_end_row + 2
    phase = state["phase"]
    if phase == "running":
        elapsed = int((time.perf_counter() - state["start"]) * 1000)
        attr = curses.A_BOLD
        display = "??" if hidden else fmt_time(elapsed)
    else:
        ms = state["last_time"]
        display = fmt_time(ms) if ms is not None else "0.00"
        attr = curses.A_BOLD if phase == "stopped" else curses.A_DIM

    center(timer_row, f"  {display}  ", attr)

    # Stats row
    stats = state["stats"]
    stats_row = timer_row + 2
    if stats.get("count", 0) > 0:
        parts = [f"solves: {stats['count']}", f"best: {fmt_time(stats['best'])}"]
        if stats.get("ao5"):
            parts.append(f"ao5: {fmt_time(int(stats['ao5']))}")
        if stats.get("ao12"):
            parts.append(f"ao12: {fmt_time(int(stats['ao12']))}")
        center(stats_row, "  ".join(parts))

    # Message
    if state.get("message"):
        center(h - 3, state["message"], curses.A_DIM)

    # Hint bar
    timer_label = "unhide" if hidden else "hide"
    training_label = "training ✓" if training else "training"
    if phase == "idle":
        hint = f"SPACE start  |  p puzzle  |  t {training_label}  |  s stats  |  h {timer_label}  |  d del  |  q quit"
    elif phase == "running":
        hint = "SPACE stop"
    else:
        hint = f"SPACE next  |  p puzzle  |  t {training_label}  |  s stats  |  h {timer_label}  |  d del  |  q quit"
    center(h - 1, hint, curses.A_DIM)

    stdscr.refresh()


def run_timer(stdscr) -> None:
    curses.use_default_colors()
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(50)

    puzzle = PUZZLE_KEYS[DEFAULT_PUZZLE_KEY]
    training: TrainingMode | None = None
    records = load_records(puzzle.key)

    state: dict = {
        "phase": "idle",
        "puzzle": puzzle,
        "training": training,
        "scramble": puzzle.scramble_fn(),
        "start": None,
        "last_time": None,
        "stats": compute_stats(records),
        "message": None,
        "timer_hidden": False,
    }

    while True:
        _draw_timer(stdscr, state)
        key = stdscr.getch()
        if key == -1:
            continue

        state["message"] = None

        if key in (ord("q"), ord("Q")):
            break

        elif key == ord(" "):
            if state["phase"] == "idle":
                state["phase"] = "running"
                state["start"] = time.perf_counter()

            elif state["phase"] == "running":
                elapsed_ms = int((time.perf_counter() - state["start"]) * 1000)
                state["last_time"] = elapsed_ms
                state["phase"] = "stopped"
                csv_key = _csv_key(state["puzzle"], state["training"])
                save_record(csv_key, state["scramble"], elapsed_ms)
                records = load_records(csv_key)
                state["stats"] = compute_stats(records)

            elif state["phase"] == "stopped":
                scramble_fn = _active_scramble_fn(state["puzzle"], state["training"])
                state["scramble"] = scramble_fn()
                state["phase"] = "idle"

        elif key in (ord("p"), ord("P")):
            if state["phase"] != "running":
                new_key = select_puzzle(stdscr, state["puzzle"].key)
                state["puzzle"] = PUZZLE_KEYS[new_key]
                state["training"] = None  # clear training on puzzle change
                state["scramble"] = state["puzzle"].scramble_fn()
                state["phase"] = "idle"
                state["last_time"] = None
                records = load_records(new_key)
                state["stats"] = compute_stats(records)
                stdscr.timeout(50)

        elif key in (ord("t"), ord("T")):
            if state["phase"] != "running":
                result = select_training(
                    stdscr,
                    state["training"].key if state["training"] else None,
                )
                if result != "cancel":
                    # Revert to 3x3 as training is ONLY for that
                    state["puzzle"] = PUZZLE_KEYS[DEFAULT_PUZZLE_KEY]
                    state["training"] = result  # None = cleared, TrainingMode = active
                    scramble_fn = _active_scramble_fn(
                        state["puzzle"], state["training"]
                    )
                    state["scramble"] = scramble_fn()
                    state["phase"] = "idle"
                    state["last_time"] = None
                    csv_key = _csv_key(state["puzzle"], state["training"])
                    records = load_records(csv_key)
                    state["stats"] = compute_stats(records)
                stdscr.timeout(50)

        elif key in (ord("s"), ord("S")):
            if state["phase"] != "running":
                csv_key = _csv_key(state["puzzle"], state["training"])
                show_stats(
                    stdscr, csv_key, _header(puzzle, state["training"]).strip("[ ]")
                )

        elif key in (ord("d"), ord("D")):
            if state["phase"] != "running":
                csv_key = _csv_key(state["puzzle"], state["training"])
                removed = delete_last_record(csv_key)
                if removed:
                    records = load_records(csv_key)
                    state["stats"] = compute_stats(records)
                    state["message"] = f"deleted: {fmt_time(int(removed['time_ms']))}"
                else:
                    state["message"] = "nothing to delete"

        elif key in (ord("h"), ord("H")):
            state["timer_hidden"] = not state["timer_hidden"]


def main():
    curses.wrapper(run_timer)


if __name__ == "__main__":
    main()
