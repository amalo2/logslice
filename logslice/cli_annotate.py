"""CLI entry point: annotate log records with metadata fields."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator, List, TextIO

from logslice.annotator import annotate_stream
from logslice.parser import parse_line


def build_annotate_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-annotate",
        description="Annotate JSON log records with computed metadata.",
    )
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Input files (default: stdin).",
    )
    p.add_argument(
        "--source",
        metavar="NAME",
        default=None,
        help="Tag every record with this source name (_source field).",
    )
    p.add_argument(
        "--watch",
        metavar="FIELD",
        action="append",
        dest="watch_fields",
        default=None,
        help="Fields to check for presence (may be repeated).",
    )
    p.add_argument(
        "--index-field",
        default="_index",
        metavar="FIELD",
        help="Name of the sequential index field (default: _index).",
    )
    p.add_argument(
        "--source-field",
        default="_source",
        metavar="FIELD",
    )
    p.add_argument(
        "--presence-field",
        default="_fields_present",
        metavar="FIELD",
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
        rec = parse_line(line.rstrip("\n"))
        if rec is not None:
            yield rec


def run_annotate(args: argparse.Namespace, out: TextIO = sys.stdout) -> int:
    raw_records = _parse_records(_iter_lines(args.files))
    annotated = annotate_stream(
        raw_records,
        source=args.source,
        watch_fields=args.watch_fields,
        index_field=args.index_field,
        source_field=args.source_field,
        presence_field=args.presence_field,
    )
    for record in annotated:
        out.write(json.dumps(record, separators=(",", ":")) + "\n")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_annotate_parser()
    args = parser.parse_args()
    sys.exit(run_annotate(args))


if __name__ == "__main__":  # pragma: no cover
    main()
