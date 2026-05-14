"""Truncate long field values in log records to keep output readable."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional


_SENTINEL = "..."


def truncate_value(value: Any, max_length: int, placeholder: str = _SENTINEL) -> Any:
    """Truncate a string value to *max_length* characters.

    Non-string values are returned unchanged.  If the value is already within
    the limit it is returned as-is.  The placeholder is appended so callers
    can tell the value was shortened.
    """
    if not isinstance(value, str):
        return value
    if len(value) <= max_length:
        return value
    cutoff = max(0, max_length - len(placeholder))
    return value[:cutoff] + placeholder


def truncate_fields(
    record: Dict[str, Any],
    fields: List[str],
    max_length: int,
    placeholder: str = _SENTINEL,
) -> Dict[str, Any]:
    """Return a shallow copy of *record* with specified fields truncated."""
    out = dict(record)
    for field in fields:
        if field in out:
            out[field] = truncate_value(out[field], max_length, placeholder)
    return out


def truncate_all(
    record: Dict[str, Any],
    max_length: int,
    exclude: Optional[List[str]] = None,
    placeholder: str = _SENTINEL,
) -> Dict[str, Any]:
    """Return a shallow copy of *record* with ALL string fields truncated.

    Fields listed in *exclude* are left untouched.
    """
    skip = set(exclude or [])
    out = {}
    for key, value in record.items():
        if key in skip:
            out[key] = value
        else:
            out[key] = truncate_value(value, max_length, placeholder)
    return out


def truncate_stream(
    records: Iterable[Dict[str, Any]],
    max_length: int,
    fields: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    placeholder: str = _SENTINEL,
) -> Iterator[Dict[str, Any]]:
    """Yield truncated versions of each record in *records*.

    If *fields* is given only those fields are truncated; otherwise all string
    fields are truncated (respecting *exclude*).
    """
    for record in records:
        if fields is not None:
            yield truncate_fields(record, fields, max_length, placeholder)
        else:
            yield truncate_all(record, max_length, exclude, placeholder)
