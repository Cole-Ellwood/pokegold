#!/usr/bin/env python3
"""One-line wrapper to arm the Pokemon Mastery Compounding Loop /pgoal.

Reads the checked-in spec files from tools/pokemon_mastery/pgoal_spec/
and shells out to ~/.claude/skills/pgoal/scripts/pgoal.py set with the
full marathon-profile configuration. Idempotent: re-running on an
already-armed slot reuses the current state.

Usage (Claude Code session — the /pgoal harness must be installed):

  python tools/pokemon_mastery/arm_pgoal.py

That's it. Run from the repo root.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE / "pgoal_spec"
PGOAL_SCRIPT = Path(os.path.expanduser("~/.claude/skills/pgoal/scripts/pgoal.py"))


def read(name: str) -> str:
    return (SPEC / name).read_text(encoding="utf-8")


def already_armed() -> bool:
    """Return True if this worktree's pgoal slot already has an active
    mastery loop goal. Re-arming would reset the harness iteration
    counter — usually not what the user wants."""
    try:
        result = subprocess.run(
            [sys.executable, str(PGOAL_SCRIPT), "status"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.SubprocessError:
        return False
    text = (result.stdout or "") + (result.stderr or "")
    return "Compounding Loop" in text and "active" in text.lower()


def main() -> int:
    if not PGOAL_SCRIPT.exists():
        print(
            f"FAIL: /pgoal harness not found at {PGOAL_SCRIPT}.\n"
            "This wrapper is for Claude Code sessions where the /pgoal "
            "skill is installed. Codex sessions invoke the loop directly "
            "via loop_runner.py.",
            file=sys.stderr,
        )
        return 1
    if "--force" not in sys.argv and already_armed():
        print(
            "Compounding Loop pgoal is already active in this worktree slot. "
            "Re-arming would reset the harness iteration counter. "
            "Pass --force to re-arm anyway, or use `pgoal.py status` to "
            "inspect the current state."
        )
        return 0
    for f in ("objective.txt", "criteria.txt", "constraints.txt", "verify.txt"):
        if not (SPEC / f).exists():
            print(f"FAIL: missing {SPEC / f}", file=sys.stderr)
            return 1
    cmd = [
        sys.executable,
        str(PGOAL_SCRIPT),
        "set",
        "--objective",
        read("objective.txt"),
        "--phase",
        "implementation",
        "--criteria",
        read("criteria.txt"),
        "--constraints",
        read("constraints.txt"),
        "--verify",
        read("verify.txt"),
        "--long-run",
        "--continuation-style",
        "adaptive",
        "--full-prompt-every-iterations",
        "25",
        "--assume-defaults",
    ]
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
