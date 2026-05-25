#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

from _common import fail

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.role_packages import (  # noqa: E402
    OUT_PATH,
    build_role_package_table,
    describe_species,
    package_names,
    render_role_package_asm,
)


SWITCH = ROOT / "engine" / "battle" / "ai" / "boss_policy_switch.asm"
CONSTANTS = ROOT / "constants" / "battle_constants.asm"

FORBIDDEN_CLASSIFIER_SYMBOLS = (
    "wBattleMonMoves",
    "wBattleMonPP",
    "wBattleMonItem",
    "wPartyMons",
    "wPartySpecies",
    "wCurPlayerMove",
    "wBattlePlayerAction",
    "hJoy",
    "wMenuCursor",
)

SWITCH_WEIGHTS = {
    "spinner": 2,
    "phazer": 4,
    "setup-sweeper": 8,
    "recovery-wall": 2,
    "priority-revenge": 6,
    "sleep/status-pressure": 4,
    "trap/perish-line": 10,
    "physical/special-wallbreaker": 6,
}


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
    pattern = re.compile(rf"^{re.escape(label)}::?:\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        fail(f"missing label {label}")
    start = match.start()
    next_label = re.search(r"^[A-Za-z_][A-Za-z0-9_]*::?:\s*$", text[match.end() :], re.MULTILINE)
    if not next_label:
        return text[start:]
    return text[start : match.end() + next_label.start()]


def count_table_rows(table_text: str) -> int:
    return sum(1 for line in table_text.splitlines() if line.strip().startswith("db "))


def role_bonus(packages: list[str], *, tier: str) -> int:
    if tier == "early":
        return 0
    return min(sum(SWITCH_WEIGHTS[pkg] for pkg in packages), 18)


def run_golden_changed_decision() -> None:
    rows = {row["species"]: row for row in describe_species(["MAGIKARP", "MISDREAVUS", "SKARMORY", "STARMIE", "SNORLAX"])}
    if rows["MAGIKARP"]["committed_packages"]:
        fail("golden control MAGIKARP should be unclassified")
    expected = {
        "STARMIE": {"spinner", "physical/special-wallbreaker"},
        "SKARMORY": {"phazer"},
        "SNORLAX": {"setup-sweeper", "physical/special-wallbreaker"},
        "MISDREAVUS": {"sleep/status-pressure", "trap/perish-line", "physical/special-wallbreaker"},
    }
    for species, wanted in expected.items():
        got = set(rows[species]["committed_packages"])
        if not wanted.issubset(got):
            fail(f"{species} packages {sorted(got)} missing expected {sorted(wanted)}")

    base_confidence = 60
    threshold = 70
    control = base_confidence + role_bonus(rows["MAGIKARP"]["committed_packages"], tier="mid")
    changed = base_confidence + role_bonus(rows["MISDREAVUS"]["committed_packages"], tier="mid")
    early = base_confidence + role_bonus(rows["MISDREAVUS"]["committed_packages"], tier="early")
    if control >= threshold:
        fail("golden control should stay below the switch threshold")
    if changed < threshold:
        fail("golden role-package scenario should cross the switch threshold")
    if early != base_confidence:
        fail("EARLY tier must get zero classifier bonus")


def main() -> int:
    switch = read(SWITCH)
    constants = read(CONSTANTS)
    table = read(OUT_PATH)

    expected = render_role_package_asm(build_role_package_table())
    if table != expected:
        fail("generated role-package table is stale")

    for needle in (
        "DEF BOSS_AI_ROLEPKG_SPINNER_F EQU 0",
        "DEF BOSS_AI_ROLEPKG_WALLBREAKER_F EQU 7",
        "DEF BOSS_AI_ROLEPKG_SWITCH_BONUS_CAP EQU 18",
    ):
        require(constants, needle, "role-package constants")

    require(table, "BossAIRolePackageBySpecies::", "role-package table")
    require(table, "table_width 1, BossAIRolePackageBySpecies", "role-package table")
    require(table, "assert_table_length NUM_POKEMON", "role-package table")
    rows = count_table_rows(table)
    if rows != 251:
        fail(f"role-package table must have 251 species rows, found {rows}")

    require_order(
        switch,
        [
            "call BossAI_ApplyPlausibleRiskToSwitchConfidence",
            "call BossAI_ApplyRolePackageSwitchBias",
            "call BossAI_ApplyPlanSwitchBias",
        ],
        "switch-confidence role package hook",
    )

    apply_bias = block(switch, "BossAI_ApplyRolePackageSwitchBias")
    require_order(
        apply_bias,
        [
            "ld a, [wBossAITier]",
            "cp AI_TIER_MID",
            "jr nc, .enabled",
            "ld a, b",
            "ret",
            "call BossAI_ClassifyActivePlayerRolePackage",
            "BOSS_AI_ROLEPKG_SWITCH_BONUS_CAP",
        ],
        "role package bias tier gate and cap",
    )

    classifier = block(switch, "BossAI_ClassifyActivePlayerRolePackage")
    require_order(
        classifier,
        [
            "ld a, [wBossAITier]",
            "cp AI_TIER_MID",
            "xor a",
            "ret",
            "ld a, [wBattleMonSpecies]",
            "ld hl, BossAIRolePackageBySpecies",
            "call BossAI_LastPlayerMoveRolePackageMask",
        ],
        "active role classifier public inputs",
    )
    for symbol in FORBIDDEN_CLASSIFIER_SYMBOLS:
        if re.search(rf"\b{re.escape(symbol)}\b", classifier):
            fail(f"classifier reads forbidden hidden/input symbol `{symbol}`")

    require(switch, 'INCLUDE "data/boss_ai/role_package_classifier.asm"', "role-package data include")
    require(switch, "BossAI_LastPlayerMoveRolePackageMask:", "last public move role reinforcement")

    run_golden_changed_decision()

    print("PASS: P6 role-package classifier")
    print("  - generated table covers all 251 species from public learnability")
    print("  - EARLY classifier returns unclassified; MID/LATE switch confidence can use package bits")
    print("  - debugger representative species tags match committed data")
    print("  - golden scenario crosses switch threshold only with a role package")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
