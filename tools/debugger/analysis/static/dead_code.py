"""Dead-code and unreferenced-label scanner.

Scans .sym exports against .asm source references to find labels
that are defined (exported with `::`) but never referenced from any
other file.  Also identifies functions with no callers in the call
graph built from `call`, `jp`, `jr`, `farcall`, `callfar` operands.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...kernel.symbol_service import SymbolService


CALL_PATTERN = re.compile(
    r"""(?:call|jp|jr|farcall|callfar|homecall)\s+"""
    r"""(?:(?:nz|z|nc|c),\s*)?"""
    r"""(\w+)""",
    re.IGNORECASE,
)

LABEL_DEF_PATTERN = re.compile(r"^(\w+)::?\s*$", re.MULTILINE)
INCLUDE_PATTERN = re.compile(r'INCLUDE\s+"([^"]+)"', re.IGNORECASE)


@dataclass
class DeadCodeEntry:
    label: str
    source_file: str
    line: int = 0
    bank: int = 0
    address: int = 0
    kind: str = "unreferenced"

    def __str__(self) -> str:
        loc = f"{self.source_file}:{self.line}" if self.line else self.source_file
        return f"[{self.kind}] {self.label} at {loc} (${self.bank:02X}:${self.address:04X})"


@dataclass
class DeadCodeReport:
    entries: list[DeadCodeEntry] = field(default_factory=list)
    total_labels: int = 0
    referenced_labels: int = 0
    scan_errors: list[str] = field(default_factory=list)

    @property
    def unreferenced_count(self) -> int:
        return len(self.entries)

    @property
    def ok(self) -> bool:
        return len(self.entries) == 0

    def summary(self, max_entries: int = 50) -> str:
        lines = [
            f"Dead code scan: {self.total_labels} labels, "
            f"{self.referenced_labels} referenced, "
            f"{self.unreferenced_count} unreferenced",
        ]
        if self.scan_errors:
            lines.append(f"Scan errors: {len(self.scan_errors)}")

        shown = self.entries[:max_entries]
        for entry in shown:
            lines.append(f"  {entry}")
        if len(self.entries) > max_entries:
            lines.append(f"  ... and {len(self.entries) - max_entries} more")

        return "\n".join(lines)


KNOWN_ENTRY_POINTS = frozenset({
    "Main", "Start", "Reset", "VBlank", "LCDStat", "Timer", "Serial", "Joypad",
    "Header", "HeaderEnd",
})

KNOWN_PREFIXES_SKIP = (
    ".", "_", "SECTION", "INCLUDE",
)


def scan_dead_code(
    project_root: Path,
    symbol_service: SymbolService | None = None,
    *,
    source_dirs: list[str] | None = None,
    skip_local: bool = True,
) -> DeadCodeReport:
    """Scan for unreferenced exported labels."""
    report = DeadCodeReport()
    root = project_root

    dirs = source_dirs or ["engine", "home", "data", "maps"]
    asm_files: list[Path] = []
    for d in dirs:
        dir_path = root / d
        if dir_path.is_dir():
            asm_files.extend(dir_path.rglob("*.asm"))

    all_defined: dict[str, tuple[str, int]] = {}
    all_referenced: set[str] = set()

    for asm_file in asm_files:
        try:
            text = asm_file.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            report.scan_errors.append(f"Read error: {asm_file}: {e}")
            continue

        rel_path = str(asm_file.relative_to(root))

        for line_num, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()

            label_match = re.match(r"^(\w+)(::?)\s*", stripped)
            if label_match:
                label = label_match.group(1)
                is_exported = label_match.group(2) == "::"
                if skip_local and not is_exported:
                    continue
                if label not in all_defined:
                    all_defined[label] = (rel_path, line_num)

            for match in CALL_PATTERN.finditer(stripped):
                all_referenced.add(match.group(1))

            inc_match = INCLUDE_PATTERN.search(stripped)
            if inc_match:
                all_referenced.add(inc_match.group(1))

            for word in re.findall(r"\b(\w+)\b", stripped):
                if word in all_defined and word != label_match.group(1) if label_match else True:
                    all_referenced.add(word)

    for asm_file in asm_files:
        try:
            text = asm_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for word in re.findall(r"\b(\w+)\b", text):
            all_referenced.add(word)

    report.total_labels = len(all_defined)
    report.referenced_labels = len(all_referenced & set(all_defined.keys()))

    for label, (src_file, line_num) in sorted(all_defined.items()):
        if label in all_referenced:
            continue
        if label in KNOWN_ENTRY_POINTS:
            continue
        if any(label.startswith(p) for p in KNOWN_PREFIXES_SKIP):
            continue

        bank = 0
        address = 0
        if symbol_service:
            sym = symbol_service.resolve(label)
            if sym:
                bank = sym.bank
                address = sym.address

        report.entries.append(DeadCodeEntry(
            label=label,
            source_file=src_file,
            line=line_num,
            bank=bank,
            address=address,
        ))

    return report


__all__ = ["DeadCodeEntry", "DeadCodeReport", "scan_dead_code"]
