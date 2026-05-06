"""Tests for logslice.report."""
import json
import pytest
from logslice.report import (
    format_summary_pretty,
    format_summary_json,
    format_summary,
    _bar,
)


@pytest.fixture()
def basic_summary():
    return {
        "total": 10,
        "by_level": {
            "debug": 1,
            "info": 5,
            "warning": 2,
            "error": 2,
            "critical": 0,
        },
    }


@pytest.fixture()
def grouped_summary(basic_summary):
    s = dict(basic_summary)
    s["by_group"] = {
        "field": "service",
        "counts": {"api": 7, "worker": 3},
    }
    return s


def test_bar_full():
    assert _bar(10, 10, 10) == "[##########]"


def test_bar_empty():
    assert _bar(0, 10, 10) == "[----------]"


def test_bar_zero_total():
    assert _bar(0, 0, 10) == "[----------]"


def test_pretty_contains_total(basic_summary):
    out = format_summary_pretty(basic_summary, color=False)
    assert "Total records : 10" in out


def test_pretty_contains_level_names(basic_summary):
    out = format_summary_pretty(basic_summary, color=False)
    for lvl in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        assert lvl in out


def test_pretty_contains_counts(basic_summary):
    out = format_summary_pretty(basic_summary, color=False)
    assert " 5" in out
    assert " 2" in out


def test_pretty_with_group(grouped_summary):
    out = format_summary_pretty(grouped_summary, color=False)
    assert "service" in out
    assert "api" in out
    assert "worker" in out


def test_json_is_valid(basic_summary):
    out = format_summary_json(basic_summary)
    parsed = json.loads(out)
    assert parsed["total"] == 10


def test_json_compact(basic_summary):
    out = format_summary_json(basic_summary)
    assert "\n" not in out


def test_format_summary_dispatches_json(basic_summary):
    out = format_summary(basic_summary, fmt="json")
    assert json.loads(out)["total"] == 10


def test_format_summary_dispatches_pretty(basic_summary):
    out = format_summary(basic_summary, fmt="pretty", color=False)
    assert "Total records" in out


def test_color_codes_present_by_default(basic_summary):
    out = format_summary_pretty(basic_summary, color=True)
    assert "\033[" in out


def test_no_color_codes_when_disabled(basic_summary):
    out = format_summary_pretty(basic_summary, color=False)
    assert "\033[" not in out
