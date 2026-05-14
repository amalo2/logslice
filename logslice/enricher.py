"""Enrich log records with derived or static fields."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

Record = Dict[str, Any]


def enrich_static(record: Record, fields: Dict[str, Any]) -> Record:
    """Return a new record with static key/value pairs added.

    Existing keys are NOT overwritten.
    """
    merged = dict(fields)
    merged.update(record)
    return merged


def enrich_copy(record: Record, mappings: List[Tuple[str, str]]) -> Record:
    """Copy values from existing fields into new fields.

    Each mapping is (source_key, dest_key).  If source_key is absent the
    dest_key is silently skipped.  Existing dest_key values are not overwritten.
    """
    result = dict(record)
    for src, dst in mappings:
        if dst not in result and src in record:
            result[dst] = record[src]
    return result


def enrich_extract(record: Record, source_key: str, pattern: str, dest_key: str) -> Record:
    """Extract a named group from a string field via regex and store it.

    The regex must contain exactly one named group ``value``.  If the field is
    absent, not a string, or the pattern does not match, the record is returned
    unchanged.
    """
    value = record.get(source_key)
    if not isinstance(value, str):
        return record
    m = re.search(pattern, value)
    if m is None:
        return record
    try:
        extracted = m.group("value")
    except IndexError:
        return record
    result = dict(record)
    result.setdefault(dest_key, extracted)
    return result


def enrich_record(
    record: Record,
    *,
    static: Optional[Dict[str, Any]] = None,
    copies: Optional[List[Tuple[str, str]]] = None,
    extractions: Optional[List[Tuple[str, str, str]]] = None,
) -> Record:
    """Apply all enrichment steps in order and return the final record."""
    if static:
        record = enrich_static(record, static)
    if copies:
        record = enrich_copy(record, copies)
    if extractions:
        for source_key, pattern, dest_key in extractions:
            record = enrich_extract(record, source_key, pattern, dest_key)
    return record


def enrich_stream(
    records: Iterable[Record],
    *,
    static: Optional[Dict[str, Any]] = None,
    copies: Optional[List[Tuple[str, str]]] = None,
    extractions: Optional[List[Tuple[str, str, str]]] = None,
) -> Iterator[Record]:
    """Apply enrichment to every record in an iterable."""
    for record in records:
        yield enrich_record(record, static=static, copies=copies, extractions=extractions)
