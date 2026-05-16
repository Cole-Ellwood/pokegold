"""Bank pressure analysis — free-space tracking and threshold enforcement.

Wraps the symbol service's bank_info into CI-actionable output: fail if
any ROMX bank's free bytes dropped below a configurable threshold.

Usage:
    from tools.debugger.analysis.static.bank_pressure import BankPressureChecker
    checker = BankPressureChecker(svc)
    report = checker.check(threshold=128)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...kernel.symbol_service import SymbolService, BankInfo


@dataclass(frozen=True)
class BankPressureEntry:
    """One bank's pressure status."""
    memory: str
    bank: int
    free_bytes: int
    used_bytes: int
    threshold: int
    over_threshold: bool

    @property
    def utilization_pct(self) -> int:
        total = self.free_bytes + self.used_bytes
        if total <= 0:
            return 0
        return self.used_bytes * 100 // total

    def summary_line(self) -> str:
        status = "OK" if self.over_threshold else "TIGHT"
        return (
            f"{self.memory} bank {self.bank:>3d}: "
            f"{self.free_bytes:>5d} free / {self.used_bytes:>5d} used "
            f"({self.utilization_pct}%) [{status}]"
        )


@dataclass
class BankPressureReport:
    """Full bank pressure report."""
    entries: list[BankPressureEntry] = field(default_factory=list)
    threshold: int = 256
    tight_count: int = 0
    total_banks: int = 0

    @property
    def ok(self) -> bool:
        return self.tight_count == 0

    def tight_banks(self) -> list[BankPressureEntry]:
        return [e for e in self.entries if not e.over_threshold]

    def summary(self) -> str:
        lines = [f"Bank pressure report (threshold={self.threshold} bytes):"]
        lines.append(f"  {self.total_banks} banks checked, {self.tight_count} tight")
        lines.append("")
        for e in self.entries:
            if not e.over_threshold:
                lines.append(f"  {e.summary_line()}")
        if self.tight_count == 0:
            lines.append("  All banks above threshold.")
        return "\n".join(lines)

    def full_report(self) -> str:
        lines = [f"Bank pressure report (threshold={self.threshold} bytes):"]
        lines.append(f"  {self.total_banks} banks, {self.tight_count} tight")
        lines.append("")
        for e in sorted(self.entries, key=lambda x: x.free_bytes):
            lines.append(f"  {e.summary_line()}")
        return "\n".join(lines)


class BankPressureChecker:
    """Checks ROM bank free space against thresholds."""

    def __init__(self, svc: SymbolService) -> None:
        self._svc = svc

    def check(
        self,
        threshold: int = 256,
        memory: str = "ROMX",
    ) -> BankPressureReport:
        entries: list[BankPressureEntry] = []
        all_info = self._svc.all_bank_info()

        for (mem, bank_num), info in sorted(all_info.items()):
            if mem != memory:
                continue
            free = info.total_free
            used = info.total_used
            entry = BankPressureEntry(
                memory=mem,
                bank=bank_num,
                free_bytes=free,
                used_bytes=used,
                threshold=threshold,
                over_threshold=free >= threshold,
            )
            entries.append(entry)

        tight_count = sum(1 for e in entries if not e.over_threshold)
        return BankPressureReport(
            entries=entries,
            threshold=threshold,
            tight_count=tight_count,
            total_banks=len(entries),
        )
