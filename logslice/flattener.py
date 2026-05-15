"""
logslice.flattener
~~~~~~~~~~~~~~~~~~
Flatten nested JSON log records into dot-notation keys.

Example
-------
    {"a": {"b": {"c": 1}}}  ->  {"a.b.c": 1}
"""
from __future__ import annotations

from typing import Any, Generator, Iterable


def flatten_record(
    record: dict[str, Any],
    separator: str = ".",
    max_depth: int = 0,
    prefix: str = "",
) -> dict[str, Any]:
    """Return a new record with nested dicts collapsed into dot-notation keys.

    Args:
        record:     The source log record.
        separator:  Character(s) used to join key segments (default ``"."``).
        max_depth:  Maximum nesting depth to flatten.  ``0`` means unlimited.
        prefix:     Internal – key prefix accumulated during recursion.

    Returns:
        A flat ``dict`` with no nested ``dict`` values (up to *max_depth*).
    """
    result: dict[str, Any] = {}
    _flatten_into(record, result, separator=separator, max_depth=max_depth,
                  prefix=prefix, depth=0)
    return result


def _flatten_into(
    obj: Any,
    out: dict[str, Any],
    *,
    separator: str,
    max_depth: int,
    prefix: str,
    depth: int,
) -> None:
    if not isinstance(obj, dict) or (max_depth and depth >= max_depth):
        out[prefix] = obj
        return
    for key, value in obj.items():
        full_key = f"{prefix}{separator}{key}" if prefix else key
        _flatten_into(value, out, separator=separator, max_depth=max_depth,
                      prefix=full_key, depth=depth + 1)


def unflatten_record(
    record: dict[str, Any],
    separator: str = ".",
) -> dict[str, Any]:
    """Reconstruct a nested dict from a flat dot-notation record."""
    result: dict[str, Any] = {}
    for key, value in record.items():
        parts = key.split(separator)
        node = result
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return result


def flatten_stream(
    records: Iterable[dict[str, Any]],
    separator: str = ".",
    max_depth: int = 0,
) -> Generator[dict[str, Any], None, None]:
    """Yield flattened versions of every record in *records*."""
    for record in records:
        yield flatten_record(record, separator=separator, max_depth=max_depth)
