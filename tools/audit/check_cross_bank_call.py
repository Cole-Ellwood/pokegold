#!/usr/bin/env python3
"""check_cross_bank_call.py

Detects plain `call <Label>` / `jp <Label>` where the caller and the
target reside in different ROM banks.

Plain `call` only reaches the current bank or HOME (ROM0). Calling a
label in another bank with `call` assembles cleanly but jumps to garbage
at runtime — same shape as the May 2026 type-immunity softlock fixed in
commit fc7f0a75 (`battle: fix cross-bank softlock on type-immune
fail-text path`). Use `farcall` for cross-bank calls.

Reads `pokegold.sym` (linker output) for label -> bank assignments. Run
`make pokegold.gbc` first if the sym file is missing.

Caveats / scope:
- Same-bank calls are silent.
- Targets in HOME (bank 0x00) are silent — universally callable.
- Conditional `call cc, Label` and `jp cc, Label` are checked.
- `jp [hl]`, `jp hl`, register targets, and macro names not in the sym
  file are silently skipped (sym lookup miss).
- `farcall` / `callfar` lines are not matched (they are correct by
  construction — the macro emits an `rst FarCall` to HOME).
- Local-label cross-references like `call Foo.bar` are checked.
- Inline `SECTION "..."` directives reset the per-file caller-bank
  tracker so labels in a new section aren't attributed to the wrong
  bank.
- HOME-bank callers (bank 0x00) are silent. HOME functions calling
  banked-implementation labels (e.g. `InitSound::` -> `_InitSound`) are
  the canonical manual-bank-switch thunk pattern; the bank IS switched
  before the `call`, the audit can't see that statically, so it would
  produce ~40 false positives if it tried. These are reviewed manually.

Exit 0 = no cross-bank calls. Exit 1 = at least one cross-bank call.
Exit 2 = sym file missing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from asm_scan import AsmFile, ROOT, TOP_LABEL_RE, SECTION_RE, iter_asm_files

SYM_PATH = ROOT / "pokegold.sym"

SYM_LINE_RE = re.compile(
    r"^([0-9a-fA-F]{2}):([0-9a-fA-F]{4})\s+([A-Za-z_][A-Za-z0-9_.]*)\s*$"
)
GLOBAL_LABEL_RE = TOP_LABEL_RE
CALL_SITE_RE = re.compile(
    r"^\s*(call|jp)\s+(?:(?:nz|z|nc|c)\s*,\s*)?"
    r"([A-Za-z_][A-Za-z0-9_.]*)\s*(?:;.*)?$"
)

SCAN_DIRS = ["engine", "home", "data", "audio", "macros", "gfx", "ram"]


def load_sym() -> dict[str, str]:
    if not SYM_PATH.exists():
        sys.stderr.write(
            f"error: {SYM_PATH} missing; run `make pokegold.gbc` first\n"
        )
        sys.exit(2)
    sym: dict[str, str] = {}
    for line in SYM_PATH.read_text(encoding="utf-8").splitlines():
        m = SYM_LINE_RE.match(line)
        if not m:
            continue
        bank, _addr, name = m.groups()
        sym[name] = bank.lower()
    return sym


def cross_bank_asm_files() -> list[AsmFile]:
    return iter_asm_files(roots=[ROOT / directory for directory in SCAN_DIRS])


def scan_file(asm_file: AsmFile, sym: dict[str, str]) -> list[tuple[int, str, str, str, str]]:
    violations: list[tuple[int, str, str, str, str]] = []
    current_label: str | None = None
    for lineno, raw in enumerate(asm_file.lines, 1):
        stripped = raw.rstrip()
        if not stripped:
            continue
        if SECTION_RE.match(stripped):
            current_label = None
            continue
        m_label = GLOBAL_LABEL_RE.match(stripped)
        if m_label:
            current_label = m_label.group("label")
            continue
        m_call = CALL_SITE_RE.match(stripped)
        if not m_call:
            continue
        op, target = m_call.group(1), m_call.group(2)
        if current_label is None:
            continue
        caller_bank = sym.get(current_label)
        target_bank = sym.get(target)
        if caller_bank is None or target_bank is None:
            continue
        if caller_bank == target_bank:
            continue
        if target_bank == "00":
            continue
        if caller_bank == "00":
            # HOME thunks doing manual bank switch before a banked call;
            # the audit can't see the runtime bank state statically.
            continue
        violations.append((lineno, op, target, caller_bank, target_bank))
    return violations


def main() -> int:
    sym = load_sym()
    total = 0
    for asm_file in cross_bank_asm_files():
        viols = scan_file(asm_file, sym)
        if not viols:
            continue
        rel = asm_file.path.relative_to(ROOT).as_posix()
        for ln, op, tgt, cb, tb in viols:
            print(
                f"{rel}:{ln}: cross-bank `{op} {tgt}` "
                f"(caller bank 0x{cb}, target bank 0x{tb}) — "
                f"use `farcall {tgt}` instead"
            )
            total += 1
    if total:
        print(f"\nFAIL: {total} cross-bank call(s) detected")
        return 1
    print("PASS: no cross-bank `call` / `jp` to non-HOME labels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
