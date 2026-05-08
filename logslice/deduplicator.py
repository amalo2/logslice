"""Deduplication of structured log records based on configurable keys."""

from __future__ import annotations

import hashlib
import json
from typing import Iterable, Iterator, List, Optional


def _fingerprint(record: dict, keys: Optional[List[str]] = None) -> str:
    """Return a stable hash string identifying a record.

    If *keys* is given, only those top-level fields contribute to the
    fingerprint.  Otherwise the entire record (sorted) is used.
    """
    if keys:
        subset = {k: record.get(k) for k in sorted(keys)}
    else:
        subset = dict(sorted(record.items()))
    serialised = json.dumps(subset, sort_keys=True, default=str)
    return hashlib.md5(serialised.encode()).hexdigest()


def deduplicate(
    records: Iterable[dict],
    keys: Optional[List[str]] = None,
    max_seen: int = 10_000,
) -> Iterator[dict]:
    """Yield each unique record exactly once.

    Parameters
    ----------
    records:
        Iterable of parsed log record dicts.
    keys:
        Optional list of field names used to define uniqueness.  When
        *None* the full record contents are compared.
    max_seen:
        Maximum number of fingerprints kept in memory.  Once the set
        exceeds this limit the oldest entries are evicted (FIFO) so
        that memory is bounded for very long streams.
    """
    seen: dict[str, None] = {}  # ordered dict used as an ordered set
    for record in records:
        fp = _fingerprint(record, keys)
        if fp in seen:
            continue
        seen[fp] = None
        if len(seen) > max_seen:
            # Evict the oldest entry
            oldest = next(iter(seen))
            del seen[oldest]
        yield record


def count_duplicates(
    records: Iterable[dict],
    keys: Optional[List[str]] = None,
) -> tuple[int, int]:
    """Return *(total, duplicates)* counts for the given records."""
    seen: set[str] = set()
    total = 0
    duplicates = 0
    for record in records:
        total += 1
        fp = _fingerprint(record, keys)
        if fp in seen:
            duplicates += 1
        else:
            seen.add(fp)
    return total, duplicates
