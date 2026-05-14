"""
Rate-limit a stream of log records, emitting at most N records per time-bucket
(second / minute / hour).  Useful for taming extremely noisy log sources
before piping output to downstream consumers.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable, Iterator, Literal

Unit = Literal["second", "minute", "hour"]

_DIVISORS: dict[Unit, int] = {
    "second": 1,
    "minute": 60,
    "hour": 3600,
}


def _bucket(ts: float, unit: Unit) -> int:
    """Return an integer bucket index for *ts* (epoch seconds)."""
    return math.floor(ts / _divisor(unit))


def _divisor(unit: Unit) -> int:
    if unit not in _DIVISORS:
        raise ValueError(f"unit must be one of {list(_DIVISORS)}; got {unit!r}")
    return _DIVISORS[unit]


def _extract_ts(record: dict) -> float | None:
    """Return a float epoch timestamp from common timestamp fields, or None."""
    for key in ("timestamp", "ts", "time", "@timestamp"):
        val = record.get(key)
        if val is None:
            continue
        try:
            return float(val)
        except (TypeError, ValueError):
            pass
    return None


def rate_limit(
    records: Iterable[dict],
    limit: int,
    unit: Unit = "second",
    group_by: str | None = None,
) -> Iterator[dict]:
    """Yield records, dropping those that exceed *limit* per *unit*.

    Parameters
    ----------
    records:  iterable of parsed log records.
    limit:    maximum number of records to emit per bucket.
    unit:     bucket granularity — ``"second"``, ``"minute"``, or ``"hour"``.
    group_by: optional field name; limits are applied independently per
              distinct value of that field (e.g. ``"service"`` or ``"level"``).
    """
    if limit < 1:
        raise ValueError(f"limit must be >= 1; got {limit}")
    _divisor(unit)  # validate early

    counts: dict[tuple, int] = defaultdict(int)
    seq = 0  # monotonic counter used when no timestamp is present

    for record in records:
        ts = _extract_ts(record)
        bucket = _bucket(ts, unit) if ts is not None else seq
        group = record.get(group_by) if group_by else None
        key = (bucket, group)
        if counts[key] < limit:
            counts[key] += 1
            yield record
        seq += 1
