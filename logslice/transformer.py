"""Field transformation and normalization for log records."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional


_TRANSFORMS: Dict[str, Callable[[Any], Any]] = {
    "upper": lambda v: v.upper() if isinstance(v, str) else v,
    "lower": lambda v: v.lower() if isinstance(v, str) else v,
    "strip": lambda v: v.strip() if isinstance(v, str) else v,
    "int": lambda v: int(v),
    "float": lambda v: float(v),
    "str": lambda v: str(v),
    "bool": lambda v: bool(v),
}


def apply_transform(value: Any, transform: str) -> Any:
    """Apply a named transform to a value. Raises KeyError for unknown transforms."""
    if transform not in _TRANSFORMS:
        raise KeyError(f"Unknown transform: {transform!r}")
    return _TRANSFORMS[transform](value)


def rename_fields(record: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
    """Return a new record with fields renamed according to mapping."""
    result = dict(record)
    for old_key, new_key in mapping.items():
        if old_key in result:
            result[new_key] = result.pop(old_key)
    return result


def drop_fields(record: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """Return a new record with specified fields removed."""
    return {k: v for k, v in record.items() if k not in fields}


def add_fields(record: Dict[str, Any], additions: Dict[str, Any]) -> Dict[str, Any]:
    """Return a new record with additional fields merged in (does not overwrite)."""
    result = dict(record)
    for k, v in additions.items():
        if k not in result:
            result[k] = v
    return result


def transform_field(
    record: Dict[str, Any],
    field: str,
    transform: str,
) -> Dict[str, Any]:
    """Return a new record with a single field transformed."""
    if field not in record:
        return dict(record)
    result = dict(record)
    result[field] = apply_transform(result[field], transform)
    return result


def transform_record(
    record: Dict[str, Any],
    *,
    rename: Optional[Dict[str, str]] = None,
    drop: Optional[List[str]] = None,
    add: Optional[Dict[str, Any]] = None,
    field_transforms: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Apply a pipeline of transformations to a record."""
    result = dict(record)
    if rename:
        result = rename_fields(result, rename)
    if drop:
        result = drop_fields(result, drop)
    if add:
        result = add_fields(result, add)
    if field_transforms:
        for field, transform in field_transforms.items():
            result = transform_field(result, field, transform)
    return result
