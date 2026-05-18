"""CLI entry-point for the compactor: merge consecutive records sharing a key."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator, List, Optional

from logslice.compactor import compact_stream
from logslice.parser import parse_line


def build_compact_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-compact",
        description="Merge consecutive JSON log records that share a key field.",
    )
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Input files (default: stdin).",
    )
    p.add_argument(
        "--key",
        required=True,
        metavar="FIELD",
        help="Field name used to group consecutive records.",
    )
    p.add_argument(
        "--count-field",
        default="_count",
        metavar="FIELD",
        help="Output field that holds the merge count (default: _count).",
    )
    p.add_argument(
        "--merge",
        dest="merge_fields",
        nargs="+",
        metavar="FIELD",
        default=None,
        help="Additional fields whose values are collected into a list.",
    )
    return p


def _iter_lines(files: List[str]) -> Iterator[str]:
    if not files:
        yield from sys.stdin
        return
    for path in files:
        with open(path) as fh:
            yield from fh


def _parse_records(lines: Iterator[str]) -> Iterator[dict]:
    for line in lines:
        record = parse_line(line.rstrip("\n"))
        if record is not None:
            yield record


def run_compact(args: argparse.Namespace, out=sys.stdout) -> int:
    lines = _iter_lines(args.files)
    records = _parse_records(lines)
    compacted = compact_stream(
        records,
        key=args.key,
        count_field=args.count_field,
        merge_fields=args.merge_fields,
    )
    for record in compacted:
        out.write(json.dumps(record, default=str) + "\n")
    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_compact_parser()
    args = parser.parse_args(argv)
    sys.exit(run_compact(args))


if __name__ == "__main__":  # pragma: no cover
    main()
