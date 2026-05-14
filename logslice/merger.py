"""Merge and interleave log records from multiple sources sorted by timestamp."""

from __future__ import annotations

import heapq
from typing import Iterable, Iterator, List, Optional, Tuple

from logslice.parser import parse_line

_TIMESTAMP_KEYS = ("timestamp", "ts", "time", "@timestamp")


def _extract_ts(record: dict) -> str:
    """Return the first timestamp value found, or empty string for stable sort."""
    for key in _TIMESTAMP_KEYS:
        if key in record:
            return str(record[key])
    return ""


def _tagged_records(
    source: Iterable[str], tag: str
) -> Iterator[Tuple[str, int, dict]]:
    """Yield (timestamp, seq, record) tuples from a line source."""
    for seq, line in enumerate(source):
        record = parse_line(line)
        if record is None:
            continue
        if tag:
            record.setdefault("_source", tag)
        yield (_extract_ts(record), seq, record)


def merge_sources(
    sources: List[Tuple[str, Iterable[str]]],
) -> Iterator[dict]:
    """Merge multiple log sources into a single timestamp-sorted stream.

    Args:
        sources: List of (tag, line_iterable) pairs.

    Yields:
        Log records in ascending timestamp order.  Records without a
        recognisable timestamp are emitted in arrival order relative to
        other timestamp-less records.
    """
    iterators = [
        _tagged_records(lines, tag) for tag, lines in sources
    ]
    for _ts, _seq, record in heapq.merge(*iterators, key=lambda t: (t[0], t[1])):
        yield record


def merge_streams(
    streams: List[Iterable[str]],
    tags: Optional[List[str]] = None,
) -> Iterator[dict]:
    """Convenience wrapper that accepts plain iterables without explicit tags.

    Args:
        streams: Ordered list of line iterables.
        tags:    Optional list of tag strings aligned with *streams*.
                 Defaults to "source_0", "source_1", …

    Yields:
        Merged, sorted log records.
    """
    if tags is None:
        tags = [f"source_{i}" for i in range(len(streams))]
    if len(tags) != len(streams):
        raise ValueError("tags length must match streams length")
    return merge_sources(list(zip(tags, streams)))
