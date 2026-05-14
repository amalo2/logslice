"""
Tests for logslice.cli_route
"""
import json
import os
import textwrap
from io import StringIO

import pytest

from logslice.cli_route import build_route_parser, _parse_rules, run_route


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_stream(*dicts):
    return StringIO("".join(json.dumps(d) + "\n" for d in dicts))


# ---------------------------------------------------------------------------
# _parse_rules
# ---------------------------------------------------------------------------

def test_parse_rules_single():
    result = _parse_rules(["level=error:errors.jsonl"])
    assert result == [("level", "error", "errors.jsonl")]


def test_parse_rules_multiple():
    result = _parse_rules(["level=error:err.jsonl", "service=auth:auth.jsonl"])
    assert len(result) == 2
    assert result[1] == ("service", "auth", "auth.jsonl")


def test_parse_rules_invalid_raises():
    with pytest.raises(SystemExit):
        _parse_rules(["no-colon-here"])


def test_parse_rules_empty():
    assert _parse_rules([]) == []


# ---------------------------------------------------------------------------
# build_route_parser
# ---------------------------------------------------------------------------

def test_parser_defaults():
    parser = build_route_parser()
    args = parser.parse_args([])
    assert args.rules == []
    assert args.default is None


def test_parser_multiple_rules():
    parser = build_route_parser()
    args = parser.parse_args(["--rule", "level=error:e.jsonl", "--rule", "level=warn:w.jsonl"])
    assert len(args.rules) == 2


# ---------------------------------------------------------------------------
# run_route — integration (writes real temp files)
# ---------------------------------------------------------------------------

def test_run_route_writes_matched_records(tmp_path):
    err_file = str(tmp_path / "errors.jsonl")
    stream = _make_stream(
        {"level": "error", "msg": "bad"},
        {"level": "info",  "msg": "ok"},
    )
    parser = build_route_parser()
    args = parser.parse_args(["--rule", f"level=error:{err_file}"])
    args.infile = stream
    rc = run_route(args)
    assert rc == 0
    lines = open(err_file).readlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["msg"] == "bad"


def test_run_route_default_file_receives_unmatched(tmp_path):
    err_file = str(tmp_path / "errors.jsonl")
    def_file = str(tmp_path / "default.jsonl")
    stream = _make_stream(
        {"level": "error", "msg": "bad"},
        {"level": "info",  "msg": "ok"},
    )
    parser = build_route_parser()
    args = parser.parse_args([
        "--rule", f"level=error:{err_file}",
        "--default", def_file,
    ])
    args.infile = stream
    run_route(args)
    assert len(open(def_file).readlines()) == 1


def test_run_route_discards_unmatched_when_no_default(tmp_path):
    err_file = str(tmp_path / "errors.jsonl")
    stream = _make_stream({"level": "info", "msg": "ok"})
    parser = build_route_parser()
    args = parser.parse_args(["--rule", f"level=error:{err_file}"])
    args.infile = stream
    run_route(args)
    assert not os.path.exists(err_file)


def test_run_route_skips_garbage_lines(tmp_path):
    err_file = str(tmp_path / "errors.jsonl")
    stream = StringIO("not json at all\n" + json.dumps({"level": "error"}) + "\n")
    parser = build_route_parser()
    args = parser.parse_args(["--rule", f"level=error:{err_file}"])
    args.infile = stream
    rc = run_route(args)
    assert rc == 0
    assert len(open(err_file).readlines()) == 1
