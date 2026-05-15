"""Tests for logslice.joiner."""
import pytest

from logslice.joiner import inner_join, join_streams, left_join


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def left_records():
    return [
        {"id": 1, "service": "auth", "level": "error"},
        {"id": 2, "service": "api", "level": "info"},
        {"id": 3, "service": "db", "level": "warn"},
    ]


@pytest.fixture()
def right_records():
    return [
        {"id": 1, "region": "us-east", "owner": "alice"},
        {"id": 2, "region": "eu-west", "owner": "bob"},
    ]


# ---------------------------------------------------------------------------
# inner_join
# ---------------------------------------------------------------------------

def test_inner_join_only_matching_keys(left_records, right_records):
    result = list(inner_join(left_records, right_records, key="id"))
    assert len(result) == 2


def test_inner_join_key_not_duplicated(left_records, right_records):
    result = list(inner_join(left_records, right_records, key="id"))
    for rec in result:
        assert list(rec.keys()).count("id") == 1


def test_inner_join_prefixes_applied(left_records, right_records):
    result = list(inner_join(left_records, right_records, key="id"))
    assert "left_service" in result[0]
    assert "right_region" in result[0]


def test_inner_join_correct_values(left_records, right_records):
    result = list(inner_join(left_records, right_records, key="id"))
    auth_rec = next(r for r in result if r["id"] == 1)
    assert auth_rec["left_service"] == "auth"
    assert auth_rec["right_owner"] == "alice"


def test_inner_join_excludes_unmatched_left(left_records, right_records):
    result = list(inner_join(left_records, right_records, key="id"))
    ids = [r["id"] for r in result]
    assert 3 not in ids


def test_inner_join_record_missing_key_is_skipped():
    left = [{"service": "auth"}, {"id": 1, "service": "api"}]
    right = [{"id": 1, "region": "us"}]
    result = list(inner_join(left, right, key="id"))
    assert len(result) == 1


# ---------------------------------------------------------------------------
# left_join
# ---------------------------------------------------------------------------

def test_left_join_keeps_all_left_records(left_records, right_records):
    result = list(left_join(left_records, right_records, key="id"))
    assert len(result) == 3


def test_left_join_unmatched_has_no_right_fields(left_records, right_records):
    result = list(left_join(left_records, right_records, key="id"))
    unmatched = next(r for r in result if r["id"] == 3)
    assert "right_region" not in unmatched
    assert "right_owner" not in unmatched


def test_left_join_matched_has_right_fields(left_records, right_records):
    result = list(left_join(left_records, right_records, key="id"))
    matched = next(r for r in result if r["id"] == 1)
    assert matched["right_region"] == "us-east"


# ---------------------------------------------------------------------------
# join_streams dispatch
# ---------------------------------------------------------------------------

def test_join_streams_inner(left_records, right_records):
    result = list(join_streams(left_records, right_records, key="id", how="inner"))
    assert len(result) == 2


def test_join_streams_left(left_records, right_records):
    result = list(join_streams(left_records, right_records, key="id", how="left"))
    assert len(result) == 3


def test_join_streams_invalid_how_raises(left_records, right_records):
    with pytest.raises(ValueError, match="Unsupported join type"):
        list(join_streams(left_records, right_records, key="id", how="outer"))


def test_join_streams_empty_right(left_records):
    result = list(join_streams(left_records, [], key="id", how="inner"))
    assert result == []


def test_join_streams_empty_left(right_records):
    result = list(join_streams([], right_records, key="id", how="left"))
    assert result == []
