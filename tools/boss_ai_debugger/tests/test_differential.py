from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.differential import build_differential_report
from tools.boss_ai_debugger.generators import write_jsonl


class DifferentialTests(unittest.TestCase):
    def test_policy_mismatch_is_reported(self) -> None:
        scenario = {
            "id": "policy_case",
            "tier": "late",
            "moves": [
                {"id": "bad_top", "name": "Bad Top", "deltas": [{"rule": "top", "delta": -4}]},
                {"id": "wanted", "name": "Wanted"},
            ],
            "expectation": {
                "best_action_ids": ["wanted"],
                "bad_action_ids": ["bad_top"],
                "policy_tags": ["unit"],
            },
        }

        report = build_differential_report(scenarios=[scenario])

        self.assertEqual(report["mismatch_count"], 1)
        self.assertEqual(
            report["mismatches"][0]["class"],
            "policy_preference_mismatch",
        )

    def test_trace_selector_mismatch_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "boss_live.txt"
            trace.write_text(
                "\n".join(
                    [
                        "boss=Exact",
                        "tier=3",
                        "move_ids=1,2,3,0",
                        "move_scores=20,20,20,80",
                        "chosen_id=3",
                        "chosen_slot=2",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_differential_report(trace_paths=[trace])

        self.assertEqual(report["mismatch_class_counts"], {"selector_mismatch": 1})
        self.assertEqual(report["mismatches"][0]["status"], "confirmed")

    def test_cli_diff_writes_json(self) -> None:
        scenario = {
            "id": "cli_policy_case",
            "tier": "late",
            "moves": [
                {"id": "bad_top", "name": "Bad Top", "deltas": [{"rule": "top", "delta": -4}]},
                {"id": "wanted", "name": "Wanted"},
            ],
            "expectation": {"best_action_ids": ["wanted"]},
        }
        with tempfile.TemporaryDirectory() as tmp:
            scenarios_path = Path(tmp) / "scenarios.jsonl"
            out = Path(tmp) / "diff.json"
            write_jsonl([scenario], scenarios_path)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "diff",
                        "--scenarios",
                        str(scenarios_path),
                        "--json-out",
                        str(out),
                    ]
                )
            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["mismatch_count"], 1)
        self.assertIn("differential report", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
