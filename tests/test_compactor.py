"""Tests for logslice.compactor."""

from __future__ import annotations

import pytest

from logslice.compactor import compact_records, compact_stream


@pytest.fixture()
def records():
    return [
        {"service": "api", "level": "error", "msg": "timeout"},
        {"service": "api", "level": "error", "msg": "timeout"},
        {"service": "api", "level": "warn",  "msg": "retry"},
        {"service": "db",  "level": "info",  "msg": "connected"},
        {"service": "db",  "level": "info",  "msg": "query"},
        {"service": "api", "level": "info",  "msg": "ok"},
    ]


def test_compact_merges_consecutive_same_key(records):
    result = list(compact_records(records, key="service"))
    # api(2), db(2), api(1) → 3 groups
    assert len(result) == 3


def test_compact_count_field_correct(records):
    result = list(compact_records(records, key="service"))
    assert result[0]["_count"] == 2
    assert result[1]["_count"] == 2
    assert result[2]["_count"] == 1


def test_compact_first_record_preserved(records):
    result = list(compact_records(records, key="service"))
    assert result[0]["msg"] == "timeout"
    assert result[1]["msg"] == "connected"


def test_compact_custom_count_field(records):
    result = list(compact_records(records, key="service", count_field="n"))
    assert "n" in result[0]
    assert "_count" not in result[0]


def test_compact_merge_fields_collected(records):
    result = list(compact_records(records, key="service", merge_fields=["msg"]))
    # first api group: timeout appears twice but deduped
    assert result[0]["msg"] == ["timeout"]


def test_compact_merge_fields_multiple_values():
    recs = [
        {"svc": "a", "code": 200},
        {"svc": "a", "code": 404},
        {"svc": "a", "code": 200},
    ]
    result = list(compact_records(recs, key="svc", merge_fields=["code"]))
    assert len(result) == 1
    assert result[0]["code"] == [200, 404]


def test_compact_empty_input():
    assert list(compact_records([], key="service")) == []


def test_compact_single_record():
    rec = {"service": "api", "level": "info"}
    result = list(compact_records([rec], key="service"))
    assert len(result) == 1
    assert result[0]["_count"] == 1


def test_compact_all_different():
    recs = [{"k": i} for i in range(5)]
    result = list(compact_records(recs, key="k"))
    assert len(result) == 5
    assert all(r["_count"] == 1 for r in result)


def test_compact_does_not_mutate_original():
    recs = [{"svc": "a", "v": 1}, {"svc": "a", "v": 2}]
    _ = list(compact_records(recs, key="svc"))
    assert "_count" not in recs[0]


def test_compact_stream_is_equivalent(records):
    a = list(compact_records(records, key="service"))
    b = list(compact_stream(records, key="service"))
    assert a == b


def test_compact_missing_key_treated_as_none():
    recs = [{"x": 1}, {"x": 1}, {"y": 2}]
    result = list(compact_records(recs, key="svc"))
    # all have svc=None → two consecutive None groups then a third None
    assert len(result) == 1
    assert result[0]["_count"] == 3
