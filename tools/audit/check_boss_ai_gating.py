#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOSS_FILE = ROOT / "engine" / "battle" / "ai" / "boss.asm"
CALLSITE_FILES = [
    ROOT / "engine" / "battle" / "core.asm",
    ROOT / "engine" / "battle" / "ai" / "move.asm",
    ROOT / "engine" / "battle" / "ai" / "items.asm",
    ROOT / "engine" / "battle" / "used_move_text.asm",
]

GUARDED_ENTRYPOINTS = {
    "BossAI_IncrementTurnsElapsed",
    "BossAI_RecordPlayerSwitch",
    "BossAI_RecordPlayerSpecies",
    "BossAI_RecordPlayerFaint",
    "BossAI_RecordRevealedPlayerMove",
    "BossAI_LoadPlayerUsedMovesForActiveSpecies",
    "BossAI_ApplyMoveModel",
    "BossAI_SelectMove",
    "BossAI_SwitchOrTryItem",
    "BossAI_OnSwitchExecuted",
    "BossAI_SelectPlanIfNeeded",
    "BossAI_ComputePlayerPlausibleTypeMask",
    "BossAI_EvaluateActionLookahead",
}

LABEL_RE = re.compile(r"^([A-Za-z0-9_]+):\s*(?:;.*)?$")
CALL_RE = re.compile(r"\b(?:callfar|call|jp)\s+(BossAI_[A-Za-z0-9_]+)\b")


def strip_comment(line: str) -> str:
    if ";" in line:
        return line.split(";", 1)[0]
    return line


def load_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def find_labels(lines: list[str]) -> dict[str, int]:
    labels: dict[str, int] = {}
    for i, line in enumerate(lines):
        m = LABEL_RE.match(line.strip())
        if m:
            labels[m.group(1)] = i
    return labels


def guard_present(lines: list[str], start_idx: int) -> bool:
    # Find ordered sequence in first instructions of function body.
    tokens = []
    i = start_idx + 1
    while i < len(lines):
        raw = lines[i]
        code = strip_comment(raw).strip()
        if code:
            if LABEL_RE.match(code):
                break
            tokens.append(code)
            if len(tokens) >= 18:
                break
        i += 1

    want = ["ld a, [wBossAITier]", "and a", "ret z"]
    pos = 0
    for token in tokens:
        if token == want[pos]:
            pos += 1
            if pos == len(want):
                return True
    return False


def audit_entrypoint_guards() -> list[str]:
    errs: list[str] = []
    lines = load_lines(BOSS_FILE)
    labels = find_labels(lines)
    for name in sorted(GUARDED_ENTRYPOINTS):
        if name not in labels:
            errs.append(f"missing entrypoint label: {name}")
            continue
        if not guard_present(lines, labels[name]):
            errs.append(f"entrypoint missing tier gate: {name}")
    return errs


def audit_callsites() -> list[str]:
    errs: list[str] = []
    for path in CALLSITE_FILES:
        lines = load_lines(path)
        for lineno, raw in enumerate(lines, start=1):
            code = strip_comment(raw).strip()
            if not code:
                continue
            m = CALL_RE.search(code)
            if not m:
                continue
            target = m.group(1)
            if target not in GUARDED_ENTRYPOINTS:
                rel = path.relative_to(ROOT)
                errs.append(f"{rel}:{lineno} calls non-guarded BossAI symbol {target}")
    return errs


def main() -> int:
    required = [BOSS_FILE, *CALLSITE_FILES]
    missing = [p for p in required if not p.exists()]
    if missing:
        print("ERROR: missing required files:", file=sys.stderr)
        for path in missing:
            print(f"  - {path}", file=sys.stderr)
        return 1

    errors = []
    errors.extend(audit_entrypoint_guards())
    errors.extend(audit_callsites())

    if errors:
        print("Boss AI gating audit FAILED.", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("Boss AI gating audit passed.")
    print("Guarded entrypoints:")
    for name in sorted(GUARDED_ENTRYPOINTS):
        print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
