#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.__main__ import main as boss_ai_debugger_main


def main(argv: list[str] | None = None) -> int:
    return boss_ai_debugger_main(["regress", *(argv or [])])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
