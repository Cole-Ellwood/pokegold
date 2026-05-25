from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.investigate import build_investigation_run
from tools.debugger.next_steps import NEXT_STEP_ROWS, build_next_step
from tools.debugger.ranking import rank_findings
from tools.debugger.reporting import build_static_report
from tools.debugger.visualization import build_visualization_report


class InvestigationTests(unittest.TestCase):
    def test_cli_investigate_symptom_only_points_to_next(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_out = Path(tmp) / "investigate.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "investigate",
                        "--symptom",
                        "boss selected wrong switch",
                        "--out-dir",
                        str(Path(tmp) / "investigate"),
                        "--max-targets",
                        "1",
                        "--max-events",
                        "1",
                        "--max-cases",
                        "1",
                        "--json-out",
                        str(json_out),
                    ]
                )

            self.assertEqual(code, 0)
            text = stdout.getvalue()
            self.assertIn("planning packet, not a repro", text)
            self.assertIn("python -m tools.debugger next --symptom", text)
            self.assertIn("Next proof path", text)
            self.assertIn("rom-switch-materialize", text)
            data = json.loads(json_out.read_text(encoding="utf-8"))
            next_step = data["symptom_only_next_step"]
            rec = next_step["recommendation"]
            self.assertEqual(next_step["kind"], "unified_debugger_next_step")
            self.assertEqual(rec["symptom_class"], "wrong_switch")
            self.assertIn("rom-switch-materialize", rec["first_command"])
            self.assertIn("tools/boss_ai_debugger/rom_switch_materialize.py", rec["source_refs"])
            self.assertIn("rom-switch-materialize", rec["evidence_standard"][0])
            self.assertIn("expected switch result", rec["disproof_standard"][0])
            self.assertIn("rom-switch-materialize", rec["regression_gate"])

    def test_investigation_replay_consumes_content_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "test.sym").write_text("00:0000 NULL\n", encoding="utf-8")
            (root / "maps" / "UnitMap.asm").write_text(
                "UnitMap_MapEvents:\n\tdef_warp_events\n\twarp_event 1, 2, ROUTE_29, 1\n",
                encoding="utf-8",
            )

            report = build_investigation_run(
                symbols_path="test.sym",
                changed_files=("maps/UnitMap.asm",),
                out_dir="run",
                max_targets=4,
                max_cases=2,
                root=root,
            )
            replay = json.loads((root / "run" / "03_replay.json").read_text(encoding="utf-8"))

        self.assertTrue(report["valid"])
        self.assertIn("02_content_scenarios", {step["id"] for step in report["steps"]})
        self.assertIn("content_scenario_1_0000", replay["replay_targets"]["scenario_ids"])

    def test_investigation_run_writes_debugger_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "test.sym").write_text(
                "0E:483E BossAI_ApplyMoveModel\n01:D0D3 wEnemyAIMoveScores\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "boss_policy_move.asm").write_text(
                "BossAI_ApplyMoveModel:\n\tld hl, wEnemyAIMoveScores\n\tret\n",
                encoding="utf-8",
            )
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "events": [
                            {
                                "event_type": "score_delta",
                                "score_pointer": "d0d3",
                                "score_before": 20,
                                "score_after": 18,
                                "source": {
                                    "full_symbol": "BossAI_ApplyMoveModel",
                                    "rule_id": "move.apply_move_model.apply_role_bias",
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out_dir = root / "investigation"

            report = build_investigation_run(
                traces=("trace.json",),
                symbols_path="test.sym",
                symbols=("BossAI_ApplyMoveModel",),
                addresses=("D0D3",),
                rules=("move.apply_move_model.apply_role_bias",),
                expectations=("event=score_delta,symbol=wEnemyAIMoveScores",),
                out_dir=str(out_dir),
                max_targets=6,
                max_cases=4,
                root=root,
            )
            step_ids = {step["id"] for step in report["steps"]}
            ingest_written = (out_dir / "01_ingest.json").exists()
            impact_written = (out_dir / "12_impact.json").exists()
            static_written = (out_dir / "investigation_report.md").exists()
            visualization_written = (out_dir / "investigation_visualization.md").exists()

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertEqual(report["kind"], "unified_debugger_investigation_run")
        self.assertIn("02_trace_index", step_ids)
        self.assertIn("08_expect", step_ids)
        self.assertGreaterEqual(report["produced_report_count"], 10)
        self.assertTrue(ingest_written)
        self.assertTrue(impact_written)
        self.assertTrue(static_written)
        self.assertTrue(visualization_written)

    def test_investigation_run_builds_state_space_from_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "data" / "types").mkdir(parents=True)
            (root / "test.sym").write_text(
                "0E:483E BossAI_ApplyMoveModel\n"
                "01:D0D3 wEnemyAIMoveScores\n"
                "01:D1EC wTypeMatchup\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "boss_policy_move.asm").write_text(
                "BossAI_ApplyMoveModel:\n\tld hl, wEnemyAIMoveScores\n\tret\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "late_gen_held_items.asm").write_text(
                "AirBalloon:\n\tret\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "effect_commands.asm").write_text(
                "BattleCommand_DamageCalc:\n\tret\n",
                encoding="utf-8",
            )
            (root / "data" / "types" / "type_matchups.asm").write_text(
                "TypeMatchups:\n\tdb 0\n",
                encoding="utf-8",
            )
            out_dir = root / "investigation"

            report = build_investigation_run(
                symbols_path="test.sym",
                patches=("wTypeMatchup=0x00",),
                watch_symbols=("wEnemyAIMoveScores",),
                changed_files=("engine/battle/ai/boss_policy_move.asm",),
                symptom="AI chose Ground move into Air Balloon immunity",
                out_dir=str(out_dir),
                max_targets=6,
                max_cases=4,
                root=root,
            )
            state_space = json.loads(
                (out_dir / "02_state_space.json").read_text(encoding="utf-8")
            )
            replay = json.loads(
                (out_dir / "03_replay.json").read_text(encoding="utf-8")
            )
            ranked = json.loads(
                (out_dir / "11_rank.json").read_text(encoding="utf-8")
            )
            impact = json.loads(
                (out_dir / "12_impact.json").read_text(encoding="utf-8")
            )

        step_ids = {step["id"] for step in report["steps"]}
        ranked_types = {item["type"] for item in ranked["findings"]}
        impact_types = {item["type"] for item in impact["items"]}

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertIn("02_state_space", step_ids)
        self.assertEqual(report["patches"], ["wTypeMatchup=0x00"])
        self.assertIn("wTypeMatchup", report["effective_watch_symbols"])
        self.assertEqual(state_space["kind"], "unified_debugger_state_space")
        self.assertEqual(state_space["state_space"]["patches"][0]["symbol"], "wTypeMatchup")
        self.assertIn("wTypeMatchup", replay["replay_targets"]["watch_symbols"])
        self.assertIn("state_space_ready", ranked_types)
        self.assertIn("state_space_ready", impact_types)

    def test_cli_investigate_writes_json_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            symbols = root / "test.sym"
            symbols.write_text(
                "0E:483E BossAI_ApplyMoveModel\n01:D0D3 wEnemyAIMoveScores\n",
                encoding="utf-8",
            )
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "events": [
                            {
                                "event_type": "score_delta",
                                "score_pointer": "d0d3",
                                "score_before": 20,
                                "score_after": 18,
                                "source": {
                                    "full_symbol": "BossAI_ApplyMoveModel",
                                    "rule_id": "move.apply_move_model.apply_role_bias",
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out_dir = root / "run"
            out = root / "investigation.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "investigate",
                        "--trace",
                        str(trace),
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "BossAI_ApplyMoveModel",
                        "--patch",
                        "wEnemyAIMoveScores=0x12",
                        "--address",
                        "D0D3",
                        "--expect",
                        "event=score_delta,symbol=wEnemyAIMoveScores",
                        "--out-dir",
                        str(out_dir),
                        "--max-targets",
                        "6",
                        "--max-cases",
                        "4",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            seeds_written = (out_dir / "generated_seeds.jsonl").exists()

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_investigation_run")
        self.assertTrue(data["passed"])
        self.assertEqual(data["patches"], ["wEnemyAIMoveScores=0x12"])
        self.assertIn("wEnemyAIMoveScores", data["effective_watch_symbols"])
        self.assertTrue(data["static_report"])
        self.assertTrue(data["visualization"])
        self.assertTrue(seeds_written)

    def test_symptom_only_investigation_preserves_embedded_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            investigation_report = root / "investigate.json"
            investigation_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_investigation_run",
                        "valid": True,
                        "passed": True,
                        "symptom": "boss selected wrong switch",
                        "steps": [],
                        "top_findings": [],
                        "top_impact": [],
                        "commands": [],
                        "errors": [],
                        "warnings": [],
                        "symptom_only_next_step_note": "No runtime evidence supplied.",
                        "symptom_only_next_step": build_next_step(symptom="boss selected wrong switch"),
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("investigate.json",), root=root)
            report = build_static_report(reports=("investigate.json",), root=root)
            visualization = build_visualization_report(reports=("investigate.json",), root=root)

        finding_types = {finding["type"] for finding in ranked["findings"]}
        graph_relations = {edge["relation"] for edge in visualization["graph"]["edges"]}
        timeline_types = {event["type"] for event in visualization["timeline"]}
        waterfall_titles = "\n".join(step["title"] for step in visualization["waterfall"])
        self.assertTrue(ranked["valid"])
        self.assertIn("next_step", finding_types)
        self.assertIn("Next proof path", report["content"])
        self.assertIn("rom-switch-materialize", report["content"])
        self.assertIn("source/data: tools/boss_ai_debugger/rom_switch_materialize.py", report["content"])
        self.assertIn("evidence standard: A scenario JSONL matching the disputed switch case passes rom-switch-materialize", report["content"])
        self.assertIn("disproof standard: If a matching scenario JSONL passes rom-switch-materialize with the expected switch result", report["content"])
        self.assertIn("regression gate: python -m tools.boss_ai_debugger rom-switch-materialize", report["content"])
        self.assertIn("next_step", timeline_types)
        self.assertIn("rom-switch-materialize", waterfall_titles)
        self.assertIn("source_ref", graph_relations)
        self.assertIn("evidence_standard", graph_relations)
        self.assertIn("disproof_standard", graph_relations)
        self.assertIn("regression_gate", graph_relations)
