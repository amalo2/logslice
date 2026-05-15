"""CLI: bucket log records into fixed time windows and emit counts or records."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator

from logslice.parser import parse_line
from logslice.windower import window_counts, window_stream


def build_window_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-window",
        description="Bucket JSON log records into fixed-size time windows.",
    )
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Input files (default: stdin).",
    )
    p.add_argument(
        "-w",
        "--window",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Window size in seconds (default: 60).",
    )
    p.add_argument(
        "--counts",
        action="store_true",
        help="Emit one JSON object per window with start/count instead of records.",
    )
    p.add_argument(
        "--drop-missing-ts",
        action="store_true",
        help="Discard records that have no parseable timestamp.",
    )
    return p


def _iter_lines(files: list) -> Iterator[str]:
    if not files:
        yield from sys.stdin
        return
    for path in files:
        with open(path) as fh:
            yield from fh


def _parse_records(lines: Iterator[str]) -> Iterator[dict]:
    for line in lines:
        rec = parse_line(line.rstrip("\n"))
        if rec is not None:
            yield rec


def run_window(args: argparse.Namespace, out=sys.stdout) -> int:
    records = list(_parse_records(_iter_lines(args.files)))

    if args.counts:
        for start, count in window_counts(
            records,
            args.window,
            drop_missing_ts=args.drop_missing_ts,
        ):
            obj = {"window_start": start, "count": count}
            out.write(json.dumps(obj) + "\n")
    else:
        for start, bucket in window_stream(
            records,
            args.window,
            drop_missing_ts=args.drop_missing_ts,
        ):
            for rec in bucket:
                out.write(json.dumps(rec) + "\n")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_window_parser()
    args = parser.parse_args()
    sys.exit(run_window(args))


if __name__ == "__main__":  # pragma: no cover
    main()
