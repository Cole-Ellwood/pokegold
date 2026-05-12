from __future__ import annotations

import io
import json
import tempfile
import unittest
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.regression import evaluate_corpus, format_json, format_summary
from tools.boss_ai_debugger.scorer import score_action
from tools.boss_ai_preference.data import (
    PreferenceDataError,
    load_fixtures,
    load_preferences,
)


def tiny_fixture() -> dict:
    return {
        "id": "synthetic_fixture",
        "leader": "Tester",
        "state": {},
        "actions": [
            {
                "id": "move_crunch",
                "kind": "move",
                "name": "Crunch",
                "explanation": "coverage move",
                "public_tradeoff": "punish visible pressure",
            },
            {
                "id": "move_tackle",
                "kind": "move",
                "name": "Tackle",
                "explanation": "plain move",
                "public_tradeoff": "neutral",
            },
        ],
    }


def tie_fixture() -> dict:
    return {
        "id": "tie_fixture",
        "leader": "Tester",
        "state": {},
        "actions": [
            {
                "id": "move_tackle",
                "kind": "move",
                "name": "Tackle",
                "explanation": "plain move",
                "public_tradeoff": "neutral",
            },
            {
                "id": "move_scratch",
                "kind": "move",
                "name": "Scratch",
                "explanation": "plain move",
                "public_tradeoff": "neutral",
            },
        ],
    }


def pairwise_label(
    choice: str,
    *,
    fixture_id: str = "synthetic_fixture",
    action_a_id: str = "move_crunch",
    action_b_id: str = "move_tackle",
) -> dict:
    preferred_action_id = None
    if choice == "a_better":
        preferred_action_id = action_a_id
    elif choice == "b_better":
        preferred_action_id = action_b_id
    return {
        "fixture_id": fixture_id,
        "state_version": 1,
        "action_a_id": action_a_id,
        "action_b_id": action_b_id,
        "choice": choice,
        "preferred_action_id": preferred_action_id,
        "reason_tags": [],
        "action_tags": {action_a_id: [], action_b_id: []},
        "note": "unit test label",
        "created_at": "2026-05-09T00:00:00+00:00",
        "tool_version": "boss-ai-preference-v0",
    }


class RegressionTests(unittest.TestCase):
    def test_existing_fixture_file_loads_realistic_corpus(self) -> None:
        fixtures = load_fixtures()
        labels = load_preferences(fixtures=fixtures)

        result = evaluate_corpus(fixtures, labels, threshold=0.80)

        expected_strict = sum(
            1 for label in labels if label["choice"] in {"a_better", "b_better"}
        )
        expected_skipped = Counter(
            label["choice"]
            for label in labels
            if label["choice"] not in {"a_better", "b_better"}
        )
        self.assertGreaterEqual(len(labels), 10)
        self.assertEqual(result.strict_label_count, expected_strict)
        self.assertEqual(result.skipped, dict(sorted(expected_skipped.items())))

    def test_lock_risk_only_applies_to_actual_lock_moves(self) -> None:
        fixture = {
            "id": "lock_text_fixture",
            "leader": "Tester",
            "state": {},
            "actions": [
                {
                    "id": "move_body_slam",
                    "kind": "move",
                    "name": "Body Slam",
                    "explanation": "Keeps pressure without locking into a bad sequence.",
                    "public_tradeoff": "Safe damage.",
                },
                {
                    "id": "move_rollout",
                    "kind": "move",
                    "name": "Rollout",
                    "explanation": "Actual ramp lock move.",
                    "public_tradeoff": "Risky lock.",
                },
            ],
        }

        body_slam = score_action(fixture, fixture["actions"][0])
        rollout = score_action(fixture, fixture["actions"][1])

        self.assertNotIn(
            "lock_risk",
            {contribution["rule"] for contribution in body_slam["contributions"]},
        )
        self.assertIn(
            "lock_risk",
            {contribution["rule"] for contribution in rollout["contributions"]},
        )

    def test_setup_prose_does_not_make_setup_a_coverage_move(self) -> None:
        fixture = {
            "id": "setup_text_fixture",
            "leader": "Tester",
            "state": {},
            "actions": [
                {
                    "id": "move_swords_dance",
                    "kind": "move",
                    "name": "Swords Dance",
                    "explanation": "Can set up if the player cannot punish.",
                    "public_tradeoff": "A real setup opportunity.",
                }
            ],
        }

        scored = score_action(fixture, fixture["actions"][0])
        rules = {contribution["rule"] for contribution in scored["contributions"]}

        self.assertIn("setup_window", rules)
        self.assertNotIn("coverage", rules)

    def test_damage_estimate_can_mark_confirmed_ko(self) -> None:
        fixture = {
            "id": "ko_fixture",
            "leader": "Tester",
            "state": {},
            "actions": [
                {
                    "id": "move_wing_attack",
                    "kind": "move",
                    "name": "Wing Attack",
                    "explanation": "Immediate damage.",
                    "public_tradeoff": "Clean tempo.",
                    "damage_estimate": {
                        "low_percent": 95,
                        "high_percent": 112,
                        "target_hp": "51%",
                    },
                }
            ],
        }

        scored = score_action(fixture, fixture["actions"][0])

        self.assertIn(
            "ko_confirmed",
            {contribution["rule"] for contribution in scored["contributions"]},
        )

    def test_strict_pair_passes_when_scorer_matches_label(self) -> None:
        result = evaluate_corpus([tiny_fixture()], [pairwise_label("a_better")], 0.80)

        self.assertEqual(result.strict_agreement_count, 1)
        self.assertTrue(result.passed)
        self.assertEqual(result.disagreements, [])

    def test_strict_pair_fails_when_scorer_disagrees(self) -> None:
        result = evaluate_corpus([tiny_fixture()], [pairwise_label("b_better")], 0.80)

        self.assertEqual(result.strict_agreement_count, 0)
        self.assertFalse(result.passed)
        self.assertEqual(len(result.disagreements), 1)
        self.assertEqual(result.disagreements[0].scorer_choice, "a_better")
        self.assertIn("move_tackle > move_crunch", format_summary(result))

    def test_score_tie_counts_as_disagreement(self) -> None:
        label = pairwise_label(
            "a_better",
            fixture_id="tie_fixture",
            action_a_id="move_tackle",
            action_b_id="move_scratch",
        )

        result = evaluate_corpus([tie_fixture()], [label], 0.80)

        self.assertEqual(result.strict_label_count, 1)
        self.assertEqual(result.strict_agreement_count, 0)
        self.assertEqual(result.disagreements[0].scorer_choice, "tie")

    def test_non_strict_choices_are_skipped(self) -> None:
        result = evaluate_corpus([tiny_fixture()], [pairwise_label("both_good")], 0.80)

        self.assertEqual(result.strict_label_count, 0)
        self.assertEqual(result.skipped, {"both_good": 1})
        self.assertEqual(result.disagreements, [])

    def test_missing_fixture_or_action_raises_schema_error(self) -> None:
        with self.assertRaisesRegex(PreferenceDataError, "unknown fixture_id"):
            evaluate_corpus(
                [tiny_fixture()],
                [pairwise_label("a_better", fixture_id="missing_fixture")],
                0.80,
            )

        with self.assertRaisesRegex(PreferenceDataError, "action_id 'missing_action'"):
            evaluate_corpus(
                [tiny_fixture()],
                [pairwise_label("a_better", action_b_id="missing_action")],
                0.80,
            )

    def test_json_report_shape(self) -> None:
        result = evaluate_corpus([tiny_fixture()], [pairwise_label("b_better")], 0.80)

        report = format_json(result)

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["threshold"], 0.80)
        self.assertEqual(report["strict_label_count"], 1)
        self.assertEqual(report["strict_agreement_count"], 0)
        self.assertEqual(report["agreement_rate"], 0.0)
        self.assertEqual(report["disagreements"][0]["label_choice"], "b_better")

    def test_cli_exit_code_tracks_threshold_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixtures_path = Path(tmp) / "fixtures.json"
            labels_path = Path(tmp) / "labels.jsonl"
            fixtures_path.write_text(
                json.dumps({"schema_version": 1, "fixtures": [tiny_fixture()]}),
                encoding="utf-8",
            )

            labels_path.write_text(
                json.dumps(pairwise_label("a_better"), sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                pass_code = debugger_main(
                    [
                        "regress",
                        "--fixtures",
                        str(fixtures_path),
                        "--labels",
                        str(labels_path),
                        "--threshold",
                        "0.80",
                        "--quiet",
                    ]
                )
            self.assertEqual(pass_code, 0)

            labels_path.write_text(
                json.dumps(pairwise_label("b_better"), sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                fail_code = debugger_main(
                    [
                        "regress",
                        "--fixtures",
                        str(fixtures_path),
                        "--labels",
                        str(labels_path),
                        "--threshold",
                        "0.80",
                        "--quiet",
                    ]
                )
            self.assertEqual(fail_code, 1)


if __name__ == "__main__":
    unittest.main()
