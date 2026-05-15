"""Validate structured log records against a schema of required fields and types."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

# Map of type name strings to Python types
_TYPE_MAP: Dict[str, type] = {
    "str": str,
    "string": str,
    "int": int,
    "integer": int,
    "float": float,
    "number": float,
    "bool": bool,
    "boolean": bool,
}


def _resolve_type(type_name: str) -> Optional[type]:
    """Return the Python type for a type name string, or None if unknown."""
    return _TYPE_MAP.get(type_name.lower())


def validate_record(
    record: Dict[str, Any],
    required: Optional[List[str]] = None,
    field_types: Optional[Dict[str, str]] = None,
) -> Tuple[bool, List[str]]:
    """Validate a single record.

    Args:
        record: The log record dict to validate.
        required: Field names that must be present.
        field_types: Mapping of field name -> expected type name.

    Returns:
        A (valid, errors) tuple where errors is a list of human-readable strings.
    """
    errors: List[str] = []

    for field in required or []:
        if field not in record:
            errors.append(f"missing required field: '{field}'")

    for field, type_name in (field_types or {}).items():
        if field not in record:
            continue  # absence handled by required check
        expected = _resolve_type(type_name)
        if expected is None:
            errors.append(f"unknown type '{type_name}' for field '{field}'")
            continue
        value = record[field]
        # bool is a subclass of int in Python; check bool explicitly
        if expected is int and isinstance(value, bool):
            errors.append(f"field '{field}': expected int, got bool")
        elif not isinstance(value, expected):
            errors.append(
                f"field '{field}': expected {type_name}, got {type(value).__name__}"
            )

    return (len(errors) == 0, errors)


def validate_stream(
    records: Iterable[Dict[str, Any]],
    required: Optional[List[str]] = None,
    field_types: Optional[Dict[str, str]] = None,
    drop_invalid: bool = False,
) -> Iterator[Tuple[Dict[str, Any], List[str]]]:
    """Validate each record in a stream.

    Yields (record, errors) tuples.  When drop_invalid is True, records with
    errors are silently skipped.
    """
    for record in records:
        valid, errors = validate_record(record, required=required, field_types=field_types)
        if not valid and drop_invalid:
            continue
        yield record, errors
