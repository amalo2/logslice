"""Group log records by one or more fields, yielding labelled batches."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Iterator, List, Optional, Tuple


def _get_field(record: dict, field: str) -> object:
    """Return the value of *field* from *record*, or None if absent."""
    return record.get(field)


def group_records(
    records: Iterable[dict],
    fields: List[str],
    max_groups: Optional[int] = None,
) -> Dict[Tuple, List[dict]]:
    """Collect *records* into a dict keyed by a tuple of field values.

    Parameters
    ----------
    records:    Iterable of parsed log records.
    fields:     Field names to group by (order matters).
    max_groups: If set, stop creating new groups after this many are seen;
                records that would start a new group beyond the limit are
                silently dropped.

    Returns
    -------
    An ordered dict mapping ``(v1, v2, …)`` tuples to lists of records.
    """
    groups: Dict[Tuple, List[dict]] = defaultdict(list)
    for record in records:
        key = tuple(_get_field(record, f) for f in fields)
        if max_groups is not None and key not in groups:
            if len(groups) >= max_groups:
                continue
        groups[key].append(record)
    return dict(groups)


def group_stream(
    records: Iterable[dict],
    fields: List[str],
    max_groups: Optional[int] = None,
) -> Iterator[Tuple[Tuple, List[dict]]]:
    """Yield ``(key, batch)`` pairs after consuming all of *records*.

    This is a convenience wrapper around :func:`group_records` that
    streams the groups in insertion order.
    """
    grouped = group_records(records, fields, max_groups=max_groups)
    yield from grouped.items()


def group_counts(
    records: Iterable[dict],
    fields: List[str],
    max_groups: Optional[int] = None,
) -> Dict[Tuple, int]:
    """Return a dict mapping each group key to its record count."""
    grouped = group_records(records, fields, max_groups=max_groups)
    return {key: len(batch) for key, batch in grouped.items()}
