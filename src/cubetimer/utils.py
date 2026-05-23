"""
utils.py — display formatting helpers
"""


def fmt_time(ms: int | float) -> str:
    """Format milliseconds as M:SS.ss or SS.ss."""
    s = ms / 1000
    if s < 60:
        return f"{s:.2f}"
    m = int(s // 60)
    s = s % 60
    return f"{m}:{s:05.2f}"


def wrap_words(text: str, width: int) -> list[str]:
    """Wrap a string to lines of at most `width` chars, on word boundaries."""
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = (line + " " + word).strip()
        if len(candidate) <= width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines or [""]
