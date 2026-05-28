#!/usr/bin/env python3
"""Confirm the boss-AI lookahead trace block is sized to BOSS_AI_LOOKAHEAD_N
(currently 4) candidates, not the legacy hardcoded 3.

If N is bumped in constants/battle_constants.asm, the wBossAITraceLookaheadBonusTop
buffer and the in-driver trace-init/store paths must follow. This audit
catches the half-update case.

Exit 0 on PASS, 1 on FAIL.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRAM = ROOT / "ram" / "wram.asm"
DRIVER_SRC = ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm"
CONSTS = ROOT / "constants" / "battle_constants.asm"


def expected_n() -> int:
    """Parse BOSS_AI_LOOKAHEAD_N from constants/battle_constants.asm."""
    text = CONSTS.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^\s*DEF\s+BOSS_AI_LOOKAHEAD_N\s+EQU\s+(\d+)", text, re.MULTILINE)
    if not m:
        raise SystemExit("FAIL: cannot parse BOSS_AI_LOOKAHEAD_N from constants/battle_constants.asm")
    return int(m.group(1))


def main() -> int:
    n = expected_n()
    failures: list[str] = []

    wram_text = WRAM.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^wBossAITraceLookaheadBonusTop::\s*ds\s+(\d+)", wram_text, re.MULTILINE)
    if not m:
        failures.append("could not find wBossAITraceLookaheadBonusTop declaration in ram/wram.asm")
    elif int(m.group(1)) != n:
        failures.append(
            f"wBossAITraceLookaheadBonusTop is `ds {m.group(1)}` but BOSS_AI_LOOKAHEAD_N = {n}"
        )

    drv = DRIVER_SRC.read_text(encoding="utf-8", errors="replace")

    # The trace-init block at the top of the driver writes one zero per candidate
    # via `ld [hli], a` (N-1 times) then `ld [hl], a` (final). Count consecutive
    # zero-writes following the trace pointer setup.
    init_re = re.compile(
        r"ld\s+hl,\s*wBossAITraceLookaheadBonusTop\s*\n"
        r"((?:\s*ld\s+\[hli\],\s*a\s*\n)*)\s*ld\s+\[hl\],\s*a"
    )
    m = init_re.search(drv)
    if not m:
        failures.append("could not find trace-init block setting wBossAITraceLookaheadBonusTop")
    else:
        hli_count = m.group(1).count("ld [hli], a")
        total = hli_count + 1  # +1 for the final ld [hl], a
        if total != n:
            failures.append(
                f"trace-init writes {total} zeros but BOSS_AI_LOOKAHEAD_N = {n}"
            )

    # The per-candidate trace store block uses `cp <N>` to bound the trace index.
    # It must compare against BOSS_AI_LOOKAHEAD_N, not a hardcoded literal.
    if re.search(r"ld\s+a,\s*b\s*\n\s*cp\s+\d+\s*\n\s*jr\s+nc,\s*\.after_trace", drv):
        failures.append(
            "trace store block uses a hardcoded literal in `cp N` "
            "(must be `cp BOSS_AI_LOOKAHEAD_N`)"
        )

    if not re.search(
        r"ld\s+a,\s*b\s*\n\s*cp\s+BOSS_AI_LOOKAHEAD_N\s*\n\s*jr\s+nc,\s*\.after_trace",
        drv,
    ):
        failures.append(
            "missing `ld a, b / cp BOSS_AI_LOOKAHEAD_N / jr nc, .after_trace` "
            "trace store guard"
        )

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1

    print(f"PASS: trace width consistent with BOSS_AI_LOOKAHEAD_N = {n}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
