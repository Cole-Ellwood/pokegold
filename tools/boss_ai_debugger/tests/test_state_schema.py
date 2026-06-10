from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.state_schema import (
    validate_fixtures_file,
    validate_scenario_file,
    validate_trace_dir,
)
from tools.boss_ai_debugger.canonical_classes import build_live_trace_class
from tools.boss_ai_preference.data import DEFAULT_FIXTURES_PATH


class StateSchemaTests(unittest.TestCase):
    def test_current_fixture_file_validates(self) -> None:
        report = validate_fixtures_file(DEFAULT_FIXTURES_PATH)

        self.assertTrue(report["valid"])
        self.assertGreaterEqual(report["checked_count"], 50)

    def test_trace_dir_validates_exact_capture_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trace_dir = Path(tmp)
            (trace_dir / "boss_live.txt").write_text(
                "\n".join(
                    [
                        "trace_rom_sha256=A",
                        "trace_symbols_sha256=B",
                        "boss=Fixture",
                        "tier=3",
                        "move_ids=1,2,3,0",
                        "move_scores=20,21,80,80",
                        "pre_model_scores=20,20,80,255",
                        "post_model_scores=20,21,80,255",
                        "chosen_id=1",
                        "chosen_slot=0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = validate_trace_dir(trace_dir)

        self.assertTrue(report["valid"])
        self.assertEqual(report["checked_count"], 1)
        self.assertEqual(report["class_id_count"], 1)

    def test_live_trace_block_derives_valid_canonical_class(self) -> None:
        fields = {
            "trace_rom_sha256": "A" * 64,
            "trace_symbols_sha256": "B" * 64,
            "boss": "Unit",
            "tier": "3",
            "move_ids": "1,2,3,4",
            "move_scores": "20,21,80,80",
            "chosen_id": "1",
            "chosen_slot": "0",
        }

        canonical = build_live_trace_class(
            fields,
            trace_path="audit/boss_ai_trace/unit_live.txt",
            capture_index=1,
        )

        self.assertTrue(canonical["valid"])
        self.assertRegex(canonical["class_id"], r"^csc_[0-9A-F]{20}$")
        self.assertEqual(canonical["proof_status"], "emulator_evidence")

    def test_live_trace_class_ignores_outcome_and_notes_but_tracks_inputs(self) -> None:
        fields = {
            "trace_rom_sha256": "A" * 64,
            "trace_symbols_sha256": "B" * 64,
            "boss": "Unit",
            "notes": "first note",
            "tier": "3",
            "move_ids": "1,2,3,4",
            "move_scores": "20,21,80,80",
            "chosen": "ONE",
            "chosen_id": "1",
            "chosen_slot": "0",
            "top_moves": "ONE:20,TWO:21",
        }
        changed_outcome = {
            **fields,
            "notes": "different note",
            "chosen": "TWO",
            "chosen_id": "2",
            "chosen_slot": "1",
            "top_moves": "TWO:21,ONE:20",
        }
        changed_input = {**fields, "move_scores": "20,22,80,80"}

        base = build_live_trace_class(fields, trace_path="unit.txt", capture_index=1)
        same_input = build_live_trace_class(changed_outcome, trace_path="unit.txt", capture_index=1)
        new_input = build_live_trace_class(changed_input, trace_path="unit.txt", capture_index=1)

        self.assertEqual(base["class_id"], same_input["class_id"])
        self.assertNotEqual(base["class_id"], new_input["class_id"])

    def test_hidden_field_rejected_for_public_only_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.json"
            path.write_text(
                json.dumps(
                    {
                        "id": "hidden_case",
                        "state": {
                            "boss": {
                                "active": {
                                    "species": "Qwilfish",
                                    "hp": "100%",
                                    "status": "none",
                                }
                            },
                            "player": {
                                "active": {
                                    "species": "Starmie",
                                    "hp": "100%",
                                    "status": "none",
                                    "hidden_moves": ["Rapid Spin"],
                                }
                            },
                        },
                        "moves": [{"id": "spikes", "name": "Spikes"}],
                    }
                ),
                encoding="utf-8",
            )

            report = validate_scenario_file(path)

        self.assertFalse(report["valid"])
        self.assertIn("hidden-info field", "\n".join(report["errors"]))

    def test_bad_generated_hash_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.json"
            path.write_text(
                json.dumps(
                    {
                        "id": "bad_hash",
                        "state_hash": "not-a-hash",
                        "moves": [{"id": "slot1", "name": "Slot 1"}],
                    }
                ),
                encoding="utf-8",
            )

            report = validate_scenario_file(path)

        self.assertFalse(report["valid"])
        self.assertIn("state_hash", "\n".join(report["errors"]))

    def test_generated_scenario_without_canonical_class_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.json"
            path.write_text(
                json.dumps(
                    {
                        "id": "generated_missing_class",
                        "generator": "boss-ai-debugger-generator-v1",
                        "state_hash": "A" * 64,
                        "moves": [{"id": "slot1", "name": "Slot 1"}],
                    }
                ),
                encoding="utf-8",
            )

            report = validate_scenario_file(path)

        self.assertFalse(report["valid"])
        self.assertIn("missing canonical_state_class", "\n".join(report["errors"]))

    def test_scenario_class_id_must_match_canonical_record(self) -> None:
        from tools.boss_ai_debugger.generators import generate_scenarios

        scenario = generate_scenarios(family="selector_edges", count=1, seed=1)[0]
        scenario["class_id"] = "csc_BAD"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.json"
            path.write_text(json.dumps(scenario), encoding="utf-8")

            report = validate_scenario_file(path)

        self.assertFalse(report["valid"])
        self.assertIn("class_id", "\n".join(report["errors"]))

    def test_cli_default_validation_checks_fixtures_and_traces(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = debugger_main(["state-schema", "validate"])

        self.assertEqual(code, 0)
        self.assertIn("validation passed", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
