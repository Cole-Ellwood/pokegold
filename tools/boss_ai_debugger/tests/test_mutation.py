from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.mutation import (
    remove_rule_mutant,
    run_scorer_mutations,
)


def coverage_fixture() -> dict:
    return {
        "id": "coverage_fixture",
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


def pairwise_label(choice: str = "a_better") -> dict:
    return {
        "fixture_id": "coverage_fixture",
        "state_version": 1,
        "action_a_id": "move_crunch",
        "action_b_id": "move_tackle",
        "choice": choice,
        "preferred_action_id": "move_crunch" if choice == "a_better" else "move_tackle",
        "reason_tags": [],
        "action_tags": {"move_crunch": [], "move_tackle": []},
        "note": "unit test label",
        "created_at": "2026-05-15T00:00:00+00:00",
        "tool_version": "boss-ai-preference-v0",
    }


class MutationTests(unittest.TestCase):
    def test_rule_removal_mutant_is_killed_by_strict_label(self) -> None:
        report = run_scorer_mutations(
            [coverage_fixture()],
            [pairwise_label()],
            threshold=0.80,
            mutants=[
                remove_rule_mutant(
                    "test.remove_coverage",
                    "coverage",
                    "Remove coverage.",
                    "medium",
                )
            ],
        )

        self.assertEqual(report["killed_count"], 1)
        self.assertEqual(report["mutants"][0]["status"], "killed")
        self.assertGreater(report["mutants"][0]["changed_strict_pair_count"], 0)

    def test_unexercised_mutant_is_reported_separately(self) -> None:
        report = run_scorer_mutations(
            [coverage_fixture()],
            [pairwise_label()],
            threshold=0.80,
            mutants=[
                remove_rule_mutant(
                    "test.remove_spinner",
                    "active_revealed_spinner_hazard_retention",
                    "Remove spinner discipline.",
                    "high",
                )
            ],
        )

        self.assertEqual(report["not_exercised_count"], 1)
        self.assertEqual(report["mutants"][0]["status"], "not_exercised")

    def test_cli_mutate_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixtures_path = Path(tmp) / "fixtures.json"
            labels_path = Path(tmp) / "labels.jsonl"
            out = Path(tmp) / "mutation.json"
            fixtures_path.write_text(
                json.dumps({"schema_version": 1, "fixtures": [coverage_fixture()]}),
                encoding="utf-8",
            )
            labels_path.write_text(
                json.dumps(pairwise_label(), sort_keys=True) + "\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "mutate",
                        "--target",
                        "scorer",
                        "--fixtures",
                        str(fixtures_path),
                        "--labels",
                        str(labels_path),
                        "--limit",
                        "1",
                        "--json-out",
                        str(out),
                    ]
                )
            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["mutant_count"], 1)
        self.assertIn("mutation report", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
