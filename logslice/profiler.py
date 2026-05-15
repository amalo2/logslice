"""Profile a stream of log records: measure field coverage, value distributions, and type consistency."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    return type(value).__name__


def profile_stream(records: Iterable[dict]) -> dict:
    """Analyse records and return a profile dict.

    Returns:
        {
          "total": int,
          "fields": {
            "<field>": {
              "count": int,          # records where field is present
              "missing": int,        # records where field is absent
              "types": {<type>: int},
              "top_values": [[value, count], ...],  # up to 10 most common
            }
          }
        }
    """
    total = 0
    field_counts: Dict[str, int] = defaultdict(int)
    field_types: Dict[str, Counter] = defaultdict(Counter)
    field_values: Dict[str, Counter] = defaultdict(Counter)

    for record in records:
        total += 1
        for key, value in record.items():
            field_counts[key] += 1
            field_types[key][_type_name(value)] += 1
            # only track value distribution for scalars
            if isinstance(value, (str, int, float, bool)) or value is None:
                field_values[key][str(value)] += 1

    all_fields = set(field_counts)
    fields: Dict[str, dict] = {}
    for field in sorted(all_fields):
        count = field_counts[field]
        top = field_values[field].most_common(10)
        fields[field] = {
            "count": count,
            "missing": total - count,
            "types": dict(field_types[field]),
            "top_values": [[v, c] for v, c in top],
        }

    return {"total": total, "fields": fields}


def coverage_report(profile: dict) -> List[dict]:
    """Return a list of field coverage dicts sorted by presence rate descending."""
    total = profile["total"]
    rows = []
    for field, info in profile["fields"].items():
        rate = (info["count"] / total) if total else 0.0
        rows.append({"field": field, "count": info["count"], "missing": info["missing"], "rate": round(rate, 4)})
    rows.sort(key=lambda r: r["rate"], reverse=True)
    return rows
