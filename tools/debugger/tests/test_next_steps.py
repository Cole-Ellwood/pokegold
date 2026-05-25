from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.next_steps import NEXT_STEP_ROWS, build_next_step


class NextStepTests(unittest.TestCase):
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

    def test_next_step_routes_switches_into_bad_target_phrase(self) -> None:
        report = build_next_step(
            symptom=(
                "Morty switches Misdreavus into Gengar against Haunter "
                "before Haunter has attacked"
            )
        )
        rec = report["recommendation"]

        self.assertEqual(rec["symptom_class"], "wrong_switch")
        self.assertIn("rom-switch-materialize", rec["first_command"])

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
            "Morty Haunter is too eager to Curse below half HP after putting Quilava to sleep, and Misdreavus used Pain Split at full HP instead of attacking": (
                "wrong_move_score",
                "decision-trace",
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
