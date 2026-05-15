from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.generators import generate_scenarios, write_jsonl
from tools.boss_ai_debugger.review_queue import build_review_queue
from tools.boss_ai_debugger.rom_scenarios import evaluate_batch


class ReviewQueueTests(unittest.TestCase):
    def test_review_queue_ranks_bad_rolls_before_weaker_items(self) -> None:
        report = {
            "scenario_count": 2,
            "verdicts": [
                {
                    "scenario_id": "weak",
                    "verdict": "weak_best",
                    "severity": 40,
                    "rom_best_probability": 0.40,
                    "policy_tags": ["tempo"],
                    "condition_tags": [],
                },
                {
                    "scenario_id": "bad",
                    "verdict": "bad_roll",
                    "severity": 80,
                    "rom_best_probability": 0.25,
                    "policy_tags": ["hazard_retention"],
                    "condition_tags": ["active_revealed_rapid_spin"],
                    "answer_changing_information": ["spinblock"],
                },
            ],
        }

        queue = build_review_queue(report, limit=2)

        self.assertEqual(queue["items"][0]["scenario_id"], "bad")
        self.assertGreater(
            queue["items"][0]["priority_score"],
            queue["items"][1]["priority_score"],
        )

    def test_cli_review_queue_from_scenarios_writes_json(self) -> None:
        scenarios = generate_scenarios(family="spikes_spin", count=12, seed=5)
        with tempfile.TemporaryDirectory() as tmp:
            scenarios_path = Path(tmp) / "scenarios.jsonl"
            out = Path(tmp) / "queue.json"
            write_jsonl(scenarios, scenarios_path)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "review-queue",
                        "--scenarios",
                        str(scenarios_path),
                        "--limit",
                        "5",
                        "--json-out",
                        str(out),
                    ]
                )
            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertLessEqual(data["returned_count"], 5)
        self.assertIn("Boss AI debugger review queue", stdout.getvalue())

    def test_review_queue_from_batch_report_shape(self) -> None:
        scenarios = generate_scenarios(family="selector_edges", count=8, seed=9)
        report = evaluate_batch(scenarios)
        queue = build_review_queue(report, limit=3)

        self.assertLessEqual(queue["returned_count"], 3)
        self.assertEqual(queue["input_scenario_count"], 8)


if __name__ == "__main__":
    unittest.main()
