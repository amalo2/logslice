"""Record sampling utilities for logslice.

Provides deterministic and rate-based sampling so large log streams
can be reduced to a representative subset before display or export.
"""

from __future__ import annotations

import hashlib
import math
from typing import Iterable, Iterator


def _record_hash(record: dict) -> int:
    """Return a stable integer hash derived from the record's content."""
    key = str(sorted(record.items())).encode()
    digest = hashlib.md5(key, usedforsecurity=False).hexdigest()
    return int(digest, 16)


def sample_records(
    records: Iterable[dict],
    rate: float,
    *,
    deterministic: bool = True,
) -> Iterator[dict]:
    """Yield a sampled subset of *records*.

    Parameters
    ----------
    records:
        Source iterable of parsed log records.
    rate:
        Fraction of records to keep, in the range (0.0, 1.0].
        A value of 1.0 keeps every record; 0.1 keeps roughly 10 %.
    deterministic:
        When *True* (default) the same record always produces the same
        keep/skip decision based on a hash of its content.  When *False*
        a simple counter-based round-robin is used instead.

    Raises
    ------
    ValueError
        If *rate* is not in the range (0.0, 1.0].
    """
    if not (0.0 < rate <= 1.0):
        raise ValueError(f"rate must be in (0.0, 1.0], got {rate!r}")

    if math.isclose(rate, 1.0):
        yield from records
        return

    if deterministic:
        threshold = int(rate * (2 ** 128))
        for record in records:
            if _record_hash(record) < threshold:
                yield record
    else:
        step = 1.0 / rate
        bucket = 0.0
        for record in records:
            bucket += 1.0
            if bucket >= step:
                bucket -= step
                yield record


def reservoir_sample(records: Iterable[dict], k: int) -> list[dict]:
    """Return exactly *k* records chosen via reservoir sampling.

    If fewer than *k* records exist the entire stream is returned.

    Parameters
    ----------
    records:
        Source iterable of parsed log records.
    k:
        Maximum number of records to return.

    Raises
    ------
    ValueError
        If *k* is not a positive integer.
    """
    if k <= 0:
        raise ValueError(f"k must be a positive integer, got {k!r}")

    import random

    reservoir: list[dict] = []
    for i, record in enumerate(records):
        if i < k:
            reservoir.append(record)
        else:
            j = random.randint(0, i)
            if j < k:
                reservoir[j] = record
    return reservoir
