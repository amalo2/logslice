"""Export filtered log records to various output formats (CSV, JSONL, plain text)."""

from __future__ import annotations

import csv
import io
import json
from typing import Iterable, Literal

ExportFormat = Literal["csv", "jsonl", "text"]

_DEFAULT_CSV_FIELDS = ["timestamp", "level", "message"]


def export_jsonl(records: Iterable[dict]) -> str:
    """Serialize records as newline-delimited JSON (JSONL)."""
    lines = []
    for record in records:
        lines.append(json.dumps(record, ensure_ascii=False))
    return "\n".join(lines)


def export_csv(
    records: Iterable[dict],
    fields: list[str] | None = None,
    include_extra: bool = False,
) -> str:
    """Serialize records as CSV.

    Args:
        records: Iterable of log record dicts.
        fields: Ordered list of field names to include as columns.
                Defaults to ["timestamp", "level", "message"].
        include_extra: When True, unknown fields are appended as additional
                       columns discovered in the first record.
    """
    records = list(records)
    if not records:
        return ""

    base_fields = list(fields) if fields else list(_DEFAULT_CSV_FIELDS)

    if include_extra:
        seen = set(base_fields)
        for record in records:
            for key in record:
                if key not in seen:
                    base_fields.append(key)
                    seen.add(key)

    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=base_fields,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    for record in records:
        writer.writerow({f: record.get(f, "") for f in base_fields})
    return buf.getvalue()


def export_text(records: Iterable[dict], template: str | None = None) -> str:
    """Serialize records as plain text lines.

    Args:
        records: Iterable of log record dicts.
        template: A Python str.format_map template, e.g.
                  "{timestamp} [{level}] {message}".  Defaults to a sensible
                  fallback when not provided.
    """
    default_template = "{timestamp} [{level}] {message}"
    tmpl = template or default_template
    lines = []
    for record in records:
        try:
            lines.append(tmpl.format_map(record))
        except KeyError:
            lines.append(str(record))
    return "\n".join(lines)


def export_records(
    records: Iterable[dict],
    fmt: ExportFormat = "jsonl",
    **kwargs,
) -> str:
    """Dispatch to the appropriate exporter based on *fmt*."""
    if fmt == "jsonl":
        return export_jsonl(records)
    if fmt == "csv":
        return export_csv(records, **kwargs)
    if fmt == "text":
        return export_text(records, **kwargs)
    raise ValueError(f"Unknown export format: {fmt!r}")
