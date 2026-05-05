"""Tests for the logslice CLI entry point."""

import json
import pytest
from unittest.mock import patch, MagicMock

from logslice.cli import build_parser, main


LINES = [
    '{"level": "info", "msg": "started", "service": "api"}\n',
    '{"level": "error", "msg": "boom", "service": "worker"}\n',
    '{"level": "warn", "msg": "slow", "service": "api"}\n',
    'not json at all\n',
]


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

def test_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.format == "pretty"
    assert args.level is None
    assert args.queries == []
    assert args.search is None
    assert not args.count


def test_parser_all_flags():
    parser = build_parser()
    args = parser.parse_args([
        "-l", "warn",
        "-q", "service=api",
        "-s", "slow",
        "-f", "json",
        "--count",
        "app.log",
    ])
    assert args.level == "warn"
    assert args.queries == ["service=api"]
    assert args.search == "slow"
    assert args.format == "json"
    assert args.count is True
    assert args.sources == ["app.log"]


def test_parser_multiple_queries():
    parser = build_parser()
    args = parser.parse_args(["-q", "service=api", "-q", "env=prod"])
    assert args.queries == ["service=api", "env=prod"]


# ---------------------------------------------------------------------------
# main() integration tests (stdin patched)
# ---------------------------------------------------------------------------

def _run_main(argv, stdin_lines):
    """Run main() with patched stdin and capture printed output."""
    printed = []
    mock_stdin = MagicMock()
    mock_stdin.__iter__ = lambda self: iter(stdin_lines)

    with patch("logslice.cli.sys.stdin", mock_stdin):
        with patch("builtins.print", side_effect=lambda x: printed.append(x)):
            rc = main(argv)
    return rc, printed


def test_main_returns_zero():
    rc, _ = _run_main(["-f", "json"], LINES)
    assert rc == 0


def test_main_json_format_valid_json():
    rc, output = _run_main(["-f", "json"], LINES)
    assert rc == 0
    for line in output:
        parsed = json.loads(line)  # must not raise
        assert "level" in parsed


def test_main_level_filter():
    _, output = _run_main(["-f", "json", "-l", "error"], LINES)
    for line in output:
        record = json.loads(line)
        assert record["level"] == "error"


def test_main_count_flag():
    _, output = _run_main(["--count"], LINES)
    assert len(output) == 1
    assert output[0].isdigit()


def test_main_count_with_level():
    _, output = _run_main(["--count", "-l", "error"], LINES)
    assert output[0] == "1"


def test_main_search_filter():
    _, output = _run_main(["-f", "json", "-s", "boom"], LINES)
    assert len(output) == 1
    record = json.loads(output[0])
    assert record["msg"] == "boom"
