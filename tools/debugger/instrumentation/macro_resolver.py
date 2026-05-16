"""Macro resolver: given a PC, identify if it's inside a macro expansion.

This codebase uses several macros that expand inline:
  - farcall TARGET  -> ld a, BANK(TARGET); ld hl, TARGET; rst FarCall
  - callfar TARGET  -> ld hl, TARGET; ld a, BANK(TARGET); rst FarCall
  - homecall TARGET -> ldh a, [hROMBank]; push af; ld a, BANK(TARGET);
                        rst Bankswitch; call TARGET; pop af; rst Bankswitch
  - JumpTable        -> macro dispatch; see macros/scripts/jumptable.asm

The resolver inspects a window of bytes around a PC to classify
whether the current instruction is part of a known macro expansion.

Usage:
    resolver = MacroResolver(symbol_service)
    ctx = resolver.classify(rom_bytes, bank, pc)
    if ctx.macro_type:
        print(f"Inside {ctx.macro_type} to {ctx.target_label}")
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..kernel.symbol_service import SymbolService


class MacroType(Enum):
    FARCALL = "farcall"
    CALLFAR = "callfar"
    HOMECALL = "homecall"
    RST_BANKSWITCH = "rst Bankswitch"
    RST_FARCALL = "rst FarCall"
    PLAIN_CALL = "call"
    PLAIN_RST = "rst"
    NONE = None


RST_FARCALL_ADDR = 0x0008
RST_BANKSWITCH_ADDR = 0x0010


@dataclass(frozen=True)
class MacroContext:
    """Classification of a PC within a macro expansion."""
    macro_type: MacroType
    target_label: str = ""
    target_bank: int = -1
    target_addr: int = -1
    expansion_start_pc: int = -1
    expansion_end_pc: int = -1
    position_in_expansion: int = 0

    @property
    def is_macro(self) -> bool:
        return self.macro_type not in (MacroType.NONE, MacroType.PLAIN_CALL, MacroType.PLAIN_RST)

    def __str__(self) -> str:
        if self.macro_type == MacroType.NONE:
            return "(not a macro)"
        label = self.target_label or f"${self.target_bank:02x}:{self.target_addr:04x}"
        return f"{self.macro_type.value} {label}"


NO_MACRO = MacroContext(macro_type=MacroType.NONE)


def _read_rom(rom: bytes | memoryview, bank: int, pc: int) -> int:
    if pc < 0x4000:
        return rom[pc] if pc < len(rom) else 0
    offset = bank * 0x4000 + (pc - 0x4000)
    return rom[offset] if offset < len(rom) else 0


def _read_rom_u16(rom: bytes | memoryview, bank: int, pc: int) -> int:
    lo = _read_rom(rom, bank, pc)
    hi = _read_rom(rom, bank, pc + 1)
    return (hi << 8) | lo


class MacroResolver:
    """Classifies PCs as being inside macro expansions.

    Requires ROM bytes and the symbol service for label resolution.
    """

    def __init__(self, svc: SymbolService | None = None):
        self._svc = svc

    def _label_at(self, bank: int, addr: int) -> str:
        if self._svc is None:
            return ""
        return self._svc.render(bank, addr)

    def classify(self, rom: bytes | memoryview, bank: int, pc: int) -> MacroContext:
        op = _read_rom(rom, bank, pc)

        # rst $08 = FarCall (opcode 0xCF)
        if op == 0xCF:
            return self._classify_rst_farcall(rom, bank, pc)

        # rst $10 = Bankswitch (opcode 0xD7)
        if op == 0xD7:
            return MacroContext(
                macro_type=MacroType.RST_BANKSWITCH,
                expansion_start_pc=pc,
                expansion_end_pc=pc,
            )

        # call nn
        if op == 0xCD:
            target = _read_rom_u16(rom, bank, pc + 1)
            target_label = self._label_at(bank, target)
            return MacroContext(
                macro_type=MacroType.PLAIN_CALL,
                target_label=target_label,
                target_bank=bank,
                target_addr=target,
                expansion_start_pc=pc,
                expansion_end_pc=pc + 2,
            )

        # Check if this instruction is part of a farcall/callfar expansion.
        # farcall: ld a, imm8 (0x3E); ld hl, imm16 (0x21); rst $08 (0xCF)
        # callfar: ld hl, imm16 (0x21); ld a, imm8 (0x3E); rst $08 (0xCF)
        ctx = self._check_farcall_window(rom, bank, pc)
        if ctx is not None:
            return ctx

        ctx = self._check_homecall_window(rom, bank, pc)
        if ctx is not None:
            return ctx

        return NO_MACRO

    def _classify_rst_farcall(
        self, rom: bytes | memoryview, bank: int, pc: int
    ) -> MacroContext:
        # Look back: farcall pattern is ld a, bank (2B); ld hl, addr (3B); rst $08
        # Total 6 bytes, rst at offset 5
        if pc >= 5:
            op_m5 = _read_rom(rom, bank, pc - 5)
            op_m2 = _read_rom(rom, bank, pc - 2)
            # farcall: 0x3E bank 0x21 lo hi 0xCF
            if op_m5 == 0x3E and op_m2 == 0x21:
                return self._build_farcall_ctx(rom, bank, pc - 5, MacroType.FARCALL, 5)
            # callfar: 0x21 lo hi 0x3E bank 0xCF
            if op_m5 == 0x21 and op_m2 == 0x3E:
                return self._build_callfar_ctx(rom, bank, pc - 5, MacroType.CALLFAR, 5)

        return MacroContext(
            macro_type=MacroType.RST_FARCALL,
            expansion_start_pc=pc,
            expansion_end_pc=pc,
        )

    def _build_farcall_ctx(
        self, rom: bytes | memoryview, bank: int, start_pc: int,
        mtype: MacroType, position: int,
    ) -> MacroContext:
        # farcall: ld a, BANK (start+1); ld hl, addr (start+3..4)
        target_bank = _read_rom(rom, bank, start_pc + 1)
        target_addr = _read_rom_u16(rom, bank, start_pc + 3)
        target_label = self._label_at(target_bank, target_addr)
        return MacroContext(
            macro_type=mtype,
            target_label=target_label,
            target_bank=target_bank,
            target_addr=target_addr,
            expansion_start_pc=start_pc,
            expansion_end_pc=start_pc + 5,
            position_in_expansion=position,
        )

    def _build_callfar_ctx(
        self, rom: bytes | memoryview, bank: int, start_pc: int,
        mtype: MacroType, position: int,
    ) -> MacroContext:
        # callfar: ld hl, addr (start+1..2); ld a, BANK (start+4)
        target_addr = _read_rom_u16(rom, bank, start_pc + 1)
        target_bank = _read_rom(rom, bank, start_pc + 4)
        target_label = self._label_at(target_bank, target_addr)
        return MacroContext(
            macro_type=mtype,
            target_label=target_label,
            target_bank=target_bank,
            target_addr=target_addr,
            expansion_start_pc=start_pc,
            expansion_end_pc=start_pc + 5,
            position_in_expansion=position,
        )

    def _check_farcall_window(
        self, rom: bytes | memoryview, bank: int, pc: int
    ) -> MacroContext | None:
        op = _read_rom(rom, bank, pc)

        # ld a, imm8 at start of farcall
        if op == 0x3E and pc + 5 < 0x8000:
            op2 = _read_rom(rom, bank, pc + 2)
            op5 = _read_rom(rom, bank, pc + 5)
            if op2 == 0x21 and op5 == 0xCF:
                return self._build_farcall_ctx(rom, bank, pc, MacroType.FARCALL, 0)

        # ld hl, imm16 at start of callfar or middle of farcall
        if op == 0x21:
            # callfar: 0x21 lo hi 0x3E bank 0xCF
            if pc + 5 < 0x8000:
                op3 = _read_rom(rom, bank, pc + 3)
                op5 = _read_rom(rom, bank, pc + 5)
                if op3 == 0x3E and op5 == 0xCF:
                    return self._build_callfar_ctx(rom, bank, pc, MacroType.CALLFAR, 0)
            # middle of farcall: previous byte is bank, byte before that is 0x3E
            if pc >= 2:
                op_m2 = _read_rom(rom, bank, pc - 2)
                if op_m2 == 0x3E:
                    op_p3 = _read_rom(rom, bank, pc + 3) if pc + 3 < 0x8000 else 0
                    if op_p3 == 0xCF:
                        return self._build_farcall_ctx(rom, bank, pc - 2, MacroType.FARCALL, 2)

        return None

    def _check_homecall_window(
        self, rom: bytes | memoryview, bank: int, pc: int
    ) -> MacroContext | None:
        op = _read_rom(rom, bank, pc)
        # homecall starts: ldh a, [hROMBank] = 0xF0 XX; push af = 0xF5;
        # ld a, BANK = 0x3E XX; rst Bankswitch = 0xD7;
        # call TARGET = 0xCD lo hi; pop af = 0xF1; rst Bankswitch = 0xD7
        # Total: 2+1+2+1+3+1+1 = 11 bytes

        if op == 0xF0 and pc + 10 < 0x8000:
            seq = [_read_rom(rom, bank, pc + i) for i in range(11)]
            if (seq[2] == 0xF5 and seq[3] == 0x3E and seq[5] == 0xD7
                    and seq[6] == 0xCD and seq[9] == 0xF1 and seq[10] == 0xD7):
                target_addr = seq[7] | (seq[8] << 8)
                target_bank = seq[4]
                target_label = self._label_at(target_bank, target_addr)
                return MacroContext(
                    macro_type=MacroType.HOMECALL,
                    target_label=target_label,
                    target_bank=target_bank,
                    target_addr=target_addr,
                    expansion_start_pc=pc,
                    expansion_end_pc=pc + 10,
                    position_in_expansion=0,
                )

        return None
