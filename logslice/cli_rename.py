"""
logslice.cli_rename
~~~~~~~~~~~~~~~~~~~
CLI entry-point for the ``logslice rename`` sub-command.

Usage examples::

    cat app.log | logslice-rename --map msg:message ts:timestamp
    logslice-rename --map msg:message --overwrite --input app.log
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator, TextIO

from logslice.parser import parse_line
from logslice.renamer import parse_mapping, rename_record


def build_rename_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    if parser is None:
        parser = argparse.ArgumentParser(
            prog="logslice-rename",
            description="Rename fields in structured JSON log records.",
        )
    parser.add_argument(
        "--map",
        metavar="OLD:NEW",
        nargs="+",
        required=True,
        help="One or more old:new field rename pairs.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite destination field if it already exists.",
    )
    parser.add_argument(
        "--input",
        metavar="FILE",
        default=None,
        help="Input file (default: stdin).",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Output file (default: stdout).",
    )
    return parser


def _iter_lines(source: TextIO) -> Iterator[str]:
    for line in source:
        yield line.rstrip("\n")


def run_rename(args: argparse.Namespace) -> int:
    try:
        mapping = parse_mapping(args.map)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    in_fh = open(args.input) if args.input else sys.stdin
    out_fh = open(args.output, "w") if args.output else sys.stdout

    try:
        for raw in _iter_lines(in_fh):
            record = parse_line(raw)
            if record is None:
                continue
            renamed = rename_record(record, mapping, overwrite=args.overwrite)
            out_fh.write(json.dumps(renamed, default=str) + "\n")
    finally:
        if args.input:
            in_fh.close()
        if args.output:
            out_fh.close()

    return 0


def main() -> None:  # pragma: no cover
    parser = build_rename_parser()
    args = parser.parse_args()
    sys.exit(run_rename(args))


if __name__ == "__main__":  # pragma: no cover
    main()
