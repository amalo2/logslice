"""Compact log records by merging consecutive records that share a key field.

Useful for collapsing bursts of related log lines into a single summary record.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional


Record = Dict[str, Any]


def _get_field(record: Record, field: str) -> Any:
    return record.get(field)


def compact_records(
    records: Iterable[Record],
    key: str,
    count_field: str = "_count",
    merge_fields: Optional[List[str]] = None,
) -> Iterator[Record]:
    """Merge consecutive records that share the same value for *key*.

    The emitted record is the first record in each run, augmented with:
    - ``count_field``: how many records were merged.
    - Any ``merge_fields`` are collected into lists (deduped, order-preserved).
    """
    pending: Optional[Record] = None
    run_count = 0
    collected: Dict[str, List[Any]] = {}

    def _flush() -> Record:
        out = dict(pending)  # type: ignore[arg-type]
        out[count_field] = run_count
        if merge_fields:
            for mf in merge_fields:
                out[mf] = collected.get(mf, [])
        return out

    for record in records:
        val = _get_field(record, key)
        if pending is None:
            pending = record
            run_count = 1
            if merge_fields:
                for mf in merge_fields:
                    v = record.get(mf)
                    collected[mf] = [v] if v is not None else []
        elif _get_field(pending, key) == val:
            run_count += 1
            if merge_fields:
                for mf in merge_fields:
                    v = record.get(mf)
                    if v is not None and v not in collected[mf]:
                        collected[mf].append(v)
        else:
            yield _flush()
            pending = record
            run_count = 1
            collected = {}
            if merge_fields:
                for mf in merge_fields:
                    v = record.get(mf)
                    collected[mf] = [v] if v is not None else []

    if pending is not None:
        yield _flush()


def compact_stream(
    records: Iterable[Record],
    key: str,
    count_field: str = "_count",
    merge_fields: Optional[List[str]] = None,
) -> Iterator[Record]:
    """Thin wrapper around :func:`compact_records` for pipeline use."""
    yield from compact_records(records, key, count_field=count_field, merge_fields=merge_fields)
