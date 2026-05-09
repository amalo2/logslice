import pytest
from logslice.redactor import (
    redact_fields,
    redact_patterns,
    redact_record,
    _PLACEHOLDER,
)


@pytest.fixture
def record():
    return {
        "level": "INFO",
        "message": "user login",
        "email": "alice@example.com",
        "password": "s3cr3t",
        "token": "abc123",
        "ip": "192.168.1.42",
        "count": 7,
    }


# --- redact_fields ---

def test_redact_fields_replaces_named_fields(record):
    result = redact_fields(record, ["password", "token"])
    assert result["password"] == _PLACEHOLDER
    assert result["token"] == _PLACEHOLDER


def test_redact_fields_leaves_other_fields_intact(record):
    result = redact_fields(record, ["password"])
    assert result["email"] == "alice@example.com"
    assert result["level"] == "INFO"


def test_redact_fields_does_not_mutate_original(record):
    original_password = record["password"]
    redact_fields(record, ["password"])
    assert record["password"] == original_password


def test_redact_fields_missing_key_is_ignored(record):
    result = redact_fields(record, ["nonexistent"])
    assert "nonexistent" not in result


def test_redact_fields_custom_placeholder(record):
    result = redact_fields(record, ["email"], placeholder="[HIDDEN]")
    assert result["email"] == "[HIDDEN]"


def test_redact_fields_non_string_value_replaced(record):
    result = redact_fields(record, ["count"])
    assert result["count"] == _PLACEHOLDER


# --- redact_patterns ---

def test_redact_patterns_masks_email(record):
    result = redact_patterns(record)
    assert _PLACEHOLDER in result["email"]
    assert "alice@example.com" not in result["email"]


def test_redact_patterns_masks_ipv4(record):
    r = {"msg": "connected from 10.0.0.1"}
    result = redact_patterns(r)
    assert "10.0.0.1" not in result["msg"]
    assert _PLACEHOLDER in result["msg"]


def test_redact_patterns_skips_non_string_values(record):
    result = redact_patterns(record)
    assert result["count"] == 7


def test_redact_patterns_masks_bearer_token():
    r = {"auth": "Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig"}
    result = redact_patterns(r)
    assert "eyJ" not in result["auth"]


# --- redact_record ---

def test_redact_record_fields_only(record):
    result = redact_record(record, fields=["password"])
    assert result["password"] == _PLACEHOLDER
    assert result["email"] == "alice@example.com"


def test_redact_record_auto_patterns_only(record):
    result = redact_record(record, auto_patterns=True)
    assert "alice@example.com" not in result["email"]


def test_redact_record_combined(record):
    result = redact_record(record, fields=["token"], auto_patterns=True)
    assert result["token"] == _PLACEHOLDER
    assert "alice@example.com" not in result["email"]


def test_redact_record_no_options_returns_copy(record):
    result = redact_record(record)
    assert result == record
    assert result is not record
