"""CLI entry-point for the pivot command."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator, List

from logslice.parser import parse_line
from logslice.pivotter import pivot_records


def build_pivot_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        description="Pivot log records into a cross-tabulation table.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    if parent is not None:
        parser = parent.add_parser("pivot", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("row", help="Field to use as pivot rows")
    parser.add_argument("col", help="Field to use as pivot columns")
    parser.add_argument(
        "--value", default=None, metavar="FIELD",
        help="Numeric field to aggregate (required for --agg sum/mean)",
    )
    parser.add_argument(
        "--agg", default="count", choices=["count", "sum", "mean"],
        help="Aggregation function (default: count)",
    )
    parser.add_argument(
        "--pretty", action="store_true",
        help="Pretty-print output JSON",
    )
    parser.add_argument(
        "files", nargs="*", metavar="FILE",
        help="Input files (default: stdin)",
    )
    return parser


def _iter_lines(files: List[str]) -> Iterator[str]:
    if not files:
        yield from sys.stdin
        return
    for path in files:
        with open(path) as fh:
            yield from fh


def _parse_records(files: List[str]) -> List[dict]:
    records = []
    for line in _iter_lines(files):
        rec = parse_line(line)
        if rec is not None:
            records.append(rec)
    return records


def run_pivot(args: argparse.Namespace, out=sys.stdout) -> int:
    records = _parse_records(args.files)
    try:
        table = pivot_records(
            records,
            row_field=args.row,
            col_field=args.col,
            value_field=args.value,
            agg=args.agg,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    for row in table:
        out.write(json.dumps(row, indent=indent) + "\n")
    return 0


def main(argv: List[str] | None = None) -> None:
    parser = build_pivot_parser()
    args = parser.parse_args(argv)
    sys.exit(run_pivot(args))


if __name__ == "__main__":  # pragma: no cover
    main()
