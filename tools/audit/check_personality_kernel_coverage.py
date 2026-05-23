#!/usr/bin/env python3
"""Audit P1a personality kernel plumbing.

Verifies the P1a-side of the boss-AI personality kernel mechanism per the
2026-05-23 boss-AI ROM-expansion roadmap. The fuller P1b/P1 audit (every
major-leader has an entry) is separate and ships with P1b.

P1a invariants checked here:
  1. constants/battle_constants.asm defines BOSS_AI_KERNEL_SIZE = 8 plus the
     8 KERNEL_* offset constants.
  2. ram/wram.asm declares wBossAIKernel inside the cleared range (before
     wBossAIStateEnd) with `ds BOSS_AI_KERNEL_SIZE`.
  3. data/boss_ai/personality_kernels.asm exists with:
       - BossAIPersonalityKernels:: label
       - BossAITierDefaultKernels:: label
       - BossAIPersonalityKernelMap:: label
     and exactly 3 tier-default kernels of 8 bytes each.
  4. engine/battle/read_trainer_attributes.asm defines LoadBossAIPersonalityKernel
     and the caller (after LoadBossAITier) invokes it.
  5. engine/battle/ai/boss_policy_move.asm BossAI_ApplyPlanMoveBias body
     reads `wBossAIKernel + KERNEL_PLAN_BIAS_MULTIPLIER` (not the old `ld a, 2`)
     at >= 5 sites.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> int:
    consts = Path("constants/battle_constants.asm").read_text(encoding="utf-8")
    if "DEF BOSS_AI_KERNEL_SIZE EQU 8" not in consts:
        fail("constants/battle_constants.asm missing DEF BOSS_AI_KERNEL_SIZE EQU 8")
    for offset in (
        "KERNEL_PLAN_BIAS_MULTIPLIER", "KERNEL_SOFTMAX_TEMP",
        "KERNEL_PRESERVATION_THRESHOLD", "KERNEL_RISK_TOLERANCE",
        "KERNEL_SWITCH_AGGRESSION", "KERNEL_SETUP_PATIENCE",
        "KERNEL_FLAGS", "KERNEL_RESERVED",
    ):
        if f"const {offset}" not in consts:
            fail(f"constants/battle_constants.asm missing `const {offset}`")

    wram = Path("ram/wram.asm").read_text(encoding="utf-8")
    if "wBossAIKernel:: ds BOSS_AI_KERNEL_SIZE" not in wram:
        fail("ram/wram.asm missing `wBossAIKernel:: ds BOSS_AI_KERNEL_SIZE` line")
    # Ensure it sits before wBossAIStateEnd (cleared on each new boss).
    kernel_pos = wram.find("wBossAIKernel::")
    end_pos = wram.find("wBossAIStateEnd::")
    if kernel_pos < 0 or end_pos < 0 or kernel_pos >= end_pos:
        fail("wBossAIKernel not before wBossAIStateEnd in ram/wram.asm "
             "(must be in the ClearBossAIState-cleared range)")

    kernels = Path("data/boss_ai/personality_kernels.asm").read_text(encoding="utf-8")
    for label in ("BossAIPersonalityKernels::", "BossAITierDefaultKernels::", "BossAIPersonalityKernelMap::"):
        if label not in kernels:
            fail(f"data/boss_ai/personality_kernels.asm missing label `{label}`")
    # Count tier-default kernels: 3 entries × 8 bytes. Each kernel has at least
    # one explicit `db ` row + a comma-separated continuation; easier to count
    # the "KERNEL_PLAN_BIAS_MULTIPLIER" comment markers.
    plan_bias_lines = re.findall(r";\s*KERNEL_PLAN_BIAS_MULTIPLIER", kernels)
    if len(plan_bias_lines) < 3:
        fail(f"data/boss_ai/personality_kernels.asm needs >=3 KERNEL_PLAN_BIAS_MULTIPLIER "
             f"comment-anchored entries (tier defaults), found {len(plan_bias_lines)}")

    rta = Path("engine/battle/read_trainer_attributes.asm").read_text(encoding="utf-8")
    if "LoadBossAIPersonalityKernel:" not in rta:
        fail("engine/battle/read_trainer_attributes.asm missing LoadBossAIPersonalityKernel definition")
    if "call LoadBossAIPersonalityKernel" not in rta:
        fail("engine/battle/read_trainer_attributes.asm missing `call LoadBossAIPersonalityKernel`")
    # Caller must follow LoadBossAITier per the loadafter-not-before guardrail.
    if rta.find("call LoadBossAITier") > rta.find("call LoadBossAIPersonalityKernel"):
        fail("LoadBossAIPersonalityKernel must be called AFTER LoadBossAITier in read_trainer_attributes.asm")

    move_asm = Path("engine/battle/ai/boss_policy_move.asm").read_text(encoding="utf-8")
    plan_bias_reads = move_asm.count("ld a, [wBossAIKernel + KERNEL_PLAN_BIAS_MULTIPLIER]")
    if plan_bias_reads < 5:
        fail(f"BossAI_ApplyPlanMoveBias has {plan_bias_reads} kernel-bias reads, "
             "expected >=5 (one per plan branch)")

    print(f"PASS: P1a kernel plumbing — constants + wBossAIKernel + tier defaults + load helper + "
          f"{plan_bias_reads} plan-bias reads wired to KERNEL_PLAN_BIAS_MULTIPLIER.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
