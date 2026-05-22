from __future__ import annotations

import unittest

from tools.debugger.vram_decode import (
    TILEMAP_A_OFFSET,
    TILEMAP_B_OFFSET,
    TILEMAP_WIDTH,
    VRAM_SIZE,
    decode_vram_state,
    diff_vram_states,
)


def blank_vram() -> bytearray:
    return bytearray(VRAM_SIZE)


def put_tile(vram: bytearray, offset: int, row: int, col: int, value: int) -> None:
    vram[offset + row * TILEMAP_WIDTH + col] = value


def oam_with_entry(index: int, *, y: int, x: int, tile: int, attr: int) -> bytes:
    oam = bytearray(40 * 4)
    base = index * 4
    oam[base : base + 4] = bytes((y, x, tile, attr))
    return bytes(oam)


class VramDecodeTests(unittest.TestCase):
    def test_vram_decode_matches_golden_battle_screen(self) -> None:
        vram0 = blank_vram()
        vram1 = blank_vram()
        put_tile(vram0, TILEMAP_A_OFFSET, 5, 7, 0x2A)
        put_tile(vram0, TILEMAP_B_OFFSET, 2, 3, 0x44)
        vram1[TILEMAP_A_OFFSET + 5 * TILEMAP_WIDTH + 7] = 0xE5
        oam = oam_with_entry(0, y=56, x=40, tile=0x21, attr=0xB7)

        state = decode_vram_state(
            bytes(vram0),
            vram1=bytes(vram1),
            oam=oam,
            io_registers={
                "rLCDC": "F3",
                "rSTAT": "03",
                "rSCX": "09",
                "rSCY": "11",
                "rWX": "07",
                "rWY": "00",
                "rVBK": "01",
                "rBGP": "E4",
                "rOBP0": "D2",
                "rOBP1": "1B",
            },
        )

        self.assertEqual(state["kind"], "unified_debugger_vram_decode")
        self.assertFalse(state["hardware_behavior_proven"])
        self.assertEqual(state["vram"]["active_vram_bank"], 1)
        self.assertEqual(state["lcd_state"]["bg_tilemap"], "9800")
        self.assertEqual(state["lcd_state"]["window_tilemap"], "9C00")
        self.assertTrue(state["lcd_state"]["sprites_enabled"])
        self.assertEqual(state["lcd_state"]["scroll"], {"scx": 9, "scy": 17, "wx": 7, "wy": 0})

        bg_cell = state["tilemaps"]["9800"]["cells"][5 * TILEMAP_WIDTH + 7]
        self.assertEqual(bg_cell["address"], "98A7")
        self.assertEqual(bg_cell["tile_hex"], "2A")
        self.assertEqual(bg_cell["attributes"]["raw_hex"], "E5")
        self.assertTrue(bg_cell["attributes"]["priority"])
        self.assertEqual(bg_cell["attributes"]["cgb_palette"], 5)

        window_cell = state["tilemaps"]["9C00"]["cells"][2 * TILEMAP_WIDTH + 3]
        self.assertEqual(window_cell["address"], "9C43")
        self.assertEqual(window_cell["tile_hex"], "44")
        self.assertTrue(state["tilemaps"]["9C00"]["selected_for_window"])

        sprite = state["oam"]["entries"][0]
        self.assertEqual(sprite["screen_x"], 32)
        self.assertEqual(sprite["screen_y"], 40)
        self.assertEqual(sprite["tile_hex"], "21")
        self.assertEqual(sprite["attributes"]["dmg_palette"], "OBP1")
        self.assertEqual(sprite["attributes"]["cgb_palette"], 7)
        self.assertTrue(sprite["visible_guess"])
        self.assertEqual(state["palettes"]["dmg"]["bgp"]["entries"][0]["shade_name"], "white")
        self.assertEqual(state["palettes"]["dmg"]["obp1"]["entries"][0]["transparent"], True)

    def test_vram_diff_finds_tile_index_shift(self) -> None:
        before_vram = blank_vram()
        after_vram = blank_vram()
        put_tile(before_vram, TILEMAP_A_OFFSET, 0, 0, 0x11)
        put_tile(before_vram, TILEMAP_A_OFFSET, 0, 1, 0x22)
        put_tile(after_vram, TILEMAP_A_OFFSET, 0, 0, 0x22)
        put_tile(after_vram, TILEMAP_A_OFFSET, 0, 1, 0x11)

        before = decode_vram_state(bytes(before_vram), io_registers={"rLCDC": "91"})
        after = decode_vram_state(bytes(after_vram), io_registers={"rLCDC": "91"})
        diff = diff_vram_states(before, after)

        self.assertEqual(diff["tilemap_changed_cell_count"], 2)
        map_delta = next(delta for delta in diff["tilemap_deltas"] if delta["tilemap"] == "9800")
        self.assertEqual(map_delta["changed_cells"][0]["before_tile"], "11")
        self.assertEqual(map_delta["changed_cells"][0]["after_tile"], "22")
        moved_tiles = {item["tile_hex"]: item for item in map_delta["tile_position_changes"]}
        self.assertEqual(moved_tiles["11"]["before_positions"], [{"row": 0, "col": 0}])
        self.assertEqual(moved_tiles["11"]["after_positions"], [{"row": 0, "col": 1}])

    def test_vram_diff_golden_smoke_may_2026_tile_jumble(self) -> None:
        before_vram = blank_vram()
        after_vram = blank_vram()
        for col, tile in enumerate((0x01, 0x02, 0x03, 0x04)):
            put_tile(before_vram, TILEMAP_A_OFFSET, 12, col, tile)
        for col, tile in enumerate((0x50, 0x51, 0x52, 0x53)):
            put_tile(after_vram, TILEMAP_A_OFFSET, 12, col, tile)
        stable_oam = oam_with_entry(0, y=72, x=88, tile=0x12, attr=0x00)
        io = {"rLCDC": "93", "rBGP": "E4", "rOBP0": "D2", "rOBP1": "D2"}

        before = decode_vram_state(bytes(before_vram), oam=stable_oam, io_registers=io)
        after = decode_vram_state(bytes(after_vram), oam=stable_oam, io_registers=io)
        diff = diff_vram_states(before, after)

        self.assertEqual(diff["tilemap_changed_cell_count"], 4)
        self.assertEqual(diff["oam_changed_count"], 0)
        self.assertEqual(diff["palette_changed_count"], 0)
        flag_ids = {flag["id"] for flag in diff["scenario_flags"]}
        self.assertIn("tilemap_changed_oam_stable", flag_ids)
        self.assertIn("tile_indices_changed_without_palette_or_lcdc_shift", flag_ids)

    def test_vram_diff_reports_palette_index_shift(self) -> None:
        vram = blank_vram()
        before = decode_vram_state(bytes(vram), io_registers={"rLCDC": "91", "rBGP": "E4"})
        after = decode_vram_state(bytes(vram), io_registers={"rLCDC": "91", "rBGP": "D4"})

        diff = diff_vram_states(before, after)

        self.assertEqual(diff["palette_changed_count"], 1)
        palette_delta = diff["palette_deltas"][0]
        self.assertEqual(palette_delta["palette"], "dmg.bgp")
        self.assertEqual(palette_delta["change_kind"], "color_index_shift")
        self.assertEqual(palette_delta["color_id"], 2)
        self.assertEqual(palette_delta["before_shade_name"], "dark_gray")
        self.assertEqual(palette_delta["after_shade_name"], "light_gray")

    def test_vram_diff_reports_oam_appeared_and_disappeared(self) -> None:
        vram = blank_vram()
        hidden_oam = oam_with_entry(0, y=0, x=40, tile=0x21, attr=0x00)
        visible_oam = oam_with_entry(0, y=56, x=40, tile=0x21, attr=0x00)
        before = decode_vram_state(bytes(vram), oam=hidden_oam, io_registers={"rLCDC": "93"})
        after = decode_vram_state(bytes(vram), oam=visible_oam, io_registers={"rLCDC": "93"})

        appeared = diff_vram_states(before, after)
        disappeared = diff_vram_states(after, before)

        self.assertEqual(appeared["oam_deltas"][0]["change_kind"], "appeared")
        self.assertEqual(disappeared["oam_deltas"][0]["change_kind"], "disappeared")


if __name__ == "__main__":
    unittest.main()
