"""
records.py — CSV persistence and solve stats
"""

import csv
from datetime import datetime

from .common import CSV_FIELDS
from .common import RECORDS_FILE


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def load_records(puzzle_key: str | None = None) -> list[dict]:
    """Load all records, optionally filtered by puzzle key."""
    if not RECORDS_FILE.exists():
        return []
    with open(RECORDS_FILE, newline="") as f:
        rows = list(csv.DictReader(f))
    if puzzle_key:
        rows = [r for r in rows if r.get("puzzle") == puzzle_key]
    return rows


def save_record(puzzle_key: str, scramble: str, elapsed_ms: int) -> None:
    exists = RECORDS_FILE.exists()
    with open(RECORDS_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "puzzle": puzzle_key,
                "time_ms": elapsed_ms,
                "scramble": scramble,
            }
        )


def delete_last_record(puzzle_key: str) -> dict | None:
    """Delete the most recent record for the given puzzle. Returns deleted row or None."""
    all_records = load_records()
    # Find last index matching this puzzle
    idx = None
    for i in range(len(all_records) - 1, -1, -1):
        if all_records[i].get("puzzle") == puzzle_key:
            idx = i
            break
    if idx is None:
        return None
    removed = all_records.pop(idx)
    with open(RECORDS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(all_records)
    return removed


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


def _trimmed_avg(times: list[int]) -> float | None:
    """WCA-style trimmed mean: drop best and worst."""
    if len(times) < 3:
        return None
    trimmed = sorted(times)[1:-1]
    return sum(trimmed) / len(trimmed)


def compute_stats(records: list[dict]) -> dict:
    times = [int(r["time_ms"]) for r in records]
    if not times:
        return {"count": 0}

    count = len(times)
    return {
        "count": count,
        "best": min(times),
        "worst": max(times),
        "mean": sum(times) / count,
        "ao5": _trimmed_avg(times[-5:]) if count >= 5 else None,
        "ao12": _trimmed_avg(times[-12:]) if count >= 12 else None,
        "ao50": _trimmed_avg(times[-50:]) if count >= 50 else None,
        "ao100": _trimmed_avg(times[-100:]) if count >= 100 else None,
    }
