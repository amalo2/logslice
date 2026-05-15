"""CLI entry point for joining two JSONL log files on a shared key."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator, TextIO

from logslice.joiner import join_streams
from logslice.parser import parse_line


def build_join_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-join",
        description="Join two JSONL streams on a shared key field.",
    )
    p.add_argument("left", help="Path to the left JSONL file (use '-' for stdin)")
    p.add_argument("right", help="Path to the right JSONL file")
    p.add_argument("-k", "--key", required=True, help="Field name to join on")
    p.add_argument(
        "--how",
        choices=["inner", "left"],
        default="inner",
        help="Join strategy (default: inner)",
    )
    p.add_argument(
        "--prefix-left",
        default="left_",
        metavar="PREFIX",
        help="Prefix for left-side fields (default: 'left_')",
    )
    p.add_argument(
        "--prefix-right",
        default="right_",
        metavar="PREFIX",
        help="Prefix for right-side fields (default: 'right_')",
    )
    return p


def _iter_records(path: str) -> Iterator[dict]:
    """Open *path* (or stdin when '-') and yield parsed JSON records."""
    fh: TextIO
    if path == "-":
        fh = sys.stdin
        close = False
    else:
        fh = open(path, "r", encoding="utf-8")
        close = True
    try:
        for raw in fh:
            rec = parse_line(raw)
            if rec is not None:
                yield rec
    finally:
        if close:
            fh.close()


def run_join(args: argparse.Namespace, out: TextIO = sys.stdout) -> int:
    left_records = list(_iter_records(args.left))
    right_records = list(_iter_records(args.right))

    for merged in join_streams(
        left_records,
        right_records,
        key=args.key,
        how=args.how,
        prefix_left=args.prefix_left,
        prefix_right=args.prefix_right,
    ):
        out.write(json.dumps(merged, default=str) + "\n")

    return 0


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = build_join_parser()
    args = parser.parse_args(argv)
    try:
        sys.exit(run_join(args))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":  # pragma: no cover
    main()
