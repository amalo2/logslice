"""Tests for logslice.exporter."""

import json
import csv
import io
import pytest

from logslice.exporter import (
    export_jsonl,
    export_csv,
    export_text,
    export_records,
)


@pytest.fixture()
def records():
    return [
        {"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "started", "service": "api"},
        {"timestamp": "2024-01-01T00:01:00Z", "level": "ERROR", "message": "boom", "service": "worker"},
        {"timestamp": "2024-01-01T00:02:00Z", "level": "DEBUG", "message": "tick", "service": "api"},
    ]


# --- JSONL ---

def test_export_jsonl_each_line_is_valid_json(records):
    output = export_jsonl(records)
    lines = output.strip().split("\n")
    assert len(lines) == 3
    for line in lines:
        obj = json.loads(line)
        assert isinstance(obj, dict)


def test_export_jsonl_preserves_all_fields(records):
    output = export_jsonl(records)
    first = json.loads(output.split("\n")[0])
    assert first["level"] == "INFO"
    assert first["service"] == "api"


def test_export_jsonl_empty_returns_empty_string():
    assert export_jsonl([]) == ""


# --- CSV ---

def test_export_csv_has_header(records):
    output = export_csv(records)
    reader = csv.reader(io.StringIO(output))
    header = next(reader)
    assert "timestamp" in header
    assert "level" in header
    assert "message" in header


def test_export_csv_row_count(records):
    output = export_csv(records)
    rows = list(csv.DictReader(io.StringIO(output)))
    assert len(rows) == 3


def test_export_csv_custom_fields(records):
    output = export_csv(records, fields=["level", "message"])
    reader = csv.DictReader(io.StringIO(output))
    assert reader.fieldnames == ["level", "message"]


def test_export_csv_include_extra_adds_columns(records):
    output = export_csv(records, include_extra=True)
    reader = csv.DictReader(io.StringIO(output))
    assert "service" in reader.fieldnames


def test_export_csv_empty_returns_empty_string():
    assert export_csv([]) == ""


# --- Text ---

def test_export_text_default_template(records):
    output = export_text(records)
    lines = output.split("\n")
    assert len(lines) == 3
    assert "[INFO]" in lines[0]
    assert "started" in lines[0]


def test_export_text_custom_template(records):
    output = export_text(records, template="{level}: {message}")
    assert output.split("\n")[1] == "ERROR: boom"


def test_export_text_missing_key_falls_back(records):
    # Template references a field that doesn't exist — should not raise.
    output = export_text(records, template="{level} {nonexistent_field}")
    lines = output.split("\n")
    assert len(lines) == 3


# --- Dispatch ---

def test_export_records_jsonl(records):
    out = export_records(records, fmt="jsonl")
    assert json.loads(out.split("\n")[0])["level"] == "INFO"


def test_export_records_csv(records):
    out = export_records(records, fmt="csv")
    assert "level" in out


def test_export_records_text(records):
    out = export_records(records, fmt="text")
    assert "INFO" in out


def test_export_records_unknown_format_raises(records):
    with pytest.raises(ValueError, match="Unknown export format"):
        export_records(records, fmt="xml")
