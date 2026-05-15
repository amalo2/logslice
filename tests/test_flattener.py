import pytest
from logslice.flattener import flatten_record, unflatten_record, flatten_stream


# ---------------------------------------------------------------------------
# flatten_record
# ---------------------------------------------------------------------------

def test_flat_record_unchanged():
    rec = {"level": "info", "msg": "hello"}
    assert flatten_record(rec) == rec


def test_single_level_nesting():
    rec = {"a": {"b": 1}}
    assert flatten_record(rec) == {"a.b": 1}


def test_deep_nesting():
    rec = {"a": {"b": {"c": {"d": 42}}}}
    assert flatten_record(rec) == {"a.b.c.d": 42}


def test_mixed_depth():
    rec = {"x": 1, "y": {"z": 2}}
    result = flatten_record(rec)
    assert result == {"x": 1, "y.z": 2}


def test_custom_separator():
    rec = {"a": {"b": 1}}
    assert flatten_record(rec, separator="__") == {"a__b": 1}


def test_max_depth_one():
    rec = {"a": {"b": {"c": 3}}}
    result = flatten_record(rec, max_depth=1)
    # depth 1: expand top-level dict; a.b still a dict
    assert result == {"a.b": {"c": 3}}


def test_max_depth_two():
    rec = {"a": {"b": {"c": 3}}}
    result = flatten_record(rec, max_depth=2)
    assert result == {"a.b.c": 3}


def test_non_dict_values_preserved():
    rec = {"tags": ["a", "b"], "meta": {"count": 5}}
    result = flatten_record(rec)
    assert result["tags"] == ["a", "b"]
    assert result["meta.count"] == 5


def test_does_not_mutate_original():
    rec = {"a": {"b": 1}}
    original = {"a": {"b": 1}}
    flatten_record(rec)
    assert rec == original


# ---------------------------------------------------------------------------
# unflatten_record
# ---------------------------------------------------------------------------

def test_unflatten_basic():
    flat = {"a.b": 1}
    assert unflatten_record(flat) == {"a": {"b": 1}}


def test_unflatten_deep():
    flat = {"a.b.c": 42}
    assert unflatten_record(flat) == {"a": {"b": {"c": 42}}}


def test_unflatten_multiple_keys():
    flat = {"a.x": 1, "a.y": 2}
    assert unflatten_record(flat) == {"a": {"x": 1, "y": 2}}


def test_unflatten_custom_separator():
    flat = {"a__b": 99}
    assert unflatten_record(flat, separator="__") == {"a": {"b": 99}}


def test_roundtrip():
    original = {"level": "info", "request": {"method": "GET", "path": "/"}}
    assert unflatten_record(flatten_record(original)) == original


# ---------------------------------------------------------------------------
# flatten_stream
# ---------------------------------------------------------------------------

def test_flatten_stream_yields_all():
    records = [{"a": {"b": i}} for i in range(5)]
    results = list(flatten_stream(records))
    assert len(results) == 5
    assert all("a.b" in r for r in results)


def test_flatten_stream_empty():
    assert list(flatten_stream([])) == []
