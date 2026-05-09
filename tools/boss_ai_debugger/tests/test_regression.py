from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.regression import evaluate_corpus, format_json, format_summary
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

        self.assertEqual(len(labels), 7)
        self.assertEqual(result.strict_label_count, 5)
        self.assertEqual(result.skipped, {"both_good": 1, "other_better": 1})

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
