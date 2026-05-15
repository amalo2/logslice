"""Pivot log records: group by a field and aggregate a value field."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, Iterator, List, Optional


def _get_field(record: Dict[str, Any], field: str) -> Any:
    return record.get(field)


def pivot_records(
    records: Iterable[Dict[str, Any]],
    row_field: str,
    col_field: str,
    value_field: Optional[str] = None,
    agg: str = "count",
) -> List[Dict[str, Any]]:
    """Pivot records into a table keyed by row_field x col_field.

    agg may be 'count', 'sum', or 'mean'.
    If value_field is None and agg != 'count', raises ValueError.
    Returns a list of dicts, one per unique row_field value.
    """
    if agg != "count" and value_field is None:
        raise ValueError(f"agg={agg!r} requires a value_field")

    # data[row][col] -> list of numeric values (or counts)
    data: Dict[Any, Dict[Any, List[float]]] = defaultdict(lambda: defaultdict(list))
    col_keys: set = set()

    for rec in records:
        row = _get_field(rec, row_field)
        col = _get_field(rec, col_field)
        col_keys.add(col)
        if agg == "count":
            data[row][col].append(1.0)
        else:
            raw = _get_field(rec, value_field)  # type: ignore[arg-type]
            try:
                data[row][col].append(float(raw))
            except (TypeError, ValueError):
                pass

    sorted_cols = sorted(col_keys, key=lambda x: (x is None, x))
    result: List[Dict[str, Any]] = []

    for row_val in sorted(data.keys(), key=lambda x: (x is None, x)):
        row_dict: Dict[str, Any] = {row_field: row_val}
        for col_val in sorted_cols:
            values = data[row_val].get(col_val, [])
            if not values:
                row_dict[str(col_val)] = 0 if agg == "count" else None
            elif agg == "count":
                row_dict[str(col_val)] = int(sum(values))
            elif agg == "sum":
                row_dict[str(col_val)] = sum(values)
            elif agg == "mean":
                row_dict[str(col_val)] = sum(values) / len(values)
        result.append(row_dict)

    return result


def pivot_stream(
    records: Iterable[Dict[str, Any]],
    row_field: str,
    col_field: str,
    value_field: Optional[str] = None,
    agg: str = "count",
) -> Iterator[Dict[str, Any]]:
    """Streaming wrapper — buffers all records then yields pivot rows."""
    yield from pivot_records(
        list(records), row_field, col_field, value_field=value_field, agg=agg
    )
