#!/usr/bin/env python3
"""Audit: debugger roadmap freshness.

Fails if docs/debugger_roadmap.md claims a phase is complete but the
phase's exit-criterion infrastructure isn't present. Specifically:

- P0: tools/debugger/__init__.py exists, tools/audit/check_debugger_roadmap_freshness.py exists
- P1: tools/debugger/kernel/symbol_service.py exists, tools/debugger/kernel/state_schema.py exists
- P2+: checked when those phases ship

Also warns if the roadmap file is missing entirely.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "docs" / "debugger_roadmap.md"

PHASE_DONE_RE = re.compile(r"P(\d+)\s.*(?:DONE|✅|complete|shipped)", re.IGNORECASE)

PHASE_REQUIREMENTS: dict[int, list[tuple[str, str]]] = {
    0: [
        ("tools/debugger/__init__.py", "debugger umbrella package"),
        ("tools/audit/check_debugger_roadmap_freshness.py", "this audit script"),
    ],
    1: [
        ("tools/debugger/kernel/symbol_service.py", "symbol service"),
        ("tools/debugger/kernel/state_schema.py", "state schema"),
    ],
}


def main() -> int:
    errors: list[str] = []

    if not ROADMAP.exists():
        print("WARN: docs/debugger_roadmap.md not found")
        print("PASS (no roadmap to check)")
        return 0

    text = ROADMAP.read_text(encoding="utf-8", errors="replace")

    done_phases: set[int] = set()
    for line in text.splitlines():
        m = PHASE_DONE_RE.search(line)
        if m:
            done_phases.add(int(m.group(1)))

    for phase in sorted(done_phases):
        reqs = PHASE_REQUIREMENTS.get(phase, [])
        for rel_path, desc in reqs:
            full = ROOT / rel_path
            if not full.exists():
                errors.append(
                    f"P{phase} marked done but {rel_path} missing ({desc})"
                )

    if errors:
        print("FAIL — debugger roadmap freshness")
        for e in errors:
            print(f"  {e}")
        return 1

    print(f"PASS — debugger roadmap freshness ({len(done_phases)} phase(s) marked done)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
