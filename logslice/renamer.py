"""
logslice.renamer
~~~~~~~~~~~~~~~~
Batch-rename fields across a stream of log records using a mapping of
old_name -> new_name pairs.  Fields that do not exist in a record are
silently skipped; existing destination fields are NOT overwritten unless
``overwrite=True`` is passed.
"""
from __future__ import annotations

from typing import Dict, Iterable, Iterator


def rename_record(
    record: dict,
    mapping: Dict[str, str],
    *,
    overwrite: bool = False,
) -> dict:
    """Return a new record with fields renamed according to *mapping*.

    Parameters
    ----------
    record:
        The source log record (not mutated).
    mapping:
        ``{old_field: new_field}`` pairs.
    overwrite:
        When *True*, the destination field is replaced even if it already
        exists in the record.  Defaults to *False*.
    """
    result = dict(record)
    for old, new in mapping.items():
        if old not in result:
            continue
        if new in result and not overwrite:
            continue
        result[new] = result.pop(old)
    return result


def rename_stream(
    records: Iterable[dict],
    mapping: Dict[str, str],
    *,
    overwrite: bool = False,
) -> Iterator[dict]:
    """Yield records from *records* with fields renamed via *mapping*."""
    for record in records:
        yield rename_record(record, mapping, overwrite=overwrite)


def parse_mapping(pairs: Iterable[str]) -> Dict[str, str]:
    """Parse an iterable of ``'old:new'`` strings into a dict.

    Raises
    ------
    ValueError
        If any pair does not contain exactly one ``':'`` separator.
    """
    mapping: Dict[str, str] = {}
    for pair in pairs:
        parts = pair.split(":", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(
                f"Invalid rename pair {pair!r}: expected 'old_field:new_field'"
            )
        mapping[parts[0]] = parts[1]
    return mapping
