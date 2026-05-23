#!/usr/bin/env python3
"""Audit gate for docs/debugger_bug_class_catalog.md (P20 first slice).

Enforces the schema and minimum-coverage rules from the roadmap §3 P20:

1. The catalog file exists.
2. At least 12 entries (across AUTO + QUERY + JUDGMENT sections).
3. Every entry has a `**Tier:**` line and a `**Lived history:**` line.
4. Every AUTO entry has a `**Detector:**` line.
5. Every QUERY entry has a `**Locate:**` line.
6. Every JUDGMENT entry has an `**Escalation:**` line.

Exit 0 on pass, non-zero on fail. Failures are listed per entry so a
catalog regression points at the exact section that needs fixing.

Out of scope for this first slice (slice-2 work, called out in the
catalog itself):
- Auto-executing every AUTO entry's `**Audit:**` line and verifying
  exit 0.
- Cross-referencing every selftest lived-smoke component to a catalog
  entry.
- Adding this audit to `tools/audit/check_release_smoke.py`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "docs" / "debugger_bug_class_catalog.md"
MIN_ENTRIES = 12

TIER_SECTION_RE = re.compile(r"^## (AUTO|QUERY|JUDGMENT) classes\s*$")
ENTRY_HEADER_RE = re.compile(r"^### (?P<name>[a-z][a-z0-9_]*)\s*$")
TIER_LINE_RE = re.compile(r"^\*\*Tier:\*\*\s*(?P<tier>AUTO|QUERY|JUDGMENT)\b")
LIVED_LINE_RE = re.compile(r"^\*\*Lived history:\*\*", re.MULTILINE)
DETECTOR_LINE_RE = re.compile(r"^\*\*Detector:\*\*", re.MULTILINE)
LOCATE_LINE_RE = re.compile(r"^\*\*Locate:\*\*", re.MULTILINE)
ESCALATION_LINE_RE = re.compile(r"^\*\*Escalation:\*\*", re.MULTILINE)


def parse_catalog(text: str) -> tuple[list[dict[str, object]], list[str]]:
    """Return (entries, parse_errors).

    Each entry is a dict {name, section_tier, body_tier, body_lines}.
    section_tier is the AUTO/QUERY/JUDGMENT section heading the entry
    sits under; body_tier is what the entry's own `**Tier:**` line
    declares. The audit later flags mismatches between the two.
    """
    entries: list[dict[str, object]] = []
    parse_errors: list[str] = []
    current_section: str | None = None
    current_entry: dict[str, object] | None = None

    for lineno, raw in enumerate(text.splitlines(), start=1):
        section_match = TIER_SECTION_RE.match(raw)
        if section_match:
            if current_entry is not None:
                entries.append(current_entry)
                current_entry = None
            current_section = section_match.group(1)
            continue

        entry_match = ENTRY_HEADER_RE.match(raw)
        if entry_match:
            if current_entry is not None:
                entries.append(current_entry)
            if current_section is None:
                parse_errors.append(
                    f"line {lineno}: entry {entry_match.group('name')!r} appears "
                    f"before any AUTO/QUERY/JUDGMENT section heading"
                )
            current_entry = {
                "name": entry_match.group("name"),
                "section_tier": current_section,
                "body_tier": None,
                "body_lines": [],
                "lineno": lineno,
            }
            continue

        if current_entry is not None:
            current_entry["body_lines"].append(raw)
            tier_match = TIER_LINE_RE.match(raw)
            if tier_match and current_entry["body_tier"] is None:
                current_entry["body_tier"] = tier_match.group("tier")

    if current_entry is not None:
        entries.append(current_entry)

    return entries, parse_errors


def validate_entry(entry: dict[str, object]) -> list[str]:
    """Return a list of validation errors for a single entry."""
    errors: list[str] = []
    name = entry["name"]
    section_tier = entry["section_tier"]
    body_tier = entry["body_tier"]
    body = "\n".join(entry["body_lines"])

    if body_tier is None:
        errors.append(f"{name}: missing **Tier:** line")
    elif section_tier is not None and body_tier != section_tier:
        errors.append(
            f"{name}: **Tier:** {body_tier} does not match its section "
            f"({section_tier} classes)"
        )

    if not LIVED_LINE_RE.search(body):
        errors.append(f"{name}: missing **Lived history:** line")

    tier = body_tier or section_tier
    if tier == "AUTO":
        if not DETECTOR_LINE_RE.search(body):
            errors.append(f"{name}: AUTO entry missing **Detector:** line")
    elif tier == "QUERY":
        if not LOCATE_LINE_RE.search(body):
            errors.append(f"{name}: QUERY entry missing **Locate:** line")
    elif tier == "JUDGMENT":
        if not ESCALATION_LINE_RE.search(body):
            errors.append(f"{name}: JUDGMENT entry missing **Escalation:** line")
    else:
        errors.append(f"{name}: unknown tier {tier!r}")

    return errors


def run_audit(catalog_path: Path = CATALOG) -> tuple[bool, list[str]]:
    """Return (ok, lines). lines is a printable per-line report."""
    lines: list[str] = []
    if not catalog_path.exists():
        return False, [f"FAIL: catalog file not found at {catalog_path}"]
    text = catalog_path.read_text(encoding="utf-8")
    entries, parse_errors = parse_catalog(text)

    ok = True
    if parse_errors:
        ok = False
        lines.append(f"FAIL: catalog parse errors ({len(parse_errors)}):")
        for err in parse_errors:
            lines.append(f"  - {err}")

    if len(entries) < MIN_ENTRIES:
        ok = False
        lines.append(
            f"FAIL: catalog has {len(entries)} entries; "
            f"minimum required is {MIN_ENTRIES}"
        )
    else:
        lines.append(
            f"OK: catalog has {len(entries)} entries (minimum {MIN_ENTRIES})"
        )

    per_tier: dict[str, int] = {}
    for entry in entries:
        tier = entry["body_tier"] or entry["section_tier"] or "UNKNOWN"
        per_tier[tier] = per_tier.get(tier, 0) + 1
    lines.append(
        "OK: per-tier counts: "
        + ", ".join(f"{tier}={per_tier[tier]}" for tier in sorted(per_tier))
    )

    all_errors: list[str] = []
    for entry in entries:
        errs = validate_entry(entry)
        all_errors.extend(errs)

    if all_errors:
        ok = False
        lines.append(f"FAIL: {len(all_errors)} entry validation errors:")
        for err in all_errors:
            lines.append(f"  - {err}")
    else:
        lines.append(
            "OK: every entry has Tier + Lived history + tier-specific "
            "Detector/Locate/Escalation"
        )

    return ok, lines


def main(argv: Iterable[str] | None = None) -> int:
    ok, lines = run_audit()
    for line in lines:
        print(line)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
