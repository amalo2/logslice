"""CLI entry-point: logslice-patch — apply field patches to JSON log lines."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Iterator, List

from logslice.parser import parse_line
from logslice.patcher import patch_record


def build_patch_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice-patch",
        description="Apply set/remove/default patches to structured JSON log lines.",
    )
    p.add_argument(
        "--set",
        metavar="PATH=VALUE",
        dest="sets",
        action="append",
        default=[],
        help="Set field at dotted PATH to VALUE (JSON-decoded if possible).",
    )
    p.add_argument(
        "--remove",
        metavar="PATH",
        dest="removes",
        action="append",
        default=[],
        help="Remove field at dotted PATH.",
    )
    p.add_argument(
        "--default",
        metavar="PATH=VALUE",
        dest="defaults",
        action="append",
        default=[],
        help="Set field at dotted PATH only when absent.",
    )
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Input files (default: stdin).",
    )
    return p


def _parse_kv(spec: str):
    """Split 'path=value' and JSON-decode value."""
    idx = spec.index("=")
    path = spec[:idx]
    raw = spec[idx + 1:]
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw
    return path, value


def _build_patches(args: argparse.Namespace) -> List[dict]:
    patches = []
    for spec in args.sets:
        path, value = _parse_kv(spec)
        patches.append({"op": "set", "path": path, "value": value})
    for path in args.removes:
        patches.append({"op": "remove", "path": path})
    for spec in args.defaults:
        path, value = _parse_kv(spec)
        patches.append({"op": "default", "path": path, "value": value})
    return patches


def _iter_lines(args: argparse.Namespace) -> Iterator[str]:
    if args.files:
        for path in args.files:
            with open(path) as fh:
                yield from fh
    else:
        yield from sys.stdin


def run_patch(args: argparse.Namespace, out=sys.stdout) -> int:
    patches = _build_patches(args)
    for raw in _iter_lines(args):
        record = parse_line(raw.rstrip("\n"))
        if record is None:
            continue
        patched = patch_record(record, patches)
        out.write(json.dumps(patched, separators=(",", ":")) + "\n")
    return 0


def main(argv=None) -> int:  # pragma: no cover
    parser = build_patch_parser()
    args = parser.parse_args(argv)
    return run_patch(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
