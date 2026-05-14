"""Tag log records with user-defined labels based on field conditions."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional

from logslice.filter import _get_nested


def _matches_condition(record: Dict[str, Any], field: str, value: Any) -> bool:
    """Return True if record[field] equals value (string comparison supported)."""
    actual = _get_nested(record, field)
    if actual is None:
        return False
    return str(actual).lower() == str(value).lower()


def tag_record(
    record: Dict[str, Any],
    rules: List[Dict[str, Any]],
    tag_field: str = "tags",
) -> Dict[str, Any]:
    """Apply tagging rules to a single record.

    Each rule is a dict with keys:
      - ``field``: the record field to inspect
      - ``value``: the value to match against
      - ``tag``:   the label to apply when the condition is met

    Tags are accumulated in *tag_field* as a sorted, deduplicated list.
    The original record is not mutated.
    """
    if not rules:
        return record

    applied: List[str] = []
    for rule in rules:
        field = rule.get("field", "")
        value = rule.get("value", "")
        tag = rule.get("tag", "")
        if not field or not tag:
            continue
        if _matches_condition(record, field, value):
            applied.append(tag)

    if not applied:
        return record

    result = dict(record)
    existing = result.get(tag_field, [])
    if isinstance(existing, list):
        merged = list(existing) + applied
    else:
        merged = [str(existing)] + applied
    result[tag_field] = sorted(set(merged))
    return result


def tag_stream(
    records: Iterable[Dict[str, Any]],
    rules: List[Dict[str, Any]],
    tag_field: str = "tags",
) -> Iterator[Dict[str, Any]]:
    """Yield tagged records from an iterable of records."""
    for record in records:
        yield tag_record(record, rules, tag_field=tag_field)
