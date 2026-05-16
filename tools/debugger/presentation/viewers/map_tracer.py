"""Map script tracer and event flag explorer.

Traces overworld map script execution and decodes named event flags
for state comparison.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ...kernel.symbol_service import SymbolService


@dataclass
class EventFlag:
    """One named event flag."""
    name: str
    byte_offset: int
    bit: int
    value: bool = False
    description: str = ""

    @property
    def flag_id(self) -> int:
        return self.byte_offset * 8 + self.bit

    def __str__(self) -> str:
        state = "SET" if self.value else "CLR"
        return f"[{state}] {self.name} (flag {self.flag_id}: byte ${self.byte_offset:02X} bit {self.bit})"


@dataclass
class MapScriptEvent:
    """One traced map script command."""
    pc: int
    bank: int
    command: str
    args: list[Any] = field(default_factory=list)
    label: str = ""
    source_file: str = ""
    source_line: int = 0

    def __str__(self) -> str:
        loc = self.label or f"${self.bank:02X}:${self.pc:04X}"
        arg_str = " ".join(str(a) for a in self.args)
        return f"{loc}: {self.command} {arg_str}"


@dataclass
class MapScriptTrace:
    """Trace of map script execution."""
    map_name: str = ""
    events: list[MapScriptEvent] = field(default_factory=list)

    def summary(self) -> str:
        return f"Map '{self.map_name}': {len(self.events)} script events"

    def render_text(self) -> str:
        lines = [self.summary(), ""]
        for e in self.events:
            lines.append(f"  {e}")
        return "\n".join(lines)


def load_event_flags(project_root: Path) -> list[EventFlag]:
    """Load named event flags from constants/event_flags.asm."""
    flags_file = project_root / "constants" / "event_flags.asm"
    flags: list[EventFlag] = []

    if not flags_file.exists():
        return flags

    text = flags_file.read_text(encoding="utf-8", errors="replace")
    flag_id = 0

    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r"const\s+(\w+)", stripped, re.IGNORECASE)
        if match:
            name = match.group(1)
            byte_offset = flag_id // 8
            bit = flag_id % 8
            flags.append(EventFlag(
                name=name,
                byte_offset=byte_offset,
                bit=bit,
            ))
            flag_id += 1

    return flags


def read_event_flags(
    flags: list[EventFlag],
    wram: bytes,
    flags_base_addr: int = 0xDA72,
    wram_base: int = 0xC000,
) -> list[EventFlag]:
    """Read event flag values from WRAM."""
    result: list[EventFlag] = []
    for f in flags:
        addr = flags_base_addr + f.byte_offset
        offset = addr - wram_base
        if 0 <= offset < len(wram):
            byte_val = wram[offset]
            f.value = bool(byte_val & (1 << f.bit))
        result.append(f)
    return result


def diff_event_flags(
    before: list[EventFlag],
    after: list[EventFlag],
) -> list[tuple[EventFlag, EventFlag]]:
    """Find event flags that changed between two states."""
    changed = []
    by_name = {f.name: f for f in before}
    for f in after:
        prev = by_name.get(f.name)
        if prev and prev.value != f.value:
            changed.append((prev, f))
    return changed


__all__ = [
    "EventFlag",
    "MapScriptEvent",
    "MapScriptTrace",
    "load_event_flags",
    "read_event_flags",
    "diff_event_flags",
]
