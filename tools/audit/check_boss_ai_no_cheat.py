#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

# Minimum required scan surface from sprint spec.
SCAN_FILES = [
    ROOT / "engine" / "battle" / "ai" / "boss_platform.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_policy_switch.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_data.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_thunks.asm",
    ROOT / "engine" / "battle" / "ai" / "move.asm",
    ROOT / "engine" / "battle" / "ai" / "items.asm",
]


@dataclass(frozen=True)
class ForbiddenPattern:
    pattern: re.Pattern[str]
    reason: str


# Curated forbidden symbols/routines for non-cheating Boss AI:
# - no unrevealed player party reads
# - no unrevealed player move/item reads
# - no direct player input reads
FORBIDDEN_PATTERNS = [
    ForbiddenPattern(re.compile(r"\bwPartyCount\b"), "unrevealed player party size"),
    ForbiddenPattern(re.compile(r"\bwPartyMons\b"), "unrevealed player party struct"),
    ForbiddenPattern(re.compile(r"\bwPartySpecies\b"), "unrevealed player party species"),
    ForbiddenPattern(re.compile(r"\bwPartyMon1[A-Za-z0-9_]*\b"), "unrevealed player party data"),
    ForbiddenPattern(re.compile(r"\bwBattleMonMoves\b"), "unrevealed active player move list"),
    ForbiddenPattern(re.compile(r"\bwBattleMonPP\b"), "unrevealed active player move PP"),
    ForbiddenPattern(re.compile(r"\bwBattleMonItem\b"), "hidden active player held item"),
    ForbiddenPattern(re.compile(r"\bwCurPlayerMove\b"), "player input read"),
    ForbiddenPattern(re.compile(r"\bwBattlePlayerAction\b"), "player input action read"),
    ForbiddenPattern(re.compile(r"\bhJoy[A-Za-z0-9_]*\b"), "joypad input read"),
    ForbiddenPattern(re.compile(r"\bwMenuCursor[A-Za-z0-9_]*\b"), "menu input read"),
]


def strip_comment(line: str) -> str:
    if ";" in line:
        return line.split(";", 1)[0]
    return line


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    issues: list[tuple[int, str, str]] = []
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for lineno, line in enumerate(raw, start=1):
        code = strip_comment(line)
        if not code.strip():
            continue
        for fp in FORBIDDEN_PATTERNS:
            if fp.pattern.search(code):
                issues.append((lineno, fp.pattern.pattern, fp.reason))
    return issues


def main() -> int:
    missing = [p for p in SCAN_FILES if not p.exists()]
    if missing:
        print("ERROR: missing required files:", file=sys.stderr)
        for p in missing:
            print(f"  - {p}", file=sys.stderr)
        return 1

    any_issues = False
    for path in SCAN_FILES:
        issues = scan_file(path)
        if issues:
            any_issues = True
            print(f"FAIL {path.relative_to(ROOT)}")
            for lineno, pat, reason in issues:
                print(f"  L{lineno}: {pat} ({reason})")

    if any_issues:
        print("Boss AI no-cheat audit FAILED.", file=sys.stderr)
        return 1

    print("Boss AI no-cheat audit passed.")
    print("Scanned files:")
    for path in SCAN_FILES:
        print(f"  - {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
