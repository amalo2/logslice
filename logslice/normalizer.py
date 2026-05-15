"""
logslice.normalizer
~~~~~~~~~~~~~~~~~~~
Normalize field names and values across log records for consistent downstream
processing (e.g. lowercase all keys, canonicalize level names, strip whitespace
from string values).
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional

Record = Dict[str, Any]

_LEVEL_ALIASES: Dict[str, str] = {
    "warn": "warning",
    "err": "error",
    "crit": "critical",
    "dbg": "debug",
    "trace": "debug",
    "fatal": "critical",
}


def normalize_keys(record: Record) -> Record:
    """Return a new record with all top-level keys lowercased."""
    return {k.lower(): v for k, v in record.items()}


def normalize_level(record: Record, field: str = "level") -> Record:
    """Canonicalize the value of *field* using known aliases.

    The field value is lowercased and looked up in ``_LEVEL_ALIASES``.  If no
    alias is found the lowercased value is kept as-is.  Records without the
    field are returned unchanged.
    """
    if field not in record:
        return record
    raw = str(record[field]).lower().strip()
    canonical = _LEVEL_ALIASES.get(raw, raw)
    return {**record, field: canonical}


def normalize_strings(record: Record, fields: Optional[List[str]] = None) -> Record:
    """Strip leading/trailing whitespace from string values.

    If *fields* is given only those fields are processed; otherwise every
    top-level string value is stripped.
    """
    out = dict(record)
    targets = fields if fields is not None else list(out.keys())
    for key in targets:
        if key in out and isinstance(out[key], str):
            out[key] = out[key].strip()
    return out


def normalize_record(
    record: Record,
    *,
    lowercase_keys: bool = True,
    canonicalize_level: bool = True,
    level_field: str = "level",
    strip_strings: bool = True,
    strip_fields: Optional[List[str]] = None,
) -> Record:
    """Apply all requested normalization steps to *record* and return a copy."""
    out = record
    if lowercase_keys:
        out = normalize_keys(out)
        # keep level_field in sync if keys were lowercased
        level_field = level_field.lower()
    if canonicalize_level:
        out = normalize_level(out, field=level_field)
    if strip_strings:
        out = normalize_strings(out, fields=strip_fields)
    return out


def normalize_stream(
    records: Iterable[Record],
    **kwargs: Any,
) -> Iterator[Record]:
    """Yield normalized copies of every record in *records*."""
    for record in records:
        yield normalize_record(record, **kwargs)
