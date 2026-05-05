"""Output formatters for logslice records."""

import json
from datetime import datetime
from typing import Any, Dict, Optional

LEVEL_COLORS = {
    "debug": "\033[36m",    # cyan
    "info": "\033[32m",     # green
    "warning": "\033[33m",  # yellow
    "warn": "\033[33m",     # yellow
    "error": "\033[31m",    # red
    "critical": "\033[35m", # magenta
    "fatal": "\033[35m",    # magenta
}
RESET = "\033[0m"
BOLD = "\033[1m"


def _colorize(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"


def _format_timestamp(record: Dict[str, Any]) -> Optional[str]:
    for key in ("timestamp", "time", "ts", "@timestamp"):
        if key in record:
            val = record[key]
            if isinstance(val, (int, float)):
                try:
                    return datetime.utcfromtimestamp(val).strftime("%Y-%m-%d %H:%M:%S")
                except (OSError, OverflowError, ValueError):
                    pass
            return str(val)
    return None


def format_pretty(record: Dict[str, Any], color: bool = True) -> str:
    """Format a log record as a human-readable line."""
    level = str(record.get("level", "info")).lower()
    message = record.get("message", record.get("msg", ""))
    timestamp = _format_timestamp(record)

    skip_keys = {"level", "message", "msg", "timestamp", "time", "ts", "@timestamp"}
    extras = {k: v for k, v in record.items() if k not in skip_keys}

    level_label = level.upper().ljust(8)
    if color:
        clr = LEVEL_COLORS.get(level, "")
        level_label = _colorize(BOLD + level_label, clr) if clr else BOLD + level_label + RESET

    parts = []
    if timestamp:
        parts.append(timestamp)
    parts.append(level_label)
    parts.append(str(message))

    if extras:
        extra_str = "  ".join(f"{k}={json.dumps(v)}" for k, v in extras.items())
        parts.append(extra_str)

    return "  ".join(parts)


def format_json(record: Dict[str, Any]) -> str:
    """Format a log record as compact JSON."""
    return json.dumps(record, default=str)


def format_record(record: Dict[str, Any], fmt: str = "pretty", color: bool = True) -> str:
    """Dispatch to the appropriate formatter."""
    if fmt == "json":
        return format_json(record)
    return format_pretty(record, color=color)
