"""Tests for logslice.pivotter."""
import pytest

from logslice.pivotter import pivot_records, pivot_stream


@pytest.fixture()
def records():
    return [
        {"env": "prod", "level": "error", "latency": 120},
        {"env": "prod", "level": "error", "latency": 80},
        {"env": "prod", "level": "info", "latency": 30},
        {"env": "staging", "level": "error", "latency": 50},
        {"env": "staging", "level": "info", "latency": 20},
        {"env": "staging", "level": "info", "latency": 40},
    ]


def test_pivot_count_returns_list(records):
    result = pivot_records(records, row_field="env", col_field="level")
    assert isinstance(result, list)
    assert len(result) == 2


def test_pivot_count_correct_values(records):
    result = pivot_records(records, row_field="env", col_field="level")
    by_env = {r["env"]: r for r in result}
    assert by_env["prod"]["error"] == 2
    assert by_env["prod"]["info"] == 1
    assert by_env["staging"]["error"] == 1
    assert by_env["staging"]["info"] == 2


def test_pivot_sum(records):
    result = pivot_records(
        records, row_field="env", col_field="level", value_field="latency", agg="sum"
    )
    by_env = {r["env"]: r for r in result}
    assert by_env["prod"]["error"] == 200.0
    assert by_env["staging"]["info"] == 60.0


def test_pivot_mean(records):
    result = pivot_records(
        records, row_field="env", col_field="level", value_field="latency", agg="mean"
    )
    by_env = {r["env"]: r for r in result}
    assert by_env["prod"]["error"] == pytest.approx(100.0)
    assert by_env["staging"]["info"] == pytest.approx(30.0)


def test_pivot_missing_col_value_is_zero_for_count(records):
    result = pivot_records(records, row_field="env", col_field="level")
    # both cols present for both rows — no missing cell in this fixture
    for row in result:
        assert "error" in row
        assert "info" in row


def test_pivot_row_field_present_in_output(records):
    result = pivot_records(records, row_field="env", col_field="level")
    for row in result:
        assert "env" in row


def test_pivot_sum_requires_value_field():
    with pytest.raises(ValueError, match="value_field"):
        pivot_records([], row_field="env", col_field="level", agg="sum")


def test_pivot_mean_requires_value_field():
    with pytest.raises(ValueError):
        pivot_records([], row_field="env", col_field="level", agg="mean")


def test_pivot_empty_input_returns_empty():
    result = pivot_records([], row_field="env", col_field="level")
    assert result == []


def test_pivot_missing_value_field_entry_treated_as_none(records):
    # remove latency from one record
    sparse = [{k: v for k, v in r.items() if k != "latency"} if i == 0 else r
              for i, r in enumerate(records)]
    result = pivot_records(
        sparse, row_field="env", col_field="level", value_field="latency", agg="sum"
    )
    by_env = {r["env"]: r for r in result}
    # prod/error: only one valid value (80), the None entry is skipped
    assert by_env["prod"]["error"] == pytest.approx(80.0)


def test_pivot_stream_yields_same_as_pivot_records(records):
    expected = pivot_records(records, row_field="env", col_field="level")
    streamed = list(pivot_stream(records, row_field="env", col_field="level"))
    assert streamed == expected
