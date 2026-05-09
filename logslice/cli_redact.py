"""
logslice.cli_redact
~~~~~~~~~~~~~~~~~~~
CLI sub-command: redact sensitive fields from a log stream.

Usage examples::

    logslice redact --fields password token < app.log
    logslice redact --auto < app.log
    logslice redact --fields email --auto --placeholder '[PII]' < app.log
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import IO, Iterator

from logslice.parser import parse_line
from logslice.redactor import redact_record


def build_redact_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs: dict = dict(
        description="Redact sensitive fields from structured JSON log lines.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    if parent is not None:
        parser = parent.add_parser("redact", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument(
        "--fields",
        nargs="*",
        default=[],
        metavar="FIELD",
        help="Field names whose values should be replaced with the placeholder.",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        default=False,
        help="Auto-detect and redact common sensitive patterns (email, IP, bearer tokens …).",
    )
    parser.add_argument(
        "--placeholder",
        default="***REDACTED***",
        metavar="TEXT",
        help="Replacement text (default: %(default)s).",
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Log files to read. Reads from stdin when omitted.",
    )
    return parser


def _iter_lines(files: list[str]) -> Iterator[str]:
    if not files:
        yield from sys.stdin
        return
    for path in files:
        with open(path) as fh:
            yield from fh


def run_redact(args: argparse.Namespace, out: IO[str] = sys.stdout) -> int:
    """Execute the redact sub-command.  Returns an exit code."""
    written = 0
    for raw in _iter_lines(args.files):
        record = parse_line(raw)
        if record is None:
            continue
        clean = redact_record(
            record,
            fields=args.fields,
            auto_patterns=args.auto,
            placeholder=args.placeholder,
        )
        out.write(json.dumps(clean, ensure_ascii=False) + "\n")
        written += 1
    return 0 if written >= 0 else 1


def main() -> None:  # pragma: no cover
    parser = build_redact_parser()
    args = parser.parse_args()
    sys.exit(run_redact(args))


if __name__ == "__main__":  # pragma: no cover
    main()
