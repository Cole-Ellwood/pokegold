from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.content_scenarios import build_content_scenario_report
from tools.debugger.next_steps import NEXT_STEP_ROWS, build_next_step
from tools.debugger.setup_plan import build_setup_plan


class SetupPlanTests(unittest.TestCase):
    def test_setup_plan_builds_damage_trigger_commands(self) -> None:
        report = build_setup_plan(
            symbols=("BattleCommand_DamageCalc",),
            watch_symbols=("wCurDamage",),
            out_scenarios=".local\\tmp\\damage_setup.jsonl",
        )

        commands = "\n".join(report["commands"])
        coverage = report["trigger_coverage"]
        target = coverage["targets"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(report["surfaces"], ["damage"])
        self.assertTrue(report["state_requirements"]["requires_positioned_state"])
        self.assertEqual(coverage["planned_target_count"], 1)
        self.assertEqual(target["status"], "planned")
        self.assertEqual(target["state_status"], "synthesizable")
        self.assertIn("state:synthesizable", target["blockers"])
        self.assertEqual(report["targets"][0]["state_synthesis_recipes"][0]["id"], "damage_snapshot_ring_runtime")
        self.assertTrue(report["targets"][0]["state_synthesis_recipes"][0]["runnable"])
        self.assertIn("no save state was supplied", "\n".join(report["warnings"]))
        self.assertIn("tools.debugger generate --family damage", commands)
        self.assertIn("tools.damage_debugger.replay", commands)
        self.assertIn("trace-instructions", commands)
        self.assertIn("--require-hit", commands)
        self.assertIn("--watch-symbol wCurDamage", commands)

    def test_setup_plan_builds_content_trigger_commands(self) -> None:
        report = build_setup_plan(
            changed_files=("maps/UnitMap.asm",),
            out_scenarios=".local\\tmp\\content_setup.jsonl",
        )

        commands = "\n".join(report["commands"])
        coverage = report["trigger_coverage"]
        target = coverage["targets"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(report["surfaces"], ["content_static"])
        self.assertFalse(report["state_requirements"]["requires_positioned_state"])
        self.assertEqual(coverage["planned_target_count"], 1)
        self.assertEqual(target["state_status"], "not-required")
        self.assertEqual(target["state_recipe_status"]["status"], "ready")
        self.assertIn("trigger:blocked", target["blockers"])
        self.assertIn("content-mirror --source-file maps/UnitMap.asm", commands)
        self.assertIn("content-scenarios --source-file maps/UnitMap.asm", commands)
        self.assertIn("--scenario .local\\tmp\\content_setup.jsonl", commands)
        self.assertIn("--scenario-id <id>", commands)
        self.assertIn("--symbol ReadMapEvents", commands)
        self.assertIn("--symbol CheckFacingBGEvent", commands)
        self.assertIn("--watch-symbol wMapGroup", commands)

    def test_setup_plan_uses_content_scenario_report_preconditions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "UnitMap_MapEvents:",
                        "\tdef_bg_events",
                        "\tbg_event 4, 5, BGEVENT_READ, UnitMapSign",
                        "UnitMapSign:",
                        "\tjumptext UnitMapText",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            scenario_report = build_content_scenario_report(
                source_files=("maps/UnitMap.asm",),
                out_scenarios="content.jsonl",
                root=root,
            )
            (root / "content.json").write_text(json.dumps(scenario_report), encoding="utf-8")

            report = build_setup_plan(
                reports=("content.json",),
                out_scenarios="content.jsonl",
                root=root,
            )

        commands = "\n".join(report["commands"])
        recipes = report["targets"][0]["state_synthesis_recipes"]
        precondition_recipe = next(item for item in recipes if item["id"] == "content_runtime_preconditions")
        precondition = precondition_recipe["preconditions"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(report["surfaces"], ["content_static"])
        self.assertTrue(report["state_requirements"]["requires_positioned_state"])
        self.assertIn("content_scenario_1_0000", report["state_requirements"]["content_scenario_ids"])
        self.assertIn("content_scenario_1_0001", report["state_requirements"]["content_scenario_ids"])
        self.assertEqual(report["trigger_coverage"]["targets"][0]["state_status"], "partially-synthesizable")
        self.assertIn("state:partially-synthesizable", report["trigger_coverage"]["targets"][0]["blockers"])
        self.assertIn("--scenario-id content_scenario_1_0000", commands)
        self.assertNotIn("--scenario-id <id>", commands)
        self.assertIn("--symbol CheckFacingBGEvent", commands)
        self.assertIn("--symbol UnitMapSign", commands)
        self.assertIn("--watch-symbol wMapGroup", commands)
        self.assertIn("tools.debugger expect --report content.json", commands)
        self.assertIn("precondition=map_position,scenario=content_scenario_1_0000", commands)
        self.assertIn("tools.debugger content-state", commands)
        self.assertIn("--base-save-state <base-state>", commands)
        self.assertNotIn("contains=<expected_text>", commands)
        self.assertEqual(precondition["kind"], "map_position")
        self.assertEqual(precondition["scenario_id"], "content_scenario_1_0000")
        self.assertEqual(precondition["values"]["script"], "UnitMapSign")
        self.assertIn("wMapGroup", precondition["watch_symbols"])

    def test_setup_content_preconditions_are_covered_with_discovered_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / ".local" / "tmp").mkdir(parents=True)
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "UnitMap_MapEvents:",
                        "\tdef_bg_events",
                        "\tbg_event 4, 5, BGEVENT_READ, UnitMapSign",
                        "UnitMapSign:",
                        "\tjumptext UnitMapText",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "case.state").write_bytes(b"state")
            scenario = {
                "id": "content_scenario_1_0000",
                "kind": "unified_debugger_content_scenario",
                "scenario_type": "map_bg_event",
                "source_file": "maps/UnitMap.asm",
                "state": "case.state",
                "state_preconditions": [
                    {
                        "id": "map_bg_event_position",
                        "kind": "map_position",
                        "values": {"script": "UnitMapSign", "source_file": "maps/UnitMap.asm"},
                        "watch_symbols": ["wMapGroup", "wMapNumber", "wXCoord", "wYCoord"],
                    }
                ],
                "runtime_targets": {
                    "trace_symbols": ["CheckFacingBGEvent"],
                    "script_symbols": ["UnitMapSign"],
                    "watch_symbols": ["wMapGroup"],
                },
            }
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [scenario],
                    }
                ),
                encoding="utf-8",
            )
            (root / ".local" / "tmp" / "content_setup.jsonl").write_text(
                json.dumps(scenario) + "\n",
                encoding="utf-8",
            )

            report = build_setup_plan(
                reports=("content.json",),
                out_scenarios=".local\\tmp\\content_setup.jsonl",
                root=root,
            )

        target = report["trigger_coverage"]["targets"][0]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "case.state")
        self.assertTrue(report["state_requirements"]["requires_positioned_state"])
        self.assertTrue(report["state_requirements"]["save_state_discovered"])
        self.assertEqual(target["state_status"], "discovered")
        self.assertEqual(target["status"], "covered")
        self.assertEqual(target["blockers"], [])
        self.assertIn("--save-state case.state", commands)
        self.assertIn("tools.debugger content-state", commands)
        self.assertIn("--base-save-state case.state", commands)
        self.assertIn("--execute", commands)
        self.assertIn("tools.debugger expect --report content.json", commands)

    def test_setup_trigger_coverage_is_covered_with_supplied_state(self) -> None:
        report = build_setup_plan(
                save_state="state.state",
            symbols=("BattleCommand_DamageCalc",),
            watch_symbols=("wCurDamage",),
        )

        coverage = report["trigger_coverage"]
        target = coverage["targets"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(coverage["covered_target_count"], 1)
        self.assertEqual(coverage["coverage_ratio"], 1.0)
        self.assertEqual(target["status"], "covered")
        self.assertEqual(target["state_status"], "supplied")
        self.assertEqual(target["blockers"], [])

    def test_setup_discovers_save_state_from_selected_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "case.state").write_bytes(b"state")
            (root / "other.state").write_bytes(b"other")
            (root / "scenarios.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"id": "other_case", "state": "other.state"}),
                        json.dumps({"capture_id": "case_one", "state": "case.state"}),
                    ]
                ),
                encoding="utf-8",
            )

            report = build_setup_plan(
                scenarios=("scenarios.jsonl",),
                scenario_ids=("case_one",),
                symbols=("BattleCommand_DamageCalc",),
                watch_symbols=("wCurDamage",),
                root=root,
            )

        commands = "\n".join(report["commands"])
        coverage = report["trigger_coverage"]
        target = coverage["targets"][0]
        selected = report["save_state_discovery"]["selected"]

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "case.state")
        self.assertTrue(report["state_requirements"]["save_state_discovered"])
        self.assertEqual(report["targets"][0]["state_synthesis_recipes"][0]["id"], "damage_snapshot_ring_runtime")
        self.assertEqual(selected["scenario_id"], "case_one")
        self.assertEqual(selected["key"], "state")
        self.assertEqual(target["state_status"], "discovered")
        self.assertEqual(target["status"], "covered")
        self.assertIn("--save-state case.state", commands)
        self.assertNotIn("no save state was supplied", "\n".join(report["warnings"]))

    def test_setup_boss_ai_recipe_targets_requested_route(self) -> None:
        report = build_setup_plan(
            scenario_ids=("falkner",),
            symbols=("BossAI_SelectMove",),
            watch_symbols=("wEnemyAIMoveScores",),
        )

        recipes = report["targets"][0]["state_synthesis_recipes"]
        commands = "\n".join(
            command["command"]
            for recipe in recipes
            for command in recipe["commands"]
        )

        self.assertEqual(report["surfaces"], ["boss_ai"])
        self.assertIn("boss_ai_route_state_factory", {recipe["id"] for recipe in recipes})
        self.assertIn("--boss falkner", commands)
        self.assertIn("rom-score-materialize", commands)

    def test_setup_plan_uses_embedded_next_step_instead_of_nested_report_surfaces(self) -> None:
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
                        "reports": [
                            {"id": "09_fuzz", "kind": "unified_debugger_fuzz_plan", "surface": "ROM banking / ABI"},
                            {"id": "06_explain", "kind": "unified_debugger_causal_explanation", "surface": "Battle damage"},
                        ],
                        "top_impact": [
                            {
                                "type": "fuzz_campaign",
                                "title": "Fuzz campaign: fuzz_banking_abi_static_watch",
                                "severity": 55,
                                "confidence": 0.62,
                                "evidence": [],
                                "next_actions": [],
                                "impact_score": 100,
                                "surface_id": "banking_abi",
                            },
                            {
                                "type": "causal_path",
                                "title": "Causal path: Battle damage",
                                "severity": 50,
                                "confidence": 0.62,
                                "evidence": [],
                                "next_actions": [],
                                "impact_score": 90,
                                "surface_id": "battle_damage",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_setup_plan(reports=("investigate.json",), root=root)

        commands = "\n".join(report["commands"])
        self.assertTrue(report["valid"])
        self.assertEqual(report["surfaces"], ["boss_ai"])
        self.assertEqual(report["target_count"], 1)
        self.assertIn("BossAI_TrySwitch", report["effective_symbols"])
        self.assertIn("wEnemySwitchMonIndex", report["effective_watch_symbols"])
        self.assertIn("engine/battle/ai/boss_policy_switch.asm", report["effective_changed_files"])
        self.assertIn("--symbol BossAI_TrySwitch", commands)
        self.assertIn("--watch-symbol wEnemySwitchMonIndex", commands)
        self.assertNotIn("--family damage", commands)
        self.assertNotIn("--family banking_abi", commands)
        self.assertNotIn("hROMBank", commands)

    def test_cli_setup_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "setup.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "setup",
                        "--changed-file",
                        "maps/UnitMap.asm",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_setup_plan")
        self.assertEqual(data["surfaces"], ["content_static"])
