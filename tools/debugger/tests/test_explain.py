from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.content_scenarios import build_content_scenario_report
from tools.debugger.explain import build_explanation_report
from tools.debugger.next_steps import NEXT_STEP_ROWS, build_next_step


class ExplanationTests(unittest.TestCase):
    def test_explain_uses_embedded_next_step_as_causal_proof_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools" / "boss_ai_debugger").mkdir(parents=True)
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "tools" / "boss_ai_debugger" / "rom_switch_materialize.py").write_text(
                "def main():\n    return 0\n",
                encoding="utf-8",
            )
            (root / "tools" / "boss_ai_debugger" / "README.md").write_text(
                "# Boss AI debugger\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "boss_policy_switch.asm").write_text(
                "BossAI_SwitchOrTryItem:\n\tret\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "switch.asm").write_text(
                "AI_SwitchOrTryItem:\n\tret\n",
                encoding="utf-8",
            )
            (root / "pokegold.sym").write_text(
                "01:4000 BossAI_SwitchOrTryItem\n01:4010 AI_SwitchOrTryItem\n",
                encoding="utf-8",
            )
            next_step = build_next_step(symptom="boss selected wrong switch")
            for source_ref in next_step["recommendation"]["source_refs"]:
                source_path = root / source_ref
                source_path.parent.mkdir(parents=True, exist_ok=True)
                if source_path.exists():
                    continue
                source_path.write_text("# source ref placeholder\n", encoding="utf-8")

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
                        "symptom_only_next_step": next_step,
                    }
                ),
                encoding="utf-8",
            )

            report = build_explanation_report(reports=("investigate.json",), root=root)

        path = report["paths"][0]
        roles = {
            node["role"]
            for causal_path in report["paths"]
            for node in causal_path.get("nodes", [])
        }
        labels = {
            node["label"]
            for causal_path in report["paths"]
            for node in causal_path.get("nodes", [])
        }
        evidence = "\n".join(path["evidence"])
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(path["id"], "next_step_1")
        self.assertIn("Next proof path: Boss selected the wrong switch", path["title"])
        self.assertIn("tools/boss_ai_debugger/rom_switch_materialize.py", path["related_files"])
        self.assertIn("first_command", roles)
        self.assertIn("source_ref", roles)
        self.assertIn("evidence_standard", roles)
        self.assertIn("disproof_standard", roles)
        self.assertIn("regression_gate", roles)
        self.assertIn("tools/boss_ai_debugger/rom_switch_materialize.py", labels)
        self.assertIn("evidence standard: A scenario JSONL matching the disputed switch case passes rom-switch-materialize", evidence)
        self.assertIn("disproof standard: If a matching scenario JSONL passes rom-switch-materialize with the expected switch result", evidence)
        self.assertIn("rom-switch-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch", commands)

    def test_explain_links_watch_event_to_static_writer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text(
                "01:D141 wCurDamage\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld [wCurDamage], a\n\tret\n",
                encoding="utf-8",
            )
            watch_report = root / "watch.json"
            watch_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "events": [
                            {
                                "frame": 7,
                                "watch": "wCurDamage",
                                "pc_label": "BattleCommand_Test",
                                "pc_bank_address": "01:4000",
                                "old_hex": "0000",
                                "new_hex": "002A",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_explanation_report(
                reports=("watch.json",),
                symbols_path="test.sym",
                symptom="damage changed unexpectedly",
                root=root,
            )

        first_path = report["paths"][0]
        relations = {edge["relation"] for edge in first_path["edges"]}
        labels = {node["label"] for node in first_path["nodes"]}

        self.assertTrue(report["valid"])
        self.assertEqual(report["dynamic_event_count"], 1)
        self.assertGreaterEqual(first_path["confidence"], 0.9)
        self.assertIn("write", relations)
        self.assertIn("wCurDamage", labels)
        self.assertIn("BattleCommand_Test", labels)
        self.assertIn("BattleCommand_Test", report["mermaid"])

    def test_explain_consumes_trace_index_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text("wCurDamage:: ds 2\n", encoding="utf-8")
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld [wCurDamage], a\n\tret\n",
                encoding="utf-8",
            )
            trace_index = root / "trace_index.json"
            trace_index.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_trace_index",
                        "events": [
                            {
                                "event_type": "watch_change",
                                "state_symbol": "wCurDamage",
                                "source_symbol": "BattleCommand_Test",
                                "pc_symbol": "BattleCommand_Test",
                                "pc_bank_address": "01:4000",
                                "before": "0000",
                                "after": "002A",
                                "source_file": "engine/battle.asm",
                                "confidence": 0.9,
                            }
                        ],
                        "causal_paths": [],
                    }
                ),
                encoding="utf-8",
            )

            report = build_explanation_report(
                reports=("trace_index.json",),
                symbols_path="test.sym",
                root=root,
            )

        labels = {
            node["label"]
            for path in report["paths"]
            for node in path.get("nodes", [])
        }

        self.assertTrue(report["valid"])
        self.assertGreaterEqual(report["dynamic_event_count"], 1)
        self.assertIn("wCurDamage", labels)
        self.assertIn("BattleCommand_Test", labels)

    def test_cli_explain_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            symbols = root / "test.sym"
            symbols.write_text("01:D141 wCurDamage\n", encoding="utf-8")
            (root / "ram" / "wram.asm").write_text("wCurDamage:: ds 2\n", encoding="utf-8")
            out = root / "explain.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "explain",
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "wCurDamage",
                        "--symptom",
                        "damage spike",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_causal_explanation")
        self.assertGreaterEqual(data["path_count"], 1)

    def test_explain_builds_content_scenario_runtime_causal_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "home").mkdir()
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
            (root / "home" / "map.asm").write_text(
                "\n".join(
                    [
                        "CheckFacingBGEvent:",
                        "\tcall CheckBGEventFlag",
                        "\tret",
                        "CheckBGEventFlag:",
                        "\tret",
                        "CallScript:",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "01:4000 UnitMap_MapEvents",
                        "01:4010 UnitMapSign",
                        "00:5000 CheckFacingBGEvent",
                        "00:5010 CheckBGEventFlag",
                        "00:5020 CallScript",
                        "01:D000 wMapGroup",
                        "01:D001 wMapNumber",
                        "01:D002 wXCoord",
                        "01:D003 wYCoord",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            scenario_report = build_content_scenario_report(
                source_files=("maps/UnitMap.asm",),
                out_scenarios="content_scenarios.jsonl",
                root=root,
            )
            (root / "content_scenarios.json").write_text(json.dumps(scenario_report), encoding="utf-8")

            report = build_explanation_report(reports=("content_scenarios.json",), root=root)

        labels = {
            node["label"]
            for path in report["paths"]
            for node in path.get("nodes", [])
        }
        roles = {
            node["role"]
            for path in report["paths"]
            for node in path.get("nodes", [])
        }
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertGreaterEqual(report["content_scenario_count"], 1)
        self.assertIn("UnitMapSign", labels)
        self.assertIn("CheckFacingBGEvent", labels)
        self.assertIn("wMapGroup", labels)
        self.assertIn("script_label", roles)
        self.assertIn("trace_helper", roles)
        self.assertIn("watch_symbol", roles)
        self.assertIn("tools.debugger replay --report content_scenarios.json", commands)
        self.assertIn("tools.debugger provenance --symbol UnitMapSign", commands)
