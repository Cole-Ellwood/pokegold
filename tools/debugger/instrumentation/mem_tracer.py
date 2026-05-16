"""Memory access tracer with configurable subscriptions.

Records per-byte read/write events for subscribed address ranges.
Subscribers register interest in specific address ranges or symbol
names; only matching events are recorded to keep overhead bounded.

Usage:
    mt = MemoryTracer()
    mt.subscribe(0xCB0C, 2, "wBattleMonHP")      # 2-byte field
    mt.subscribe(0xFF80, 1, "hROMBank")
    mt.on_write(cycle=1234, pc=0x4567, bank=0x0b, addr=0xCB0C, old=0x00, new=0x2A)
    events = mt.events
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MemoryEvent:
    """A single memory read or write."""
    cycle: int
    pc: int
    bank: int
    address: int
    old_byte: int
    new_byte: int
    is_write: bool
    symbol_name: str = ""

    @property
    def changed(self) -> bool:
        return self.old_byte != self.new_byte

    def to_event(self) -> dict[str, Any]:
        return {
            "name": "memory_write" if self.is_write else "memory_read",
            "start_cycle": self.cycle,
            "end_cycle": self.cycle,
            "attributes": {
                "pc": self.pc,
                "bank": self.bank,
                "address": self.address,
                "old_byte": self.old_byte,
                "new_byte": self.new_byte,
                "symbol": self.symbol_name,
            },
        }


@dataclass
class MemorySubscription:
    """A range of addresses to monitor."""
    start: int
    length: int
    label: str = ""

    @property
    def end(self) -> int:
        return self.start + self.length - 1

    def contains(self, addr: int) -> bool:
        return self.start <= addr <= self.end


class MemoryTracer:
    """Subscription-based memory event recorder."""

    def __init__(self) -> None:
        self._subscriptions: list[MemorySubscription] = []
        self._events: list[MemoryEvent] = []
        self._fast_lookup: dict[int, str] = {}

    def subscribe(self, start: int, length: int = 1, label: str = "") -> None:
        sub = MemorySubscription(start=start, length=length, label=label)
        self._subscriptions.append(sub)
        for addr in range(start, start + length):
            self._fast_lookup[addr] = label

    def subscribe_symbol(self, svc, name: str, length: int = 1) -> bool:
        sym = svc.resolve(name)
        if sym is None:
            return False
        self.subscribe(sym.address, length, name)
        return True

    def is_subscribed(self, addr: int) -> bool:
        return addr in self._fast_lookup

    def on_write(
        self, cycle: int, pc: int, bank: int,
        addr: int, old: int, new: int,
    ) -> MemoryEvent | None:
        label = self._fast_lookup.get(addr)
        if label is None:
            return None
        ev = MemoryEvent(
            cycle=cycle, pc=pc, bank=bank,
            address=addr, old_byte=old, new_byte=new,
            is_write=True, symbol_name=label,
        )
        self._events.append(ev)
        return ev

    def on_read(
        self, cycle: int, pc: int, bank: int,
        addr: int, value: int,
    ) -> MemoryEvent | None:
        label = self._fast_lookup.get(addr)
        if label is None:
            return None
        ev = MemoryEvent(
            cycle=cycle, pc=pc, bank=bank,
            address=addr, old_byte=value, new_byte=value,
            is_write=False, symbol_name=label,
        )
        self._events.append(ev)
        return ev

    @property
    def events(self) -> list[MemoryEvent]:
        return list(self._events)

    @property
    def write_events(self) -> list[MemoryEvent]:
        return [e for e in self._events if e.is_write]

    @property
    def changed_events(self) -> list[MemoryEvent]:
        return [e for e in self._events if e.is_write and e.changed]

    def events_for_address(self, addr: int) -> list[MemoryEvent]:
        return [e for e in self._events if e.address == addr]

    def last_write_to(self, addr: int) -> MemoryEvent | None:
        for e in reversed(self._events):
            if e.address == addr and e.is_write:
                return e
        return None

    def clear(self) -> None:
        self._events.clear()

    def to_events(self) -> list[dict[str, Any]]:
        return [e.to_event() for e in self._events]
