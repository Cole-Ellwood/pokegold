#!/usr/bin/env python3
"""Legacy CLI name: verify exhaustive lookahead against independent ROM calls.

The mixed raw/evaluated-score futility bound was unsound for signed deltas and
left late hedge candidates unevaluated. All four selectable slots now receive
the same evaluation. This checks behavior rather than requiring the old pruning
implementation to remain present. Requires a freshly built Gold ROM and PyBoy.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.boss_ai_fixtures.runner import Skip, report, run_all


def main() -> int:
    try:
        results, _ = run_all(only="strategy/exhaustive-lookahead")
    except Skip as exc:
        print(f"FAIL: exhaustive lookahead was not verified: {exc}")
        return 1
    return report(results)


if __name__ == "__main__":
    raise SystemExit(main())
