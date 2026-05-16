"""Whole-program stack-depth bounds analysis.

Builds a reachable call graph from entry points (Main + interrupt handlers),
computes per-function local stack usage, and runs worst-path analysis to
flag any path that could overflow the stack region.

Interrupts add a frame on every cycle, so worst-path adds their depth
to every non-interrupt path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .clobber_inference import RegisterSummary


SM83_STACK_BASE = 0xDFFF
SM83_STACK_LIMIT = 0xDF00
SM83_STACK_SIZE = SM83_STACK_BASE - SM83_STACK_LIMIT


@dataclass(frozen=True)
class StackPathEntry:
    """One function in a call chain."""
    name: str
    local_depth: int
    cumulative_depth: int


@dataclass
class StackDepthResult:
    """Result of stack depth analysis for one entry point."""
    entry: str
    worst_path: list[StackPathEntry] = field(default_factory=list)
    worst_depth: int = 0
    stack_limit: int = SM83_STACK_SIZE
    overflows: bool = False

    def summary(self) -> str:
        status = "OVERFLOW" if self.overflows else "OK"
        lines = [
            f"Stack depth from {self.entry}: "
            f"{self.worst_depth} bytes (limit {self.stack_limit}) [{status}]"
        ]
        if self.worst_path:
            lines.append("  Worst path:")
            for entry in self.worst_path:
                lines.append(
                    f"    {entry.name}: "
                    f"+{entry.local_depth} = {entry.cumulative_depth} total"
                )
        return "\n".join(lines)


@dataclass
class StackDepthReport:
    """Full stack depth report across all entry points."""
    results: list[StackDepthResult] = field(default_factory=list)
    interrupt_overhead: int = 0

    @property
    def ok(self) -> bool:
        return not any(r.overflows for r in self.results)

    def summary(self) -> str:
        lines = ["Stack depth analysis:"]
        if self.interrupt_overhead > 0:
            lines.append(f"  Interrupt worst-case overhead: {self.interrupt_overhead} bytes")
        for r in self.results:
            status = "OVERFLOW" if r.overflows else "ok"
            lines.append(f"  {r.entry}: {r.worst_depth} bytes [{status}]")
        return "\n".join(lines)


def compute_stack_depth(
    summaries: dict[str, RegisterSummary],
    entry: str,
    interrupt_entries: list[str] | None = None,
    visited: set[str] | None = None,
) -> StackDepthResult:
    """Compute worst-case stack depth from an entry point.

    Uses the per-function stack_depth from RegisterSummary (counts push,
    call, rst, dec sp). Walks the call graph via DFS, tracking cumulative
    depth. Cycles are broken by the visited set.
    """
    if visited is None:
        visited = set()

    result = StackDepthResult(entry=entry)
    _dfs_stack_depth(summaries, entry, 0, [], result, visited)

    if interrupt_entries:
        interrupt_depth = 0
        for ie in interrupt_entries:
            ir = StackDepthResult(entry=ie)
            _dfs_stack_depth(summaries, ie, 0, [], ir, set())
            interrupt_depth = max(interrupt_depth, ir.worst_depth)
        result.worst_depth += interrupt_depth + 2  # +2 for the interrupt push
        if result.worst_path:
            result.worst_path.append(StackPathEntry(
                name=f"<interrupt:{interrupt_entries[0]}>",
                local_depth=interrupt_depth + 2,
                cumulative_depth=result.worst_depth,
            ))

    result.overflows = result.worst_depth > result.stack_limit
    return result


def _dfs_stack_depth(
    summaries: dict[str, RegisterSummary],
    name: str,
    cumulative: int,
    path: list[StackPathEntry],
    result: StackDepthResult,
    visited: set[str],
) -> None:
    if name in visited:
        return
    visited.add(name)

    summary = summaries.get(name)
    local = summary.stack_depth if summary else 2  # default: one call frame

    new_cumulative = cumulative + local
    new_path = path + [StackPathEntry(
        name=name,
        local_depth=local,
        cumulative_depth=new_cumulative,
    )]

    if new_cumulative > result.worst_depth:
        result.worst_depth = new_cumulative
        result.worst_path = list(new_path)

    if summary and summary.calls:
        for callee in summary.calls:
            _dfs_stack_depth(summaries, callee, new_cumulative, new_path, result, visited)

    visited.discard(name)
