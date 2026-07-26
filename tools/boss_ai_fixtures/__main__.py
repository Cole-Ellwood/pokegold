"""CLI: python -m tools.boss_ai_fixtures [--only X] [--verbose] [--list]"""
from __future__ import annotations

import argparse
import sys

from tools.boss_ai_fixtures.cases import CASES, by_path
from tools.boss_ai_fixtures.runner import Skip, report, run_all


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.boss_ai_fixtures")
    ap.add_argument("--only", help="substring filter on fixture id or path")
    ap.add_argument("--rom", default="pokegold")
    ap.add_argument("--verbose", action="store_true",
                    help="show what each fixture pins and the observed state")
    ap.add_argument("--list", action="store_true",
                    help="list fixtures without running the ROM")
    args = ap.parse_args(argv)

    if args.list:
        for path, cases in sorted(by_path().items()):
            print(f"\n{path}")
            for c in cases:
                print(f"  {c.id}")
                print(f"      {c.pins}")
        print(f"\n{len(CASES)} fixtures across {len(by_path())} decision paths")
        return 0

    try:
        results, _ = run_all(args.rom, only=args.only, verbose=args.verbose)
    except Skip as exc:
        print(f"SKIP: boss-AI decision-path fixtures ({exc})")
        return 0
    return report(results, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
