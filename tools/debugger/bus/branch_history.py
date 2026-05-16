"""Branch history database.

Sequence of (cycle, PC, taken). Queries: "did this jr nz ever fall
through during the scenario?" in O(log n).
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass


@dataclass(frozen=True)
class BranchRecord:
    """One conditional branch event."""
    cycle: int
    bank: int
    pc: int
    taken: bool
    mnemonic: str = ""

    @property
    def fell_through(self) -> bool:
        return not self.taken


class BranchHistory:
    """Temporal branch-decision store."""

    def __init__(self) -> None:
        self._branches: list[tuple[int, BranchRecord]] = []
        self._by_pc: dict[tuple[int, int], list[int]] = {}

    def record(self, branch: BranchRecord) -> None:
        idx = len(self._branches)
        self._branches.append((branch.cycle, branch))
        key = (branch.bank, branch.pc)
        self._by_pc.setdefault(key, []).append(idx)

    def record_branch(
        self, cycle: int, bank: int, pc: int, taken: bool, mnemonic: str = "",
    ) -> BranchRecord:
        b = BranchRecord(cycle=cycle, bank=bank, pc=pc, taken=taken, mnemonic=mnemonic)
        self.record(b)
        return b

    @property
    def total_branches(self) -> int:
        return len(self._branches)

    def branches_at(self, bank: int, pc: int) -> list[BranchRecord]:
        indices = self._by_pc.get((bank, pc), [])
        return [self._branches[i][1] for i in indices]

    def branches_in_range(self, cycle_lo: int, cycle_hi: int) -> list[BranchRecord]:
        lo = bisect.bisect_left(self._branches, (cycle_lo,))
        hi = bisect.bisect_right(self._branches, (cycle_hi + 1,))
        return [b for _, b in self._branches[lo:hi]]

    def ever_taken(self, bank: int, pc: int) -> bool:
        return any(b.taken for b in self.branches_at(bank, pc))

    def ever_fell_through(self, bank: int, pc: int) -> bool:
        return any(not b.taken for b in self.branches_at(bank, pc))

    def taken_ratio(self, bank: int, pc: int) -> float | None:
        records = self.branches_at(bank, pc)
        if not records:
            return None
        return sum(1 for b in records if b.taken) / len(records)

    def unique_branch_pcs(self) -> set[tuple[int, int]]:
        return set(self._by_pc.keys())

    def coverage_summary(self) -> dict[str, int]:
        total = len(self._by_pc)
        both = sum(
            1 for key in self._by_pc
            if self.ever_taken(*key) and self.ever_fell_through(*key)
        )
        taken_only = sum(
            1 for key in self._by_pc
            if self.ever_taken(*key) and not self.ever_fell_through(*key)
        )
        fell_only = sum(
            1 for key in self._by_pc
            if not self.ever_taken(*key) and self.ever_fell_through(*key)
        )
        return {
            "total_branch_pcs": total,
            "both_paths_covered": both,
            "taken_only": taken_only,
            "fell_through_only": fell_only,
        }

    def clear(self) -> None:
        self._branches.clear()
        self._by_pc.clear()
