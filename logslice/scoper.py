"""Scope records to a time range using timestamp fields."""
from __future__ import annotations

from typing import Iterable, Iterator, Optional


def _extract_ts(record: dict) -> Optional[float]:
    """Return a numeric timestamp from common timestamp field names."""
    for key in ("timestamp", "ts", "time", "@timestamp"):
        val = record.get(key)
        if val is None:
            continue
        try:
            return float(val)
        except (TypeError, ValueError):
            continue
    return None


def scope_records(
    records: Iterable[dict],
    *,
    since: Optional[float] = None,
    until: Optional[float] = None,
    drop_missing: bool = False,
) -> Iterator[dict]:
    """Yield records whose timestamp falls within [since, until].

    Args:
        records:      Iterable of parsed log records.
        since:        Inclusive lower bound (epoch seconds).  None = no lower bound.
        until:        Inclusive upper bound (epoch seconds).  None = no upper bound.
        drop_missing: If True, records with no recognisable timestamp are dropped.
                      If False (default) they are passed through unchanged.
    """
    for record in records:
        ts = _extract_ts(record)
        if ts is None:
            if not drop_missing:
                yield record
            continue
        if since is not None and ts < since:
            continue
        if until is not None and ts > until:
            continue
        yield record


def scope_stream(
    lines: Iterable[str],
    *,
    since: Optional[float] = None,
    until: Optional[float] = None,
    drop_missing: bool = False,
) -> Iterator[dict]:
    """Parse JSON lines and scope them to a time range."""
    import json

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        yield from scope_records(
            [record], since=since, until=until, drop_missing=drop_missing
        )
