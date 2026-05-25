from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.expect import build_expectation_report


class ExpectationTests(unittest.TestCase):
    def test_expectation_report_passes_event_and_rule(self) -> None:
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
                                "source_symbol": "BossAI_ApplyMoveModel.ApplyRoleBias",
                                "rule_id": "move.apply_move_model.apply_role_bias",
                                "address": "D0D3",
                                "after": "15",
                                "evidence": ["score_delta"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_expectation_report(
                reports=("trace_index.json",),
                expectations=(
                    "event=score_delta,symbol=wEnemyAIMoveScores",
                    "rule=move.apply_move_model.apply_role_bias",
                ),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertEqual(report["failed_count"], 0)
        self.assertEqual(report["passed_count"], 2)

    def test_expectation_report_fails_missing_symbol(self) -> None:
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
                                "event_type": "watch_change",
                                "state_symbol": "wCurDamage",
                                "source_symbol": "BattleCommand_Test",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_expectation_report(
                reports=("trace_index.json",),
                expectations=("symbol=BossAI_SelectMove",),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertFalse(report["passed"])
        self.assertEqual(report["failed_count"], 1)
        self.assertEqual(report["expectations"][0]["status"], "failed")

    def test_expectation_report_checks_static_source_file_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            source = root / "maps" / "NewBarkTown.asm"
            source.write_text(
                "NewBarkTown_MapScripts:\n\tdef_scene_scripts\n\twarp_event  1,  1, ELMS_LAB, 1\n",
                encoding="utf-8",
            )

            report = build_expectation_report(
                source_files=("maps/NewBarkTown.asm",),
                expectations=("contains=warp_event", "not-contains=TODO"),
                root=root,
            )

        statuses = {item["id"]: item["status"] for item in report["expectations"]}

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertEqual(report["source_artifact_count"], 1)
        self.assertIn("maps/NewBarkTown.asm", report["evidence_summary"]["source_files"])
        self.assertEqual(statuses["cli_contains_warp_event"], "passed")
        self.assertEqual(statuses["cli_not_contains_TODO"], "passed")

    def test_expectation_report_checks_content_scenario_preconditions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario_report = root / "content_scenarios.json"
            scenario_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "map_bg_event",
                                "source_file": "maps/UnitMap.asm",
                                "state_preconditions": [
                                    {
                                        "id": "map_bg_event_position",
                                        "kind": "map_position",
                                        "values": {
                                            "source_file": "maps/UnitMap.asm",
                                            "map_label": "UnitMap_MapEvents",
                                            "script": "UnitMapSign",
                                        },
                                        "watch_symbols": ["wMapGroup", "wMapNumber", "wXCoord", "wYCoord"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_expectation_report(
                reports=("content_scenarios.json",),
                expectations=(
                    "scenario=content_scenario_1_0000",
                    "precondition=map_position,scenario=content_scenario_1_0000,symbol=wMapGroup",
                    "symbol=wMapGroup",
                ),
                root=root,
            )

        statuses = {item["id"]: item["status"] for item in report["expectations"]}

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertEqual(report["evidence_scenario_count"], 1)
        self.assertEqual(report["evidence_state_precondition_count"], 1)
        self.assertEqual(statuses["cli_scenario_content_scenario_1_0000"], "passed")
        self.assertEqual(statuses["cli_precondition_map_position_content_scenario_1_0000_wMapGroup"], "passed")
        self.assertEqual(statuses["cli_symbol_wMapGroup"], "passed")

    def test_expectation_report_checks_content_state_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_state_report = root / "content_state.json"
            content_state_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "executed": True,
                        "out_state": "patched.state",
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0000",
                                "precondition_kind": "map_position",
                                "source_file": "maps/UnitMap.asm",
                                "status": "ready",
                                "patches": [
                                    {
                                        "symbol": "wMapGroup",
                                        "value": 24,
                                        "value_hex": "18",
                                        "bank_address": "01:DA00",
                                    }
                                ],
                            }
                        ],
                        "execution": {
                            "executed": True,
                            "out_state": "patched.state",
                            "applied_patches": [
                                {
                                    "symbol": "wMapGroup",
                                    "value": 24,
                                    "value_hex": "18",
                                    "observed": 24,
                                    "observed_hex": "18",
                                    "verified": True,
                                    "bank_address": "01:DA00",
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_expectation_report(
                reports=("content_state.json",),
                expectations=(
                    "state-patch=wMapGroup,scenario=content_scenario_1_0000,value=0x18",
                    "state-patch=wMapGroup,applied=true,verified=true,value=24",
                    "symbol=wMapGroup",
                ),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertGreaterEqual(report["evidence_state_patch_count"], 2)
        self.assertIn("wMapGroup", report["evidence_summary"]["symbols"])
        self.assertIn("content_scenario_1_0000", report["evidence_summary"]["scenario_ids"])
        self.assertEqual(
            {item["status"] for item in report["expectations"]},
            {"passed"},
        )

    def test_cli_expect_checks_source_file_exists_and_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            source = root / "maps" / "UnitMap.asm"
            source.write_text("UnitMap:\n\tobject_event 1, 1, SPRITE_CHRIS\n", encoding="utf-8")
            out = root / "expect.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "expect",
                        "--source-file",
                        str(source),
                        "--expect",
                        "contains=object_event",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_expectation_report")
        self.assertTrue(data["passed"])
        self.assertEqual(data["source_artifact_count"], 1)

    def test_cli_expect_writes_json(self) -> None:
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
                                "rule_id": "move.apply_move_model",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "expect.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "expect",
                        "--report",
                        str(trace_index),
                        "--expect",
                        "event=score_delta,symbol=wEnemyAIMoveScores",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_expectation_report")
        self.assertTrue(data["passed"])
