#!/usr/bin/env python3
"""Concatenate input files in order to a single output. Cross-platform
replacement for `cat $^ > $@` in the Makefile.

Usage: concat_files.py OUT SRC1 [SRC2 ...]

Used by the intro fire-tile assembly: each output frame is a head-tail
concat of static charizard / blastoise / venusaur 2bpp tiles.
"""
from __future__ import annotations

import sys


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        sys.stderr.write(f"usage: {argv[0]} OUT SRC1 [SRC2 ...]\n")
        return 2
    out_path = argv[1]
    with open(out_path, "wb") as out:
        for src in argv[2:]:
            with open(src, "rb") as f:
                out.write(f.read())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
