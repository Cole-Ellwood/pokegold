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

  (d) Flush call site sequenced BEFORE the enemy-action dispatcher.
      `callfar BossAI_FlushPendingHakiTaunt` in engine/battle/core.asm
      must appear in `Battle_EnemyFirst:` between `AI_SwitchOrTryItem`
      and `EnemyTurn_EndOpponentProtectEndureDestinyBond`. Wrong order
      would print the taunt AFTER the move animation (no longer a
      pre-fire signal).

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
TAUNT_QUEUE_PATH = REPO / "engine" / "battle" / "ai" / "haki_taunt_queue.asm"
ORACLE_PATH = REPO / "engine" / "battle" / "ai" / "boss_policy_switch.asm"
CORE_PATH = REPO / "engine" / "battle" / "core.asm"


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


def check_flush_sequencing() -> tuple[bool, str]:
    """(d) Flush call appears between AI_SwitchOrTryItem and the enemy-action dispatcher."""
    if not CORE_PATH.exists():
        return False, f"(d) FAIL: {CORE_PATH} not found"
    text = CORE_PATH.read_text(encoding="utf-8")
    # Find Battle_EnemyFirst body
    m = re.search(
        r"^Battle_EnemyFirst:.*?(?=^\S+:)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not m:
        return False, "(d) FAIL: Battle_EnemyFirst: label not found in engine/battle/core.asm"
    body = m.group(0)
    # Find positions of the three load-bearing tokens.
    p_dispatch = body.find("AI_SwitchOrTryItem")
    p_flush = body.find("BossAI_FlushPendingHakiTaunt")
    p_enemy_action = body.find("EnemyTurn_EndOpponentProtectEndureDestinyBond")
    if p_dispatch < 0:
        return False, "(d) FAIL: AI_SwitchOrTryItem call site not found in Battle_EnemyFirst"
    if p_flush < 0:
        return False, "(d) FAIL: BossAI_FlushPendingHakiTaunt call site not found in Battle_EnemyFirst"
    if p_enemy_action < 0:
        return False, (
            "(d) FAIL: EnemyTurn_EndOpponentProtectEndureDestinyBond call site not "
            "found in Battle_EnemyFirst (anchor for ordering check)"
        )
    if not (p_dispatch < p_flush < p_enemy_action):
        return False, (
            f"(d) FAIL: flush ordering wrong. Positions: "
            f"AI_SwitchOrTryItem={p_dispatch}, "
            f"BossAI_FlushPendingHakiTaunt={p_flush}, "
            f"EnemyTurn_EndOpponentProtectEndureDestinyBond={p_enemy_action}. "
            f"Expected dispatch < flush < enemy_action."
        )
    return True, (
        "(d) PASS: BossAI_FlushPendingHakiTaunt is sequenced between "
        "AI_SwitchOrTryItem and EnemyTurn_EndOpponentProtectEndureDestinyBond "
        "in Battle_EnemyFirst (taunt prints before enemy move animation)."
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
        check_excluded_coverage(),
        check_flush_sequencing(),
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
