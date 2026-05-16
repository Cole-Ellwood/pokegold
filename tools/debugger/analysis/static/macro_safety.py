"""Macro safety audits — farcall hl/a clobber + c-mirror checks.

Structured library versions of the existing audit scripts:
- check_farcall_hl_clobber.py
- check_farcall_a_clobber.py
- check_typepassive_c_mirror.py

These are composable building blocks; the audit scripts call through here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...kernel.symbol_service import SymbolService
    from .clobber_inference import RegisterSummary


@dataclass(frozen=True)
class FarcallHLViolation:
    """A farcall to a function that reads HL as input."""
    caller_bank: int
    caller_pc: int
    caller_label: str
    target_name: str
    target_bank: int
    target_addr: int

    def summary_line(self) -> str:
        return (
            f"${self.caller_bank:02x}:{self.caller_pc:04x} ({self.caller_label}) "
            f"farcalls {self.target_name} which uses HL as input"
        )


@dataclass(frozen=True)
class FarcallAClobber:
    """A farcall site where caller reads `a` post-farcall but target doesn't mirror to `c`."""
    caller_bank: int
    caller_pc: int
    caller_label: str
    target_name: str

    def summary_line(self) -> str:
        return (
            f"${self.caller_bank:02x}:{self.caller_pc:04x} ({self.caller_label}) "
            f"reads A after farcall to {self.target_name} "
            f"(target may not mirror A->C)"
        )


@dataclass(frozen=True)
class CMirrorViolation:
    """A function reachable via farcall that writes C at exit, clobbering a caller's live C."""
    function_name: str
    bank: int
    address: int
    caller_names: tuple[str, ...] = ()

    def summary_line(self) -> str:
        callers = ", ".join(self.caller_names[:3])
        if len(self.caller_names) > 3:
            callers += f" +{len(self.caller_names) - 3} more"
        return (
            f"{self.function_name} at ${self.bank:02x}:{self.address:04x} "
            f"writes C at exit (callers: {callers})"
        )


@dataclass
class MacroSafetyReport:
    """Combined report from all macro safety checks."""
    hl_violations: list[FarcallHLViolation] = field(default_factory=list)
    a_clobbers: list[FarcallAClobber] = field(default_factory=list)
    c_mirror_violations: list[CMirrorViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            len(self.hl_violations) == 0
            and len(self.a_clobbers) == 0
            and len(self.c_mirror_violations) == 0
        )

    @property
    def total_findings(self) -> int:
        return (
            len(self.hl_violations)
            + len(self.a_clobbers)
            + len(self.c_mirror_violations)
        )

    def summary(self) -> str:
        lines = [f"Macro safety audit: {self.total_findings} findings"]
        if self.hl_violations:
            lines.append(f"  farcall HL clobber: {len(self.hl_violations)}")
            for v in self.hl_violations[:5]:
                lines.append(f"    {v.summary_line()}")
        if self.a_clobbers:
            lines.append(f"  farcall A clobber: {len(self.a_clobbers)}")
            for v in self.a_clobbers[:5]:
                lines.append(f"    {v.summary_line()}")
        if self.c_mirror_violations:
            lines.append(f"  C-mirror violations: {len(self.c_mirror_violations)}")
            for v in self.c_mirror_violations[:5]:
                lines.append(f"    {v.summary_line()}")
        if self.ok:
            lines.append("  All checks passed.")
        return "\n".join(lines)


def check_farcall_hl_input(
    summaries: dict[str, RegisterSummary],
    farcall_sites: list[tuple[int, int, str, str]],
) -> list[FarcallHLViolation]:
    """Check for farcalls to functions that use HL as input.

    farcall_sites: list of (caller_bank, caller_pc, caller_label, target_name)
    """
    violations = []
    for caller_bank, caller_pc, caller_label, target_name in farcall_sites:
        summary = summaries.get(target_name)
        if summary is None:
            continue
        if "H" in summary.uses or "L" in summary.uses:
            violations.append(FarcallHLViolation(
                caller_bank=caller_bank,
                caller_pc=caller_pc,
                caller_label=caller_label,
                target_name=target_name,
                target_bank=summary.bank,
                target_addr=summary.address,
            ))
    return violations


def check_c_mirror_safety(
    summaries: dict[str, RegisterSummary],
    farcall_targets: dict[str, list[str]],
) -> list[CMirrorViolation]:
    """Check for functions that write C at exit and are called via farcall.

    farcall_targets: mapping from target_name -> list of caller_names
    """
    violations = []
    for target_name, callers in farcall_targets.items():
        summary = summaries.get(target_name)
        if summary is None:
            continue
        if "C" in summary.defs and "C" not in summary.preserves:
            violations.append(CMirrorViolation(
                function_name=target_name,
                bank=summary.bank,
                address=summary.address,
                caller_names=tuple(callers),
            ))
    return violations
