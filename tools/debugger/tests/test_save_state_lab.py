from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tools.debugger.save_state_lab import (
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


if __name__ == "__main__":
    unittest.main()
