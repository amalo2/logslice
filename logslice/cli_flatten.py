"""
logslice.cli_flatten
~~~~~~~~~~~~~~~~~~~~
CLI entry-point: flatten nested JSON log records.

Usage examples
--------------
    cat app.log | python -m logslice.cli_flatten
    python -m logslice.cli_flatten --separator __ --max-depth 1 app.log
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable, Iterator

from logslice.flattener import flatten_record
from logslice.parser import parse_line


def build_flatten_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-flatten",
        description="Flatten nested JSON log records into dot-notation keys.",
    )
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Input files (default: stdin).",
    )
    p.add_argument(
        "--separator",
        default=".",
        metavar="SEP",
        help="Key separator (default: '.').",
    )
    p.add_argument(
        "--max-depth",
        type=int,
        default=0,
        metavar="N",
        help="Maximum nesting depth to flatten; 0 = unlimited (default: 0).",
    )
    p.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Silently skip lines that cannot be parsed as JSON.",
    )
    return p


def _iter_lines(files: list[str]) -> Iterator[str]:
    if not files:
        yield from sys.stdin
        return
    for path in files:
        with open(path) as fh:
            yield from fh


def run_flatten(
    lines: Iterable[str],
    separator: str = ".",
    max_depth: int = 0,
    skip_invalid: bool = False,
    out=None,
) -> int:
    if out is None:
        out = sys.stdout
    errors = 0
    for line in lines:
        record = parse_line(line.rstrip("\n"))
        if record is None:
            if not skip_invalid and line.strip():
                print(
                    f"logslice-flatten: could not parse line: {line.rstrip()}",
                    file=sys.stderr,
                )
                errors += 1
            continue
        flat = flatten_record(record, separator=separator, max_depth=max_depth)
        out.write(json.dumps(flat, ensure_ascii=False) + "\n")
    return 0 if errors == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_flatten_parser()
    args = parser.parse_args(argv)
    lines = _iter_lines(args.files)
    return run_flatten(
        lines,
        separator=args.separator,
        max_depth=args.max_depth,
        skip_invalid=args.skip_invalid,
    )


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
