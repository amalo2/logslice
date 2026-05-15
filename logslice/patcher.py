"""Apply JSON-patch-style field updates to log records."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional


Record = Dict[str, Any]


def _set_nested(record: Record, path: str, value: Any, sep: str = ".") -> Record:
    """Return a shallow-copied record with *path* set to *value*."""
    out = dict(record)
    parts = path.split(sep)
    if len(parts) == 1:
        out[path] = value
        return out
    # Walk / create nested dicts
    node = out
    for part in parts[:-1]:
        child = node.get(part)
        if not isinstance(child, dict):
            child = {}
        else:
            child = dict(child)
        node[part] = child
        node = child
    node[parts[-1]] = value
    return out


def _del_nested(record: Record, path: str, sep: str = ".") -> Record:
    """Return a copy of *record* with *path* removed (no-op if missing)."""
    out = dict(record)
    parts = path.split(sep)
    if len(parts) == 1:
        out.pop(path, None)
        return out
    node = out
    for part in parts[:-1]:
        child = node.get(part)
        if not isinstance(child, dict):
            return out
        child = dict(child)
        node[part] = child
        node = child
    node.pop(parts[-1], None)
    return out


def patch_record(
    record: Record,
    patches: List[Dict[str, Any]],
    sep: str = ".",
) -> Record:
    """Apply a list of patch operations to *record*.

    Each patch dict must have an ``op`` key:
    - ``{"op": "set", "path": "a.b", "value": 1}``
    - ``{"op": "remove", "path": "a.b"}``
    - ``{"op": "default", "path": "a.b", "value": 1}``  (set only if absent)
    """
    out = record
    for p in patches:
        op = p.get("op")
        path: Optional[str] = p.get("path")
        if not path:
            continue
        if op == "set":
            out = _set_nested(out, path, p.get("value"), sep)
        elif op == "remove":
            out = _del_nested(out, path, sep)
        elif op == "default":
            parts = path.split(sep)
            node: Any = out
            for part in parts:
                if not isinstance(node, dict):
                    node = None
                    break
                node = node.get(part)
            if node is None:
                out = _set_nested(out, path, p.get("value"), sep)
    return out


def patch_stream(
    records: Iterable[Record],
    patches: List[Dict[str, Any]],
    sep: str = ".",
) -> Iterator[Record]:
    """Yield patched copies of every record in *records*."""
    for record in records:
        yield patch_record(record, patches, sep)
