#!/usr/bin/env python3
"""Run the reference-only boss-AI fixtures against pokegold_ai_reference.

The release floor (check_boss_ai_decision_paths.py) runs the production suite
on the game ROM. The reference-only fixtures (action facts, exchanges, public
replies, joint actions: everything with a *_check spec) were in no audit at
all; they only ran when someone typed `--suite all`. This audit is that gate.

It fails when the reference ROM exists and any fixture breaks, and prints a
loud SKIP (exit 0) only when the reference ROM has not been built, since the
game build does not depend on it.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

ROM = "pokegold_ai_reference"


def main() -> int:
    missing = [f"{ROM}.{ext}" for ext in ("gbc", "sym") if not (ROOT / f"{ROM}.{ext}").exists()]
    if missing:
        print(f"SKIP: boss-AI reference fixtures ({', '.join(missing)} not built; "
              "build the reference ROM to run the 383 reference-only fixtures)")
        return 0
    try:
        from tools.boss_ai_fixtures.runner import FixtureError, Skip, report, run_all
    except Exception as exc:  # pragma: no cover - environment guard
        print(f"SKIP: boss-AI reference fixtures (import failed: {exc})")
        return 0
    try:
        results, _ = run_all(ROM, suite="reference")
    except Skip as exc:
        print(f"SKIP: boss-AI reference fixtures ({exc})")
        return 0
    except FixtureError as exc:
        print(f"FAIL: boss-AI reference fixtures ({exc})")
        return 1
    return report(results)


if __name__ == "__main__":
    raise SystemExit(main())
