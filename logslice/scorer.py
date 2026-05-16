"""Score log records by relevance based on keyword weights."""

from __future__ import annotations

import re
from typing import Dict, Iterable, Iterator, List, Tuple


def _text_of(record: dict) -> str:
    """Return a flat string of all string values in the record."""
    parts: List[str] = []
    for v in record.values():
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, (int, float, bool)):
            parts.append(str(v))
    return " ".join(parts)


def score_record(
    record: dict,
    weights: Dict[str, float],
    *,
    case_sensitive: bool = False,
) -> float:
    """Return a relevance score for *record* given keyword *weights*.

    Each keyword in *weights* is searched in the flattened record text.
    The score is the sum of weight * occurrence_count for every keyword.
    Keywords with negative weights act as penalties.
    """
    text = _text_of(record)
    if not case_sensitive:
        text = text.lower()

    total = 0.0
    for keyword, weight in weights.items():
        needle = keyword if case_sensitive else keyword.lower()
        count = len(re.findall(re.escape(needle), text))
        total += weight * count
    return total


def score_stream(
    records: Iterable[dict],
    weights: Dict[str, float],
    *,
    case_sensitive: bool = False,
    field: str = "_score",
) -> Iterator[dict]:
    """Yield records annotated with a ``_score`` field (or *field*)."""
    for record in records:
        s = score_record(record, weights, case_sensitive=case_sensitive)
        yield {**record, field: s}


def top_records(
    records: Iterable[dict],
    weights: Dict[str, float],
    n: int = 10,
    *,
    case_sensitive: bool = False,
    score_field: str = "_score",
) -> List[Tuple[float, dict]]:
    """Return the top-*n* records by score as ``(score, record)`` pairs."""
    scored = [
        (score_record(r, weights, case_sensitive=case_sensitive), r)
        for r in records
    ]
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[:n]
