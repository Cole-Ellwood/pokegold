from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.runtime_watch import build_watch_event_cause, build_watch_report


class WatchTests(unittest.TestCase):
    def test_watch_plan_resolves_symbols_without_executing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = root / "test.gbc"
            rom.write_bytes(bytes(0x8000))
            symbols = root / "test.sym"
            symbols.write_text(
                "00:0000 NULL\n01:D141 wCurDamage\n",
                encoding="utf-8",
            )

            report = build_watch_report(
                watch_symbols=("wCurDamage",),
                rom_path="test.gbc",
                symbols_path="test.sym",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertFalse(report["executed"])
        self.assertEqual(report["watches"][0]["bank_address"], "01:D141")
        self.assertEqual(report["watches"][0]["size"], 2)

    def test_watch_plan_treats_script_pointers_as_words(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text(
                "01:D160 wScriptBank\n01:D161 wScriptPos\n00:CF36 wScriptAfterPointer\n",
                encoding="utf-8",
            )

            report = build_watch_report(
                watch_symbols=("wScriptBank", "wScriptPos", "wScriptAfterPointer"),
                rom_path="test.gbc",
                symbols_path="test.sym",
                root=root,
            )

        sizes = {watch["name"]: watch["size"] for watch in report["watches"]}
        self.assertEqual(sizes["wScriptBank"], 1)
        self.assertEqual(sizes["wScriptPos"], 2)
        self.assertEqual(sizes["wScriptAfterPointer"], 2)

    def test_watch_plan_records_scheduled_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text("01:D160 wScriptBank\n", encoding="utf-8")

            report = build_watch_report(
                watch_symbols=("wScriptBank",),
                rom_path="test.gbc",
                symbols_path="test.sym",
                input_events=("0:a:4,45:start",),
                root=root,
            )

        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(
            [(event["frame"], event["button"], event["delay"]) for event in report["input_events"]],
            [(0, "a", 4), (45, "start", 8)],
        )

    def test_watch_plan_reports_missing_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text("00:0000 NULL\n", encoding="utf-8")

            report = build_watch_report(
                watch_symbols=("NoSuchSymbol",),
                rom_path="test.gbc",
                symbols_path="test.sym",
                root=root,
            )

        self.assertFalse(report["valid"])
        self.assertIn("NoSuchSymbol", report["errors"][0])

    def test_watch_event_cause_links_hit_to_static_writer(self) -> None:
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

            cause = build_watch_event_cause(
                watch_symbol="wCurDamage",
                pc_label="BattleCommand_Test+0x2",
                symbols_path="test.sym",
                root=root,
            )

        self.assertGreaterEqual(cause["candidate_count"], 1)
        self.assertEqual(cause["candidates"][0]["access"], "write")
        self.assertEqual(cause["candidates"][0]["source_file"], "engine/battle.asm")
        self.assertIn("tools.debugger localize --symbol wCurDamage", "\n".join(cause["commands"]))

    def test_watch_execution_records_dynamic_context_window(self) -> None:
        class FakeRegisters:
            A = 0x12
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
            def __init__(self) -> None:
                self.values = {0xD141: 0x00, 0xD142: 0x00}

            def __getitem__(self, key):
                return self.values.get(key, 0)

            def __setitem__(self, key, value) -> None:
                self.values[key] = value

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()

            def tick(self, *_args) -> None:
                self.register_file.PC = 0x4003
                self.memory[0xD141] = 0x34

            def stop(self, save=False) -> None:
                self.stopped = True

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text(
                "00:D141 wCurDamage\n00:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text("wCurDamage:: ds 2\n", encoding="utf-8")
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld [wCurDamage], a\n\tret\n",
                encoding="utf-8",
            )

            with patch("tools.debugger.runtime_watch.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                report = build_watch_report(
                    watch_symbols=("wCurDamage",),
                    rom_path="test.gbc",
                    symbols_path="test.sym",
                    frames=1,
                    context_frames=2,
                    execute=True,
                    root=root,
                )

        event = report["events"][0]
        context = event["dynamic_context"]

        self.assertTrue(report["valid"])
        self.assertTrue(report["executed"])
        self.assertEqual(report["hit_count"], 1)
        self.assertEqual(report["dynamic_context_event_count"], 1)
        self.assertEqual(report["runtime_summary"]["initial"]["registers"]["register_pc"], "4000")
        self.assertEqual(report["runtime_summary"]["final"]["registers"]["register_sp"], "FFFE")
        self.assertEqual(event["old_hex"], "0000")
        self.assertEqual(event["new_hex"], "3400")
        self.assertEqual(context["context_frame_count"], 1)
        self.assertEqual(context["prelude"][0]["pc_bank_address"], "00:4000")
        self.assertEqual(context["after"]["pc_label"], "BattleCommand_Test+0x3")
        self.assertEqual(context["after"]["registers"]["register_pc"], "4003")
        self.assertEqual(context["after"]["watch_values"]["wCurDamage"], "3400")
        self.assertIn("tools.debugger trace-index --report <watch_report.json>", "\n".join(event["commands"]))

    def test_watch_execution_applies_scheduled_inputs(self) -> None:
        class FakeRegisters:
            A = 0
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0
            L = 0
            SP = 0xDFF0
            PC = 0x4000

        class FakeMemory:
            def __getitem__(self, _key):
                return 0

            def __setitem__(self, _key, _value) -> None:
                return None

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()
                self.buttons: list[tuple[str, int]] = []

            def button(self, name: str, delay: int = 8) -> None:
                self.buttons.append((name, delay))

            def tick(self, *_args) -> None:
                return None

            def stop(self, save=False) -> None:
                return None

        fake = FakePyBoy()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text("01:D160 wScriptBank\n", encoding="utf-8")

            with patch("tools.debugger.runtime_watch.trace_runtime.open_pyboy", return_value=fake):
                report = build_watch_report(
                    watch_symbols=("wScriptBank",),
                    rom_path="test.gbc",
                    symbols_path="test.sym",
                    input_events=("0:a:4",),
                    frames=1,
                    execute=True,
                    root=root,
                )

        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(fake.buttons, [("a", 4)])
        self.assertEqual(report["runtime_summary"]["applied_input_count"], 1)
        self.assertEqual(report["runtime_summary"]["applied_inputs"][0]["button"], "a")

    def test_watch_execution_can_boot_from_battery_save(self) -> None:
        class FakeRegisters:
            A = 0
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0
            L = 0
            SP = 0xDFF0
            PC = 0x4000

        class FakeMemory:
            def __getitem__(self, _key):
                return 0

            def __setitem__(self, _key, _value) -> None:
                return None

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()
                self.buttons: list[str] = []

            def button(self, name: str, delay: int = 8) -> None:
                self.buttons.append(name)

            def tick(self, *_args) -> None:
                return None

            def save_state(self, fh) -> None:
                fh.write(b"state")

            def stop(self, save=False) -> None:
                return None

        fake = FakePyBoy()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sav").write_bytes(bytes(0x8000))
            out_state = root / "booted.state"
            (root / "test.sym").write_text("01:D160 wScriptBank\n", encoding="utf-8")

            with patch("tools.debugger.runtime_watch.trace_runtime.open_pyboy", return_value=fake):
                report = build_watch_report(
                    watch_symbols=("wScriptBank",),
                    rom_path="test.gbc",
                    symbols_path="test.sym",
                    battery_save="test.sav",
                    out_initial_state="booted.state",
                    frames=0,
                    execute=True,
                    root=root,
                )
            out_state_exists = out_state.exists()

        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(fake.buttons, ["start", "a", "a", "a"])
        self.assertTrue(out_state_exists)
        self.assertTrue(report["boot_continue"])
        self.assertTrue(report["runtime_summary"]["battery_save_booted"])
        self.assertEqual(report["runtime_summary"]["out_initial_state"], "booted.state")

    def test_watch_reset_sentinel_records_reset_context_without_watch_symbol(self) -> None:
        class FakeRegisters:
            A = 0x12
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0
            L = 0
            SP = 0xDFF0
            PC = 0x4000

        class FakeMemory:
            def __init__(self) -> None:
                self.values = {
                    0xFFB8: 0x0E,
                    0xFFB9: 0x01,
                    (1, 0xD22D): 0x00,
                    (1, 0xD0F0): 0xA1,
                }

            def __getitem__(self, key):
                return self.values.get(key, 0)

            def __setitem__(self, key, value) -> None:
                self.values[key] = value

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()
                self.hooks = {}

            def hook_register(self, bank, pc, callback, context) -> None:
                self.hooks[(bank, pc)] = callback

            def hook_deregister(self, bank, pc) -> None:
                self.hooks.pop((bank, pc), None)

            def tick(self, *_args) -> None:
                self.register_file.PC = 0x0100
                callback = self.hooks.get((0, 0x0100))
                if callback is not None:
                    callback(None)

            def stop(self, save=False) -> None:
                self.stopped = True

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "00:0100 Start",
                        "00:0594 Reset",
                        "00:05AA _Start",
                        "00:FFB8 hROMBank",
                        "00:FFB9 hWRAMBank",
                        "01:D22D wBattleMode",
                        "01:D0F0 wTempWildMonSpecies",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with patch("tools.debugger.runtime_watch.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                report = build_watch_report(
                    watch_symbols=(),
                    rom_path="test.gbc",
                    symbols_path="test.sym",
                    frames=1,
                    context_frames=2,
                    execute=True,
                    reset_sentinel=True,
                    root=root,
                )

        event = report["reset_events"][0]

        self.assertTrue(report["valid"])
        self.assertTrue(report["executed"])
        self.assertEqual(report["hit_count"], 0)
        self.assertEqual(report["reset_event_count"], 1)
        self.assertEqual(event["pc_bank_address"], "00:0100")
        self.assertEqual(event["pc_label"], "Start")
        self.assertEqual(event["context_symbols"]["hWRAMBank"], "01")
        self.assertEqual(event["context_symbols"]["wTempWildMonSpecies"], "A1")
        self.assertEqual(event["dynamic_context"]["context_frame_count"], 1)

    def test_watch_execution_records_invalid_script_state(self) -> None:
        class FakeRegisters:
            A = 0
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0
            L = 0
            SP = 0xDFF0
            PC = 0x4000

        class FakeMemory:
            def __init__(self) -> None:
                self.values = {
                    (1, 0xD15E): 1,
                    (1, 0xD15F): 1,
                    (1, 0xD160): 0xB4,
                    (1, 0xD161): 0x02,
                    (1, 0xD162): 0x00,
                }

            def __getitem__(self, key):
                return self.values.get(key, 0)

            def __setitem__(self, key, value) -> None:
                self.values[key] = value

        class FakePyBoy:
            def __init__(self) -> None:
                self.register_file = FakeRegisters()
                self.memory = FakeMemory()

            def tick(self, *_args) -> None:
                return None

            def stop(self, save=False) -> None:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.gbc").write_bytes(bytes(0x8000))
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:D15E wScriptMode",
                        "01:D15F wScriptRunning",
                        "01:D160 wScriptBank",
                        "01:D161 wScriptPos",
                        "01:4000 ScriptEvents",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with patch("tools.debugger.runtime_watch.trace_runtime.open_pyboy", return_value=FakePyBoy()):
                report = build_watch_report(
                    watch_symbols=("wScriptBank", "wScriptPos"),
                    rom_path="test.gbc",
                    symbols_path="test.sym",
                    frames=0,
                    execute=True,
                    root=root,
                )

        event = report["events"][0]
        self.assertTrue(report["valid"])
        self.assertEqual(report["script_state_event_count"], 1)
        self.assertEqual(event["event_type"], "invalid_script_state")
        self.assertEqual(event["script"], "B4:0002")
        self.assertIn("below the switchable ROM window", "\n".join(event["reasons"]))

    def test_cli_watch_plan_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rom = root / "test.gbc"
            rom.write_bytes(bytes(0x8000))
            symbols = root / "test.sym"
            symbols.write_text("00:0000 NULL\n01:D141 wCurDamage\n", encoding="utf-8")
            out = root / "watch.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "watch",
                        "--rom",
                        str(rom),
                        "--symbols",
                        str(symbols),
                        "--watch-symbol",
                        "wCurDamage",
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_watch_report")
            self.assertFalse(data["executed"])
