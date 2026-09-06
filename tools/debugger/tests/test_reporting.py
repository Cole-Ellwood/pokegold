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
    def test_controlled_hypotheses_precede_generic_findings_without_becoming_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = root / "input source"
            fixture.mkdir()
            atom = {"claim_type": "diagnosis.hypothesis", "observation_type": "controlled_runtime_comparison",
                    "proof_status": "instruction_observed", "precision": {"source_file": "engine/unit.asm", "source_line": 12, "source_symbol": "Caller"},
                    "source_report": str(root / "mapping.json"), "detail": {
                        "intervention": {"at": "Callee", "register": "A", "expected": 17, "value": 2},
                        "reproducer": str(root / "baseline.json"), "regression": str(root / "contract.json"),
                        "observations": [{"trace": str(root / "trace.jsonl"), "call_input_change": {"before": "02", "after": "11"},
                                          "counted_pointer_loop": {"iterations": 17, "stride": 47, "proof_status": "instruction_observed"},
                                          "pointer_write": {"store": {"bank": 0, "address": 0xA91F, "value": 0}},
                                          "causal_chain": [{"seq": 1}, {"seq": 2}]}],
                        "uncertainty": "Corrected-source regression remains unverified. <script>bad()</script>"}}
            for present in (False, True):
                (root / "investigation.json").write_text(json.dumps({"kind": "unified_debugger_investigation_run", "root": str(fixture),
                                                                    "valid": True, "evidence_atoms": [atom] if present else []}))
                for format in ("markdown", "html"):
                    with self.subTest(present=present, format=format):
                        report = build_static_report(reports=("investigation.json",), output_format=format, root=root)
                        content = report["content"]
                        if not present:
                            self.assertNotIn("Controlled hypotheses", content)
                            continue
                        self.assertLess(content.index("Controlled hypotheses"), content.index("Highest Priority Findings"))
                        for text in ("Caller", "Callee", "17 iterations", "47", "A91F", "2 instruction citations", "not a complete root-cause proof", "Corrected-source regression remains unverified"):
                            self.assertIn(text, content)
                        self.assertIn("baseline.json", content)
                        self.assertIn("contract.json", content)
                        self.assertIn("mapping.json", content)
                        self.assertIn("input%20source" if format == "html" else "input source", content)
                        self.assertNotIn("<script>bad()</script>", content)

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
