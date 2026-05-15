from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.counterfactuals import (
    explain_counterfactuals,
    score_flip_for_action,
)
from tools.boss_ai_debugger.generators import generate_scenarios, write_jsonl
from tools.boss_ai_debugger.localize import localize_report
from tools.boss_ai_debugger.minimize import minimize_scenario
from tools.boss_ai_debugger.rom_scenarios import evaluate_batch


class AnalysisToolTests(unittest.TestCase):
    def test_counterfactual_reports_smallest_score_flip(self) -> None:
        scenario = {
            "id": "counterfactual_case",
            "tier": "late",
            "moves": [
                {"id": "bad_top", "name": "Bad Top", "deltas": [{"rule": "top", "delta": -4}]},
                {"id": "wanted", "name": "Wanted"},
            ],
            "expectation": {
                "best_action_ids": ["wanted"],
                "bad_action_ids": ["bad_top"],
                "condition_tags": ["immediate_pressure"],
            },
        }

        report = explain_counterfactuals(scenario)

        self.assertEqual(report["smallest_score_flip"]["action_id"], "wanted")
        self.assertLess(report["smallest_score_flip"]["required_delta"], 0)
        self.assertTrue(report["public_fact_counterfactuals"])

    def test_counterfactual_score_floor_marks_impossible_flip(self) -> None:
        flip = score_flip_for_action(
            "wanted",
            {"best": 1, "wanted": 4},
            {"best": 1, "wanted": 2},
            best_score=1,
            best_slot=1,
        )

        self.assertFalse(flip["available"])
        self.assertIn("score floor", flip["reason"])

    def test_minimize_preserves_verdict_and_removes_noise(self) -> None:
        scenario = {
            "id": "minimize_case",
            "generator": "test",
            "family": "test",
            "seed": 1,
            "case_index": 0,
            "notes": ["noise"],
            "tier": "late",
            "moves": [
                {"id": "bad_top", "name": "Bad Top", "deltas": [{"rule": "top", "delta": -4}]},
                {"id": "wanted", "name": "Wanted"},
                {"id": "irrelevant", "name": "Irrelevant", "deltas": [{"rule": "bad", "delta": 5}]},
            ],
            "expectation": {
                "best_action_ids": ["wanted"],
                "bad_action_ids": ["bad_top"],
                "policy_tags": ["test"],
                "why": "noise",
            },
        }

        report = minimize_scenario(scenario)

        self.assertTrue(report["preserved"])
        self.assertIn("notes", report["removed_fields"])
        self.assertIn("irrelevant", report["removed_actions"])

    def test_localize_counts_reviewable_tags(self) -> None:
        scenarios = generate_scenarios(family="spikes_spin", count=20, seed=15)
        batch = evaluate_batch(scenarios)
        report = localize_report(batch, scenarios=scenarios, source="inline")

        self.assertGreater(report["reviewable_count"], 0)
        self.assertTrue(report["top_condition_tags"])
        self.assertTrue(report["likely_causes"])

    def test_cli_analysis_commands(self) -> None:
        scenarios = generate_scenarios(family="spikes_spin", count=12, seed=15)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenarios.jsonl"
            write_jsonl(scenarios, path)
            counter_out = Path(tmp) / "counter.json"
            minimize_out = Path(tmp) / "minimize.json"
            localize_out = Path(tmp) / "localize.json"
            with redirect_stdout(io.StringIO()):
                counter_code = debugger_main(
                    [
                        "counterfactual",
                        "--scenario",
                        str(path),
                        "--json-out",
                        str(counter_out),
                    ]
                )
                minimize_code = debugger_main(
                    [
                        "minimize",
                        "--scenario",
                        str(path),
                        "--json-out",
                        str(minimize_out),
                    ]
                )
                localize_code = debugger_main(
                    [
                        "localize",
                        "--scenarios",
                        str(path),
                        "--json-out",
                        str(localize_out),
                    ]
                )

            counter = json.loads(counter_out.read_text(encoding="utf-8"))
            minimized = json.loads(minimize_out.read_text(encoding="utf-8"))
            localized = json.loads(localize_out.read_text(encoding="utf-8"))

        self.assertEqual(counter_code, 0)
        self.assertEqual(minimize_code, 0)
        self.assertEqual(localize_code, 0)
        self.assertIn("score_flips_to_expected_best", counter)
        self.assertIn("minimized_scenario", minimized)
        self.assertIn("likely_causes", localized)


if __name__ == "__main__":
    unittest.main()
