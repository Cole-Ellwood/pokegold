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
from tools.debugger.reporting import build_static_report
from tools.debugger.visualization import build_visualization_report


class VisualizationTests(unittest.TestCase):
    def test_visualization_report_builds_timeline_waterfall_and_graph(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "events": [
                            {
                                "frame": 3,
                                "watch": "wCurDamage",
                                "old_hex": "0000",
                                "new_hex": "002A",
                                "pc_label": "BattleCommand_Test",
                                "pc_bank_address": "01:4000",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            explain_report = root / "explain.json"
            explain_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_causal_explanation",
                        "valid": True,
                        "paths": [
                            {
                                "id": "event_1",
                                "title": "wCurDamage changed",
                                "score": 95,
                                "confidence": 0.93,
                                "nodes": [
                                    {
                                        "id": "state",
                                        "label": "wCurDamage",
                                        "type": "state",
                                    },
                                    {
                                        "id": "source",
                                        "label": "BattleCommand_Test",
                                        "type": "source",
                                    },
                                ],
                                "edges": [
                                    {
                                        "from": "state",
                                        "to": "source",
                                        "relation": "write",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            replay_report = root / "replay.json"
            replay_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_replay_plan",
                        "valid": True,
                        "phase_steps": [
                            {
                                "phase": "reproduce",
                                "steps": [
                                    {
                                        "command": "python -m tools.debugger watch --watch-symbol wCurDamage",
                                        "reason": "observe the changed byte",
                                        "runnable": True,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            dynamic_report = root / "dynamic_write.json"
            dynamic_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_dynamic_taint_report",
                        "valid": True,
                        "write_attribution_count": 1,
                        "write_attributions": [
                            {
                                "target": "wCurDamage",
                                "pc_label": "BattleCommand_Test",
                                "seq": 7,
                                "address": "D141",
                                "mnemonic": "ld [$d141], a",
                                "score": 72,
                                "related_symbols": ["wCurDamage", "BattleCommand_Test"],
                                "related_files": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_visualization_report(
                reports=("watch.json", "explain.json", "replay.json", "dynamic_write.json"),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertGreaterEqual(report["timeline_event_count"], 4)
        self.assertEqual(report["waterfall_step_count"], 1)
        self.assertGreaterEqual(report["graph_edge_count"], 3)
        self.assertFalse(report["interactive"])
        self.assertGreater(report["inspector_item_count"], 0)
        self.assertIn("timeline", report["mermaid_timeline"])
        self.assertIn("BattleCommand_Test", report["mermaid_graph"])
        self.assertIn("dynamic_write", report["content"])
        self.assertIn("Workflow Waterfall", report["content"])

    def test_cli_visualize_writes_static_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "events": [
                            {
                                "frame": 1,
                                "watch": "wCurDamage",
                                "old_hex": "00",
                                "new_hex": "01",
                                "pc_label": "BattleCommand_Test",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "visualization.html"
            json_out = root / "visualization.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "visualize",
                        "--report",
                        str(watch_report),
                        "--format",
                        "html",
                        "--out",
                        str(out),
                        "--json-out",
                        str(json_out),
                    ]
                )

            content = out.read_text(encoding="utf-8")
            data = json.loads(json_out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("<!doctype html>", content)
        self.assertIn('data-kind="interactive-inspector"', content)
        self.assertIn('id="evidence-search"', content)
        self.assertIn("debugger-visualization-data", content)
        self.assertEqual(data["kind"], "unified_debugger_visualization")
        self.assertTrue(data["interactive"])
        self.assertGreaterEqual(data["timeline_event_count"], 1)
        self.assertGreater(data["inspector_item_count"], 0)

    def test_visualization_consumes_content_behavioral_probes(self) -> None:
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
                                "scenario_type": "map_warp",
                                "source_file": "maps/UnitMap.asm",
                                "line": 4,
                                "runtime_targets": {
                                    "source_symbols": ["UnitMap_MapEvents"],
                                    "trace_symbols": ["WarpCheck", "ReadMapEvents"],
                                    "watch_symbols": ["wMapGroup"],
                                },
                                "behavioral_probes": [
                                    {
                                        "id": "content_replay_route",
                                        "phase": "replay",
                                        "proof_level": "runtime_planned",
                                        "command": "python -m tools.debugger replay --scenario content.jsonl --scenario-id content_scenario_1_0000",
                                        "reason": "prove in ROM when positioned",
                                        "runnable": True,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_visualization_report(reports=("content_scenarios.json",), root=root)

        self.assertTrue(report["valid"])
        self.assertEqual(report["waterfall_step_count"], 1)
        graph_node_types = {node["type"] for node in report["graph"]["nodes"]}
        self.assertIn("behavioral_probe", graph_node_types)
        self.assertIn("runtime_helper", graph_node_types)
        self.assertIn("runtime_watch", graph_node_types)
        self.assertIn("content_replay_route", report["mermaid_graph"])
        self.assertIn("WarpCheck", report["mermaid_graph"])
        self.assertIn("wMapGroup", report["mermaid_graph"])
        self.assertIn("python -m tools.debugger replay", report["content"])

    def test_visualization_consumes_content_state_materializations(self) -> None:
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
                                "commands": [
                                    "python -m tools.debugger watch --watch-symbol wMapGroup --execute --save-state <patched-state>"
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
                                    "verified": True,
                                    "bank_address": "01:DA00",
                                }
                            ],
                        },
                        "commands": [
                            "python -m tools.debugger content-state --report content_scenarios.json --execute"
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_visualization_report(reports=("content_state.json",), root=root)

        graph_node_types = {node["type"] for node in report["graph"]["nodes"]}
        lanes = {lane["lane"] for lane in report["lane_summary"]}

        self.assertTrue(report["valid"])
        self.assertGreaterEqual(report["timeline_event_count"], 2)
        self.assertGreaterEqual(report["waterfall_step_count"], 2)
        self.assertIn("content_state", lanes)
        self.assertIn("content_state_materialization", graph_node_types)
        self.assertIn("runtime_state_patch", graph_node_types)
        self.assertIn("save_state", graph_node_types)
        self.assertIn("wMapGroup", report["mermaid_graph"])
        self.assertIn("patched.state", report["mermaid_graph"])
        self.assertIn("python -m tools.debugger content-state", report["content"])

    def test_visualization_consumes_instruction_trace_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_report = root / "instruction_trace.json"
            trace_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": True,
                        "executed": True,
                        "effective_save_state": "patched.state",
                        "captured_frame_count": 2,
                        "functions": [
                            {
                                "symbol": "RunScriptCommand",
                                "instruction_count": 5,
                                "hook_count": 5,
                                "instructions": [
                                    {
                                        "bank_address": "01:4000",
                                        "mnemonic": "ld a, [$d15e]",
                                    }
                                ],
                            },
                            {
                                "symbol": "CallScript",
                                "instruction_count": 2,
                                "hook_count": 2,
                                "instructions": [],
                            },
                        ],
                        "watches": [{"name": "wScriptPos"}],
                        "execution_validation": {
                            "attempted": True,
                            "required": True,
                            "planned_hook_count": 7,
                            "captured_frame_count": 2,
                            "hit": True,
                            "hit_function_symbols": ["RunScriptCommand"],
                            "missing_function_symbols": ["CallScript"],
                            "watch_symbols": ["wScriptPos"],
                            "ready_for_dynamic_taint": True,
                            "trace_record_limit_hit": True,
                        },
                        "trace_output": {
                            "path": ".local\\tmp\\instruction_trace.jsonl",
                            "written": True,
                            "record_count": 2,
                        },
                        "sample_records": [
                            {
                                "seq": 0,
                                "pc_label": "RunScriptCommand",
                                "mnemonic": "ld a, [$d15e]",
                                "pc_bank_address": "01:4000",
                                "function": "RunScriptCommand",
                            }
                        ],
                        "commands": [
                            "python -m tools.debugger trace-instructions --symbol RunScriptCommand --symbol CallScript --execute --require-hit --out-trace .local\\tmp\\instruction_trace.jsonl"
                        ],
                    }
                ),
                encoding="utf-8",
            )
            ready_report = root / "instruction_trace_ready.json"
            ready_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": True,
                        "executed": True,
                        "effective_save_state": "patched.state",
                        "captured_frame_count": 3,
                        "functions": [
                            {
                                "symbol": "RunScriptCommand",
                                "instruction_count": 5,
                                "hook_count": 5,
                                "instructions": [],
                            }
                        ],
                        "watches": [{"name": "wScriptPos"}],
                        "execution_validation": {
                            "attempted": True,
                            "required": True,
                            "planned_hook_count": 5,
                            "captured_frame_count": 3,
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
                            "record_count": 3,
                        },
                        "commands": [
                            "python -m tools.debugger trace-instructions --symbol RunScriptCommand --execute --require-hit --out-trace .local\\tmp\\ready_trace.jsonl"
                        ],
                    }
                ),
                encoding="utf-8",
            )

            visualization = build_visualization_report(
                reports=("instruction_trace_ready.json", "instruction_trace.json"),
                root=root,
            )
            static_report = build_static_report(
                reports=("instruction_trace_ready.json", "instruction_trace.json"),
                root=root,
            )

        graph_node_types = {node["type"] for node in visualization["graph"]["nodes"]}
        lanes = {lane["lane"] for lane in visualization["lane_summary"]}
        event_types = {event["type"] for event in visualization["timeline"]}
        waterfall_statuses = {step["status"] for step in visualization["waterfall"]}
        graph_relations = {edge["relation"] for edge in visualization["graph"]["edges"]}

        self.assertTrue(visualization["valid"])
        self.assertIn("instruction_trace", lanes)
        self.assertGreaterEqual(visualization["waterfall_step_count"], 4)
        self.assertIn("ready", waterfall_statuses)
        self.assertIn("limit", waterfall_statuses)
        self.assertIn("writes_trace", graph_relations)
        self.assertIn("validation_ready", event_types)
        self.assertIn("validation_partial", event_types)
        self.assertIn("validation_limit", event_types)
        self.assertIn("instruction_trace_validation", graph_node_types)
        self.assertIn("instruction_trace_output", graph_node_types)
        self.assertIn("instruction_hit", graph_node_types)
        self.assertIn("instruction_miss", graph_node_types)
        self.assertIn("RunScriptCommand", visualization["mermaid_graph"])
        self.assertIn("CallScript", visualization["mermaid_graph"])
        self.assertIn("Instruction trace ready for dynamic taint", visualization["content"])
        self.assertIn("Instruction trace missed selected routines", visualization["content"])
        self.assertIn("ready dynamic-taint trace: .local\\tmp\\ready_trace.jsonl", static_report["content"])
        self.assertIn("instruction trace missed functions: CallScript", static_report["content"])
        self.assertIn("instruction trace validation: hit=True", static_report["content"])

    def test_visualization_preserves_next_step_proof_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            next_report = root / "next.json"
            next_report.write_text(
                json.dumps(build_next_step(symptom="boss selected wrong switch")),
                encoding="utf-8",
            )

            visualization = build_visualization_report(reports=("next.json",), root=root)

        event_types = {event["type"] for event in visualization["timeline"]}
        waterfall_statuses = {step["status"] for step in visualization["waterfall"]}
        graph_relations = {edge["relation"] for edge in visualization["graph"]["edges"]}
        graph_node_types = {node["type"] for node in visualization["graph"]["nodes"]}
        graph_labels = {node["label"] for node in visualization["graph"]["nodes"]}

        self.assertTrue(visualization["valid"])
        self.assertEqual(visualization["warning_count"], 0)
        self.assertIn("next_step", event_types)
        self.assertIn("needs-input", waterfall_statuses)
        self.assertIn("first_command", graph_relations)
        self.assertIn("source_ref", graph_relations)
        self.assertIn("evidence_standard", graph_relations)
        self.assertIn("disproof_standard", graph_relations)
        self.assertIn("regression_gate", graph_relations)
        self.assertIn("source_ref", graph_node_types)
        self.assertIn("evidence_standard", graph_node_types)
        self.assertIn("disproof_standard", graph_node_types)
        self.assertIn("engine/battle/ai/boss_policy_switch.asm", graph_labels)
        self.assertIn("regression_gate", graph_node_types)
        self.assertIn("Next proof path", visualization["content"])
        self.assertIn("rom-switch-materialize", visualization["content"])
        self.assertIn("tools/boss_ai_debugger/rom_switch_materialize.py", visualization["content"])
        self.assertIn("evidence_standard=", visualization["content"])
        self.assertIn("disproof_standard=", visualization["content"])
        self.assertIn("scenario JSONL with the disputed switch case", visualization["content"])
        self.assertIn("Regression gate", visualization["content"])
        self.assertIn("Proof limit:", visualization["content"])

    def test_visualization_preserves_ready_capability_audit_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit_report = root / "audit.json"
            audit_report.write_text(
                json.dumps(build_capability_report()),
                encoding="utf-8",
            )

            visualization = build_visualization_report(reports=("audit.json",), root=root)

        lanes = {lane["lane"] for lane in visualization["lane_summary"]}
        event_types = {event["type"] for event in visualization["timeline"]}
        graph_node_types = {node["type"] for node in visualization["graph"]["nodes"]}

        self.assertTrue(visualization["valid"])
        self.assertEqual(visualization["warning_count"], 0)
        self.assertIn("graph", lanes)
        self.assertEqual(event_types, set())
        self.assertNotIn("capability_partial", event_types)
        self.assertIn("capability_audit", graph_node_types)
        self.assertNotIn("gap_action", graph_node_types)
        self.assertIn("ready=True", visualization["content"])
