from __future__ import annotations

import json
import copy
from pathlib import Path
import tempfile
import unittest

from tools.debugger.effect_trace import build_effect_trace_report


class EffectTraceRegressionTests(unittest.TestCase):
    def test_input_hypothesis_checks_counted_pointer_loop_transitions(self):
        rows = []
        def emit(pc, opcode, *, bank=2, a=2, hl=0xFFF0, bc=16, f=0, operand=(), label=""):
            rows.append({"seq": len(rows), "bank": bank, "pc": pc, "opcode": opcode,
                         "operand": list(operand), "pc_label": label,
                         "A": a, "B": bc >> 8, "C": bc & 255, "H": hl >> 8, "L": hl & 255, "F": f})
        emit(0x4000, 0x3E, bank=1, a=0, operand=(1,))
        emit(0x4002, 0x3E, bank=1, a=1, operand=(2,), label="Caller+2")
        emit(0x4004, 0x21, bank=1, operand=(0, 0x41))
        emit(0x4007, 0xCF, bank=1, hl=0x4100)
        emit(8, 0xE9, bank=0, hl=0x4100)
        emit(0x4100, 0x21, hl=0x4100, operand=(0xF0, 0xFF), label="Callee")
        emit(0x4103, 0x01, operand=(16, 0))
        emit(0x4106, 0xA7, label="Callee.count")
        emit(0x4107, 0xC8, f=0x20)
        emit(0x4108, 0x09, f=0x20, label="Callee.loop")
        emit(0x4109, 0x3D, hl=0, f=0x30)
        emit(0x410A, 0x20, a=1, hl=0, f=0x50, operand=(0xFC,))
        emit(0x4108, 0x09, a=1, hl=0, f=0x50, label="Callee.loop")
        emit(0x4109, 0x3D, a=1, hl=16, f=0)
        emit(0x410A, 0x20, a=0, hl=16, f=0xC0, operand=(0xFC,))
        emit(0x410C, 0xC9, a=0, hl=16, f=0xC0)
        for mode in ("complete", "pointer", "counter", "stride", "flags", "guard_flags", "successor_flags", "jump", "bank", "gap", "missing_register", "truncated"):
            with self.subTest(mode=mode):
                records = copy.deepcopy(rows)
                if mode == "pointer":
                    records[10]["L"] = 1
                elif mode == "counter":
                    records[11]["A"] = 0
                elif mode == "stride":
                    records[12]["C"] = 17
                elif mode == "flags":
                    records[11]["F"] = 0xD0
                elif mode == "guard_flags":
                    records[9]["F"] = 0
                elif mode == "successor_flags":
                    records[15]["F"] = 0x40
                elif mode == "jump":
                    records[11]["operand"] = [0xFD]
                elif mode == "bank":
                    records[12]["bank"] = 3
                elif mode == "gap":
                    records.pop(10)
                elif mode == "missing_register":
                    records[13].pop("H")
                elif mode == "truncated":
                    records.pop()
                report = self.report(records)
                atom, = [a for e in report["events"] for a in e["evidence_atoms"] if a["claim_type"] == "diagnosis.hypothesis"]
                loop = atom["detail"].get("counted_pointer_loop")
                self.assertEqual(bool(loop), mode == "complete")
                if loop:
                    self.assertEqual(loop["proof_status"], "instruction_observed")
                    self.assertEqual((loop["counter_initial"], loop["stride"], loop["pointer_initial"], loop["pointer_final"]), (2, 16, 0xFFF0, 16))
                    self.assertEqual(loop["iterations"], 2)
                    self.assertEqual(loop["exit_seq"], 15)
                    self.assertEqual(loop["iteration_seqs"], [[9, 10, 11], [12, 13, 14]])
                self.assertEqual(atom["proof_status"], "planned_only")
                self.assertNotIn("diagnosis.root_cause", str(report))

    def test_farcall_input_overwrite_proposes_entry_trial(self):
        records = [
            {"seq": 0, "bank": 1, "pc": 0x4000, "opcode": 0x3E, "operand": [2], "A": 0},
            {"seq": 1, "bank": 1, "pc": 0x4002, "pc_label": "Caller+2", "opcode": 0x3E, "operand": [17], "A": 2},
            {"seq": 2, "bank": 1, "pc": 0x4004, "opcode": 0x21, "operand": [0, 0x41], "A": 17},
            {"seq": 3, "bank": 1, "pc": 0x4007, "opcode": 0xCF, "A": 17, "H": 0x41, "L": 0},
            {"seq": 4, "bank": 0, "pc": 8, "opcode": 0xE9, "A": 17, "H": 0x41, "L": 0},
            {"seq": 5, "bank": 17, "pc": 0x4100, "pc_label": "Callee", "opcode": 0x01, "operand": [47, 0], "A": 17},
            {"seq": 6, "bank": 17, "pc": 0x4103, "opcode": 0xA7, "A": 17},
        ]
        for mode in ("candidate", "memory_input", "zero", "same_value", "unknown_input", "unconfirmed_load", "wrong_bank",
                     "wrong_target", "gap", "wrong_dispatch", "rewritten", "missing_consumer"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "engine").mkdir()
                (root / "engine/unit.asm").write_text("Caller:\n\tld a, 2\n\tfarcall Callee\nCallee:\n\tret\n")
                (root / "test.sym").write_text("01:4000 Caller\n11:4100 Callee\n")
                rows = copy.deepcopy(records)
                if mode == "memory_input":
                    rows[0].update(opcode=0xF0, operand=[0x80])
                elif mode == "zero":
                    rows[0]["operand"] = [0]
                    rows[1]["A"] = 0
                elif mode == "same_value":
                    rows[0]["operand"] = [17]
                    rows[1]["A"] = 17
                elif mode == "unknown_input":
                    rows[1].pop("A")
                elif mode == "unconfirmed_load":
                    rows[0]["operand"] = [3]
                elif mode == "wrong_bank":
                    rows[5]["bank"] = 18
                elif mode == "wrong_target":
                    rows[5]["pc"] += 1
                elif mode == "gap":
                    rows[4]["seq"] = 10
                elif mode == "wrong_dispatch":
                    rows[4]["opcode"] = 0
                elif mode == "rewritten":
                    rows[5].update(opcode=0x3E, operand=[17])
                    rows[6]["pc"] -= 1
                elif mode == "missing_consumer":
                    rows.pop()
                (root / "trace.json").write_text(json.dumps(rows))
                report = build_effect_trace_report(traces=("trace.json",), symbols_path="test.sym", root=root)
                hypotheses = [a for e in report["events"] for a in e["evidence_atoms"] if a["claim_type"] == "diagnosis.hypothesis"]
                self.assertEqual(len(hypotheses), int(mode in ("candidate", "memory_input", "zero")))
                if hypotheses:
                    atom = hypotheses[0]
                    self.assertEqual(atom["proof_status"], "planned_only")
                    self.assertEqual(atom["detail"]["intervention"], {"at": "Callee", "register": "A", "expected": 17, "value": 0 if mode == "zero" else 2})
                    self.assertEqual(atom["detail"]["consumer_seq"], 6)
                    self.assertEqual([c["source_line"] for c in atom["detail"]["source_candidates"]], [3])
                self.assertNotIn("diagnosis.root_cause", str(report))

    def test_hypothesis_cites_matching_source_calls_without_claiming_build_correspondence(self):
        from tools.debugger.report_envelope import sha256_file
        records = [
            {"seq": 0, "bank": 1, "pc": 0x4000, "pc_label": "Caller", "opcode": 0xCD, "operand": [0, 0x41], "D": 2, "SP": 0xD100},
            {"seq": 1, "bank": 1, "pc": 0x4100, "opcode": 0x16, "operand": [203], "D": 2, "SP": 0xD0FE},
            {"seq": 2, "bank": 1, "pc": 0x4102, "opcode": 0xC9, "D": 203, "SP": 0xD0FE},
            {"seq": 3, "bank": 1, "pc": 0x4003, "pc_label": "Caller+0x3", "opcode": 0x7A, "D": 203, "SP": 0xD100},
            {"seq": 4, "bank": 1, "pc": 0x4004, "opcode": 0xFE, "operand": [2], "A": 203, "D": 203, "SP": 0xD100}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine").mkdir()
            source = root / "engine/unit.asm"
            (root / "trace.json").write_text(json.dumps(records))
            for mode, expected_lines in (("single", [2]), ("repeated", [2, 3]), ("edited", [3]), ("bank", []), ("caller", []), ("callee", []), ("conditional", [])):
                with self.subTest(mode=mode):
                    calls = "\tcall Other\n" if mode == "callee" else "\tcall Callee\n"
                    if mode == "conditional":
                        calls = "\tcall z, Callee\n"
                    if mode == "repeated":
                        calls += calls
                    if mode == "edited":
                        calls = "; inserted comment\n" + calls
                    source.write_text("Caller:\n" + calls + "\tret\nCallee:\n\tret\nOther:\n\tret\n")
                    (root / "test.sym").write_text(
                        ("02:4000 Caller\n" if mode == "caller" else "01:4000 Caller\n") +
                        ("02:4100 Callee\n" if mode == "bank" else "01:4100 Callee\n") + "01:4200 Other\n")
                    report = build_effect_trace_report(traces=("trace.json",), symbols_path="test.sym", root=root)
                    atom = next(a for e in report["events"] for a in e["evidence_atoms"] if a["claim_type"] == "diagnosis.hypothesis")
                    candidates = atom["detail"].get("source_candidates", [])
                    self.assertEqual([c["source_line"] for c in candidates], expected_lines)
                    for candidate in candidates:
                        self.assertEqual(candidate["source_file"], "engine/unit.asm")
                        self.assertEqual(candidate["source_symbol"], "Caller")
                        self.assertEqual(candidate["source_sha256"], sha256_file(source))
                    self.assertEqual(atom["proof_status"], "planned_only")
                    self.assertNotIn("source_line", atom["precision"])
                    self.assertNotIn("diagnosis.root_cause", str(report))

    def test_changed_register_compared_to_its_prior_value_proposes_consumer_trial(self):
        records = [
            {"seq": 0, "bank": 1, "pc": 0x4000, "pc_label": "Caller", "opcode": 0xCD, "operand": [0, 0x41], "D": 2, "SP": 0xD100},
            {"seq": 1, "bank": 1, "pc": 0x4100, "opcode": 0x16, "operand": [203], "D": 2, "SP": 0xD0FE},
            {"seq": 2, "bank": 1, "pc": 0x4102, "opcode": 0xC9, "D": 203, "SP": 0xD0FE},
            {"seq": 3, "bank": 1, "pc": 0x4003, "pc_label": "Caller+0x3", "opcode": 0x7A, "D": 203, "A": 0, "SP": 0xD100},
            {"seq": 4, "bank": 1, "pc": 0x4004, "opcode": 0xFE, "operand": [2], "D": 203, "A": 203, "SP": 0xD100},
        ]
        report = self.report(records)
        hypotheses = [a for e in report["events"] for a in e["evidence_atoms"] if a["claim_type"] == "diagnosis.hypothesis"]
        self.assertEqual(len(hypotheses), 1)
        self.assertEqual(hypotheses[0]["proof_status"], "planned_only")
        self.assertEqual(hypotheses[0]["detail"]["intervention"],
                         {"at": "Caller+0x3", "register": "D", "expected": 203, "value": 2})
        self.assertEqual(hypotheses[0]["detail"]["consumer_seq"], 3)
        self.assertEqual(hypotheses[0]["detail"]["call_register_change"],
                         {"before": "02", "after": "CB", "observed_write_seqs": [1], "entry_seq": 1, "return_seq": 3,
                          "direct_continuity_to_consumer": True})
        self.assertNotIn("diagnosis.root_cause", str(report))
        zero = copy.deepcopy(records)
        zero[0]["D"] = zero[1]["D"] = 0
        zero[-1]["operand"] = [0]
        zero_report = self.report(zero)
        zero_trial = next(a for e in zero_report["events"] for a in e["evidence_atoms"] if a["claim_type"] == "diagnosis.hypothesis")
        self.assertEqual(zero_trial["detail"]["intervention"]["value"], 0)
        for mode in ("taken", "fallthrough", "flags_changed", "flags_missing", "flags_rewritten", "gap", "wrong_target", "wrong_bank", "missing_successor"):
            with self.subTest(branch=mode):
                branched = copy.deepcopy(records)
                branched[-1]["F"] = 0
                branched.extend([
                    {"seq": 5, "bank": 1, "pc": 0x4006, "opcode": 0x3E, "operand": [6], "A": 203, "F": 0x40},
                    {"seq": 6, "bank": 1, "pc": 0x4008, "opcode": 0x28 if mode == "fallthrough" else 0x20, "operand": [2], "A": 6, "F": 0x40},
                    {"seq": 7, "bank": 1, "pc": 0x400A if mode == "fallthrough" else 0x400C, "opcode": 0, "A": 6, "F": 0x40},
                ])
                if mode == "flags_changed":
                    branched[5]["F"] = 0xC0
                elif mode == "flags_missing":
                    branched[6].pop("F")
                elif mode == "flags_rewritten":
                    branched[5].update(opcode=0xFE, operand=[2])
                elif mode == "gap":
                    branched[6]["seq"] += 1
                elif mode == "wrong_target":
                    branched[7]["pc"] += 1
                elif mode == "wrong_bank":
                    branched[7]["bank"] = 2
                elif mode == "missing_successor":
                    branched.pop()
                result = self.report(branched)
                detail = next(a["detail"] for e in result["events"] for a in e["evidence_atoms"] if a["claim_type"] == "diagnosis.hypothesis")
                if mode in ("taken", "fallthrough"):
                    self.assertEqual(detail["comparison_branch"], {"comparison_seq": 4, "branch_seq": 6, "successor_seq": 7,
                        "condition": "z" if mode == "fallthrough" else "nz", "taken": mode == "taken",
                        "target": branched[-1]["pc"], "bank": 1, "flags_hex": "40"})
                else:
                    self.assertNotIn("comparison_branch", detail)
        for last_change in ({"operand": [3]}, {"A": 2}):
            changed = copy.deepcopy(records)
            changed[-1].update(last_change)
            report = self.report(changed)
            self.assertFalse([a for e in report["events"] for a in e["evidence_atoms"] if a["claim_type"] == "diagnosis.hypothesis"])
        for mode in ("preserved", "redefined", "gap", "unknown", "changed"):
            with self.subTest(propagation=mode):
                delayed = copy.deepcopy(records)
                inserted = {"seq": 3, "bank": 1, "pc": 0x4003, "opcode": 0,
                            "D": 203, "SP": 0xD100}
                if mode == "redefined":
                    inserted.update(opcode=0x16, operand=[203])
                if mode == "unknown":
                    del inserted["D"]
                if mode == "changed":
                    inserted["D"] = 2
                delayed.insert(3, inserted)
                for index in (4, 5):
                    delayed[index]["seq"] += 2 if mode == "gap" else 1
                    delayed[index]["pc"] += 2 if mode == "redefined" else 1
                result = self.report(delayed)
                found = [a for e in result["events"] for a in e["evidence_atoms"] if a["claim_type"] == "diagnosis.hypothesis"]
                self.assertEqual(len(found), 0 if mode in ("unknown", "changed") else 1)
                if found:
                    self.assertEqual(found[0]["detail"]["call_register_change"]["direct_continuity_to_consumer"], mode == "preserved")

    def test_call_boundary_distinguishes_changed_and_restored_registers(self):
        records = [
            {"seq": 0, "bank": 1, "pc": 0x4000, "opcode": 0xCD, "operand": [0, 0x41], "D": 2, "E": 7, "SP": 0xD100},
            {"seq": 1, "bank": 1, "pc": 0x4100, "opcode": 0x11, "operand": [14, 0xCB], "D": 2, "E": 7, "SP": 0xD0FE},
            {"seq": 2, "bank": 1, "pc": 0x4103, "opcode": 0xC9, "D": 203, "E": 14, "SP": 0xD0FE},
            {"seq": 3, "bank": 1, "pc": 0x4003, "opcode": 0, "D": 203, "E": 14, "SP": 0xD100},
        ]
        report = self.report(records)
        atoms = [a for a in report["events"][0]["evidence_atoms"] if a["claim_type"] == "effect.call_registers"]
        self.assertEqual(len(atoms), 1)
        self.assertEqual(atoms[0]["detail"]["changes"]["D"], {"before": "02", "after": "CB", "observed_write_seqs": [1]})
        self.assertEqual(atoms[0]["detail"]["return_seq"], 3)
        self.assertNotIn("A", atoms[0]["detail"]["changes"])
        self.assertNotIn("A", atoms[0]["detail"].get("preserved_registers", []))
        records[2] = {"seq": 2, "bank": 1, "pc": 0x4103, "opcode": 0x16, "operand": [2], "D": 203, "E": 14, "SP": 0xD0FE}
        records[3] = {"seq": 3, "bank": 1, "pc": 0x4105, "opcode": 0xC9, "D": 2, "E": 14, "SP": 0xD0FE}
        records.append({"seq": 4, "bank": 1, "pc": 0x4003, "opcode": 0, "D": 2, "E": 14, "SP": 0xD100})
        report = self.report(records)
        atom = next(a for a in report["events"][0]["evidence_atoms"] if a["claim_type"] == "effect.call_registers")
        self.assertNotIn("D", atom["detail"]["changes"])
        self.assertIn("D", atom["detail"]["preserved_registers"])
        self.assertNotIn("diagnosis.root_cause", str(report))

    def test_call_boundary_requires_entry_return_stack_and_register_observations(self):
        original = [
            {"seq": 0, "bank": 1, "pc": 0x4000, "opcode": 0xCD, "operand": [0, 0x41], "D": 2, "SP": 0xD100},
            {"seq": 1, "bank": 1, "pc": 0x4100, "opcode": 0xC9, "D": 2, "SP": 0xD0FE},
            {"seq": 2, "bank": 1, "pc": 0x4003, "opcode": 0, "D": 203, "SP": 0xD100},
        ]
        for index, key, value in ((1, "bank", 2), (1, "pc", 0x4101), (1, "SP", 0xD0FC),
                                  (2, "bank", 2), (2, "pc", 0x4004), (2, "SP", 0xD0FE),
                                  (0, "SP", None), (2, "SP", None)):
            with self.subTest(index=index, key=key, value=value):
                records = copy.deepcopy(original)
                if value is None:
                    del records[index][key]
                else:
                    records[index][key] = value
                report = self.report(records)
                self.assertFalse([a for e in report["events"] for a in e["evidence_atoms"]
                                  if a["claim_type"] == "effect.call_registers"])
        self.assertFalse([a for e in self.report(original[:-1])["events"] for a in e["evidence_atoms"]
                          if a["claim_type"] == "effect.call_registers"])
        original[1]["opcode"] = 0xC8  # conditional RET without observed flags
        self.assertFalse([a for e in self.report(original)["events"] for a in e["evidence_atoms"]
                          if a["claim_type"] == "effect.call_registers"])

    def test_call_return_from_a_different_recording_is_not_matched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:4000 Caller\n")
            (root / "first.json").write_text(json.dumps([
                {"seq": 0, "bank": 1, "pc": 0x4000, "opcode": 0xCD, "operand": [0, 0x41], "D": 2, "SP": 0xD100},
                {"seq": 1, "bank": 1, "pc": 0x4100, "opcode": 0xC9, "D": 203, "SP": 0xD0FE},
            ]))
            (root / "second.json").write_text(json.dumps([
                {"seq": 2, "bank": 1, "pc": 0x4003, "opcode": 0, "D": 203, "SP": 0xD100},
            ]))
            report = build_effect_trace_report(traces=("first.json", "second.json"), symbols_path="test.sym", root=root)
        self.assertFalse([a for e in report["events"] for a in e["evidence_atoms"]
                          if a["claim_type"] == "effect.call_registers"])

    def report(self, records, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'test.sym').write_text('01:D141 Target\n', encoding='utf-8')
            (root / 'trace.json').write_text(json.dumps(records), encoding='utf-8')
            return build_effect_trace_report(traces=('trace.json',), symbols_path='test.sym', root=root, **kwargs)

    def test_hex_operand_encodings_produce_the_same_write(self):
        for operand in ('41D1', '41 D1', '0x41 0xD1', '$41 $D1', '41,D1', [65, 209]):
            with self.subTest(operand=operand):
                report = self.report([{'pc': 0x4000, 'opcode': 0xEA, 'operand': operand, 'A': 42}])
                writes = [e for event in report['events'] for e in event['effects'] if e['kind'] == 'memory_write']
                self.assertTrue(report['valid'])
                self.assertEqual([e['address_hex'] for e in writes], ['D141'])

    def test_incomplete_or_excess_operands_are_rejected_before_effects(self):
        for opcode, operand in ((0xEA, None), (0xEA, []), (0xEA, [0]), (0x3E, []), (0xCB, []), (0, [0]), (0xEA, [0, 0, 0])):
            with self.subTest(opcode=opcode, operand=operand):
                report = self.report([{'pc': 0x4000, 'opcode': opcode, 'operand': operand, 'A': 10}])
                self.assertTrue(report['errors'])
                self.assertEqual(report['events'], [])
        for opcode, operand in ((0xEA, [0, 0]), (0x3E, [0]), (0xCB, [0]), (0, [])):
            with self.subTest(valid_opcode=opcode):
                self.assertFalse(self.report([{'pc': 0x4000, 'opcode': opcode, 'operand': operand}])['errors'])

    def test_invalid_register_is_record_local(self):
        for field in ({'A': 'unknown'}, {'regs': {'A': 'unknown'}}, {'registers': {'SP': 'unknown'}}):
            with self.subTest(field=field):
                report = self.report([{'pc': 0x4000, 'opcode': 0}, {'pc': 0x4001, 'opcode': 0xEA, 'operand': [0, 0], **field}, {'pc': 0x4004, 'opcode': 0}])
                self.assertEqual(len(report['errors']), 1)
                self.assertEqual(len(report['events']), 2)
                self.assertFalse(any(e['access'] == 'write' for event in report['events'] for e in event['effects']))

    def test_post_register_validation_requires_observed_registers(self):
        for regs, count, status in (({}, 0, None), ({'A': 0}, 1, 'matched'), ({'A': 1}, 1, 'mismatch')):
            with self.subTest(regs=regs):
                report = self.report([{'pc': 0x4000, 'opcode': 0x3E, 'operand': [0]}, {'pc': 0x4002, 'opcode': 0, 'regs': regs}])
                writes = [e for e in report['events'][0]['effects'] if e['access'] == 'register_write']
                self.assertEqual(sum('post_register_hex' in e for e in writes), count)
                if status:
                    self.assertEqual(writes[0]['post_register_status'], status)
        for regs, observed in (({'H': 0}, False), ({'HL': 0}, True), ({'H': 0, 'L': 0}, True)):
            with self.subTest(pair=regs):
                report = self.report([{'pc': 0x4000, 'opcode': 0x21, 'operand': [0, 0]}, {'pc': 0x4003, 'opcode': 0, 'regs': regs}])
                write = next(e for e in report['events'][0]['effects'] if e['access'] == 'register_write')
                self.assertEqual('post_register_hex' in write, observed)

    def test_zero_idioms_write_constant_accumulator_and_flags(self):
        for opcode, flags in ((0xAF, '80'), (0x97, 'C0')):
            for regs in ({}, {'A': 99, 'F': 0}):
                with self.subTest(opcode=opcode, regs=regs):
                    report = self.report([{'pc': 0x4000, 'opcode': opcode, 'regs': regs}, {'pc': 0x4001, 'opcode': 0, 'F': int(flags, 16)}])
                    writes = {e['register']: e for e in report['events'][0]['effects'] if e['access'] == 'register_write'}
                    self.assertEqual(writes['A']['value_hex'], '00')
                    self.assertEqual(writes['F']['value_hex'], flags)
                    self.assertEqual(writes['F']['post_register_status'], 'matched')

    def test_unknown_conditional_flags_are_explicitly_unmodeled(self):
        families = (([0xC0, 0xC8, 0xD0, 0xD8], []), ([0xC4, 0xCC, 0xD4, 0xDC], [0, 0x50]), ([0xC2, 0xCA, 0xD2, 0xDA], [0, 0x50]), ([0x20, 0x28, 0x30, 0x38], [1]))
        for opcodes, operand in families:
            for opcode, taken_flags, other_flags in zip(opcodes, (0, 0x80, 0, 0x10), (0x80, 0, 0x10, 0)):
                for flags in (None, taken_flags, other_flags):
                    with self.subTest(opcode=opcode, flags=flags):
                        record = {'pc': 0x4000, 'opcode': opcode, 'operand': operand, 'SP': 0xC100}
                        if flags is not None:
                            record['F'] = flags
                        effects = self.report([record])['events'][0]['effects']
                        unmodeled = [e for e in effects if e['access'] == 'unmodeled']
                        if flags is None:
                            self.assertTrue(any('F' in e.get('missing_registers', []) for e in unmodeled))
                            self.assertFalse(any(e['access'] in {'write', 'register_write', 'control'} or e['kind'] == 'stack_read' for e in effects))
                        else:
                            self.assertFalse(unmodeled)
                            self.assertEqual(any(e['access'] == 'control' for e in effects), flags == taken_flags)

    def test_unknown_selector_writes_invalidate_carried_bank_state(self):
        for selector, address, key, initial in ((0xFF70, 0xD141, 'wram', 1), (0xFF4F, 0x8000, 'vram', 0), (0x2000, 0x4000, 'rom', 1), (0x4000, 0xA000, 'sram', 0)):
            for value in (None, 1):
                with self.subTest(selector=selector, value=value):
                    first = {'pc': 0x6000, 'opcode': 0xEA, 'operand': [selector & 255, selector >> 8], 'bank_state': {key: initial, key + '_raw': initial}}
                    if value is not None:
                        first['A'] = value
                    records = [first, {'pc': 0x6003, 'opcode': 0xFA, 'operand': [address & 255, address >> 8]}, {'pc': 0x6006, 'opcode': 0xFA, 'operand': [address & 255, address >> 8], 'bank_state': {key: initial}}]
                    events = self.report(records)['events']
                    self.assertEqual(key in events[1].get('bank_state', {}), value is not None)
                    self.assertEqual(key + '_raw' in events[1].get('bank_state', {}), value is not None)
                    self.assertEqual(events[2]['bank_state'][key], initial)

    def test_banked_watch_matches_all_and_only_in_range_bytes(self):
        for watch in ({'watch_symbols': ('Target',)}, {'watch_addresses': ('01:D141',)}):
            for address, bank, count in ((0xD141, 1, 1), (0xD142, 1, 1), (0xD143, 1, 0), (0xD142, 2, 0)):
                with self.subTest(watch=watch, address=address, bank=bank):
                    report = self.report([{'pc': 0x4000, 'opcode': 0xEA, 'operand': [address & 255, address >> 8], 'A': 1, 'bank_state': {'wram': bank}}], watch_size=2, **watch)
                    self.assertEqual(report['watch_write_count'], count)

    def test_typed_bank_provenance_survives_effect_synthesis(self):
        for source, kind, inferred in (('inferred_bank_state.wram', 'inferred_from_io_write', True), ('bank_state.wram', 'runtime_observed', False), ('default_bank_state.wram', 'default', False), ('mapper_bank_state.wram', 'mapper_derived', False)):
            with self.subTest(source=source):
                report = self.report([{'pc': 0x4000, 'opcode': 0xEA, 'operand': [0x41, 0xD1], 'A': 1, 'bank_state_records': [{'name': 'wram', 'value': 1, 'source': source, 'state_kind': kind, 'inferred': inferred}]}])
                event = report['events'][0]
                bank_record = next(r for r in event['bank_state_records'] if r['name'] == 'wram')
                self.assertEqual(bank_record['source'], source)
                self.assertEqual(bank_record['state_kind'], kind)
                self.assertEqual(bank_record['inferred'], inferred)


    def test_summary_counts_finalized_effects_and_watch_hits(self):
        records = [
            {'pc': 0x4000, 'opcode': 0x3E, 'operand': [42]},
            {'pc': 0x4002, 'opcode': 0xEA, 'operand': [65, 209], 'A': 42, 'bank_state': {'wram': 1}},
            {'pc': 0x4005, 'opcode': 0xFA, 'operand': [65, 209], 'A': 42, 'bank_state': {'wram': 1}},
        ]
        report = self.report(records, watch_symbols=('Target',))
        expected = {
            'memory_read_count': 1, 'memory_write_count': 1,
            'register_write_count': 2, 'effect_event_count': 3,
            'watch_hit_count': 2, 'watch_read_count': 1, 'watch_write_count': 1,
            'watch_bank_match_counts': {'exact': 2},
            'post_register_observed_count': 1, 'post_register_match_count': 1,
            'post_register_mismatch_count': 0,
            'effect_proof_status_counts': {'instruction_observed': 12},
            'instruction_observed_effect_count': 12, 'planned_only_effect_count': 0,
            'evidence_source_counts': {'modeled_from_instruction_frame': 12},
            'evidence_status_counts': {'modeled': 12},
        }
        for key, value in expected.items():
            with self.subTest(key=key):
                self.assertEqual(report[key], value)
        limited = self.report(records, watch_symbols=('Target',), max_events=1)
        self.assertEqual(limited['effect_event_count'], 1)
        self.assertEqual(limited['memory_write_count'], 0)
        self.assertEqual(limited['watch_hit_count'], 0)

    def test_empty_trace_keeps_zero_summary_fields(self):
        report = self.report([])
        self.assertTrue(report['valid'])
        for key in ('memory_read_count', 'memory_write_count', 'register_write_count',
                    'watch_hit_count', 'post_register_observed_count',
                    'planned_only_effect_count', 'hardware_side_effect_count',
                    'rmw_pre_state_sample_count', 'unmodeled_observed_change_count'):
            with self.subTest(key=key):
                self.assertEqual(report[key], 0)
        for key in ('effect_proof_status_counts', 'evidence_source_counts',
                    'evidence_status_counts', 'watch_bank_match_counts',
                    'rmw_pre_state_validation_counts'):
            with self.subTest(key=key):
                self.assertEqual(report[key], {})
