"""Tests for logslice.scoper."""
import json
import pytest
from logslice.scoper import _extract_ts, scope_records, scope_stream


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def records():
    return [
        {"timestamp": 1000.0, "level": "info",  "msg": "early"},
        {"timestamp": 2000.0, "level": "warn",  "msg": "middle"},
        {"timestamp": 3000.0, "level": "error", "msg": "late"},
    ]


# ---------------------------------------------------------------------------
# _extract_ts
# ---------------------------------------------------------------------------

def test_extract_ts_from_timestamp_key():
    assert _extract_ts({"timestamp": 1234.5}) == 1234.5

def test_extract_ts_from_ts_key():
    assert _extract_ts({"ts": "9999"}) == 9999.0

def test_extract_ts_from_time_key():
    assert _extract_ts({"time": 500}) == 500.0

def test_extract_ts_returns_none_when_missing():
    assert _extract_ts({"msg": "no ts here"}) is None

def test_extract_ts_returns_none_for_non_numeric():
    assert _extract_ts({"timestamp": "not-a-number"}) is None


# ---------------------------------------------------------------------------
# scope_records
# ---------------------------------------------------------------------------

def test_scope_records_no_bounds_returns_all(records):
    result = list(scope_records(records))
    assert len(result) == 3

def test_scope_records_since_filters_early(records):
    result = list(scope_records(records, since=1500.0))
    assert all(r["timestamp"] >= 1500.0 for r in result)
    assert len(result) == 2

def test_scope_records_until_filters_late(records):
    result = list(scope_records(records, until=2500.0))
    assert all(r["timestamp"] <= 2500.0 for r in result)
    assert len(result) == 2

def test_scope_records_since_and_until_exact_bounds(records):
    result = list(scope_records(records, since=1000.0, until=2000.0))
    assert len(result) == 2
    assert result[0]["msg"] == "early"
    assert result[1]["msg"] == "middle"

def test_scope_records_since_and_until_narrow_window(records):
    result = list(scope_records(records, since=1500.0, until=2500.0))
    assert len(result) == 1
    assert result[0]["msg"] == "middle"

def test_scope_records_no_match_returns_empty(records):
    result = list(scope_records(records, since=9000.0))
    assert result == []

def test_scope_records_missing_ts_passed_through_by_default():
    recs = [{"msg": "no ts"}, {"timestamp": 1000.0, "msg": "has ts"}]
    result = list(scope_records(recs, since=500.0))
    assert len(result) == 2

def test_scope_records_missing_ts_dropped_when_requested():
    recs = [{"msg": "no ts"}, {"timestamp": 1000.0, "msg": "has ts"}]
    result = list(scope_records(recs, since=500.0, drop_missing=True))
    assert len(result) == 1
    assert result[0]["msg"] == "has ts"


# ---------------------------------------------------------------------------
# scope_stream
# ---------------------------------------------------------------------------

def test_scope_stream_parses_and_filters():
    lines = [
        json.dumps({"ts": 100, "msg": "a"}),
        json.dumps({"ts": 200, "msg": "b"}),
        json.dumps({"ts": 300, "msg": "c"}),
    ]
    result = list(scope_stream(lines, since=150.0, until=250.0))
    assert len(result) == 1
    assert result[0]["msg"] == "b"

def test_scope_stream_skips_invalid_json():
    lines = ["not json", json.dumps({"ts": 500, "msg": "ok"})]
    result = list(scope_stream(lines, since=0.0))
    assert len(result) == 1

def test_scope_stream_skips_empty_lines():
    lines = ["", "   ", json.dumps({"ts": 1, "msg": "x"})]
    result = list(scope_stream(lines))
    assert len(result) == 1
