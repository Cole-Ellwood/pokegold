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
    def test_return_address_overwrites_remove_old_stack_taint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("00:C200 wSink\n")
            for opcode, flags, overwritten in ((0, 0, False), (0xCD, 0, True), (0xC4, 0, True),
                                                (0xC4, 0x80, False), (0xCF, 0, True)):
                with self.subTest(opcode=opcode, flags=flags):
                    records = [
                        {"seq": 0, "pc": 0x4000, "opcode": 0xD5, "regs": {"D": 2, "E": 3, "SP": 0xC100}},
                        {"seq": 1, "pc": 0x4001, "opcode": opcode, "operand": [0, 0x50] if opcode in (0xCD, 0xC4) else [],
                         "regs": {"SP": 0xC100, "F": flags}},
                        {"seq": 2, "pc": 0x5000, "opcode": 0xC1, "regs": {"SP": 0xC0FE}},
                        {"seq": 3, "pc": 0x5001, "opcode": 0x78, "regs": {"B": 2}},
                        {"seq": 4, "pc": 0x5002, "opcode": 0xEA, "operand": [0, 0xC2], "regs": {"A": 2}},
                    ]
                    (root / "trace.jsonl").write_text("\n".join(json.dumps(record) for record in records))
                    report = build_dynamic_taint_report(traces=("trace.jsonl",), symbols_path="test.sym",
                                                       source_regs=("d=returned_value",), sink_symbols=("wSink",), root=root)
                    self.assertTrue(report["valid"], report["errors"])
                    self.assertEqual(report["write_attributions"][-1]["taint"], [] if overwritten else ["returned_value"])

    def test_push_writes_have_byte_sources_and_matching_taint(self) -> None:
        for opcode, low, high in ((0xC5, "c", "b"), (0xD5, "e", "d"), (0xE5, "l", "h"), (0xF5, "f", "a")):
            with self.subTest(opcode=opcode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "test.sym").write_text("00:C0FE wStackSink\n", encoding="utf-8")
                (root / "trace.jsonl").write_text(json.dumps({
                    "opcode": opcode, "pc": 0x4000,
                    "regs": {"A": 0x12, "F": 0x30, "B": 0x45, "C": 0x67,
                             "D": 0x89, "E": 0xAB, "H": 0xCD, "L": 0xEF,
                             "HL": 0xCDEF, "SP": 0xC100},
                }) + "\n", encoding="utf-8")
                report = build_dynamic_taint_report(
                    traces=("trace.jsonl",), symbols_path="test.sym",
                    source_regs=(f"{low}=low_byte", f"{high}=high_byte"),
                    sink_symbols=("wStackSink",), sink_size=2, root=root,
                )
                self.assertTrue(report["valid"])
                self.assertEqual(report["finding_count"], 2)
                self.assertEqual(report["write_attribution_count"], 2)
                writes = report["write_attributions"]
                self.assertEqual([w["address"] for w in writes], ["C0FE", "C0FF"])
                self.assertEqual([w["source_operands"][0]["name"] for w in writes], [low, high])
                self.assertEqual([w["taint"] for w in writes], [["low_byte"], ["high_byte"]])

    def test_missing_stack_pointer_does_not_invent_write_addresses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("00:FFFE wSink\n", encoding="utf-8")
            (root / "trace.jsonl").write_text(json.dumps({
                "opcode": 0xC5, "pc": 0x4000, "regs": {"B": 1, "C": 2},
            }) + "\n", encoding="utf-8")
            report = build_dynamic_taint_report(
                traces=("trace.jsonl",), symbols_path="test.sym",
                sink_symbols=("wSink",), sink_size=2, root=root,
            )
            self.assertTrue(report["valid"])
            self.assertEqual(report["write_attributions"], [])

    def test_return_address_writes_follow_taken_calls_and_restarts(self) -> None:
        cases = [(0xCD, 0, True)]
        for opcode, taken_flags, other_flags in ((0xC4, 0, 0x80), (0xCC, 0x80, 0), (0xD4, 0, 0x10), (0xDC, 0x10, 0)):
            cases.extend(((opcode, taken_flags, True), (opcode, other_flags, False), (opcode, None, False)))
        cases.extend((opcode, 0, True) for opcode in (0xC7, 0xCF, 0xD7, 0xDF, 0xE7, 0xEF, 0xF7, 0xFF))
        for opcode, flags, taken in cases:
            with self.subTest(opcode=opcode, flags=flags), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "test.sym").write_text("00:C0FE wStackSink\n", encoding="utf-8")
                registers = {"SP": 0xC100}
                if flags is not None:
                    registers["F"] = flags
                operand = [] if opcode & 7 == 7 else [0, 0x50]
                (root / "trace.jsonl").write_text(json.dumps({
                    "opcode": opcode, "operand": operand, "pc": 0x4000, "regs": registers,
                }) + "\n", encoding="utf-8")
                report = build_dynamic_taint_report(
                    traces=("trace.jsonl",), symbols_path="test.sym",
                    sink_symbols=("wStackSink",), sink_size=2, root=root,
                )
                self.assertTrue(report["valid"])
                self.assertEqual(report["write_attribution_count"], 2 if taken else 0)
                self.assertEqual(report["trace_runs"][0]["unsupported_count"], 0)
                if taken:
                    self.assertEqual(
                        [w["source_operands"] for w in report["write_attributions"]],
                        [[{"kind": "immediate", "value": "01" if not operand else "03"}],
                         [{"kind": "immediate", "value": "40"}]],
                    )

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

class DynamicTaintRegressionTests(unittest.TestCase):
    def report(self, records, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'test.sym').write_text('01:D141 Target\n02:D141 OtherTarget\n01:D100 Secret\n02:D100 OtherSecret\n00:C100 Sink\n00:C0FE Stack\n', encoding='utf-8')
            (root / 'trace.json').write_text(json.dumps(records), encoding='utf-8')
            return build_dynamic_taint_report(traces=('trace.json',), symbols_path='test.sym', root=root, **kwargs)

    def test_sink_identity_uses_runtime_bank_and_warns_when_unknown(self):
        for bank in (1, 2, None):
            with self.subTest(bank=bank):
                row = {'pc': 0x4000, 'opcode': 0xEA, 'operand': [0x41, 0xD1], 'A': 42}
                if bank is not None:
                    row['bank_state'] = {'wram': bank}
                report = self.report([row], source_regs=('a=secret',), sink_symbols=('Target',))
                self.assertEqual(report['finding_count'], 0 if bank == 2 else 1)
                self.assertEqual(report['write_attribution_count'], 0 if bank == 2 else 1)
                if bank is None:
                    self.assertIn('bank', ' '.join(report['warnings']).lower())
                    self.assertLessEqual(report['write_attributions'][0]['confidence'], 0.5)
                    self.assertLessEqual(report['paths'][0]['confidence'], 0.5)
                    self.assertIn('provisional', ' '.join(report['paths'][0]['evidence']))
                elif bank == 1:
                    self.assertFalse(report['warnings'])
                    self.assertEqual(report['write_attributions'][0]['address_symbol'], 'Target')
        report = self.report([{'pc': 0x4000, 'opcode': 0xEA, 'operand': [0x41, 0xD1], 'A': 42, 'bank_state': {'wram': 2}}], source_regs=('a=secret',), sink_symbols=('Target', 'OtherTarget'))
        self.assertEqual([w['target'] for w in report['write_attributions']], ['OtherTarget'])
        self.assertEqual(report['write_attributions'][0]['address_symbol'], 'OtherTarget')
        self.assertNotIn('Target', report['write_attributions'][0]['related_symbols'])

    def test_banked_source_seeds_do_not_leak_to_other_bank(self):
        for source in ('Secret', 'OtherSecret'):
            for bank in (1, 2, None):
                with self.subTest(source=source, bank=bank):
                    read = {'pc': 0x4000, 'opcode': 0xFA, 'operand': [0, 0xD1]}
                    if bank is not None:
                        read['bank_state'] = {'wram': bank}
                    report = self.report([read, {'pc': 0x4003, 'opcode': 0xEA, 'operand': [0, 0xC1], 'A': 42}], source_symbols=(source,), sink_symbols=('Sink',))
                    self.assertEqual(report['finding_count'], int(bank is None or bank == (1 if source == 'Secret' else 2)))
                    if bank is None:
                        self.assertIn('bank', ' '.join(report['warnings']).lower())

    def test_bank_switch_restores_each_banks_memory_taint(self):
        records = [
            {'pc': 0x4000, 'opcode': 0xEA, 'operand': [0, 0xD1], 'A': 1, 'bank_state': {'wram': 1}},
            {'pc': 0x4003, 'opcode': 0xAF},
            {'pc': 0x4004, 'opcode': 0xE0, 'operand': [0x70], 'A': 2},
            {'pc': 0x4006, 'opcode': 0xEA, 'operand': [0, 0xD1], 'A': 0},
            {'pc': 0x4009, 'opcode': 0xFA, 'operand': [0, 0xD1]},
            {'pc': 0x400C, 'opcode': 0xEA, 'operand': [0, 0xC1], 'A': 0},
            {'pc': 0x400F, 'opcode': 0xE0, 'operand': [0x70], 'A': 1},
            {'pc': 0x4011, 'opcode': 0xFA, 'operand': [0, 0xD1]},
            {'pc': 0x4014, 'opcode': 0xEA, 'operand': [0, 0xC1], 'A': 1},
        ]
        report = self.report(records, source_regs=('a=secret',), sink_symbols=('Sink',))
        self.assertEqual([f['seq'] for f in report['findings']], [8])
        self.assertEqual([w['taint'] for w in report['write_attributions']], [[], ['secret']])

    def test_simultaneous_banked_source_symbols_remain_distinct(self):
        for bank, expected in ((1, ['source_symbol:Secret']), (2, ['source_symbol:OtherSecret'])):
            with self.subTest(bank=bank):
                report = self.report([
                    {'pc': 0x4000, 'opcode': 0xFA, 'operand': [0, 0xD1], 'bank_state': {'wram': bank}},
                    {'pc': 0x4003, 'opcode': 0xEA, 'operand': [0, 0xC1], 'A': 1},
                ], source_symbols=('Secret', 'OtherSecret'), sink_symbols=('Sink',))
                self.assertEqual(report['source_count'], 2)
                self.assertEqual(report['write_attributions'][0]['taint'], expected)

    def test_explicit_banked_sources_and_sinks_keep_identity(self):
        for bank in (1, 2, None):
            with self.subTest(bank=bank):
                read = {'pc': 0x4000, 'opcode': 0xFA, 'operand': [0, 0xD1]}
                if bank is not None:
                    read['bank_state'] = {'wram': bank}
                report = self.report([read, {'pc': 0x4003, 'opcode': 0xEA, 'operand': [0, 0xC1], 'A': 42}], source_mems=('01:D100=secret',), sink_symbols=('Sink',))
                self.assertEqual(report['finding_count'], int(bank != 2))
                if bank is None:
                    self.assertIn('bank', ' '.join(report['warnings']).lower())
                write = {'pc': 0x4000, 'opcode': 0xEA, 'operand': [0x41, 0xD1], 'A': 42}
                if bank is not None:
                    write['bank_state'] = {'wram': bank}
                report = self.report([write], source_regs=('a=secret',), sink_addresses=('01:D141',))
                self.assertEqual(report['write_attribution_count'], int(bank != 2))
                if bank is None:
                    self.assertIn('bank', ' '.join(report['warnings']).lower())

    def test_missing_write_source_value_is_not_zero(self):
        for value in (None, 0, 42):
            with self.subTest(value=value):
                record = {'pc': 0x4000, 'opcode': 0xEA, 'operand': [0, 0xC1]}
                if value is not None:
                    record['A'] = value
                report = self.report([record], sink_symbols=('Sink',))
                operand = report['write_attributions'][0]['source_operands'][0]
                self.assertEqual('value' in operand, value is not None)
                if value is not None:
                    self.assertEqual(operand['value'], f'{value:02X}')
                else:
                    self.assertNotIn('$00', ' '.join(report['write_attributions'][0]['evidence']))
        report = self.report([{'pc': 0x4000, 'opcode': 0xC5, 'SP': 0xC100, 'B': 0}], sink_symbols=('Stack',), sink_size=2)
        operands = [w['source_operands'][0] for w in report['write_attributions']]
        self.assertNotIn('value', operands[0])
        self.assertEqual(operands[1]['value'], '00')

    def test_overwritten_sources_do_not_remain_contributors(self):
        for overwrite in ({'opcode': 0xAF}, {'opcode': 0x3E, 'operand': [0]}):
            with self.subTest(overwrite=overwrite):
                report = self.report([{'pc': 0x4000, **overwrite}, {'pc': 0x4002, 'opcode': 0xEA, 'operand': [0, 0xC1], 'A': 0}], source_regs=('a=secret',), sink_symbols=('Sink',))
                self.assertEqual(report['findings'], [])
                self.assertEqual(report['write_attributions'][0]['contributors'], [])
                self.assertNotIn('origin', report['write_attributions'][0]['source_operands'][0])
                self.assertEqual(report['targets'][0]['contributors'], [])
        report = self.report([{'pc': 0x4000, 'opcode': 0x47, 'A': 42}, {'pc': 0x4001, 'opcode': 0xAF}, {'pc': 0x4002, 'opcode': 0x78, 'B': 42}, {'pc': 0x4003, 'opcode': 0xEA, 'operand': [0, 0xC1], 'A': 42}], source_regs=('a=secret',), sink_symbols=('Sink',))
        self.assertEqual(report['write_attributions'][0]['taint'], ['secret'])
        self.assertEqual([c['symbol'] for c in report['write_attributions'][0]['contributors']], ['secret'])
        report = self.report([{'pc': 0x4000, 'opcode': 0xEA, 'operand': [0, 0xD1], 'A': 0, 'bank_state': {'wram': 1}}, {'pc': 0x4003, 'opcode': 0xFA, 'operand': [0, 0xD1]}, {'pc': 0x4006, 'opcode': 0xEA, 'operand': [0, 0xC1], 'A': 0}], source_symbols=('Secret',), sink_symbols=('Sink',))
        self.assertEqual(report['findings'], [])
        self.assertEqual(report['targets'][0]['contributors'], [])
