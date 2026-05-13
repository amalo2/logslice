"""CLI sub-command: transform — reshape log records before output."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator, List, Optional

from logslice.parser import parse_line
from logslice.transformer import transform_record


def build_transform_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(
        description="Transform fields in JSON log records.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    if parent is not None:
        parser = parent.add_parser("transform", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="logslice transform", **kwargs)

    parser.add_argument("files", nargs="*", metavar="FILE", help="Input files (default: stdin)")
    parser.add_argument(
        "--rename",
        nargs=2,
        metavar=("OLD", "NEW"),
        action="append",
        default=[],
        help="Rename a field: --rename old_name new_name",
    )
    parser.add_argument(
        "--drop",
        metavar="FIELD",
        action="append",
        default=[],
        help="Drop a field from output",
    )
    parser.add_argument(
        "--add",
        nargs=2,
        metavar=("KEY", "VALUE"),
        action="append",
        default=[],
        help="Add a field if absent: --add key value",
    )
    parser.add_argument(
        "--apply",
        nargs=2,
        metavar=("FIELD", "TRANSFORM"),
        action="append",
        default=[],
        help="Apply transform to a field: --apply field upper",
    )
    return parser


def _iter_lines(files: List[str]) -> Iterator[str]:
    if not files:
        yield from sys.stdin
        return
    for path in files:
        with open(path) as fh:
            yield from fh


def run_transform(args: argparse.Namespace) -> int:
    rename = {old: new for old, new in args.rename}
    add = {k: v for k, v in args.add}
    field_transforms = {field: tr for field, tr in args.apply}

    skipped = 0
    for raw in _iter_lines(args.files):
        record = parse_line(raw.rstrip("\n"))
        if record is None:
            skipped += 1
            continue
        result = transform_record(
            record,
            rename=rename or None,
            drop=args.drop or None,
            add=add or None,
            field_transforms=field_transforms or None,
        )
        sys.stdout.write(json.dumps(result) + "\n")

    if skipped:
        print(f"Warning: skipped {skipped} non-JSON line(s).", file=sys.stderr)

    return 0


def main() -> None:
    parser = build_transform_parser()
    args = parser.parse_args()
    sys.exit(run_transform(args))


if __name__ == "__main__":
    main()
