"""Tests for logslice.parser module."""

import pytest
from logslice.parser import parse_line, parse_lines


class TestParseLine:
    def test_pure_json(self):
        line = '{"level": "info", "msg": "started", "pid": 42}'
        result = parse_line(line)
        assert result == {"level": "info", "msg": "started", "pid": 42}

    def test_prefixed_json(self):
        line = '2024-01-15T12:00:00Z INFO {"msg": "hello", "svc": "api"}'
        result = parse_line(line)
        assert result["msg"] == "hello"
        assert result["svc"] == "api"
        assert result["timestamp"] == "2024-01-15T12:00:00Z"
        assert result["level"] == "info"

    def test_prefixed_json_does_not_overwrite_existing_level(self):
        line = '2024-01-15T12:00:00Z WARN {"level": "warning", "msg": "oops"}'
        result = parse_line(line)
        # JSON-embedded level takes precedence via setdefault
        assert result["level"] == "warning"

    def test_empty_line_returns_none(self):
        assert parse_line("") is None
        assert parse_line("   ") is None

    def test_plain_text_returns_none(self):
        assert parse_line("this is not json") is None

    def test_invalid_json_returns_none(self):
        assert parse_line("{bad json}") is None

    def test_prefixed_invalid_json_returns_none(self):
        line = "2024-01-15T12:00:00Z ERROR {bad}"
        assert parse_line(line) is None

    def test_whitespace_stripped(self):
        line = '  {"level": "debug", "msg": "trace"}  '
        result = parse_line(line)
        assert result["level"] == "debug"


class TestParseLines:
    def test_filters_unparseable(self):
        lines = [
            '{"level": "info", "msg": "ok"}',
            "not json at all",
            '{"level": "error", "msg": "fail"}',
        ]
        results = parse_lines(lines)
        assert len(results) == 2
        assert results[0]["msg"] == "ok"
        assert results[1]["msg"] == "fail"

    def test_empty_input(self):
        assert parse_lines([]) == []

    def test_all_invalid(self):
        assert parse_lines(["garbage", "more garbage", ""]) == []
