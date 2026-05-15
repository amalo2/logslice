import pytest
from logslice.renamer import rename_record, rename_stream, parse_mapping


@pytest.fixture()
def record():
    return {"level": "info", "msg": "hello", "ts": 1234567890}


# ---------------------------------------------------------------------------
# rename_record
# ---------------------------------------------------------------------------

def test_rename_record_basic(record):
    result = rename_record(record, {"msg": "message"})
    assert "message" in result
    assert "msg" not in result


def test_rename_record_preserves_other_fields(record):
    result = rename_record(record, {"msg": "message"})
    assert result["level"] == "info"
    assert result["ts"] == 1234567890


def test_rename_record_missing_source_is_skipped(record):
    result = rename_record(record, {"nonexistent": "target"})
    assert result == record


def test_rename_record_does_not_mutate_original(record):
    original = dict(record)
    rename_record(record, {"msg": "message"})
    assert record == original


def test_rename_record_no_overwrite_by_default(record):
    # 'level' already exists; rename 'msg' -> 'level' should be skipped
    result = rename_record(record, {"msg": "level"})
    assert result["level"] == "info"   # unchanged
    assert "msg" in result             # not removed


def test_rename_record_overwrite_replaces_destination(record):
    result = rename_record(record, {"msg": "level"}, overwrite=True)
    assert result["level"] == "hello"
    assert "msg" not in result


def test_rename_record_multiple_pairs(record):
    result = rename_record(record, {"msg": "message", "ts": "timestamp"})
    assert "message" in result
    assert "timestamp" in result
    assert "msg" not in result
    assert "ts" not in result


# ---------------------------------------------------------------------------
# rename_stream
# ---------------------------------------------------------------------------

def test_rename_stream_yields_all_records():
    records = [{"a": 1}, {"a": 2}, {"a": 3}]
    out = list(rename_stream(records, {"a": "b"}))
    assert len(out) == 3


def test_rename_stream_applies_mapping_to_each():
    records = [{"msg": "one"}, {"msg": "two"}]
    out = list(rename_stream(records, {"msg": "message"}))
    assert all("message" in r for r in out)
    assert all("msg" not in r for r in out)


def test_rename_stream_empty_input():
    assert list(rename_stream([], {"a": "b"})) == []


# ---------------------------------------------------------------------------
# parse_mapping
# ---------------------------------------------------------------------------

def test_parse_mapping_single():
    assert parse_mapping(["old:new"]) == {"old": "new"}


def test_parse_mapping_multiple():
    result = parse_mapping(["a:b", "c:d"])
    assert result == {"a": "b", "c": "d"}


def test_parse_mapping_invalid_no_colon():
    with pytest.raises(ValueError, match="Invalid rename pair"):
        parse_mapping(["nodivider"])


def test_parse_mapping_invalid_empty_old():
    with pytest.raises(ValueError, match="Invalid rename pair"):
        parse_mapping([":new"])


def test_parse_mapping_invalid_empty_new():
    with pytest.raises(ValueError, match="Invalid rename pair"):
        parse_mapping(["old:"])
