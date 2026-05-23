#!/usr/bin/env python3
"""Audit Haki coverage tool.

Runs `python -m tools.boss_ai_debugger haki-coverage --self-test` and confirms
exit 0 + the Cole-approved 2026-05-23 gate rule maps cleanly onto
data/trainers/ai_tiers.asm's BossAITierMap.

Checks:
  - All 16 included trainer classes (Johto post-Whitney + Silver + Rocket
    executives + E4 + Champion + Blue + Red) have at least one tier-MID
    or tier-LATE row in BossAITierMap.
  - All 7 excluded trainer classes (Kanto gyms minus Blue) are still in
    the map (so the gate sees them and rejects).
"""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "tools.boss_ai_debugger", "haki-coverage", "--self-test"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("FAIL: haki-coverage --self-test exit", result.returncode)
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        return 1
    out = result.stdout
    if "MISSING_ELIGIBLE:" in out:
        print("FAIL: haki-coverage reports missing eligible classes")
        print(out)
        return 1
    if "MISSING_EXCLUDED:" in out:
        print("FAIL: haki-coverage reports missing excluded classes (would cause gate to silently pass them through)")
        print(out)
        return 1
    print("PASS: Haki gate-rule classes all present in BossAITierMap "
          "(16 included with tier MID+, 7 excluded recognized).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
