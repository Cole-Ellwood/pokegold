#!/usr/bin/env python3
"""Audit Uniform Haki Oracle invariants (P1H lane closure).

Verifies the contract from docs/boss_ai_spec.md and the P1H section of
docs/boss_ai_rom_expansion_2026-05-23_codex_task.md:

  (a) No surviving bespoke `BossAI_TryMortyHakiOracle`-style entry points.
      The refactor renamed to `BossAI_OracleHakiRead`; any leftover bespoke
      Morty-only label would indicate the refactor missed a site.

  (b) Per-leader taunt rows cover all 16 eligible trainer classes
      (the gate-rule included set). Missing rows would mean a Haki fire
      on that leader produces no taunt — silent contract violation.

  (c) Exclusion table covers all 7 Kanto-minus-Blue classes
      (BROCK, MISTY, LT_SURGE, ERIKA, JANINE, SABRINA, BLAINE). Missing
      entries would let those classes fire Haki post-Champion, breaking
      the design intent ("player outranks them, so they don't get the
      unfair-intervention privilege").

  (d) Haki dispatch is sequenced after player action parse and before
      `DetermineMoveOrder`, so priority and speed-order outcomes can see
      the Oracle-selected enemy move.

  (e) Flush call sites are sequenced BEFORE the enemy-action dispatcher in
      both `Battle_EnemyFirst:` and `Battle_PlayerFirst:`. Wrong order would
      print the taunt AFTER the move animation (no longer a pre-fire signal).

  (f) Oracle Haki feeds the locked player move into normal Boss AI move
      scoring. It must not regress to a Haki-only list of special-case
      answers such as Destiny Bond / Protect / Endure.

Promotion to release-smoke floor: this audit is mechanically reliable
(grep-based, no ROM dependency), so it's a candidate for inclusion in
the release-smoke set once any Haki regression is observed in playtest.
For now it stays in the targeted-audit tier.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Expected included trainer classes per docs/boss_ai_spec.md:67-100 (gate rule).
EXPECTED_INCLUDED_CLASSES = (
    "MORTY", "CHUCK", "JASMINE", "PRYCE", "CLAIR",
    "RIVAL1", "RIVAL2",
    "EXECUTIVEM", "EXECUTIVEF",
    "WILL", "BRUNO", "KOGA", "KAREN",
    "CHAMPION",
    "BLUE", "RED",
)

EXPECTED_EXCLUDED_CLASSES = (
    "BROCK", "MISTY", "LT_SURGE", "ERIKA", "JANINE", "SABRINA", "BLAINE",
)

# File anchors.
EXCLUDED_PATH = REPO / "data" / "trainers" / "ai_haki_excluded.asm"
TAUNTS_PATH = REPO / "data" / "boss_ai" / "haki_taunts.asm"
BATTLE_TEXT_PATH = REPO / "data" / "text" / "battle.asm"
TAUNT_QUEUE_PATH = REPO / "engine" / "battle" / "ai" / "haki_taunt_queue.asm"
ORACLE_PATH = REPO / "engine" / "battle" / "ai" / "boss_policy_switch.asm"
CORE_PATH = REPO / "engine" / "battle" / "core.asm"
MOVE_POLICY_PATH = REPO / "engine" / "battle" / "ai" / "boss_policy_move.asm"


EXCLUDED_PATH_PARTS = (
    ".git",
    ".claude",            # sibling worktrees + scratch
    ".claude_handoffs",
    ".local",
    "workspace",
    "dist",
    "pokegold.gbc.apr26-backup",
)


def _is_excluded(path: Path) -> bool:
    return any(part in path.parts for part in EXCLUDED_PATH_PARTS)


def check_no_bespoke_entry_points() -> tuple[bool, str]:
    """(a) No surviving `BossAI_TryMortyHakiOracle` references in live source.

    Skips sibling git worktrees under `.claude/worktrees/` and scratch
    directories — those carry pre-refactor snapshots and would create
    false positives without indicating any live-source regression.
    """
    bad_paths: list[str] = []
    for path in REPO.rglob("*.asm"):
        if _is_excluded(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "BossAI_TryMortyHakiOracle" in text:
            bad_paths.append(str(path.relative_to(REPO)))
    if bad_paths:
        return False, (
            "(a) FAIL: bespoke `BossAI_TryMortyHakiOracle` references survive in: "
            + ", ".join(bad_paths)
        )
    return True, "(a) PASS: no surviving bespoke `BossAI_TryMortyHakiOracle` entry points in live source."


def check_excluded_coverage() -> tuple[bool, str]:
    """(c) BossAIHakiExcludedClasses has all 7 Kanto-minus-Blue classes."""
    if not EXCLUDED_PATH.exists():
        return False, f"(c) FAIL: {EXCLUDED_PATH} not found"
    text = EXCLUDED_PATH.read_text(encoding="utf-8")
    listed = set(re.findall(r"db\s+(\w+)\b", text)) - {"0"}
    missing = [c for c in EXPECTED_EXCLUDED_CLASSES if c not in listed]
    extra = sorted(listed - set(EXPECTED_EXCLUDED_CLASSES))
    if missing:
        return False, f"(c) FAIL: BossAIHakiExcludedClasses missing {missing}"
    if extra:
        return False, f"(c) FAIL: BossAIHakiExcludedClasses has unexpected entries {extra}"
    return True, f"(c) PASS: BossAIHakiExcludedClasses has exactly the 7 Kanto-minus-Blue classes."


def check_taunt_coverage() -> tuple[bool, str]:
    """(b) BossAIHakiTauntMap covers all 16 eligible trainer classes."""
    if not TAUNTS_PATH.exists():
        return False, f"(b) FAIL: {TAUNTS_PATH} not found"
    text = TAUNTS_PATH.read_text(encoding="utf-8")
    # Map rows: `db <CLASS>, <ID>`
    rows = re.findall(r"^\s*db\s+(\w+)\s*,\s*\w+\s*(?:;|$)", text, flags=re.MULTILINE)
    classes_with_taunt = set(rows) - {"0"}
    missing = [c for c in EXPECTED_INCLUDED_CLASSES if c not in classes_with_taunt]
    if missing:
        return False, f"(b) FAIL: BossAIHakiTauntMap missing classes {missing}"
    return True, (
        f"(b) PASS: BossAIHakiTauntMap covers all {len(EXPECTED_INCLUDED_CLASSES)} eligible "
        f"trainer classes ({len(rows)} (class, id) rows total)."
    )


def check_taunt_text_bank() -> tuple[bool, str]:
    """Haki taunt text labels must live in BattleText's bank.

    BossAI_FlushPendingHakiTaunt passes the queued pointer through
    StdBattleTextbox, which switches to BANK(BattleText) before PrintText.
    If the text labels are defined in the Boss AI bank instead, the same
    pointer address is read from the wrong bank and can walk garbage text.
    """
    if not TAUNTS_PATH.exists():
        return False, f"text-bank FAIL: {TAUNTS_PATH} not found"
    if not BATTLE_TEXT_PATH.exists():
        return False, f"text-bank FAIL: {BATTLE_TEXT_PATH} not found"
    taunts = TAUNTS_PATH.read_text(encoding="utf-8")
    battle_text = BATTLE_TEXT_PATH.read_text(encoding="utf-8")
    labels = re.findall(r"^\s*dw\s+(BossAIHakiTaunt\w+Text)\b", taunts, flags=re.MULTILINE)
    missing = [label for label in sorted(set(labels)) if f"{label}:" not in battle_text]
    local_defs = re.findall(r"^(BossAIHakiTaunt\w+Text):", taunts, flags=re.MULTILINE)
    if missing:
        return False, f"text-bank FAIL: taunt pointer labels missing from data/text/battle.asm: {missing}"
    if local_defs:
        return False, f"text-bank FAIL: taunt text labels must not be defined in data/boss_ai/haki_taunts.asm: {local_defs}"
    return True, (
        "text-bank PASS: Haki taunt pointers resolve to labels in data/text/battle.asm, "
        "the bank used by StdBattleTextbox."
    )


def _label_body(text: str, label: str) -> str | None:
    m = re.search(
        rf"^{re.escape(label)}:.*?(?=^\S+:)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    return m.group(0) if m else None


def check_pre_order_hook() -> tuple[bool, str]:
    """(d) Haki dispatch runs after player intent exists and before order is finalized."""
    if not CORE_PATH.exists():
        return False, f"(d) FAIL: {CORE_PATH} not found"
    text = CORE_PATH.read_text(encoding="utf-8")
    main = text.split("Battle_EnemyFirst:", 1)[0]
    p_parse = main.find("ParsePlayerAction")
    p_haki = main.find("BossAI_OracleHakiRead")
    p_order = main.find("DetermineMoveOrder")
    if p_parse < 0:
        return False, "(d) FAIL: ParsePlayerAction call site not found before turn-order dispatch"
    if p_haki < 0:
        return False, "(d) FAIL: BossAI_OracleHakiRead pre-order call site not found"
    if p_order < 0:
        return False, "(d) FAIL: DetermineMoveOrder call site not found before turn-order dispatch"
    if not (p_parse < p_haki < p_order):
        return False, (
            f"(d) FAIL: Haki hook ordering wrong. Positions: "
            f"ParsePlayerAction={p_parse}, BossAI_OracleHakiRead={p_haki}, "
            f"DetermineMoveOrder={p_order}. Expected parse < haki < order."
        )
    return True, (
        "(d) PASS: BossAI_OracleHakiRead runs after ParsePlayerAction and "
        "before DetermineMoveOrder, independent of enemy-first/player-first order."
    )


def _check_flush_body(body: str | None, label: str) -> tuple[bool, str]:
    if body is None:
        return False, f"(e) FAIL: {label}: label not found in engine/battle/core.asm"
    p_dispatch = body.find("AI_SwitchOrTryItem")
    p_flush = body.find("BossAI_FlushPendingHakiTaunt")
    p_enemy_action = body.find("EnemyTurn_EndOpponentProtectEndureDestinyBond")
    if p_dispatch < 0:
        return False, f"(e) FAIL: AI_SwitchOrTryItem call site not found in {label}"
    if p_flush < 0:
        return False, f"(e) FAIL: BossAI_FlushPendingHakiTaunt call site not found in {label}"
    if p_enemy_action < 0:
        return False, (
            f"(e) FAIL: EnemyTurn_EndOpponentProtectEndureDestinyBond call site not "
            f"found in {label} (anchor for ordering check)"
        )
    if not (p_dispatch < p_flush < p_enemy_action):
        return False, (
            f"(e) FAIL: {label} flush ordering wrong. Positions: "
            f"AI_SwitchOrTryItem={p_dispatch}, "
            f"BossAI_FlushPendingHakiTaunt={p_flush}, "
            f"EnemyTurn_EndOpponentProtectEndureDestinyBond={p_enemy_action}. "
            f"Expected dispatch < flush < enemy_action."
        )
    return True, f"(e) PASS: {label} flushes Haki taunts before the enemy move animation."


def check_flush_sequencing() -> tuple[bool, str]:
    """(e) Flush call appears in both turn-order branches before enemy action."""
    if not CORE_PATH.exists():
        return False, f"(e) FAIL: {CORE_PATH} not found"
    text = CORE_PATH.read_text(encoding="utf-8")
    checks = [
        _check_flush_body(_label_body(text, "Battle_EnemyFirst"), "Battle_EnemyFirst"),
        _check_flush_body(_label_body(text, "Battle_PlayerFirst"), "Battle_PlayerFirst"),
    ]
    failures = [message for ok, message in checks if not ok]
    if failures:
        return False, "; ".join(failures)
    return True, "(e) PASS: Haki taunts flush before enemy action in both turn-order branches."


def check_oracle_uses_normal_move_scoring() -> tuple[bool, str]:
    """(f) Haki should re-score through the normal Boss AI move model."""
    if not ORACLE_PATH.exists():
        return False, f"(f) FAIL: {ORACLE_PATH} not found"
    if not MOVE_POLICY_PATH.exists():
        return False, f"(f) FAIL: {MOVE_POLICY_PATH} not found"
    oracle_text = ORACLE_PATH.read_text(encoding="utf-8")
    move_text = MOVE_POLICY_PATH.read_text(encoding="utf-8")
    oracle_body = _label_body(oracle_text, "BossAI_OracleHakiRead") or ""
    score_body = _label_body(oracle_text, "BossAI_OracleScoreKnownPlayerAction") or ""
    if not oracle_body:
        return False, "(f) FAIL: BossAI_OracleHakiRead body not found"
    forbidden = [
        "BossAI_ApplyKnownPlayerActionOracleBias",
        "BossAI_HakiPlayerSelectedStrongSuperEffectiveAttack",
    ]
    found_forbidden = [name for name in forbidden if name in oracle_text]
    if found_forbidden:
        return False, (
            "(f) FAIL: Haki still has bespoke locked-move answer predicates: "
            + ", ".join(found_forbidden)
        )
    for token in (
        "BossAI_BeginOracleHakiScoring",
        "BossAI_OracleScoreKnownPlayerAction",
        "BossAI_EndOracleHakiScoring",
    ):
        if token not in oracle_body:
            return False, f"(f) FAIL: BossAI_OracleHakiRead does not call {token}"
    if "farcall CheckEnemyLockedIn" not in oracle_body:
        return False, "(f) FAIL: BossAI_OracleHakiRead does not inherit enemy lock-in gating"
    for token in (
        "BossAI_OracleResetMoveScores",
        "BossAI_ApplyMoveModel",
        "BossAI_ApplyLookaheadToTopMoveCandidates",
        "BossAI_ChooseBestOracleMove",
    ):
        if token not in score_body:
            return False, f"(f) FAIL: BossAI_OracleScoreKnownPlayerAction does not call {token}"
    if "BossAI_AddHakiSelectedMoveToPlausibleMasks" not in move_text:
        return False, "(f) FAIL: move scoring does not add the Haki-selected move to plausible masks"
    if "BossAI_HakiSelectedMove:" not in move_text or "wCurPlayerMove" not in move_text:
        return False, "(f) FAIL: move scoring has no quarantined selected-move helper"
    return True, (
        "(f) PASS: Haki re-scores through BossAI_ApplyMoveModel/lookahead with "
        "the locked move available through a quarantined scoring context."
    )


def check_oracle_uniform_label() -> tuple[bool, str]:
    """Smoke-check: `BossAI_OracleHakiRead` exists (the new uniform label)."""
    if not ORACLE_PATH.exists():
        return False, f"smoke FAIL: {ORACLE_PATH} not found"
    text = ORACLE_PATH.read_text(encoding="utf-8")
    if "BossAI_OracleHakiRead:" not in text:
        return False, (
            "smoke FAIL: BossAI_OracleHakiRead: label not found in "
            "engine/battle/ai/boss_policy_switch.asm — the uniform Oracle "
            "entry point may have been renamed again or removed."
        )
    return True, "smoke PASS: BossAI_OracleHakiRead: label present in boss_policy_switch.asm."


def main() -> int:
    checks = [
        check_oracle_uniform_label(),
        check_no_bespoke_entry_points(),
        check_taunt_coverage(),
        check_taunt_text_bank(),
        check_excluded_coverage(),
        check_pre_order_hook(),
        check_flush_sequencing(),
        check_oracle_uses_normal_move_scoring(),
    ]
    all_ok = all(ok for ok, _ in checks)
    for _, msg in checks:
        print(msg)
    print()
    if all_ok:
        print("PASS: Uniform Haki Oracle invariants intact (no bespoke entry points + "
              "taunt + exclusion + flush-sequencing all green).")
        return 0
    else:
        print("FAIL: Uniform Haki Oracle invariants violated. Fix the failing items above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
