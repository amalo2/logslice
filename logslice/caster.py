"""Field type casting for structured log records."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional


_CASTERS = {
    "int": int,
    "float": float,
    "str": str,
    "bool": lambda v: v if isinstance(v, bool) else str(v).lower() in ("1", "true", "yes"),
}


def _cast_value(value: Any, target_type: str) -> Any:
    """Cast *value* to *target_type*. Returns the original value on failure."""
    caster = _CASTERS.get(target_type)
    if caster is None:
        raise ValueError(f"Unknown cast type: {target_type!r}")
    try:
        return caster(value)
    except (ValueError, TypeError):
        return value


def cast_fields(
    record: Dict[str, Any],
    casts: Dict[str, str],
) -> Dict[str, Any]:
    """Return a copy of *record* with specified fields cast to new types.

    *casts* maps field names to target type strings (``'int'``, ``'float'``,
    ``'str'``, ``'bool'``).  Fields absent from the record are silently
    skipped.  Unrecognised type names raise :class:`ValueError`.
    """
    result = dict(record)
    for field, target_type in casts.items():
        if field in result:
            result[field] = _cast_value(result[field], target_type)
    return result


def cast_stream(
    records: Iterable[Dict[str, Any]],
    casts: Dict[str, str],
) -> Iterator[Dict[str, Any]]:
    """Yield records from *records* with fields cast according to *casts*."""
    for record in records:
        yield cast_fields(record, casts)


def parse_cast_specs(specs: List[str]) -> Dict[str, str]:
    """Parse a list of ``'field:type'`` strings into a mapping.

    >>> parse_cast_specs(["status:int", "ratio:float"])
    {'status': 'int', 'ratio': 'float'}
    """
    mapping: Dict[str, str] = {}
    for spec in specs:
        if ":" not in spec:
            raise ValueError(f"Invalid cast spec (expected 'field:type'): {spec!r}")
        field, _, target_type = spec.partition(":")
        field = field.strip()
        target_type = target_type.strip()
        if not field or not target_type:
            raise ValueError(f"Invalid cast spec (empty field or type): {spec!r}")
        mapping[field] = target_type
    return mapping
