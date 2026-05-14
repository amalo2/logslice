"""CLI helpers for the `logslice export` sub-command.

This module wires the exporter into the CLI so users can redirect filtered
log output directly to a file in a chosen format::

    logslice export --format csv --output out.csv app.log
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from logslice.exporter import export_records, ExportFormat
from logslice.parser import parse_line
from logslice.query import parse_query
from logslice.pipeline import _matches


def build_export_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Register the *export* sub-command on *parent*."""
    p = parent.add_parser(
        "export",
        help="Export filtered log records to CSV, JSONL, or plain text.",
    )
    p.add_argument(
        "sources",
        nargs="*",
        metavar="FILE",
        help="Log files to read.  Omit to read from stdin.",
    )
    p.add_argument(
        "--format",
        dest="fmt",
        choices=["csv", "jsonl", "text"],
        default="jsonl",
        help="Output format (default: jsonl).",
    )
    p.add_argument(
        "--output",
        "-o",
        default="-",
        metavar="FILE",
        help="Destination file path.  Use - for stdout (default).",
    )
    p.add_argument(
        "--fields",
        nargs="+",
        metavar="FIELD",
        help="CSV columns to include (CSV format only).",
    )
    p.add_argument(
        "--query",
        "-q",
        action="append",
        default=[],
        metavar="EXPR",
        help="Filter expressions, e.g. level=ERROR  (repeatable).",
    )
    p.set_defaults(func=run_export)
    return p


def _iter_records(sources: list[str], queries: list[str]):
    """Yield parsed records from *sources* that match all *queries*."""
    parsed_queries = [parse_query(q) for q in queries]

    def _lines():
        if not sources:
            yield from sys.stdin
            return
        for path in sources:
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    yield from fh
            except OSError as exc:
                print(f"logslice export: cannot open '{path}': {exc}", file=sys.stderr)

    for raw in _lines():
        record = parse_line(raw.rstrip("\n"))
        if record is None:
            continue
        if all(_matches(record, q) for q in parsed_queries):
            yield record


def run_export(args: argparse.Namespace) -> int:
    """Entry point for the *export* sub-command."""
    records = list(_iter_records(args.sources, args.query))

    kwargs = {}
    if args.fmt == "csv" and args.fields:
        kwargs["fields"] = args.fields

    output = export_records(records, fmt=args.fmt, **kwargs)

    if args.output == "-":
        print(output)
    else:
        try:
            Path(args.output).write_text(output, encoding="utf-8")
        except OSError as exc:
            print(f"logslice export: cannot write '{args.output}': {exc}", file=sys.stderr)
            return 1

    return 0
