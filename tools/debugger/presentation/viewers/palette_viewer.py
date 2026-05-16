"""GBC palette viewer.

Decodes CGB palette RAM (BG + OBJ, 8 palettes × 4 colors each)
from IO register dumps.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Color:
    """One 15-bit GBC color."""
    r5: int = 0
    g5: int = 0
    b5: int = 0

    @staticmethod
    def from_raw(lo: int, hi: int) -> Color:
        raw = lo | (hi << 8)
        return Color(
            r5=raw & 0x1F,
            g5=(raw >> 5) & 0x1F,
            b5=(raw >> 10) & 0x1F,
        )

    @property
    def rgb24(self) -> tuple[int, int, int]:
        return (self.r5 << 3, self.g5 << 3, self.b5 << 3)

    @property
    def hex(self) -> str:
        r, g, b = self.rgb24
        return f"#{r:02X}{g:02X}{b:02X}"

    def __str__(self) -> str:
        return self.hex


@dataclass
class Palette:
    """One 4-color GBC palette."""
    index: int
    kind: str = "bg"  # "bg" or "obj"
    colors: list[Color] = field(default_factory=list)

    def __str__(self) -> str:
        cols = " ".join(str(c) for c in self.colors)
        return f"PAL[{self.kind.upper()}{self.index}] {cols}"


@dataclass
class PaletteSnapshot:
    """All BG and OBJ palettes."""
    bg_palettes: list[Palette] = field(default_factory=list)
    obj_palettes: list[Palette] = field(default_factory=list)

    @staticmethod
    def from_bytes(bg_data: bytes, obj_data: bytes) -> PaletteSnapshot:
        snap = PaletteSnapshot()
        for pal_idx in range(8):
            pal = Palette(index=pal_idx, kind="bg")
            for col_idx in range(4):
                offset = pal_idx * 8 + col_idx * 2
                if offset + 1 < len(bg_data):
                    pal.colors.append(Color.from_raw(bg_data[offset], bg_data[offset + 1]))
                else:
                    pal.colors.append(Color())
            snap.bg_palettes.append(pal)

        for pal_idx in range(8):
            pal = Palette(index=pal_idx, kind="obj")
            for col_idx in range(4):
                offset = pal_idx * 8 + col_idx * 2
                if offset + 1 < len(obj_data):
                    pal.colors.append(Color.from_raw(obj_data[offset], obj_data[offset + 1]))
                else:
                    pal.colors.append(Color())
            snap.obj_palettes.append(pal)

        return snap

    def render_text(self) -> str:
        lines = ["BG Palettes:"]
        for p in self.bg_palettes:
            lines.append(f"  {p}")
        lines.append("OBJ Palettes:")
        for p in self.obj_palettes:
            lines.append(f"  {p}")
        return "\n".join(lines)


__all__ = ["Color", "Palette", "PaletteSnapshot"]
