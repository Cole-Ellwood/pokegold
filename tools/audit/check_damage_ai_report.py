#!/usr/bin/env python3
"""Audit wrapper for the unified damage plus Boss AI report."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.boss_ai_debugger", "damage-ai-report", "--self-test"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
    if proc.returncode != 0:
        print("FAIL: damage-ai-report self-test failed")
        return 1
    print("PASS: damage-ai-report audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
