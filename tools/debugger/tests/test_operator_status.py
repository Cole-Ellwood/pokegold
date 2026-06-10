from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.debugger.operator_status import (
    artifact_hash_mismatches,
    build_operator_status,
    format_operator_status,
    latest_run_store,
)


class OperatorStatusTests(unittest.TestCase):
    def test_latest_run_store_reads_metadata_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "audit" / "boss_ai_debugger" / "runs" / "20260101_changed_ai"
            run.mkdir(parents=True)
            queue = run / "review_queue.json"
            queue.write_text(json.dumps({"items": [], "returned_count": 0}), encoding="utf-8")
            metadata = {
                "run_id": "20260101_changed_ai",
                "profile": "changed-ai",
                "created_at": "2026-01-01T00:00:00Z",
                "git_commit": "abc",
                "artifacts": {"review_queue": "audit/boss_ai_debugger/runs/20260101_changed_ai/review_queue.json"},
                "artifact_hashes": {},
                "batch_summary": {"scenario_count": 1},
                "review_queue_summary": {"returned_count": 0},
                "known_gaps": ["gap"],
            }
            (run / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

            latest = latest_run_store(root)

        self.assertTrue(latest["available"])
        self.assertEqual(latest["run_id"], "20260101_changed_ai")
        self.assertEqual(latest["known_gaps"], ["gap"])

    def test_operator_status_shape_has_next_commands_and_taxonomy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_operator_status(Path(tmp))

        self.assertTrue(report["read_only"])
        self.assertEqual(report["kind"], "debugger_operator_status")
        self.assertIn("top_next_commands", report)
        self.assertIn("--read-only", report["top_next_commands"][1])
        self.assertIn("command_taxonomy", report)
        self.assertEqual(report["command_taxonomy"]["side_effect_unknown_command_count"], 0)
        self.assertTrue(report["command_taxonomy"]["read_only_refusal_enforced"])
        text = format_operator_status(report)
        self.assertIn("operator status", text)
        self.assertIn("Top next commands", text)
        self.assertIn("read_only_enforced=True", text)

    def test_operator_status_promotes_top_review_queue_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "audit" / "boss_ai_debugger" / "runs" / "20260101_changed_ai"
            run.mkdir(parents=True)
            queue_items = [
                {
                    "scenario_id": "scenario_one",
                    "verdict": "bad_roll",
                    "priority_score": 300,
                    "next_action": "check first fact",
                    "explain_decision": {"command": "cmd-one"},
                },
                {
                    "scenario_id": "scenario_two",
                    "verdict": "acceptable_top",
                    "priority_score": 200,
                    "next_action": "check second fact",
                    "explain_decision": {"command": "cmd-two"},
                },
                {
                    "scenario_id": "scenario_three",
                    "verdict": "bad_roll",
                    "priority_score": 100,
                    "next_action": "check third fact",
                    "explain_decision": {"command": "cmd-three"},
                },
            ]
            queue = run / "review_queue.json"
            queue.write_text(json.dumps({"items": queue_items, "returned_count": 3}), encoding="utf-8")
            metadata = {
                "run_id": "20260101_changed_ai",
                "profile": "changed-ai",
                "created_at": "2026-01-01T00:00:00Z",
                "artifacts": {"review_queue": "audit/boss_ai_debugger/runs/20260101_changed_ai/review_queue.json"},
                "artifact_hashes": {},
            }
            (run / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

            report = build_operator_status(root)

        self.assertEqual(report["top_next_commands"], ["cmd-one", "cmd-two", "cmd-three"])
        text = format_operator_status(report)
        self.assertIn("Top review queue items", text)
        for expected in ("scenario_one", "scenario_two", "scenario_three", "cmd-one", "cmd-two", "cmd-three"):
            self.assertIn(expected, text)

    def test_latest_run_store_hash_audit_checks_list_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "present.json").write_text("new value", encoding="utf-8")
            metadata = {
                "artifacts": {"some_list": ["present.json", "missing.json"]},
                "artifact_hashes": {
                    "some_list": {
                        "present.json": "STALE",
                        "missing.json": "MISSING",
                    }
                },
            }

            mismatches = artifact_hash_mismatches(root, metadata)

        self.assertEqual(len(mismatches), 2)
        self.assertEqual({item["path"] for item in mismatches}, {"present.json", "missing.json"})


if __name__ == "__main__":
    unittest.main()
