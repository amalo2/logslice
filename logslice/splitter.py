"""Split a log stream into multiple output files based on a field value."""

from __future__ import annotations

import os
from typing import Dict, Iterable, Iterator, Optional

from logslice.parser import parse_line


def _get_field(record: dict, field: str) -> Optional[str]:
    """Return a string representation of *field* from *record*, or None."""
    value = record.get(field)
    if value is None:
        return None
    return str(value)


def split_records(
    records: Iterable[dict],
    field: str,
    fallback: str = "__other__",
) -> Dict[str, list]:
    """Partition *records* into buckets keyed by the value of *field*.

    Records that do not contain *field* are placed in the *fallback* bucket.
    Returns a plain dict mapping bucket name -> list of records.
    """
    buckets: Dict[str, list] = {}
    for record in records:
        key = _get_field(record, field) or fallback
        buckets.setdefault(key, []).append(record)
    return buckets


def split_stream(
    lines: Iterable[str],
    field: str,
    fallback: str = "__other__",
) -> Dict[str, list]:
    """Parse *lines* and partition resulting records by *field*.

    Non-JSON / unparseable lines are silently skipped.
    """
    records = (r for line in lines if (r := parse_line(line)) is not None)
    return split_records(records, field, fallback=fallback)


def write_splits(
    buckets: Dict[str, list],
    output_dir: str,
    prefix: str = "",
    suffix: str = ".jsonl",
) -> Dict[str, str]:
    """Write each bucket to a separate file inside *output_dir*.

    Returns a mapping of bucket name -> file path for every file written.
    """
    import json

    os.makedirs(output_dir, exist_ok=True)
    written: Dict[str, str] = {}
    for key, records in buckets.items():
        safe_key = key.replace(os.sep, "_").replace(" ", "_")
        filename = f"{prefix}{safe_key}{suffix}"
        path = os.path.join(output_dir, filename)
        with open(path, "w", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        written[key] = path
    return written
