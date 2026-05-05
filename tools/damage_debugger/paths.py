"""Locate ROMs and sym files across project root + git worktrees.

In a worktree, build artifacts (ROM, .sym) live at the parent project
root, not in the worktree itself. We search a chain of plausible roots.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def candidate_roots(start: Path) -> Iterable[Path]:
    yield start
    cur = start
    for _ in range(6):
        cur = cur.parent
        yield cur
        if (cur / ".git").exists() or (cur / "Makefile").exists():
            yield cur


def find_artifact(name: str, start: Path | None = None) -> Path:
    """Search for a build artifact by name. Raises FileNotFoundError if missing."""
    if start is None:
        start = Path(__file__).resolve().parents[2]
    seen: set[Path] = set()
    for root in candidate_roots(start):
        if root in seen:
            continue
        seen.add(root)
        candidate = root / name
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        f"Could not find {name!r} in any ancestor of {start} (searched {len(seen)} roots)"
    )


def find_rom(variant: str = "pokegold_debug") -> Path:
    return find_artifact(f"{variant}.gbc")


def find_sym(variant: str = "pokegold_debug") -> Path:
    return find_artifact(f"{variant}.sym")
