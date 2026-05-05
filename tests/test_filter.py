"""Tests for logslice.filter."""

import pytest
from logslice.filter import (
    apply_filter,
    matches_fields,
    matches_level,
    matches_search,
)


@pytest.fixture
def info_record():
    return {"level": "info", "msg": "server started", "service": "api", "port": 8080}


@pytest.fixture
def error_record():
    return {"level": "error", "msg": "connection refused", "service": "db"}


# --- matches_level ---

def test_matches_level_equal(info_record):
    assert matches_level(info_record, "info") is True


def test_matches_level_above(error_record):
    assert matches_level(error_record, "info") is True


def test_matches_level_below(info_record):
    assert matches_level(info_record, "error") is False


def test_matches_level_missing_level_passes():
    assert matches_level({"msg": "hello"}, "error") is True


def test_matches_level_warn_alias():
    record = {"level": "warn", "msg": "low disk"}
    assert matches_level(record, "warning") is True


# --- matches_fields ---

def test_matches_fields_exact(info_record):
    assert matches_fields(info_record, {"service": "api"}) is True


def test_matches_fields_no_match(info_record):
    assert matches_fields(info_record, {"service": "worker"}) is False


def test_matches_fields_nested():
    record = {"user": {"id": 42}, "msg": "login"}
    assert matches_fields(record, {"user.id": 42}) is True


def test_matches_fields_integer(info_record):
    assert matches_fields(info_record, {"port": 8080}) is True


# --- matches_search ---

def test_matches_search_in_msg(info_record):
    assert matches_search(info_record, "started") is True


def test_matches_search_case_insensitive(error_record):
    assert matches_search(error_record, "CONNECTION") is True


def test_matches_search_no_match(info_record):
    assert matches_search(info_record, "timeout") is False


# --- apply_filter ---

def test_apply_filter_all_pass(info_record):
    assert apply_filter(info_record, min_level="info", fields={"service": "api"}, search="started") is True


def test_apply_filter_level_blocks(info_record):
    assert apply_filter(info_record, min_level="error") is False


def test_apply_filter_no_filters(info_record):
    assert apply_filter(info_record) is True
