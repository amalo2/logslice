"""Tests for logslice.merger."""

import json
import pytest

from logslice.merger import merge_sources, merge_streams


def _line(ts: str, msg: str, level: str = "info") -> str:
    return json.dumps({"timestamp": ts, "message": msg, "level": level})


def _line_no_ts(msg: str) -> str:
    return json.dumps({"message": msg, "level": "debug"})


# ---------------------------------------------------------------------------
# merge_sources
# ---------------------------------------------------------------------------

def test_merge_sources_empty_yields_nothing():
    result = list(merge_sources([]))
    assert result == []


def test_merge_sources_single_stream_passthrough():
    lines = [_line("2024-01-01T00:00:01Z", "a"), _line("2024-01-01T00:00:02Z", "b")]
    result = list(merge_sources([("svc", iter(lines))]))
    assert [r["message"] for r in result] == ["a", "b"]


def test_merge_sources_interleaves_by_timestamp():
    stream_a = [
        _line("2024-01-01T00:00:01Z", "a1"),
        _line("2024-01-01T00:00:03Z", "a2"),
    ]
    stream_b = [
        _line("2024-01-01T00:00:02Z", "b1"),
        _line("2024-01-01T00:00:04Z", "b2"),
    ]
    result = list(merge_sources([("A", iter(stream_a)), ("B", iter(stream_b))]))
    assert [r["message"] for r in result] == ["a1", "b1", "a2", "b2"]


def test_merge_sources_tags_records():
    lines = [_line("2024-01-01T00:00:01Z", "x")]
    result = list(merge_sources([("my-service", iter(lines))]))
    assert result[0]["_source"] == "my-service"


def test_merge_sources_does_not_overwrite_existing_source_tag():
    record = {"timestamp": "2024-01-01T00:00:01Z", "message": "x", "_source": "original"}
    lines = [json.dumps(record)]
    result = list(merge_sources([("new-tag", iter(lines))]))
    assert result[0]["_source"] == "original"


def test_merge_sources_skips_garbage_lines():
    lines = ["not json", _line("2024-01-01T00:00:01Z", "valid"), "also garbage"]
    result = list(merge_sources([("svc", iter(lines))]))
    assert len(result) == 1
    assert result[0]["message"] == "valid"


def test_merge_sources_records_without_timestamp_are_included():
    lines = [_line_no_ts("no-ts"), _line("2024-01-01T00:00:01Z", "with-ts")]
    result = list(merge_sources([("svc", iter(lines))]))
    messages = {r["message"] for r in result}
    assert messages == {"no-ts", "with-ts"}


# ---------------------------------------------------------------------------
# merge_streams
# ---------------------------------------------------------------------------

def test_merge_streams_default_tags():
    stream_a = [_line("2024-01-01T00:00:01Z", "a")]
    stream_b = [_line("2024-01-01T00:00:02Z", "b")]
    result = list(merge_streams([iter(stream_a), iter(stream_b)]))
    sources = {r["_source"] for r in result}
    assert sources == {"source_0", "source_1"}


def test_merge_streams_custom_tags():
    stream_a = [_line("2024-01-01T00:00:01Z", "a")]
    result = list(merge_streams([iter(stream_a)], tags=["alpha"]))
    assert result[0]["_source"] == "alpha"


def test_merge_streams_mismatched_tags_raises():
    with pytest.raises(ValueError, match="tags length"):
        list(merge_streams([iter([]), iter([])], tags=["only-one"]))


def test_merge_streams_empty_inputs():
    result = list(merge_streams([iter([]), iter([])]))
    assert result == []
