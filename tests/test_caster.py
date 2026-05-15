"""Tests for logslice.caster."""

import pytest

from logslice.caster import (
    _cast_value,
    cast_fields,
    cast_stream,
    parse_cast_specs,
)


# ---------------------------------------------------------------------------
# _cast_value
# ---------------------------------------------------------------------------

def test_cast_value_str_to_int():
    assert _cast_value("42", "int") == 42


def test_cast_value_str_to_float():
    assert _cast_value("3.14", "float") == pytest.approx(3.14)


def test_cast_value_int_to_str():
    assert _cast_value(99, "str") == "99"


def test_cast_value_bool_true_variants():
    for raw in ("true", "1", "yes", "True", "YES"):
        assert _cast_value(raw, "bool") is True, raw


def test_cast_value_bool_false_variants():
    for raw in ("false", "0", "no", "False", ""):
        assert _cast_value(raw, "bool") is False, raw


def test_cast_value_bool_passthrough_when_already_bool():
    assert _cast_value(True, "bool") is True
    assert _cast_value(False, "bool") is False


def test_cast_value_invalid_int_returns_original():
    assert _cast_value("not-a-number", "int") == "not-a-number"


def test_cast_value_unknown_type_raises():
    with pytest.raises(ValueError, match="Unknown cast type"):
        _cast_value("x", "uuid")


# ---------------------------------------------------------------------------
# cast_fields
# ---------------------------------------------------------------------------

def test_cast_fields_converts_specified_fields():
    record = {"status": "200", "latency": "1.5", "message": "ok"}
    result = cast_fields(record, {"status": "int", "latency": "float"})
    assert result["status"] == 200
    assert result["latency"] == pytest.approx(1.5)
    assert result["message"] == "ok"


def test_cast_fields_does_not_mutate_original():
    record = {"code": "404"}
    cast_fields(record, {"code": "int"})
    assert record["code"] == "404"


def test_cast_fields_missing_field_is_skipped():
    record = {"level": "info"}
    result = cast_fields(record, {"status": "int"})
    assert "status" not in result


def test_cast_fields_empty_casts_returns_copy():
    record = {"a": 1}
    result = cast_fields(record, {})
    assert result == record
    assert result is not record


# ---------------------------------------------------------------------------
# cast_stream
# ---------------------------------------------------------------------------

def test_cast_stream_yields_all_records():
    records = [{"n": "1"}, {"n": "2"}, {"n": "3"}]
    out = list(cast_stream(records, {"n": "int"}))
    assert [r["n"] for r in out] == [1, 2, 3]


def test_cast_stream_empty_input():
    assert list(cast_stream([], {"x": "float"})) == []


# ---------------------------------------------------------------------------
# parse_cast_specs
# ---------------------------------------------------------------------------

def test_parse_cast_specs_single():
    assert parse_cast_specs(["status:int"]) == {"status": "int"}


def test_parse_cast_specs_multiple():
    result = parse_cast_specs(["status:int", "ratio:float", "name:str"])
    assert result == {"status": "int", "ratio": "float", "name": "str"}


def test_parse_cast_specs_missing_colon_raises():
    with pytest.raises(ValueError, match="Invalid cast spec"):
        parse_cast_specs(["statusint"])


def test_parse_cast_specs_empty_field_raises():
    with pytest.raises(ValueError, match="Invalid cast spec"):
        parse_cast_specs([":int"])


def test_parse_cast_specs_empty_type_raises():
    with pytest.raises(ValueError, match="Invalid cast spec"):
        parse_cast_specs(["status:"])


def test_parse_cast_specs_empty_list():
    assert parse_cast_specs([]) == {}
