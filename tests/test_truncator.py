"""Tests for logslice.truncator."""

from __future__ import annotations

import pytest

from logslice.truncator import (
    truncate_value,
    truncate_fields,
    truncate_all,
    truncate_stream,
)


# ---------------------------------------------------------------------------
# truncate_value
# ---------------------------------------------------------------------------

def test_truncate_value_short_string_unchanged():
    assert truncate_value("hello", 10) == "hello"


def test_truncate_value_exact_length_unchanged():
    assert truncate_value("hello", 5) == "hello"


def test_truncate_value_long_string_truncated():
    result = truncate_value("hello world", 8)
    assert len(result) == 8
    assert result.endswith("...")


def test_truncate_value_custom_placeholder():
    result = truncate_value("abcdefgh", 5, placeholder="!")
    assert result == "abcd!"
    assert len(result) == 5


def test_truncate_value_non_string_returned_unchanged():
    assert truncate_value(42, 3) == 42
    assert truncate_value(3.14, 2) == 3.14
    assert truncate_value(None, 5) is None
    assert truncate_value(["a", "b"], 1) == ["a", "b"]


def test_truncate_value_max_length_zero():
    result = truncate_value("hi", 0)
    assert result == "..."


def test_truncate_value_max_length_shorter_than_placeholder():
    # placeholder itself is 3 chars; max_length=2 → cutoff=0
    result = truncate_value("hello", 2)
    assert result == "..."


# ---------------------------------------------------------------------------
# truncate_fields
# ---------------------------------------------------------------------------

def test_truncate_fields_only_named_fields_affected():
    record = {"msg": "a long message here", "level": "info", "code": 200}
    out = truncate_fields(record, ["msg"], 10)
    assert len(out["msg"]) == 10
    assert out["level"] == "info"
    assert out["code"] == 200


def test_truncate_fields_missing_field_ignored():
    record = {"level": "warn"}
    out = truncate_fields(record, ["msg"], 5)
    assert out == {"level": "warn"}


def test_truncate_fields_does_not_mutate_original():
    record = {"msg": "hello world"}
    truncate_fields(record, ["msg"], 5)
    assert record["msg"] == "hello world"


# ---------------------------------------------------------------------------
# truncate_all
# ---------------------------------------------------------------------------

def test_truncate_all_truncates_every_string():
    record = {"a": "long value one", "b": "long value two", "n": 1}
    out = truncate_all(record, 8)
    assert len(out["a"]) == 8
    assert len(out["b"]) == 8
    assert out["n"] == 1


def test_truncate_all_exclude_leaves_field_intact():
    record = {"msg": "a very long message", "service": "my-service-name"}
    out = truncate_all(record, 5, exclude=["service"])
    assert out["service"] == "my-service-name"
    assert len(out["msg"]) == 5


# ---------------------------------------------------------------------------
# truncate_stream
# ---------------------------------------------------------------------------

def test_truncate_stream_yields_all_records():
    records = [{"msg": "hello"}, {"msg": "world"}]
    out = list(truncate_stream(records, max_length=20))
    assert len(out) == 2


def test_truncate_stream_with_fields():
    records = [{"msg": "a very long message", "level": "info"}]
    out = list(truncate_stream(records, max_length=8, fields=["msg"]))
    assert len(out[0]["msg"]) == 8
    assert out[0]["level"] == "info"


def test_truncate_stream_without_fields_truncates_all():
    records = [{"msg": "long message", "svc": "my-svc"}]
    out = list(truncate_stream(records, max_length=5))
    assert len(out[0]["msg"]) == 5
    assert len(out[0]["svc"]) == 5


def test_truncate_stream_empty_input():
    assert list(truncate_stream([], max_length=10)) == []
