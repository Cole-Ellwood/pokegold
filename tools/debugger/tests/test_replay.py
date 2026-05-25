from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.localize import build_localization_plan
from tools.debugger.next_steps import NEXT_STEP_ROWS, build_next_step
from tools.debugger.replay import build_replay_plan


class ReplayTests(unittest.TestCase):
    def test_replay_plan_fingerprints_inputs_and_builds_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine" / "battle").mkdir(parents=True)
            rom = root / "test.gbc"
            rom.write_bytes(bytes(0x8000))
            symbols = root / "test.sym"
            symbols.write_text(
                "00:0000 NULL\n01:D141 wCurDamage\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            save_state = root / "state.state"
            save_state.write_bytes(b"opaque-state")
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "full_symbol": "BattleCommand_Test",
                        "source_file": "engine/battle/effect_commands.asm",
                    }
                ),
                encoding="utf-8",
            )
            scenario = root / "scenario.jsonl"
            scenario.write_text(
                json.dumps({"id": "case_one", "family": "unit"}) + "\n",
                encoding="utf-8",
            )
            changed = root / "engine" / "battle" / "effect_commands.asm"
            changed.write_text("BattleCommand_Test:\n\tret\n", encoding="utf-8")

            report = build_replay_plan(
                rom_path="test.gbc",
                symbols_path="test.sym",
                save_state="state.state",
                traces=("trace.json",),
                scenarios=("scenario.jsonl",),
                scenario_ids=("manual_case",),
                watch_symbols=("wCurDamage",),
                changed_files=("engine/battle/effect_commands.asm",),
                root=root,
            )

        commands = "\n".join(report["commands"])
        phases = {phase["phase"] for phase in report["phase_steps"]}

        self.assertTrue(report["valid"])
        self.assertEqual(report["artifact_manifest"]["artifact_count"], 6)
        self.assertIn("wCurDamage", report["replay_targets"]["watch_symbols"])
        self.assertIn("case_one", report["replay_targets"]["scenario_ids"])
        self.assertIn("manual_case", report["replay_targets"]["scenario_ids"])
        self.assertIn("ingest", phases)
        self.assertIn("setup", phases)
        self.assertIn("reproduce", phases)
        self.assertIn("prove", phases)
        self.assertIn("tools.debugger setup", commands)
        self.assertIn("tools.debugger watch", commands)
        self.assertIn("tools.debugger trace-instructions", commands)
        self.assertIn("tools.debugger coverage", commands)
        self.assertIn("tools.debugger minimize", commands)
        self.assertIn("--scenario-id manual_case", commands)
        self.assertIn("--trace trace.json", commands)
        self.assertIn("--out-trace .local\\tmp\\debugger_replay_minimized_trace.json", commands)

    def test_replay_plan_derives_watch_targets_from_reports(self) -> None:
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
                                "watch": "wEnemyAIMoveScores",
                                "pc_label": "BossAI_SelectMove",
                                "pc_bank_address": "03:4123",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_replay_plan(reports=("watch.json",), root=root)

        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("wEnemyAIMoveScores", report["replay_targets"]["watch_symbols"])
        self.assertIn("BossAI_SelectMove", report["replay_targets"]["symbols"])
        self.assertIn("tools.debugger localize --report watch.json", commands)
        self.assertIn("tools.debugger impact --report watch.json", commands)
        self.assertIn("tools.debugger trace-instructions", commands)
        self.assertIn("--report watch.json", commands)

    def test_replay_and_localize_consume_content_rom_mirrors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gfx").mkdir()
            (root / "gfx" / "footprints.asm").write_text("Footprints:\n\tret\n", encoding="utf-8")
            (root / "pokegold.sym").write_text("3E:5302 Footprints\n", encoding="utf-8")
            content_report = root / "content.json"
            content_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_mirror",
                        "rom_mirrors": [
                            {
                                "type": "incbin_table_rom_bytes",
                                "status": "passed",
                                "title": "Footprints ROM bytes match",
                                "source_file": "gfx/footprints.asm",
                                "related_files": ["gfx/footprints.asm", "gfx/footprints/bulbasaur.1bpp"],
                                "related_symbols": ["Footprints"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            replay = build_replay_plan(reports=("content.json",), root=root)
            localized = build_localization_plan(reports=("content.json",), root=root)

        replay_commands = "\n".join(replay["commands"])
        localized_commands = "\n".join(localized["commands"])
        candidate_ids = {candidate["id"] for candidate in localized["candidates"]}

        self.assertTrue(replay["valid"])
        self.assertIn("Footprints", replay["replay_targets"]["symbols"])
        self.assertIn("gfx/footprints.asm", replay["replay_targets"]["source_files"])
        self.assertIn("--symbol Footprints", replay_commands)
        self.assertTrue(localized["valid"])
        self.assertIn("Footprints", candidate_ids)
        self.assertIn("gfx/footprints.asm", candidate_ids)
        self.assertIn("provenance --symbol Footprints", localized_commands)

    def test_replay_plan_uses_existing_discovered_save_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text("01:D141 wCurDamage\n", encoding="utf-8")
            (root / "case.state").write_bytes(b"state")
            (root / "scenarios.jsonl").write_text(
                json.dumps({"id": "case_one", "state": "case.state"}) + "\n",
                encoding="utf-8",
            )

            report = build_replay_plan(
                rom_path="test.gbc",
                symbols_path="test.sym",
                scenarios=("scenarios.jsonl",),
                scenario_ids=("case_one",),
                watch_symbols=("wCurDamage",),
                root=root,
            )

        commands = "\n".join(report["commands"])
        selected = report["save_state_discovery"]["selected"]

        self.assertTrue(report["valid"])
        self.assertEqual(report["save_state"], "")
        self.assertEqual(report["effective_save_state"], "case.state")
        self.assertEqual(selected["scenario_id"], "case_one")
        self.assertTrue(selected["exists"])
        self.assertIn("save_state", {artifact["kind"] for artifact in report["artifact_manifest"]["artifacts"]})
        self.assertIn("--save-state case.state", commands)
        self.assertIn("case.state", report["setup_plan"]["effective_save_state"])

    def test_replay_plan_consumes_content_state_materialization_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pokegold.gbc").write_bytes(bytes(0x8000))
            (root / "pokegold.sym").write_text(
                "01:DA00 wMapGroup\n01:DA01 wMapNumber\n01:DA02 wYCoord\n01:DA03 wXCoord\n",
                encoding="utf-8",
            )
            (root / "patched.state").write_bytes(b"patched-state")
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

            report = build_replay_plan(reports=("content_state.json",), root=root)

        commands = "\n".join(report["commands"])
        selected = report["save_state_discovery"]["selected"]

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "patched.state")
        self.assertEqual(selected["key"], "out_state")
        self.assertTrue(selected["exists"])
        self.assertIn("wMapGroup", report["replay_targets"]["watch_symbols"])
        self.assertIn("content_scenario_1_0000", report["replay_targets"]["scenario_ids"])
        self.assertIn("maps/UnitMap.asm", report["replay_targets"]["source_files"])
        self.assertIn("--save-state patched.state", commands)
        self.assertIn("--scenario-id content_scenario_1_0000", commands)

    def test_replay_plan_consumes_state_space_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pokegold.gbc").write_bytes(bytes(0x8000))
            (root / "pokegold.sym").write_text(
                "01:4000 ScriptEvents\n01:DA10 wScriptBank\n01:DA11 wScriptPos\n",
                encoding="utf-8",
            )
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
                        "watch_symbols": ["wScriptPos"],
                        "state_space": {
                            "scenario_ids": ["script_entry_1"],
                            "source_files": ["maps/UnitMap.asm"],
                            "out_state": "patched.state",
                            "patches": [
                                {
                                    "symbol": "wScriptBank",
                                    "base_symbol": "wScriptBank",
                                    "value": 2,
                                    "value_hex": "02",
                                    "scenario_id": "script_entry_1",
                                    "source_file": "maps/UnitMap.asm",
                                },
                                {
                                    "symbol": "wScriptPos",
                                    "base_symbol": "wScriptPos",
                                    "value": 80,
                                    "value_hex": "50",
                                    "scenario_id": "script_entry_1",
                                    "source_file": "maps/UnitMap.asm",
                                },
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

            report = build_replay_plan(reports=("state_space.json",), root=root)

        commands = "\n".join(report["commands"])
        selected = report["save_state_discovery"]["selected"]

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "patched.state")
        self.assertTrue(selected["exists"])
        self.assertIn("wScriptBank", report["replay_targets"]["watch_symbols"])
        self.assertIn("wScriptPos", report["replay_targets"]["watch_symbols"])
        self.assertIn("script_entry_1", report["replay_targets"]["scenario_ids"])
        self.assertIn("maps/UnitMap.asm", report["replay_targets"]["source_files"])
        self.assertIn("--save-state patched.state", commands)
        self.assertIn("--scenario-id script_entry_1", commands)

    def test_replay_plan_does_not_use_missing_discovered_save_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text("01:D141 wCurDamage\n", encoding="utf-8")
            (root / "scenarios.jsonl").write_text(
                json.dumps({"id": "case_one", "state": "missing.state"}) + "\n",
                encoding="utf-8",
            )

            report = build_replay_plan(
                rom_path="test.gbc",
                symbols_path="test.sym",
                scenarios=("scenarios.jsonl",),
                scenario_ids=("case_one",),
                watch_symbols=("wCurDamage",),
                root=root,
            )

        commands = "\n".join(report["commands"])
        candidates = report["save_state_discovery"]["candidates"]

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "")
        self.assertEqual(report["save_state_discovery"]["selected"], {})
        self.assertEqual(candidates[0]["path"], "missing.state")
        self.assertFalse(candidates[0]["exists"])
        self.assertNotIn("--save-state missing.state", commands)

    def test_replay_plan_does_not_treat_query_flags_as_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_index = root / "trace_index.json"
            trace_index.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_trace_index",
                        "valid": True,
                        "query": {
                            "active": True,
                            "symbols": [],
                            "source_files": ["maps/NewBarkTown.asm"],
                        },
                        "events": [],
                    }
                ),
                encoding="utf-8",
            )

            report = build_replay_plan(reports=("trace_index.json",), root=root)

        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertNotIn("True", report["replay_targets"]["symbols"])
        self.assertNotIn("--symbol True", commands)
        self.assertIn("maps/NewBarkTown.asm", report["replay_targets"]["source_files"])

    def test_replay_plan_uses_embedded_next_step_instead_of_impact_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            investigation = root / "investigate.json"
            investigation.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_investigation_run",
                        "valid": True,
                        "symptom": "boss selected wrong switch",
                        "symptom_only_next_step": build_next_step(symptom="boss selected wrong switch"),
                        "top_impact": [
                            {
                                "type": "fuzz_campaign",
                                "title": "Fuzz campaign: fuzz_boss_ai_generated_policy",
                                "impact_score": 100,
                                "related_symbols": [
                                    "Broad",
                                    "Fuzz",
                                    "Python",
                                    "ROM-materialized",
                                    "boss_ai",
                                    "fuzz_boss_ai_generated_policy",
                                    "proof_level",
                                ],
                                "related_files": ["engine/battle/ai/boss_policy_move.asm"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_replay_plan(reports=("investigate.json",), root=root)

        commands = "\n".join(report["commands"])
        targets = report["replay_targets"]
        self.assertTrue(report["valid"])
        self.assertIn("BossAI_SwitchOrTryItem", targets["symbols"])
        self.assertIn("wEnemySwitchMonIndex", targets["watch_symbols"])
        self.assertIn("wEnemySwitchMonParam", targets["watch_symbols"])
        self.assertIn("wEnemyAIMoveScores", targets["watch_symbols"])
        self.assertIn("engine/battle/ai/boss_policy_switch.asm", targets["source_files"])
        self.assertIn("--symbol BossAI_SwitchOrTryItem", commands)
        self.assertIn("--watch-symbol wEnemySwitchMonIndex", commands)
        self.assertNotIn("Broad", targets["symbols"])
        self.assertNotIn("Fuzz", targets["symbols"])
        self.assertNotIn("Python", targets["symbols"])
        self.assertNotIn("ROM-materialized", targets["symbols"])
        self.assertNotIn("--symbol Broad", commands)

    def test_cli_replay_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "replay.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "replay",
                        "--symbol",
                        "wCurDamage",
                        "--symptom",
                        "damage spike",
                        "--scenario-id",
                        "content_scenario_1_0000",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_replay_plan")
        self.assertIn("wCurDamage", data["replay_targets"]["watch_symbols"])
        self.assertIn("content_scenario_1_0000", data["replay_targets"]["scenario_ids"])
