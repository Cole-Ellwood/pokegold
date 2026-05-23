#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.role_packages import (
    OUT_PATH,
    build_role_package_table,
    render_role_package_asm,
    write_role_package_asm,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Boss AI role-package table.")
    parser.add_argument("--check", action="store_true", help="fail if committed output is stale")
    args = parser.parse_args(argv)

    expected = render_role_package_asm(build_role_package_table())
    if args.check:
        actual = OUT_PATH.read_text(encoding="utf-8") if OUT_PATH.exists() else ""
        if actual != expected:
            print(f"FAIL: {OUT_PATH} is stale; run scripts/generate_boss_role_package_table.py", file=sys.stderr)
            return 1
        print("PASS: boss role-package table is current")
        return 0

    write_role_package_asm()
    print(f"wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
