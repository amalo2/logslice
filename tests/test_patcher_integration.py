"""Integration tests combining patcher with parser and stream helpers."""
from __future__ import annotations

import json

from logslice.parser import parse_lines
from logslice.patcher import patch_stream


def _raw_lines(*records):
    return [json.dumps(r) for r in records]


def test_parse_then_patch_set():
    lines = _raw_lines({"level": "info", "msg": "hello"})
    records = list(parse_lines(lines))
    patched = list(patch_stream(records, [{"op": "set", "path": "level", "value": "error"}]))
    assert patched[0]["level"] == "error"
    assert patched[0]["msg"] == "hello"


def test_parse_then_patch_remove():
    lines = _raw_lines({"level": "info", "token": "abc123"})
    records = list(parse_lines(lines))
    patched = list(patch_stream(records, [{"op": "remove", "path": "token"}]))
    assert "token" not in patched[0]


def test_patch_stream_preserves_record_count():
    lines = _raw_lines(*[{"n": i} for i in range(10)])
    records = list(parse_lines(lines))
    patched = list(patch_stream(records, [{"op": "set", "path": "tagged", "value": True}]))
    assert len(patched) == 10


def test_patch_nested_field_end_to_end():
    lines = _raw_lines({"meta": {"env": "dev"}, "level": "info"})
    records = list(parse_lines(lines))
    patched = list(patch_stream(records, [{"op": "set", "path": "meta.env", "value": "prod"}]))
    assert patched[0]["meta"]["env"] == "prod"


def test_default_patch_fills_missing_field_in_stream():
    lines = _raw_lines({"level": "info"}, {"level": "error", "env": "staging"})
    records = list(parse_lines(lines))
    patched = list(patch_stream(records, [{"op": "default", "path": "env", "value": "prod"}]))
    assert patched[0]["env"] == "prod"
    assert patched[1]["env"] == "staging"


def test_chained_patches_applied_sequentially():
    lines = _raw_lines({"a": 1, "b": 2})
    records = list(parse_lines(lines))
    patches = [
        {"op": "set", "path": "a", "value": 10},
        {"op": "remove", "path": "b"},
        {"op": "set", "path": "c", "value": 30},
    ]
    patched = list(patch_stream(records, patches))
    assert patched[0]["a"] == 10
    assert "b" not in patched[0]
    assert patched[0]["c"] == 30
