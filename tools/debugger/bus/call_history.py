"""Call history database.

Sequence of (cycle, caller_bank, caller_pc, callee_bank, callee_pc,
is_far, label). Queries: "who called BattleCommand_DamageCalc between
cycles X and Y?" in O(log n) via bisect.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass


@dataclass(frozen=True)
class CallRecord:
    """One function call event."""
    cycle: int
    caller_bank: int
    caller_pc: int
    callee_bank: int
    callee_pc: int
    is_far: bool
    label: str = ""
    return_cycle: int = -1


class CallHistory:
    """Temporal call-sequence store."""

    def __init__(self) -> None:
        self._calls: list[tuple[int, CallRecord]] = []  # sorted by cycle
        self._by_label: dict[str, list[int]] = {}  # label -> list of indices

    def record(self, call: CallRecord) -> None:
        idx = len(self._calls)
        self._calls.append((call.cycle, call))
        if call.label:
            self._by_label.setdefault(call.label, []).append(idx)

    def record_call(
        self, cycle: int, caller_bank: int, caller_pc: int,
        callee_bank: int, callee_pc: int, is_far: bool, label: str = "",
    ) -> CallRecord:
        c = CallRecord(
            cycle=cycle, caller_bank=caller_bank, caller_pc=caller_pc,
            callee_bank=callee_bank, callee_pc=callee_pc,
            is_far=is_far, label=label,
        )
        self.record(c)
        return c

    @property
    def total_calls(self) -> int:
        return len(self._calls)

    def calls_in_range(self, cycle_lo: int, cycle_hi: int) -> list[CallRecord]:
        lo = bisect.bisect_left(self._calls, (cycle_lo,))
        hi = bisect.bisect_right(self._calls, (cycle_hi + 1,))
        return [c for _, c in self._calls[lo:hi]]

    def calls_to_label(self, label: str) -> list[CallRecord]:
        indices = self._by_label.get(label, [])
        return [self._calls[i][1] for i in indices]

    def calls_to_pc(self, bank: int, pc: int) -> list[CallRecord]:
        return [c for _, c in self._calls
                if c.callee_bank == bank and c.callee_pc == pc]

    def far_calls(self) -> list[CallRecord]:
        return [c for _, c in self._calls if c.is_far]

    def last_call_to(self, label: str, before_cycle: int | None = None) -> CallRecord | None:
        indices = self._by_label.get(label, [])
        if not indices:
            return None
        if before_cycle is None:
            return self._calls[indices[-1]][1]
        for idx in reversed(indices):
            if self._calls[idx][0] <= before_cycle:
                return self._calls[idx][1]
        return None

    def all_labels(self) -> set[str]:
        return set(self._by_label.keys())

    def clear(self) -> None:
        self._calls.clear()
        self._by_label.clear()
