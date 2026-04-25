#!/usr/bin/env python3
"""Cross-platform best-effort file removal for Makefile cleanup targets."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def main() -> int:
    for arg in sys.argv[1:]:
        remove_path(Path(arg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
