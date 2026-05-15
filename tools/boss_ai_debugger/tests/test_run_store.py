from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.run_store import run_changed_ai_suite, run_generated_smoke_suite


def write_unit_contribution_trace(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "source": "trace_rom_pyboy_hooks",
                "save_state": "route:unit",
                "event_count": 1,
                "changed_event_count": 1,
                "trace_basis": {},
                "chosen": {},
                "events": [
                    {
                        "changed": True,
                        "operation": "encourage_score",
                        "candidate": {"kind": "move", "slot_index": 0, "move_id": 57},
                        "source": {
                            "rule_id": "move.unit_trace_rule",
                            "classification": "public_info",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


class RunStoreTests(unittest.TestCase):
    def test_generated_smoke_suite_writes_reproducible_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp)
            metadata = run_generated_smoke_suite(
                count=10,
                seed=4,
                run_id="test_run",
                runs_dir=runs_dir,
            )
            run_dir = runs_dir / "test_run"

            self.assertTrue((run_dir / "metadata.json").exists())
            self.assertTrue((run_dir / "scenarios.jsonl").exists())
            self.assertTrue((run_dir / "batch_report.json").exists())
            self.assertTrue((run_dir / "review_queue.json").exists())
            self.assertTrue((run_dir / "summary.md").exists())

        self.assertEqual(metadata["run_id"], "test_run")
        self.assertEqual(metadata["batch_summary"]["scenario_count"], 10)
        self.assertTrue(metadata["validation"]["valid"])

    def test_cli_run_suite_generated_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "run-suite",
                        "--profile",
                        "generated-smoke",
                        "--count",
                        "6",
                        "--seed",
                        "2",
                        "--run-id",
                        "cli_run",
                        "--runs-dir",
                        tmp,
                        "--json",
                    ]
                )
            data = json.loads(stdout.getvalue())

        self.assertEqual(code, 0)
        self.assertEqual(data["run_id"], "cli_run")
        self.assertEqual(data["batch_summary"]["scenario_count"], 6)

    def test_changed_ai_suite_records_debugger_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp)
            contribution_trace = runs_dir / "unit_rom_trace.json"
            write_unit_contribution_trace(contribution_trace)
            metadata = run_changed_ai_suite(
                count=6,
                seed=3,
                run_id="changed_run",
                runs_dir=runs_dir,
                trace_dir=None,
                rom_contribution_trace_paths=[contribution_trace],
            )
            run_dir = runs_dir / "changed_run"

            self.assertTrue((run_dir / "route_eval.json").exists())
            self.assertTrue((run_dir / "differential.json").exists())
            self.assertTrue((run_dir / "mutation.json").exists())
            self.assertTrue((run_dir / "invariants.json").exists())
            self.assertTrue((run_dir / "trace_replay.json").exists())
            self.assertTrue((run_dir / "rom_contribution_trace_summary.json").exists())
            self.assertTrue((run_dir / "summary.md").exists())
            contribution_summary = json.loads(
                (run_dir / "rom_contribution_trace_summary.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(metadata["profile"], "changed-ai")
        self.assertEqual(metadata["batch_summary"]["scenario_count"], 6)
        self.assertIn("route_eval_summary", metadata)
        self.assertIn("differential_summary", metadata)
        self.assertIn("contribution_comparison", metadata["differential_summary"])
        self.assertEqual(contribution_summary["covered_rule_count"], 1)
        self.assertEqual(metadata["rom_contribution_summary"]["covered_rule_count"], 1)
        self.assertFalse(metadata["parameters"]["refresh_rom_contribution_trace"])
        self.assertIn("rom_contribution_trace_summary", metadata["artifacts"])
        self.assertIn("rom_contribution_trace_summary", metadata["artifact_hashes"])
        self.assertIn("known_gaps", metadata)

    def test_cli_run_suite_changed_ai(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            contribution_trace = Path(tmp) / "unit_rom_trace.json"
            write_unit_contribution_trace(contribution_trace)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "run-suite",
                        "--profile",
                        "changed-ai",
                        "--count",
                        "4",
                        "--seed",
                        "5",
                        "--run-id",
                        "cli_changed",
                        "--runs-dir",
                        tmp,
                        "--trace-dir",
                        str(Path(tmp) / "missing_traces"),
                        "--rom-contribution-trace",
                        str(contribution_trace),
                        "--json",
                    ]
                )
            data = json.loads(stdout.getvalue())

        self.assertEqual(code, 0)
        self.assertEqual(data["profile"], "changed-ai")
        self.assertEqual(data["run_id"], "cli_changed")
        self.assertEqual(data["batch_summary"]["scenario_count"], 4)
        self.assertEqual(data["rom_contribution_summary"]["covered_rule_count"], 1)


if __name__ == "__main__":
    unittest.main()
