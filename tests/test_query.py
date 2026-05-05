"""Tests for logslice.query."""

import pytest
from logslice.query import Query, _coerce, parse_query


# --- _coerce ---

def test_coerce_int():
    assert _coerce("42") == 42


def test_coerce_float():
    assert _coerce("3.14") == 3.14


def test_coerce_bool_true():
    assert _coerce("true") is True


def test_coerce_bool_false():
    assert _coerce("False") is False


def test_coerce_string():
    assert _coerce("api") == "api"


# --- parse_query ---

def test_parse_empty_query():
    q = parse_query("")
    assert q.min_level is None
    assert q.fields == {}
    assert q.search is None


def test_parse_level_only():
    q = parse_query("level:error")
    assert q.min_level == "error"
    assert q.fields == {}
    assert q.search is None


def test_parse_field_string():
    q = parse_query("service=api")
    assert q.fields == {"service": "api"}


def test_parse_field_integer():
    q = parse_query("port=8080")
    assert q.fields == {"port": 8080}


def test_parse_nested_field():
    q = parse_query("user.id=42")
    assert q.fields == {"user.id": 42}


def test_parse_search_text():
    q = parse_query("connection refused")
    assert q.search == "connection refused"
    assert q.min_level is None


def test_parse_combined():
    q = parse_query("level:warn service=db connection timeout")
    assert q.min_level == "warn"
    assert q.fields == {"service": "db"}
    assert q.search == "connection timeout"


def test_parse_quoted_search():
    q = parse_query('level:info "server started"')
    assert q.min_level == "info"
    assert q.search == "server started"


def test_query_repr_exists():
    q = Query(min_level="info", fields={"k": "v"}, search="test")
    assert isinstance(repr(q), str)
