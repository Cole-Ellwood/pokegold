#!/usr/bin/env python3
"""Confirm BossAI_ApplyLookaheadToTopMoveCandidates uses the dynamic
lower-is-better futility cutoff against wBossAILookaheadRunningBest, not
the legacy stack-pushed initial-best bound.

The cutoff is load-bearing: a regression to the static bound would silently
loosen the lookahead behavior in near-tie cases.

Exit 0 on PASS, 1 on FAIL.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm"

DRIVER_NAME = "BossAI_ApplyLookaheadToTopMoveCandidates"
LABEL_RE = re.compile(r"^([A-Za-z0-9_]+):\s*(?:;.*)?$")


def extract_driver_body(text: str) -> list[str]:
    """Return the source lines from the driver's label to the next top-level label."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{DRIVER_NAME}:"):
            start = i
            break
    if start is None:
        return []
    body: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.endswith(":") and not stripped.startswith(".") and LABEL_RE.match(stripped):
            break
        body.append(line)
    return body


def main() -> int:
    text = SRC.read_text(encoding="utf-8", errors="replace")
    body = extract_driver_body(text)
    if not body:
        print(f"FAIL: could not find {DRIVER_NAME} in {SRC}", file=sys.stderr)
        return 1

    joined = "\n".join(body)

    failures: list[str] = []

    # 1. Initial running_best write after the min scan (direct addressing).
    if "ld [wBossAILookaheadRunningBest], a" not in joined:
        failures.append(
            "missing initial direct write to wBossAILookaheadRunningBest after .best_done"
        )

    # 2. Running_best read inside the eval loop (the futility cutoff). Either
    #    a direct `ld a, [SYM]` for the +CAP comparison, or an hl-swap
    #    (`ld hl, SYM`) used by the update path.
    if (
        "ld a, [wBossAILookaheadRunningBest]" not in joined
        and "ld hl, wBossAILookaheadRunningBest" not in joined
    ):
        failures.append(
            "missing read of wBossAILookaheadRunningBest inside .eval_loop "
            "(no futility cutoff)"
        )

    # 3. At least TWO writes total — initial set + tightening update after eval.
    #    The tightening update may be written via either direct addressing
    #    (`ld [SYM], a`) or hl-swap (`ld hl, SYM` followed by `ld [hl], a`).
    direct_writes = joined.count("ld [wBossAILookaheadRunningBest], a")
    hl_swap_blocks = len(
        re.findall(
            r"ld\s+hl,\s*wBossAILookaheadRunningBest\b[^\n]*\n(?:[^\n]*\n){0,8}?[^\n]*ld\s+\[hl\],\s*a",
            joined,
        )
    )
    total_writes = direct_writes + hl_swap_blocks
    if total_writes < 2:
        failures.append(
            f"expected >= 2 writes to wBossAILookaheadRunningBest "
            f"(initial + tightening); direct={direct_writes}, hl-swap={hl_swap_blocks}"
        )

    # 4. The legacy static bound should be gone:
    #    `add BOSS_AI_LOOKAHEAD_BONUS_CAP` followed shortly by `push af` then a
    #    later `pop af` paired with `cp [hl]` was the v1 pattern. The new code
    #    no longer pushes the bound onto the stack.
    if re.search(
        r"add\s+BOSS_AI_LOOKAHEAD_BONUS_CAP\s*\n\s*push\s+af",
        joined,
    ):
        failures.append(
            "legacy stack-pushed initial-best bound is still present "
            "(add BOSS_AI_LOOKAHEAD_BONUS_CAP / push af)"
        )

    # 5. The futility comparison should add CAP to running_best, then cp against
    #    the candidate score. Confirm the add+cp sequence exists.
    if not re.search(
        r"ld\s+a,\s*\[wBossAILookaheadRunningBest\]\s*\n\s*add\s+BOSS_AI_LOOKAHEAD_BONUS_CAP\s*\n\s*cp\s+c",
        joined,
    ):
        failures.append(
            "missing 'ld a, [wBossAILookaheadRunningBest] / add CAP / cp c' "
            "futility-test sequence"
        )

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1

    print(f"PASS: {DRIVER_NAME} uses the dynamic running-best futility cutoff.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
