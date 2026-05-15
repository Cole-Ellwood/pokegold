from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.run_store import (
    build_previous_run_diff,
    run_changed_ai_suite,
    run_generated_smoke_suite,
)


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
            self.assertTrue((run_dir / "rom_score_materialization.json").exists())
            self.assertTrue((run_dir / "rom_rebuild.json").exists())
            self.assertTrue((run_dir / "live_trace_refresh.json").exists())
            self.assertTrue((run_dir / "previous_run_diff.json").exists())
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
        self.assertFalse(metadata["parameters"]["refresh_rom_score_materialization"])
        self.assertIn("rom_contribution_trace_summary", metadata["artifacts"])
        self.assertIn("rom_score_materialization", metadata["artifacts"])
        self.assertIn("previous_run_diff", metadata["artifacts"])
        self.assertIn("rom_rebuild", metadata["artifacts"])
        self.assertIn("live_trace_refresh", metadata["artifacts"])
        self.assertIn("rom_contribution_trace_summary", metadata["artifact_hashes"])
        self.assertIn("rom_score_materialization", metadata["artifact_hashes"])
        self.assertIn("previous_run_diff", metadata["artifact_hashes"])
        self.assertFalse(metadata["rom_rebuild_summary"]["requested"])
        self.assertFalse(metadata["live_trace_refresh_summary"]["requested"])
        self.assertFalse(metadata["previous_run_diff_summary"]["available"])
        self.assertEqual(
            metadata["rom_score_materialization_summary"]["checked_count"],
            0,
        )
        self.assertIn("known_gaps", metadata)

    def test_changed_ai_suite_records_requested_rebuild_and_trace_commands(self) -> None:
        calls = []

        def fake_runner(command):
            calls.append(command)
            return {
                "argv": command,
                "returncode": 0,
                "elapsed_seconds": 0.01,
                "stdout": "ok",
                "stderr": "",
            }

        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp)
            contribution_trace = runs_dir / "unit_rom_trace.json"
            write_unit_contribution_trace(contribution_trace)
            metadata = run_changed_ai_suite(
                count=2,
                seed=3,
                run_id="changed_run",
                runs_dir=runs_dir,
                trace_dir=None,
                rom_contribution_trace_paths=[contribution_trace],
                rebuild_roms=True,
                refresh_live_traces=True,
                command_runner=fake_runner,
            )
            run_dir = runs_dir / "changed_run"
            rom_rebuild = json.loads(
                (run_dir / "rom_rebuild.json").read_text(encoding="utf-8")
            )
            live_refresh = json.loads(
                (run_dir / "live_trace_refresh.json").read_text(encoding="utf-8")
            )

        self.assertEqual(len(calls), 3)
        self.assertTrue(rom_rebuild["requested"])
        self.assertTrue(rom_rebuild["passed"])
        self.assertEqual(rom_rebuild["command_count"], 1)
        self.assertTrue(live_refresh["requested"])
        self.assertTrue(live_refresh["passed"])
        self.assertEqual(live_refresh["command_count"], 2)
        self.assertTrue(metadata["rom_rebuild_summary"]["passed"])
        self.assertTrue(metadata["live_trace_refresh_summary"]["passed"])

    def test_previous_run_diff_reports_metric_deltas(self) -> None:
        previous = {
            "run_id": "previous",
            "profile": "changed-ai",
            "git_commit": "old",
            "batch_summary": {"scenario_count": 4, "reviewable_count": 3},
            "differential_summary": {
                "mismatch_count": 2,
                "contribution_comparison": {"mismatch_count": 1},
            },
            "trace_replay_summary": {"failure_count": 0},
            "rom_score_materialization_summary": {
                "error_count": 0,
                "contribution_mismatch_count": 1,
            },
            "mutation_summary": {"survived_count": 4},
            "invariant_summary": {"violation_count": 5},
            "artifact_hashes": {
                "batch_report": "OLD",
                "previous_run_diff": "OLD_SELF",
            },
            "changed_files": ["engine/battle/ai/boss_policy_move.asm"],
        }
        current = {
            "run_id": "current",
            "profile": "changed-ai",
            "git_commit": "new",
            "batch_summary": {"scenario_count": 6, "reviewable_count": 5},
            "differential_summary": {
                "mismatch_count": 1,
                "contribution_comparison": {"mismatch_count": 0},
            },
            "trace_replay_summary": {"failure_count": 0},
            "rom_score_materialization_summary": {
                "error_count": 0,
                "contribution_mismatch_count": 0,
            },
            "mutation_summary": {"survived_count": 2},
            "invariant_summary": {"violation_count": 5},
            "artifact_hashes": {
                "batch_report": "NEW",
                "previous_run_diff": "NEW_SELF",
            },
            "changed_files": [
                "engine/battle/ai/boss_policy_move.asm",
                "tools/boss_ai_debugger/scorer.py",
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp)
            previous_dir = runs_dir / "previous"
            previous_dir.mkdir()
            (previous_dir / "metadata.json").write_text(
                json.dumps({**previous, "created_at": "2026-05-15T00:00:00Z"}),
                encoding="utf-8",
            )

            diff = build_previous_run_diff(
                runs_dir=runs_dir,
                current_run_id="current",
                current_metadata=current,
            )

        self.assertTrue(diff["available"])
        self.assertEqual(diff["previous_run_id"], "previous")
        self.assertEqual(diff["metric_deltas"]["scenario_count"]["delta"], 2)
        self.assertEqual(diff["metric_deltas"]["reviewable_count"]["delta"], 2)
        self.assertEqual(
            diff["metric_deltas"]["differential_mismatch_count"]["delta"],
            -1,
        )
        self.assertEqual(diff["summary"]["artifact_hash_change_count"], 1)
        self.assertEqual(
            [change["artifact"] for change in diff["artifact_hash_changes"]],
            ["batch_report"],
        )
        self.assertEqual(diff["summary"]["changed_file_added_count"], 1)
        self.assertEqual(
            diff["changed_file_diff"]["added"],
            ["tools/boss_ai_debugger/scorer.py"],
        )

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
