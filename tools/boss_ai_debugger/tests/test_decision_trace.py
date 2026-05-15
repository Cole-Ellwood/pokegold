from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.decision_trace import decision_trace_for_scenario
from tools.boss_ai_debugger.generators import write_jsonl


class DecisionTraceTests(unittest.TestCase):
    def test_scenario_trace_contains_score_and_selector_events(self) -> None:
        trace = decision_trace_for_scenario(
            {
                "id": "trace_case",
                "tier": "late",
                "moves": [
                    {
                        "id": "a",
                        "name": "A",
                        "deltas": [{"rule": "test_rule", "delta": -4}],
                    },
                    {"id": "b", "name": "B"},
                ],
                "expectation": {"best_action_ids": ["a"]},
            }
        )
        event_types = {event["event_type"] for event in trace["events"]}

        self.assertIn("score_rule", event_types)
        self.assertIn("selector", event_types)
        self.assertIn("policy_check", event_types)
        self.assertEqual(trace["source"], "python_scenario")

    def test_cli_decision_trace_writes_json(self) -> None:
        scenario = {
            "id": "cli_trace_case",
            "tier": "late",
            "moves": [
                {"id": "a", "name": "A", "deltas": [{"rule": "test", "delta": -1}]},
                {"id": "b", "name": "B"},
            ],
            "expectation": {"best_action_ids": ["a"]},
        }
        with tempfile.TemporaryDirectory() as tmp:
            scenarios_path = Path(tmp) / "scenarios.jsonl"
            out = Path(tmp) / "trace.json"
            write_jsonl([scenario], scenarios_path)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "decision-trace",
                        "--scenario",
                        str(scenarios_path),
                        "--json-out",
                        str(out),
                    ]
                )
            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertGreater(data["event_count"], 0)
        self.assertIn("decision trace", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
