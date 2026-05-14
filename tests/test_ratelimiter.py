import pytest
from logslice.ratelimiter import rate_limit, _bucket, _extract_ts


def _rec(ts=None, level="info", msg="hello", service=None):
    r = {"level": level, "message": msg}
    if ts is not None:
        r["timestamp"] = ts
    if service is not None:
        r["service"] = service
    return r


# ---------------------------------------------------------------------------
# _extract_ts
# ---------------------------------------------------------------------------

def test_extract_ts_from_timestamp_key():
    assert _extract_ts({"timestamp": 1000.0}) == 1000.0


def test_extract_ts_from_ts_key():
    assert _extract_ts({"ts": "1500"}) == 1500.0


def test_extract_ts_returns_none_when_missing():
    assert _extract_ts({"message": "hi"}) is None


def test_extract_ts_returns_none_on_non_numeric():
    assert _extract_ts({"timestamp": "not-a-number"}) is None


# ---------------------------------------------------------------------------
# _bucket
# ---------------------------------------------------------------------------

def test_bucket_second_granularity():
    assert _bucket(1000.9, "second") == 1000


def test_bucket_minute_granularity():
    assert _bucket(120.0, "minute") == 2


def test_bucket_hour_granularity():
    assert _bucket(7200.0, "hour") == 2


# ---------------------------------------------------------------------------
# rate_limit — basic
# ---------------------------------------------------------------------------

def test_invalid_limit_raises():
    with pytest.raises(ValueError, match="limit must be"):
        list(rate_limit([], limit=0))


def test_invalid_unit_raises():
    with pytest.raises(ValueError, match="unit must be"):
        list(rate_limit([_rec(ts=1.0)], limit=1, unit="week"))  # type: ignore[arg-type]


def test_all_pass_when_under_limit():
    records = [_rec(ts=float(i)) for i in range(5)]
    result = list(rate_limit(records, limit=10, unit="second"))
    assert len(result) == 5


def test_drops_excess_in_same_bucket():
    # all records share the same second-bucket (ts 0.0 – 0.9)
    records = [_rec(ts=0.1 * i) for i in range(10)]
    result = list(rate_limit(records, limit=3, unit="second"))
    assert len(result) == 3


def test_limit_resets_across_buckets():
    # 3 records in bucket 0, 3 records in bucket 1
    bucket0 = [_rec(ts=0.1 * i) for i in range(3)]
    bucket1 = [_rec(ts=1.0 + 0.1 * i) for i in range(3)]
    result = list(rate_limit(bucket0 + bucket1, limit=2, unit="second"))
    assert len(result) == 4  # 2 from each bucket


def test_no_timestamp_uses_monotonic_counter():
    records = [_rec() for _ in range(6)]
    result = list(rate_limit(records, limit=2, unit="second"))
    # Without timestamps every record lands in its own seq-bucket, all pass
    assert len(result) == 6


# ---------------------------------------------------------------------------
# rate_limit — group_by
# ---------------------------------------------------------------------------

def test_group_by_applies_limit_per_group():
    # 4 records per service in the same bucket
    records = [
        _rec(ts=0.0, service="svc-a"),
        _rec(ts=0.1, service="svc-a"),
        _rec(ts=0.2, service="svc-a"),
        _rec(ts=0.3, service="svc-b"),
        _rec(ts=0.4, service="svc-b"),
        _rec(ts=0.5, service="svc-b"),
    ]
    result = list(rate_limit(records, limit=2, unit="second", group_by="service"))
    assert len(result) == 4  # 2 per service


def test_group_by_missing_field_grouped_together():
    records = [_rec(ts=0.1 * i) for i in range(6)]  # no 'service' field
    result = list(rate_limit(records, limit=2, unit="second", group_by="service"))
    assert len(result) == 2
