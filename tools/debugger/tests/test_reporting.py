from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.catalog import (
    build_capability_report,
    build_inventory,
    triage_request,
)
from tools.debugger.next_steps import NEXT_STEP_ROWS, build_next_step
from tools.debugger.ranking import rank_findings
from tools.debugger.reporting import build_static_report


class StaticReportTests(unittest.TestCase):
    def test_static_report_summarizes_findings_and_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            compare_report = root / "compare.json"
            compare_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_compare_plan",
                        "match_count": 1,
                        "matches": [
                            {
                                "id": "static_expectations",
                                "gaps": ["not dynamic yet"],
                                "commands": ["python compare.py"],
                                "materialization_commands": ["python prove.py"],
                            }
                        ],
                        "commands": ["python compare.py"],
                        "materialization_commands": ["python prove.py"],
                    }
                ),
                encoding="utf-8",
            )

            report = build_static_report(
                reports=("compare.json",),
                title="Debug Session",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["kind"], "unified_debugger_static_report")
        self.assertIn("# Debug Session", report["content"])
        self.assertIn("Mirror gap", report["content"])
        self.assertIn("python compare.py", report["content"])

    def test_static_report_preserves_next_step_proof_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            next_report = root / "next.json"
            next_report.write_text(
                json.dumps(build_next_step(symptom="boss selected wrong switch")),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("next.json",), root=root)
            report = build_static_report(reports=("next.json",), root=root)

        self.assertTrue(ranked["valid"])
        self.assertEqual(ranked["findings"][0]["type"], "next_step")
        self.assertNotIn("Unsupported report kind", report["content"])
        self.assertIn("Next proof path", report["content"])
        self.assertIn("rom-switch-materialize", report["content"])
        self.assertIn("scenario JSONL with the disputed switch case", report["content"])
        self.assertIn("source/data: tools/boss_ai_debugger/rom_switch_materialize.py", report["content"])
        self.assertIn("evidence standard: A scenario JSONL matching the disputed switch case passes rom-switch-materialize", report["content"])
        self.assertIn("disproof standard: If a matching scenario JSONL passes rom-switch-materialize with the expected switch result", report["content"])
        self.assertIn("regression gate: python -m tools.boss_ai_debugger rom-switch-materialize", report["content"])
        self.assertIn("Proof limit:", report["content"])

    def test_static_report_preserves_ready_capability_audit_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit_report = root / "audit.json"
            audit_report.write_text(
                json.dumps(build_capability_report()),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("audit.json",), root=root)
            report = build_static_report(reports=("audit.json",), root=root)

        finding_types = {finding["type"] for finding in ranked["findings"]}
        self.assertTrue(ranked["valid"])
        self.assertNotIn("capability_partial", finding_types)
        self.assertNotIn("Unsupported report kind", report["content"])
        self.assertIn("ready=True", report["content"])
        self.assertIn("gap_action_count=0", report["content"])
        self.assertNotIn("gap action:", report["content"])
        self.assertIn("python -m tools.debugger setup --symbol wCurDamage", report["content"])

    def test_cli_report_writes_static_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "executed": True,
                        "hit_count": 1,
                        "events": [
                            {
                                "watch": "wCurDamage",
                                "pc_bank_address": "01:4000",
                                "old_hex": "00",
                                "new_hex": "01",
                                "pc_label": "BattleCommand_Test",
                                "suggested_commands": ["python replay.py"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "debugger_report.html"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "report",
                        "--report",
                        str(watch_report),
                        "--format",
                        "html",
                        "--out",
                        str(out),
                    ]
                )

            content = out.read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertIn("<!doctype html>", content)
        self.assertIn("wCurDamage changed", content)
