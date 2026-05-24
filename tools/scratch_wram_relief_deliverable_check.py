"""Verifier for the 2026-05-24 WRAMX bank 1 relief research deliverable.

This is the correct gate for a read-only research-doc pgoal whose stated
deliverable is `journal/2026-05-24_wram_relief_scratchpad.md with byte-
level estimates per proposed change`. The auto-discovered `pytest` gate
was structurally wrong for this goal (it ran the project's full test
suite, which fails on a pre-existing dirty file unrelated to this
audit).

Pass conditions:
  - the scratchpad exists
  - it mentions the three packaged plans (A, B, C)
  - it cites at least one concrete byte count >= 410 (the 10% floor)
  - it references the Boss AI Reserve and at least one bank-2
    relocation candidate
  - it acknowledges the save-format constraint
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


SCRATCHPAD = Path(__file__).resolve().parents[1] / "journal" / "2026-05-24_wram_relief_scratchpad.md"


def main() -> int:
    if not SCRATCHPAD.exists():
        print(f"FAIL: deliverable missing at {SCRATCHPAD}")
        return 1
    text = SCRATCHPAD.read_text(encoding="utf-8")
    checks = [
        ("Package A bundle named", r"\bPackage A\b"),
        ("Package B bundle named", r"\bPackage B\b"),
        ("Package C bundle named", r"\bPackage C\b"),
        ("Boss AI Reserve referenced", r"Boss AI (WRAM )?Reserve"),
        ("Bank-2 relocation discussed", r"bank[- ]?2|BANK\[2\]|WRAMX2|wBossAIWramx2"),
        ("Save-format constraint noted", r"save[- ]format|SAVE_FORMAT_VERSION|wPlayerData3"),
        ("Byte-level estimate >= floor", None),  # special: any 3-digit byte count >= 410
        ("Byte-table for Tier 1 / 2", r"Tier[- ]?[12]"),
    ]
    failed = []
    for name, pattern in checks:
        if name == "Byte-level estimate >= floor":
            counts = [int(m.group(1)) for m in re.finditer(r"(\d{3,4})\s*bytes?\b", text)]
            ok = any(c >= 410 for c in counts)
        else:
            ok = bool(re.search(pattern, text, re.IGNORECASE))
        if not ok:
            failed.append(name)
        print(f"  {'OK ' if ok else 'FAIL'}  {name}")
    if failed:
        print(f"\nFAIL: {len(failed)} check(s) failed: {', '.join(failed)}")
        return 1
    print("\nOK: deliverable satisfies all checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
