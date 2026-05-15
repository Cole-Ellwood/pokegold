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
    ROOT / "engine" / "battle" / "ai" / "boss_thunks.asm",
    ROOT / "engine" / "battle" / "ai" / "move.asm",
    ROOT / "engine" / "battle" / "ai" / "items.asm",
]


@dataclass(frozen=True)
class ForbiddenPattern:
    pattern: re.Pattern[str]
    reason: str


@dataclass(frozen=True)
class ApprovedDirectHelperException:
    path: str
    helper: str
    top_label: str
    reason: str


@dataclass(frozen=True)
class ApprovedForbiddenPatternException:
    path: str
    reason: str
    top_label: str
    approval: str


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

DIRECT_EXACT_HELPER_RE = re.compile(
    r"\b(?:call|farcall|jp|farjp)\s+"
    r"(?P<helper>AIDamageCalc|AICompareSpeed|CheckPlayerMoveTypeMatchups)\b"
)
TOP_LABEL_RE = re.compile(r"^(?P<label>[A-Za-z_][A-Za-z0-9_]*):{1,2}$")

APPROVED_DIRECT_HELPER_EXCEPTIONS = [
    ApprovedDirectHelperException(
        path="engine/battle/ai/boss_policy_move.asm",
        helper="AICompareSpeed",
        top_label="BossAI_SetupBoostHasFurtherValue",
        reason="approved setup-speed headroom check",
    ),
]

APPROVED_FORBIDDEN_PATTERN_EXCEPTIONS = [
    ApprovedForbiddenPatternException(
        path="engine/battle/ai/boss_policy_switch.asm",
        reason="player input read",
        top_label="BossAI_TryMortyHakiOracle",
        approval="quarantined Morty/Gengar Haki oracle",
    ),
    ApprovedForbiddenPatternException(
        path="engine/battle/ai/boss_policy_switch.asm",
        reason="player input action read",
        top_label="BossAI_TryMortyHakiOracle",
        approval="quarantined Morty/Gengar Haki oracle",
    ),
]


def strip_comment(line: str) -> str:
    if ";" in line:
        return line.split(";", 1)[0]
    return line


def top_label_for_line(raw: list[str], index: int) -> str:
    for line in reversed(raw[: index + 1]):
        match = TOP_LABEL_RE.match(strip_comment(line).strip())
        if match:
            return match.group("label")
    return ""


def is_approved_direct_helper_exception(path: Path, helper: str, top_label: str) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return any(
        exception.path == rel
        and exception.helper == helper
        and exception.top_label == top_label
        for exception in APPROVED_DIRECT_HELPER_EXCEPTIONS
    )


def is_approved_forbidden_pattern_exception(path: Path, reason: str, top_label: str) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return any(
        exception.path == rel
        and exception.reason == reason
        and exception.top_label == top_label
        for exception in APPROVED_FORBIDDEN_PATTERN_EXCEPTIONS
    )


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    issues: list[tuple[int, str, str]] = []
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(raw):
        lineno = index + 1
        code = strip_comment(line)
        if not code.strip():
            continue
        top_label = top_label_for_line(raw, index)
        for fp in FORBIDDEN_PATTERNS:
            if fp.pattern.search(code):
                if is_approved_forbidden_pattern_exception(path, fp.reason, top_label):
                    continue
                issues.append((lineno, fp.pattern.pattern, fp.reason))
        helper_match = DIRECT_EXACT_HELPER_RE.search(code)
        if helper_match:
            helper = helper_match.group("helper")
            if not is_approved_direct_helper_exception(path, helper, top_label):
                issues.append((lineno, helper, "unapproved exact battle helper call"))
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
    print("Approved exact-helper exceptions:")
    for exception in APPROVED_DIRECT_HELPER_EXCEPTIONS:
        print(
            f"  - {exception.path}:{exception.top_label} "
            f"may call {exception.helper} ({exception.reason})"
        )
    print("Approved forbidden-symbol exceptions:")
    for exception in APPROVED_FORBIDDEN_PATTERN_EXCEPTIONS:
        print(
            f"  - {exception.path}:{exception.top_label} may read "
            f"{exception.reason} ({exception.approval})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
