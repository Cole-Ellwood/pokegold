from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.run_store import run_generated_smoke_suite


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


if __name__ == "__main__":
    unittest.main()
