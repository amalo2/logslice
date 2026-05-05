"""Command-line interface for logslice."""

import sys
import argparse
from typing import List, Optional

from logslice.pipeline import process_sources, count_matches
from logslice.query import parse_query


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Stream and filter structured JSON logs from multiple sources.",
    )
    parser.add_argument(
        "sources",
        nargs="*",
        metavar="FILE",
        help="Log files to read. Use '-' or omit for stdin.",
    )
    parser.add_argument(
        "-l", "--level",
        metavar="LEVEL",
        help="Minimum log level to include (e.g. warn, error).",
    )
    parser.add_argument(
        "-q", "--query",
        metavar="EXPR",
        action="append",
        dest="queries",
        default=[],
        help="Field filter expression, e.g. 'service=api' or 'latency>200'. May be repeated.",
    )
    parser.add_argument(
        "-s", "--search",
        metavar="TEXT",
        help="Full-text search string to match anywhere in the record.",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["pretty", "json"],
        default="pretty",
        help="Output format (default: pretty).",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Print only the count of matching records.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    sources = args.sources if args.sources else ["-"]
    queries = [parse_query(q) for q in args.queries]

    streams = []
    opened = []
    try:
        for src in sources:
            if src == "-":
                streams.append(sys.stdin)
            else:
                fh = open(src, "r", encoding="utf-8")
                opened.append(fh)
                streams.append(fh)

        if args.count:
            total = count_matches(
                streams,
                level=args.level,
                queries=queries,
                search=args.search,
            )
            print(total)
        else:
            for line in process_sources(
                streams,
                level=args.level,
                queries=queries,
                search=args.search,
                fmt=args.format,
            ):
                print(line)
    finally:
        for fh in opened:
            fh.close()

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
