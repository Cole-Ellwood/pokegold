#!/usr/bin/env python3
"""Audit rSVBK write-site discipline.

Codex's bonus catch from P0.5b chat-ack: after the WRAMX bank-switch idiom
exists, `[rSVBK]` writes should appear ONLY in:

  - home/init.asm (boot init, before the shadow is valid)
  - home/wram_bank.asm (the SetWRAMBank helper)

Any other rSVBK write is either an undisciplined inline switch (must also
update hWRAMBank) or a stale pattern. This audit flags both so the shadow
register can't silently desync from the hardware register.

Inline writes elsewhere ARE allowed if they update BOTH [rSVBK] and
[hWRAMBank] on the same line or within 3 lines. The audit detects that
pair and lets it pass with a note.

Exits 0 on clean; 1 on undisciplined writes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


ALLOWED_FILES = {
    Path("home/init.asm"),
    Path("home/wram_bank.asm"),
}

# Pair-with-shadow window: within N lines, a matching [hWRAMBank] write
# means the inline switch is disciplined.
PAIR_WINDOW = 3


def main() -> int:
    repo_root = Path(".")
    asm_files = list(repo_root.rglob("*.asm"))
    # Filter out worktrees + scratch
    asm_files = [
        p for p in asm_files
        if ".local" not in p.parts and ".claude" not in p.parts
    ]

    write_re = re.compile(r"\b(?:ld|ldh)\s+\[\s*rSVBK\s*\]\s*,", re.IGNORECASE)
    shadow_re = re.compile(r"\b(?:ld|ldh)\s+\[\s*hWRAMBank\s*\]\s*,", re.IGNORECASE)

    undisciplined: list[tuple[str, int, str]] = []
    disciplined_inline: list[tuple[str, int]] = []

    for path in asm_files:
        if path in ALLOWED_FILES:
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines):
            if not write_re.search(line):
                continue
            # Look for a paired hWRAMBank write within the next PAIR_WINDOW lines.
            window = lines[i : i + PAIR_WINDOW + 1]
            paired = any(shadow_re.search(w) for w in window)
            if paired:
                disciplined_inline.append((str(path), i + 1))
            else:
                undisciplined.append((str(path), i + 1, line.strip()))

    if undisciplined:
        print("FAIL: undisciplined [rSVBK] writes (no [hWRAMBank] update within "
              f"{PAIR_WINDOW} lines):")
        for path, line_no, snippet in undisciplined:
            print(f"  {path}:{line_no}: {snippet[:80]}")
        print("")
        print("Either move the write through SetWRAMBank, OR add an [hWRAMBank] write")
        print("within 3 lines to keep the shadow in sync.")
        return 1

    if disciplined_inline:
        print(f"PASS (with {len(disciplined_inline)} disciplined inline switch(es)):")
        for path, line_no in disciplined_inline:
            print(f"  inline: {path}:{line_no}")
    else:
        print("PASS: [rSVBK] writes confined to home/init.asm + home/wram_bank.asm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
