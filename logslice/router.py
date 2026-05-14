"""
logslice.router
~~~~~~~~~~~~~~~
Route log records to different outputs based on field-matching rules.

Each rule maps a field condition to a named destination label.
The first matching rule wins; unmatched records go to the default
destination ("default").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple


@dataclass
class RoutingRule:
    """A single field == value routing rule."""
    field: str
    value: Any
    destination: str


@dataclass
class Router:
    rules: List[RoutingRule] = field(default_factory=list)
    default_destination: str = "default"

    def add_rule(self, field_name: str, value: Any, destination: str) -> None:
        """Append a routing rule."""
        self.rules.append(RoutingRule(field=field_name, value=value, destination=destination))

    def route(self, record: Dict[str, Any]) -> str:
        """Return the destination label for *record*."""
        for rule in self.rules:
            if record.get(rule.field) == rule.value:
                return rule.destination
        return self.default_destination


def build_router(rules: List[Tuple[str, Any, str]], default: str = "default") -> Router:
    """Convenience factory: build a Router from a list of (field, value, dest) tuples."""
    router = Router(default_destination=default)
    for field_name, value, destination in rules:
        router.add_rule(field_name, value, destination)
    return router


def route_records(
    records: Iterable[Dict[str, Any]],
    router: Router,
) -> Iterator[Tuple[str, Dict[str, Any]]]:
    """Yield (destination, record) pairs for each record."""
    for record in records:
        yield router.route(record), record


def group_by_destination(
    records: Iterable[Dict[str, Any]],
    router: Router,
) -> Dict[str, List[Dict[str, Any]]]:
    """Partition *records* into a dict keyed by destination label."""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for destination, record in route_records(records, router):
        groups.setdefault(destination, []).append(record)
    return groups
