"""Differential against vanilla pokegold.

Compares the hack ROM against a vanilla pokegold ROM (built from
upstream pret/pokegold) to verify parity-preserving changes produce
zero diffs where expected.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


VANILLA_GOLD_SHA1 = "d8b8a3600a465308c9953dfa04f0081c05bdcb94"


@dataclass
class RomRegion:
    """A named region of the ROM for comparison."""
    name: str
    start: int
    end: int
    description: str = ""

    @property
    def size(self) -> int:
        return self.end - self.start


FIXED_REGIONS = [
    RomRegion("header", 0x0100, 0x0150, "ROM header / entry point"),
    RomRegion("home_bank", 0x0000, 0x4000, "ROM0 — home bank"),
    RomRegion("bank_01", 0x4000, 0x8000, "ROMX bank 1"),
]


@dataclass
class ByteDiff:
    """One differing byte between two ROMs."""
    offset: int
    bank: int
    bank_offset: int
    vanilla_byte: int
    hack_byte: int
    label: str = ""

    def __str__(self) -> str:
        loc = self.label or f"${self.bank:02X}:${self.bank_offset:04X}"
        return f"${self.offset:06X} ({loc}): ${self.vanilla_byte:02X} → ${self.hack_byte:02X}"


@dataclass
class VanillaDiffReport:
    """Full diff report between vanilla and hack ROMs."""
    vanilla_path: str = ""
    hack_path: str = ""
    vanilla_sha1: str = ""
    hack_sha1: str = ""
    vanilla_size: int = 0
    hack_size: int = 0
    total_diffs: int = 0
    diffs_by_bank: dict[int, int] = field(default_factory=dict)
    sample_diffs: list[ByteDiff] = field(default_factory=list)
    parity_regions_checked: int = 0
    parity_regions_clean: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self, max_per_bank: int = 5) -> str:
        lines = [
            f"Vanilla diff: {self.vanilla_path} vs {self.hack_path}",
            f"Vanilla SHA1: {self.vanilla_sha1}",
            f"Hack SHA1:    {self.hack_sha1}",
            f"Total diffs:  {self.total_diffs} bytes",
        ]

        if self.diffs_by_bank:
            lines.append("\nDiffs by bank:")
            for bank in sorted(self.diffs_by_bank):
                count = self.diffs_by_bank[bank]
                lines.append(f"  Bank ${bank:02X}: {count} bytes changed")

        if self.sample_diffs:
            lines.append(f"\nSample diffs (first {len(self.sample_diffs)}):")
            for d in self.sample_diffs:
                lines.append(f"  {d}")

        if self.errors:
            lines.append(f"\nErrors: {', '.join(self.errors)}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "vanilla_sha1": self.vanilla_sha1,
            "hack_sha1": self.hack_sha1,
            "total_diffs": self.total_diffs,
            "diffs_by_bank": {f"${k:02X}": v for k, v in self.diffs_by_bank.items()},
            "parity_regions_checked": self.parity_regions_checked,
            "parity_regions_clean": self.parity_regions_clean,
            "errors": self.errors,
        }


def _sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def _offset_to_bank(offset: int) -> tuple[int, int]:
    if offset < 0x4000:
        return 0, offset
    bank = offset // 0x4000
    bank_offset = (offset % 0x4000) + 0x4000
    return bank, bank_offset


def diff_roms(
    vanilla_path: str | Path,
    hack_path: str | Path,
    *,
    max_sample_diffs: int = 100,
    parity_banks: set[int] | None = None,
) -> VanillaDiffReport:
    """Compare vanilla and hack ROMs byte-by-byte."""
    vanilla_path = Path(vanilla_path)
    hack_path = Path(hack_path)
    report = VanillaDiffReport(
        vanilla_path=str(vanilla_path),
        hack_path=str(hack_path),
    )

    if not vanilla_path.exists():
        report.errors.append(f"Vanilla ROM not found: {vanilla_path}")
        return report
    if not hack_path.exists():
        report.errors.append(f"Hack ROM not found: {hack_path}")
        return report

    vanilla = vanilla_path.read_bytes()
    hack = hack_path.read_bytes()
    report.vanilla_size = len(vanilla)
    report.hack_size = len(hack)
    report.vanilla_sha1 = _sha1(vanilla)
    report.hack_sha1 = _sha1(hack)

    min_len = min(len(vanilla), len(hack))
    for offset in range(min_len):
        if vanilla[offset] != hack[offset]:
            report.total_diffs += 1
            bank, bank_offset = _offset_to_bank(offset)
            report.diffs_by_bank[bank] = report.diffs_by_bank.get(bank, 0) + 1

            if len(report.sample_diffs) < max_sample_diffs:
                report.sample_diffs.append(ByteDiff(
                    offset=offset,
                    bank=bank,
                    bank_offset=bank_offset,
                    vanilla_byte=vanilla[offset],
                    hack_byte=hack[offset],
                ))

    if parity_banks:
        for bank in parity_banks:
            report.parity_regions_checked += 1
            if bank not in report.diffs_by_bank:
                report.parity_regions_clean += 1

    if len(vanilla) != len(hack):
        report.errors.append(
            f"Size mismatch: vanilla={len(vanilla)}, hack={len(hack)}"
        )

    return report


def build_vanilla(project_root: Path, output_dir: Path | None = None) -> Path | None:
    """Build vanilla pokegold from upstream pret source (if available)."""
    output = output_dir or project_root / "audit" / "debugger" / "baseline" / "vanilla"
    output.mkdir(parents=True, exist_ok=True)

    vanilla_rom = output / "pokegold.gbc"
    if vanilla_rom.exists():
        sha1 = _sha1(vanilla_rom.read_bytes())
        if sha1 == VANILLA_GOLD_SHA1:
            return vanilla_rom

    return None


__all__ = [
    "ByteDiff",
    "VanillaDiffReport",
    "diff_roms",
    "build_vanilla",
    "VANILLA_GOLD_SHA1",
]
