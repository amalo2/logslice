"""CLI entry-point for the *split* sub-command.

Usage example::

    logslice-split --field level --output-dir ./out/ app.log
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterator

from logslice.splitter import split_stream, write_splits


def build_split_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    kwargs = dict(
        prog="logslice-split",
        description="Split a log stream into per-value files based on a field.",
    )
    if parent is not None:
        parser = parent.add_parser("split", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Input log files (default: stdin).",
    )
    parser.add_argument(
        "--field",
        "-f",
        required=True,
        metavar="FIELD",
        help="Record field whose value determines the output bucket.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default=".",
        metavar="DIR",
        help="Directory where split files are written (default: current dir).",
    )
    parser.add_argument(
        "--prefix",
        default="",
        help="Optional filename prefix for each output file.",
    )
    parser.add_argument(
        "--fallback",
        default="__other__",
        help="Bucket name for records missing the split field.",
    )
    return parser


def _iter_lines(files: list[str]) -> Iterator[str]:
    if not files:
        yield from sys.stdin
        return
    for path in files:
        with open(path, encoding="utf-8") as fh:
            yield from fh


def run_split(args: argparse.Namespace) -> int:
    lines = _iter_lines(args.files)
    buckets = split_stream(lines, field=args.field, fallback=args.fallback)
    if not buckets:
        print("No records found.", file=sys.stderr)
        return 0
    written = write_splits(
        buckets,
        output_dir=args.output_dir,
        prefix=args.prefix,
    )
    for key, path in sorted(written.items()):
        count = len(buckets[key])
        print(f"{key}: {count} record(s) -> {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_split_parser()
    args = parser.parse_args(argv)
    return run_split(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
