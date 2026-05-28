#!/usr/bin/env python3
"""Confirm wBossAILookaheadRunningBest has a clean lifecycle:

1. Declared in ram/wram.asm inside the boss AI per-tick cache section.
2. Only read/written by BossAI_ApplyLookaheadToTopMoveCandidates — no other
   code reaches into this scratch byte.
3. The driver writes to the symbol before any read in the same call (no
   reset is performed by BossAI_ResetTurnCaches; we save the bank-0E ROM
   bytes by relying on the driver's own initialization from the .best_loop
   minimum).

Exit 0 on PASS, 1 on FAIL.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRAM = ROOT / "ram" / "wram.asm"
PLATFORM = ROOT / "engine" / "battle" / "ai" / "boss_platform.asm"
DRIVER_SRC = ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm"

SYMBOL = "wBossAILookaheadRunningBest"
DRIVER = "BossAI_ApplyLookaheadToTopMoveCandidates"

ALLOWED_FILES = {DRIVER_SRC, WRAM}


def main() -> int:
    failures: list[str] = []

    # 1. Declaration in ram/wram.asm.
    wram_text = WRAM.read_text(encoding="utf-8", errors="replace")
    if not re.search(rf"^{SYMBOL}::\s*db\b", wram_text, re.MULTILINE):
        failures.append(f"{SYMBOL} is not declared as `db` in ram/wram.asm")

    # 2. Read/write reachability — only allowed inside the driver and the
    #    declaration site. The driver unconditionally initializes running_best
    #    from the .best_loop minimum before any read, so it does not need a
    #    sentinel reset in BossAI_ResetTurnCaches (skipped to save bank-0E
    #    ROM bytes).
    for p in ROOT.rglob("*.asm"):
        if p in ALLOWED_FILES:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if SYMBOL in text:
            failures.append(
                f"{SYMBOL} referenced outside {DRIVER} / wram.asm: "
                f"{p.relative_to(ROOT)}"
            )

    # 3. Driver actually reads + writes the symbol AND writes it before any
    #    read (regression guard against the missing-init bug if reset is
    #    skipped).
    drv_text = DRIVER_SRC.read_text(encoding="utf-8", errors="replace")
    drv_body = extract_label_body(drv_text, DRIVER)
    if not drv_body:
        failures.append(f"could not find {DRIVER} in {DRIVER_SRC.name}")
    else:
        first_write = drv_body.find(f"ld [{SYMBOL}], a")
        first_read = drv_body.find(f"ld a, [{SYMBOL}]")
        # Also catch the hl-swap read pattern: `ld hl, wBossAILookaheadRunningBest`
        # followed by `cp [hl]` or `ld a, [hl]`.
        first_hl_read = drv_body.find(f"ld hl, {SYMBOL}")
        if first_write < 0:
            failures.append(f"{DRIVER} does not write to {SYMBOL}")
        if first_read < 0 and first_hl_read < 0:
            failures.append(f"{DRIVER} does not read from {SYMBOL}")
        if first_write >= 0:
            earliest_read = min(
                (x for x in (first_read, first_hl_read) if x >= 0),
                default=-1,
            )
            if earliest_read >= 0 and earliest_read < first_write:
                failures.append(
                    f"{DRIVER} reads {SYMBOL} before writing it "
                    "(no reset in ResetTurnCaches — init must come first)"
                )

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1

    print(f"PASS: {SYMBOL} lifecycle is clean (declared, reset, driver-only).")
    return 0


def extract_label_body(text: str, label: str) -> str:
    """Return text from `label:` to the next top-level label."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{label}:"):
            start = i
            break
    if start is None:
        return ""
    body_lines: list[str] = []
    label_re = re.compile(r"^([A-Za-z0-9_]+):\s*(?:;.*)?$")
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if (
            stripped
            and not stripped.startswith(".")
            and label_re.match(stripped)
        ):
            break
        body_lines.append(line)
    return "\n".join(body_lines)


if __name__ == "__main__":
    sys.exit(main())
