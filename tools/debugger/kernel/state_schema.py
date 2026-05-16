"""Project-wide state schema for WRAM / SRAM / HRAM / IO regions.

Stdlib-only (dataclasses, no Pydantic). Models the debugger's view of
memory at a point in time: which regions exist, what named fields they
contain, and how to decode bytes into meaningful values.

The schema is built from .sym + .map data at runtime. It does NOT parse
ram/*.asm directly — the linker output is the source of truth for actual
addresses.

Usage:
    from tools.debugger.kernel.state_schema import WorldState, MemoryRegion
    ws = WorldState.from_symbol_service(svc)
    print(ws.summary())
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .symbol_service import SymbolService, SymbolEntry


class RegionType(Enum):
    ROM0 = "ROM0"
    ROMX = "ROMX"
    VRAM = "VRAM"
    SRAM = "SRAM"
    WRAM0 = "WRAM0"
    WRAMX = "WRAMX"
    OAM = "OAM"
    HRAM = "HRAM"
    IO = "IO"


REGION_RANGES: dict[RegionType, tuple[int, int]] = {
    RegionType.ROM0:  (0x0000, 0x3FFF),
    RegionType.ROMX:  (0x4000, 0x7FFF),
    RegionType.VRAM:  (0x8000, 0x9FFF),
    RegionType.SRAM:  (0xA000, 0xBFFF),
    RegionType.WRAM0: (0xC000, 0xCFFF),
    RegionType.WRAMX: (0xD000, 0xDFFF),
    RegionType.OAM:   (0xFE00, 0xFE9F),
    RegionType.IO:    (0xFF00, 0xFF7F),
    RegionType.HRAM:  (0xFF80, 0xFFFE),
}


class Visibility(Enum):
    PUBLIC = "public"
    SEMI_PUBLIC = "semi_public"
    HIDDEN = "hidden"
    HAKI = "haki"


BATTLE_PUBLIC_PREFIXES = (
    "wBattleMon", "wEnemyMon", "wPlayerMon",
    "wCurDamage", "wTypeModifier",
)
BATTLE_HIDDEN_PREFIXES = (
    "wEnemyMonUnrevealedMoves", "wEnemyParty",
)


@dataclass(frozen=True)
class NamedField:
    """A named memory location from .sym."""
    name: str
    bank: int
    address: int
    size: int = 1
    visibility: Visibility = Visibility.PUBLIC
    doc: str = ""

    @property
    def region_type(self) -> RegionType:
        for rt, (lo, hi) in REGION_RANGES.items():
            if lo <= self.address <= hi:
                return rt
        return RegionType.WRAM0

    def __str__(self) -> str:
        return f"${self.bank:02x}:{self.address:04x} {self.name} ({self.size}B)"


@dataclass
class MemoryRegion:
    """A contiguous memory region with its named fields."""
    region_type: RegionType
    bank: int
    start: int
    end: int
    fields: list[NamedField] = field(default_factory=list)

    @property
    def size(self) -> int:
        return self.end - self.start + 1

    @property
    def field_count(self) -> int:
        return len(self.fields)

    def field_at(self, addr: int) -> NamedField | None:
        for f in self.fields:
            if f.address == addr:
                return f
        return None

    def fields_in_range(self, lo: int, hi: int) -> list[NamedField]:
        return [f for f in self.fields if lo <= f.address <= hi]

    def summary_line(self) -> str:
        return (
            f"{self.region_type.value} bank {self.bank}: "
            f"${self.start:04x}-${self.end:04x} "
            f"({self.size} bytes, {self.field_count} fields)"
        )


@dataclass
class BattleState:
    """Subset of WorldState focused on battle-engine fields.

    Organized by the convention: wBattleMon* = player active,
    wEnemyMon* = enemy active. Stat-stage bytes use base-7 encoding.
    """
    player_fields: list[NamedField] = field(default_factory=list)
    enemy_fields: list[NamedField] = field(default_factory=list)
    shared_fields: list[NamedField] = field(default_factory=list)

    @property
    def field_count(self) -> int:
        return (len(self.player_fields) + len(self.enemy_fields)
                + len(self.shared_fields))


@dataclass
class SaveState:
    """Subset focused on SRAM fields (save-format-sensitive)."""
    fields: list[NamedField] = field(default_factory=list)
    save_format_version_field: NamedField | None = None

    @property
    def field_count(self) -> int:
        return len(self.fields)


def _classify_visibility(name: str) -> Visibility:
    for prefix in BATTLE_HIDDEN_PREFIXES:
        if name.startswith(prefix):
            return Visibility.HIDDEN
    return Visibility.PUBLIC


def _infer_size(symbols_sorted: list[tuple[int, str]], idx: int, region_end: int) -> int:
    if idx + 1 < len(symbols_sorted):
        next_addr = symbols_sorted[idx + 1][0]
        gap = next_addr - symbols_sorted[idx][0]
        if 0 < gap <= 256:
            return gap
    return 1


@dataclass
class WorldState:
    """Top-level state model: all memory regions + convenience views."""
    regions: list[MemoryRegion] = field(default_factory=list)
    battle: BattleState = field(default_factory=BattleState)
    save: SaveState = field(default_factory=SaveState)

    @classmethod
    def from_symbol_service(cls, svc: SymbolService) -> WorldState:
        regions: list[MemoryRegion] = []
        all_fields: list[NamedField] = []

        for rt, (lo, hi) in REGION_RANGES.items():
            region_fields: list[NamedField] = []

            for bank, items in sorted(
                ((b, items) for b, items in (
                    (b, svc.labels_in_bank(b)) for b in range(256)
                ) if items),
            ):
                bank_fields = []
                bank_items = [(addr, name) for addr, name in items if lo <= addr <= hi]
                if not bank_items:
                    continue

                for i, (addr, name) in enumerate(bank_items):
                    size = _infer_size(bank_items, i, hi)
                    nf = NamedField(
                        name=name,
                        bank=bank,
                        address=addr,
                        size=size,
                        visibility=_classify_visibility(name),
                    )
                    bank_fields.append(nf)
                    all_fields.append(nf)

                if bank_fields:
                    region = MemoryRegion(
                        region_type=rt,
                        bank=bank,
                        start=lo,
                        end=hi,
                        fields=bank_fields,
                    )
                    regions.append(region)

        battle = BattleState()
        save = SaveState()

        for nf in all_fields:
            if nf.name.startswith("wBattleMon") or nf.name.startswith("wPlayerMon"):
                battle.player_fields.append(nf)
            elif nf.name.startswith("wEnemyMon"):
                battle.enemy_fields.append(nf)
            elif nf.name.startswith(("wCurDamage", "wTypeModifier", "wBattle")):
                battle.shared_fields.append(nf)

            if nf.region_type == RegionType.SRAM:
                save.fields.append(nf)
                if "SaveFormatVersion" in nf.name or "SAVE_FORMAT_VERSION" in nf.name:
                    save.save_format_version_field = nf

        return cls(regions=regions, battle=battle, save=save)

    def summary(self) -> str:
        lines = ["=== World State Summary ===", ""]
        by_type: dict[RegionType, list[MemoryRegion]] = {}
        for r in self.regions:
            by_type.setdefault(r.region_type, []).append(r)

        for rt in RegionType:
            regs = by_type.get(rt, [])
            if not regs:
                continue
            total_fields = sum(r.field_count for r in regs)
            lines.append(
                f"{rt.value}: {len(regs)} bank(s), {total_fields} named fields"
            )

        lines.append("")
        lines.append(f"Battle fields: {self.battle.field_count}")
        lines.append(f"Save (SRAM) fields: {self.save.field_count}")
        if self.save.save_format_version_field:
            lines.append(
                f"Save format version at: {self.save.save_format_version_field}"
            )
        return "\n".join(lines)

    def region_summary_table(self) -> list[str]:
        lines = []
        for r in self.regions:
            lines.append(r.summary_line())
        return lines
