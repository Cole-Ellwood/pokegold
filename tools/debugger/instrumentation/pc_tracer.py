"""Extended PC tracer with bank + cycle + macro context.

Extends the existing damage_debugger tracer pattern with:
- Per-instruction bank tracking (from hROMBank HRAM shadow)
- Cycle counting
- Macro context classification for each frame
- Event-shaped output (OTel-compatible dict)

This module does NOT require PyBoy — it defines the data model and
post-processing. The actual hook wiring lives in the emulator-specific
code (damage_debugger/tracer.py for PyBoy).

Usage:
    frame = TracerFrame(
        seq=0, bank=0x0b, pc=0x4000, cycle=12345,
        regs=RegisterSnapshot(A=0, F=0, B=0, C=0, D=0, E=0, HL=0, SP=0xDFFF),
        macro=MacroContext(macro_type=MacroType.FARCALL, target_label="Fn"),
    )
    event = frame.to_event()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .macro_resolver import MacroContext, MacroType, NO_MACRO


@dataclass(frozen=True)
class RegisterSnapshot:
    """CPU register file at a point in time."""
    A: int
    F: int
    B: int
    C: int
    D: int
    E: int
    HL: int
    SP: int

    @property
    def Z(self) -> int:
        return (self.F >> 7) & 1

    @property
    def N(self) -> int:
        return (self.F >> 6) & 1

    @property
    def H(self) -> int:
        return (self.F >> 5) & 1

    @property
    def Cf(self) -> int:
        return (self.F >> 4) & 1

    @property
    def BC(self) -> int:
        return (self.B << 8) | self.C

    @property
    def DE(self) -> int:
        return (self.D << 8) | self.E

    def to_dict(self) -> dict[str, int]:
        return {
            "A": self.A, "F": self.F,
            "B": self.B, "C": self.C,
            "D": self.D, "E": self.E,
            "HL": self.HL, "SP": self.SP,
        }


@dataclass
class TracerFrame:
    """One instruction's worth of trace data."""
    seq: int
    bank: int
    pc: int
    cycle: int
    regs: RegisterSnapshot
    macro: MacroContext = field(default_factory=lambda: NO_MACRO)
    mnemonic: str = ""
    pc_label: str = ""
    watches: dict[str, list[int]] = field(default_factory=dict)

    def to_event(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {
            "seq": self.seq,
            "bank": self.bank,
            "pc": self.pc,
            "cycle": self.cycle,
            "mnemonic": self.mnemonic,
            "pc_label": self.pc_label,
            **self.regs.to_dict(),
        }
        if self.macro.is_macro:
            attrs["macro_type"] = self.macro.macro_type.value
            attrs["macro_target"] = self.macro.target_label
        if self.watches:
            attrs["watches"] = self.watches
        return {
            "name": "instruction",
            "start_cycle": self.cycle,
            "end_cycle": self.cycle,
            "attributes": attrs,
        }


@dataclass
class TraceSession:
    """A collection of trace frames from one scenario run."""
    frames: list[TracerFrame] = field(default_factory=list)
    scenario_id: str = ""
    rom_hash: str = ""
    sym_hash: str = ""

    def append(self, frame: TracerFrame) -> None:
        self.frames.append(frame)

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def cycle_range(self) -> tuple[int, int]:
        if not self.frames:
            return (0, 0)
        return (self.frames[0].cycle, self.frames[-1].cycle)

    @property
    def bank_set(self) -> set[int]:
        return {f.bank for f in self.frames}

    @property
    def pc_set(self) -> set[int]:
        return {f.pc for f in self.frames}

    def frames_at_pc(self, pc: int) -> list[TracerFrame]:
        return [f for f in self.frames if f.pc == pc]

    def frames_in_bank(self, bank: int) -> list[TracerFrame]:
        return [f for f in self.frames if f.bank == bank]

    def macro_frames(self) -> list[TracerFrame]:
        return [f for f in self.frames if f.macro.is_macro]

    def to_events(self) -> list[dict[str, Any]]:
        return [f.to_event() for f in self.frames]
