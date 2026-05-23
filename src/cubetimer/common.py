"""
common.py — shared constants, puzzle registry, path config
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


RECORDS_FILE = Path.home() / ".cubetimer.csv"
CSV_FIELDS = ["timestamp", "puzzle", "time_ms", "scramble"]


@dataclass(frozen=True)
class Puzzle:
    key: str  # internal key used in CSV
    label: str  # display name
    scramble_fn: Callable[[], str]


@dataclass(frozen=True)
class TrainingMode:
    key: str  # appended to puzzle key in CSV: "3x3:pll"
    label: str  # display name
    scramble_fn: Callable[[], str]


def _load_puzzles() -> list[Puzzle]:
    """
    Ordered list of puzzles. Ed's puzzles first, then full WCA roster.
    mirror cube is a 3x3 alias.
    """
    import pyTwistyScrambler.clockScrambler as clock
    import pyTwistyScrambler.megaminxScrambler as mega
    import pyTwistyScrambler.pyraminxScrambler as pyra
    import pyTwistyScrambler.scrambler222 as s2
    import pyTwistyScrambler.scrambler333 as s3
    import pyTwistyScrambler.scrambler444 as s4
    import pyTwistyScrambler.scrambler555 as s5
    import pyTwistyScrambler.scrambler666 as s6
    import pyTwistyScrambler.scrambler777 as s7
    import pyTwistyScrambler.skewbScrambler as skewb
    import pyTwistyScrambler.squareOneScrambler as sq1

    return [
        # --- Ed's puzzles ---
        Puzzle("3x3", "3x3x3", s3.get_WCA_scramble),
        Puzzle("4x4", "4x4x4", s4.get_WCA_scramble),
        Puzzle("3x3-feet", "3x3x3 (Feet)", s3.get_WCA_scramble),
        Puzzle("mirror", "Mirror Cube (3x3)", s3.get_WCA_scramble),
        # --- full WCA roster ---
        Puzzle("2x2", "2x2x2", s2.get_WCA_scramble),
        Puzzle("5x5", "5x5x5", s5.get_WCA_scramble),
        Puzzle("6x6", "6x6x6", s6.get_WCA_scramble),
        Puzzle("7x7", "7x7x7", s7.get_WCA_scramble),
        Puzzle("pyra", "Pyraminx", pyra.get_WCA_scramble),
        Puzzle("skewb", "Skewb", skewb.get_WCA_scramble),
        Puzzle("mega", "Megaminx", mega.get_WCA_scramble),
        Puzzle("sq1", "Square-1", sq1.get_WCA_scramble),
        Puzzle("clock", "Clock", clock.get_WCA_scramble),
    ]


def _load_training_modes() -> list[TrainingMode]:
    """
    Training modes for 3x3. Scramble functions target specific subsets.
    Keyed by puzzle in CSV as e.g. "3x3:ll", "3x3:pll".
    """
    import pyTwistyScrambler.scrambler333 as s3

    return [
        TrainingMode("ll", "Last Layer", s3.get_LL_scramble),
        TrainingMode("pll", "PLL", s3.get_ZBLL_scramble),
        TrainingMode("f2l", "F2L", s3.get_F2L_scramble),
        TrainingMode("cmll", "CMLL", s3.get_CMLL_scramble),
        TrainingMode("zbls", "ZBLS", s3.get_ZBLS_scramble),
        TrainingMode("lse", "LSE", s3.get_LSE_scramble),
        TrainingMode("2gen-ru", "2-gen RU", s3.get_2genRU_scramble),
        TrainingMode("2gen-lu", "2-gen LU", s3.get_2genLU_scramble),
        TrainingMode("2gen-mu", "2-gen MU", s3.get_2genMU_scramble),
        TrainingMode("ht", "Half-turns only", s3.get_half_turns_scramble),
    ]


# Lazy-load once at import time
PUZZLES: list[Puzzle] = _load_puzzles()
PUZZLE_KEYS: dict[str, Puzzle] = {p.key: p for p in PUZZLES}
DEFAULT_PUZZLE_KEY = "3x3"

TRAINING_MODES: list[TrainingMode] = _load_training_modes()
TRAINING_MODE_KEYS: dict[str, TrainingMode] = {t.key: t for t in TRAINING_MODES}
