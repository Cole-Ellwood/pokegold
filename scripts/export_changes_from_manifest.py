#!/usr/bin/env python3
"""Export batch change bullets from docs/manifest.md into docs/CHANGES.txt."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re
import sys


CATEGORY_RE = re.compile(r"^##\s+(.+?)\s*$")
SECTION_RE = re.compile(r"^###\s+(.+?)\s*$")


def section_bullets(lines: list[str], start: int) -> tuple[list[str], int]:
    bullets: list[str] = []
    in_bullet = False
    j = start

    while j < len(lines):
        current = lines[j]
        if current.startswith("### ") or current.startswith("## "):
            break
        if current.lstrip().startswith("- "):
            bullets.append(current.rstrip())
            in_bullet = True
        elif in_bullet and current.startswith((" ", "\t")) and current.strip():
            bullets.append(current.rstrip())
        elif current.strip():
            in_bullet = False
        j += 1

    return bullets, j


def flat_title(title: str, category: str, seen_titles: set[str]) -> str:
    if title.startswith("Batch "):
        return title
    if title not in seen_titles:
        seen_titles.add(title)
        return title
    if category:
        return f"{title} {category.lower()}"
    return title


def extract_change_sections(lines: list[str]) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_category = ""
    seen_titles: set[str] = set()
    i = 0

    while i < len(lines):
        line = lines[i]
        category_match = CATEGORY_RE.match(line)
        if category_match:
            current_category = category_match.group(1)
            i += 1
            continue

        section_match = SECTION_RE.match(line)
        if section_match:
            title = section_match.group(1)
            bullets, j = section_bullets(lines, i + 1)
            if bullets:
                sections.append((f"### {flat_title(title, current_category, seen_titles)}", bullets))
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
    sections = extract_change_sections(lines)

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
