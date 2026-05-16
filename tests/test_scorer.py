"""Tests for logslice.scorer."""

import pytest
from logslice.scorer import score_record, score_stream, top_records


@pytest.fixture()
def records():
    return [
        {"level": "error", "msg": "disk full", "host": "web-01"},
        {"level": "info", "msg": "user login", "host": "web-02"},
        {"level": "error", "msg": "disk error disk", "host": "db-01"},
        {"level": "warn", "msg": "high memory", "host": "web-01"},
    ]


def test_score_zero_when_no_match():
    record = {"msg": "all good"}
    assert score_record(record, {"error": 1.0}) == 0.0


def test_score_single_keyword_single_hit():
    record = {"msg": "disk full"}
    assert score_record(record, {"disk": 2.0}) == 2.0


def test_score_multiple_occurrences():
    record = {"msg": "disk error disk"}
    assert score_record(record, {"disk": 1.5}) == 3.0


def test_score_multiple_keywords():
    record = {"msg": "disk full", "level": "error"}
    result = score_record(record, {"disk": 1.0, "error": 2.0})
    assert result == 3.0


def test_score_negative_weight_is_penalty():
    record = {"msg": "user login", "level": "info"}
    result = score_record(record, {"login": 1.0, "info": -0.5})
    assert result == 0.5


def test_score_case_insensitive_by_default():
    record = {"msg": "Disk Full"}
    assert score_record(record, {"disk": 1.0}) == 1.0


def test_score_case_sensitive_no_match():
    record = {"msg": "Disk Full"}
    assert score_record(record, {"disk": 1.0}, case_sensitive=True) == 0.0


def test_score_case_sensitive_match():
    record = {"msg": "Disk Full"}
    assert score_record(record, {"Disk": 1.0}, case_sensitive=True) == 1.0


def test_score_ignores_non_string_values_gracefully():
    record = {"count": 5, "active": True, "msg": "ok"}
    # Should not raise; numeric/bool values are stringified
    result = score_record(record, {"5": 1.0})
    assert result == 1.0


def test_score_stream_annotates_field(records):
    weights = {"error": 1.0}
    scored = list(score_stream(records, weights))
    assert all("_score" in r for r in scored)


def test_score_stream_custom_field(records):
    scored = list(score_stream(records, {"disk": 1.0}, field="relevance"))
    assert all("relevance" in r for r in scored)


def test_score_stream_does_not_mutate_originals(records):
    originals = [dict(r) for r in records]
    _ = list(score_stream(records, {"error": 1.0}))
    for orig, rec in zip(originals, records):
        assert "_score" not in rec
        assert rec == orig


def test_top_records_returns_n(records):
    top = top_records(records, {"error": 1.0}, n=2)
    assert len(top) == 2


def test_top_records_ordered_descending(records):
    top = top_records(records, {"disk": 1.0})
    scores = [t[0] for t in top]
    assert scores == sorted(scores, reverse=True)


def test_top_records_highest_score_first(records):
    # "disk error disk" has 2 hits for 'disk'
    top = top_records(records, {"disk": 1.0}, n=1)
    assert top[0][1]["msg"] == "disk error disk"


def test_top_records_n_larger_than_input(records):
    top = top_records(records, {"error": 1.0}, n=100)
    assert len(top) == len(records)
