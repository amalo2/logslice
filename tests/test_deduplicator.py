"""Tests for logslice.deduplicator."""

import pytest

from logslice.deduplicator import count_duplicates, deduplicate, _fingerprint


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def records():
    return [
        {"level": "info", "msg": "started", "service": "api"},
        {"level": "info", "msg": "started", "service": "api"},  # exact dup
        {"level": "error", "msg": "failed", "service": "api"},
        {"level": "info", "msg": "started", "service": "worker"},  # different service
        {"level": "error", "msg": "failed", "service": "api"},  # exact dup
    ]


# ---------------------------------------------------------------------------
# _fingerprint
# ---------------------------------------------------------------------------

def test_fingerprint_same_record_is_stable():
    r = {"level": "info", "msg": "hello"}
    assert _fingerprint(r) == _fingerprint(r)


def test_fingerprint_different_records_differ():
    r1 = {"level": "info", "msg": "hello"}
    r2 = {"level": "error", "msg": "hello"}
    assert _fingerprint(r1) != _fingerprint(r2)


def test_fingerprint_with_keys_ignores_other_fields():
    r1 = {"level": "info", "msg": "hello", "ts": "2024-01-01"}
    r2 = {"level": "info", "msg": "hello", "ts": "2024-06-01"}
    assert _fingerprint(r1, keys=["level", "msg"]) == _fingerprint(r2, keys=["level", "msg"])


def test_fingerprint_missing_key_treated_as_none():
    r1 = {"level": "info"}
    r2 = {"level": "info", "msg": None}
    # both yield msg=None when keyed on ["level", "msg"]
    assert _fingerprint(r1, keys=["level", "msg"]) == _fingerprint(r2, keys=["level", "msg"])


# ---------------------------------------------------------------------------
# deduplicate
# ---------------------------------------------------------------------------

def test_deduplicate_removes_exact_duplicates(records):
    result = list(deduplicate(records))
    assert len(result) == 3


def test_deduplicate_preserves_order(records):
    result = list(deduplicate(records))
    assert result[0]["msg"] == "started"
    assert result[1]["msg"] == "failed"


def test_deduplicate_by_keys_collapses_on_subset(records):
    # Using only "level" + "msg" collapses "started/api" and "started/worker"
    result = list(deduplicate(records, keys=["level", "msg"]))
    assert len(result) == 2


def test_deduplicate_empty_input():
    assert list(deduplicate([])) == []


def test_deduplicate_no_duplicates_returns_all():
    recs = [{"id": i} for i in range(5)]
    assert list(deduplicate(recs)) == recs


def test_deduplicate_max_seen_evicts_old_entries():
    # With max_seen=2 the first fingerprint is evicted after 3 unique records,
    # so a later re-occurrence of the first record is treated as new.
    recs = [
        {"id": 1},
        {"id": 2},
        {"id": 3},
        {"id": 1},  # would normally be a dup, but evicted with max_seen=2
    ]
    result = list(deduplicate(recs, max_seen=2))
    assert len(result) == 4


# ---------------------------------------------------------------------------
# count_duplicates
# ---------------------------------------------------------------------------

def test_count_duplicates_total(records):
    total, _ = count_duplicates(records)
    assert total == 5


def test_count_duplicates_count(records):
    _, dupes = count_duplicates(records)
    assert dupes == 2


def test_count_duplicates_no_dupes():
    recs = [{"id": i} for i in range(4)]
    total, dupes = count_duplicates(recs)
    assert total == 4
    assert dupes == 0


def test_count_duplicates_with_keys(records):
    _, dupes = count_duplicates(records, keys=["level", "msg"])
    assert dupes == 3  # two "started" dups + one "failed" dup
