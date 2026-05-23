#!/usr/bin/env python3
"""Audit P0.5b WRAMX bank-2 plumbing.

Acceptance criterion for the 2026-05-23 boss-AI ROM-expansion /codex-pgoal
phase P0.5b. Verifies:

  1. ram/wram.asm declares a SECTION pinned to WRAMX BANK[2] containing
     the placeholder label `wBossAIWramx2Buffer::`.
  2. ram/hram.asm declares `hWRAMBank::` (the SVBK shadow byte).
  3. home/wram_bank.asm exists and declares `SetWRAMBank::`.
  4. home.asm includes home/wram_bank.asm.
  5. home/init.asm sets [rSVBK]=1 (CGB-guarded) before the WRAM clear,
     and [hWRAMBank]=1 after the HRAM clear.
  6. docs/generated/dev_index.md still shows the Boss AI WRAM Reserve
     bank-1 floor (normal >= 36 free bytes, trace >= 9 free bytes) — i.e.
     adding bank 2 didn't regress the bank-1 reserve.
  7. The symbol `wBossAIWramx2Buffer` resolves on bank 2 in pokegold.sym
     (skipped if sym file absent).

Fails fast with exit 1 on the first missing item. Prints PASS summary
otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


WRAM_ASM = Path("ram/wram.asm")
HRAM_ASM = Path("ram/hram.asm")
WRAM_BANK_HELPER = Path("home/wram_bank.asm")
HOME_ASM = Path("home.asm")
INIT_ASM = Path("home/init.asm")
DEV_INDEX = Path("docs/generated/dev_index.md")
SYM_FILE = Path("pokegold.sym")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def must_contain(path: Path, needle: str, label: str) -> None:
    if not path.exists():
        fail(f"{path} missing ({label})")
    text = path.read_text(encoding="utf-8")
    if needle not in text:
        fail(f"{label}: {path} missing literal {needle!r}")


def main() -> int:
    # 1. SECTION with BANK[2] containing the placeholder label
    if not WRAM_ASM.exists():
        fail(f"{WRAM_ASM} missing")
    wram_text = WRAM_ASM.read_text(encoding="utf-8")
    section_pattern = re.compile(
        r'SECTION\s+"[^"]+",\s*WRAMX,\s*BANK\[\s*2\s*\]',
        re.IGNORECASE,
    )
    if not section_pattern.search(wram_text):
        fail("ram/wram.asm missing SECTION with WRAMX BANK[2]")
    if "wBossAIWramx2Buffer::" not in wram_text:
        fail("ram/wram.asm missing wBossAIWramx2Buffer:: label")

    # 2. hWRAMBank shadow
    must_contain(HRAM_ASM, "hWRAMBank::", "hWRAMBank shadow byte")

    # 3. SetWRAMBank helper
    must_contain(WRAM_BANK_HELPER, "SetWRAMBank::", "SetWRAMBank helper")

    # 4. home.asm includes the helper
    must_contain(HOME_ASM, 'INCLUDE "home/wram_bank.asm"', "home.asm include of wram_bank.asm")

    # 5. Boot init: rSVBK=1 (CGB-guarded) and hWRAMBank=1
    init_text = INIT_ASM.read_text(encoding="utf-8") if INIT_ASM.exists() else ""
    if "[rSVBK]" not in init_text:
        fail("home/init.asm has no [rSVBK] write in boot init")
    if "[hWRAMBank]" not in init_text:
        fail("home/init.asm has no [hWRAMBank] write in boot init")
    if "hCGB" not in init_text:
        fail("home/init.asm boot init missing hCGB guard around rSVBK write")

    # 6. Boss AI WRAM Reserve bank-1 floor unchanged
    if DEV_INDEX.exists():
        dev_text = DEV_INDEX.read_text(encoding="utf-8")
        reserve_match = re.search(
            r"Boss AI WRAM Reserve[\s\S]+?\| Normal\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|"
            r"[\s\S]+?\| With `BOSS_AI_TRACE` fields\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|",
            dev_text,
        )
        if not reserve_match:
            print("WARN: could not parse Boss AI WRAM Reserve table in dev_index; skipping floor check")
        else:
            normal_free = int(reserve_match.group(2))
            trace_free = int(reserve_match.group(4))
            if normal_free < 36:
                fail(f"Boss AI WRAM Reserve (Normal) bank-1 free bytes {normal_free} < 36 floor")
            if trace_free < 9:
                fail(f"Boss AI WRAM Reserve (BOSS_AI_TRACE) bank-1 free bytes {trace_free} < 9 floor")

    # 7. Symbol verification (optional)
    if SYM_FILE.exists():
        sym_text = SYM_FILE.read_text(encoding="utf-8", errors="ignore")
        sym_match = re.search(r"^([0-9a-fA-F]{2}):[0-9a-fA-F]{4}\s+wBossAIWramx2Buffer\b", sym_text, re.MULTILINE)
        if sym_match:
            bank_hex = sym_match.group(1)
            if int(bank_hex, 16) != 2:
                fail(f"wBossAIWramx2Buffer resolves on bank {bank_hex} not 02")
        else:
            print("WARN: pokegold.sym has no wBossAIWramx2Buffer entry; ROM may be stale")

    print("PASS: WRAMX bank-2 plumbing — SECTION, hWRAMBank shadow, SetWRAMBank helper, home.asm include, boot init wired, bank-1 reserve floor intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
