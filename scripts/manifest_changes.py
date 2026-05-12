from __future__ import annotations

import re
from dataclasses import dataclass


CATEGORY_RE = re.compile(r"^##\s+(.+?)\s*$")
SECTION_RE = re.compile(r"^###\s+(.+?)\s*$")


@dataclass
class ChangeSection:
    heading: str
    bullets: list[str]


@dataclass
class CategorySection:
    heading: str
    sections: list[ChangeSection]


@dataclass
class ManifestChanges:
    categories: list[CategorySection]
    found_category: bool
    found_section: bool


def section_bullets(lines: list[str], start: int) -> tuple[list[str], int]:
    bullets: list[str] = []
    in_bullet = False
    index = start

    while index < len(lines):
        current_line = lines[index]
        if current_line.startswith("### ") or current_line.startswith("## "):
            break
        if current_line.lstrip().startswith("- "):
            bullets.append(current_line.rstrip())
            in_bullet = True
        elif in_bullet and current_line.startswith((" ", "\t")) and current_line.strip():
            bullets.append(current_line.rstrip())
        elif current_line.strip():
            in_bullet = False
        index += 1

    return bullets, index


def parse_manifest(lines: list[str]) -> ManifestChanges:
    categories: list[CategorySection] = []
    found_category = False
    found_section = False
    current_category: CategorySection | None = None
    index = 0

    while index < len(lines):
        line = lines[index]
        category_match = CATEGORY_RE.match(line)
        if category_match:
            found_category = True
            current_category = CategorySection(heading=f"## {category_match.group(1)}", sections=[])
            categories.append(current_category)
            index += 1
            continue

        section_match = SECTION_RE.match(line)
        if section_match:
            found_section = True
            bullets, next_index = section_bullets(lines, index + 1)
            if current_category is not None and bullets:
                current_category.sections.append(
                    ChangeSection(heading=f"### {section_match.group(1)}", bullets=bullets)
                )
            index = next_index
            continue

        index += 1

    return ManifestChanges(
        categories=categories,
        found_category=found_category,
        found_section=found_section,
    )


def flat_title(title: str, category: str, seen_titles: set[str]) -> str:
    if title.startswith("Batch "):
        return title
    if title not in seen_titles:
        seen_titles.add(title)
        return title
    if category:
        return f"{title} {category.lower()}"
    return title


def flat_change_sections(changes: ManifestChanges) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    seen_titles: set[str] = set()

    for category in changes.categories:
        category_title = category.heading.removeprefix("## ")
        for section in category.sections:
            title = section.heading.removeprefix("### ")
            sections.append((f"### {flat_title(title, category_title, seen_titles)}", section.bullets))

    return sections
