"""
logslice.redactor
~~~~~~~~~~~~~~~~~
Redact sensitive fields from log records before output.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

_PLACEHOLDER = "***REDACTED***"

# Common patterns for auto-detection
_SENSITIVE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("bearer", re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)),
    ("secret_key", re.compile(r"(?i)(secret|password|token|api[_-]?key)[=:\s]+\S+")),
]


def redact_fields(
    record: dict[str, Any],
    fields: Iterable[str],
    placeholder: str = _PLACEHOLDER,
) -> dict[str, Any]:
    """Return a shallow copy of *record* with *fields* replaced by *placeholder*."""
    out = dict(record)
    for field in fields:
        if field in out:
            out[field] = placeholder
    return out


def redact_patterns(
    record: dict[str, Any],
    placeholder: str = _PLACEHOLDER,
    patterns: list[tuple[str, re.Pattern[str]]] | None = None,
) -> dict[str, Any]:
    """Scan all string values in *record* and mask recognised sensitive patterns."""
    if patterns is None:
        patterns = _SENSITIVE_PATTERNS
    out = dict(record)
    for key, value in out.items():
        if not isinstance(value, str):
            continue
        for _name, pat in patterns:
            value = pat.sub(placeholder, value)
        out[key] = value
    return out


def redact_record(
    record: dict[str, Any],
    fields: Iterable[str] | None = None,
    auto_patterns: bool = False,
    placeholder: str = _PLACEHOLDER,
) -> dict[str, Any]:
    """Apply field-level and/or pattern-level redaction to *record*."""
    if fields:
        record = redact_fields(record, fields, placeholder=placeholder)
    if auto_patterns:
        record = redact_patterns(record, placeholder=placeholder)
    return record
