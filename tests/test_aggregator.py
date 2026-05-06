"""Tests for logslice.aggregator."""
import pytest
from logslice.aggregator import Aggregator, aggregate_records, LEVEL_ORDER


@pytest.fixture()
def records():
    return [
        {"level": "info", "service": "api", "msg": "started"},
        {"level": "info", "service": "worker", "msg": "processing"},
        {"level": "error", "service": "api", "msg": "timeout"},
        {"level": "debug", "service": "api", "msg": "trace"},
        {"level": "warning", "service": "worker", "msg": "slow"},
        {"level": "critical", "service": "db", "msg": "down"},
    ]


def test_total_count(records):
    agg = Aggregator()
    for r in records:
        agg.add(r)
    assert agg.summary()["total"] == 6


def test_by_level_counts(records):
    agg = Aggregator()
    for r in records:
        agg.add(r)
    by_level = agg.summary()["by_level"]
    assert by_level["info"] == 2
    assert by_level["error"] == 1
    assert by_level["debug"] == 1
    assert by_level["warning"] == 1
    assert by_level["critical"] == 1


def test_by_level_all_keys_present(records):
    agg = Aggregator()
    for r in records:
        agg.add(r)
    by_level = agg.summary()["by_level"]
    for lvl in LEVEL_ORDER:
        assert lvl in by_level


def test_group_by(records):
    agg = Aggregator(group_by="service")
    for r in records:
        agg.add(r)
    summary = agg.summary()
    assert "by_group" in summary
    assert summary["by_group"]["field"] == "service"
    counts = summary["by_group"]["counts"]
    assert counts["api"] == 3
    assert counts["worker"] == 2
    assert counts["db"] == 1


def test_top_groups(records):
    agg = Aggregator(group_by="service")
    for r in records:
        agg.add(r)
    top = agg.top_groups(n=2)
    assert top[0][0] == "api"
    assert top[0][1] == 3
    assert len(top) == 2


def test_missing_group_field(records):
    agg = Aggregator(group_by="nonexistent")
    for r in records:
        agg.add(r)
    counts = agg.summary()["by_group"]["counts"]
    assert counts.get("<missing>") == 6


def test_unknown_level():
    agg = Aggregator()
    agg.add({"level": "verbose", "msg": "x"})
    summary = agg.summary()
    assert summary["by_level"].get("unknown") == 1


def test_aggregate_records_convenience(records):
    summary = aggregate_records(records, group_by="service")
    assert summary["total"] == 6
    assert "by_group" in summary


def test_empty_stream():
    summary = aggregate_records([])
    assert summary["total"] == 0
    assert all(v == 0 for v in summary["by_level"].values())
