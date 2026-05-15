"""Tests for logslice.profiler."""

import pytest
from logslice.profiler import profile_stream, coverage_report


@pytest.fixture()
def records():
    return [
        {"level": "info", "msg": "started", "latency": 12},
        {"level": "error", "msg": "failed", "latency": 300, "code": 500},
        {"level": "info", "msg": "done"},
        {"level": "warn", "msg": "slow", "latency": 800},
    ]


def test_total_count(records):
    p = profile_stream(records)
    assert p["total"] == 4


def test_all_fields_present_in_profile(records):
    p = profile_stream(records)
    assert set(p["fields"]) == {"level", "msg", "latency", "code"}


def test_field_count_for_always_present_field(records):
    p = profile_stream(records)
    assert p["fields"]["level"]["count"] == 4
    assert p["fields"]["level"]["missing"] == 0


def test_field_count_for_sparse_field(records):
    p = profile_stream(records)
    assert p["fields"]["code"]["count"] == 1
    assert p["fields"]["code"]["missing"] == 3


def test_type_tracking(records):
    p = profile_stream(records)
    assert p["fields"]["latency"]["types"] == {"int": 3}
    assert p["fields"]["level"]["types"] == {"str": 4}


def test_top_values_for_level(records):
    p = profile_stream(records)
    top = dict(p["fields"]["level"]["top_values"])
    assert top["info"] == 2
    assert top["error"] == 1


def test_empty_stream_returns_zero_total():
    p = profile_stream([])
    assert p["total"] == 0
    assert p["fields"] == {}


def test_coverage_report_sorted_by_rate(records):
    p = profile_stream(records)
    rows = coverage_report(p)
    rates = [r["rate"] for r in rows]
    assert rates == sorted(rates, reverse=True)


def test_coverage_report_rate_values(records):
    p = profile_stream(records)
    rows = coverage_report(p)
    by_field = {r["field"]: r for r in rows}
    assert by_field["level"]["rate"] == 1.0
    assert by_field["code"]["rate"] == 0.25


def test_coverage_report_empty_stream():
    p = profile_stream([])
    rows = coverage_report(p)
    assert rows == []


def test_top_values_capped_at_ten():
    big_records = [{"x": i} for i in range(50)]
    p = profile_stream(big_records)
    assert len(p["fields"]["x"]["top_values"]) <= 10
