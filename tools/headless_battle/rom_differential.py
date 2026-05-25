"""ROM-backed differential goldens for the headless battle simulator.

These checks intentionally stay tiny. They do not make the simulator a full
emulator; they pin one selected headless turn against the same battle-command
sequence in the built ROM so future slices can see when a source-mirrored path
has crossed into differential proof.

Usage:
    python -m tools.headless_battle.rom_differential
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools.damage_debugger.boot_cache import BootStateCache
from tools.damage_debugger.paths import find_rom, find_sym
from tools.damage_debugger.safe_call import (
    call_function_safe,
    read_be_u16_banked,
    read_byte_banked,
    write_byte_banked,
)
from tools.damage_debugger.symbols import SymbolTable
from tools.headless_battle.simulator import simulate_payload


TACKLE_MOVE_ID = 0x21
NORMAL_TYPE = 0x00
FLYING_TYPE = 0x02
FIRE_TYPE = 0x14
LINK_MODE = 1
FIXED_RNG_VALUES = (255, 255)
CALL_BUDGET = 50_000
NORMAL_HIT_CHAIN = (
    "BattleCommand_DoTurn",
    "BattleCommand_Critical",
    "BattleCommand_DamageStats",
    "BattleCommand_DamageCalc",
    "BattleCommand_Stab",
    "BattleCommand_DamageVariation",
    "BattleCommand_CheckHit",
    "BattleCommand_ApplyDamage",
)


@dataclass(frozen=True)
class RomNormalHitResult:
    scenario_id: str
    player_hp_before: int
    player_hp_after: int
    enemy_pp_before: int
    enemy_pp_after: int
    damage: int
    attack_missed: bool
    critical: bool
    rng_values: tuple[int, ...]
    rng_consumed: int
    command_returns: dict[str, bool]


@dataclass(frozen=True)
class DifferentialResult:
    scenario_id: str
    ok: bool
    errors: tuple[str, ...]
    rom: dict[str, Any]
    headless: dict[str, Any]


def _read_byte(pyboy: Any, syms: dict[str, tuple[int, int]], name: str, offset: int = 0) -> int:
    bank, addr = syms[name]
    return read_byte_banked(pyboy, addr + offset, bank)


def _write_byte(pyboy: Any, syms: dict[str, tuple[int, int]], name: str, value: int, offset: int = 0) -> None:
    bank, addr = syms[name]
    write_byte_banked(pyboy, addr + offset, value, bank)


def _read_u16(pyboy: Any, syms: dict[str, tuple[int, int]], name: str) -> int:
    bank, addr = syms[name]
    return read_be_u16_banked(pyboy, addr, bank)


def _write_u16(pyboy: Any, syms: dict[str, tuple[int, int]], name: str, value: int) -> None:
    _write_byte(pyboy, syms, name, (value >> 8) & 0xFF)
    _write_byte(pyboy, syms, name, value & 0xFF, 1)


def _seed_common(pyboy: Any, syms: dict[str, tuple[int, int]]) -> None:
    for name in (
        "wCriticalHit",
        "wTypeModifier",
        "wAttackMissed",
        "wIsConfusionDamage",
        "wEffectFailed",
        "wEnemyScreens",
        "wPlayerScreens",
        "wBattleMonStatus",
        "wEnemyMonStatus",
        "wBattleWeather",
        "wJohtoBadges",
        "wKantoBadges",
        "wCurEnemyMove",
        "wCurPlayerMove",
        "wPlayerSubStatus1",
        "wPlayerSubStatus2",
        "wPlayerSubStatus3",
        "wPlayerSubStatus4",
        "wPlayerSubStatus5",
        "wEnemySubStatus1",
        "wEnemySubStatus2",
        "wEnemySubStatus3",
        "wEnemySubStatus4",
        "wEnemySubStatus5",
    ):
        _write_byte(pyboy, syms, name, 0)
    _write_byte(pyboy, syms, "wTypeMatchup", 0x10)
    _write_u16(pyboy, syms, "wCurDamage", 0)
    for stage in ("Atk", "Def", "Spd", "SAtk", "SDef"):
        _write_byte(pyboy, syms, f"wPlayer{stage}Level", 7)
        _write_byte(pyboy, syms, f"wEnemy{stage}Level", 7)
    for stage in ("Acc", "Eva"):
        _write_byte(pyboy, syms, f"wPlayer{stage}Level", 7)
        _write_byte(pyboy, syms, f"wEnemy{stage}Level", 7)


def _seed_rom_normal_hit(pyboy: Any, syms: dict[str, tuple[int, int]]) -> None:
    _seed_common(pyboy, syms)

    _write_byte(pyboy, syms, "wBattleMonSpecies", 155)
    _write_byte(pyboy, syms, "wBattleMonLevel", 5)
    _write_byte(pyboy, syms, "wBattleMonType1", FIRE_TYPE)
    _write_byte(pyboy, syms, "wBattleMonType2", FIRE_TYPE)
    _write_byte(pyboy, syms, "wBattleMonItem", 0)
    _write_u16(pyboy, syms, "wBattleMonHP", 20)
    _write_u16(pyboy, syms, "wBattleMonMaxHP", 20)
    _write_u16(pyboy, syms, "wBattleMonAttack", 10)
    _write_u16(pyboy, syms, "wBattleMonDefense", 9)
    _write_u16(pyboy, syms, "wBattleMonSpeed", 11)
    _write_u16(pyboy, syms, "wBattleMonSpclAtk", 11)
    _write_u16(pyboy, syms, "wBattleMonSpclDef", 10)

    _write_byte(pyboy, syms, "wEnemyMonSpecies", 16)
    _write_byte(pyboy, syms, "wEnemyMonLevel", 2)
    _write_byte(pyboy, syms, "wEnemyMonType1", NORMAL_TYPE)
    _write_byte(pyboy, syms, "wEnemyMonType2", FLYING_TYPE)
    _write_byte(pyboy, syms, "wEnemyMonItem", 0)
    _write_u16(pyboy, syms, "wEnemyMonHP", 12)
    _write_u16(pyboy, syms, "wEnemyMonMaxHP", 12)
    _write_u16(pyboy, syms, "wEnemyMonAttack", 6)
    _write_u16(pyboy, syms, "wEnemyMonDefense", 6)
    _write_u16(pyboy, syms, "wEnemyMonSpeed", 7)
    _write_u16(pyboy, syms, "wEnemyMonSpclAtk", 5)
    _write_u16(pyboy, syms, "wEnemyMonSpclDef", 5)

    _write_u16(pyboy, syms, "wPlayerAttack", 10)
    _write_u16(pyboy, syms, "wPlayerDefense", 9)
    _write_u16(pyboy, syms, "wPlayerSpAtk", 11)
    _write_u16(pyboy, syms, "wPlayerSpDef", 10)
    _write_u16(pyboy, syms, "wEnemyAttack", 6)
    _write_u16(pyboy, syms, "wEnemyDefense", 6)
    _write_u16(pyboy, syms, "wEnemySpAtk", 5)
    _write_u16(pyboy, syms, "wEnemySpDef", 5)

    for offset, value in (
        (0, TACKLE_MOVE_ID),
        (1, 0x00),  # EFFECT_NORMAL_HIT
        (2, 40),
        (3, NORMAL_TYPE),
        (4, 0xFF),
        (5, 35),
        (6, 0),
    ):
        _write_byte(pyboy, syms, "wEnemyMoveStruct", value, offset)
    _write_byte(pyboy, syms, "wEnemyMonMoves", TACKLE_MOVE_ID, 0)
    _write_byte(pyboy, syms, "wWildMonMoves", TACKLE_MOVE_ID, 0)
    _write_byte(pyboy, syms, "wEnemyMonPP", 35, 0)
    _write_byte(pyboy, syms, "wWildMonPP", 35, 0)
    _write_byte(pyboy, syms, "wCurEnemyMove", TACKLE_MOVE_ID)
    _write_byte(pyboy, syms, "wCurEnemyMoveNum", 0)
    _write_byte(pyboy, syms, "hBattleTurn", 1)
    _write_byte(pyboy, syms, "wBattleMode", 1)

    _write_byte(pyboy, syms, "wLinkMode", LINK_MODE)
    _write_byte(pyboy, syms, "wLinkBattleRNCount", 0)
    for index, value in enumerate(FIXED_RNG_VALUES):
        _write_byte(pyboy, syms, "wLinkBattleRNs", value, index)


def run_rom_normal_hit() -> RomNormalHitResult:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    try:
        pyboy = cache.restore()
        _seed_rom_normal_hit(pyboy, syms)
        player_hp_before = _read_u16(pyboy, syms, "wBattleMonHP")
        enemy_pp_before = _read_byte(pyboy, syms, "wEnemyMonPP")
        command_returns: dict[str, bool] = {}
        for command in NORMAL_HIT_CHAIN:
            _, returned, _ = call_function_safe(pyboy, syms, command, budget=CALL_BUDGET)
            command_returns[command] = returned
        return RomNormalHitResult(
            scenario_id="normal_hit_fixed_rng_enemy_pidgey_tackle",
            player_hp_before=player_hp_before,
            player_hp_after=_read_u16(pyboy, syms, "wBattleMonHP"),
            enemy_pp_before=enemy_pp_before,
            enemy_pp_after=_read_byte(pyboy, syms, "wEnemyMonPP"),
            damage=_read_u16(pyboy, syms, "wCurDamage"),
            attack_missed=bool(_read_byte(pyboy, syms, "wAttackMissed")),
            critical=bool(_read_byte(pyboy, syms, "wCriticalHit")),
            rng_values=FIXED_RNG_VALUES,
            rng_consumed=_read_byte(pyboy, syms, "wLinkBattleRNCount"),
            command_returns=command_returns,
        )
    finally:
        cache.stop()


def normal_hit_payload() -> dict[str, Any]:
    return {
        "rng": {"mode": "fixed", "values": list(FIXED_RNG_VALUES)},
        "state": {
            "weather": "none",
            "weather_count": 0,
            "turn": 1,
            "player": {
                "species": "CYNDAQUIL",
                "level": 5,
                "types": ["FIRE", "FIRE"],
                "hp": 20,
                "max_hp": 20,
                "stats": {
                    "attack": 10,
                    "defense": 9,
                    "speed": 11,
                    "sp_attack": 11,
                    "sp_defense": 10,
                },
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0, "priority": 0, "pp": 35}],
            },
            "enemy": {
                "species": "PIDGEY",
                "level": 2,
                "types": ["NORMAL", "FLYING"],
                "hp": 12,
                "max_hp": 12,
                "stats": {
                    "attack": 6,
                    "defense": 6,
                    "speed": 7,
                    "sp_attack": 5,
                    "sp_defense": 5,
                },
                "moves": [
                    {
                        "name": "TACKLE",
                        "type": "NORMAL",
                        "bp": 40,
                        "priority": 1,
                        "accuracy": 255,
                        "pp": 35,
                    }
                ],
            },
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def compare_normal_hit_fixed_rng() -> DifferentialResult:
    rom = run_rom_normal_hit()
    report = simulate_payload(normal_hit_payload())
    outcome = report["outcomes"][0]
    damage_events = [
        event
        for event in outcome["events"]
        if event.get("actor") == "enemy" and event.get("type") == "damage"
    ]
    errors: list[str] = []
    if len(damage_events) != 1:
        errors.append(f"expected one enemy damage event, got {len(damage_events)}")
        damage_event: dict[str, Any] = {}
    else:
        damage_event = damage_events[0]
    if damage_event.get("damage") != rom.damage:
        errors.append(f"damage mismatch: headless={damage_event.get('damage')} rom={rom.damage}")
    if damage_event.get("actual_damage") != rom.player_hp_before - rom.player_hp_after:
        errors.append(
            "actual damage mismatch: "
            f"headless={damage_event.get('actual_damage')} rom={rom.player_hp_before - rom.player_hp_after}"
        )
    if damage_event.get("target_hp_after") != rom.player_hp_after:
        errors.append(
            f"target HP mismatch: headless={damage_event.get('target_hp_after')} rom={rom.player_hp_after}"
        )
    if damage_event.get("pp_after") != rom.enemy_pp_after:
        errors.append(f"PP mismatch: headless={damage_event.get('pp_after')} rom={rom.enemy_pp_after}")
    if bool(damage_event.get("critical_check", {}).get("critical")) != rom.critical:
        errors.append(
            "critical mismatch: "
            f"headless={damage_event.get('critical_check', {}).get('critical')} rom={rom.critical}"
        )
    if bool(damage_event.get("accuracy_check", {}).get("hit") is False) != rom.attack_missed:
        errors.append(
            "hit/miss mismatch: "
            f"headless_hit={damage_event.get('accuracy_check', {}).get('hit')} rom_missed={rom.attack_missed}"
        )
    if tuple(outcome.get("rng_consumed", ())) != rom.rng_values:
        errors.append(f"RNG values mismatch: headless={outcome.get('rng_consumed')} rom={list(rom.rng_values)}")
    if outcome["state"]["player"]["hp"] != rom.player_hp_after:
        errors.append(f"final player HP mismatch: headless={outcome['state']['player']['hp']} rom={rom.player_hp_after}")
    if rom.rng_consumed != len(rom.rng_values):
        errors.append(f"ROM RNG consumption mismatch: consumed={rom.rng_consumed} seeded={len(rom.rng_values)}")
    for command, returned in rom.command_returns.items():
        if command == "BattleCommand_ApplyDamage":
            continue
        if not returned:
            errors.append(f"{command} did not return to sentinel")
    if rom.command_returns.get("BattleCommand_ApplyDamage", True):
        errors.append("BattleCommand_ApplyDamage unexpectedly returned; fixture expects HUD non-return after HP write")
    return DifferentialResult(
        scenario_id=rom.scenario_id,
        ok=not errors,
        errors=tuple(errors),
        rom={
            "player_hp_before": rom.player_hp_before,
            "player_hp_after": rom.player_hp_after,
            "enemy_pp_before": rom.enemy_pp_before,
            "enemy_pp_after": rom.enemy_pp_after,
            "damage": rom.damage,
            "attack_missed": rom.attack_missed,
            "critical": rom.critical,
            "rng_values": list(rom.rng_values),
            "rng_consumed": rom.rng_consumed,
            "command_returns": rom.command_returns,
        },
        headless={
            "player_hp_after": outcome["state"]["player"]["hp"],
            "rng_consumed": outcome.get("rng_consumed", []),
            "damage_event": damage_event,
        },
    )


def main() -> int:
    result = compare_normal_hit_fixed_rng()
    if result.ok:
        print(
            "normal_hit_fixed_rng_differential: PASS "
            f"damage={result.rom['damage']} hp={result.rom['player_hp_before']}->{result.rom['player_hp_after']} "
            f"pp={result.rom['enemy_pp_before']}->{result.rom['enemy_pp_after']}"
        )
        return 0
    print("normal_hit_fixed_rng_differential: FAIL")
    for error in result.errors:
        print(f"  - {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
