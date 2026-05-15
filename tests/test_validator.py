"""Tests for logslice.validator."""

import pytest

from logslice.validator import validate_record, validate_stream, _resolve_type


# ---------------------------------------------------------------------------
# _resolve_type
# ---------------------------------------------------------------------------

def test_resolve_type_str():
    assert _resolve_type("str") is str
    assert _resolve_type("string") is str


def test_resolve_type_int():
    assert _resolve_type("int") is int
    assert _resolve_type("integer") is int


def test_resolve_type_float():
    assert _resolve_type("float") is float
    assert _resolve_type("number") is float


def test_resolve_type_bool():
    assert _resolve_type("bool") is bool
    assert _resolve_type("boolean") is bool


def test_resolve_type_unknown_returns_none():
    assert _resolve_type("uuid") is None


def test_resolve_type_case_insensitive():
    assert _resolve_type("String") is str
    assert _resolve_type("INT") is int


# ---------------------------------------------------------------------------
# validate_record
# ---------------------------------------------------------------------------

def test_valid_record_returns_true_and_no_errors():
    record = {"level": "info", "msg": "ok", "code": 200}
    valid, errors = validate_record(
        record, required=["level", "msg"], field_types={"code": "int"}
    )
    assert valid is True
    assert errors == []


def test_missing_required_field_reports_error():
    record = {"msg": "hi"}
    valid, errors = validate_record(record, required=["level"])
    assert valid is False
    assert any("level" in e for e in errors)


def test_multiple_missing_fields_all_reported():
    record = {}
    valid, errors = validate_record(record, required=["level", "msg"])
    assert valid is False
    assert len(errors) == 2


def test_wrong_type_reports_error():
    record = {"code": "not-an-int"}
    valid, errors = validate_record(record, field_types={"code": "int"})
    assert valid is False
    assert any("code" in e for e in errors)


def test_bool_rejected_for_int_field():
    record = {"flag": True}
    valid, errors = validate_record(record, field_types={"flag": "int"})
    assert valid is False
    assert any("flag" in e for e in errors)


def test_unknown_type_name_is_reported():
    record = {"id": "abc"}
    valid, errors = validate_record(record, field_types={"id": "uuid"})
    assert valid is False
    assert any("unknown type" in e for e in errors)


def test_absent_typed_field_not_flagged_without_required():
    record = {"msg": "hi"}
    valid, errors = validate_record(record, field_types={"code": "int"})
    assert valid is True


# ---------------------------------------------------------------------------
# validate_stream
# ---------------------------------------------------------------------------

def test_validate_stream_yields_all_records_by_default():
    records = [{"level": "info"}, {"msg": "only-msg"}]
    results = list(validate_stream(records, required=["level"]))
    assert len(results) == 2


def test_validate_stream_drop_invalid_skips_bad_records():
    records = [
        {"level": "info", "msg": "good"},
        {"msg": "bad"},  # missing level
    ]
    results = list(
        validate_stream(records, required=["level"], drop_invalid=True)
    )
    assert len(results) == 1
    assert results[0][0]["msg"] == "good"


def test_validate_stream_errors_attached_to_record():
    records = [{"msg": "no-level"}]
    results = list(validate_stream(records, required=["level"]))
    rec, errors = results[0]
    assert len(errors) == 1
    assert "level" in errors[0]


def test_validate_stream_empty_input_yields_nothing():
    results = list(validate_stream([], required=["level"]))
    assert results == []
