"""Pipeline: wire together parsing, filtering, and formatting for a stream of log lines."""

from __future__ import annotations

from typing import Iterable, Iterator, Optional

from logslice.filter import matches_record
from logslice.formatter import format_record
from logslice.parser import parse_line
from logslice.query import Query


def process_stream(
    lines: Iterable[str],
    query: Optional[Query] = None,
    output_format: str = "pretty",
) -> Iterator[str]:
    """Parse, filter, and format an iterable of raw log lines.

    Args:
        lines: Raw text lines (e.g. from stdin or a file).
        query: Optional Query object used to filter records.
        output_format: One of ``"pretty"`` or ``"json"``.

    Yields:
        Formatted strings for records that pass the filter.
    """
    for raw in lines:
        record = parse_line(raw)
        if record is None:
            continue
        if query is not None and not matches_record(record, query):
            continue
        yield format_record(record, fmt=output_format)


def process_sources(
    sources: Iterable[Iterable[str]],
    query: Optional[Query] = None,
    output_format: str = "pretty",
) -> Iterator[str]:
    """Process multiple line sources (files, streams) through the same pipeline.

    Records from all sources are interleaved in arrival order.

    Args:
        sources: An iterable of iterables, each yielding raw log lines.
        query: Optional Query object used to filter records.
        output_format: One of ``"pretty"`` or ``"json"``.

    Yields:
        Formatted strings for records that pass the filter.
    """
    for source in sources:
        yield from process_stream(source, query=query, output_format=output_format)


def count_matches(
    lines: Iterable[str],
    query: Optional[Query] = None,
) -> int:
    """Count the number of log records that match the given query.

    Useful for summary reporting without paying the cost of formatting.

    Args:
        lines: Raw text lines (e.g. from stdin or a file).
        query: Optional Query object used to filter records.

    Returns:
        The number of parsed records that pass the filter.
    """
    count = 0
    for raw in lines:
        record = parse_line(raw)
        if record is None:
            continue
        if query is not None and not matches_record(record, query):
            continue
        count += 1
    return count
