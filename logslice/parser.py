"""JSON log line parser for logslice.

Parses individual log lines into structured dicts, handling both
pure JSON and common log formats with a JSON payload.
"""

import json
import re
from typing import Optional

# Matches lines like: 2024-01-15T12:00:00Z INFO {"key": "value"}
_PREFIX_RE = re.compile(
    r'^(?P<ts>\S+)\s+(?P<level>[A-Z]+)\s+(?P<json>\{.*)$'
)


def parse_line(line: str) -> Optional[dict]:
    """Parse a single log line into a dict.

    Supports:
    - Pure JSON objects: {"level": "info", "msg": "hello"}
    - Prefixed JSON: 2024-01-15T12:00:00Z INFO {"msg": "hello"}

    Returns None if the line cannot be parsed.
    """
    line = line.strip()
    if not line:
        return None

    # Try pure JSON first
    if line.startswith('{'):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return None

    # Try prefixed format
    match = _PREFIX_RE.match(line)
    if match:
        try:
            record = json.loads(match.group('json'))
            record.setdefault('timestamp', match.group('ts'))
            record.setdefault('level', match.group('level').lower())
            return record
        except json.JSONDecodeError:
            return None

    return None


def parse_lines(lines) -> list[dict]:
    """Parse an iterable of log lines, skipping unparseable ones."""
    results = []
    for line in lines:
        record = parse_line(line)
        if record is not None:
            results.append(record)
    return results
