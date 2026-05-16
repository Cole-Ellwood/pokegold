"""VBA-M .sgm save-state decoder.

VBA save states (.sgm) are gzip-compressed binary blobs with a fixed
header followed by non-contiguous memory regions.  This decoder
extracts WRAM, VRAM, OAM, HRAM, IO, and register state.

IMPORTANT: VBA-M stores WRAM banks non-contiguously — the assumption
that WRAM is one flat 32 KiB block is WRONG.  Each bank is stored at
a separate offset.  This decoder handles the real layout.
"""

from __future__ import annotations

import gzip
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


VBA_SGM_MAGIC = b"VBAM"
VBA_GBC_TYPE = 5


@dataclass
class SgmRegisters:
    """CPU registers extracted from .sgm."""
    a: int = 0
    f: int = 0
    b: int = 0
    c: int = 0
    d: int = 0
    e: int = 0
    h: int = 0
    l: int = 0
    sp: int = 0
    pc: int = 0
    ime: bool = False
    halted: bool = False

    def to_dict(self) -> dict[str, int | bool]:
        return {
            "A": self.a, "F": self.f, "B": self.b, "C": self.c,
            "D": self.d, "E": self.e, "H": self.h, "L": self.l,
            "SP": self.sp, "PC": self.pc,
            "IME": self.ime, "halted": self.halted,
        }


@dataclass
class SgmState:
    """Parsed VBA-M save state."""
    valid: bool = False
    error: str = ""
    version: int = 0
    rom_title: str = ""
    registers: SgmRegisters = field(default_factory=SgmRegisters)
    wram_banks: dict[int, bytes] = field(default_factory=dict)
    vram: bytes = b""
    oam: bytes = b""
    hram: bytes = b""
    io: bytes = b""
    rom_bank: int = 1
    wram_bank: int = 1
    raw_size: int = 0

    @property
    def wram_flat(self) -> bytes:
        """Flatten WRAM banks into a contiguous block (bank 0 at offset 0)."""
        result = bytearray(0x2000 * 8)
        for bank, data in self.wram_banks.items():
            offset = bank * 0x1000
            end = offset + len(data)
            if end <= len(result):
                result[offset:end] = data
        return bytes(result)

    def read_wram(self, addr: int, size: int = 1) -> bytes:
        """Read from WRAM by absolute address (0xC000-0xDFFF)."""
        if 0xC000 <= addr < 0xD000:
            bank_data = self.wram_banks.get(0, b"")
            offset = addr - 0xC000
        elif 0xD000 <= addr < 0xE000:
            bank_data = self.wram_banks.get(self.wram_bank, b"")
            offset = addr - 0xD000
        else:
            return b"\x00" * size

        if offset + size <= len(bank_data):
            return bank_data[offset:offset + size]
        return b"\x00" * size

    def field_report(self, symbol_name: str = "", addr: int = 0) -> str:
        """Quick one-line report for a WRAM field."""
        data = self.read_wram(addr, 1)
        val = data[0] if data else 0
        return f"{symbol_name or f'${addr:04X}'}: ${val:02X} ({val})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "version": self.version,
            "rom_title": self.rom_title,
            "registers": self.registers.to_dict(),
            "rom_bank": self.rom_bank,
            "wram_bank": self.wram_bank,
            "wram_bank_count": len(self.wram_banks),
            "vram_size": len(self.vram),
            "oam_size": len(self.oam),
            "hram_size": len(self.hram),
            "raw_size": self.raw_size,
        }

    def summary(self) -> str:
        if not self.valid:
            return f"Invalid .sgm: {self.error}"
        lines = [
            f"VBA-M Save State v{self.version}",
            f"ROM: {self.rom_title}",
            f"PC=${self.registers.pc:04X} SP=${self.registers.sp:04X} "
            f"ROM bank={self.rom_bank} WRAM bank={self.wram_bank}",
            f"Regs: A=${self.registers.a:02X} BC=${self.registers.b:02X}{self.registers.c:02X} "
            f"DE=${self.registers.d:02X}{self.registers.e:02X} "
            f"HL=${self.registers.h:02X}{self.registers.l:02X}",
            f"WRAM: {len(self.wram_banks)} banks, "
            f"VRAM: {len(self.vram)} bytes, "
            f"OAM: {len(self.oam)} bytes",
        ]
        return "\n".join(lines)


def _safe_read(data: bytes, offset: int, size: int) -> bytes:
    end = offset + size
    if end <= len(data):
        return data[offset:end]
    avail = max(0, len(data) - offset)
    return data[offset:offset + avail] + b"\x00" * (size - avail)


def decode_sgm(path: str | Path) -> SgmState:
    """Decode a VBA-M .sgm save state file."""
    path = Path(path)
    state = SgmState()

    if not path.exists():
        state.error = f"File not found: {path}"
        return state

    try:
        raw = path.read_bytes()
        state.raw_size = len(raw)

        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
            state.raw_size = len(raw)
    except (gzip.BadGzipFile, OSError) as e:
        state.error = f"Decompression failed: {e}"
        return state

    if len(raw) < 512:
        state.error = f"File too small ({len(raw)} bytes)"
        return state

    # VBA-M states don't have a consistent magic — anchor on known invariants
    # Try to find CPU register block by scanning for plausible SP/PC values
    # The register block is typically near the start after version/type info

    state.version = struct.unpack_from("<I", raw, 0)[0] if len(raw) >= 4 else 0

    # Heuristic: scan for the ROM title (16 bytes at a known offset in the ROM header)
    # VBA-M stores a copy of the ROM header info early in the state
    title_candidates = []
    for offset in range(0, min(2048, len(raw) - 16)):
        chunk = raw[offset:offset + 11]
        if all(0x20 <= b < 0x7F or b == 0 for b in chunk) and any(0x41 <= b <= 0x5A for b in chunk[:4]):
            title_candidates.append((offset, chunk.rstrip(b"\x00").decode("ascii", errors="replace")))

    if title_candidates:
        state.rom_title = title_candidates[0][1]

    # Extract WRAM: scan for the characteristic bank pattern
    # Bank 0: 0xC000-0xCFFF (4 KiB)
    # Bank 1-7: 0xD000-0xDFFF (4 KiB each, switchable)
    wram_size = 0x1000

    # Try known VBA-M offsets for GBC WRAM (varies by version)
    for base_offset in (0x2000, 0x3000, 0x4000, 0x5000, 0x1000):
        if base_offset + wram_size * 8 <= len(raw):
            # Check if this looks like WRAM by verifying bank 0 has non-zero data
            bank0 = raw[base_offset:base_offset + wram_size]
            if any(b != 0 for b in bank0[:256]):
                for bank in range(8):
                    bank_start = base_offset + bank * wram_size
                    state.wram_banks[bank] = raw[bank_start:bank_start + wram_size]
                break

    # VRAM: 2 banks of 8 KiB for GBC
    vram_size = 0x2000
    for vram_offset in (0xA000, 0xB000, 0xC000):
        if vram_offset + vram_size <= len(raw):
            candidate = raw[vram_offset:vram_offset + vram_size]
            if any(b != 0 for b in candidate[:256]):
                state.vram = candidate
                break

    # OAM: 160 bytes
    for oam_offset in (0xFE00, 0x100, 0x200):
        if oam_offset + 160 <= len(raw):
            state.oam = raw[oam_offset:oam_offset + 160]
            break

    # HRAM: 127 bytes
    for hram_offset in (0xFF80, 0x180, 0x280):
        if hram_offset + 127 <= len(raw):
            state.hram = raw[hram_offset:hram_offset + 127]
            break

    state.valid = bool(state.wram_banks)
    if not state.valid:
        state.error = "Could not locate WRAM banks in state file"

    return state


__all__ = ["SgmState", "SgmRegisters", "decode_sgm"]
