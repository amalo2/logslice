"""CLI entry-point for the *group* sub-command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator, List, TextIO

from logslice.grouper import group_stream
from logslice.parser import parse_line


def build_group_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="logslice group",
        description="Group JSON log records by one or more fields.",
    )
    parser = parent.add_parser("group", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument(
        "fields",
        nargs="+",
        metavar="FIELD",
        help="Field name(s) to group by.",
    )
    parser.add_argument(
        "--max-groups",
        type=int,
        default=None,
        metavar="N",
        help="Maximum number of distinct groups to emit.",
    )
    parser.add_argument(
        "--counts-only",
        action="store_true",
        help="Emit only group keys and counts instead of full records.",
    )
    parser.add_argument(
        "--input",
        "-i",
        default="-",
        metavar="FILE",
        help="Input file (default: stdin).",
    )
    return parser


def _iter_lines(path: str) -> Iterator[str]:
    if path == "-":
        yield from sys.stdin
    else:
        with open(path) as fh:
            yield from fh


def run_group(args: argparse.Namespace, out: TextIO = sys.stdout) -> int:
    records = (
        r
        for line in _iter_lines(args.input)
        if (r := parse_line(line)) is not None
    )

    for key, batch in group_stream(records, args.fields, max_groups=args.max_groups):
        key_dict = dict(zip(args.fields, key))
        if args.counts_only:
            out.write(json.dumps({**key_dict, "_count": len(batch)}) + "\n")
        else:
            out.write(json.dumps({"_group": key_dict, "_count": len(batch), "records": batch}) + "\n")
    return 0


def main(argv: List[str] | None = None) -> int:  # pragma: no cover
    parser = build_group_parser()
    args = parser.parse_args(argv)
    return run_group(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
