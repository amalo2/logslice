"""Filter structured log records based on field expressions."""

from typing import Any, Dict, List, Optional


LEVEL_ORDER = {
    "trace": 0,
    "debug": 1,
    "info": 2,
    "warning": 3,
    "warn": 3,
    "error": 4,
    "fatal": 5,
    "critical": 5,
}


def _get_nested(record: Dict[str, Any], key: str) -> Any:
    """Retrieve a possibly dot-nested key from a record."""
    parts = key.split(".")
    value = record
    for part in parts:
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def matches_level(record: Dict[str, Any], min_level: str) -> bool:
    """Return True if the record's level is >= min_level."""
    raw = _get_nested(record, "level")
    if raw is None:
        return True
    record_rank = LEVEL_ORDER.get(str(raw).lower(), -1)
    min_rank = LEVEL_ORDER.get(min_level.lower(), -1)
    return record_rank >= min_rank


def matches_fields(record: Dict[str, Any], fields: Dict[str, Any]) -> bool:
    """Return True if all field filters match the record."""
    for key, expected in fields.items():
        actual = _get_nested(record, key)
        if actual != expected:
            return False
    return True


def matches_search(record: Dict[str, Any], search: str) -> bool:
    """Return True if search string appears in any string value of the record."""
    search_lower = search.lower()

    def _scan(value: Any) -> bool:
        if isinstance(value, str):
            return search_lower in value.lower()
        if isinstance(value, dict):
            return any(_scan(v) for v in value.values())
        if isinstance(value, list):
            return any(_scan(v) for v in value)
        return search_lower in str(value).lower()

    return _scan(record)


def apply_filter(
    record: Dict[str, Any],
    min_level: Optional[str] = None,
    fields: Optional[Dict[str, Any]] = None,
    search: Optional[str] = None,
) -> bool:
    """Return True if the record passes all active filters."""
    if min_level and not matches_level(record, min_level):
        return False
    if fields and not matches_fields(record, fields):
        return False
    if search and not matches_search(record, search):
        return False
    return True
