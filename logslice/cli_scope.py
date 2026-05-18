"""CLI entry point for the `scope` sub-command.

Scope a stream of JSON log lines to a time window defined by --since and
--until (both expressed as epoch seconds, floats accepted).

Usage examples::

    logslice-scope --since 1700000000 --until 1700003600 app.log
    cat app.log | logslice-scope --since 1700000000
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator, List, Optional

from logslice.scoper import scope_records
from logslice.parser import parse_line


def build_scope_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-scope",
        description="Restrict JSON log records to a timestamp window.",
    )
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Input files (default: stdin).",
    )
    p.add_argument(
        "--since",
        type=float,
        default=None,
        metavar="TS",
        help="Keep records at or after this epoch timestamp.",
    )
    p.add_argument(
        "--until",
        type=float,
        default=None,
        metavar="TS",
        help="Keep records at or before this epoch timestamp.",
    )
    p.add_argument(
        "--drop-missing",
        action="store_true",
        default=False,
        help="Drop records that have no recognisable timestamp field.",
    )
    p.add_argument(
        "--output",
        choices=("json", "pretty"),
        default="json",
        help="Output format (default: json).",
    )
    return p


def _iter_lines(files: List[str]) -> Iterator[str]:
    if not files:
        yield from sys.stdin
        return
    for path in files:
        with open(path) as fh:
            yield from fh


def run_scope(args: argparse.Namespace, *, out=None) -> int:
    if out is None:
        out = sys.stdout

    raw_records = (
        parse_line(line)
        for line in _iter_lines(args.files)
    )
    parsed = (r for r in raw_records if r is not None)

    scoped = scope_records(
        parsed,
        since=args.since,
        until=args.until,
        drop_missing=args.drop_missing,
    )

    for record in scoped:
        if args.output == "pretty":
            ts = record.get("timestamp") or record.get("ts") or ""
            level = record.get("level", "").upper()
            msg = record.get("msg") or record.get("message", "")
            out.write(f"[{ts}] {level:5s} {msg}\n")
        else:
            out.write(json.dumps(record) + "\n")

    return 0


def main(argv: Optional[List[str]] = None) -> int:  # pragma: no cover
    parser = build_scope_parser()
    args = parser.parse_args(argv)
    return run_scope(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
