from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.explain import build_explanation_report
from tools.debugger.trace_index import build_trace_index_report


class TraceIndexTests(unittest.TestCase):
    def test_trace_index_extracts_watch_and_score_delta_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n0E:483E BossAI_ApplyMoveModel\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text("wCurDamage:: ds 2\n", encoding="utf-8")
            (root / "engine" / "battle" / "ai" / "boss_policy_move.asm").write_text(
                "BossAI_ApplyMoveModel:\n\tret\n",
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
                                    "rule_id": "move.apply_move_model",
                                },
                            },
                            {
                                "watch": "wCurDamage",
                                "old_hex": "0000",
                                "new_hex": "002A",
                                "pc_label": "BossAI_ApplyMoveModel",
                                "pc_bank_address": "0E:483E",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = build_trace_index_report(
                traces=("trace.json",),
                addresses=("D0D3",),
                watch_symbols=("wCurDamage",),
                symbols_path="test.sym",
                root=root,
            )

        event_types = {event["event_type"] for event in report["events"]}
        indexed_addresses = {item["address"] for item in report["address_index"]}
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertIn("score_delta", event_types)
        self.assertIn("watch_change", event_types)
        self.assertIn("D0D3", indexed_addresses)
        self.assertGreaterEqual(report["path_count"], 1)
        self.assertIn("tools.debugger explain", commands)

    def test_trace_index_consumes_watch_dynamic_context_frames(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "00:D141 wCurDamage\n00:4000 BattleCommand_Test\n",
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
                                "watch": "wCurDamage",
                                "old_hex": "0000",
                                "new_hex": "3400",
                                "pc_label": "BattleCommand_Test+0x3",
                                "pc_bank_address": "00:4003",
                                "dynamic_context": {
                                    "context_frame_count": 1,
                                    "prelude": [
                                        {
                                            "kind": "runtime_context_frame",
                                            "event_type": "control_flow",
                                            "frame": 0,
                                            "pc": 0x4000,
                                            "pc_bank": 0,
                                            "pc_bank_address": "00:4000",
                                            "pc_label": "BattleCommand_Test",
                                            "registers": {"register_pc": "4000", "register_a": "12"},
                                            "register_pc": "4000",
                                            "register_a": "12",
                                            "watch_values": {"wCurDamage": "0000"},
                                        }
                                    ],
                                    "after": {
                                        "kind": "runtime_context_frame",
                                        "event_type": "control_flow",
                                        "frame": 1,
                                        "pc": 0x4003,
                                        "pc_bank": 0,
                                        "pc_bank_address": "00:4003",
                                        "pc_label": "BattleCommand_Test+0x3",
                                        "registers": {"register_pc": "4003", "register_a": "12"},
                                        "register_pc": "4003",
                                        "register_a": "12",
                                        "watch_values": {"wCurDamage": "3400"},
                                    },
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_trace_index_report(
                reports=("watch.json",),
                symbols_path="test.sym",
                root=root,
            )

        event_types = [event["event_type"] for event in report["events"]]
        control_flow_pcs = {
            event["pc_bank_address"]
            for event in report["events"]
            if event["event_type"] == "control_flow"
        }

        self.assertTrue(report["valid"])
        self.assertIn("watch_change", event_types)
        self.assertGreaterEqual(event_types.count("control_flow"), 2)
        self.assertIn("00:4000", control_flow_pcs)
        self.assertIn("00:4003", control_flow_pcs)

    def test_trace_index_builds_reverse_attribution_window(self) -> None:
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
                                "source_file": "engine/battle/effect_commands.asm",
                            },
                            {
                                "access": "write",
                                "symbol": "wCurDamage",
                                "address": "D141",
                                "old_value": "0000",
                                "new_value": "002A",
                                "register_a": "2A",
                                "pc_label": "BattleCommand_DamageCalc",
                                "source_file": "engine/battle/effect_commands.asm",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = build_trace_index_report(
                traces=("trace.json",),
                watch_symbols=("wCurDamage",),
                symbols_path="test.sym",
                root=root,
            )
            (root / "trace_index.json").write_text(json.dumps(report), encoding="utf-8")
            explanation = build_explanation_report(
                reports=("trace_index.json",),
                symbols_path="test.sym",
                root=root,
            )

        relations = {link["relation"] for link in report["causal_links"]}
        attribution = report["reverse_attributions"][0]
        path_labels = {
            node["label"]
            for path in report["causal_paths"]
            for node in path.get("nodes", [])
        }
        explanation_labels = {
            node["label"]
            for path in explanation["paths"]
            for node in path.get("nodes", [])
        }

        self.assertTrue(report["valid"])
        self.assertEqual(report["reverse_attribution_count"], 1)
        self.assertIn("prior_read", relations)
        self.assertEqual(attribution["state"], "wCurDamage")
        self.assertEqual(attribution["contributors"][0]["state"], "wBattleMonAttack")
        self.assertIn("prior_read: wBattleMonAttack", path_labels)
        self.assertIn("wBattleMonAttack", explanation_labels)

    def test_cli_trace_index_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "watch": "wCurDamage",
                        "old_hex": "0000",
                        "new_hex": "0001",
                        "pc_label": "BattleCommand_Test",
                    }
                ),
                encoding="utf-8",
            )
            out = root / "trace_index.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "trace-index",
                        "--trace",
                        str(trace),
                        "--watch-symbol",
                        "wCurDamage",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_trace_index")
        self.assertEqual(data["event_count"], 1)
