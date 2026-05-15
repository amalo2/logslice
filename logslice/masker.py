"""Field value masking with configurable strategies."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Iterator, List, Optional


_MASK_CHAR = "*"


def mask_full(value: Any, placeholder: str = "[MASKED]") -> str:
    """Replace the entire value with a placeholder."""
    return placeholder


def mask_partial(value: Any, visible: int = 4, placeholder: str = "*") -> str:
    """Show only the last *visible* characters; mask the rest."""
    s = str(value)
    if len(s) <= visible:
        return placeholder * len(s)
    masked_len = len(s) - visible
    return placeholder * masked_len + s[-visible:]


def mask_pattern(value: Any, pattern: str, replacement: str = "[MASKED]") -> str:
    """Replace regex matches within the value string."""
    return re.sub(pattern, replacement, str(value))


def mask_record(
    record: Dict[str, Any],
    fields: List[str],
    strategy: str = "full",
    visible: int = 4,
    placeholder: str = "[MASKED]",
    pattern: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a copy of *record* with the specified fields masked.

    Strategies:
      - ``full``    – replace entire value with *placeholder*.
      - ``partial`` – keep last *visible* chars, mask the rest.
      - ``pattern`` – apply regex *pattern*, replacing matches with *placeholder*.
    """
    result = dict(record)
    for field in fields:
        if field not in result:
            continue
        value = result[field]
        if strategy == "partial":
            result[field] = mask_partial(value, visible=visible, placeholder="*")
        elif strategy == "pattern":
            pat = pattern or r"."
            result[field] = mask_pattern(value, pat, replacement=placeholder)
        else:
            result[field] = mask_full(value, placeholder=placeholder)
    return result


def mask_stream(
    records: Iterable[Dict[str, Any]],
    fields: List[str],
    strategy: str = "full",
    visible: int = 4,
    placeholder: str = "[MASKED]",
    pattern: Optional[str] = None,
) -> Iterator[Dict[str, Any]]:
    """Apply :func:`mask_record` to every record in *records*."""
    for record in records:
        yield mask_record(
            record,
            fields,
            strategy=strategy,
            visible=visible,
            placeholder=placeholder,
            pattern=pattern,
        )
