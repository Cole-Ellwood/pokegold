#!/usr/bin/env python3
"""Audit wrapper for the Boss AI move-score probe."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from _trace_artifacts import require_manifest_basis


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    require_manifest_basis()
    proc = subprocess.run(
        [sys.executable, "-m", "tools.boss_ai_debugger", "move-score-probe", "--self-test"],
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
        print("FAIL: move-score-probe self-test failed")
        return 1
    print("PASS: move-score-probe audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
