"""Per-address byte-write history for omniscient queries.

Stores (cycle, pc, bank, addr, old_byte, new_byte) for every CPU-driven
write to subscribed addresses. Backed by a dict-of-lists in memory (fast,
fits ROM-hack scale). Queries: "when did wCurDamage last change?" in O(log n)
via bisect.

DMA/OAM writes get tagged pc=None, source="OAM_DMA".
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ByteWrite:
    """One byte-level write event."""
    cycle: int
    pc: int       # -1 for DMA writes
    bank: int
    address: int
    old_byte: int
    new_byte: int
    source: str = ""  # e.g. "OAM_DMA", or empty for CPU

    @property
    def changed(self) -> bool:
        return self.old_byte != self.new_byte


class ByteHistory:
    """Per-address write history with fast temporal queries.

    Internal: dict[address] -> sorted list of (cycle, ByteWrite).
    Queries use bisect for O(log n) lookups.
    """

    def __init__(self) -> None:
        self._writes: dict[int, list[tuple[int, ByteWrite]]] = {}
        self._total = 0

    def record(self, write: ByteWrite) -> None:
        addr = write.address
        if addr not in self._writes:
            self._writes[addr] = []
        self._writes[addr].append((write.cycle, write))
        self._total += 1

    def record_write(
        self, cycle: int, pc: int, bank: int,
        addr: int, old: int, new: int, source: str = "",
    ) -> ByteWrite:
        w = ByteWrite(cycle=cycle, pc=pc, bank=bank, address=addr,
                       old_byte=old, new_byte=new, source=source)
        self.record(w)
        return w

    @property
    def total_writes(self) -> int:
        return self._total

    @property
    def tracked_addresses(self) -> int:
        return len(self._writes)

    def writes_to(self, addr: int) -> list[ByteWrite]:
        entries = self._writes.get(addr, [])
        return [w for _, w in entries]

    def writes_to_in_range(self, addr: int, cycle_lo: int, cycle_hi: int) -> list[ByteWrite]:
        entries = self._writes.get(addr, [])
        if not entries:
            return []
        lo = bisect.bisect_left(entries, (cycle_lo,))
        hi = bisect.bisect_right(entries, (cycle_hi + 1,))
        return [w for _, w in entries[lo:hi]]

    def last_write_to(self, addr: int, before_cycle: int | None = None) -> ByteWrite | None:
        entries = self._writes.get(addr, [])
        if not entries:
            return None
        if before_cycle is None:
            return entries[-1][1]
        idx = bisect.bisect_right(entries, (before_cycle,)) - 1
        if idx < 0:
            return None
        return entries[idx][1]

    def first_write_to(self, addr: int, after_cycle: int = 0) -> ByteWrite | None:
        entries = self._writes.get(addr, [])
        if not entries:
            return None
        idx = bisect.bisect_left(entries, (after_cycle,))
        if idx >= len(entries):
            return None
        return entries[idx][1]

    def value_at(self, addr: int, cycle: int, initial: int = 0) -> int:
        w = self.last_write_to(addr, before_cycle=cycle)
        if w is None:
            return initial
        return w.new_byte

    def changes_in(self, addr: int) -> list[ByteWrite]:
        return [w for w in self.writes_to(addr) if w.changed]

    def all_writes_sorted(self) -> list[ByteWrite]:
        all_entries: list[tuple[int, ByteWrite]] = []
        for entries in self._writes.values():
            all_entries.extend(entries)
        all_entries.sort(key=lambda e: e[0])
        return [w for _, w in all_entries]

    def clear(self) -> None:
        self._writes.clear()
        self._total = 0
