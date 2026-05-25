from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.minimize import build_minimization_plan


class MinimizationTests(unittest.TestCase):
    def test_minimize_extracts_boss_ai_scenario_subset_and_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenarios = root / "scenarios.jsonl"
            scenarios.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "id": "case_keep",
                                "family": "unit",
                                "moves": [{"id": "a"}, {"id": "b"}],
                            }
                        ),
                        json.dumps(
                            {
                                "id": "case_other",
                                "family": "unit",
                                "moves": [{"id": "c"}],
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            out = root / "subset.jsonl"

            report = build_minimization_plan(
                scenarios=("scenarios.jsonl",),
                scenario_ids=("case_keep",),
                symbols=("BossAI_SelectMove",),
                out_scenarios="subset.jsonl",
                root=root,
            )

            subset_lines = out.read_text(encoding="utf-8").splitlines()

        self.assertTrue(report["valid"])
        self.assertEqual(report["selected_scenario_ids"], ["case_keep"])
        self.assertEqual(report["subset_output"]["record_count"], 1)
        self.assertEqual(len(subset_lines), 1)
        commands = "\n".join(report["commands"])
        self.assertIn("tools.boss_ai_debugger minimize", commands)
        self.assertIn("counterfactual", commands)

    def test_minimize_routes_damage_bug_to_ddmin_and_replay(self) -> None:
        report = build_minimization_plan(
            symbols=("wCurDamage",),
            bug_ids=("hp_d_clobber",),
        )
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("tools.damage_debugger.minimize --bug hp_d_clobber", commands)
        self.assertIn("tools.damage_debugger.replay", commands)

    def test_minimize_reduces_generic_trace_against_expectations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "events": [
                            {
                                "access": "read",
                                "symbol": "wBattleMonAttack",
                                "address": "D142",
                                "value": "2A",
                                "pc_label": "BattleCommand_DamageCalc",
                            },
                            {
                                "access": "write",
                                "symbol": "wCurDamage",
                                "address": "D141",
                                "old_value": "0000",
                                "new_value": "002A",
                                "pc_label": "BattleCommand_DamageCalc",
                            },
                            {
                                "access": "read",
                                "symbol": "wUnrelated",
                                "address": "D200",
                                "value": "FF",
                                "pc_label": "OtherRoutine",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out_trace = root / "minimized_trace.json"

            report = build_minimization_plan(
                traces=(str(trace),),
                expectations=(
                    "event=memory_read,symbol=wBattleMonAttack",
                    "event=memory_write,symbol=wCurDamage",
                ),
                out_trace=str(out_trace),
                root=root,
            )
            minimized = json.loads(out_trace.read_text(encoding="utf-8"))

        evidence = report["evidence_minimization"]

        self.assertTrue(report["valid"])
        self.assertTrue(evidence["attempted"])
        self.assertTrue(evidence["preserved"])
        self.assertEqual(evidence["original_count"], 3)
        self.assertEqual(evidence["minimized_count"], 2)
        self.assertEqual(len(minimized["events"]), 2)
        self.assertEqual(
            {event["symbol"] for event in minimized["events"]},
            {"wBattleMonAttack", "wCurDamage"},
        )

    def test_minimize_reduces_watch_report_and_dynamic_context(self) -> None:
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
                                "watch": "wNoise",
                                "old_hex": "00",
                                "new_hex": "01",
                                "pc_label": "NoiseRoutine",
                            },
                            {
                                "watch": "wCurDamage",
                                "old_hex": "0000",
                                "new_hex": "3400",
                                "pc_label": "BattleCommand_Final",
                                "dynamic_context": {
                                    "context_frame_count": 3,
                                    "prelude": [
                                        {
                                            "kind": "runtime_context_frame",
                                            "event_type": "control_flow",
                                            "frame": 0,
                                            "pc_label": "NoiseRoutine",
                                        },
                                        {
                                            "kind": "runtime_context_frame",
                                            "event_type": "control_flow",
                                            "frame": 1,
                                            "pc_label": "BattleCommand_Seed",
                                        },
                                        {
                                            "kind": "runtime_context_frame",
                                            "event_type": "control_flow",
                                            "frame": 2,
                                            "pc_label": "BattleCommand_DamageCalc",
                                        },
                                    ],
                                    "after": {
                                        "kind": "runtime_context_frame",
                                        "event_type": "control_flow",
                                        "frame": 3,
                                        "pc_label": "BattleCommand_Final",
                                    },
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out_trace = root / "minimized_watch.json"

            report = build_minimization_plan(
                reports=("watch.json",),
                expectations=(
                    "event=watch_change,symbol=wCurDamage",
                    "event=control_flow,symbol=BattleCommand_DamageCalc",
                ),
                out_trace="minimized_watch.json",
                root=root,
            )
            minimized = json.loads(out_trace.read_text(encoding="utf-8"))

        evidence = report["evidence_minimization"]
        event = minimized["events"][0]
        context = event["dynamic_context"]

        self.assertTrue(report["valid"])
        self.assertTrue(evidence["preserved"])
        self.assertEqual(evidence["source_kind"], "report")
        self.assertEqual(evidence["original_count"], 2)
        self.assertEqual(evidence["minimized_count"], 1)
        self.assertEqual(evidence["context_frame_original_count"], 3)
        self.assertEqual(evidence["context_frame_minimized_count"], 1)
        self.assertEqual(evidence["context_frame_removed_count"], 2)
        self.assertEqual(len(minimized["events"]), 1)
        self.assertEqual(event["watch"], "wCurDamage")
        self.assertEqual(context["context_frame_count"], 1)
        self.assertEqual(context["prelude"][0]["pc_label"], "BattleCommand_DamageCalc")

    def test_minimize_reduces_content_state_patch_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_state = root / "content_state.json"
            content_state.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "executed": False,
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
                                    },
                                    {
                                        "symbol": "wMapNumber",
                                        "value": 3,
                                        "value_hex": "03",
                                        "bank_address": "01:DA01",
                                    },
                                    {
                                        "symbol": "wXCoord",
                                        "value": 6,
                                        "value_hex": "06",
                                        "bank_address": "01:DA03",
                                    },
                                ],
                            }
                        ],
                        "patch_count": 3,
                        "commands": [
                            "python -m tools.debugger content-state --report content_scenarios.json --execute"
                        ],
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )
            out_state_report = root / "minimized_content_state.json"

            report = build_minimization_plan(
                reports=("content_state.json",),
                expectations=("state-patch=wMapGroup,scenario=content_scenario_1_0000,value=0x18",),
                out_state_report="minimized_content_state.json",
                root=root,
            )
            minimized = json.loads(out_state_report.read_text(encoding="utf-8"))

        state_patch = report["state_patch_minimization"]
        commands = "\n".join(report["commands"])
        patches = minimized["materializations"][0]["patches"]

        self.assertTrue(report["valid"])
        self.assertTrue(state_patch["attempted"])
        self.assertTrue(state_patch["preserved"])
        self.assertEqual(state_patch["original_patch_count"], 3)
        self.assertEqual(state_patch["minimized_patch_count"], 1)
        self.assertEqual(state_patch["removed_patch_count"], 2)
        self.assertTrue(state_patch["written"])
        self.assertIn("maps/UnitMap.asm", state_patch["source_files"])
        self.assertEqual([patch["symbol"] for patch in patches], ["wMapGroup"])
        self.assertTrue(minimized["minimized_evidence_view"])
        self.assertIn("tools.debugger expect --report minimized_content_state.json", commands)
        self.assertIn("tools.debugger replay --report minimized_content_state.json --scenario-id content_scenario_1_0000", commands)
        self.assertIn("tools.debugger compare --report minimized_content_state.json", commands)

    def test_minimize_reduces_generic_state_space_patch_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_space = root / "state_space.json"
            state_space.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_state_space",
                        "valid": True,
                        "state_space": {
                            "surface": "script_entry",
                            "patches": [
                                {
                                    "symbol": "wScriptBank",
                                    "value": 2,
                                    "value_hex": "02",
                                    "source_file": "maps/UnitMap.asm",
                                    "scenario_id": "script_entry_1",
                                },
                                {
                                    "symbol": "wScriptPos",
                                    "value": 0x50,
                                    "value_hex": "50",
                                    "source_file": "maps/UnitMap.asm",
                                    "scenario_id": "script_entry_1",
                                },
                                {
                                    "symbol": "wUnusedDebugByte",
                                    "value": 255,
                                    "value_hex": "ff",
                                    "source_file": "engine/debug.asm",
                                },
                            ],
                        },
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )
            out_state_report = root / "minimized_state_space.json"

            report = build_minimization_plan(
                reports=("state_space.json",),
                expectations=("state-patch=wScriptPos,scenario=script_entry_1,value=0x50",),
                out_state_report="minimized_state_space.json",
                root=root,
            )
            minimized = json.loads(out_state_report.read_text(encoding="utf-8"))

        state_patch = report["state_patch_minimization"]
        patches = minimized["state_space"]["patches"]

        self.assertTrue(report["valid"])
        self.assertTrue(state_patch["attempted"])
        self.assertTrue(state_patch["preserved"])
        self.assertEqual(state_patch["content_state_report_count"], 0)
        self.assertEqual(state_patch["state_space_report_count"], 1)
        self.assertEqual(state_patch["original_patch_count"], 3)
        self.assertEqual(state_patch["minimized_patch_count"], 1)
        self.assertEqual(state_patch["removed_patch_count"], 2)
        self.assertIn("script_entry_1", state_patch["scenario_ids"])
        self.assertIn("maps/UnitMap.asm", state_patch["source_files"])
        self.assertEqual([patch["symbol"] for patch in patches], ["wScriptPos"])
        self.assertTrue(minimized["minimized_evidence_view"])
        self.assertIn("minimized generic state-space evidence view", "\n".join(minimized["warnings"]))

    def test_minimize_executes_generic_state_space_candidates(self) -> None:
        class FakeMemory:
            def __init__(self) -> None:
                self.values: dict[Any, int] = {0xFF70: 1}

            def __getitem__(self, key: Any) -> int:
                return self.values.get(key, 0)

            def __setitem__(self, key: Any, value: int) -> None:
                self.values[key] = value & 0xFF

        class FakePyBoy:
            def __init__(self) -> None:
                self.memory = FakeMemory()

            def load_state(self, fh: Any) -> None:
                fh.read()
                self.memory = FakeMemory()

            def save_state(self, fh: Any) -> None:
                fh.write(b"patched-state")

            def stop(self, save: bool = False) -> None:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(b"rom")
            (root / "base.state").write_bytes(b"base-state")
            state_space = root / "state_space.json"
            state_space.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_state_space",
                        "valid": True,
                        "rom": "test.gbc",
                        "base_save_state": "base.state",
                        "state_space": {
                            "surface": "script_entry",
                            "base_save_state": "base.state",
                            "patches": [
                                {
                                    "symbol": "wScriptBank",
                                    "value": 2,
                                    "value_hex": "02",
                                    "bank": 1,
                                    "address": 0xDA10,
                                    "source_file": "maps/UnitMap.asm",
                                    "scenario_id": "script_entry_1",
                                },
                                {
                                    "symbol": "wScriptPos",
                                    "value": 0x50,
                                    "value_hex": "50",
                                    "bank": 1,
                                    "address": 0xDA11,
                                    "source_file": "maps/UnitMap.asm",
                                    "scenario_id": "script_entry_1",
                                },
                                {
                                    "symbol": "wUnusedDebugByte",
                                    "value": 255,
                                    "value_hex": "ff",
                                    "bank": 1,
                                    "address": 0xDA12,
                                    "source_file": "engine/debug.asm",
                                },
                            ],
                        },
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )
            out_state_report = root / "minimized_state_space.json"

            with patch("tools.debugger.state_space.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                report = build_minimization_plan(
                    reports=("state_space.json",),
                    expectations=(
                        "state-patch=wScriptPos,scenario=script_entry_1,value=0x50,applied=true,verified=true",
                    ),
                    out_state_report="minimized_state_space.json",
                    execute_state_patches=True,
                    root=root,
                )
            minimized = json.loads(out_state_report.read_text(encoding="utf-8"))
            candidate_state_written = (root / minimized["execution"]["out_state"]).exists()

        state_patch = report["state_patch_minimization"]
        patches = minimized["state_space"]["patches"]

        self.assertTrue(report["valid"])
        self.assertTrue(state_patch["preserved"])
        self.assertTrue(state_patch["execute_state_patches"])
        self.assertGreater(state_patch["execution_attempt_count"], 0)
        self.assertEqual(state_patch["executed_candidate_count"], state_patch["execution_attempt_count"])
        self.assertEqual(state_patch["minimized_patch_count"], 1)
        self.assertEqual([patch["symbol"] for patch in patches], ["wScriptPos"])
        self.assertTrue(patches[0]["applied"])
        self.assertTrue(patches[0]["verified"])
        self.assertTrue(minimized["minimized_execution_view"])
        self.assertTrue(candidate_state_written)

    def test_minimize_extracts_content_report_scenarios_with_preconditions(self) -> None:
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
                                "state_preconditions": [
                                    {
                                        "id": "map_warp_position",
                                        "kind": "map_position",
                                        "values": {
                                            "source_file": "maps/UnitMap.asm",
                                            "map_label": "UnitMap_MapEvents",
                                            "x": 1,
                                            "y": 2,
                                            "destination_map": "TARGET_MAP",
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
            out_scenarios = root / "minimized_content.jsonl"

            report = build_minimization_plan(
                reports=("content_scenarios.json",),
                scenario_ids=("content_scenario_1_0000",),
                out_scenarios="minimized_content.jsonl",
                root=root,
            )
            minimized = [
                json.loads(line)
                for line in out_scenarios.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        preconditions = report["precondition_minimization"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["report_scenario_count"], 1)
        self.assertEqual(report["subset_output"]["record_count"], 1)
        self.assertEqual(minimized[0]["state_preconditions"][0]["kind"], "map_position")
        self.assertTrue(preconditions["attempted"])
        self.assertEqual(preconditions["selected_precondition_count"], 1)
        self.assertIn("precondition=map_position,scenario=content_scenario_1_0000", preconditions["expectations"])
        self.assertIn("tools.debugger expect --report content_scenarios.json", commands)
        self.assertIn("tools.debugger slice --source-file maps/UnitMap.asm", commands)
        self.assertIn("tools.debugger setup --report content_scenarios.json --scenario-id content_scenario_1_0000", commands)

    def test_cli_minimize_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scenarios = root / "scenarios.jsonl"
            scenarios.write_text(
                json.dumps({"id": "unit_case", "moves": [{"id": "a"}]}) + "\n",
                encoding="utf-8",
            )
            out = root / "minimize.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "minimize",
                        "--scenario",
                        str(scenarios),
                        "--scenario-id",
                        "unit_case",
                        "--symbol",
                        "BossAI_SelectMove",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_minimization_plan")
        self.assertIn("unit_case", data["selected_scenario_ids"])

    def test_cli_minimize_writes_minimized_content_state_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_state = root / "content_state.json"
            content_state.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0000",
                                "status": "ready",
                                "patches": [
                                    {"symbol": "wMapGroup", "value": 24, "value_hex": "18"},
                                    {"symbol": "wMapNumber", "value": 3, "value_hex": "03"},
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "minimize.json"
            out_state_report = root / "minimized_state.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "minimize",
                        "--report",
                        str(content_state),
                        "--expect",
                        "state-patch=wMapGroup,scenario=content_scenario_1_0000,value=0x18",
                        "--out-state-report",
                        str(out_state_report),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            minimized = json.loads(out_state_report.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertTrue(data["state_patch_minimization"]["preserved"])
        self.assertEqual(data["state_patch_minimization"]["minimized_patch_count"], 1)
        self.assertEqual(minimized["materializations"][0]["patches"][0]["symbol"], "wMapGroup")

    def test_cli_minimize_writes_generic_minimized_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "events": [
                            {"access": "read", "symbol": "wNoise", "address": "D250"},
                            {"access": "write", "symbol": "wCurDamage", "address": "D141"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out = root / "minimize.json"
            out_trace = root / "minimized_trace.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "minimize",
                        "--trace",
                        str(trace),
                        "--expect",
                        "event=memory_write,symbol=wCurDamage",
                        "--out-trace",
                        str(out_trace),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            minimized = json.loads(out_trace.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertTrue(data["evidence_minimization"]["preserved"])
        self.assertEqual(len(minimized["events"]), 1)
        self.assertEqual(minimized["events"][0]["symbol"], "wCurDamage")

    def test_cli_minimize_writes_minimized_watch_report_context(self) -> None:
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
                                "watch": "wCurDamage",
                                "old_hex": "0000",
                                "new_hex": "3400",
                                "pc_label": "BattleCommand_Final",
                                "dynamic_context": {
                                    "context_frame_count": 2,
                                    "prelude": [
                                        {
                                            "kind": "runtime_context_frame",
                                            "event_type": "control_flow",
                                            "frame": 0,
                                            "pc_label": "BattleCommand_Seed",
                                        },
                                        {
                                            "kind": "runtime_context_frame",
                                            "event_type": "control_flow",
                                            "frame": 1,
                                            "pc_label": "BattleCommand_DamageCalc",
                                        },
                                    ],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "minimize.json"
            out_trace = root / "minimized_watch.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "minimize",
                        "--report",
                        str(watch_report),
                        "--expect",
                        "event=watch_change,symbol=wCurDamage",
                        "--expect",
                        "event=control_flow,symbol=BattleCommand_DamageCalc",
                        "--out-trace",
                        str(out_trace),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            minimized = json.loads(out_trace.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertTrue(data["evidence_minimization"]["preserved"])
        self.assertEqual(data["evidence_minimization"]["source_kind"], "report")
        self.assertEqual(data["evidence_minimization"]["context_frame_minimized_count"], 1)
        self.assertEqual(minimized["events"][0]["dynamic_context"]["prelude"][0]["pc_label"], "BattleCommand_DamageCalc")
