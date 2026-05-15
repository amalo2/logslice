"""Integration tests for logslice.cli_patch."""
from __future__ import annotations

import io
import json

import pytest

from logslice.cli_patch import build_patch_parser, run_patch, _parse_kv, _build_patches


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_lines(*records):
    return io.StringIO("\n".join(json.dumps(r) for r in records) + "\n")


def _run(argv, stdin_lines):
    parser = build_patch_parser()
    args = parser.parse_args(argv)
    # Patch stdin via _iter_lines indirection — feed via file list not needed;
    # instead we monkey-patch the generator.
    out = io.StringIO()
    # We inject lines by temporarily replacing sys.stdin inside run_patch:
    import logslice.cli_patch as mod
    orig = mod.sys.stdin
    mod.sys.stdin = stdin_lines
    try:
        rc = run_patch(args, out)
    finally:
        mod.sys.stdin = orig
    return rc, out.getvalue()


# ---------------------------------------------------------------------------
# _parse_kv
# ---------------------------------------------------------------------------

def test_parse_kv_string_value():
    path, value = _parse_kv("level=info")
    assert path == "level"
    assert value == "info"


def test_parse_kv_json_int():
    path, value = _parse_kv("retries=3")
    assert value == 3


def test_parse_kv_json_bool():
    _, value = _parse_kv("ok=true")
    assert value is True


def test_parse_kv_value_contains_equals():
    path, value = _parse_kv("msg=a=b")
    assert path == "msg"
    assert value == "a=b"


# ---------------------------------------------------------------------------
# _build_patches
# ---------------------------------------------------------------------------

def test_build_patches_set():
    parser = build_patch_parser()
    args = parser.parse_args(["--set", "level=error"])
    patches = _build_patches(args)
    assert patches == [{"op": "set", "path": "level", "value": "error"}]


def test_build_patches_remove():
    parser = build_patch_parser()
    args = parser.parse_args(["--remove", "secret"])
    patches = _build_patches(args)
    assert patches == [{"op": "remove", "path": "secret"}]


def test_build_patches_default():
    parser = build_patch_parser()
    args = parser.parse_args(["--default", "env=prod"])
    patches = _build_patches(args)
    assert patches == [{"op": "default", "path": "env", "value": "prod"}]


# ---------------------------------------------------------------------------
# run_patch
# ---------------------------------------------------------------------------

def test_run_patch_returns_zero():
    lines = _make_lines({"level": "info", "msg": "hi"})
    rc, _ = _run(["--set", "level=error"], lines)
    assert rc == 0


def test_run_patch_output_is_valid_json():
    lines = _make_lines({"level": "info"})
    _, out = _run(["--set", "level=error"], lines)
    parsed = json.loads(out.strip())
    assert parsed["level"] == "error"


def test_run_patch_garbage_lines_skipped():
    stdin = io.StringIO("not json\n" + json.dumps({"a": 1}) + "\n")
    _, out = _run(["--set", "a=2"], stdin)
    records = [json.loads(l) for l in out.strip().splitlines()]
    assert len(records) == 1
    assert records[0]["a"] == 2


def test_run_patch_remove_field():
    lines = _make_lines({"a": 1, "secret": "x"})
    _, out = _run(["--remove", "secret"], lines)
    r = json.loads(out.strip())
    assert "secret" not in r
    assert r["a"] == 1


def test_run_patch_default_does_not_overwrite():
    lines = _make_lines({"env": "staging"})
    _, out = _run(["--default", "env=prod"], lines)
    r = json.loads(out.strip())
    assert r["env"] == "staging"


def test_run_patch_no_ops_passthrough():
    records = [{"x": i} for i in range(3)]
    lines = _make_lines(*records)
    _, out = _run([], lines)
    result = [json.loads(l) for l in out.strip().splitlines()]
    assert result == records
