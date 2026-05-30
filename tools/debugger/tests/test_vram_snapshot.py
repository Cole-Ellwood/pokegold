from __future__ import annotations

import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.debugger.vram_diff import build_vram_diff_report, main as diff_main
from tools.debugger.vram_snapshot import build_vram_snapshot_report, main as snapshot_main


def raw_state(tile: int = 0x2A, *, lcdc: int = 0x93, oam_visible: bool = True) -> bytes:
    data = bytearray(0x10000)
    data[0x9800] = tile
    data[0xFF40] = lcdc
    data[0xFF47] = 0xE4
    if oam_visible:
        data[0xFE00 : 0xFE04] = bytes((56, 40, 0x21, 0x10))
    return bytes(data)


class VramSnapshotCliTests(unittest.TestCase):
    def test_vram_snapshot_decode_raw_memory_64k(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "raw.bin"
            state.write_bytes(raw_state(tile=0x2A))

            report = build_vram_snapshot_report(state_path="raw.bin", decode=True, root=root)

        self.assertTrue(report["valid"], report)
        self.assertEqual(report["format"]["id"], "raw_memory_64k")
        decoded = report["decoded"]
        self.assertEqual(decoded["tilemaps"]["9800"]["cells"][0]["tile_hex"], "2A")
        self.assertEqual(decoded["oam"]["visible_guess_count"], 1)
        self.assertEqual(decoded["lcd_state"]["bg_tilemap"], "9800")

    def test_vram_snapshot_rejects_opaque_vba_sgm_candidate(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "bug.sgm"
            state.write_bytes(b"VBA\x00POKEMON_GLD\x00\x00\x00\x00" + bytes(128))

            report = build_vram_snapshot_report(state_path="bug.sgm", decode=True, root=root)

        self.assertFalse(report["valid"])
        self.assertEqual(report["format"]["id"], "vba_sgm_candidate")
        self.assertIn("unsupported state format", report["errors"][0])

    def test_vram_diff_reports_tilemap_jumble_flag_from_raw_states(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base.raw"
            other = root / "other.raw"
            base.write_bytes(raw_state(tile=0x11))
            other.write_bytes(raw_state(tile=0x22))

            report = build_vram_diff_report(base_state_path="base.raw", other_state_path="other.raw", root=root)

        self.assertTrue(report["valid"], report)
        diff = report["diff"]
        self.assertEqual(diff["tilemap_changed_cell_count"], 1)
        self.assertEqual(diff["oam_changed_count"], 0)
        self.assertIn("tilemap_changed_oam_stable", {flag["id"] for flag in diff["scenario_flags"]})

    def test_vram_snapshot_cli_json_is_machine_readable(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / "raw.bin"
            state.write_bytes(raw_state(tile=0x33))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                exit_code = snapshot_main(["--save-state", str(state), "--decode", "--json"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["kind"], "unified_debugger_vram_snapshot")
        self.assertEqual(payload["decoded"]["tilemaps"]["9800"]["cells"][0]["tile_hex"], "33")

    def test_vram_diff_cli_text_mentions_changed_tilemap(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base.raw"
            other = root / "other.raw"
            base.write_bytes(raw_state(tile=0x11))
            other.write_bytes(raw_state(tile=0x22))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                exit_code = diff_main([str(base), str(other)])

        self.assertEqual(exit_code, 0)
        self.assertIn("tilemap_cells=1", out.getvalue())

    def test_vram_snapshot_self_test_prints_acceptance_string(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = snapshot_main(["--self-test"])

        self.assertEqual(exit_code, 0)
        self.assertIn("vram structured-decode self-test PASS", out.getvalue())


if __name__ == "__main__":
    unittest.main()
