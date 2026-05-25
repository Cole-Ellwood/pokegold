from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.state_space import build_state_space_report


class StateSpaceTests(unittest.TestCase):
    def test_state_space_builds_generic_patch_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "01:DA10 wScriptBank\n01:DA11 wScriptPos\n01:DA13 wScriptMode\n",
                encoding="utf-8",
            )

            report = build_state_space_report(
                patches=("wScriptBank=0x02", "wScriptPos=0x50,0x40", "wScriptMode=1"),
                watch_symbols=("wScriptPos",),
                scenario_id="script_entry_1",
                source_files=("maps/UnitMap.asm",),
                symbols_path="test.sym",
                report_path="state_space.json",
                root=root,
            )

        patches = report["state_space"]["patches"]
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertFalse(report["executed"])
        self.assertEqual(report["patch_count"], 4)
        self.assertEqual([patch["symbol"] for patch in patches], ["wScriptBank", "wScriptPos", "wScriptPos+1", "wScriptMode"])
        self.assertEqual(patches[1]["bank_address"], "01:DA11")
        self.assertEqual(patches[2]["bank_address"], "01:DA12")
        self.assertEqual(patches[2]["value_hex"], "40")
        self.assertIn("wScriptPos", report["watch_symbols"])
        self.assertIn("tools.debugger expect --report state_space.json --expect state-patch=wScriptBank,scenario=script_entry_1,value=0x02", commands)
        self.assertIn("tools.debugger minimize --report state_space.json", commands)
        self.assertIn("tools.debugger trace-instructions --report state_space.json --scenario-id script_entry_1", commands)

    def test_cli_state_space_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:DA11 wScriptPos\n", encoding="utf-8")
            out = root / "state_space.json"

            with patch("tools.debugger.catalog.ROOT", root), redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "state-space",
                        "--patch",
                        "wScriptPos=0x50",
                        "--symbols",
                        str(root / "test.sym"),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_state_space")
        self.assertEqual(data["patch_count"], 1)
        self.assertEqual(data["state_space"]["patches"][0]["symbol"], "wScriptPos")

    def test_state_space_execute_patches_and_writes_state(self) -> None:
        class FakeMemory:
            def __init__(self) -> None:
                self.values: dict[Any, int] = {0xFF70: 1}

            def __getitem__(self, key: Any) -> int:
                return self.values.get(key, 0)

            def __setitem__(self, key: Any, value: int) -> None:
                self.values[key] = int(value) & 0xFF

        class FakePyBoy:
            def __init__(self) -> None:
                self.memory = FakeMemory()
                self.loaded = False
                self.stopped = False

            def load_state(self, _fh: Any) -> None:
                self.loaded = True

            def save_state(self, fh: Any) -> None:
                fh.write(b"patched-state")

            def stop(self, save: bool = False) -> None:
                self.stopped = True

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("01:DA11 wScriptPos\n", encoding="utf-8")
            (root / "rom.gbc").write_bytes(b"rom")
            (root / "base.state").write_bytes(b"base")
            out_state = root / "patched.state"
            fake = FakePyBoy()

            with patch("tools.debugger.state_space.trace_runtime.open_pyboy", return_value=fake):
                report = build_state_space_report(
                    patches=("wScriptPos=0x50",),
                    symbols_path="test.sym",
                    rom_path="rom.gbc",
                    base_save_state="base.state",
                    out_state="patched.state",
                    execute=True,
                    root=root,
                )

            written = out_state.read_bytes()

        self.assertTrue(report["valid"])
        self.assertTrue(report["executed"])
        self.assertEqual(report["execution"]["patch_count"], 1)
        self.assertEqual(report["state_space"]["patches"][0]["observed_hex"], "50")
        self.assertTrue(report["state_space"]["patches"][0]["verified"])
        self.assertIn("--execute-state-patches", "\n".join(report["commands"]))
        self.assertEqual(written, b"patched-state")
        self.assertTrue(fake.loaded)
        self.assertTrue(fake.stopped)
