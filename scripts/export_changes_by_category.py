#!/usr/bin/env python3
"""Export batch change bullets grouped by manifest category."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import sys


CATEGORY_RE = re.compile(r"^##\s+(.+?)\s*$")
BATCH_RE = re.compile(r"^###\s+Batch\s+(\d+)\s*$")


@dataclass
class BatchSection:
    number: int
    bullets: list[str]


@dataclass
class CategorySection:
    heading: str
    batches: list[BatchSection]


def parse_manifest(lines: list[str]) -> tuple[list[CategorySection], bool, bool]:
    categories: list[CategorySection] = []
    found_category = False
    found_batch = False
    current_category: CategorySection | None = None
    i = 0

    while i < len(lines):
        line = lines[i]
        category_match = CATEGORY_RE.match(line)
        if category_match:
            found_category = True
            current_category = CategorySection(heading=f"## {category_match.group(1)}", batches=[])
            categories.append(current_category)
            i += 1
            continue

        batch_match = BATCH_RE.match(line)
        if batch_match:
            found_batch = True
            batch_number = int(batch_match.group(1))
            bullets: list[str] = []
            j = i + 1
            while j < len(lines):
                current_line = lines[j]
                if current_line.startswith("### ") or current_line.startswith("## "):
                    break
                if current_line.lstrip().startswith("- "):
                    bullets.append(current_line.rstrip())
                j += 1
            if current_category is not None:
                current_category.batches.append(BatchSection(number=batch_number, bullets=bullets))
            i = j
            continue

        i += 1

    return categories, found_category, found_batch


def build_output(categories: list[CategorySection], generated_on: str) -> str:
    output_lines: list[str] = [
        "CHANGES BY CATEGORY",
        "GENERATED FROM docs/manifest.md",
        f"GENERATED: {generated_on}",
        "",
    ]

    for category in categories:
        if not category.batches:
            continue
        output_lines.append(category.heading)
        for batch in sorted(category.batches, key=lambda item: item.number):
            output_lines.append(f"### Batch {batch.number}")
            output_lines.extend(batch.bullets)
            output_lines.append("")
        output_lines.append("")

    return "\n".join(output_lines).rstrip() + "\n"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = repo_root / "docs" / "manifest.md"
    output_path = repo_root / "docs" / "CHANGES_BY_CATEGORY.txt"

    if not manifest_path.exists():
        print(f"error: missing manifest file: {manifest_path}", file=sys.stderr)
        return 1

    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    categories, found_category, found_batch = parse_manifest(lines)

    if not found_category:
        print("error: no top-level '## ' category headings found in docs/manifest.md", file=sys.stderr)
        return 1
    if not found_batch:
        print("error: no '### Batch N' sections found in docs/manifest.md", file=sys.stderr)
        return 1

    output_text = build_output(categories, date.today().isoformat())
    output_path.write_text(output_text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
