"""Tests for logslice.sampler."""

import pytest

from logslice.sampler import reservoir_sample, sample_records


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_records(n: int) -> list[dict]:
    return [{"index": i, "level": "info", "message": f"msg {i}"} for i in range(n)]


# ---------------------------------------------------------------------------
# sample_records — validation
# ---------------------------------------------------------------------------


def test_invalid_rate_zero():
    with pytest.raises(ValueError, match="rate"):
        list(sample_records(_make_records(10), 0.0))


def test_invalid_rate_negative():
    with pytest.raises(ValueError, match="rate"):
        list(sample_records(_make_records(10), -0.5))


def test_invalid_rate_above_one():
    with pytest.raises(ValueError, match="rate"):
        list(sample_records(_make_records(10), 1.1))


# ---------------------------------------------------------------------------
# sample_records — rate 1.0 keeps everything
# ---------------------------------------------------------------------------


def test_rate_one_keeps_all_deterministic():
    records = _make_records(50)
    result = list(sample_records(records, 1.0, deterministic=True))
    assert result == records


def test_rate_one_keeps_all_round_robin():
    records = _make_records(50)
    result = list(sample_records(records, 1.0, deterministic=False))
    assert result == records


# ---------------------------------------------------------------------------
# sample_records — deterministic mode
# ---------------------------------------------------------------------------


def test_deterministic_is_repeatable():
    records = _make_records(200)
    first = list(sample_records(records, 0.3, deterministic=True))
    second = list(sample_records(records, 0.3, deterministic=True))
    assert first == second


def test_deterministic_approximate_rate():
    records = _make_records(1000)
    result = list(sample_records(records, 0.5, deterministic=True))
    # Allow ±15 % tolerance around the expected count
    assert 350 <= len(result) <= 650


def test_deterministic_returns_subset():
    records = _make_records(100)
    result = list(sample_records(records, 0.2, deterministic=True))
    assert all(r in records for r in result)


# ---------------------------------------------------------------------------
# sample_records — round-robin mode
# ---------------------------------------------------------------------------


def test_round_robin_approximate_rate():
    records = _make_records(1000)
    result = list(sample_records(records, 0.25, deterministic=False))
    assert 200 <= len(result) <= 300


def test_round_robin_returns_subset():
    records = _make_records(100)
    result = list(sample_records(records, 0.5, deterministic=False))
    assert all(r in records for r in result)


# ---------------------------------------------------------------------------
# reservoir_sample
# ---------------------------------------------------------------------------


def test_reservoir_invalid_k():
    with pytest.raises(ValueError, match="k"):
        reservoir_sample(_make_records(10), 0)


def test_reservoir_returns_k_records():
    records = _make_records(100)
    result = reservoir_sample(records, 10)
    assert len(result) == 10


def test_reservoir_fewer_than_k():
    records = _make_records(5)
    result = reservoir_sample(records, 20)
    assert len(result) == 5


def test_reservoir_all_from_source():
    records = _make_records(50)
    result = reservoir_sample(records, 15)
    assert all(r in records for r in result)


def test_reservoir_exact_k():
    records = _make_records(10)
    result = reservoir_sample(records, 10)
    assert sorted(result, key=lambda r: r["index"]) == records
