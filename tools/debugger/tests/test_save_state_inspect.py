from __future__ import annotations

import gzip
import io
import json
import struct
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.debugger.__main__ import main as debugger_main
from tools.debugger.catalog import triage_request
from tools.debugger.next_steps import build_next_step
from tools.debugger.save_state_inspect import build_save_state_inspection_report


SYMBOLS = {
    "wSeenTrainerBank": (0x00, 0xCF29),
    "wScriptAfterPointer": (0x00, 0xCF36),
    "wRunningTrainerBattleScript": (0x00, 0xCF38),
    "wBattleResult": (0x00, 0xCFE9),
    "wMapScriptsBank": (0x01, 0xD08C),
    "wMapScriptsPointer": (0x01, 0xD08D),
    "wEvolutionOldSpecies": (0x01, 0xD0D3),
    "wEvolutionNewSpecies": (0x01, 0xD0D4),
    "wEvolutionCanceled": (0x01, 0xD0D6),
    "wBattleMode": (0x01, 0xD116),
    "wBattleType": (0x01, 0xD119),
    "wScriptMode": (0x01, 0xD15E),
    "wScriptRunning": (0x01, 0xD15F),
    "wScriptBank": (0x01, 0xD160),
    "wScriptPos": (0x01, 0xD161),
    "wScriptStackSize": (0x01, 0xD163),
    "wScriptStack": (0x01, 0xD164),
    "wMapGroup": (0x01, 0xDA00),
    "wMapNumber": (0x01, 0xDA01),
    "wYCoord": (0x01, 0xDA02),
    "wXCoord": (0x01, 0xDA03),
    "wPartyCount": (0x01, 0xDA22),
    "wPartySpecies": (0x01, 0xDA23),
    "wTrainerBattleContextBackup": (0x01, 0xD049),
    "wTrainerBattleContextBackupActive": (0x01, 0xD059),
    "SlowpokeWellB1F_MapScripts": (0x44, 0x58DA),
    "SlowpokeWellB1F_MapEvents": (0x44, 0x5F92),
}


class SaveStateInspectTests(unittest.TestCase):
    def test_vbam_sgm_reports_impossible_post_battle_script_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_repo_fixture(root)
            write_vbam_sgm_fixture(root / "state.sgm")

            report = build_save_state_inspection_report(
                save_state="state.sgm",
                rom_path="pokegold.gbc",
                symbols_path="pokegold.sym",
                root=root,
            )

        finding_ids = {finding["id"] for finding in report["findings"]}

        self.assertTrue(report["valid"])
        self.assertEqual(report["state_format"], "vbam_sgm")
        self.assertEqual(report["memory"]["map"]["name"], "SLOWPOKE_WELL_B1F")
        self.assertEqual(report["memory"]["script_vm"]["bank"], "$B4")
        self.assertEqual(report["memory"]["script_vm"]["pos"], "$0002")
        self.assertEqual(report["memory"]["party"]["species"][0]["name"], "FLAAFFY")
        self.assertIn("script_pos_rom0_header", finding_ids)
        self.assertIn("invalid_script_bank", finding_ids)
        self.assertIn("script_bank_not_map_bank", finding_ids)
        self.assertIn("battle_finished_script_still_active", finding_ids)

    def test_state_inspect_cli_writes_json_and_alias_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_repo_fixture(root)
            write_vbam_sgm_fixture(root / "state.sgm")
            out = root / "state.json"

            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "inspect-state",
                        "--save-state",
                        str(root / "state.sgm"),
                        "--rom",
                        str(root / "pokegold.gbc"),
                        "--symbols",
                        str(root / "pokegold.sym"),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_save_state_inspection")
        self.assertGreaterEqual(data["blocking_finding_count"], 1)

    def test_frozen_trainer_evolution_symptom_routes_to_state_inspect_first(self) -> None:
        symptom = "music is playing but frozen after trainer battle and evolved Flaaffy"

        triage = triage_request(symptom=symptom)
        next_step = build_next_step(symptom=symptom)

        self.assertEqual(triage["matches"][0]["id"], "script_vm_impossible_state")
        self.assertIn("state-inspect", triage["commands"][0])
        self.assertEqual(
            next_step["recommendation"]["symptom_class"],
            "script_vm_impossible_state",
        )

    def test_script_resume_gate_formats_state_inspection_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_repo_fixture(root)
            write_vbam_sgm_fixture(root / "state.sgm")
            report = build_save_state_inspection_report(
                save_state="state.sgm",
                rom_path="pokegold.gbc",
                symbols_path="pokegold.sym",
                root=root,
            )
            report_path = root / "state_report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                code = debugger_main(["script-resume-gate", "--report", str(report_path)])

            text = stdout.getvalue()

        self.assertEqual(code, 1)
        self.assertIn("passed=False", text)
        self.assertIn("script_pos_rom0_header", text)


def write_repo_fixture(root: Path) -> None:
    (root / "constants").mkdir(parents=True)
    (root / "data" / "maps").mkdir(parents=True)
    (root / "pokegold.gbc").write_bytes(bytes(0x200000))
    (root / "pokegold.sym").write_text(
        "\n".join(f"{bank:02x}:{address:04x} {label}" for label, (bank, address) in SYMBOLS.items())
        + "\n",
        encoding="utf-8",
    )
    map_lines = ["\tconst_def", "\tnewgroup GROUP_ONE", "\tmap_const GROUP_ONE_MAP, 1, 1", "\tendgroup"]
    map_lines.extend(["\tnewgroup GROUP_TWO", "\tmap_const GROUP_TWO_MAP, 1, 1", "\tendgroup"])
    map_lines.append("\tnewgroup DUNGEONS")
    for index in range(1, 32):
        map_lines.append(f"\tmap_const DUMMY_DUNGEON_{index}, 1, 1")
    map_lines.append("\tmap_const SLOWPOKE_WELL_B1F, 10, 9")
    map_lines.append("\tendgroup")
    (root / "constants" / "map_constants.asm").write_text("\n".join(map_lines) + "\n", encoding="utf-8")
    (root / "data" / "maps" / "attributes.asm").write_text(
        "\tmap_attributes SlowpokeWellB1F, SLOWPOKE_WELL_B1F, $09, 0\n",
        encoding="utf-8",
    )
    species = ["DUMMY"] * 251
    species[0x5C - 1] = "GASTLY"
    species[0x9C - 1] = "QUILAVA"
    species[0xB3 - 1] = "MAREEP"
    species[0xB4 - 1] = "FLAAFFY"
    pokemon_lines = ["\tconst_def 1"]
    pokemon_lines.extend(f"\tconst {name}_{idx}" if name == "DUMMY" else f"\tconst {name}" for idx, name in enumerate(species, 1))
    pokemon_lines.append("DEF NUM_POKEMON EQU const_value - 1")
    (root / "constants" / "pokemon_constants.asm").write_text(
        "\n".join(pokemon_lines) + "\n",
        encoding="utf-8",
    )


def write_vbam_sgm_fixture(path: Path) -> None:
    raw = bytearray(0x5000)
    d000_base = 0x3000
    wram0_base = 0x2000
    struct.pack_into("<I", raw, 0, 12)
    raw[4:19] = b"POKEMON_GLDAAUE"
    struct.pack_into("<6H", raw, 27, 0x0040, 0xDFE5, 0xCF50, 0x060C, 0x16E5, 0x2880)

    def offset(address: int) -> int:
        if address < 0xD000:
            return wram0_base + (address - 0xC000)
        return d000_base + (address - 0xD000)

    def put_u8(symbol: str, value: int) -> None:
        raw[offset(SYMBOLS[symbol][1])] = value

    def put_u16(symbol: str, value: int) -> None:
        pos = offset(SYMBOLS[symbol][1])
        raw[pos] = value & 0xFF
        raw[pos + 1] = value >> 8

    put_u8("wMapGroup", 3)
    put_u8("wMapNumber", 32)
    put_u8("wYCoord", 4)
    put_u8("wXCoord", 13)
    put_u8("wMapScriptsBank", 0x44)
    put_u16("wMapScriptsPointer", 0x58DA)
    put_u8("wBattleMode", 0)
    put_u8("wBattleType", 0)
    put_u8("wScriptMode", 1)
    put_u8("wScriptRunning", 1)
    put_u8("wScriptBank", 0xB4)
    put_u16("wScriptPos", 0x0002)
    put_u8("wScriptStackSize", 1)
    stack = offset(SYMBOLS["wScriptStack"][1])
    raw[stack : stack + 3] = bytes([0xB4, 0x83, 0x59])
    put_u8("wSeenTrainerBank", 0xFF)
    put_u16("wScriptAfterPointer", 0)
    put_u8("wRunningTrainerBattleScript", 0xFF)
    put_u8("wPartyCount", 6)
    party = offset(SYMBOLS["wPartySpecies"][1])
    raw[party : party + 7] = bytes([0xB4, 0xC2, 0x9C, 0x2B, 0x5C, 0x10, 0xFF])
    sp = d000_base + (0xDFE5 - 0xD000)
    raw[sp : sp + 2] = bytes([0x4F, 0xEC])

    with gzip.open(path, "wb") as fh:
        fh.write(raw)


if __name__ == "__main__":
    unittest.main()
