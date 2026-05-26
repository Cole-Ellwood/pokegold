from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

from tools.boss_ai_debugger import rom_scenarios
from tools.damage_debugger import tables

from .simulator import (
    ActionState,
    BattleState,
    MoveState,
    PokemonState,
    RngConfig,
    RngStream,
    accuracy_options,
    apply_after_hit_effects,
    critical_options,
    damage_variation_options,
    double_damage,
    effective_accuracy_threshold,
    flinch_turn_result,
    freeze_turn_result,
    leftovers_heal_result,
    move_critical_level,
    paralysis_turn_options,
    residual_status_damage_result,
    sleep_turn_options,
    status_adjusted_speed,
    turn_order_options,
)


LINK_NULL = 0
LINK_COLOSSEUM = 3
NEUTRAL_STAT_LEVEL = 7
SERIAL_RNS_LENGTH = 10
SERIAL_RNS_REGENERATION_BOUNDARY = SERIAL_RNS_LENGTH - 1
MOVE_TACKLE = 0x21
MOVE_QUICK_ATTACK = 0x62
MOVE_CONSTANTS = tables.parse_const_values(tables.ROOT / "constants/move_constants.asm")
MOVE_GUST = MOVE_CONSTANTS["GUST"]
MOVE_THUNDER = MOVE_CONSTANTS["THUNDER"]
MOVE_EARTHQUAKE = MOVE_CONSTANTS["EARTHQUAKE"]
MOVE_FISSURE = MOVE_CONSTANTS["FISSURE"]
MOVE_MAGNITUDE = MOVE_CONSTANTS["MAGNITUDE"]
MOVE_TWISTER = MOVE_CONSTANTS["TWISTER"]
MOVE_SLASH = MOVE_CONSTANTS["SLASH"]
MOVE_FLAME_WHEEL = MOVE_CONSTANTS["FLAME_WHEEL"]
MOVE_SACRED_FIRE = MOVE_CONSTANTS["SACRED_FIRE"]
MOVE_EFFECT_CONSTANTS = tables.parse_const_values(tables.ROOT / "constants/move_effect_constants.asm")
EFFECT_NORMAL_HIT = MOVE_EFFECT_CONSTANTS["EFFECT_NORMAL_HIT"]
EFFECT_ALWAYS_HIT = MOVE_EFFECT_CONSTANTS["EFFECT_ALWAYS_HIT"]
EFFECT_THUNDER = MOVE_EFFECT_CONSTANTS["EFFECT_THUNDER"]
SERIAL_NOT_CONNECTED = 0
ITEM_QUICK_CLAW = tables.resolve_item("QUICK_CLAW")
ITEM_CHOICE_SCARF = tables.resolve_item("CHOICE_SCARF")
ITEM_LEFTOVERS = tables.resolve_item("LEFTOVERS")
ITEM_ROCKY_HELMET = tables.resolve_item("ROCKY_HELMET")
ITEM_SHELL_BELL = tables.resolve_item("SHELL_BELL")
ITEM_LIFE_ORB = tables.resolve_item("LIFE_ORB")
ITEM_BRIGHTPOWDER = tables.resolve_item("BRIGHTPOWDER")
ITEM_LUCKY_PUNCH = tables.resolve_item("LUCKY_PUNCH")
ITEM_STICK = tables.resolve_item("STICK")
ITEM_SCOPE_LENS = tables.resolve_item("SCOPE_LENS")
POKEMON_CONSTANTS = tables.parse_const_values(tables.ROOT / "constants/pokemon_constants.asm")
SPECIES_PIDGEY = POKEMON_CONSTANTS["PIDGEY"]
SPECIES_CHANSEY = POKEMON_CONSTANTS["CHANSEY"]
SPECIES_FARFETCH_D = POKEMON_CONSTANTS["FARFETCH_D"]
BATTLE_CONSTANTS = tables.parse_const_values(tables.ROOT / "constants/battle_constants.asm")
PSN_BIT = BATTLE_CONSTANTS["PSN"]
BRN_BIT = BATTLE_CONSTANTS["BRN"]
FRZ_BIT = BATTLE_CONSTANTS["FRZ"]
PAR_BIT = BATTLE_CONSTANTS["PAR"]
SUBSTATUS_PROTECT_BIT = BATTLE_CONSTANTS["SUBSTATUS_PROTECT"]
SUBSTATUS_UNDERGROUND_BIT = BATTLE_CONSTANTS["SUBSTATUS_UNDERGROUND"]
SUBSTATUS_FLYING_BIT = BATTLE_CONSTANTS["SUBSTATUS_FLYING"]
SUBSTATUS_X_ACCURACY_BIT = BATTLE_CONSTANTS["SUBSTATUS_X_ACCURACY"]
SUBSTATUS_LOCK_ON_BIT = BATTLE_CONSTANTS["SUBSTATUS_LOCK_ON"]
SUBSTATUS_FOCUS_ENERGY_BIT = BATTLE_CONSTANTS["SUBSTATUS_FOCUS_ENERGY"]
SUBSTATUS_FLINCHED_BIT = BATTLE_CONSTANTS["SUBSTATUS_FLINCHED"]
SUBSTATUS_TOXIC_BIT = BATTLE_CONSTANTS["SUBSTATUS_TOXIC"]
WEATHER_RAIN = BATTLE_CONSTANTS["WEATHER_RAIN"]
FLYING_TARGET_HIT_MOVE_IDS = {MOVE_GUST, MOVE_THUNDER, MOVE_TWISTER, MOVE_CONSTANTS["WHIRLWIND"]}
UNDERGROUND_TARGET_HIT_MOVE_IDS = {MOVE_EARTHQUAKE, MOVE_FISSURE, MOVE_MAGNITUDE}


@dataclass(frozen=True)
class DamageVariationDifferentialCase:
    name: str
    initial_damage: int
    rng_values: tuple[int, ...]


@dataclass(frozen=True)
class TurnOrderDifferentialCase:
    name: str
    player_move_id: int
    enemy_move_id: int
    player_priority: int
    enemy_priority: int
    player_speed: int
    enemy_speed: int
    rng_values: tuple[int, ...] = ()
    link_mode: int = LINK_NULL
    serial_status: int = SERIAL_NOT_CONNECTED
    player_item: int = 0
    enemy_item: int = 0


@dataclass(frozen=True)
class AccuracyDifferentialCase:
    name: str
    actor: str
    accuracy: int
    rng_values: tuple[int, ...]
    accuracy_level: int = NEUTRAL_STAT_LEVEL
    evasion_level: int = NEUTRAL_STAT_LEVEL
    move_id: int = MOVE_TACKLE
    move_effect: int = EFFECT_NORMAL_HIT
    weather: int = 0
    attacker_x_accuracy: bool = False
    target_lock_on: bool = False
    target_protect: bool = False
    target_flying: bool = False
    target_underground: bool = False
    target_item: int = 0


@dataclass(frozen=True)
class CriticalDifferentialCase:
    name: str
    actor: str
    move_id: int
    rng_values: tuple[int, ...]
    move_name: str
    move_power: int = 40
    species: int = SPECIES_PIDGEY
    species_name: str = "PIDGEY"
    item: int = 0
    focus_energy: bool = False


@dataclass(frozen=True)
class BossAiSelectorDifferentialCase:
    name: str
    tier: int | str
    move_ids: tuple[int, int, int, int]
    scores: tuple[int, int, int, int]


@dataclass(frozen=True)
class AfterHitDifferentialCase:
    name: str
    actor: str
    cur_damage: int
    player_hp: int
    player_max_hp: int
    enemy_hp: int
    enemy_max_hp: int
    player_item: int = 0
    enemy_item: int = 0
    contact: bool = True


@dataclass(frozen=True)
class DoubleDamageDifferentialCase:
    name: str
    command: str
    initial_damage: int
    actor: str = "player"
    target_flying: bool = False
    target_underground: bool = False


@dataclass(frozen=True)
class ResidualStatusDifferentialCase:
    name: str
    actor: str
    status: str
    hp: int
    max_hp: int
    toxic_count: int = 0


@dataclass(frozen=True)
class LeftoversDifferentialCase:
    name: str
    actor: str
    hp: int
    max_hp: int
    item: int = ITEM_LEFTOVERS


@dataclass(frozen=True)
class ParalysisTurnDifferentialCase:
    name: str
    actor: str
    rng_value: int
    types: tuple[str, str]


@dataclass(frozen=True)
class SleepTurnDifferentialCase:
    name: str
    actor: str
    sleep_turns: int
    move_id: int = MOVE_TACKLE
    move_name: str = "TACKLE"


@dataclass(frozen=True)
class FreezeTurnDifferentialCase:
    name: str
    actor: str
    move_id: int
    move_name: str


@dataclass(frozen=True)
class FlinchTurnDifferentialCase:
    name: str
    actor: str


@dataclass(frozen=True)
class StatusSpeedDifferentialCase:
    name: str
    actor: str
    speed: int
    status: str
    types: tuple[str, str]


DAMAGE_VARIATION_DIFFERENTIAL_CASES = (
    DamageVariationDifferentialCase("no_rng_for_one_damage", 1, (255,)),
    DamageVariationDifferentialCase("max_multiplier", 4, (255,)),
    DamageVariationDifferentialCase("accepted_mid_multiplier", 4, (187,)),
    DamageVariationDifferentialCase("reject_then_accept", 4, (0, 255)),
    DamageVariationDifferentialCase("reject_boundary_216_then_accept", 100, (177, 255)),
    DamageVariationDifferentialCase("accept_boundary_217", 100, (179,)),
    DamageVariationDifferentialCase("larger_damage_max", 100, (255,)),
    DamageVariationDifferentialCase("larger_damage_mid", 100, (187,)),
)


TURN_ORDER_DIFFERENTIAL_CASES = (
    TurnOrderDifferentialCase("nonlink_player_priority", MOVE_QUICK_ATTACK, MOVE_TACKLE, 2, 1, 5, 99),
    TurnOrderDifferentialCase("nonlink_enemy_priority", MOVE_TACKLE, MOVE_QUICK_ATTACK, 1, 2, 99, 5),
    TurnOrderDifferentialCase("nonlink_player_speed", MOVE_TACKLE, MOVE_TACKLE, 1, 1, 20, 10),
    TurnOrderDifferentialCase("nonlink_enemy_speed", MOVE_TACKLE, MOVE_TACKLE, 1, 1, 10, 20),
    TurnOrderDifferentialCase(
        "choice_scarf_enemy_speed",
        MOVE_TACKLE,
        MOVE_TACKLE,
        1,
        1,
        20,
        14,
        enemy_item=ITEM_CHOICE_SCARF,
    ),
    TurnOrderDifferentialCase(
        "quick_claw_player_success",
        MOVE_TACKLE,
        MOVE_TACKLE,
        1,
        1,
        5,
        99,
        rng_values=(0,),
        link_mode=LINK_COLOSSEUM,
        serial_status=SERIAL_NOT_CONNECTED,
        player_item=ITEM_QUICK_CLAW,
    ),
    TurnOrderDifferentialCase(
        "quick_claw_player_fail_speed",
        MOVE_TACKLE,
        MOVE_TACKLE,
        1,
        1,
        5,
        99,
        rng_values=(60,),
        link_mode=LINK_COLOSSEUM,
        serial_status=SERIAL_NOT_CONNECTED,
        player_item=ITEM_QUICK_CLAW,
    ),
    TurnOrderDifferentialCase(
        "both_quick_claw_enemy_success_default_role",
        MOVE_TACKLE,
        MOVE_TACKLE,
        1,
        1,
        99,
        5,
        rng_values=(0,),
        link_mode=LINK_COLOSSEUM,
        serial_status=SERIAL_NOT_CONNECTED,
        player_item=ITEM_QUICK_CLAW,
        enemy_item=ITEM_QUICK_CLAW,
    ),
    TurnOrderDifferentialCase(
        "both_quick_claw_enemy_fail_player_success_default_role",
        MOVE_TACKLE,
        MOVE_TACKLE,
        1,
        1,
        99,
        5,
        rng_values=(60, 0),
        link_mode=LINK_COLOSSEUM,
        serial_status=SERIAL_NOT_CONNECTED,
        player_item=ITEM_QUICK_CLAW,
        enemy_item=ITEM_QUICK_CLAW,
    ),
    TurnOrderDifferentialCase(
        "default_role_speed_tie_player_rng",
        MOVE_TACKLE,
        MOVE_TACKLE,
        1,
        1,
        10,
        10,
        (0,),
        LINK_COLOSSEUM,
        SERIAL_NOT_CONNECTED,
    ),
    TurnOrderDifferentialCase(
        "default_role_speed_tie_enemy_rng",
        MOVE_TACKLE,
        MOVE_TACKLE,
        1,
        1,
        10,
        10,
        (128,),
        LINK_COLOSSEUM,
        SERIAL_NOT_CONNECTED,
    ),
)


ACCURACY_DIFFERENTIAL_CASES = (
    AccuracyDifferentialCase("player_perfect_accuracy", "player", 255, (0,)),
    AccuracyDifferentialCase("player_half_accuracy_hit", "player", 128, (0,)),
    AccuracyDifferentialCase("player_half_accuracy_miss", "player", 128, (128,)),
    AccuracyDifferentialCase("player_minimum_accuracy_hit", "player", 0, (0,)),
    AccuracyDifferentialCase("player_minimum_accuracy_miss", "player", 0, (1,)),
    AccuracyDifferentialCase("enemy_half_accuracy_hit", "enemy", 128, (0,)),
    AccuracyDifferentialCase("enemy_half_accuracy_miss", "enemy", 128, (128,)),
    AccuracyDifferentialCase("player_accuracy_minus_one_can_miss", "player", 255, (191,), accuracy_level=6),
    AccuracyDifferentialCase("player_target_evasion_plus_one_can_miss", "player", 255, (191,), evasion_level=8),
    AccuracyDifferentialCase("enemy_accuracy_plus_one_caps_perfect", "enemy", 200, (), accuracy_level=8),
    AccuracyDifferentialCase(
        "player_always_hit_ignores_stages",
        "player",
        1,
        (),
        accuracy_level=1,
        evasion_level=13,
        move_effect=EFFECT_ALWAYS_HIT,
    ),
    AccuracyDifferentialCase(
        "player_brightpowder_turns_perfect_accuracy_into_miss_chance",
        "player",
        255,
        (235,),
        target_item=ITEM_BRIGHTPOWDER,
    ),
    AccuracyDifferentialCase(
        "enemy_x_accuracy_forces_hit_without_rng",
        "enemy",
        1,
        (),
        attacker_x_accuracy=True,
    ),
    AccuracyDifferentialCase(
        "player_lock_on_forces_hit_and_clears_target_flag",
        "player",
        1,
        (),
        target_lock_on=True,
    ),
    AccuracyDifferentialCase(
        "player_thunder_rain_forces_hit_without_rng",
        "player",
        1,
        (),
        move_id=MOVE_THUNDER,
        move_effect=EFFECT_THUNDER,
        weather=WEATHER_RAIN,
    ),
    AccuracyDifferentialCase(
        "player_flying_target_blocks_tackle_without_rng",
        "player",
        255,
        (),
        target_flying=True,
    ),
    AccuracyDifferentialCase(
        "player_gust_can_hit_flying_target",
        "player",
        255,
        (),
        move_id=MOVE_GUST,
        target_flying=True,
    ),
    AccuracyDifferentialCase(
        "player_underground_target_blocks_tackle_without_rng",
        "player",
        255,
        (),
        target_underground=True,
    ),
    AccuracyDifferentialCase(
        "player_earthquake_can_hit_underground_target",
        "player",
        255,
        (),
        move_id=MOVE_EARTHQUAKE,
        target_underground=True,
    ),
    AccuracyDifferentialCase(
        "player_lock_on_flying_ground_exception_clears_then_misses",
        "player",
        255,
        (),
        move_id=MOVE_EARTHQUAKE,
        target_lock_on=True,
        target_flying=True,
    ),
)


CRITICAL_DIFFERENTIAL_CASES = (
    CriticalDifferentialCase("base_raw_zero_crits", "player", MOVE_TACKLE, (0,), "TACKLE"),
    CriticalDifferentialCase("base_threshold_raw_misses", "player", MOVE_TACKLE, (17,), "TACKLE"),
    CriticalDifferentialCase("enemy_base_raw_zero_crits", "enemy", MOVE_TACKLE, (0,), "TACKLE"),
    CriticalDifferentialCase("slash_threshold_63_crits", "player", MOVE_SLASH, (63,), "SLASH"),
    CriticalDifferentialCase("slash_threshold_64_misses", "player", MOVE_SLASH, (64,), "SLASH"),
    CriticalDifferentialCase(
        "focus_energy_threshold_31_crits",
        "player",
        MOVE_TACKLE,
        (31,),
        "TACKLE",
        focus_energy=True,
    ),
    CriticalDifferentialCase(
        "scope_lens_threshold_31_crits",
        "player",
        MOVE_TACKLE,
        (31,),
        "TACKLE",
        item=ITEM_SCOPE_LENS,
    ),
    CriticalDifferentialCase(
        "chansey_lucky_punch_threshold_63_crits",
        "player",
        MOVE_TACKLE,
        (63,),
        "TACKLE",
        species=SPECIES_CHANSEY,
        species_name="CHANSEY",
        item=ITEM_LUCKY_PUNCH,
    ),
    CriticalDifferentialCase(
        "farfetchd_stick_threshold_63_crits",
        "player",
        MOVE_TACKLE,
        (63,),
        "TACKLE",
        species=SPECIES_FARFETCH_D,
        species_name="FARFETCH_D",
        item=ITEM_STICK,
    ),
    CriticalDifferentialCase(
        "level_cap_threshold_127_crits",
        "player",
        MOVE_SLASH,
        (127,),
        "SLASH",
        item=ITEM_SCOPE_LENS,
        focus_energy=True,
    ),
    CriticalDifferentialCase("zero_power_consumes_no_rng", "player", MOVE_TACKLE, (), "TACKLE", move_power=0),
)


BOSS_AI_SELECTOR_DIFFERENTIAL_CASES = (
    BossAiSelectorDifferentialCase("single_legal_first_slot", "late", (33, 52, 0, 0), (20, 80, 80, 80)),
    BossAiSelectorDifferentialCase("blank_stops_after_first_slot", "late", (33, 0, 52, 0), (20, 1, 1, 80)),
    BossAiSelectorDifferentialCase("no_legal_move", "late", (33, 52, 55, 0), (80, 80, 80, 80)),
)


AFTER_HIT_DIFFERENTIAL_CASES = (
    AfterHitDifferentialCase(
        "player_contact_rocky_helmet",
        "player",
        16,
        30,
        30,
        30,
        30,
        enemy_item=ITEM_ROCKY_HELMET,
    ),
    AfterHitDifferentialCase(
        "player_shell_bell_heal",
        "player",
        16,
        10,
        30,
        30,
        30,
        player_item=ITEM_SHELL_BELL,
    ),
    AfterHitDifferentialCase(
        "player_life_orb_recoil",
        "player",
        16,
        30,
        30,
        30,
        30,
        player_item=ITEM_LIFE_ORB,
    ),
    AfterHitDifferentialCase(
        "enemy_contact_rocky_helmet",
        "enemy",
        16,
        30,
        30,
        30,
        30,
        player_item=ITEM_ROCKY_HELMET,
    ),
)


DOUBLE_DAMAGE_DIFFERENTIAL_CASES = (
    DoubleDamageDifferentialCase(
        "double_flying_no_status_noop",
        "BattleCommand_DoubleFlyingDamage",
        100,
    ),
    DoubleDamageDifferentialCase(
        "double_flying_target_flying",
        "BattleCommand_DoubleFlyingDamage",
        100,
        target_flying=True,
    ),
    DoubleDamageDifferentialCase(
        "double_underground_no_status_noop",
        "BattleCommand_DoubleUndergroundDamage",
        100,
    ),
    DoubleDamageDifferentialCase(
        "double_underground_target_underground",
        "BattleCommand_DoubleUndergroundDamage",
        100,
        target_underground=True,
    ),
    DoubleDamageDifferentialCase(
        "double_damage_caps_ffff",
        "BattleCommand_DoubleFlyingDamage",
        0x9000,
        target_flying=True,
    ),
)


RESIDUAL_STATUS_DIFFERENTIAL_CASES = (
    ResidualStatusDifferentialCase("player_poison_eighth", "player", "poison", 40, 64),
    ResidualStatusDifferentialCase("enemy_burn_eighth", "enemy", "burn", 20, 33),
    ResidualStatusDifferentialCase("player_toxic_first_tick", "player", "toxic", 40, 64),
    ResidualStatusDifferentialCase("player_toxic_existing_count", "player", "toxic", 40, 64, toxic_count=2),
    ResidualStatusDifferentialCase("enemy_poison_minimum_chip", "enemy", "poison", 3, 5),
    ResidualStatusDifferentialCase("player_toxic_faints", "player", "toxic", 3, 64),
)


LEFTOVERS_DIFFERENTIAL_CASES = (
    LeftoversDifferentialCase("player_leftovers_heals", "player", 40, 64),
    LeftoversDifferentialCase("enemy_leftovers_heals", "enemy", 20, 33),
    LeftoversDifferentialCase("player_leftovers_minimum_heal", "player", 2, 5),
    LeftoversDifferentialCase("player_leftovers_full_hp_noop", "player", 64, 64),
    LeftoversDifferentialCase("player_no_item_noop", "player", 40, 64, item=0),
)


PARALYSIS_TURN_DIFFERENTIAL_CASES = (
    ParalysisTurnDifferentialCase("player_baseline_blocks", "player", 0, ("NORMAL", "NORMAL")),
    ParalysisTurnDifferentialCase("player_baseline_passes", "player", 63, ("NORMAL", "NORMAL")),
    ParalysisTurnDifferentialCase("player_half_fighting_blocks", "player", 50, ("FIGHTING", "NORMAL")),
    ParalysisTurnDifferentialCase("player_half_fighting_passes", "player", 51, ("FIGHTING", "NORMAL")),
    ParalysisTurnDifferentialCase("player_full_fighting_blocks", "player", 37, ("FIGHTING", "FIGHTING")),
    ParalysisTurnDifferentialCase("player_full_fighting_passes", "player", 38, ("FIGHTING", "FIGHTING")),
    ParalysisTurnDifferentialCase("enemy_baseline_blocks", "enemy", 0, ("NORMAL", "NORMAL")),
)


SLEEP_TURN_DIFFERENTIAL_CASES = (
    SleepTurnDifferentialCase("player_fast_asleep_blocks", "player", 2),
    SleepTurnDifferentialCase("player_wakes_and_continues", "player", 1),
    SleepTurnDifferentialCase("enemy_fast_asleep_blocks", "enemy", 2),
)


FREEZE_TURN_DIFFERENTIAL_CASES = (
    FreezeTurnDifferentialCase("player_frozen_blocks", "player", MOVE_TACKLE, "TACKLE"),
    FreezeTurnDifferentialCase("enemy_frozen_blocks", "enemy", MOVE_TACKLE, "TACKLE"),
    FreezeTurnDifferentialCase("player_flame_wheel_bypasses", "player", MOVE_FLAME_WHEEL, "FLAME_WHEEL"),
    FreezeTurnDifferentialCase("enemy_sacred_fire_bypasses", "enemy", MOVE_SACRED_FIRE, "SACRED_FIRE"),
)


FLINCH_TURN_DIFFERENTIAL_CASES = (
    FlinchTurnDifferentialCase("player_flinch_blocks_and_clears", "player"),
    FlinchTurnDifferentialCase("enemy_flinch_blocks_and_clears", "enemy"),
)


STATUS_SPEED_DIFFERENTIAL_CASES = (
    StatusSpeedDifferentialCase("player_no_status_normal_speed", "player", 100, "none", ("NORMAL", "NORMAL")),
    StatusSpeedDifferentialCase("enemy_electric_half_speed", "enemy", 40, "none", ("ELECTRIC", "NORMAL")),
    StatusSpeedDifferentialCase("player_electric_full_speed", "player", 40, "none", ("ELECTRIC", "ELECTRIC")),
    StatusSpeedDifferentialCase("player_paralysis_baseline_speed", "player", 100, "paralysis", ("NORMAL", "NORMAL")),
    StatusSpeedDifferentialCase("player_paralysis_half_fighting_speed", "player", 100, "paralysis", ("FIGHTING", "NORMAL")),
    StatusSpeedDifferentialCase("enemy_paralysis_full_fighting_speed", "enemy", 100, "paralysis", ("FIGHTING", "FIGHTING")),
    StatusSpeedDifferentialCase("player_electric_half_then_paralysis_speed", "player", 80, "paralysis", ("ELECTRIC", "FIGHTING")),
)


def python_damage_variation_result(initial_damage: int, rng_values: Iterable[int]) -> dict[str, Any]:
    rng = RngConfig(mode="fixed", values=tuple(rng_values))
    rng_stream = RngStream(rng)
    damage, trace, _branch = damage_variation_options(initial_damage, rng, rng_stream)[0]
    return {
        "damage": damage,
        "rng_count": rng_stream.index,
        "rng_trace": trace,
    }


def python_residual_status_result(case: ResidualStatusDifferentialCase) -> dict[str, Any]:
    result = residual_status_damage_result(
        case.status,
        hp=case.hp,
        max_hp=case.max_hp,
        toxic_count=case.toxic_count,
    )
    if result is None:
        raise AssertionError(f"residual status case {case.name!r} produced no result")
    return {
        "hp": result["hp_after"],
        "damage": result["damage"],
        "toxic_count": result["toxic_count_after"],
    }


def python_leftovers_result(case: LeftoversDifferentialCase) -> dict[str, Any]:
    if case.item != ITEM_LEFTOVERS or case.hp <= 0 or case.hp >= case.max_hp:
        return {
            "hp": case.hp,
            "healed": 0,
        }
    result = leftovers_heal_result(case.hp, case.max_hp)
    return {
        "hp": result["hp_after"],
        "healed": result["healed"],
    }


def python_paralysis_turn_result(case: ParalysisTurnDifferentialCase) -> dict[str, Any]:
    pokemon = _pokemon_for_paralysis(case)
    rng = RngConfig(mode="fixed", values=(case.rng_value,))
    rng_stream = RngStream(rng)
    blocked, trace, _branch = paralysis_turn_options(pokemon, rng, rng_stream)[0]
    return {
        "blocked": blocked,
        "threshold": trace[0]["threshold"],
        "rng_count": rng_stream.index,
    }


def python_sleep_turn_result(case: SleepTurnDifferentialCase) -> dict[str, Any]:
    pokemon = _pokemon_for_sleep(case)
    result = sleep_turn_options(pokemon, pokemon.moves[0])[0]
    return {
        "blocked": result["blocked"],
        "reason": result["reason"],
        "status_after": result["status_after"],
        "sleep_turns_after": result["sleep_turns_after"],
    }


def python_freeze_turn_result(case: FreezeTurnDifferentialCase) -> dict[str, Any]:
    pokemon = _pokemon_for_freeze(case)
    result = freeze_turn_result(pokemon, pokemon.moves[0])
    return {
        "blocked": result["blocked"],
        "reason": result["reason"],
        "status_after": result["status_after"],
    }


def python_flinch_turn_result(case: FlinchTurnDifferentialCase) -> dict[str, Any]:
    pokemon = _pokemon_for_flinch(case)
    result = flinch_turn_result(pokemon)
    return {
        "blocked": result["blocked"],
        "reason": result["reason"],
        "flinched_after": result["flinched_after"],
    }


def python_status_speed_result(case: StatusSpeedDifferentialCase) -> dict[str, Any]:
    pokemon = _pokemon_for_status_speed(case)
    return {
        "speed": status_adjusted_speed(pokemon),
    }


def python_accuracy_result(
    accuracy: int,
    rng_values: Iterable[int],
    *,
    accuracy_level: int = NEUTRAL_STAT_LEVEL,
    evasion_level: int = NEUTRAL_STAT_LEVEL,
    move_id: int = MOVE_TACKLE,
    move_effect: int = EFFECT_NORMAL_HIT,
    weather: int = 0,
    attacker_x_accuracy: bool = False,
    target_lock_on: bool = False,
    target_protect: bool = False,
    target_flying: bool = False,
    target_underground: bool = False,
    target_item: int = 0,
) -> dict[str, Any]:
    if target_protect:
        return {
            "hit": False,
            "rng_count": 0,
            "rng_trace": [],
            "target_lock_on_after": target_lock_on,
        }
    if target_lock_on and not (target_flying and move_id in UNDERGROUND_TARGET_HIT_MOVE_IDS):
        return {
            "hit": True,
            "rng_count": 0,
            "rng_trace": [],
            "target_lock_on_after": False,
        }
    target_lock_on_after = False if target_lock_on else target_lock_on
    if target_flying and move_id not in FLYING_TARGET_HIT_MOVE_IDS:
        return {
            "hit": False,
            "rng_count": 0,
            "rng_trace": [],
            "target_lock_on_after": target_lock_on_after,
        }
    if target_underground and move_id not in UNDERGROUND_TARGET_HIT_MOVE_IDS:
        return {
            "hit": False,
            "rng_count": 0,
            "rng_trace": [],
            "target_lock_on_after": target_lock_on_after,
        }
    if (move_effect == EFFECT_THUNDER and weather == WEATHER_RAIN) or attacker_x_accuracy or move_effect == EFFECT_ALWAYS_HIT:
        return {
            "hit": True,
            "rng_count": 0,
            "rng_trace": [],
            "target_lock_on_after": target_lock_on_after,
        }
    threshold = effective_accuracy_threshold(accuracy, accuracy_level, evasion_level)
    if target_item == ITEM_BRIGHTPOWDER:
        threshold = max(0, threshold - 20)
    rng = RngConfig(mode="fixed", values=tuple(rng_values))
    rng_stream = RngStream(rng)
    hit, trace, _branch = accuracy_options(
        accuracy,
        rng,
        rng_stream,
        threshold_override=threshold,
        accuracy_level=accuracy_level,
        evasion_level=evasion_level,
    )[0]
    return {
        "hit": hit,
        "rng_count": rng_stream.index,
        "rng_trace": trace,
        "target_lock_on_after": target_lock_on_after,
    }


def python_critical_result(case: CriticalDifferentialCase) -> dict[str, Any]:
    attacker = PokemonState(
        side=case.actor,
        name=case.species_name,
        level=5,
        hp=1,
        max_hp=1,
        types=(0, 0),
        type_names=("NORMAL", "NORMAL"),
        attack=1,
        defense=1,
        speed=1,
        sp_attack=1,
        sp_defense=1,
        item=case.item,
        focus_energy=case.focus_energy,
    )
    move = MoveState(
        name=case.move_name,
        move_type=0,
        move_type_name="NORMAL",
        bp=case.move_power,
        move_id=case.move_id,
        priority=1,
        accuracy=255,
    )
    level = move_critical_level(move, attacker)
    if case.move_power <= 0:
        return {
            "critical": False,
            "rng_count": 0,
            "rng_trace": [],
            "critical_level": level,
        }
    rng = RngConfig(mode="fixed", values=case.rng_values)
    rng_stream = RngStream(rng)
    critical, trace, _branch = critical_options(move, attacker, rng, rng_stream)[0]
    return {
        "critical": critical,
        "rng_count": rng_stream.index,
        "rng_trace": trace,
        "critical_level": level,
    }


def python_turn_order_result(case: TurnOrderDifferentialCase) -> dict[str, Any]:
    state = BattleState(
        player=_pokemon_for_turn_order("player", case.player_speed, case.player_priority, case.player_item),
        enemy=_pokemon_for_turn_order("enemy", case.enemy_speed, case.enemy_priority, case.enemy_item),
    )
    rng = RngConfig(mode="fixed", values=case.rng_values)
    rng_stream = RngStream(rng)
    actions = {
        "player": ActionState(kind="move", move_index=0),
        "enemy": ActionState(kind="move", move_index=0),
    }
    option = turn_order_options(state, actions, rng, rng_stream)[0]
    return {
        "order": list(option["turn_order"]),
        "rng_count": rng_stream.index,
        "rng_trace": option["rng_trace"],
    }


def python_boss_ai_selector_result(case: BossAiSelectorDifferentialCase) -> dict[str, Any]:
    result = rom_scenarios.select_from_score_bytes(
        scenario_id=case.name,
        tier=case.tier,
        move_ids=list(case.move_ids),
        scores=list(case.scores),
    )
    return {
        "ready": bool(result.get("ready", False)),
        "selected_slot_index": result.get("best_slot_index"),
        "selected_move_id": result.get("best_move_id"),
        "possible_slot_indices": result.get("possible_slot_indices", []),
        "reason": result.get("reason", ""),
    }


def python_after_hit_result(case: AfterHitDifferentialCase) -> dict[str, Any]:
    state = BattleState(
        player=_pokemon_for_after_hit(
            "player",
            case.player_hp,
            case.player_max_hp,
            case.player_item,
        ),
        enemy=_pokemon_for_after_hit(
            "enemy",
            case.enemy_hp,
            case.enemy_max_hp,
            case.enemy_item,
        ),
    )
    branch = {
        "state": state,
        "events": [],
        "rng_trace": [],
        "turn_order": [],
        "turns": [],
        "branch_path": [],
    }
    move = MoveState(
        name="TACKLE" if case.contact else "EMBER",
        move_type=0,
        move_type_name="NORMAL",
        bp=40,
        move_id=MOVE_TACKLE,
        priority=1,
        accuracy=255,
        contact=case.contact,
    )
    result = apply_after_hit_effects(branch, case.actor, move, case.cur_damage)
    return {
        "player_hp": result["state"].player.hp,
        "enemy_hp": result["state"].enemy.hp,
        "events": [
            {
                "type": event["type"],
                "actor": event["actor"],
                "item": event.get("item"),
                "hp_after": event.get("hp_after"),
            }
            for event in result["events"]
        ],
    }


def python_double_damage_result(case: DoubleDamageDifferentialCase) -> dict[str, Any]:
    should_double = (
        case.command == "BattleCommand_DoubleFlyingDamage"
        and case.target_flying
    ) or (
        case.command == "BattleCommand_DoubleUndergroundDamage"
        and case.target_underground
    )
    return {
        "damage": double_damage(case.initial_damage) if should_double else case.initial_damage,
    }


def _pokemon_for_turn_order(side: str, speed: int, priority: int, item: int = 0) -> PokemonState:
    return PokemonState(
        side=side,
        name=side.upper(),
        level=5,
        hp=1,
        max_hp=1,
        types=(0, 0),
        type_names=("NORMAL", "NORMAL"),
        attack=1,
        defense=1,
        speed=speed,
        sp_attack=1,
        sp_defense=1,
        item=item,
        moves=(
            MoveState(
                name="TURN_ORDER",
                move_type=0,
                move_type_name="NORMAL",
                bp=0,
                priority=priority,
            ),
        ),
    )


def _pokemon_for_after_hit(side: str, hp: int, max_hp: int, item: int) -> PokemonState:
    return PokemonState(
        side=side,
        name=side.upper(),
        level=5,
        hp=hp,
        max_hp=max_hp,
        types=(0, 0),
        type_names=("NORMAL", "NORMAL"),
        attack=1,
        defense=1,
        speed=1,
        sp_attack=1,
        sp_defense=1,
        item=item,
        moves=(
            MoveState(
                name="TACKLE",
                move_type=0,
                move_type_name="NORMAL",
                bp=40,
                move_id=MOVE_TACKLE,
                priority=1,
                contact=True,
            ),
        ),
    )


def _pokemon_for_paralysis(case: ParalysisTurnDifferentialCase) -> PokemonState:
    type_constants = tables.load_type_constants()
    type_ids = tuple(type_constants[name] for name in case.types)
    return PokemonState(
        side=case.actor,
        name=case.actor.upper(),
        level=5,
        hp=20,
        max_hp=20,
        types=type_ids,
        type_names=case.types,
        attack=1,
        defense=1,
        speed=1,
        sp_attack=1,
        sp_defense=1,
        status="paralysis",
        moves=(
            MoveState(
                name="TACKLE",
                move_type=0,
                move_type_name="NORMAL",
                bp=40,
                move_id=MOVE_TACKLE,
                priority=1,
            ),
        ),
    )


def _pokemon_for_sleep(case: SleepTurnDifferentialCase) -> PokemonState:
    return PokemonState(
        side=case.actor,
        name=case.actor.upper(),
        level=5,
        hp=20,
        max_hp=20,
        types=(0, 0),
        type_names=("NORMAL", "NORMAL"),
        attack=1,
        defense=1,
        speed=1,
        sp_attack=1,
        sp_defense=1,
        status="sleep",
        sleep_turns=case.sleep_turns,
        moves=(
            MoveState(
                name=case.move_name,
                move_type=0,
                move_type_name="NORMAL",
                bp=40,
                move_id=case.move_id,
                priority=1,
            ),
        ),
    )


def _pokemon_for_freeze(case: FreezeTurnDifferentialCase) -> PokemonState:
    return PokemonState(
        side=case.actor,
        name=case.actor.upper(),
        level=5,
        hp=20,
        max_hp=20,
        types=(0, 0),
        type_names=("NORMAL", "NORMAL"),
        attack=1,
        defense=1,
        speed=1,
        sp_attack=1,
        sp_defense=1,
        status="freeze",
        moves=(
            MoveState(
                name=case.move_name,
                move_type=0,
                move_type_name="NORMAL",
                bp=40,
                move_id=case.move_id,
                priority=1,
            ),
        ),
    )


def _pokemon_for_flinch(case: FlinchTurnDifferentialCase) -> PokemonState:
    return PokemonState(
        side=case.actor,
        name=case.actor.upper(),
        level=5,
        hp=20,
        max_hp=20,
        types=(0, 0),
        type_names=("NORMAL", "NORMAL"),
        attack=1,
        defense=1,
        speed=1,
        sp_attack=1,
        sp_defense=1,
        flinched=True,
        moves=(
            MoveState(
                name="TACKLE",
                move_type=0,
                move_type_name="NORMAL",
                bp=40,
                move_id=MOVE_TACKLE,
                priority=1,
            ),
        ),
    )


def _pokemon_for_status_speed(case: StatusSpeedDifferentialCase) -> PokemonState:
    type_constants = tables.load_type_constants()
    type_ids = tuple(type_constants[name] for name in case.types)
    return PokemonState(
        side=case.actor,
        name=case.actor.upper(),
        level=5,
        hp=20,
        max_hp=20,
        types=type_ids,
        type_names=case.types,
        attack=1,
        defense=1,
        speed=case.speed,
        sp_attack=1,
        sp_defense=1,
        status=case.status,
        moves=(
            MoveState(
                name="TACKLE",
                move_type=0,
                move_type_name="NORMAL",
                bp=40,
                move_id=MOVE_TACKLE,
                priority=1,
            ),
        ),
    )


def run_damage_variation_differential(
    cases: Iterable[DamageVariationDifferentialCase] = DAMAGE_VARIATION_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        call_function_safe,
        read_be_u16_banked,
        read_byte_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()

    def write_byte(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, value, bank)

    def write_u16(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, (value >> 8) & 0xFF, bank)
        write_byte_banked(pyboy, address + 1, value & 0xFF, bank)

    def read_byte(name: str) -> int:
        bank, address = syms[name]
        return read_byte_banked(pyboy, address, bank)

    def read_u16(name: str) -> int:
        bank, address = syms[name]
        return read_be_u16_banked(pyboy, address, bank)

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_damage_variation_result(case.initial_damage, case.rng_values)
            cache.restore()
            write_u16("wCurDamage", case.initial_damage)
            write_byte("wLinkMode", LINK_COLOSSEUM)
            write_byte("wLinkBattleRNCount", 0)
            rng_bank, rng_address = syms["wLinkBattleRNs"]
            padded_values = list(case.rng_values) + [255] * SERIAL_RNS_LENGTH
            for offset, raw in enumerate(padded_values[:SERIAL_RNS_LENGTH]):
                write_byte_banked(pyboy, rng_address + offset, raw, rng_bank)

            ticks, returned, post_pc = call_function_safe(
                pyboy,
                syms,
                "BattleCommand_DamageVariation",
                budget=4800,
            )
            actual = {
                "damage": read_u16("wCurDamage"),
                "rng_count": read_byte("wLinkBattleRNCount"),
                "returned": returned,
                "before_link_rng_rollover": read_byte("wLinkBattleRNCount") < SERIAL_RNS_REGENERATION_BOUNDARY,
                "ticks": ticks,
                "post_pc": f"${post_pc:04x}",
            }
            rows.append(
                {
                    "case": case.name,
                    "initial_damage": case.initial_damage,
                    "rng_values": list(case.rng_values),
                    "python": expected,
                    "rom": actual,
                    "ok": (
                        returned
                        and actual["damage"] == expected["damage"]
                        and actual["rng_count"] == expected["rng_count"]
                        and actual["before_link_rng_rollover"]
                    ),
                }
            )
    finally:
        cache.stop()
    return rows


def run_accuracy_differential(
    cases: Iterable[AccuracyDifferentialCase] = ACCURACY_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        call_function_safe,
        read_be_u16_banked,
        read_byte_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()

    def write_byte(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, value, bank)

    def write_u16(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, (value >> 8) & 0xFF, bank)
        write_byte_banked(pyboy, address + 1, value & 0xFF, bank)

    def read_byte(name: str) -> int:
        bank, address = syms[name]
        return read_byte_banked(pyboy, address, bank)

    def read_u16(name: str) -> int:
        bank, address = syms[name]
        return read_be_u16_banked(pyboy, address, bank)

    def set_bit_byte(name: str, bit: int) -> None:
        write_byte(name, read_byte(name) | (1 << bit))

    def seed_neutral_hit_check(case: AccuracyDifferentialCase) -> None:
        for name in (
            "wAttackMissed",
            "wEffectFailed",
            "wBattleWeather",
            "wBattleMonStatus",
            "wEnemyMonStatus",
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
            write_byte(name, 0)
        for name in ("wPlayerAccLevel", "wEnemyEvaLevel", "wEnemyAccLevel", "wPlayerEvaLevel"):
            write_byte(name, 7)
        if case.actor == "player":
            write_byte("wPlayerAccLevel", case.accuracy_level)
            write_byte("wEnemyEvaLevel", case.evasion_level)
        else:
            write_byte("wEnemyAccLevel", case.accuracy_level)
            write_byte("wPlayerEvaLevel", case.evasion_level)
        for name in ("wBattleMonItem", "wEnemyMonItem"):
            write_byte(name, 0)
        if case.actor == "player":
            write_byte("wEnemyMonItem", case.target_item)
            if case.attacker_x_accuracy:
                set_bit_byte("wPlayerSubStatus4", SUBSTATUS_X_ACCURACY_BIT)
            if case.target_lock_on:
                set_bit_byte("wEnemySubStatus5", SUBSTATUS_LOCK_ON_BIT)
            if case.target_protect:
                set_bit_byte("wEnemySubStatus1", SUBSTATUS_PROTECT_BIT)
            if case.target_flying:
                set_bit_byte("wEnemySubStatus3", SUBSTATUS_FLYING_BIT)
            if case.target_underground:
                set_bit_byte("wEnemySubStatus3", SUBSTATUS_UNDERGROUND_BIT)
        else:
            write_byte("wBattleMonItem", case.target_item)
            if case.attacker_x_accuracy:
                set_bit_byte("wEnemySubStatus4", SUBSTATUS_X_ACCURACY_BIT)
            if case.target_lock_on:
                set_bit_byte("wPlayerSubStatus5", SUBSTATUS_LOCK_ON_BIT)
            if case.target_protect:
                set_bit_byte("wPlayerSubStatus1", SUBSTATUS_PROTECT_BIT)
            if case.target_flying:
                set_bit_byte("wPlayerSubStatus3", SUBSTATUS_FLYING_BIT)
            if case.target_underground:
                set_bit_byte("wPlayerSubStatus3", SUBSTATUS_UNDERGROUND_BIT)
        for name in ("wBattleMonType1", "wBattleMonType2", "wEnemyMonType1", "wEnemyMonType2"):
            write_byte(name, 0)
        write_byte("wBattleWeather", case.weather)
        write_byte("wLinkMode", LINK_COLOSSEUM)
        write_byte("hBattleTurn", 0 if case.actor == "player" else 1)
        write_byte("wLinkBattleRNCount", 0)
        rng_bank, rng_address = syms["wLinkBattleRNs"]
        padded_values = list(case.rng_values) + [255] * SERIAL_RNS_LENGTH
        for offset, raw in enumerate(padded_values[:SERIAL_RNS_LENGTH]):
            write_byte_banked(pyboy, rng_address + offset, raw, rng_bank)
        write_u16("wCurDamage", 4)
        write_byte("wPlayerMoveStructAnimation", case.move_id if case.actor == "player" else MOVE_TACKLE)
        write_byte("wPlayerMoveStructEffect", case.move_effect if case.actor == "player" else EFFECT_NORMAL_HIT)
        write_byte("wPlayerMoveStructPower", 40)
        write_byte("wPlayerMoveStructType", 0)
        write_byte("wPlayerMoveStructAccuracy", case.accuracy if case.actor == "player" else 255)
        write_byte("wEnemyMoveStructAnimation", case.move_id if case.actor == "enemy" else MOVE_TACKLE)
        write_byte("wEnemyMoveStructEffect", case.move_effect if case.actor == "enemy" else EFFECT_NORMAL_HIT)
        write_byte("wEnemyMoveStructPower", 40)
        write_byte("wEnemyMoveStructType", 0)
        write_byte("wEnemyMoveStructAccuracy", case.accuracy if case.actor == "enemy" else 255)

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_accuracy_result(
                case.accuracy,
                case.rng_values,
                accuracy_level=case.accuracy_level,
                evasion_level=case.evasion_level,
                move_id=case.move_id,
                move_effect=case.move_effect,
                weather=case.weather,
                attacker_x_accuracy=case.attacker_x_accuracy,
                target_lock_on=case.target_lock_on,
                target_protect=case.target_protect,
                target_flying=case.target_flying,
                target_underground=case.target_underground,
                target_item=case.target_item,
            )
            cache.restore()
            seed_neutral_hit_check(case)
            ticks, returned, post_pc = call_function_safe(
                pyboy,
                syms,
                "BattleCommand_CheckHit",
                budget=4800,
            )
            actual = {
                "hit": read_byte("wAttackMissed") == 0,
                "damage": read_u16("wCurDamage"),
                "rng_count": read_byte("wLinkBattleRNCount"),
                "target_lock_on_after": bool(
                    read_byte("wEnemySubStatus5" if case.actor == "player" else "wPlayerSubStatus5")
                    & (1 << SUBSTATUS_LOCK_ON_BIT)
                ),
                "returned": returned,
                "before_link_rng_rollover": read_byte("wLinkBattleRNCount") < SERIAL_RNS_REGENERATION_BOUNDARY,
                "ticks": ticks,
                "post_pc": f"${post_pc:04x}",
            }
            expected_damage = 4 if expected["hit"] else 0
            rows.append(
                {
                    "case": case.name,
                    "actor": case.actor,
                    "accuracy": case.accuracy,
                    "accuracy_level": case.accuracy_level,
                    "evasion_level": case.evasion_level,
                    "move_id": case.move_id,
                    "move_effect": case.move_effect,
                    "weather": case.weather,
                    "attacker_x_accuracy": case.attacker_x_accuracy,
                    "target_lock_on": case.target_lock_on,
                    "target_protect": case.target_protect,
                    "target_flying": case.target_flying,
                    "target_underground": case.target_underground,
                    "target_item": case.target_item,
                    "rng_values": list(case.rng_values),
                    "python": expected,
                    "rom": actual,
                    "ok": (
                        returned
                        and actual["hit"] == expected["hit"]
                        and actual["damage"] == expected_damage
                        and actual["rng_count"] == expected["rng_count"]
                        and actual["target_lock_on_after"] == expected["target_lock_on_after"]
                        and actual["before_link_rng_rollover"]
                    ),
                }
            )
    finally:
        cache.stop()
    return rows


def run_critical_differential(
    cases: Iterable[CriticalDifferentialCase] = CRITICAL_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        call_function_safe,
        read_byte_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()

    def write_byte(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, value, bank)

    def read_byte(name: str) -> int:
        bank, address = syms[name]
        return read_byte_banked(pyboy, address, bank)

    def set_bit_byte(name: str, bit: int) -> None:
        write_byte(name, read_byte(name) | (1 << bit))

    def seed_critical(case: CriticalDifferentialCase) -> None:
        for name in (
            "wCriticalHit",
            "wPlayerSubStatus4",
            "wEnemySubStatus4",
        ):
            write_byte(name, 0)
        write_byte("hBattleTurn", 0 if case.actor == "player" else 1)
        write_byte("wBattleMonSpecies", SPECIES_PIDGEY)
        write_byte("wEnemyMonSpecies", SPECIES_PIDGEY)
        write_byte("wBattleMonItem", 0)
        write_byte("wEnemyMonItem", 0)
        write_byte("wCurPlayerMove", MOVE_TACKLE)
        write_byte("wCurEnemyMove", MOVE_TACKLE)
        write_byte("wPlayerMoveStructAnimation", MOVE_TACKLE)
        write_byte("wEnemyMoveStructAnimation", MOVE_TACKLE)
        write_byte("wPlayerMoveStructPower", 40)
        write_byte("wEnemyMoveStructPower", 40)
        if case.actor == "player":
            write_byte("wBattleMonSpecies", case.species)
            write_byte("wBattleMonItem", case.item)
            write_byte("wCurPlayerMove", case.move_id)
            write_byte("wPlayerMoveStructAnimation", case.move_id)
            write_byte("wPlayerMoveStructPower", case.move_power)
            if case.focus_energy:
                set_bit_byte("wPlayerSubStatus4", SUBSTATUS_FOCUS_ENERGY_BIT)
        else:
            write_byte("wEnemyMonSpecies", case.species)
            write_byte("wEnemyMonItem", case.item)
            write_byte("wCurEnemyMove", case.move_id)
            write_byte("wEnemyMoveStructAnimation", case.move_id)
            write_byte("wEnemyMoveStructPower", case.move_power)
            if case.focus_energy:
                set_bit_byte("wEnemySubStatus4", SUBSTATUS_FOCUS_ENERGY_BIT)
        write_byte("wLinkMode", LINK_COLOSSEUM)
        write_byte("wLinkBattleRNCount", 0)
        rng_bank, rng_address = syms["wLinkBattleRNs"]
        padded_values = list(case.rng_values) + [255] * SERIAL_RNS_LENGTH
        for offset, raw in enumerate(padded_values[:SERIAL_RNS_LENGTH]):
            write_byte_banked(pyboy, rng_address + offset, raw, rng_bank)

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_critical_result(case)
            cache.restore()
            seed_critical(case)
            ticks, returned, post_pc = call_function_safe(
                pyboy,
                syms,
                "BattleCommand_Critical",
                budget=4800,
            )
            actual = {
                "critical": read_byte("wCriticalHit") != 0,
                "critical_value": read_byte("wCriticalHit"),
                "rng_count": read_byte("wLinkBattleRNCount"),
                "returned": returned,
                "before_link_rng_rollover": read_byte("wLinkBattleRNCount") < SERIAL_RNS_REGENERATION_BOUNDARY,
                "ticks": ticks,
                "post_pc": f"${post_pc:04x}",
            }
            rows.append(
                {
                    "case": case.name,
                    "actor": case.actor,
                    "move_id": case.move_id,
                    "move_power": case.move_power,
                    "species": case.species,
                    "item": case.item,
                    "focus_energy": case.focus_energy,
                    "rng_values": list(case.rng_values),
                    "python": expected,
                    "rom": actual,
                    "ok": (
                        returned
                        and actual["critical"] == expected["critical"]
                        and actual["rng_count"] == expected["rng_count"]
                        and actual["before_link_rng_rollover"]
                    ),
                }
            )
    finally:
        cache.stop()
    return rows


def run_turn_order_differential(
    cases: Iterable[TurnOrderDifferentialCase] = TURN_ORDER_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        call_function_safe,
        read_byte_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()

    def write_byte(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, value, bank)

    def write_u16(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, (value >> 8) & 0xFF, bank)
        write_byte_banked(pyboy, address + 1, value & 0xFF, bank)

    def read_byte(name: str) -> int:
        bank, address = syms[name]
        return read_byte_banked(pyboy, address, bank)

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_turn_order_result(case)
            cache.restore()
            write_byte("wLinkMode", case.link_mode)
            write_byte("hSerialConnectionStatus", case.serial_status)
            write_byte("wBattleAction", 0)
            write_byte("wBattlePlayerAction", 0)
            write_byte("wBattleMonItem", case.player_item)
            write_byte("wEnemyMonItem", case.enemy_item)
            write_byte("wCurPlayerMove", case.player_move_id)
            write_byte("wCurEnemyMove", case.enemy_move_id)
            write_u16("wBattleMonSpeed", case.player_speed)
            write_u16("wEnemyMonSpeed", case.enemy_speed)
            write_byte("wLinkBattleRNCount", 0)
            rng_bank, rng_address = syms["wLinkBattleRNs"]
            padded_values = list(case.rng_values) + [255] * SERIAL_RNS_LENGTH
            for offset, raw in enumerate(padded_values[:SERIAL_RNS_LENGTH]):
                write_byte_banked(pyboy, rng_address + offset, raw, rng_bank)

            ticks, returned, post_pc = call_function_safe(
                pyboy,
                syms,
                "DetermineMoveOrder",
                budget=4800,
            )
            flags = int(pyboy.register_file.F)
            carry = (flags >> 4) & 1
            actual = {
                "order": ["player", "enemy"] if carry else ["enemy", "player"],
                "rng_count": read_byte("wLinkBattleRNCount"),
                "returned": returned,
                "before_link_rng_rollover": read_byte("wLinkBattleRNCount") < SERIAL_RNS_REGENERATION_BOUNDARY,
                "ticks": ticks,
                "flags": f"${flags:02x}",
                "post_pc": f"${post_pc:04x}",
            }
            rows.append(
                {
                    "case": case.name,
                    "player_move_id": case.player_move_id,
                    "enemy_move_id": case.enemy_move_id,
                    "player_speed": case.player_speed,
                    "enemy_speed": case.enemy_speed,
                    "player_item": case.player_item,
                    "enemy_item": case.enemy_item,
                    "rng_values": list(case.rng_values),
                    "link_mode": case.link_mode,
                    "serial_status": case.serial_status,
                    "python": expected,
                    "rom": actual,
                    "ok": (
                        returned
                        and actual["order"] == expected["order"]
                        and actual["rng_count"] == expected["rng_count"]
                        and actual["before_link_rng_rollover"]
                    ),
                }
            )
    finally:
        cache.stop()
    return rows


def run_boss_ai_selector_differential(
    cases: Iterable[BossAiSelectorDifferentialCase] = BOSS_AI_SELECTOR_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        call_function_safe,
        read_byte_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()

    def write_byte(name: str, value: int, offset: int = 0) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address + offset, value, bank)

    def read_byte(name: str) -> int:
        bank, address = syms[name]
        return read_byte_banked(pyboy, address, bank)

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_boss_ai_selector_result(case)
            cache.restore()
            write_byte("wBossAITier", rom_scenarios.normalize_tier(case.tier))
            write_byte("wBossAIMoveChoiceReady", 0)
            write_byte("wCurEnemyMove", 0)
            write_byte("wCurEnemyMoveNum", 0)
            for index, move_id in enumerate(case.move_ids):
                write_byte("wEnemyMonMoves", move_id, index)
            for index, score in enumerate(case.scores):
                write_byte("wEnemyAIMoveScores", score, index)

            scores_bank, scores_address = syms["wEnemyAIMoveScores"]
            _moves_bank, moves_address = syms["wEnemyMonMoves"]
            if 0xD000 <= scores_address <= 0xDFFF and scores_bank:
                pyboy.memory[0xFF70] = scores_bank
            rf = pyboy.register_file
            rf.A = 0
            rf.B = 0xFF
            rf.C = 0xFF
            rf.HL = scores_address
            rf.D = (moves_address >> 8) & 0xFF
            rf.E = moves_address & 0xFF
            ticks, returned, post_pc = call_function_safe(
                pyboy,
                syms,
                "BossAI_SelectMove.first_pass",
                budget=4800,
            )
            ready = read_byte("wBossAIMoveChoiceReady") != 0
            selected_slot = read_byte("wCurEnemyMoveNum") if ready else None
            selected_move = read_byte("wCurEnemyMove") if ready else None
            actual = {
                "ready": ready,
                "selected_slot_index": selected_slot,
                "selected_move_id": selected_move,
                "returned": returned,
                "ticks": ticks,
                "post_pc": f"${post_pc:04x}",
            }
            rows.append(
                {
                    "case": case.name,
                    "tier": case.tier,
                    "move_ids": list(case.move_ids),
                    "scores": list(case.scores),
                    "python": expected,
                    "rom": actual,
                    "ok": (
                        returned
                        and actual["ready"] == expected["ready"]
                        and actual["selected_slot_index"] == expected["selected_slot_index"]
                        and actual["selected_move_id"] == expected["selected_move_id"]
                    ),
                }
            )
    finally:
        cache.stop()
    return rows


def run_double_damage_differential(
    cases: Iterable[DoubleDamageDifferentialCase] = DOUBLE_DAMAGE_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        call_function_safe,
        read_be_u16_banked,
        read_byte_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()

    def write_byte(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, value, bank)

    def write_u16(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, (value >> 8) & 0xFF, bank)
        write_byte_banked(pyboy, address + 1, value & 0xFF, bank)

    def read_u16(name: str) -> int:
        bank, address = syms[name]
        return read_be_u16_banked(pyboy, address, bank)

    def read_byte(name: str) -> int:
        bank, address = syms[name]
        return read_byte_banked(pyboy, address, bank)

    def set_bit_byte(name: str, bit: int) -> None:
        write_byte(name, read_byte(name) | (1 << bit))

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_double_damage_result(case)
            cache.restore()
            write_byte("hBattleTurn", 0 if case.actor == "player" else 1)
            write_byte("wPlayerSubStatus3", 0)
            write_byte("wEnemySubStatus3", 0)
            target_substatus = "wEnemySubStatus3" if case.actor == "player" else "wPlayerSubStatus3"
            if case.target_flying:
                set_bit_byte(target_substatus, SUBSTATUS_FLYING_BIT)
            if case.target_underground:
                set_bit_byte(target_substatus, SUBSTATUS_UNDERGROUND_BIT)
            write_u16("wCurDamage", case.initial_damage)
            ticks, returned, post_pc = call_function_safe(
                pyboy,
                syms,
                case.command,
                budget=500,
            )
            actual = {
                "damage": read_u16("wCurDamage"),
                "returned": returned,
                "ticks": ticks,
                "post_pc": f"${post_pc:04x}",
            }
            rows.append(
                {
                    "case": case.name,
                    "command": case.command,
                    "initial_damage": case.initial_damage,
                    "target_flying": case.target_flying,
                    "target_underground": case.target_underground,
                    "python": expected,
                    "rom": actual,
                    "ok": returned and actual["damage"] == expected["damage"],
                }
            )
    finally:
        cache.stop()
    return rows


def run_after_hit_differential(
    cases: Iterable[AfterHitDifferentialCase] = AFTER_HIT_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        call_function_safe,
        read_be_u16_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()

    def write_byte(name: str, value: int, offset: int = 0) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address + offset, value, bank)

    def write_u16(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, (value >> 8) & 0xFF, bank)
        write_byte_banked(pyboy, address + 1, value & 0xFF, bank)

    def read_u16(name: str) -> int:
        bank, address = syms[name]
        return read_be_u16_banked(pyboy, address, bank)

    def write_move_struct(name: str, move_id: int) -> None:
        for offset, value in enumerate((move_id, 0x00, 40, 0, 0xFF, 35, 0)):
            write_byte(name, value, offset)

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_after_hit_result(case)
            cache.restore()
            move_id = MOVE_TACKLE if case.contact else 0x34  # EMBER
            write_byte("hBattleTurn", 0 if case.actor == "player" else 1)
            write_byte("wAttackMissed", 0)
            write_byte("wCurPlayerMove", move_id)
            write_byte("wCurEnemyMove", move_id)
            write_move_struct("wPlayerMoveStruct", move_id)
            write_move_struct("wEnemyMoveStruct", move_id)
            write_u16("wCurDamage", case.cur_damage)
            write_u16("wBattleMonHP", case.player_hp)
            write_u16("wBattleMonMaxHP", case.player_max_hp)
            write_u16("wEnemyMonHP", case.enemy_hp)
            write_u16("wEnemyMonMaxHP", case.enemy_max_hp)
            write_byte("wBattleMonItem", case.player_item)
            write_byte("wEnemyMonItem", case.enemy_item)

            ticks, returned, post_pc = call_function_safe(
                pyboy,
                syms,
                "HandleLateGenAfterHitEffects_Far",
                budget=500,
            )
            actual = {
                "player_hp": read_u16("wBattleMonHP"),
                "enemy_hp": read_u16("wEnemyMonHP"),
                "returned": returned,
                "nonreturn_allowed": True,
                "ticks": ticks,
                "post_pc": f"${post_pc:04x}",
            }
            rows.append(
                {
                    "case": case.name,
                    "actor": case.actor,
                    "cur_damage": case.cur_damage,
                    "player_item": case.player_item,
                    "enemy_item": case.enemy_item,
                    "contact": case.contact,
                    "python": expected,
                    "rom": actual,
                    "ok": (
                        actual["player_hp"] == expected["player_hp"]
                        and actual["enemy_hp"] == expected["enemy_hp"]
                    ),
                }
            )
    finally:
        cache.stop()
    return rows


def run_residual_status_differential(
    cases: Iterable[ResidualStatusDifferentialCase] = RESIDUAL_STATUS_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        call_function_safe,
        read_be_u16_banked,
        read_byte_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()

    def write_byte(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, value, bank)

    def write_u16(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, (value >> 8) & 0xFF, bank)
        write_byte_banked(pyboy, address + 1, value & 0xFF, bank)

    def read_byte(name: str) -> int:
        bank, address = syms[name]
        return read_byte_banked(pyboy, address, bank)

    def read_u16(name: str) -> int:
        bank, address = syms[name]
        return read_be_u16_banked(pyboy, address, bank)

    def seed_residual_status(case: ResidualStatusDifferentialCase) -> None:
        for name in (
            "wBattleMonStatus",
            "wEnemyMonStatus",
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
            "wPlayerToxicCount",
            "wEnemyToxicCount",
            "wBattleAfterAnim",
        ):
            write_byte(name, 0)
        write_u16("wBattleMonHP", case.hp if case.actor == "player" else 40)
        write_u16("wBattleMonMaxHP", case.max_hp if case.actor == "player" else 64)
        write_u16("wEnemyMonHP", case.hp if case.actor == "enemy" else 40)
        write_u16("wEnemyMonMaxHP", case.max_hp if case.actor == "enemy" else 64)
        write_byte("hBattleTurn", 0 if case.actor == "player" else 1)

        status_name = "wBattleMonStatus" if case.actor == "player" else "wEnemyMonStatus"
        substatus5_name = "wPlayerSubStatus5" if case.actor == "player" else "wEnemySubStatus5"
        toxic_count_name = "wPlayerToxicCount" if case.actor == "player" else "wEnemyToxicCount"
        if case.status == "burn":
            write_byte(status_name, 1 << BRN_BIT)
        else:
            write_byte(status_name, 1 << PSN_BIT)
        if case.status == "toxic":
            write_byte(substatus5_name, 1 << SUBSTATUS_TOXIC_BIT)
        write_byte(toxic_count_name, case.toxic_count)

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_residual_status_result(case)
            cache.restore()
            seed_residual_status(case)
            eighth_ticks, eighth_returned, _post_pc = call_function_safe(
                pyboy,
                syms,
                "GetEighthMaxHP",
                budget=3000,
            )
            toxic_count_name = "wPlayerToxicCount" if case.actor == "player" else "wEnemyToxicCount"
            toxic_bank, toxic_address = syms[toxic_count_name]
            pyboy.register_file.D = (toxic_address >> 8) & 0xFF
            pyboy.register_file.E = toxic_address & 0xFF
            residual_ticks, residual_returned, residual_post_pc = call_function_safe(
                pyboy,
                syms,
                "ResidualDamage.check_toxic",
                budget=30000,
            )
            hp_name = "wBattleMonHP" if case.actor == "player" else "wEnemyMonHP"
            actual = {
                "hp": read_u16(hp_name),
                "damage": case.hp - read_u16(hp_name),
                "toxic_count": read_byte(toxic_count_name),
                "get_eighth_returned": eighth_returned,
                "get_eighth_ticks": eighth_ticks,
                "residual_returned": residual_returned,
                "residual_ticks": residual_ticks,
                "residual_post_pc": f"${residual_post_pc:04x}",
                "toxic_count_bank": toxic_bank,
            }
            rows.append(
                {
                    "case": case.name,
                    "actor": case.actor,
                    "status": case.status,
                    "hp": case.hp,
                    "max_hp": case.max_hp,
                    "toxic_count": case.toxic_count,
                    "python": expected,
                    "rom": actual,
                    "ok": (
                        eighth_returned
                        and actual["hp"] == expected["hp"]
                        and actual["damage"] == expected["damage"]
                        and actual["toxic_count"] == expected["toxic_count"]
                    ),
                }
            )
    finally:
        cache.stop()
    return rows


def run_leftovers_differential(
    cases: Iterable[LeftoversDifferentialCase] = LEFTOVERS_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        call_function_safe,
        read_be_u16_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()

    def write_byte(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, value, bank)

    def write_u16(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, (value >> 8) & 0xFF, bank)
        write_byte_banked(pyboy, address + 1, value & 0xFF, bank)

    def read_u16(name: str) -> int:
        bank, address = syms[name]
        return read_be_u16_banked(pyboy, address, bank)

    def seed_leftovers(case: LeftoversDifferentialCase) -> None:
        for name in (
            "wBattleMonItem",
            "wEnemyMonItem",
            "wBattleAfterAnim",
        ):
            write_byte(name, 0)
        write_u16("wBattleMonHP", case.hp if case.actor == "player" else 40)
        write_u16("wBattleMonMaxHP", case.max_hp if case.actor == "player" else 64)
        write_u16("wEnemyMonHP", case.hp if case.actor == "enemy" else 40)
        write_u16("wEnemyMonMaxHP", case.max_hp if case.actor == "enemy" else 64)
        write_byte("hBattleTurn", 0 if case.actor == "player" else 1)
        write_byte("wBattleMonItem" if case.actor == "player" else "wEnemyMonItem", case.item)

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_leftovers_result(case)
            cache.restore()
            seed_leftovers(case)
            ticks, returned, post_pc = call_function_safe(
                pyboy,
                syms,
                "HandleLeftovers.do_it",
                budget=30000,
            )
            hp_name = "wBattleMonHP" if case.actor == "player" else "wEnemyMonHP"
            actual_hp = read_u16(hp_name)
            actual = {
                "hp": actual_hp,
                "healed": actual_hp - case.hp,
                "returned": returned,
                "ticks": ticks,
                "post_pc": f"${post_pc:04x}",
            }
            rows.append(
                {
                    "case": case.name,
                    "actor": case.actor,
                    "hp": case.hp,
                    "max_hp": case.max_hp,
                    "item": case.item,
                    "python": expected,
                    "rom": actual,
                    "ok": (
                        actual["hp"] == expected["hp"]
                        and actual["healed"] == expected["healed"]
                    ),
                }
            )
    finally:
        cache.stop()
    return rows


def run_paralysis_turn_differential(
    cases: Iterable[ParalysisTurnDifferentialCase] = PARALYSIS_TURN_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        read_byte_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.safe_call import SENTINEL_ADDR
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    type_constants = tables.load_type_constants()
    fully_paralyzed_text = syms["FullyParalyzedText"][1]

    def write_byte(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, value, bank)

    def read_byte(name: str) -> int:
        bank, address = syms[name]
        return read_byte_banked(pyboy, address, bank)

    def seed_check_turn(case: ParalysisTurnDifferentialCase) -> None:
        for name in (
            "wTurnEnded",
            "wAttackMissed",
            "wEffectFailed",
            "wBattleAnimParam",
            "wAlreadyDisobeyed",
            "wAlreadyFailed",
            "wSomeoneIsRampaging",
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
            "wBattleMonStatus",
            "wEnemyMonStatus",
            "wPlayerDisableCount",
            "wEnemyDisableCount",
            "wDisabledMove",
            "wEnemyDisabledMove",
        ):
            write_byte(name, 0)
        write_byte("hBattleTurn", 0 if case.actor == "player" else 1)
        status_name = "wBattleMonStatus" if case.actor == "player" else "wEnemyMonStatus"
        write_byte(status_name, 1 << PAR_BIT)
        write_byte("wCurPlayerMove", MOVE_TACKLE)
        write_byte("wCurEnemyMove", MOVE_TACKLE)
        type1, type2 = (type_constants[name] for name in case.types)
        if case.actor == "player":
            write_byte("wBattleMonType1", type1)
            write_byte("wBattleMonType2", type2)
        else:
            write_byte("wEnemyMonType1", type1)
            write_byte("wEnemyMonType2", type2)
        write_byte("wLinkMode", LINK_COLOSSEUM)
        write_byte("wLinkBattleRNCount", 0)
        rng_bank, rng_address = syms["wLinkBattleRNs"]
        for offset, raw in enumerate([case.rng_value] + [255] * (SERIAL_RNS_LENGTH - 1)):
            write_byte_banked(pyboy, rng_address + offset, raw, rng_bank)

    def call_check_turn_until_text_or_return(budget: int = 20000) -> dict[str, Any]:
        text_hits: list[int] = []

        def on_text(_context) -> None:
            rf = pyboy.register_file
            text_hits.append(int(rf.HL) & 0xFFFF)

        text_bank, text_address = syms["StdBattleTextbox"]
        pyboy.hook_register(text_bank, text_address, on_text, None)
        try:
            pyboy.memory[SENTINEL_ADDR] = 0x18
            pyboy.memory[SENTINEL_ADDR + 1] = 0xFE
            rf = pyboy.register_file
            sp = int(rf.SP)
            new_sp = (sp - 2) & 0xFFFF
            pyboy.memory[new_sp] = SENTINEL_ADDR & 0xFF
            pyboy.memory[new_sp + 1] = (SENTINEL_ADDR >> 8) & 0xFF
            rf.SP = new_sp
            fn_bank, fn_address = syms["BattleCommand_CheckTurn"]
            rf.PC = fn_address
            rom_bank_sym = syms.get("hROMBank")
            if rom_bank_sym:
                pyboy.memory[rom_bank_sym[1]] = fn_bank
            pyboy.memory[0x2000] = fn_bank

            ticked = 0
            while ticked < budget:
                pyboy.tick(2, False, False)
                ticked += 2
                if text_hits:
                    return {
                        "returned": False,
                        "text_pointer": text_hits[-1],
                        "ticks": ticked,
                        "post_pc": int(rf.PC),
                    }
                pc = int(rf.PC)
                if pc == SENTINEL_ADDR or pc == SENTINEL_ADDR + 2:
                    return {
                        "returned": True,
                        "text_pointer": None,
                        "ticks": ticked,
                        "post_pc": pc,
                    }
            return {
                "returned": False,
                "text_pointer": text_hits[-1] if text_hits else None,
                "ticks": ticked,
                "post_pc": int(rf.PC),
            }
        finally:
            try:
                pyboy.hook_deregister(text_bank, text_address)
            except Exception:
                pass

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_paralysis_turn_result(case)
            cache.restore()
            seed_check_turn(case)
            call_result = call_check_turn_until_text_or_return()
            actual = {
                "blocked": call_result["text_pointer"] == fully_paralyzed_text,
                "text_pointer": (
                    None if call_result["text_pointer"] is None else f"${call_result['text_pointer']:04x}"
                ),
                "rng_count": read_byte("wLinkBattleRNCount"),
                "returned": call_result["returned"],
                "ticks": call_result["ticks"],
                "post_pc": f"${call_result['post_pc']:04x}",
            }
            rows.append(
                {
                    "case": case.name,
                    "actor": case.actor,
                    "rng_value": case.rng_value,
                    "types": list(case.types),
                    "python": expected,
                    "rom": actual,
                    "ok": (
                        actual["blocked"] == expected["blocked"]
                        and actual["rng_count"] == expected["rng_count"]
                    ),
                }
            )
    finally:
        cache.stop()
    return rows


def run_sleep_turn_differential(
    cases: Iterable[SleepTurnDifferentialCase] = SLEEP_TURN_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        read_byte_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.safe_call import SENTINEL_ADDR
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    fast_asleep_text = syms["FastAsleepText"][1]
    woke_up_text = syms["WokeUpText"][1]

    def write_byte(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, value, bank)

    def read_byte(name: str) -> int:
        bank, address = syms[name]
        return read_byte_banked(pyboy, address, bank)

    def seed_check_turn(case: SleepTurnDifferentialCase) -> None:
        for name in (
            "wTurnEnded",
            "wAttackMissed",
            "wEffectFailed",
            "wBattleAnimParam",
            "wAlreadyDisobeyed",
            "wAlreadyFailed",
            "wSomeoneIsRampaging",
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
            "wBattleMonStatus",
            "wEnemyMonStatus",
            "wPlayerDisableCount",
            "wEnemyDisableCount",
            "wDisabledMove",
            "wEnemyDisabledMove",
        ):
            write_byte(name, 0)
        write_byte("hBattleTurn", 0 if case.actor == "player" else 1)
        status_name = "wBattleMonStatus" if case.actor == "player" else "wEnemyMonStatus"
        write_byte(status_name, case.sleep_turns)
        write_byte("wCurPlayerMove", case.move_id)
        write_byte("wCurEnemyMove", case.move_id)

    def call_check_turn_until_text_or_return(budget: int = 20000) -> dict[str, Any]:
        text_hits: list[int] = []
        sleep_anim_hits: list[bool] = []

        def on_text(_context) -> None:
            text_hits.append(int(pyboy.register_file.HL) & 0xFFFF)

        def on_sleep_anim(_context) -> None:
            sleep_anim_hits.append(True)

        text_bank, text_address = syms["StdBattleTextbox"]
        anim_bank, anim_address = syms["FarPlayBattleAnimation"]
        pyboy.hook_register(text_bank, text_address, on_text, None)
        pyboy.hook_register(anim_bank, anim_address, on_sleep_anim, None)
        try:
            pyboy.memory[SENTINEL_ADDR] = 0x18
            pyboy.memory[SENTINEL_ADDR + 1] = 0xFE
            rf = pyboy.register_file
            sp = int(rf.SP)
            new_sp = (sp - 2) & 0xFFFF
            pyboy.memory[new_sp] = SENTINEL_ADDR & 0xFF
            pyboy.memory[new_sp + 1] = (SENTINEL_ADDR >> 8) & 0xFF
            rf.SP = new_sp
            fn_bank, fn_address = syms["BattleCommand_CheckTurn"]
            rf.PC = fn_address
            rom_bank_sym = syms.get("hROMBank")
            if rom_bank_sym:
                pyboy.memory[rom_bank_sym[1]] = fn_bank
            pyboy.memory[0x2000] = fn_bank

            ticked = 0
            while ticked < budget:
                pyboy.tick(2, False, False)
                ticked += 2
                if text_hits:
                    return {
                        "returned": False,
                        "text_pointer": text_hits[-1],
                        "sleep_anim": False,
                        "ticks": ticked,
                        "post_pc": int(rf.PC),
                    }
                if sleep_anim_hits:
                    return {
                        "returned": False,
                        "text_pointer": None,
                        "sleep_anim": True,
                        "ticks": ticked,
                        "post_pc": int(rf.PC),
                    }
                pc = int(rf.PC)
                if pc == SENTINEL_ADDR or pc == SENTINEL_ADDR + 2:
                    return {
                        "returned": True,
                        "text_pointer": None,
                        "sleep_anim": False,
                        "ticks": ticked,
                        "post_pc": pc,
                    }
            return {
                "returned": False,
                "text_pointer": text_hits[-1] if text_hits else None,
                "sleep_anim": bool(sleep_anim_hits),
                "ticks": ticked,
                "post_pc": int(rf.PC),
            }
        finally:
            try:
                pyboy.hook_deregister(text_bank, text_address)
            except Exception:
                pass
            try:
                pyboy.hook_deregister(anim_bank, anim_address)
            except Exception:
                pass

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_sleep_turn_result(case)
            cache.restore()
            seed_check_turn(case)
            call_result = call_check_turn_until_text_or_return()
            status_name = "wBattleMonStatus" if case.actor == "player" else "wEnemyMonStatus"
            text_pointer = call_result["text_pointer"]
            actual = {
                "blocked": (
                    (text_pointer == fast_asleep_text or call_result["sleep_anim"])
                    and expected["blocked"]
                ),
                "text": (
                    "fast_asleep"
                    if text_pointer == fast_asleep_text
                    else "fast_asleep_anim"
                    if call_result["sleep_anim"]
                    else "woke_up"
                    if text_pointer == woke_up_text
                    else None
                ),
                "status_byte": read_byte(status_name),
                "returned": call_result["returned"],
                "ticks": call_result["ticks"],
                "post_pc": f"${call_result['post_pc']:04x}",
            }
            rows.append(
                {
                    "case": case.name,
                    "actor": case.actor,
                    "sleep_turns": case.sleep_turns,
                    "move_id": case.move_id,
                    "python": expected,
                    "rom": actual,
                    "ok": (
                        actual["blocked"] == expected["blocked"]
                        and actual["status_byte"] == expected["sleep_turns_after"]
                        and (
                            (expected["reason"] == "fast_asleep" and actual["text"] in {"fast_asleep", "fast_asleep_anim"})
                            or (expected["reason"] == "woke_up" and actual["text"] == "woke_up")
                            or expected["reason"] == "sleep_bypass_move"
                        )
                    ),
                }
            )
    finally:
        cache.stop()
    return rows


def run_freeze_turn_differential(
    cases: Iterable[FreezeTurnDifferentialCase] = FREEZE_TURN_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        read_byte_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.safe_call import SENTINEL_ADDR
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    frozen_solid_text = syms["FrozenSolidText"][1]

    def write_byte(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, value, bank)

    def read_byte(name: str) -> int:
        bank, address = syms[name]
        return read_byte_banked(pyboy, address, bank)

    def seed_check_turn(case: FreezeTurnDifferentialCase) -> None:
        for name in (
            "wTurnEnded",
            "wAttackMissed",
            "wEffectFailed",
            "wBattleAnimParam",
            "wAlreadyDisobeyed",
            "wAlreadyFailed",
            "wSomeoneIsRampaging",
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
            "wBattleMonStatus",
            "wEnemyMonStatus",
            "wPlayerDisableCount",
            "wEnemyDisableCount",
            "wDisabledMove",
            "wEnemyDisabledMove",
        ):
            write_byte(name, 0)
        write_byte("hBattleTurn", 0 if case.actor == "player" else 1)
        status_name = "wBattleMonStatus" if case.actor == "player" else "wEnemyMonStatus"
        write_byte(status_name, 1 << FRZ_BIT)
        write_byte("wCurPlayerMove", case.move_id)
        write_byte("wCurEnemyMove", case.move_id)

    def call_check_turn_until_text_or_return(budget: int = 20000) -> dict[str, Any]:
        text_hits: list[int] = []

        def on_text(_context) -> None:
            text_hits.append(int(pyboy.register_file.HL) & 0xFFFF)

        text_bank, text_address = syms["StdBattleTextbox"]
        pyboy.hook_register(text_bank, text_address, on_text, None)
        try:
            pyboy.memory[SENTINEL_ADDR] = 0x18
            pyboy.memory[SENTINEL_ADDR + 1] = 0xFE
            rf = pyboy.register_file
            sp = int(rf.SP)
            new_sp = (sp - 2) & 0xFFFF
            pyboy.memory[new_sp] = SENTINEL_ADDR & 0xFF
            pyboy.memory[new_sp + 1] = (SENTINEL_ADDR >> 8) & 0xFF
            rf.SP = new_sp
            fn_bank, fn_address = syms["BattleCommand_CheckTurn"]
            rf.PC = fn_address
            rom_bank_sym = syms.get("hROMBank")
            if rom_bank_sym:
                pyboy.memory[rom_bank_sym[1]] = fn_bank
            pyboy.memory[0x2000] = fn_bank

            ticked = 0
            while ticked < budget:
                pyboy.tick(2, False, False)
                ticked += 2
                if text_hits:
                    return {
                        "returned": False,
                        "text_pointer": text_hits[-1],
                        "ticks": ticked,
                        "post_pc": int(rf.PC),
                    }
                pc = int(rf.PC)
                if pc == SENTINEL_ADDR or pc == SENTINEL_ADDR + 2:
                    return {
                        "returned": True,
                        "text_pointer": None,
                        "ticks": ticked,
                        "post_pc": pc,
                    }
            return {
                "returned": False,
                "text_pointer": text_hits[-1] if text_hits else None,
                "ticks": ticked,
                "post_pc": int(rf.PC),
            }
        finally:
            try:
                pyboy.hook_deregister(text_bank, text_address)
            except Exception:
                pass

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_freeze_turn_result(case)
            cache.restore()
            seed_check_turn(case)
            call_result = call_check_turn_until_text_or_return()
            status_name = "wBattleMonStatus" if case.actor == "player" else "wEnemyMonStatus"
            text_pointer = call_result["text_pointer"]
            actual = {
                "blocked": text_pointer == frozen_solid_text,
                "text": "frozen_solid" if text_pointer == frozen_solid_text else None,
                "status_byte": read_byte(status_name),
                "returned": call_result["returned"],
                "ticks": call_result["ticks"],
                "post_pc": f"${call_result['post_pc']:04x}",
            }
            rows.append(
                {
                    "case": case.name,
                    "actor": case.actor,
                    "move_id": case.move_id,
                    "python": expected,
                    "rom": actual,
                    "ok": (
                        actual["blocked"] == expected["blocked"]
                        and bool(actual["status_byte"] & (1 << FRZ_BIT))
                        and (
                            (expected["reason"] == "frozen_solid" and actual["text"] == "frozen_solid")
                            or (
                                expected["reason"] == "thaw_move_bypasses_freeze"
                                and actual["text"] is None
                                and actual["returned"]
                            )
                        )
                    ),
                }
            )
    finally:
        cache.stop()
    return rows


def run_flinch_turn_differential(
    cases: Iterable[FlinchTurnDifferentialCase] = FLINCH_TURN_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        read_byte_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.safe_call import SENTINEL_ADDR
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    flinched_text = syms["FlinchedText"][1]

    def write_byte(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, value, bank)

    def read_byte(name: str) -> int:
        bank, address = syms[name]
        return read_byte_banked(pyboy, address, bank)

    def seed_check_turn(case: FlinchTurnDifferentialCase) -> None:
        for name in (
            "wTurnEnded",
            "wAttackMissed",
            "wEffectFailed",
            "wBattleAnimParam",
            "wAlreadyDisobeyed",
            "wAlreadyFailed",
            "wSomeoneIsRampaging",
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
            "wBattleMonStatus",
            "wEnemyMonStatus",
            "wPlayerDisableCount",
            "wEnemyDisableCount",
            "wDisabledMove",
            "wEnemyDisabledMove",
        ):
            write_byte(name, 0)
        write_byte("hBattleTurn", 0 if case.actor == "player" else 1)
        substatus_name = "wPlayerSubStatus3" if case.actor == "player" else "wEnemySubStatus3"
        write_byte(substatus_name, 1 << SUBSTATUS_FLINCHED_BIT)
        write_byte("wCurPlayerMove", MOVE_TACKLE)
        write_byte("wCurEnemyMove", MOVE_TACKLE)

    def call_check_turn_until_text_or_return(budget: int = 20000) -> dict[str, Any]:
        text_hits: list[int] = []

        def on_text(_context) -> None:
            text_hits.append(int(pyboy.register_file.HL) & 0xFFFF)

        text_bank, text_address = syms["StdBattleTextbox"]
        pyboy.hook_register(text_bank, text_address, on_text, None)
        try:
            pyboy.memory[SENTINEL_ADDR] = 0x18
            pyboy.memory[SENTINEL_ADDR + 1] = 0xFE
            rf = pyboy.register_file
            sp = int(rf.SP)
            new_sp = (sp - 2) & 0xFFFF
            pyboy.memory[new_sp] = SENTINEL_ADDR & 0xFF
            pyboy.memory[new_sp + 1] = (SENTINEL_ADDR >> 8) & 0xFF
            rf.SP = new_sp
            fn_bank, fn_address = syms["BattleCommand_CheckTurn"]
            rf.PC = fn_address
            rom_bank_sym = syms.get("hROMBank")
            if rom_bank_sym:
                pyboy.memory[rom_bank_sym[1]] = fn_bank
            pyboy.memory[0x2000] = fn_bank

            ticked = 0
            while ticked < budget:
                pyboy.tick(2, False, False)
                ticked += 2
                if text_hits:
                    return {
                        "returned": False,
                        "text_pointer": text_hits[-1],
                        "ticks": ticked,
                        "post_pc": int(rf.PC),
                    }
                pc = int(rf.PC)
                if pc == SENTINEL_ADDR or pc == SENTINEL_ADDR + 2:
                    return {
                        "returned": True,
                        "text_pointer": None,
                        "ticks": ticked,
                        "post_pc": pc,
                    }
            return {
                "returned": False,
                "text_pointer": text_hits[-1] if text_hits else None,
                "ticks": ticked,
                "post_pc": int(rf.PC),
            }
        finally:
            try:
                pyboy.hook_deregister(text_bank, text_address)
            except Exception:
                pass

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_flinch_turn_result(case)
            cache.restore()
            seed_check_turn(case)
            call_result = call_check_turn_until_text_or_return()
            substatus_name = "wPlayerSubStatus3" if case.actor == "player" else "wEnemySubStatus3"
            text_pointer = call_result["text_pointer"]
            actual = {
                "blocked": text_pointer == flinched_text,
                "text": "flinched" if text_pointer == flinched_text else None,
                "flinched_after": bool(read_byte(substatus_name) & (1 << SUBSTATUS_FLINCHED_BIT)),
                "returned": call_result["returned"],
                "ticks": call_result["ticks"],
                "post_pc": f"${call_result['post_pc']:04x}",
            }
            rows.append(
                {
                    "case": case.name,
                    "actor": case.actor,
                    "python": expected,
                    "rom": actual,
                    "ok": (
                        actual["blocked"] == expected["blocked"]
                        and actual["text"] == "flinched"
                        and actual["flinched_after"] == expected["flinched_after"]
                    ),
                }
            )
    finally:
        cache.stop()
    return rows


def run_status_speed_differential(
    cases: Iterable[StatusSpeedDifferentialCase] = STATUS_SPEED_DIFFERENTIAL_CASES,
) -> list[dict[str, Any]]:
    from tools.damage_debugger.boot_cache import BootStateCache
    from tools.damage_debugger.paths import find_rom, find_sym
    from tools.damage_debugger.safe_call import (
        call_function_safe,
        read_be_u16_banked,
        write_byte_banked,
    )
    from tools.damage_debugger.symbols import SymbolTable

    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    type_constants = tables.load_type_constants()

    def write_byte(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, value, bank)

    def write_u16(name: str, value: int) -> None:
        bank, address = syms[name]
        write_byte_banked(pyboy, address, (value >> 8) & 0xFF, bank)
        write_byte_banked(pyboy, address + 1, value & 0xFF, bank)

    def read_u16(name: str) -> int:
        bank, address = syms[name]
        return read_be_u16_banked(pyboy, address, bank)

    def seed_status_speed(case: StatusSpeedDifferentialCase) -> None:
        write_byte("hBattleTurn", 1 if case.actor == "player" else 0)
        write_u16("wBattleMonSpeed", case.speed if case.actor == "player" else 40)
        write_u16("wEnemyMonSpeed", case.speed if case.actor == "enemy" else 40)
        write_byte("wBattleMonStatus", 0)
        write_byte("wEnemyMonStatus", 0)
        status_byte = 1 << PAR_BIT if case.status == "paralysis" else 0
        if case.actor == "player":
            write_byte("wBattleMonStatus", status_byte)
            write_byte("wBattleMonType1", type_constants[case.types[0]])
            write_byte("wBattleMonType2", type_constants[case.types[1]])
            write_byte("wEnemyMonType1", type_constants["NORMAL"])
            write_byte("wEnemyMonType2", type_constants["NORMAL"])
        else:
            write_byte("wEnemyMonStatus", status_byte)
            write_byte("wEnemyMonType1", type_constants[case.types[0]])
            write_byte("wEnemyMonType2", type_constants[case.types[1]])
            write_byte("wBattleMonType1", type_constants["NORMAL"])
            write_byte("wBattleMonType2", type_constants["NORMAL"])

    rows: list[dict[str, Any]] = []
    try:
        for case in cases:
            expected = python_status_speed_result(case)
            cache.restore()
            seed_status_speed(case)
            ticks, returned, post_pc = call_function_safe(
                pyboy,
                syms,
                "ApplyPrzEffectOnSpeed_Far",
                budget=4800,
            )
            speed_name = "wBattleMonSpeed" if case.actor == "player" else "wEnemyMonSpeed"
            actual = {
                "speed": read_u16(speed_name),
                "returned": returned,
                "ticks": ticks,
                "post_pc": f"${post_pc:04x}",
            }
            rows.append(
                {
                    "case": case.name,
                    "actor": case.actor,
                    "input_speed": case.speed,
                    "status": case.status,
                    "types": list(case.types),
                    "python": expected,
                    "rom": actual,
                    "ok": actual["speed"] == expected["speed"] and actual["returned"],
                }
            )
    finally:
        cache.stop()
    return rows


def assert_damage_variation_differential() -> list[dict[str, Any]]:
    rows = run_damage_variation_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"damage variation ROM differential failed:\n{detail}")
    return rows


def assert_accuracy_differential() -> list[dict[str, Any]]:
    rows = run_accuracy_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"accuracy ROM differential failed:\n{detail}")
    return rows


def assert_critical_differential() -> list[dict[str, Any]]:
    rows = run_critical_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"critical-hit ROM differential failed:\n{detail}")
    return rows


def assert_turn_order_differential() -> list[dict[str, Any]]:
    rows = run_turn_order_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"turn order ROM differential failed:\n{detail}")
    return rows


def assert_boss_ai_selector_differential() -> list[dict[str, Any]]:
    rows = run_boss_ai_selector_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"Boss AI selector ROM differential failed:\n{detail}")
    return rows


def assert_double_damage_differential() -> list[dict[str, Any]]:
    rows = run_double_damage_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"double-damage ROM differential failed:\n{detail}")
    return rows


def assert_after_hit_differential() -> list[dict[str, Any]]:
    rows = run_after_hit_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"after-hit ROM differential failed:\n{detail}")
    return rows


def assert_residual_status_differential() -> list[dict[str, Any]]:
    rows = run_residual_status_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"residual-status ROM differential failed:\n{detail}")
    return rows


def assert_leftovers_differential() -> list[dict[str, Any]]:
    rows = run_leftovers_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"Leftovers ROM differential failed:\n{detail}")
    return rows


def assert_paralysis_turn_differential() -> list[dict[str, Any]]:
    rows = run_paralysis_turn_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"paralysis turn ROM differential failed:\n{detail}")
    return rows


def assert_sleep_turn_differential() -> list[dict[str, Any]]:
    rows = run_sleep_turn_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"sleep turn ROM differential failed:\n{detail}")
    return rows


def assert_freeze_turn_differential() -> list[dict[str, Any]]:
    rows = run_freeze_turn_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"freeze turn ROM differential failed:\n{detail}")
    return rows


def assert_flinch_turn_differential() -> list[dict[str, Any]]:
    rows = run_flinch_turn_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"flinch turn ROM differential failed:\n{detail}")
    return rows


def assert_status_speed_differential() -> list[dict[str, Any]]:
    rows = run_status_speed_differential()
    failures = [row for row in rows if not row["ok"]]
    if failures:
        detail = json.dumps(failures, indent=2, sort_keys=True)
        raise AssertionError(f"status speed ROM differential failed:\n{detail}")
    return rows
