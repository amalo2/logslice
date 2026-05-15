"""Integration tests combining sorter with parser and filter modules."""

import json

from logslice.parser import parse_lines
from logslice.sorter import sort_records, sort_stream
from logslice.filter import matches_level


def _make_record(ts, level, msg):
    return {"timestamp": ts, "level": level, "msg": msg}


def _raw_lines(*records):
    return [json.dumps(r) for r in records]


def test_sort_parsed_stream_by_timestamp():
    lines = _raw_lines(
        _make_record(30, "info", "third"),
        _make_record(10, "error", "first"),
        _make_record(20, "warn", "second"),
    )
    records = list(parse_lines(iter(lines)))
    sorted_recs = sort_records(records, ["timestamp"])
    assert [r["timestamp"] for r in sorted_recs] == [10, 20, 30]


def test_sort_then_filter_preserves_order():
    lines = _raw_lines(
        _make_record(3, "info", "c"),
        _make_record(1, "error", "a"),
        _make_record(2, "info", "b"),
    )
    records = list(parse_lines(iter(lines)))
    sorted_recs = sort_records(records, ["timestamp"])
    info_only = [r for r in sorted_recs if matches_level(r, "info")]
    assert [r["timestamp"] for r in info_only] == [2, 3]


def test_sort_stream_limit_top_n():
    records = [{"ts": i} for i in range(10, 0, -1)]
    top3 = list(sort_stream(records, ["ts"], limit=3))
    assert len(top3) == 3
    assert top3[0]["ts"] == 1


def test_sort_stable_on_equal_keys():
    """Records with equal sort keys should maintain relative insertion order."""
    records = [
        {"ts": 1, "seq": 0},
        {"ts": 1, "seq": 1},
        {"ts": 1, "seq": 2},
    ]
    result = sort_records(records, ["ts"])
    # Python sort is stable, so seq order must be preserved
    assert [r["seq"] for r in result] == [0, 1, 2]


def test_sort_by_level_string():
    records = [
        {"level": "warn"},
        {"level": "debug"},
        {"level": "info"},
        {"level": "error"},
    ]
    result = sort_records(records, ["level"])
    levels = [r["level"] for r in result]
    assert levels == sorted(["warn", "debug", "info", "error"])
