#!/usr/bin/env python3
"""One-shot fixer for boss_ai_logic.md line drift.

Parses the FAIL output of check_boss_ai_index_lines.py and applies the
old-line -> new-line corrections to docs/agent_navigation/subsystems/boss_ai_logic.md
in place. Run after a non-trivial boss.asm edit when the audit reports drift.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "docs" / "agent_navigation" / "subsystems" / "boss_ai_logic.md"

# Pattern matched against audit output:
#   FAIL: index says `Label:OLD`, source has `Label` at <path>:NEW. ...
DRIFT_RE = re.compile(
    r"FAIL: index says `(?P<label>\.?[A-Za-z_]\w*):(?P<old>\d+)`, "
    r"source has `[^`]+` at [^:]+:(?P<new>\d+)\. "
)


def main() -> int:
    audit = subprocess.run(
        [sys.executable, str(ROOT / "tools/audit/check_boss_ai_index_lines.py")],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    text = INDEX.read_text(encoding="utf-8")
    fixes: list[tuple[str, str]] = []
    for line in audit.stdout.splitlines():
        m = DRIFT_RE.match(line)
        if not m:
            continue
        old_ref = f"`{m['label']}:{m['old']}`"
        new_ref = f"`{m['label']}:{m['new']}`"
        fixes.append((old_ref, new_ref))

    if not fixes:
        print("No drift to fix.")
        return 0

    applied = 0
    for old, new in fixes:
        if old in text:
            text = text.replace(old, new)
            applied += 1
    INDEX.write_text(text, encoding="utf-8")
    print(f"Applied {applied} of {len(fixes)} corrections to {INDEX.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
