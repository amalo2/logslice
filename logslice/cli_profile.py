"""CLI entry-point: logslice-profile — profile a stream of JSON log records."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from logslice.parser import parse_line
from logslice.profiler import coverage_report, profile_stream


def build_profile_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-profile",
        description="Profile field coverage and value distributions in JSON log streams.",
    )
    p.add_argument("files", nargs="*", metavar="FILE", help="Log files to read (default: stdin)")
    p.add_argument("--format", choices=["pretty", "json"], default="pretty", help="Output format")
    p.add_argument("--top", type=int, default=5, metavar="N", help="Top N values to show per field (pretty mode)")
    p.add_argument("--min-rate", type=float, default=0.0, metavar="RATE", help="Only show fields with coverage >= RATE (0–1)")
    return p


def _iter_lines(files: List[str]):
    if not files:
        yield from sys.stdin
        return
    for path in files:
        with open(path) as fh:
            yield from fh


def _parse_records(files: List[str]):
    for line in _iter_lines(files):
        record = parse_line(line)
        if record is not None:
            yield record


def _print_pretty(profile: dict, top: int, min_rate: float) -> None:
    total = profile["total"]
    print(f"Total records : {total}")
    print(f"Unique fields : {len(profile['fields'])}")
    print()
    rows = coverage_report(profile)
    rows = [r for r in rows if r["rate"] >= min_rate]
    header = f"{'Field':<30}  {'Count':>7}  {'Missing':>7}  {'Rate':>6}  Types"
    print(header)
    print("-" * len(header))
    for row in rows:
        field = row["field"]
        info = profile["fields"][field]
        types_str = ", ".join(f"{t}:{c}" for t, c in info["types"].items())
        top_vals = ", ".join(f"{v}({c})" for v, c in info["top_values"][:top])
        print(f"{field:<30}  {row['count']:>7}  {row['missing']:>7}  {row['rate']:>6.1%}  [{types_str}]")
        if top_vals:
            print(f"  {'':30}  top: {top_vals}")


def run_profile(args: Optional[List[str]] = None) -> int:
    parser = build_profile_parser()
    ns = parser.parse_args(args)

    records = list(_parse_records(ns.files))
    profile = profile_stream(records)

    if ns.format == "json":
        json.dump(profile, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        _print_pretty(profile, top=ns.top, min_rate=ns.min_rate)

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_profile())


if __name__ == "__main__":  # pragma: no cover
    main()
