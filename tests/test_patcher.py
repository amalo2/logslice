"""Tests for logslice.patcher."""
import pytest

from logslice.patcher import patch_record, patch_stream, _set_nested, _del_nested


# ---------------------------------------------------------------------------
# _set_nested
# ---------------------------------------------------------------------------

def test_set_nested_top_level():
    r = _set_nested({"a": 1}, "a", 99)
    assert r["a"] == 99


def test_set_nested_creates_new_key():
    r = _set_nested({"a": 1}, "b", 2)
    assert r["b"] == 2
    assert r["a"] == 1


def test_set_nested_deep_path():
    r = _set_nested({}, "x.y.z", "hello")
    assert r["x"]["y"]["z"] == "hello"


def test_set_nested_does_not_mutate_original():
    orig = {"a": {"b": 1}}
    _set_nested(orig, "a.b", 999)
    assert orig["a"]["b"] == 1


# ---------------------------------------------------------------------------
# _del_nested
# ---------------------------------------------------------------------------

def test_del_nested_top_level():
    r = _del_nested({"a": 1, "b": 2}, "a")
    assert "a" not in r
    assert r["b"] == 2


def test_del_nested_missing_key_is_noop():
    r = _del_nested({"a": 1}, "z")
    assert r == {"a": 1}


def test_del_nested_deep_path():
    r = _del_nested({"x": {"y": {"z": 1, "w": 2}}}, "x.y.z")
    assert "z" not in r["x"]["y"]
    assert r["x"]["y"]["w"] == 2


def test_del_nested_does_not_mutate_original():
    orig = {"a": {"b": 1}}
    _del_nested(orig, "a.b")
    assert orig["a"]["b"] == 1


# ---------------------------------------------------------------------------
# patch_record
# ---------------------------------------------------------------------------

def test_patch_set_op():
    r = patch_record({"level": "info"}, [{"op": "set", "path": "level", "value": "error"}])
    assert r["level"] == "error"


def test_patch_remove_op():
    r = patch_record({"a": 1, "b": 2}, [{"op": "remove", "path": "a"}])
    assert "a" not in r
    assert r["b"] == 2


def test_patch_default_op_sets_when_absent():
    r = patch_record({"a": 1}, [{"op": "default", "path": "b", "value": 42}])
    assert r["b"] == 42


def test_patch_default_op_does_not_overwrite():
    r = patch_record({"a": 1}, [{"op": "default", "path": "a", "value": 99}])
    assert r["a"] == 1


def test_patch_multiple_ops_applied_in_order():
    patches = [
        {"op": "set", "path": "x", "value": 10},
        {"op": "set", "path": "x", "value": 20},
    ]
    r = patch_record({}, patches)
    assert r["x"] == 20


def test_patch_unknown_op_is_skipped():
    r = patch_record({"a": 1}, [{"op": "unknown", "path": "a", "value": 9}])
    assert r["a"] == 1


def test_patch_missing_path_is_skipped():
    r = patch_record({"a": 1}, [{"op": "set", "value": 9}])
    assert r == {"a": 1}


def test_patch_does_not_mutate_original():
    orig = {"a": 1}
    patch_record(orig, [{"op": "set", "path": "a", "value": 2}])
    assert orig["a"] == 1


# ---------------------------------------------------------------------------
# patch_stream
# ---------------------------------------------------------------------------

def test_patch_stream_yields_all_records():
    records = [{"n": i} for i in range(5)]
    result = list(patch_stream(records, [{"op": "set", "path": "tag", "value": "x"}]))
    assert len(result) == 5
    assert all(r["tag"] == "x" for r in result)


def test_patch_stream_empty_patches_passthrough():
    records = [{"a": 1}, {"a": 2}]
    result = list(patch_stream(records, []))
    assert result == records
