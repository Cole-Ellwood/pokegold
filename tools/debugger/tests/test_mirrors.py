from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.mirrors import build_compare_plan
from tools.debugger.next_steps import NEXT_STEP_ROWS, build_next_step


class ComparePlanTests(unittest.TestCase):
    def test_compare_plan_maps_damage_symbol_to_oracle(self) -> None:
        report = build_compare_plan(symbols=("wCurDamage",))
        commands = "\n".join(report["commands"])
        proof = "\n".join(report["materialization_commands"])

        self.assertIn("damage_oracle", {match["id"] for match in report["matches"]})
        self.assertIn("tools.damage_debugger.oracle", commands)
        self.assertIn("tools.damage_debugger.replay", proof)

    def test_compare_plan_maps_boss_ai_source_to_materialization(self) -> None:
        report = build_compare_plan(
            changed_files=("engine/battle/ai/boss_policy_move.asm",),
        )
        proof = "\n".join(report["materialization_commands"])

        self.assertIn(
            "boss_ai_policy_mirror",
            {match["id"] for match in report["matches"]},
        )
        self.assertIn("rom-score-materialize", proof)

    def test_compare_plan_uses_embedded_next_step_as_mirror_route(self) -> None:
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
                    }
                ),
                encoding="utf-8",
            )

            report = build_compare_plan(reports=("investigate.json",), root=root)

        commands = "\n".join(report["commands"])
        proof = "\n".join(report["materialization_commands"])
        evidence = "\n".join(item for match in report["matches"] for item in match["evidence"])

        self.assertTrue(report["valid"])
        self.assertEqual({match["id"] for match in report["matches"]}, {"boss_ai_policy_mirror"})
        self.assertIn("next_step", report["matches"][0]["matched_by"])
        self.assertIn("rom-switch-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch", commands)
        self.assertIn("rom-switch-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch", proof)
        self.assertIn("run-suite --profile changed-ai", proof)
        self.assertIn("source_ref=engine/battle/ai/boss_policy_switch.asm", evidence)
        self.assertIn("evidence standard: A scenario JSONL matching the disputed switch case passes rom-switch-materialize", evidence)
        self.assertNotIn("damage_debugger", commands)
        self.assertNotIn("uncovered_surface", {match["id"] for match in report["matches"]})

    def test_compare_plan_routes_content_to_static_expectations(self) -> None:
        report = build_compare_plan(changed_files=("maps/NewBarkTown.asm",))
        commands = "\n".join(report["commands"])
        proof = "\n".join(report["materialization_commands"])

        self.assertIn("static_invariant_mirror", {match["id"] for match in report["matches"]})
        self.assertIn("tools.debugger content-mirror", commands)
        self.assertIn("tools.debugger expect --source-file", commands)
        self.assertIn("content-mirror --source-file", proof)
        self.assertIn("contains=<expected_text>", proof)

    def test_compare_plan_consumes_content_state_behavioral_mirror(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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
                                    },
                                    {
                                        "symbol": "wMapNumber",
                                        "value": 4,
                                        "value_hex": "04",
                                        "bank_address": "01:DA01",
                                    },
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

            report = build_compare_plan(reports=("content_state.json",), root=root)

        commands = "\n".join(report["commands"])
        proof = "\n".join(report["materialization_commands"])
        match = report["matches"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(match["id"], "content_state_behavioral_mirror")
        self.assertEqual(match["gaps"], [])
        self.assertIn("content_state.json", report["input_reports"])
        self.assertIn("state-patch=wMapGroup,scenario=content_scenario_1_0000,value=0x18", commands)
        self.assertIn("replay --report content_state.json --scenario-id content_scenario_1_0000 --execute-watch", proof)
        self.assertIn("--save-state patched.state --execute", proof)

    def test_cli_compare_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "compare.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "compare",
                        "--symbol",
                        "BossAI_SelectMove",
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_compare_plan")
            self.assertTrue(data["matches"])
