from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.instruction_trace import build_instruction_trace_report


class InstructionTraceTests(unittest.TestCase):
    def test_plan_includes_branch_target_immediately_after_loop_terminator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:4000 Scan\n01:4004 Scan.done\n01:4007 Other\n")
            # Conditional loop exit targets the instruction immediately after
            # the unconditional back edge, as in the historical link parser.
            for branch, expected in ((0x28, [0x4000, 0x4002, 0x4004, 0x4006]),
                                      (0x00, [0x4000, 0x4001, 0x4002])):
                with self.subTest(branch=branch):
                    rom = bytearray(32768)
                    rom[0x4000:0x4008] = bytes([branch, 2 if branch else 0, 0x18, 0xFC, 0x3E, 9, 0xC9, 0])
                    (root / "test.gbc").write_bytes(rom)
                    report = build_instruction_trace_report(root=root, rom_path="test.gbc", symbols_path="test.sym",
                                                           function_symbols=("Scan",))
                    self.assertTrue(report["valid"], report["errors"])
                    self.assertEqual([row["pc"] for row in report["functions"][0]["instructions"]], expected)

    def test_capture_observes_stack_bytes_for_pop_and_return_in_ram(self):
        from types import SimpleNamespace
        from tools.debugger.instruction_frames import parse_instruction_record

        class Memory(dict):
            def __getitem__(self, address):
                self.reads.append(address)
                return self.get(address, 0)

        class Emulator:
            def __init__(self, sp):
                self.register_file = SimpleNamespace(A=0, F=0, B=0, C=0, D=0, E=0, H=0, L=0, SP=sp, PC=0x4000)
                self.memory = Memory({sp: 0x34, (sp + 1) & 65535: 0x12})
                self.memory.reads = []
                self.callbacks = []
            def hook_register(self, bank, pc, callback, context):
                self.callbacks.append((pc, callback))
            def hook_deregister(self, bank, pc):
                pass
            def tick(self, *_args):
                for pc, callback in self.callbacks:
                    self.register_file.PC = pc
                    callback(None)
            def stop(self, save=False):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(32768)
            rom[0x4000:0x4003] = bytes([0, 0xD1, 0xC9])
            (root / "unit.gbc").write_bytes(rom)
            (root / "test.sym").write_text("01:4000 Unit\n01:4003 End\n")
            for sp, addresses in ((0xC100, [0xC100, 0xC101]), (0xCFFF, [0xCFFF, 0xD000]),
                                  (0xDFFF, [0xDFFF]), (0xFFFD, [0xFFFD, 0xFFFE]),
                                  (0xFFFE, [0xFFFE]), (0x8000, [])):
                with self.subTest(sp=sp):
                    emulator = Emulator(sp)
                    with patch("tools.debugger.instruction_trace.trace_runtime.open_pyboy", return_value=emulator):
                        report = build_instruction_trace_report(root=root, rom_path="unit.gbc", symbols_path="test.sym",
                                                               function_symbols=("Unit",), execute=True, out_trace="stack.jsonl")
                    self.assertTrue(report["valid"], report["errors"])
                    records = [json.loads(line) for line in (root / "stack.jsonl").read_text().splitlines()]
                    self.assertNotIn("watch_value_specs", records[0])
                    for record in records[1:]:
                        frame = parse_instruction_record(record, default_seq=0)["frame"]
                        self.assertEqual(dict(frame.memory), {address: emulator.memory.get(address) for address in addresses})
                    self.assertEqual(emulator.memory.reads, addresses * 2)

    def test_overlapping_function_windows_capture_once_and_credit_both_targets(self):
        from collections import defaultdict
        from types import SimpleNamespace

        class FakePyBoy:
            def __init__(self):
                self.register_file = SimpleNamespace(
                    A=42, F=0, B=0, C=0, D=0, E=0, H=0, L=0, SP=0xFFFE, PC=0x4000,
                )
                self.memory = defaultdict(int)
                self.callbacks = {}

            def load_state(self, handle):
                self.loaded_state = handle.read()

            def hook_register(self, bank, pc, callback, context):
                if (bank, pc) in self.callbacks:
                    raise ValueError("Hook already registered for this bank and address.")
                self.callbacks[bank, pc] = callback

            def hook_deregister(self, bank, pc):
                del self.callbacks[bank, pc]

            def tick(self, *_args):
                for (_, pc), callback in self.callbacks.items():
                    self.register_file.PC = pc
                    callback(None)

            def stop(self, save=False):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4006] = bytes([0x3E, 0x2A, 0xEA, 0x41, 0xD1, 0xC9])
            (root / "unit.gbc").write_bytes(rom)
            (root / "test.sym").write_text(
                "01:4000 UnitFunc\n01:4002 UnitFunc.body\n01:4006 NextFunc\n",
                encoding="utf-8",
            )
            emulator = FakePyBoy()
            (root / "initial.state").write_bytes(b"initial")
            with patch("tools.debugger.instruction_trace.trace_runtime.open_pyboy", return_value=emulator):
                report = build_instruction_trace_report(
                    function_symbols=("UnitFunc", "UnitFunc.body"),
                    rom_path="unit.gbc", symbols_path="test.sym",
                    save_state="initial.state",
                    execute=True, require_hit=True, out_trace="trace.jsonl", root=root,
                )
            rows = [json.loads(line) for line in (root / "trace.jsonl").read_text().splitlines()]
            from tools.debugger.report_envelope import sha256_file
            self.assertEqual(report["state_basis"]["initial_state_sha256"], sha256_file(root / "initial.state"))
            self.assertEqual(report["trace_sha256"], sha256_file(root / "trace.jsonl"))
            self.assertEqual(rows[0]["basis"]["state_basis"], report["state_basis"])
            self.assertEqual(report["backend_sha256"], sha256_file(Path(__file__)))
            original_basis = report["state_basis"]
            for state_bytes, frames, changed_key in ((b"changed", 300, "initial_state_sha256"),
                                                     (b"initial", 301, "input_log_sha256")):
                (root / "initial.state").write_bytes(state_bytes)
                with patch("tools.debugger.instruction_trace.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                    changed = build_instruction_trace_report(
                        function_symbols=("UnitFunc",), rom_path="unit.gbc", symbols_path="test.sym",
                        save_state="initial.state", execute=True, frames=frames, root=root)
                self.assertNotEqual(changed["state_basis"][changed_key], original_basis[changed_key])
            from tools.debugger.instruction_frames import parse_instruction_record
            for version, mode, selector, expected in ((17, 1, 0, 1), (17, 1, 7, 7), (17, 0, 7, 1),
                                                      (8, 1, 2, 2), (15, 1, 3, 3), (16, 1, 4, 4),
                                                      (7, 1, 7, None), (18, 1, 7, None), (17, 2, 7, None)):
                with self.subTest(version=version, mode=mode, selector=selector):
                    header = bytearray([version, 0, 0, 0, 0, 0])
                    header[4 if version <= 15 else 5] = mode
                    (root / "initial.state").write_bytes(header)
                    bank_emulator = FakePyBoy()
                    bank_emulator.memory[0xFF70] = selector
                    with patch("tools.debugger.instruction_trace.trace_runtime.open_pyboy", return_value=bank_emulator):
                        capture = build_instruction_trace_report(
                            function_symbols=("UnitFunc",), rom_path="unit.gbc", symbols_path="test.sym",
                            save_state="initial.state", execute=True, out_trace="banks.jsonl", root=root)
                    self.assertTrue(capture["valid"], capture["errors"])
                    for line in (root / "banks.jsonl").read_text().splitlines():
                        record = json.loads(line)
                        frame = parse_instruction_record(record, default_seq=0)["frame"]
                        self.assertEqual(dict(frame.bank_state).get("wram"), expected)
                        if expected is None:
                            self.assertNotIn("bank_state", record)
                    self.assertEqual(bank_emulator.memory[0xFF70], selector)
            (root / "initial.state").write_bytes(bytes([17, 0, 0, 0, 0, 1]))
            changing = FakePyBoy()
            def changing_tick(*_args):
                for selector, ((_, pc), callback) in enumerate(changing.callbacks.items(), 1):
                    changing.memory[0xFF70] = selector
                    changing.register_file.PC = pc
                    callback(None)
            changing.tick = changing_tick
            with patch("tools.debugger.instruction_trace.trace_runtime.open_pyboy", return_value=changing):
                changing_report = build_instruction_trace_report(
                    function_symbols=("UnitFunc",), rom_path="unit.gbc", symbols_path="test.sym",
                    save_state="initial.state", execute=True, out_trace="changing.jsonl", root=root)
            self.assertTrue(changing_report["valid"], changing_report["errors"])
            self.assertEqual([json.loads(line)["bank_state"]["wram_raw"] for line in
                              (root / "changing.jsonl").read_text().splitlines()], [1, 2, 3])

        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual([row["pc"] for row in rows], [0x4000, 0x4002, 0x4005])
        validation = report["execution_validation"]
        self.assertEqual(validation["planned_hook_count"], 3)
        self.assertEqual(validation["hit_function_symbols"], ["UnitFunc", "UnitFunc.body"])
        self.assertEqual(validation["missing_function_symbols"], [])
        self.assertEqual(emulator.callbacks, {})

    def test_instruction_trace_plans_function_hooks_from_rom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4006] = bytes([0x3E, 0x2A, 0xEA, 0x41, 0xD1, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 UnitFunc\n01:4006 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                function_symbols=("UnitFunc",),
                watch_symbols=("wCurDamage",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        instructions = report["functions"][0]["instructions"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertFalse(report["executed"])
        self.assertEqual(report["instruction_count"], 3)
        self.assertEqual(instructions[0]["mnemonic"], "ld a, $2a")
        self.assertEqual(instructions[1]["mnemonic"], "ld [$d141], a")
        self.assertIn("tools.debugger trace-instructions", commands)
        self.assertIn("tools.debugger dynamic-taint", commands)
        self.assertIn("--sink-symbol wCurDamage", commands)

    def test_instruction_trace_derives_window_from_watch_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4006] = bytes([0x3E, 0x2A, 0xEA, 0x41, 0xD1, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 UnitFunc\n01:4006 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )
            (root / "watch.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "valid": True,
                        "events": [
                            {
                                "watch": "wCurDamage",
                                "old_hex": "0000",
                                "new_hex": "002A",
                                "pc_label": "UnitFunc+0x5",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                reports=("watch.json",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        selection = report["target_selection"]

        self.assertTrue(report["valid"])
        self.assertEqual(selection["function_symbols"], ["UnitFunc"])
        self.assertEqual(selection["watch_symbols"], ["wCurDamage"])
        self.assertEqual(report["instruction_count"], 3)

    def test_instruction_trace_derives_window_from_content_scenario_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:4000 UnitHelper",
                        "01:4003 NextFunc",
                        "02:5000 UnitMovement",
                        "01:D140 wMovementPointer",
                        "01:D142 wMovementObject",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "movement_data",
                                "label": "UnitMovement",
                                "state_preconditions": [
                                    {
                                        "kind": "movement_entry",
                                        "watch_symbols": ["wMovementObject"],
                                    }
                                ],
                                "runtime_targets": {
                                    "trace_symbols": ["UnitHelper"],
                                    "script_symbols": ["UnitMovement"],
                                    "watch_symbols": ["wMovementPointer"],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                reports=("content.json",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        selection = report["target_selection"]

        self.assertTrue(report["valid"])
        self.assertEqual(selection["function_symbols"], ["UnitHelper"])
        self.assertNotIn("UnitMovement", selection["function_symbols"])
        self.assertEqual(selection["watch_symbols"], ["wMovementObject", "wMovementPointer"])
        self.assertEqual(report["instruction_count"], 3)

    def test_instruction_trace_filters_content_scenario_report_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            rom[0x4010:0x4013] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:4000 FirstHelper",
                        "01:4003 FirstNext",
                        "01:4010 SecondHelper",
                        "01:4013 SecondNext",
                        "01:D140 wFirstWatch",
                        "01:D141 wSecondWatch",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "runtime_targets": {
                                    "trace_symbols": ["FirstHelper"],
                                    "watch_symbols": ["wFirstWatch"],
                                },
                            },
                            {
                                "id": "content_scenario_1_0001",
                                "kind": "unified_debugger_content_scenario",
                                "runtime_targets": {
                                    "trace_symbols": ["SecondHelper"],
                                    "watch_symbols": ["wSecondWatch"],
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                reports=("content.json",),
                scenario_ids=("content_scenario_1_0001",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        selection = report["target_selection"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(selection["function_symbols"], ["SecondHelper"])
        self.assertEqual(selection["watch_symbols"], ["wSecondWatch"])
        self.assertNotIn("FirstHelper", selection["function_symbols"])
        self.assertIn("--scenario-id content_scenario_1_0001", commands)

    def test_instruction_trace_derives_window_from_content_state_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            for offset in range(0x4000, 0x4020, 3):
                rom[offset : offset + 3] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:4000 ScriptEvents",
                        "01:4003 RunScriptCommand",
                        "01:4006 CallScript",
                        "01:4009 ApplyMovement",
                        "01:400C GetMovementData",
                        "01:400F HandleMovementData",
                        "01:4012 WaitScriptMovement",
                        "01:4015 NextFunc",
                        "01:D140 wScriptPos",
                        "01:D141 wMovementDataAddress",
                        "01:D143 wMovementPointer",
                        "01:D145 wMovementObject",
                        "01:D146 wScriptMode",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "content_state.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0000",
                                "scenario_type": "script_command_stream",
                                "precondition_kind": "script_entry",
                                "status": "ready",
                                "patches": [{"symbol": "wScriptPos", "base_symbol": "wScriptPos", "value": 0}],
                            },
                            {
                                "scenario_id": "content_scenario_1_0001",
                                "scenario_type": "movement_data",
                                "precondition_kind": "movement_entry",
                                "status": "ready",
                                "patches": [
                                    {"symbol": "wMovementDataAddress", "base_symbol": "wMovementDataAddress", "value": 0},
                                    {"symbol": "wMovementPointer", "base_symbol": "wMovementPointer", "value": 0},
                                    {"symbol": "wMovementObject", "base_symbol": "wMovementObject", "value": 0},
                                    {"symbol": "wScriptMode", "base_symbol": "wScriptMode", "value": 2},
                                ],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                reports=("content_state.json",),
                scenario_ids=("content_scenario_1_0001",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        selection = report["target_selection"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(
            selection["function_symbols"],
            ["ApplyMovement", "GetMovementData", "HandleMovementData", "WaitScriptMovement"],
        )
        self.assertNotIn("ScriptEvents", selection["function_symbols"])
        self.assertEqual(
            selection["watch_symbols"],
            ["wMovementDataAddress", "wMovementObject", "wMovementPointer", "wScriptMode"],
        )
        self.assertNotIn("wScriptPos", selection["watch_symbols"])
        self.assertIn("--report content_state.json --scenario-id content_scenario_1_0001", commands)

    def test_instruction_trace_uses_executed_content_state_out_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            for offset in range(0x4000, 0x4020, 3):
                rom[offset : offset + 3] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "patched.state").write_bytes(b"patched-state")
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:4000 ApplyMovement",
                        "01:4003 GetMovementData",
                        "01:4006 HandleMovementData",
                        "01:4009 WaitScriptMovement",
                        "01:400C NextFunc",
                        "01:D141 wMovementDataAddress",
                        "01:D143 wMovementPointer",
                        "01:D145 wMovementObject",
                        "01:D146 wScriptMode",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "content_state.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "executed": True,
                        "out_state": "patched.state",
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0001",
                                "scenario_type": "movement_data",
                                "precondition_kind": "movement_entry",
                                "status": "ready",
                                "patches": [
                                    {"symbol": "wMovementDataAddress", "base_symbol": "wMovementDataAddress", "value": 0},
                                    {"symbol": "wMovementPointer", "base_symbol": "wMovementPointer", "value": 0},
                                    {"symbol": "wMovementObject", "base_symbol": "wMovementObject", "value": 0},
                                    {"symbol": "wScriptMode", "base_symbol": "wScriptMode", "value": 2},
                                ],
                            },
                        ],
                        "execution": {
                            "executed": True,
                            "out_state": "patched.state",
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                reports=("content_state.json",),
                scenario_ids=("content_scenario_1_0001",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        selection = report["target_selection"]
        selected_state = report["save_state_discovery"]["selected"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(selection["function_symbols"], ["ApplyMovement", "GetMovementData", "HandleMovementData", "WaitScriptMovement"])
        self.assertEqual(report["input_save_state"], "")
        self.assertEqual(report["effective_save_state"], "patched.state")
        self.assertEqual(report["save_state"], "patched.state")
        self.assertEqual(selected_state["key"], "execution.out_state")
        self.assertEqual(selected_state["scenario_id"], "content_scenario_1_0001")
        self.assertTrue(selected_state["exists"])
        self.assertIn("--save-state patched.state", commands)

    def test_instruction_trace_uses_executed_state_space_out_state_and_watches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "patched.state").write_bytes(b"patched-state")
            (root / "test.sym").write_text(
                "01:4000 ScriptEvents\n01:4003 NextFunc\n01:DA10 wScriptBank\n01:DA11 wScriptPos\n",
                encoding="utf-8",
            )
            (root / "state_space.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_state_space",
                        "valid": True,
                        "executed": True,
                        "scenario_id": "script_entry_1",
                        "out_state": "patched.state",
                        "watch_symbols": ["wScriptPos"],
                        "state_space": {
                            "scenario_ids": ["script_entry_1"],
                            "patches": [
                                {
                                    "symbol": "wScriptBank",
                                    "base_symbol": "wScriptBank",
                                    "value": 2,
                                    "value_hex": "02",
                                    "scenario_id": "script_entry_1",
                                },
                                {
                                    "symbol": "wScriptPos",
                                    "base_symbol": "wScriptPos",
                                    "value": 80,
                                    "value_hex": "50",
                                    "scenario_id": "script_entry_1",
                                },
                            ],
                        },
                        "execution": {
                            "executed": True,
                            "out_state": "patched.state",
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                function_symbols=("ScriptEvents",),
                reports=("state_space.json",),
                scenario_ids=("script_entry_1",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        selection = report["target_selection"]
        selected_state = report["save_state_discovery"]["selected"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(selection["function_symbols"], ["ScriptEvents"])
        self.assertIn("wScriptBank", selection["watch_symbols"])
        self.assertIn("wScriptPos", selection["watch_symbols"])
        self.assertEqual(report["effective_save_state"], "patched.state")
        self.assertEqual(selected_state["key"], "execution.out_state")
        self.assertEqual(selected_state["scenario_id"], "script_entry_1")
        self.assertTrue(selected_state["exists"])
        self.assertIn("--save-state patched.state", commands)
        self.assertIn("--scenario-id script_entry_1", commands)

    def test_instruction_trace_does_not_use_unexecuted_content_state_out_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "patched.state").write_bytes(b"planned-state")
            (root / "test.sym").write_text(
                "01:4000 ApplyMovement\n01:4003 NextFunc\n01:D145 wMovementObject\n",
                encoding="utf-8",
            )
            (root / "content_state.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_state_materialization",
                        "valid": True,
                        "executed": False,
                        "out_state": "patched.state",
                        "materializations": [
                            {
                                "scenario_id": "content_scenario_1_0001",
                                "scenario_type": "movement_data",
                                "precondition_kind": "movement_entry",
                                "status": "ready",
                                "patches": [{"symbol": "wMovementObject", "base_symbol": "wMovementObject", "value": 0}],
                            }
                        ],
                        "execution": {
                            "executed": False,
                            "out_state": "patched.state",
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                reports=("content_state.json",),
                scenario_ids=("content_scenario_1_0001",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "")
        self.assertEqual(report["save_state_discovery"]["selected"], {})
        self.assertNotIn("--save-state patched.state", commands)

    def test_instruction_trace_does_not_use_unexecuted_state_space_out_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "patched.state").write_bytes(b"planned-state")
            (root / "test.sym").write_text("01:4000 ScriptEvents\n01:4003 NextFunc\n01:DA11 wScriptPos\n", encoding="utf-8")
            (root / "state_space.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_state_space",
                        "valid": True,
                        "executed": False,
                        "scenario_id": "script_entry_1",
                        "out_state": "patched.state",
                        "state_space": {
                            "scenario_ids": ["script_entry_1"],
                            "patches": [{"symbol": "wScriptPos", "base_symbol": "wScriptPos", "value": 80}],
                        },
                        "execution": {
                            "executed": False,
                            "out_state": "patched.state",
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                function_symbols=("ScriptEvents",),
                reports=("state_space.json",),
                scenario_ids=("script_entry_1",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["effective_save_state"], "")
        self.assertEqual(report["save_state_discovery"]["selected"], {})
        self.assertIn("wScriptPos", report["target_selection"]["watch_symbols"])
        self.assertNotIn("--save-state patched.state", commands)

    def test_instruction_trace_derives_window_from_changed_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine" / "battle").mkdir(parents=True)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 SourceFunc\n01:4003 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "unit.asm").write_text(
                "SourceFunc:\n\tnop\n\tret\n",
                encoding="utf-8",
            )

            report = build_instruction_trace_report(
                changed_files=("engine/battle/unit.asm",),
                watch_symbols=("wCurDamage",),
                rom_path="unit.gbc",
                symbols_path="test.sym",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["target_selection"]["function_symbols"], ["SourceFunc"])
        self.assertEqual(report["target_selection"]["watch_symbols"], ["wCurDamage"])

    def test_cli_trace_instructions_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4006] = bytes([0x3E, 0x2A, 0xEA, 0x41, 0xD1, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 UnitFunc\n01:4006 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )
            out = root / "instruction_trace.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "trace-instructions",
                        "--rom",
                        str(root / "unit.gbc"),
                        "--symbols",
                        str(root / "test.sym"),
                        "--symbol",
                        "UnitFunc",
                        "--watch-symbol",
                        "wCurDamage",
                        "--require-hit",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_instruction_trace")
        self.assertTrue(data["valid"])
        self.assertTrue(data["require_hit"])
        self.assertIn("--require-hit is only enforced with --execute", data["warnings"])
        self.assertEqual(data["instruction_count"], 3)
        self.assertFalse(data["trace_output"]["written"])

    def test_instruction_trace_validates_executed_hook_hits(self) -> None:
        class FakeRegisters:
            A = 0x2A
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0xD1
            L = 0x41
            SP = 0xFFFE
            PC = 0x4000

        class FakeMemory:
            def __init__(self) -> None:
                self.values = {
                    (1, 0xD141): 0x00,
                    (1, 0xD142): 0x2A,
                    0xFF70: 1,
                }

            def __getitem__(self, key):
                return self.values.get(key, 0)

            def __setitem__(self, key, value) -> None:
                self.values[key] = value

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()
                self.callbacks = []

            def hook_register(self, bank, pc, callback, _ctx) -> None:
                self.callbacks.append((bank, pc, callback))

            def hook_deregister(self, bank, pc) -> None:
                self.callbacks = [
                    item for item in self.callbacks if item[:2] != (bank, pc)
                ]

            def tick(self, *_args) -> None:
                for _bank, pc, callback in list(self.callbacks):
                    self.register_file.PC = pc
                    callback(None)

            def stop(self, save=False) -> None:
                self.stopped = True

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4006] = bytes([0x3E, 0x2A, 0xEA, 0x41, 0xD1, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 UnitFunc\n01:4006 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )
            out_trace = root / "trace.jsonl"

            with patch("tools.debugger.instruction_trace.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                report = build_instruction_trace_report(
                    function_symbols=("UnitFunc",),
                    watch_symbols=("wCurDamage",),
                    rom_path="unit.gbc",
                    symbols_path="test.sym",
                    execute=True,
                    require_hit=True,
                    out_trace=str(out_trace),
                    root=root,
                )

            rows = [
                json.loads(line)
                for line in out_trace.read_text(encoding="utf-8").splitlines()
            ]

        validation = report["execution_validation"]

        self.assertTrue(report["valid"])
        self.assertTrue(report["executed"])
        self.assertTrue(validation["hit"])
        self.assertTrue(validation["ready_for_dynamic_taint"])
        self.assertEqual(validation["hit_function_symbols"], ["UnitFunc"])
        self.assertEqual(validation["missing_function_symbols"], [])
        self.assertEqual(report["captured_frame_count"], 3)
        self.assertEqual(report["trace_output"]["record_count"], 3)
        self.assertEqual(rows[0]["function"], "UnitFunc")
        self.assertEqual(rows[0]["watch_values"]["wCurDamage"], "002A")

    def test_instruction_trace_can_require_an_executed_hook_hit(self) -> None:
        class FakeRegisters:
            A = 0
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0
            L = 0
            SP = 0xFFFE
            PC = 0x4000

        class FakeMemory:
            def __getitem__(self, key):
                return 0

            def __setitem__(self, key, value) -> None:
                pass

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()

            def hook_register(self, *_args) -> None:
                pass

            def hook_deregister(self, *_args) -> None:
                pass

            def tick(self, *_args) -> None:
                pass

            def stop(self, save=False) -> None:
                pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 UnitFunc\n01:4003 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )

            with patch("tools.debugger.instruction_trace.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                strict_report = build_instruction_trace_report(
                    function_symbols=("UnitFunc",),
                    watch_symbols=("wCurDamage",),
                    rom_path="unit.gbc",
                    symbols_path="test.sym",
                    execute=True,
                    require_hit=True,
                    root=root,
                )
            with patch("tools.debugger.instruction_trace.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                loose_report = build_instruction_trace_report(
                    function_symbols=("UnitFunc",),
                    watch_symbols=("wCurDamage",),
                    rom_path="unit.gbc",
                    symbols_path="test.sym",
                    execute=True,
                    root=root,
                )

        self.assertFalse(strict_report["valid"])
        self.assertFalse(strict_report["execution_validation"]["hit"])
        self.assertIn("none of the selected hooks fired", "\n".join(strict_report["errors"]))
        self.assertTrue(loose_report["valid"])
        self.assertIn("none of the selected hooks fired", "\n".join(loose_report["warnings"]))

    def test_cli_trace_instructions_uses_report_for_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = bytearray(0x8000)
            rom[0x4000:0x4003] = bytes([0x00, 0x00, 0xC9])
            (root / "unit.gbc").write_bytes(bytes(rom))
            (root / "test.sym").write_text(
                "01:4000 UnitFunc\n01:4003 NextFunc\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )
            (root / "watch.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_watch_report",
                        "events": [{"watch": "wCurDamage", "pc_label": "UnitFunc"}],
                    }
                ),
                encoding="utf-8",
            )
            out = root / "instruction_trace.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "trace-instructions",
                        "--rom",
                        str(root / "unit.gbc"),
                        "--symbols",
                        str(root / "test.sym"),
                        "--report",
                        str(root / "watch.json"),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["target_selection"]["function_symbols"], ["UnitFunc"])
        self.assertEqual(data["target_selection"]["watch_symbols"], ["wCurDamage"])
