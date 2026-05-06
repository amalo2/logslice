"""Keyword highlighting for log output in logslice."""

import re
from typing import Optional

# ANSI escape codes
_RESET = "\033[0m"
_HIGHLIGHT = "\033[1;33m"  # Bold yellow
_HIGHLIGHT_BG = "\033[1;37;41m"  # White on red background


def highlight_text(
    text: str,
    keyword: str,
    *,
    case_sensitive: bool = False,
    style: str = "bold",
) -> str:
    """Return *text* with all occurrences of *keyword* wrapped in ANSI codes.

    Args:
        text: The source string to search within.
        keyword: The substring to highlight.
        case_sensitive: Whether the match should be case-sensitive.
        style: ``"bold"`` (default) or ``"bg"`` for background highlight.

    Returns:
        A new string with ANSI escape sequences inserted around matches.
        If *keyword* is empty or not found the original *text* is returned.
    """
    if not keyword:
        return text

    ansi_open = _HIGHLIGHT_BG if style == "bg" else _HIGHLIGHT
    flags = 0 if case_sensitive else re.IGNORECASE

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        return f"{ansi_open}{match.group(0)}{_RESET}"

    return re.sub(re.escape(keyword), _replace, text, flags=flags)


def highlight_record(
    record: dict,
    keyword: Optional[str],
    *,
    case_sensitive: bool = False,
    style: str = "bold",
) -> dict:
    """Return a shallow copy of *record* with string values highlighted.

    Only top-level string values are processed so that the original record
    is not mutated and nested structures remain intact.

    Args:
        record: A parsed log record (dict).
        keyword: The term to highlight.  ``None`` or empty string is a no-op.
        case_sensitive: Forwarded to :func:`highlight_text`.
        style: Forwarded to :func:`highlight_text`.

    Returns:
        A new dict with highlighted string values.
    """
    if not keyword:
        return record

    highlighted: dict = {}
    for key, value in record.items():
        if isinstance(value, str):
            highlighted[key] = highlight_text(
                value, keyword, case_sensitive=case_sensitive, style=style
            )
        else:
            highlighted[key] = value
    return highlighted


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from *text* (useful for tests)."""
    return re.sub(r"\033\[[0-9;]*m", "", text)
