"""Tests for logslice.formatter."""

import json
import pytest
from logslice.formatter import format_json, format_pretty, format_record, _format_timestamp


@pytest.fixture
def basic_record():
    return {"level": "info", "message": "hello world", "timestamp": "2024-01-15T10:00:00Z"}


@pytest.fixture
def record_with_extras():
    return {"level": "error", "message": "something failed", "service": "api", "code": 500}


def test_format_json_is_valid_json(basic_record):
    result = format_json(basic_record)
    parsed = json.loads(result)
    assert parsed["level"] == "info"
    assert parsed["message"] == "hello world"


def test_format_json_compact(basic_record):
    result = format_json(basic_record)
    assert "\n" not in result


def test_format_pretty_contains_level(basic_record):
    result = format_pretty(basic_record, color=False)
    assert "INFO" in result


def test_format_pretty_contains_message(basic_record):
    result = format_pretty(basic_record, color=False)
    assert "hello world" in result


def test_format_pretty_contains_timestamp(basic_record):
    result = format_pretty(basic_record, color=False)
    assert "2024-01-15T10:00:00Z" in result


def test_format_pretty_includes_extras(record_with_extras):
    result = format_pretty(record_with_extras, color=False)
    assert "service" in result
    assert "api" in result
    assert "code" in result


def test_format_pretty_skips_known_keys(basic_record):
    result = format_pretty(basic_record, color=False)
    # 'level' and 'message' should not appear as extra key=value pairs
    assert "level=" not in result
    assert "message=" not in result


def test_format_pretty_with_color_contains_ansi(basic_record):
    result = format_pretty(basic_record, color=True)
    assert "\033[" in result


def test_format_pretty_no_color_no_ansi(basic_record):
    result = format_pretty(basic_record, color=False)
    assert "\033[" not in result


def test_format_record_dispatches_json(basic_record):
    result = format_record(basic_record, fmt="json")
    parsed = json.loads(result)
    assert parsed["message"] == "hello world"


def test_format_record_dispatches_pretty(basic_record):
    result = format_record(basic_record, fmt="pretty", color=False)
    assert "INFO" in result
    assert "hello world" in result


def test_format_timestamp_unix_float():
    record = {"ts": 1705312800.0}
    ts = _format_timestamp(record)
    assert ts is not None
    assert "2024" in ts


def test_format_timestamp_missing_returns_none():
    record = {"level": "info", "message": "no time"}
    assert _format_timestamp(record) is None


def test_format_pretty_unknown_level_no_crash():
    record = {"level": "verbose", "message": "test"}
    result = format_pretty(record, color=True)
    assert "VERBOSE" in result
