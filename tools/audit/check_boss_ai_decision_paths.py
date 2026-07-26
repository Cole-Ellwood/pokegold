#!/usr/bin/env python3
"""Release-smoke wrapper for the boss-AI decision-path fixtures.

Fixtures live in tools/boss_ai_fixtures/cases.py; the harness that drives them on
the real ROM is tools/boss_ai_fixtures/harness.py. Run them directly with:

    python -m tools.boss_ai_fixtures            # all
    python -m tools.boss_ai_fixtures --list     # what is pinned, no ROM needed
    python -m tools.boss_ai_fixtures --verbose  # show observed state per fixture
    python -m tools.boss_ai_fixtures --only haki

This replaces the standalone check_haki_move_choice.py: its cases were folded into
the fixture table so there is one harness rather than a script per bug.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main() -> int:
    try:
        from tools.boss_ai_fixtures.runner import Skip, report, run_all
    except Exception as exc:  # pragma: no cover - environment guard
        print(f"SKIP: boss-AI decision-path fixtures (import failed: {exc})")
        return 0
    try:
        results, _ = run_all()
    except Skip as exc:
        print(f"SKIP: boss-AI decision-path fixtures ({exc})")
        return 0
    return report(results)


if __name__ == "__main__":
    raise SystemExit(main())
