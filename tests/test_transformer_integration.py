"""Integration tests: transformer used through the pipeline."""

from __future__ import annotations

from logslice.transformer import transform_record


def _make_record(**kwargs):
    base = {"level": "INFO", "msg": "test message", "ts": "2024-01-01T00:00:00Z"}
    base.update(kwargs)
    return base


def test_rename_then_drop():
    record = _make_record(service="web", trace_id="abc")
    result = transform_record(record, rename={"msg": "message"}, drop=["trace_id"])
    assert "message" in result
    assert "msg" not in result
    assert "trace_id" not in result
    assert result["service"] == "web"


def test_add_does_not_clobber_existing():
    record = _make_record(env="prod")
    result = transform_record(record, add={"env": "staging", "region": "us-east-1"})
    assert result["env"] == "prod"
    assert result["region"] == "us-east-1"


def test_field_transform_chain():
    record = _make_record(level="INFO", msg="  spaced  ")
    result = transform_record(
        record,
        field_transforms={"level": "lower", "msg": "strip"},
    )
    assert result["level"] == "info"
    assert result["msg"] == "spaced"


def test_full_pipeline_idempotent_on_empty_options():
    record = _make_record(service="api")
    result = transform_record(record)
    assert result == record
    assert result is not record  # new dict


def test_drop_all_extra_fields_leaves_core():
    record = _make_record(service="api", trace="xyz", user="bob")
    result = transform_record(record, drop=["service", "trace", "user"])
    assert set(result.keys()) == {"level", "msg", "ts"}


def test_rename_and_apply_combined():
    record = _make_record(raw_count="10")
    result = transform_record(
        record,
        rename={"raw_count": "count"},
        field_transforms={"count": "int"},
    )
    assert result["count"] == 10
    assert "raw_count" not in result
