#!/usr/bin/env python3
"""Audit mechanics helper docs and Boss AI fixture notes for known drift."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = ROOT / "scripts" / "generate_hack_mechanics_reference.py"
REFERENCE_PATH = ROOT / "docs" / "agent_navigation" / "hack_mechanics_reference.md"

DOCS_AND_NOTES = (
    ROOT / "docs" / "agent_navigation" / "gen2_vs_modern_mechanics.md",
    REFERENCE_PATH,
    ROOT / "docs" / "mechanics_changes_from_base.md",
    ROOT / "docs" / "boss_ai_teaching_heuristics.md",
    ROOT / "tools" / "boss_ai_preference" / "README.md",
    ROOT / "tools" / "boss_ai_preference" / "SCHEMA.md",
    ROOT / "tools" / "boss_ai_preference" / "fixtures" / "boss_ai_preference_fixtures.json",
    ROOT / "tools" / "boss_ai_preference" / "labels" / "boss_ai_pairwise_preferences.jsonl",
    ROOT / "tools" / "boss_ai_preference" / "labels" / "boss_ai_trajectory_preferences.jsonl",
    ROOT / "tools" / "boss_ai_preference" / "labels" / "boss_ai_plan_demonstrations.jsonl",
)

FORBIDDEN_PHRASES = (
    "Steel still resists Dark and Ghost",
    "SPECIAL = 19",
    "FIRE is 19",
    "Pidgey's Flying resistance",
    "Steelix in the back resists Fire and Ground",
    "Pivots to a Fire-resistant ace.",
    "Piloswine 4x weak to Fire",
    "Cloyster shares the weakness",
    "Dark moves are physical",
    "Crunch is physical",
    "Ground super-effective into Miltank",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("hack_mechanics_reference", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        fail(f"could not load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def run_generated_reference_check() -> None:
    proc = subprocess.run(
        [sys.executable, str(GENERATOR_PATH), "--check"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout, end="")
        print(proc.stderr, end="", file=sys.stderr)
        fail("hack mechanics reference is not regenerated from current source")


def scan_for_forbidden_phrases() -> None:
    for path in DOCS_AND_NOTES:
        if not path.exists():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for phrase in FORBIDDEN_PHRASES:
                if phrase in line:
                    fail(f"{path.relative_to(ROOT)}:{line_number}: forbidden stale mechanics phrase: {phrase}")
            if (
                "super-effective Ground damage" in line
                and "not super-effective Ground damage" not in line
            ):
                fail(
                    f"{path.relative_to(ROOT)}:{line_number}: Ground damage claim must be checked; "
                    "Magnitude into Miltank is neutral, not super-effective"
                )


def assert_source_mechanics(module: ModuleType) -> None:
    type_values, special_threshold = module.parse_type_constants()
    chart, foresight_removed = module.parse_type_matchups()
    moves = {
        move.constant: move
        for move in module.parse_moves(type_values, special_threshold)
    }

    require(special_threshold == 20, "SPECIAL threshold should be 20 with FIRE as first special type")
    require(type_values["DARK"] >= special_threshold, "DARK must remain special")
    require(type_values["GHOST"] < special_threshold, "GHOST must remain physical")
    require(type_values["POISON"] < special_threshold, "POISON must remain physical")

    require(chart[("NORMAL", "GHOST")] == 0, "Normal into Ghost should be 0x without Foresight")
    require(chart[("FIGHTING", "GHOST")] == 0, "Fighting into Ghost should be 0x without Foresight")
    require(foresight_removed[("NORMAL", "GHOST")] == 0, "Foresight sentinel should mark Normal/Ghost")
    require(foresight_removed[("FIGHTING", "GHOST")] == 0, "Foresight sentinel should mark Fighting/Ghost")
    require(chart.get(("GRASS", "FLYING"), 10) == 10, "Grass into Flying should be neutral in this hack")
    require(chart.get(("GROUND", "FIRE"), 10) == 10, "Ground into Fire should be neutral in this hack")
    require(chart.get(("DARK", "STEEL"), 10) == 10, "Dark into Steel should be neutral in this hack")
    require(chart[("GHOST", "STEEL")] == 0, "Ghost into Steel should be 0x in this hack")
    require(chart.get(("PSYCHIC_TYPE", "POISON"), 10) == 10, "Psychic into Poison should be neutral in this hack")
    require(chart[("POISON", "NORMAL")] == 20, "Poison into Normal should be 2x in this hack")

    require(module.move_category(moves["CRUNCH"], type_values, special_threshold) == "special", "Crunch should be special")
    require(module.move_category(moves["BITE"], type_values, special_threshold) == "special", "Bite should be special")
    require(module.move_category(moves["SHADOW_BALL"], type_values, special_threshold) == "physical", "Shadow Ball should be physical")
    require(module.move_category(moves["SLUDGE_BOMB"], type_values, special_threshold) == "physical", "Sludge Bomb should be physical")
    require(moves["PETAL_DANCE"].power == 120 and moves["PETAL_DANCE"].pp == 10, "Petal Dance should be 120 BP / 10 PP")
    require(moves["FUTURE_SIGHT"].power == 120, "Future Sight should be 120 BP")
    require(moves["DRAGON_DANCE"].effect == "EFFECT_DRAGON_DANCE", "Dragon Dance should use EFFECT_DRAGON_DANCE")

    type_passive_source = (ROOT / "engine" / "battle" / "type_passive_damage_mods.asm").read_text(encoding="utf-8")
    boss_platform_source = (ROOT / "engine" / "battle" / "ai" / "boss_platform.asm").read_text(encoding="utf-8")
    require(
        "TypePassive_ApplyDragonsMajestyMultiplier_Far" in type_passive_source,
        "Dragon's Majesty source helper should exist",
    )
    require(
        "cp NO_EFFECT" in type_passive_source and "ld c, NOT_VERY_EFFECTIVE" in type_passive_source,
        "Dragon's Majesty should convert immunities to resistance",
    )
    require(
        "EFFECT_FUTURE_SIGHT" in type_passive_source,
        "Dragon's Majesty exclusion list should include Future Sight",
    )
    require(
        "BossAI_ApplyDragonsMajestyNoItem" in boss_platform_source,
        "Boss AI no-item matchup helpers should mirror Dragon's Majesty",
    )


def assert_reference_notes() -> None:
    text = REFERENCE_PATH.read_text(encoding="utf-8")
    require("Maintenance rule:" in text, "reference must include maintenance rule")
    require(
        "Stat stages multiply the already-calculated battle stat, not the base" in text,
        "reference must include calculated-stat boost warning",
    )
    require("Dragon Dance is not plain +Atk here" in text, "reference must document Dragon Dance bestattackup")
    require("## Dragon Type Passives" in text, "reference must include Dragon type passives")
    require("Dragon's Majesty is an offensive damage rule" in text, "reference must document Dragon's Majesty")
    require("Imperial Scales is the Dragon defensive damage rule" in text, "reference must document Imperial Scales")


def main() -> int:
    module = load_generator()
    run_generated_reference_check()
    scan_for_forbidden_phrases()
    assert_source_mechanics(module)
    assert_reference_notes()
    print("PASS: mechanics docs and Boss AI fixture notes are source-aligned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
