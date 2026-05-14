"""Tests for logslice.counter."""

import pytest
from logslice.counter import count_field, count_stream, count_multi_fields


@pytest.fixture()
def records():
    return [
        {"level": "info",  "service": "api"},
        {"level": "error", "service": "api"},
        {"level": "info",  "service": "worker"},
        {"level": "info",  "service": "api"},
        {"level": "warn",  "service": "worker"},
        {"level": "error", "service": "api"},
        {"level": "info",  "service": "api"},
    ]


# --- count_field ---

def test_count_field_returns_sorted_by_frequency(records):
    result = count_field(records, "level")
    values = [v for v, _ in result]
    counts = [c for _, c in result]
    assert values[0] == "info"          # most frequent
    assert counts == sorted(counts, reverse=True)


def test_count_field_correct_totals(records):
    result = dict(count_field(records, "level"))
    assert result["info"] == 4
    assert result["error"] == 2
    assert result["warn"] == 1


def test_count_field_limit_truncates(records):
    result = count_field(records, "level", limit=2)
    assert len(result) == 2


def test_count_field_missing_field_counted_as_none(records):
    result = dict(count_field(records, "nonexistent"))
    assert result[None] == len(records)


def test_count_field_empty_input():
    result = count_field([], "level")
    assert result == []


# --- count_stream ---

def test_count_stream_yields_dicts(records):
    results = list(count_stream(records, "level"))
    assert all(isinstance(r, dict) for r in results)
    assert all("count" in r and "level" in r for r in results)


def test_count_stream_min_count_filters(records):
    results = list(count_stream(records, "level", min_count=2))
    assert all(r["count"] >= 2 for r in results)
    levels = {r["level"] for r in results}
    assert "warn" not in levels


def test_count_stream_limit_respected(records):
    results = list(count_stream(records, "level", limit=1))
    assert len(results) == 1
    assert results[0]["level"] == "info"


def test_count_stream_empty_input():
    assert list(count_stream([], "level")) == []


# --- count_multi_fields ---

def test_count_multi_fields_composite_key(records):
    result = count_multi_fields(records, ["level", "service"])
    result_dict = {k: v for k, v in result}
    assert result_dict[("info", "api")] == 3
    assert result_dict[("error", "api")] == 2


def test_count_multi_fields_limit(records):
    result = count_multi_fields(records, ["level", "service"], limit=2)
    assert len(result) == 2


def test_count_multi_fields_empty_input():
    assert count_multi_fields([], ["level", "service"]) == []
