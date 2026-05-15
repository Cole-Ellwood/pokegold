from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.generators import generate_scenarios, write_jsonl
from tools.boss_ai_debugger.invariants import mine_invariants


class InvariantMiningTests(unittest.TestCase):
    def test_mines_scenario_candidate_invariants(self) -> None:
        scenarios = generate_scenarios(family="selector_edges", count=8, seed=3)
        report = mine_invariants(scenarios=scenarios)
        candidates = {item["id"]: item for item in report["candidates"]}

        self.assertIn("scenario.selector_probability_surface", candidates)
        self.assertGreater(
            candidates["scenario.selector_probability_surface"]["support_count"],
            0,
        )
        self.assertEqual(report["status"], "candidate")

    def test_mines_trace_candidate_invariants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "boss_live.txt"
            trace.write_text(
                "\n".join(
                    [
                        "boss=Exact",
                        "tier=3",
                        "move_ids=1,2,3,0",
                        "move_scores=20,20,20,80",
                        "chosen_id=2",
                        "chosen_slot=1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = mine_invariants(trace_paths=[trace])
            candidates = {item["id"]: item for item in report["candidates"]}

        self.assertIn("trace.chosen_slot_is_possible", candidates)
        self.assertEqual(candidates["trace.chosen_slot_is_possible"]["violation_count"], 0)

    def test_cli_invariants_mine_writes_reports(self) -> None:
        scenarios = generate_scenarios(family="spikes_spin", count=6, seed=4)
        with tempfile.TemporaryDirectory() as tmp:
            scenarios_path = Path(tmp) / "scenarios.jsonl"
            json_out = Path(tmp) / "invariants.json"
            md_out = Path(tmp) / "invariants.md"
            write_jsonl(scenarios, scenarios_path)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "invariants",
                        "mine",
                        "--scenarios",
                        str(scenarios_path),
                        "--json-out",
                        str(json_out),
                        "--out",
                        str(md_out),
                    ]
                )
            data = json.loads(json_out.read_text(encoding="utf-8"))
            markdown_exists = md_out.exists()

        self.assertEqual(code, 0)
        self.assertTrue(markdown_exists)
        self.assertGreater(data["candidate_count"], 0)
        self.assertIn("candidate invariants", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
