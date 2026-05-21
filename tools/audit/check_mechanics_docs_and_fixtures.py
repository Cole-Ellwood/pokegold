#!/usr/bin/env python3
"""Audit mechanics helper docs and Boss AI fixture notes for known drift."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = ROOT / "scripts" / "generate_hack_mechanics_reference.py"
BALANCE_AUDIT_GENERATOR_PATH = ROOT / "scripts" / "generate_balance_audit.py"
REFERENCE_PATH = ROOT / "docs" / "agent_navigation" / "hack_mechanics_reference.md"
BALANCE_AUDIT_PATH = ROOT / "docs" / "generated" / "balance_audit.md"
INVENTORY_PATH = ROOT / "docs" / "pokemon_mastery" / "romhack_deltas" / "mechanics_inventory.md"
ROMHACK_BOSS_AI_MASTERY_PATH = ROOT / "docs" / "pokemon_mastery" / "romhack_boss_ai_mastery.md"
ROMHACK_PLAY_MASTERY_TRANSFER_PATH = ROOT / "docs" / "pokemon_mastery" / "romhack_play_mastery_transfer.md"
ROMHACK_TRANSFER_DRILLS_PATH = ROOT / "docs" / "pokemon_mastery" / "romhack_drills" / "transfer_drills_001.jsonl"
ROMHACK_TRANSFER_DRILL_SCORES_PATH = ROOT / "docs" / "pokemon_mastery" / "romhack_drills" / "transfer_drills_001_scores.jsonl"
ROMHACK_TRANSFER_DRILL_RESULTS_PATH = ROOT / "docs" / "pokemon_mastery" / "romhack_drills" / "transfer_drills_001_results.md"

DOCS_AND_NOTES = (
    ROOT / "docs" / "agent_navigation" / "gen2_vs_modern_mechanics.md",
    REFERENCE_PATH,
    INVENTORY_PATH,
    ROMHACK_BOSS_AI_MASTERY_PATH,
    ROMHACK_PLAY_MASTERY_TRANSFER_PATH,
    ROOT / "docs" / "pokemon_mastery" / "romhack_drills" / "README.md",
    ROMHACK_TRANSFER_DRILLS_PATH,
    ROMHACK_TRANSFER_DRILL_SCORES_PATH,
    ROMHACK_TRANSFER_DRILL_RESULTS_PATH,
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


def normalize_generated_timestamp(lines: list[str]) -> list[str]:
    return [
        "Generated: <normalized>" if line.startswith("Generated: ") else line
        for line in lines
    ]


def run_balance_audit_data_check() -> None:
    proc = subprocess.run(
        [sys.executable, str(BALANCE_AUDIT_GENERATOR_PATH), "--stdout"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout, end="")
        print(proc.stderr, end="", file=sys.stderr)
        fail("could not regenerate balance audit for data comparison")

    current = normalize_generated_timestamp(BALANCE_AUDIT_PATH.read_text(encoding="utf-8").splitlines())
    regenerated = normalize_generated_timestamp(proc.stdout.splitlines())
    if current != regenerated:
        fail("balance audit data has drifted from current source")


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

    battle_constants = (ROOT / "constants" / "battle_constants.asm").read_text(encoding="utf-8")
    spikes_source = (ROOT / "engine" / "battle" / "move_effects" / "spikes.asm").read_text(encoding="utf-8")
    rapid_spin_source = (ROOT / "engine" / "battle" / "move_effects" / "rapid_spin.asm").read_text(encoding="utf-8")
    boss_policy_move = (ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm").read_text(encoding="utf-8")
    require("SCREENS_SPIKES_2" in battle_constants, "Spikes should have a second layer bit")
    require("SCREENS_SPIKES_MASK" in battle_constants, "Spikes layer mask should exist")
    require("cp 3" in spikes_source, "Spikes should fail only at three layers")
    require("res SCREENS_SPIKES_2" in rapid_spin_source, "Rapid Spin should clear the second Spikes bit")
    require(".ApplySpikesLayerBias" in boss_policy_move, "Boss AI should include layer-aware Spikes scoring")

    item_constants = (ROOT / "constants" / "item_constants.asm").read_text(encoding="utf-8")
    late_gen_items = (ROOT / "engine" / "battle" / "late_gen_held_items.asm").read_text(encoding="utf-8")
    for item in (
        "LIFE_ORB",
        "CHOICE_BAND",
        "CHOICE_SPECS",
        "CHOICE_SCARF",
        "ASSAULT_VEST",
        "EXPERT_BELT",
        "MUSCLE_BAND",
        "WISE_GLASSES",
        "EVOLITE",
        "AIR_BALLOON",
        "SHELL_BELL",
        "ROCKY_HELMET",
        "METRONOME_ITEM",
    ):
        require(item in item_constants, f"{item} should have an item constant")
    for held_effect in (
        "HELD_LIFE_ORB",
        "HELD_CHOICE_BAND",
        "HELD_CHOICE_SPECS",
        "HELD_CHOICE_SCARF",
        "HELD_ASSAULT_VEST",
        "HELD_EXPERT_BELT",
        "HELD_MUSCLE_BAND",
        "HELD_WISE_GLASSES",
        "HELD_EVOLITE",
        "HELD_AIR_BALLOON",
        "HELD_SHELL_BELL",
        "HELD_ROCKY_HELMET",
        "HELD_METRONOME",
    ):
        require(held_effect in late_gen_items, f"{held_effect} should be handled by late-gen item code")

    clobber_smoke = (ROOT / "tools" / "damage_debugger" / "clobber_smoke.py").read_text(encoding="utf-8")
    require("afterhit_air_balloon" in clobber_smoke, "Air Balloon pop should have a runtime after-hit smoke")
    require("wOTPartyMon1Item" in clobber_smoke, "Air Balloon smoke should verify party item clear")


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


def assert_inventory_notes() -> None:
    text = INVENTORY_PATH.read_text(encoding="utf-8")
    required_phrases = (
        "Status: active front-door reference.",
        "## Source-Of-Truth Order",
        "Local assembly/data source.",
        "`docs/agent_navigation/hack_mechanics_reference.md`",
        "`docs/generated/balance_audit.md`",
        "Historical manifest/change logs",
        "exact current truth",
        "## What Is New Or Different",
        "### Type Chart And Categories",
        "Dark remains special",
        "Poison hits Normal super-effectively",
        "### Type Passives",
        "### Spikes And Rapid Spin",
        "Spikes has 3 layers",
        "Rapid Spin clears all layers",
        "### Late-Gen Held Items",
        "Eviolite / EVOLITE",
        "### Contact System",
        "### Move Data",
        "### Pokemon Stats, Types, TMs, And Learnsets",
        "## AI Assumption Firewall",
        "`romhack_deltas/mechanics_pending_index.md`",
    )
    for phrase in required_phrases:
        require(phrase in text, f"mechanics inventory missing required phrase: {phrase}")


def assert_boss_ai_mastery_notes() -> None:
    text = ROMHACK_BOSS_AI_MASTERY_PATH.read_text(encoding="utf-8")
    required_phrases = (
        "Status: active implementation-prep reference.",
        "## Source Stack",
        "Do not teach the boss AI from vanilla GSC memory",
        "## Boss AI Legality Model",
        "Ordinary boss AI should not use hidden party slots",
        "## Pre-Scoring Mechanics Gate",
        "## Local Mechanics That Must Shape Scoring",
        "Dark remains special and hits Steel neutrally",
        "Spikes is a route multiplier, not a checkbox",
        "Successful Rapid Spin clears all layers",
        "Eviolite / EVOLITE",
        "Air Balloon makes Ground attacks no-effect",
        "## Boss Scoring Skeleton",
        "## Candidate Generation Contract",
        "Missing a live role is a candidate-generation bug",
        "Promoting the wrong live role is a route-budget bug",
        "## Implementation Prep Checklist",
        "## Current Open Risks",
    )
    for phrase in required_phrases:
        require(phrase in text, f"romhack boss AI mastery missing required phrase: {phrase}")


def assert_play_mastery_transfer_notes() -> None:
    text = ROMHACK_PLAY_MASTERY_TRANSFER_PATH.read_text(encoding="utf-8")
    required_phrases = (
        "Status: active transfer workbench.",
        "## Transfer Ladder",
        "## GSC Concept To Romhack Rewrite",
        "Three-layer Spikes creates separate 0->1, 1->2, and 2->3 decisions",
        "## Boss-Meta Families From Current Rosters",
        "### Hazard, Spin, And Phaze Economy",
        "### Late-Gen Item Commitments",
        "### Type-Passive And Contact Routing",
        "## Damage Range Anchors",
        "Choice Specs turns Psychic",
        "## Debugger-Assisted Mechanics Rule",
        "Air Balloon quick matchup check",
        "## Drill Packet 001: Romhack Transfer Decisions",
        "RMT-001: Lt. Surge Air Balloon Opening",
        "RMT-004: Sabrina Choice Specs Lock",
        "RMT-011: Red Snorlax RestTalk Anchor",
        "## Scoring The Transfer Drills",
        "`local_mechanic_checked`",
        "failure_tag",
        "## Next Work",
    )
    for phrase in required_phrases:
        require(phrase in text, f"romhack play mastery transfer missing required phrase: {phrase}")


def assert_romhack_transfer_drills() -> None:
    required_fields = {
        "id",
        "boss",
        "contamination_label",
        "source_refs",
        "public_state",
        "gsc_transfer",
        "romhack_rewrite",
        "expected_candidate_classes",
        "mechanics_gates",
        "failure_tags",
    }
    required_ids = {f"RMT-{index:03d}" for index in range(1, 13)}
    seen_ids: set[str] = set()
    bosses: set[str] = set()
    mechanic_needles = {
        "Air Balloon": False,
        "3-layer": False,
        "Choice": False,
        "Life Orb": False,
        "Rocky Helmet": False,
        "Dragon Dance": False,
        "Rest": False,
        "Explosion": False,
    }
    for line_number, raw_line in enumerate(ROMHACK_TRANSFER_DRILLS_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        require(raw_line.strip(), f"{ROMHACK_TRANSFER_DRILLS_PATH.relative_to(ROOT)}:{line_number}: blank JSONL line")
        try:
            row = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            fail(f"{ROMHACK_TRANSFER_DRILLS_PATH.relative_to(ROOT)}:{line_number}: invalid JSON: {exc}")
        missing = required_fields - set(row)
        require(not missing, f"{ROMHACK_TRANSFER_DRILLS_PATH.relative_to(ROOT)}:{line_number}: missing fields {sorted(missing)}")
        drill_id = row["id"]
        require(drill_id not in seen_ids, f"duplicate romhack transfer drill id: {drill_id}")
        seen_ids.add(drill_id)
        bosses.add(row["boss"])
        joined = json.dumps(row, sort_keys=True)
        for needle in mechanic_needles:
            if needle in joined:
                mechanic_needles[needle] = True
        require(row["contamination_label"] == "practice_source_derived", f"{drill_id}: unexpected contamination label")
        for list_field in ("source_refs", "expected_candidate_classes", "mechanics_gates", "failure_tags"):
            require(isinstance(row[list_field], list) and row[list_field], f"{drill_id}: {list_field} must be a non-empty list")

    require(required_ids <= seen_ids, f"romhack transfer drills missing ids: {sorted(required_ids - seen_ids)}")
    require(len(bosses) >= 8, "romhack transfer drills should cover at least eight distinct bosses")
    missing_needles = [needle for needle, present in mechanic_needles.items() if not present]
    require(not missing_needles, f"romhack transfer drills missing mechanic coverage: {missing_needles}")


def assert_romhack_transfer_drill_scores() -> None:
    required_score_fields = {
        "local_mechanic_checked",
        "boss_route_named",
        "player_route_named",
        "top_three_cover_roles",
        "route_budget_top1",
        "hidden_info_clean",
        "damage_or_fixture_needed_named",
    }
    required_row_fields = {
        "id",
        "contamination_label",
        "top_action_class",
        "top_three_candidate_classes",
        "why_1_over_2",
        "mechanics_gates_checked",
        "damage_or_fixture_needed",
        "score",
        "failure_tag_if_missed",
    }
    drill_ids = {
        json.loads(line)["id"]
        for line in ROMHACK_TRANSFER_DRILLS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    score_ids: set[str] = set()
    for line_number, raw_line in enumerate(ROMHACK_TRANSFER_DRILL_SCORES_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        require(raw_line.strip(), f"{ROMHACK_TRANSFER_DRILL_SCORES_PATH.relative_to(ROOT)}:{line_number}: blank JSONL line")
        try:
            row = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            fail(f"{ROMHACK_TRANSFER_DRILL_SCORES_PATH.relative_to(ROOT)}:{line_number}: invalid JSON: {exc}")
        missing = required_row_fields - set(row)
        require(not missing, f"{ROMHACK_TRANSFER_DRILL_SCORES_PATH.relative_to(ROOT)}:{line_number}: missing fields {sorted(missing)}")
        drill_id = row["id"]
        require(drill_id in drill_ids, f"{drill_id}: score row has no matching drill")
        require(drill_id not in score_ids, f"duplicate romhack transfer score id: {drill_id}")
        score_ids.add(drill_id)
        require(row["contamination_label"] == "practice_source_derived", f"{drill_id}: unexpected score contamination label")
        require(isinstance(row["top_three_candidate_classes"], list) and len(row["top_three_candidate_classes"]) == 3, f"{drill_id}: expected exactly three candidate classes")
        require(isinstance(row["mechanics_gates_checked"], list) and row["mechanics_gates_checked"], f"{drill_id}: mechanics_gates_checked must be a non-empty list")
        score = row["score"]
        require(isinstance(score, dict), f"{drill_id}: score must be an object")
        missing_score = required_score_fields - set(score)
        require(not missing_score, f"{drill_id}: score missing fields {sorted(missing_score)}")
        for field in required_score_fields:
            require(isinstance(score[field], bool), f"{drill_id}: score.{field} must be boolean")
        require(row["damage_or_fixture_needed"].strip(), f"{drill_id}: damage_or_fixture_needed must be non-empty")

    require(drill_ids == score_ids, f"score ids do not match drill ids: missing={sorted(drill_ids - score_ids)} extra={sorted(score_ids - drill_ids)}")


def assert_romhack_transfer_results_notes() -> None:
    text = ROMHACK_TRANSFER_DRILL_RESULTS_PATH.read_text(encoding="utf-8")
    required_phrases = (
        "Status: practice-source-derived self-check, not validation.",
        "Decisions answered | 12",
        "Distinct bosses covered | 10",
        "`local_mechanic_checked` | 12/12",
        "`top_three_cover_roles` | 12/12",
        "`hidden_info_clean` | 12/12",
        "not proof of live romhack play mastery",
        "Air Balloon is now covered for Ground immunity",
        "Next packet should test",
    )
    for phrase in required_phrases:
        require(phrase in text, f"romhack transfer drill results missing required phrase: {phrase}")


def main() -> int:
    module = load_generator()
    run_generated_reference_check()
    run_balance_audit_data_check()
    scan_for_forbidden_phrases()
    assert_source_mechanics(module)
    assert_reference_notes()
    assert_inventory_notes()
    assert_boss_ai_mastery_notes()
    assert_play_mastery_transfer_notes()
    assert_romhack_transfer_drills()
    assert_romhack_transfer_drill_scores()
    assert_romhack_transfer_results_notes()
    print("PASS: mechanics docs and Boss AI fixture notes are source-aligned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
