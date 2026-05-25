from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from tools.debugger.script_resume_gate import build_script_resume_gate_report


class ScriptResumeGateTests(unittest.TestCase):
    def test_script_resume_gate_fails_unexecuted_watch_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "executed": False,
                        "reset_sentinel": False,
                        "watches": [],
                        "events": [],
                        "reset_event_count": 0,
                    }
                ),
                encoding="utf-8",
            )

            report = build_script_resume_gate_report(
                reports=("watch.json",),
                root=root,
            )

        finding_ids = {finding["id"] for finding in report["findings"]}

        self.assertFalse(report["passed"])
        self.assertIn("watch_not_executed", finding_ids)
        self.assertIn("watch_too_short", finding_ids)
        self.assertIn("watch_no_runtime_signal", finding_ids)
        self.assertIn("required_watch_symbol_missing", finding_ids)
        self.assertIn("pc_sp_snapshot_missing", finding_ids)

    def test_script_resume_gate_passes_complete_clean_watch_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "executed": True,
                        "frames": 60,
                        "hit_count": 1,
                        "reset_sentinel": True,
                        "watches": [
                            {"name": "wSeenTrainerBank", "found": True},
                            {"name": "wScriptAfterPointer", "found": True},
                            {"name": "wRunningTrainerBattleScript", "found": True},
                            {"name": "wScriptBank", "found": True},
                            {"name": "wScriptPos", "found": True},
                        ],
                        "runtime_summary": {
                            "initial": {"registers": {"register_pc": "4000", "register_sp": "DFF0"}},
                            "final": {"registers": {"register_pc": "5123", "register_sp": "DFE8"}},
                        },
                        "events": [
                            {
                                "event_type": "watch_change",
                                "watch": "wScriptPos",
                                "old_hex": "1050",
                                "new_hex": "2050",
                            }
                        ],
                        "reset_event_count": 0,
                    }
                ),
                encoding="utf-8",
            )

            report = build_script_resume_gate_report(
                reports=("watch.json",),
                root=root,
            )

        self.assertTrue(report["passed"], report["findings"])
        self.assertEqual(report["findings"][0]["id"], "watch_script_resume_ok")

    def test_script_resume_gate_rejects_trainer_bank_only_watch_activity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "executed": True,
                        "frames": 30,
                        "hit_count": 1,
                        "reset_sentinel": True,
                        "watches": [
                            {"name": "wSeenTrainerBank", "found": True},
                            {"name": "wScriptAfterPointer", "found": True},
                            {"name": "wRunningTrainerBattleScript", "found": True},
                            {"name": "wScriptBank", "found": True},
                            {"name": "wScriptPos", "found": True},
                        ],
                        "runtime_summary": {
                            "initial": {"registers": {"register_pc": "4000", "register_sp": "DFF0"}},
                            "final": {"registers": {"register_pc": "4010", "register_sp": "DFE8"}},
                        },
                        "events": [
                            {
                                "event_type": "watch_change",
                                "watch": "wSeenTrainerBank",
                                "old_hex": "00",
                                "new_hex": "07",
                            }
                        ],
                        "reset_event_count": 0,
                    }
                ),
                encoding="utf-8",
            )

            report = build_script_resume_gate_report(
                reports=("watch.json",),
                root=root,
            )

        finding_ids = {finding["id"] for finding in report["findings"]}

        self.assertFalse(report["passed"])
        self.assertIn("watch_no_script_resume_signal", finding_ids)

    def test_script_resume_gate_fails_runtime_state_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_report = root / "runtime_state.json"
            state_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_runtime_state_report",
                        "valid": True,
                        "passed": False,
                        "findings": [
                            {
                                "id": "invalid_script_pc",
                                "severity": 94,
                                "title": "Script VM is running from an invalid ROM address",
                                "evidence": ["wScriptBank:wScriptPos=B4:0002"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_script_resume_gate_report(
                reports=("runtime_state.json",),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertFalse(report["passed"])
        self.assertEqual(report["findings"][0]["id"], "invalid_script_pc")
        self.assertIn("B4:0002", report["findings"][0]["evidence"][0])
