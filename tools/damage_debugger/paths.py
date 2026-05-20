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
        f"Could not find {name!r} in any ancestor of {start} (searched {len(seen)} roots). "
        "Build matching debug artifacts in this worktree before running ROM-backed "
        "damage checks. Usual Windows/WSL command: "
        "bash -lc 'cd \"<repo-wsl-path>\" && make -j4 PYTHON=python3 "
        "RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe "
        "RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe "
        "pokegold_debug.gbc'. If this is an external git worktree, build in that "
        "worktree; using another checkout's ROM can hide source/ROM mismatches."
    )


def find_rom(variant: str = "pokegold_debug") -> Path:
    return find_artifact(f"{variant}.gbc")


def find_sym(variant: str = "pokegold_debug") -> Path:
    return find_artifact(f"{variant}.sym")
