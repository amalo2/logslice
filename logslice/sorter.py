"""Sort log records by one or more fields."""

from __future__ import annotations

from typing import Any, Iterable, Iterator, List, Optional, Tuple


def _get_field(record: dict, field: str) -> Any:
    """Return the value of *field* from *record*, or None if absent."""
    return record.get(field)


def _sort_key(record: dict, fields: List[str]) -> Tuple:
    """Build a sort key tuple from *fields* for comparison.

    None values sort before everything else so that records missing a
    field appear first regardless of direction.
    """
    key = []
    for field in fields:
        val = _get_field(record, field)
        # (0, val) sorts before (1, None) when reversed; use (is_none, val)
        key.append((0 if val is None else 1, val if val is not None else ""))
    return tuple(key)


def sort_records(
    records: Iterable[dict],
    fields: List[str],
    *,
    reverse: bool = False,
) -> List[dict]:
    """Return a sorted list of *records*.

    Args:
        records: Iterable of parsed log records.
        fields:  Field names to sort by, in priority order.
        reverse: When True, sort in descending order.

    Returns:
        A new list; the input iterable is not mutated.
    """
    if not fields:
        return list(records)
    return sorted(
        records,
        key=lambda r: _sort_key(r, fields),
        reverse=reverse,
    )


def sort_stream(
    records: Iterable[dict],
    fields: List[str],
    *,
    reverse: bool = False,
    limit: Optional[int] = None,
) -> Iterator[dict]:
    """Sort *records* and yield them one by one.

    Because sorting requires materialising the full stream, this helper
    buffers all records before yielding.  Use *limit* to cap output.
    """
    sorted_records = sort_records(records, fields, reverse=reverse)
    if limit is not None:
        sorted_records = sorted_records[:limit]
    yield from sorted_records
