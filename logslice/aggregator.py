"""Aggregation utilities for summarising log streams."""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional


LEVEL_ORDER = ["debug", "info", "warning", "error", "critical"]


class Aggregator:
    """Collects records and produces summary statistics."""

    def __init__(self, group_by: Optional[str] = None) -> None:
        self.group_by = group_by
        self._total = 0
        self._level_counts: Counter = Counter()
        self._group_counts: Counter = Counter()
        self._field_values: Dict[str, Counter] = defaultdict(Counter)

    def add(self, record: Dict[str, Any]) -> None:
        """Ingest a single parsed log record."""
        self._total += 1
        level = str(record.get("level", "unknown")).lower()
        self._level_counts[level] += 1

        if self.group_by:
            key = record.get(self.group_by, "<missing>")
            self._group_counts[str(key)] += 1

    def summary(self) -> Dict[str, Any]:
        """Return a dict summarising all ingested records."""
        result: Dict[str, Any] = {
            "total": self._total,
            "by_level": {
                lvl: self._level_counts.get(lvl, 0) for lvl in LEVEL_ORDER
            },
        }
        unknown = {k: v for k, v in self._level_counts.items() if k not in LEVEL_ORDER}
        if unknown:
            result["by_level"]["unknown"] = sum(unknown.values())

        if self.group_by:
            result["by_group"] = {
                "field": self.group_by,
                "counts": dict(self._group_counts.most_common()),
            }
        return result

    def top_groups(self, n: int = 5) -> List[tuple]:
        """Return the top-n groups by record count."""
        return self._group_counts.most_common(n)


def aggregate_records(
    records: Iterable[Dict[str, Any]],
    group_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience wrapper: aggregate an iterable of records and return summary."""
    agg = Aggregator(group_by=group_by)
    for rec in records:
        agg.add(rec)
    return agg.summary()
