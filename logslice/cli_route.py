"""
logslice.cli_route
~~~~~~~~~~~~~~~~~~
CLI entry-point: route log records from stdin to per-destination JSONL files.

Usage example::

    cat app.log | python -m logslice.cli_route \\
        --rule level=error:errors.jsonl \\
        --rule service=auth:auth.jsonl \\
        --default default.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, IO, List, Optional

from logslice.parser import parse_line
from logslice.router import build_router, route_records


def build_route_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-route",
        description="Route structured JSON log lines to separate output files.",
    )
    p.add_argument(
        "--rule",
        metavar="FIELD=VALUE:DEST",
        action="append",
        dest="rules",
        default=[],
        help="Routing rule in the form field=value:destination_file. May be repeated.",
    )
    p.add_argument(
        "--default",
        metavar="FILE",
        default=None,
        help="File for unmatched records (omit to discard them).",
    )
    p.add_argument(
        "infile",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="Input file (default: stdin).",
    )
    return p


def _parse_rules(raw_rules: List[str]):
    """Parse 'field=value:dest' strings into (field, value, dest) tuples."""
    parsed = []
    for raw in raw_rules:
        try:
            condition, dest = raw.rsplit(":", 1)
            field_name, value = condition.split("=", 1)
        except ValueError:
            raise SystemExit(f"Invalid rule format (expected field=value:dest): {raw!r}")
        parsed.append((field_name.strip(), value.strip(), dest.strip()))
    return parsed


def run_route(args: argparse.Namespace) -> int:
    parsed_rules = _parse_rules(args.rules)
    router = build_router(parsed_rules, default="__default__")

    handles: Dict[str, IO] = {}

    def _get_handle(path: str) -> IO:
        if path not in handles:
            handles[path] = open(path, "w", encoding="utf-8")  # noqa: WPS515
        return handles[path]

    try:
        records = (parse_line(line) for line in args.infile)
        valid = (r for r in records if r is not None)
        for destination, record in route_records(valid, router):
            if destination == "__default__":
                if args.default is None:
                    continue
                fh = _get_handle(args.default)
            else:
                fh = _get_handle(destination)
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    finally:
        for fh in handles.values():
            fh.close()

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_route_parser()
    args = parser.parse_args(argv)
    return run_route(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
