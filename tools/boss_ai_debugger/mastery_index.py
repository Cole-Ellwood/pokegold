from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError


ROOT = Path(__file__).resolve().parents[2]
MASTERY_ROOT = ROOT / "docs" / "pokemon_mastery"
POLICY_CARD_DIR = MASTERY_ROOT / "policy_cards"
QUICK_TEST_DIR = MASTERY_ROOT / "workspace" / "quick_tests"
REVIEWS_DIR = MASTERY_ROOT / "reviews"
SOURCE_TO_POLICY_LEDGER = MASTERY_ROOT / "source_to_policy_ledger.md"
DEFAULT_MASTERY_INDEX_PATH = ROOT / "audit" / "boss_ai_debugger" / "mastery_index.json"

SECTION_NAMES = (
    "Trigger",
    "Default",
    "Opposite boundary",
    "Exceptions",
    "Worst branch",
    "Local status",
    "Evidence",
    "Drill",
)
SECTION_RE = re.compile(r"^(?P<name>[A-Z][A-Za-z -]+):\s*$")
STP_RE = re.compile(r"^## (?P<id>STP-\d+): (?P<title>.+)$")
BACKTICK_PATH_RE = re.compile(r"`([^`]+)`")


def build_mastery_index(root: Path = MASTERY_ROOT) -> dict[str, Any]:
    policy_dir = root / "policy_cards"
    quick_dir = root / "workspace" / "quick_tests"
    reviews_dir = root / "reviews"
    ledger = root / "source_to_policy_ledger.md"
    policy_cards = [
        parse_policy_card(path)
        for path in sorted(policy_dir.glob("*.md"))
        if path.name.lower() != "readme.md"
    ]
    quick_tests = [relative_path(path) for path in sorted(quick_dir.glob("*.md"))]
    reviews = [relative_path(path) for path in sorted(reviews_dir.glob("*.md"))]
    source_policies = parse_source_to_policy_ledger(ledger) if ledger.exists() else []
    data = {
        "schema_version": 1,
        "policy_card_count": len(policy_cards),
        "quick_test_count": len(quick_tests),
        "review_count": len(reviews),
        "source_policy_count": len(source_policies),
        "policy_cards": policy_cards,
        "quick_tests": quick_tests,
        "reviews": reviews,
        "source_policies": source_policies,
    }
    errors = validate_mastery_index(data)
    if errors:
        raise PreferenceDataError("\n".join(errors))
    return data


def parse_policy_card(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].removeprefix("# ").strip() if lines else path.stem
    title = title.removeprefix("Policy Card: ").strip()
    sections = parse_sections(lines)
    evidence = extract_evidence(sections.get("Evidence", []))
    return {
        "id": path.stem,
        "title": title,
        "path": relative_path(path),
        "status": first_prefixed_line(lines, "Status:"),
        "use_when": first_prefixed_line(lines, "Use when:"),
        "trigger": clean_section(sections.get("Trigger", [])),
        "default": clean_section(sections.get("Default", [])),
        "exceptions": clean_section(sections.get("Exceptions", [])),
        "worst_branch": " ".join(clean_section(sections.get("Worst branch", []))),
        "evidence": evidence,
    }


def parse_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        match = SECTION_RE.match(line.strip())
        if match and match.group("name") in SECTION_NAMES:
            current = match.group("name")
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def clean_section(lines: list[str]) -> list[str]:
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        cleaned.append(stripped.removeprefix("- ").strip())
    return cleaned


def extract_evidence(lines: list[str]) -> list[str]:
    evidence: list[str] = []
    for line in lines:
        for match in BACKTICK_PATH_RE.finditer(line):
            evidence.append(match.group(1))
    return evidence


def parse_source_to_policy_ledger(path: Path) -> list[dict[str, Any]]:
    policies: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = STP_RE.match(line)
        if match:
            if current is not None:
                current.update(parse_source_policy_body(current_lines))
                policies.append(current)
            current = {
                "id": match.group("id"),
                "title": match.group("title").strip(),
                "path": relative_path(path),
            }
            current_lines = []
            continue
        if current is not None:
            current_lines.append(line)
    if current is not None:
        current.update(parse_source_policy_body(current_lines))
        policies.append(current)
    return policies


def parse_source_policy_body(lines: list[str]) -> dict[str, Any]:
    fields = {"source": "", "trigger": "", "policy": "", "exceptions": "", "worst_branch": ""}
    for line in lines:
        stripped = line.strip()
        for key in list(fields):
            prefix = key.replace("_", " ").title()
            if stripped.startswith(prefix + ":"):
                fields[key] = stripped.split(":", 1)[1].strip()
    return fields


def validate_mastery_index(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("mastery index schema_version must be 1")
    cards = data.get("policy_cards")
    if not isinstance(cards, list) or not cards:
        errors.append("mastery index must contain policy cards")
    else:
        seen = set()
        for index, card in enumerate(cards):
            card_id = card.get("id") if isinstance(card, dict) else None
            if not card_id:
                errors.append(f"policy_cards[{index}]: missing id")
            elif card_id in seen:
                errors.append(f"policy_cards[{index}]: duplicate id {card_id}")
            else:
                seen.add(card_id)
    return errors


def write_mastery_index(data: dict[str, Any], path: Path = DEFAULT_MASTERY_INDEX_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def format_mastery_index(data: dict[str, Any]) -> str:
    return "\n".join(
        [
            "Boss AI mastery index",
            (
                f"policy_cards={data['policy_card_count']} "
                f"source_policies={data['source_policy_count']} "
                f"quick_tests={data['quick_test_count']} "
                f"reviews={data['review_count']}"
            ),
        ]
    )


def first_prefixed_line(lines: list[str], prefix: str) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return ""


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)
