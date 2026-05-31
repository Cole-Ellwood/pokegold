from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.audit import check_debugger_godmode_benchmark as benchmark


class GodmodeBenchmarkTests(unittest.TestCase):
    def test_in_process_next_writes_payload_without_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "next.json"
            run, payload = benchmark.run_debugger_json(
                name="next",
                args=["next", "--symptom", "boss selected wrong switch"],
                json_path=path,
                timeout=120,
                subprocess_mode=False,
            )

        self.assertEqual(run.exit_code, 0)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["kind"], "unified_debugger_next_step")
        self.assertEqual(payload["recommendation"]["symptom_class"], "wrong_switch")

    def test_summary_records_execution_mode(self) -> None:
        summary = benchmark.summarize(
            [],
            threshold=0.85,
            baseline=False,
            questions_path=benchmark.DEFAULT_QUESTIONS,
            source_anchor_threshold=0.5,
            standard_token_threshold=3,
            next_only=False,
            subprocess_mode=False,
        )

        self.assertEqual(summary["execution_mode"], "in_process")


if __name__ == "__main__":
    unittest.main()
