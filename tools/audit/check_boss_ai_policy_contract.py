#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BOSS_FILES = (
    ROOT / "engine" / "battle" / "ai" / "boss_platform.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_policy_switch.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_thunks.asm",
)
CONSTANTS = ROOT / "constants" / "battle_constants.asm"
PLATFORM_API = ROOT / "engine" / "battle" / "ai" / "PLATFORM_API.md"
POLICY_DESIGN = ROOT / "engine" / "battle" / "ai" / "POLICY_DESIGN.md"
DEBUGGER = ROOT / "tools" / "boss_ai_debugger"
PREFERENCE = ROOT / "tools" / "boss_ai_preference"


REQUIRED_BOSS_LABELS = (
    "BossAI_ComputePlayerPlausibleTypeMask:",
    "BossAI_SelectPlanIfNeeded:",
    "BossAI_ApplyLookaheadToTopMoveCandidates:",
    "BossAI_SelectMove:",
    "BossAI_PredictPlayerSwitch:",
    "BossAI_ApplyRepeatPenalty:",
    "BossAI_RefineSwitchCandidateForPlausibleRisk:",
    "BossAI_ShouldScout:",
)

REQUIRED_BOSS_SNIPPETS = (
    "call .DamagingMoveBlockedByTypeImmunity\n\tret c",
    ".DamagingMoveBlockedByTypeImmunity\n\tld a, [wEnemyMoveStruct + MOVE_POWER]",
    "push hl\n\tcall BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem\n\tpop hl\n\tld a, [wTypeMatchup]\n\tand a\n\tjr nz, .damage_type_legal\n\tld a, 80\n\tcall BossAI_SetScoreHL",
    "call .StatusMoveWouldFailPublicly\n\tjr nc, .status_ok\n\tld a, 80\n\tcall BossAI_SetScoreHL",
    "cp EFFECT_SLEEP\n\tjp z, .check_sleep",
    ".check_sleep\n\tcall .PrimaryStatusBlocked\n\tret c",
    "ld a, [wEnemySleepClauseSlot]\n\tand a\n\tjp nz, .status_fail",
)

REQUIRED_CONSTANTS = (
    "DEF BOSS_AI_PLAUSIBLE_MIN_POWER EQU",
    "DEF BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_EARLY EQU",
    "DEF BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_MID",
    "DEF BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_LATE",
    "DEF BOSS_AI_SCOUT_PROB_TIER_EARLY EQU",
    "DEF BOSS_AI_REPEAT_PENALTY EQU",
    "const BOSS_PLAN_TEMPO_PRESSURE",
    "const BOSS_PLAN_SETUP_SWEEP",
    "const BOSS_PLAN_ANTI_SETUP_DENIAL",
)

REQUIRED_POLICY_SNIPPETS = (
    "Use the simpler unified public-info scorer.",
    "BossAI_ComputePlayerPlausibleTypeMask",
    "BOSSAI-004 labels are now the taste source",
    "No black-box training output lands in asm.",
)

REQUIRED_PLATFORM_SNIPPETS = (
    "Platform State Tracking",
    "Public Threat Model",
    "Policy Surface",
    "check_boss_ai_no_cheat.py",
)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"missing required file: {path.relative_to(ROOT)}")


def require_contains(text: str, needle: str, label: str, errors: list[str]) -> None:
    if needle not in text:
        errors.append(f"{label} missing {needle!r}")


def main() -> int:
    errors: list[str] = []
    boss = "\n".join(read(path) for path in BOSS_FILES)
    constants = read(CONSTANTS)
    platform = read(PLATFORM_API)
    policy = read(POLICY_DESIGN)

    for path in (DEBUGGER, PREFERENCE):
        if not path.exists():
            errors.append(f"missing required path: {path.relative_to(ROOT)}")

    for needle in REQUIRED_BOSS_LABELS:
        require_contains(boss, needle, "boss AI split architecture", errors)
    for needle in REQUIRED_BOSS_SNIPPETS:
        require_contains(boss, needle, "boss AI sleep-clause legality mirror", errors)
    for needle in REQUIRED_CONSTANTS:
        require_contains(constants, needle, "battle_constants.asm policy constants", errors)
    for needle in REQUIRED_POLICY_SNIPPETS:
        require_contains(policy, needle, "POLICY_DESIGN.md", errors)
    for needle in REQUIRED_PLATFORM_SNIPPETS:
        require_contains(platform, needle, "PLATFORM_API.md", errors)

    if errors:
        print("Boss AI policy contract audit FAILED.", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("Boss AI policy contract audit passed.")
    print("Accepted architecture: unified public-info scorer + fixture-backed debugger.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
