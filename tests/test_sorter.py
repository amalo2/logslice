"""Tests for logslice.sorter."""

import pytest
from logslice.sorter import sort_records, sort_stream, _sort_key


@pytest.fixture()
def records():
    return [
        {"level": "error", "ts": 3, "msg": "c"},
        {"level": "info",  "ts": 1, "msg": "a"},
        {"level": "warn",  "ts": 2, "msg": "b"},
    ]


def test_sort_records_by_single_field(records):
    result = sort_records(records, ["ts"])
    assert [r["ts"] for r in result] == [1, 2, 3]


def test_sort_records_descending(records):
    result = sort_records(records, ["ts"], reverse=True)
    assert [r["ts"] for r in result] == [3, 2, 1]


def test_sort_records_by_string_field(records):
    result = sort_records(records, ["msg"])
    assert [r["msg"] for r in result] == ["a", "b", "c"]


def test_sort_records_no_fields_returns_original_order(records):
    result = sort_records(records, [])
    assert result == records


def test_sort_records_missing_field_sorts_first():
    recs = [
        {"ts": 5},
        {"ts": 1},
        {},           # missing 'ts'
    ]
    result = sort_records(recs, ["ts"])
    assert result[0] == {}  # None sorts first
    assert result[1]["ts"] == 1
    assert result[2]["ts"] == 5


def test_sort_records_multi_field_tiebreak():
    recs = [
        {"level": "info", "ts": 2},
        {"level": "info", "ts": 1},
        {"level": "error", "ts": 3},
    ]
    result = sort_records(recs, ["level", "ts"])
    levels = [r["level"] for r in result]
    assert levels[0] == "error"
    assert levels[1] == "info"
    assert levels[2] == "info"
    # within same level, ts should be ascending
    info_records = [r for r in result if r["level"] == "info"]
    assert info_records[0]["ts"] == 1


def test_sort_records_does_not_mutate_input(records):
    original_ids = [id(r) for r in records]
    sort_records(records, ["ts"])
    assert [id(r) for r in records] == original_ids


def test_sort_stream_yields_sorted(records):
    result = list(sort_stream(records, ["ts"]))
    assert [r["ts"] for r in result] == [1, 2, 3]


def test_sort_stream_limit_truncates(records):
    result = list(sort_stream(records, ["ts"], limit=2))
    assert len(result) == 2
    assert result[0]["ts"] == 1
    assert result[1]["ts"] == 2


def test_sort_stream_reverse_with_limit(records):
    result = list(sort_stream(records, ["ts"], reverse=True, limit=1))
    assert len(result) == 1
    assert result[0]["ts"] == 3


def test_sort_stream_empty_input():
    result = list(sort_stream([], ["ts"]))
    assert result == []
