"""Render aggregation summaries as human-readable or JSON reports."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from logslice.aggregator import LEVEL_ORDER


_LEVEL_COLORS = {
    "debug": "\033[36m",
    "info": "\033[32m",
    "warning": "\033[33m",
    "error": "\033[31m",
    "critical": "\033[35m",
    "unknown": "\033[37m",
}
_RESET = "\033[0m"


def _bar(count: int, total: int, width: int = 20) -> str:
    if total == 0:
        filled = 0
    else:
        filled = round(count / total * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def format_summary_pretty(
    summary: Dict[str, Any],
    color: bool = True,
    bar_width: int = 20,
) -> str:
    """Return a multi-line human-readable summary string."""
    lines = []
    total = summary.get("total", 0)
    lines.append(f"Total records : {total}")
    lines.append("By level:")

    by_level = summary.get("by_level", {})
    ordered_keys = [k for k in LEVEL_ORDER if k in by_level]
    ordered_keys += [k for k in by_level if k not in LEVEL_ORDER]

    for lvl in ordered_keys:
        count = by_level[lvl]
        bar = _bar(count, total, bar_width)
        label = lvl.upper().ljust(8)
        if color:
            col = _LEVEL_COLORS.get(lvl, "")
            label = f"{col}{label}{_RESET}"
        lines.append(f"  {label} {bar} {count}")

    if "by_group" in summary:
        field = summary["by_group"]["field"]
        lines.append(f"By '{field}':")
        for name, cnt in summary["by_group"]["counts"].items():
            bar = _bar(cnt, total, bar_width)
            lines.append(f"  {name:<20} {bar} {cnt}")

    return "\n".join(lines)


def format_summary_json(summary: Dict[str, Any]) -> str:
    """Return the summary serialised as compact JSON."""
    return json.dumps(summary, separators=(",", ":"))


def format_summary(
    summary: Dict[str, Any],
    fmt: str = "pretty",
    color: bool = True,
) -> str:
    """Dispatch to the appropriate formatter."""
    if fmt == "json":
        return format_summary_json(summary)
    return format_summary_pretty(summary, color=color)
