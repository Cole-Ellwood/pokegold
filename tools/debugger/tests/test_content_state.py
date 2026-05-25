from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.debugger.content_state import build_content_state_report


class ContentStateTests(unittest.TestCase):
    def test_content_state_materializes_map_precondition_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data" / "maps").mkdir(parents=True)
            (root / "data" / "maps" / "maps.asm").write_text(
                "\n".join(
                    [
                        "MapGroup_NewBark:",
                        "\ttable_width MAP_LENGTH",
                        "\tmap Route29, TILESET_JOHTO, ROUTE, LANDMARK_ROUTE_29, MUSIC_ROUTE_29, FALSE, PALETTE_AUTO, FISHGROUP_SHORE",
                        "\tmap NewBarkTown, TILESET_JOHTO, TOWN, LANDMARK_NEW_BARK_TOWN, MUSIC_NEW_BARK_TOWN, FALSE, PALETTE_AUTO, FISHGROUP_OCEAN",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:DA00 wMapGroup",
                        "01:DA01 wMapNumber",
                        "01:DA02 wYCoord",
                        "01:DA03 wXCoord",
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
                                "scenario_type": "map_warp",
                                "source_file": "maps/NewBarkTown.asm",
                                "state_preconditions": [
                                    {
                                        "id": "map_warp_position",
                                        "kind": "map_position",
                                        "values": {
                                            "map_label": "NewBarkTown_MapEvents",
                                            "source_file": "maps/NewBarkTown.asm",
                                            "x": 6,
                                            "y": 3,
                                        },
                                        "watch_symbols": ["wMapGroup", "wMapNumber", "wXCoord", "wYCoord"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_content_state_report(
                reports=("content.json",),
                scenario_ids=("content_scenario_1_0000",),
                symbols_path="test.sym",
                root=root,
            )

        patches = {
            patch["symbol"]: patch
            for patch in report["materializations"][0]["patches"]
        }

        self.assertTrue(report["valid"])
        self.assertEqual(report["patch_count"], 4)
        self.assertEqual(report["materializations"][0]["status"], "ready")
        self.assertEqual(report["materializations"][0]["map_resolution"]["map_group"], 1)
        self.assertEqual(report["materializations"][0]["map_resolution"]["map_number"], 2)
        self.assertEqual(patches["wMapGroup"]["value"], 1)
        self.assertEqual(patches["wMapNumber"]["value"], 2)
        self.assertEqual(patches["wXCoord"]["value"], 6)
        self.assertEqual(patches["wYCoord"]["value"], 3)

    def test_content_state_materializes_script_entry_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "02:5000 UnitScript",
                        "01:DA10 wScriptBank",
                        "01:DA11 wScriptPos",
                        "01:DA13 wScriptRunning",
                        "01:DA14 wScriptMode",
                        "01:DA15 wScriptStackSize",
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
                                "scenario_type": "script_command_stream",
                                "source_file": "maps/UnitMap.asm",
                                "label": "UnitScript",
                                "state_preconditions": [
                                    {
                                        "id": "script_engine_entry",
                                        "kind": "script_entry",
                                        "values": {
                                            "script_label": "UnitScript",
                                            "source_file": "maps/UnitMap.asm",
                                        },
                                        "watch_symbols": ["wScriptBank", "wScriptPos"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_content_state_report(
                reports=("content.json",),
                scenario_ids=("content_scenario_1_0000",),
                symbols_path="test.sym",
                root=root,
            )

        materialization = report["materializations"][0]
        patches = {patch["symbol"]: patch for patch in materialization["patches"]}
        commands = "\n".join(materialization["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["error_count"], 0)
        self.assertEqual(report["patch_count"], 6)
        self.assertEqual(materialization["status"], "ready")
        self.assertEqual(materialization["precondition_kind"], "script_entry")
        self.assertEqual(materialization["script_resolution"]["bank_address"], "02:5000")
        self.assertEqual(patches["wScriptBank"]["value"], 0x02)
        self.assertEqual(patches["wScriptPos"]["value"], 0x00)
        self.assertEqual(patches["wScriptPos+1"]["value"], 0x50)
        self.assertEqual(patches["wScriptPos+1"]["address"], 0xDA12)
        self.assertEqual(patches["wScriptRunning"]["value"], 0xFF)
        self.assertEqual(patches["wScriptMode"]["value"], 0x01)
        self.assertEqual(patches["wScriptStackSize"]["value"], 0x00)
        self.assertIn("--symbol ScriptEvents --symbol RunScriptCommand", commands)
        self.assertIn("--watch-symbol wScriptPos --watch-symbol wScriptVar", commands)

    def test_content_state_materializes_movement_entry_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "02:6000 UnitMovement",
                        "01:DB00 wMovementObject",
                        "01:DB01 wMovementDataBank",
                        "01:DB02 wMovementDataAddress",
                        "01:DB04 wMovementPointer",
                        "01:DB06 wScriptMode",
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
                                "source_file": "scripts/unit_movement.asm",
                                "label": "UnitMovement",
                                "state_preconditions": [
                                    {
                                        "id": "movement_engine_entry",
                                        "kind": "movement_entry",
                                        "values": {
                                            "movement_label": "UnitMovement",
                                            "source_file": "scripts/unit_movement.asm",
                                            "object_id": 0,
                                        },
                                        "watch_symbols": ["wMovementPointer", "wMovementObject"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_content_state_report(
                reports=("content.json",),
                scenario_ids=("content_scenario_1_0000",),
                symbols_path="test.sym",
                root=root,
            )

        materialization = report["materializations"][0]
        patches = {patch["symbol"]: patch for patch in materialization["patches"]}
        commands = "\n".join(materialization["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["error_count"], 0)
        self.assertEqual(report["patch_count"], 7)
        self.assertEqual(materialization["status"], "ready")
        self.assertEqual(materialization["precondition_kind"], "movement_entry")
        self.assertEqual(materialization["movement_resolution"]["bank_address"], "02:6000")
        self.assertEqual(patches["wMovementObject"]["value"], 0x00)
        self.assertEqual(patches["wMovementDataBank"]["value"], 0x02)
        self.assertEqual(patches["wMovementDataAddress"]["value"], 0x00)
        self.assertEqual(patches["wMovementDataAddress+1"]["value"], 0x60)
        self.assertEqual(patches["wMovementDataAddress+1"]["address"], 0xDB03)
        self.assertEqual(patches["wMovementPointer"]["value"], 0x00)
        self.assertEqual(patches["wMovementPointer+1"]["value"], 0x60)
        self.assertEqual(patches["wMovementPointer+1"]["address"], 0xDB05)
        self.assertEqual(patches["wScriptMode"]["value"], 0x02)
        self.assertIn("--symbol ApplyMovement --symbol GetMovementData --symbol HandleMovementData", commands)
        self.assertIn("--watch-symbol wMovementDataAddress --watch-symbol wMovementPointer", commands)

    def test_content_state_plans_audio_and_asset_runtime_proofs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.sym").write_text("00:0000 NULL\n", encoding="utf-8")
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "audio_channel_block",
                                "source_file": "audio/unit.asm",
                                "label": "Music_Unit",
                                "state_preconditions": [
                                    {
                                        "id": "audio_channel_runtime",
                                        "kind": "audio_engine_entry",
                                        "values": {
                                            "music_label": "Music_Unit",
                                            "source_file": "audio/unit.asm",
                                            "channel_count": 2,
                                        },
                                    }
                                ],
                            },
                            {
                                "id": "content_scenario_1_0001",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "asset_materialization",
                                "source_file": "gfx/unit.asm",
                                "label": "UnitGraphic",
                                "state_preconditions": [
                                    {
                                        "id": "asset_loader_runtime",
                                        "kind": "asset_loader_entry",
                                        "values": {
                                            "asset": "gfx/unit.2bpp",
                                            "source_file": "gfx/unit.asm",
                                            "label": "UnitGraphic",
                                        },
                                    }
                                ],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_content_state_report(
                reports=("content.json",),
                symbols_path="test.sym",
                root=root,
            )

        materializations = {
            item["precondition_kind"]: item
            for item in report["materializations"]
        }
        audio_commands = "\n".join(materializations["audio_engine_entry"]["commands"])
        asset_commands = "\n".join(materializations["asset_loader_entry"]["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["patch_count"], 0)
        self.assertEqual(report["materialization_count"], 2)
        self.assertEqual(materializations["audio_engine_entry"]["status"], "planned")
        self.assertIn("wMusicID", materializations["audio_engine_entry"]["watch_symbols"])
        self.assertIn("--symbol PlayMusic --symbol _PlayMusic", audio_commands)
        self.assertIn("--watch-symbol wMusicID", audio_commands)
        self.assertEqual(materializations["asset_loader_entry"]["status"], "planned")
        self.assertIn("wRequested2bppSource", materializations["asset_loader_entry"]["watch_symbols"])
        self.assertIn("--symbol Request2bpp --symbol Get1bpp --symbol Decompress", asset_commands)
        self.assertIn("--watch-symbol wRequested2bppSource", asset_commands)

    def test_content_state_execute_patches_and_writes_state(self) -> None:
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
            (root / "data" / "maps").mkdir(parents=True)
            (root / "data" / "maps" / "maps.asm").write_text(
                "MapGroup_NewBark:\n\tmap NewBarkTown, TILESET_JOHTO, TOWN, LANDMARK_NEW_BARK_TOWN, MUSIC_NEW_BARK_TOWN, FALSE, PALETTE_AUTO, FISHGROUP_OCEAN\n",
                encoding="utf-8",
            )
            (root / "test.sym").write_text(
                "01:DA00 wMapGroup\n01:DA01 wMapNumber\n01:DA02 wYCoord\n01:DA03 wXCoord\n",
                encoding="utf-8",
            )
            (root / "rom.gbc").write_bytes(b"rom")
            (root / "base.state").write_bytes(b"base")
            out_state = root / "patched.state"
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0000",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "map_bg_event",
                                "source_file": "maps/NewBarkTown.asm",
                                "state_preconditions": [
                                    {
                                        "id": "map_bg_event_position",
                                        "kind": "map_position",
                                        "values": {"map_label": "NewBarkTown_MapEvents", "x": 4, "y": 5},
                                        "watch_symbols": ["wMapGroup"],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            fake = FakePyBoy()

            with patch("tools.debugger.content_state.trace_runtime.open_pyboy", return_value=fake):
                report = build_content_state_report(
                    reports=("content.json",),
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
        self.assertEqual(report["execution"]["patch_count"], 4)
        self.assertEqual(written, b"patched-state")
        self.assertTrue(fake.loaded)
        self.assertTrue(fake.stopped)
