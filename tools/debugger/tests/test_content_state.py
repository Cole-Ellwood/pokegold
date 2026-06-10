from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.debugger.canonical_state_class import validate_canonical_state_class
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
        self.assertRegex(report["materializations"][0]["class_id"], r"^csc_[0-9A-F]{20}$")
        self.assertEqual(
            validate_canonical_state_class(report["materializations"][0]["canonical_state_class"]),
            [],
        )
        self.assertEqual(
            report["materializations"][0]["canonical_state_class"]["surface_facts"]["content"]["precondition_kind"],
            "map_position",
        )
        self.assertEqual(patches["wMapGroup"]["value"], 1)
        self.assertEqual(patches["wMapNumber"]["value"], 2)
        self.assertEqual(patches["wXCoord"]["value"], 6)
        self.assertEqual(patches["wYCoord"]["value"], 3)

    def test_content_state_materializes_object_visibility_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data" / "maps").mkdir(parents=True)
            (root / "data" / "sprites").mkdir(parents=True)
            (root / "maps").mkdir()
            (root / "data" / "maps" / "maps.asm").write_text(
                "\n".join(
                    [
                        "MapGroup_Unit:",
                        "\ttable_width MAP_LENGTH",
                        "\tmap UnitMap, TILESET_JOHTO, TOWN, LANDMARK_NEW_BARK_TOWN, MUSIC_NONE, FALSE, PALETTE_AUTO, FISHGROUP_NONE",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "data" / "sprites" / "map_objects.asm").write_text(
                "\n".join(
                    [
                        "SpriteMovementData::",
                        "\tdb 6",
                        "\tdb 2",
                        "\tdb 1",
                        "\tdb 0",
                        "\tdb 0",
                        "\tdb 0",
                        "\tassert_table_length 1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "UnitMap_MapEvents:",
                        "\tdef_object_events",
                        "\tobject_event 5, 7, 3, 0, 0, 0, -1, -1, 0, 0, 0, UnitScript, -1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "02:5000 UnitScript",
                        "01:DA00 wMapGroup",
                        "01:DA01 wMapNumber",
                        "01:DA02 wYCoord",
                        "01:DA03 wXCoord",
                        "01:DB00 wMap2ObjectStructID",
                        "01:DB01 wMap2ObjectSprite",
                        "01:DB02 wMap2ObjectYCoord",
                        "01:DB03 wMap2ObjectXCoord",
                        "01:DB04 wMap2ObjectMovement",
                        "01:DB05 wMap2ObjectRadius",
                        "01:DB06 wMap2ObjectHour1",
                        "01:DB07 wMap2ObjectHour2",
                        "01:DB08 wMap2ObjectType",
                        "01:DB09 wMap2ObjectSightRange",
                        "01:DB0A wMap2ObjectScript",
                        "01:DB0C wMap2ObjectEventFlag",
                        "01:DC00 wObject1MapObjectIndex",
                        "01:DC01 wObject1Sprite",
                        "01:DC02 wObject1MovementType",
                        "01:DC03 wObject1Flags",
                        "01:DC05 wObject1Palette",
                        "01:DC06 wObject1Walking",
                        "01:DC07 wObject1Direction",
                        "01:DC08 wObject1StepType",
                        "01:DC09 wObject1Action",
                        "01:DC0A wObject1Facing",
                        "01:DC0B wObject1MapX",
                        "01:DC0C wObject1MapY",
                        "01:DC0D wObject1LastMapX",
                        "01:DC0E wObject1LastMapY",
                        "01:DC0F wObject1InitX",
                        "01:DC10 wObject1InitY",
                        "01:DC11 wObject1Radius",
                        "01:DC12 wObject1Range",
                        "01:DD00 wObjectMasks",
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
                                "id": "content_scenario_1_0019",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "map_object_event",
                                "source_file": "maps/UnitMap.asm",
                                "line": 3,
                                "trigger": {
                                    "x": "5",
                                    "y": "7",
                                    "object_type": "0",
                                    "script": "UnitScript",
                                    "event_flag": "-1",
                                },
                                "state_preconditions": [
                                    {
                                        "id": "map_object_event_position",
                                        "kind": "map_position",
                                        "values": {
                                            "map_label": "UnitMap_MapEvents",
                                            "source_file": "maps/UnitMap.asm",
                                            "x": 5,
                                            "y": 7,
                                        },
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
                scenario_ids=("content_scenario_1_0019",),
                symbols_path="test.sym",
                root=root,
            )

        materialization = report["materializations"][0]
        visibility = materialization["object_visibility_materializer"]
        visibility_patches = {patch["symbol"]: patch for patch in visibility["patches"]}

        self.assertTrue(report["valid"])
        self.assertEqual(report["patch_count"], 4)
        self.assertEqual(materialization["status"], "ready")
        self.assertEqual(visibility["status"], "ready")
        self.assertEqual(visibility["proof_status"], "static_synthetic")
        self.assertEqual(visibility["map_object_index"], 2)
        self.assertEqual(visibility["object_struct_index"], 1)
        self.assertEqual(visibility_patches["wMap2ObjectStructID"]["value"], 1)
        self.assertEqual(visibility_patches["wMap2ObjectYCoord"]["value"], 11)
        self.assertEqual(visibility_patches["wMap2ObjectXCoord"]["value"], 9)
        self.assertEqual(visibility_patches["wMap2ObjectScript"]["value"], 0x00)
        self.assertEqual(visibility_patches["wMap2ObjectScript+1"]["value"], 0x50)
        self.assertEqual(visibility_patches["wObject1MapObjectIndex"]["value"], 2)
        self.assertEqual(visibility_patches["wObject1Walking"]["value"], 0xFF)
        self.assertEqual(visibility_patches["wObject1Direction"]["value"], 8)
        self.assertEqual(visibility_patches["wObject1MapX"]["value"], 9)
        self.assertEqual(visibility_patches["wObject1MapY"]["value"], 11)
        self.assertEqual(visibility_patches["wObjectMasks+2"]["address"], 0xDD02)
        self.assertEqual(visibility_patches["wObjectMasks+2"]["value"], 0)

    def test_content_state_blocks_on_unresolvable_movement_constant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data" / "maps").mkdir(parents=True)
            (root / "data" / "sprites").mkdir(parents=True)
            (root / "maps").mkdir()
            (root / "data" / "maps" / "maps.asm").write_text(
                "\n".join(
                    [
                        "MapGroup_Unit:",
                        "\ttable_width MAP_LENGTH",
                        "\tmap UnitMap, TILESET_JOHTO, TOWN, LANDMARK_NEW_BARK_TOWN, MUSIC_NONE, FALSE, PALETTE_AUTO, FISHGROUP_NONE",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "data" / "sprites" / "map_objects.asm").write_text(
                "\n".join(
                    [
                        "SpriteMovementData::",
                        "\tdb 6",
                        "\tdb 2",
                        "\tdb 1",
                        "\tdb 0",
                        "\tdb 0",
                        "\tdb 0",
                        "\tassert_table_length 1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "UnitMap_MapEvents:",
                        "\tdef_object_events",
                        "\tobject_event 5, 7, 3, SPRITEMOVEDATA_NOT_A_REAL_CONSTANT, 0, 0, -1, -1, 0, 0, 0, UnitScript, -1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "test.sym").write_text(
                "02:5000 UnitScript\n01:DA00 wMapGroup\n",
                encoding="utf-8",
            )
            (root / "content.json").write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_scenarios",
                        "valid": True,
                        "scenarios": [
                            {
                                "id": "content_scenario_1_0019",
                                "kind": "unified_debugger_content_scenario",
                                "scenario_type": "map_object_event",
                                "source_file": "maps/UnitMap.asm",
                                "line": 3,
                                "trigger": {
                                    "x": "5",
                                    "y": "7",
                                    "object_type": "0",
                                    "script": "UnitScript",
                                    "event_flag": "-1",
                                },
                                "state_preconditions": [
                                    {
                                        "id": "map_object_event_position",
                                        "kind": "map_position",
                                        "values": {
                                            "map_label": "UnitMap_MapEvents",
                                            "source_file": "maps/UnitMap.asm",
                                            "x": 5,
                                            "y": 7,
                                        },
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
                scenario_ids=("content_scenario_1_0019",),
                symbols_path="test.sym",
                root=root,
            )

        visibility = report["materializations"][0]["object_visibility_materializer"]
        self.assertEqual(visibility["status"], "blocked")
        self.assertTrue(
            any("movement" in error for error in visibility["errors"]),
            visibility["errors"],
        )

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
                                            "selected_script_label": "ShouldNotEnterPublicFacts",
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
        self.assertRegex(materialization["class_id"], r"^csc_[0-9A-F]{20}$")
        self.assertEqual(validate_canonical_state_class(materialization["canonical_state_class"]), [])
        self.assertEqual(
            materialization["canonical_state_class"]["public_facts"]["script_label"],
            "UnitScript",
        )
        self.assertNotIn(
            "selected_script_label",
            materialization["canonical_state_class"]["public_facts"]["values"],
        )
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
