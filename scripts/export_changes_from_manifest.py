#!/usr/bin/env python3
"""Export batch change bullets from docs/manifest.md into docs/CHANGES.txt."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

from manifest_changes import flat_change_sections, parse_manifest


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = repo_root / "docs" / "manifest.md"
    output_path = repo_root / "docs" / "CHANGES.txt"

    if not manifest_path.exists():
        print(f"error: missing manifest file: {manifest_path}", file=sys.stderr)
        return 1

    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    sections = flat_change_sections(parse_manifest(lines))

    if not sections:
        print("error: no '### ' change sections with bullets found in docs/manifest.md", file=sys.stderr)
        return 1

    today = date.today().isoformat()
    output_lines: list[str] = [
        "Rebalance Changes",
        f"Generated: {today}",
        "GENERATED FROM docs/manifest.md",
        "",
    ]

    for title, bullets in sections:
        output_lines.append(title)
        output_lines.extend(bullets)
        output_lines.append("")

    output_text = "\n".join(output_lines).rstrip() + "\n"
    output_path.write_text(output_text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
