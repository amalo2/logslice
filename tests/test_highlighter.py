"""Tests for logslice.highlighter."""

import pytest

from logslice.highlighter import (
    highlight_text,
    highlight_record,
    strip_ansi,
)


# ---------------------------------------------------------------------------
# highlight_text
# ---------------------------------------------------------------------------

def test_empty_keyword_returns_original():
    assert highlight_text("hello world", "") == "hello world"


def test_keyword_not_present_returns_original():
    assert highlight_text("hello world", "missing") == "hello world"


def test_highlight_wraps_keyword_with_ansi():
    result = highlight_text("hello world", "world")
    assert "world" in result
    assert "\033[" in result


def test_highlight_case_insensitive_by_default():
    result = highlight_text("Hello World", "hello")
    stripped = strip_ansi(result)
    assert stripped == "Hello World"
    assert "\033[" in result


def test_highlight_case_sensitive_no_match():
    result = highlight_text("Hello World", "hello", case_sensitive=True)
    assert result == "Hello World"
    assert "\033[" not in result


def test_highlight_case_sensitive_match():
    result = highlight_text("Hello World", "Hello", case_sensitive=True)
    assert "\033[" in result


def test_highlight_multiple_occurrences():
    result = highlight_text("foo foo foo", "foo")
    # Each occurrence should be wrapped; strip and verify text is preserved.
    assert strip_ansi(result) == "foo foo foo"
    assert result.count("\033[") >= 3  # at least one open per occurrence


def test_highlight_style_bg():
    bold_result = highlight_text("error", "error", style="bold")
    bg_result = highlight_text("error", "error", style="bg")
    # Both highlight but use different ANSI codes.
    assert bold_result != bg_result
    assert strip_ansi(bold_result) == strip_ansi(bg_result)


# ---------------------------------------------------------------------------
# strip_ansi
# ---------------------------------------------------------------------------

def test_strip_ansi_removes_codes():
    coloured = "\033[1;33mhello\033[0m world"
    assert strip_ansi(coloured) == "hello world"


def test_strip_ansi_plain_string_unchanged():
    assert strip_ansi("plain text") == "plain text"


# ---------------------------------------------------------------------------
# highlight_record
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_record():
    return {
        "level": "error",
        "message": "Connection refused",
        "count": 42,
        "details": {"host": "localhost"},
    }


def test_highlight_record_none_keyword(sample_record):
    result = highlight_record(sample_record, None)
    assert result == sample_record


def test_highlight_record_empty_keyword(sample_record):
    result = highlight_record(sample_record, "")
    assert result == sample_record


def test_highlight_record_does_not_mutate_original(sample_record):
    original_message = sample_record["message"]
    highlight_record(sample_record, "Connection")
    assert sample_record["message"] == original_message


def test_highlight_record_string_values_highlighted(sample_record):
    result = highlight_record(sample_record, "refused")
    assert "\033[" in result["message"]
    assert strip_ansi(result["message"]) == "Connection refused"


def test_highlight_record_non_string_values_unchanged(sample_record):
    result = highlight_record(sample_record, "42")
    # Integer value should not be converted or altered.
    assert result["count"] == 42


def test_highlight_record_nested_dict_unchanged(sample_record):
    result = highlight_record(sample_record, "localhost")
    # Nested dicts are not recursed into.
    assert result["details"] == {"host": "localhost"}
