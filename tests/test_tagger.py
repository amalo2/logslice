"""Tests for logslice.tagger."""

import pytest

from logslice.tagger import tag_record, tag_stream


@pytest.fixture()
def base_record():
    return {"level": "error", "service": "auth", "msg": "login failed"}


@pytest.fixture()
def rules():
    return [
        {"field": "level", "value": "error", "tag": "alert"},
        {"field": "service", "value": "auth", "tag": "security"},
        {"field": "level", "value": "debug", "tag": "verbose"},
    ]


def test_no_rules_returns_record_unchanged(base_record):
    result = tag_record(base_record, [])
    assert result == base_record


def test_matching_rule_adds_tag(base_record, rules):
    result = tag_record(base_record, rules)
    assert "alert" in result["tags"]


def test_multiple_matching_rules_add_all_tags(base_record, rules):
    result = tag_record(base_record, rules)
    assert "alert" in result["tags"]
    assert "security" in result["tags"]


def test_non_matching_rule_not_applied(base_record, rules):
    result = tag_record(base_record, rules)
    assert "verbose" not in result["tags"]


def test_tags_are_sorted(base_record, rules):
    result = tag_record(base_record, rules)
    assert result["tags"] == sorted(result["tags"])


def test_tags_are_deduplicated():
    record = {"level": "error"}
    rules = [
        {"field": "level", "value": "error", "tag": "alert"},
        {"field": "level", "value": "error", "tag": "alert"},
    ]
    result = tag_record(record, rules)
    assert result["tags"].count("alert") == 1


def test_original_record_not_mutated(base_record, rules):
    original = dict(base_record)
    tag_record(base_record, rules)
    assert base_record == original


def test_custom_tag_field(base_record, rules):
    result = tag_record(base_record, rules, tag_field="labels")
    assert "labels" in result
    assert "tags" not in result


def test_existing_tags_are_preserved():
    record = {"level": "error", "tags": ["existing"]}
    rules = [{"field": "level", "value": "error", "tag": "alert"}]
    result = tag_record(record, rules)
    assert "existing" in result["tags"]
    assert "alert" in result["tags"]


def test_no_match_leaves_tags_absent():
    record = {"level": "info"}
    rules = [{"field": "level", "value": "error", "tag": "alert"}]
    result = tag_record(record, rules)
    assert "tags" not in result


def test_tag_stream_yields_all_records():
    records = [
        {"level": "error"},
        {"level": "info"},
        {"level": "error"},
    ]
    rules = [{"field": "level", "value": "error", "tag": "alert"}]
    results = list(tag_stream(records, rules))
    assert len(results) == 3
    assert results[0]["tags"] == ["alert"]
    assert "tags" not in results[1]
    assert results[2]["tags"] == ["alert"]


def test_rule_with_missing_field_skipped(base_record):
    rules = [{"field": "", "value": "error", "tag": "alert"}]
    result = tag_record(base_record, rules)
    assert "tags" not in result


def test_rule_with_missing_tag_skipped(base_record):
    rules = [{"field": "level", "value": "error", "tag": ""}]
    result = tag_record(base_record, rules)
    assert "tags" not in result
