#!/usr/bin/env python3
"""check_fast_contact_flags.py

The offline AI reference's moves mirror folds each move's contact flag into
bit 7 of its type byte from `engine/battle/ai/fast_contact_flags.inc`, a file
generated from `data/moves/contact_flags.asm` by
`scripts/generate_fast_contact_flags.py`. This audit regenerates the include
in memory and fails when the committed file has drifted from the table, so a
contact flag edited in the data file cannot silently leave the reference
compiler reading the old value.

Exit 0 = in sync. Exit 1 = drift (run the generator).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_fast_contact_flags.py"), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
