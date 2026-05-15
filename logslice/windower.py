"""Time-window bucketing for structured log records."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict, Iterable, Iterator, List, Optional, Tuple


def _extract_ts(record: dict) -> Optional[float]:
    """Return a numeric timestamp from common timestamp keys."""
    for key in ("timestamp", "ts", "time", "t"):
        val = record.get(key)
        if isinstance(val, (int, float)):
            return float(val)
    return None


def _bucket_key(ts: float, window_seconds: float) -> float:
    """Return the start of the window bucket that *ts* falls into."""
    return math.floor(ts / window_seconds) * window_seconds


def window_records(
    records: Iterable[dict],
    window_seconds: float,
    *,
    drop_missing_ts: bool = False,
) -> Dict[float, List[dict]]:
    """Group *records* into fixed-size time windows.

    Returns a dict mapping window-start (float) -> list of records.
    Records without a parseable timestamp are placed under the key ``None``
    unless *drop_missing_ts* is True, in which case they are discarded.
    """
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")

    buckets: Dict[float, List[dict]] = defaultdict(list)
    no_ts: List[dict] = []

    for rec in records:
        ts = _extract_ts(rec)
        if ts is None:
            if not drop_missing_ts:
                no_ts.append(rec)
        else:
            buckets[_bucket_key(ts, window_seconds)].append(rec)

    result: Dict = dict(buckets)
    if no_ts:
        result[None] = no_ts  # type: ignore[assignment]
    return result


def window_stream(
    records: Iterable[dict],
    window_seconds: float,
    *,
    drop_missing_ts: bool = False,
) -> Iterator[Tuple[Optional[float], List[dict]]]:
    """Yield ``(window_start, records)`` tuples in ascending order.

    Windows with no timestamp are yielded last.
    """
    bucketed = window_records(
        records, window_seconds, drop_missing_ts=drop_missing_ts
    )
    no_ts_bucket = bucketed.pop(None, None)  # type: ignore[arg-type]

    for key in sorted(bucketed):
        yield key, bucketed[key]

    if no_ts_bucket is not None:
        yield None, no_ts_bucket


def window_counts(
    records: Iterable[dict],
    window_seconds: float,
    *,
    drop_missing_ts: bool = False,
) -> Iterator[Tuple[Optional[float], int]]:
    """Yield ``(window_start, count)`` tuples — a lightweight histogram."""
    for start, recs in window_stream(
        records, window_seconds, drop_missing_ts=drop_missing_ts
    ):
        yield start, len(recs)
