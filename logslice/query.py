"""Parse a logslice query string into filter parameters."""

import re
import shlex
from typing import Any, Dict, Optional, Tuple


_FIELD_RE = re.compile(r'^([\w.]+)=(.+)$')


class Query:
    """Represents a parsed logslice query."""

    def __init__(
        self,
        min_level: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None,
    ):
        self.min_level = min_level
        self.fields: Dict[str, Any] = fields or {}
        self.search = search

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Query(min_level={self.min_level!r}, "
            f"fields={self.fields!r}, search={self.search!r})"
        )


def _coerce(value: str) -> Any:
    """Try to coerce a string value to int, float, bool, or leave as str."""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def parse_query(query_string: str) -> Query:
    """Parse a query string into a Query object.

    Syntax:
        [level:<MIN_LEVEL>] [field=value ...] [free text search]

    Examples:
        "level:error service=api"
        "level:warn user.id=42 timeout"
        "database connection refused"
    """
    tokens = shlex.split(query_string)
    min_level: Optional[str] = None
    fields: Dict[str, Any] = {}
    search_parts = []

    for token in tokens:
        if token.startswith("level:"):
            min_level = token[len("level:"):]
        else:
            m = _FIELD_RE.match(token)
            if m:
                fields[m.group(1)] = _coerce(m.group(2))
            else:
                search_parts.append(token)

    search = " ".join(search_parts) if search_parts else None
    return Query(min_level=min_level, fields=fields, search=search)
