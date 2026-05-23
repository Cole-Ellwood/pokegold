#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.coach_plan_templates import (  # noqa: E402
    parse_coach_plan_templates,
    run_coach_plan_template_report,
)


CONSTANTS = ROOT / "constants" / "battle_constants.asm"
MOVE_POLICY = ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm"
TEMPLATE_DATA = ROOT / "data" / "boss_ai" / "coach_plan_templates.asm"

EXPECTED_ROWS = {
    ("CHAMPION", "LANCE", "DRAGONITE"): {
        "plan_id": "BOSS_PLAN_TEMPLATE_SETUP_ONCE_THEN_ATTACK",
        "phase_moves": ["DRAGON_DANCE", "OUTRAGE", "OUTRAGE"],
        "stop_effect": "EFFECT_FORCE_SWITCH",
    },
    ("KOGA", "KOGA1", "MUK"): {
        "plan_id": "BOSS_PLAN_TEMPLATE_PRESSURE_RECOVER_THEN_LOCK",
        "phase_moves": ["TOXIC", "CURSE", "REST"],
        "stop_effect": "EFFECT_HEAL_BELL",
    },
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8", errors="replace")


def require(text: str, needle: str, context: str) -> None:
    if needle not in text:
        fail(f"{context}: missing `{needle}`")


def require_order(text: str, needles: list[str], context: str) -> None:
    pos = -1
    for needle in needles:
        nxt = text.find(needle, pos + 1)
        if nxt < 0:
            fail(f"{context}: missing `{needle}` in order")
        pos = nxt


def block(text: str, label: str) -> str:
    pattern = re.compile(rf"^{re.escape(label)}:{{1,2}}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        fail(f"missing label {label}")
    start = match.start()
    next_label = re.search(
        r"^[A-Za-z_][A-Za-z0-9_]*::?:\s*$",
        text[match.end() :],
        re.MULTILINE,
    )
    if not next_label:
        return text[start:]
    return text[start : match.end() + next_label.start()]


def check_constants(constants: str) -> None:
    for needle in (
        "DEF BOSS_AI_COACH_TEMPLATE_ROW_SIZE EQU 9",
        "DEF BOSS_AI_COACH_TEMPLATE_MOVE_BONUS EQU 6",
        "const BOSS_PLAN_TEMPLATE_SETUP_ONCE_THEN_ATTACK",
        "const BOSS_PLAN_TEMPLATE_PRESSURE_RECOVER_THEN_LOCK",
    ):
        require(constants, needle, "coach-template constants")


def check_data_rows() -> None:
    rows = parse_coach_plan_templates()
    if len(rows) != len(EXPECTED_ROWS):
        fail(f"expected {len(EXPECTED_ROWS)} coach-template rows, found {len(rows)}")
    seen = {(row["trainer_class"], row["trainer_id"], row["species"]): row for row in rows}
    if set(seen) != set(EXPECTED_ROWS):
        fail(f"coach-template row keys mismatch: found {sorted(seen)}")
    for key, expected in EXPECTED_ROWS.items():
        row = seen[key]
        for field, wanted in expected.items():
            got = row[field]
            if got != wanted:
                fail(f"{key} {field} mismatch: got {got!r}, expected {wanted!r}")
        confidence = row["confidence"]
        if not 1 <= confidence <= 100:
            fail(f"{key} confidence must be 1..100, got {confidence}")


def check_plan_selection(move_policy: str) -> None:
    select = block(move_policy, "BossAI_SelectPlanIfNeeded")
    require_order(
        select,
        [
            ".ChooseInitialPlan",
            "call BossAI_TryCoachPlanTemplate",
            "ret c",
            "ld a, BOSS_PLAN_TEMPO_PRESSURE",
        ],
        "initial coach-template selection",
    )
    require_order(
        select,
        [
            ".AdaptPlan",
            "call BossAI_CurrentPlanIsCoachTemplate",
            "call BossAI_TryCoachPlanTemplate",
            "ret c",
            ".check_coach_valid",
            "call BossAI_CoachPlanStillValid",
            "call .DropCoachPlanToGeneric",
        ],
        "active-species coach-template selection and abandon path",
    )

    try_template = block(move_policy, "BossAI_TryCoachPlanTemplate")
    require_order(
        try_template,
        [
            "ld a, [wBossAITier]",
            "cp AI_TIER_LATE",
            "jr nc, .late",
            "and a",
            "ret",
            "call BossAI_FindCoachPlanTemplate",
            "call BossAI_CoachTemplateStopConditionClear",
        ],
        "LATE-only template gate",
    )

    stop = block(move_policy, "BossAI_CoachTemplateStopConditionClear")
    for needle in (
        "call BossAI_HasRevealedSuperEffectiveMove",
        "call BossAI_PlayerHasRevealedEffectA_Coach",
        "call BossAI_CoachExpectedMoveResistedByPlayer",
    ):
        require(stop, needle, "coach-template stop conditions")

    resist = block(move_policy, "BossAI_CoachExpectedMoveResistedByPlayer")
    require_order(
        resist,
        [
            "ld a, [wBossAIPlanPhase]",
            "and a",
            "jr z, .no",
            "call BossAI_CoachTemplateExpectedMoveFromHL",
            "ld hl, Moves + MOVE_POWER",
            "call BossAI_GetMoveAttr",
            "ld hl, Moves + MOVE_TYPE",
            "call BossAI_GetMoveAttr",
            "call BossAI_CheckTypeMatchupNoItem",
        ],
        "resisted-lock stop condition",
    )

    revealed = block(move_policy, "BossAI_PlayerHasRevealedEffectA_Coach")
    require(revealed, "ld hl, wPlayerUsedMoves", "revealed-effect public source")
    forbidden = ("wBattleMonMoves", "wBattleMonPP", "wPartyMons", "wPartySpecies")
    for symbol in forbidden:
        if re.search(rf"\b{re.escape(symbol)}\b", revealed):
            fail(f"revealed-effect stop condition reads forbidden symbol `{symbol}`")


def check_move_bias(move_policy: str) -> None:
    bias = block(move_policy, "BossAI_ApplyPlanMoveBias")
    require_order(
        bias,
        [
            "call BossAI_ApplyCoachPlanMoveBias",
            "ret c",
            "ld a, [wBossAIPlanId]",
            "cp BOSS_PLAN_SETUP_SWEEP",
        ],
        "coach-template move bias preempts generic plan bias",
    )
    require_order(
        bias,
        [
            ".check_denial",
            "cp BOSS_PLAN_ANTI_SETUP_DENIAL",
            "ret nz",
            "call BossAI_IsDenialEffect",
        ],
        "new template plan ids do not fall through to denial bias",
    )

    coach_bias = block(move_policy, "BossAI_ApplyCoachPlanMoveBias")
    require_order(
        coach_bias,
        [
            "call BossAI_CurrentPlanIsCoachTemplate",
            "call BossAI_FindCoachPlanTemplate",
            "call BossAI_CoachTemplateStopConditionClear",
            "call BossAI_CoachTemplateExpectedMoveFromHL",
            "ld a, [wEnemyMoveStruct + MOVE_ANIM]",
            "BOSS_AI_COACH_TEMPLATE_MOVE_BONUS",
            "call BossAI_EncourageScoreHL",
            "scf",
        ],
        "coach-template expected-move encouragement",
    )


def check_debugger_report() -> None:
    report = run_coach_plan_template_report()
    if not report.get("ok"):
        fail("coach-plan debugger report is not ok")
    rows = report.get("templates", [])
    if len(rows) != len(EXPECTED_ROWS):
        fail("coach-plan debugger row count mismatch")
    golden = report.get("golden_changed_decisions", [])
    if len(golden) != len(EXPECTED_ROWS):
        fail("golden changed-decision scenario count mismatch")
    for item in golden:
        if not item.get("changed_decision"):
            fail(f"golden scenario did not change decision: {item}")
        if item.get("early_tier_decision") != "generic_attack":
            fail(f"EARLY control should stay generic: {item}")
        if not item.get("stop_effect_blocks_template"):
            fail(f"stop-effect control should block template: {item}")


def main() -> int:
    constants = read(CONSTANTS)
    move_policy = read(MOVE_POLICY)
    read(TEMPLATE_DATA)

    check_constants(constants)
    check_data_rows()
    check_plan_selection(move_policy)
    check_move_bias(move_policy)
    check_debugger_report()

    print("PASS: P7 coach-plan templates")
    print("  - LATE-only Lance and Koga templates are data-backed")
    print("  - active-species template selection and abandon paths are wired")
    print("  - explicit revealed-answer stop conditions are present")
    print("  - golden scenarios change the chosen phase move only with template bonus")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
