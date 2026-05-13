import pytest
from logslice.differ import diff_records, is_empty_diff, diff_stream


# ---------------------------------------------------------------------------
# diff_records
# ---------------------------------------------------------------------------

def test_diff_records_no_change():
    rec = {"level": "info", "msg": "hello"}
    d = diff_records(rec, rec.copy())
    assert is_empty_diff(d)


def test_diff_records_added_key():
    before = {"level": "info"}
    after = {"level": "info", "request_id": "abc"}
    d = diff_records(before, after)
    assert d["added"] == {"request_id": "abc"}
    assert not d["removed"]
    assert not d["changed"]


def test_diff_records_removed_key():
    before = {"level": "info", "request_id": "abc"}
    after = {"level": "info"}
    d = diff_records(before, after)
    assert d["removed"] == {"request_id": "abc"}
    assert not d["added"]
    assert not d["changed"]


def test_diff_records_changed_value():
    before = {"level": "info", "count": 1}
    after = {"level": "info", "count": 2}
    d = diff_records(before, after)
    assert d["changed"] == {"count": {"before": 1, "after": 2}}
    assert not d["added"]
    assert not d["removed"]


def test_diff_records_ignore_keys():
    before = {"level": "info", "ts": "2024-01-01", "msg": "a"}
    after = {"level": "info", "ts": "2024-01-02", "msg": "b"}
    d = diff_records(before, after, ignore_keys=["ts"])
    assert "ts" not in d["changed"]
    assert d["changed"] == {"msg": {"before": "a", "after": "b"}}


def test_diff_records_does_not_mutate():
    before = {"level": "info", "x": 1}
    after = {"level": "info", "x": 2}
    before_copy = dict(before)
    diff_records(before, after)
    assert before == before_copy


# ---------------------------------------------------------------------------
# is_empty_diff
# ---------------------------------------------------------------------------

def test_is_empty_diff_true():
    assert is_empty_diff({"added": {}, "removed": {}, "changed": {}})


def test_is_empty_diff_false_when_added():
    assert not is_empty_diff({"added": {"k": 1}, "removed": {}, "changed": {}})


# ---------------------------------------------------------------------------
# diff_stream
# ---------------------------------------------------------------------------

def test_diff_stream_yields_changed_pairs():
    records = [
        {"level": "info", "count": 1},
        {"level": "info", "count": 2},
        {"level": "info", "count": 2},  # identical to previous – skipped
    ]
    results = list(diff_stream(iter(records)))
    assert len(results) == 1
    before, after, d = results[0]
    assert d["changed"]["count"] == {"before": 1, "after": 2}


def test_diff_stream_with_key_skips_different_group():
    records = [
        {"service": "a", "count": 1},
        {"service": "b", "count": 2},  # different key value – skip
        {"service": "b", "count": 3},  # same key value – compare
    ]
    results = list(diff_stream(iter(records), key="service"))
    assert len(results) == 1
    _, _, d = results[0]
    assert "count" in d["changed"]


def test_diff_stream_single_record_yields_nothing():
    records = [{"level": "info"}]
    assert list(diff_stream(iter(records))) == []


def test_diff_stream_empty_yields_nothing():
    assert list(diff_stream(iter([]))) == []
