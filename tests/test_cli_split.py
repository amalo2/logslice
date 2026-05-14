"""Integration tests for logslice.cli_split."""

import json
import os
from io import StringIO
from unittest import mock

import pytest

from logslice.cli_split import build_split_parser, main, run_split


def _make_lines(*records):
    return [json.dumps(r) for r in records]


@pytest.fixture()
def log_file(tmp_path):
    path = tmp_path / "app.log"
    lines = _make_lines(
        {"level": "info", "msg": "ok"},
        {"level": "error", "msg": "fail"},
        {"level": "info", "msg": "also ok"},
        {"msg": "no level"},
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def _run(argv):
    return main(argv)


def test_parser_requires_field():
    parser = build_split_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--output-dir", "."])


def test_parser_defaults():
    parser = build_split_parser()
    args = parser.parse_args(["--field", "level"])
    assert args.output_dir == "."
    assert args.prefix == ""
    assert args.fallback == "__other__"


def test_run_creates_output_files(log_file, tmp_path):
    out = str(tmp_path / "out")
    rc = _run(["--field", "level", "--output-dir", out, log_file])
    assert rc == 0
    files = os.listdir(out)
    assert any("info" in f for f in files)
    assert any("error" in f for f in files)


def test_run_fallback_file_created(log_file, tmp_path):
    out = str(tmp_path / "out")
    _run(["--field", "level", "--output-dir", out, log_file])
    files = os.listdir(out)
    assert any("__other__" in f for f in files)


def test_run_custom_fallback(log_file, tmp_path):
    out = str(tmp_path / "out")
    _run(["--field", "level", "--output-dir", out, "--fallback", "misc", log_file])
    files = os.listdir(out)
    assert any("misc" in f for f in files)


def test_run_prefix_applied(log_file, tmp_path):
    out = str(tmp_path / "out")
    _run(["--field", "level", "--output-dir", out, "--prefix", "app_", log_file])
    for f in os.listdir(out):
        assert f.startswith("app_")


def test_run_output_is_valid_jsonl(log_file, tmp_path):
    out = str(tmp_path / "out")
    _run(["--field", "level", "--output-dir", out, log_file])
    for fname in os.listdir(out):
        with open(os.path.join(out, fname), encoding="utf-8") as fh:
            for line in fh:
                obj = json.loads(line)
                assert isinstance(obj, dict)


def test_run_empty_stream_returns_zero(tmp_path):
    out = str(tmp_path / "out")
    fake_stdin = StringIO("")
    with mock.patch("sys.stdin", fake_stdin):
        rc = _run(["--field", "level", "--output-dir", out])
    assert rc == 0
