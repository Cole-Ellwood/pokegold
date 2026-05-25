from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.next_steps import NEXT_STEP_ROWS, build_next_step
from tools.debugger.testgen import suggest_tests


class SuggestTestsTests(unittest.TestCase):
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
