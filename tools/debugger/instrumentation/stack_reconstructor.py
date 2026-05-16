"""Cross-bank stack reconstructor.

farcall/callfar use `rst FarCall` which pushes a return address that's
inside the FarCall_hl ROM0 trampoline, not the original call site.
This module reconstructs the logical call stack by tracking:
  1. farcall/callfar expansions (detected by macro_resolver)
  2. rst FarCall entries and exits
  3. Bank switches via hROMBank

The result is a logical call stack where each frame has:
  (caller_bank, caller_pc, callee_bank, callee_pc, callee_label, is_far)

Usage:
    sr = StackReconstructor(symbol_service)
    sr.on_instruction(cycle, bank, pc, sp, rom_bytes)
    stack = sr.current_stack()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from .macro_resolver import MacroContext, MacroResolver, MacroType

if TYPE_CHECKING:
    from ..kernel.symbol_service import SymbolService


@dataclass(frozen=True)
class CallFrame:
    """One frame in the logical call stack."""
    caller_bank: int
    caller_pc: int
    callee_bank: int
    callee_pc: int
    callee_label: str
    is_far: bool
    entry_cycle: int
    sp_at_entry: int

    def __str__(self) -> str:
        far_tag = " [far]" if self.is_far else ""
        return (
            f"${self.caller_bank:02x}:{self.caller_pc:04x} -> "
            f"{self.callee_label or f'${self.callee_bank:02x}:{self.callee_pc:04x}'}"
            f"{far_tag}"
        )


class StackReconstructor:
    """Reconstruct the logical call stack across bank switches.

    Feed it every instruction via on_instruction(). It maintains
    a shadow stack that correctly handles farcall/callfar transitions.
    """

    def __init__(self, svc: SymbolService | None = None) -> None:
        self._svc = svc
        self._resolver = MacroResolver(svc)
        self._stack: list[CallFrame] = []
        self._prev_bank: int = 0
        self._prev_pc: int = 0
        self._prev_sp: int = 0xDFFF
        self._in_farcall: bool = False
        self._farcall_caller_bank: int = 0
        self._farcall_caller_pc: int = 0

    def on_instruction(
        self,
        cycle: int,
        bank: int,
        pc: int,
        sp: int,
        rom: bytes | memoryview,
    ) -> None:
        sp_delta = sp - self._prev_sp

        # Detect call entry: SP decreased by 2 (return address pushed)
        if sp_delta == -2 and pc != self._prev_pc + 1:
            ctx = self._resolver.classify(rom, self._prev_bank, self._prev_pc)
            is_far = ctx.macro_type in (
                MacroType.FARCALL, MacroType.CALLFAR,
                MacroType.RST_FARCALL, MacroType.HOMECALL,
            )
            label = ""
            if self._svc:
                label = self._svc.render(bank, pc)

            frame = CallFrame(
                caller_bank=self._prev_bank,
                caller_pc=self._prev_pc,
                callee_bank=bank,
                callee_pc=pc,
                callee_label=label,
                is_far=is_far,
                entry_cycle=cycle,
                sp_at_entry=sp,
            )
            self._stack.append(frame)

        # Detect return: SP increased by 2 and we're back at a previous frame's context
        elif sp_delta == 2 and self._stack:
            top = self._stack[-1]
            if sp >= top.sp_at_entry:
                self._stack.pop()

        # Detect farcall trampoline return: SP increased by more than 2
        # (FarCall_hl pops its own frame + restores bank)
        elif sp_delta > 2 and self._stack:
            while self._stack and sp >= self._stack[-1].sp_at_entry:
                self._stack.pop()

        self._prev_bank = bank
        self._prev_pc = pc
        self._prev_sp = sp

    def current_stack(self) -> list[CallFrame]:
        return list(self._stack)

    @property
    def depth(self) -> int:
        return len(self._stack)

    @property
    def far_depth(self) -> int:
        return sum(1 for f in self._stack if f.is_far)

    def format_stack(self) -> str:
        if not self._stack:
            return "(empty stack)"
        lines = []
        for i, frame in enumerate(reversed(self._stack)):
            indent = "  " * i
            lines.append(f"{indent}{frame}")
        return "\n".join(lines)

    def clear(self) -> None:
        self._stack.clear()
        self._prev_bank = 0
        self._prev_pc = 0
        self._prev_sp = 0xDFFF
