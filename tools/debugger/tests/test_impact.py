from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.impact import build_impact_report


class ImpactTests(unittest.TestCase):
    def test_impact_report_prioritizes_gate_failure_over_coverage_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gate_report = root / "gate.json"
            gate_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_gate_plan",
                        "steps": [
                            {
                                "status": "failed",
                                "command": "python tools\\audit\\check_release_smoke.py",
                                "stderr_tail": ["release smoke failed"],
                                "stdout_tail": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            coverage_report = root / "coverage.json"
            coverage_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_coverage_report",
                        "uncovered_targets": [
                            {
                                "type": "symbol",
                                "id": "BattleCommand_DamageCalc",
                                "commands": [
                                    "python -m tools.debugger localize --symbol BattleCommand_DamageCalc"
                                ],
                                "related_files": ["engine/battle/effect_commands.asm"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_impact_report(
                reports=("gate.json", "coverage.json"),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["items"][0]["type"], "gate_failed")
        self.assertGreater(
            report["items"][0]["impact_score"],
            report["items"][-1]["impact_score"],
        )
        self.assertIn(
            "python tools\\audit\\check_release_smoke.py",
            report["commands"],
        )

    def test_impact_report_classifies_boss_ai_score_delta_as_boss_ai(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_index = root / "trace_index.json"
            trace_index.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_trace_index",
                        "valid": True,
                        "events": [
                            {
                                "event_type": "score_delta",
                                "state_symbol": "wEnemyAIMoveScores",
                                "source_symbol": "BossAI_ApplyMoveModel",
                                "rule_id": "move.apply_move_model",
                                "evidence": ["event_type=score_delta"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_impact_report(reports=("trace_index.json",), root=root)

        surfaces = {item["surface"] for item in report["items"]}

        self.assertTrue(report["valid"])
        self.assertIn("Boss AI", surfaces)

    def test_cli_impact_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            coverage_report = root / "coverage.json"
            coverage_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_coverage_report",
                        "uncovered_targets": [
                            {
                                "type": "source_file",
                                "id": "engine/battle/effect_commands.asm",
                                "commands": [
                                    "python -m tools.debugger gate --changed-file engine/battle/effect_commands.asm"
                                ],
                                "related_symbols": ["wCurDamage"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "impact.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "impact",
                        "--report",
                        str(coverage_report),
                        "--symbol",
                        "wCurDamage",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_impact_report")
        self.assertGreater(data["impact_count"], 0)
        self.assertIn("Battle damage", {item["surface"] for item in data["items"]})
