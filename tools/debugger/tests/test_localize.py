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
from tools.debugger.taint import build_taint_report


class LocalizationTests(unittest.TestCase):
    def test_localize_scores_symbols_and_builds_phase_plan(self) -> None:
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

            report = build_localization_plan(
                symbols=("wCurDamage",),
                symptom="damage spike",
                symbols_path="test.sym",
                root=root,
            )

        self.assertTrue(report["valid"])
        candidate_ids = [candidate["id"] for candidate in report["candidates"]]
        phase_names = [phase["phase"] for phase in report["phase_steps"]]
        commands = "\n".join(report["commands"])

        self.assertIn("wCurDamage", candidate_ids)
        self.assertIn("observe", phase_names)
        self.assertIn("slice", phase_names)
        self.assertIn("tools.debugger watch", commands)
        self.assertIn("tools.damage_debugger", commands)

    def test_localize_routes_air_balloon_immunity_to_type_matchup_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine" / "battle").mkdir(parents=True)
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "data" / "types").mkdir(parents=True)
            (root / "ram").mkdir()
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "0d:4936 BattleCheckTypeMatchup",
                        "0d:4941 CheckTypeMatchup",
                        "0d:4900 TypeMatchups",
                        "01:d151 wTypeMatchup",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "effect_commands.asm").write_text(
                "\n".join(
                    [
                        "BattleCheckTypeMatchup:",
                        "\tld [wTypeMatchup], a",
                        "\tld hl, TypeMatchups",
                        "\tret",
                        "CheckTypeMatchup:",
                        "\tcall BattleCheckTypeMatchup",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "late_gen_held_items.asm").write_text(
                ".MaybePopAirBalloon:\n\tld hl, BattleText_AirBalloonPopped\n\tret\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "boss_policy_move.asm").write_text(
                "BossAI_ApplyMoveModel:\n\tld a, [wTypeMatchup]\n\tret\n",
                encoding="utf-8",
            )
            (root / "data" / "types" / "type_matchups.asm").write_text(
                "TypeMatchups:\n\tdb GROUND, FLYING, 0\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wTypeMatchup:: ds 1\n",
                encoding="utf-8",
            )

            report = build_localization_plan(
                symptom="Air Balloon Ground immunity",
                symbols_path="test.sym",
                root=root,
            )

        candidate_ids = [candidate["id"] for candidate in report["candidates"]]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("damage_chain", report["triage_match_ids"])
        self.assertNotIn("boss_ai", report["triage_match_ids"])
        self.assertIn("BattleCheckTypeMatchup", candidate_ids)
        self.assertIn("wTypeMatchup", candidate_ids)
        self.assertIn("engine/battle/late_gen_held_items.asm", candidate_ids)
        self.assertNotIn("BossAI_SelectMove", candidate_ids)
        self.assertNotIn("tools.boss_ai_debugger", commands)
        self.assertIn("tools.debugger watch --watch-symbol wTypeMatchup", commands)
        self.assertIn("tools.debugger slice --symbol BattleCheckTypeMatchup", commands)
        self.assertIn("tools.debugger slice --source-file engine/battle/late_gen_held_items.asm", commands)

    def test_localize_uses_embedded_next_step_sources_and_proof_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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

            report = build_localization_plan(reports=("investigate.json",), root=root)

        candidate_ids = {candidate["id"] for candidate in report["candidates"]}
        signal_types = {item["type"] for item in report["signals"]}
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("tools/boss_ai_debugger/rom_switch_materialize.py", candidate_ids)
        self.assertIn("engine/battle/ai/boss_policy_switch.asm", candidate_ids)
        self.assertIn("engine/battle/ai/switch.asm", candidate_ids)
        self.assertIn("next_step_source_ref", signal_types)
        self.assertIn("next_step_evidence_standard", signal_types)
        self.assertIn("next_step_disproof_standard", signal_types)
        self.assertIn("next_step_regression_gate", signal_types)
        self.assertIn("rom-switch-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch", commands)

    def test_localize_uses_watch_report_events_as_strong_signal(self) -> None:
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
                                "old_hex": "00",
                                "new_hex": "10",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_localization_plan(
                reports=("watch.json",),
                symbols_path="missing.sym",
                root=root,
            )

        self.assertFalse(report["valid"])
        self.assertEqual(report["candidates"][0]["id"], "wEnemyAIMoveScores")
        self.assertIn("missing symbol file", report["errors"][0])

    def test_localize_uses_trace_reverse_attribution_as_strong_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine" / "battle").mkdir(parents=True)
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:D142 wBattleMonAttack\n01:4000 BattleCommand_DamageCalc\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\nwBattleMonAttack:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "effect_commands.asm").write_text(
                "BattleCommand_DamageCalc:\n\tld a, [wBattleMonAttack]\n\tld [wCurDamage], a\n\tret\n",
                encoding="utf-8",
            )
            trace_index = root / "trace_index.json"
            trace_index.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_trace_index",
                        "valid": True,
                        "events": [
                            {
                                "event_type": "memory_write",
                                "state_symbol": "wCurDamage",
                                "source_symbol": "BattleCommand_DamageCalc",
                                "source_file": "engine/battle/effect_commands.asm",
                                "before": "0000",
                                "after": "002A",
                            }
                        ],
                        "reverse_attributions": [
                            {
                                "state": "wCurDamage",
                                "title": "wCurDamage memory_write reverse attribution",
                                "source_symbol": "BattleCommand_DamageCalc",
                                "contributors": [
                                    {
                                        "relation": "prior_read",
                                        "state": "wBattleMonAttack",
                                    }
                                ],
                                "related_symbols": ["wCurDamage", "wBattleMonAttack"],
                                "related_files": ["engine/battle/effect_commands.asm"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_localization_plan(
                reports=("trace_index.json",),
                symbols_path="test.sym",
                root=root,
            )

        candidate_ids = {candidate["id"] for candidate in report["candidates"]}
        commands = "\n".join(report["commands"])

        by_id = {candidate["id"]: candidate for candidate in report["candidates"]}

        self.assertTrue(report["valid"])
        self.assertGreater(by_id["wCurDamage"]["score"], by_id["wBattleMonAttack"]["score"])
        self.assertIn("wBattleMonAttack", candidate_ids)
        self.assertIn("tools.debugger slice --symbol wCurDamage", commands)

    def test_localize_uses_failed_expectation_as_strong_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "maps").mkdir()
            (root / "test.sym").write_text("01:D100 wMapGroup\n", encoding="utf-8")
            (root / "ram" / "wram.asm").write_text("wMapGroup:: ds 1\n", encoding="utf-8")
            (root / "maps" / "NewBarkTown.asm").write_text(
                "NewBarkTown_MapEvents:\n\tdef_warp_events\n",
                encoding="utf-8",
            )
            expectation_report = root / "expectation.json"
            expectation_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_expectation_report",
                        "valid": True,
                        "passed": False,
                        "expectations": [
                            {
                                "id": "map_group_observed",
                                "status": "failed",
                                "description": "map group should be observed",
                                "expectation": {
                                    "symbol": "wMapGroup",
                                    "source_file": "maps/NewBarkTown.asm",
                                    "event_type": "memory_write",
                                },
                            }
                        ],
                        "evidence_summary": {
                            "symbols": ["wMapGroup"],
                            "source_files": ["maps/NewBarkTown.asm"],
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_localization_plan(
                reports=("expectation.json",),
                symbols_path="test.sym",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["candidates"][0]["id"], "wMapGroup")
        self.assertIn("maps/NewBarkTown.asm", {candidate["id"] for candidate in report["candidates"]})

    def test_localize_uses_taint_report_contributors_as_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:D142 wBattleMonAttack\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\nwBattleMonAttack:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld a, [wBattleMonAttack]\n\tld [wCurDamage], a\n",
                encoding="utf-8",
            )
            taint = build_taint_report(
                symbols_path="test.sym",
                symbols=("wCurDamage",),
                source_files=("engine/battle.asm",),
                root=root,
            )
            (root / "taint.json").write_text(json.dumps(taint), encoding="utf-8")

            report = build_localization_plan(
                reports=("taint.json",),
                symbols_path="test.sym",
                root=root,
            )

        candidate_ids = {candidate["id"] for candidate in report["candidates"]}

        self.assertTrue(report["valid"])
        self.assertIn("wCurDamage", candidate_ids)
        self.assertIn("wBattleMonAttack", candidate_ids)
        self.assertIn("engine/battle.asm", candidate_ids)

    def test_cli_localize_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            symbols = root / "test.sym"
            symbols.write_text("01:D141 wCurDamage\n", encoding="utf-8")
            (root / "ram" / "wram.asm").write_text("wCurDamage:: ds 2\n", encoding="utf-8")
            out = root / "localize.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "localize",
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "wCurDamage",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_localization_plan")
        self.assertTrue(data["candidates"])
