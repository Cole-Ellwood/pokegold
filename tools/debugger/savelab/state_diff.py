"""Field-by-field save-state comparison.

Compares two UnifiedState objects and reports every difference at the
named-field level (using the symbol service for field names) plus
raw byte diffs for unnamed regions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..kernel.symbol_service import SymbolService

from .state_conv import UnifiedState


@dataclass
class FieldDiff:
    """One differing field between two states."""
    name: str
    address: int
    left_value: int
    right_value: int
    left_hex: str = ""
    right_hex: str = ""
    region: str = "wram"

    def __post_init__(self) -> None:
        if not self.left_hex:
            self.left_hex = f"${self.left_value:02X}"
        if not self.right_hex:
            self.right_hex = f"${self.right_value:02X}"

    def __str__(self) -> str:
        return f"{self.name} (${self.address:04X}): {self.left_hex} → {self.right_hex}"


@dataclass
class StateDiffReport:
    """Full diff report between two states."""
    left_source: str = ""
    right_source: str = ""
    register_diffs: list[FieldDiff] = field(default_factory=list)
    wram_diffs: list[FieldDiff] = field(default_factory=list)
    vram_diffs: list[FieldDiff] = field(default_factory=list)
    hram_diffs: list[FieldDiff] = field(default_factory=list)
    oam_diffs: list[FieldDiff] = field(default_factory=list)

    @property
    def total_diffs(self) -> int:
        return (len(self.register_diffs) + len(self.wram_diffs) +
                len(self.vram_diffs) + len(self.hram_diffs) + len(self.oam_diffs))

    @property
    def identical(self) -> bool:
        return self.total_diffs == 0

    def summary(self, max_per_region: int = 20) -> str:
        lines = [
            f"State diff: {self.left_source} vs {self.right_source}",
            f"Total differences: {self.total_diffs}",
        ]

        if self.register_diffs:
            lines.append(f"\nRegisters ({len(self.register_diffs)} diffs):")
            for d in self.register_diffs:
                lines.append(f"  {d}")

        for label, diffs in [
            ("WRAM", self.wram_diffs),
            ("VRAM", self.vram_diffs),
            ("HRAM", self.hram_diffs),
            ("OAM", self.oam_diffs),
        ]:
            if diffs:
                shown = diffs[:max_per_region]
                lines.append(f"\n{label} ({len(diffs)} diffs):")
                for d in shown:
                    lines.append(f"  {d}")
                if len(diffs) > max_per_region:
                    lines.append(f"  ... and {len(diffs) - max_per_region} more")

        if self.identical:
            lines.append("\nStates are identical.")

        return "\n".join(lines)


def _diff_bytes(
    left: bytes,
    right: bytes,
    base_addr: int,
    region: str,
    symbol_service: SymbolService | None = None,
) -> list[FieldDiff]:
    diffs: list[FieldDiff] = []
    min_len = min(len(left), len(right))

    for i in range(min_len):
        if left[i] != right[i]:
            addr = base_addr + i
            name = f"${addr:04X}"
            if symbol_service:
                label = symbol_service.render(0, addr)
                if label and not label.startswith("$"):
                    name = label
            diffs.append(FieldDiff(
                name=name,
                address=addr,
                left_value=left[i],
                right_value=right[i],
                region=region,
            ))

    if len(left) != len(right):
        diffs.append(FieldDiff(
            name=f"{region}_size",
            address=0,
            left_value=len(left),
            right_value=len(right),
            left_hex=f"{len(left)} bytes",
            right_hex=f"{len(right)} bytes",
            region=region,
        ))

    return diffs


def diff_states(
    left: UnifiedState,
    right: UnifiedState,
    *,
    symbol_service: SymbolService | None = None,
    skip_vram: bool = False,
) -> StateDiffReport:
    """Compare two UnifiedStates field-by-field."""
    report = StateDiffReport(
        left_source=f"{left.source_format}:{left.source_path}",
        right_source=f"{right.source_format}:{right.source_path}",
    )

    left_regs = left.registers or {}
    right_regs = right.registers or {}
    all_reg_names = sorted(set(left_regs) | set(right_regs))
    for name in all_reg_names:
        lv = left_regs.get(name, 0)
        rv = right_regs.get(name, 0)
        if isinstance(lv, bool):
            lv = int(lv)
        if isinstance(rv, bool):
            rv = int(rv)
        if lv != rv:
            report.register_diffs.append(FieldDiff(
                name=name, address=0,
                left_value=lv, right_value=rv,
                region="registers",
            ))

    report.wram_diffs = _diff_bytes(
        left.wram, right.wram, 0xC000, "wram", symbol_service
    )

    if not skip_vram:
        report.vram_diffs = _diff_bytes(
            left.vram, right.vram, 0x8000, "vram", symbol_service
        )

    report.hram_diffs = _diff_bytes(
        left.hram, right.hram, 0xFF80, "hram", symbol_service
    )

    report.oam_diffs = _diff_bytes(
        left.oam, right.oam, 0xFE00, "oam", symbol_service
    )

    return report


__all__ = ["FieldDiff", "StateDiffReport", "diff_states"]
