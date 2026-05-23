#!/usr/bin/env python3
"""Audit P0.5c haki-coverage tool.

Runs `python -m tools.boss_ai_debugger haki-coverage --self-test` and confirms
exit 0 + all 19 expected leaders parsed from docs/boss_ai_spec.md per the
P0.5c acceptance criterion in the boss-AI ROM-expansion roadmap.
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
    if "MISSING:" in out:
        print("FAIL: haki-coverage reports missing leaders")
        print(out)
        return 1
    if "EXTRA:" in out:
        print("FAIL: haki-coverage reports extra leaders not in expected list")
        print(out)
        return 1
    # Expect the 19-of-19 line. Be lenient on whitespace.
    if "leaders: 19" not in out:
        print("FAIL: haki-coverage did not report exactly 19 leaders")
        print(out)
        return 1
    print("PASS: haki-coverage --self-test reports 19/19 expected Haki leaders.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
