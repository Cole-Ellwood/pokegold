#!/usr/bin/env python3
"""Export batch change bullets from docs/manifest.md into docs/CHANGES.txt."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys


def extract_batch_sections(lines: list[str]) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith("### Batch "):
            title = line.rstrip()
            bullets: list[str] = []
            j = i + 1
            while j < len(lines):
                current = lines[j]
                if current.startswith("### Batch ") or current.startswith("## "):
                    break
                if current.lstrip().startswith("- "):
                    bullets.append(current.rstrip())
                j += 1
            sections.append((title, bullets))
            i = j
            continue
        i += 1

    return sections


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = repo_root / "docs" / "manifest.md"
    output_path = repo_root / "docs" / "CHANGES.txt"

    if not manifest_path.exists():
        print(f"error: missing manifest file: {manifest_path}", file=sys.stderr)
        return 1

    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    sections = extract_batch_sections(lines)

    if not sections:
        print("error: no '### Batch N' sections found in docs/manifest.md", file=sys.stderr)
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
