from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.impact import build_impact_report
from tools.debugger.localize import build_localization_plan
from tools.debugger.ranking import rank_findings
from tools.debugger.setup_plan import build_setup_plan
from tools.debugger.visualization import build_visualization_report


class RankFindingsTests(unittest.TestCase):
    def test_rank_localize_and_impact_consume_dynamic_taint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dynamic_taint = root / "dynamic_taint.json"
            dynamic_taint.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_dynamic_taint_report",
                        "valid": True,
                        "errors": [],
                        "warnings": [],
                        "targets": [
                            {
                                "symbol": "wCurDamage",
                                "found": True,
                                "sink_count": 1,
                                "contributor_count": 1,
                                "sinks": [{"routine": "BattleCommand_Test", "access": "dynamic_write"}],
                                "contributors": [
                                    {
                                        "symbol": "move_power",
                                        "relation": "register_taints_sink",
                                    }
                                ],
                            }
                        ],
                        "paths": [
                            {
                                "title": "move_power -> wCurDamage",
                                "target": "wCurDamage",
                                "access": "dynamic_write",
                                "score": 92,
                                "confidence": 0.9,
                                "evidence": ["seq=3 pc=$4005", "ld [hli], a"],
                                "commands": ["python -m tools.debugger replay --symbol wCurDamage"],
                                "related_symbols": ["wCurDamage", "move_power"],
                                "related_files": [],
                                "contributors": [
                                    {
                                        "symbol": "move_power",
                                        "relation": "register_taints_sink",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("dynamic_taint.json",), root=root)
            localized = build_localization_plan(reports=("dynamic_taint.json",), root=root)
            impact = build_impact_report(reports=("dynamic_taint.json",), root=root)

        self.assertIn("taint_path", {finding["type"] for finding in ranked["findings"]})
        self.assertIn("wCurDamage", {candidate["id"] for candidate in localized["candidates"]})
        self.assertIn("taint_path", {item["type"] for item in impact["items"]})

    def test_rank_localize_and_impact_consume_dynamic_write_attribution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dynamic_taint = root / "dynamic_write.json"
            dynamic_taint.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_dynamic_taint_report",
                        "valid": True,
                        "errors": [],
                        "warnings": [],
                        "targets": [
                            {
                                "symbol": "wCurDamage",
                                "found": True,
                                "sink_count": 1,
                                "write_attribution_count": 1,
                                "sinks": [{"routine": "UnitWriter", "access": "dynamic_write"}],
                                "contributors": [],
                            }
                        ],
                        "paths": [],
                        "write_attributions": [
                            {
                                "target": "wCurDamage",
                                "pc_label": "UnitWriter",
                                "mnemonic": "ld [$d141], a",
                                "score": 72,
                                "confidence": 0.76,
                                "evidence": [
                                    "seq=0 pc=$4000",
                                    "ld [$d141], a",
                                    "write wCurDamage@$D141",
                                    "sources=register:a=$2A",
                                ],
                                "related_symbols": ["wCurDamage", "UnitWriter", "a"],
                                "related_files": [],
                                "commands": ["python -m tools.debugger explain --symbol wCurDamage"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("dynamic_write.json",), root=root)
            localized = build_localization_plan(reports=("dynamic_write.json",), root=root)
            impact = build_impact_report(reports=("dynamic_write.json",), root=root)

        self.assertIn("reverse_attribution", {finding["type"] for finding in ranked["findings"]})
        self.assertIn("wCurDamage", {candidate["id"] for candidate in localized["candidates"]})
        self.assertIn("UnitWriter", {candidate["id"] for candidate in localized["candidates"]})
        self.assertIn("reverse_attribution", {item["type"] for item in impact["items"]})

    def test_rank_impact_and_visualization_consume_state_space_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "patched.state").write_bytes(b"patched-state")
            (root / "state_space.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_state_space",
                        "valid": True,
                        "executed": True,
                        "scenario_id": "script_entry_1",
                        "source_files": ["maps/UnitMap.asm"],
                        "out_state": "patched.state",
                        "state_space": {
                            "scenario_ids": ["script_entry_1"],
                            "source_files": ["maps/UnitMap.asm"],
                            "out_state": "patched.state",
                            "patches": [
                                {
                                    "symbol": "wScriptPos",
                                    "base_symbol": "wScriptPos",
                                    "value": 80,
                                    "value_hex": "50",
                                    "bank_address": "01:DA11",
                                    "scenario_id": "script_entry_1",
                                    "source_file": "maps/UnitMap.asm",
                                }
                            ],
                        },
                        "execution": {
                            "executed": True,
                            "out_state": "patched.state",
                            "applied_patches": [
                                {
                                    "symbol": "wScriptPos",
                                    "base_symbol": "wScriptPos",
                                    "value": 80,
                                    "value_hex": "50",
                                    "observed": 80,
                                    "observed_hex": "50",
                                    "verified": True,
                                    "bank_address": "01:DA11",
                                    "scenario_id": "script_entry_1",
                                    "source_file": "maps/UnitMap.asm",
                                    "applied": True,
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("state_space.json",), root=root)
            impact = build_impact_report(reports=("state_space.json",), root=root)
            visualization = build_visualization_report(reports=("state_space.json",), root=root)

        ranked_types = {item["type"] for item in ranked["findings"]}
        impact_types = {item["type"] for item in impact["items"]}
        lanes = {item["lane"] for item in visualization["timeline"]}
        graph_node_types = {node["type"] for node in visualization["graph"]["nodes"]}
        commands = "\n".join(
            action
            for item in impact["items"]
            for action in item.get("next_actions", [])
        )

        self.assertIn("state_space_ready", ranked_types)
        self.assertIn("state_space_executed", ranked_types)
        self.assertIn("state_space_ready", impact_types)
        self.assertIn("state_space_executed", impact_types)
        self.assertIn("wScriptPos", {symbol for item in impact["items"] for symbol in item.get("related_symbols", [])})
        self.assertIn("maps/UnitMap.asm", {path for item in impact["items"] for path in item.get("related_files", [])})
        self.assertIn("tools.debugger replay --report state_space.json --scenario-id script_entry_1", commands)
        self.assertIn("tools.debugger watch --watch-symbol wScriptPos --save-state patched.state --execute", commands)
        self.assertIn("state_space", lanes)
        self.assertIn("runtime", lanes)
        self.assertIn("state_space_materialization", graph_node_types)
        self.assertIn("runtime_state_patch", graph_node_types)
        self.assertIn("save_state", graph_node_types)

    def test_rank_and_impact_consume_setup_trigger_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_report = build_setup_plan(
                symbols=("BattleCommand_DamageCalc",),
                watch_symbols=("wCurDamage",),
                root=root,
            )
            (root / "setup.json").write_text(
                json.dumps(setup_report),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("setup.json",), root=root)
            impact = build_impact_report(reports=("setup.json",), root=root)

        ranked_types = {finding["type"] for finding in ranked["findings"]}
        impact_types = {item["type"] for item in impact["items"]}
        ranked_gap = next(item for item in ranked["findings"] if item["type"] == "setup_trigger_gap")
        impact_gap = next(item for item in impact["items"] if item["type"] == "setup_trigger_gap")

        self.assertIn("setup_trigger_gap", ranked_types)
        self.assertIn("setup_trigger_gap", impact_types)
        self.assertIn("state:synthesizable", ranked_gap["evidence"])
        self.assertIn("trace-instructions", "\n".join(ranked_gap["next_actions"]))
        self.assertIn("wCurDamage", impact_gap["related_symbols"])

    def test_rank_findings_orders_failures_above_gaps(self) -> None:
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
                                "command": "python test.py",
                                "stderr_tail": ["boom"],
                                "stdout_tail": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            compare_report = root / "compare.json"
            compare_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_compare_plan",
                        "matches": [
                            {
                                "id": "static",
                                "gaps": ["not dynamic"],
                                "materialization_commands": ["prove"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = rank_findings(
                reports=("gate.json", "compare.json"),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["findings"][0]["type"], "gate_failed")
        self.assertEqual(report["findings"][1]["type"], "compare_gap")

    def test_rank_findings_promotes_runtime_state_impossibilities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_report = root / "runtime_state.json"
            runtime_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_runtime_state_report",
                        "save_state": "for_codex1.sgm",
                        "passed": False,
                        "commands": ["python -m tools.debugger state-inspect"],
                        "findings": [
                            {
                                "id": "invalid_script_pc",
                                "type": "runtime_state_impossible",
                                "severity": 94,
                                "confidence": 0.9,
                                "title": "Script VM is running from an invalid ROM address",
                                "evidence": ["wScriptBank:wScriptPos=B4:0002"],
                                "next_actions": ["python -m tools.debugger watch --watch-symbol wScriptBank"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = rank_findings(reports=("runtime_state.json",), root=root)

        self.assertTrue(report["valid"])
        self.assertEqual(report["findings"][0]["type"], "runtime_state_impossible")
        self.assertGreaterEqual(report["findings"][0]["severity"], 94)
        self.assertIn("B4:0002", report["findings"][0]["evidence"][0])

    def test_rank_findings_calibrates_rom_surface_severity(self) -> None:
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
                                "id": "docs/notes.md",
                                "commands": [
                                    "python -m tools.debugger coverage --changed-file docs/notes.md"
                                ],
                            },
                            {
                                "type": "source_file",
                                "id": "home/bankswitch.asm",
                                "commands": [
                                    "python -m tools.debugger coverage --changed-file home/bankswitch.asm"
                                ],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = rank_findings(reports=("coverage.json",), root=root)

        first = report["findings"][0]

        self.assertTrue(report["valid"])
        self.assertIn("home/bankswitch.asm", first["title"])
        self.assertEqual(first["surface"], "ROM banking / ABI")
        self.assertGreater(first["severity"], first["severity_base"])
        self.assertIn("ROM surface calibration: ROM banking / ABI (+10)", first["evidence"])

    def test_rank_and_impact_consume_content_mirror_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_report = root / "content.json"
            content_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_mirror",
                        "valid": True,
                        "passed": False,
                        "invariant_count": 1,
                        "invariants": [
                            {
                                "id": "maps/UnitMap.asm:incbin_asset_exists:gfx/missing.2bpp",
                                "type": "incbin_asset_exists",
                                "status": "failed",
                                "severity": 78,
                                "title": "Missing INCBIN asset: gfx/missing.2bpp",
                                "source_file": "maps/UnitMap.asm",
                                "evidence": ["asset=gfx/missing.2bpp"],
                                "commands": [
                                    "python -m tools.debugger content-mirror --source-file maps/UnitMap.asm"
                                ],
                                "related_files": ["maps/UnitMap.asm", "gfx/missing.2bpp"],
                            }
                        ],
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("content.json",), root=root)
            impact = build_impact_report(reports=("content.json",), root=root)

        self.assertTrue(ranked["valid"])
        self.assertEqual(ranked["findings"][0]["type"], "content_mirror_failed")
        self.assertTrue(impact["valid"])
        self.assertEqual(impact["items"][0]["type"], "content_mirror_failed")
        self.assertIn("Maps, scripts, and text", {item["surface"] for item in impact["items"]})

    def test_rank_and_impact_consume_content_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenario_report = root / "content_scenarios.json"
            scenario_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenario_count": 1,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "map_warp",
                                "proof_level": "semantic_source",
                                "source_file": "maps/UnitMap.asm",
                                "line": 3,
                                "expected": ["destination_map=ROUTE_29"],
                                "commands": [
                                    "python -m tools.debugger replay --changed-file maps/UnitMap.asm --scenario-id content_scenario_1_0000"
                                ],
                            }
                        ],
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("content_scenarios.json",), root=root)
            impact = build_impact_report(reports=("content_scenarios.json",), root=root)

        self.assertTrue(ranked["valid"])
        self.assertIn("content_scenario", {item["type"] for item in ranked["findings"]})
        self.assertTrue(impact["valid"])
        self.assertIn("content_scenario", {item["type"] for item in impact["items"]})
        self.assertIn("Maps, scripts, and text", {item["surface"] for item in impact["items"]})

    def test_rank_and_impact_consume_content_state_materializations(self) -> None:
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
                        "materialization_count": 2,
                        "patch_count": 1,
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0000",
                                "scenario_type": "map_bg_event",
                                "precondition_kind": "map_position",
                                "source_file": "maps/UnitMap.asm",
                                "map_name": "UnitMap",
                                "map_resolution": {
                                    "source_file": "data/maps/maps.asm",
                                    "map_group": 24,
                                    "map_number": 3,
                                },
                                "status": "ready",
                                "patches": [
                                    {
                                        "symbol": "wMapGroup",
                                        "value": 24,
                                        "value_hex": "18",
                                        "bank_address": "01:DA00",
                                    }
                                ],
                            },
                            {
                                "scenario_id": "content_scenario_2_0000",
                                "precondition_kind": "map_position",
                                "source_file": "maps/MissingMap.asm",
                                "map_name": "MissingMap",
                                "status": "blocked",
                                "patches": [],
                                "errors": ["map not found in data/maps/maps.asm: MissingMap"],
                            },
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
                        "commands": [
                            "python -m tools.debugger content-state --report content_scenarios.json --execute"
                        ],
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("content_state.json",), root=root)
            impact = build_impact_report(reports=("content_state.json",), root=root)

        ranked_types = [item["type"] for item in ranked["findings"]]
        ranked_actions = "\n".join(
            action
            for finding in ranked["findings"]
            for action in finding["next_actions"]
        )
        impact_types = {item["type"] for item in impact["items"]}
        ready_item = next(item for item in impact["items"] if item["type"] == "content_state_ready")

        self.assertTrue(ranked["valid"])
        self.assertIn("content_state_ready", ranked_types)
        self.assertIn("content_state_blocked", ranked_types)
        self.assertIn("content_state_executed", ranked_types)
        self.assertLess(ranked_types.index("content_state_blocked"), ranked_types.index("content_state_ready"))
        self.assertIn(
            "tools.debugger expect --report content_state.json --expect state-patch=wMapGroup,scenario=content_scenario_1_0000,value=0x18",
            ranked_actions,
        )
        self.assertIn(
            "tools.debugger replay --report content_state.json --scenario-id content_scenario_1_0000 --execute-watch",
            ranked_actions,
        )
        self.assertIn(
            "tools.debugger watch --watch-symbol wMapGroup --save-state patched.state --execute",
            ranked_actions,
        )
        self.assertTrue(impact["valid"])
        self.assertIn("content_state_ready", impact_types)
        self.assertIn("content_state_blocked", impact_types)
        self.assertIn("content_state_executed", impact_types)
        self.assertIn("wMapGroup", ready_item["related_symbols"])
        self.assertIn("maps/UnitMap.asm", ready_item["related_files"])
        self.assertIn("data/maps/maps.asm", ready_item["related_files"])

    def test_rank_and_impact_consume_instruction_trace_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "missed_trace.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": False,
                        "executed": True,
                        "effective_save_state": "content.state",
                        "captured_frame_count": 0,
                        "functions": [
                            {
                                "symbol": "ApplyMovement",
                                "instruction_count": 4,
                                "hook_count": 4,
                            }
                        ],
                        "watches": [{"name": "wMovementPointer"}],
                        "execution_validation": {
                            "attempted": True,
                            "required": True,
                            "planned_hook_count": 4,
                            "captured_frame_count": 0,
                            "hit": False,
                            "hit_function_symbols": [],
                            "missing_function_symbols": ["ApplyMovement"],
                            "watch_symbols": ["wMovementPointer"],
                            "ready_for_dynamic_taint": False,
                        },
                        "trace_output": {
                            "path": ".local\\tmp\\missed_trace.jsonl",
                            "written": True,
                            "record_count": 0,
                        },
                        "commands": [
                            "python -m tools.debugger trace-instructions --report content_state.json --scenario-id content_scenario_1_0000 --execute --require-hit"
                        ],
                        "errors": ["instruction trace executed but none of the selected hooks fired"],
                        "warnings": [],
                    }
                ),
                encoding="utf-8",
            )
            (root / "ready_trace.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": True,
                        "executed": True,
                        "effective_save_state": "content.state",
                        "captured_frame_count": 2,
                        "functions": [
                            {
                                "symbol": "RunScriptCommand",
                                "instruction_count": 5,
                                "hook_count": 5,
                            }
                        ],
                        "watches": [{"name": "wScriptPos"}],
                        "execution_validation": {
                            "attempted": True,
                            "required": True,
                            "planned_hook_count": 5,
                            "captured_frame_count": 2,
                            "hit": True,
                            "hit_function_symbols": ["RunScriptCommand"],
                            "missing_function_symbols": [],
                            "watch_symbols": ["wScriptPos"],
                            "ready_for_dynamic_taint": True,
                            "trace_record_limit_hit": False,
                        },
                        "trace_output": {
                            "path": ".local\\tmp\\ready_trace.jsonl",
                            "written": True,
                            "record_count": 2,
                        },
                        "commands": [],
                        "errors": [],
                        "warnings": [],
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("missed_trace.json", "ready_trace.json"), root=root)
            impact = build_impact_report(reports=("missed_trace.json", "ready_trace.json"), root=root)

        ranked_types = [item["type"] for item in ranked["findings"]]
        ranked_actions = "\n".join(
            action
            for finding in ranked["findings"]
            for action in finding["next_actions"]
        )
        impact_types = {item["type"] for item in impact["items"]}
        ready_item = next(item for item in impact["items"] if item["type"] == "instruction_trace_ready")
        miss_item = next(item for item in impact["items"] if item["type"] == "instruction_trace_miss")

        self.assertTrue(ranked["valid"])
        self.assertEqual(ranked_types[0], "instruction_trace_miss")
        self.assertIn("instruction_trace_miss", ranked_types)
        self.assertIn("instruction_trace_ready", ranked_types)
        self.assertLess(ranked_types.index("instruction_trace_miss"), ranked_types.index("instruction_trace_ready"))
        self.assertIn(
            "tools.debugger dynamic-taint --trace .local\\tmp\\ready_trace.jsonl --sink-symbol wScriptPos",
            ranked_actions,
        )
        self.assertIn("instruction_trace_miss", impact_types)
        self.assertIn("instruction_trace_ready", impact_types)
        self.assertIn("RunScriptCommand", ready_item["related_symbols"])
        self.assertIn("wScriptPos", ready_item["related_symbols"])
        self.assertIn("ApplyMovement", miss_item["related_symbols"])

    def test_cli_rank_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ingest_report = root / "ingest.json"
            ingest_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_ingest_manifest",
                        "artifacts": [
                            {
                                "kind": "scenario",
                                "path": "bad.jsonl",
                                "errors": ["invalid JSON"],
                                "warnings": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "rank.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "rank",
                        "--report",
                        str(ingest_report),
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_ranked_findings")
            self.assertEqual(data["findings"][0]["type"], "ingest_error")
