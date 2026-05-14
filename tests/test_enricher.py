"""Tests for logslice.enricher."""

import pytest

from logslice.enricher import (
    enrich_copy,
    enrich_extract,
    enrich_record,
    enrich_static,
    enrich_stream,
)


@pytest.fixture()
def record():
    return {"level": "info", "message": "hello world", "service": "api"}


# --- enrich_static ---

def test_enrich_static_adds_new_fields(record):
    result = enrich_static(record, {"env": "prod", "region": "us-east-1"})
    assert result["env"] == "prod"
    assert result["region"] == "us-east-1"


def test_enrich_static_does_not_overwrite_existing(record):
    result = enrich_static(record, {"level": "debug", "host": "box1"})
    assert result["level"] == "info"  # original preserved
    assert result["host"] == "box1"


def test_enrich_static_does_not_mutate_original(record):
    enrich_static(record, {"env": "prod"})
    assert "env" not in record


# --- enrich_copy ---

def test_enrich_copy_copies_existing_field(record):
    result = enrich_copy(record, [("service", "svc")])
    assert result["svc"] == "api"


def test_enrich_copy_skips_missing_source(record):
    result = enrich_copy(record, [("missing_key", "dest")])
    assert "dest" not in result


def test_enrich_copy_does_not_overwrite_dest(record):
    record_with_dest = {**record, "svc": "existing"}
    result = enrich_copy(record_with_dest, [("service", "svc")])
    assert result["svc"] == "existing"


def test_enrich_copy_multiple_mappings(record):
    result = enrich_copy(record, [("level", "lvl"), ("service", "svc")])
    assert result["lvl"] == "info"
    assert result["svc"] == "api"


# --- enrich_extract ---

def test_enrich_extract_named_group(record):
    r = {**record, "message": "user=alice logged in"}
    result = enrich_extract(r, "message", r"user=(?P<value>\w+)", "user")
    assert result["user"] == "alice"


def test_enrich_extract_no_match_returns_unchanged(record):
    result = enrich_extract(record, "message", r"user=(?P<value>\w+)", "user")
    assert "user" not in result


def test_enrich_extract_missing_source_key(record):
    result = enrich_extract(record, "nonexistent", r"(?P<value>\w+)", "dest")
    assert result == record


def test_enrich_extract_non_string_value(record):
    r = {**record, "code": 404}
    result = enrich_extract(r, "code", r"(?P<value>\d+)", "status")
    assert "status" not in result


def test_enrich_extract_does_not_overwrite_existing_dest():
    r = {"msg": "id=42", "id": "existing"}
    result = enrich_extract(r, "msg", r"id=(?P<value>\d+)", "id")
    assert result["id"] == "existing"


# --- enrich_record ---

def test_enrich_record_combines_all_steps():
    r = {"message": "req_id=abc123 done", "level": "info"}
    result = enrich_record(
        r,
        static={"env": "staging"},
        copies=[("level", "lvl")],
        extractions=[("message", r"req_id=(?P<value>\w+)", "req_id")],
    )
    assert result["env"] == "staging"
    assert result["lvl"] == "info"
    assert result["req_id"] == "abc123"


# --- enrich_stream ---

def test_enrich_stream_applies_to_all_records():
    records = [{"level": "info"}, {"level": "error"}]
    results = list(enrich_stream(records, static={"env": "prod"}))
    assert all(r["env"] == "prod" for r in results)
    assert len(results) == 2


def test_enrich_stream_empty_input():
    results = list(enrich_stream([], static={"env": "prod"}))
    assert results == []
