"""CLI entry-point for the ``logslice cast`` sub-command.

Reads JSON log records from one or more files (or stdin), casts the
specified fields to new types, and writes the results to stdout.

Usage example::

    logslice cast --cast status:int latency:float -- app.log
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator, List, TextIO

from logslice.caster import cast_fields, parse_cast_specs
from logslice.parser import parse_line


def build_cast_parser(sub: "argparse._SubParsersAction | None" = None) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="logslice cast",
        description="Cast field values to new types in JSON log records.",
    )
    parser = sub.add_parser("cast", **kwargs) if sub is not None else argparse.ArgumentParser(**kwargs)
    parser.add_argument(
        "--cast",
        metavar="FIELD:TYPE",
        nargs="+",
        default=[],
        help="One or more field:type pairs, e.g. status:int latency:float.",
    )
    parser.add_argument(
        "--output",
        choices=("json", "pretty"),
        default="json",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "files",
        metavar="FILE",
        nargs="*",
        help="Input files.  Reads from stdin when omitted.",
    )
    return parser


def _iter_lines(files: List[str]) -> Iterator[str]:
    if not files:
        yield from sys.stdin
        return
    for path in files:
        with open(path) as fh:
            yield from fh


def run_cast(args: argparse.Namespace, stdout: TextIO = sys.stdout) -> int:
    try:
        casts = parse_cast_specs(args.cast)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for raw in _iter_lines(args.files):
        record = parse_line(raw)
        if record is None:
            continue
        result = cast_fields(record, casts)
        if args.output == "json":
            stdout.write(json.dumps(result, default=str) + "\n")
        else:
            parts = [f"{k}={v!r}" for k, v in result.items()]
            stdout.write(" ".join(parts) + "\n")

    return 0


def main(argv: List[str] | None = None) -> None:
    parser = build_cast_parser()
    args = parser.parse_args(argv)
    sys.exit(run_cast(args))


if __name__ == "__main__":
    main()
