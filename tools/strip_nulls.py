#!/usr/bin/env python3
"""Strip 0x00 bytes from a binary file. Cross-platform replacement for
`tr -d '\\000' < $< > $@` in the Makefile.

Usage: strip_nulls.py SRC DST

Used by the SGB border tilemap build: gold_border.bin / silver_border.bin
are dumped with trailing nulls that need to be removed before linking.
"""
from __future__ import annotations

import sys


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        sys.stderr.write(f"usage: {argv[0]} SRC DST\n")
        return 2
    with open(argv[1], "rb") as f:
        data = f.read()
    with open(argv[2], "wb") as f:
        f.write(data.replace(b"\x00", b""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
