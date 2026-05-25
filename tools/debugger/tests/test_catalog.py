from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.damage_debugger import state as damage_state
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.catalog import (
    build_capability_report,
    build_inventory,
    triage_request,
)
from tools.debugger.content_mirror import build_content_mirror_report
from tools.debugger.content_scenarios import build_content_scenario_report
from tools.debugger.content_state import build_content_state_report
from tools.debugger.coverage import build_coverage_report
from tools.debugger.dynamic_taint import build_dynamic_taint_report
from tools.debugger.explain import build_explanation_report
from tools.debugger.expect import build_expectation_report
from tools.debugger.fuzz import build_fuzz_plan
from tools.debugger.generate import build_generation_plan
from tools.debugger.impact import build_impact_report
from tools.debugger.ingest import ingest_artifacts
from tools.debugger.instruction_trace import build_instruction_trace_report
from tools.debugger.investigate import build_investigation_run
from tools.debugger.localize import build_localization_plan
from tools.debugger.minimize import build_minimization_plan
from tools.debugger.mirrors import build_compare_plan
from tools.debugger.next_steps import NEXT_STEP_ROWS, build_next_step
from tools.debugger.pokemon_semantics import (
    build_grass_regrowth_report,
    build_learnset_inspection_report,
)
from tools.debugger.proof_runner import build_proof_campaign, build_proof_card, command_record
from tools.debugger.provenance import build_provenance_report
from tools.debugger.ranking import rank_findings
from tools.debugger.replay import build_replay_plan
from tools.debugger.repro_recipes import build_repro_recipe_report
from tools.debugger.reporting import build_static_report
from tools.debugger.runtime_watch import build_watch_event_cause, build_watch_report
from tools.debugger.script_resume_gate import build_script_resume_gate_report
from tools.debugger.setup_plan import build_setup_plan
from tools.debugger.state_space import build_state_space_report
from tools.debugger.slicing import build_slice_report
from tools.debugger.taint import build_taint_report
from tools.debugger.testgen import suggest_tests
from tools.debugger.trace_index import build_trace_index_report
from tools.debugger.visualization import build_visualization_report
from tools.debugger.wram_bank_hazards import build_wram_bank_hazard_report
from tools.debugger.wram_ownership import build_wram_ownership_report
from tools.debugger.workflow import build_gate_plan, command_is_runnable


class UnifiedDebuggerCatalogTests(unittest.TestCase):
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

    def test_next_step_routes_boss_ai_symptoms_to_one_proof_path(self) -> None:
        report = build_next_step(symptom="boss selected wrong switch")
        rec = report["recommendation"]

        self.assertEqual(report["kind"], "unified_debugger_next_step")
        self.assertEqual(rec["symptom_class"], "wrong_switch")
        self.assertEqual(rec["matched_lane"], "boss_ai")
        self.assertIn("rom-switch-materialize", rec["first_command"])
        self.assertTrue(rec["required_inputs"])
        self.assertTrue(rec["proof_limit"])
        self.assertIn("tools/boss_ai_debugger/rom_switch_materialize.py", rec["source_refs"])
        self.assertIn("engine/battle/ai/boss_policy_switch.asm", rec["source_refs"])
        self.assertIn("rom-switch-materialize", rec["evidence_standard"][0])
        self.assertIn("expected switch result", rec["disproof_standard"][0])
        self.assertIn("rom-switch-materialize", rec["regression_gate"])
        self.assertIn("escalation_command", rec)

    def test_next_step_routes_natural_wrong_switch_phrase(self) -> None:
        report = build_next_step(symptom="why did the boss switch when expected to stay in")
        rec = report["recommendation"]

        self.assertEqual(rec["symptom_class"], "wrong_switch")
        self.assertIn("rom-switch-materialize", rec["first_command"])

    def test_proof_card_executes_safe_fast_unified_command(self) -> None:
        report = build_proof_card(
            symptom="How much does grass regrowth heal at 300 hp?",
            execute=True,
            timeout_seconds=30,
        )

        self.assertEqual(report["kind"], "unified_debugger_proof_card")
        self.assertEqual(report["proof_depth"], "executed")
        self.assertTrue(report["passed"])
        self.assertIn("grass-regrowth", report["chosen_command"])

    def test_proof_campaign_classifies_routes_and_executes_case(self) -> None:
        report = build_proof_campaign(
            cases=(
                {
                    "id": "grass",
                    "command": "python -m tools.debugger grass-regrowth --max-total-hp 300",
                    "expected_exit_codes": [0],
                },
            ),
            include_all_routes=True,
            execute=True,
            timeout_seconds=30,
        )

        self.assertEqual(report["kind"], "unified_debugger_proof_campaign")
        self.assertTrue(report["valid"])
        self.assertGreaterEqual(report["route_row_count"], 35)
        self.assertGreaterEqual(report["blocked_reason_counts"]["placeholder_input"], 1)
        self.assertEqual(report["executed_unique_command_count"], 1)

    def test_proof_campaign_rejects_execute_all_routes_without_suite(self) -> None:
        report = build_proof_campaign(
            cases=(),
            include_all_routes=True,
            execute=True,
            timeout_seconds=30,
        )

        self.assertFalse(report["valid"])
        self.assertIn("--execute with --all-routes requires --suite", report["validation_errors"][0])
        self.assertEqual(report["executed_unique_command_count"], 0)

    def test_proof_campaign_rejects_command_limit_truncation(self) -> None:
        report = build_proof_campaign(
            cases=(
                {
                    "id": "grass",
                    "command": "python -m tools.debugger grass-regrowth --max-total-hp 300",
                },
                {
                    "id": "mirror",
                    "command": "python -m tools.debugger content-mirror --source-file maps\\NewBarkTown.asm",
                },
            ),
            execute=True,
            max_commands=1,
            timeout_seconds=30,
        )

        self.assertFalse(report["valid"])
        self.assertEqual(report["status_counts"]["not_run_limit"], 1)

    def test_proof_campaign_enforces_expected_disposition(self) -> None:
        report = build_proof_campaign(
            cases=(
                {
                    "id": "wrong_expectation",
                    "command": "python -m tools.debugger grass-regrowth --max-total-hp 300",
                    "expected_exit_codes": [0],
                    "expected_disposition": "discrepancy_found",
                },
            ),
            execute=True,
            timeout_seconds=30,
        )

        self.assertFalse(report["valid"])
        self.assertEqual(report["status_counts"]["passed"], 1)
        self.assertEqual(len(report["expectation_errors"]), 1)

    def test_proof_command_records_block_reasons(self) -> None:
        placeholder = command_record("python -m tools.debugger triage --symptom <symptom>")
        shell = command_record("python tools\\audit\\check_release_smoke.py & git status")

        self.assertFalse(placeholder["safe"])
        self.assertEqual(placeholder["blocked_reason"], "placeholder_input")
        self.assertFalse(shell["safe"])
        self.assertEqual(shell["blocked_reason"], "shell_metacharacter")

    def test_next_step_routes_reset_crashes_before_counter_substrings(self) -> None:
        report = build_next_step(
            symptom="first wild encounter reset to intro then black screen",
        )
        rec = report["recommendation"]

        self.assertEqual(rec["symptom_class"], "crash_reset")
        self.assertEqual(rec["matched_lane"], "runtime_crash")
        self.assertIn("--reset-sentinel", rec["first_command"])
        self.assertIn("first-wild-route29", rec["repro_recipes"])
        self.assertNotEqual(rec["symptom_class"], "revealed_effect_response")

    def test_next_step_routes_frozen_music_after_trainer_to_state_inspect(self) -> None:
        report = build_next_step(
            symptom="music is playing but frozen after trainer battle and Flaaffy evolution",
        )
        rec = report["recommendation"]

        self.assertEqual(rec["symptom_class"], "script_vm_impossible_state")
        self.assertEqual(rec["matched_lane"], "runtime_state")
        self.assertIn("state-inspect", rec["first_command"])
        self.assertIn("trainer-battle-evolution-resume", rec["repro_recipes"])
        self.assertIn("repro-recipe", rec["escalation_command"])

    def test_triage_routes_frozen_music_after_trainer_to_runtime_state(self) -> None:
        report = triage_request(
            symptom="music is playing but frozen after trainer battle and Flaaffy evolution",
        )

        self.assertEqual(report["matches"][0]["id"], "script_vm_impossible_state")
        commands = "\n".join(report["commands"])
        self.assertIn("state-inspect", commands)
        self.assertIn("wScriptBank", commands)
        self.assertIn("wScriptPos", commands)

    def test_next_step_routes_evolution_graphics_reset_to_vram_contract(self) -> None:
        report = build_next_step(
            symptom="Cyndaquil evolved to Quilava then reset and colors inverted",
        )
        rec = report["recommendation"]

        self.assertEqual(rec["symptom_class"], "vram_request_contract")
        self.assertEqual(rec["matched_lane"], "graphics_vram")
        self.assertIn("check_vram_request_contract.py", rec["first_command"])
        self.assertIn("--reset-sentinel", rec["escalation_command"])

    def test_next_step_table_covers_rom_expansion_boss_ai_classes(self) -> None:
        classes = {row["symptom_class"] for row in NEXT_STEP_ROWS}

        self.assertGreaterEqual(
            classes,
            {
                "crash_reset",
                "script_vm_impossible_state",
                "vram_request_contract",
                "wrong_switch",
                "wrong_move_score",
                "haki_taunt_read",
                "ko_band_pressure",
                "revealed_effect_response",
                "observation_tendency_behavior",
                "role_package",
                "coach_template",
            },
        )
        for row in NEXT_STEP_ROWS:
            self.assertTrue(row["matched_lane"])
            self.assertTrue(row["first_command"])
            self.assertTrue(row["required_inputs"])
            self.assertTrue(row["proof_limit"])
            self.assertTrue(row["source_refs"])
            self.assertTrue(row["evidence_standard"])
            self.assertTrue(row["disproof_standard"])
            self.assertTrue(row["regression_gate"])
            self.assertIn("escalation_command", row)

    def test_next_step_routes_each_rom_expansion_boss_ai_class(self) -> None:
        cases = {
            "boss selected wrong switch": "wrong_switch",
            "boss picked the wrong move score": "wrong_move_score",
            "Haki taunt read fired oddly": "haki_taunt_read",
            "KO-band pressure bonus looks wrong": "ko_band_pressure",
            "revealed Protect response was wrong": "revealed_effect_response",
            "observation tendency memory changed the fight": "observation_tendency_behavior",
            "role package classifier tagged Dragonite wrong": "role_package",
            "coach template picked wrong move": "coach_template",
        }

        for symptom, expected_class in cases.items():
            with self.subTest(symptom=symptom):
                report = build_next_step(symptom=symptom)
                self.assertEqual(
                    report["recommendation"]["symptom_class"],
                    expected_class,
                )

    def test_next_step_routes_recent_live_bug_classes_to_exact_tools(self) -> None:
        cases = {
            "Falkner used Hypnosis even though Sleep Clause was active": (
                "boss_ai_sleep_clause_move_legality",
                "damage-ai-report",
            ),
            "Falkner used a Normal-type move on Gastly and it doesn't affect": (
                "boss_ai_type_immunity_move_choice",
                "damage-ai-report",
            ),
            "Rival Magneton Hidden Power was treated as stale Normal immunity": (
                "boss_ai_hidden_power_type",
                "move-score-probe",
            ),
            "Silver early boss spammed Leer and never attacked": (
                "early_boss_debuff_spam",
                "damage-ai-report",
            ),
        }

        for symptom, (expected_class, command_fragment) in cases.items():
            with self.subTest(symptom=symptom):
                report = build_next_step(symptom=symptom)
                rec = report["recommendation"]
                self.assertEqual(rec["symptom_class"], expected_class)
                self.assertEqual(rec["matched_lane"], "boss_ai")
                self.assertIn(command_fragment, rec["first_command"])

    def test_next_step_routes_known_red_audits_and_semantic_questions(self) -> None:
        cases = {
            "walking poison took a poisoned mon from 1 HP to 0 HP": (
                "overworld_poison_cure",
                "check_overworld_poison_cure.py",
            ),
            "regular trainer Assault Vest chose an illegal status move": (
                "base_ai_move_legality",
                "check_base_ai_mechanics_correctness.py",
            ),
            "Gastly level 14 learnset should include Confusion not Spite": (
                "learnset_semantics",
                "learnset-inspect",
            ),
            "level 3 Hoppip grass heal cutoff felt wrong": (
                "grass_regrowth_balance",
                "grass-regrowth",
            ),
            "Mirror Move copied Sketch and corrupted memory": (
                "move_search_unbounded",
                "bug_hunt_triage.py",
            ),
        }

        for symptom, (expected_class, command_fragment) in cases.items():
            with self.subTest(symptom=symptom):
                report = build_next_step(symptom=symptom)
                rec = report["recommendation"]
                self.assertEqual(rec["symptom_class"], expected_class)
                self.assertIn(command_fragment, rec["first_command"])

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
        self.assertIn("implicit replacement without auto_replace_or", rec["disproof_standard"][0])

    def test_species_id_map_ignores_unown_form_constants(self) -> None:
        by_id = damage_state.species_name_by_id()

        self.assertEqual(by_id[1], "BULBASAUR")
        self.assertEqual(by_id[16], "PIDGEY")
        self.assertEqual(by_id[201], "UNOWN")

    def test_learnset_and_grass_semantic_reports_answer_live_questions(self) -> None:
        learnset = build_learnset_inspection_report(species="GASTLY", level=14)
        regrowth = build_grass_regrowth_report(max_total_hp=300)

        self.assertTrue(learnset["valid"])
        self.assertEqual(learnset["species"], "GASTLY")
        self.assertIn("LICK", learnset["current_moves"])
        self.assertTrue(learnset["current_moves"])
        self.assertTrue(regrowth["valid"])
        self.assertEqual(regrowth["cutoffs"]["full_grass"][0], {"min_hp": 1, "max_hp": 47, "heals": 1})
        self.assertEqual(regrowth["cutoffs"]["half_grass"][0], {"min_hp": 1, "max_hp": 95, "heals": 1})

    def test_cli_next_json_schema_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "next.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "next",
                        "--symptom",
                        "coach template picked wrong move",
                        "--json-out",
                        str(path),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_next_step")
            self.assertEqual(data["recommendation"]["symptom_class"], "coach_template")
            for key in (
                "matched_lane",
                "first_command",
                "required_inputs",
                "proof_limit",
                "source_refs",
                "evidence_standard",
                "disproof_standard",
                "regression_gate",
                "escalation_command",
            ):
                self.assertIn(key, data["recommendation"])

    def test_repro_recipe_exposes_first_wild_route29_capture_path(self) -> None:
        report = build_repro_recipe_report(ids=("first-wild-route29",))
        recipe = report["recipes"][0]
        commands = "\n".join(recipe["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(recipe["id"], "first-wild-route29")
        self.assertIn("--reset-sentinel", commands)
        self.assertIn("wram-bank-hazards", commands)
        self.assertIn("route29-before-grass.state", commands)

    def test_repro_recipe_exposes_trainer_evolution_resume_path(self) -> None:
        report = build_repro_recipe_report(ids=("trainer-battle-evolution-resume",))
        recipe = report["recipes"][0]
        commands = "\n".join(recipe["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(recipe["bug_class"], "post_battle_script_resume")
        self.assertIn("state-inspect", commands)
        self.assertIn("script-resume-gate", commands)
        self.assertIn("wSeenTrainerBank", commands)
        self.assertIn("EvolveAfterBattle", commands)

    def test_cli_investigate_symptom_only_points_to_next(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_out = Path(tmp) / "investigate.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "investigate",
                        "--symptom",
                        "boss selected wrong switch",
                        "--out-dir",
                        str(Path(tmp) / "investigate"),
                        "--max-targets",
                        "1",
                        "--max-events",
                        "1",
                        "--max-cases",
                        "1",
                        "--json-out",
                        str(json_out),
                    ]
                )

            self.assertEqual(code, 0)
            text = stdout.getvalue()
            self.assertIn("planning packet, not a repro", text)
            self.assertIn("python -m tools.debugger next --symptom", text)
            self.assertIn("Next proof path", text)
            self.assertIn("rom-switch-materialize", text)
            data = json.loads(json_out.read_text(encoding="utf-8"))
            next_step = data["symptom_only_next_step"]
            rec = next_step["recommendation"]
            self.assertEqual(next_step["kind"], "unified_debugger_next_step")
            self.assertEqual(rec["symptom_class"], "wrong_switch")
            self.assertIn("rom-switch-materialize", rec["first_command"])
            self.assertIn("tools/boss_ai_debugger/rom_switch_materialize.py", rec["source_refs"])
            self.assertIn("rom-switch-materialize", rec["evidence_standard"][0])
            self.assertIn("expected switch result", rec["disproof_standard"][0])
            self.assertIn("rom-switch-materialize", rec["regression_gate"])

    def test_cli_audit_strict_passes_when_whole_rom_goal_is_done(self) -> None:
        with redirect_stdout(io.StringIO()):
            code = debugger_main(["audit", "--strict"])

        self.assertEqual(code, 0)

    def test_cli_writes_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "triage.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "triage",
                        "--symptom",
                        "damage spike",
                        "--json-out",
                        str(path),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_triage")
            self.assertTrue(data["commands"])

    def test_ingest_manifest_accepts_core_artifact_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = root / "test.gbc"
            rom_bytes = bytearray(0x8000)
            rom_bytes[0x134:0x13C] = b"DBGTEST\0"
            rom.write_bytes(rom_bytes)
            symbols = root / "test.sym"
            symbols.write_text(
                "; generated\n00:0000 NULL\n01:4000 ExampleLabel\n",
                encoding="utf-8",
            )
            trace = root / "trace.txt"
            trace.write_text(
                "trace_rom_sha256=ABC\nchosen=TACKLE\nmove_scores=1,2,3,4\n",
                encoding="utf-8",
            )
            save_state = root / "state.sgm"
            save_state.write_bytes(b"opaque-state")
            scenario = root / "scenarios.jsonl"
            scenario.write_text(
                json.dumps(
                    {
                        "id": "scenario_1",
                        "family": "test_family",
                        "moves": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            changed = root / "engine" / "battle" / "effect_commands.asm"
            changed.parent.mkdir(parents=True)
            changed.write_text("BattleCommand_Test:\n\tret\n", encoding="utf-8")

            report = ingest_artifacts(
                roms=("test.gbc",),
                symbols=("test.sym",),
                traces=("trace.txt",),
                save_states=("state.sgm",),
                scenarios=("scenarios.jsonl",),
                changed_files=("engine/battle/effect_commands.asm",),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["artifact_count"], 6)
        by_kind = {artifact["kind"]: artifact for artifact in report["artifacts"]}
        self.assertEqual(by_kind["rom"]["metadata"]["title"], "DBGTEST")
        self.assertEqual(by_kind["symbols"]["metadata"]["label_count"], 2)
        self.assertEqual(by_kind["scenario"]["metadata"]["record_count"], 1)
        self.assertIn(
            "damage_chain",
            by_kind["source_change"]["metadata"]["triage_match_ids"],
        )

    def test_ingest_manifest_reports_invalid_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario = root / "bad.jsonl"
            scenario.write_text("{bad json}\n", encoding="utf-8")

            report = ingest_artifacts(scenarios=("bad.jsonl",), root=root)

        self.assertFalse(report["valid"])
        self.assertEqual(report["error_count"], 1)

    def test_ingest_manifest_accepts_json_trace_without_key_value_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "events": [
                            {
                                "full_symbol": "BattleCommand_Test",
                                "source_file": "engine/battle/effect_commands.asm",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = ingest_artifacts(traces=("trace.json",), root=root)

        artifact = report["artifacts"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(artifact["metadata"]["format"], "json")
        self.assertIn("BattleCommand_Test", artifact["metadata"]["symbol_sample"])
        self.assertFalse(artifact["warnings"])

    def test_cli_ingest_writes_json_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario = root / "scenario.json"
            scenario.write_text(
                json.dumps({"id": "one", "family": "cli"}),
                encoding="utf-8",
            )
            out = root / "manifest.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "ingest",
                        "--scenario",
                        str(scenario),
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_ingest_manifest")
            self.assertTrue(data["valid"])

    def test_gate_plan_orders_runnable_debugger_commands(self) -> None:
        report = build_gate_plan(
            changed_files=("engine/battle/late_gen_held_items.asm",),
        )
        commands = [step["command"] for step in report["steps"]]

        self.assertFalse(report["executed"])
        self.assertIn("python -m tools.damage_debugger.clobber_smoke", commands)
        self.assertIn("python tools\\audit\\check_cross_bank_call.py", commands)
        self.assertEqual(report["steps"][0]["priority"], 10)

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

    def test_gate_marks_placeholder_commands_not_runnable(self) -> None:
        self.assertFalse(command_is_runnable("python -m tool <scenario>"))
        self.assertTrue(command_is_runnable("python tools\\audit\\check_release_smoke.py"))

    def test_cli_gate_plan_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "gate.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "gate",
                        "--symptom",
                        "boss ai selector issue",
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_gate_plan")
            self.assertFalse(data["executed"])
            self.assertTrue(data["steps"])

    def test_localize_scores_symbols_and_builds_phase_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text(
                "01:D141 wCurDamage\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld [wCurDamage], a\n\tret\n",
                encoding="utf-8",
            )

            report = build_localization_plan(
                symbols=("wCurDamage",),
                symptom="damage spike",
                symbols_path="test.sym",
                root=root,
            )

        self.assertTrue(report["valid"])
        candidate_ids = [candidate["id"] for candidate in report["candidates"]]
        phase_names = [phase["phase"] for phase in report["phase_steps"]]
        commands = "\n".join(report["commands"])

        self.assertIn("wCurDamage", candidate_ids)
        self.assertIn("observe", phase_names)
        self.assertIn("slice", phase_names)
        self.assertIn("tools.debugger watch", commands)
        self.assertIn("tools.damage_debugger", commands)

    def test_localize_routes_air_balloon_immunity_to_type_matchup_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine" / "battle").mkdir(parents=True)
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "data" / "types").mkdir(parents=True)
            (root / "ram").mkdir()
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "0d:4936 BattleCheckTypeMatchup",
                        "0d:4941 CheckTypeMatchup",
                        "0d:4900 TypeMatchups",
                        "01:d151 wTypeMatchup",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "effect_commands.asm").write_text(
                "\n".join(
                    [
                        "BattleCheckTypeMatchup:",
                        "\tld [wTypeMatchup], a",
                        "\tld hl, TypeMatchups",
                        "\tret",
                        "CheckTypeMatchup:",
                        "\tcall BattleCheckTypeMatchup",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "late_gen_held_items.asm").write_text(
                ".MaybePopAirBalloon:\n\tld hl, BattleText_AirBalloonPopped\n\tret\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "boss_policy_move.asm").write_text(
                "BossAI_ApplyMoveModel:\n\tld a, [wTypeMatchup]\n\tret\n",
                encoding="utf-8",
            )
            (root / "data" / "types" / "type_matchups.asm").write_text(
                "TypeMatchups:\n\tdb GROUND, FLYING, 0\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wTypeMatchup:: ds 1\n",
                encoding="utf-8",
            )

            report = build_localization_plan(
                symptom="Air Balloon Ground immunity",
                symbols_path="test.sym",
                root=root,
            )

        candidate_ids = [candidate["id"] for candidate in report["candidates"]]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("damage_chain", report["triage_match_ids"])
        self.assertNotIn("boss_ai", report["triage_match_ids"])
        self.assertIn("BattleCheckTypeMatchup", candidate_ids)
        self.assertIn("wTypeMatchup", candidate_ids)
        self.assertIn("engine/battle/late_gen_held_items.asm", candidate_ids)
        self.assertNotIn("BossAI_SelectMove", candidate_ids)
        self.assertNotIn("tools.boss_ai_debugger", commands)
        self.assertIn("tools.debugger watch --watch-symbol wTypeMatchup", commands)
        self.assertIn("tools.debugger slice --symbol BattleCheckTypeMatchup", commands)
        self.assertIn("tools.debugger slice --source-file engine/battle/late_gen_held_items.asm", commands)

    def test_localize_uses_embedded_next_step_sources_and_proof_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            next_step = build_next_step(symptom="boss selected wrong switch")
            for source_ref in next_step["recommendation"]["source_refs"]:
                source_path = root / source_ref
                source_path.parent.mkdir(parents=True, exist_ok=True)
                if source_path.exists():
                    continue
                source_path.write_text("# source ref placeholder\n", encoding="utf-8")

            investigation_report = root / "investigate.json"
            investigation_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_investigation_run",
                        "valid": True,
                        "passed": True,
                        "symptom": "boss selected wrong switch",
                        "steps": [],
                        "top_findings": [],
                        "top_impact": [],
                        "commands": [],
                        "errors": [],
                        "warnings": [],
                        "symptom_only_next_step": next_step,
                    }
                ),
                encoding="utf-8",
            )

            report = build_localization_plan(reports=("investigate.json",), root=root)

        candidate_ids = {candidate["id"] for candidate in report["candidates"]}
        signal_types = {item["type"] for item in report["signals"]}
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("tools/boss_ai_debugger/rom_switch_materialize.py", candidate_ids)
        self.assertIn("engine/battle/ai/boss_policy_switch.asm", candidate_ids)
        self.assertIn("engine/battle/ai/switch.asm", candidate_ids)
        self.assertIn("next_step_source_ref", signal_types)
        self.assertIn("next_step_evidence_standard", signal_types)
        self.assertIn("next_step_disproof_standard", signal_types)
        self.assertIn("next_step_regression_gate", signal_types)
        self.assertIn("rom-switch-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch", commands)

    def test_explain_uses_embedded_next_step_as_causal_proof_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools" / "boss_ai_debugger").mkdir(parents=True)
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "tools" / "boss_ai_debugger" / "rom_switch_materialize.py").write_text(
                "def main():\n    return 0\n",
                encoding="utf-8",
            )
            (root / "tools" / "boss_ai_debugger" / "README.md").write_text(
                "# Boss AI debugger\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "boss_policy_switch.asm").write_text(
                "BossAI_SwitchOrTryItem:\n\tret\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "switch.asm").write_text(
                "AI_SwitchOrTryItem:\n\tret\n",
                encoding="utf-8",
            )
            (root / "pokegold.sym").write_text(
                "01:4000 BossAI_SwitchOrTryItem\n01:4010 AI_SwitchOrTryItem\n",
                encoding="utf-8",
            )
            next_step = build_next_step(symptom="boss selected wrong switch")
            for source_ref in next_step["recommendation"]["source_refs"]:
                source_path = root / source_ref
                source_path.parent.mkdir(parents=True, exist_ok=True)
                if source_path.exists():
                    continue
                source_path.write_text("# source ref placeholder\n", encoding="utf-8")

            investigation_report = root / "investigate.json"
            investigation_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_investigation_run",
                        "valid": True,
                        "passed": True,
                        "symptom": "boss selected wrong switch",
                        "steps": [],
                        "top_findings": [],
                        "top_impact": [],
                        "commands": [],
                        "errors": [],
                        "warnings": [],
                        "symptom_only_next_step": next_step,
                    }
                ),
                encoding="utf-8",
            )

            report = build_explanation_report(reports=("investigate.json",), root=root)

        path = report["paths"][0]
        roles = {
            node["role"]
            for causal_path in report["paths"]
            for node in causal_path.get("nodes", [])
        }
        labels = {
            node["label"]
            for causal_path in report["paths"]
            for node in causal_path.get("nodes", [])
        }
        evidence = "\n".join(path["evidence"])
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(path["id"], "next_step_1")
        self.assertIn("Next proof path: Boss selected the wrong switch", path["title"])
        self.assertIn("tools/boss_ai_debugger/rom_switch_materialize.py", path["related_files"])
        self.assertIn("first_command", roles)
        self.assertIn("source_ref", roles)
        self.assertIn("evidence_standard", roles)
        self.assertIn("disproof_standard", roles)
        self.assertIn("regression_gate", roles)
        self.assertIn("tools/boss_ai_debugger/rom_switch_materialize.py", labels)
        self.assertIn("evidence standard: A scenario JSONL matching the disputed switch case passes rom-switch-materialize", evidence)
        self.assertIn("disproof standard: If a matching scenario JSONL passes rom-switch-materialize with the expected switch result", evidence)
        self.assertIn("rom-switch-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch", commands)

    def test_localize_uses_watch_report_events_as_strong_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "events": [
                            {
                                "watch": "wEnemyAIMoveScores",
                                "pc_label": "BossAI_SelectMove",
                                "pc_bank_address": "03:4123",
                                "old_hex": "00",
                                "new_hex": "10",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_localization_plan(
                reports=("watch.json",),
                symbols_path="missing.sym",
                root=root,
            )

        self.assertFalse(report["valid"])
        self.assertEqual(report["candidates"][0]["id"], "wEnemyAIMoveScores")
        self.assertIn("missing symbol file", report["errors"][0])

    def test_localize_uses_trace_reverse_attribution_as_strong_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine" / "battle").mkdir(parents=True)
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:D142 wBattleMonAttack\n01:4000 BattleCommand_DamageCalc\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\nwBattleMonAttack:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "effect_commands.asm").write_text(
                "BattleCommand_DamageCalc:\n\tld a, [wBattleMonAttack]\n\tld [wCurDamage], a\n\tret\n",
                encoding="utf-8",
            )
            trace_index = root / "trace_index.json"
            trace_index.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_trace_index",
                        "valid": True,
                        "events": [
                            {
                                "event_type": "memory_write",
                                "state_symbol": "wCurDamage",
                                "source_symbol": "BattleCommand_DamageCalc",
                                "source_file": "engine/battle/effect_commands.asm",
                                "before": "0000",
                                "after": "002A",
                            }
                        ],
                        "reverse_attributions": [
                            {
                                "state": "wCurDamage",
                                "title": "wCurDamage memory_write reverse attribution",
                                "source_symbol": "BattleCommand_DamageCalc",
                                "contributors": [
                                    {
                                        "relation": "prior_read",
                                        "state": "wBattleMonAttack",
                                    }
                                ],
                                "related_symbols": ["wCurDamage", "wBattleMonAttack"],
                                "related_files": ["engine/battle/effect_commands.asm"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_localization_plan(
                reports=("trace_index.json",),
                symbols_path="test.sym",
                root=root,
            )

        candidate_ids = {candidate["id"] for candidate in report["candidates"]}
        commands = "\n".join(report["commands"])

        by_id = {candidate["id"]: candidate for candidate in report["candidates"]}

        self.assertTrue(report["valid"])
        self.assertGreater(by_id["wCurDamage"]["score"], by_id["wBattleMonAttack"]["score"])
        self.assertIn("wBattleMonAttack", candidate_ids)
        self.assertIn("tools.debugger slice --symbol wCurDamage", commands)

    def test_localize_uses_failed_expectation_as_strong_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "maps").mkdir()
            (root / "test.sym").write_text("01:D100 wMapGroup\n", encoding="utf-8")
            (root / "ram" / "wram.asm").write_text("wMapGroup:: ds 1\n", encoding="utf-8")
            (root / "maps" / "NewBarkTown.asm").write_text(
                "NewBarkTown_MapEvents:\n\tdef_warp_events\n",
                encoding="utf-8",
            )
            expectation_report = root / "expectation.json"
            expectation_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_expectation_report",
                        "valid": True,
                        "passed": False,
                        "expectations": [
                            {
                                "id": "map_group_observed",
                                "status": "failed",
                                "description": "map group should be observed",
                                "expectation": {
                                    "symbol": "wMapGroup",
                                    "source_file": "maps/NewBarkTown.asm",
                                    "event_type": "memory_write",
                                },
                            }
                        ],
                        "evidence_summary": {
                            "symbols": ["wMapGroup"],
                            "source_files": ["maps/NewBarkTown.asm"],
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_localization_plan(
                reports=("expectation.json",),
                symbols_path="test.sym",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["candidates"][0]["id"], "wMapGroup")
        self.assertIn("maps/NewBarkTown.asm", {candidate["id"] for candidate in report["candidates"]})

    def test_localize_uses_taint_report_contributors_as_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:D142 wBattleMonAttack\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\nwBattleMonAttack:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld a, [wBattleMonAttack]\n\tld [wCurDamage], a\n",
                encoding="utf-8",
            )
            taint = build_taint_report(
                symbols_path="test.sym",
                symbols=("wCurDamage",),
                source_files=("engine/battle.asm",),
                root=root,
            )
            (root / "taint.json").write_text(json.dumps(taint), encoding="utf-8")

            report = build_localization_plan(
                reports=("taint.json",),
                symbols_path="test.sym",
                root=root,
            )

        candidate_ids = {candidate["id"] for candidate in report["candidates"]}

        self.assertTrue(report["valid"])
        self.assertIn("wCurDamage", candidate_ids)
        self.assertIn("wBattleMonAttack", candidate_ids)
        self.assertIn("engine/battle.asm", candidate_ids)

    def test_cli_localize_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            symbols = root / "test.sym"
            symbols.write_text("01:D141 wCurDamage\n", encoding="utf-8")
            (root / "ram" / "wram.asm").write_text("wCurDamage:: ds 2\n", encoding="utf-8")
            out = root / "localize.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "localize",
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "wCurDamage",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_localization_plan")
        self.assertTrue(data["candidates"])

    def test_coverage_marks_direct_and_indirect_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text(
                "01:D141 wCurDamage\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld [wCurDamage], a\n\tret\n",
                encoding="utf-8",
            )
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "covered_rule_ids": ["damage.test"],
                        "events": [
                            {
                                "source": {
                                    "full_symbol": "BattleCommand_Test",
                                    "source_file": "engine/battle.asm",
                                    "rule_id": "damage.test",
                                }
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_coverage_report(
                traces=("trace.json",),
                symbols=("BattleCommand_Test", "wCurDamage"),
                rules=("damage.test",),
                changed_files=("engine/battle.asm",),
                symbols_path="test.sym",
                root=root,
            )

        by_id = {target["id"]: target for target in report["targets"]}
        self.assertTrue(report["valid"])
        self.assertEqual(by_id["BattleCommand_Test"]["status"], "covered")
        self.assertEqual(by_id["engine/battle.asm"]["status"], "covered")
        self.assertEqual(by_id["wCurDamage"]["status"], "indirect")
        self.assertEqual(by_id["damage.test"]["status"], "covered")
        self.assertGreaterEqual(report["covered_rule_count"], 1)

    def test_coverage_uses_content_rom_mirror_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_report = root / "content.json"
            content_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_mirror",
                        "rom_mirrors": [
                            {
                                "type": "incbin_table_rom_bytes",
                                "status": "passed",
                                "title": "Footprints ROM bytes match",
                                "source_file": "gfx/footprints.asm",
                                "related_files": ["gfx/footprints.asm", "gfx/footprints/bulbasaur.1bpp"],
                                "related_symbols": ["Footprints"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_coverage_report(reports=("content.json",), root=root)

        by_id = {target["id"]: target for target in report["targets"]}
        self.assertTrue(report["valid"])
        self.assertEqual(by_id["Footprints"]["status"], "covered")
        self.assertEqual(by_id["gfx/footprints.asm"]["status"], "covered")
        self.assertIn("Footprints", by_id["gfx/footprints.asm"]["related_symbols"])

    def test_cli_coverage_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text("01:4000 BattleCommand_Test\n", encoding="utf-8")
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tret\n",
                encoding="utf-8",
            )
            trace = root / "trace.json"
            trace.write_text(
                json.dumps({"full_symbol": "BattleCommand_Test"}),
                encoding="utf-8",
            )
            out = root / "coverage.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "coverage",
                        "--trace",
                        str(trace),
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "BattleCommand_Test",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_coverage_report")
        self.assertEqual(data["covered_target_count"], 1)

    def test_minimize_extracts_boss_ai_scenario_subset_and_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenarios = root / "scenarios.jsonl"
            scenarios.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "id": "case_keep",
                                "family": "unit",
                                "moves": [{"id": "a"}, {"id": "b"}],
                            }
                        ),
                        json.dumps(
                            {
                                "id": "case_other",
                                "family": "unit",
                                "moves": [{"id": "c"}],
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            out = root / "subset.jsonl"

            report = build_minimization_plan(
                scenarios=("scenarios.jsonl",),
                scenario_ids=("case_keep",),
                symbols=("BossAI_SelectMove",),
                out_scenarios="subset.jsonl",
                root=root,
            )

            subset_lines = out.read_text(encoding="utf-8").splitlines()

        self.assertTrue(report["valid"])
        self.assertEqual(report["selected_scenario_ids"], ["case_keep"])
        self.assertEqual(report["subset_output"]["record_count"], 1)
        self.assertEqual(len(subset_lines), 1)
        commands = "\n".join(report["commands"])
        self.assertIn("tools.boss_ai_debugger minimize", commands)
        self.assertIn("counterfactual", commands)

    def test_minimize_routes_damage_bug_to_ddmin_and_replay(self) -> None:
        report = build_minimization_plan(
            symbols=("wCurDamage",),
            bug_ids=("hp_d_clobber",),
        )
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("tools.damage_debugger.minimize --bug hp_d_clobber", commands)
        self.assertIn("tools.damage_debugger.replay", commands)

    def test_minimize_reduces_generic_trace_against_expectations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "events": [
                            {
                                "access": "read",
                                "symbol": "wBattleMonAttack",
                                "address": "D142",
                                "value": "2A",
                                "pc_label": "BattleCommand_DamageCalc",
                            },
                            {
                                "access": "write",
                                "symbol": "wCurDamage",
                                "address": "D141",
                                "old_value": "0000",
                                "new_value": "002A",
                                "pc_label": "BattleCommand_DamageCalc",
                            },
                            {
                                "access": "read",
                                "symbol": "wUnrelated",
                                "address": "D200",
                                "value": "FF",
                                "pc_label": "OtherRoutine",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out_trace = root / "minimized_trace.json"

            report = build_minimization_plan(
                traces=(str(trace),),
                expectations=(
                    "event=memory_read,symbol=wBattleMonAttack",
                    "event=memory_write,symbol=wCurDamage",
                ),
                out_trace=str(out_trace),
                root=root,
            )
            minimized = json.loads(out_trace.read_text(encoding="utf-8"))

        evidence = report["evidence_minimization"]

        self.assertTrue(report["valid"])
        self.assertTrue(evidence["attempted"])
        self.assertTrue(evidence["preserved"])
        self.assertEqual(evidence["original_count"], 3)
        self.assertEqual(evidence["minimized_count"], 2)
        self.assertEqual(len(minimized["events"]), 2)
        self.assertEqual(
            {event["symbol"] for event in minimized["events"]},
            {"wBattleMonAttack", "wCurDamage"},
        )

    def test_minimize_reduces_watch_report_and_dynamic_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "events": [
                            {
                                "watch": "wNoise",
                                "old_hex": "00",
                                "new_hex": "01",
                                "pc_label": "NoiseRoutine",
                            },
                            {
                                "watch": "wCurDamage",
                                "old_hex": "0000",
                                "new_hex": "3400",
                                "pc_label": "BattleCommand_Final",
                                "dynamic_context": {
                                    "context_frame_count": 3,
                                    "prelude": [
                                        {
                                            "kind": "runtime_context_frame",
                                            "event_type": "control_flow",
                                            "frame": 0,
                                            "pc_label": "NoiseRoutine",
                                        },
                                        {
                                            "kind": "runtime_context_frame",
                                            "event_type": "control_flow",
                                            "frame": 1,
                                            "pc_label": "BattleCommand_Seed",
                                        },
                                        {
                                            "kind": "runtime_context_frame",
                                            "event_type": "control_flow",
                                            "frame": 2,
                                            "pc_label": "BattleCommand_DamageCalc",
                                        },
                                    ],
                                    "after": {
                                        "kind": "runtime_context_frame",
                                        "event_type": "control_flow",
                                        "frame": 3,
                                        "pc_label": "BattleCommand_Final",
                                    },
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out_trace = root / "minimized_watch.json"

            report = build_minimization_plan(
                reports=("watch.json",),
                expectations=(
                    "event=watch_change,symbol=wCurDamage",
                    "event=control_flow,symbol=BattleCommand_DamageCalc",
                ),
                out_trace="minimized_watch.json",
                root=root,
            )
            minimized = json.loads(out_trace.read_text(encoding="utf-8"))

        evidence = report["evidence_minimization"]
        event = minimized["events"][0]
        context = event["dynamic_context"]

        self.assertTrue(report["valid"])
        self.assertTrue(evidence["preserved"])
        self.assertEqual(evidence["source_kind"], "report")
        self.assertEqual(evidence["original_count"], 2)
        self.assertEqual(evidence["minimized_count"], 1)
        self.assertEqual(evidence["context_frame_original_count"], 3)
        self.assertEqual(evidence["context_frame_minimized_count"], 1)
        self.assertEqual(evidence["context_frame_removed_count"], 2)
        self.assertEqual(len(minimized["events"]), 1)
        self.assertEqual(event["watch"], "wCurDamage")
        self.assertEqual(context["context_frame_count"], 1)
        self.assertEqual(context["prelude"][0]["pc_label"], "BattleCommand_DamageCalc")

    def test_minimize_reduces_content_state_patch_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_state = root / "content_state.json"
            content_state.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "executed": False,
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0000",
                                "precondition_kind": "map_position",
                                "source_file": "maps/UnitMap.asm",
                                "status": "ready",
                                "patches": [
                                    {
                                        "symbol": "wMapGroup",
                                        "value": 24,
                                        "value_hex": "18",
                                        "bank_address": "01:DA00",
                                    },
                                    {
                                        "symbol": "wMapNumber",
                                        "value": 3,
                                        "value_hex": "03",
                                        "bank_address": "01:DA01",
                                    },
                                    {
                                        "symbol": "wXCoord",
                                        "value": 6,
                                        "value_hex": "06",
                                        "bank_address": "01:DA03",
                                    },
                                ],
                            }
                        ],
                        "patch_count": 3,
                        "commands": [
                            "python -m tools.debugger content-state --report content_scenarios.json --execute"
                        ],
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )
            out_state_report = root / "minimized_content_state.json"

            report = build_minimization_plan(
                reports=("content_state.json",),
                expectations=("state-patch=wMapGroup,scenario=content_scenario_1_0000,value=0x18",),
                out_state_report="minimized_content_state.json",
                root=root,
            )
            minimized = json.loads(out_state_report.read_text(encoding="utf-8"))

        state_patch = report["state_patch_minimization"]
        commands = "\n".join(report["commands"])
        patches = minimized["materializations"][0]["patches"]

        self.assertTrue(report["valid"])
        self.assertTrue(state_patch["attempted"])
        self.assertTrue(state_patch["preserved"])
        self.assertEqual(state_patch["original_patch_count"], 3)
        self.assertEqual(state_patch["minimized_patch_count"], 1)
        self.assertEqual(state_patch["removed_patch_count"], 2)
        self.assertTrue(state_patch["written"])
        self.assertIn("maps/UnitMap.asm", state_patch["source_files"])
        self.assertEqual([patch["symbol"] for patch in patches], ["wMapGroup"])
        self.assertTrue(minimized["minimized_evidence_view"])
        self.assertIn("tools.debugger expect --report minimized_content_state.json", commands)
        self.assertIn("tools.debugger replay --report minimized_content_state.json --scenario-id content_scenario_1_0000", commands)
        self.assertIn("tools.debugger compare --report minimized_content_state.json", commands)

    def test_minimize_reduces_generic_state_space_patch_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_space = root / "state_space.json"
            state_space.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_state_space",
                        "valid": True,
                        "state_space": {
                            "surface": "script_entry",
                            "patches": [
                                {
                                    "symbol": "wScriptBank",
                                    "value": 2,
                                    "value_hex": "02",
                                    "source_file": "maps/UnitMap.asm",
                                    "scenario_id": "script_entry_1",
                                },
                                {
                                    "symbol": "wScriptPos",
                                    "value": 0x50,
                                    "value_hex": "50",
                                    "source_file": "maps/UnitMap.asm",
                                    "scenario_id": "script_entry_1",
                                },
                                {
                                    "symbol": "wUnusedDebugByte",
                                    "value": 255,
                                    "value_hex": "ff",
                                    "source_file": "engine/debug.asm",
                                },
                            ],
                        },
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )
            out_state_report = root / "minimized_state_space.json"

            report = build_minimization_plan(
                reports=("state_space.json",),
                expectations=("state-patch=wScriptPos,scenario=script_entry_1,value=0x50",),
                out_state_report="minimized_state_space.json",
                root=root,
            )
            minimized = json.loads(out_state_report.read_text(encoding="utf-8"))

        state_patch = report["state_patch_minimization"]
        patches = minimized["state_space"]["patches"]

        self.assertTrue(report["valid"])
        self.assertTrue(state_patch["attempted"])
        self.assertTrue(state_patch["preserved"])
        self.assertEqual(state_patch["content_state_report_count"], 0)
        self.assertEqual(state_patch["state_space_report_count"], 1)
        self.assertEqual(state_patch["original_patch_count"], 3)
        self.assertEqual(state_patch["minimized_patch_count"], 1)
        self.assertEqual(state_patch["removed_patch_count"], 2)
        self.assertIn("script_entry_1", state_patch["scenario_ids"])
        self.assertIn("maps/UnitMap.asm", state_patch["source_files"])
        self.assertEqual([patch["symbol"] for patch in patches], ["wScriptPos"])
        self.assertTrue(minimized["minimized_evidence_view"])
        self.assertIn("minimized generic state-space evidence view", "\n".join(minimized["warnings"]))

    def test_minimize_executes_generic_state_space_candidates(self) -> None:
        class FakeMemory:
            def __init__(self) -> None:
                self.values: dict[Any, int] = {0xFF70: 1}

            def __getitem__(self, key: Any) -> int:
                return self.values.get(key, 0)

            def __setitem__(self, key: Any, value: int) -> None:
                self.values[key] = value & 0xFF

        class FakePyBoy:
            def __init__(self) -> None:
                self.memory = FakeMemory()

            def load_state(self, fh: Any) -> None:
                fh.read()
                self.memory = FakeMemory()

            def save_state(self, fh: Any) -> None:
                fh.write(b"patched-state")

            def stop(self, save: bool = False) -> None:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(b"rom")
            (root / "base.state").write_bytes(b"base-state")
            state_space = root / "state_space.json"
            state_space.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_state_space",
                        "valid": True,
                        "rom": "test.gbc",
                        "base_save_state": "base.state",
                        "state_space": {
                            "surface": "script_entry",
                            "base_save_state": "base.state",
                            "patches": [
                                {
                                    "symbol": "wScriptBank",
                                    "value": 2,
                                    "value_hex": "02",
                                    "bank": 1,
                                    "address": 0xDA10,
                                    "source_file": "maps/UnitMap.asm",
                                    "scenario_id": "script_entry_1",
                                },
                                {
                                    "symbol": "wScriptPos",
                                    "value": 0x50,
                                    "value_hex": "50",
                                    "bank": 1,
                                    "address": 0xDA11,
                                    "source_file": "maps/UnitMap.asm",
                                    "scenario_id": "script_entry_1",
                                },
                                {
                                    "symbol": "wUnusedDebugByte",
                                    "value": 255,
                                    "value_hex": "ff",
                                    "bank": 1,
                                    "address": 0xDA12,
                                    "source_file": "engine/debug.asm",
                                },
                            ],
                        },
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )
            out_state_report = root / "minimized_state_space.json"

            with patch("tools.debugger.state_space.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                report = build_minimization_plan(
                    reports=("state_space.json",),
                    expectations=(
                        "state-patch=wScriptPos,scenario=script_entry_1,value=0x50,applied=true,verified=true",
                    ),
                    out_state_report="minimized_state_space.json",
                    execute_state_patches=True,
                    root=root,
                )
            minimized = json.loads(out_state_report.read_text(encoding="utf-8"))
            candidate_state_written = (root / minimized["execution"]["out_state"]).exists()

        state_patch = report["state_patch_minimization"]
        patches = minimized["state_space"]["patches"]

        self.assertTrue(report["valid"])
        self.assertTrue(state_patch["preserved"])
        self.assertTrue(state_patch["execute_state_patches"])
        self.assertGreater(state_patch["execution_attempt_count"], 0)
        self.assertEqual(state_patch["executed_candidate_count"], state_patch["execution_attempt_count"])
        self.assertEqual(state_patch["minimized_patch_count"], 1)
        self.assertEqual([patch["symbol"] for patch in patches], ["wScriptPos"])
        self.assertTrue(patches[0]["applied"])
        self.assertTrue(patches[0]["verified"])
        self.assertTrue(minimized["minimized_execution_view"])
        self.assertTrue(candidate_state_written)

    def test_minimize_extracts_content_report_scenarios_with_preconditions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario_report = root / "content_scenarios.json"
            scenario_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "map_warp",
                                "source_file": "maps/UnitMap.asm",
                                "state_preconditions": [
                                    {
                                        "id": "map_warp_position",
                                        "kind": "map_position",
                                        "values": {
                                            "source_file": "maps/UnitMap.asm",
                                            "map_label": "UnitMap_MapEvents",
                                            "x": 1,
                                            "y": 2,
                                            "destination_map": "TARGET_MAP",
                                        },
                                        "watch_symbols": ["wMapGroup", "wMapNumber", "wXCoord", "wYCoord"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out_scenarios = root / "minimized_content.jsonl"

            report = build_minimization_plan(
                reports=("content_scenarios.json",),
                scenario_ids=("content_scenario_1_0000",),
                out_scenarios="minimized_content.jsonl",
                root=root,
            )
            minimized = [
                json.loads(line)
                for line in out_scenarios.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        preconditions = report["precondition_minimization"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["report_scenario_count"], 1)
        self.assertEqual(report["subset_output"]["record_count"], 1)
        self.assertEqual(minimized[0]["state_preconditions"][0]["kind"], "map_position")
        self.assertTrue(preconditions["attempted"])
        self.assertEqual(preconditions["selected_precondition_count"], 1)
        self.assertIn("precondition=map_position,scenario=content_scenario_1_0000", preconditions["expectations"])
        self.assertIn("tools.debugger expect --report content_scenarios.json", commands)
        self.assertIn("tools.debugger slice --source-file maps/UnitMap.asm", commands)
        self.assertIn("tools.debugger setup --report content_scenarios.json --scenario-id content_scenario_1_0000", commands)

    def test_cli_minimize_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenarios = root / "scenarios.jsonl"
            scenarios.write_text(
                json.dumps({"id": "unit_case", "moves": [{"id": "a"}]}) + "\n",
                encoding="utf-8",
            )
            out = root / "minimize.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "minimize",
                        "--scenario",
                        str(scenarios),
                        "--scenario-id",
                        "unit_case",
                        "--symbol",
                        "BossAI_SelectMove",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_minimization_plan")
        self.assertIn("unit_case", data["selected_scenario_ids"])

    def test_cli_minimize_writes_minimized_content_state_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_state = root / "content_state.json"
            content_state.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0000",
                                "status": "ready",
                                "patches": [
                                    {"symbol": "wMapGroup", "value": 24, "value_hex": "18"},
                                    {"symbol": "wMapNumber", "value": 3, "value_hex": "03"},
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "minimize.json"
            out_state_report = root / "minimized_state.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "minimize",
                        "--report",
                        str(content_state),
                        "--expect",
                        "state-patch=wMapGroup,scenario=content_scenario_1_0000,value=0x18",
                        "--out-state-report",
                        str(out_state_report),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            minimized = json.loads(out_state_report.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertTrue(data["state_patch_minimization"]["preserved"])
        self.assertEqual(data["state_patch_minimization"]["minimized_patch_count"], 1)
        self.assertEqual(minimized["materializations"][0]["patches"][0]["symbol"], "wMapGroup")

    def test_cli_minimize_writes_generic_minimized_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "events": [
                            {"access": "read", "symbol": "wNoise", "address": "D250"},
                            {"access": "write", "symbol": "wCurDamage", "address": "D141"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out = root / "minimize.json"
            out_trace = root / "minimized_trace.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "minimize",
                        "--trace",
                        str(trace),
                        "--expect",
                        "event=memory_write,symbol=wCurDamage",
                        "--out-trace",
                        str(out_trace),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            minimized = json.loads(out_trace.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertTrue(data["evidence_minimization"]["preserved"])
        self.assertEqual(len(minimized["events"]), 1)
        self.assertEqual(minimized["events"][0]["symbol"], "wCurDamage")

    def test_cli_minimize_writes_minimized_watch_report_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "events": [
                            {
                                "watch": "wCurDamage",
                                "old_hex": "0000",
                                "new_hex": "3400",
                                "pc_label": "BattleCommand_Final",
                                "dynamic_context": {
                                    "context_frame_count": 2,
                                    "prelude": [
                                        {
                                            "kind": "runtime_context_frame",
                                            "event_type": "control_flow",
                                            "frame": 0,
                                            "pc_label": "BattleCommand_Seed",
                                        },
                                        {
                                            "kind": "runtime_context_frame",
                                            "event_type": "control_flow",
                                            "frame": 1,
                                            "pc_label": "BattleCommand_DamageCalc",
                                        },
                                    ],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "minimize.json"
            out_trace = root / "minimized_watch.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "minimize",
                        "--report",
                        str(watch_report),
                        "--expect",
                        "event=watch_change,symbol=wCurDamage",
                        "--expect",
                        "event=control_flow,symbol=BattleCommand_DamageCalc",
                        "--out-trace",
                        str(out_trace),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            minimized = json.loads(out_trace.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertTrue(data["evidence_minimization"]["preserved"])
        self.assertEqual(data["evidence_minimization"]["source_kind"], "report")
        self.assertEqual(data["evidence_minimization"]["context_frame_minimized_count"], 1)
        self.assertEqual(minimized["events"][0]["dynamic_context"]["prelude"][0]["pc_label"], "BattleCommand_DamageCalc")

    def test_provenance_maps_symbols_to_source_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text(
                "01:4000 BattleCommand_Test\n02:5abc wCurDamage\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld hl, wCurDamage\n\tret\n",
                encoding="utf-8",
            )

            report = build_provenance_report(
                symbols_path="test.sym",
                symbols=("wCurDamage", "BattleCommand_Test"),
                source_files=("engine/battle.asm",),
                root=root,
            )

        self.assertTrue(report["valid"])
        by_query = {item["query"]: item for item in report["symbols"]}
        self.assertEqual(by_query["wCurDamage"]["address"]["bank_address"], "02:5ABC")
        self.assertGreaterEqual(by_query["wCurDamage"]["source_hit_count"], 2)
        self.assertEqual(by_query["wCurDamage"]["source_hits"][0]["kind"], "definition")
        self.assertEqual(report["source_files"][0]["symbols_matched_count"], 1)

    def test_cli_provenance_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            symbols = root / "test.sym"
            symbols.write_text("01:4000 LabelOne\n", encoding="utf-8")
            out = root / "provenance.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "provenance",
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "LabelOne",
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_provenance_report")
            self.assertTrue(data["valid"])

    def test_slice_maps_symbol_to_static_reference_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text(
                "01:D141 wCurDamage\n01:4000 BattleCommand_Test\n01:4010 Helper\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "\n".join(
                    [
                        "BattleCommand_Test:",
                        "\tld [wCurDamage], a",
                        "\tjr .done",
                        "\tcall Helper",
                        "\tret",
                        ".done",
                        "\tret",
                        "Helper:",
                        "\tld a, [wCurDamage]",
                        "\tret",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_slice_report(
                symbols_path="test.sym",
                symbols=("wCurDamage", "BattleCommand_Test"),
                root=root,
            )

        self.assertTrue(report["valid"])
        target = report["targets"][0]
        self.assertTrue(target["found"])
        self.assertEqual(target["definition"]["path"], "ram/wram.asm")
        accesses = {edge["access"] for edge in target["incoming"]}
        sources = {edge["source"] for edge in target["incoming"]}
        self.assertIn("write", accesses)
        self.assertIn("read", accesses)
        self.assertIn("BattleCommand_Test", sources)
        self.assertIn("Helper", sources)
        routine = report["targets"][1]
        self.assertIn(
            "BattleCommand_Test.done",
            {edge["target"] for edge in routine["outgoing"]},
        )

    def test_slice_ignores_rgbds_control_directives_as_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            (root / "test.sym").write_text(
                "01:D0D3 wEnemyAIMoveScores\n01:4000 BossAI_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wEnemyAIMoveScores:: ds 4\n",
                encoding="utf-8",
            )
            (root / "engine" / "ai.asm").write_text(
                "\n".join(
                    [
                        "IF DEF(_DEBUG)",
                        "ENDC",
                        "\tdw wEnemyAIMoveScores",
                        "BossAI_Test:",
                        "\tld hl, wEnemyAIMoveScores",
                        "\tret",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_slice_report(
                symbols_path="test.sym",
                symbols=("wEnemyAIMoveScores",),
                root=root,
            )

        incoming_sources = {edge["source"] for edge in report["targets"][0]["incoming"]}

        self.assertTrue(report["valid"])
        self.assertNotIn("ENDC", incoming_sources)
        self.assertIn("BossAI_Test", incoming_sources)

    def test_cli_slice_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            symbols = root / "test.sym"
            symbols.write_text("01:D141 wCurDamage\n", encoding="utf-8")
            (root / "ram" / "wram.asm").write_text("wCurDamage:: ds 2\n", encoding="utf-8")
            out = root / "slice.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "slice",
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "wCurDamage",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_causal_slice")
        self.assertTrue(data["valid"])

    def test_instruction_trace_plans_function_hooks_from_rom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4006] = bytes([0x3E, 0x2A, 0xEA, 0x41, 0xD1, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 UnitFunc\n01:4006 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                function_symbols=("UnitFunc",),
                watch_symbols=("wCurDamage",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        instructions = report["functions"][0]["instructions"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertFalse(report["executed"])
        self.assertEqual(report["instruction_count"], 3)
        self.assertEqual(instructions[0]["mnemonic"], "ld a, $2a")
        self.assertEqual(instructions[1]["mnemonic"], "ld [$d141], a")
        self.assertIn("tools.debugger trace-instructions", commands)
        self.assertIn("tools.debugger dynamic-taint", commands)
        self.assertIn("--sink-symbol wCurDamage", commands)

    def test_instruction_trace_derives_window_from_watch_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4006] = bytes([0x3E, 0x2A, 0xEA, 0x41, 0xD1, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 UnitFunc\n01:4006 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )
            (root / "watch.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "events": [
                            {
                                "watch": "wCurDamage",
                                "old_hex": "0000",
                                "new_hex": "002A",
                                "pc_label": "UnitFunc+0x5",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                reports=("watch.json",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        selection = report["target_selection"]

        self.assertTrue(report["valid"])
        self.assertEqual(selection["function_symbols"], ["UnitFunc"])
        self.assertEqual(selection["watch_symbols"], ["wCurDamage"])
        self.assertEqual(report["instruction_count"], 3)

    def test_instruction_trace_derives_window_from_content_scenario_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:4000 UnitHelper",
                        "01:4003 NextFunc",
                        "02:5000 UnitMovement",
                        "01:D140 wMovementPointer",
                        "01:D142 wMovementObject",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "movement_data",
                                "label": "UnitMovement",
                                "state_preconditions": [
                                    {
                                        "kind": "movement_entry",
                                        "watch_symbols": ["wMovementObject"],
                                    }
                                ],
                                "runtime_targets": {
                                    "trace_symbols": ["UnitHelper"],
                                    "script_symbols": ["UnitMovement"],
                                    "watch_symbols": ["wMovementPointer"],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                reports=("content.json",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        selection = report["target_selection"]

        self.assertTrue(report["valid"])
        self.assertEqual(selection["function_symbols"], ["UnitHelper"])
        self.assertNotIn("UnitMovement", selection["function_symbols"])
        self.assertEqual(selection["watch_symbols"], ["wMovementObject", "wMovementPointer"])
        self.assertEqual(report["instruction_count"], 3)

    def test_instruction_trace_filters_content_scenario_report_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            rom[0x4010:0x4013] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:4000 FirstHelper",
                        "01:4003 FirstNext",
                        "01:4010 SecondHelper",
                        "01:4013 SecondNext",
                        "01:D140 wFirstWatch",
                        "01:D141 wSecondWatch",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "runtime_targets": {
                                    "trace_symbols": ["FirstHelper"],
                                    "watch_symbols": ["wFirstWatch"],
                                },
                            },
                            {
                                "id": "content_scenario_1_0001",
                                "kind": "unified_debugger_content_scenario",
                                "runtime_targets": {
                                    "trace_symbols": ["SecondHelper"],
                                    "watch_symbols": ["wSecondWatch"],
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                reports=("content.json",),
                scenario_ids=("content_scenario_1_0001",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        selection = report["target_selection"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(selection["function_symbols"], ["SecondHelper"])
        self.assertEqual(selection["watch_symbols"], ["wSecondWatch"])
        self.assertNotIn("FirstHelper", selection["function_symbols"])
        self.assertIn("--scenario-id content_scenario_1_0001", commands)

    def test_instruction_trace_derives_window_from_content_state_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            for offset in range(0x4000, 0x4020, 3):
                rom[offset : offset + 3] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:4000 ScriptEvents",
                        "01:4003 RunScriptCommand",
                        "01:4006 CallScript",
                        "01:4009 ApplyMovement",
                        "01:400C GetMovementData",
                        "01:400F HandleMovementData",
                        "01:4012 WaitScriptMovement",
                        "01:4015 NextFunc",
                        "01:D140 wScriptPos",
                        "01:D141 wMovementDataAddress",
                        "01:D143 wMovementPointer",
                        "01:D145 wMovementObject",
                        "01:D146 wScriptMode",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "content_state.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0000",
                                "scenario_type": "script_command_stream",
                                "precondition_kind": "script_entry",
                                "status": "ready",
                                "patches": [{"symbol": "wScriptPos", "base_symbol": "wScriptPos", "value": 0}],
                            },
                            {
                                "scenario_id": "content_scenario_1_0001",
                                "scenario_type": "movement_data",
                                "precondition_kind": "movement_entry",
                                "status": "ready",
                                "patches": [
                                    {"symbol": "wMovementDataAddress", "base_symbol": "wMovementDataAddress", "value": 0},
                                    {"symbol": "wMovementPointer", "base_symbol": "wMovementPointer", "value": 0},
                                    {"symbol": "wMovementObject", "base_symbol": "wMovementObject", "value": 0},
                                    {"symbol": "wScriptMode", "base_symbol": "wScriptMode", "value": 2},
                                ],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                reports=("content_state.json",),
                scenario_ids=("content_scenario_1_0001",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        selection = report["target_selection"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(
            selection["function_symbols"],
            ["ApplyMovement", "GetMovementData", "HandleMovementData", "WaitScriptMovement"],
        )
        self.assertNotIn("ScriptEvents", selection["function_symbols"])
        self.assertEqual(
            selection["watch_symbols"],
            ["wMovementDataAddress", "wMovementObject", "wMovementPointer", "wScriptMode"],
        )
        self.assertNotIn("wScriptPos", selection["watch_symbols"])
        self.assertIn("--report content_state.json --scenario-id content_scenario_1_0001", commands)

    def test_instruction_trace_uses_executed_content_state_out_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            for offset in range(0x4000, 0x4020, 3):
                rom[offset : offset + 3] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "patched.state").write_bytes(b"patched-state")
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:4000 ApplyMovement",
                        "01:4003 GetMovementData",
                        "01:4006 HandleMovementData",
                        "01:4009 WaitScriptMovement",
                        "01:400C NextFunc",
                        "01:D141 wMovementDataAddress",
                        "01:D143 wMovementPointer",
                        "01:D145 wMovementObject",
                        "01:D146 wScriptMode",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "content_state.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "executed": True,
                        "out_state": "patched.state",
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0001",
                                "scenario_type": "movement_data",
                                "precondition_kind": "movement_entry",
                                "status": "ready",
                                "patches": [
                                    {"symbol": "wMovementDataAddress", "base_symbol": "wMovementDataAddress", "value": 0},
                                    {"symbol": "wMovementPointer", "base_symbol": "wMovementPointer", "value": 0},
                                    {"symbol": "wMovementObject", "base_symbol": "wMovementObject", "value": 0},
                                    {"symbol": "wScriptMode", "base_symbol": "wScriptMode", "value": 2},
                                ],
                            },
                        ],
                        "execution": {
                            "executed": True,
                            "out_state": "patched.state",
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                reports=("content_state.json",),
                scenario_ids=("content_scenario_1_0001",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        selection = report["target_selection"]
        selected_state = report["save_state_discovery"]["selected"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(selection["function_symbols"], ["ApplyMovement", "GetMovementData", "HandleMovementData", "WaitScriptMovement"])
        self.assertEqual(report["input_save_state"], "")
        self.assertEqual(report["effective_save_state"], "patched.state")
        self.assertEqual(report["save_state"], "patched.state")
        self.assertEqual(selected_state["key"], "execution.out_state")
        self.assertEqual(selected_state["scenario_id"], "content_scenario_1_0001")
        self.assertTrue(selected_state["exists"])
        self.assertIn("--save-state patched.state", commands)

    def test_instruction_trace_uses_executed_state_space_out_state_and_watches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "patched.state").write_bytes(b"patched-state")
            (root / "test.sym").write_text(
                "01:4000 ScriptEvents\n01:4003 NextFunc\n01:DA10 wScriptBank\n01:DA11 wScriptPos\n",
                encoding="utf-8",
            )
            (root / "state_space.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_state_space",
                        "valid": True,
                        "executed": True,
                        "scenario_id": "script_entry_1",
                        "out_state": "patched.state",
                        "watch_symbols": ["wScriptPos"],
                        "state_space": {
                            "scenario_ids": ["script_entry_1"],
                            "patches": [
                                {
                                    "symbol": "wScriptBank",
                                    "base_symbol": "wScriptBank",
                                    "value": 2,
                                    "value_hex": "02",
                                    "scenario_id": "script_entry_1",
                                },
                                {
                                    "symbol": "wScriptPos",
                                    "base_symbol": "wScriptPos",
                                    "value": 80,
                                    "value_hex": "50",
                                    "scenario_id": "script_entry_1",
                                },
                            ],
                        },
                        "execution": {
                            "executed": True,
                            "out_state": "patched.state",
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                function_symbols=("ScriptEvents",),
                reports=("state_space.json",),
                scenario_ids=("script_entry_1",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        selection = report["target_selection"]
        selected_state = report["save_state_discovery"]["selected"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(selection["function_symbols"], ["ScriptEvents"])
        self.assertIn("wScriptBank", selection["watch_symbols"])
        self.assertIn("wScriptPos", selection["watch_symbols"])
        self.assertEqual(report["effective_save_state"], "patched.state")
        self.assertEqual(selected_state["key"], "execution.out_state")
        self.assertEqual(selected_state["scenario_id"], "script_entry_1")
        self.assertTrue(selected_state["exists"])
        self.assertIn("--save-state patched.state", commands)
        self.assertIn("--scenario-id script_entry_1", commands)

    def test_instruction_trace_does_not_use_unexecuted_content_state_out_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "patched.state").write_bytes(b"planned-state")
            (root / "test.sym").write_text(
                "01:4000 ApplyMovement\n01:4003 NextFunc\n01:D145 wMovementObject\n",
                encoding="utf-8",
            )
            (root / "content_state.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "executed": False,
                        "out_state": "patched.state",
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0001",
                                "scenario_type": "movement_data",
                                "precondition_kind": "movement_entry",
                                "status": "ready",
                                "patches": [{"symbol": "wMovementObject", "base_symbol": "wMovementObject", "value": 0}],
                            }
                        ],
                        "execution": {
                            "executed": False,
                            "out_state": "patched.state",
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                reports=("content_state.json",),
                scenario_ids=("content_scenario_1_0001",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "")
        self.assertEqual(report["save_state_discovery"]["selected"], {})
        self.assertNotIn("--save-state patched.state", commands)

    def test_instruction_trace_does_not_use_unexecuted_state_space_out_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "patched.state").write_bytes(b"planned-state")
            (root / "test.sym").write_text("01:4000 ScriptEvents\n01:4003 NextFunc\n01:DA11 wScriptPos\n", encoding="utf-8")
            (root / "state_space.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_state_space",
                        "valid": True,
                        "executed": False,
                        "scenario_id": "script_entry_1",
                        "out_state": "patched.state",
                        "state_space": {
                            "scenario_ids": ["script_entry_1"],
                            "patches": [{"symbol": "wScriptPos", "base_symbol": "wScriptPos", "value": 80}],
                        },
                        "execution": {
                            "executed": False,
                            "out_state": "patched.state",
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                function_symbols=("ScriptEvents",),
                reports=("state_space.json",),
                scenario_ids=("script_entry_1",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "")
        self.assertEqual(report["save_state_discovery"]["selected"], {})
        self.assertIn("wScriptPos", report["target_selection"]["watch_symbols"])
        self.assertNotIn("--save-state patched.state", commands)

    def test_instruction_trace_derives_window_from_changed_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine" / "battle").mkdir(parents=True)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 SourceFunc\n01:4003 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "unit.asm").write_text(
                "SourceFunc:\n\tnop\n\tret\n",
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                changed_files=("engine/battle/unit.asm",),
                watch_symbols=("wCurDamage",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["target_selection"]["function_symbols"], ["SourceFunc"])
        self.assertEqual(report["target_selection"]["watch_symbols"], ["wCurDamage"])

    def test_cli_trace_instructions_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4006] = bytes([0x3E, 0x2A, 0xEA, 0x41, 0xD1, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 UnitFunc\n01:4006 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )
            out = root / "instruction_trace.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "trace-instructions",
                        "--rom",
                        str(root / "unit.gbc"),
                        "--symbols",
                        str(root / "test.sym"),
                        "--symbol",
                        "UnitFunc",
                        "--watch-symbol",
                        "wCurDamage",
                        "--require-hit",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_instruction_trace")
        self.assertTrue(data["valid"])
        self.assertTrue(data["require_hit"])
        self.assertIn("--require-hit is only enforced with --execute", data["warnings"])
        self.assertEqual(data["instruction_count"], 3)
        self.assertFalse(data["trace_output"]["written"])

    def test_instruction_trace_validates_executed_hook_hits(self) -> None:
        class FakeRegisters:
            A = 0x2A
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0xD1
            L = 0x41
            SP = 0xFFFE
            PC = 0x4000

        class FakeMemory:
            def __init__(self) -> None:
                self.values = {
                    (1, 0xD141): 0x00,
                    (1, 0xD142): 0x2A,
                    0xFF70: 1,
                }

            def __getitem__(self, key):
                return self.values.get(key, 0)

            def __setitem__(self, key, value) -> None:
                self.values[key] = value

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()
                self.callbacks = []

            def hook_register(self, bank, pc, callback, _ctx) -> None:
                self.callbacks.append((bank, pc, callback))

            def hook_deregister(self, bank, pc) -> None:
                self.callbacks = [
                    item for item in self.callbacks if item[:2] != (bank, pc)
                ]

            def tick(self, *_args) -> None:
                for _bank, pc, callback in list(self.callbacks):
                    self.register_file.PC = pc
                    callback(None)

            def stop(self, save=False) -> None:
                self.stopped = True

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4006] = bytes([0x3E, 0x2A, 0xEA, 0x41, 0xD1, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 UnitFunc\n01:4006 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )
            out_trace = root / "trace.jsonl"

            with patch("tools.debugger.instruction_trace.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                report = build_instruction_trace_report(
                    function_symbols=("UnitFunc",),
                    watch_symbols=("wCurDamage",),
                    rom_path="unit.gbc",
                    symbols_path="test.sym",
                    execute=True,
                    require_hit=True,
                    out_trace=str(out_trace),
                    root=root,
                )

            rows = [
                json.loads(line)
                for line in out_trace.read_text(encoding="utf-8").splitlines()
            ]

        validation = report["execution_validation"]

        self.assertTrue(report["valid"])
        self.assertTrue(report["executed"])
        self.assertTrue(validation["hit"])
        self.assertTrue(validation["ready_for_dynamic_taint"])
        self.assertEqual(validation["hit_function_symbols"], ["UnitFunc"])
        self.assertEqual(validation["missing_function_symbols"], [])
        self.assertEqual(report["captured_frame_count"], 3)
        self.assertEqual(report["trace_output"]["record_count"], 3)
        self.assertEqual(rows[0]["function"], "UnitFunc")
        self.assertEqual(rows[0]["watch_values"]["wCurDamage"], "002A")

    def test_instruction_trace_can_require_an_executed_hook_hit(self) -> None:
        class FakeRegisters:
            A = 0
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0
            L = 0
            SP = 0xFFFE
            PC = 0x4000

        class FakeMemory:
            def __getitem__(self, key):
                return 0

            def __setitem__(self, key, value) -> None:
                pass

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()

            def hook_register(self, *_args) -> None:
                pass

            def hook_deregister(self, *_args) -> None:
                pass

            def tick(self, *_args) -> None:
                pass

            def stop(self, save=False) -> None:
                pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 UnitFunc\n01:4003 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )

            with patch("tools.debugger.instruction_trace.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                strict_report = build_instruction_trace_report(
                    function_symbols=("UnitFunc",),
                    watch_symbols=("wCurDamage",),
                    rom_path="unit.gbc",
                    symbols_path="test.sym",
                    execute=True,
                    require_hit=True,
                    root=root,
                )
            with patch("tools.debugger.instruction_trace.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                loose_report = build_instruction_trace_report(
                    function_symbols=("UnitFunc",),
                    watch_symbols=("wCurDamage",),
                    rom_path="unit.gbc",
                    symbols_path="test.sym",
                    execute=True,
                    root=root,
                )

        self.assertFalse(strict_report["valid"])
        self.assertFalse(strict_report["execution_validation"]["hit"])
        self.assertIn("none of the selected hooks fired", "\n".join(strict_report["errors"]))
        self.assertTrue(loose_report["valid"])
        self.assertIn("none of the selected hooks fired", "\n".join(loose_report["warnings"]))

    def test_cli_trace_instructions_uses_report_for_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 UnitFunc\n01:4003 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )
            (root / "watch.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "events": [{"watch": "wCurDamage", "pc_label": "UnitFunc"}],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "instruction_trace.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "trace-instructions",
                        "--rom",
                        str(root / "unit.gbc"),
                        "--symbols",
                        str(root / "test.sym"),
                        "--report",
                        str(root / "watch.json"),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["target_selection"]["function_symbols"], ["UnitFunc"])
        self.assertEqual(data["target_selection"]["watch_symbols"], ["wCurDamage"])

    def test_dynamic_taint_traces_instruction_source_to_sink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            trace = root / "instruction_trace.jsonl"
            trace.write_text(
                "\n".join(
                    json.dumps(row)
                    for row in [
                        {
                            "seq": 0,
                            "bank": 1,
                            "pc": 0x4000,
                            "pc_label": "BattleCommand_Test",
                            "opcode": 0x4F,
                            "regs": {"A": 0x37, "C": 0, "HL": 0, "SP": 0xDFF0},
                        },
                        {
                            "seq": 1,
                            "bank": 1,
                            "pc": 0x4001,
                            "pc_label": "BattleCommand_Test+0x1",
                            "opcode": 0x79,
                            "regs": {"A": 0x37, "C": 0x37, "HL": 0, "SP": 0xDFF0},
                        },
                        {
                            "seq": 2,
                            "bank": 1,
                            "pc": 0x4002,
                            "pc_label": "BattleCommand_Test+0x2",
                            "opcode": 0x21,
                            "operand": [0x41, 0xD1],
                            "regs": {"A": 0x37, "C": 0x37, "HL": 0, "SP": 0xDFF0},
                        },
                        {
                            "seq": 3,
                            "bank": 1,
                            "pc": 0x4005,
                            "pc_label": "BattleCommand_Test+0x5",
                            "opcode": 0x22,
                            "regs": {"A": 0x37, "C": 0x37, "HL": 0xD141, "SP": 0xDFF0},
                        },
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_dynamic_taint_report(
                traces=("instruction_trace.jsonl",),
                symbols_path="test.sym",
                source_regs=("a=move_power",),
                sink_symbols=("wCurDamage",),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["finding_count"], 1)
        self.assertEqual(report["paths"][0]["target"], "wCurDamage")
        self.assertIn("move_power", report["paths"][0]["taint"])
        self.assertEqual(report["trace_runs"][0]["unsupported_count"], 0)

    def test_cli_dynamic_taint_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:D141 wCurDamage\n", encoding="utf-8")
            trace = root / "instruction_trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "instructions": [
                            {
                                "seq": 0,
                                "bank": 1,
                                "pc": 0x4000,
                                "pc_label": "UnitCopy",
                                "opcode": 0xEA,
                                "operand": [0x41, 0xD1],
                                "regs": {"A": 0x2A, "SP": 0xDFF0},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out = root / "dynamic_taint.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "dynamic-taint",
                        "--trace",
                        str(trace),
                        "--symbols",
                        str(root / "test.sym"),
                        "--source-reg",
                        "a=move_power",
                        "--sink-symbol",
                        "wCurDamage",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_dynamic_taint_report")
        self.assertTrue(data["valid"])
        self.assertEqual(data["path_count"], 1)
        self.assertIn("move_power", data["paths"][0]["taint"])

    def test_cli_dynamic_taint_accepts_instruction_trace_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:D141 wCurDamage\n", encoding="utf-8")
            (root / "instruction_trace.jsonl").write_text(
                json.dumps(
                    {
                        "seq": 0,
                        "bank": 1,
                        "pc": 0x4000,
                        "pc_label": "UnitCopy",
                        "opcode": 0xEA,
                        "operand": [0x41, 0xD1],
                        "regs": {"A": 0x2A, "SP": 0xDFF0},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "instruction_trace_report.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": True,
                        "executed": True,
                        "trace_output": {"path": "instruction_trace.jsonl", "written": True},
                        "execution_validation": {
                            "attempted": True,
                            "hit": True,
                            "watch_symbols": ["wCurDamage"],
                            "ready_for_dynamic_taint": True,
                        },
                        "dynamic_taint_sources": {"source_regs": ["a=move_power"]},
                    }
                ),
                encoding="utf-8",
            )
            out = root / "dynamic_taint.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "dynamic-taint",
                        "--report",
                        str(root / "instruction_trace_report.json"),
                        "--symbols",
                        str(root / "test.sym"),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertTrue(data["valid"])
        self.assertEqual(len(data["effective_traces"]), 1)
        self.assertTrue(data["effective_traces"][0].endswith("instruction_trace.jsonl"))
        self.assertEqual(data["path_count"], 1)
        self.assertIn("move_power", data["paths"][0]["taint"])

    def test_dynamic_taint_attributes_sink_write_without_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:4000 UnitWriter\n",
                encoding="utf-8",
            )
            trace = root / "instruction_trace.jsonl"
            trace.write_text(
                json.dumps(
                    {
                        "seq": 0,
                        "bank": 1,
                        "pc": 0x4000,
                        "pc_label": "UnitWriter",
                        "opcode": 0xEA,
                        "operand": [0x41, 0xD1],
                        "regs": {"A": 0x2A, "SP": 0xDFF0},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_dynamic_taint_report(
                traces=("instruction_trace.jsonl",),
                symbols_path="test.sym",
                sink_symbols=("wCurDamage",),
                root=root,
            )

        attribution = report["write_attributions"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(report["source_count"], 0)
        self.assertEqual(report["finding_count"], 0)
        self.assertEqual(report["path_count"], 0)
        self.assertEqual(report["write_attribution_count"], 1)
        self.assertIn("no taint sources supplied", "\n".join(report["warnings"]))
        self.assertEqual(attribution["target"], "wCurDamage")
        self.assertEqual(attribution["pc_label"], "UnitWriter")
        self.assertEqual(attribution["address"], "D141")
        self.assertEqual(attribution["source_operands"][0]["kind"], "register")
        self.assertEqual(attribution["source_operands"][0]["name"], "a")
        self.assertEqual(attribution["source_operands"][0]["value"], "2A")
        self.assertIn("register:a=$2A", "\n".join(attribution["evidence"]))
        self.assertEqual(report["targets"][0]["write_attribution_count"], 1)

    def test_dynamic_taint_discovers_trace_inputs_from_instruction_trace_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:4000 UnitWriter\n",
                encoding="utf-8",
            )
            (root / "instruction_trace.jsonl").write_text(
                json.dumps(
                    {
                        "seq": 0,
                        "bank": 1,
                        "pc": 0x4000,
                        "pc_label": "UnitWriter",
                        "opcode": 0xEA,
                        "operand": [0x41, 0xD1],
                        "regs": {"A": 0x2A, "SP": 0xDFF0},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "instruction_trace_report.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": True,
                        "executed": True,
                        "execution_validation": {
                            "attempted": True,
                            "hit": True,
                            "watch_symbols": ["wCurDamage"],
                            "ready_for_dynamic_taint": True,
                        },
                        "trace_output": {
                            "path": "instruction_trace.jsonl",
                            "written": True,
                            "record_count": 1,
                        },
                        "watches": [{"name": "wCurDamage"}],
                        "dynamic_taint_sources": {
                            "source_regs": ["a=script_arg"],
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_dynamic_taint_report(
                reports=("instruction_trace_report.json",),
                symbols_path="test.sym",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["report_count"], 1)
        self.assertEqual(report["effective_traces"], ["instruction_trace.jsonl"])
        self.assertEqual(report["input_discovery"]["sink_symbols"], ["wCurDamage"])
        self.assertEqual(report["input_discovery"]["source_regs"], ["a=script_arg"])
        self.assertEqual(report["source_count"], 1)
        self.assertEqual(report["sink_count"], 1)
        self.assertEqual(report["path_count"], 1)
        self.assertEqual(report["write_attribution_count"], 1)
        self.assertIn("script_arg", report["paths"][0]["taint"])

    def test_rank_localize_and_impact_consume_dynamic_taint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dynamic_taint = root / "dynamic_taint.json"
            dynamic_taint.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_dynamic_taint_report",
                        "valid": True,
                        "errors": [],
                        "warnings": [],
                        "targets": [
                            {
                                "symbol": "wCurDamage",
                                "found": True,
                                "sink_count": 1,
                                "contributor_count": 1,
                                "sinks": [{"routine": "BattleCommand_Test", "access": "dynamic_write"}],
                                "contributors": [
                                    {
                                        "symbol": "move_power",
                                        "relation": "register_taints_sink",
                                    }
                                ],
                            }
                        ],
                        "paths": [
                            {
                                "title": "move_power -> wCurDamage",
                                "target": "wCurDamage",
                                "access": "dynamic_write",
                                "score": 92,
                                "confidence": 0.9,
                                "evidence": ["seq=3 pc=$4005", "ld [hli], a"],
                                "commands": ["python -m tools.debugger replay --symbol wCurDamage"],
                                "related_symbols": ["wCurDamage", "move_power"],
                                "related_files": [],
                                "contributors": [
                                    {
                                        "symbol": "move_power",
                                        "relation": "register_taints_sink",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("dynamic_taint.json",), root=root)
            localized = build_localization_plan(reports=("dynamic_taint.json",), root=root)
            impact = build_impact_report(reports=("dynamic_taint.json",), root=root)

        self.assertIn("taint_path", {finding["type"] for finding in ranked["findings"]})
        self.assertIn("wCurDamage", {candidate["id"] for candidate in localized["candidates"]})
        self.assertIn("taint_path", {item["type"] for item in impact["items"]})

    def test_rank_localize_and_impact_consume_dynamic_write_attribution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dynamic_taint = root / "dynamic_write.json"
            dynamic_taint.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_dynamic_taint_report",
                        "valid": True,
                        "errors": [],
                        "warnings": [],
                        "targets": [
                            {
                                "symbol": "wCurDamage",
                                "found": True,
                                "sink_count": 1,
                                "write_attribution_count": 1,
                                "sinks": [{"routine": "UnitWriter", "access": "dynamic_write"}],
                                "contributors": [],
                            }
                        ],
                        "paths": [],
                        "write_attributions": [
                            {
                                "target": "wCurDamage",
                                "pc_label": "UnitWriter",
                                "mnemonic": "ld [$d141], a",
                                "score": 72,
                                "confidence": 0.76,
                                "evidence": [
                                    "seq=0 pc=$4000",
                                    "ld [$d141], a",
                                    "write wCurDamage@$D141",
                                    "sources=register:a=$2A",
                                ],
                                "related_symbols": ["wCurDamage", "UnitWriter", "a"],
                                "related_files": [],
                                "commands": ["python -m tools.debugger explain --symbol wCurDamage"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("dynamic_write.json",), root=root)
            localized = build_localization_plan(reports=("dynamic_write.json",), root=root)
            impact = build_impact_report(reports=("dynamic_write.json",), root=root)

        self.assertIn("reverse_attribution", {finding["type"] for finding in ranked["findings"]})
        self.assertIn("wCurDamage", {candidate["id"] for candidate in localized["candidates"]})
        self.assertIn("UnitWriter", {candidate["id"] for candidate in localized["candidates"]})
        self.assertIn("reverse_attribution", {item["type"] for item in impact["items"]})

    def test_taint_traces_register_loads_to_memory_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine" / "battle").mkdir(parents=True)
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:D141 wCurDamage",
                        "01:D142 wBattleMonAttack",
                        "01:D144 wPlayerMovePower",
                        "01:4000 BattleCommand_DamageCalc",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\nwBattleMonAttack:: ds 2\nwPlayerMovePower:: ds 1\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "effect_commands.asm").write_text(
                "\n".join(
                    [
                        "BattleCommand_DamageCalc:",
                        "\tld a, [wBattleMonAttack]",
                        "\tadd a, [wPlayerMovePower]",
                        "\tld [wCurDamage], a",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_taint_report(
                symbols_path="test.sym",
                symbols=("wCurDamage",),
                source_files=("engine/battle/effect_commands.asm",),
                root=root,
            )

        target = report["targets"][0]
        contributors = {item["symbol"] for item in target["contributors"]}
        relations = {item["relation"] for item in target["contributors"]}

        self.assertTrue(report["valid"])
        self.assertEqual(report["sink_count"], 1)
        self.assertIn("wBattleMonAttack", contributors)
        self.assertIn("wPlayerMovePower", contributors)
        self.assertIn("memory_load", relations)
        self.assertIn("value_transform", relations)
        self.assertIn("tools.debugger taint --symbol wBattleMonAttack", "\n".join(report["commands"]))

    def test_taint_resolves_same_routine_indirect_hl_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:D0D3 wEnemyAIMoveScores",
                        "01:D0E0 wBossAIRole",
                        "01:4000 BossAI_Test",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wEnemyAIMoveScores:: ds 4\nwBossAIRole:: ds 1\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "boss.asm").write_text(
                "\n".join(
                    [
                        "BossAI_Test:",
                        "\tld hl, wEnemyAIMoveScores",
                        "\tld a, [wBossAIRole]",
                        "\tld [hl], a",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_taint_report(
                symbols_path="test.sym",
                symbols=("wEnemyAIMoveScores",),
                source_files=("engine/battle/ai/boss.asm",),
                root=root,
            )

        target = report["targets"][0]
        contributors = {item["symbol"]: item for item in target["contributors"]}

        self.assertTrue(report["valid"])
        self.assertEqual(target["sinks"][0]["access"], "indirect_write")
        self.assertEqual(target["sinks"][0]["pointer_register"], "hl")
        self.assertIn("wBossAIRole", contributors)
        self.assertEqual(contributors["wBossAIRole"]["relation"], "memory_load")

    def test_cli_taint_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text(
                "01:D141 wCurDamage\n01:D142 wBattleMonAttack\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\nwBattleMonAttack:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld a, [wBattleMonAttack]\n\tld [wCurDamage], a\n",
                encoding="utf-8",
            )
            out = root / "taint.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "taint",
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "wCurDamage",
                        "--source-file",
                        str(root / "engine" / "battle.asm"),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_taint_report")
        self.assertEqual(data["sink_count"], 1)

    def test_explain_links_watch_event_to_static_writer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text(
                "01:D141 wCurDamage\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld [wCurDamage], a\n\tret\n",
                encoding="utf-8",
            )
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "events": [
                            {
                                "frame": 7,
                                "watch": "wCurDamage",
                                "pc_label": "BattleCommand_Test",
                                "pc_bank_address": "01:4000",
                                "old_hex": "0000",
                                "new_hex": "002A",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_explanation_report(
                reports=("watch.json",),
                symbols_path="test.sym",
                symptom="damage changed unexpectedly",
                root=root,
            )

        first_path = report["paths"][0]
        relations = {edge["relation"] for edge in first_path["edges"]}
        labels = {node["label"] for node in first_path["nodes"]}

        self.assertTrue(report["valid"])
        self.assertEqual(report["dynamic_event_count"], 1)
        self.assertGreaterEqual(first_path["confidence"], 0.9)
        self.assertIn("write", relations)
        self.assertIn("wCurDamage", labels)
        self.assertIn("BattleCommand_Test", labels)
        self.assertIn("BattleCommand_Test", report["mermaid"])

    def test_trace_index_extracts_watch_and_score_delta_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n0E:483E BossAI_ApplyMoveModel\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text("wCurDamage:: ds 2\n", encoding="utf-8")
            (root / "engine" / "battle" / "ai" / "boss_policy_move.asm").write_text(
                "BossAI_ApplyMoveModel:\n\tret\n",
                encoding="utf-8",
            )
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "events": [
                            {
                                "event_type": "score_delta",
                                "score_pointer": "d0d3",
                                "score_before": 20,
                                "score_after": 18,
                                "source": {
                                    "full_symbol": "BossAI_ApplyMoveModel",
                                    "rule_id": "move.apply_move_model",
                                },
                            },
                            {
                                "watch": "wCurDamage",
                                "old_hex": "0000",
                                "new_hex": "002A",
                                "pc_label": "BossAI_ApplyMoveModel",
                                "pc_bank_address": "0E:483E",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = build_trace_index_report(
                traces=("trace.json",),
                addresses=("D0D3",),
                watch_symbols=("wCurDamage",),
                symbols_path="test.sym",
                root=root,
            )

        event_types = {event["event_type"] for event in report["events"]}
        indexed_addresses = {item["address"] for item in report["address_index"]}
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("score_delta", event_types)
        self.assertIn("watch_change", event_types)
        self.assertIn("D0D3", indexed_addresses)
        self.assertGreaterEqual(report["path_count"], 1)
        self.assertIn("tools.debugger explain", commands)

    def test_trace_index_consumes_watch_dynamic_context_frames(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "00:D141 wCurDamage\n00:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "events": [
                            {
                                "watch": "wCurDamage",
                                "old_hex": "0000",
                                "new_hex": "3400",
                                "pc_label": "BattleCommand_Test+0x3",
                                "pc_bank_address": "00:4003",
                                "dynamic_context": {
                                    "context_frame_count": 1,
                                    "prelude": [
                                        {
                                            "kind": "runtime_context_frame",
                                            "event_type": "control_flow",
                                            "frame": 0,
                                            "pc": 0x4000,
                                            "pc_bank": 0,
                                            "pc_bank_address": "00:4000",
                                            "pc_label": "BattleCommand_Test",
                                            "registers": {"register_pc": "4000", "register_a": "12"},
                                            "register_pc": "4000",
                                            "register_a": "12",
                                            "watch_values": {"wCurDamage": "0000"},
                                        }
                                    ],
                                    "after": {
                                        "kind": "runtime_context_frame",
                                        "event_type": "control_flow",
                                        "frame": 1,
                                        "pc": 0x4003,
                                        "pc_bank": 0,
                                        "pc_bank_address": "00:4003",
                                        "pc_label": "BattleCommand_Test+0x3",
                                        "registers": {"register_pc": "4003", "register_a": "12"},
                                        "register_pc": "4003",
                                        "register_a": "12",
                                        "watch_values": {"wCurDamage": "3400"},
                                    },
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_trace_index_report(
                reports=("watch.json",),
                symbols_path="test.sym",
                root=root,
            )

        event_types = [event["event_type"] for event in report["events"]]
        control_flow_pcs = {
            event["pc_bank_address"]
            for event in report["events"]
            if event["event_type"] == "control_flow"
        }

        self.assertTrue(report["valid"])
        self.assertIn("watch_change", event_types)
        self.assertGreaterEqual(event_types.count("control_flow"), 2)
        self.assertIn("00:4000", control_flow_pcs)
        self.assertIn("00:4003", control_flow_pcs)

    def test_trace_index_builds_reverse_attribution_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine" / "battle").mkdir(parents=True)
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:D142 wBattleMonAttack\n01:4000 BattleCommand_DamageCalc\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\nwBattleMonAttack:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "effect_commands.asm").write_text(
                "BattleCommand_DamageCalc:\n\tld a, [wBattleMonAttack]\n\tld [wCurDamage], a\n\tret\n",
                encoding="utf-8",
            )
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "events": [
                            {
                                "access": "read",
                                "symbol": "wBattleMonAttack",
                                "address": "D142",
                                "value": "2A",
                                "pc_label": "BattleCommand_DamageCalc",
                                "source_file": "engine/battle/effect_commands.asm",
                            },
                            {
                                "access": "write",
                                "symbol": "wCurDamage",
                                "address": "D141",
                                "old_value": "0000",
                                "new_value": "002A",
                                "register_a": "2A",
                                "pc_label": "BattleCommand_DamageCalc",
                                "source_file": "engine/battle/effect_commands.asm",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = build_trace_index_report(
                traces=("trace.json",),
                watch_symbols=("wCurDamage",),
                symbols_path="test.sym",
                root=root,
            )
            (root / "trace_index.json").write_text(json.dumps(report), encoding="utf-8")
            explanation = build_explanation_report(
                reports=("trace_index.json",),
                symbols_path="test.sym",
                root=root,
            )

        relations = {link["relation"] for link in report["causal_links"]}
        attribution = report["reverse_attributions"][0]
        path_labels = {
            node["label"]
            for path in report["causal_paths"]
            for node in path.get("nodes", [])
        }
        explanation_labels = {
            node["label"]
            for path in explanation["paths"]
            for node in path.get("nodes", [])
        }

        self.assertTrue(report["valid"])
        self.assertEqual(report["reverse_attribution_count"], 1)
        self.assertIn("prior_read", relations)
        self.assertEqual(attribution["state"], "wCurDamage")
        self.assertEqual(attribution["contributors"][0]["state"], "wBattleMonAttack")
        self.assertIn("prior_read: wBattleMonAttack", path_labels)
        self.assertIn("wBattleMonAttack", explanation_labels)

    def test_explain_consumes_trace_index_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text("wCurDamage:: ds 2\n", encoding="utf-8")
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld [wCurDamage], a\n\tret\n",
                encoding="utf-8",
            )
            trace_index = root / "trace_index.json"
            trace_index.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_trace_index",
                        "events": [
                            {
                                "event_type": "watch_change",
                                "state_symbol": "wCurDamage",
                                "source_symbol": "BattleCommand_Test",
                                "pc_symbol": "BattleCommand_Test",
                                "pc_bank_address": "01:4000",
                                "before": "0000",
                                "after": "002A",
                                "source_file": "engine/battle.asm",
                                "confidence": 0.9,
                            }
                        ],
                        "causal_paths": [],
                    }
                ),
                encoding="utf-8",
            )

            report = build_explanation_report(
                reports=("trace_index.json",),
                symbols_path="test.sym",
                root=root,
            )

        labels = {
            node["label"]
            for path in report["paths"]
            for node in path.get("nodes", [])
        }

        self.assertTrue(report["valid"])
        self.assertGreaterEqual(report["dynamic_event_count"], 1)
        self.assertIn("wCurDamage", labels)
        self.assertIn("BattleCommand_Test", labels)

    def test_cli_trace_index_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "watch": "wCurDamage",
                        "old_hex": "0000",
                        "new_hex": "0001",
                        "pc_label": "BattleCommand_Test",
                    }
                ),
                encoding="utf-8",
            )
            out = root / "trace_index.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "trace-index",
                        "--trace",
                        str(trace),
                        "--watch-symbol",
                        "wCurDamage",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_trace_index")
        self.assertEqual(data["event_count"], 1)

    def test_cli_explain_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            symbols = root / "test.sym"
            symbols.write_text("01:D141 wCurDamage\n", encoding="utf-8")
            (root / "ram" / "wram.asm").write_text("wCurDamage:: ds 2\n", encoding="utf-8")
            out = root / "explain.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "explain",
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "wCurDamage",
                        "--symptom",
                        "damage spike",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_causal_explanation")
        self.assertGreaterEqual(data["path_count"], 1)

    def test_watch_plan_resolves_symbols_without_executing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = root / "test.gbc"
            rom.write_bytes(bytes(0x8000))
            symbols = root / "test.sym"
            symbols.write_text(
                "00:0000 NULL\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )

            report = build_watch_report(
                watch_symbols=("wCurDamage",),
                rom_path="test.gbc",
                symbols_path="test.sym",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertFalse(report["executed"])
        self.assertEqual(report["watches"][0]["bank_address"], "01:D141")
        self.assertEqual(report["watches"][0]["size"], 2)

    def test_watch_plan_treats_script_pointers_as_words(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text(
                "01:D160 wScriptBank\n01:D161 wScriptPos\n00:CF36 wScriptAfterPointer\n",
                encoding="utf-8",
            )

            report = build_watch_report(
                watch_symbols=("wScriptBank", "wScriptPos", "wScriptAfterPointer"),
                rom_path="test.gbc",
                symbols_path="test.sym",
                root=root,
            )

        sizes = {watch["name"]: watch["size"] for watch in report["watches"]}
        self.assertEqual(sizes["wScriptBank"], 1)
        self.assertEqual(sizes["wScriptPos"], 2)
        self.assertEqual(sizes["wScriptAfterPointer"], 2)

    def test_watch_plan_records_scheduled_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text("01:D160 wScriptBank\n", encoding="utf-8")

            report = build_watch_report(
                watch_symbols=("wScriptBank",),
                rom_path="test.gbc",
                symbols_path="test.sym",
                input_events=("0:a:4,45:start",),
                root=root,
            )

        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(
            [(event["frame"], event["button"], event["delay"]) for event in report["input_events"]],
            [(0, "a", 4), (45, "start", 8)],
        )

    def test_watch_plan_reports_missing_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text("00:0000 NULL\n", encoding="utf-8")

            report = build_watch_report(
                watch_symbols=("NoSuchSymbol",),
                rom_path="test.gbc",
                symbols_path="test.sym",
                root=root,
            )

        self.assertFalse(report["valid"])
        self.assertIn("NoSuchSymbol", report["errors"][0])

    def test_watch_event_cause_links_hit_to_static_writer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text("wCurDamage:: ds 2\n", encoding="utf-8")
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld [wCurDamage], a\n\tret\n",
                encoding="utf-8",
            )

            cause = build_watch_event_cause(
                watch_symbol="wCurDamage",
                pc_label="BattleCommand_Test+0x2",
                symbols_path="test.sym",
                root=root,
            )

        self.assertGreaterEqual(cause["candidate_count"], 1)
        self.assertEqual(cause["candidates"][0]["access"], "write")
        self.assertEqual(cause["candidates"][0]["source_file"], "engine/battle.asm")
        self.assertIn("tools.debugger localize --symbol wCurDamage", "\n".join(cause["commands"]))

    def test_watch_execution_records_dynamic_context_window(self) -> None:
        class FakeRegisters:
            A = 0x12
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0
            L = 0
            SP = 0xFFFE
            PC = 0x4000

        class FakeMemory:
            def __init__(self) -> None:
                self.values = {0xD141: 0x00, 0xD142: 0x00}

            def __getitem__(self, key):
                return self.values.get(key, 0)

            def __setitem__(self, key, value) -> None:
                self.values[key] = value

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()

            def tick(self, *_args) -> None:
                self.register_file.PC = 0x4003
                self.memory[0xD141] = 0x34

            def stop(self, save=False) -> None:
                self.stopped = True

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text(
                "00:D141 wCurDamage\n00:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text("wCurDamage:: ds 2\n", encoding="utf-8")
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld [wCurDamage], a\n\tret\n",
                encoding="utf-8",
            )

            with patch("tools.debugger.runtime_watch.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                report = build_watch_report(
                    watch_symbols=("wCurDamage",),
                    rom_path="test.gbc",
                    symbols_path="test.sym",
                    frames=1,
                    context_frames=2,
                    execute=True,
                    root=root,
                )

        event = report["events"][0]
        context = event["dynamic_context"]

        self.assertTrue(report["valid"])
        self.assertTrue(report["executed"])
        self.assertEqual(report["hit_count"], 1)
        self.assertEqual(report["dynamic_context_event_count"], 1)
        self.assertEqual(report["runtime_summary"]["initial"]["registers"]["register_pc"], "4000")
        self.assertEqual(report["runtime_summary"]["final"]["registers"]["register_sp"], "FFFE")
        self.assertEqual(event["old_hex"], "0000")
        self.assertEqual(event["new_hex"], "3400")
        self.assertEqual(context["context_frame_count"], 1)
        self.assertEqual(context["prelude"][0]["pc_bank_address"], "00:4000")
        self.assertEqual(context["after"]["pc_label"], "BattleCommand_Test+0x3")
        self.assertEqual(context["after"]["registers"]["register_pc"], "4003")
        self.assertEqual(context["after"]["watch_values"]["wCurDamage"], "3400")
        self.assertIn("tools.debugger trace-index --report <watch_report.json>", "\n".join(event["commands"]))

    def test_watch_execution_applies_scheduled_inputs(self) -> None:
        class FakeRegisters:
            A = 0
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0
            L = 0
            SP = 0xDFF0
            PC = 0x4000

        class FakeMemory:
            def __getitem__(self, _key):
                return 0

            def __setitem__(self, _key, _value) -> None:
                return None

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()
                self.buttons: list[tuple[str, int]] = []

            def button(self, name: str, delay: int = 8) -> None:
                self.buttons.append((name, delay))

            def tick(self, *_args) -> None:
                return None

            def stop(self, save=False) -> None:
                return None

        fake = FakePyBoy()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text("01:D160 wScriptBank\n", encoding="utf-8")

            with patch("tools.debugger.runtime_watch.trace_runtime.open_pyboy", return_value=fake):
                report = build_watch_report(
                    watch_symbols=("wScriptBank",),
                    rom_path="test.gbc",
                    symbols_path="test.sym",
                    input_events=("0:a:4",),
                    frames=1,
                    execute=True,
                    root=root,
                )

        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(fake.buttons, [("a", 4)])
        self.assertEqual(report["runtime_summary"]["applied_input_count"], 1)
        self.assertEqual(report["runtime_summary"]["applied_inputs"][0]["button"], "a")

    def test_watch_execution_can_boot_from_battery_save(self) -> None:
        class FakeRegisters:
            A = 0
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0
            L = 0
            SP = 0xDFF0
            PC = 0x4000

        class FakeMemory:
            def __getitem__(self, _key):
                return 0

            def __setitem__(self, _key, _value) -> None:
                return None

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()
                self.buttons: list[str] = []

            def button(self, name: str, delay: int = 8) -> None:
                self.buttons.append(name)

            def tick(self, *_args) -> None:
                return None

            def save_state(self, fh) -> None:
                fh.write(b"state")

            def stop(self, save=False) -> None:
                return None

        fake = FakePyBoy()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sav").write_bytes(bytes(0x8000))
            out_state = root / "booted.state"
            (root / "test.sym").write_text("01:D160 wScriptBank\n", encoding="utf-8")

            with patch("tools.debugger.runtime_watch.trace_runtime.open_pyboy", return_value=fake):
                report = build_watch_report(
                    watch_symbols=("wScriptBank",),
                    rom_path="test.gbc",
                    symbols_path="test.sym",
                    battery_save="test.sav",
                    out_initial_state="booted.state",
                    frames=0,
                    execute=True,
                    root=root,
                )
            out_state_exists = out_state.exists()

        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(fake.buttons, ["start", "a", "a", "a"])
        self.assertTrue(out_state_exists)
        self.assertTrue(report["boot_continue"])
        self.assertTrue(report["runtime_summary"]["battery_save_booted"])
        self.assertEqual(report["runtime_summary"]["out_initial_state"], "booted.state")

    def test_watch_reset_sentinel_records_reset_context_without_watch_symbol(self) -> None:
        class FakeRegisters:
            A = 0x12
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0
            L = 0
            SP = 0xDFF0
            PC = 0x4000

        class FakeMemory:
            def __init__(self) -> None:
                self.values = {
                    0xFFB8: 0x0E,
                    0xFFB9: 0x01,
                    (1, 0xD22D): 0x00,
                    (1, 0xD0F0): 0xA1,
                }

            def __getitem__(self, key):
                return self.values.get(key, 0)

            def __setitem__(self, key, value) -> None:
                self.values[key] = value

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()
                self.hooks = {}

            def hook_register(self, bank, pc, callback, context) -> None:
                self.hooks[(bank, pc)] = callback

            def hook_deregister(self, bank, pc) -> None:
                self.hooks.pop((bank, pc), None)

            def tick(self, *_args) -> None:
                self.register_file.PC = 0x0100
                callback = self.hooks.get((0, 0x0100))
                if callback is not None:
                    callback(None)

            def stop(self, save=False) -> None:
                self.stopped = True

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "00:0100 Start",
                        "00:0594 Reset",
                        "00:05AA _Start",
                        "00:FFB8 hROMBank",
                        "00:FFB9 hWRAMBank",
                        "01:D22D wBattleMode",
                        "01:D0F0 wTempWildMonSpecies",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with patch("tools.debugger.runtime_watch.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                report = build_watch_report(
                    watch_symbols=(),
                    rom_path="test.gbc",
                    symbols_path="test.sym",
                    frames=1,
                    context_frames=2,
                    execute=True,
                    reset_sentinel=True,
                    root=root,
                )

        event = report["reset_events"][0]

        self.assertTrue(report["valid"])
        self.assertTrue(report["executed"])
        self.assertEqual(report["hit_count"], 0)
        self.assertEqual(report["reset_event_count"], 1)
        self.assertEqual(event["pc_bank_address"], "00:0100")
        self.assertEqual(event["pc_label"], "Start")
        self.assertEqual(event["context_symbols"]["hWRAMBank"], "01")
        self.assertEqual(event["context_symbols"]["wTempWildMonSpecies"], "A1")
        self.assertEqual(event["dynamic_context"]["context_frame_count"], 1)

    def test_watch_execution_records_invalid_script_state(self) -> None:
        class FakeRegisters:
            A = 0
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0
            L = 0
            SP = 0xDFF0
            PC = 0x4000

        class FakeMemory:
            def __init__(self) -> None:
                self.values = {
                    (1, 0xD15E): 1,
                    (1, 0xD15F): 1,
                    (1, 0xD160): 0xB4,
                    (1, 0xD161): 0x02,
                    (1, 0xD162): 0x00,
                }

            def __getitem__(self, key):
                return self.values.get(key, 0)

            def __setitem__(self, key, value) -> None:
                self.values[key] = value

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()

            def tick(self, *_args) -> None:
                return None

            def stop(self, save=False) -> None:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:D15E wScriptMode",
                        "01:D15F wScriptRunning",
                        "01:D160 wScriptBank",
                        "01:D161 wScriptPos",
                        "01:4000 ScriptEvents",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with patch("tools.debugger.runtime_watch.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                report = build_watch_report(
                    watch_symbols=("wScriptBank", "wScriptPos"),
                    rom_path="test.gbc",
                    symbols_path="test.sym",
                    frames=0,
                    execute=True,
                    root=root,
                )

        event = report["events"][0]
        self.assertTrue(report["valid"])
        self.assertEqual(report["script_state_event_count"], 1)
        self.assertEqual(event["event_type"], "invalid_script_state")
        self.assertEqual(event["script"], "B4:0002")
        self.assertIn("below the switchable ROM window", "\n".join(event["reasons"]))

    def test_script_resume_gate_fails_unexecuted_watch_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "executed": False,
                        "reset_sentinel": False,
                        "watches": [],
                        "events": [],
                        "reset_event_count": 0,
                    }
                ),
                encoding="utf-8",
            )

            report = build_script_resume_gate_report(
                reports=("watch.json",),
                root=root,
            )

        finding_ids = {finding["id"] for finding in report["findings"]}

        self.assertFalse(report["passed"])
        self.assertIn("watch_not_executed", finding_ids)
        self.assertIn("watch_too_short", finding_ids)
        self.assertIn("watch_no_runtime_signal", finding_ids)
        self.assertIn("required_watch_symbol_missing", finding_ids)
        self.assertIn("pc_sp_snapshot_missing", finding_ids)

    def test_script_resume_gate_passes_complete_clean_watch_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "executed": True,
                        "frames": 60,
                        "hit_count": 1,
                        "reset_sentinel": True,
                        "watches": [
                            {"name": "wSeenTrainerBank", "found": True},
                            {"name": "wScriptAfterPointer", "found": True},
                            {"name": "wRunningTrainerBattleScript", "found": True},
                            {"name": "wScriptBank", "found": True},
                            {"name": "wScriptPos", "found": True},
                        ],
                        "runtime_summary": {
                            "initial": {"registers": {"register_pc": "4000", "register_sp": "DFF0"}},
                            "final": {"registers": {"register_pc": "5123", "register_sp": "DFE8"}},
                        },
                        "events": [
                            {
                                "event_type": "watch_change",
                                "watch": "wScriptPos",
                                "old_hex": "1050",
                                "new_hex": "2050",
                            }
                        ],
                        "reset_event_count": 0,
                    }
                ),
                encoding="utf-8",
            )

            report = build_script_resume_gate_report(
                reports=("watch.json",),
                root=root,
            )

        self.assertTrue(report["passed"], report["findings"])
        self.assertEqual(report["findings"][0]["id"], "watch_script_resume_ok")

    def test_script_resume_gate_rejects_trainer_bank_only_watch_activity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "executed": True,
                        "frames": 30,
                        "hit_count": 1,
                        "reset_sentinel": True,
                        "watches": [
                            {"name": "wSeenTrainerBank", "found": True},
                            {"name": "wScriptAfterPointer", "found": True},
                            {"name": "wRunningTrainerBattleScript", "found": True},
                            {"name": "wScriptBank", "found": True},
                            {"name": "wScriptPos", "found": True},
                        ],
                        "runtime_summary": {
                            "initial": {"registers": {"register_pc": "4000", "register_sp": "DFF0"}},
                            "final": {"registers": {"register_pc": "4010", "register_sp": "DFE8"}},
                        },
                        "events": [
                            {
                                "event_type": "watch_change",
                                "watch": "wSeenTrainerBank",
                                "old_hex": "00",
                                "new_hex": "07",
                            }
                        ],
                        "reset_event_count": 0,
                    }
                ),
                encoding="utf-8",
            )

            report = build_script_resume_gate_report(
                reports=("watch.json",),
                root=root,
            )

        finding_ids = {finding["id"] for finding in report["findings"]}

        self.assertFalse(report["passed"])
        self.assertIn("watch_no_script_resume_signal", finding_ids)

    def test_script_resume_gate_fails_runtime_state_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_report = root / "runtime_state.json"
            state_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_runtime_state_report",
                        "valid": True,
                        "passed": False,
                        "findings": [
                            {
                                "id": "invalid_script_pc",
                                "severity": 94,
                                "title": "Script VM is running from an invalid ROM address",
                                "evidence": ["wScriptBank:wScriptPos=B4:0002"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_script_resume_gate_report(
                reports=("runtime_state.json",),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertFalse(report["passed"])
        self.assertEqual(report["findings"][0]["id"], "invalid_script_pc")
        self.assertIn("B4:0002", report["findings"][0]["evidence"][0])

    def test_wram_ownership_reports_union_cotenants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "ram" / "wram.asm").write_text(
                "\n".join(
                    [
                        "UNION",
                        "wSeenTrainerBank:: db",
                        "wScriptAfterPointer:: dw",
                        "NEXTU",
                        "wMenuItemsList:: ds 16",
                        "ENDU",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_wram_ownership_report(
                symbols=("wSeenTrainerBank",),
                root=root,
            )

        owner = report["ownership"][0]
        self.assertTrue(report["valid"])
        self.assertEqual(owner["status"], "union_member")
        self.assertEqual(owner["same_arm_labels"], ["wSeenTrainerBank", "wScriptAfterPointer"])
        self.assertEqual(owner["other_union_arms"][0]["labels"], ["wMenuItemsList"])
        self.assertEqual(owner["risk"], "high")

    def test_wram_bank_hazard_report_flags_helper_call_and_cross_bank_pop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "engine" / "battle" / "ai" / "bad.asm"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "BadCall::",
                        "\tpush af",
                        "\tld a, 2",
                        "\tcall SetWRAMBank",
                        "\tpop af",
                        "\tret",
                        "",
                        "BadInline::",
                        "\tpush af",
                        "\tboss_ai_set_wram_bank 2",
                        "\tpop af",
                        "\tboss_ai_set_wram_bank 1",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_wram_bank_hazard_report(
                source_files=("engine/battle/ai/bad.asm",),
                root=root,
            )

        finding_types = {finding["type"] for finding in report["findings"]}

        self.assertTrue(report["valid"])
        self.assertFalse(report["passed"])
        self.assertIn("set_wram_bank_call", finding_types)
        self.assertIn("stack_bank_mismatch", finding_types)

    def test_wram_bank_hazard_report_accepts_current_observation_log_idiom(self) -> None:
        report = build_wram_bank_hazard_report(
            source_files=("engine/battle/ai/observation_log.asm",),
        )

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])

    def test_cli_watch_plan_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = root / "test.gbc"
            rom.write_bytes(bytes(0x8000))
            symbols = root / "test.sym"
            symbols.write_text("00:0000 NULL\n01:D141 wCurDamage\n", encoding="utf-8")
            out = root / "watch.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "watch",
                        "--rom",
                        str(rom),
                        "--symbols",
                        str(symbols),
                        "--watch-symbol",
                        "wCurDamage",
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_watch_report")
            self.assertFalse(data["executed"])

    def test_replay_plan_fingerprints_inputs_and_builds_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine" / "battle").mkdir(parents=True)
            rom = root / "test.gbc"
            rom.write_bytes(bytes(0x8000))
            symbols = root / "test.sym"
            symbols.write_text(
                "00:0000 NULL\n01:D141 wCurDamage\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            save_state = root / "state.state"
            save_state.write_bytes(b"opaque-state")
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "full_symbol": "BattleCommand_Test",
                        "source_file": "engine/battle/effect_commands.asm",
                    }
                ),
                encoding="utf-8",
            )
            scenario = root / "scenario.jsonl"
            scenario.write_text(
                json.dumps({"id": "case_one", "family": "unit"}) + "\n",
                encoding="utf-8",
            )
            changed = root / "engine" / "battle" / "effect_commands.asm"
            changed.write_text("BattleCommand_Test:\n\tret\n", encoding="utf-8")

            report = build_replay_plan(
                rom_path="test.gbc",
                symbols_path="test.sym",
                save_state="state.state",
                traces=("trace.json",),
                scenarios=("scenario.jsonl",),
                scenario_ids=("manual_case",),
                watch_symbols=("wCurDamage",),
                changed_files=("engine/battle/effect_commands.asm",),
                root=root,
            )

        commands = "\n".join(report["commands"])
        phases = {phase["phase"] for phase in report["phase_steps"]}

        self.assertTrue(report["valid"])
        self.assertEqual(report["artifact_manifest"]["artifact_count"], 6)
        self.assertIn("wCurDamage", report["replay_targets"]["watch_symbols"])
        self.assertIn("case_one", report["replay_targets"]["scenario_ids"])
        self.assertIn("manual_case", report["replay_targets"]["scenario_ids"])
        self.assertIn("ingest", phases)
        self.assertIn("setup", phases)
        self.assertIn("reproduce", phases)
        self.assertIn("prove", phases)
        self.assertIn("tools.debugger setup", commands)
        self.assertIn("tools.debugger watch", commands)
        self.assertIn("tools.debugger trace-instructions", commands)
        self.assertIn("tools.debugger coverage", commands)
        self.assertIn("tools.debugger minimize", commands)
        self.assertIn("--scenario-id manual_case", commands)
        self.assertIn("--trace trace.json", commands)
        self.assertIn("--out-trace .local\\tmp\\debugger_replay_minimized_trace.json", commands)

    def test_replay_plan_derives_watch_targets_from_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "events": [
                            {
                                "watch": "wEnemyAIMoveScores",
                                "pc_label": "BossAI_SelectMove",
                                "pc_bank_address": "03:4123",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_replay_plan(reports=("watch.json",), root=root)

        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("wEnemyAIMoveScores", report["replay_targets"]["watch_symbols"])
        self.assertIn("BossAI_SelectMove", report["replay_targets"]["symbols"])
        self.assertIn("tools.debugger localize --report watch.json", commands)
        self.assertIn("tools.debugger impact --report watch.json", commands)
        self.assertIn("tools.debugger trace-instructions", commands)
        self.assertIn("--report watch.json", commands)

    def test_replay_and_localize_consume_content_rom_mirrors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gfx").mkdir()
            (root / "gfx" / "footprints.asm").write_text("Footprints:\n\tret\n", encoding="utf-8")
            (root / "pokegold.sym").write_text("3E:5302 Footprints\n", encoding="utf-8")
            content_report = root / "content.json"
            content_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_mirror",
                        "rom_mirrors": [
                            {
                                "type": "incbin_table_rom_bytes",
                                "status": "passed",
                                "title": "Footprints ROM bytes match",
                                "source_file": "gfx/footprints.asm",
                                "related_files": ["gfx/footprints.asm", "gfx/footprints/bulbasaur.1bpp"],
                                "related_symbols": ["Footprints"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            replay = build_replay_plan(reports=("content.json",), root=root)
            localized = build_localization_plan(reports=("content.json",), root=root)

        replay_commands = "\n".join(replay["commands"])
        localized_commands = "\n".join(localized["commands"])
        candidate_ids = {candidate["id"] for candidate in localized["candidates"]}

        self.assertTrue(replay["valid"])
        self.assertIn("Footprints", replay["replay_targets"]["symbols"])
        self.assertIn("gfx/footprints.asm", replay["replay_targets"]["source_files"])
        self.assertIn("--symbol Footprints", replay_commands)
        self.assertTrue(localized["valid"])
        self.assertIn("Footprints", candidate_ids)
        self.assertIn("gfx/footprints.asm", candidate_ids)
        self.assertIn("provenance --symbol Footprints", localized_commands)

    def test_replay_plan_uses_existing_discovered_save_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text("01:D141 wCurDamage\n", encoding="utf-8")
            (root / "case.state").write_bytes(b"state")
            (root / "scenarios.jsonl").write_text(
                json.dumps({"id": "case_one", "state": "case.state"}) + "\n",
                encoding="utf-8",
            )

            report = build_replay_plan(
                rom_path="test.gbc",
                symbols_path="test.sym",
                scenarios=("scenarios.jsonl",),
                scenario_ids=("case_one",),
                watch_symbols=("wCurDamage",),
                root=root,
            )

        commands = "\n".join(report["commands"])
        selected = report["save_state_discovery"]["selected"]

        self.assertTrue(report["valid"])
        self.assertEqual(report["save_state"], "")
        self.assertEqual(report["effective_save_state"], "case.state")
        self.assertEqual(selected["scenario_id"], "case_one")
        self.assertTrue(selected["exists"])
        self.assertIn("save_state", {artifact["kind"] for artifact in report["artifact_manifest"]["artifacts"]})
        self.assertIn("--save-state case.state", commands)
        self.assertIn("case.state", report["setup_plan"]["effective_save_state"])

    def test_replay_plan_consumes_content_state_materialization_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pokegold.gbc").write_bytes(bytes(0x8000))
            (root / "pokegold.sym").write_text(
                "01:DA00 wMapGroup\n01:DA01 wMapNumber\n01:DA02 wYCoord\n01:DA03 wXCoord\n",
                encoding="utf-8",
            )
            (root / "patched.state").write_bytes(b"patched-state")
            content_state_report = root / "content_state.json"
            content_state_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "executed": True,
                        "out_state": "patched.state",
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0000",
                                "precondition_kind": "map_position",
                                "source_file": "maps/UnitMap.asm",
                                "status": "ready",
                                "patches": [
                                    {
                                        "symbol": "wMapGroup",
                                        "value": 24,
                                        "value_hex": "18",
                                        "bank_address": "01:DA00",
                                    }
                                ],
                            }
                        ],
                        "execution": {
                            "executed": True,
                            "out_state": "patched.state",
                            "applied_patches": [
                                {
                                    "symbol": "wMapGroup",
                                    "value": 24,
                                    "value_hex": "18",
                                    "observed": 24,
                                    "observed_hex": "18",
                                    "verified": True,
                                    "bank_address": "01:DA00",
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_replay_plan(reports=("content_state.json",), root=root)

        commands = "\n".join(report["commands"])
        selected = report["save_state_discovery"]["selected"]

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "patched.state")
        self.assertEqual(selected["key"], "out_state")
        self.assertTrue(selected["exists"])
        self.assertIn("wMapGroup", report["replay_targets"]["watch_symbols"])
        self.assertIn("content_scenario_1_0000", report["replay_targets"]["scenario_ids"])
        self.assertIn("maps/UnitMap.asm", report["replay_targets"]["source_files"])
        self.assertIn("--save-state patched.state", commands)
        self.assertIn("--scenario-id content_scenario_1_0000", commands)

    def test_replay_plan_consumes_state_space_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pokegold.gbc").write_bytes(bytes(0x8000))
            (root / "pokegold.sym").write_text(
                "01:4000 ScriptEvents\n01:DA10 wScriptBank\n01:DA11 wScriptPos\n",
                encoding="utf-8",
            )
            (root / "patched.state").write_bytes(b"patched-state")
            (root / "state_space.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_state_space",
                        "valid": True,
                        "executed": True,
                        "scenario_id": "script_entry_1",
                        "source_files": ["maps/UnitMap.asm"],
                        "out_state": "patched.state",
                        "watch_symbols": ["wScriptPos"],
                        "state_space": {
                            "scenario_ids": ["script_entry_1"],
                            "source_files": ["maps/UnitMap.asm"],
                            "out_state": "patched.state",
                            "patches": [
                                {
                                    "symbol": "wScriptBank",
                                    "base_symbol": "wScriptBank",
                                    "value": 2,
                                    "value_hex": "02",
                                    "scenario_id": "script_entry_1",
                                    "source_file": "maps/UnitMap.asm",
                                },
                                {
                                    "symbol": "wScriptPos",
                                    "base_symbol": "wScriptPos",
                                    "value": 80,
                                    "value_hex": "50",
                                    "scenario_id": "script_entry_1",
                                    "source_file": "maps/UnitMap.asm",
                                },
                            ],
                        },
                        "execution": {
                            "executed": True,
                            "out_state": "patched.state",
                            "applied_patches": [
                                {
                                    "symbol": "wScriptPos",
                                    "base_symbol": "wScriptPos",
                                    "value": 80,
                                    "value_hex": "50",
                                    "scenario_id": "script_entry_1",
                                    "source_file": "maps/UnitMap.asm",
                                    "applied": True,
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_replay_plan(reports=("state_space.json",), root=root)

        commands = "\n".join(report["commands"])
        selected = report["save_state_discovery"]["selected"]

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "patched.state")
        self.assertTrue(selected["exists"])
        self.assertIn("wScriptBank", report["replay_targets"]["watch_symbols"])
        self.assertIn("wScriptPos", report["replay_targets"]["watch_symbols"])
        self.assertIn("script_entry_1", report["replay_targets"]["scenario_ids"])
        self.assertIn("maps/UnitMap.asm", report["replay_targets"]["source_files"])
        self.assertIn("--save-state patched.state", commands)
        self.assertIn("--scenario-id script_entry_1", commands)

    def test_replay_plan_does_not_use_missing_discovered_save_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text("01:D141 wCurDamage\n", encoding="utf-8")
            (root / "scenarios.jsonl").write_text(
                json.dumps({"id": "case_one", "state": "missing.state"}) + "\n",
                encoding="utf-8",
            )

            report = build_replay_plan(
                rom_path="test.gbc",
                symbols_path="test.sym",
                scenarios=("scenarios.jsonl",),
                scenario_ids=("case_one",),
                watch_symbols=("wCurDamage",),
                root=root,
            )

        commands = "\n".join(report["commands"])
        candidates = report["save_state_discovery"]["candidates"]

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "")
        self.assertEqual(report["save_state_discovery"]["selected"], {})
        self.assertEqual(candidates[0]["path"], "missing.state")
        self.assertFalse(candidates[0]["exists"])
        self.assertNotIn("--save-state missing.state", commands)

    def test_replay_plan_does_not_treat_query_flags_as_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_index = root / "trace_index.json"
            trace_index.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_trace_index",
                        "valid": True,
                        "query": {
                            "active": True,
                            "symbols": [],
                            "source_files": ["maps/NewBarkTown.asm"],
                        },
                        "events": [],
                    }
                ),
                encoding="utf-8",
            )

            report = build_replay_plan(reports=("trace_index.json",), root=root)

        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertNotIn("True", report["replay_targets"]["symbols"])
        self.assertNotIn("--symbol True", commands)
        self.assertIn("maps/NewBarkTown.asm", report["replay_targets"]["source_files"])

    def test_replay_plan_uses_embedded_next_step_instead_of_impact_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            investigation = root / "investigate.json"
            investigation.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_investigation_run",
                        "valid": True,
                        "symptom": "boss selected wrong switch",
                        "symptom_only_next_step": build_next_step(symptom="boss selected wrong switch"),
                        "top_impact": [
                            {
                                "type": "fuzz_campaign",
                                "title": "Fuzz campaign: fuzz_boss_ai_generated_policy",
                                "impact_score": 100,
                                "related_symbols": [
                                    "Broad",
                                    "Fuzz",
                                    "Python",
                                    "ROM-materialized",
                                    "boss_ai",
                                    "fuzz_boss_ai_generated_policy",
                                    "proof_level",
                                ],
                                "related_files": ["engine/battle/ai/boss_policy_move.asm"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_replay_plan(reports=("investigate.json",), root=root)

        commands = "\n".join(report["commands"])
        targets = report["replay_targets"]
        self.assertTrue(report["valid"])
        self.assertIn("BossAI_SwitchOrTryItem", targets["symbols"])
        self.assertIn("wEnemySwitchMonIndex", targets["watch_symbols"])
        self.assertIn("wEnemySwitchMonParam", targets["watch_symbols"])
        self.assertIn("wEnemyAIMoveScores", targets["watch_symbols"])
        self.assertIn("engine/battle/ai/boss_policy_switch.asm", targets["source_files"])
        self.assertIn("--symbol BossAI_SwitchOrTryItem", commands)
        self.assertIn("--watch-symbol wEnemySwitchMonIndex", commands)
        self.assertNotIn("Broad", targets["symbols"])
        self.assertNotIn("Fuzz", targets["symbols"])
        self.assertNotIn("Python", targets["symbols"])
        self.assertNotIn("ROM-materialized", targets["symbols"])
        self.assertNotIn("--symbol Broad", commands)

    def test_cli_replay_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "replay.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "replay",
                        "--symbol",
                        "wCurDamage",
                        "--symptom",
                        "damage spike",
                        "--scenario-id",
                        "content_scenario_1_0000",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_replay_plan")
        self.assertIn("wCurDamage", data["replay_targets"]["watch_symbols"])
        self.assertIn("content_scenario_1_0000", data["replay_targets"]["scenario_ids"])

    def test_setup_plan_builds_damage_trigger_commands(self) -> None:
        report = build_setup_plan(
            symbols=("BattleCommand_DamageCalc",),
            watch_symbols=("wCurDamage",),
            out_scenarios=".local\\tmp\\damage_setup.jsonl",
        )

        commands = "\n".join(report["commands"])
        coverage = report["trigger_coverage"]
        target = coverage["targets"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(report["surfaces"], ["damage"])
        self.assertTrue(report["state_requirements"]["requires_positioned_state"])
        self.assertEqual(coverage["planned_target_count"], 1)
        self.assertEqual(target["status"], "planned")
        self.assertEqual(target["state_status"], "synthesizable")
        self.assertIn("state:synthesizable", target["blockers"])
        self.assertEqual(report["targets"][0]["state_synthesis_recipes"][0]["id"], "damage_snapshot_ring_runtime")
        self.assertTrue(report["targets"][0]["state_synthesis_recipes"][0]["runnable"])
        self.assertIn("no save state was supplied", "\n".join(report["warnings"]))
        self.assertIn("tools.debugger generate --family damage", commands)
        self.assertIn("tools.damage_debugger.replay", commands)
        self.assertIn("trace-instructions", commands)
        self.assertIn("--require-hit", commands)
        self.assertIn("--watch-symbol wCurDamage", commands)

    def test_setup_plan_builds_content_trigger_commands(self) -> None:
        report = build_setup_plan(
            changed_files=("maps/UnitMap.asm",),
            out_scenarios=".local\\tmp\\content_setup.jsonl",
        )

        commands = "\n".join(report["commands"])
        coverage = report["trigger_coverage"]
        target = coverage["targets"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(report["surfaces"], ["content_static"])
        self.assertFalse(report["state_requirements"]["requires_positioned_state"])
        self.assertEqual(coverage["planned_target_count"], 1)
        self.assertEqual(target["state_status"], "not-required")
        self.assertEqual(target["state_recipe_status"]["status"], "ready")
        self.assertIn("trigger:blocked", target["blockers"])
        self.assertIn("content-mirror --source-file maps/UnitMap.asm", commands)
        self.assertIn("content-scenarios --source-file maps/UnitMap.asm", commands)
        self.assertIn("--scenario .local\\tmp\\content_setup.jsonl", commands)
        self.assertIn("--scenario-id <id>", commands)
        self.assertIn("--symbol ReadMapEvents", commands)
        self.assertIn("--symbol CheckFacingBGEvent", commands)
        self.assertIn("--watch-symbol wMapGroup", commands)

    def test_setup_plan_uses_content_scenario_report_preconditions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "UnitMap_MapEvents:",
                        "\tdef_bg_events",
                        "\tbg_event 4, 5, BGEVENT_READ, UnitMapSign",
                        "UnitMapSign:",
                        "\tjumptext UnitMapText",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            scenario_report = build_content_scenario_report(
                source_files=("maps/UnitMap.asm",),
                out_scenarios="content.jsonl",
                root=root,
            )
            (root / "content.json").write_text(json.dumps(scenario_report), encoding="utf-8")

            report = build_setup_plan(
                reports=("content.json",),
                out_scenarios="content.jsonl",
                root=root,
            )

        commands = "\n".join(report["commands"])
        recipes = report["targets"][0]["state_synthesis_recipes"]
        precondition_recipe = next(item for item in recipes if item["id"] == "content_runtime_preconditions")
        precondition = precondition_recipe["preconditions"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(report["surfaces"], ["content_static"])
        self.assertTrue(report["state_requirements"]["requires_positioned_state"])
        self.assertIn("content_scenario_1_0000", report["state_requirements"]["content_scenario_ids"])
        self.assertIn("content_scenario_1_0001", report["state_requirements"]["content_scenario_ids"])
        self.assertEqual(report["trigger_coverage"]["targets"][0]["state_status"], "partially-synthesizable")
        self.assertIn("state:partially-synthesizable", report["trigger_coverage"]["targets"][0]["blockers"])
        self.assertIn("--scenario-id content_scenario_1_0000", commands)
        self.assertNotIn("--scenario-id <id>", commands)
        self.assertIn("--symbol CheckFacingBGEvent", commands)
        self.assertIn("--symbol UnitMapSign", commands)
        self.assertIn("--watch-symbol wMapGroup", commands)
        self.assertIn("tools.debugger expect --report content.json", commands)
        self.assertIn("precondition=map_position,scenario=content_scenario_1_0000", commands)
        self.assertIn("tools.debugger content-state", commands)
        self.assertIn("--base-save-state <base-state>", commands)
        self.assertNotIn("contains=<expected_text>", commands)
        self.assertEqual(precondition["kind"], "map_position")
        self.assertEqual(precondition["scenario_id"], "content_scenario_1_0000")
        self.assertEqual(precondition["values"]["script"], "UnitMapSign")
        self.assertIn("wMapGroup", precondition["watch_symbols"])

    def test_setup_content_preconditions_are_covered_with_discovered_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / ".local" / "tmp").mkdir(parents=True)
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "UnitMap_MapEvents:",
                        "\tdef_bg_events",
                        "\tbg_event 4, 5, BGEVENT_READ, UnitMapSign",
                        "UnitMapSign:",
                        "\tjumptext UnitMapText",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "case.state").write_bytes(b"state")
            scenario = {
                "id": "content_scenario_1_0000",
                "kind": "unified_debugger_content_scenario",
                "scenario_type": "map_bg_event",
                "source_file": "maps/UnitMap.asm",
                "state": "case.state",
                "state_preconditions": [
                    {
                        "id": "map_bg_event_position",
                        "kind": "map_position",
                        "values": {"script": "UnitMapSign", "source_file": "maps/UnitMap.asm"},
                        "watch_symbols": ["wMapGroup", "wMapNumber", "wXCoord", "wYCoord"],
                    }
                ],
                "runtime_targets": {
                    "trace_symbols": ["CheckFacingBGEvent"],
                    "script_symbols": ["UnitMapSign"],
                    "watch_symbols": ["wMapGroup"],
                },
            }
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [scenario],
                    }
                ),
                encoding="utf-8",
            )
            (root / ".local" / "tmp" / "content_setup.jsonl").write_text(
                json.dumps(scenario) + "\n",
                encoding="utf-8",
            )

            report = build_setup_plan(
                reports=("content.json",),
                out_scenarios=".local\\tmp\\content_setup.jsonl",
                root=root,
            )

        target = report["trigger_coverage"]["targets"][0]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "case.state")
        self.assertTrue(report["state_requirements"]["requires_positioned_state"])
        self.assertTrue(report["state_requirements"]["save_state_discovered"])
        self.assertEqual(target["state_status"], "discovered")
        self.assertEqual(target["status"], "covered")
        self.assertEqual(target["blockers"], [])
        self.assertIn("--save-state case.state", commands)
        self.assertIn("tools.debugger content-state", commands)
        self.assertIn("--base-save-state case.state", commands)
        self.assertIn("--execute", commands)
        self.assertIn("tools.debugger expect --report content.json", commands)

    def test_content_state_materializes_map_precondition_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data" / "maps").mkdir(parents=True)
            (root / "data" / "maps" / "maps.asm").write_text(
                "\n".join(
                    [
                        "MapGroup_NewBark:",
                        "\ttable_width MAP_LENGTH",
                        "\tmap Route29, TILESET_JOHTO, ROUTE, LANDMARK_ROUTE_29, MUSIC_ROUTE_29, FALSE, PALETTE_AUTO, FISHGROUP_SHORE",
                        "\tmap NewBarkTown, TILESET_JOHTO, TOWN, LANDMARK_NEW_BARK_TOWN, MUSIC_NEW_BARK_TOWN, FALSE, PALETTE_AUTO, FISHGROUP_OCEAN",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:DA00 wMapGroup",
                        "01:DA01 wMapNumber",
                        "01:DA02 wYCoord",
                        "01:DA03 wXCoord",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "map_warp",
                                "source_file": "maps/NewBarkTown.asm",
                                "state_preconditions": [
                                    {
                                        "id": "map_warp_position",
                                        "kind": "map_position",
                                        "values": {
                                            "map_label": "NewBarkTown_MapEvents",
                                            "source_file": "maps/NewBarkTown.asm",
                                            "x": 6,
                                            "y": 3,
                                        },
                                        "watch_symbols": ["wMapGroup", "wMapNumber", "wXCoord", "wYCoord"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_content_state_report(
                reports=("content.json",),
                scenario_ids=("content_scenario_1_0000",),
                symbols_path="test.sym",
                root=root,
            )

        patches = {
            patch["symbol"]: patch
            for patch in report["materializations"][0]["patches"]
        }

        self.assertTrue(report["valid"])
        self.assertEqual(report["patch_count"], 4)
        self.assertEqual(report["materializations"][0]["status"], "ready")
        self.assertEqual(report["materializations"][0]["map_resolution"]["map_group"], 1)
        self.assertEqual(report["materializations"][0]["map_resolution"]["map_number"], 2)
        self.assertEqual(patches["wMapGroup"]["value"], 1)
        self.assertEqual(patches["wMapNumber"]["value"], 2)
        self.assertEqual(patches["wXCoord"]["value"], 6)
        self.assertEqual(patches["wYCoord"]["value"], 3)

    def test_content_state_materializes_script_entry_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "02:5000 UnitScript",
                        "01:DA10 wScriptBank",
                        "01:DA11 wScriptPos",
                        "01:DA13 wScriptRunning",
                        "01:DA14 wScriptMode",
                        "01:DA15 wScriptStackSize",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "script_command_stream",
                                "source_file": "maps/UnitMap.asm",
                                "label": "UnitScript",
                                "state_preconditions": [
                                    {
                                        "id": "script_engine_entry",
                                        "kind": "script_entry",
                                        "values": {
                                            "script_label": "UnitScript",
                                            "source_file": "maps/UnitMap.asm",
                                        },
                                        "watch_symbols": ["wScriptBank", "wScriptPos"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_content_state_report(
                reports=("content.json",),
                scenario_ids=("content_scenario_1_0000",),
                symbols_path="test.sym",
                root=root,
            )

        materialization = report["materializations"][0]
        patches = {patch["symbol"]: patch for patch in materialization["patches"]}
        commands = "\n".join(materialization["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["error_count"], 0)
        self.assertEqual(report["patch_count"], 6)
        self.assertEqual(materialization["status"], "ready")
        self.assertEqual(materialization["precondition_kind"], "script_entry")
        self.assertEqual(materialization["script_resolution"]["bank_address"], "02:5000")
        self.assertEqual(patches["wScriptBank"]["value"], 0x02)
        self.assertEqual(patches["wScriptPos"]["value"], 0x00)
        self.assertEqual(patches["wScriptPos+1"]["value"], 0x50)
        self.assertEqual(patches["wScriptPos+1"]["address"], 0xDA12)
        self.assertEqual(patches["wScriptRunning"]["value"], 0xFF)
        self.assertEqual(patches["wScriptMode"]["value"], 0x01)
        self.assertEqual(patches["wScriptStackSize"]["value"], 0x00)
        self.assertIn("--symbol ScriptEvents --symbol RunScriptCommand", commands)
        self.assertIn("--watch-symbol wScriptPos --watch-symbol wScriptVar", commands)

    def test_content_state_materializes_movement_entry_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "02:6000 UnitMovement",
                        "01:DB00 wMovementObject",
                        "01:DB01 wMovementDataBank",
                        "01:DB02 wMovementDataAddress",
                        "01:DB04 wMovementPointer",
                        "01:DB06 wScriptMode",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "movement_data",
                                "source_file": "scripts/unit_movement.asm",
                                "label": "UnitMovement",
                                "state_preconditions": [
                                    {
                                        "id": "movement_engine_entry",
                                        "kind": "movement_entry",
                                        "values": {
                                            "movement_label": "UnitMovement",
                                            "source_file": "scripts/unit_movement.asm",
                                            "object_id": 0,
                                        },
                                        "watch_symbols": ["wMovementPointer", "wMovementObject"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_content_state_report(
                reports=("content.json",),
                scenario_ids=("content_scenario_1_0000",),
                symbols_path="test.sym",
                root=root,
            )

        materialization = report["materializations"][0]
        patches = {patch["symbol"]: patch for patch in materialization["patches"]}
        commands = "\n".join(materialization["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["error_count"], 0)
        self.assertEqual(report["patch_count"], 7)
        self.assertEqual(materialization["status"], "ready")
        self.assertEqual(materialization["precondition_kind"], "movement_entry")
        self.assertEqual(materialization["movement_resolution"]["bank_address"], "02:6000")
        self.assertEqual(patches["wMovementObject"]["value"], 0x00)
        self.assertEqual(patches["wMovementDataBank"]["value"], 0x02)
        self.assertEqual(patches["wMovementDataAddress"]["value"], 0x00)
        self.assertEqual(patches["wMovementDataAddress+1"]["value"], 0x60)
        self.assertEqual(patches["wMovementDataAddress+1"]["address"], 0xDB03)
        self.assertEqual(patches["wMovementPointer"]["value"], 0x00)
        self.assertEqual(patches["wMovementPointer+1"]["value"], 0x60)
        self.assertEqual(patches["wMovementPointer+1"]["address"], 0xDB05)
        self.assertEqual(patches["wScriptMode"]["value"], 0x02)
        self.assertIn("--symbol ApplyMovement --symbol GetMovementData --symbol HandleMovementData", commands)
        self.assertIn("--watch-symbol wMovementDataAddress --watch-symbol wMovementPointer", commands)

    def test_content_state_plans_audio_and_asset_runtime_proofs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("00:0000 NULL\n", encoding="utf-8")
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "audio_channel_block",
                                "source_file": "audio/unit.asm",
                                "label": "Music_Unit",
                                "state_preconditions": [
                                    {
                                        "id": "audio_channel_runtime",
                                        "kind": "audio_engine_entry",
                                        "values": {
                                            "music_label": "Music_Unit",
                                            "source_file": "audio/unit.asm",
                                            "channel_count": 2,
                                        },
                                    }
                                ],
                            },
                            {
                                "id": "content_scenario_1_0001",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "asset_materialization",
                                "source_file": "gfx/unit.asm",
                                "label": "UnitGraphic",
                                "state_preconditions": [
                                    {
                                        "id": "asset_loader_runtime",
                                        "kind": "asset_loader_entry",
                                        "values": {
                                            "asset": "gfx/unit.2bpp",
                                            "source_file": "gfx/unit.asm",
                                            "label": "UnitGraphic",
                                        },
                                    }
                                ],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_content_state_report(
                reports=("content.json",),
                symbols_path="test.sym",
                root=root,
            )

        materializations = {
            item["precondition_kind"]: item
            for item in report["materializations"]
        }
        audio_commands = "\n".join(materializations["audio_engine_entry"]["commands"])
        asset_commands = "\n".join(materializations["asset_loader_entry"]["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["patch_count"], 0)
        self.assertEqual(report["materialization_count"], 2)
        self.assertEqual(materializations["audio_engine_entry"]["status"], "planned")
        self.assertIn("wMusicID", materializations["audio_engine_entry"]["watch_symbols"])
        self.assertIn("--symbol PlayMusic --symbol _PlayMusic", audio_commands)
        self.assertIn("--watch-symbol wMusicID", audio_commands)
        self.assertEqual(materializations["asset_loader_entry"]["status"], "planned")
        self.assertIn("wRequested2bppSource", materializations["asset_loader_entry"]["watch_symbols"])
        self.assertIn("--symbol Request2bpp --symbol Get1bpp --symbol Decompress", asset_commands)
        self.assertIn("--watch-symbol wRequested2bppSource", asset_commands)

    def test_content_state_execute_patches_and_writes_state(self) -> None:
        class FakeMemory:
            def __init__(self) -> None:
                self.values: dict[Any, int] = {0xFF70: 1}

            def __getitem__(self, key: Any) -> int:
                return self.values.get(key, 0)

            def __setitem__(self, key: Any, value: int) -> None:
                self.values[key] = int(value) & 0xFF

        class FakePyBoy:
            def __init__(self) -> None:
                self.memory = FakeMemory()
                self.loaded = False
                self.stopped = False

            def load_state(self, _fh: Any) -> None:
                self.loaded = True

            def save_state(self, fh: Any) -> None:
                fh.write(b"patched-state")

            def stop(self, save: bool = False) -> None:
                self.stopped = True

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data" / "maps").mkdir(parents=True)
            (root / "data" / "maps" / "maps.asm").write_text(
                "MapGroup_NewBark:\n\tmap NewBarkTown, TILESET_JOHTO, TOWN, LANDMARK_NEW_BARK_TOWN, MUSIC_NEW_BARK_TOWN, FALSE, PALETTE_AUTO, FISHGROUP_OCEAN\n",
                encoding="utf-8",
            )
            (root / "test.sym").write_text(
                "01:DA00 wMapGroup\n01:DA01 wMapNumber\n01:DA02 wYCoord\n01:DA03 wXCoord\n",
                encoding="utf-8",
            )
            (root / "rom.gbc").write_bytes(b"rom")
            (root / "base.state").write_bytes(b"base")
            out_state = root / "patched.state"
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "map_bg_event",
                                "source_file": "maps/NewBarkTown.asm",
                                "state_preconditions": [
                                    {
                                        "id": "map_bg_event_position",
                                        "kind": "map_position",
                                        "values": {"map_label": "NewBarkTown_MapEvents", "x": 4, "y": 5},
                                        "watch_symbols": ["wMapGroup"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            fake = FakePyBoy()

            with patch("tools.debugger.content_state.trace_runtime.open_pyboy", return_value=fake):
                report = build_content_state_report(
                    reports=("content.json",),
                    symbols_path="test.sym",
                    rom_path="rom.gbc",
                    base_save_state="base.state",
                    out_state="patched.state",
                    execute=True,
                    root=root,
                )

            written = out_state.read_bytes()

        self.assertTrue(report["valid"])
        self.assertTrue(report["executed"])
        self.assertEqual(report["execution"]["patch_count"], 4)
        self.assertEqual(written, b"patched-state")
        self.assertTrue(fake.loaded)
        self.assertTrue(fake.stopped)

    def test_state_space_builds_generic_patch_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "01:DA10 wScriptBank\n01:DA11 wScriptPos\n01:DA13 wScriptMode\n",
                encoding="utf-8",
            )

            report = build_state_space_report(
                patches=("wScriptBank=0x02", "wScriptPos=0x50,0x40", "wScriptMode=1"),
                watch_symbols=("wScriptPos",),
                scenario_id="script_entry_1",
                source_files=("maps/UnitMap.asm",),
                symbols_path="test.sym",
                report_path="state_space.json",
                root=root,
            )

        patches = report["state_space"]["patches"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertFalse(report["executed"])
        self.assertEqual(report["patch_count"], 4)
        self.assertEqual([patch["symbol"] for patch in patches], ["wScriptBank", "wScriptPos", "wScriptPos+1", "wScriptMode"])
        self.assertEqual(patches[1]["bank_address"], "01:DA11")
        self.assertEqual(patches[2]["bank_address"], "01:DA12")
        self.assertEqual(patches[2]["value_hex"], "40")
        self.assertIn("wScriptPos", report["watch_symbols"])
        self.assertIn("tools.debugger expect --report state_space.json --expect state-patch=wScriptBank,scenario=script_entry_1,value=0x02", commands)
        self.assertIn("tools.debugger minimize --report state_space.json", commands)
        self.assertIn("tools.debugger trace-instructions --report state_space.json --scenario-id script_entry_1", commands)

    def test_cli_state_space_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:DA11 wScriptPos\n", encoding="utf-8")
            out = root / "state_space.json"

            with patch("tools.debugger.catalog.ROOT", root), redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "state-space",
                        "--patch",
                        "wScriptPos=0x50",
                        "--symbols",
                        str(root / "test.sym"),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_state_space")
        self.assertEqual(data["patch_count"], 1)
        self.assertEqual(data["state_space"]["patches"][0]["symbol"], "wScriptPos")

    def test_state_space_execute_patches_and_writes_state(self) -> None:
        class FakeMemory:
            def __init__(self) -> None:
                self.values: dict[Any, int] = {0xFF70: 1}

            def __getitem__(self, key: Any) -> int:
                return self.values.get(key, 0)

            def __setitem__(self, key: Any, value: int) -> None:
                self.values[key] = int(value) & 0xFF

        class FakePyBoy:
            def __init__(self) -> None:
                self.memory = FakeMemory()
                self.loaded = False
                self.stopped = False

            def load_state(self, _fh: Any) -> None:
                self.loaded = True

            def save_state(self, fh: Any) -> None:
                fh.write(b"patched-state")

            def stop(self, save: bool = False) -> None:
                self.stopped = True

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:DA11 wScriptPos\n", encoding="utf-8")
            (root / "rom.gbc").write_bytes(b"rom")
            (root / "base.state").write_bytes(b"base")
            out_state = root / "patched.state"
            fake = FakePyBoy()

            with patch("tools.debugger.state_space.trace_runtime.open_pyboy", return_value=fake):
                report = build_state_space_report(
                    patches=("wScriptPos=0x50",),
                    symbols_path="test.sym",
                    rom_path="rom.gbc",
                    base_save_state="base.state",
                    out_state="patched.state",
                    execute=True,
                    root=root,
                )

            written = out_state.read_bytes()

        self.assertTrue(report["valid"])
        self.assertTrue(report["executed"])
        self.assertEqual(report["execution"]["patch_count"], 1)
        self.assertEqual(report["state_space"]["patches"][0]["observed_hex"], "50")
        self.assertTrue(report["state_space"]["patches"][0]["verified"])
        self.assertIn("--execute-state-patches", "\n".join(report["commands"]))
        self.assertEqual(written, b"patched-state")
        self.assertTrue(fake.loaded)
        self.assertTrue(fake.stopped)

    def test_rank_impact_and_visualization_consume_state_space_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "patched.state").write_bytes(b"patched-state")
            (root / "state_space.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_state_space",
                        "valid": True,
                        "executed": True,
                        "scenario_id": "script_entry_1",
                        "source_files": ["maps/UnitMap.asm"],
                        "out_state": "patched.state",
                        "state_space": {
                            "scenario_ids": ["script_entry_1"],
                            "source_files": ["maps/UnitMap.asm"],
                            "out_state": "patched.state",
                            "patches": [
                                {
                                    "symbol": "wScriptPos",
                                    "base_symbol": "wScriptPos",
                                    "value": 80,
                                    "value_hex": "50",
                                    "bank_address": "01:DA11",
                                    "scenario_id": "script_entry_1",
                                    "source_file": "maps/UnitMap.asm",
                                }
                            ],
                        },
                        "execution": {
                            "executed": True,
                            "out_state": "patched.state",
                            "applied_patches": [
                                {
                                    "symbol": "wScriptPos",
                                    "base_symbol": "wScriptPos",
                                    "value": 80,
                                    "value_hex": "50",
                                    "observed": 80,
                                    "observed_hex": "50",
                                    "verified": True,
                                    "bank_address": "01:DA11",
                                    "scenario_id": "script_entry_1",
                                    "source_file": "maps/UnitMap.asm",
                                    "applied": True,
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("state_space.json",), root=root)
            impact = build_impact_report(reports=("state_space.json",), root=root)
            visualization = build_visualization_report(reports=("state_space.json",), root=root)

        ranked_types = {item["type"] for item in ranked["findings"]}
        impact_types = {item["type"] for item in impact["items"]}
        lanes = {item["lane"] for item in visualization["timeline"]}
        graph_node_types = {node["type"] for node in visualization["graph"]["nodes"]}
        commands = "\n".join(
            action
            for item in impact["items"]
            for action in item.get("next_actions", [])
        )

        self.assertIn("state_space_ready", ranked_types)
        self.assertIn("state_space_executed", ranked_types)
        self.assertIn("state_space_ready", impact_types)
        self.assertIn("state_space_executed", impact_types)
        self.assertIn("wScriptPos", {symbol for item in impact["items"] for symbol in item.get("related_symbols", [])})
        self.assertIn("maps/UnitMap.asm", {path for item in impact["items"] for path in item.get("related_files", [])})
        self.assertIn("tools.debugger replay --report state_space.json --scenario-id script_entry_1", commands)
        self.assertIn("tools.debugger watch --watch-symbol wScriptPos --save-state patched.state --execute", commands)
        self.assertIn("state_space", lanes)
        self.assertIn("runtime", lanes)
        self.assertIn("state_space_materialization", graph_node_types)
        self.assertIn("runtime_state_patch", graph_node_types)
        self.assertIn("save_state", graph_node_types)

    def test_setup_trigger_coverage_is_covered_with_supplied_state(self) -> None:
        report = build_setup_plan(
                save_state="state.state",
            symbols=("BattleCommand_DamageCalc",),
            watch_symbols=("wCurDamage",),
        )

        coverage = report["trigger_coverage"]
        target = coverage["targets"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(coverage["covered_target_count"], 1)
        self.assertEqual(coverage["coverage_ratio"], 1.0)
        self.assertEqual(target["status"], "covered")
        self.assertEqual(target["state_status"], "supplied")
        self.assertEqual(target["blockers"], [])

    def test_setup_discovers_save_state_from_selected_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "case.state").write_bytes(b"state")
            (root / "other.state").write_bytes(b"other")
            (root / "scenarios.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"id": "other_case", "state": "other.state"}),
                        json.dumps({"capture_id": "case_one", "state": "case.state"}),
                    ]
                ),
                encoding="utf-8",
            )

            report = build_setup_plan(
                scenarios=("scenarios.jsonl",),
                scenario_ids=("case_one",),
                symbols=("BattleCommand_DamageCalc",),
                watch_symbols=("wCurDamage",),
                root=root,
            )

        commands = "\n".join(report["commands"])
        coverage = report["trigger_coverage"]
        target = coverage["targets"][0]
        selected = report["save_state_discovery"]["selected"]

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "case.state")
        self.assertTrue(report["state_requirements"]["save_state_discovered"])
        self.assertEqual(report["targets"][0]["state_synthesis_recipes"][0]["id"], "damage_snapshot_ring_runtime")
        self.assertEqual(selected["scenario_id"], "case_one")
        self.assertEqual(selected["key"], "state")
        self.assertEqual(target["state_status"], "discovered")
        self.assertEqual(target["status"], "covered")
        self.assertIn("--save-state case.state", commands)
        self.assertNotIn("no save state was supplied", "\n".join(report["warnings"]))

    def test_setup_boss_ai_recipe_targets_requested_route(self) -> None:
        report = build_setup_plan(
            scenario_ids=("falkner",),
            symbols=("BossAI_SelectMove",),
            watch_symbols=("wEnemyAIMoveScores",),
        )

        recipes = report["targets"][0]["state_synthesis_recipes"]
        commands = "\n".join(
            command["command"]
            for recipe in recipes
            for command in recipe["commands"]
        )

        self.assertEqual(report["surfaces"], ["boss_ai"])
        self.assertIn("boss_ai_route_state_factory", {recipe["id"] for recipe in recipes})
        self.assertIn("--boss falkner", commands)
        self.assertIn("rom-score-materialize", commands)

    def test_setup_plan_uses_embedded_next_step_instead_of_nested_report_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            investigation = root / "investigate.json"
            investigation.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_investigation_run",
                        "valid": True,
                        "symptom": "boss selected wrong switch",
                        "symptom_only_next_step": build_next_step(symptom="boss selected wrong switch"),
                        "reports": [
                            {"id": "09_fuzz", "kind": "unified_debugger_fuzz_plan", "surface": "ROM banking / ABI"},
                            {"id": "06_explain", "kind": "unified_debugger_causal_explanation", "surface": "Battle damage"},
                        ],
                        "top_impact": [
                            {
                                "type": "fuzz_campaign",
                                "title": "Fuzz campaign: fuzz_banking_abi_static_watch",
                                "severity": 55,
                                "confidence": 0.62,
                                "evidence": [],
                                "next_actions": [],
                                "impact_score": 100,
                                "surface_id": "banking_abi",
                            },
                            {
                                "type": "causal_path",
                                "title": "Causal path: Battle damage",
                                "severity": 50,
                                "confidence": 0.62,
                                "evidence": [],
                                "next_actions": [],
                                "impact_score": 90,
                                "surface_id": "battle_damage",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_setup_plan(reports=("investigate.json",), root=root)

        commands = "\n".join(report["commands"])
        self.assertTrue(report["valid"])
        self.assertEqual(report["surfaces"], ["boss_ai"])
        self.assertEqual(report["target_count"], 1)
        self.assertIn("BossAI_SwitchOrTryItem", report["effective_symbols"])
        self.assertIn("wEnemySwitchMonIndex", report["effective_watch_symbols"])
        self.assertIn("engine/battle/ai/boss_policy_switch.asm", report["effective_changed_files"])
        self.assertIn("--symbol BossAI_SwitchOrTryItem", commands)
        self.assertIn("--watch-symbol wEnemySwitchMonIndex", commands)
        self.assertNotIn("--family damage", commands)
        self.assertNotIn("--family banking_abi", commands)
        self.assertNotIn("hROMBank", commands)

    def test_rank_and_impact_consume_setup_trigger_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_report = build_setup_plan(
                symbols=("BattleCommand_DamageCalc",),
                watch_symbols=("wCurDamage",),
                root=root,
            )
            (root / "setup.json").write_text(
                json.dumps(setup_report),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("setup.json",), root=root)
            impact = build_impact_report(reports=("setup.json",), root=root)

        ranked_types = {finding["type"] for finding in ranked["findings"]}
        impact_types = {item["type"] for item in impact["items"]}
        ranked_gap = next(item for item in ranked["findings"] if item["type"] == "setup_trigger_gap")
        impact_gap = next(item for item in impact["items"] if item["type"] == "setup_trigger_gap")

        self.assertIn("setup_trigger_gap", ranked_types)
        self.assertIn("setup_trigger_gap", impact_types)
        self.assertIn("state:synthesizable", ranked_gap["evidence"])
        self.assertIn("trace-instructions", "\n".join(ranked_gap["next_actions"]))
        self.assertIn("wCurDamage", impact_gap["related_symbols"])

    def test_cli_setup_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "setup.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "setup",
                        "--changed-file",
                        "maps/UnitMap.asm",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_setup_plan")
        self.assertEqual(data["surfaces"], ["content_static"])

    def test_suggest_tests_maps_damage_symbol_to_fuzzers(self) -> None:
        report = suggest_tests(symbols=("wCurDamage",))
        commands = "\n".join(report["commands"])
        counterexamples = "\n".join(report["counterexample_commands"])

        self.assertIn("damage_counterexamples", {match["id"] for match in report["matches"]})
        self.assertIn("tools.damage_debugger.fuzz", commands)
        self.assertIn("tools.damage_debugger.replay", counterexamples)

    def test_suggest_tests_maps_boss_ai_change_to_generators(self) -> None:
        report = suggest_tests(
            changed_files=("engine/battle/ai/boss_policy_move.asm",),
        )
        commands = "\n".join(report["commands"])

        self.assertIn("boss_ai_counterexamples", {match["id"] for match in report["matches"]})
        self.assertIn("tools.boss_ai_debugger generate", commands)

    def test_suggest_tests_routes_content_to_source_expectations(self) -> None:
        report = suggest_tests(changed_files=("maps/NewBarkTown.asm",))
        commands = "\n".join(report["commands"])
        counterexamples = "\n".join(report["counterexample_commands"])

        self.assertIn("content_static_counterexamples", {match["id"] for match in report["matches"]})
        self.assertIn("tools.debugger expect --source-file", commands)
        self.assertIn("contains=<expected_text>", counterexamples)

    def test_suggest_tests_uses_embedded_next_step_regression_gate_from_investigation_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            investigation_report = root / "investigate.json"
            investigation_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_investigation_run",
                        "valid": True,
                        "symptom": "boss selected wrong switch",
                        "symptom_only_next_step": build_next_step(symptom="boss selected wrong switch"),
                    }
                ),
                encoding="utf-8",
            )

            report = suggest_tests(reports=("investigate.json",), root=root)

        commands = "\n".join(report["commands"])
        counterexamples = "\n".join(report["counterexample_commands"])
        notes = "\n".join(
            note
            for match in report["matches"]
            for note in match.get("notes", [])
        )
        self.assertTrue(report["valid"])
        self.assertEqual(report["input_reports"], ["investigate.json"])
        self.assertIn("next_step_regression_gate", {match["id"] for match in report["matches"]})
        self.assertIn("rom-switch-materialize", commands)
        self.assertIn("--fail-on-mismatch", commands)
        self.assertIn("run-suite --profile changed-ai", counterexamples)
        self.assertIn("source/data: tools/boss_ai_debugger/rom_switch_materialize.py", notes)
        self.assertIn("disproof standard: If a matching scenario JSONL passes rom-switch-materialize with the expected switch result", notes)
        self.assertIn("proof limit: ROM materialization proof for supplied switch scenarios", notes)

    def test_cli_suggest_tests_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "suggestions.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "suggest-tests",
                        "--symbol",
                        "BossAI_SelectMove",
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_test_suggestions")
            self.assertTrue(data["matches"])

    def test_generate_routes_damage_and_writes_seed_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_file = root / "generated.jsonl"
            report = build_generation_plan(
                symbols=("wCurDamage",),
                changed_files=("engine/battle/effect_commands.asm",),
                out_scenarios=str(seed_file),
                max_cases=4,
                seed=7,
                root=root,
            )

            rows = [
                json.loads(line)
                for line in seed_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("damage", report["surfaces"])
        self.assertIn("damage_fuzz", {item["id"] for item in report["generators"]})
        self.assertTrue(report["seed_manifest"]["written"])
        self.assertEqual(report["seed_manifest"]["record_count"], 4)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["family"], "damage")
        self.assertIn("tools.damage_debugger.fuzz", commands)

    def test_generate_routes_boss_ai_to_generators(self) -> None:
        report = build_generation_plan(
            changed_files=("engine/battle/ai/boss_policy_move.asm",),
            symbols=("BossAI_SelectMove",),
            max_cases=8,
            seed=3,
        )
        commands = "\n".join(report["commands"])
        materialization = "\n".join(
            step["command"] for step in report["materialization_steps"]
        )

        self.assertTrue(report["valid"])
        self.assertIn("boss_ai", report["surfaces"])
        self.assertIn("boss_ai_generated_policy", {item["id"] for item in report["generators"]})
        self.assertIn("tools.boss_ai_debugger generate", commands)
        self.assertIn("rom-score-materialize", materialization)
        self.assertIn(".local\\tmp\\debugger_boss_ai_generated.jsonl", materialization)

    def test_generate_uses_embedded_next_step_instead_of_nested_report_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            investigation = root / "investigate.json"
            investigation.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_investigation_run",
                        "valid": True,
                        "symptom": "boss selected wrong switch",
                        "symptom_only_next_step": build_next_step(symptom="boss selected wrong switch"),
                        "reports": [
                            {"id": "09_fuzz", "kind": "unified_debugger_fuzz_plan", "surface": "ROM banking / ABI"},
                            {"id": "06_explain", "kind": "unified_debugger_causal_explanation", "surface": "Battle damage"},
                        ],
                        "top_impact": [
                            {
                                "type": "fuzz_campaign",
                                "title": "Fuzz campaign: fuzz_banking_abi_static_watch",
                                "severity": 55,
                                "confidence": 0.62,
                                "evidence": [],
                                "next_actions": [],
                                "impact_score": 100,
                                "surface_id": "banking_abi",
                            },
                            {
                                "type": "causal_path",
                                "title": "Causal path: Battle damage",
                                "severity": 50,
                                "confidence": 0.62,
                                "evidence": [],
                                "next_actions": [],
                                "impact_score": 90,
                                "surface_id": "battle_damage",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_generation_plan(
                reports=("investigate.json",),
                max_cases=8,
                seed=3,
                root=root,
            )
            fuzz = build_fuzz_plan(
                reports=("investigate.json",),
                max_cases=8,
                seed=3,
                root=root,
            )

        commands = "\n".join(report["commands"])
        materialization = "\n".join(step["command"] for step in report["materialization_steps"])
        fuzz_commands = "\n".join(fuzz["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["surfaces"], ["boss_ai"])
        self.assertEqual(report["effective_families"], ["switch_sack"])
        self.assertIn("boss_ai_generated_policy", {item["id"] for item in report["generators"]})
        self.assertIn("generate --family switch_sack", commands)
        self.assertIn("rom-switch-materialize --scenarios .local\\tmp\\debugger_boss_ai_generated.jsonl --limit 20 --fail-on-mismatch", materialization)
        self.assertNotIn("tools.damage_debugger.fuzz", commands)
        self.assertNotIn("check_farcall_a_clobber", commands)
        self.assertEqual(fuzz["surfaces"], ["boss_ai"])
        self.assertEqual({campaign["surface"] for campaign in fuzz["campaigns"]}, {"boss_ai"})
        self.assertIn("generate --family switch_sack", fuzz_commands)
        self.assertNotIn("tools.damage_debugger.fuzz", fuzz_commands)
        self.assertNotIn("hROMBank", fuzz_commands)

    def test_generate_routes_content_to_static_expectation_seeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            source = root / "maps" / "NewBarkTown.asm"
            source.write_text(
                "\n".join(
                    [
                        "NewBarkTown_MapEvents:",
                        "\tdef_warp_events",
                        "\twarp_event  1,  1, ROUTE_29, 1",
                        "\tdef_bg_events",
                        "\tbg_event  4,  5, BGEVENT_READ, NewBarkTownSign",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            seed_file = root / "generated.jsonl"
            report = build_generation_plan(
                changed_files=("maps/NewBarkTown.asm",),
                out_scenarios="generated.jsonl",
                max_cases=3,
                seed=2,
                root=root,
            )
            rows = [
                json.loads(line)
                for line in seed_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        commands = "\n".join(report["commands"])
        materialization = "\n".join(
            step["command"] for step in report["materialization_steps"]
        )

        self.assertTrue(report["valid"])
        self.assertIn("content_static", report["surfaces"])
        self.assertIn("content_static_seed_manifest", {item["id"] for item in report["generators"]})
        self.assertIn("positioned-state-planned", {item["status"] for item in report["generators"]})
        self.assertIn("map_warp", {row.get("scenario_type") for row in rows})
        self.assertIn("positioned_state_dynamic_planned", {row.get("proof_level") for row in rows})
        self.assertIn("behavioral_probes", rows[0])
        self.assertIn("runtime_targets", rows[0])
        self.assertIn("materialization_request", rows[0])
        self.assertIn(
            "content_replay_route",
            {probe["id"] for probe in rows[0]["behavioral_probes"]},
        )
        self.assertIn(
            "content_runtime_trace_route",
            {probe["id"] for probe in rows[0]["behavioral_probes"]},
        )
        self.assertIn(
            "content_state_execution_route",
            {probe["id"] for probe in rows[0]["behavioral_probes"]},
        )
        self.assertIn(
            "content_positioned_replay_route",
            {probe["id"] for probe in rows[0]["behavioral_probes"]},
        )
        self.assertIn(
            "content_positioned_instruction_trace_route",
            {probe["id"] for probe in rows[0]["behavioral_probes"]},
        )
        self.assertIn("tools.debugger expect --source-file", commands)
        self.assertIn("tools.debugger content-scenarios", commands)
        self.assertIn("tools.debugger content-state", commands)
        self.assertIn("tools.debugger trace-instructions --report .local\\tmp\\debugger_content_state_debugger_generated_content_static_2_0000.json", commands)
        self.assertIn("--execute --json-out .local\\tmp\\debugger_content_state_debugger_generated_content_static_2_0000.json", commands)
        self.assertIn("--scenario generated.jsonl --scenario-id debugger_generated_content_static_2_0000", commands)
        self.assertIn("--symbol WarpCheck", commands)
        self.assertIn("not-contains=<forbidden_text>", commands)
        self.assertIn("replay --report .local\\tmp\\debugger_content_state_<id>.json", materialization)

    def test_generate_hands_ready_instruction_trace_to_dynamic_taint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "instruction_trace.jsonl").write_text(
                json.dumps({"seq": 1, "bank": 1, "pc": 0x4000, "opcode": 0xEA, "operand": [0x41, 0xD1]}) + "\n",
                encoding="utf-8",
            )
            (root / "instruction_trace_report.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": True,
                        "trace_output": {"path": "instruction_trace.jsonl", "written": True},
                        "execution_validation": {
                            "ready_for_dynamic_taint": True,
                            "hit_count": 1,
                            "watch_symbols": ["wCurDamage"],
                        },
                        "dynamic_taint_sources": {"source_regs": ["a=move_power"]},
                    }
                ),
                encoding="utf-8",
            )

            report = build_generation_plan(
                reports=("instruction_trace_report.json",),
                max_cases=2,
                root=root,
            )

        commands = "\n".join(report["commands"])
        handoff = report["dynamic_taint_handoffs"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(report["dynamic_taint_handoff_count"], 1)
        self.assertEqual(handoff["source_report"], "instruction_trace_report.json")
        self.assertEqual(handoff["traces"], ["instruction_trace.jsonl"])
        self.assertEqual(handoff["sink_symbols"], ["wCurDamage"])
        self.assertEqual(handoff["source_regs"], ["a=move_power"])
        self.assertIn("python -m tools.debugger dynamic-taint --report instruction_trace_report.json", commands)
        self.assertIn("dynamic-taint", {item["source"] for item in report["counterexamples"]})

    def test_cli_generate_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "generate.json"
            seed_file = Path(tmp) / "generated.jsonl"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "generate",
                        "--symbol",
                        "wCurDamage",
                        "--out-scenarios",
                        str(seed_file),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            rows = [
                json.loads(line)
                for line in seed_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_generation_plan")
        self.assertIn("damage", data["surfaces"])
        self.assertTrue(rows)

    def test_fuzz_routes_content_to_source_expectation_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            source = root / "maps" / "NewBarkTown.asm"
            source.write_text(
                "\n".join(
                    [
                        "NewBarkTown_MapEvents:",
                        "\tdef_warp_events",
                        "\twarp_event  1,  1, ROUTE_29, 1",
                        "\tdef_object_events",
                        "\tobject_event  5,  5, SPRITE_SILVER, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, 0, OBJECTTYPE_SCRIPT, 0, RivalScript, -1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            cases_file = root / "fuzz_cases.jsonl"

            report = build_fuzz_plan(
                changed_files=("maps/NewBarkTown.asm",),
                out_cases="fuzz_cases.jsonl",
                max_cases=8,
                seed=11,
                root=root,
            )
            rows = [
                json.loads(line)
                for line in cases_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        commands = "\n".join(report["commands"])
        expectations = {
            expectation
            for case in report["fuzz_cases"]
            for expectation in case["expectations"]
        }
        fuzz_types = {case["fuzz_type"] for case in report["fuzz_cases"]}
        proof_levels = {case["proof_level"] for case in report["fuzz_cases"]}

        self.assertTrue(report["valid"])
        self.assertIn("content_static", report["surfaces"])
        self.assertEqual(report["dynamic_campaign_count"], 1)
        self.assertTrue(report["case_manifest"]["written"])
        self.assertEqual(len(rows), report["fuzz_case_count"])
        self.assertIn("map_warp", fuzz_types)
        self.assertIn("map_object_event", fuzz_types)
        self.assertIn("positioned_state_dynamic_planned", proof_levels)
        self.assertIn("static_expectation", proof_levels)
        self.assertIn("materialization_request", report["fuzz_cases"][0])
        self.assertIn(
            "trace-instructions",
            "\n".join(report["fuzz_cases"][0]["materialization_request"]["commands"]),
        )
        self.assertIn("contains=warp_event", expectations)
        self.assertIn("contains=object_event", expectations)
        self.assertIn("not-contains=__DEBUGGER_FORBIDDEN_SENTINEL__", expectations)
        self.assertIn("tools.debugger expect --source-file maps/NewBarkTown.asm", commands)
        self.assertIn("tools.debugger content-scenarios", commands)
        self.assertIn("tools.debugger content-state", commands)

    def test_fuzz_turns_ready_instruction_trace_into_dynamic_taint_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "instruction_trace.jsonl").write_text(
                json.dumps({"seq": 1, "bank": 1, "pc": 0x4000, "opcode": 0xEA, "operand": [0x41, 0xD1]}) + "\n",
                encoding="utf-8",
            )
            (root / "instruction_trace_report.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": True,
                        "trace_output": {"path": "instruction_trace.jsonl", "written": True},
                        "execution_validation": {
                            "ready_for_dynamic_taint": True,
                            "hit_count": 1,
                            "watch_symbols": ["wCurDamage"],
                        },
                        "dynamic_taint_sources": {"source_regs": ["a=move_power"]},
                    }
                ),
                encoding="utf-8",
            )

            report = build_fuzz_plan(
                reports=("instruction_trace_report.json",),
                max_cases=4,
                root=root,
            )

        commands = "\n".join(report["commands"])
        case = next(item for item in report["fuzz_cases"] if item["fuzz_type"] == "dynamic_taint_handoff")

        self.assertTrue(report["valid"])
        self.assertEqual(report["dynamic_taint_handoff_count"], 1)
        self.assertGreaterEqual(report["dynamic_campaign_count"], 1)
        self.assertIn("instruction_trace", {campaign["surface"] for campaign in report["campaigns"]})
        self.assertEqual(case["proof_level"], "dynamic_trace")
        self.assertEqual(case["source_report"], "instruction_trace_report.json")
        self.assertEqual(case["sink_symbols"], ["wCurDamage"])
        self.assertIn("python -m tools.debugger dynamic-taint --report instruction_trace_report.json", commands)

    def test_fuzz_keeps_map_report_surfaces_content_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "maps" / "NewBarkTown.asm").write_text(
                "NewBarkTown_MapEvents:\n\tdef_warp_events\n\twarp_event 1, 1, ROUTE_29, 1\n",
                encoding="utf-8",
            )
            trace_index = root / "trace_index.json"
            trace_index.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_trace_index",
                        "valid": True,
                        "query": {
                            "active": True,
                            "source_files": ["maps/NewBarkTown.asm"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            impact = root / "impact.json"
            impact.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_impact_report",
                        "valid": True,
                        "items": [
                            {
                                "type": "coverage_gap",
                                "title": "Uncovered source_file: maps/NewBarkTown.asm",
                                "severity": 40,
                                "confidence": 0.7,
                                "evidence": [],
                                "next_actions": [],
                                "impact_score": 70,
                                "related_files": [
                                    "maps/NewBarkTown.asm",
                                    "tools/audit/check_pic_bank_pressure.py",
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_fuzz_plan(
                reports=("trace_index.json", "impact.json"),
                changed_files=("maps/NewBarkTown.asm",),
                max_cases=4,
                root=root,
            )

        self.assertEqual(report["surfaces"], ["content_static"])
        self.assertEqual({campaign["surface"] for campaign in report["campaigns"]}, {"content_static"})
        self.assertEqual(report["dynamic_campaign_count"], 1)
        self.assertIn("positioned_state_dynamic_planned", {campaign["proof_level"] for campaign in report["campaigns"]})
        self.assertIn("materialization_request", report["fuzz_cases"][0])
        self.assertIn("tools.debugger content-state", "\n".join(report["commands"]))
        self.assertIn("tools.debugger replay --report .local\\tmp\\debugger_content_state_", "\n".join(report["commands"]))

    def test_fuzz_routes_damage_to_dynamic_campaign(self) -> None:
        report = build_fuzz_plan(
            symbols=("wCurDamage",),
            changed_files=("engine/battle/effect_commands.asm",),
            max_cases=4,
            seed=5,
        )
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("damage", report["surfaces"])
        self.assertEqual(report["dynamic_campaign_count"], 1)
        self.assertIn("dynamic_counterexample", {case["fuzz_type"] for case in report["fuzz_cases"]})
        self.assertIn("tools.damage_debugger.fuzz", commands)

    def test_cli_fuzz_writes_json_and_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "maps" / "NewBarkTown.asm").write_text(
                "NewBarkTown_MapEvents:\n\twarp_event 1, 1, ROUTE_29, 1\n",
                encoding="utf-8",
            )
            out = root / "fuzz.json"
            cases = root / "cases.jsonl"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "fuzz",
                        "--changed-file",
                        str(root / "maps" / "NewBarkTown.asm"),
                        "--out-cases",
                        str(cases),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            rows = [
                json.loads(line)
                for line in cases.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_fuzz_plan")
        self.assertTrue(rows)

    def test_compare_plan_maps_damage_symbol_to_oracle(self) -> None:
        report = build_compare_plan(symbols=("wCurDamage",))
        commands = "\n".join(report["commands"])
        proof = "\n".join(report["materialization_commands"])

        self.assertIn("damage_oracle", {match["id"] for match in report["matches"]})
        self.assertIn("tools.damage_debugger.oracle", commands)
        self.assertIn("tools.damage_debugger.replay", proof)

    def test_compare_plan_maps_boss_ai_source_to_materialization(self) -> None:
        report = build_compare_plan(
            changed_files=("engine/battle/ai/boss_policy_move.asm",),
        )
        proof = "\n".join(report["materialization_commands"])

        self.assertIn(
            "boss_ai_policy_mirror",
            {match["id"] for match in report["matches"]},
        )
        self.assertIn("rom-score-materialize", proof)

    def test_compare_plan_uses_embedded_next_step_as_mirror_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            investigation = root / "investigate.json"
            investigation.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_investigation_run",
                        "valid": True,
                        "symptom": "boss selected wrong switch",
                        "symptom_only_next_step": build_next_step(symptom="boss selected wrong switch"),
                        "reports": [
                            {"id": "09_fuzz", "kind": "unified_debugger_fuzz_plan", "surface": "ROM banking / ABI"},
                            {"id": "06_explain", "kind": "unified_debugger_causal_explanation", "surface": "Battle damage"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_compare_plan(reports=("investigate.json",), root=root)

        commands = "\n".join(report["commands"])
        proof = "\n".join(report["materialization_commands"])
        evidence = "\n".join(item for match in report["matches"] for item in match["evidence"])

        self.assertTrue(report["valid"])
        self.assertEqual({match["id"] for match in report["matches"]}, {"boss_ai_policy_mirror"})
        self.assertIn("next_step", report["matches"][0]["matched_by"])
        self.assertIn("rom-switch-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch", commands)
        self.assertIn("rom-switch-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch", proof)
        self.assertIn("run-suite --profile changed-ai", proof)
        self.assertIn("source_ref=engine/battle/ai/boss_policy_switch.asm", evidence)
        self.assertIn("evidence standard: A scenario JSONL matching the disputed switch case passes rom-switch-materialize", evidence)
        self.assertNotIn("damage_debugger", commands)
        self.assertNotIn("uncovered_surface", {match["id"] for match in report["matches"]})

    def test_compare_plan_routes_content_to_static_expectations(self) -> None:
        report = build_compare_plan(changed_files=("maps/NewBarkTown.asm",))
        commands = "\n".join(report["commands"])
        proof = "\n".join(report["materialization_commands"])

        self.assertIn("static_invariant_mirror", {match["id"] for match in report["matches"]})
        self.assertIn("tools.debugger content-mirror", commands)
        self.assertIn("tools.debugger expect --source-file", commands)
        self.assertIn("content-mirror --source-file", proof)
        self.assertIn("contains=<expected_text>", proof)

    def test_compare_plan_consumes_content_state_behavioral_mirror(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "patched.state").write_bytes(b"patched-state")
            content_state_report = root / "content_state.json"
            content_state_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "executed": True,
                        "out_state": "patched.state",
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0000",
                                "precondition_kind": "map_position",
                                "source_file": "maps/UnitMap.asm",
                                "status": "ready",
                                "patches": [
                                    {
                                        "symbol": "wMapGroup",
                                        "value": 24,
                                        "value_hex": "18",
                                        "bank_address": "01:DA00",
                                    },
                                    {
                                        "symbol": "wMapNumber",
                                        "value": 4,
                                        "value_hex": "04",
                                        "bank_address": "01:DA01",
                                    },
                                ],
                            }
                        ],
                        "execution": {
                            "executed": True,
                            "out_state": "patched.state",
                            "applied_patches": [
                                {
                                    "symbol": "wMapGroup",
                                    "value": 24,
                                    "value_hex": "18",
                                    "observed": 24,
                                    "observed_hex": "18",
                                    "verified": True,
                                    "bank_address": "01:DA00",
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_compare_plan(reports=("content_state.json",), root=root)

        commands = "\n".join(report["commands"])
        proof = "\n".join(report["materialization_commands"])
        match = report["matches"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(match["id"], "content_state_behavioral_mirror")
        self.assertEqual(match["gaps"], [])
        self.assertIn("content_state.json", report["input_reports"])
        self.assertIn("state-patch=wMapGroup,scenario=content_scenario_1_0000,value=0x18", commands)
        self.assertIn("replay --report content_state.json --scenario-id content_scenario_1_0000 --execute-watch", proof)
        self.assertIn("--save-state patched.state --execute", proof)

    def test_content_mirror_validates_map_event_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "\tobject_const_def",
                        "\tconst UNITMAP_NPC",
                        "",
                        "UnitMap_MapScripts:",
                        "\tdef_scene_scripts",
                        "\tdef_callbacks",
                        "",
                        "UnitMap_MapEvents:",
                        "\tdb 0, 0 ; filler",
                        "",
                        "\tdef_warp_events",
                        "\twarp_event 1, 2, ROUTE_29, 1",
                        "",
                        "\tdef_coord_events",
                        "\tcoord_event 2, 3, SCENE_UNITMAP, UnitMapScene",
                        "",
                        "\tdef_bg_events",
                        "\tbg_event 4, 5, BGEVENT_READ, UnitMapSign",
                        "",
                        "\tdef_object_events",
                        "\tobject_event 6, 7, SPRITE_CHRIS, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, 0, OBJECTTYPE_SCRIPT, 0, UnitMapNPCScript, -1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("maps/UnitMap.asm",),
                root=root,
            )

        invariant_ids = {item["id"] for item in report["invariants"]}
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertEqual(report["failed_invariant_count"], 0)
        self.assertIn("maps/UnitMap.asm:map_warp_event_section", invariant_ids)
        self.assertIn("maps/UnitMap.asm:map_object_event_section", invariant_ids)
        self.assertIn("tools.debugger content-mirror --source-file maps/UnitMap.asm", commands)
        self.assertIn("tools.debugger expect --source-file maps/UnitMap.asm", commands)

    def test_content_mirror_compares_map_events_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "constants").mkdir()
            (root / "constants" / "map_constants.asm").write_text(
                "\n".join(
                    [
                        "const_def",
                        "newgroup NEW_BARK",
                        "map_const ROUTE_29, 30, 9",
                        "endgroup",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "constants" / "script_constants.asm").write_text(
                "const_def\nconst BGEVENT_READ\n",
                encoding="utf-8",
            )
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "UnitMapSign:",
                        "\tjumptext UnitMapSignText",
                        "",
                        "UnitMap_MapEvents:",
                        "\tdb 0, 0 ; filler",
                        "\tdef_warp_events",
                        "\twarp_event 1, 2, ROUTE_29, 1",
                        "\tdef_coord_events",
                        "\tdef_bg_events",
                        "\tbg_event 4, 5, BGEVENT_READ, UnitMapSign",
                        "\tdef_object_events",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes(
                [
                    0,
                    0,
                    1,
                    2,
                    1,
                    1,
                    1,
                    1,
                    0,
                    1,
                    5,
                    4,
                    0,
                    0x20,
                    0x01,
                    0,
                ]
            )
            rom = bytearray([0xFF] * 0x200)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "00:0100 UnitMap_MapEvents\n00:0120 UnitMapSign\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("maps/UnitMap.asm",),
                root=root,
            )
            rom[0x100 + 4] = 9
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("maps/UnitMap.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        self.assertTrue(report["rom_available"])
        map_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "map_event_rom_bytes"]
        self.assertEqual(len(map_mirrors), 1)
        self.assertEqual(map_mirrors[0]["status"], "passed")
        self.assertIn(
            "maps/UnitMap.asm:map_event_rom_bytes",
            {item["id"] for item in report["rom_mirrors"]},
        )
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        failed_map_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_map_mirror["type"], "map_event_rom_bytes")
        self.assertIn("first_mismatch=", "\n".join(failed_map_mirror["evidence"]))

    def test_content_mirror_compares_labeled_incbin_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gfx").mkdir()
            source = root / "gfx" / "unit.asm"
            asset = root / "gfx" / "unit.2bpp"
            source.write_text(
                "UnitGraphic:\nINCBIN \"gfx/unit.2bpp\"\n",
                encoding="utf-8",
            )
            asset.write_bytes(bytes([1, 2, 3, 4, 5]))
            rom = bytearray([0xFF] * 0x200)
            rom[0x100:0x105] = asset.read_bytes()
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text("00:0100 UnitGraphic\n", encoding="utf-8")

            report = build_content_mirror_report(
                source_files=("gfx/unit.asm",),
                root=root,
            )
            rom[0x102] = 9
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("gfx/unit.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(report["rom_mirror_count"], 1)
        self.assertEqual(report["passed_rom_mirror_count"], 1)
        self.assertIn("incbin_asset_rom_bytes", {item["type"] for item in report["rom_mirrors"]})
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        self.assertIn("first_mismatch=", "\n".join(mismatch["rom_mirrors"][0]["evidence"]))

    def test_content_mirror_compares_incbin_table_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gfx").mkdir()
            source = root / "gfx" / "table.asm"
            first = root / "gfx" / "first.bin"
            second = root / "gfx" / "second.bin"
            source.write_text(
                "\n".join(
                    [
                        'DEF first_slice EQUS "1, 2"',
                        "UnitTable:",
                        "\ttable_width 4",
                        '\tINCBIN "gfx/first.bin", first_slice',
                        '\tINCBIN "gfx/second.bin"',
                        "\tassert_table_length 2",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            first.write_bytes(bytes([0, 1, 2, 9]))
            second.write_bytes(bytes([3, 4]))
            expected = bytes([1, 2, 3, 4])
            rom = bytearray([0xFF] * 0x200)
            rom[0x100:0x104] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text("00:0100 UnitTable\n", encoding="utf-8")

            report = build_content_mirror_report(
                source_files=("gfx/table.asm",),
                root=root,
            )
            rom[0x103] = 8
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("gfx/table.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        table_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "incbin_table_rom_bytes"]
        self.assertEqual(len(table_mirrors), 1)
        self.assertEqual(table_mirrors[0]["status"], "passed")
        self.assertFalse(mismatch["passed"])
        failed_table_mirror = next(item for item in mismatch["rom_mirrors"] if item["type"] == "incbin_table_rom_bytes" and item["status"] == "failed")
        self.assertIn("first_mismatch=", "\n".join(failed_table_mirror["evidence"]))

    def test_content_mirror_compares_audio_channel_header_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "audio").mkdir()
            source = root / "audio" / "unit.asm"
            source.write_text(
                "\n".join(
                    [
                        "Music_Unit:",
                        "\tchannel_count 2",
                        "\tchannel 1, Music_Unit_Ch1",
                        "\tchannel 2, Music_Unit_Ch2",
                        "Music_Unit_Ch1:",
                        "\tnote C_, 1",
                        "Music_Unit_Ch2:",
                        "\tnote D_, 1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes([0x40, 0x20, 0x01, 0x01, 0x30, 0x01])
            rom = bytearray([0xFF] * 0x200)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "00:0100 Music_Unit\n00:0120 Music_Unit_Ch1\n00:0130 Music_Unit_Ch2\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("audio/unit.asm",),
                root=root,
            )
            rom[0x100] = 0x30
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("audio/unit.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        audio_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "audio_channel_rom_bytes"]
        self.assertEqual(len(audio_mirrors), 1)
        self.assertEqual(audio_mirrors[0]["status"], "passed")
        self.assertFalse(mismatch["passed"])
        failed_audio_mirror = next(item for item in mismatch["rom_mirrors"] if item["type"] == "audio_channel_rom_bytes" and item["status"] == "failed")
        self.assertIn("first_mismatch=", "\n".join(failed_audio_mirror["evidence"]))

    def test_content_mirror_compares_labeled_data_block_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constants").mkdir()
            (root / "data").mkdir()
            (root / "constants" / "charmap.asm").write_text(
                "\n".join(
                    [
                        'charmap "<NEXT>", $4e',
                        'charmap "@", $50',
                        'charmap "U", $80',
                        'charmap "N", $81',
                        'charmap "I", $82',
                        'charmap "T", $83',
                        'charmap "O", $84',
                        'charmap "K", $85',
                        'charmap "3", $86',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "constants" / "unit_constants.asm").write_text(
                "DEF CONST_VALUE EQU $03\n",
                encoding="utf-8",
            )
            source = root / "data" / "unit.asm"
            source.write_text(
                "\n".join(
                    [
                        "UnitData:",
                        "\tdb 1, $02, CONST_VALUE",
                        "\tdw UnitTarget",
                        "\tdn 3, 4",
                        "\tdb \"UNIT{d:CONST_VALUE}@\"",
                        "\tnext \"OK@\"",
                        "",
                        "UnitTarget:",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes([1, 2, 3, 0x34, 0x12, 0x34, 0x80, 0x81, 0x82, 0x83, 0x86, 0x50, 0x4E, 0x84, 0x85, 0x50])
            rom = bytearray([0xFF] * 0x2000)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "00:0100 UnitData\n00:1234 UnitTarget\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("data/unit.asm",),
                root=root,
            )
            rom[0x103] = 9
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("data/unit.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(report["source_files"][0]["data_block_count"], 1)
        self.assertEqual(report["rom_mirror_count"], 1)
        self.assertEqual(report["passed_rom_mirror_count"], 1)
        self.assertIn("labeled_data_rom_bytes", {item["type"] for item in report["rom_mirrors"]})
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        self.assertIn("first_mismatch=", "\n".join(mismatch["rom_mirrors"][0]["evidence"]))

    def test_content_mirror_compares_script_commands_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            source = root / "scripts" / "unit_script.asm"
            source.write_text(
                "\n".join(
                    [
                        "UnitScript:",
                        "\topentext",
                        "\twritetext UnitText",
                        "\twaitbutton",
                        "\tclosetext",
                        "\tend",
                        "",
                        "UnitJump:",
                        "\tjumptext UnitText",
                        "",
                        "UnitFlagCallback:",
                        "\tsetflag ENGINE_UNIT_FLAG",
                        "\tendcallback",
                        "",
                        "UnitText:",
                        "\ttext \"HELLO\"",
                        "\tdone",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            script_bytes = bytes([0x47, 0x4C, 0x80, 0x01, 0x53, 0x49, 0x90])
            jump_bytes = bytes([0x52, 0x80, 0x01])
            flag_bytes = bytes([0x36, 0x34, 0x12, 0x8F])
            rom = bytearray([0xFF] * 0x400)
            rom[0x100:0x100 + len(script_bytes)] = script_bytes
            rom[0x120:0x120 + len(jump_bytes)] = jump_bytes
            rom[0x140:0x140 + len(flag_bytes)] = flag_bytes
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitScript",
                        "00:0120 UnitJump",
                        "00:0140 UnitFlagCallback",
                        "00:0180 UnitText",
                        "47 opentext_command",
                        "4c writetext_command",
                        "53 waitbutton_command",
                        "49 closetext_command",
                        "90 end_command",
                        "52 jumptext_command",
                        "36 setflag_command",
                        "8f endcallback_command",
                        "1234 ENGINE_UNIT_FLAG",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_script.asm",),
                root=root,
            )
            rom[0x102] = 0x81
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_script.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(report["source_files"][0]["script_block_count"], 3)
        script_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "script_command_rom_bytes"]
        self.assertEqual(len(script_mirrors), 3)
        self.assertTrue(all(item["status"] == "passed" for item in script_mirrors))
        self.assertIn("script_command_rom_bytes", {item["type"] for item in report["rom_mirrors"]})
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        failed_script_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_script_mirror["type"], "script_command_rom_bytes")
        self.assertIn("first_mismatch=", "\n".join(failed_script_mirror["evidence"]))

    def test_content_mirror_compares_map_script_action_commands_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constants").mkdir()
            (root / "scripts").mkdir()
            (root / "constants" / "trainer_constants.asm").write_text(
                "\n".join(
                    [
                        "DEF __trainer_class__ = 7",
                        "\ttrainerclass RIVAL1",
                        "\tconst RIVAL1_2_TOTODILE",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "constants" / "item_constants.asm").write_text(
                "\n".join(
                    [
                        "const_def $bf",
                        "DEF __tmhm_value__ = 1",
                        "\tadd_tm DYNAMICPUNCH",
                        "\tadd_tm LEECH_LIFE",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "constants" / "mart_constants.asm").write_text(
                "\n".join(
                    [
                        "const_def",
                        "\tconst MARTTYPE_STANDARD",
                        "const_def 5",
                        "\tconst MART_UNIT",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            source = root / "scripts" / "unit_map_actions.asm"
            source.write_text(
                "\n".join(
                    [
                        "object_const_def",
                        "\tconst UNIT_OBJECT",
                        "",
                        "UnitActionScript:",
                        "\trandom 6",
                        "\tpokemart MARTTYPE_STANDARD, MART_UNIT",
                        "\tverbosegiveitem TM_LEECH_LIFE",
                        "\tgettrainername STRING_BUFFER_4, RIVAL1, RIVAL1_2_TOTODILE",
                        "\twritecmdqueue UnitQueue",
                        "\tmoveobject UNIT_OBJECT, 11, 12",
                        "\tspecial FadeOutMusic",
                        "\tpause 15",
                        "\tappear UNIT_OBJECT",
                        "\tsetmapscene UNIT_MAP, 2",
                        "\twinlosstext UnitWinText, UnitLoseText",
                        "\tsetlasttalked UNIT_OBJECT",
                        "\tloadtrainer RIVAL1, RIVAL1_2_TOTODILE",
                        "\tstartbattle",
                        "\tdontrestartmapmusic",
                        "\treloadmapafterbattle",
                        "\tplaymusic MUSIC_RIVAL_AFTER",
                        "\tplaymapmusic",
                        "\tdisappear UNIT_OBJECT",
                        "\tend",
                        "",
                        "UnitWinText:",
                        "\ttext \"WIN\"",
                        "\tdone",
                        "",
                        "UnitLoseText:",
                        "\ttext \"LOSE\"",
                        "\tdone",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes(
                [
                    0x17, 0x06,
                    0x93, 0x00, 0x05, 0x00,
                    0x9D, 0xC0, 0x01,
                    0x43, 0x07, 0x01, 0x04,
                    0x7C, 0x20, 0x02,
                    0x71, 0x02, 0x0B, 0x0C,
                    0x0F, 0x03, 0x00,
                    0x8A, 0x0F,
                    0x6E, 0x02,
                    0x12, 0x04, 0x05, 0x02,
                    0x63, 0x90, 0x01, 0xA0, 0x01,
                    0x67, 0x02,
                    0x5D, 0x07, 0x01,
                    0x5E,
                    0x82,
                    0x5F,
                    0x7E, 0x20, 0x00,
                    0x81,
                    0x6D, 0x02,
                    0x90,
                ]
            )
            rom = bytearray([0xFF] * 0x400)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitActionScript",
                        "00:0190 UnitWinText",
                        "00:01a0 UnitLoseText",
                        "00:0200 SpecialsPointers",
                        "00:0209 FadeOutMusicSpecial",
                        "00:0220 UnitQueue",
                        "71 moveobject_command",
                        "17 random_command",
                        "93 pokemart_command",
                        "9d verbosegiveitem_command",
                        "43 gettrainername_command",
                        "7c writecmdqueue_command",
                        "0f special_command",
                        "8a pause_command",
                        "6e appear_command",
                        "12 setmapscene_command",
                        "63 winlosstext_command",
                        "67 setlasttalked_command",
                        "5d loadtrainer_command",
                        "5e startbattle_command",
                        "82 dontrestartmapmusic_command",
                        "5f reloadmapafterbattle_command",
                        "7e playmusic_command",
                        "81 playmapmusic_command",
                        "6d disappear_command",
                        "90 end_command",
                        "04 GROUP_UNIT_MAP",
                        "05 MAP_UNIT_MAP",
                        "20 MUSIC_RIVAL_AFTER",
                        "04 STRING_BUFFER_4",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_map_actions.asm",),
                root=root,
            )
            rom[0x105] = 0x04
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_map_actions.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        script_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "script_command_rom_bytes"]
        self.assertEqual(len(script_mirrors), 1)
        self.assertEqual(script_mirrors[0]["status"], "passed")
        self.assertIn("FadeOutMusicSpecial", script_mirrors[0]["related_symbols"])
        self.assertFalse(mismatch["passed"])
        failed_script_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_script_mirror["type"], "script_command_rom_bytes")
        self.assertIn("first_mismatch=", "\n".join(failed_script_mirror["evidence"]))

    def test_content_mirror_compares_trainer_record_scripts_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constants").mkdir()
            (root / "scripts").mkdir()
            (root / "constants" / "trainer_constants.asm").write_text(
                "\n".join(
                    [
                        "DEF __trainer_class__ = 7",
                        "\ttrainerclass RIVAL1",
                        "\tconst RIVAL1_2_TOTODILE",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            source = root / "scripts" / "unit_trainer.asm"
            source.write_text(
                "\n".join(
                    [
                        "UnitTrainer:",
                        "\ttrainer RIVAL1, RIVAL1_2_TOTODILE, EVENT_BEAT_UNIT, UnitSeenText, UnitWinText, 0, .AfterScript",
                        "",
                        ".AfterScript:",
                        "\tendifjustbattled",
                        "\tend",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes(
                [
                    0x34, 0x12,
                    0x07,
                    0x01,
                    0x00, 0x02,
                    0x10, 0x02,
                    0x00, 0x00,
                    0x0C, 0x01,
                    0x65,
                    0x90,
                ]
            )
            rom = bytearray([0xFF] * 0x400)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitTrainer",
                        "00:010c UnitTrainer.AfterScript",
                        "00:0200 UnitSeenText",
                        "00:0210 UnitWinText",
                        "1234 EVENT_BEAT_UNIT",
                        "65 endifjustbattled_command",
                        "90 end_command",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_trainer.asm",),
                root=root,
            )
            rom[0x100] = 0x35
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_trainer.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        script_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "script_command_rom_bytes"]
        self.assertEqual(len(script_mirrors), 1)
        self.assertEqual(script_mirrors[0]["status"], "passed")
        self.assertFalse(mismatch["passed"])
        failed_script_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_script_mirror["type"], "script_command_rom_bytes")
        self.assertIn("first_mismatch=", "\n".join(failed_script_mirror["evidence"]))

    def test_content_mirror_compares_macro_generated_script_data_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            source = root / "scripts" / "unit_macro_script_data.asm"
            source.write_text(
                "\n".join(
                    [
                        "DEF UNDERGROUND_DOOR_OPEN1 EQU $2d",
                        "",
                        "MACRO ugdoor",
                        "\tDEF UGDOOR_\\1_XCOORD EQU \\2",
                        "\tDEF UGDOOR_\\1_YCOORD EQU \\3",
                        "ENDM",
                        "",
                        "\tugdoor 1, 6, 16",
                        "",
                        "UnitScript:",
                        "\twritecmdqueue UnitQueue",
                        "\tdoorstate 1, OPEN1",
                        "\tcallasm UnitAsm",
                        "\tautoinput UnitAutoInput",
                        "\tgetstring STRING_BUFFER_3, .itemname",
                        "\tend",
                        ".itemname",
                        "\tdb \"BIKE@\"",
                        "",
                        "UnitQueue:",
                        "\tcmdqueue CMDQUEUE_STONETABLE, UnitStoneTable",
                        "",
                        "UnitStoneTable:",
                        "\tstonetable 5, UNIT_OBJECT, UnitFall",
                        "\tdb -1",
                        "",
                        "UnitFall:",
                        "\tdisappear UNIT_OBJECT",
                        "\tend",
                        "",
                        "UnitAsm:",
                        "\tret",
                        "",
                        "UnitAutoInput:",
                        "\tdb $01",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            unit_script = bytes(
                [
                    0x7C, 0x20, 0x01,
                    0x79, 0x10, 0x06, 0x2D,
                    0x0E, 0x02, 0x00, 0x40,
                    0x88, 0x02, 0x10, 0x40,
                    0x44, 0x50, 0x01, 0x03,
                    0x90,
                ]
            )
            queue = bytes([0x02, 0x30, 0x01, 0x00, 0x00])
            stone_table = bytes([0x05, 0x02, 0x40, 0x01, 0xFF])
            fall_script = bytes([0x6D, 0x02, 0x90])
            rom = bytearray([0xFF] * 0x8020)
            rom[0x100:0x100 + len(unit_script)] = unit_script
            rom[0x120:0x120 + len(queue)] = queue
            rom[0x130:0x130 + len(stone_table)] = stone_table
            rom[0x140:0x140 + len(fall_script)] = fall_script
            rom[0x8010] = 0x01
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitScript",
                        "00:0150 UnitScript.itemname",
                        "00:0120 UnitQueue",
                        "00:0130 UnitStoneTable",
                        "00:0140 UnitFall",
                        "02:4000 UnitAsm",
                        "02:4010 UnitAutoInput",
                        "7c writecmdqueue_command",
                        "79 changeblock_command",
                        "0e callasm_command",
                        "88 autoinput_command",
                        "44 getstring_command",
                        "90 end_command",
                        "6d disappear_command",
                        "02 CMDQUEUE_STONETABLE",
                        "02 UNIT_OBJECT",
                        "03 STRING_BUFFER_3",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_macro_script_data.asm",),
                root=root,
            )
            rom[0x134] = 0x00
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_macro_script_data.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        script_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "script_command_rom_bytes"]
        self.assertEqual(
            {item["related_symbols"][0] for item in script_mirrors},
            {"UnitScript", "UnitQueue", "UnitStoneTable", "UnitFall"},
        )
        self.assertTrue(all(item["status"] == "passed" for item in script_mirrors))
        self.assertIn("UnitAsm", script_mirrors[0]["related_symbols"])
        self.assertIn("UnitAutoInput", script_mirrors[0]["related_symbols"])
        self.assertFalse(mismatch["passed"])
        failed_script_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_script_mirror["type"], "script_command_rom_bytes")
        self.assertIn("UnitStoneTable", failed_script_mirror["related_symbols"])
        self.assertIn("first_mismatch=", "\n".join(failed_script_mirror["evidence"]))

    def test_content_mirror_compares_misc_script_commands_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            source = root / "scripts" / "unit_misc_script.asm"
            source.write_text(
                "\n".join(
                    [
                        "UnitMiscScript:",
                        "\tgivemoney YOUR_MONEY, 1000",
                        "\tcheckcoins 300",
                        "\tgetstring STRING_BUFFER_3, UnitString",
                        "\tgivepoke PIKACHU, 5",
                        "\tloadvar VAR_BATTLETYPE, BATTLETYPE_FORCEITEM",
                        "\tloadwildmon HO_OH, 40",
                        "\tvariablesprite SPRITE_FUCHSIA_GYM_1, SPRITE_JANINE",
                        "\tfollow PLAYER, UNIT_OBJECT",
                        "\tstopfollow",
                        "\tend",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes(
                [
                    0x22, 0x00, 0x00, 0x03, 0xE8,
                    0x27, 0x2C, 0x01,
                    0x44, 0x00, 0x02, 0x03,
                    0x2D, 0x19, 0x05, 0x00, 0x00,
                    0x1E, 0x01, 0x02,
                    0x5C, 0xFA, 0x28,
                    0x6C, 0x03, 0x44,
                    0x6F, 0x00, 0x02,
                    0x70,
                    0x90,
                ]
            )
            rom = bytearray([0xFF] * 0x400)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitMiscScript",
                        "00:0200 UnitString",
                        "22 givemoney_command",
                        "27 checkcoins_command",
                        "44 getstring_command",
                        "2d givepoke_command",
                        "1e loadvar_command",
                        "5c loadwildmon_command",
                        "6c variablesprite_command",
                        "6f follow_command",
                        "70 stopfollow_command",
                        "90 end_command",
                        "00 YOUR_MONEY",
                        "03 STRING_BUFFER_3",
                        "00 NO_ITEM",
                        "00 FALSE",
                        "19 PIKACHU",
                        "01 VAR_BATTLETYPE",
                        "02 BATTLETYPE_FORCEITEM",
                        "fa HO_OH",
                        "10 SPRITE_VARS",
                        "13 SPRITE_FUCHSIA_GYM_1",
                        "44 SPRITE_JANINE",
                        "00 PLAYER",
                        "02 UNIT_OBJECT",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_misc_script.asm",),
                root=root,
            )
            rom[0x103] = 0x04
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_misc_script.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        script_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "script_command_rom_bytes"]
        self.assertEqual(len(script_mirrors), 1)
        self.assertEqual(script_mirrors[0]["status"], "passed")
        self.assertFalse(mismatch["passed"])
        failed_script_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_script_mirror["type"], "script_command_rom_bytes")
        self.assertIn("first_mismatch=", "\n".join(failed_script_mirror["evidence"]))

    def test_content_mirror_compares_text_blocks_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constants").mkdir()
            (root / "text").mkdir()
            (root / "constants" / "charmap.asm").write_text(
                "\n".join(
                    [
                        'charmap "<LINE>", $4f',
                        'charmap "<DONE>", $57',
                        'charmap "<PLAYER>", $52',
                        'charmap "H", $80',
                        'charmap "E", $81',
                        'charmap "L", $82',
                        'charmap "O", $83',
                        'charmap "!", $e7',
                        'charmap "1", $f7',
                        'charmap "2", $f8',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            source = root / "text" / "unit_text.asm"
            source.write_text(
                "\n".join(
                    [
                        "DEF TEXT_VALUE EQU 12",
                        "",
                        "UnitText:",
                        "\ttext \"HELLO\"",
                        "\tline \"<PLAYER>!{d:TEXT_VALUE}\"",
                        "\tdone",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes([0x00, 0x80, 0x81, 0x82, 0x82, 0x83, 0x4F, 0x52, 0xE7, 0xF7, 0xF8, 0x57])
            rom = bytearray([0xFF] * 0x200)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "00:0100 UnitText\n00 TX_START\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("text/unit_text.asm",),
                root=root,
            )
            rom[0x104] = 0x99
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("text/unit_text.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(report["source_files"][0]["text_block_count"], 1)
        self.assertEqual(report["rom_mirror_count"], 1)
        self.assertEqual(report["passed_rom_mirror_count"], 1)
        self.assertIn("text_block_rom_bytes", {item["type"] for item in report["rom_mirrors"]})
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        self.assertIn("first_mismatch=", "\n".join(mismatch["rom_mirrors"][0]["evidence"]))

    def test_content_mirror_compares_local_text_labels_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constants").mkdir()
            (root / "scripts").mkdir()
            (root / "constants" / "charmap.asm").write_text(
                "\n".join(
                    [
                        'charmap "<LINE>", $4f',
                        'charmap "<DONE>", $57',
                        'charmap "R", $80',
                        'charmap "E", $81',
                        'charmap "A", $82',
                        'charmap "D", $83',
                        'charmap "Y", $84',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            source = root / "scripts" / "unit_cable_club.asm"
            source.write_text(
                "\n".join(
                    [
                        "CableClubFriendScript:",
                        "\topentext",
                        "\twritetext .FriendReadyText",
                        "\twaitbutton",
                        "\tclosetext",
                        "\tend",
                        "",
                        ".FriendReadyText:",
                        "\ttext \"READY\"",
                        "\tdone",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            script_bytes = bytes([0x47, 0x4C, 0x10, 0x01, 0x53, 0x49, 0x90])
            text_bytes = bytes([0x00, 0x80, 0x81, 0x82, 0x83, 0x84, 0x57])
            rom = bytearray([0xFF] * 0x300)
            rom[0x100:0x100 + len(script_bytes)] = script_bytes
            rom[0x110:0x110 + len(text_bytes)] = text_bytes
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 CableClubFriendScript",
                        "00:0110 CableClubFriendScript.FriendReadyText",
                        "47 opentext_command",
                        "4c writetext_command",
                        "53 waitbutton_command",
                        "49 closetext_command",
                        "90 end_command",
                        "00 TX_START",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_cable_club.asm",),
                root=root,
            )
            rom[0x111] = 0x82
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_cable_club.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        text_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "text_block_rom_bytes"]
        self.assertEqual(len(text_mirrors), 1)
        self.assertEqual(text_mirrors[0]["status"], "passed")
        self.assertEqual(text_mirrors[0]["related_symbols"], ["CableClubFriendScript.FriendReadyText"])
        self.assertFalse(mismatch["passed"])
        failed_text_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_text_mirror["type"], "text_block_rom_bytes")
        self.assertIn("first_mismatch=", "\n".join(failed_text_mirror["evidence"]))

    def test_content_mirror_compares_text_ram_blocks_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constants").mkdir()
            (root / "text").mkdir()
            (root / "constants" / "charmap.asm").write_text(
                "\n".join(
                    [
                        'charmap "<LINE>", $4f',
                        'charmap "<DONE>", $57',
                        'charmap " ", $7f',
                        'charmap "O", $80',
                        'charmap "K", $81',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            source = root / "text" / "unit_text_ram.asm"
            source.write_text(
                "\n".join(
                    [
                        "UnitTextRam:",
                        "\ttext_ram wStringBuffer3",
                        "\ttext \" OK\"",
                        "\tdone",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes([0x01, 0x91, 0xCF, 0x00, 0x7F, 0x80, 0x81, 0x57])
            rom = bytearray([0xFF] * 0x300)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitTextRam",
                        "00:cf91 wStringBuffer3",
                        "01 TX_RAM",
                        "00 TX_START",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("text/unit_text_ram.asm",),
                root=root,
            )
            rom[0x101] = 0x92
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("text/unit_text_ram.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        text_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "text_block_rom_bytes"]
        self.assertEqual(len(text_mirrors), 1)
        self.assertEqual(text_mirrors[0]["status"], "passed")
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        self.assertIn("first_mismatch=", "\n".join(mismatch["rom_mirrors"][0]["evidence"]))

    def test_content_mirror_compares_movement_blocks_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            source = root / "scripts" / "unit_movement.asm"
            source.write_text(
                "\n".join(
                    [
                        "UnitMovement:",
                        "\tstep LEFT",
                        "\tturn_head UP",
                        "\tstep_sleep 9",
                        "\tstep_end",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes([0x0E, 0x01, 0x46, 0x09, 0x47])
            rom = bytearray([0xFF] * 0x300)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitMovement",
                        "0c movement_step",
                        "00 movement_turn_head",
                        "3e movement_step_sleep",
                        "47 movement_step_end",
                        "02 LEFT",
                        "01 UP",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_movement.asm",),
                root=root,
            )
            rom[0x102] = 0x45
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_movement.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(report["source_files"][0]["movement_block_count"], 1)
        self.assertEqual(report["rom_mirror_count"], 1)
        self.assertEqual(report["passed_rom_mirror_count"], 1)
        self.assertIn("movement_data_rom_bytes", {item["type"] for item in report["rom_mirrors"]})
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        self.assertIn("first_mismatch=", "\n".join(mismatch["rom_mirrors"][0]["evidence"]))

    def test_content_mirror_reports_missing_incbin_asset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gfx").mkdir()
            (root / "gfx" / "unit.asm").write_text(
                'UnitGraphic: INCBIN "gfx/missing.2bpp"\n',
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("gfx/unit.asm",),
                root=root,
            )

        failed_ids = {item["id"] for item in report["failed_invariants"]}

        self.assertTrue(report["valid"])
        self.assertFalse(report["passed"])
        self.assertEqual(report["failed_invariant_count"], 1)
        self.assertIn("gfx/unit.asm:incbin_asset_exists:gfx/missing.2bpp", failed_ids)

    def test_content_scenarios_generate_script_command_stream_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "unit_script.asm").write_text(
                "\n".join(
                    [
                        "UnitScript:",
                        "\topentext",
                        "\twritetext UnitText",
                        "\twaitbutton",
                        "\tclosetext",
                        "\tend",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            out_scenarios = root / "content_scenarios.jsonl"

            report = build_content_scenario_report(
                source_files=("scripts/unit_script.asm",),
                out_scenarios="content_scenarios.jsonl",
                max_cases=4,
                seed=7,
                root=root,
            )
            rows = [
                json.loads(line)
                for line in out_scenarios.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        scenario = report["scenarios"][0]
        probe_ids = {probe["id"] for probe in scenario["behavioral_probes"]}
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["scenario_count"], 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(scenario["scenario_type"], "script_command_stream")
        self.assertEqual(scenario["trigger"]["script"], "UnitScript")
        self.assertEqual(scenario["state_preconditions"][0]["kind"], "script_entry")
        self.assertEqual(scenario["state_preconditions"][0]["values"]["script_label"], "UnitScript")
        self.assertIn("wScriptPos", scenario["state_preconditions"][0]["watch_symbols"])
        self.assertIn("UnitScript", scenario["runtime_targets"]["script_symbols"])
        self.assertIn("RunScriptCommand", scenario["runtime_targets"]["trace_symbols"])
        self.assertIn("content_runtime_setup_route", probe_ids)
        self.assertIn("content_state_materialization_route", probe_ids)
        self.assertIn("content_positioned_instruction_trace_route", probe_ids)
        self.assertIn("content_script_provenance", probe_ids)
        self.assertIn("--symbol RunScriptCommand", commands)
        self.assertIn("trace-instructions --report .local\\tmp\\debugger_content_state_content_scenario_7_0000.json", commands)
        self.assertIn("tools.debugger expect --source-file scripts/unit_script.asm --expect contains=opentext", commands)

    def test_content_scenarios_generate_text_block_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "text").mkdir()
            (root / "text" / "unit_text.asm").write_text(
                "\n".join(
                    [
                        "UnitText:",
                        "\ttext \"HELLO\"",
                        "\tline \"THERE\"",
                        "\tdone",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            out_scenarios = root / "content_scenarios.jsonl"

            report = build_content_scenario_report(
                source_files=("text/unit_text.asm",),
                out_scenarios="content_scenarios.jsonl",
                max_cases=4,
                seed=9,
                root=root,
            )
            rows = [
                json.loads(line)
                for line in out_scenarios.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        scenario = report["scenarios"][0]
        probe_ids = {probe["id"] for probe in scenario["behavioral_probes"]}
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["scenario_count"], 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(scenario["scenario_type"], "text_block")
        self.assertEqual(scenario["trigger"]["text"], "UnitText")
        self.assertIn("UnitText", scenario["runtime_targets"]["script_symbols"])
        self.assertIn("PrintText", scenario["runtime_targets"]["trace_symbols"])
        self.assertIn("content_runtime_setup_route", probe_ids)
        self.assertIn("content_script_provenance", probe_ids)
        self.assertIn("--symbol PrintText", commands)
        self.assertIn("tools.debugger expect --source-file text/unit_text.asm --expect contains=text", commands)

    def test_content_scenarios_generate_movement_data_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "unit_movement.asm").write_text(
                "\n".join(
                    [
                        "UnitMovement:",
                        "\tstep LEFT",
                        "\tturn_head UP",
                        "\tstep_end",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            out_scenarios = root / "content_scenarios.jsonl"

            report = build_content_scenario_report(
                source_files=("scripts/unit_movement.asm",),
                out_scenarios="content_scenarios.jsonl",
                max_cases=4,
                seed=11,
                root=root,
            )
            rows = [
                json.loads(line)
                for line in out_scenarios.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        scenario = report["scenarios"][0]
        probe_ids = {probe["id"] for probe in scenario["behavioral_probes"]}
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["scenario_count"], 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(scenario["scenario_type"], "movement_data")
        self.assertEqual(scenario["trigger"]["movement"], "UnitMovement")
        self.assertEqual(scenario["state_preconditions"][0]["kind"], "movement_entry")
        self.assertEqual(scenario["state_preconditions"][0]["values"]["movement_label"], "UnitMovement")
        self.assertEqual(scenario["state_preconditions"][0]["values"]["object_id"], 0)
        self.assertIn("wMovementPointer", scenario["state_preconditions"][0]["watch_symbols"])
        self.assertIn("UnitMovement", scenario["runtime_targets"]["script_symbols"])
        self.assertIn("ApplyMovement", scenario["runtime_targets"]["trace_symbols"])
        self.assertIn("HandleMovementData", scenario["runtime_targets"]["trace_symbols"])
        self.assertIn("wMovementDataAddress", scenario["runtime_targets"]["watch_symbols"])
        self.assertEqual(scenario["runtime_targets"]["runtime_route"], "movement_engine")
        self.assertIn("content_runtime_setup_route", probe_ids)
        self.assertIn("content_script_provenance", probe_ids)
        self.assertIn("content_positioned_instruction_trace_route", probe_ids)
        self.assertIn("--symbol ApplyMovement", commands)
        self.assertIn("trace-instructions --report .local\\tmp\\debugger_content_state_content_scenario_11_0000.json", commands)
        self.assertIn("tools.debugger expect --source-file scripts/unit_movement.asm --expect contains=movement", commands)

    def test_content_scenarios_generates_map_event_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "UnitMap_MapEvents:",
                        "\tdef_warp_events",
                        "\twarp_event 1, 2, ROUTE_29, 1",
                        "\tdef_coord_events",
                        "\tcoord_event 2, 3, SCENE_UNITMAP, UnitMapScene",
                        "\tdef_bg_events",
                        "\tbg_event 4, 5, BGEVENT_READ, UnitMapSign",
                        "\tdef_object_events",
                        "\tobject_event 6, 7, SPRITE_CHRIS, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, 0, OBJECTTYPE_SCRIPT, 0, UnitMapNPCScript, -1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            out_scenarios = root / "content_scenarios.jsonl"

            report = build_content_scenario_report(
                source_files=("maps/UnitMap.asm",),
                out_scenarios="content_scenarios.jsonl",
                max_cases=8,
                seed=5,
                root=root,
            )
            rows = [
                json.loads(line)
                for line in out_scenarios.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        scenario_types = {item["scenario_type"] for item in report["scenarios"]}
        commands = "\n".join(report["commands"])
        bg_scenario = next(item for item in report["scenarios"] if item["scenario_type"] == "map_bg_event")
        object_scenario = next(item for item in report["scenarios"] if item["scenario_type"] == "map_object_event")
        bg_probe_ids = {probe["id"] for probe in bg_scenario["behavioral_probes"]}

        self.assertTrue(report["valid"])
        self.assertEqual(report["scenario_count"], 4)
        self.assertGreaterEqual(report["runtime_probe_count"], 4)
        self.assertEqual(len(rows), 4)
        self.assertEqual(report["scenario_manifest"]["record_count"], 4)
        self.assertIn("map_warp", scenario_types)
        self.assertIn("map_coord_event", scenario_types)
        self.assertIn("map_bg_event", scenario_types)
        self.assertIn("map_object_event", scenario_types)
        self.assertIn("tools.debugger replay --changed-file maps/UnitMap.asm --scenario-id", commands)
        self.assertGreater(report["behavioral_probe_count"], 0)
        self.assertEqual(report["scenarios"][0]["behavioral_probe_count"], len(report["scenarios"][0]["behavioral_probes"]))
        self.assertIn(
            "content_replay_route",
            {probe["id"] for probe in report["scenarios"][0]["behavioral_probes"]},
        )
        self.assertIn(
            "--scenario content_scenarios.jsonl --scenario-id content_scenario_5_0000",
            commands,
        )
        self.assertIn("content_runtime_setup_route", bg_probe_ids)
        self.assertIn("content_runtime_trace_route", bg_probe_ids)
        self.assertIn("content_runtime_watch_route", bg_probe_ids)
        self.assertIn("content_state_materialization_route", bg_probe_ids)
        self.assertIn("content_state_execution_route", bg_probe_ids)
        self.assertIn("content_positioned_replay_route", bg_probe_ids)
        self.assertIn("content_positioned_instruction_trace_route", bg_probe_ids)
        self.assertIn("content_script_provenance", bg_probe_ids)
        self.assertIn("CheckFacingBGEvent", bg_scenario["runtime_targets"]["trace_symbols"])
        self.assertIn("UnitMapSign", bg_scenario["runtime_targets"]["script_symbols"])
        self.assertIn("wMapGroup", bg_scenario["runtime_targets"]["watch_symbols"])
        self.assertIn("UnitMapNPCScript", object_scenario["related_symbols"])
        self.assertIn("--symbol CheckFacingBGEvent", commands)
        self.assertIn("--watch-symbol wMapGroup", commands)
        self.assertIn("tools.debugger content-state", commands)
        self.assertIn("tools.debugger trace-instructions --report .local\\tmp\\debugger_content_state_content_scenario_5_0002.json", commands)
        self.assertIn("tools.debugger expect --source-file maps/UnitMap.asm --expect contains=warp_event", commands)

    def test_content_scenarios_feed_replay_localize_and_coverage_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "home").mkdir()
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "UnitMap_MapEvents:",
                        "\tdef_bg_events",
                        "\tbg_event 4, 5, BGEVENT_READ, UnitMapSign",
                        "UnitMapSign:",
                        "\tjumptext UnitMapText",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "home" / "map.asm").write_text(
                "\n".join(
                    [
                        "CheckFacingBGEvent:",
                        "\tcall CheckBGEventFlag",
                        "\tret",
                        "CheckBGEventFlag:",
                        "\tret",
                        "CallScript:",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "01:4000 UnitMap_MapEvents",
                        "01:4010 UnitMapSign",
                        "00:5000 CheckFacingBGEvent",
                        "00:5010 CheckBGEventFlag",
                        "00:5020 CallScript",
                        "01:D000 wMapGroup",
                        "01:D001 wMapNumber",
                        "01:D002 wXCoord",
                        "01:D003 wYCoord",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            scenario_report = build_content_scenario_report(
                source_files=("maps/UnitMap.asm",),
                out_scenarios="content_scenarios.jsonl",
                root=root,
            )
            (root / "content_scenarios.json").write_text(json.dumps(scenario_report), encoding="utf-8")

            replay = build_replay_plan(reports=("content_scenarios.json",), root=root)
            localized = build_localization_plan(reports=("content_scenarios.json",), root=root)
            coverage = build_coverage_report(reports=("content_scenarios.json",), root=root)

        localized_ids = {candidate["id"] for candidate in localized["candidates"]}
        covered = {target["id"]: target for target in coverage["targets"]}

        self.assertTrue(replay["valid"])
        self.assertTrue(localized["valid"])
        self.assertTrue(coverage["valid"])
        self.assertIn("CheckFacingBGEvent", replay["replay_targets"]["symbols"])
        self.assertIn("wMapGroup", replay["replay_targets"]["watch_symbols"])
        self.assertNotIn("wMapGroup", replay["replay_targets"]["symbols"])
        self.assertIn("UnitMapSign", localized_ids)
        self.assertIn("CheckFacingBGEvent", localized_ids)
        self.assertEqual(covered["maps/UnitMap.asm"]["status"], "covered")
        self.assertEqual(covered["CheckFacingBGEvent"]["status"], "covered")
        self.assertIn("wMapGroup", covered)

    def test_explain_builds_content_scenario_runtime_causal_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "home").mkdir()
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "UnitMap_MapEvents:",
                        "\tdef_bg_events",
                        "\tbg_event 4, 5, BGEVENT_READ, UnitMapSign",
                        "UnitMapSign:",
                        "\tjumptext UnitMapText",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "home" / "map.asm").write_text(
                "\n".join(
                    [
                        "CheckFacingBGEvent:",
                        "\tcall CheckBGEventFlag",
                        "\tret",
                        "CheckBGEventFlag:",
                        "\tret",
                        "CallScript:",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "01:4000 UnitMap_MapEvents",
                        "01:4010 UnitMapSign",
                        "00:5000 CheckFacingBGEvent",
                        "00:5010 CheckBGEventFlag",
                        "00:5020 CallScript",
                        "01:D000 wMapGroup",
                        "01:D001 wMapNumber",
                        "01:D002 wXCoord",
                        "01:D003 wYCoord",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            scenario_report = build_content_scenario_report(
                source_files=("maps/UnitMap.asm",),
                out_scenarios="content_scenarios.jsonl",
                root=root,
            )
            (root / "content_scenarios.json").write_text(json.dumps(scenario_report), encoding="utf-8")

            report = build_explanation_report(reports=("content_scenarios.json",), root=root)

        labels = {
            node["label"]
            for path in report["paths"]
            for node in path.get("nodes", [])
        }
        roles = {
            node["role"]
            for path in report["paths"]
            for node in path.get("nodes", [])
        }
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertGreaterEqual(report["content_scenario_count"], 1)
        self.assertIn("UnitMapSign", labels)
        self.assertIn("CheckFacingBGEvent", labels)
        self.assertIn("wMapGroup", labels)
        self.assertIn("script_label", roles)
        self.assertIn("trace_helper", roles)
        self.assertIn("watch_symbol", roles)
        self.assertIn("tools.debugger replay --report content_scenarios.json", commands)
        self.assertIn("tools.debugger provenance --symbol UnitMapSign", commands)

    def test_cli_content_scenarios_writes_json_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "audio").mkdir()
            source = root / "audio" / "unit.asm"
            source.write_text(
                "Music_Unit:\n\tchannel_count 2\n\tchannel 1, Music_Unit_Ch1\n\tchannel 2, Music_Unit_Ch2\n",
                encoding="utf-8",
            )
            out = root / "content_scenarios.json"
            manifest = root / "content_scenarios.jsonl"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "content-scenarios",
                        "--source-file",
                        str(source),
                        "--out-scenarios",
                        str(manifest),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            rows = [
                json.loads(line)
                for line in manifest.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_content_scenarios")
        audio_rows = [row for row in rows if row["scenario_type"] == "audio_channel_block"]
        self.assertEqual(len(audio_rows), 1)
        self.assertEqual(data["scenario_count"], len(rows))
        self.assertEqual(audio_rows[0]["behavioral_probe_count"], len(audio_rows[0]["behavioral_probes"]))
        self.assertIn("content_replay_route", {probe["id"] for probe in audio_rows[0]["behavioral_probes"]})
        self.assertIn("content_runtime_watch_route", {probe["id"] for probe in audio_rows[0]["behavioral_probes"]})
        self.assertIn("content_state_materialization_route", {probe["id"] for probe in audio_rows[0]["behavioral_probes"]})
        self.assertIn("wMusicID", audio_rows[0]["state_preconditions"][0]["watch_symbols"])
        self.assertIn("wMusicID", audio_rows[0]["runtime_targets"]["watch_symbols"])
        self.assertIn("--watch-symbol wMusicID", "\n".join(data["commands"]))
        self.assertIn("contains=channel_count", "\n".join(data["commands"]))

    def test_investigation_replay_consumes_content_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "test.sym").write_text("00:0000 NULL\n", encoding="utf-8")
            (root / "maps" / "UnitMap.asm").write_text(
                "UnitMap_MapEvents:\n\tdef_warp_events\n\twarp_event 1, 2, ROUTE_29, 1\n",
                encoding="utf-8",
            )

            report = build_investigation_run(
                symbols_path="test.sym",
                changed_files=("maps/UnitMap.asm",),
                out_dir="run",
                max_targets=4,
                max_cases=2,
                root=root,
            )
            replay = json.loads((root / "run" / "03_replay.json").read_text(encoding="utf-8"))

        self.assertTrue(report["valid"])
        self.assertIn("02_content_scenarios", {step["id"] for step in report["steps"]})
        self.assertIn("content_scenario_1_0000", replay["replay_targets"]["scenario_ids"])

    def test_cli_content_mirror_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "audio").mkdir()
            source = root / "audio" / "unit.asm"
            source.write_text(
                "Music_Unit:\n\tchannel_count 2\n\tchannel 1, Music_Unit_Ch1\n\tchannel 2, Music_Unit_Ch2\n",
                encoding="utf-8",
            )
            out = root / "content.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "content-mirror",
                        "--source-file",
                        str(source),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_content_mirror")
        self.assertTrue(data["passed"])
        self.assertGreater(data["invariant_count"], 0)

    def test_cli_compare_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "compare.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "compare",
                        "--symbol",
                        "BossAI_SelectMove",
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_compare_plan")
            self.assertTrue(data["matches"])

    def test_expectation_report_passes_event_and_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_index = root / "trace_index.json"
            trace_index.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_trace_index",
                        "valid": True,
                        "events": [
                            {
                                "event_type": "score_delta",
                                "state_symbol": "wEnemyAIMoveScores",
                                "source_symbol": "BossAI_ApplyMoveModel.ApplyRoleBias",
                                "rule_id": "move.apply_move_model.apply_role_bias",
                                "address": "D0D3",
                                "after": "15",
                                "evidence": ["score_delta"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_expectation_report(
                reports=("trace_index.json",),
                expectations=(
                    "event=score_delta,symbol=wEnemyAIMoveScores",
                    "rule=move.apply_move_model.apply_role_bias",
                ),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertEqual(report["failed_count"], 0)
        self.assertEqual(report["passed_count"], 2)

    def test_expectation_report_fails_missing_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_index = root / "trace_index.json"
            trace_index.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_trace_index",
                        "valid": True,
                        "events": [
                            {
                                "event_type": "watch_change",
                                "state_symbol": "wCurDamage",
                                "source_symbol": "BattleCommand_Test",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_expectation_report(
                reports=("trace_index.json",),
                expectations=("symbol=BossAI_SelectMove",),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertFalse(report["passed"])
        self.assertEqual(report["failed_count"], 1)
        self.assertEqual(report["expectations"][0]["status"], "failed")

    def test_expectation_report_checks_static_source_file_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            source = root / "maps" / "NewBarkTown.asm"
            source.write_text(
                "NewBarkTown_MapScripts:\n\tdef_scene_scripts\n\twarp_event  1,  1, ELMS_LAB, 1\n",
                encoding="utf-8",
            )

            report = build_expectation_report(
                source_files=("maps/NewBarkTown.asm",),
                expectations=("contains=warp_event", "not-contains=TODO"),
                root=root,
            )

        statuses = {item["id"]: item["status"] for item in report["expectations"]}

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertEqual(report["source_artifact_count"], 1)
        self.assertIn("maps/NewBarkTown.asm", report["evidence_summary"]["source_files"])
        self.assertEqual(statuses["cli_contains_warp_event"], "passed")
        self.assertEqual(statuses["cli_not_contains_TODO"], "passed")

    def test_expectation_report_checks_content_scenario_preconditions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario_report = root / "content_scenarios.json"
            scenario_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "map_bg_event",
                                "source_file": "maps/UnitMap.asm",
                                "state_preconditions": [
                                    {
                                        "id": "map_bg_event_position",
                                        "kind": "map_position",
                                        "values": {
                                            "source_file": "maps/UnitMap.asm",
                                            "map_label": "UnitMap_MapEvents",
                                            "script": "UnitMapSign",
                                        },
                                        "watch_symbols": ["wMapGroup", "wMapNumber", "wXCoord", "wYCoord"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_expectation_report(
                reports=("content_scenarios.json",),
                expectations=(
                    "scenario=content_scenario_1_0000",
                    "precondition=map_position,scenario=content_scenario_1_0000,symbol=wMapGroup",
                    "symbol=wMapGroup",
                ),
                root=root,
            )

        statuses = {item["id"]: item["status"] for item in report["expectations"]}

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertEqual(report["evidence_scenario_count"], 1)
        self.assertEqual(report["evidence_state_precondition_count"], 1)
        self.assertEqual(statuses["cli_scenario_content_scenario_1_0000"], "passed")
        self.assertEqual(statuses["cli_precondition_map_position_content_scenario_1_0000_wMapGroup"], "passed")
        self.assertEqual(statuses["cli_symbol_wMapGroup"], "passed")

    def test_expectation_report_checks_content_state_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_state_report = root / "content_state.json"
            content_state_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "executed": True,
                        "out_state": "patched.state",
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0000",
                                "precondition_kind": "map_position",
                                "source_file": "maps/UnitMap.asm",
                                "status": "ready",
                                "patches": [
                                    {
                                        "symbol": "wMapGroup",
                                        "value": 24,
                                        "value_hex": "18",
                                        "bank_address": "01:DA00",
                                    }
                                ],
                            }
                        ],
                        "execution": {
                            "executed": True,
                            "out_state": "patched.state",
                            "applied_patches": [
                                {
                                    "symbol": "wMapGroup",
                                    "value": 24,
                                    "value_hex": "18",
                                    "observed": 24,
                                    "observed_hex": "18",
                                    "verified": True,
                                    "bank_address": "01:DA00",
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_expectation_report(
                reports=("content_state.json",),
                expectations=(
                    "state-patch=wMapGroup,scenario=content_scenario_1_0000,value=0x18",
                    "state-patch=wMapGroup,applied=true,verified=true,value=24",
                    "symbol=wMapGroup",
                ),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertGreaterEqual(report["evidence_state_patch_count"], 2)
        self.assertIn("wMapGroup", report["evidence_summary"]["symbols"])
        self.assertIn("content_scenario_1_0000", report["evidence_summary"]["scenario_ids"])
        self.assertEqual(
            {item["status"] for item in report["expectations"]},
            {"passed"},
        )

    def test_cli_expect_checks_source_file_exists_and_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            source = root / "maps" / "UnitMap.asm"
            source.write_text("UnitMap:\n\tobject_event 1, 1, SPRITE_CHRIS\n", encoding="utf-8")
            out = root / "expect.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "expect",
                        "--source-file",
                        str(source),
                        "--expect",
                        "contains=object_event",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_expectation_report")
        self.assertTrue(data["passed"])
        self.assertEqual(data["source_artifact_count"], 1)

    def test_cli_expect_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_index = root / "trace_index.json"
            trace_index.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_trace_index",
                        "valid": True,
                        "events": [
                            {
                                "event_type": "score_delta",
                                "state_symbol": "wEnemyAIMoveScores",
                                "rule_id": "move.apply_move_model",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "expect.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "expect",
                        "--report",
                        str(trace_index),
                        "--expect",
                        "event=score_delta,symbol=wEnemyAIMoveScores",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_expectation_report")
        self.assertTrue(data["passed"])

    def test_investigation_run_writes_debugger_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "test.sym").write_text(
                "0E:483E BossAI_ApplyMoveModel\n01:D0D3 wEnemyAIMoveScores\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "boss_policy_move.asm").write_text(
                "BossAI_ApplyMoveModel:\n\tld hl, wEnemyAIMoveScores\n\tret\n",
                encoding="utf-8",
            )
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "events": [
                            {
                                "event_type": "score_delta",
                                "score_pointer": "d0d3",
                                "score_before": 20,
                                "score_after": 18,
                                "source": {
                                    "full_symbol": "BossAI_ApplyMoveModel",
                                    "rule_id": "move.apply_move_model.apply_role_bias",
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out_dir = root / "investigation"

            report = build_investigation_run(
                traces=("trace.json",),
                symbols_path="test.sym",
                symbols=("BossAI_ApplyMoveModel",),
                addresses=("D0D3",),
                rules=("move.apply_move_model.apply_role_bias",),
                expectations=("event=score_delta,symbol=wEnemyAIMoveScores",),
                out_dir=str(out_dir),
                max_targets=6,
                max_cases=4,
                root=root,
            )
            step_ids = {step["id"] for step in report["steps"]}
            ingest_written = (out_dir / "01_ingest.json").exists()
            impact_written = (out_dir / "12_impact.json").exists()
            static_written = (out_dir / "investigation_report.md").exists()
            visualization_written = (out_dir / "investigation_visualization.md").exists()

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertEqual(report["kind"], "unified_debugger_investigation_run")
        self.assertIn("02_trace_index", step_ids)
        self.assertIn("08_expect", step_ids)
        self.assertGreaterEqual(report["produced_report_count"], 10)
        self.assertTrue(ingest_written)
        self.assertTrue(impact_written)
        self.assertTrue(static_written)
        self.assertTrue(visualization_written)

    def test_investigation_run_builds_state_space_from_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "data" / "types").mkdir(parents=True)
            (root / "test.sym").write_text(
                "0E:483E BossAI_ApplyMoveModel\n"
                "01:D0D3 wEnemyAIMoveScores\n"
                "01:D1EC wTypeMatchup\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "boss_policy_move.asm").write_text(
                "BossAI_ApplyMoveModel:\n\tld hl, wEnemyAIMoveScores\n\tret\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "late_gen_held_items.asm").write_text(
                "AirBalloon:\n\tret\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "effect_commands.asm").write_text(
                "BattleCommand_DamageCalc:\n\tret\n",
                encoding="utf-8",
            )
            (root / "data" / "types" / "type_matchups.asm").write_text(
                "TypeMatchups:\n\tdb 0\n",
                encoding="utf-8",
            )
            out_dir = root / "investigation"

            report = build_investigation_run(
                symbols_path="test.sym",
                patches=("wTypeMatchup=0x00",),
                watch_symbols=("wEnemyAIMoveScores",),
                changed_files=("engine/battle/ai/boss_policy_move.asm",),
                symptom="AI chose Ground move into Air Balloon immunity",
                out_dir=str(out_dir),
                max_targets=6,
                max_cases=4,
                root=root,
            )
            state_space = json.loads(
                (out_dir / "02_state_space.json").read_text(encoding="utf-8")
            )
            replay = json.loads(
                (out_dir / "03_replay.json").read_text(encoding="utf-8")
            )
            ranked = json.loads(
                (out_dir / "11_rank.json").read_text(encoding="utf-8")
            )
            impact = json.loads(
                (out_dir / "12_impact.json").read_text(encoding="utf-8")
            )

        step_ids = {step["id"] for step in report["steps"]}
        ranked_types = {item["type"] for item in ranked["findings"]}
        impact_types = {item["type"] for item in impact["items"]}

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertIn("02_state_space", step_ids)
        self.assertEqual(report["patches"], ["wTypeMatchup=0x00"])
        self.assertIn("wTypeMatchup", report["effective_watch_symbols"])
        self.assertEqual(state_space["kind"], "unified_debugger_state_space")
        self.assertEqual(state_space["state_space"]["patches"][0]["symbol"], "wTypeMatchup")
        self.assertIn("wTypeMatchup", replay["replay_targets"]["watch_symbols"])
        self.assertIn("state_space_ready", ranked_types)
        self.assertIn("state_space_ready", impact_types)

    def test_cli_investigate_writes_json_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            symbols = root / "test.sym"
            symbols.write_text(
                "0E:483E BossAI_ApplyMoveModel\n01:D0D3 wEnemyAIMoveScores\n",
                encoding="utf-8",
            )
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "events": [
                            {
                                "event_type": "score_delta",
                                "score_pointer": "d0d3",
                                "score_before": 20,
                                "score_after": 18,
                                "source": {
                                    "full_symbol": "BossAI_ApplyMoveModel",
                                    "rule_id": "move.apply_move_model.apply_role_bias",
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out_dir = root / "run"
            out = root / "investigation.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "investigate",
                        "--trace",
                        str(trace),
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "BossAI_ApplyMoveModel",
                        "--patch",
                        "wEnemyAIMoveScores=0x12",
                        "--address",
                        "D0D3",
                        "--expect",
                        "event=score_delta,symbol=wEnemyAIMoveScores",
                        "--out-dir",
                        str(out_dir),
                        "--max-targets",
                        "6",
                        "--max-cases",
                        "4",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            seeds_written = (out_dir / "generated_seeds.jsonl").exists()

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_investigation_run")
        self.assertTrue(data["passed"])
        self.assertEqual(data["patches"], ["wEnemyAIMoveScores=0x12"])
        self.assertIn("wEnemyAIMoveScores", data["effective_watch_symbols"])
        self.assertTrue(data["static_report"])
        self.assertTrue(data["visualization"])
        self.assertTrue(seeds_written)

    def test_rank_findings_orders_failures_above_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gate_report = root / "gate.json"
            gate_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_gate_plan",
                        "steps": [
                            {
                                "status": "failed",
                                "command": "python test.py",
                                "stderr_tail": ["boom"],
                                "stdout_tail": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            compare_report = root / "compare.json"
            compare_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_compare_plan",
                        "matches": [
                            {
                                "id": "static",
                                "gaps": ["not dynamic"],
                                "materialization_commands": ["prove"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = rank_findings(
                reports=("gate.json", "compare.json"),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["findings"][0]["type"], "gate_failed")
        self.assertEqual(report["findings"][1]["type"], "compare_gap")

    def test_rank_findings_promotes_runtime_state_impossibilities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_report = root / "runtime_state.json"
            runtime_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_runtime_state_report",
                        "save_state": "for_codex1.sgm",
                        "passed": False,
                        "commands": ["python -m tools.debugger state-inspect"],
                        "findings": [
                            {
                                "id": "invalid_script_pc",
                                "type": "runtime_state_impossible",
                                "severity": 94,
                                "confidence": 0.9,
                                "title": "Script VM is running from an invalid ROM address",
                                "evidence": ["wScriptBank:wScriptPos=B4:0002"],
                                "next_actions": ["python -m tools.debugger watch --watch-symbol wScriptBank"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = rank_findings(reports=("runtime_state.json",), root=root)

        self.assertTrue(report["valid"])
        self.assertEqual(report["findings"][0]["type"], "runtime_state_impossible")
        self.assertGreaterEqual(report["findings"][0]["severity"], 94)
        self.assertIn("B4:0002", report["findings"][0]["evidence"][0])

    def test_rank_findings_calibrates_rom_surface_severity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            coverage_report = root / "coverage.json"
            coverage_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_coverage_report",
                        "uncovered_targets": [
                            {
                                "type": "source_file",
                                "id": "docs/notes.md",
                                "commands": [
                                    "python -m tools.debugger coverage --changed-file docs/notes.md"
                                ],
                            },
                            {
                                "type": "source_file",
                                "id": "home/bankswitch.asm",
                                "commands": [
                                    "python -m tools.debugger coverage --changed-file home/bankswitch.asm"
                                ],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = rank_findings(reports=("coverage.json",), root=root)

        first = report["findings"][0]

        self.assertTrue(report["valid"])
        self.assertIn("home/bankswitch.asm", first["title"])
        self.assertEqual(first["surface"], "ROM banking / ABI")
        self.assertGreater(first["severity"], first["severity_base"])
        self.assertIn("ROM surface calibration: ROM banking / ABI (+10)", first["evidence"])

    def test_rank_and_impact_consume_content_mirror_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_report = root / "content.json"
            content_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_mirror",
                        "valid": True,
                        "passed": False,
                        "invariant_count": 1,
                        "invariants": [
                            {
                                "id": "maps/UnitMap.asm:incbin_asset_exists:gfx/missing.2bpp",
                                "type": "incbin_asset_exists",
                                "status": "failed",
                                "severity": 78,
                                "title": "Missing INCBIN asset: gfx/missing.2bpp",
                                "source_file": "maps/UnitMap.asm",
                                "evidence": ["asset=gfx/missing.2bpp"],
                                "commands": [
                                    "python -m tools.debugger content-mirror --source-file maps/UnitMap.asm"
                                ],
                                "related_files": ["maps/UnitMap.asm", "gfx/missing.2bpp"],
                            }
                        ],
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("content.json",), root=root)
            impact = build_impact_report(reports=("content.json",), root=root)

        self.assertTrue(ranked["valid"])
        self.assertEqual(ranked["findings"][0]["type"], "content_mirror_failed")
        self.assertTrue(impact["valid"])
        self.assertEqual(impact["items"][0]["type"], "content_mirror_failed")
        self.assertIn("Maps, scripts, and text", {item["surface"] for item in impact["items"]})

    def test_rank_and_impact_consume_content_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario_report = root / "content_scenarios.json"
            scenario_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenario_count": 1,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "map_warp",
                                "proof_level": "semantic_source",
                                "source_file": "maps/UnitMap.asm",
                                "line": 3,
                                "expected": ["destination_map=ROUTE_29"],
                                "commands": [
                                    "python -m tools.debugger replay --changed-file maps/UnitMap.asm --scenario-id content_scenario_1_0000"
                                ],
                            }
                        ],
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("content_scenarios.json",), root=root)
            impact = build_impact_report(reports=("content_scenarios.json",), root=root)

        self.assertTrue(ranked["valid"])
        self.assertIn("content_scenario", {item["type"] for item in ranked["findings"]})
        self.assertTrue(impact["valid"])
        self.assertIn("content_scenario", {item["type"] for item in impact["items"]})
        self.assertIn("Maps, scripts, and text", {item["surface"] for item in impact["items"]})

    def test_rank_and_impact_consume_content_state_materializations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_state_report = root / "content_state.json"
            content_state_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "executed": True,
                        "out_state": "patched.state",
                        "materialization_count": 2,
                        "patch_count": 1,
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0000",
                                "scenario_type": "map_bg_event",
                                "precondition_kind": "map_position",
                                "source_file": "maps/UnitMap.asm",
                                "map_name": "UnitMap",
                                "map_resolution": {
                                    "source_file": "data/maps/maps.asm",
                                    "map_group": 24,
                                    "map_number": 3,
                                },
                                "status": "ready",
                                "patches": [
                                    {
                                        "symbol": "wMapGroup",
                                        "value": 24,
                                        "value_hex": "18",
                                        "bank_address": "01:DA00",
                                    }
                                ],
                            },
                            {
                                "scenario_id": "content_scenario_2_0000",
                                "precondition_kind": "map_position",
                                "source_file": "maps/MissingMap.asm",
                                "map_name": "MissingMap",
                                "status": "blocked",
                                "patches": [],
                                "errors": ["map not found in data/maps/maps.asm: MissingMap"],
                            },
                        ],
                        "execution": {
                            "executed": True,
                            "out_state": "patched.state",
                            "applied_patches": [
                                {
                                    "symbol": "wMapGroup",
                                    "value": 24,
                                    "value_hex": "18",
                                    "observed": 24,
                                    "observed_hex": "18",
                                    "verified": True,
                                    "bank_address": "01:DA00",
                                }
                            ],
                        },
                        "commands": [
                            "python -m tools.debugger content-state --report content_scenarios.json --execute"
                        ],
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("content_state.json",), root=root)
            impact = build_impact_report(reports=("content_state.json",), root=root)

        ranked_types = [item["type"] for item in ranked["findings"]]
        ranked_actions = "\n".join(
            action
            for finding in ranked["findings"]
            for action in finding["next_actions"]
        )
        impact_types = {item["type"] for item in impact["items"]}
        ready_item = next(item for item in impact["items"] if item["type"] == "content_state_ready")

        self.assertTrue(ranked["valid"])
        self.assertIn("content_state_ready", ranked_types)
        self.assertIn("content_state_blocked", ranked_types)
        self.assertIn("content_state_executed", ranked_types)
        self.assertLess(ranked_types.index("content_state_blocked"), ranked_types.index("content_state_ready"))
        self.assertIn(
            "tools.debugger expect --report content_state.json --expect state-patch=wMapGroup,scenario=content_scenario_1_0000,value=0x18",
            ranked_actions,
        )
        self.assertIn(
            "tools.debugger replay --report content_state.json --scenario-id content_scenario_1_0000 --execute-watch",
            ranked_actions,
        )
        self.assertIn(
            "tools.debugger watch --watch-symbol wMapGroup --save-state patched.state --execute",
            ranked_actions,
        )
        self.assertTrue(impact["valid"])
        self.assertIn("content_state_ready", impact_types)
        self.assertIn("content_state_blocked", impact_types)
        self.assertIn("content_state_executed", impact_types)
        self.assertIn("wMapGroup", ready_item["related_symbols"])
        self.assertIn("maps/UnitMap.asm", ready_item["related_files"])
        self.assertIn("data/maps/maps.asm", ready_item["related_files"])

    def test_rank_and_impact_consume_instruction_trace_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "missed_trace.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": False,
                        "executed": True,
                        "effective_save_state": "content.state",
                        "captured_frame_count": 0,
                        "functions": [
                            {
                                "symbol": "ApplyMovement",
                                "instruction_count": 4,
                                "hook_count": 4,
                            }
                        ],
                        "watches": [{"name": "wMovementPointer"}],
                        "execution_validation": {
                            "attempted": True,
                            "required": True,
                            "planned_hook_count": 4,
                            "captured_frame_count": 0,
                            "hit": False,
                            "hit_function_symbols": [],
                            "missing_function_symbols": ["ApplyMovement"],
                            "watch_symbols": ["wMovementPointer"],
                            "ready_for_dynamic_taint": False,
                        },
                        "trace_output": {
                            "path": ".local\\tmp\\missed_trace.jsonl",
                            "written": True,
                            "record_count": 0,
                        },
                        "commands": [
                            "python -m tools.debugger trace-instructions --report content_state.json --scenario-id content_scenario_1_0000 --execute --require-hit"
                        ],
                        "errors": ["instruction trace executed but none of the selected hooks fired"],
                        "warnings": [],
                    }
                ),
                encoding="utf-8",
            )
            (root / "ready_trace.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": True,
                        "executed": True,
                        "effective_save_state": "content.state",
                        "captured_frame_count": 2,
                        "functions": [
                            {
                                "symbol": "RunScriptCommand",
                                "instruction_count": 5,
                                "hook_count": 5,
                            }
                        ],
                        "watches": [{"name": "wScriptPos"}],
                        "execution_validation": {
                            "attempted": True,
                            "required": True,
                            "planned_hook_count": 5,
                            "captured_frame_count": 2,
                            "hit": True,
                            "hit_function_symbols": ["RunScriptCommand"],
                            "missing_function_symbols": [],
                            "watch_symbols": ["wScriptPos"],
                            "ready_for_dynamic_taint": True,
                            "trace_record_limit_hit": False,
                        },
                        "trace_output": {
                            "path": ".local\\tmp\\ready_trace.jsonl",
                            "written": True,
                            "record_count": 2,
                        },
                        "commands": [],
                        "errors": [],
                        "warnings": [],
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("missed_trace.json", "ready_trace.json"), root=root)
            impact = build_impact_report(reports=("missed_trace.json", "ready_trace.json"), root=root)

        ranked_types = [item["type"] for item in ranked["findings"]]
        ranked_actions = "\n".join(
            action
            for finding in ranked["findings"]
            for action in finding["next_actions"]
        )
        impact_types = {item["type"] for item in impact["items"]}
        ready_item = next(item for item in impact["items"] if item["type"] == "instruction_trace_ready")
        miss_item = next(item for item in impact["items"] if item["type"] == "instruction_trace_miss")

        self.assertTrue(ranked["valid"])
        self.assertEqual(ranked_types[0], "instruction_trace_miss")
        self.assertIn("instruction_trace_miss", ranked_types)
        self.assertIn("instruction_trace_ready", ranked_types)
        self.assertLess(ranked_types.index("instruction_trace_miss"), ranked_types.index("instruction_trace_ready"))
        self.assertIn(
            "tools.debugger dynamic-taint --trace .local\\tmp\\ready_trace.jsonl --sink-symbol wScriptPos",
            ranked_actions,
        )
        self.assertIn("instruction_trace_miss", impact_types)
        self.assertIn("instruction_trace_ready", impact_types)
        self.assertIn("RunScriptCommand", ready_item["related_symbols"])
        self.assertIn("wScriptPos", ready_item["related_symbols"])
        self.assertIn("ApplyMovement", miss_item["related_symbols"])

    def test_impact_report_prioritizes_gate_failure_over_coverage_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gate_report = root / "gate.json"
            gate_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_gate_plan",
                        "steps": [
                            {
                                "status": "failed",
                                "command": "python tools\\audit\\check_release_smoke.py",
                                "stderr_tail": ["release smoke failed"],
                                "stdout_tail": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            coverage_report = root / "coverage.json"
            coverage_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_coverage_report",
                        "uncovered_targets": [
                            {
                                "type": "symbol",
                                "id": "BattleCommand_DamageCalc",
                                "commands": [
                                    "python -m tools.debugger localize --symbol BattleCommand_DamageCalc"
                                ],
                                "related_files": ["engine/battle/effect_commands.asm"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_impact_report(
                reports=("gate.json", "coverage.json"),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["items"][0]["type"], "gate_failed")
        self.assertGreater(
            report["items"][0]["impact_score"],
            report["items"][-1]["impact_score"],
        )
        self.assertIn(
            "python tools\\audit\\check_release_smoke.py",
            report["commands"],
        )

    def test_impact_report_classifies_boss_ai_score_delta_as_boss_ai(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_index = root / "trace_index.json"
            trace_index.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_trace_index",
                        "valid": True,
                        "events": [
                            {
                                "event_type": "score_delta",
                                "state_symbol": "wEnemyAIMoveScores",
                                "source_symbol": "BossAI_ApplyMoveModel",
                                "rule_id": "move.apply_move_model",
                                "evidence": ["event_type=score_delta"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_impact_report(reports=("trace_index.json",), root=root)

        surfaces = {item["surface"] for item in report["items"]}

        self.assertTrue(report["valid"])
        self.assertIn("Boss AI", surfaces)

    def test_cli_impact_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            coverage_report = root / "coverage.json"
            coverage_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_coverage_report",
                        "uncovered_targets": [
                            {
                                "type": "source_file",
                                "id": "engine/battle/effect_commands.asm",
                                "commands": [
                                    "python -m tools.debugger gate --changed-file engine/battle/effect_commands.asm"
                                ],
                                "related_symbols": ["wCurDamage"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "impact.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "impact",
                        "--report",
                        str(coverage_report),
                        "--symbol",
                        "wCurDamage",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_impact_report")
        self.assertGreater(data["impact_count"], 0)
        self.assertIn("Battle damage", {item["surface"] for item in data["items"]})

    def test_cli_rank_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ingest_report = root / "ingest.json"
            ingest_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_ingest_manifest",
                        "artifacts": [
                            {
                                "kind": "scenario",
                                "path": "bad.jsonl",
                                "errors": ["invalid JSON"],
                                "warnings": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "rank.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "rank",
                        "--report",
                        str(ingest_report),
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_ranked_findings")
            self.assertEqual(data["findings"][0]["type"], "ingest_error")

    def test_visualization_report_builds_timeline_waterfall_and_graph(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "events": [
                            {
                                "frame": 3,
                                "watch": "wCurDamage",
                                "old_hex": "0000",
                                "new_hex": "002A",
                                "pc_label": "BattleCommand_Test",
                                "pc_bank_address": "01:4000",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            explain_report = root / "explain.json"
            explain_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_causal_explanation",
                        "valid": True,
                        "paths": [
                            {
                                "id": "event_1",
                                "title": "wCurDamage changed",
                                "score": 95,
                                "confidence": 0.93,
                                "nodes": [
                                    {
                                        "id": "state",
                                        "label": "wCurDamage",
                                        "type": "state",
                                    },
                                    {
                                        "id": "source",
                                        "label": "BattleCommand_Test",
                                        "type": "source",
                                    },
                                ],
                                "edges": [
                                    {
                                        "from": "state",
                                        "to": "source",
                                        "relation": "write",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            replay_report = root / "replay.json"
            replay_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_replay_plan",
                        "valid": True,
                        "phase_steps": [
                            {
                                "phase": "reproduce",
                                "steps": [
                                    {
                                        "command": "python -m tools.debugger watch --watch-symbol wCurDamage",
                                        "reason": "observe the changed byte",
                                        "runnable": True,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            dynamic_report = root / "dynamic_write.json"
            dynamic_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_dynamic_taint_report",
                        "valid": True,
                        "write_attribution_count": 1,
                        "write_attributions": [
                            {
                                "target": "wCurDamage",
                                "pc_label": "BattleCommand_Test",
                                "seq": 7,
                                "address": "D141",
                                "mnemonic": "ld [$d141], a",
                                "score": 72,
                                "related_symbols": ["wCurDamage", "BattleCommand_Test"],
                                "related_files": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_visualization_report(
                reports=("watch.json", "explain.json", "replay.json", "dynamic_write.json"),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertGreaterEqual(report["timeline_event_count"], 4)
        self.assertEqual(report["waterfall_step_count"], 1)
        self.assertGreaterEqual(report["graph_edge_count"], 3)
        self.assertFalse(report["interactive"])
        self.assertGreater(report["inspector_item_count"], 0)
        self.assertIn("timeline", report["mermaid_timeline"])
        self.assertIn("BattleCommand_Test", report["mermaid_graph"])
        self.assertIn("dynamic_write", report["content"])
        self.assertIn("Workflow Waterfall", report["content"])

    def test_cli_visualize_writes_static_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "events": [
                            {
                                "frame": 1,
                                "watch": "wCurDamage",
                                "old_hex": "00",
                                "new_hex": "01",
                                "pc_label": "BattleCommand_Test",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "visualization.html"
            json_out = root / "visualization.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "visualize",
                        "--report",
                        str(watch_report),
                        "--format",
                        "html",
                        "--out",
                        str(out),
                        "--json-out",
                        str(json_out),
                    ]
                )

            content = out.read_text(encoding="utf-8")
            data = json.loads(json_out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("<!doctype html>", content)
        self.assertIn('data-kind="interactive-inspector"', content)
        self.assertIn('id="evidence-search"', content)
        self.assertIn("debugger-visualization-data", content)
        self.assertEqual(data["kind"], "unified_debugger_visualization")
        self.assertTrue(data["interactive"])
        self.assertGreaterEqual(data["timeline_event_count"], 1)
        self.assertGreater(data["inspector_item_count"], 0)

    def test_visualization_consumes_content_behavioral_probes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario_report = root / "content_scenarios.json"
            scenario_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "map_warp",
                                "source_file": "maps/UnitMap.asm",
                                "line": 4,
                                "runtime_targets": {
                                    "source_symbols": ["UnitMap_MapEvents"],
                                    "trace_symbols": ["WarpCheck", "ReadMapEvents"],
                                    "watch_symbols": ["wMapGroup"],
                                },
                                "behavioral_probes": [
                                    {
                                        "id": "content_replay_route",
                                        "phase": "replay",
                                        "proof_level": "runtime_planned",
                                        "command": "python -m tools.debugger replay --scenario content.jsonl --scenario-id content_scenario_1_0000",
                                        "reason": "prove in ROM when positioned",
                                        "runnable": True,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_visualization_report(reports=("content_scenarios.json",), root=root)

        self.assertTrue(report["valid"])
        self.assertEqual(report["waterfall_step_count"], 1)
        graph_node_types = {node["type"] for node in report["graph"]["nodes"]}
        self.assertIn("behavioral_probe", graph_node_types)
        self.assertIn("runtime_helper", graph_node_types)
        self.assertIn("runtime_watch", graph_node_types)
        self.assertIn("content_replay_route", report["mermaid_graph"])
        self.assertIn("WarpCheck", report["mermaid_graph"])
        self.assertIn("wMapGroup", report["mermaid_graph"])
        self.assertIn("python -m tools.debugger replay", report["content"])

    def test_visualization_consumes_content_state_materializations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_state_report = root / "content_state.json"
            content_state_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "executed": True,
                        "out_state": "patched.state",
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0000",
                                "precondition_kind": "map_position",
                                "source_file": "maps/UnitMap.asm",
                                "map_name": "UnitMap",
                                "map_resolution": {
                                    "source_file": "data/maps/maps.asm",
                                    "map_group": 24,
                                    "map_number": 3,
                                },
                                "status": "ready",
                                "patches": [
                                    {
                                        "symbol": "wMapGroup",
                                        "value": 24,
                                        "value_hex": "18",
                                        "bank_address": "01:DA00",
                                    }
                                ],
                                "commands": [
                                    "python -m tools.debugger watch --watch-symbol wMapGroup --execute --save-state <patched-state>"
                                ],
                            }
                        ],
                        "execution": {
                            "executed": True,
                            "out_state": "patched.state",
                            "applied_patches": [
                                {
                                    "symbol": "wMapGroup",
                                    "value": 24,
                                    "value_hex": "18",
                                    "verified": True,
                                    "bank_address": "01:DA00",
                                }
                            ],
                        },
                        "commands": [
                            "python -m tools.debugger content-state --report content_scenarios.json --execute"
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_visualization_report(reports=("content_state.json",), root=root)

        graph_node_types = {node["type"] for node in report["graph"]["nodes"]}
        lanes = {lane["lane"] for lane in report["lane_summary"]}

        self.assertTrue(report["valid"])
        self.assertGreaterEqual(report["timeline_event_count"], 2)
        self.assertGreaterEqual(report["waterfall_step_count"], 2)
        self.assertIn("content_state", lanes)
        self.assertIn("content_state_materialization", graph_node_types)
        self.assertIn("runtime_state_patch", graph_node_types)
        self.assertIn("save_state", graph_node_types)
        self.assertIn("wMapGroup", report["mermaid_graph"])
        self.assertIn("patched.state", report["mermaid_graph"])
        self.assertIn("python -m tools.debugger content-state", report["content"])

    def test_visualization_consumes_instruction_trace_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_report = root / "instruction_trace.json"
            trace_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": True,
                        "executed": True,
                        "effective_save_state": "patched.state",
                        "captured_frame_count": 2,
                        "functions": [
                            {
                                "symbol": "RunScriptCommand",
                                "instruction_count": 5,
                                "hook_count": 5,
                                "instructions": [
                                    {
                                        "bank_address": "01:4000",
                                        "mnemonic": "ld a, [$d15e]",
                                    }
                                ],
                            },
                            {
                                "symbol": "CallScript",
                                "instruction_count": 2,
                                "hook_count": 2,
                                "instructions": [],
                            },
                        ],
                        "watches": [{"name": "wScriptPos"}],
                        "execution_validation": {
                            "attempted": True,
                            "required": True,
                            "planned_hook_count": 7,
                            "captured_frame_count": 2,
                            "hit": True,
                            "hit_function_symbols": ["RunScriptCommand"],
                            "missing_function_symbols": ["CallScript"],
                            "watch_symbols": ["wScriptPos"],
                            "ready_for_dynamic_taint": True,
                            "trace_record_limit_hit": True,
                        },
                        "trace_output": {
                            "path": ".local\\tmp\\instruction_trace.jsonl",
                            "written": True,
                            "record_count": 2,
                        },
                        "sample_records": [
                            {
                                "seq": 0,
                                "pc_label": "RunScriptCommand",
                                "mnemonic": "ld a, [$d15e]",
                                "pc_bank_address": "01:4000",
                                "function": "RunScriptCommand",
                            }
                        ],
                        "commands": [
                            "python -m tools.debugger trace-instructions --symbol RunScriptCommand --symbol CallScript --execute --require-hit --out-trace .local\\tmp\\instruction_trace.jsonl"
                        ],
                    }
                ),
                encoding="utf-8",
            )
            ready_report = root / "instruction_trace_ready.json"
            ready_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": True,
                        "executed": True,
                        "effective_save_state": "patched.state",
                        "captured_frame_count": 3,
                        "functions": [
                            {
                                "symbol": "RunScriptCommand",
                                "instruction_count": 5,
                                "hook_count": 5,
                                "instructions": [],
                            }
                        ],
                        "watches": [{"name": "wScriptPos"}],
                        "execution_validation": {
                            "attempted": True,
                            "required": True,
                            "planned_hook_count": 5,
                            "captured_frame_count": 3,
                            "hit": True,
                            "hit_function_symbols": ["RunScriptCommand"],
                            "missing_function_symbols": [],
                            "watch_symbols": ["wScriptPos"],
                            "ready_for_dynamic_taint": True,
                            "trace_record_limit_hit": False,
                        },
                        "trace_output": {
                            "path": ".local\\tmp\\ready_trace.jsonl",
                            "written": True,
                            "record_count": 3,
                        },
                        "commands": [
                            "python -m tools.debugger trace-instructions --symbol RunScriptCommand --execute --require-hit --out-trace .local\\tmp\\ready_trace.jsonl"
                        ],
                    }
                ),
                encoding="utf-8",
            )

            visualization = build_visualization_report(
                reports=("instruction_trace_ready.json", "instruction_trace.json"),
                root=root,
            )
            static_report = build_static_report(
                reports=("instruction_trace_ready.json", "instruction_trace.json"),
                root=root,
            )

        graph_node_types = {node["type"] for node in visualization["graph"]["nodes"]}
        lanes = {lane["lane"] for lane in visualization["lane_summary"]}
        event_types = {event["type"] for event in visualization["timeline"]}
        waterfall_statuses = {step["status"] for step in visualization["waterfall"]}
        graph_relations = {edge["relation"] for edge in visualization["graph"]["edges"]}

        self.assertTrue(visualization["valid"])
        self.assertIn("instruction_trace", lanes)
        self.assertGreaterEqual(visualization["waterfall_step_count"], 4)
        self.assertIn("ready", waterfall_statuses)
        self.assertIn("limit", waterfall_statuses)
        self.assertIn("writes_trace", graph_relations)
        self.assertIn("validation_ready", event_types)
        self.assertIn("validation_partial", event_types)
        self.assertIn("validation_limit", event_types)
        self.assertIn("instruction_trace_validation", graph_node_types)
        self.assertIn("instruction_trace_output", graph_node_types)
        self.assertIn("instruction_hit", graph_node_types)
        self.assertIn("instruction_miss", graph_node_types)
        self.assertIn("RunScriptCommand", visualization["mermaid_graph"])
        self.assertIn("CallScript", visualization["mermaid_graph"])
        self.assertIn("Instruction trace ready for dynamic taint", visualization["content"])
        self.assertIn("Instruction trace missed selected routines", visualization["content"])
        self.assertIn("ready dynamic-taint trace: .local\\tmp\\ready_trace.jsonl", static_report["content"])
        self.assertIn("instruction trace missed functions: CallScript", static_report["content"])
        self.assertIn("instruction trace validation: hit=True", static_report["content"])

    def test_visualization_preserves_next_step_proof_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            next_report = root / "next.json"
            next_report.write_text(
                json.dumps(build_next_step(symptom="boss selected wrong switch")),
                encoding="utf-8",
            )

            visualization = build_visualization_report(reports=("next.json",), root=root)

        event_types = {event["type"] for event in visualization["timeline"]}
        waterfall_statuses = {step["status"] for step in visualization["waterfall"]}
        graph_relations = {edge["relation"] for edge in visualization["graph"]["edges"]}
        graph_node_types = {node["type"] for node in visualization["graph"]["nodes"]}
        graph_labels = {node["label"] for node in visualization["graph"]["nodes"]}

        self.assertTrue(visualization["valid"])
        self.assertEqual(visualization["warning_count"], 0)
        self.assertIn("next_step", event_types)
        self.assertIn("needs-input", waterfall_statuses)
        self.assertIn("first_command", graph_relations)
        self.assertIn("source_ref", graph_relations)
        self.assertIn("evidence_standard", graph_relations)
        self.assertIn("disproof_standard", graph_relations)
        self.assertIn("regression_gate", graph_relations)
        self.assertIn("source_ref", graph_node_types)
        self.assertIn("evidence_standard", graph_node_types)
        self.assertIn("disproof_standard", graph_node_types)
        self.assertIn("engine/battle/ai/boss_policy_switch.asm", graph_labels)
        self.assertIn("regression_gate", graph_node_types)
        self.assertIn("Next proof path", visualization["content"])
        self.assertIn("rom-switch-materialize", visualization["content"])
        self.assertIn("tools/boss_ai_debugger/rom_switch_materialize.py", visualization["content"])
        self.assertIn("evidence_standard=", visualization["content"])
        self.assertIn("disproof_standard=", visualization["content"])
        self.assertIn("scenario JSONL with the disputed switch case", visualization["content"])
        self.assertIn("Regression gate", visualization["content"])
        self.assertIn("Proof limit:", visualization["content"])

    def test_visualization_preserves_ready_capability_audit_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit_report = root / "audit.json"
            audit_report.write_text(
                json.dumps(build_capability_report()),
                encoding="utf-8",
            )

            visualization = build_visualization_report(reports=("audit.json",), root=root)

        lanes = {lane["lane"] for lane in visualization["lane_summary"]}
        event_types = {event["type"] for event in visualization["timeline"]}
        graph_node_types = {node["type"] for node in visualization["graph"]["nodes"]}

        self.assertTrue(visualization["valid"])
        self.assertEqual(visualization["warning_count"], 0)
        self.assertIn("graph", lanes)
        self.assertEqual(event_types, set())
        self.assertNotIn("capability_partial", event_types)
        self.assertIn("capability_audit", graph_node_types)
        self.assertNotIn("gap_action", graph_node_types)
        self.assertIn("ready=True", visualization["content"])

    def test_static_report_summarizes_findings_and_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            compare_report = root / "compare.json"
            compare_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_compare_plan",
                        "match_count": 1,
                        "matches": [
                            {
                                "id": "static_expectations",
                                "gaps": ["not dynamic yet"],
                                "commands": ["python compare.py"],
                                "materialization_commands": ["python prove.py"],
                            }
                        ],
                        "commands": ["python compare.py"],
                        "materialization_commands": ["python prove.py"],
                    }
                ),
                encoding="utf-8",
            )

            report = build_static_report(
                reports=("compare.json",),
                title="Debug Session",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["kind"], "unified_debugger_static_report")
        self.assertIn("# Debug Session", report["content"])
        self.assertIn("Mirror gap", report["content"])
        self.assertIn("python compare.py", report["content"])

    def test_static_report_preserves_next_step_proof_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            next_report = root / "next.json"
            next_report.write_text(
                json.dumps(build_next_step(symptom="boss selected wrong switch")),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("next.json",), root=root)
            report = build_static_report(reports=("next.json",), root=root)

        self.assertTrue(ranked["valid"])
        self.assertEqual(ranked["findings"][0]["type"], "next_step")
        self.assertNotIn("Unsupported report kind", report["content"])
        self.assertIn("Next proof path", report["content"])
        self.assertIn("rom-switch-materialize", report["content"])
        self.assertIn("scenario JSONL with the disputed switch case", report["content"])
        self.assertIn("source/data: tools/boss_ai_debugger/rom_switch_materialize.py", report["content"])
        self.assertIn("evidence standard: A scenario JSONL matching the disputed switch case passes rom-switch-materialize", report["content"])
        self.assertIn("disproof standard: If a matching scenario JSONL passes rom-switch-materialize with the expected switch result", report["content"])
        self.assertIn("regression gate: python -m tools.boss_ai_debugger rom-switch-materialize", report["content"])
        self.assertIn("Proof limit:", report["content"])

    def test_symptom_only_investigation_preserves_embedded_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            investigation_report = root / "investigate.json"
            investigation_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_investigation_run",
                        "valid": True,
                        "passed": True,
                        "symptom": "boss selected wrong switch",
                        "steps": [],
                        "top_findings": [],
                        "top_impact": [],
                        "commands": [],
                        "errors": [],
                        "warnings": [],
                        "symptom_only_next_step_note": "No runtime evidence supplied.",
                        "symptom_only_next_step": build_next_step(symptom="boss selected wrong switch"),
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("investigate.json",), root=root)
            report = build_static_report(reports=("investigate.json",), root=root)
            visualization = build_visualization_report(reports=("investigate.json",), root=root)

        finding_types = {finding["type"] for finding in ranked["findings"]}
        graph_relations = {edge["relation"] for edge in visualization["graph"]["edges"]}
        timeline_types = {event["type"] for event in visualization["timeline"]}
        waterfall_titles = "\n".join(step["title"] for step in visualization["waterfall"])
        self.assertTrue(ranked["valid"])
        self.assertIn("next_step", finding_types)
        self.assertIn("Next proof path", report["content"])
        self.assertIn("rom-switch-materialize", report["content"])
        self.assertIn("source/data: tools/boss_ai_debugger/rom_switch_materialize.py", report["content"])
        self.assertIn("evidence standard: A scenario JSONL matching the disputed switch case passes rom-switch-materialize", report["content"])
        self.assertIn("disproof standard: If a matching scenario JSONL passes rom-switch-materialize with the expected switch result", report["content"])
        self.assertIn("regression gate: python -m tools.boss_ai_debugger rom-switch-materialize", report["content"])
        self.assertIn("next_step", timeline_types)
        self.assertIn("rom-switch-materialize", waterfall_titles)
        self.assertIn("source_ref", graph_relations)
        self.assertIn("evidence_standard", graph_relations)
        self.assertIn("disproof_standard", graph_relations)
        self.assertIn("regression_gate", graph_relations)

    def test_static_report_preserves_ready_capability_audit_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit_report = root / "audit.json"
            audit_report.write_text(
                json.dumps(build_capability_report()),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("audit.json",), root=root)
            report = build_static_report(reports=("audit.json",), root=root)

        finding_types = {finding["type"] for finding in ranked["findings"]}
        self.assertTrue(ranked["valid"])
        self.assertNotIn("capability_partial", finding_types)
        self.assertNotIn("Unsupported report kind", report["content"])
        self.assertIn("ready=True", report["content"])
        self.assertIn("gap_action_count=0", report["content"])
        self.assertNotIn("gap action:", report["content"])
        self.assertIn("python -m tools.debugger setup --symbol wCurDamage", report["content"])

    def test_cli_report_writes_static_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "executed": True,
                        "hit_count": 1,
                        "events": [
                            {
                                "watch": "wCurDamage",
                                "pc_bank_address": "01:4000",
                                "old_hex": "00",
                                "new_hex": "01",
                                "pc_label": "BattleCommand_Test",
                                "suggested_commands": ["python replay.py"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "debugger_report.html"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "report",
                        "--report",
                        str(watch_report),
                        "--format",
                        "html",
                        "--out",
                        str(out),
                    ]
                )

            content = out.read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertIn("<!doctype html>", content)
        self.assertIn("wCurDamage changed", content)


if __name__ == "__main__":
    unittest.main()
