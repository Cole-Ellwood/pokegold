#!/usr/bin/env python3
from __future__ import annotations

import re
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

EXPECTED_TIER_CONSTANTS = {
    "AI_SWITCH_THRESHOLD_EARLY": 80,
    "AI_SWITCH_THRESHOLD_MID": 70,
    "AI_SWITCH_THRESHOLD_LATE": 60,
    "BOSS_AI_LOOKAHEAD_ENABLE_TIER_MIN": 2,
    "BOSS_AI_LOOKAHEAD_HORIZON_MID": 4,
    "BOSS_AI_LOOKAHEAD_HORIZON_LATE": 5,
    "BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_EARLY": 4,
    "BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_MID": 7,
    "BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_LATE": 10,
    "BOSS_AI_SCOUT_PROB_TIER_EARLY": 51,
    "BOSS_AI_SCOUT_PROB_TIER_MID": 102,
    "BOSS_AI_SCOUT_PROB_TIER_LATE": 153,
}

EXPECTED_TIER_WEIGHT_ROWS = (
    (4, 2, 1, 1, 1, 1, 2),
    (5, 3, 2, 2, 1, 1, 2),
    (7, 4, 4, 2, 2, 3, 1),
    (5, 2, 1, 1, 1, 1, 2),
    (5, 3, 1, 1, 1, 1, 2),
)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"missing required file: {path.relative_to(ROOT)}")


def require_contains(text: str, needle: str, label: str, errors: list[str]) -> None:
    if needle not in text:
        errors.append(f"{label} missing {needle!r}")


def parse_equ_constants(text: str) -> dict[str, int]:
    constants: dict[str, int] = {}
    for raw_line in text.splitlines():
        code = raw_line.split(";", 1)[0].strip()
        match = re.match(r"^DEF\s+([A-Z0-9_]+)\s+EQU\s+([0-9]+)$", code)
        if not match:
            continue
        name, value = match.groups()
        constants[name] = int(value)
    return constants


def parse_tier_weight_rows(text: str) -> list[tuple[int, ...]]:
    rows: list[tuple[int, ...]] = []
    in_table = False
    for raw_line in text.splitlines():
        code = raw_line.split(";", 1)[0].strip()
        if code in ("BossAITierWeights:", "BossAITierWeights::"):
            in_table = True
            continue
        if not in_table:
            continue
        if not code:
            continue
        if code.endswith(":") and not code.startswith("."):
            break
        if not code.startswith("db "):
            continue
        rows.append(tuple(int(part.strip()) for part in code[3:].split(",")))
    return rows


def label_body(text: str, label: str) -> str:
    pattern = rf"^{re.escape(label)}\n(?P<body>.*?)(?=^[A-Za-z0-9_.]+:|\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    return match.group("body") if match else ""


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
    for needle in REQUIRED_CONSTANTS:
        require_contains(constants, needle, "battle_constants.asm policy constants", errors)
    for needle in REQUIRED_POLICY_SNIPPETS:
        require_contains(policy, needle, "POLICY_DESIGN.md", errors)
    for needle in REQUIRED_PLATFORM_SNIPPETS:
        require_contains(platform, needle, "PLATFORM_API.md", errors)

    parsed_constants = parse_equ_constants(constants)
    for name, expected in EXPECTED_TIER_CONSTANTS.items():
        actual = parsed_constants.get(name)
        if actual != expected:
            errors.append(
                f"battle_constants.asm {name} is {actual!r}; expected exact value {expected}"
            )

    switch_values = [
        parsed_constants.get("AI_SWITCH_THRESHOLD_EARLY"),
        parsed_constants.get("AI_SWITCH_THRESHOLD_MID"),
        parsed_constants.get("AI_SWITCH_THRESHOLD_LATE"),
    ]
    if switch_values != sorted(switch_values or [], reverse=True):
        errors.append(
            "switch thresholds must become less conservative by tier: early > mid > late"
        )

    for ordered_names, label in (
        (
            (
                "BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_EARLY",
                "BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_MID",
                "BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_LATE",
            ),
            "plausible risk weights",
        ),
        (
            (
                "BOSS_AI_SCOUT_PROB_TIER_EARLY",
                "BOSS_AI_SCOUT_PROB_TIER_MID",
                "BOSS_AI_SCOUT_PROB_TIER_LATE",
            ),
            "scout probabilities",
        ),
    ):
        values = [parsed_constants.get(name) for name in ordered_names]
        if any(value is None for value in values) or not (values[0] < values[1] < values[2]):
            errors.append(f"{label} must increase by tier: early < mid < late")

    weight_rows = parse_tier_weight_rows(boss)
    if tuple(weight_rows[: len(EXPECTED_TIER_WEIGHT_ROWS)]) != EXPECTED_TIER_WEIGHT_ROWS:
        errors.append(
            "BossAITierWeights first rows must exactly encode early/mid/late skill "
            f"and early ramp rows: got {weight_rows[:len(EXPECTED_TIER_WEIGHT_ROWS)]!r}"
        )

    lookahead_body = label_body(boss, "BossAI_ApplyLookaheadToTopMoveCandidates:")
    if not lookahead_body:
        errors.append("could not locate BossAI_ApplyLookaheadToTopMoveCandidates body")
    elif (
        "cp BOSS_AI_LOOKAHEAD_ENABLE_TIER_MIN" not in lookahead_body
        or "ret c" not in lookahead_body
    ):
        errors.append("lookahead must be gated off below AI_TIER_MID")

    switch_body = label_body(boss, "BossAI_GetSwitchThreshold:")
    for needle in (
        "cp AI_TIER_LATE",
        "ld a, AI_SWITCH_THRESHOLD_LATE",
        "cp AI_TIER_MID",
        "ld a, AI_SWITCH_THRESHOLD_MID",
        "ld a, AI_SWITCH_THRESHOLD_EARLY",
    ):
        require_contains(switch_body, needle, "BossAI_GetSwitchThreshold", errors)

    for label, required in (
        (
            "BossAI_GetTierPlausibleRiskWeight:",
            (
                "BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_LATE",
                "BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_MID",
                "BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_EARLY",
            ),
        ),
        (
            "BossAI_GetScoutRollThreshold:",
            (
                "BOSS_AI_SCOUT_PROB_TIER_LATE",
                "BOSS_AI_SCOUT_PROB_TIER_MID",
                "BOSS_AI_SCOUT_PROB_TIER_EARLY",
            ),
        ),
    ):
        body = label_body(boss, label)
        if not body:
            errors.append(f"could not locate {label} body")
            continue
        for needle in required:
            require_contains(body, needle, label, errors)

    for needle in (
        "BOSS_AI_LOOKAHEAD_HORIZON_LATE - 1",
        "BOSS_AI_LOOKAHEAD_HORIZON_MID - 1",
    ):
        require_contains(boss, needle, "multi-turn projection tier horizon", errors)

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
