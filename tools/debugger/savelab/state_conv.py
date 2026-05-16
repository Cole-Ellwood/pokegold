"""Cross-format state conversion: VBA .sgm ↔ PyBoy .state.

Provides bidirectional conversion (where possible) between VBA-M save
states and PyBoy save states, plus a common intermediate format for
field-level inspection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .sgm_decoder import SgmState, decode_sgm


@dataclass
class UnifiedState:
    """Format-neutral state for cross-format comparison."""
    source_format: str = ""
    source_path: str = ""
    registers: dict[str, int] = field(default_factory=dict)
    wram: bytes = b""
    vram: bytes = b""
    oam: bytes = b""
    hram: bytes = b""
    rom_bank: int = 1
    wram_bank: int = 1
    extra: dict[str, Any] = field(default_factory=dict)

    def read_byte(self, addr: int) -> int:
        if 0xC000 <= addr < 0xE000:
            offset = addr - 0xC000
            if offset < len(self.wram):
                return self.wram[offset]
        elif 0xFF80 <= addr <= 0xFFFE:
            offset = addr - 0xFF80
            if offset < len(self.hram):
                return self.hram[offset]
        return 0

    def read_word_be(self, addr: int) -> int:
        return (self.read_byte(addr) << 8) | self.read_byte(addr + 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_format": self.source_format,
            "source_path": self.source_path,
            "registers": self.registers,
            "rom_bank": self.rom_bank,
            "wram_bank": self.wram_bank,
            "wram_size": len(self.wram),
            "vram_size": len(self.vram),
            "oam_size": len(self.oam),
            "hram_size": len(self.hram),
        }


def from_sgm(path: str | Path) -> UnifiedState:
    """Convert a VBA-M .sgm to UnifiedState."""
    sgm = decode_sgm(path)
    if not sgm.valid:
        return UnifiedState(source_format="sgm", source_path=str(path),
                            extra={"error": sgm.error})

    return UnifiedState(
        source_format="sgm",
        source_path=str(path),
        registers=sgm.registers.to_dict(),
        wram=sgm.wram_flat,
        vram=sgm.vram,
        oam=sgm.oam,
        hram=sgm.hram,
        rom_bank=sgm.rom_bank,
        wram_bank=sgm.wram_bank,
    )


def from_pyboy(path: str | Path) -> UnifiedState:
    """Convert a PyBoy .state to UnifiedState.

    PyBoy states are opaque binary — we extract WRAM/registers by
    loading the state into PyBoy and reading memory.  Without a live
    PyBoy instance, we do best-effort binary extraction.
    """
    path = Path(path)
    state = UnifiedState(source_format="pyboy", source_path=str(path))

    if not path.exists():
        state.extra["error"] = f"File not found: {path}"
        return state

    try:
        import io
        import zipfile

        raw = path.read_bytes()

        if raw[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                names = zf.namelist()
                for name in names:
                    data = zf.read(name)
                    if "wram" in name.lower() or "ram" in name.lower():
                        state.wram = data
                    elif "vram" in name.lower():
                        state.vram = data
                    elif "oam" in name.lower():
                        state.oam = data
                    elif "hram" in name.lower():
                        state.hram = data
                    elif "cpu" in name.lower() or "reg" in name.lower():
                        state.extra["cpu_blob"] = data
        else:
            # Raw binary state — try PyBoy's internal format
            # WRAM is typically at a known offset
            state.extra["raw_size"] = len(raw)
            # Best-effort: treat as raw WRAM dump if size matches
            if len(raw) >= 0x8000:
                state.wram = raw[:0x8000]

    except Exception as e:
        state.extra["error"] = str(e)

    return state


def convert(path: str | Path) -> UnifiedState:
    """Auto-detect format and convert to UnifiedState."""
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".sgm":
        return from_sgm(path)
    elif suffix == ".state":
        return from_pyboy(path)
    else:
        sgm = from_sgm(path)
        if sgm.wram:
            return sgm
        return from_pyboy(path)


__all__ = ["UnifiedState", "from_sgm", "from_pyboy", "convert"]
