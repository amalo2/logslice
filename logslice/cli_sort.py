"""CLI entry-point for the sort sub-command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator

from logslice.parser import parse_line
from logslice.sorter import sort_stream


def build_sort_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="logslice sort",
        description="Sort JSON log records by one or more fields.",
    )
    parser = (
        parent.add_parser("sort", **kwargs)  # type: ignore[arg-type]
        if parent is not None
        else argparse.ArgumentParser(**kwargs)
    )
    parser.add_argument(
        "fields",
        nargs="+",
        metavar="FIELD",
        help="Fields to sort by, in priority order.",
    )
    parser.add_argument(
        "--desc",
        action="store_true",
        default=False,
        help="Sort in descending order.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Emit at most N records after sorting.",
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


def run_sort(args: argparse.Namespace) -> int:
    raw_records = (
        parse_line(line)
        for line in _iter_lines(args.input)
    )
    records = (r for r in raw_records if r is not None)

    for record in sort_stream(
        records,
        args.fields,
        reverse=args.desc,
        limit=args.limit,
    ):
        sys.stdout.write(json.dumps(record) + "\n")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_sort_parser()
    args = parser.parse_args()
    sys.exit(run_sort(args))


if __name__ == "__main__":  # pragma: no cover
    main()
