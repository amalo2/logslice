import pytest
from logslice.normalizer import (
    normalize_keys,
    normalize_level,
    normalize_strings,
    normalize_record,
    normalize_stream,
)


# ---------------------------------------------------------------------------
# normalize_keys
# ---------------------------------------------------------------------------

def test_normalize_keys_lowercases_all():
    result = normalize_keys({"Level": "info", "Message": "hi", "TS": 1})
    assert set(result.keys()) == {"level", "message", "ts"}


def test_normalize_keys_does_not_mutate_original():
    original = {"Level": "info"}
    normalize_keys(original)
    assert "Level" in original


def test_normalize_keys_already_lowercase_unchanged():
    record = {"level": "info", "msg": "ok"}
    assert normalize_keys(record) == record


# ---------------------------------------------------------------------------
# normalize_level
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("alias,canonical", [
    ("warn", "warning"),
    ("WARN", "warning"),
    ("err", "error"),
    ("crit", "critical"),
    ("fatal", "critical"),
    ("dbg", "debug"),
    ("trace", "debug"),
])
def test_normalize_level_aliases(alias, canonical):
    record = {"level": alias}
    assert normalize_level(record)["level"] == canonical


def test_normalize_level_known_value_unchanged():
    record = {"level": "info"}
    assert normalize_level(record)["level"] == "info"


def test_normalize_level_missing_field_returns_record_unchanged():
    record = {"msg": "hello"}
    assert normalize_level(record) == record


def test_normalize_level_custom_field():
    record = {"severity": "warn"}
    result = normalize_level(record, field="severity")
    assert result["severity"] == "warning"


# ---------------------------------------------------------------------------
# normalize_strings
# ---------------------------------------------------------------------------

def test_normalize_strings_strips_whitespace():
    record = {"msg": "  hello  ", "level": " info "}
    result = normalize_strings(record)
    assert result["msg"] == "hello"
    assert result["level"] == "info"


def test_normalize_strings_specific_fields_only():
    record = {"msg": "  hello  ", "level": " info "}
    result = normalize_strings(record, fields=["msg"])
    assert result["msg"] == "hello"
    assert result["level"] == " info "  # untouched


def test_normalize_strings_non_string_values_unchanged():
    record = {"count": 42, "active": True}
    result = normalize_strings(record)
    assert result["count"] == 42
    assert result["active"] is True


# ---------------------------------------------------------------------------
# normalize_record
# ---------------------------------------------------------------------------

def test_normalize_record_full_pipeline():
    record = {"Level": "  WARN  ", "Message": "  test  ", "Count": 3}
    result = normalize_record(record)
    assert result["level"] == "warning"
    assert result["message"] == "test"
    assert result["count"] == 3


def test_normalize_record_does_not_mutate_original():
    record = {"Level": "warn", "msg": "hi"}
    normalize_record(record)
    assert "Level" in record


def test_normalize_record_flags_respected():
    record = {"Level": "warn", "msg": "  hi  "}
    result = normalize_record(record, lowercase_keys=False, strip_strings=False)
    assert "Level" in result          # keys not lowercased
    assert result["msg"] == "  hi  "  # strings not stripped


# ---------------------------------------------------------------------------
# normalize_stream
# ---------------------------------------------------------------------------

def test_normalize_stream_yields_all_records():
    records = [{"Level": "warn"}, {"Level": "err"}]
    results = list(normalize_stream(records))
    assert len(results) == 2
    assert results[0]["level"] == "warning"
    assert results[1]["level"] == "error"


def test_normalize_stream_empty_input():
    assert list(normalize_stream([])) == []
