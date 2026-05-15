"""Join records from two streams on a shared key field."""
from __future__ import annotations

from typing import Dict, Iterable, Iterator, List, Optional


def _index_records(
    records: Iterable[dict],
    key: str,
) -> Dict[str, List[dict]]:
    """Build an index mapping key values to lists of matching records."""
    index: Dict[str, List[dict]] = {}
    for rec in records:
        val = rec.get(key)
        if val is None:
            continue
        k = str(val)
        index.setdefault(k, []).append(rec)
    return index


def inner_join(
    left: Iterable[dict],
    right: Iterable[dict],
    key: str,
    prefix_left: str = "left_",
    prefix_right: str = "right_",
) -> Iterator[dict]:
    """Yield merged records where *key* exists in both streams."""
    right_index = _index_records(right, key)
    for rec in left:
        val = rec.get(key)
        if val is None:
            continue
        k = str(val)
        for right_rec in right_index.get(k, []):
            merged: dict = {}
            for field, value in rec.items():
                merged[field if field == key else f"{prefix_left}{field}"] = value
            for field, value in right_rec.items():
                if field != key:
                    merged[f"{prefix_right}{field}"] = value
            yield merged


def left_join(
    left: Iterable[dict],
    right: Iterable[dict],
    key: str,
    prefix_left: str = "left_",
    prefix_right: str = "right_",
) -> Iterator[dict]:
    """Yield all left records, enriched with matching right records when found."""
    right_index = _index_records(right, key)
    for rec in left:
        val = rec.get(key)
        k = str(val) if val is not None else None
        matches: List[dict] = right_index.get(k, [{}]) if k else [{}]
        for right_rec in matches:
            merged: dict = {}
            for field, value in rec.items():
                merged[field if field == key else f"{prefix_left}{field}"] = value
            for field, value in right_rec.items():
                if field != key:
                    merged[f"{prefix_right}{field}"] = value
            yield merged


def join_streams(
    left: Iterable[dict],
    right: Iterable[dict],
    key: str,
    how: str = "inner",
    prefix_left: str = "left_",
    prefix_right: str = "right_",
) -> Iterator[dict]:
    """Dispatch to the appropriate join strategy."""
    if how == "inner":
        yield from inner_join(left, right, key, prefix_left, prefix_right)
    elif how == "left":
        yield from left_join(left, right, key, prefix_left, prefix_right)
    else:
        raise ValueError(f"Unsupported join type: {how!r}. Use 'inner' or 'left'.")
