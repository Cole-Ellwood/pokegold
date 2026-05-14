"""Runtime smoke checks for Spikes and Rapid Spin hazard state.

This harness intentionally checks only WRAM state transitions. Directly calling
the move-effect commands reaches animation/text code that does not return to
the HRAM sentinel in this context, but the hazard bits are already updated by
then. Use these checks as fixture evidence for layer state, not for PP, text,
or full turn timing.

Usage:
    python -m tools.damage_debugger.hazard_smoke
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from .boot_cache import BootStateCache
from .paths import find_rom, find_sym
from .safe_call import call_function_safe, read_byte_banked, write_byte_banked
from .symbols import SymbolTable


LOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "audit"
    / "damage_debugger"
    / "hazard_smoke.log"
)

SPIKES_MASK = 0b00000011
CALL_BUDGET = 500
NORMAL_TYPE = 0x00
FLYING_TYPE = 0x02


@dataclass(frozen=True)
class HazardCase:
    name: str
    command: str
    battle_turn: int
    player_screens: int
    enemy_screens: int
    expected_player_screens: int
    expected_enemy_screens: int
    note: str


@dataclass(frozen=True)
class FractionCase:
    name: str
    command: str
    max_hp: int
    expected_damage: int
    note: str


@dataclass(frozen=True)
class ImmunityCase:
    name: str
    battle_turn: int
    player_screens: int
    enemy_screens: int
    type1: int
    type2: int
    hp_name: str
    type_name: str
    note: str


CASES = [
    HazardCase(
        "gll-spikes-001-player-0-to-1",
        "BattleCommand_Spikes",
        0,
        0,
        0,
        0,
        1,
        "player Spikes targets enemy side and increments 0 -> 1",
    ),
    HazardCase(
        "gll-spikes-001-player-1-to-2",
        "BattleCommand_Spikes",
        0,
        0,
        1,
        0,
        2,
        "player Spikes targets enemy side and increments 1 -> 2",
    ),
    HazardCase(
        "gll-spikes-001-player-2-to-3",
        "BattleCommand_Spikes",
        0,
        0,
        2,
        0,
        3,
        "player Spikes targets enemy side and increments 2 -> 3",
    ),
    HazardCase(
        "gll-spikes-001-enemy-0-to-1",
        "BattleCommand_Spikes",
        1,
        0,
        0,
        1,
        0,
        "enemy Spikes targets player side and increments 0 -> 1",
    ),
    HazardCase(
        "gll-spikes-002-fourth-click-fails",
        "BattleCommand_Spikes",
        0,
        0,
        3,
        0,
        3,
        "player Spikes at 3 layers leaves enemy side at 3",
    ),
    HazardCase(
        "gll-spin-001-player-clears-one-layer",
        "BattleCommand_ClearHazards",
        0,
        1,
        3,
        0,
        3,
        "player Rapid Spin hazard clear removes own-side 1-layer Spikes",
    ),
    HazardCase(
        "gll-spin-001-player-clears-two-layers",
        "BattleCommand_ClearHazards",
        0,
        2,
        3,
        0,
        3,
        "player Rapid Spin hazard clear removes own-side 2-layer Spikes",
    ),
    HazardCase(
        "gll-spin-001-player-clears-three-layers",
        "BattleCommand_ClearHazards",
        0,
        3,
        3,
        0,
        3,
        "player Rapid Spin hazard clear removes own-side 3-layer Spikes",
    ),
    HazardCase(
        "gll-spin-001-enemy-clears-three-layers",
        "BattleCommand_ClearHazards",
        1,
        3,
        3,
        3,
        0,
        "enemy Rapid Spin hazard clear removes own-side 3-layer Spikes",
    ),
    HazardCase(
        "gll-spin-002-no-layers-control",
        "BattleCommand_ClearHazards",
        0,
        0,
        3,
        0,
        3,
        "player Rapid Spin hazard clear leaves own-side 0 layers unchanged",
    ),
]


FRACTION_CASES = [
    FractionCase(
        "gll-spikes-003-one-layer-fraction",
        "GetEighthMaxHP",
        120,
        15,
        "1-layer Spikes uses maxHP/8 on a 120-HP target",
    ),
    FractionCase(
        "gll-spikes-003-two-layer-fraction",
        "GetSixthMaxHP_Far",
        120,
        20,
        "2-layer Spikes uses maxHP/6 on a 120-HP target",
    ),
    FractionCase(
        "gll-spikes-003-three-layer-fraction",
        "GetQuarterMaxHP",
        120,
        30,
        "3-layer Spikes uses maxHP/4 on a 120-HP target",
    ),
]


IMMUNITY_CASES = [
    ImmunityCase(
        "gll-spikes-004-player-flying-type1",
        0,
        3,
        0,
        FLYING_TYPE,
        NORMAL_TYPE,
        "wBattleMonHP",
        "wBattleMonType",
        "player-side incoming Flying type slot 1 takes no Spikes damage",
    ),
    ImmunityCase(
        "gll-spikes-004-player-flying-type2",
        0,
        3,
        0,
        NORMAL_TYPE,
        FLYING_TYPE,
        "wBattleMonHP",
        "wBattleMonType",
        "player-side incoming Flying type slot 2 takes no Spikes damage",
    ),
    ImmunityCase(
        "gll-spikes-004-enemy-flying-type1",
        1,
        0,
        3,
        FLYING_TYPE,
        NORMAL_TYPE,
        "wEnemyMonHP",
        "wEnemyMonType",
        "enemy-side incoming Flying type slot 1 takes no Spikes damage",
    ),
    ImmunityCase(
        "gll-spikes-004-enemy-flying-type2",
        1,
        0,
        3,
        NORMAL_TYPE,
        FLYING_TYPE,
        "wEnemyMonHP",
        "wEnemyMonType",
        "enemy-side incoming Flying type slot 2 takes no Spikes damage",
    ),
]


def _read_byte(pyboy, syms: dict, name: str) -> int:
    bank, addr = syms[name]
    return read_byte_banked(pyboy, addr, bank)


def _write_byte(pyboy, syms: dict, name: str, value: int) -> None:
    bank, addr = syms[name]
    write_byte_banked(pyboy, addr, value, bank)


def _write_byte_offset(pyboy, syms: dict, name: str, offset: int, value: int) -> None:
    bank, addr = syms[name]
    write_byte_banked(pyboy, addr + offset, value, bank)


def _read_u16(pyboy, syms: dict, name: str) -> int:
    bank, addr = syms[name]
    hi = read_byte_banked(pyboy, addr, bank)
    lo = read_byte_banked(pyboy, addr + 1, bank)
    return (hi << 8) | lo


def _write_u16(pyboy, syms: dict, name: str, value: int) -> None:
    bank, addr = syms[name]
    write_byte_banked(pyboy, addr, (value >> 8) & 0xFF, bank)
    write_byte_banked(pyboy, addr + 1, value & 0xFF, bank)


def _run_case(case: HazardCase, cache: BootStateCache, syms: dict) -> tuple[bool, str]:
    pyboy = cache.restore()

    _write_byte(pyboy, syms, "hBattleTurn", case.battle_turn)
    _write_byte(pyboy, syms, "wPlayerScreens", case.player_screens)
    _write_byte(pyboy, syms, "wEnemyScreens", case.enemy_screens)
    _write_byte(pyboy, syms, "wPlayerWrapCount", 0)
    _write_byte(pyboy, syms, "wEnemyWrapCount", 0)
    _write_byte(pyboy, syms, "wEffectFailed", 0)

    ticks, returned, post_pc = call_function_safe(
        pyboy,
        syms,
        case.command,
        budget=CALL_BUDGET,
    )

    got_player = _read_byte(pyboy, syms, "wPlayerScreens") & SPIKES_MASK
    got_enemy = _read_byte(pyboy, syms, "wEnemyScreens") & SPIKES_MASK
    ok = (
        got_player == case.expected_player_screens
        and got_enemy == case.expected_enemy_screens
    )

    detail = (
        f"{case.name:<38s} player={got_player} enemy={got_enemy} "
        f"expected={case.expected_player_screens}/{case.expected_enemy_screens} "
        f"returned={returned} ticks={ticks} pc=${post_pc:04x}  {case.note}"
    )
    return ok, detail


def _run_fraction_case(
    case: FractionCase,
    cache: BootStateCache,
    syms: dict,
) -> tuple[bool, str]:
    pyboy = cache.restore()

    _write_byte(pyboy, syms, "hBattleTurn", 0)
    _write_u16(pyboy, syms, "wBattleMonMaxHP", case.max_hp)
    _write_u16(pyboy, syms, "wEnemyMonMaxHP", case.max_hp)

    ticks, returned, post_pc = call_function_safe(
        pyboy,
        syms,
        case.command,
        budget=CALL_BUDGET,
    )

    rf = pyboy.register_file
    got = (int(rf.B) << 8) | int(rf.C)
    ok = got == case.expected_damage and returned
    detail = (
        f"{case.name:<38s} damage={got} expected={case.expected_damage} "
        f"returned={returned} ticks={ticks} pc=${post_pc:04x}  {case.note}"
    )
    return ok, detail


def _run_immunity_case(
    case: ImmunityCase,
    cache: BootStateCache,
    syms: dict,
) -> tuple[bool, str]:
    pyboy = cache.restore()

    _write_byte(pyboy, syms, "hBattleTurn", case.battle_turn)
    _write_byte(pyboy, syms, "wPlayerScreens", case.player_screens)
    _write_byte(pyboy, syms, "wEnemyScreens", case.enemy_screens)
    _write_byte_offset(pyboy, syms, case.type_name, 0, case.type1)
    _write_byte_offset(pyboy, syms, case.type_name, 1, case.type2)
    _write_u16(pyboy, syms, case.hp_name, 120)
    _write_u16(pyboy, syms, case.hp_name.replace("HP", "MaxHP"), 120)

    ticks, returned, post_pc = call_function_safe(
        pyboy,
        syms,
        "SpikesDamage",
        budget=CALL_BUDGET,
    )

    got_hp = _read_u16(pyboy, syms, case.hp_name)
    ok = got_hp == 120 and returned
    detail = (
        f"{case.name:<38s} hp={got_hp} expected=120 "
        f"returned={returned} ticks={ticks} pc=${post_pc:04x}  {case.note}"
    )
    return ok, detail


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv:
        print("usage: python -m tools.damage_debugger.hazard_smoke", file=sys.stderr)
        return 2

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    rom = find_rom("pokegold_debug")
    sym = find_sym("pokegold_debug")
    syms = SymbolTable.load(sym).as_legacy_dict()

    cache = BootStateCache(rom)
    cache.prime()

    total_cases = len(CASES) + len(FRACTION_CASES) + len(IMMUNITY_CASES)
    lines = [
        f"hazard_smoke: running {total_cases} cases against {rom}",
        "note: returned=False is expected for text/animation move-effect calls",
        "",
    ]
    failures: list[str] = []
    try:
        for case in CASES:
            ok, detail = _run_case(case, cache, syms)
            status = "PASS" if ok else "FAIL"
            line = f"{status} {detail}"
            lines.append(line)
            if not ok:
                failures.append(line)
        for case in FRACTION_CASES:
            ok, detail = _run_fraction_case(case, cache, syms)
            status = "PASS" if ok else "FAIL"
            line = f"{status} {detail}"
            lines.append(line)
            if not ok:
                failures.append(line)
        for case in IMMUNITY_CASES:
            ok, detail = _run_immunity_case(case, cache, syms)
            status = "PASS" if ok else "FAIL"
            line = f"{status} {detail}"
            lines.append(line)
            if not ok:
                failures.append(line)
    finally:
        cache.stop()

    lines.append("")
    if failures:
        lines.append(f"FAIL: {len(failures)} hazard smoke case(s) failed.")
    else:
        lines.append("PASS: all hazard smoke cases matched expected state.")

    text = "\n".join(lines)
    print(text)
    LOG_PATH.write_text(text + "\n", encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
