"""Tests for logslice.transformer."""

import pytest

from logslice.transformer import (
    apply_transform,
    rename_fields,
    drop_fields,
    add_fields,
    transform_field,
    transform_record,
)


@pytest.fixture
def record():
    return {"level": "INFO", "msg": "  hello  ", "count": "42", "service": "api"}


def test_apply_transform_upper():
    assert apply_transform("hello", "upper") == "HELLO"


def test_apply_transform_lower():
    assert apply_transform("HELLO", "lower") == "hello"


def test_apply_transform_strip():
    assert apply_transform("  hi  ", "strip") == "hi"


def test_apply_transform_int():
    assert apply_transform("7", "int") == 7


def test_apply_transform_float():
    assert apply_transform("3.14", "float") == pytest.approx(3.14)


def test_apply_transform_unknown_raises():
    with pytest.raises(KeyError, match="unknown_op"):
        apply_transform("x", "unknown_op")


def test_rename_fields_basic(record):
    result = rename_fields(record, {"msg": "message"})
    assert "message" in result
    assert "msg" not in result
    assert result["message"] == "  hello  "


def test_rename_fields_missing_key_is_ignored(record):
    result = rename_fields(record, {"nonexistent": "other"})
    assert result == record


def test_rename_fields_does_not_mutate(record):
    original = dict(record)
    rename_fields(record, {"level": "severity"})
    assert record == original


def test_drop_fields_removes_keys(record):
    result = drop_fields(record, ["service", "count"])
    assert "service" not in result
    assert "count" not in result
    assert "level" in result


def test_drop_fields_missing_key_is_ignored(record):
    result = drop_fields(record, ["nonexistent"])
    assert result == record


def test_add_fields_adds_new_key(record):
    result = add_fields(record, {"env": "prod"})
    assert result["env"] == "prod"


def test_add_fields_does_not_overwrite(record):
    result = add_fields(record, {"level": "DEBUG"})
    assert result["level"] == "INFO"


def test_transform_field_applies_transform(record):
    result = transform_field(record, "count", "int")
    assert result["count"] == 42


def test_transform_field_missing_key_returns_copy(record):
    result = transform_field(record, "nonexistent", "upper")
    assert result == record


def test_transform_record_full_pipeline(record):
    result = transform_record(
        record,
        rename={"msg": "message"},
        drop=["service"],
        add={"env": "staging"},
        field_transforms={"count": "int", "message": "strip"},
    )
    assert result["message"] == "hello"
    assert result["count"] == 42
    assert result["env"] == "staging"
    assert "service" not in result
    assert "msg" not in result
