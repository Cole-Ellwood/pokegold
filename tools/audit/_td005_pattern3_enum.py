#!/usr/bin/env python3
"""TD-005 Pattern 3 enumerator — strict pre-load shape.

Looks for exactly:
    ld hl, wPlayer<X>          ; or wBattle<X>
    ldh a, [hBattleTurn]
    and a
    jr z, .<label>
    ld hl, wEnemy<X>           ; arm A
.<label>                        ; arm B (rejoin)

OR the inverse:
    ld hl, wEnemy<X>
    ldh a, [hBattleTurn]
    and a
    jr nz, .<label>
    ld hl, wPlayer<X>          ; or wBattle<X>
.<label>

Output: one bucket per containing section, with file/line evidence.
Skips engine/pokemon/experience.asm (user WIP).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
SKIP_FILES = {"engine/pokemon/experience.asm"}

# Two strict shapes
SHAPE_PLAYER_DEFAULT = re.compile(
    r"""
        ^[ \t]*ld[ \t]+hl,[ \t]*(?P<player>(?:wPlayer|wBattle)[A-Za-z0-9_+\- ]+)[ \t]*(?:;.*)?$\n
        ^[ \t]*ldh[ \t]+a,[ \t]*\[hBattleTurn\][ \t]*(?:;.*)?$\n
        ^[ \t]*and[ \t]+a[ \t]*(?:;.*)?$\n
        ^[ \t]*jr[ \t]+z,[ \t]*(?P<label>\.[A-Za-z0-9_]+)[ \t]*(?:;.*)?$\n
        ^[ \t]*ld[ \t]+hl,[ \t]*(?P<enemy>wEnemy[A-Za-z0-9_+\- ]+)[ \t]*(?:;.*)?$\n
        ^(?P<labeldef>[ \t]*\.[A-Za-z0-9_]+[ \t]*(?:;.*)?)$
    """,
    re.MULTILINE | re.VERBOSE,
)

SHAPE_ENEMY_DEFAULT = re.compile(
    r"""
        ^[ \t]*ld[ \t]+hl,[ \t]*(?P<enemy>wEnemy[A-Za-z0-9_+\- ]+)[ \t]*(?:;.*)?$\n
        ^[ \t]*ldh[ \t]+a,[ \t]*\[hBattleTurn\][ \t]*(?:;.*)?$\n
        ^[ \t]*and[ \t]+a[ \t]*(?:;.*)?$\n
        ^[ \t]*jr[ \t]+nz,[ \t]*(?P<label>\.[A-Za-z0-9_]+)[ \t]*(?:;.*)?$\n
        ^[ \t]*ld[ \t]+hl,[ \t]*(?P<player>(?:wPlayer|wBattle)[A-Za-z0-9_+\- ]+)[ \t]*(?:;.*)?$\n
        ^(?P<labeldef>[ \t]*\.[A-Za-z0-9_]+[ \t]*(?:;.*)?)$
    """,
    re.MULTILINE | re.VERBOSE,
)


def find_in_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    out = []
    for m in SHAPE_PLAYER_DEFAULT.finditer(text):
        line = text[: m.start()].count("\n") + 1
        # Verify the labeldef matches the jr target
        target = m.group("label")
        ldef = m.group("labeldef").strip().rstrip(":")
        if ldef != target:
            continue
        out.append({
            "shape": "player_default",
            "line": line,
            "player": m.group("player").strip(),
            "enemy": m.group("enemy").strip(),
            "label": target,
        })
    for m in SHAPE_ENEMY_DEFAULT.finditer(text):
        line = text[: m.start()].count("\n") + 1
        target = m.group("label")
        ldef = m.group("labeldef").strip().rstrip(":")
        if ldef != target:
            continue
        out.append({
            "shape": "enemy_default",
            "line": line,
            "player": m.group("player").strip(),
            "enemy": m.group("enemy").strip(),
            "label": target,
        })
    return out


def main() -> int:
    by_file: dict[str, list[dict]] = defaultdict(list)
    total = 0
    for asm_path in sorted(ROOT.rglob("*.asm")):
        try:
            rel = asm_path.relative_to(ROOT).as_posix()
        except ValueError:
            continue
        if rel in SKIP_FILES or rel.startswith(".claude/"):
            continue
        try:
            sites = find_in_file(asm_path)
        except Exception as exc:
            print(f"# ERROR reading {rel}: {exc}", file=sys.stderr)
            continue
        if sites:
            by_file[rel].extend(sites)
            total += len(sites)

    print(f"# TD-005 Pattern 3 — strict pre-load shape\n")
    print(f"Total sites: {total}\n")
    print(f"Skipped: {sorted(SKIP_FILES)}\n")
    print("## Sites by file\n")
    for rel in sorted(by_file):
        rows = by_file[rel]
        print(f"### `{rel}` ({len(rows)} sites)\n")
        print("| Line | Shape | Player addr | Enemy addr | Rejoin label |")
        print("|---|---|---|---|---|")
        for r in rows:
            print(
                f"| {r['line']} | {r['shape']} | `{r['player']}` | `{r['enemy']}` | `{r['label']}` |"
            )
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
