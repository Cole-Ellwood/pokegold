#!/usr/bin/env python3
"""Export batch change bullets grouped by manifest category."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

from manifest_changes import CategorySection, parse_manifest


def build_output(categories: list[CategorySection], generated_on: str) -> str:
    output_lines: list[str] = [
        "CHANGES BY CATEGORY",
        "GENERATED FROM docs/manifest.md",
        f"GENERATED: {generated_on}",
        "",
    ]

    for category in categories:
        if not category.sections:
            continue
        output_lines.append(category.heading)
        for section in category.sections:
            output_lines.append(section.heading)
            output_lines.extend(section.bullets)
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
    changes = parse_manifest(lines)

    if not changes.found_category:
        print("error: no top-level '## ' category headings found in docs/manifest.md", file=sys.stderr)
        return 1
    if not changes.found_section:
        print("error: no '### ' change sections found in docs/manifest.md", file=sys.stderr)
        return 1

    output_text = build_output(changes.categories, date.today().isoformat())
    output_path.write_text(output_text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
