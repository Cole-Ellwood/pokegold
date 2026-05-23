#!/usr/bin/env python3
"""Audit P3 revealed-effect matrix coverage.

The P3 contract moves the row-shaped revealed-effect interactions out of
scattered hand-coded predicates and into `data/boss_ai/revealed_effect_matrix.asm`.
Some effect families named by the roadmap are not row-shaped yet (for example
own-side Perish escape and Spikes/Rapid Spin hazard state), so this audit
separates:

  (a) runtime matrix rows that the new dispatcher consumes, and
  (b) public-source anchors that remain bespoke because their input shape is
      board-state, not a simple revealed-effect/candidate-effect pair.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm"
SWITCH = ROOT / "engine" / "battle" / "ai" / "boss_policy_switch.asm"
MATRIX = ROOT / "data" / "boss_ai" / "revealed_effect_matrix.asm"


RUNTIME_ROWS = {
    "protect_selfdestruct": (
        "EFFECT_PROTECT",
        "EFFECT_SELFDESTRUCT",
        "BOSS_AI_REM_RULE_DISCOURAGE",
        "10",
    ),
    "protect_hyper_beam": (
        "EFFECT_PROTECT",
        "EFFECT_HYPER_BEAM",
        "BOSS_AI_REM_RULE_DISCOURAGE",
        "4",
    ),
    "recovery_status_denial": (
        "BOSS_AI_REM_GROUP_RECOVERY",
        "BOSS_AI_REM_GROUP_STATUS_DENIAL",
        "BOSS_AI_REM_RULE_RECOVERY_STATUS_DENIAL",
        "4",
    ),
    "recovery_phaze_denial": (
        "BOSS_AI_REM_GROUP_RECOVERY",
        "EFFECT_FORCE_SWITCH",
        "BOSS_AI_REM_RULE_RECOVERY_UTILITY_DENIAL",
        "3",
    ),
    "revealed_encore_avoidance": (
        "EFFECT_ENCORE",
        "BOSS_AI_REM_GROUP_COMMITMENT",
        "BOSS_AI_REM_RULE_FAST_ENCORE_AVOIDANCE",
        "5",
    ),
    "last_move_encore_trap": (
        "BOSS_AI_REM_GROUP_LAST_MOVE_ENCORE_TRAP",
        "EFFECT_ENCORE",
        "BOSS_AI_REM_RULE_LAST_MOVE_ENCORE_TRAP",
        "6",
    ),
    "selfdestruct_protect": (
        "EFFECT_SELFDESTRUCT",
        "EFFECT_PROTECT",
        "BOSS_AI_REM_RULE_SELFDESTRUCT_PROTECT",
        "5",
    ),
    "sleep_preempt": (
        "EFFECT_SLEEP",
        "BOSS_AI_REM_GROUP_SLEEP_PREEMPT",
        "BOSS_AI_REM_RULE_SLEEP_PREEMPT",
        "5",
    ),
    "destiny_bond_avoidance": (
        "EFFECT_DESTINY_BOND",
        "BOSS_AI_REM_GROUP_DAMAGING",
        "BOSS_AI_REM_RULE_DESTINY_BOND_AVOIDANCE",
        "7",
    ),
    "counter_avoidance": (
        "EFFECT_COUNTER",
        "BOSS_AI_REM_GROUP_PHYSICAL_DAMAGE",
        "BOSS_AI_REM_RULE_COUNTERCOAT_AVOIDANCE",
        "5",
    ),
    "mirror_coat_avoidance": (
        "EFFECT_MIRROR_COAT",
        "BOSS_AI_REM_GROUP_SPECIAL_DAMAGE",
        "BOSS_AI_REM_RULE_COUNTERCOAT_AVOIDANCE",
        "5",
    ),
}


BESPOKE_PUBLIC_ANCHORS = {
    "disable_public_fail_gate": (POLICY, ("cp EFFECT_DISABLE", ".check_disable", "wPlayerDisableCount")),
    "mean_look_public_fail_gate": (POLICY, ("cp EFFECT_MEAN_LOOK", ".check_mean_look", "SUBSTATUS_CANT_RUN")),
    "perish_public_escape": (SWITCH, ("BossAI_EnemyPerishEscapeUrgent", "wEnemyPerishCount", "SUBSTATUS_PERISH")),
    "rampage_bias": (POLICY, ("EFFECT_ROLLOUT", "EFFECT_FURY_CUTTER", ".ApplyRampMoveBias")),
    "charge_bias": (POLICY, ("EFFECT_SOLARBEAM", "SUBSTATUS_CHARGED", ".ApplyChargeMoveBias")),
    "hazard_spin_bias": (POLICY, ("EFFECT_SPIKES", "EFFECT_RAPID_SPIN", ".ApplyRevealedRapidSpinSpikesRisk")),
}


OLD_BESPOKE_LABELS = (
    ".ApplyRevealedDestinyBondAvoidance",
    ".ApplyRevealedCounterCoatAvoidance",
    ".ApplyRevealedProtectCommitmentRisk",
    ".ApplyRevealedRecoveryDenialBias",
    ".ApplyRevealedFastEncoreAvoidance",
    ".ApplyLastMoveEncoreTrapBias",
    ".ApplyRevealedSelfdestructProtectBias",
    ".ApplyRevealedSleepPreemptBias",
)


def _read(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8", errors="replace")


def _matrix_rows(text: str) -> set[tuple[str, str, str, str]]:
    rows: set[tuple[str, str, str, str]] = set()
    for match in re.finditer(r"^\s*db\s+([^;\n]+)", text, flags=re.MULTILINE):
        fields = [field.strip() for field in match.group(1).split(",")]
        if len(fields) == 4:
            rows.add(tuple(fields))  # type: ignore[arg-type]
    return rows


def check_dispatcher(policy: str, matrix: str) -> tuple[bool, str]:
    required = (
        'INCLUDE "data/boss_ai/revealed_effect_matrix.asm"',
        "call .ApplyRevealedEffectMatrixBias",
        "ld hl, BossAIRevealedEffectMatrix",
        "call .MatrixCandidateMatchesA",
        "call .MatrixRevealedKeyMatchesA",
        "call .MatrixApplyRuleA",
        "jp .PlayerHasRevealedEffectA",
        "wBossAIScorePtr",
    )
    missing = [needle for needle in required if needle not in policy]
    if missing:
        return False, f"(a) FAIL: dispatcher missing {missing}"
    if "BossAIRevealedEffectMatrix:" not in matrix:
        return False, "(a) FAIL: matrix label missing"
    match = re.search(
        r"\.ApplyRevealedEffectMatrixBias(?P<body>.*?)\.matrix_loop",
        policy,
        flags=re.S,
    )
    if not match:
        return False, "(a) FAIL: couldn't locate .ApplyRevealedEffectMatrixBias body"
    body = match.group("body")
    tier_gate = [
        "ld a, [wBossAITier]",
        "cp AI_TIER_MID",
        "ret c",
        "ld hl, BossAIRevealedEffectMatrix",
    ]
    pos = -1
    for needle in tier_gate:
        nxt = body.find(needle, pos + 1)
        if nxt < 0:
            return False, f"(a) FAIL: matrix dispatcher missing tier-gate sequence `{needle}`"
        pos = nxt
    return True, "(a) PASS: revealed-effect matrix is included, tier-gated, and dispatched from move scoring."


def check_runtime_rows(matrix: str) -> tuple[bool, str]:
    rows = _matrix_rows(matrix)
    missing = [name for name, row in RUNTIME_ROWS.items() if row not in rows]
    if missing:
        return False, f"(b) FAIL: matrix missing runtime rows {missing}"
    return True, f"(b) PASS: matrix has all {len(RUNTIME_ROWS)} runtime revealed-effect rows."


def check_old_labels_removed(policy: str) -> tuple[bool, str]:
    leftovers = [label for label in OLD_BESPOKE_LABELS if label in policy]
    if leftovers:
        return False, f"(c) FAIL: old bespoke labels still live in boss_policy_move.asm: {leftovers}"
    return True, "(c) PASS: old row-shaped bespoke revealed-effect labels were removed."


def check_bespoke_public_anchors() -> tuple[bool, str]:
    missing: list[str] = []
    for name, (path, needles) in BESPOKE_PUBLIC_ANCHORS.items():
        text = _read(path)
        absent = [needle for needle in needles if needle not in text]
        if absent:
            missing.append(f"{name}: {absent}")
    if missing:
        return False, "(d) FAIL: public bespoke anchors missing: " + "; ".join(missing)
    return True, f"(d) PASS: {len(BESPOKE_PUBLIC_ANCHORS)} non-row-shaped public anchors remain covered."


def main() -> int:
    try:
        policy = _read(POLICY)
        matrix = _read(MATRIX)
        checks = [
            check_dispatcher(policy, matrix),
            check_runtime_rows(matrix),
            check_old_labels_removed(policy),
            check_bespoke_public_anchors(),
        ]
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        return 1

    ok = all(result for result, _ in checks)
    for _, message in checks:
        print(message)
    print()
    if ok:
        print("PASS: P3 revealed-effect matrix coverage green.")
        return 0
    print("FAIL: P3 revealed-effect matrix coverage failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
