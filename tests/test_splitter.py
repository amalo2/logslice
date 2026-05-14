"""Tests for logslice.splitter."""

import json
import os

import pytest

from logslice.splitter import split_records, split_stream, write_splits


@pytest.fixture()
def records():
    return [
        {"level": "info", "msg": "started"},
        {"level": "error", "msg": "boom"},
        {"level": "info", "msg": "done"},
        {"msg": "no level here"},
    ]


def test_split_records_groups_by_field(records):
    buckets = split_records(records, "level")
    assert set(buckets["info"]) == {frozenset(r.items()) for r in records if r.get("level") == "info"}
    assert len(buckets["info"]) == 2
    assert len(buckets["error"]) == 1


def test_split_records_fallback_for_missing_field(records):
    buckets = split_records(records, "level")
    assert "__other__" in buckets
    assert buckets["__other__"][0]["msg"] == "no level here"


def test_split_records_custom_fallback(records):
    buckets = split_records(records, "level", fallback="unknown")
    assert "unknown" in buckets
    assert "__other__" not in buckets


def test_split_records_empty_input():
    assert split_records([], "level") == {}


def test_split_stream_parses_json_lines():
    lines = [
        json.dumps({"level": "warn", "msg": "a"}),
        json.dumps({"level": "info", "msg": "b"}),
        "not json at all",
        json.dumps({"level": "warn", "msg": "c"}),
    ]
    buckets = split_stream(lines, "level")
    assert len(buckets["warn"]) == 2
    assert len(buckets["info"]) == 1


def test_split_stream_skips_garbage_lines():
    lines = ["garbage", "", "   ", json.dumps({"level": "debug", "msg": "x"})]
    buckets = split_stream(lines, "level")
    assert list(buckets.keys()) == ["debug"]


def test_write_splits_creates_files(tmp_path, records):
    buckets = split_records(records, "level")
    written = write_splits(buckets, str(tmp_path))
    for key, path in written.items():
        assert os.path.isfile(path)


def test_write_splits_each_file_is_valid_jsonl(tmp_path, records):
    buckets = split_records(records, "level")
    written = write_splits(buckets, str(tmp_path))
    for key, path in written.items():
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                obj = json.loads(line)
                assert isinstance(obj, dict)


def test_write_splits_prefix_and_suffix(tmp_path, records):
    buckets = split_records(records, "level")
    written = write_splits(buckets, str(tmp_path), prefix="app_", suffix=".log")
    for key, path in written.items():
        basename = os.path.basename(path)
        assert basename.startswith("app_")
        assert basename.endswith(".log")


def test_write_splits_returns_mapping_of_all_buckets(tmp_path, records):
    buckets = split_records(records, "level")
    written = write_splits(buckets, str(tmp_path))
    assert set(written.keys()) == set(buckets.keys())
