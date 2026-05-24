from __future__ import annotations

import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.debugger.ingest import ingest_artifacts
from tools.debugger.replay import build_replay_plan
from tools.debugger.runtime_state import build_runtime_state_report


class RuntimeStateInspectorTests(unittest.TestCase):
    def test_valid_map_script_pointer_and_callback_stack_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_runtime_state_root(Path(tmp))
            write_fake_sgm(
                root / "state.sgm",
                script_bank=0x02,
                script_pos=0x5010,
                stack_frames=[(0x82, 0x5020)],
                top_return=0x4000,
            )

            report = build_runtime_state_report(
                rom_path="pokegold.gbc",
                symbols_path="pokegold.sym",
                save_state="state.sgm",
                root=root,
            )

        self.assertTrue(report["valid"], report["errors"])
        self.assertTrue(report["passed"], report["findings"])
        self.assertEqual(report["map"]["name"], "TestMap")
        self.assertEqual(report["script_vm"]["current"]["nearest_label"], "TestMap.Script")
        self.assertTrue(report["script_vm"]["stack_frames"][0]["in_current_map_script_range"])

    def test_invalid_script_bank_and_position_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_runtime_state_root(Path(tmp))
            write_fake_sgm(
                root / "state.sgm",
                script_bank=0xB4,
                script_pos=0x0002,
                stack_frames=[],
                top_return=0x4000,
            )

            report = build_runtime_state_report(
                rom_path="pokegold.gbc",
                symbols_path="pokegold.sym",
                save_state="state.sgm",
                root=root,
            )

        finding_ids = {item["id"] for item in report["findings"]}

        self.assertTrue(report["valid"], report["errors"])
        self.assertFalse(report["passed"])
        self.assertIn("invalid_script_pc", finding_ids)
        self.assertIn("script_bank_mismatch_current_map", finding_ids)
        self.assertEqual(report["script_vm"]["bank_address"], "B4:0002")

    def test_cpu_stack_return_to_echo_ram_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_runtime_state_root(Path(tmp))
            write_fake_sgm(
                root / "state.sgm",
                script_bank=0x02,
                script_pos=0x5010,
                stack_frames=[],
                top_return=0xEC4F,
            )

            report = build_runtime_state_report(
                rom_path="pokegold.gbc",
                symbols_path="pokegold.sym",
                save_state="state.sgm",
                root=root,
            )

        finding_ids = {item["id"] for item in report["findings"]}

        self.assertIn("stack_return_to_echo_ram", finding_ids)
        self.assertEqual(report["cpu"]["top_stack_return_hex"], "EC4F")

    def test_known_map_anchor_beats_earlier_decoy_wram_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_runtime_state_root(Path(tmp))
            write_fake_sgm(
                root / "state.sgm",
                script_bank=0xB4,
                script_pos=0x0002,
                stack_frames=[],
                top_return=0xEC4F,
                include_decoy=True,
            )

            report = build_runtime_state_report(
                rom_path="pokegold.gbc",
                symbols_path="pokegold.sym",
                save_state="state.sgm",
                root=root,
            )

        self.assertEqual(report["snapshot_metadata"]["d000_base"], "0x2000")
        self.assertEqual(report["map"]["name"], "TestMap")
        self.assertEqual(report["script_vm"]["bank_address"], "B4:0002")

    def test_ingest_records_vbam_sgm_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_runtime_state_root(Path(tmp))
            write_fake_sgm(
                root / "state.sgm",
                script_bank=0x02,
                script_pos=0x5010,
                stack_frames=[],
                top_return=0x4000,
            )

            report = ingest_artifacts(save_states=("state.sgm",), root=root)

        metadata = report["artifacts"][0]["metadata"]
        self.assertTrue(report["valid"])
        self.assertEqual(metadata["format"], "vbam_sgm")
        self.assertEqual(metadata["version"], 12)
        self.assertFalse(metadata["opaque"])

    def test_ingest_records_battery_save_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_runtime_state_root(Path(tmp))
            (root / "state.sav").write_bytes(bytes(0x8000))

            report = ingest_artifacts(save_states=("state.sav",), root=root)

        metadata = report["artifacts"][0]["metadata"]
        self.assertTrue(report["valid"])
        self.assertEqual(metadata["format"], "battery_save")
        self.assertEqual(metadata["size_bytes"], 0x8000)
        self.assertIn("state-inspect", metadata["suggested_commands"][0])

    def test_replay_skips_pyboy_watch_execution_for_vbam_sgm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_runtime_state_root(Path(tmp))
            write_fake_sgm(
                root / "state.sgm",
                script_bank=0x02,
                script_pos=0x5010,
                stack_frames=[],
                top_return=0x4000,
            )

            report = build_replay_plan(
                rom_path="pokegold.gbc",
                symbols_path="pokegold.sym",
                save_state="state.sgm",
                watch_symbols=("wScriptBank",),
                execute_watch=True,
                root=root,
            )

        commands = "\n".join(report["commands"])
        self.assertTrue(report["valid"], report["errors"])
        self.assertIn("state-inspect", commands)
        self.assertNotIn("python -m tools.debugger watch", commands)
        self.assertIn("PyBoy watch replay needs a .state", "\n".join(report["warnings"]))

    def test_replay_routes_battery_save_watch_through_battery_save_arg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_runtime_state_root(Path(tmp))
            (root / "state.sav").write_bytes(bytes(0x8000))

            report = build_replay_plan(
                rom_path="pokegold.gbc",
                symbols_path="pokegold.sym",
                save_state="state.sav",
                watch_symbols=("wScriptBank",),
                execute_watch=False,
                root=root,
            )

        commands = "\n".join(report["commands"])
        self.assertTrue(report["valid"], report["errors"])
        self.assertIn("state-inspect", commands)
        self.assertIn("watch --rom pokegold.gbc --symbols pokegold.sym --battery-save state.sav", commands)
        self.assertIn("--out-initial-state .local\\tmp\\debugger_replay_continue.state", commands)
        self.assertIn("trace-instructions --rom pokegold.gbc --symbols pokegold.sym", commands)
        self.assertIn("--save-state .local\\tmp\\debugger_replay_continue.state", commands)

    def test_battery_save_inspection_boots_continue_and_reads_runtime_state(self) -> None:
        class FakeRegisters:
            PC = 0x5010
            SP = 0xDFF0
            A = 0
            F = 0
            B = 0
            C = 0
            D = 0
            E = 0
            H = 0
            L = 0

        class FakeMemory:
            def __init__(self) -> None:
                self.data = bytearray(0x2000)

            def __getitem__(self, key):
                if isinstance(key, int) and 0xC000 <= key < 0xE000:
                    return self.data[key - 0xC000]
                return 0

            def __setitem__(self, key, value) -> None:
                if isinstance(key, int) and 0xC000 <= key < 0xE000:
                    self.data[key - 0xC000] = value & 0xFF

        class FakePyBoy:
            def __init__(self, memory: FakeMemory) -> None:
                self.register_file = FakeRegisters()
                self.memory = memory
                self.buttons: list[str] = []

            def button(self, name: str, delay: int = 8) -> None:
                self.buttons.append(name)

            def tick(self, *_args) -> None:
                return None

            def stop(self, save=False) -> None:
                return None

        with tempfile.TemporaryDirectory() as tmp:
            root = make_runtime_state_root(Path(tmp))
            (root / "state.sav").write_bytes(bytes(0x8000))
            memory = FakeMemory()
            write_fake_live_memory(memory.data, script_bank=0x02, script_pos=0x5010, top_return=0x4000)
            fake = FakePyBoy(memory)

            with patch("tools.trace.runtime.open_pyboy", return_value=fake):
                report = build_runtime_state_report(
                    rom_path="pokegold.gbc",
                    symbols_path="pokegold.sym",
                    save_state="state.sav",
                    root=root,
                )

        self.assertTrue(report["valid"], report["errors"])
        self.assertTrue(report["passed"], report["findings"])
        self.assertEqual(report["state_format"], "battery_save_continue")
        self.assertEqual(report["map"]["name"], "TestMap")
        self.assertEqual(report["script_vm"]["bank_address"], "02:5010")
        self.assertEqual(fake.buttons, ["start", "a", "a", "a"])


def make_runtime_state_root(root: Path) -> Path:
    (root / "constants").mkdir(parents=True)
    (root / "data" / "maps").mkdir(parents=True)
    (root / "maps").mkdir()
    rom = bytearray(0xC000)
    rom[0x134:0x13C] = b"DBGTEST\0"
    rom[0x9000] = 0x91
    rom[0x9010] = 0x65
    (root / "pokegold.gbc").write_bytes(rom)
    (root / "pokegold.sym").write_text(
        "\n".join(
            [
                "00:0100 Start",
                "02:5000 TestMap_MapScripts",
                "02:5010 TestMap.Script",
                "02:5020 TestMap.CallbackReturn",
                "02:5100 TestMap_MapEvents",
                "01:D116 wBattleMode",
                "01:D119 wBattleType",
                "01:D15E wScriptMode",
                "01:D15F wScriptRunning",
                "01:D160 wScriptBank",
                "01:D161 wScriptPos",
                "01:D163 wScriptStackSize",
                "01:D164 wScriptStack",
                "01:D173 wScriptVar",
                "01:D174 wScriptDelay",
                "01:D180 wBattleScriptFlags",
                "01:D08C wMapScriptsBank",
                "01:D08D wMapScriptsPointer",
                "01:DA00 wMapGroup",
                "01:DA01 wMapNumber",
                "01:DA02 wYCoord",
                "01:DA03 wXCoord",
                "01:DA22 wPartyCount",
                "01:DA23 wPartySpecies",
                "00:CF29 wSeenTrainerBank",
                "00:CF36 wScriptAfterPointer",
                "00:CF38 wRunningTrainerBattleScript",
                "01:D059 wTrainerBattleContextBackupActive",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "constants" / "map_constants.asm").write_text(
        "\n".join(
            [
                "const_def",
                "newgroup TEST",
                "map_const TEST_MAP, 10, 9",
                "endgroup",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "data" / "maps" / "attributes.asm").write_text(
        "map_attributes TestMap, TEST_MAP, $00, 0\n",
        encoding="utf-8",
    )
    (root / "maps" / "TestMap.asm").write_text(
        "TestMap_MapScripts:\n\tdef_scene_scripts\nTestMap_MapEvents:\n",
        encoding="utf-8",
    )
    return root


def write_fake_live_memory(
    data: bytearray,
    *,
    script_bank: int,
    script_pos: int,
    top_return: int,
) -> None:
    def write_d(address: int, values: list[int]) -> None:
        offset = 0x1000 + (address - 0xD000)
        data[offset:offset + len(values)] = bytes(values)

    def write_c(address: int, values: list[int]) -> None:
        offset = address - 0xC000
        data[offset:offset + len(values)] = bytes(values)

    write_d(0xDA00, [0x01, 0x01, 0x04, 0x05])
    write_d(0xDA22, [0x01, 0xB4, 0xFF])
    write_d(0xD08C, [0x02, 0x00, 0x50])
    write_d(0xD15E, [0x01, 0x01, script_bank, script_pos & 0xFF, script_pos >> 8])
    write_d(0xD163, [0])
    write_d(0xDFF0, [top_return & 0xFF, top_return >> 8])
    write_c(0xCF29, [0x02])
    write_c(0xCF36, [0x10, 0x50])
    write_c(0xCF38, [0x01])


def write_fake_sgm(
    path: Path,
    *,
    script_bank: int,
    script_pos: int,
    stack_frames: list[tuple[int, int]],
    top_return: int,
    include_decoy: bool = False,
) -> None:
    data = bytearray(0x4000)
    write_u32(data, 0, 12)
    data[4:20] = b"POKEMON_GLDAAUE\0"
    register_offset = 27
    write_u16(data, register_offset, 0x1234)
    write_u16(data, register_offset + 2, 0xDFF0)
    write_u16(data, register_offset + 4, 0xCF50)
    write_u16(data, register_offset + 6, 0x060C)
    write_u16(data, register_offset + 8, 0x16E5)
    write_u16(data, register_offset + 10, 0x2880)

    def write_d(address: int, values: list[int]) -> None:
        offset = 0x2000 + (address - 0xD000)
        data[offset:offset + len(values)] = bytes(values)

    def write_c(address: int, values: list[int]) -> None:
        offset = 0x1000 + (address - 0xC000)
        data[offset:offset + len(values)] = bytes(values)

    def write_decoy_d(address: int, values: list[int]) -> None:
        offset = 0x0200 + (address - 0xD000)
        data[offset:offset + len(values)] = bytes(values)

    if include_decoy:
        write_decoy_d(0xDA00, [0x01, 0x33, 0x04, 0x05])
        write_decoy_d(0xDA22, [0x01, 0xAB, 0xFF])
        write_decoy_d(0xD08C, [0x0D, 0x00, 0x50])
        write_decoy_d(0xD15E, [0x00, 0x00, 0x00, 0x00, 0x00])
        write_decoy_d(0xD163, [0x00])

    write_d(0xDA00, [0x01, 0x01, 0x04, 0x05])
    write_d(0xDA22, [0x01, 0xB4, 0xFF])
    write_d(0xD08C, [0x02, 0x00, 0x50])
    write_d(0xD15E, [0x01, 0x01, script_bank, script_pos & 0xFF, script_pos >> 8])
    write_d(0xD163, [len(stack_frames)])
    stack_bytes: list[int] = []
    for raw_bank, address in stack_frames:
        stack_bytes.extend([raw_bank, address & 0xFF, address >> 8])
    stack_bytes.extend([0] * (15 - len(stack_bytes)))
    write_d(0xD164, stack_bytes)
    write_d(0xDFF0, [top_return & 0xFF, top_return >> 8])
    write_c(0xCF29, [0x02])
    write_c(0xCF36, [0x10, 0x50])
    write_c(0xCF38, [0x01])
    path.write_bytes(gzip.compress(bytes(data)))


def write_u16(data: bytearray, offset: int, value: int) -> None:
    data[offset] = value & 0xFF
    data[offset + 1] = value >> 8


def write_u32(data: bytearray, offset: int, value: int) -> None:
    data[offset] = value & 0xFF
    data[offset + 1] = (value >> 8) & 0xFF
    data[offset + 2] = (value >> 16) & 0xFF
    data[offset + 3] = (value >> 24) & 0xFF
