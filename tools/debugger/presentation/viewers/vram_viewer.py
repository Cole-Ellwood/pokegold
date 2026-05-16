"""VRAM tile viewer, BG map viewer, tilemap diff.

Reads VRAM state from a PyBoy instance or raw bytes and renders:
  - Tile data (8x8 tiles, 2bpp)
  - BG tile map (32x32 entries)
  - Window tile map
  - Tilemap diff between two states
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


TILE_SIZE = 16  # 2bpp: 8 rows × 2 bytes
TILES_PER_BANK = 256
BG_MAP_WIDTH = 32
BG_MAP_HEIGHT = 32
BG_MAP_SIZE = BG_MAP_WIDTH * BG_MAP_HEIGHT


@dataclass
class Tile:
    """One 8x8 2bpp tile."""
    index: int
    bank: int = 0
    data: bytes = b""

    @property
    def pixels(self) -> list[list[int]]:
        """Decode 2bpp tile data to 8x8 pixel array (0-3)."""
        rows: list[list[int]] = []
        for y in range(8):
            if y * 2 + 1 >= len(self.data):
                rows.append([0] * 8)
                continue
            lo = self.data[y * 2]
            hi = self.data[y * 2 + 1]
            row = []
            for x in range(7, -1, -1):
                bit0 = (lo >> x) & 1
                bit1 = (hi >> x) & 1
                row.append((bit1 << 1) | bit0)
            rows.append(row)
        return rows

    def render_ascii(self) -> str:
        chars = " ░▒█"
        lines = []
        for row in self.pixels:
            lines.append("".join(chars[p] for p in row))
        return "\n".join(lines)


@dataclass
class BgMapEntry:
    """One BG map entry."""
    x: int
    y: int
    tile_index: int
    attributes: int = 0  # GBC: palette, bank, flip flags

    @property
    def palette(self) -> int:
        return self.attributes & 0x07

    @property
    def vram_bank(self) -> int:
        return (self.attributes >> 3) & 1

    @property
    def h_flip(self) -> bool:
        return bool(self.attributes & 0x20)

    @property
    def v_flip(self) -> bool:
        return bool(self.attributes & 0x40)


@dataclass
class VramSnapshot:
    """Complete VRAM state at one point in time."""
    tiles_bank0: list[Tile] = field(default_factory=list)
    tiles_bank1: list[Tile] = field(default_factory=list)
    bg_map: list[BgMapEntry] = field(default_factory=list)
    window_map: list[BgMapEntry] = field(default_factory=list)
    scroll_x: int = 0
    scroll_y: int = 0
    window_x: int = 0
    window_y: int = 0
    lcdc: int = 0

    @staticmethod
    def from_bytes(vram: bytes, io_regs: bytes | None = None) -> VramSnapshot:
        snap = VramSnapshot()

        # Bank 0 tiles: 0x8000-0x97FF (offset 0x0000-0x17FF in VRAM)
        for i in range(TILES_PER_BANK):
            offset = i * TILE_SIZE
            end = offset + TILE_SIZE
            data = vram[offset:end] if end <= len(vram) else b"\x00" * TILE_SIZE
            snap.tiles_bank0.append(Tile(index=i, bank=0, data=data))

        # Bank 1 tiles: same offsets, second 8 KiB bank
        bank1_offset = 0x2000
        for i in range(TILES_PER_BANK):
            offset = bank1_offset + i * TILE_SIZE
            end = offset + TILE_SIZE
            data = vram[offset:end] if end <= len(vram) else b"\x00" * TILE_SIZE
            snap.tiles_bank1.append(Tile(index=i, bank=1, data=data))

        # BG map: 0x9800-0x9BFF (offset 0x1800-0x1BFF)
        bg_offset = 0x1800
        for y in range(BG_MAP_HEIGHT):
            for x in range(BG_MAP_WIDTH):
                idx = bg_offset + y * BG_MAP_WIDTH + x
                tile_idx = vram[idx] if idx < len(vram) else 0
                snap.bg_map.append(BgMapEntry(x=x, y=y, tile_index=tile_idx))

        # Window map: 0x9C00-0x9FFF (offset 0x1C00-0x1FFF)
        win_offset = 0x1C00
        for y in range(BG_MAP_HEIGHT):
            for x in range(BG_MAP_WIDTH):
                idx = win_offset + y * BG_MAP_WIDTH + x
                tile_idx = vram[idx] if idx < len(vram) else 0
                snap.window_map.append(BgMapEntry(x=x, y=y, tile_index=tile_idx))

        if io_regs and len(io_regs) >= 0x50:
            snap.scroll_y = io_regs[0x42]
            snap.scroll_x = io_regs[0x43]
            snap.lcdc = io_regs[0x40]
            snap.window_y = io_regs[0x4A]
            snap.window_x = io_regs[0x4B]

        return snap

    def summary(self) -> str:
        non_empty_b0 = sum(1 for t in self.tiles_bank0 if any(b != 0 for b in t.data))
        non_empty_b1 = sum(1 for t in self.tiles_bank1 if any(b != 0 for b in t.data))
        return (
            f"VRAM: {non_empty_b0} tiles (bank 0), {non_empty_b1} tiles (bank 1)\n"
            f"Scroll: ({self.scroll_x}, {self.scroll_y}), "
            f"Window: ({self.window_x}, {self.window_y})\n"
            f"LCDC: ${self.lcdc:02X}"
        )


@dataclass
class TilemapDiff:
    """Diff between two tilemap states."""
    changed_tiles: list[tuple[int, int, int, int]] = field(default_factory=list)
    changed_bg_entries: list[tuple[int, int, int, int]] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.changed_tiles) + len(self.changed_bg_entries)

    def summary(self) -> str:
        return (
            f"Tilemap diff: {len(self.changed_tiles)} tile changes, "
            f"{len(self.changed_bg_entries)} BG map changes"
        )


def diff_vram(a: VramSnapshot, b: VramSnapshot) -> TilemapDiff:
    """Diff two VRAM snapshots."""
    result = TilemapDiff()

    for i, (ta, tb) in enumerate(zip(a.tiles_bank0, b.tiles_bank0)):
        if ta.data != tb.data:
            result.changed_tiles.append((0, i, 0, 0))

    for i, (ea, eb) in enumerate(zip(a.bg_map, b.bg_map)):
        if ea.tile_index != eb.tile_index:
            result.changed_bg_entries.append((ea.x, ea.y, ea.tile_index, eb.tile_index))

    return result


__all__ = [
    "Tile", "BgMapEntry", "VramSnapshot", "TilemapDiff",
    "diff_vram", "TILE_SIZE", "BG_MAP_WIDTH", "BG_MAP_HEIGHT",
]
