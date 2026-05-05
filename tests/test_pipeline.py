"""Tests for logslice.pipeline."""

from __future__ import annotations

import json

import pytest

from logslice.pipeline import process_sources, process_stream
from logslice.query import parse_query


INFO_LINE = json.dumps({"level": "info", "message": "server started", "port": 8080})
ERROR_LINE = json.dumps({"level": "error", "message": "connection refused", "code": 111})
DEBUG_LINE = json.dumps({"level": "debug", "message": "heartbeat"})
GARBAGE_LINE = "not json at all"


@pytest.fixture()
def mixed_lines():
    return [INFO_LINE, ERROR_LINE, DEBUG_LINE, GARBAGE_LINE]


def test_process_stream_no_filter_skips_garbage(mixed_lines):
    results = list(process_stream(mixed_lines))
    # garbage line is dropped; 3 valid JSON records remain
    assert len(results) == 3


def test_process_stream_filters_by_level(mixed_lines):
    query = parse_query("level=error")
    results = list(process_stream(mixed_lines, query=query))
    assert len(results) == 1
    assert "error" in results[0].lower() or "connection refused" in results[0]


def test_process_stream_json_output_is_valid(mixed_lines):
    results = list(process_stream(mixed_lines, output_format="json"))
    for r in results:
        parsed = json.loads(r)  # must not raise
        assert isinstance(parsed, dict)


def test_process_stream_pretty_output_is_string(mixed_lines):
    results = list(process_stream(mixed_lines, output_format="pretty"))
    for r in results:
        assert isinstance(r, str)
        assert len(r) > 0


def test_process_stream_empty_input():
    results = list(process_stream([]))
    assert results == []


def test_process_stream_all_garbage():
    results = list(process_stream(["nope", "still nope", ""]))
    assert results == []


def test_process_sources_combines_multiple_streams():
    source_a = [INFO_LINE]
    source_b = [ERROR_LINE, DEBUG_LINE]
    results = list(process_sources([source_a, source_b]))
    assert len(results) == 3


def test_process_sources_filter_applies_across_sources():
    source_a = [INFO_LINE]
    source_b = [ERROR_LINE]
    query = parse_query("level=info")
    results = list(process_sources([source_a, source_b], query=query))
    assert len(results) == 1


def test_process_sources_empty_sources():
    results = list(process_sources([]))
    assert results == []


def test_process_stream_search_filter(mixed_lines):
    query = parse_query('"heartbeat"')
    results = list(process_stream(mixed_lines, query=query))
    assert len(results) == 1
