#!/usr/bin/env python3
"""Copy a single file. Cross-platform replacement for `cp -f` in the Makefile.

Usage: copy_file.py SRC DST

The build runs through WSL bash so plain `cp -f` works today, but the
Python form is portable across native Windows, macOS, and Linux make
invocations and clearer about what is happening (single-file copy, not
mass copy or directory copy).
"""
from __future__ import annotations

import shutil
import sys


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        sys.stderr.write(f"usage: {argv[0]} SRC DST\n")
        return 2
    shutil.copyfile(argv[1], argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
