#!/usr/bin/env python3
"""Release smoke checks for key gameplay and integration invariants."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def parse_moves(path: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    pat = re.compile(
        r"^\s*move\s+([A-Z0-9_]+),\s*([A-Z0-9_]+),\s*(\d+),\s*([A-Z0-9_]+),\s*(\d+),\s*(\d+),\s*(\d+)"
    )
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pat.match(line)
        if not m:
            continue
        name, effect, power, move_type, acc, pp, chance = m.groups()
        out[name] = {
            "effect": effect,
            "power": power,
            "type": move_type,
            "accuracy": acc,
            "pp": pp,
            "chance": chance,
        }
    return out


def parse_base_stats(path: Path) -> tuple[list[int], tuple[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    stats_pat = re.compile(r"^\s*db\s+(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)")
    type_pat = re.compile(r"^\s*db\s+([A-Z0-9_]+),\s*([A-Z0-9_]+)\s*;\s*type\b")
    stats: list[int] | None = None
    types: tuple[str, str] | None = None
    for line in lines:
        if stats is None:
            m = stats_pat.match(line)
            if m:
                stats = [int(x) for x in m.groups()]
                continue
        if types is None:
            m = type_pat.match(line)
            if m:
                types = (m.group(1), m.group(2))
                continue
        if stats is not None and types is not None:
            break
    if stats is None or types is None:
        fail(f"could not parse stats/types from {path}")
    return stats, types


def parse_levelup_block(path: Path, label: str) -> dict[str, int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_block = False
    out: dict[str, int] = {}
    move_pat = re.compile(r"^\s*db\s+(\d+),\s*([A-Z0-9_]+)\s*$")
    for line in lines:
        if line.strip() == f"{label}:":
            in_block = True
            continue
        if not in_block:
            continue
        if line.strip() == "db 0 ; no more level-up moves":
            return out
        m = move_pat.match(line)
        if m:
            level = int(m.group(1))
            move = m.group(2)
            out[move] = level
    fail(f"did not find level-up terminator for {label}")
    return {}


def require_text(path: Path, needle: str) -> None:
    text = path.read_text(encoding="utf-8")
    if needle not in text:
        fail(f"missing '{needle}' in {path}")


def main() -> int:
    moves = parse_moves(ROOT / "data/moves/moves.asm")
    expected_moves = {
        "CUT": {"effect": "EFFECT_NORMAL_HIT", "power": "70", "accuracy": "100", "pp": "30"},
        "FIRE_SPIN": {"effect": "EFFECT_TRAP_TARGET", "power": "25", "accuracy": "85", "pp": "10"},
        "MUD_SLAP": {"effect": "EFFECT_ACCURACY_DOWN_HIT", "power": "30", "accuracy": "100", "pp": "10"},
    }
    for move, checks in expected_moves.items():
        if move not in moves:
            fail(f"missing move {move}")
        for key, expected in checks.items():
            actual = moves[move][key]
            if actual != expected:
                fail(f"{move} {key}: expected {expected}, got {actual}")
    print("PASS: key move table checks")

    expected_species = {
        "meganium.asm": ([110, 82, 100, 80, 83, 100], ("GRASS", "GRASS")),
        "typhlosion.asm": ([78, 84, 78, 100, 130, 85], ("FIRE", "NORMAL")),
        "feraligatr.asm": ([85, 105, 100, 87, 95, 83], ("WATER", "FIGHTING")),
    }
    for filename, (expected_stats, expected_types) in expected_species.items():
        stats, types = parse_base_stats(ROOT / "data/pokemon/base_stats" / filename)
        if stats != expected_stats:
            fail(f"{filename} stats mismatch: expected {expected_stats}, got {stats}")
        if types != expected_types:
            fail(f"{filename} types mismatch: expected {expected_types}, got {types}")
    print("PASS: starter final evolution stat/type checks")

    evos_path = ROOT / "data/pokemon/evos_attacks.asm"
    expected_level_moves = {
        "MeganiumEvosAttacks": {"HEAL_BELL": 33, "SOLARBEAM": 41},
        "TyphlosionEvosAttacks": {"FIRE_BLAST": 37, "ANCIENTPOWER": 45},
        "FeraligatrEvosAttacks": {"DRAGON_DANCE": 38, "HYDRO_PUMP": 45},
    }
    for label, checks in expected_level_moves.items():
        learned = parse_levelup_block(evos_path, label)
        for move, level in checks.items():
            actual = learned.get(move)
            if actual != level:
                fail(f"{label} {move}: expected Lv{level}, got {actual}")
    print("PASS: key learnset checks")

    require_text(ROOT / "main.asm", 'INCLUDE "engine/events/move_reminder.asm"')
    require_text(ROOT / "main.asm", 'INCLUDE "engine/events/tm_tutor.asm"')
    require_text(ROOT / "main.asm", 'INCLUDE "engine/battle/ai/boss.asm"')
    require_text(ROOT / "data/events/special_pointers.asm", "add_special MoveReminder")
    print("PASS: core module integration checks")

    print("ALL RELEASE SMOKE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
