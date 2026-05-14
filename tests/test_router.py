"""
Tests for logslice.router
"""
import pytest
from logslice.router import (
    Router,
    RoutingRule,
    build_router,
    route_records,
    group_by_destination,
)


@pytest.fixture()
def records():
    return [
        {"level": "error", "msg": "boom", "service": "auth"},
        {"level": "info",  "msg": "ok",   "service": "auth"},
        {"level": "warn",  "msg": "slow",  "service": "payments"},
        {"level": "error", "msg": "fail",  "service": "payments"},
        {"msg": "bare"},
    ]


def test_router_default_destination_when_no_rules(records):
    router = Router()
    for rec in records:
        assert router.route(rec) == "default"


def test_router_matches_first_rule():
    router = build_router([
        ("level", "error", "errors"),
        ("level", "error", "should_not_reach"),
    ])
    assert router.route({"level": "error"}) == "errors"


def test_router_falls_through_to_default():
    router = build_router([("level", "error", "errors")])
    assert router.route({"level": "info"}) == "default"


def test_router_custom_default():
    router = build_router([], default="catch_all")
    assert router.route({"level": "debug"}) == "catch_all"


def test_router_missing_field_does_not_match():
    router = build_router([("level", "error", "errors")])
    assert router.route({"msg": "no level here"}) == "default"


def test_add_rule_appends_in_order():
    router = Router()
    router.add_rule("service", "auth", "auth_sink")
    router.add_rule("level", "error", "error_sink")
    assert len(router.rules) == 2
    assert router.rules[0].destination == "auth_sink"
    assert router.rules[1].destination == "error_sink"


def test_route_records_yields_pairs(records):
    router = build_router([("level", "error", "errors")])
    pairs = list(route_records(records, router))
    assert len(pairs) == len(records)
    destinations = [d for d, _ in pairs]
    assert destinations.count("errors") == 2
    assert destinations.count("default") == 3


def test_group_by_destination_keys(records):
    router = build_router([
        ("level", "error", "errors"),
        ("service", "payments", "payments"),
    ])
    groups = group_by_destination(records, router)
    # Two error records go to 'errors'; the warn/payments record goes to 'payments';
    # remaining records go to 'default'.
    assert set(groups.keys()) == {"errors", "payments", "default"}
    assert len(groups["errors"]) == 2
    assert len(groups["payments"]) == 1


def test_group_by_destination_empty_input():
    router = build_router([("level", "error", "errors")])
    groups = group_by_destination([], router)
    assert groups == {}


def test_routing_rule_dataclass():
    rule = RoutingRule(field="level", value="warn", destination="warnings")
    assert rule.field == "level"
    assert rule.value == "warn"
    assert rule.destination == "warnings"
