"""Generic data-shaping helpers shared by every ranking module.

No internal imports — leaf of the ranking package.
"""

from __future__ import annotations

from typing import Any


def finding(
    *,
    finding_type: str,
    title: str,
    source: str,
    severity: int,
    confidence: float,
    evidence: list[str],
    next_actions: list[str],
) -> dict[str, Any]:
    return {
        "type": finding_type,
        "title": title,
        "source": source,
        "severity": severity,
        "confidence": confidence,
        "evidence": [item for item in evidence if item],
        "next_actions": [item for item in next_actions if item],
    }


def string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple | set):
        return [
            nested
            for item in value
            for nested in string_items(item)
        ]
    return [str(value)] if value else []


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list | tuple):
        return [item for item in value if isinstance(item, dict)]
    return []


def unique_string_items(values: list[str]) -> list[str]:
    out = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out
