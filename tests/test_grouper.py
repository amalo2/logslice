"""Tests for logslice.grouper."""

from __future__ import annotations

import pytest

from logslice.grouper import group_counts, group_records, group_stream


@pytest.fixture()
def records():
    return [
        {"level": "info", "service": "api", "msg": "started"},
        {"level": "error", "service": "api", "msg": "crash"},
        {"level": "info", "service": "worker", "msg": "started"},
        {"level": "info", "service": "api", "msg": "ready"},
        {"level": "error", "service": "worker", "msg": "timeout"},
    ]


def test_group_records_single_field(records):
    groups = group_records(records, ["level"])
    assert set(groups.keys()) == {("info",), ("error",)}


def test_group_records_single_field_counts(records):
    groups = group_records(records, ["level"])
    assert len(groups[("info",)]) == 3
    assert len(groups[("error",)]) == 2


def test_group_records_multi_field(records):
    groups = group_records(records, ["level", "service"])
    assert ("info", "api") in groups
    assert ("error", "worker") in groups
    assert len(groups) == 4


def test_group_records_missing_field_uses_none(records):
    groups = group_records(records, ["nonexistent"])
    assert list(groups.keys()) == [(None,)]
    assert len(groups[(None,)]) == len(records)


def test_group_records_empty_input():
    groups = group_records([], ["level"])
    assert groups == {}


def test_group_records_max_groups_limits(records):
    groups = group_records(records, ["level"], max_groups=1)
    assert len(groups) == 1


def test_group_records_max_groups_drops_overflow(records):
    groups = group_records(records, ["level", "service"], max_groups=2)
    assert len(groups) == 2
    total = sum(len(v) for v in groups.values())
    assert total < len(records)


def test_group_stream_yields_tuples(records):
    results = list(group_stream(records, ["level"]))
    assert all(isinstance(k, tuple) for k, _ in results)
    assert all(isinstance(b, list) for _, b in results)


def test_group_stream_insertion_order(records):
    keys = [k for k, _ in group_stream(records, ["level"])]
    assert keys[0] == ("info",)  # first seen
    assert keys[1] == ("error",)


def test_group_counts_returns_int_values(records):
    counts = group_counts(records, ["level"])
    assert all(isinstance(v, int) for v in counts.values())


def test_group_counts_sums_correctly(records):
    counts = group_counts(records, ["level"])
    assert sum(counts.values()) == len(records)


def test_group_counts_multi_field(records):
    counts = group_counts(records, ["level", "service"])
    assert counts[("info", "api")] == 2
    assert counts[("error", "api")] == 1
