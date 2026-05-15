"""Tests for logslice.windower."""

import pytest

from logslice.windower import (
    _bucket_key,
    _extract_ts,
    window_counts,
    window_records,
    window_stream,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _rec(ts=None, **extra):
    r = dict(extra)
    if ts is not None:
        r["timestamp"] = ts
    return r


# ---------------------------------------------------------------------------
# _extract_ts
# ---------------------------------------------------------------------------

def test_extract_ts_from_timestamp_key():
    assert _extract_ts({"timestamp": 1000.0}) == 1000.0


def test_extract_ts_from_ts_key():
    assert _extract_ts({"ts": 500}) == 500.0


def test_extract_ts_returns_none_when_missing():
    assert _extract_ts({"msg": "hello"}) is None


def test_extract_ts_returns_none_for_non_numeric():
    assert _extract_ts({"timestamp": "2024-01-01"}) is None


# ---------------------------------------------------------------------------
# _bucket_key
# ---------------------------------------------------------------------------

def test_bucket_key_exact_boundary():
    assert _bucket_key(60.0, 60.0) == 60.0


def test_bucket_key_mid_window():
    assert _bucket_key(75.0, 60.0) == 60.0


def test_bucket_key_start_of_window():
    assert _bucket_key(0.0, 60.0) == 0.0


# ---------------------------------------------------------------------------
# window_records
# ---------------------------------------------------------------------------

def test_window_records_groups_correctly():
    records = [_rec(10), _rec(20), _rec(70), _rec(130)]
    result = window_records(records, 60.0)
    assert set(result.keys()) == {0.0, 60.0, 120.0}
    assert len(result[0.0]) == 2
    assert len(result[60.0]) == 1


def test_window_records_no_ts_goes_to_none_key():
    records = [_rec(), _rec(10)]
    result = window_records(records, 60.0)
    assert None in result
    assert len(result[None]) == 1


def test_window_records_drop_missing_ts():
    records = [_rec(), _rec(10)]
    result = window_records(records, 60.0, drop_missing_ts=True)
    assert None not in result
    assert len(result[0.0]) == 1


def test_window_records_invalid_window_raises():
    with pytest.raises(ValueError):
        window_records([], 0)


def test_window_records_negative_window_raises():
    with pytest.raises(ValueError):
        window_records([], -5.0)


# ---------------------------------------------------------------------------
# window_stream
# ---------------------------------------------------------------------------

def test_window_stream_yields_sorted_windows():
    records = [_rec(130), _rec(10), _rec(70)]
    starts = [start for start, _ in window_stream(records, 60.0)]
    assert starts == sorted(starts)


def test_window_stream_none_bucket_last():
    records = [_rec(), _rec(10)]
    pairs = list(window_stream(records, 60.0))
    assert pairs[-1][0] is None


def test_window_stream_empty_input():
    assert list(window_stream([], 60.0)) == []


# ---------------------------------------------------------------------------
# window_counts
# ---------------------------------------------------------------------------

def test_window_counts_correct_totals():
    records = [_rec(10), _rec(20), _rec(70)]
    counts = dict(window_counts(records, 60.0))
    assert counts[0.0] == 2
    assert counts[60.0] == 1


def test_window_counts_empty_input():
    assert list(window_counts([], 60.0)) == []
