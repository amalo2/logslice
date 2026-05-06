"""CLI entry-point for the *sample* sub-command.

Allows users to draw a representative subset from a log stream:

    logslice sample --rate 0.1 app.log
    logslice sample --reservoir 500 app.log app2.log
    cat app.log | logslice sample --rate 0.25 --format pretty
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Iterator

from logslice.formatter import format_record
from logslice.parser import parse_line
from logslice.sampler import reservoir_sample, sample_records


def build_sample_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice sample",
        description="Sample a fraction of structured log records from one or more sources.",
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--rate",
        type=float,
        metavar="RATE",
        help="Fraction of records to keep, e.g. 0.1 for 10 %% (deterministic).",
    )
    group.add_argument(
        "--reservoir",
        type=int,
        metavar="K",
        help="Keep exactly K records chosen via reservoir sampling.",
    )
    p.add_argument(
        "--round-robin",
        action="store_true",
        default=False,
        help="Use round-robin instead of hash-based sampling (only with --rate).",
    )
    p.add_argument(
        "--format",
        choices=["pretty", "json"],
        default="pretty",
        help="Output format (default: pretty).",
    )
    p.add_argument(
        "sources",
        nargs="*",
        metavar="FILE",
        help="Log files to read.  Reads from stdin when omitted.",
    )
    return p


def _iter_lines(sources: list[str]) -> Iterator[str]:
    if not sources:
        yield from sys.stdin
        return
    for path in sources:
        with open(path) as fh:
            yield from fh


def _parse_records(lines: Iterable[str]) -> Iterator[dict]:
    for line in lines:
        record = parse_line(line)
        if record is not None:
            yield record


def run_sample(argv: list[str] | None = None) -> int:
    parser = build_sample_parser()
    args = parser.parse_args(argv)

    records = _parse_records(_iter_lines(args.sources))

    if args.reservoir is not None:
        sampled: Iterable[dict] = reservoir_sample(records, args.reservoir)
    else:
        sampled = sample_records(
            records,
            args.rate,
            deterministic=not args.round_robin,
        )

    for record in sampled:
        print(format_record(record, fmt=args.format))

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run_sample())
