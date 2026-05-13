"""Tests for logslice.cli_transform."""

import json
import sys
from io import StringIO
from unittest import mock

import pytest

from logslice.cli_transform import build_transform_parser, run_transform


def _run(args_list, stdin_lines=None):
    """Parse args and run transform, capturing stdout. Returns (exit_code, lines)."""
    parser = build_transform_parser()
    args = parser.parse_args(args_list)
    captured = StringIO()
    if stdin_lines is not None:
        fake_stdin = StringIO("\n".join(stdin_lines) + "\n")
    else:
        fake_stdin = StringIO()
    with mock.patch("sys.stdout", captured), mock.patch("sys.stdin", fake_stdin):
        code = run_transform(args)
    output = [l for l in captured.getvalue().splitlines() if l]
    return code, output


SAMPLE = json.dumps({"level": "INFO", "msg": "hello", "service": "api", "count": "3"})


def test_passthrough_returns_zero():
    code, lines = _run([], stdin_lines=[SAMPLE])
    assert code == 0


def test_passthrough_outputs_valid_json():
    _, lines = _run([], stdin_lines=[SAMPLE])
    assert len(lines) == 1
    assert json.loads(lines[0])


def test_garbage_lines_are_skipped():
    _, lines = _run([], stdin_lines=["not json at all", SAMPLE])
    assert len(lines) == 1


def test_rename_field():
    _, lines = _run(["--rename", "msg", "message"], stdin_lines=[SAMPLE])
    record = json.loads(lines[0])
    assert "message" in record
    assert "msg" not in record


def test_drop_field():
    _, lines = _run(["--drop", "service"], stdin_lines=[SAMPLE])
    record = json.loads(lines[0])
    assert "service" not in record


def test_add_field_new_key():
    _, lines = _run(["--add", "env", "prod"], stdin_lines=[SAMPLE])
    record = json.loads(lines[0])
    assert record["env"] == "prod"


def test_add_field_does_not_overwrite_existing():
    _, lines = _run(["--add", "level", "DEBUG"], stdin_lines=[SAMPLE])
    record = json.loads(lines[0])
    assert record["level"] == "INFO"


def test_apply_transform_upper():
    _, lines = _run(["--apply", "level", "lower"], stdin_lines=[SAMPLE])
    record = json.loads(lines[0])
    assert record["level"] == "info"


def test_apply_transform_int():
    _, lines = _run(["--apply", "count", "int"], stdin_lines=[SAMPLE])
    record = json.loads(lines[0])
    assert record["count"] == 3


def test_combined_operations():
    _, lines = _run(
        ["--rename", "msg", "message", "--drop", "service", "--add", "env", "test"],
        stdin_lines=[SAMPLE],
    )
    record = json.loads(lines[0])
    assert "message" in record
    assert "msg" not in record
    assert "service" not in record
    assert record["env"] == "test"


def test_empty_input_produces_no_output():
    _, lines = _run([], stdin_lines=[])
    assert lines == []
