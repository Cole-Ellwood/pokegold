from __future__ import annotations

import unittest
from tools.debugger.catalog import (
    build_capability_report,
    build_inventory,
    triage_request,
)
from tools.debugger.mirrors import build_compare_plan
from tools.debugger.next_steps import NEXT_STEP_ROWS, build_next_step
from tools.debugger.testgen import suggest_tests
from tools.debugger.workflow import build_gate_plan, command_is_runnable


class CatalogTriageTests(unittest.TestCase):
    def test_inventory_lists_existing_debugger_subsystems(self) -> None:
        report = build_inventory()
        subsystem_ids = {subsystem["id"] for subsystem in report["subsystems"]}

        self.assertIn("boss_ai", subsystem_ids)
        self.assertIn("damage", subsystem_ids)
        self.assertIn("trace_runtime", subsystem_ids)

    def test_capability_report_marks_godmode_surface_ready(self) -> None:
        report = build_capability_report()
        statuses = {
            capability["id"]: capability["status"]
            for capability in report["capabilities"]
        }

        self.assertTrue(report["ready"])
        self.assertEqual(statuses["unified_front_door"], "complete")
        self.assertEqual(statuses["boss_ai_state_of_art"], "complete")
        self.assertEqual(statuses["damage_state_of_art"], "complete")
        self.assertEqual(statuses["whole_rom_ingest"], "complete")
        self.assertEqual(statuses["whole_rom_replay_localization"], "complete")
        self.assertEqual(report["blocking_gap_count"], 0)

    def test_capability_report_suppresses_closed_gap_action_for_wrong_switch_replay(self) -> None:
        report = build_capability_report()
        replay = next(
            capability
            for capability in report["capabilities"]
            if capability["id"] == "whole_rom_replay_localization"
        )

        self.assertEqual(report["gap_action_count"], 0)
        self.assertEqual(replay["status"], "complete")
        self.assertEqual(replay["gap_actions"], [])
        self.assertEqual(replay["gaps"], [])

    def test_damage_changed_file_triages_to_damage_debugger(self) -> None:
        report = triage_request(
            changed_files=("engine/battle/late_gen_held_items.asm",),
        )
        commands = "\n".join(report["commands"])

        self.assertIn("tools.damage_debugger.clobber_smoke", commands)
        self.assertIn("check_farcall", commands)

    def test_boss_ai_symptom_triages_to_boss_ai_debugger(self) -> None:
        report = triage_request(symptom="boss ai selector picked a bad switch")
        commands = "\n".join(report["commands"])

        self.assertIn("tools.boss_ai_debugger", commands)
        self.assertIn("check_boss_ai_debugger_done.py", commands)

    def test_symptom_keyword_matching_does_not_match_inside_words(self) -> None:
        report = triage_request(symptom="Air Balloon Ground immunity")
        tests = suggest_tests(symptom="Air Balloon Ground immunity")
        compare = build_compare_plan(symptom="Air Balloon Ground immunity")
        match_ids = {match["id"] for match in report["matches"]}
        damage_match = next(match for match in report["matches"] if match["id"] == "damage_chain")
        commands = "\n".join(report["commands"] + tests["commands"] + compare["commands"])

        self.assertNotIn("boss_ai", match_ids)
        self.assertIn("damage_chain", match_ids)
        self.assertIn("air balloon", damage_match["matched_symptom_keywords"])
        self.assertIn("ground", damage_match["matched_symptom_keywords"])
        self.assertIn("immunity", damage_match["matched_symptom_keywords"])
        self.assertIn("tools.damage_debugger", commands)
        self.assertNotIn("tools.boss_ai_debugger", commands)

    def test_unknown_triage_returns_general_baseline(self) -> None:
        report = triage_request(symptom="unknown title screen issue")

        self.assertEqual(report["matches"][0]["id"], "general")
        self.assertIn("python -m tools.debugger audit", report["commands"])

    def test_triage_routes_frozen_music_after_trainer_to_runtime_state(self) -> None:
        report = triage_request(
            symptom="music is playing but frozen after trainer battle and Flaaffy evolution",
        )

        self.assertEqual(report["matches"][0]["id"], "script_vm_impossible_state")
        commands = "\n".join(report["commands"])
        self.assertIn("state-inspect", commands)
        self.assertIn("wScriptBank", commands)
        self.assertIn("wScriptPos", commands)

    def test_changed_pokemon_data_routes_to_semantic_inspection(self) -> None:
        report = build_next_step(changed_files=("data/pokemon/evos_attacks.asm",))
        rec = report["recommendation"]

        self.assertEqual(rec["matched_lane"], "pokemon_semantics")
        self.assertIn("learnset-inspect", rec["first_command"])
        self.assertIn("data/pokemon/evos_attacks.asm", rec["source_refs"])
        self.assertIn("Source semantic inspection", rec["evidence_standard"][0])
        self.assertIn("expected semantics", rec["disproof_standard"][0])
        self.assertIn("learnset-inspect", rec["regression_gate"])

    def test_headless_battle_routes_to_headless_simulator(self) -> None:
        report = build_next_step(symptom="I want a text-only battle simulator with fixed RNG")
        rec = report["recommendation"]

        self.assertEqual(rec["symptom_class"], "headless_battle_simulation")
        self.assertEqual(rec["matched_lane"], "headless_battle")
        self.assertIn("tools.headless_battle", rec["first_command"])
        self.assertIn("check_headless_battle_simulator.py", rec["regression_gate"])
        self.assertIn("repeat/max_turns", rec["proof_limit"])
        self.assertIn("auto_replace_or", rec["proof_limit"])
        self.assertIn("wild_random_move", rec["proof_limit"])
        self.assertIn("Full Restore", rec["proof_limit"])
        self.assertIn("stat-stage", rec["proof_limit"])
        self.assertIn("single-stat stage moves", rec["proof_limit"])
        self.assertIn("setup moves", rec["proof_limit"])
        self.assertIn("self-heal moves", rec["proof_limit"])
        self.assertIn("poison-status moves", rec["proof_limit"])
        self.assertIn("paralysis-status moves", rec["proof_limit"])
        self.assertIn("damaging status secondaries", rec["proof_limit"])
        self.assertIn("drain moves", rec["proof_limit"])
        self.assertIn("sleep action denial", rec["proof_limit"])
        self.assertIn("selected held PSNCUREBERRY", rec["proof_limit"])
        self.assertIn("Safeguard/Substitute status blockers", rec["proof_limit"])
        self.assertIn("Rocky Helmet", rec["proof_limit"])

    def test_headless_battle_routes_turn_by_turn_wording(self) -> None:
        report = build_next_step(symptom="Can the debugger walk a battle turn by turn with text only?")
        rec = report["recommendation"]
        triage = triage_request(symptom="Can the debugger walk a battle turn by turn with text only?")

        self.assertEqual(rec["symptom_class"], "headless_battle_simulation")
        self.assertEqual(rec["matched_lane"], "headless_battle")
        self.assertIn("headless_battle", {match["id"] for match in triage["matches"]})
        self.assertIn("actions-or-turns-or-repeat", rec["evidence_standard"][0])
        self.assertIn("active HP restore item actions", rec["evidence_standard"][0])
        self.assertIn("stat-stage state", rec["evidence_standard"][0])
        self.assertIn("single-stat stage moves", rec["evidence_standard"][0])
        self.assertIn("setup moves", rec["evidence_standard"][0])
        self.assertIn("self-heal moves", rec["evidence_standard"][0])
        self.assertIn("poison-status moves", rec["evidence_standard"][0])
        self.assertIn("paralysis-status moves", rec["evidence_standard"][0])
        self.assertIn("damaging burn/poison/paralysis status secondaries", rec["evidence_standard"][0])
        self.assertIn("Leech Life/Giga Drain drain moves", rec["evidence_standard"][0])
        self.assertIn("sleep action denial/wake handling", rec["evidence_standard"][0])
        self.assertIn("selected held PSNCUREBERRY", rec["evidence_standard"][0])
        self.assertIn("Safeguard/Substitute status blockers", rec["evidence_standard"][0])
        self.assertIn("implicit replacement without auto_replace_or", rec["disproof_standard"][0])

    def test_vram_graphics_triage_uses_contract_audit(self) -> None:
        report = triage_request(
            changed_files=("home/gfx.asm",),
            symptom="Cyndaquil evolved to Quilava then reset and colors inverted",
        )
        match_ids = {match["id"] for match in report["matches"]}
        commands = "\n".join(report["commands"])
        gate = build_gate_plan(changed_files=("home/gfx.asm",))
        gate_commands = [step["command"] for step in gate["steps"]]

        self.assertIn("vram_request_contract", match_ids)
        self.assertIn("banking_and_abi", match_ids)
        self.assertIn("python tools\\audit\\check_vram_request_contract.py", commands)
        self.assertEqual(gate_commands[0], "python tools\\audit\\check_vram_request_contract.py")
