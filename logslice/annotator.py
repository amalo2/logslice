"""Annotate log records with computed metadata fields."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional

Record = Dict[str, Any]


def annotate_index(
    record: Record,
    index: int,
    field: str = "_index",
) -> Record:
    """Add a sequential index field to a record."""
    out = dict(record)
    out[field] = index
    return out


def annotate_source(
    record: Record,
    source: str,
    field: str = "_source",
) -> Record:
    """Tag a record with the name of its originating source."""
    out = dict(record)
    out[field] = source
    return out


def annotate_fields_present(
    record: Record,
    fields: List[str],
    field: str = "_fields_present",
) -> Record:
    """Add a list of which watched fields are present and non-null."""
    out = dict(record)
    out[field] = [f for f in fields if record.get(f) is not None]
    return out


def annotate_record(
    record: Record,
    *,
    index: Optional[int] = None,
    source: Optional[str] = None,
    watch_fields: Optional[List[str]] = None,
    index_field: str = "_index",
    source_field: str = "_source",
    presence_field: str = "_fields_present",
) -> Record:
    """Apply all requested annotations to a single record."""
    out = dict(record)
    if index is not None:
        out = annotate_index(out, index, field=index_field)
    if source is not None:
        out = annotate_source(out, source, field=source_field)
    if watch_fields is not None:
        out = annotate_fields_present(out, watch_fields, field=presence_field)
    return out


def annotate_stream(
    records: Iterable[Record],
    *,
    source: Optional[str] = None,
    watch_fields: Optional[List[str]] = None,
    index_field: str = "_index",
    source_field: str = "_source",
    presence_field: str = "_fields_present",
) -> Iterator[Record]:
    """Annotate every record in a stream with index and optional metadata."""
    for i, record in enumerate(records):
        yield annotate_record(
            record,
            index=i,
            source=source,
            watch_fields=watch_fields,
            index_field=index_field,
            source_field=source_field,
            presence_field=presence_field,
        )
