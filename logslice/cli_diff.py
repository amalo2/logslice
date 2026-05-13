"""
logslice.cli_diff
~~~~~~~~~~~~~~~~~
CLI entry-point: compare consecutive JSON log records and print diffs.

Usage examples::

    logslice-diff app.log
    logslice-diff --key service --ignore ts --format json app.log
    cat app.log | logslice-diff -
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator, List, Optional

from logslice.parser import parse_line
from logslice.differ import diff_stream


def build_diff_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-diff",
        description="Show field-level diffs between consecutive JSON log records.",
    )
    p.add_argument(
        "sources",
        nargs="*",
        default=["-"],
        metavar="FILE",
        help="Log files to read (use '-' for stdin).",
    )
    p.add_argument(
        "--key",
        default=None,
        metavar="FIELD",
        help="Only diff consecutive records that share the same value for FIELD.",
    )
    p.add_argument(
        "--ignore",
        nargs="+",
        default=[],
        metavar="FIELD",
        help="Fields to exclude from comparison (e.g. timestamps).",
    )
    p.add_argument(
        "--format",
        choices=["pretty", "json"],
        default="pretty",
        help="Output format (default: pretty).",
    )
    return p


def _iter_lines(sources: List[str]) -> Iterator[str]:
    for src in sources:
        fh = sys.stdin if src == "-" else open(src)
        try:
            yield from fh
        finally:
            if src != "-":
                fh.close()


def _format_pretty(before: dict, after: dict, diff: dict) -> str:
    lines = []
    b_id = before.get("msg") or before.get("message") or json.dumps(before)
    a_id = after.get("msg") or after.get("message") or json.dumps(after)
    lines.append(f"--- {b_id}")
    lines.append(f"+++ {a_id}")
    for k, v in diff["added"].items():
        lines.append(f"  + {k}: {v!r}")
    for k, v in diff["removed"].items():
        lines.append(f"  - {k}: {v!r}")
    for k, chg in diff["changed"].items():
        lines.append(f"  ~ {k}: {chg['before']!r} -> {chg['after']!r}")
    return "\n".join(lines)


def run_diff(args: Optional[List[str]] = None) -> int:
    parser = build_diff_parser()
    ns = parser.parse_args(args)

    records = (
        r
        for line in _iter_lines(ns.sources)
        for r in [parse_line(line.rstrip("\n"))]
        if r is not None
    )

    found = False
    for before, after, diff in diff_stream(records, key=ns.key, ignore_keys=ns.ignore):
        found = True
        if ns.format == "json":
            print(json.dumps({"before": before, "after": after, "diff": diff}))
        else:
            print(_format_pretty(before, after, diff))
            print()

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_diff())


if __name__ == "__main__":  # pragma: no cover
    main()
