"""Tests for logslice.masker."""
from __future__ import annotations

import pytest

from logslice.masker import (
    mask_full,
    mask_partial,
    mask_pattern,
    mask_record,
    mask_stream,
)


# ---------------------------------------------------------------------------
# mask_full
# ---------------------------------------------------------------------------

def test_mask_full_default_placeholder():
    assert mask_full("secret") == "[MASKED]"


def test_mask_full_custom_placeholder():
    assert mask_full("secret", placeholder="***") == "***"


def test_mask_full_non_string_value():
    assert mask_full(12345) == "[MASKED]"


# ---------------------------------------------------------------------------
# mask_partial
# ---------------------------------------------------------------------------

def test_mask_partial_shows_last_four():
    assert mask_partial("abcdefgh", visible=4) == "****efgh"


def test_mask_partial_value_shorter_than_visible():
    assert mask_partial("ab", visible=4) == "**"


def test_mask_partial_visible_zero_masks_all():
    result = mask_partial("hello", visible=0)
    assert result == "*****"


def test_mask_partial_numeric_value():
    result = mask_partial(4111111111111111, visible=4)
    assert result.endswith("1111")
    assert "*" in result


# ---------------------------------------------------------------------------
# mask_pattern
# ---------------------------------------------------------------------------

def test_mask_pattern_replaces_match():
    result = mask_pattern("call 555-1234 now", r"\d{3}-\d{4}")
    assert result == "call [MASKED] now"


def test_mask_pattern_no_match_returns_original():
    result = mask_pattern("hello world", r"\d+")
    assert result == "hello world"


def test_mask_pattern_custom_replacement():
    result = mask_pattern("foo@bar.com", r"[^@]+@", replacement="***@")
    assert result == "***@bar.com"


# ---------------------------------------------------------------------------
# mask_record
# ---------------------------------------------------------------------------

@pytest.fixture()
def record():
    return {"user": "alice", "token": "abc123xyz", "level": "info", "count": 7}


def test_mask_record_full_strategy(record):
    result = mask_record(record, fields=["token"])
    assert result["token"] == "[MASKED]"
    assert result["user"] == "alice"


def test_mask_record_does_not_mutate_original(record):
    mask_record(record, fields=["token"])
    assert record["token"] == "abc123xyz"


def test_mask_record_partial_strategy(record):
    result = mask_record(record, fields=["token"], strategy="partial", visible=3)
    assert result["token"].endswith("xyz")
    assert result["token"].startswith("*")


def test_mask_record_pattern_strategy(record):
    result = mask_record(
        record, fields=["token"], strategy="pattern", pattern=r"\d+"
    )
    assert "123" not in result["token"]


def test_mask_record_missing_field_is_ignored(record):
    result = mask_record(record, fields=["password"])
    assert "password" not in result
    assert set(result.keys()) == set(record.keys())


def test_mask_record_multiple_fields(record):
    result = mask_record(record, fields=["token", "user"])
    assert result["token"] == "[MASKED]"
    assert result["user"] == "[MASKED]"
    assert result["level"] == "info"


# ---------------------------------------------------------------------------
# mask_stream
# ---------------------------------------------------------------------------

def test_mask_stream_applies_to_all_records():
    records = [
        {"token": "aaa", "level": "info"},
        {"token": "bbb", "level": "error"},
    ]
    results = list(mask_stream(records, fields=["token"]))
    assert all(r["token"] == "[MASKED]" for r in results)


def test_mask_stream_empty_input_yields_nothing():
    assert list(mask_stream([], fields=["token"])) == []


def test_mask_stream_preserves_unmasked_fields():
    records = [{"token": "secret", "msg": "hello"}]
    results = list(mask_stream(records, fields=["token"]))
    assert results[0]["msg"] == "hello"
