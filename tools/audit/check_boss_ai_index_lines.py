#!/usr/bin/env python3
"""Audit that the Boss AI logic index matches generated source citations."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "docs" / "agent_navigation" / "subsystems" / "boss_ai_logic.md"
GENERATOR = ROOT / "scripts" / "generate_boss_ai_index.py"


def main() -> int:
    if not INDEX.exists():
        print(f"FAIL: missing index file: {INDEX.relative_to(ROOT)}")
        return 1
    if not GENERATOR.exists():
        print(f"FAIL: missing generator: {GENERATOR.relative_to(ROOT)}")
        return 1

    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--stdout"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        return result.returncode

    current = INDEX.read_text(encoding="utf-8")
    if current != result.stdout:
        print(f"FAIL: {INDEX.relative_to(ROOT).as_posix()} is stale")
        print("Run: python scripts/generate_boss_ai_index.py")
        return 1

    print(
        "PASS: docs/agent_navigation/subsystems/boss_ai_logic.md "
        "matches scripts/generate_boss_ai_index.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
