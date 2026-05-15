from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.generators import generate_scenarios, write_jsonl
from tools.boss_ai_debugger.route_eval import evaluate_route_scenario


class RouteEvalTests(unittest.TestCase):
    def test_pass_classification(self) -> None:
        item = evaluate_route_scenario(
            {
                "id": "pass_case",
                "tier": "late",
                "moves": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}],
                "expectation": {"best_action_ids": ["a"]},
            }
        )

        self.assertEqual(item["classification"], "route_pass")
        self.assertEqual(item["route_bucket"], "pass")

    def test_acceptable_top_near_tie_classification(self) -> None:
        item = evaluate_route_scenario(
            {
                "id": "near_tie_case",
                "tier": "late",
                "moves": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}],
                "expectation": {
                    "best_action_ids": ["b"],
                    "acceptable_action_ids": ["a"],
                },
            }
        )

        self.assertEqual(item["classification"], "route_acceptable_but_review")
        self.assertEqual(item["route_bucket"], "acceptable_near_tie")
        self.assertTrue(item["near_tie"])

    def test_route_weight_mismatch_needs_context(self) -> None:
        item = evaluate_route_scenario(
            {
                "id": "route_context_case",
                "tier": "late",
                "moves": [
                    {"id": "a", "name": "A", "deltas": [{"rule": "now", "delta": -10}]},
                    {"id": "b", "name": "B"},
                ],
                "expectation": {
                    "best_action_ids": ["b"],
                    "policy_tags": ["hazard_retention"],
                    "condition_tags": ["route_trade"],
                    "lesson_type": "weight_hint",
                    "answer_changing_information": ["future route value"],
                },
            }
        )

        self.assertEqual(item["classification"], "route_wrong_top")
        self.assertEqual(item["route_bucket"], "needs_context")
        self.assertFalse(item["near_tie"])
        self.assertIn("hazard_route", item["route_family_tags"])

    def test_missing_expectation_needs_context(self) -> None:
        item = evaluate_route_scenario(
            {
                "id": "missing_expectation_case",
                "tier": "late",
                "moves": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}],
            }
        )

        self.assertEqual(item["classification"], "route_missing_expectation")
        self.assertEqual(item["route_bucket"], "needs_context")

    def test_no_legal_choice_is_bad_route_surface(self) -> None:
        item = evaluate_route_scenario(
            {
                "id": "no_choice_case",
                "tier": "late",
                "moves": [
                    {"id": "a", "name": "A", "blocked": True},
                    {"id": "b", "name": "B", "blocked": True},
                ],
                "expectation": {"best_action_ids": ["a"]},
            }
        )

        self.assertEqual(item["classification"], "route_no_legal_choice")
        self.assertEqual(item["route_bucket"], "actually_bad")

    def test_expected_route_unreachable(self) -> None:
        item = evaluate_route_scenario(
            {
                "id": "unreachable_case",
                "tier": "late",
                "moves": [
                    {"id": "slot1", "name": "Slot 1"},
                    {"id": "slot2", "name": "Slot 2"},
                    {"id": "slot3", "name": "Slot 3"},
                ],
                "expectation": {"best_action_ids": ["slot3"]},
            }
        )

        self.assertEqual(item["classification"], "route_expected_unreachable")
        self.assertEqual(item["route_bucket"], "actually_bad")

    def test_weak_best_probability_floor(self) -> None:
        item = evaluate_route_scenario(
            {
                "id": "weak_best_case",
                "tier": "late",
                "moves": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}],
                "expectation": {
                    "best_action_ids": ["a"],
                    "min_best_probability": 0.90,
                },
            }
        )

        self.assertEqual(item["classification"], "route_weak_best")
        self.assertEqual(item["route_bucket"], "acceptable_near_tie")

    def test_hazard_family_tags_from_structured_tags(self) -> None:
        item = evaluate_route_scenario(
            {
                "id": "hazard_tag_case",
                "tier": "late",
                "moves": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}],
                "expectation": {
                    "best_action_ids": ["a"],
                    "policy_tags": ["hazard_retention", "spikes"],
                    "condition_tags": [
                        "spikes_layers_3",
                        "active_revealed_rapid_spin",
                        "active_ghost_spinblock",
                        "immediate_pressure",
                    ],
                    "lesson_type": "hard_rule",
                },
            }
        )

        self.assertIn("hazard_route", item["route_family_tags"])
        self.assertIn("spikes_capped", item["route_family_tags"])
        self.assertIn("active_spinner_risk", item["route_family_tags"])
        self.assertIn("spinblocked", item["route_family_tags"])
        self.assertIn("tempo_pressure", item["route_family_tags"])

    def test_catastrophic_roll_is_actually_bad(self) -> None:
        item = evaluate_route_scenario(
            {
                "id": "catastrophic_case",
                "tier": "late",
                "moves": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}],
                "expectation": {
                    "best_action_ids": ["b"],
                    "catastrophic_action_ids": ["a"],
                },
            }
        )

        self.assertEqual(item["classification"], "route_catastrophic")
        self.assertEqual(item["route_bucket"], "actually_bad")

    def test_multi_turn_route_projects_named_factors(self) -> None:
        item = evaluate_route_scenario(
            {
                "id": "multi_turn_case",
                "tier": "late",
                "moves": [
                    {"id": "set_spikes", "name": "Spikes"},
                    {"id": "roar_branch", "name": "Roar"},
                    {"id": "sleep_line", "name": "Hypnosis"},
                    {"id": "cashout", "name": "Explosion"},
                ],
                "expectation": {
                    "best_action_ids": ["set_spikes"],
                    "condition_tags": [
                        "spikes_layers_1",
                        "active_revealed_rapid_spin",
                        "active_ghost_spinblock",
                        "one_time_trade_named_converter",
                    ],
                },
            },
            horizon=5,
        )

        route = item["multi_turn_route"]

        self.assertEqual(route["horizon"], 5)
        self.assertIn("hazards", route["implemented_factors"])
        self.assertIn("spin", route["observed_factors"])
        self.assertIn("phazing", route["observed_factors"])
        self.assertIn("sleep", route["observed_factors"])
        self.assertIn("self_ko", route["observed_factors"])
        self.assertTrue(any(line["branches"] for line in route["lines"]))

    def test_multi_turn_route_tracks_recovery_and_ace_preservation(self) -> None:
        item = evaluate_route_scenario(
            {
                "id": "recovery_ace_case",
                "tier": "late",
                "moves": [
                    {"id": "preserve_ace", "name": "Recover"},
                    {"id": "attack", "name": "Attack"},
                ],
                "expectation": {
                    "best_action_ids": ["preserve_ace"],
                    "condition_tags": ["ace_preservation"],
                },
            },
            horizon=2,
        )

        factors = item["multi_turn_route"]["observed_factors"]

        self.assertIn("recovery", factors)
        self.assertIn("ace_preservation", factors)

    def test_cli_route_eval_writes_batch_json(self) -> None:
        scenarios = generate_scenarios(family="spikes_spin", count=8, seed=7)
        with tempfile.TemporaryDirectory() as tmp:
            scenarios_path = Path(tmp) / "scenarios.jsonl"
            out = Path(tmp) / "route_eval.json"
            write_jsonl(scenarios, scenarios_path)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "route-eval",
                        "--scenario",
                        str(scenarios_path),
                        "--horizon",
                        "4",
                        "--json-out",
                        str(out),
                    ]
                )
            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["scenario_count"], 8)
        self.assertEqual(data["multi_turn_summary"]["horizon"], 4)
        self.assertIn("classification_counts", data)
        self.assertIn("route evaluation", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
