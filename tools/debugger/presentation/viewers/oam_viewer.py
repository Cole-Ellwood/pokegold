"""OAM (Object Attribute Memory) sprite viewer.

Decodes the 40 OAM entries (4 bytes each, 160 total) into
human-readable sprite state: position, tile, palette, flags.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

OAM_ENTRY_SIZE = 4
OAM_ENTRY_COUNT = 40
OAM_TOTAL_SIZE = OAM_ENTRY_SIZE * OAM_ENTRY_COUNT


@dataclass
class OamEntry:
    """One OAM sprite entry."""
    index: int
    y: int = 0
    x: int = 0
    tile: int = 0
    attributes: int = 0

    @property
    def screen_y(self) -> int:
        return self.y - 16

    @property
    def screen_x(self) -> int:
        return self.x - 8

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

    @property
    def priority(self) -> bool:
        return bool(self.attributes & 0x80)

    @property
    def visible(self) -> bool:
        return 0 < self.y < 160 and 0 < self.x < 168

    def __str__(self) -> str:
        flags = ""
        if self.h_flip:
            flags += "H"
        if self.v_flip:
            flags += "V"
        if self.priority:
            flags += "P"
        vis = "vis" if self.visible else "hid"
        return (
            f"OAM[{self.index:2d}] ({self.screen_x:4d},{self.screen_y:4d}) "
            f"tile=${self.tile:02X} pal={self.palette} {flags} [{vis}]"
        )


@dataclass
class OamSnapshot:
    """All 40 OAM entries."""
    entries: list[OamEntry] = field(default_factory=list)
    sprite_size_8x16: bool = False

    @staticmethod
    def from_bytes(oam: bytes, lcdc: int = 0) -> OamSnapshot:
        snap = OamSnapshot(sprite_size_8x16=bool(lcdc & 0x04))
        for i in range(min(OAM_ENTRY_COUNT, len(oam) // OAM_ENTRY_SIZE)):
            base = i * OAM_ENTRY_SIZE
            snap.entries.append(OamEntry(
                index=i,
                y=oam[base],
                x=oam[base + 1],
                tile=oam[base + 2],
                attributes=oam[base + 3],
            ))
        return snap

    @property
    def visible_count(self) -> int:
        return sum(1 for e in self.entries if e.visible)

    def summary(self) -> str:
        mode = "8x16" if self.sprite_size_8x16 else "8x8"
        return (
            f"OAM: {len(self.entries)} sprites ({self.visible_count} visible), "
            f"mode={mode}"
        )

    def render_text(self, visible_only: bool = True) -> str:
        lines = [self.summary(), ""]
        for entry in self.entries:
            if visible_only and not entry.visible:
                continue
            lines.append(str(entry))
        return "\n".join(lines)


__all__ = ["OamEntry", "OamSnapshot", "OAM_ENTRY_COUNT"]
