"""Field-value frequency counter for structured log records."""

from collections import Counter
from typing import Iterable, Iterator, Optional


def _get_field(record: dict, field: str):
    """Return the value of *field* from *record*, or None if absent."""
    return record.get(field)


def count_field(
    records: Iterable[dict],
    field: str,
    limit: Optional[int] = None,
) -> list[tuple]:
    """Count occurrences of each distinct value for *field*.

    Returns a list of (value, count) pairs sorted by count descending.
    If *limit* is given, only the top *limit* entries are returned.
    """
    counter: Counter = Counter()
    for record in records:
        value = _get_field(record, field)
        counter[value] += 1
    ranked = counter.most_common(limit)
    return ranked


def count_stream(
    records: Iterable[dict],
    field: str,
    limit: Optional[int] = None,
    min_count: int = 1,
) -> Iterator[dict]:
    """Yield summary dicts ``{field: value, 'count': n}`` for each distinct
    value observed in *records*, ordered by frequency descending.

    *min_count* filters out values that appear fewer times than the threshold.
    """
    ranked = count_field(records, field, limit=limit)
    for value, n in ranked:
        if n < min_count:
            continue
        yield {field: value, "count": n}


def count_multi_fields(
    records: Iterable[dict],
    fields: list[str],
    limit: Optional[int] = None,
) -> list[tuple]:
    """Count co-occurrences of a tuple of field values.

    Returns a list of (tuple_of_values, count) pairs sorted by count descending.
    """
    counter: Counter = Counter()
    for record in records:
        key = tuple(_get_field(record, f) for f in fields)
        counter[key] += 1
    return counter.most_common(limit)
