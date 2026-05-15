"""Integration tests for logslice.cli_sort."""

import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from logslice.cli_sort import build_sort_parser, run_sort


def _make_lines(*records):
    return [json.dumps(r) for r in records]


def _run(args_list, lines):
    parser = build_sort_parser()
    args = parser.parse_args(args_list)
    captured = StringIO()
    with patch("logslice.cli_sort._iter_lines", return_value=iter(lines)), \
         patch("sys.stdout", captured):
        rc = run_sort(args)
    return rc, captured.getvalue()


def test_parser_requires_at_least_one_field():
    parser = build_sort_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_parser_defaults():
    parser = build_sort_parser()
    args = parser.parse_args(["ts"])
    assert args.fields == ["ts"]
    assert args.desc is False
    assert args.limit is None
    assert args.input == "-"


def test_run_sort_ascending():
    lines = _make_lines(
        {"ts": 3, "msg": "c"},
        {"ts": 1, "msg": "a"},
        {"ts": 2, "msg": "b"},
    )
    rc, out = _run(["ts"], lines)
    assert rc == 0
    results = [json.loads(l) for l in out.strip().splitlines()]
    assert [r["ts"] for r in results] == [1, 2, 3]


def test_run_sort_descending():
    lines = _make_lines(
        {"ts": 1},
        {"ts": 3},
        {"ts": 2},
    )
    rc, out = _run(["ts", "--desc"], lines)
    assert rc == 0
    results = [json.loads(l) for l in out.strip().splitlines()]
    assert [r["ts"] for r in results] == [3, 2, 1]


def test_run_sort_with_limit():
    lines = _make_lines(
        {"ts": 3},
        {"ts": 1},
        {"ts": 2},
    )
    rc, out = _run(["ts", "--limit", "2"], lines)
    assert rc == 0
    results = [json.loads(l) for l in out.strip().splitlines()]
    assert len(results) == 2
    assert results[0]["ts"] == 1


def test_run_sort_skips_garbage():
    lines = ["not json", json.dumps({"ts": 1}), "also bad"]
    rc, out = _run(["ts"], lines)
    assert rc == 0
    results = [json.loads(l) for l in out.strip().splitlines()]
    assert len(results) == 1


def test_run_sort_empty_input():
    rc, out = _run(["ts"], [])
    assert rc == 0
    assert out.strip() == ""


def test_run_sort_output_is_valid_json():
    lines = _make_lines({"ts": 2, "level": "info"}, {"ts": 1, "level": "error"})
    rc, out = _run(["ts"], lines)
    for line in out.strip().splitlines():
        json.loads(line)  # must not raise
