"""Stream processing pipeline: parse → filter → format / aggregate."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional

from logslice.parser import parse_line
from logslice.filter import matches_level, matches_fields, matches_search
from logslice.formatter import format_record
from logslice.aggregator import Aggregator
from logslice.query import Query


def _matches(record: Dict[str, Any], query: Optional[Query]) -> bool:
    if query is None:
        return True
    if not matches_level(record, query.level):
        return False
    if query.fields and not matches_fields(record, query.fields):
        return False
    if query.search and not matches_search(record, query.search):
        return False
    return True


def process_stream(
    lines: Iterable[str],
    query: Optional[Query] = None,
    fmt: str = "pretty",
    color: bool = True,
) -> Iterator[str]:
    """Parse and filter lines, yielding formatted output strings."""
    for line in lines:
        record = parse_line(line)
        if record is None:
            continue
        if _matches(record, query):
            yield format_record(record, fmt=fmt, color=color)


def process_sources(
    sources: Iterable[Iterable[str]],
    query: Optional[Query] = None,
    fmt: str = "pretty",
    color: bool = True,
) -> Iterator[str]:
    """Process multiple line sources (e.g. open file handles) in order."""
    for source in sources:
        yield from process_stream(source, query=query, fmt=fmt, color=color)


def count_matches(
    lines: Iterable[str],
    query: Optional[Query] = None,
) -> int:
    """Return the number of records that match the query."""
    total = 0
    for line in lines:
        record = parse_line(line)
        if record is None:
            continue
        if _matches(record, query):
            total += 1
    return total


def aggregate_stream(
    lines: Iterable[str],
    query: Optional[Query] = None,
    group_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Parse, filter, and aggregate a stream of lines into a summary dict."""
    agg = Aggregator(group_by=group_by)
    for line in lines:
        record = parse_line(line)
        if record is None:
            continue
        if _matches(record, query):
            agg.add(record)
    return agg.summary()
