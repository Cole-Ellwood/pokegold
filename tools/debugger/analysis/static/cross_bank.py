"""Cross-bank call audit — promoted from tools/audit/check_cross_bank_call.py.

Detects plain `call` to a label in a different ROMX bank. A bare `call`
only reaches the current bank or ROM0 — calling a `::` label in another
bank with `call` assembles but jumps to garbage at runtime.

This is the same check as the existing audit script, but structured as
a library that other analysis tools can compose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...kernel.symbol_service import SymbolService


@dataclass(frozen=True)
class CrossBankViolation:
    """One instance of a plain call to another bank."""
    caller_bank: int
    caller_pc: int
    caller_label: str
    target_bank: int
    target_addr: int
    target_label: str

    def summary_line(self) -> str:
        return (
            f"${self.caller_bank:02x}:{self.caller_pc:04x} ({self.caller_label}) "
            f"calls ${self.target_bank:02x}:{self.target_addr:04x} "
            f"({self.target_label}) via plain call"
        )


@dataclass
class CrossBankReport:
    """Results of the cross-bank call scan."""
    violations: list[CrossBankViolation] = field(default_factory=list)
    banks_scanned: int = 0
    calls_checked: int = 0

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        lines = [
            f"Cross-bank call audit: {len(self.violations)} violations "
            f"({self.banks_scanned} banks, {self.calls_checked} calls checked)"
        ]
        for v in self.violations[:20]:
            lines.append(f"  {v.summary_line()}")
        if len(self.violations) > 20:
            lines.append(f"  ... and {len(self.violations) - 20} more")
        return "\n".join(lines)


CALL_OPCODES = {0xCD, 0xC4, 0xCC, 0xD4, 0xDC}


def scan_cross_bank_calls(
    rom: bytes,
    svc: SymbolService,
    banks: list[int] | None = None,
) -> CrossBankReport:
    """Scan ROM for plain calls that cross ROMX bank boundaries."""
    from tools.damage_debugger.disasm import opcode_length

    report = CrossBankReport()

    if banks is None:
        max_bank = len(rom) // 0x4000
        banks = list(range(1, max_bank))

    for bank in banks:
        report.banks_scanned += 1
        bank_start = bank * 0x4000
        bank_end = bank_start + 0x4000

        if bank_end > len(rom):
            continue

        pc = 0x4000
        while pc < 0x8000:
            offset = bank_start + (pc - 0x4000)
            if offset >= len(rom):
                break

            op = rom[offset]
            length = opcode_length(op)

            if op in CALL_OPCODES and length == 3:
                if offset + 3 <= len(rom):
                    target_lo = rom[offset + 1]
                    target_hi = rom[offset + 2]
                    target_addr = (target_hi << 8) | target_lo

                    report.calls_checked += 1

                    if 0x4000 <= target_addr < 0x8000:
                        target_label = svc.render(bank, target_addr)
                        for other_bank in range(1, len(rom) // 0x4000):
                            if other_bank == bank:
                                continue
                            sym_label = svc.render(other_bank, target_addr)
                            if sym_label != f"${other_bank:02x}:{target_addr:04x}":
                                pass

                        sym = None
                        for b in range(256):
                            if b == bank:
                                continue
                            labels = svc.labels_in_bank(b)
                            for addr, name in labels:
                                if addr == target_addr and 0x4000 <= addr < 0x8000:
                                    sym = (b, name)
                                    break
                            if sym:
                                break

                        if sym is not None:
                            target_bank, target_name = sym
                            caller_label = svc.render(bank, pc)
                            report.violations.append(CrossBankViolation(
                                caller_bank=bank,
                                caller_pc=pc,
                                caller_label=caller_label,
                                target_bank=target_bank,
                                target_addr=target_addr,
                                target_label=target_name,
                            ))

            pc += length

    return report
