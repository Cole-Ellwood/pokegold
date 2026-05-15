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

    def test_cli_default_validation_checks_fixtures_and_traces(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = debugger_main(["state-schema", "validate"])

        self.assertEqual(code, 0)
        self.assertIn("validation passed", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
