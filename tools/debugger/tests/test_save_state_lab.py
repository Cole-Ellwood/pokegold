from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tools.debugger.save_state_lab import (
    build_synth_report,
    build_save_state_diff_report,
    build_save_state_inspect_report,
    main,
)


class SaveStateLabTests(unittest.TestCase):
    def test_inspect_raw_memory_resolves_named_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            symbols = root / "unit.sym"
            symbols.write_text("01:D000 wMapGroup\n01:D001 wMapNumber\n", encoding="utf-8")
            state = root / "unit.state"
            data = bytearray(0x10000)
            data[0xD000] = 0x12
            data[0xD001] = 0x34
            state.write_bytes(data)

            report = build_save_state_inspect_report(
                state_path="unit.state",
                symbols_path="unit.sym",
                symbols=("wMapGroup", "wMapNumber"),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["format"]["id"], "raw_memory_64k")
        values = {item["symbol"]: item for item in report["symbols"]}
        self.assertEqual(values["wMapGroup"]["value_hex"], "12")
        self.assertEqual(values["wMapNumber"]["value_hex"], "34")

    def test_diff_raw_memory_reports_named_symbol_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            symbols = root / "unit.sym"
            symbols.write_text("00:D141 wCurDamage\n", encoding="utf-8")
            base = root / "base.state"
            other = root / "other.state"
            base_data = bytearray(0x10000)
            other_data = bytearray(base_data)
            base_data[0xD141] = 0x10
            base_data[0xD142] = 0x00
            other_data[0xD141] = 0x34
            other_data[0xD142] = 0x12
            base.write_bytes(base_data)
            other.write_bytes(other_data)

            report = build_save_state_diff_report(
                base_state_path="base.state",
                other_state_path="other.state",
                symbols_path="unit.sym",
                symbols=("wCurDamage",),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["changed_byte_count"], 2)
        self.assertEqual(report["symbol_delta_count"], 1)
        delta = report["symbol_deltas"][0]
        self.assertEqual(delta["symbol"], "wCurDamage")
        self.assertEqual(delta["before_hex"], "10 00")
        self.assertEqual(delta["after_hex"], "34 12")
        self.assertEqual(delta["after_little_endian"], 0x1234)

    def test_vba_sgm_candidate_fails_decode_honestly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "unit.sym").write_text("00:D141 wCurDamage\n", encoding="utf-8")
            state = root / "debug1.sgm"
            state.write_bytes(b"\x0c\x00\x00\x00POKEMON_GLDAAUE\x00" + bytes(256))

            report = build_save_state_inspect_report(
                state_path="debug1.sgm",
                symbols_path="unit.sym",
                symbols=("wCurDamage",),
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["format"]["id"], "vba_sgm_candidate")
        self.assertFalse(report["format"]["decode_supported"])
        self.assertEqual(report["format"]["rom_title"], "POKEMON_GLDAAUE")
        self.assertTrue(any("no trusted WRAM offset decoder" in warning for warning in report["warnings"]))
        self.assertEqual(report["symbols"][0]["status"], "unmapped")

    def test_diff_unsupported_formats_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "unit.sym").write_text("00:D141 wCurDamage\n", encoding="utf-8")
            for name in ("a.sgm", "b.sgm"):
                (root / name).write_bytes(b"\x0c\x00\x00\x00POKEMON_GLDAAUE\x00" + bytes(256))

            report = build_save_state_diff_report(
                base_state_path="a.sgm",
                other_state_path="b.sgm",
                symbols_path="unit.sym",
                symbols=("wCurDamage",),
                root=root,
            )

        self.assertFalse(report["valid"])
        self.assertIn("cannot diff these state formats", "\n".join(report["errors"]))
        self.assertEqual(report["changed_byte_count"], 0)

    def test_module_cli_inspect_json_works_without_front_door_wiring(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "unit.sym").write_text("01:D000 wMapGroup\n", encoding="utf-8")
            state = root / "unit.state"
            data = bytearray(0x10000)
            data[0xD000] = 0x44
            state.write_bytes(data)

            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(
                    [
                        "inspect",
                        str(state),
                        "--symbols",
                        str(root / "unit.sym"),
                        "--symbol",
                        "wMapGroup",
                        "--json",
                    ]
                )

        self.assertEqual(code, 0)
        self.assertIn('"format"', stdout.getvalue())
        self.assertIn('"wMapGroup"', stdout.getvalue())

    def test_synth_report_delegates_to_navigator_and_verifies_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state = root / "bedroom.state"
            manifest = root / "bedroom.manifest.json"

            def fake_navigator(predicate: str, **kwargs: object) -> dict[str, object]:
                self.assertEqual(predicate, "map=PLAYERS_HOUSE_2F")
                self.assertEqual(kwargs["checkpoint"], "auto")
                self.assertEqual(Path(str(kwargs["save_state"])), state)
                self.assertEqual(Path(str(kwargs["manifest_out"])), manifest)
                return {
                    "predicate": predicate,
                    "checkpoint": "new_game",
                    "reached": True,
                    "frame": 123,
                    "map": "PLAYERS_HOUSE_2F",
                    "map_desc": "map=PLAYERS_HOUSE_2F (24:7)",
                    "state_path": str(state),
                    "manifest_path": str(manifest),
                    "observed_signature": {"map": "PLAYERS_HOUSE_2F"},
                }

            def fake_verifier(manifest_path: str, **kwargs: object) -> dict[str, object]:
                self.assertEqual(Path(manifest_path), manifest)
                self.assertEqual(Path(str(kwargs["rom"])), root / "pokegold.gbc")
                self.assertEqual(Path(str(kwargs["symbols_path"])), root / "pokegold.sym")
                return {"passed": True, "observed": "map=PLAYERS_HOUSE_2F (24:7)"}

            report = build_synth_report(
                predicate="map=PLAYERS_HOUSE_2F",
                rom_path="pokegold.gbc",
                symbols_path="pokegold.sym",
                save_state="bedroom.state",
                manifest_out="bedroom.manifest.json",
                root=root,
                navigator=fake_navigator,
                verifier=fake_verifier,
            )

        self.assertTrue(report["valid"], report["errors"])
        self.assertTrue(report["synthesized"])
        self.assertEqual(report["backend"], "pyboy")
        self.assertEqual(report["state"], "bedroom.state")
        self.assertEqual(report["manifest"], "bedroom.manifest.json")
        self.assertTrue(report["verification"]["passed"])

    def test_synth_report_fails_closed_when_navigator_cannot_reach_predicate(self) -> None:
        def fake_navigator(predicate: str, **kwargs: object) -> dict[str, object]:
            return {
                "predicate": predicate,
                "checkpoint": "new_game",
                "reached": False,
                "nearest": "map=PLAYERS_HOUSE_2F (24:7)",
                "unmet": ["map == NEVERLAND"],
            }

        report = build_synth_report(
            predicate="map=NEVERLAND",
            verify=False,
            navigator=fake_navigator,
        )

        self.assertFalse(report["valid"])
        self.assertFalse(report["reached"])
        self.assertFalse(report["synthesized"])
        self.assertIn("could not reach", "\n".join(report["errors"]))


if __name__ == "__main__":
    unittest.main()
