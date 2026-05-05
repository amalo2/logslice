"""Filtering logic: decide whether a parsed log record matches a Query."""

from __future__ import annotations

from typing import Any, Dict, Optional

from logslice.query import Query

LEVEL_ORDER = ["trace", "debug", "info", "warning", "warn", "error", "critical", "fatal"]

_LEVEL_RANK: Dict[str, int] = {lvl: i for i, lvl in enumerate(LEVEL_ORDER)}
# Normalise common aliases
_LEVEL_RANK["warn"] = _LEVEL_RANK["warning"]
_LEVEL_RANK["fatal"] = _LEVEL_RANK["critical"]


def _get_nested(record: Dict[str, Any], key: str) -> Optional[Any]:
    """Return a value from a nested dict using dot-notation keys."""
    parts = key.split(".")
    node: Any = record
    for part in parts:
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def matches_level(record: Dict[str, Any], query: Query) -> bool:
    """Return True when the record's level satisfies the query's level constraint."""
    if query.level is None:
        return True
    record_level = str(record.get("level", "")).lower()
    query_level = str(query.level).lower()
    if query.level_op == "=":
        return record_level == query_level
    rec_rank = _LEVEL_RANK.get(record_level)
    qry_rank = _LEVEL_RANK.get(query_level)
    if rec_rank is None or qry_rank is None:
        return False
    if query.level_op == ">=":
        return rec_rank >= qry_rank
    if query.level_op == "<=":
        return rec_rank <= qry_rank
    if query.level_op == ">":
        return rec_rank > qry_rank
    if query.level_op == "<":
        return rec_rank < qry_rank
    return False


def matches_fields(record: Dict[str, Any], query: Query) -> bool:
    """Return True when all field constraints in the query are satisfied."""
    for key, value in query.fields.items():
        actual = _get_nested(record, key)
        if actual is None:
            return False
        if isinstance(actual, str) and isinstance(value, str):
            if actual.lower() != value.lower():
                return False
        elif actual != value:
            return False
    return True


def matches_search(record: Dict[str, Any], query: Query) -> bool:
    """Return True when the free-text search term appears anywhere in the record."""
    if not query.search:
        return True
    term = query.search.lower()
    return _scan(record, term)


def _scan(node: Any, term: str) -> bool:
    """Recursively search all string values in a nested structure."""
    if isinstance(node, str):
        return term in node.lower()
    if isinstance(node, dict):
        return any(_scan(v, term) for v in node.values())
    if isinstance(node, (list, tuple)):
        return any(_scan(item, term) for item in node)
    return term in str(node).lower()


def matches_record(record: Dict[str, Any], query: Query) -> bool:
    """Return True when a record satisfies every constraint in *query*."""
    return (
        matches_level(record, query)
        and matches_fields(record, query)
        and matches_search(record, query)
    )
