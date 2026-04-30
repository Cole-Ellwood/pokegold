#!/usr/bin/env python3
"""Verify files against an sha1sum-compatible manifest."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def parse_manifest_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line:
        return None
    try:
        expected, name = line.split(maxsplit=1)
    except ValueError:
        raise ValueError(f"invalid manifest line: {line!r}") from None
    return expected.lower(), name.lstrip("*")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_sha1.py <manifest>", file=sys.stderr)
        return 2

    manifest_path = Path(sys.argv[1]).resolve()
    if not manifest_path.exists():
        print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    failures = 0
    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        parsed = parse_manifest_line(raw_line)
        if parsed is None:
            continue
        expected, rel_path = parsed
        file_path = Path(rel_path)
        if not file_path.is_absolute():
            file_path = manifest_path.parent / file_path
        if not file_path.exists():
            print(f"{rel_path}: MISSING")
            failures += 1
            continue
        actual = sha1_file(file_path)
        if actual == expected:
            print(f"{rel_path}: OK")
        else:
            print(f"{rel_path}: FAIL expected {expected} got {actual}")
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
