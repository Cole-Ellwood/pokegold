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
from tools.boss_ai_debugger.confidence_report import build_confidence_report
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

    def test_counterfactual_public_fact_flips_follow_policy_family(self) -> None:
        scenario = generate_scenarios(family="support_handoff", count=2, seed=23)[1]

        report = explain_counterfactuals(scenario)
        text = " ".join(report["public_fact_counterfactuals"])

        self.assertIn("absorber", text)
        self.assertIn("branch", text)
        self.assertNotIn("Rapid Spin", text)

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
        scenarios = [
            {
                "id": "localize_reviewable_case",
                "tier": "late",
                "moves": [
                    {
                        "id": "bad_top",
                        "name": "Bad Top",
                        "deltas": [{"rule": "top", "delta": -4}],
                    },
                    {"id": "wanted", "name": "Wanted"},
                ],
                "expectation": {
                    "best_action_ids": ["wanted"],
                    "bad_action_ids": ["bad_top"],
                    "condition_tags": ["bench_revealed_rapid_spin"],
                },
            }
        ]
        batch = evaluate_batch(scenarios)
        report = localize_report(batch, scenarios=scenarios, source="inline")

        self.assertGreater(report["reviewable_count"], 0)
        self.assertTrue(report["top_condition_tags"])
        self.assertTrue(report["likely_causes"])

    def test_confidence_report_summarizes_generated_and_materialized_strata(self) -> None:
        scenarios = generate_scenarios(family="prediction_mix", count=9, seed=21)
        batch = evaluate_batch(scenarios)
        report = build_confidence_report(
            batch,
            materialization_reports=[
                {
                    "kind": "rom_selector_materialization",
                    "verdicts": [
                        {
                            "scenario_id": scenarios[0]["id"],
                            "status": "pass",
                            "agreement": True,
                        }
                    ],
                },
                {
                    "kind": "rom_score_materialization",
                    "verdicts": [
                        {
                            "scenario_id": scenarios[1]["id"],
                            "family": "prediction_mix",
                            "status": "pass",
                            "selector_top_match": True,
                            "score_bytes_match": False,
                            "rom_policy": {"verdict": "bad_roll", "severity": 80},
                        }
                    ],
                },
                {
                    "kind": "rom_switch_materialization",
                    "verdicts": [
                        {
                            "scenario_id": "generated_switch_sack_21_00000_case",
                            "family": "switch_sack",
                            "status": "pass",
                            "rom_policy": {"verdict": "mismatch", "severity": 70},
                        }
                    ],
                }
            ],
        )

        families = {row["key"]: row for row in report["families"]}

        self.assertIn("prediction_mix", families)
        self.assertGreater(families["prediction_mix"]["scenario_count"], 0)
        self.assertIn("hard_failure_rate_95_upper", families["prediction_mix"])
        self.assertEqual(
            families["prediction_mix"]["materialization"]["selector_checked_count"],
            1,
        )
        self.assertEqual(
            families["prediction_mix"]["materialization"]["score_checked_count"],
            1,
        )
        self.assertEqual(
            families["prediction_mix"]["materialization"][
                "score_policy_reviewable_count"
            ],
            1,
        )
        self.assertEqual(
            report["materialization"]["by_family"]["switch_sack"][
                "switch_checked_count"
            ],
            1,
        )

    def test_cli_analysis_commands(self) -> None:
        scenarios = generate_scenarios(family="spikes_spin", count=12, seed=15)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenarios.jsonl"
            write_jsonl(scenarios, path)
            counter_out = Path(tmp) / "counter.json"
            minimize_out = Path(tmp) / "minimize.json"
            localize_out = Path(tmp) / "localize.json"
            batch_out = Path(tmp) / "batch.json"
            confidence_out = Path(tmp) / "confidence.json"
            batch_out.write_text(
                json.dumps(evaluate_batch(scenarios), indent=2, sort_keys=True),
                encoding="utf-8",
            )
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
                confidence_code = debugger_main(
                    [
                        "confidence-report",
                        "--batch-report",
                        str(batch_out),
                        "--json-out",
                        str(confidence_out),
                    ]
                )

            counter = json.loads(counter_out.read_text(encoding="utf-8"))
            minimized = json.loads(minimize_out.read_text(encoding="utf-8"))
            localized = json.loads(localize_out.read_text(encoding="utf-8"))
            confidence = json.loads(confidence_out.read_text(encoding="utf-8"))

        self.assertEqual(counter_code, 0)
        self.assertEqual(minimize_code, 0)
        self.assertEqual(localize_code, 0)
        self.assertEqual(confidence_code, 0)
        self.assertIn("score_flips_to_expected_best", counter)
        self.assertIn("minimized_scenario", minimized)
        self.assertIn("likely_causes", localized)
        self.assertIn("families", confidence)


if __name__ == "__main__":
    unittest.main()
