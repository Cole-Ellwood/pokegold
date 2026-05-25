from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.content_mirror import build_content_mirror_report


class ContentMirrorTests(unittest.TestCase):
    def test_content_mirror_validates_map_event_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "\tobject_const_def",
                        "\tconst UNITMAP_NPC",
                        "",
                        "UnitMap_MapScripts:",
                        "\tdef_scene_scripts",
                        "\tdef_callbacks",
                        "",
                        "UnitMap_MapEvents:",
                        "\tdb 0, 0 ; filler",
                        "",
                        "\tdef_warp_events",
                        "\twarp_event 1, 2, ROUTE_29, 1",
                        "",
                        "\tdef_coord_events",
                        "\tcoord_event 2, 3, SCENE_UNITMAP, UnitMapScene",
                        "",
                        "\tdef_bg_events",
                        "\tbg_event 4, 5, BGEVENT_READ, UnitMapSign",
                        "",
                        "\tdef_object_events",
                        "\tobject_event 6, 7, SPRITE_CHRIS, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, 0, OBJECTTYPE_SCRIPT, 0, UnitMapNPCScript, -1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("maps/UnitMap.asm",),
                root=root,
            )

        invariant_ids = {item["id"] for item in report["invariants"]}
        commands = "\n".join(report["commands"])

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertEqual(report["failed_invariant_count"], 0)
        self.assertIn("maps/UnitMap.asm:map_warp_event_section", invariant_ids)
        self.assertIn("maps/UnitMap.asm:map_object_event_section", invariant_ids)
        self.assertIn("tools.debugger content-mirror --source-file maps/UnitMap.asm", commands)
        self.assertIn("tools.debugger expect --source-file maps/UnitMap.asm", commands)

    def test_content_mirror_compares_map_events_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "maps").mkdir()
            (root / "constants").mkdir()
            (root / "constants" / "map_constants.asm").write_text(
                "\n".join(
                    [
                        "const_def",
                        "newgroup NEW_BARK",
                        "map_const ROUTE_29, 30, 9",
                        "endgroup",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "constants" / "script_constants.asm").write_text(
                "const_def\nconst BGEVENT_READ\n",
                encoding="utf-8",
            )
            (root / "maps" / "UnitMap.asm").write_text(
                "\n".join(
                    [
                        "UnitMapSign:",
                        "\tjumptext UnitMapSignText",
                        "",
                        "UnitMap_MapEvents:",
                        "\tdb 0, 0 ; filler",
                        "\tdef_warp_events",
                        "\twarp_event 1, 2, ROUTE_29, 1",
                        "\tdef_coord_events",
                        "\tdef_bg_events",
                        "\tbg_event 4, 5, BGEVENT_READ, UnitMapSign",
                        "\tdef_object_events",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes(
                [
                    0,
                    0,
                    1,
                    2,
                    1,
                    1,
                    1,
                    1,
                    0,
                    1,
                    5,
                    4,
                    0,
                    0x20,
                    0x01,
                    0,
                ]
            )
            rom = bytearray([0xFF] * 0x200)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "00:0100 UnitMap_MapEvents\n00:0120 UnitMapSign\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("maps/UnitMap.asm",),
                root=root,
            )
            rom[0x100 + 4] = 9
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("maps/UnitMap.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        self.assertTrue(report["rom_available"])
        map_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "map_event_rom_bytes"]
        self.assertEqual(len(map_mirrors), 1)
        self.assertEqual(map_mirrors[0]["status"], "passed")
        self.assertIn(
            "maps/UnitMap.asm:map_event_rom_bytes",
            {item["id"] for item in report["rom_mirrors"]},
        )
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        failed_map_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_map_mirror["type"], "map_event_rom_bytes")
        self.assertIn("first_mismatch=", "\n".join(failed_map_mirror["evidence"]))

    def test_content_mirror_compares_labeled_incbin_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gfx").mkdir()
            source = root / "gfx" / "unit.asm"
            asset = root / "gfx" / "unit.2bpp"
            source.write_text(
                "UnitGraphic:\nINCBIN \"gfx/unit.2bpp\"\n",
                encoding="utf-8",
            )
            asset.write_bytes(bytes([1, 2, 3, 4, 5]))
            rom = bytearray([0xFF] * 0x200)
            rom[0x100:0x105] = asset.read_bytes()
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text("00:0100 UnitGraphic\n", encoding="utf-8")

            report = build_content_mirror_report(
                source_files=("gfx/unit.asm",),
                root=root,
            )
            rom[0x102] = 9
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("gfx/unit.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(report["rom_mirror_count"], 1)
        self.assertEqual(report["passed_rom_mirror_count"], 1)
        self.assertIn("incbin_asset_rom_bytes", {item["type"] for item in report["rom_mirrors"]})
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        self.assertIn("first_mismatch=", "\n".join(mismatch["rom_mirrors"][0]["evidence"]))

    def test_content_mirror_compares_incbin_table_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gfx").mkdir()
            source = root / "gfx" / "table.asm"
            first = root / "gfx" / "first.bin"
            second = root / "gfx" / "second.bin"
            source.write_text(
                "\n".join(
                    [
                        'DEF first_slice EQUS "1, 2"',
                        "UnitTable:",
                        "\ttable_width 4",
                        '\tINCBIN "gfx/first.bin", first_slice',
                        '\tINCBIN "gfx/second.bin"',
                        "\tassert_table_length 2",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            first.write_bytes(bytes([0, 1, 2, 9]))
            second.write_bytes(bytes([3, 4]))
            expected = bytes([1, 2, 3, 4])
            rom = bytearray([0xFF] * 0x200)
            rom[0x100:0x104] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text("00:0100 UnitTable\n", encoding="utf-8")

            report = build_content_mirror_report(
                source_files=("gfx/table.asm",),
                root=root,
            )
            rom[0x103] = 8
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("gfx/table.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        table_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "incbin_table_rom_bytes"]
        self.assertEqual(len(table_mirrors), 1)
        self.assertEqual(table_mirrors[0]["status"], "passed")
        self.assertFalse(mismatch["passed"])
        failed_table_mirror = next(item for item in mismatch["rom_mirrors"] if item["type"] == "incbin_table_rom_bytes" and item["status"] == "failed")
        self.assertIn("first_mismatch=", "\n".join(failed_table_mirror["evidence"]))

    def test_content_mirror_compares_audio_channel_header_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "audio").mkdir()
            source = root / "audio" / "unit.asm"
            source.write_text(
                "\n".join(
                    [
                        "Music_Unit:",
                        "\tchannel_count 2",
                        "\tchannel 1, Music_Unit_Ch1",
                        "\tchannel 2, Music_Unit_Ch2",
                        "Music_Unit_Ch1:",
                        "\tnote C_, 1",
                        "Music_Unit_Ch2:",
                        "\tnote D_, 1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes([0x40, 0x20, 0x01, 0x01, 0x30, 0x01])
            rom = bytearray([0xFF] * 0x200)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "00:0100 Music_Unit\n00:0120 Music_Unit_Ch1\n00:0130 Music_Unit_Ch2\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("audio/unit.asm",),
                root=root,
            )
            rom[0x100] = 0x30
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("audio/unit.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        audio_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "audio_channel_rom_bytes"]
        self.assertEqual(len(audio_mirrors), 1)
        self.assertEqual(audio_mirrors[0]["status"], "passed")
        self.assertFalse(mismatch["passed"])
        failed_audio_mirror = next(item for item in mismatch["rom_mirrors"] if item["type"] == "audio_channel_rom_bytes" and item["status"] == "failed")
        self.assertIn("first_mismatch=", "\n".join(failed_audio_mirror["evidence"]))

    def test_content_mirror_compares_labeled_data_block_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constants").mkdir()
            (root / "data").mkdir()
            (root / "constants" / "charmap.asm").write_text(
                "\n".join(
                    [
                        'charmap "<NEXT>", $4e',
                        'charmap "@", $50',
                        'charmap "U", $80',
                        'charmap "N", $81',
                        'charmap "I", $82',
                        'charmap "T", $83',
                        'charmap "O", $84',
                        'charmap "K", $85',
                        'charmap "3", $86',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "constants" / "unit_constants.asm").write_text(
                "DEF CONST_VALUE EQU $03\n",
                encoding="utf-8",
            )
            source = root / "data" / "unit.asm"
            source.write_text(
                "\n".join(
                    [
                        "UnitData:",
                        "\tdb 1, $02, CONST_VALUE",
                        "\tdw UnitTarget",
                        "\tdn 3, 4",
                        "\tdb \"UNIT{d:CONST_VALUE}@\"",
                        "\tnext \"OK@\"",
                        "",
                        "UnitTarget:",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes([1, 2, 3, 0x34, 0x12, 0x34, 0x80, 0x81, 0x82, 0x83, 0x86, 0x50, 0x4E, 0x84, 0x85, 0x50])
            rom = bytearray([0xFF] * 0x2000)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "00:0100 UnitData\n00:1234 UnitTarget\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("data/unit.asm",),
                root=root,
            )
            rom[0x103] = 9
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("data/unit.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(report["source_files"][0]["data_block_count"], 1)
        self.assertEqual(report["rom_mirror_count"], 1)
        self.assertEqual(report["passed_rom_mirror_count"], 1)
        self.assertIn("labeled_data_rom_bytes", {item["type"] for item in report["rom_mirrors"]})
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        self.assertIn("first_mismatch=", "\n".join(mismatch["rom_mirrors"][0]["evidence"]))

    def test_content_mirror_compares_script_commands_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            source = root / "scripts" / "unit_script.asm"
            source.write_text(
                "\n".join(
                    [
                        "UnitScript:",
                        "\topentext",
                        "\twritetext UnitText",
                        "\twaitbutton",
                        "\tclosetext",
                        "\tend",
                        "",
                        "UnitJump:",
                        "\tjumptext UnitText",
                        "",
                        "UnitFlagCallback:",
                        "\tsetflag ENGINE_UNIT_FLAG",
                        "\tendcallback",
                        "",
                        "UnitText:",
                        "\ttext \"HELLO\"",
                        "\tdone",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            script_bytes = bytes([0x47, 0x4C, 0x80, 0x01, 0x53, 0x49, 0x90])
            jump_bytes = bytes([0x52, 0x80, 0x01])
            flag_bytes = bytes([0x36, 0x34, 0x12, 0x8F])
            rom = bytearray([0xFF] * 0x400)
            rom[0x100:0x100 + len(script_bytes)] = script_bytes
            rom[0x120:0x120 + len(jump_bytes)] = jump_bytes
            rom[0x140:0x140 + len(flag_bytes)] = flag_bytes
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitScript",
                        "00:0120 UnitJump",
                        "00:0140 UnitFlagCallback",
                        "00:0180 UnitText",
                        "47 opentext_command",
                        "4c writetext_command",
                        "53 waitbutton_command",
                        "49 closetext_command",
                        "90 end_command",
                        "52 jumptext_command",
                        "36 setflag_command",
                        "8f endcallback_command",
                        "1234 ENGINE_UNIT_FLAG",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_script.asm",),
                root=root,
            )
            rom[0x102] = 0x81
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_script.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(report["source_files"][0]["script_block_count"], 3)
        script_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "script_command_rom_bytes"]
        self.assertEqual(len(script_mirrors), 3)
        self.assertTrue(all(item["status"] == "passed" for item in script_mirrors))
        self.assertIn("script_command_rom_bytes", {item["type"] for item in report["rom_mirrors"]})
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        failed_script_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_script_mirror["type"], "script_command_rom_bytes")
        self.assertIn("first_mismatch=", "\n".join(failed_script_mirror["evidence"]))

    def test_content_mirror_compares_map_script_action_commands_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constants").mkdir()
            (root / "scripts").mkdir()
            (root / "constants" / "trainer_constants.asm").write_text(
                "\n".join(
                    [
                        "DEF __trainer_class__ = 7",
                        "\ttrainerclass RIVAL1",
                        "\tconst RIVAL1_2_TOTODILE",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "constants" / "item_constants.asm").write_text(
                "\n".join(
                    [
                        "const_def $bf",
                        "DEF __tmhm_value__ = 1",
                        "\tadd_tm DYNAMICPUNCH",
                        "\tadd_tm LEECH_LIFE",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "constants" / "mart_constants.asm").write_text(
                "\n".join(
                    [
                        "const_def",
                        "\tconst MARTTYPE_STANDARD",
                        "const_def 5",
                        "\tconst MART_UNIT",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            source = root / "scripts" / "unit_map_actions.asm"
            source.write_text(
                "\n".join(
                    [
                        "object_const_def",
                        "\tconst UNIT_OBJECT",
                        "",
                        "UnitActionScript:",
                        "\trandom 6",
                        "\tpokemart MARTTYPE_STANDARD, MART_UNIT",
                        "\tverbosegiveitem TM_LEECH_LIFE",
                        "\tgettrainername STRING_BUFFER_4, RIVAL1, RIVAL1_2_TOTODILE",
                        "\twritecmdqueue UnitQueue",
                        "\tmoveobject UNIT_OBJECT, 11, 12",
                        "\tspecial FadeOutMusic",
                        "\tpause 15",
                        "\tappear UNIT_OBJECT",
                        "\tsetmapscene UNIT_MAP, 2",
                        "\twinlosstext UnitWinText, UnitLoseText",
                        "\tsetlasttalked UNIT_OBJECT",
                        "\tloadtrainer RIVAL1, RIVAL1_2_TOTODILE",
                        "\tstartbattle",
                        "\tdontrestartmapmusic",
                        "\treloadmapafterbattle",
                        "\tplaymusic MUSIC_RIVAL_AFTER",
                        "\tplaymapmusic",
                        "\tdisappear UNIT_OBJECT",
                        "\tend",
                        "",
                        "UnitWinText:",
                        "\ttext \"WIN\"",
                        "\tdone",
                        "",
                        "UnitLoseText:",
                        "\ttext \"LOSE\"",
                        "\tdone",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes(
                [
                    0x17, 0x06,
                    0x93, 0x00, 0x05, 0x00,
                    0x9D, 0xC0, 0x01,
                    0x43, 0x07, 0x01, 0x04,
                    0x7C, 0x20, 0x02,
                    0x71, 0x02, 0x0B, 0x0C,
                    0x0F, 0x03, 0x00,
                    0x8A, 0x0F,
                    0x6E, 0x02,
                    0x12, 0x04, 0x05, 0x02,
                    0x63, 0x90, 0x01, 0xA0, 0x01,
                    0x67, 0x02,
                    0x5D, 0x07, 0x01,
                    0x5E,
                    0x82,
                    0x5F,
                    0x7E, 0x20, 0x00,
                    0x81,
                    0x6D, 0x02,
                    0x90,
                ]
            )
            rom = bytearray([0xFF] * 0x400)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitActionScript",
                        "00:0190 UnitWinText",
                        "00:01a0 UnitLoseText",
                        "00:0200 SpecialsPointers",
                        "00:0209 FadeOutMusicSpecial",
                        "00:0220 UnitQueue",
                        "71 moveobject_command",
                        "17 random_command",
                        "93 pokemart_command",
                        "9d verbosegiveitem_command",
                        "43 gettrainername_command",
                        "7c writecmdqueue_command",
                        "0f special_command",
                        "8a pause_command",
                        "6e appear_command",
                        "12 setmapscene_command",
                        "63 winlosstext_command",
                        "67 setlasttalked_command",
                        "5d loadtrainer_command",
                        "5e startbattle_command",
                        "82 dontrestartmapmusic_command",
                        "5f reloadmapafterbattle_command",
                        "7e playmusic_command",
                        "81 playmapmusic_command",
                        "6d disappear_command",
                        "90 end_command",
                        "04 GROUP_UNIT_MAP",
                        "05 MAP_UNIT_MAP",
                        "20 MUSIC_RIVAL_AFTER",
                        "04 STRING_BUFFER_4",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_map_actions.asm",),
                root=root,
            )
            rom[0x105] = 0x04
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_map_actions.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        script_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "script_command_rom_bytes"]
        self.assertEqual(len(script_mirrors), 1)
        self.assertEqual(script_mirrors[0]["status"], "passed")
        self.assertIn("FadeOutMusicSpecial", script_mirrors[0]["related_symbols"])
        self.assertFalse(mismatch["passed"])
        failed_script_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_script_mirror["type"], "script_command_rom_bytes")
        self.assertIn("first_mismatch=", "\n".join(failed_script_mirror["evidence"]))

    def test_content_mirror_compares_trainer_record_scripts_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constants").mkdir()
            (root / "scripts").mkdir()
            (root / "constants" / "trainer_constants.asm").write_text(
                "\n".join(
                    [
                        "DEF __trainer_class__ = 7",
                        "\ttrainerclass RIVAL1",
                        "\tconst RIVAL1_2_TOTODILE",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            source = root / "scripts" / "unit_trainer.asm"
            source.write_text(
                "\n".join(
                    [
                        "UnitTrainer:",
                        "\ttrainer RIVAL1, RIVAL1_2_TOTODILE, EVENT_BEAT_UNIT, UnitSeenText, UnitWinText, 0, .AfterScript",
                        "",
                        ".AfterScript:",
                        "\tendifjustbattled",
                        "\tend",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes(
                [
                    0x34, 0x12,
                    0x07,
                    0x01,
                    0x00, 0x02,
                    0x10, 0x02,
                    0x00, 0x00,
                    0x0C, 0x01,
                    0x65,
                    0x90,
                ]
            )
            rom = bytearray([0xFF] * 0x400)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitTrainer",
                        "00:010c UnitTrainer.AfterScript",
                        "00:0200 UnitSeenText",
                        "00:0210 UnitWinText",
                        "1234 EVENT_BEAT_UNIT",
                        "65 endifjustbattled_command",
                        "90 end_command",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_trainer.asm",),
                root=root,
            )
            rom[0x100] = 0x35
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_trainer.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        script_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "script_command_rom_bytes"]
        self.assertEqual(len(script_mirrors), 1)
        self.assertEqual(script_mirrors[0]["status"], "passed")
        self.assertFalse(mismatch["passed"])
        failed_script_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_script_mirror["type"], "script_command_rom_bytes")
        self.assertIn("first_mismatch=", "\n".join(failed_script_mirror["evidence"]))

    def test_content_mirror_compares_macro_generated_script_data_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            source = root / "scripts" / "unit_macro_script_data.asm"
            source.write_text(
                "\n".join(
                    [
                        "DEF UNDERGROUND_DOOR_OPEN1 EQU $2d",
                        "",
                        "MACRO ugdoor",
                        "\tDEF UGDOOR_\\1_XCOORD EQU \\2",
                        "\tDEF UGDOOR_\\1_YCOORD EQU \\3",
                        "ENDM",
                        "",
                        "\tugdoor 1, 6, 16",
                        "",
                        "UnitScript:",
                        "\twritecmdqueue UnitQueue",
                        "\tdoorstate 1, OPEN1",
                        "\tcallasm UnitAsm",
                        "\tautoinput UnitAutoInput",
                        "\tgetstring STRING_BUFFER_3, .itemname",
                        "\tend",
                        ".itemname",
                        "\tdb \"BIKE@\"",
                        "",
                        "UnitQueue:",
                        "\tcmdqueue CMDQUEUE_STONETABLE, UnitStoneTable",
                        "",
                        "UnitStoneTable:",
                        "\tstonetable 5, UNIT_OBJECT, UnitFall",
                        "\tdb -1",
                        "",
                        "UnitFall:",
                        "\tdisappear UNIT_OBJECT",
                        "\tend",
                        "",
                        "UnitAsm:",
                        "\tret",
                        "",
                        "UnitAutoInput:",
                        "\tdb $01",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            unit_script = bytes(
                [
                    0x7C, 0x20, 0x01,
                    0x79, 0x10, 0x06, 0x2D,
                    0x0E, 0x02, 0x00, 0x40,
                    0x88, 0x02, 0x10, 0x40,
                    0x44, 0x50, 0x01, 0x03,
                    0x90,
                ]
            )
            queue = bytes([0x02, 0x30, 0x01, 0x00, 0x00])
            stone_table = bytes([0x05, 0x02, 0x40, 0x01, 0xFF])
            fall_script = bytes([0x6D, 0x02, 0x90])
            rom = bytearray([0xFF] * 0x8020)
            rom[0x100:0x100 + len(unit_script)] = unit_script
            rom[0x120:0x120 + len(queue)] = queue
            rom[0x130:0x130 + len(stone_table)] = stone_table
            rom[0x140:0x140 + len(fall_script)] = fall_script
            rom[0x8010] = 0x01
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitScript",
                        "00:0150 UnitScript.itemname",
                        "00:0120 UnitQueue",
                        "00:0130 UnitStoneTable",
                        "00:0140 UnitFall",
                        "02:4000 UnitAsm",
                        "02:4010 UnitAutoInput",
                        "7c writecmdqueue_command",
                        "79 changeblock_command",
                        "0e callasm_command",
                        "88 autoinput_command",
                        "44 getstring_command",
                        "90 end_command",
                        "6d disappear_command",
                        "02 CMDQUEUE_STONETABLE",
                        "02 UNIT_OBJECT",
                        "03 STRING_BUFFER_3",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_macro_script_data.asm",),
                root=root,
            )
            rom[0x134] = 0x00
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_macro_script_data.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        script_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "script_command_rom_bytes"]
        self.assertEqual(
            {item["related_symbols"][0] for item in script_mirrors},
            {"UnitScript", "UnitQueue", "UnitStoneTable", "UnitFall"},
        )
        self.assertTrue(all(item["status"] == "passed" for item in script_mirrors))
        self.assertIn("UnitAsm", script_mirrors[0]["related_symbols"])
        self.assertIn("UnitAutoInput", script_mirrors[0]["related_symbols"])
        self.assertFalse(mismatch["passed"])
        failed_script_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_script_mirror["type"], "script_command_rom_bytes")
        self.assertIn("UnitStoneTable", failed_script_mirror["related_symbols"])
        self.assertIn("first_mismatch=", "\n".join(failed_script_mirror["evidence"]))

    def test_content_mirror_compares_misc_script_commands_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            source = root / "scripts" / "unit_misc_script.asm"
            source.write_text(
                "\n".join(
                    [
                        "UnitMiscScript:",
                        "\tgivemoney YOUR_MONEY, 1000",
                        "\tcheckcoins 300",
                        "\tgetstring STRING_BUFFER_3, UnitString",
                        "\tgivepoke PIKACHU, 5",
                        "\tloadvar VAR_BATTLETYPE, BATTLETYPE_FORCEITEM",
                        "\tloadwildmon HO_OH, 40",
                        "\tvariablesprite SPRITE_FUCHSIA_GYM_1, SPRITE_JANINE",
                        "\tfollow PLAYER, UNIT_OBJECT",
                        "\tstopfollow",
                        "\tend",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes(
                [
                    0x22, 0x00, 0x00, 0x03, 0xE8,
                    0x27, 0x2C, 0x01,
                    0x44, 0x00, 0x02, 0x03,
                    0x2D, 0x19, 0x05, 0x00, 0x00,
                    0x1E, 0x01, 0x02,
                    0x5C, 0xFA, 0x28,
                    0x6C, 0x03, 0x44,
                    0x6F, 0x00, 0x02,
                    0x70,
                    0x90,
                ]
            )
            rom = bytearray([0xFF] * 0x400)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitMiscScript",
                        "00:0200 UnitString",
                        "22 givemoney_command",
                        "27 checkcoins_command",
                        "44 getstring_command",
                        "2d givepoke_command",
                        "1e loadvar_command",
                        "5c loadwildmon_command",
                        "6c variablesprite_command",
                        "6f follow_command",
                        "70 stopfollow_command",
                        "90 end_command",
                        "00 YOUR_MONEY",
                        "03 STRING_BUFFER_3",
                        "00 NO_ITEM",
                        "00 FALSE",
                        "19 PIKACHU",
                        "01 VAR_BATTLETYPE",
                        "02 BATTLETYPE_FORCEITEM",
                        "fa HO_OH",
                        "10 SPRITE_VARS",
                        "13 SPRITE_FUCHSIA_GYM_1",
                        "44 SPRITE_JANINE",
                        "00 PLAYER",
                        "02 UNIT_OBJECT",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_misc_script.asm",),
                root=root,
            )
            rom[0x103] = 0x04
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_misc_script.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        script_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "script_command_rom_bytes"]
        self.assertEqual(len(script_mirrors), 1)
        self.assertEqual(script_mirrors[0]["status"], "passed")
        self.assertFalse(mismatch["passed"])
        failed_script_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_script_mirror["type"], "script_command_rom_bytes")
        self.assertIn("first_mismatch=", "\n".join(failed_script_mirror["evidence"]))

    def test_content_mirror_compares_text_blocks_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constants").mkdir()
            (root / "text").mkdir()
            (root / "constants" / "charmap.asm").write_text(
                "\n".join(
                    [
                        'charmap "<LINE>", $4f',
                        'charmap "<DONE>", $57',
                        'charmap "<PLAYER>", $52',
                        'charmap "H", $80',
                        'charmap "E", $81',
                        'charmap "L", $82',
                        'charmap "O", $83',
                        'charmap "!", $e7',
                        'charmap "1", $f7',
                        'charmap "2", $f8',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            source = root / "text" / "unit_text.asm"
            source.write_text(
                "\n".join(
                    [
                        "DEF TEXT_VALUE EQU 12",
                        "",
                        "UnitText:",
                        "\ttext \"HELLO\"",
                        "\tline \"<PLAYER>!{d:TEXT_VALUE}\"",
                        "\tdone",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes([0x00, 0x80, 0x81, 0x82, 0x82, 0x83, 0x4F, 0x52, 0xE7, 0xF7, 0xF8, 0x57])
            rom = bytearray([0xFF] * 0x200)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "00:0100 UnitText\n00 TX_START\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("text/unit_text.asm",),
                root=root,
            )
            rom[0x104] = 0x99
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("text/unit_text.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(report["source_files"][0]["text_block_count"], 1)
        self.assertEqual(report["rom_mirror_count"], 1)
        self.assertEqual(report["passed_rom_mirror_count"], 1)
        self.assertIn("text_block_rom_bytes", {item["type"] for item in report["rom_mirrors"]})
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        self.assertIn("first_mismatch=", "\n".join(mismatch["rom_mirrors"][0]["evidence"]))

    def test_content_mirror_compares_local_text_labels_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constants").mkdir()
            (root / "scripts").mkdir()
            (root / "constants" / "charmap.asm").write_text(
                "\n".join(
                    [
                        'charmap "<LINE>", $4f',
                        'charmap "<DONE>", $57',
                        'charmap "R", $80',
                        'charmap "E", $81',
                        'charmap "A", $82',
                        'charmap "D", $83',
                        'charmap "Y", $84',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            source = root / "scripts" / "unit_cable_club.asm"
            source.write_text(
                "\n".join(
                    [
                        "CableClubFriendScript:",
                        "\topentext",
                        "\twritetext .FriendReadyText",
                        "\twaitbutton",
                        "\tclosetext",
                        "\tend",
                        "",
                        ".FriendReadyText:",
                        "\ttext \"READY\"",
                        "\tdone",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            script_bytes = bytes([0x47, 0x4C, 0x10, 0x01, 0x53, 0x49, 0x90])
            text_bytes = bytes([0x00, 0x80, 0x81, 0x82, 0x83, 0x84, 0x57])
            rom = bytearray([0xFF] * 0x300)
            rom[0x100:0x100 + len(script_bytes)] = script_bytes
            rom[0x110:0x110 + len(text_bytes)] = text_bytes
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 CableClubFriendScript",
                        "00:0110 CableClubFriendScript.FriendReadyText",
                        "47 opentext_command",
                        "4c writetext_command",
                        "53 waitbutton_command",
                        "49 closetext_command",
                        "90 end_command",
                        "00 TX_START",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_cable_club.asm",),
                root=root,
            )
            rom[0x111] = 0x82
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_cable_club.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        text_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "text_block_rom_bytes"]
        self.assertEqual(len(text_mirrors), 1)
        self.assertEqual(text_mirrors[0]["status"], "passed")
        self.assertEqual(text_mirrors[0]["related_symbols"], ["CableClubFriendScript.FriendReadyText"])
        self.assertFalse(mismatch["passed"])
        failed_text_mirror = next(item for item in mismatch["rom_mirrors"] if item["status"] == "failed")
        self.assertEqual(failed_text_mirror["type"], "text_block_rom_bytes")
        self.assertIn("first_mismatch=", "\n".join(failed_text_mirror["evidence"]))

    def test_content_mirror_compares_text_ram_blocks_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constants").mkdir()
            (root / "text").mkdir()
            (root / "constants" / "charmap.asm").write_text(
                "\n".join(
                    [
                        'charmap "<LINE>", $4f',
                        'charmap "<DONE>", $57',
                        'charmap " ", $7f',
                        'charmap "O", $80',
                        'charmap "K", $81',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            source = root / "text" / "unit_text_ram.asm"
            source.write_text(
                "\n".join(
                    [
                        "UnitTextRam:",
                        "\ttext_ram wStringBuffer3",
                        "\ttext \" OK\"",
                        "\tdone",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes([0x01, 0x91, 0xCF, 0x00, 0x7F, 0x80, 0x81, 0x57])
            rom = bytearray([0xFF] * 0x300)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitTextRam",
                        "00:cf91 wStringBuffer3",
                        "01 TX_RAM",
                        "00 TX_START",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("text/unit_text_ram.asm",),
                root=root,
            )
            rom[0x101] = 0x92
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("text/unit_text_ram.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        text_mirrors = [item for item in report["rom_mirrors"] if item["type"] == "text_block_rom_bytes"]
        self.assertEqual(len(text_mirrors), 1)
        self.assertEqual(text_mirrors[0]["status"], "passed")
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        self.assertIn("first_mismatch=", "\n".join(mismatch["rom_mirrors"][0]["evidence"]))

    def test_content_mirror_compares_movement_blocks_to_rom_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            source = root / "scripts" / "unit_movement.asm"
            source.write_text(
                "\n".join(
                    [
                        "UnitMovement:",
                        "\tstep LEFT",
                        "\tturn_head UP",
                        "\tstep_sleep 9",
                        "\tstep_end",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            expected = bytes([0x0E, 0x01, 0x46, 0x09, 0x47])
            rom = bytearray([0xFF] * 0x300)
            rom[0x100:0x100 + len(expected)] = expected
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text(
                "\n".join(
                    [
                        "00:0100 UnitMovement",
                        "0c movement_step",
                        "00 movement_turn_head",
                        "3e movement_step_sleep",
                        "47 movement_step_end",
                        "02 LEFT",
                        "01 UP",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("scripts/unit_movement.asm",),
                root=root,
            )
            rom[0x102] = 0x45
            (root / "pokegold.gbc").write_bytes(rom)
            mismatch = build_content_mirror_report(
                source_files=("scripts/unit_movement.asm",),
                root=root,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(report["source_files"][0]["movement_block_count"], 1)
        self.assertEqual(report["rom_mirror_count"], 1)
        self.assertEqual(report["passed_rom_mirror_count"], 1)
        self.assertIn("movement_data_rom_bytes", {item["type"] for item in report["rom_mirrors"]})
        self.assertFalse(mismatch["passed"])
        self.assertEqual(mismatch["failed_rom_mirror_count"], 1)
        self.assertIn("first_mismatch=", "\n".join(mismatch["rom_mirrors"][0]["evidence"]))

    def test_content_mirror_reports_missing_incbin_asset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gfx").mkdir()
            (root / "gfx" / "unit.asm").write_text(
                'UnitGraphic: INCBIN "gfx/missing.2bpp"\n',
                encoding="utf-8",
            )

            report = build_content_mirror_report(
                source_files=("gfx/unit.asm",),
                root=root,
            )

        failed_ids = {item["id"] for item in report["failed_invariants"]}

        self.assertTrue(report["valid"])
        self.assertFalse(report["passed"])
        self.assertEqual(report["failed_invariant_count"], 1)
        self.assertIn("gfx/unit.asm:incbin_asset_exists:gfx/missing.2bpp", failed_ids)

    def test_cli_content_mirror_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "audio").mkdir()
            source = root / "audio" / "unit.asm"
            source.write_text(
                "Music_Unit:\n\tchannel_count 2\n\tchannel 1, Music_Unit_Ch1\n\tchannel 2, Music_Unit_Ch2\n",
                encoding="utf-8",
            )
            out = root / "content.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "content-mirror",
                        "--source-file",
                        str(source),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_content_mirror")
        self.assertTrue(data["passed"])
        self.assertGreater(data["invariant_count"], 0)
