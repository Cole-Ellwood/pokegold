"""Register-change tracer with configurable subscriptions.

Records per-instruction register deltas for subscribed registers.
Defaults to tracking all registers; can be narrowed to specific ones.

Usage:
    rt = RegisterTracer(track={"A", "HL", "SP"})
    rt.on_instruction(cycle=100, pc=0x4000, bank=0, regs=snapshot)
    deltas = rt.deltas
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .pc_tracer import RegisterSnapshot


ALL_REGS = frozenset({"A", "F", "B", "C", "D", "E", "HL", "SP"})


@dataclass(frozen=True)
class RegisterDelta:
    """A change in one or more registers between two instructions."""
    cycle: int
    pc: int
    bank: int
    changes: dict[str, tuple[int, int]]  # reg -> (old, new)

    @property
    def changed_regs(self) -> set[str]:
        return set(self.changes.keys())

    def to_event(self) -> dict[str, Any]:
        return {
            "name": "register_change",
            "start_cycle": self.cycle,
            "end_cycle": self.cycle,
            "attributes": {
                "pc": self.pc,
                "bank": self.bank,
                "changes": {
                    reg: {"old": old, "new": new}
                    for reg, (old, new) in self.changes.items()
                },
            },
        }


class RegisterTracer:
    """Track register changes per instruction."""

    def __init__(self, track: set[str] | None = None) -> None:
        self._track = track or ALL_REGS
        self._prev: RegisterSnapshot | None = None
        self._deltas: list[RegisterDelta] = []

    def on_instruction(
        self, cycle: int, pc: int, bank: int, regs: RegisterSnapshot,
    ) -> RegisterDelta | None:
        if self._prev is None:
            self._prev = regs
            return None

        changes: dict[str, tuple[int, int]] = {}
        prev = self._prev
        for reg in self._track:
            old = getattr(prev, reg)
            new = getattr(regs, reg)
            if old != new:
                changes[reg] = (old, new)

        self._prev = regs

        if not changes:
            return None

        delta = RegisterDelta(cycle=cycle, pc=pc, bank=bank, changes=changes)
        self._deltas.append(delta)
        return delta

    @property
    def deltas(self) -> list[RegisterDelta]:
        return list(self._deltas)

    def deltas_for_reg(self, reg: str) -> list[RegisterDelta]:
        return [d for d in self._deltas if reg in d.changes]

    def clear(self) -> None:
        self._deltas.clear()
        self._prev = None

    def to_events(self) -> list[dict[str, Any]]:
        return [d.to_event() for d in self._deltas]
