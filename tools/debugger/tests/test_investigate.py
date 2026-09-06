from __future__ import annotations

import io
import copy
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.investigate import build_investigation_run
from tools.debugger.next_steps import NEXT_STEP_ROWS, build_next_step
from tools.debugger.report_envelope import sha256_file
from tools.debugger.ranking import rank_findings
from tools.debugger.reporting import build_static_report
from tools.debugger.visualization import build_visualization_report


class InvestigationTests(unittest.TestCase):
    def test_pointer_hypothesis_exports_ordered_replay_citations_only_with_complete_links(self):
        # The existing loop/transport tests own dependency semantics. This public
        # orchestration test checks citation selection from their proved output.
        from tools.debugger.report_envelope import replay_state_basis
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine").mkdir()
            (root / "engine/unit.asm").write_text("Caller:\n\tfarcall Callee\nCallee:\n\tret\n")
            (root / "test.sym").write_text("01:4000 Caller\n01:4100 Callee\n00:3000 Loop\n00:3100 Fill\n00:C000 Target\n")
            rom = bytearray(32768)
            rom[0x147] = 0x10
            (root / "unit.gbc").write_bytes(rom)
            (root / "initial.state").write_bytes(b"state")
            identity = {"rom_sha256": sha256_file(root / "unit.gbc"), "symbols_sha256": sha256_file(root / "test.sym"),
                        "backend": "unit", "backend_sha256": "unit", "state_basis": replay_state_basis(root / "initial.state", 1)}
            candidate = {"source_file": "engine/unit.asm", "source_symbol": "Caller", "source_line": 2,
                         "source_sha256": sha256_file(root / "engine/unit.asm"), "instruction": "farcall Callee"}
            trace = root / "trace.json"
            for mode in ("complete", "gap", "duplicate", "reordered", "wrong_return_stack", "wrong_fill_stack", "missing_fill",
                         "pointer_killed", "input_killed", "pointer_unverified", "input_unverified", "loop_unverified", "missing_iterations", "unexecuted"):
                with self.subTest(mode=mode):
                    pcs = [0x4000, 0x4002, 0x4005, 0x4100, 0x4103, 0x3000, 0x3002, 0x3005, 0x4109, 0x3100, 0x3101, 0x3102, 0x100, 0x4006]
                    opcodes = [0x3E, 0x21, 0xCF, 0x21, 1, 0xA7, 9, 0xC9, 0xCD, 0, 0x22, 0xC9, 0, 0]
                    records = [{"seq": seq, "bank": int(pc >= 0x4000), "pc": pc, "opcode": opcode,
                                "regs": {"A": 1, "B": 0, "C": 2, "D": 0, "E": 0, "H": 0xA0, "L": 0, "F": 0,
                                         "SP": 0xD100 if seq in (0, 1, 2, 13) else 0xD0FC if seq in (9, 10, 11) else 0xD0FE},
                                "watch_values": {"Target": "01"}}
                               for seq, (pc, opcode) in enumerate(zip(pcs, opcodes))]
                    records[8]["operand"] = [0, 0x31]
                    if mode == "gap":
                        records.pop(12)
                    elif mode == "duplicate":
                        records.insert(12, copy.deepcopy(records[12]))
                    elif mode == "reordered":
                        records[11], records[12] = records[12], records[11]
                    elif mode == "wrong_return_stack":
                        records[-1]["regs"]["SP"] -= 2
                    elif mode == "wrong_fill_stack":
                        records[9]["regs"]["SP"] -= 2
                    elif mode == "missing_fill":
                        records[8]["opcode"] = 0
                    trace.write_text(json.dumps(records))
                    capture = {"valid": True, "executed": True, **identity, "trace_sha256": sha256_file(trace),
                               "watches": [{"name": "Target", "found": True}], "trace_output": {"written": True, "path": str(trace)}}
                    detail = {"intervention": {"at": "Callee", "register": "A", "expected": 1, "value": 2}, "consumer_seq": 5,
                              "call_input_change": {"before": "02", "after": "01", "entry_seq": 3, "source_seq": 0},
                              "counted_pointer_loop": {"proof_status": "planned_only" if mode == "loop_unverified" else "instruction_observed", "input_seq": 5, "exit_seq": 7,
                                                       "iterations": 1, "iteration_seqs": [] if mode == "missing_iterations" else [[6]]},
                              "source_candidates": [candidate]}
                    effects = {"valid": True, "events": [{"seq": 0, "bank": 1, "pc": 0x4000, "trace_source": str(trace),
                               "evidence_atoms": [{"claim_type": "diagnosis.hypothesis", "detail": detail}]}]}
                    pointer = {"pointer_write": {"store": {"seq": 10}, "registers": {
                        register: {"proof_status": "planned_only" if mode == "pointer_unverified" else "taint_proven", "depends_on_pointer_base": mode != "pointer_killed"}
                        for register in ("H", "L")}}}
                    def replay(**kwargs):
                        restored = bool(kwargs["interventions"] and kwargs["interventions"][0]["value"] == 2)
                        return {"kind": "unified_debugger_runtime_experiment", "valid": True, "executed": mode != "unexecuted", **identity, "events": [],
                                "interventions": list(kwargs["interventions"]), "final": {"watch_values": {"Target": "02" if restored else "01"}}}
                    mapping = {"valid": True, "kind": "unified_debugger_provenance_report", **identity,
                               "evidence_atoms": [{"claim_type": "provenance.source_mapping", "proof_status": "mirror_passed",
                                                   "precision": {key: candidate[key] for key in ("source_file", "source_symbol", "source_line")}}]}
                    with patch("tools.debugger.investigate.localized_captures", return_value=iter([capture])), \
                         patch("tools.debugger.investigate.build_runtime_state_report", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.build_replay_plan", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.build_effect_trace_report", return_value=effects), \
                         patch("tools.debugger.investigate._register_transport", return_value={"proof_status": "planned_only" if mode == "input_unverified" else "taint_proven", "depends_on_return": mode != "input_killed"}), \
                         patch("tools.debugger.investigate._loop_pointer_write", return_value=pointer), \
                         patch("tools.debugger.investigate.run_runtime_experiment", side_effect=replay), \
                         patch("tools.debugger.investigate.source_mapping_builder", return_value=lambda path: None), \
                         patch("tools.debugger.investigate.build_source_mapping_report", return_value=mapping):
                        result = build_investigation_run(root=root, rom_path="unit.gbc", symbols_path="test.sym", save_state="initial.state",
                                                         execute_watch=True, frames=1, max_cases=1, out_dir=mode,
                                                         expectations=("event=memory_read,symbol=Target,operation=baseline.final,value=02",))
                    self.assertNotIn("diagnosis.root_cause", str(result))
                    atoms = result["evidence_atoms"]
                    if mode == "unexecuted":
                        self.assertEqual(atoms, [])
                        self.assertFalse(result["valid"])
                        self.assertFalse(any("replay_runtime_experiment" in command for command in result["commands"]), result["commands"])
                        continue
                    if mode == "input_killed":
                        self.assertEqual(atoms, [])
                        continue
                    self.assertEqual(len(atoms), 1)
                    rendered = (root / mode / "investigation_report.md").read_text()
                    self.assertLess(rendered.index("Controlled hypotheses"), rendered.index("Highest Priority Findings"))
                    self.assertIn("not a complete root-cause proof", rendered)
                    self.assertEqual(atoms[0]["scope"]["state_basis"], identity["state_basis"])
                    packet = atoms[0]["detail"]
                    self.assertEqual(packet["reproducer"], packet["trials"]["baseline"]["report"])
                    recipe = json.loads(Path(packet["reproducer"]).read_text())
                    contract = json.loads(Path(packet["regression"]).read_text())
                    self.assertEqual(recipe["interventions"], [])
                    self.assertEqual(contract["expectations"], packet["expectations"])
                    self.assertIn(recipe["repro_command"], result["commands"])
                    self.assertIn("replay_runtime_experiment", recipe["repro_command"])
                    self.assertTrue(packet["uncertainty"])
                    observation = atoms[0]["detail"]["observations"][0]
                    if mode == "complete":
                        self.assertEqual(observation["causal_chain"], [{"trace": str(trace), "trace_sha256": sha256_file(trace), "seq": seq}
                                                                     for seq in (0, 1, 3, 5, 6, 9, 13)])
                    else:
                        self.assertNotIn("causal_chain", observation)

    def test_default_rom_ingestion_follows_execution_without_a_saved_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:4000 Caller\n")
            rom = bytearray(32768)
            rom[0x147] = 0x10
            (root / "pokegold.gbc").write_bytes(rom)
            for execute in (False, True):
                with self.subTest(execute=execute), \
                     patch("tools.debugger.investigate.build_replay_plan", return_value={"valid": True}), \
                     patch("tools.debugger.investigate.build_runtime_state_report", return_value={"valid": True}):
                    build_investigation_run(root=root, symbols_path="test.sym", execute_watch=execute,
                                            frames=1, max_targets=1, max_events=1, max_cases=1, out_dir=str(execute))
                    ingest = json.loads((root / str(execute) / "01_ingest.json").read_text())
                    roms = [artifact for artifact in ingest["artifacts"] if artifact["kind"] == "rom"]
                    self.assertEqual(len(roms), int(execute))
                    if execute:
                        self.assertEqual(roms[0]["sha256"], sha256_file(root / "pokegold.gbc"))
                        self.assertEqual(roms[0]["metadata"]["cartridge_type"], "0x10")

    def test_capture_follows_observed_restart_dispatch_within_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine").mkdir()
            (root / "engine/unit.asm").write_text("ParcelCaller:\n\trst $08\n\tret\nVector:\n\tjp Dispatch\nDispatch:\n\tcall Helper\n\tret\nHelper:\n\tret\n")
            (root / "unit.gbc").write_bytes(bytes(32768))
            (root / "test.sym").write_text("01:4000 ParcelCaller\n00:0008 Vector\n00:0100 Dispatch\n00:0110 Helper\n")
            (root / "initial.state").write_bytes(b"fixture")
            for mode, budget in (("restart", 4), ("unobserved", 4), ("stale", 4), ("budget", 2)):
                with self.subTest(mode=mode):
                    captures = []
                    def capture(**kwargs):
                        captures.append(kwargs)
                        path = root / kwargs["out_trace"]
                        path.write_text(json.dumps({"seq": 0, "bank": 1, "pc": 0x4000, "pc_label": "ParcelCaller",
                                                    "opcode": 0 if mode == "unobserved" else 0xCF, "SP": 0xC100}))
                        return {"kind": "unified_debugger_instruction_trace", "valid": True, "executed": True,
                                "trace_output": {"written": True, "path": str(path)},
                                "trace_sha256": "stale" if mode == "stale" else sha256_file(path),
                                "execution_validation": {"hit_function_symbols": ["ParcelCaller"]}}
                    with patch("tools.debugger.investigate.build_instruction_trace_report", side_effect=capture), \
                         patch("tools.debugger.investigate.build_runtime_state_report", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.build_replay_plan", return_value={"valid": True}):
                        report = build_investigation_run(root=root, rom_path="unit.gbc", symbols_path="test.sym", save_state="initial.state",
                                                        symbols=("ParcelCaller",), execute_watch=True, frames=1, out_dir=mode,
                                                        max_targets=budget, max_cases=1)
                    self.assertEqual(report["valid"], mode != "stale", report["errors"])
                    self.assertEqual(len(captures), 1 if mode in ("unobserved", "stale") else 2)
                    if mode == "restart":
                        self.assertEqual(captures[1]["function_symbols"], ("ParcelCaller", "Vector", "Dispatch", "Helper"))
                    if mode == "budget":
                        self.assertEqual(captures[1]["function_symbols"], ("ParcelCaller", "Vector"))
                    self.assertTrue(all(len(capture["function_symbols"]) <= budget for capture in captures))

    def test_supplied_contract_routes_replay_without_symptom_keywords(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("00:C000 wParcelCount\n")
            (root / "unit.gbc").write_bytes(bytes(32768))
            (root / "initial.state").write_bytes(b"state")
            contract = {"type": "event_observed", "event_type": "memory_read", "state_symbol": "wParcelCount",
                        "operation": "baseline.final", "value": "02"}
            (root / "expected.json").write_text(json.dumps(contract))
            for mode in ("cli", "file", "duplicate", "plan", "absent"):
                with self.subTest(mode=mode):
                    trial = {"kind": "unified_debugger_runtime_experiment", "valid": True, "executed": True,
                             "interventions": [], "final": {"watch_values": {"wParcelCount": "01"}}}
                    with patch("tools.debugger.investigate.localized_captures", return_value=iter([])), \
                         patch("tools.debugger.investigate.build_runtime_state_report", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.run_runtime_experiment", return_value=trial), \
                         patch("tools.debugger.replay.build_watch_report", return_value={"valid": True}) as watch:
                        report = build_investigation_run(
                            root=root, rom_path="unit.gbc", symbols_path="test.sym", save_state="initial.state",
                            symptom="parcel total remains unchanged", execute_watch=mode != "plan", frames=1,
                            max_targets=2, max_cases=1, out_dir=mode,
                            watch_symbols=("wParcelCount",) if mode == "duplicate" else (),
                            expectation_files=("expected.json",) if mode in ("file", "duplicate", "plan") else (),
                            expectations=("event=memory_read,symbol=wParcelCount,operation=baseline.final,value=02",) if mode == "cli" else ())
                    replay = json.loads((root / mode / "03_replay.json").read_text())
                    if mode == "absent":
                        self.assertFalse(replay["valid"])
                        self.assertIn("no watchable replay target was found", replay["errors"])
                    else:
                        self.assertTrue(replay["valid"], replay["errors"])
                        self.assertEqual(replay["replay_targets"]["watch_symbols"], ["wParcelCount"])
                        self.assertFalse(report["passed"])
                    self.assertEqual(watch.call_count, 0 if mode in ("plan", "absent") else 1)
                    if watch.called:
                        self.assertEqual(watch.call_args.kwargs["watch_symbols"], ("wParcelCount",))
                    self.assertEqual(json.loads((root / "expected.json").read_text()), contract)

    def test_discriminating_trial_maps_source_once_and_checks_mapping_identity(self):
        from tools.debugger.report_envelope import replay_state_basis
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:4000 Caller\n01:4100 Callee\n01:4006 Caller.check\n00:C000 Target\n")
            (root / "unit.gbc").write_bytes(bytes(32768))
            (root / "initial.state").write_bytes(b"state")
            (root / "trace.json").write_text("[]")
            identity = {"rom_sha256": "rom", "symbols_sha256": "sym", "backend": "unit", "backend_sha256": "unit",
                        "state_basis": replay_state_basis(root / "initial.state", 1)}
            capture = {"kind": "unified_debugger_instruction_trace", "valid": True, "executed": True, **identity,
                       "trace_sha256": sha256_file(root / "trace.json"), "watches": [{"name": "Target", "found": True}],
                       "trace_output": {"written": True, "path": str(root / "trace.json")}}
            (root / "engine").mkdir()
            (root / "engine/unit.asm").write_text("Caller:\n\tcall Callee\n\tret\nCallee:\n\tret\n")
            candidate = {"source_file": "engine/unit.asm", "source_symbol": "Caller", "source_line": 2, "source_sha256": sha256_file(root / "engine/unit.asm"), "instruction": "call Callee"}
            effect = {"valid": True, "kind": "unified_debugger_effect_trace", "events": [{"bank": 1, "pc": 16384, "seq": 4, "trace_source": str(root / "trace.json"), "evidence_atoms": [
                {"claim_type": "diagnosis.hypothesis", "detail": {"intervention": {"at": "Caller+3", "register": "D", "expected": 203, "value": 2},
                 "consumer_seq": 10, "comparison_seq": 11,
                 "call_register_change": {"before": "02", "after": "CB", "entry_seq": 5, "return_seq": 8,
                                          "observed_write_seqs": [6], "direct_continuity_to_consumer": False},
                 "source_candidates": [candidate, candidate]}}]}]}
            incomplete_transport = {"transport_unknown_sram_mapper", "input_changed", "input_gap", "transport_gap", "transport_unknown_bank", "transport_unknown_register", "transport_duplicate",
                                    "transport_order", "transport_missing_seq", "transport_unsupported", "transport_control_gap",
                                    "transport_code_bank", "transport_return_target", "transport_unknown_mapper",
                                    "transport_mapper_identity", "transport_wrong_mapped_bank",
                                    "transport_missing_low", "transport_missing_high", "transport_changed_stack",
                                    "transport_wrong_d", "transport_wrong_e", "transport_wrong_sp"}
            comparison_errors = {"checkpoint_missing_seq", "checkpoint_duplicate_seq", "checkpoint_order", "checkpoint_negative_seq", "checkpoint_bool_seq"}
            sram_mapper_modes = {"transport_mbc3_enable": 0x0000, "transport_mbc3_select": 0x4000, "transport_mbc3_latch": 0x6000}
            pointer_modes = {"input_downstream", "input_downstream_killed", "input_downstream_gap", "input_downstream_absolute", "input_downstream_unknown", "input_downstream_disabled", "input_downstream_mismatch", "input_downstream_context"}
            proven_transport = {*sram_mapper_modes, *pointer_modes, "input_default_rom", "input_immediate", "input_hypothesis", "mapped", "distinct_bad_control", "downstream", "downstream_budget", "transport_mbc3", "transport_mbc3_zero", *comparison_errors}
            for mode in ("input_default_rom", *sorted(pointer_modes), "input_immediate", "input_hypothesis", "input_killed", "mapped", "distinct_bad_control", "control_matches_restore", "downstream", "downstream_budget", *sorted(comparison_errors), "no_contrast", "unavailable", "stale", "failed", "wrong_invariant", "unproven_mapping",
                         "transport_killed", "transport_other_bank", "transport_mbc3", "transport_mbc3_zero", *sram_mapper_modes, *sorted(incomplete_transport)):
                with self.subTest(mode=mode):
                    rom = bytearray(32768)
                    effect["events"] = effect["events"][:1]
                    effect_detail = effect["events"][0]["evidence_atoms"][0]["detail"]
                    effect_detail.pop("call_input_change", None)
                    effect_detail.pop("counted_pointer_loop", None)
                    effect_detail["consumer_seq"] = 8 if mode == "input_immediate" else 10
                    effect_detail["intervention"]["register"] = "A" if mode.startswith("input_") else "D"
                    if mode.startswith("input_"):
                        effect_detail["call_input_change"] = {"before": "02", "after": "CB", "entry_seq": 8,
                                                              "source_seq": 3, "callee_bank": 1, "callee_pc": 0x4100}
                    if mode in pointer_modes:
                        effect_detail["counted_pointer_loop"] = {"proof_status": "instruction_observed", "iterations": 2,
                                                                 "input_seq": 10, "exit_seq": 13, "counter_initial": 2, "stride": 0, "pointer_initial": 0xA010, "pointer_final": 0xA010}
                    effect_detail.pop("comparison_branch", None)
                    if mode in ("mapped", "downstream", "downstream_budget"):
                        effect_detail["comparison_branch"] = {"comparison_seq": 11, "branch_seq": 12, "successor_seq": 13,
                            "condition": "nz", "taken": True, "target": 0x4010, "bank": 1, "flags_hex": "40"}
                    if mode in ("input_default_rom", "transport_mbc3", "transport_mbc3_zero", "transport_mapper_identity", "transport_wrong_mapped_bank") or mode in sram_mapper_modes or mode in pointer_modes - {"input_downstream_unknown"}:
                        rom[0x147] = 0x10
                    (root / "unit.gbc").write_bytes(rom)
                    if mode == "input_default_rom":
                        (root / "pokegold.gbc").write_bytes(rom)
                    identity["rom_sha256"] = "stale-rom" if mode == "transport_mapper_identity" else sha256_file(root / "unit.gbc")
                    capture["rom_sha256"] = identity["rom_sha256"]
                    registers = {"A": 203 if mode.startswith("input_") else 0, "F": 0, "B": 0, "C": 0, "D": 203, "E": 1, "H": 0, "L": 0, "SP": 0xD100}
                    records = [
                        {"seq": 8, "pc": 0x4003, "bank": 1, "opcode": 0xD5, "regs": dict(registers), "bank_state": {"wram": 1}},
                        {"seq": 9, "pc": 0x4004, "bank": 1, "opcode": 0xD1, "regs": {**registers, "SP": 0xD0FE}, "bank_state": {"wram": 1}},
                        {"seq": 10, "pc": 0x4005, "bank": 1, "opcode": 0x7A, "regs": dict(registers), "bank_state": {"wram": 1}},
                    ]
                    records[1]["watch_value_specs"] = [{"address": 0xD0FE, "value_hex": "01"}, {"address": 0xD0FF, "value_hex": "CB"}]
                    if mode == "input_killed":
                        records[1].update(opcode=0x3E, operand=[203])
                        records[2]["pc"] += 1
                    elif mode == "input_gap":
                        records.pop(1)
                    elif mode == "input_changed":
                        records[1]["regs"]["A"] = records[2]["regs"]["A"] = 202
                    if mode in pointer_modes or mode in ("downstream", "downstream_budget"):
                        if mode not in pointer_modes:
                            effect_detail["comparison_branch"]["target"] = 0x400C
                        else:
                            records[-1]["opcode"] = 0xA7
                            effect["events"].append({"seq": 10, "trace_source": str(root / "trace.json"), "pc_label": "Caller.consume", "opcode": 0xA7, "effects": []})
                        records.extend([
                            {"seq": 11, "pc": 0x4006, "bank": 1, "opcode": 0xFE, "operand": [2], "regs": {**registers, "A": 203}},
                            {"seq": 12, "pc": 0x4008, "bank": 1, "opcode": 0x20, "operand": [2], "regs": {**registers, "A": 203, "F": 0x40}},
                            {"seq": 13, "pc": 0x400C, "bank": 1, "opcode": 0x81, "regs": {**registers, "A": 203, "C": 1}},
                            {"seq": 14, "pc": 0x400D, "bank": 1, "opcode": 0xEA, "operand": [0, 0xC0], "regs": {**registers, "A": 204}},
                            {"seq": 15, "pc": 0x4010, "bank": 1, "opcode": 0, "regs": {**registers, "A": 204}},
                        ])
                        for record in records:
                            record["watch_values"] = {"Target": "02" if record["seq"] == 15 else "01"}
                        for seq, label in ((11, "Caller.compare"), (12, "Caller.branch"), (13, "Caller.add"), (14, "Caller.store")):
                            effect["events"].append({"seq": seq, "trace_source": str(root / "trace.json"), "pc_label": label, "opcode": 0x20 if seq == 12 else 0,
                                "effects": [{"access": "register_write", "register": "A", "source_operands": [{"kind": "register", "name": "a"}]}] if seq == 13 else []})
                        if mode in pointer_modes:
                            for record in records:
                                record["regs"].update(H=0xA0, L=0x10)
                            if mode != "input_downstream_context":
                                effect["events"].append({"seq": 9, "trace_source": str(root / "trace.json"), "bank": 1, "pc": 0x4004,
                                                         "known_registers": ["H", "L"], "pre_registers": {"H": "A0", "L": "10"}, "effects": []})
                            store = next(event for event in effect["events"] if event["seq"] == 14)
                            store.update(bank=1, pc=0x400D, opcode=0xEA if mode == "input_downstream_absolute" else 0x22,
                                         known_registers=["H", "L"], pre_registers={"H": "A0", "L": "11" if mode == "input_downstream_mismatch" else "10"},
                                         effects=[{"access": "write", "space": "sram", "bank": 0, "address": 0xA010,
                                                   "sram_enabled": 0 if mode == "input_downstream_disabled" else 1, "value": 204}])
                            raw_store = next(record for record in records if record["seq"] == 14)
                            raw_store.update(opcode=store["opcode"], operand=[0x10, 0xA0] if mode == "input_downstream_absolute" else [])
                            if mode == "input_downstream_killed":
                                next(record for record in records if record["seq"] == 13).update(opcode=0x21, operand=[0x10, 0xA0])
                                raw_store["pc"] = store["pc"] = 0x400F
                            elif mode == "input_downstream_gap":
                                records.remove(next(record for record in records if record["seq"] == 11))
                    if mode in ("transport_missing_low", "transport_missing_high"):
                        records[1]["watch_value_specs"].pop(0 if mode == "transport_missing_low" else 1)
                    elif mode == "transport_changed_stack":
                        records[1]["watch_value_specs"][1]["value_hex"] = "CA"
                        records[2]["regs"]["D"] = 202
                    elif mode in ("transport_wrong_d", "transport_wrong_e", "transport_wrong_sp"):
                        records[2]["regs"][mode.removeprefix("transport_wrong_").upper()] += 1
                    if mode == "transport_killed":
                        records[1].update(opcode=0x16, operand=[203])
                        records[2]["pc"] += 1
                    elif mode == "transport_other_bank":
                        records[1]["bank_state"]["wram"] = 2
                    elif mode == "transport_gap":
                        records.pop(1)
                    elif mode == "transport_unknown_bank":
                        for record in records:
                            record.pop("bank_state")
                    elif mode == "transport_unknown_register":
                        records[1]["regs"].pop("D")
                    elif mode == "transport_duplicate":
                        records.insert(1, records[1])
                    elif mode == "transport_order":
                        records[0], records[1] = records[1], records[0]
                    elif mode == "transport_missing_seq":
                        records[1].pop("seq")
                    elif mode == "transport_unsupported":
                        records[1]["opcode"] = 0xD3
                    elif mode == "transport_control_gap":
                        records[1]["pc"] = 0x5000
                    elif mode == "transport_code_bank":
                        records[1]["bank"] = 2
                    elif mode == "transport_return_target":
                        records[1]["opcode"] = 0xC9
                    elif mode in ("transport_mbc3", "transport_mbc3_zero", "transport_unknown_mapper", "transport_mapper_identity", "transport_wrong_mapped_bank"):
                        registers["A"] = 0 if mode == "transport_mbc3_zero" else 2
                        records[0].update(pc=0x100, bank=0, opcode=0xEA, operand=[0, 0x20], regs=dict(registers))
                        records[1].update(pc=0x103, bank=0, opcode=0xC3, operand=[5, 0x40], regs=dict(registers))
                        records[2]["bank"] = 1 if mode == "transport_mbc3_zero" else 3 if mode == "transport_wrong_mapped_bank" else 2
                    elif mode in sram_mapper_modes or mode == "transport_unknown_sram_mapper":
                        address = sram_mapper_modes.get(mode, 0x4000)
                        records[0].update(pc=0x100, bank=0, opcode=0xEA, operand=[address & 255, address >> 8], regs=dict(registers))
                        records[1].update(pc=0x103, bank=0, opcode=0xC3, operand=[5, 1], regs=dict(registers))
                        records[2].update(pc=0x105, bank=0)
                    (root / "trace.json").write_text(json.dumps(records))
                    capture["trace_sha256"] = sha256_file(root / "trace.json")
                    def replay(**kwargs):
                        restored = bool(kwargs["interventions"] and kwargs["interventions"][0]["value"] == 2)
                        events = [{"seq": 0, "bank": 1, "pc": 16390, "targets": ["Caller.check"],
                                   "registers": {"register_d": "02" if restored and mode != "wrong_invariant" else "CB"}}]
                        if mode == "downstream":
                            for value in (["04"] if restored else ["04", "02"]):
                                events.append({"seq": len(events), "bank": 1, "pc": 0x400C, "targets": ["Caller.add"],
                                               "registers": {"register_c": value, "register_a": "00"},
                                               "after_registers": {"register_c": value, "register_a": "00"}})
                            events.append({"seq": len(events), "bank": 2, "pc": 0x400C, "targets": ["Other.add"],
                                           "registers": {"register_c": "99"} if not kwargs["interventions"] or restored else {}})
                            events.append({"seq": len(events), "bank": 3, "pc": 0x400C, "targets": ["Other.check"],
                                           "registers": {"register_c": "88"}, "after_registers": {"register_a": "02" if restored else "01"},
                                           "watch_values": {"Target": "02" if restored else "01"}})
                            if not restored:
                                events.append({"seq": len(events), "bank": 1, "pc": 0x4011, "targets": ["Caller.side"],
                                               "registers": {"register_c": "10"}})
                        if mode in comparison_errors:
                            events.append({"seq": 1, "bank": 1, "pc": 0x4007, "targets": ["Caller.extra"], "registers": {}})
                            if mode == "checkpoint_missing_seq":
                                events[0].pop("seq")
                            elif mode == "checkpoint_duplicate_seq":
                                events[1]["seq"] = 0
                            elif mode == "checkpoint_negative_seq":
                                events[0]["seq"] = -1
                            elif mode == "checkpoint_bool_seq":
                                events[0]["seq"] = False
                            else:
                                events[0]["seq"], events[1]["seq"] = 1, 0
                        final_value = "02" if restored and mode != "no_contrast" else "01"
                        if kwargs["interventions"] and not restored:
                            if mode == "distinct_bad_control":
                                final_value = "03"
                            elif mode == "control_matches_restore":
                                final_value = "02"
                        return {"kind": "unified_debugger_runtime_experiment", "valid": True, "executed": True, "errors": [], **identity,
                                "interventions": list(kwargs["interventions"]),
                                "events": events,
                                "final": {"watch_values": {"Target": final_value}}}
                    mapping = {"kind": "unified_debugger_provenance_report", "valid": mode != "failed",
                               "errors": ["build failed"] if mode == "failed" else [],
                               "rom_sha256": "other" if mode == "stale" else identity["rom_sha256"], "symbols_sha256": "sym", "evidence_atoms": [{
                                   "claim_type": "provenance.source_mapping", "proof_status": "planned_only" if mode == "unproven_mapping" else "mirror_passed",
                                   "precision": {key: candidate[key] for key in ("source_file", "source_symbol", "source_line")},
                                   "detail": {"source_sha256": candidate["source_sha256"]}}]}
                    with patch("tools.debugger.investigate.localized_captures", return_value=iter([capture])) as captures, \
                         patch("tools.debugger.investigate.build_runtime_state_report", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.build_replay_plan", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.build_effect_trace_report", return_value=effect), \
                         patch("tools.debugger.investigate.run_runtime_experiment", side_effect=replay) as replay_call, \
                         patch("tools.debugger.investigate.source_mapping_builder", return_value=None if mode == "unavailable" else lambda path: None), \
                         patch("tools.debugger.investigate.build_source_mapping_report", return_value=mapping) as map_call:
                        report = build_investigation_run(rom_path="" if mode == "input_default_rom" else "unit.gbc", symbols_path="test.sym", save_state="initial.state", execute_watch=True,
                                                        frames=1, max_cases=1, max_targets=3 if mode == "downstream_budget" else 24, out_dir=mode, root=root,
                                                        expectations=("event=memory_read,symbol=Target,operation=baseline.final,value=02",
                                                                      "event=control_flow,pc_symbol=Caller.check,operation=baseline.checkpoint.register_d,value=02"))
                    self.assertEqual(replay_call.call_count, 4)
                    self.assertIn("Target", captures.call_args.kwargs["watch_symbols"])
                    for call in replay_call.call_args_list[1:]:
                        extra = ("Caller.consume", "Caller.branch", "Caller.store", "Caller.add") if mode in pointer_modes else ("Caller.compare", "Caller.branch", "Caller.add", "Caller.store") if mode == "downstream" else ("Caller.compare",) if mode == "downstream_budget" else ()
                        self.assertEqual(call.kwargs["observe"], ("Caller+3", "Caller.check", *extra))
                    for trial_mode in ("baseline", "restore", "control"):
                        check = json.loads((root / mode / f"04_trial_1_{trial_mode}_expect.json").read_text())
                        self.assertTrue(check["valid"], check["errors"])
                        self.assertEqual(check["passed"], trial_mode == "restore" and mode not in ("no_contrast", "wrong_invariant"), check["expectations"])
                        self.assertEqual(check["expectation_count"], 2)
                    self.assertFalse(report["passed"])
                    self.assertEqual(map_call.call_count, 0 if mode in ("input_killed", "no_contrast", "control_matches_restore", "unavailable", "transport_killed", "transport_other_bank") else 1)
                    saved_effects = json.loads((root / mode / "04_capture_effects.json").read_text())
                    saved_transport = saved_effects["events"][0]["evidence_atoms"][0]["detail"]["register_transport"]
                    if mode in ("transport_killed", "transport_other_bank"):
                        self.assertIs(saved_transport["depends_on_return"], False)
                    if mode == "input_killed":
                        self.assertIs(saved_transport["depends_on_entry"], False)
                    self.assertEqual(report["valid"], mode not in ("stale", "failed"), report["errors"])
                    if map_call.call_count:
                        self.assertEqual(map_call.call_args.kwargs["candidate"], candidate)
                        self.assertEqual((map_call.call_args.kwargs["bank"], map_call.call_args.kwargs["pc"]), (1, 16384))
                    self.assertNotIn("diagnosis.root_cause", str(report))
                    hypotheses = report["evidence_atoms"]
                    self.assertEqual(len(hypotheses), 1 if mode in proven_transport or mode in incomplete_transport else 0)
                    if hypotheses:
                        atom = hypotheses[0]
                        comparison = atom["detail"]["checkpoint_comparison"]
                        if mode in comparison_errors:
                            self.assertTrue(comparison["errors"])
                            self.assertEqual(comparison.get("checkpoints", []), [])
                        else:
                            self.assertEqual(comparison.get("errors", []), [])
                            self.assertEqual(comparison["checkpoints"][0]["differences"]["registers"]["register_d"],
                                             {"baseline": [{"seq": 0, "value": "CB"}], "restore": [{"seq": 0, "value": "02"}], "control": [{"seq": 0, "value": "CB"}]})
                        if mode == "downstream":
                            points = {(point["bank"], point["pc"]): point for point in comparison["checkpoints"]}
                            self.assertEqual(points[1, 0x400C]["hit_counts"], {"baseline": 2, "restore": 1, "control": 2})
                            self.assertNotIn("register_a", points[1, 0x400C]["differences"]["registers"])
                            self.assertNotIn("after_registers", points[1, 0x400C]["differences"])
                            self.assertEqual(points[1, 0x400C]["seqs"], {"baseline": [1, 2], "restore": [1], "control": [1, 2]})
                            self.assertEqual(points[1, 0x400C]["differences"]["registers"]["register_c"],
                                             {"baseline": [{"seq": 1, "value": "04"}, {"seq": 2, "value": "02"}],
                                              "restore": [{"seq": 1, "value": "04"}], "control": [{"seq": 1, "value": "04"}, {"seq": 2, "value": "02"}]})
                            self.assertEqual(points[2, 0x400C]["hit_counts"], {"baseline": 1, "restore": 1, "control": 1})
                            self.assertEqual(points[2, 0x400C]["differences"]["registers"]["register_c"],
                                             {"baseline": [{"seq": 3, "value": "99"}], "restore": [{"seq": 2, "value": "99"}], "control": [{"seq": 3}]})
                            self.assertEqual(points[1, 0x4011]["hit_counts"], {"baseline": 1, "restore": 0, "control": 1})
                            self.assertEqual(points[1, 0x4011]["seqs"].get("restore", []), [])
                            self.assertNotIn("registers", points[3, 0x400C]["differences"])
                            expected_values = {"baseline": [{"seq": 4, "value": "01"}], "restore": [{"seq": 3, "value": "02"}], "control": [{"seq": 4, "value": "01"}]}
                            self.assertEqual(points[3, 0x400C]["differences"]["after_registers"]["register_a"], expected_values)
                            self.assertEqual(points[3, 0x400C]["differences"]["watch_values"]["Target"], expected_values)
                        self.assertEqual(atom["claim_type"], "diagnosis.hypothesis")
                        self.assertEqual(atom["precision"], mapping["evidence_atoms"][0]["precision"])
                        for key in ("rom_sha256", "symbols_sha256", "backend", "backend_sha256"):
                            self.assertEqual(atom["scope"][key], identity[key])
                        self.assertEqual(atom["scope"]["state_basis"]["input_log_sha256"], identity["state_basis"]["input_log_sha256"])
                        observation = dict(atom["detail"]["observations"][0])
                        transport = observation.pop("register_transport")
                        if mode == "input_default_rom":
                            self.assertEqual(transport["mapper"], "MBC3")
                            ingested = json.loads((root / mode / "01_ingest.json").read_text())
                            rom_artifact, = [item for item in ingested["artifacts"] if item["kind"] == "rom"]
                            self.assertEqual(rom_artifact["sha256"], identity["rom_sha256"])
                        if mode in ("mapped", "downstream", "downstream_budget"):
                            self.assertEqual(observation.pop("comparison_branch"), effect_detail["comparison_branch"])
                        self.assertEqual(transport["proof_status"], "taint_proven" if mode in proven_transport else "planned_only")
                        if mode in proven_transport:
                            self.assertTrue(transport["depends_on_entry" if mode.startswith("input_") else "depends_on_return"])
                            self.assertEqual([step["seq"] for step in transport.get("transfers", [])], [] if mode == "input_immediate" or mode in sram_mapper_modes else [8] if mode in ("transport_mbc3", "transport_mbc3_zero") else [8, 9])
                            if mode in sram_mapper_modes:
                                self.assertEqual(transport["mapper"], "MBC3")
                            if mode in ("transport_mbc3", "transport_mbc3_zero"):
                                self.assertEqual(transport["mapper"], "MBC3")
                                self.assertEqual(transport["transfers"][0]["rom_bank_after"], 1 if mode == "transport_mbc3_zero" else 2)
                        else:
                            self.assertNotIn("depends_on_return", transport)
                            self.assertTrue(transport["errors"])
                        expected_observation = {"trace": str(root / "trace.json"), "trace_sha256": sha256_file(root / "trace.json"), "seq": 4, "consumer_seq": effect_detail["consumer_seq"], "comparison_seq": 11,
                            "call_register_change": {"before": "02", "after": "CB", "entry_seq": 5, "return_seq": 8,
                                                     "observed_write_seqs": [6], "direct_continuity_to_consumer": False}}
                        if mode.startswith("input_"):
                            expected_observation.pop("call_register_change")
                            expected_observation.pop("comparison_seq")
                            expected_observation["call_input_change"] = effect_detail["call_input_change"]
                            self.assertEqual(atom["detail"]["intervention"]["register"], "A")
                            self.assertNotIn("depends_on_return", transport)
                            self.assertNotIn("register_depends_on_return", str(transport))
                        if mode in pointer_modes:
                            expected_observation["counted_pointer_loop"] = effect_detail["counted_pointer_loop"]
                            if mode in ("input_downstream", "input_downstream_killed", "input_downstream_gap"):
                                pointer_write = observation.pop("pointer_write")
                                self.assertEqual(pointer_write["context_seq"], 9)
                                self.assertEqual(pointer_write["store"]["seq"], 14)
                                self.assertEqual(pointer_write["store"]["address"], 0xA010)
                                for register in ("H", "L"):
                                    proof = pointer_write["registers"][register]
                                    if mode == "input_downstream_gap":
                                        self.assertEqual(proof["proof_status"], "planned_only")
                                        self.assertNotIn("depends_on_pointer_base", proof)
                                        self.assertTrue(proof["errors"])
                                    else:
                                        self.assertEqual(proof["depends_on_pointer_base"], mode == "input_downstream")
                                        self.assertEqual(proof["proof_status"], "taint_proven")
                                self.assertNotIn("depends_on_return", str(pointer_write))
                        self.assertEqual(observation, expected_observation)
                        self.assertEqual(atom["detail"]["source_sha256"], candidate["source_sha256"])
                        for trial in atom["detail"]["trials"].values():
                            self.assertTrue(Path(trial["report"]).is_file())
                            self.assertTrue(Path(trial["expectation_report"]).is_file())
                            self.assertEqual(trial["report_sha256"], sha256_file(trial["report"]))
                            self.assertEqual(trial["expectation_report_sha256"], sha256_file(trial["expectation_report"]))
                        self.assertEqual(atom["detail"]["source_mapping_sha256"], sha256_file(atom["source_report"]))

    def test_baseline_duration_reduction_preserves_failure_and_checks_each_shorter_window(self):
        from tools.debugger.report_envelope import replay_state_basis
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:4000 Caller.shift\n00:C000 Target\n")
            (root / "unit.gbc").write_bytes(bytes(32768))
            (root / "initial.state").write_bytes(b"state")
            for mode in ("first", "second", "limit", "identity", "symbols_identity", "backend_identity", "state_identity", "unreached", "initial", "event", "error", "unexecuted", "zero_budget", "original_minimum"):
                with self.subTest(mode=mode):
                    baseline_frames = 2 if mode == "original_minimum" else 7
                    identity_error = mode.endswith("identity")
                    def replay(**kwargs):
                        duration = kwargs["frames"]
                        report = {"kind": "unified_debugger_runtime_experiment", "valid": True, "executed": True,
                                  "frames": duration, "interventions": [], "errors": [],
                                  "rom_sha256": "rom", "symbols_sha256": "sym", "backend": "unit", "backend_sha256": "unit",
                                  "state_basis": replay_state_basis(root / "initial.state", duration),
                                  "initial": {"watch_values": {"Target": "00"}},
                                  "final": {"watch_values": {"Target": "01"}},
                                  "events": [{"bank": 1, "pc": 16384, "targets": ["Caller.shift"], "registers": {"register_d": "01"}}]}
                        if duration < baseline_frames:
                            if mode in ("limit", "original_minimum") or mode == "second" and duration == 1:
                                report["final"]["watch_values"]["Target"] = "02"
                            elif identity_error:
                                key = {"identity": "rom_sha256", "symbols_identity": "symbols_sha256",
                                       "backend_identity": "backend_sha256", "state_identity": "state_basis"}[mode]
                                report[key] = "different"
                            elif mode == "error":
                                report.update(valid=False, errors=["runtime experiment failed"])
                            elif mode == "unexecuted":
                                report["executed"] = False
                            elif duration == 1 and mode == "unreached":
                                report.update(valid=False, events=[], errors=["checkpoint not reached: Caller.shift"])
                            elif duration == 1 and mode == "initial":
                                report["initial"]["watch_values"]["Target"] = "FF"
                            elif duration == 1 and mode == "event":
                                report["events"][0]["registers"]["register_d"] = "02"
                        return report
                    with patch("tools.debugger.investigate.localized_captures", return_value=iter([])), \
                         patch("tools.debugger.investigate.build_runtime_state_report", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.build_replay_plan", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.run_runtime_experiment", side_effect=replay) as run:
                        report = build_investigation_run(rom_path="unit.gbc", symbols_path="test.sym", save_state="initial.state",
                                                        execute_watch=True, frames=baseline_frames, max_cases=0 if mode == "zero_budget" else 2, out_dir=mode,
                                                        expectations=("event=memory_read,symbol=Target,operation=baseline.final,value=02",), root=root)
                    self.assertFalse(report["passed"])
                    self.assertEqual(report["valid"], not identity_error, report["errors"])
                    minimum = json.loads((root / mode / "10_minimize.json").read_text())
                    retained = identity_error or mode in ("limit", "error", "unexecuted", "zero_budget", "original_minimum")
                    self.assertEqual(minimum["frames"], baseline_frames if retained else 1 if mode == "first" else 2)
                    self.assertEqual(minimum["validation"]["minimal_positive_window"],
                                     not identity_error and mode not in ("limit", "error", "unexecuted", "zero_budget"))
                    if identity_error:
                        self.assertNotIn("repro_command", minimum)
                    expected_calls = [baseline_frames] if mode == "zero_budget" else [baseline_frames, 1]
                    if not identity_error and mode not in ("first", "error", "unexecuted", "zero_budget", "original_minimum"):
                        expected_calls.append(2)
                    self.assertEqual([call.kwargs["frames"] for call in run.call_args_list], expected_calls)
                    self.assertEqual(len(minimum["validation"]["attempts"]), len(expected_calls) - 1)
                    for attempt in minimum["validation"]["attempts"]:
                        saved = json.loads(Path(attempt["report"]).read_text())
                        self.assertEqual(saved["frames"], attempt["frames"])
                    original = json.loads(Path(minimum["validation"]["reference_report"]).read_text())
                    self.assertEqual(original["frames"], baseline_frames)
                    self.assertEqual(minimum["final"]["watch_values"]["Target"], "01")

    def test_expected_baseline_runs_without_a_hypothesis_and_preserves_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:4000 Caller.shift\n00:C000 Target\n")
            (root / "unit.gbc").write_bytes(bytes(32768))
            (root / "initial.state").write_bytes(b"state")
            expected = {"expectations": [
                {"type": "event_observed", "event_type": "memory_read", "symbol": "Target", "operation": "baseline.final", "value": "02"},
                {"type": "event_observed", "event_type": "control_flow", "pc_symbol": "Caller.shift", "operation": "baseline.checkpoint.register_d", "value": "02"}]}
            (root / "expected.json").write_text(json.dumps(expected))
            for mode in ("correct", "cli", "broken", "plan", "missing_contract"):
                with self.subTest(mode=mode):
                    value = "01" if mode == "broken" else "02"
                    trial = {"kind": "unified_debugger_runtime_experiment", "valid": True, "executed": True,
                             "interventions": [], "initial": {"watch_values": {"Target": "00"}},
                             "final": {"watch_values": {"Target": value}}, "events": [
                                 {"bank": 1, "pc": 16384, "targets": ["Caller.shift"], "registers": {"register_d": value}}]}
                    with patch("tools.debugger.investigate.localized_captures", return_value=iter([])), \
                         patch("tools.debugger.investigate.build_runtime_state_report", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.build_replay_plan", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.run_runtime_experiment", return_value=trial) as run:
                        report = build_investigation_run(rom_path="unit.gbc", symbols_path="test.sym", save_state="initial.state",
                                                        execute_watch=mode != "plan", frames=1, max_cases=1,
                                                        expectation_files=() if mode == "cli" else ("missing.json" if mode == "missing_contract" else "expected.json",),
                                                        expectations=("event=memory_read,symbol=Target,operation=baseline.final,value=02",
                                                                      "event=control_flow,pc_symbol=Caller.shift,operation=baseline.checkpoint.register_d,value=02") if mode == "cli" else (),
                                                        out_dir=mode, root=root)
                    self.assertEqual(report["passed"], mode in ("correct", "cli"))
                    self.assertEqual(run.call_count, 0 if mode in ("plan", "missing_contract") else 1)
                    if run.call_count:
                        self.assertEqual(run.call_args.kwargs["observe"], ("Caller.shift",))
                        self.assertEqual(run.call_args.kwargs["watch_symbols"], ("Target",))
                        self.assertEqual(run.call_args.kwargs["interventions"], ())
                        self.assertTrue(report["valid"], report["errors"])
                        recorded = json.loads((root / mode / "04_expected_baseline.json").read_text())
                        self.assertTrue(recorded["validation"]["minimal_positive_window"])
                        self.assertIn("tools.audit.replay_runtime_experiment", recorded["repro_command"])
                        minimum = json.loads((root / mode / "10_minimize.json").read_text())
                        self.assertEqual(minimum["final"], trial["final"])
                    self.assertNotIn("diagnosis.root_cause", str(report))

    def test_changed_or_unexecuted_capture_stops_before_effects_and_interventions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:4000 Caller\n")
            (root / "unit.gbc").write_bytes(bytes(32768))
            (root / "initial.state").write_bytes(b"state")
            trace = root / "trace.json"
            for mode in ("changed", "truncated", "missing", "no_hash", "plan", "failed", "failed_after_valid"):
                with self.subTest(mode=mode):
                    trace.write_text('[{"seq":0,"opcode":0}]')
                    capture = {"kind": "unified_debugger_instruction_trace", "valid": True,
                               "executed": True, "errors": [], "trace_sha256": sha256_file(trace),
                               "trace_output": {"written": True, "path": str(trace)}}
                    if mode == "changed":
                        trace.write_text('[{"seq":0,"opcode":1}]')
                    elif mode == "truncated":
                        trace.write_text('[')
                    elif mode == "missing":
                        trace.unlink()
                    elif mode == "no_hash":
                        del capture["trace_sha256"]
                    elif mode == "plan":
                        capture["executed"] = False
                    else:
                        capture["valid"] = False
                    captures = [capture, capture]
                    if mode == "failed_after_valid":
                        captures.insert(0, {**capture, "valid": True, "errors": []})
                    with patch("tools.debugger.investigate.localized_captures", return_value=iter(captures)), \
                         patch("tools.debugger.investigate.build_runtime_state_report", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.build_replay_plan", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.build_effect_trace_report", return_value={"valid": True, "events": []}) as effects, \
                         patch("tools.debugger.investigate.run_runtime_experiment") as replay:
                        report = build_investigation_run(rom_path="unit.gbc", symbols_path="test.sym",
                                                        save_state="initial.state", execute_watch=True,
                                                        max_cases=1, out_dir=mode, root=root)
                    self.assertFalse(report["valid"])
                    self.assertIn("captured trace", str(report["errors"]))
                    effects.assert_not_called()
                    replay.assert_not_called()
                    stopped_index = 3 if mode == "failed_after_valid" else 2
                    self.assertFalse((root / mode / f"04_capture_{stopped_index}.json").exists())

    def test_one_frame_reproducer_requires_all_reference_observations(self):
        from tools.debugger.report_envelope import replay_state_basis

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:4000 Caller\n01:C000 Target\n")
            (root / "unit.gbc").write_bytes(bytes(32768))
            (root / "initial.state").write_bytes(b"state")
            (root / "trace.json").write_text("[]")
            identity = {"rom_sha256": "rom", "symbols_sha256": "sym", "backend": "unit", "backend_sha256": "binary"}
            capture = {"valid": True, "kind": "unified_debugger_instruction_trace", **identity,
                       "state_basis": replay_state_basis(root / "initial.state", 7),
                       "watches": [{"name": "Target", "found": True}],
                       "executed": True, "trace_sha256": sha256_file(root / "trace.json"),
                       "trace_output": {"written": True, "path": str(root / "trace.json")}}
            effect = {"valid": True, "kind": "unified_debugger_effect_trace", "events": [{"evidence_atoms": [
                {"claim_type": "diagnosis.hypothesis", "detail": {"intervention":
                    {"at": "Caller", "register": "D", "expected": 203, "value": 2}}}]}]}
            for mismatch in ("none", "watch", "event", "identity", "missing", "unexecuted"):
                with self.subTest(mismatch=mismatch):
                    def replay(**kwargs):
                        value = kwargs["interventions"][0]["value"] if kwargs["interventions"] else 203
                        result = {"valid": True, "executed": True, "kind": "unified_debugger_runtime_experiment",
                                  "errors": [], **identity, "state_basis": replay_state_basis(root / "initial.state", kwargs["frames"]),
                                  "interventions": list(kwargs["interventions"]), "events": [{"value": value}],
                                  "initial": {"watch_values": {"Target": "00"}},
                                  "final": {"watch_values": {"Target": "02" if value == 2 else "01"}}}
                        if mismatch == "missing":
                            result["events"] = []
                        if kwargs["frames"] == 1:
                            if mismatch == "watch":
                                result["final"]["watch_values"]["Target"] = "FF"
                            elif mismatch == "event":
                                result["events"] = [{"value": 99}]
                            elif mismatch == "identity":
                                result["state_basis"]["initial_state_sha256"] = "different"
                            elif mismatch == "unexecuted":
                                result["executed"] = False
                        return result

                    with patch("tools.debugger.investigate.localized_captures", return_value=iter([capture])), \
                         patch("tools.debugger.investigate.build_runtime_state_report", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.build_replay_plan", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.build_effect_trace_report", return_value=effect), \
                         patch("tools.debugger.investigate.run_runtime_experiment", side_effect=replay) as run:
                        report = build_investigation_run(rom_path="unit.gbc", symbols_path="test.sym", save_state="initial.state",
                                                        execute_watch=True, frames=7, max_cases=1, out_dir=mismatch, root=root)
                    paths = sorted((root / mismatch).glob("04_short_*.json"))
                    self.assertEqual(run.call_count, 6 if mismatch == "none" else 3 if mismatch == "missing" else 4)
                    self.assertEqual(len(paths), 3 if mismatch == "none" else 0 if mismatch == "missing" else 1)
                    for path in paths:
                        short = json.loads(path.read_text())
                        self.assertEqual(short["validation"]["minimal_positive_window"], mismatch == "none")
                        if short["valid"]:
                            self.assertIn("tools.audit.replay_runtime_experiment", short["repro_command"])
                        else:
                            self.assertNotIn("repro_command", short)
                    if mismatch in ("identity", "unexecuted"):
                        self.assertFalse(report["valid"])

    def test_inferred_consumer_trial_runs_baseline_before_restoration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine").mkdir()
            (root / "engine" / "unit.asm").write_text("Caller:\n; Parcel nickname.\n\tcall Callee\n\tret\nCallee:\n\tret\n")
            (root / "test.sym").write_text("01:4000 Caller\n01:4100 Callee\n01:C000 Target\n")
            (root / "test.gbc").write_bytes(bytes(32768))
            (root / "state").write_bytes(b"fixture")
            records = [
                {"seq": 0, "bank": 1, "pc": 0x4000, "pc_label": "Caller", "opcode": 0xCD, "operand": [0, 0x41], "D": 2, "SP": 0xD100},
                {"seq": 1, "bank": 1, "pc": 0x4100, "opcode": 0x16, "operand": [203], "D": 2, "SP": 0xD0FE},
                {"seq": 2, "bank": 1, "pc": 0x4102, "opcode": 0xC9, "D": 203, "SP": 0xD0FE},
                {"seq": 3, "bank": 1, "pc": 0x4003, "pc_label": "Caller+0x3", "opcode": 0x7A, "D": 203, "SP": 0xD100},
                {"seq": 4, "bank": 1, "pc": 0x4004, "opcode": 0xFE, "operand": [2], "A": 203, "D": 203, "SP": 0xD100},
            ]
            (root / "capture.json").write_text(json.dumps(records))
            capture = {"valid": True, "kind": "unified_debugger_instruction_trace",
                       "watches": [{"name": "Target", "found": True}],
                       "trace_output": {"written": True, "path": str(root / "capture.json")}}
            identity = {"rom_sha256": "rom", "symbols_sha256": "symbols", "state_basis": {"initial_state_sha256": "state"},
                        "backend": "test emulator", "backend_sha256": "emulator binary"}
            capture.update(identity)
            cases = [(True, "", 2, 203), (False, "", 2, 203),
                     *((True, key, 2, 203) for key in identity), (True, "", 0, 1), (True, "", 255, 0)]
            for baseline_valid, stale_key, prior, observed in cases:
                with self.subTest(baseline_valid=baseline_valid, stale_key=stale_key, prior=prior):
                    records[0]["D"] = records[1]["D"] = prior
                    records[1]["operand"] = [observed]
                    records[2]["D"] = records[3]["D"] = records[4]["D"] = records[4]["A"] = observed
                    records[4]["operand"] = [prior]
                    (root / "capture.json").write_text(json.dumps(records))
                    capture["executed"] = True
                    capture["trace_sha256"] = sha256_file(root / "capture.json")
                    replay = {"valid": baseline_valid, "executed": True, "errors": [] if baseline_valid else ["unreached"], **identity}
                    if stale_key:
                        replay[stale_key] = "different"
                    with patch("tools.debugger.investigate.localized_captures", return_value=iter([capture, capture])), \
                         patch("tools.debugger.investigate.build_runtime_state_report", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.build_replay_plan", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.run_runtime_experiment", return_value=replay) as run:
                        report = build_investigation_run(
                            symptom="parcel nickname", rom_path="test.gbc", symbols_path="test.sym", save_state="state",
                            execute_watch=True, max_targets=4, max_events=32, max_cases=1, frames=7, out_dir="run", root=root)
                    self.assertEqual(run.call_count, 3 if baseline_valid and not stale_key else 1)
                    self.assertEqual(run.call_args_list[0].kwargs["interventions"], ())
                    self.assertEqual(run.call_args_list[0].kwargs["watch_symbols"], ("Target",))
                    if baseline_valid and not stale_key:
                        self.assertTrue(report["valid"], report["errors"])
                        self.assertEqual(run.call_args_list[1].kwargs["interventions"],
                                         ({"at": "Caller+0x3", "register": "D", "expected": observed, "value": prior},))
                        control = run.call_args_list[2].kwargs["interventions"][0]
                        self.assertEqual(control["at"], "Caller+0x3")
                        self.assertEqual(control["expected"], observed)
                        self.assertNotIn(control["value"], (prior, observed))
                        self.assertTrue(0 <= control["value"] <= 255)
                    else:
                        self.assertFalse(report["valid"])
                    self.assertNotIn("diagnosis.root_cause", str(report))

    def test_execution_follows_retrieved_code_then_observed_callees(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine").mkdir()
            (root / "test.sym").write_text("01:4000 RestoreParcel\n01:4100 CopyParcel\n01:4200 ParcelText\n01:C000 wParcelCount\n")
            (root / "test.gbc").write_bytes(bytes(32768))
            (root / "before.state").write_bytes(b"fixture")
            (root / "engine" / "storage.asm").write_text(
                "RestoreParcel:\n; Withdraw parcel nickname.\n\tcall CopyParcel\n\tret\n"
                "CopyParcel:\n\tld a, [wParcelCount]\n\tret\n"
                "ParcelText:\n; Withdraw parcel nickname.\n\tdb 0\n")
            runs = []

            def capture(**kwargs):
                runs.append(kwargs)
                trace = Path(kwargs["out_trace"])
                if not trace.is_absolute():
                    trace = root / trace
                trace.write_text(json.dumps({"event_type": "instruction", "opcode": 0, "pc_label": kwargs["function_symbols"][0],
                                             "bank": 1, "pc": 16384, "seq": 0}) + "\n")
                return {"kind": "unified_debugger_instruction_trace", "valid": True,
                        "executed": True, "errors": [], "functions": [], "trace_sha256": sha256_file(trace),
                        "execution_validation": {"hit_function_symbols": list(kwargs["function_symbols"])},
                        "trace_output": {"written": True, "path": str(trace)}}

            with patch("tools.debugger.investigate.build_instruction_trace_report", side_effect=capture), \
                 patch("tools.debugger.investigate.build_runtime_state_report", return_value={"valid": True}), \
                 patch("tools.debugger.investigate.build_replay_plan", return_value={"valid": True}):
                report = build_investigation_run(
                    symptom="withdraw parcel nickname at 1 hp", rom_path="test.gbc", symbols_path="test.sym",
                    save_state="before.state", execute_watch=True, out_dir="run", max_targets=4,
                    max_events=32, max_cases=1, frames=7, root=root)
            self.assertTrue(report["valid"], report["errors"])
            self.assertEqual(len(runs), 2)
            self.assertEqual(runs[0]["function_symbols"], ("RestoreParcel",))
            self.assertIn("CopyParcel", runs[1]["function_symbols"])
            self.assertTrue(all("ParcelText" not in run["function_symbols"] for run in runs))
            self.assertIn("wParcelCount", runs[1]["watch_symbols"])
            self.assertTrue(all(run["frames"] == 7 and run["max_frames"] == 32 for run in runs))
            self.assertEqual((root / "before.state").read_bytes(), b"fixture")
            index = json.loads((root / "run" / "04_capture_index.json").read_text())
            self.assertGreater(index["event_count"], 0)
            effects = json.loads((root / "run" / "04_capture_effects.json").read_text())
            self.assertEqual(len(effects["events"]), 2)
            self.assertFalse([atom for atom in report.get("evidence_atoms", [])
                              if atom.get("claim_type") == "diagnosis.root_cause"])

    def test_capture_stops_on_missing_hits_failure_or_trial_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine").mkdir()
            (root / "test.sym").write_text("\n".join(f"01:{0x4000+i*32:04x} Parcel{i}" for i in range(6)))
            (root / "test.gbc").write_bytes(bytes(32768))
            (root / "before.state").write_bytes(b"fixture")
            (root / "engine" / "storage.asm").write_text(
                "Parcel0:\n; Withdraw nickname.\n\tcall Parcel1\n\tret\n" +
                "\n".join(f"Parcel{i}:\n\tcall Parcel{i+1}\n\tret" for i in range(1, 5)) +
                "\nParcel5:\n\tret\n")
            for mode, expected_runs in (("no_hit", 1), ("failure", 1), ("expanding", 3), ("plan", 0)):
                with self.subTest(mode=mode):
                    runs = []

                    def capture(**kwargs):
                        runs.append(kwargs)
                        return {"kind": "unified_debugger_instruction_trace", "valid": mode != "failure",
                                "executed": True, "errors": ["bad state"] if mode == "failure" else [],
                                "execution_validation": {"hit_function_symbols": [] if mode == "no_hit" else list(kwargs["function_symbols"])},
                                "trace_output": {"written": False}}

                    with patch("tools.debugger.investigate.build_instruction_trace_report", side_effect=capture), \
                         patch("tools.debugger.investigate.build_runtime_state_report", return_value={"valid": True}), \
                         patch("tools.debugger.investigate.build_replay_plan", return_value={"valid": True}):
                        report = build_investigation_run(
                            symptom="withdraw nickname", rom_path="test.gbc", symbols_path="test.sym",
                            save_state="before.state", execute_watch=mode != "plan", out_dir=mode,
                            max_targets=4, max_events=16, max_cases=1, frames=5, root=root)
                    self.assertEqual(len(runs), expected_runs)
                    targets = [frozenset(run["function_symbols"]) for run in runs]
                    self.assertEqual(len(targets), len(set(targets)))
                    self.assertTrue(all(len(target) <= 4 for target in targets))
                    if mode == "failure":
                        self.assertFalse(report["valid"])
                        self.assertIn("bad state", str(report["errors"]))

    def test_cli_investigate_symptom_only_points_to_next(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_out = Path(tmp) / "investigate.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "investigate",
                        "--symptom",
                        "boss selected wrong switch",
                        "--out-dir",
                        str(Path(tmp) / "investigate"),
                        "--max-targets",
                        "1",
                        "--max-events",
                        "1",
                        "--max-cases",
                        "1",
                        "--json-out",
                        str(json_out),
                    ]
                )

            self.assertEqual(code, 0)
            text = stdout.getvalue()
            self.assertIn("planning packet, not a repro", text)
            self.assertIn("python -m tools.debugger next --symptom", text)
            self.assertIn("Next proof path", text)
            self.assertIn("rom-switch-materialize", text)
            data = json.loads(json_out.read_text(encoding="utf-8"))
            next_step = data["symptom_only_next_step"]
            rec = next_step["recommendation"]
            self.assertEqual(next_step["kind"], "unified_debugger_next_step")
            self.assertEqual(rec["symptom_class"], "wrong_switch")
            self.assertIn("rom-switch-materialize", rec["first_command"])
            self.assertIn("tools/boss_ai_debugger/rom_switch_materialize.py", rec["source_refs"])
            self.assertIn("rom-switch-materialize", rec["evidence_standard"][0])
            self.assertIn("expected switch result", rec["disproof_standard"][0])
            self.assertIn("rom-switch-materialize", rec["regression_gate"])

    def test_investigation_replay_consumes_content_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "test.sym").write_text("00:0000 NULL\n", encoding="utf-8")
            (root / "maps" / "UnitMap.asm").write_text(
                "UnitMap_MapEvents:\n\tdef_warp_events\n\twarp_event 1, 2, ROUTE_29, 1\n",
                encoding="utf-8",
            )

            report = build_investigation_run(
                symbols_path="test.sym",
                changed_files=("maps/UnitMap.asm",),
                out_dir="run",
                max_targets=4,
                max_cases=2,
                root=root,
            )
            replay = json.loads((root / "run" / "03_replay.json").read_text(encoding="utf-8"))

        self.assertTrue(report["valid"])
        self.assertIn("02_content_scenarios", {step["id"] for step in report["steps"]})
        self.assertIn("content_scenario_1_0000", replay["replay_targets"]["scenario_ids"])

    def test_investigation_run_writes_debugger_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "test.sym").write_text(
                "0E:483E BossAI_ApplyMoveModel\n01:D0D3 wEnemyAIMoveScores\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "boss_policy_move.asm").write_text(
                "BossAI_ApplyMoveModel:\n\tld hl, wEnemyAIMoveScores\n\tret\n",
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
                                    "rule_id": "move.apply_move_model.apply_role_bias",
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out_dir = root / "investigation"

            report = build_investigation_run(
                traces=("trace.json",),
                symbols_path="test.sym",
                symbols=("BossAI_ApplyMoveModel",),
                addresses=("D0D3",),
                rules=("move.apply_move_model.apply_role_bias",),
                expectations=("event=score_delta,symbol=wEnemyAIMoveScores",),
                out_dir=str(out_dir),
                max_targets=6,
                max_cases=4,
                root=root,
            )
            step_ids = {step["id"] for step in report["steps"]}
            ingest_written = (out_dir / "01_ingest.json").exists()
            impact_written = (out_dir / "12_impact.json").exists()
            static_written = (out_dir / "investigation_report.md").exists()
            visualization_written = (out_dir / "investigation_visualization.md").exists()

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertEqual(report["kind"], "unified_debugger_investigation_run")
        self.assertIn("02_trace_index", step_ids)
        self.assertIn("08_expect", step_ids)
        self.assertGreaterEqual(report["produced_report_count"], 10)
        self.assertTrue(ingest_written)
        self.assertTrue(impact_written)
        self.assertTrue(static_written)
        self.assertTrue(visualization_written)

    def test_investigation_run_builds_state_space_from_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "data" / "types").mkdir(parents=True)
            (root / "test.sym").write_text(
                "0E:483E BossAI_ApplyMoveModel\n"
                "01:D0D3 wEnemyAIMoveScores\n"
                "01:D1EC wTypeMatchup\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "boss_policy_move.asm").write_text(
                "BossAI_ApplyMoveModel:\n\tld hl, wEnemyAIMoveScores\n\tret\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "late_gen_held_items.asm").write_text(
                "AirBalloon:\n\tret\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "effect_commands.asm").write_text(
                "BattleCommand_DamageCalc:\n\tret\n",
                encoding="utf-8",
            )
            (root / "data" / "types" / "type_matchups.asm").write_text(
                "TypeMatchups:\n\tdb 0\n",
                encoding="utf-8",
            )
            out_dir = root / "investigation"

            report = build_investigation_run(
                symbols_path="test.sym",
                patches=("wTypeMatchup=0x00",),
                watch_symbols=("wEnemyAIMoveScores",),
                changed_files=("engine/battle/ai/boss_policy_move.asm",),
                symptom="AI chose Ground move into Air Balloon immunity",
                out_dir=str(out_dir),
                max_targets=6,
                max_cases=4,
                root=root,
            )
            state_space = json.loads(
                (out_dir / "02_state_space.json").read_text(encoding="utf-8")
            )
            replay = json.loads(
                (out_dir / "03_replay.json").read_text(encoding="utf-8")
            )
            ranked = json.loads(
                (out_dir / "11_rank.json").read_text(encoding="utf-8")
            )
            impact = json.loads(
                (out_dir / "12_impact.json").read_text(encoding="utf-8")
            )

        step_ids = {step["id"] for step in report["steps"]}
        ranked_types = {item["type"] for item in ranked["findings"]}
        impact_types = {item["type"] for item in impact["items"]}

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertIn("02_state_space", step_ids)
        self.assertEqual(report["patches"], ["wTypeMatchup=0x00"])
        self.assertIn("wTypeMatchup", report["effective_watch_symbols"])
        self.assertEqual(state_space["kind"], "unified_debugger_state_space")
        self.assertEqual(state_space["state_space"]["patches"][0]["symbol"], "wTypeMatchup")
        self.assertIn("wTypeMatchup", replay["replay_targets"]["watch_symbols"])
        self.assertIn("state_space_ready", ranked_types)
        self.assertIn("state_space_ready", impact_types)

    def test_cli_investigate_writes_json_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            symbols = root / "test.sym"
            symbols.write_text(
                "0E:483E BossAI_ApplyMoveModel\n01:D0D3 wEnemyAIMoveScores\n",
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
                                    "rule_id": "move.apply_move_model.apply_role_bias",
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out_dir = root / "run"
            out = root / "investigation.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "investigate",
                        "--trace",
                        str(trace),
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "BossAI_ApplyMoveModel",
                        "--patch",
                        "wEnemyAIMoveScores=0x12",
                        "--address",
                        "D0D3",
                        "--expect",
                        "event=score_delta,symbol=wEnemyAIMoveScores",
                        "--out-dir",
                        str(out_dir),
                        "--max-targets",
                        "6",
                        "--max-cases",
                        "4",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))
            seeds_written = (out_dir / "generated_seeds.jsonl").exists()

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_investigation_run")
        self.assertTrue(data["passed"])
        self.assertEqual(data["patches"], ["wEnemyAIMoveScores=0x12"])
        self.assertIn("wEnemyAIMoveScores", data["effective_watch_symbols"])
        self.assertTrue(data["static_report"])
        self.assertTrue(data["visualization"])
        self.assertTrue(seeds_written)

    def test_symptom_only_investigation_preserves_embedded_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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
                        "symptom_only_next_step_note": "No runtime evidence supplied.",
                        "symptom_only_next_step": build_next_step(symptom="boss selected wrong switch"),
                    }
                ),
                encoding="utf-8",
            )

            ranked = rank_findings(reports=("investigate.json",), root=root)
            report = build_static_report(reports=("investigate.json",), root=root)
            visualization = build_visualization_report(reports=("investigate.json",), root=root)

        finding_types = {finding["type"] for finding in ranked["findings"]}
        graph_relations = {edge["relation"] for edge in visualization["graph"]["edges"]}
        timeline_types = {event["type"] for event in visualization["timeline"]}
        waterfall_titles = "\n".join(step["title"] for step in visualization["waterfall"])
        self.assertTrue(ranked["valid"])
        self.assertIn("next_step", finding_types)
        self.assertIn("Next proof path", report["content"])
        self.assertIn("rom-switch-materialize", report["content"])
        self.assertIn("source/data: tools/boss_ai_debugger/rom_switch_materialize.py", report["content"])
        self.assertIn("evidence standard: A scenario JSONL matching the disputed switch case passes rom-switch-materialize", report["content"])
        self.assertIn("disproof standard: If a matching scenario JSONL passes rom-switch-materialize with the expected switch result", report["content"])
        self.assertIn("regression gate: python -m tools.boss_ai_debugger rom-switch-materialize", report["content"])
        self.assertIn("next_step", timeline_types)
        self.assertIn("rom-switch-materialize", waterfall_titles)
        self.assertIn("source_ref", graph_relations)
        self.assertIn("evidence_standard", graph_relations)
        self.assertIn("disproof_standard", graph_relations)
        self.assertIn("regression_gate", graph_relations)
