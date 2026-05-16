"""CLI entry-point: score and rank log records by keyword relevance."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List, Optional

from logslice.parser import parse_line
from logslice.scorer import score_stream, top_records


def build_score_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-score",
        description="Score and rank log records by keyword relevance.",
    )
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Input log files (default: stdin).",
    )
    p.add_argument(
        "-w",
        "--weight",
        dest="weights",
        action="append",
        metavar="KEYWORD:WEIGHT",
        default=[],
        help="Keyword and numeric weight, e.g. error:2.0. Repeat for multiple.",
    )
    p.add_argument(
        "-n",
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="Emit only the top-N records by score (default: all).",
    )
    p.add_argument(
        "--min-score",
        type=float,
        default=None,
        metavar="MIN",
        help="Only emit records with score >= MIN.",
    )
    p.add_argument(
        "--score-field",
        default="_score",
        metavar="FIELD",
        help="Name of the injected score field (default: _score).",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Match keywords case-sensitively.",
    )
    return p


def _parse_weights(raw: List[str]) -> Dict[str, float]:
    weights: Dict[str, float] = {}
    for item in raw:
        if ":" not in item:
            raise SystemExit(f"Invalid weight spec (expected KEYWORD:WEIGHT): {item!r}")
        keyword, _, value = item.partition(":")
        try:
            weights[keyword] = float(value)
        except ValueError:
            raise SystemExit(f"Weight must be a number, got: {value!r}")
    return weights


def _iter_lines(files: List[str]):
    if not files:
        yield from sys.stdin
        return
    for path in files:
        with open(path) as fh:
            yield from fh


def run_score(args: argparse.Namespace, *, out=None) -> int:
    if out is None:
        out = sys.stdout
    weights = _parse_weights(args.weights)
    records = [
        r
        for line in _iter_lines(args.files)
        if (r := parse_line(line)) is not None
    ]
    if args.top is not None:
        pairs = top_records(records, weights, n=args.top, case_sensitive=args.case_sensitive)
        scored = [{**r, args.score_field: s} for s, r in pairs]
    else:
        scored = list(
            score_stream(records, weights, case_sensitive=args.case_sensitive, field=args.score_field)
        )
    if args.min_score is not None:
        scored = [r for r in scored if r.get(args.score_field, 0.0) >= args.min_score]
    for record in scored:
        out.write(json.dumps(record, separators=(",", ":")) + "\n")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_score_parser()
    args = parser.parse_args(argv)
    return run_score(args)


if __name__ == "__main__":
    sys.exit(main())
