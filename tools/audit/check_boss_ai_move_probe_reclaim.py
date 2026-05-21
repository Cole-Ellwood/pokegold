#!/usr/bin/env python3
"""Audit that the Boss AI move-probe scratch reclaim is still in place.

The earlier design saved/restored ``wEnemyMoveStruct`` through a 7-byte
``wBossAISavedEnemyMoveStruct`` scratch buffer and a pair of helpers
(``BossAI_SaveEnemyMoveStruct`` / ``BossAI_RestoreEnemyMoveStruct``).
The refactor that shipped instead uses ``*Pure`` move evaluators that
read move bytes without touching ``wEnemyMoveStruct``, removing the
scratch dependency entirely.

This audit's job now is to keep the reclaim from being undone: the
scratch symbol, the save/restore helpers, and any calls to them must
remain absent from ``ram/wram.asm`` and ``engine/battle/ai/*.asm``.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WRAM = ROOT / "ram" / "wram.asm"
ENGINE_AI = ROOT / "engine" / "battle" / "ai"

FORBIDDEN = (
    "wBossAISavedEnemyMoveStruct",
    "BossAI_SaveEnemyMoveStruct",
    "BossAI_RestoreEnemyMoveStruct",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_lines(path: Path) -> list[str]:
    if not path.exists():
        fail(f"missing required file: {rel(path)}")
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def main() -> int:
    scanned = [WRAM, *sorted(ENGINE_AI.glob("*.asm"))]
    hits: list[str] = []
    for path in scanned:
        for line_no, line in enumerate(load_lines(path), start=1):
            for needle in FORBIDDEN:
                if needle in line:
                    hits.append(f"{rel(path)}:{line_no}: {needle}")
    if hits:
        print("Move-probe scratch reclaim is not in place:")
        for hit in hits[:20]:
            print(f"  {hit}")
        if len(hits) > 20:
            print(f"  ... {len(hits) - 20} more")
        fail("expected no move-struct scratch symbol, helper, or call references")

    print("Boss AI move-probe reclaim audit passed.")
    print("The 7-byte saved enemy move struct dependency is absent from WRAM and Boss AI source.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
