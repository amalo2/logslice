"""
logslice.differ
~~~~~~~~~~~~~~~
Compare two streams of JSON log records and surface added, removed,
or changed fields between consecutive matching records.
"""
from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Tuple

Record = Dict[str, Any]


def diff_records(
    before: Record,
    after: Record,
    ignore_keys: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Return a structured diff between two records.

    Returns a dict with three keys:
      - ``added``   – keys present in *after* but not in *before*
      - ``removed`` – keys present in *before* but not in *after*
      - ``changed`` – keys present in both whose values differ
    """
    ignore = set(ignore_keys or [])

    before_keys = {k for k in before if k not in ignore}
    after_keys = {k for k in after if k not in ignore}

    added = {k: after[k] for k in after_keys - before_keys}
    removed = {k: before[k] for k in before_keys - after_keys}
    changed = {
        k: {"before": before[k], "after": after[k]}
        for k in before_keys & after_keys
        if before[k] != after[k]
    }

    return {"added": added, "removed": removed, "changed": changed}


def is_empty_diff(diff: Dict[str, Dict[str, Any]]) -> bool:
    """Return True when a diff produced by :func:`diff_records` has no changes."""
    return not diff["added"] and not diff["removed"] and not diff["changed"]


def diff_stream(
    records: Iterator[Record],
    key: Optional[str] = None,
    ignore_keys: Optional[List[str]] = None,
) -> Iterator[Tuple[Record, Record, Dict[str, Dict[str, Any]]]]:
    """Yield ``(before, after, diff)`` tuples for consecutive record pairs.

    If *key* is given, only consecutive records that share the same value for
    *key* are compared; otherwise every adjacent pair is compared.
    """
    prev: Optional[Record] = None

    for record in records:
        if prev is not None:
            if key is None or prev.get(key) == record.get(key):
                d = diff_records(prev, record, ignore_keys=ignore_keys)
                if not is_empty_diff(d):
                    yield prev, record, d
        prev = record
