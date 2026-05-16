#!/usr/bin/env python3
"""Verifier for the 2026-05-16 ROM crash-bug audit report.

Pass if:
  - Report file exists.
  - Report has >= 5 structured findings (### Finding N ...).
  - Every finding block has Severity:, Confidence:, Category:, File:, Why:.
  - Every finding's File: line matches `path/to/file.{asm,inc,py,sh}[:LINE]` form.
  - Coverage log contains >= 8 "Files reviewed" entries (proves substantive scan).

Run:
    python scripts/verify_rom_bug_audit.py

Non-zero exit means /pgoal verifier failed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "docs" / "audits" / "rom_bug_audit_2026-05-16.md"

REQUIRED_FIELDS = ("Severity:", "Confidence:", "Category:", "File:", "Why:")
MIN_FINDINGS = 5
MIN_FILES_REVIEWED = 8


def main() -> int:
    if not REPORT.exists():
        print(f"FAIL: report not at {REPORT}")
        return 1

    text = REPORT.read_text(encoding="utf-8")

    # Block out the template comment so it doesn't satisfy field checks.
    text_no_template = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    finding_headers = re.findall(
        r"^### Finding \d+",
        text_no_template,
        flags=re.MULTILINE,
    )
    n_findings = len(finding_headers)

    # Split into finding bodies by header position.
    finding_blocks = re.split(r"^### Finding \d+", text_no_template, flags=re.MULTILINE)[1:]

    errors: list[str] = []

    if n_findings < MIN_FINDINGS:
        errors.append(f"need >= {MIN_FINDINGS} findings, have {n_findings}")

    for i, block in enumerate(finding_blocks, start=1):
        for field in REQUIRED_FIELDS:
            if field not in block:
                errors.append(f"finding {i}: missing field {field!r}")

        file_match = re.search(
            r"\*\*File:\*\*\s+`([^`]+)`",
            block,
        )
        if file_match:
            path = file_match.group(1)
            if not re.match(r"^[\w./\-]+\.(asm|inc|py|sh|md)(?::\d+(?:-\d+)?)?$", path):
                errors.append(
                    f"finding {i}: File: {path!r} doesn't look like path[:line]"
                )
        else:
            errors.append(f"finding {i}: no parseable **File:** line")

    files_reviewed_section = re.search(
        r"### Files reviewed\s*\n(.*?)(?=\n### |\n---|\Z)",
        text_no_template,
        flags=re.DOTALL,
    )
    n_files_reviewed = 0
    if files_reviewed_section:
        # Each entry is a markdown bullet starting with "- ".
        entries = re.findall(
            r"^\s*-\s+", files_reviewed_section.group(1), flags=re.MULTILINE
        )
        n_files_reviewed = len(entries)

    if n_files_reviewed < MIN_FILES_REVIEWED:
        errors.append(
            f"need >= {MIN_FILES_REVIEWED} 'Files reviewed' entries, have {n_files_reviewed}"
        )

    print(f"findings: {n_findings}")
    print(f"files reviewed: {n_files_reviewed}")

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
