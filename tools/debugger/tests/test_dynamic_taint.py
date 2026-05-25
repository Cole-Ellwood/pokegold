from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.dynamic_taint import build_dynamic_taint_report


class DynamicTaintTests(unittest.TestCase):
    def test_dynamic_taint_traces_instruction_source_to_sink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            trace = root / "instruction_trace.jsonl"
            trace.write_text(
                "\n".join(
                    json.dumps(row)
                    for row in [
                        {
                            "seq": 0,
                            "bank": 1,
                            "pc": 0x4000,
                            "pc_label": "BattleCommand_Test",
                            "opcode": 0x4F,
                            "regs": {"A": 0x37, "C": 0, "HL": 0, "SP": 0xDFF0},
                        },
                        {
                            "seq": 1,
                            "bank": 1,
                            "pc": 0x4001,
                            "pc_label": "BattleCommand_Test+0x1",
                            "opcode": 0x79,
                            "regs": {"A": 0x37, "C": 0x37, "HL": 0, "SP": 0xDFF0},
                        },
                        {
                            "seq": 2,
                            "bank": 1,
                            "pc": 0x4002,
                            "pc_label": "BattleCommand_Test+0x2",
                            "opcode": 0x21,
                            "operand": [0x41, 0xD1],
                            "regs": {"A": 0x37, "C": 0x37, "HL": 0, "SP": 0xDFF0},
                        },
                        {
                            "seq": 3,
                            "bank": 1,
                            "pc": 0x4005,
                            "pc_label": "BattleCommand_Test+0x5",
                            "opcode": 0x22,
                            "regs": {"A": 0x37, "C": 0x37, "HL": 0xD141, "SP": 0xDFF0},
                        },
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_dynamic_taint_report(
                traces=("instruction_trace.jsonl",),
                symbols_path="test.sym",
                source_regs=("a=move_power",),
                sink_symbols=("wCurDamage",),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["finding_count"], 1)
        self.assertEqual(report["paths"][0]["target"], "wCurDamage")
        self.assertIn("move_power", report["paths"][0]["taint"])
        self.assertEqual(report["trace_runs"][0]["unsupported_count"], 0)

    def test_cli_dynamic_taint_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:D141 wCurDamage\n", encoding="utf-8")
            trace = root / "instruction_trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "instructions": [
                            {
                                "seq": 0,
                                "bank": 1,
                                "pc": 0x4000,
                                "pc_label": "UnitCopy",
                                "opcode": 0xEA,
                                "operand": [0x41, 0xD1],
                                "regs": {"A": 0x2A, "SP": 0xDFF0},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out = root / "dynamic_taint.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "dynamic-taint",
                        "--trace",
                        str(trace),
                        "--symbols",
                        str(root / "test.sym"),
                        "--source-reg",
                        "a=move_power",
                        "--sink-symbol",
                        "wCurDamage",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_dynamic_taint_report")
        self.assertTrue(data["valid"])
        self.assertEqual(data["path_count"], 1)
        self.assertIn("move_power", data["paths"][0]["taint"])

    def test_cli_dynamic_taint_accepts_instruction_trace_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:D141 wCurDamage\n", encoding="utf-8")
            (root / "instruction_trace.jsonl").write_text(
                json.dumps(
                    {
                        "seq": 0,
                        "bank": 1,
                        "pc": 0x4000,
                        "pc_label": "UnitCopy",
                        "opcode": 0xEA,
                        "operand": [0x41, 0xD1],
                        "regs": {"A": 0x2A, "SP": 0xDFF0},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "instruction_trace_report.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": True,
                        "executed": True,
                        "trace_output": {"path": "instruction_trace.jsonl", "written": True},
                        "execution_validation": {
                            "attempted": True,
                            "hit": True,
                            "watch_symbols": ["wCurDamage"],
                            "ready_for_dynamic_taint": True,
                        },
                        "dynamic_taint_sources": {"source_regs": ["a=move_power"]},
                    }
                ),
                encoding="utf-8",
            )
            out = root / "dynamic_taint.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "dynamic-taint",
                        "--report",
                        str(root / "instruction_trace_report.json"),
                        "--symbols",
                        str(root / "test.sym"),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertTrue(data["valid"])
        self.assertEqual(len(data["effective_traces"]), 1)
        self.assertTrue(data["effective_traces"][0].endswith("instruction_trace.jsonl"))
        self.assertEqual(data["path_count"], 1)
        self.assertIn("move_power", data["paths"][0]["taint"])

    def test_dynamic_taint_attributes_sink_write_without_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:4000 UnitWriter\n",
                encoding="utf-8",
            )
            trace = root / "instruction_trace.jsonl"
            trace.write_text(
                json.dumps(
                    {
                        "seq": 0,
                        "bank": 1,
                        "pc": 0x4000,
                        "pc_label": "UnitWriter",
                        "opcode": 0xEA,
                        "operand": [0x41, 0xD1],
                        "regs": {"A": 0x2A, "SP": 0xDFF0},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_dynamic_taint_report(
                traces=("instruction_trace.jsonl",),
                symbols_path="test.sym",
                sink_symbols=("wCurDamage",),
                root=root,
            )

        attribution = report["write_attributions"][0]

        self.assertTrue(report["valid"])
        self.assertEqual(report["source_count"], 0)
        self.assertEqual(report["finding_count"], 0)
        self.assertEqual(report["path_count"], 0)
        self.assertEqual(report["write_attribution_count"], 1)
        self.assertIn("no taint sources supplied", "\n".join(report["warnings"]))
        self.assertEqual(attribution["target"], "wCurDamage")
        self.assertEqual(attribution["pc_label"], "UnitWriter")
        self.assertEqual(attribution["address"], "D141")
        self.assertEqual(attribution["source_operands"][0]["kind"], "register")
        self.assertEqual(attribution["source_operands"][0]["name"], "a")
        self.assertEqual(attribution["source_operands"][0]["value"], "2A")
        self.assertIn("register:a=$2A", "\n".join(attribution["evidence"]))
        self.assertEqual(report["targets"][0]["write_attribution_count"], 1)

    def test_dynamic_taint_discovers_trace_inputs_from_instruction_trace_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "01:D141 wCurDamage\n01:4000 UnitWriter\n",
                encoding="utf-8",
            )
            (root / "instruction_trace.jsonl").write_text(
                json.dumps(
                    {
                        "seq": 0,
                        "bank": 1,
                        "pc": 0x4000,
                        "pc_label": "UnitWriter",
                        "opcode": 0xEA,
                        "operand": [0x41, 0xD1],
                        "regs": {"A": 0x2A, "SP": 0xDFF0},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "instruction_trace_report.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_instruction_trace",
                        "valid": True,
                        "executed": True,
                        "execution_validation": {
                            "attempted": True,
                            "hit": True,
                            "watch_symbols": ["wCurDamage"],
                            "ready_for_dynamic_taint": True,
                        },
                        "trace_output": {
                            "path": "instruction_trace.jsonl",
                            "written": True,
                            "record_count": 1,
                        },
                        "watches": [{"name": "wCurDamage"}],
                        "dynamic_taint_sources": {
                            "source_regs": ["a=script_arg"],
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_dynamic_taint_report(
                reports=("instruction_trace_report.json",),
                symbols_path="test.sym",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["report_count"], 1)
        self.assertEqual(report["effective_traces"], ["instruction_trace.jsonl"])
        self.assertEqual(report["input_discovery"]["sink_symbols"], ["wCurDamage"])
        self.assertEqual(report["input_discovery"]["source_regs"], ["a=script_arg"])
        self.assertEqual(report["source_count"], 1)
        self.assertEqual(report["sink_count"], 1)
        self.assertEqual(report["path_count"], 1)
        self.assertEqual(report["write_attribution_count"], 1)
        self.assertIn("script_arg", report["paths"][0]["taint"])
