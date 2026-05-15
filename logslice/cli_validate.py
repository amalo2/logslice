"""CLI entry-point for validating a stream of JSON log records."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.parser import parse_line
from logslice.validator import validate_record


def build_validate_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-validate",
        description="Validate structured JSON log records against a schema.",
    )
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Log files to validate (default: stdin).",
    )
    p.add_argument(
        "--require",
        dest="required",
        action="append",
        default=[],
        metavar="FIELD",
        help="Field that must be present (repeatable).",
    )
    p.add_argument(
        "--type",
        dest="field_types",
        action="append",
        default=[],
        metavar="FIELD:TYPE",
        help="Expected type for a field, e.g. code:int (repeatable).",
    )
    p.add_argument(
        "--drop",
        action="store_true",
        default=False,
        help="Suppress invalid records from output; only print valid ones.",
    )
    p.add_argument(
        "--errors-only",
        action="store_true",
        default=False,
        help="Only print records that fail validation.",
    )
    return p


def _parse_field_types(specs: List[str]) -> dict:
    result = {}
    for spec in specs:
        if ":" not in spec:
            raise SystemExit(f"Invalid --type spec (expected FIELD:TYPE): {spec!r}")
        field, _, type_name = spec.partition(":")
        result[field.strip()] = type_name.strip()
    return result


def _iter_lines(files: List[str]):
    if not files:
        yield from sys.stdin
        return
    for path in files:
        with open(path) as fh:
            yield from fh


def run_validate(args: argparse.Namespace) -> int:
    field_types = _parse_field_types(args.field_types)
    invalid_count = 0
    total = 0

    for raw in _iter_lines(args.files):
        record = parse_line(raw)
        if record is None:
            continue
        total += 1
        valid, errors = validate_record(
            record, required=args.required, field_types=field_types
        )
        if not valid:
            invalid_count += 1

        if args.drop and not valid:
            continue
        if args.errors_only and valid:
            continue

        out = dict(record)
        if errors:
            out["_validation_errors"] = errors
        print(json.dumps(out))

    if invalid_count:
        print(
            f"validation: {invalid_count}/{total} records failed",
            file=sys.stderr,
        )
        return 1
    return 0


def main(argv: Optional[List[str]] = None) -> int:  # pragma: no cover
    parser = build_validate_parser()
    args = parser.parse_args(argv)
    return run_validate(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
