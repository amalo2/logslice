"""Tests for logslice.annotator."""

import pytest

from logslice.annotator import (
    annotate_fields_present,
    annotate_index,
    annotate_record,
    annotate_source,
    annotate_stream,
)


@pytest.fixture()
def record():
    return {"level": "info", "message": "hello", "user": "alice"}


# annotate_index

def test_annotate_index_adds_field(record):
    out = annotate_index(record, 3)
    assert out["_index"] == 3


def test_annotate_index_custom_field(record):
    out = annotate_index(record, 7, field="seq")
    assert out["seq"] == 7


def test_annotate_index_does_not_mutate(record):
    annotate_index(record, 0)
    assert "_index" not in record


# annotate_source

def test_annotate_source_adds_field(record):
    out = annotate_source(record, "app.log")
    assert out["_source"] == "app.log"


def test_annotate_source_custom_field(record):
    out = annotate_source(record, "syslog", field="origin")
    assert out["origin"] == "syslog"


def test_annotate_source_does_not_mutate(record):
    annotate_source(record, "x")
    assert "_source" not in record


# annotate_fields_present

def test_fields_present_lists_existing(record):
    out = annotate_fields_present(record, ["level", "user", "missing"])
    assert out["_fields_present"] == ["level", "user"]


def test_fields_present_none_value_excluded():
    r = {"a": None, "b": "ok"}
    out = annotate_fields_present(r, ["a", "b"])
    assert out["_fields_present"] == ["b"]


def test_fields_present_empty_watch_list(record):
    out = annotate_fields_present(record, [])
    assert out["_fields_present"] == []


# annotate_record

def test_annotate_record_all_options(record):
    out = annotate_record(record, index=2, source="srv", watch_fields=["level", "user"])
    assert out["_index"] == 2
    assert out["_source"] == "srv"
    assert "level" in out["_fields_present"]


def test_annotate_record_no_options_unchanged(record):
    out = annotate_record(record)
    assert out == record


# annotate_stream

def test_annotate_stream_indexes_sequentially():
    records = [{"msg": "a"}, {"msg": "b"}, {"msg": "c"}]
    results = list(annotate_stream(records))
    assert [r["_index"] for r in results] == [0, 1, 2]


def test_annotate_stream_with_source():
    records = [{"msg": "x"}]
    results = list(annotate_stream(records, source="test.log"))
    assert results[0]["_source"] == "test.log"


def test_annotate_stream_empty_input():
    assert list(annotate_stream([])) == []


def test_annotate_stream_does_not_mutate_originals():
    records = [{"a": 1}]
    list(annotate_stream(records, source="s"))
    assert "_source" not in records[0]
