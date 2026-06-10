"""ROM-backed differential goldens for the headless battle simulator.

These checks intentionally stay tiny. They do not make the simulator a full
emulator; they pin one selected headless turn against the same battle-command
sequence in the built ROM so future slices can see when a source-mirrored path
has crossed into differential proof.

Usage:
    python -m tools.headless_battle.rom_differential
    python -m tools.headless_battle.rom_differential --json-out audit/headless_battle/rom_differential.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.damage_debugger.boot_cache import BootStateCache
from tools.damage_debugger.paths import find_rom, find_sym
from tools.damage_debugger.safe_call import (
    SENTINEL_ADDR,
    call_function_safe,
    read_be_u16_banked,
    read_byte_banked,
    write_byte_banked,
)
from tools.damage_debugger.symbols import SymbolTable
from tools.headless_battle.simulator import (
    ITEM_LUCKY_PUNCH,
    ITEM_SCOPE_LENS,
    MoveState,
    PokemonState,
    RngConfig,
    RuntimeRng,
    critical_results,
    damage_variation_results,
    simulate_payload,
)


TACKLE_MOVE_ID = 0x21
BODY_SLAM_MOVE_ID = 0x22
EMBER_MOVE_ID = 0x34
SLUDGE_MOVE_ID = 0x7C
ABSORB_MOVE_ID = 0x47
MEGA_DRAIN_MOVE_ID = 0x48
LEECH_LIFE_MOVE_ID = 0x8D
GIGA_DRAIN_MOVE_ID = 0xCA
RAIN_DANCE_MOVE_ID = 0xF0
SUNNY_DAY_MOVE_ID = 0xF1
SUBSTITUTE_MOVE_ID = 0xA4
RECOVER_MOVE_ID = 0x69
SOFTBOILED_MOVE_ID = 0x87
REST_MOVE_ID = 0x9C
MILK_DRINK_MOVE_ID = 0xD0
LIFE_ORB_ITEM_ID = 0x46
FULL_RESTORE_ITEM_ID = 0x0E
MAX_POTION_ITEM_ID = 0x0F
HYPER_POTION_ITEM_ID = 0x10
POTION_ITEM_ID = 0x12
SHELL_BELL_ITEM_ID = 0x95
ROCKY_HELMET_ITEM_ID = 0x99
SLASH_MOVE_ID = 0xA3
CYNDAQUIL_SPECIES = 155
CHANSEY_SPECIES = 0x71
SUBSTATUS_FOCUS_ENERGY_MASK = 1 << 2  # wPlayerSubStatus4 / wEnemySubStatus4 bit 2
NORMAL_TYPE = 0x00
POISON_TYPE = 0x03
FLYING_TYPE = 0x02
FIRE_TYPE = 0x14
WEATHER_RAIN = 1
WEATHER_SUN = 2
LINK_MODE = 1
CALL_BUDGET = 50_000
COMPONENT_NONRETURN_CALL_BUDGET = 500
RESIDUAL_CALL_BUDGET = 100_000
EI_STUB_ADDR = 0xFFF8
PSN_STATUS = 1 << 3
BRN_STATUS = 1 << 4
PAR_STATUS = 1 << 6
SLEEP_STATUS_BYTE_3_TURNS = 3
SUBSTATUS_NIGHTMARE_BIT = 0
SUBSTATUS_CONFUSED_BIT = 7
SUBSTATUS_SUBSTITUTE_BIT = 4
SUBSTATUS_TOXIC_BIT = 0
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
class NormalHitScenario:
    scenario_id: str
    rom_scenario_id: str
    rng_values: tuple[int, ...]
    move_accuracy: int = 255


NORMAL_HIT_SCENARIOS = (
    NormalHitScenario(
        scenario_id="normal_hit_fixed_rng_differential",
        rom_scenario_id="normal_hit_fixed_rng_enemy_pidgey_tackle",
        rng_values=(255, 255),
    ),
    NormalHitScenario(
        scenario_id="normal_hit_low_variation_differential",
        rom_scenario_id="normal_hit_low_variation_enemy_pidgey_tackle",
        rng_values=(255, 179),
    ),
    NormalHitScenario(
        scenario_id="normal_hit_critical_differential",
        rom_scenario_id="normal_hit_critical_enemy_pidgey_tackle",
        rng_values=(0, 255),
    ),
    NormalHitScenario(
        scenario_id="normal_hit_accuracy_miss_differential",
        rom_scenario_id="normal_hit_accuracy_miss_enemy_pidgey_tackle",
        rng_values=(255, 255, 255),
        move_accuracy=242,
    ),
)
DEFAULT_NORMAL_HIT_SCENARIO = NORMAL_HIT_SCENARIOS[0]


@dataclass(frozen=True)
class StatusComponentScenario:
    scenario_id: str
    move_name: str
    move_id: int
    move_type: int
    target_command: str
    status_name: str
    expected_status_byte: int
    chance_threshold: int
    effect_chance_rng: int
    expect_success: bool
    headless_rng_values: tuple[int, ...]


STATUS_COMPONENT_SCENARIOS = (
    StatusComponentScenario(
        scenario_id="component_ember_burn_success",
        move_name="EMBER",
        move_id=EMBER_MOVE_ID,
        move_type=FIRE_TYPE,
        target_command="BattleCommand_BurnTarget",
        status_name="burn",
        expected_status_byte=BRN_STATUS,
        chance_threshold=25,
        effect_chance_rng=0,
        expect_success=True,
        headless_rng_values=(255, 255, 0),
    ),
    StatusComponentScenario(
        scenario_id="component_sludge_poison_success",
        move_name="SLUDGE",
        move_id=SLUDGE_MOVE_ID,
        move_type=POISON_TYPE,
        target_command="BattleCommand_PoisonTarget",
        status_name="poison",
        expected_status_byte=PSN_STATUS,
        chance_threshold=76,
        effect_chance_rng=0,
        expect_success=True,
        headless_rng_values=(255, 255, 0),
    ),
    StatusComponentScenario(
        scenario_id="component_body_slam_paralyze_success",
        move_name="BODY_SLAM",
        move_id=BODY_SLAM_MOVE_ID,
        move_type=NORMAL_TYPE,
        target_command="BattleCommand_ParalyzeTarget",
        status_name="paralyze",
        expected_status_byte=PAR_STATUS,
        chance_threshold=76,
        effect_chance_rng=0,
        expect_success=True,
        headless_rng_values=(255, 255, 0, 255),
    ),
    StatusComponentScenario(
        scenario_id="component_body_slam_paralyze_effectchance_fail",
        move_name="BODY_SLAM",
        move_id=BODY_SLAM_MOVE_ID,
        move_type=NORMAL_TYPE,
        target_command="BattleCommand_ParalyzeTarget",
        status_name="paralyze",
        expected_status_byte=0,
        chance_threshold=76,
        effect_chance_rng=255,
        expect_success=False,
        headless_rng_values=(255, 255, 255),
    ),
)


@dataclass(frozen=True)
class DrainComponentScenario:
    scenario_id: str
    move_name: str
    move_id: int
    hp_before: int
    max_hp: int
    damage: int
    expected_raw_heal: int
    expected_heal: int
    expected_hp_after: int
    headless_target_hp: int


DRAIN_COMPONENT_SCENARIOS = (
    DrainComponentScenario(
        scenario_id="component_giga_drain_half_heal",
        move_name="GIGA_DRAIN",
        move_id=GIGA_DRAIN_MOVE_ID,
        hp_before=5,
        max_hp=40,
        damage=15,
        expected_raw_heal=7,
        expected_heal=7,
        expected_hp_after=12,
        headless_target_hp=40,
    ),
    DrainComponentScenario(
        scenario_id="component_absorb_min_one_heal",
        move_name="ABSORB",
        move_id=ABSORB_MOVE_ID,
        hp_before=5,
        max_hp=40,
        damage=1,
        expected_raw_heal=1,
        expected_heal=1,
        expected_hp_after=6,
        headless_target_hp=1,
    ),
    DrainComponentScenario(
        scenario_id="component_giga_drain_max_hp_cap",
        move_name="GIGA_DRAIN",
        move_id=GIGA_DRAIN_MOVE_ID,
        hp_before=39,
        max_hp=40,
        damage=15,
        expected_raw_heal=7,
        expected_heal=1,
        expected_hp_after=40,
        headless_target_hp=40,
    ),
)


@dataclass(frozen=True)
class DrainMoveTurnScenario:
    scenario_id: str
    move_name: str
    move_id: int
    hp_before: int
    max_hp: int
    damage: int
    expected_raw_heal: int
    expected_heal: int
    expected_hp_after: int
    headless_target_hp: int
    pp_before: int


DRAIN_MOVE_TURN_SCENARIOS = (
    DrainMoveTurnScenario(
        scenario_id="selected_drain_absorb_alias",
        move_name="ABSORB",
        move_id=ABSORB_MOVE_ID,
        hp_before=5,
        max_hp=40,
        damage=7,
        expected_raw_heal=3,
        expected_heal=3,
        expected_hp_after=8,
        headless_target_hp=40,
        pp_before=35,
    ),
    DrainMoveTurnScenario(
        scenario_id="selected_drain_mega_drain_alias",
        move_name="MEGA_DRAIN",
        move_id=MEGA_DRAIN_MOVE_ID,
        hp_before=5,
        max_hp=40,
        damage=10,
        expected_raw_heal=5,
        expected_heal=5,
        expected_hp_after=10,
        headless_target_hp=40,
        pp_before=20,
    ),
    DrainMoveTurnScenario(
        scenario_id="selected_drain_leech_life_alias",
        move_name="LEECH_LIFE",
        move_id=LEECH_LIFE_MOVE_ID,
        hp_before=5,
        max_hp=40,
        damage=12,
        expected_raw_heal=6,
        expected_heal=6,
        expected_hp_after=11,
        headless_target_hp=40,
        pp_before=20,
    ),
    DrainMoveTurnScenario(
        scenario_id="selected_drain_giga_drain_half_heal",
        move_name="GIGA_DRAIN",
        move_id=GIGA_DRAIN_MOVE_ID,
        hp_before=5,
        max_hp=40,
        damage=15,
        expected_raw_heal=7,
        expected_heal=7,
        expected_hp_after=12,
        headless_target_hp=40,
        pp_before=25,
    ),
    DrainMoveTurnScenario(
        scenario_id="selected_drain_absorb_min_one_heal",
        move_name="ABSORB",
        move_id=ABSORB_MOVE_ID,
        hp_before=5,
        max_hp=40,
        damage=1,
        expected_raw_heal=1,
        expected_heal=1,
        expected_hp_after=6,
        headless_target_hp=1,
        pp_before=35,
    ),
    DrainMoveTurnScenario(
        scenario_id="selected_drain_giga_drain_max_hp_cap",
        move_name="GIGA_DRAIN",
        move_id=GIGA_DRAIN_MOVE_ID,
        hp_before=39,
        max_hp=40,
        damage=15,
        expected_raw_heal=7,
        expected_heal=1,
        expected_hp_after=40,
        headless_target_hp=40,
        pp_before=25,
    ),
)


@dataclass(frozen=True)
class ItemRestoreComponentScenario:
    scenario_id: str
    item_name: str
    item_id: int
    hp_before: int
    max_hp: int
    expected_table_amount: int
    expected_hp_after: int

    @property
    def expected_heal(self) -> int:
        return self.expected_hp_after - self.hp_before


ITEM_RESTORE_COMPONENT_SCENARIOS = (
    ItemRestoreComponentScenario(
        scenario_id="component_potion_partial_heal",
        item_name="POTION",
        item_id=POTION_ITEM_ID,
        hp_before=5,
        max_hp=32,
        expected_table_amount=20,
        expected_hp_after=25,
    ),
    ItemRestoreComponentScenario(
        scenario_id="component_hyper_potion_cap",
        item_name="HYPER_POTION",
        item_id=HYPER_POTION_ITEM_ID,
        hp_before=180,
        max_hp=220,
        expected_table_amount=200,
        expected_hp_after=220,
    ),
    ItemRestoreComponentScenario(
        scenario_id="component_max_potion_full_heal",
        item_name="MAX_POTION",
        item_id=MAX_POTION_ITEM_ID,
        hp_before=10,
        max_hp=30,
        expected_table_amount=999,
        expected_hp_after=30,
    ),
    ItemRestoreComponentScenario(
        scenario_id="component_full_restore_hp_heal",
        item_name="FULL_RESTORE",
        item_id=FULL_RESTORE_ITEM_ID,
        hp_before=10,
        max_hp=30,
        expected_table_amount=999,
        expected_hp_after=30,
    ),
)


@dataclass(frozen=True)
class FullRestoreStatusCureScenario:
    scenario_id: str
    status_before: int
    sub1_before: int  # wPlayerSubStatus1 (NIGHTMARE bit)
    sub3_before: int  # wPlayerSubStatus3 (CONFUSED bit)
    sub5_before: int  # wPlayerSubStatus5 (TOXIC bit)
    headless_status: str | None  # "burn", "poison", "toxic", "paralyze", "sleep", or None
    headless_toxic_count: int
    headless_sleep_turns: int


FULL_RESTORE_STATUS_CURE_SCENARIOS = (
    FullRestoreStatusCureScenario(
        scenario_id="component_full_restore_clears_burn",
        status_before=BRN_STATUS,
        sub1_before=0,
        sub3_before=0,
        sub5_before=0,
        headless_status="burn",
        headless_toxic_count=0,
        headless_sleep_turns=0,
    ),
    FullRestoreStatusCureScenario(
        scenario_id="component_full_restore_clears_paralyze",
        status_before=PAR_STATUS,
        sub1_before=0,
        sub3_before=0,
        sub5_before=0,
        headless_status="paralyze",
        headless_toxic_count=0,
        headless_sleep_turns=0,
    ),
    FullRestoreStatusCureScenario(
        scenario_id="component_full_restore_clears_toxic_and_poison",
        status_before=PSN_STATUS,
        sub1_before=0,
        sub3_before=0,
        sub5_before=1 << SUBSTATUS_TOXIC_BIT,
        headless_status="toxic",
        headless_toxic_count=3,
        headless_sleep_turns=0,
    ),
    FullRestoreStatusCureScenario(
        scenario_id="component_full_restore_clears_sleep_and_nightmare",
        status_before=SLEEP_STATUS_BYTE_3_TURNS,
        sub1_before=1 << SUBSTATUS_NIGHTMARE_BIT,
        sub3_before=0,
        sub5_before=0,
        headless_status="sleep",
        headless_toxic_count=0,
        headless_sleep_turns=3,
    ),
    FullRestoreStatusCureScenario(
        scenario_id="component_full_restore_clears_confusion_only",
        status_before=0,
        sub1_before=0,
        sub3_before=1 << SUBSTATUS_CONFUSED_BIT,
        sub5_before=0,
        headless_status=None,
        headless_toxic_count=0,
        headless_sleep_turns=0,
    ),
)


@dataclass(frozen=True)
class PPDecrementComponentScenario:
    scenario_id: str
    actor: str
    battle_mode: int
    party_pp_symbol: str
    party_move_symbol: str
    turns_taken_symbol: str
    pp_before: int = 35


PP_DECREMENT_COMPONENT_SCENARIOS = (
    PPDecrementComponentScenario(
        scenario_id="component_player_selected_move_pp_decrement",
        actor="player",
        battle_mode=1,
        party_pp_symbol="wPartyMon1PP",
        party_move_symbol="wPartyMon1Moves",
        turns_taken_symbol="wPlayerTurnsTaken",
    ),
    PPDecrementComponentScenario(
        scenario_id="component_wild_enemy_selected_move_pp_decrement",
        actor="enemy",
        battle_mode=1,
        party_pp_symbol="wWildMonPP",
        party_move_symbol="wWildMonMoves",
        turns_taken_symbol="wEnemyTurnsTaken",
    ),
    PPDecrementComponentScenario(
        scenario_id="component_trainer_enemy_selected_move_pp_decrement",
        actor="enemy",
        battle_mode=2,
        party_pp_symbol="wOTPartyMon1PP",
        party_move_symbol="wOTPartyMon1Moves",
        turns_taken_symbol="wEnemyTurnsTaken",
    ),
)


@dataclass(frozen=True)
class WeatherSetupComponentScenario:
    scenario_id: str
    move_name: str
    move_id: int
    command: str
    weather_name: str
    expected_weather: int


WEATHER_SETUP_COMPONENT_SCENARIOS = (
    WeatherSetupComponentScenario(
        scenario_id="component_rain_dance_sets_weather",
        move_name="RAIN_DANCE",
        move_id=RAIN_DANCE_MOVE_ID,
        command="BattleCommand_StartRain",
        weather_name="rain",
        expected_weather=WEATHER_RAIN,
    ),
    WeatherSetupComponentScenario(
        scenario_id="component_sunny_day_sets_weather",
        move_name="SUNNY_DAY",
        move_id=SUNNY_DAY_MOVE_ID,
        command="BattleCommand_StartSun",
        weather_name="sun",
        expected_weather=WEATHER_SUN,
    ),
)


@dataclass(frozen=True)
class SubstituteMoveTurnScenario:
    scenario_id: str
    case_name: str
    hp_before: int
    max_hp: int
    substitute_before: bool
    substitute_hp_before: int
    expected_event_type: str
    expected_blocked_reason: str | None
    expected_hp_after: int
    expected_substitute_after: bool
    expected_substitute_hp_after: int
    expected_text_symbol: str = ""
    pp_before: int = 10


SUBSTITUTE_MOVE_TURN_SCENARIOS = (
    SubstituteMoveTurnScenario(
        scenario_id="selected_substitute_move_create",
        case_name="create",
        hp_before=16,
        max_hp=16,
        substitute_before=False,
        substitute_hp_before=0,
        expected_event_type="substitute_create",
        expected_blocked_reason=None,
        expected_hp_after=12,
        expected_substitute_after=True,
        expected_substitute_hp_after=4,
    ),
    SubstituteMoveTurnScenario(
        scenario_id="selected_substitute_move_too_weak",
        case_name="too_weak",
        hp_before=4,
        max_hp=16,
        substitute_before=False,
        substitute_hp_before=0,
        expected_event_type="substitute_no_effect",
        expected_blocked_reason="too_weak",
        expected_hp_after=4,
        expected_substitute_after=False,
        expected_substitute_hp_after=4,
        expected_text_symbol="TooWeakSubText",
    ),
    SubstituteMoveTurnScenario(
        scenario_id="selected_substitute_move_already_active",
        case_name="already_active",
        hp_before=16,
        max_hp=16,
        substitute_before=True,
        substitute_hp_before=4,
        expected_event_type="substitute_no_effect",
        expected_blocked_reason="already_has_substitute",
        expected_hp_after=16,
        expected_substitute_after=True,
        expected_substitute_hp_after=4,
        expected_text_symbol="HasSubstituteText",
    ),
)


@dataclass(frozen=True)
class SelfHealMoveTurnScenario:
    scenario_id: str
    move_name: str
    move_id: int
    hp_before: int
    max_hp: int
    expected_event_type: str
    expected_blocked_reason: str | None
    expected_raw_heal: int
    expected_heal: int
    expected_hp_after: int
    expected_text_symbol: str = ""
    pp_before: int = 10


SELF_HEAL_MOVE_TURN_SCENARIOS = (
    SelfHealMoveTurnScenario(
        scenario_id="selected_self_heal_recover_half",
        move_name="RECOVER",
        move_id=RECOVER_MOVE_ID,
        hp_before=10,
        max_hp=40,
        expected_event_type="self_heal",
        expected_blocked_reason=None,
        expected_raw_heal=20,
        expected_heal=20,
        expected_hp_after=30,
        pp_before=20,
    ),
    SelfHealMoveTurnScenario(
        scenario_id="selected_self_heal_milk_drink_cap",
        move_name="MILK_DRINK",
        move_id=MILK_DRINK_MOVE_ID,
        hp_before=35,
        max_hp=40,
        expected_event_type="self_heal",
        expected_blocked_reason=None,
        expected_raw_heal=20,
        expected_heal=5,
        expected_hp_after=40,
    ),
    SelfHealMoveTurnScenario(
        scenario_id="selected_self_heal_softboiled_full_hp",
        move_name="SOFTBOILED",
        move_id=SOFTBOILED_MOVE_ID,
        hp_before=40,
        max_hp=40,
        expected_event_type="self_heal_no_effect",
        expected_blocked_reason="hp_full",
        expected_raw_heal=20,
        expected_heal=0,
        expected_hp_after=40,
        expected_text_symbol="HPIsFullText",
    ),
)


@dataclass(frozen=True)
class RestMoveTurnScenario:
    scenario_id: str
    case_name: str
    hp_before: int
    max_hp: int
    status_before: int
    toxic_flag_before: bool
    toxic_count_before: int
    expected_event_type: str
    expected_reason: str | None
    expected_hp_after: int
    expected_status_after: int
    expected_toxic_flag_after: bool
    expected_headless_status_after: str
    expected_headless_sleep_turns_after: int
    expected_headless_toxic_count_after: int
    expected_headless_final_hp: int
    expected_text_symbol: str = ""
    pp_before: int = 10


REST_MOVE_TURN_SCENARIOS = (
    RestMoveTurnScenario(
        scenario_id="selected_rest_move_toxic_full_heal",
        case_name="toxic_full_heal",
        hp_before=10,
        max_hp=40,
        status_before=PSN_STATUS,
        toxic_flag_before=True,
        toxic_count_before=2,
        expected_event_type="rest",
        expected_reason=None,
        expected_hp_after=40,
        expected_status_after=SLEEP_STATUS_BYTE_3_TURNS,
        expected_toxic_flag_after=False,
        expected_headless_status_after="sleep",
        expected_headless_sleep_turns_after=3,
        expected_headless_toxic_count_after=0,
        expected_headless_final_hp=40,
        pp_before=10,
    ),
    RestMoveTurnScenario(
        scenario_id="selected_rest_move_full_hp_no_effect_preserves_toxic",
        case_name="full_hp_no_effect",
        hp_before=40,
        max_hp=40,
        status_before=PSN_STATUS,
        toxic_flag_before=True,
        toxic_count_before=2,
        expected_event_type="rest_no_effect",
        expected_reason="hp_full",
        expected_hp_after=40,
        expected_status_after=PSN_STATUS,
        expected_toxic_flag_after=True,
        expected_headless_status_after="toxic",
        expected_headless_sleep_turns_after=0,
        expected_headless_toxic_count_after=3,
        expected_headless_final_hp=34,
        expected_text_symbol="HPIsFullText",
        pp_before=10,
    ),
)


@dataclass(frozen=True)
class AfterHitItemEffectScenario:
    scenario_id: str
    player_hp_before: int
    player_max_hp: int
    enemy_hp_before: int
    enemy_max_hp: int
    cur_damage: int
    player_item_id: int
    player_item_name: str | None
    enemy_item_id: int
    enemy_item_name: str | None
    expected_player_hp_after: int
    expected_enemy_hp_after: int
    expected_event_items: tuple[str, ...]
    expected_event_types: tuple[str, ...]
    expected_event_values: tuple[int, ...]
    call_budget: int = 700


AFTER_HIT_ITEM_EFFECT_SCENARIOS = (
    AfterHitItemEffectScenario(
        scenario_id="afterhit_rocky_helmet",
        player_hp_before=30,
        player_max_hp=30,
        enemy_hp_before=30,
        enemy_max_hp=30,
        cur_damage=16,
        player_item_id=0,
        player_item_name=None,
        enemy_item_id=ROCKY_HELMET_ITEM_ID,
        enemy_item_name="ROCKY_HELMET",
        expected_player_hp_after=25,
        expected_enemy_hp_after=30,
        expected_event_items=("ROCKY_HELMET",),
        expected_event_types=("after_hit_recoil",),
        expected_event_values=(5,),
        call_budget=500,
    ),
    AfterHitItemEffectScenario(
        scenario_id="afterhit_shell_bell",
        player_hp_before=10,
        player_max_hp=30,
        enemy_hp_before=30,
        enemy_max_hp=30,
        cur_damage=16,
        player_item_id=SHELL_BELL_ITEM_ID,
        player_item_name="SHELL_BELL",
        enemy_item_id=0,
        enemy_item_name=None,
        expected_player_hp_after=12,
        expected_enemy_hp_after=30,
        expected_event_items=("SHELL_BELL",),
        expected_event_types=("after_hit_heal",),
        expected_event_values=(2,),
        call_budget=500,
    ),
    AfterHitItemEffectScenario(
        scenario_id="afterhit_rocky_helmet_before_shell_bell",
        player_hp_before=5,
        player_max_hp=30,
        enemy_hp_before=30,
        enemy_max_hp=30,
        cur_damage=16,
        player_item_id=SHELL_BELL_ITEM_ID,
        player_item_name="SHELL_BELL",
        enemy_item_id=ROCKY_HELMET_ITEM_ID,
        enemy_item_name="ROCKY_HELMET",
        expected_player_hp_after=0,
        expected_enemy_hp_after=30,
        expected_event_items=("ROCKY_HELMET",),
        expected_event_types=("after_hit_recoil",),
        expected_event_values=(5,),
    ),
    AfterHitItemEffectScenario(
        scenario_id="afterhit_life_orb",
        player_hp_before=30,
        player_max_hp=30,
        enemy_hp_before=30,
        enemy_max_hp=30,
        cur_damage=16,
        player_item_id=LIFE_ORB_ITEM_ID,
        player_item_name="LIFE_ORB",
        enemy_item_id=0,
        enemy_item_name=None,
        expected_player_hp_after=27,
        expected_enemy_hp_after=30,
        expected_event_items=("LIFE_ORB",),
        expected_event_types=("after_hit_recoil",),
        expected_event_values=(3,),
        call_budget=500,
    ),
)


@dataclass(frozen=True)
class ResidualComponentScenario:
    scenario_id: str
    actor: str
    status_name: str
    status_byte: int
    toxic_flag: bool = False
    toxic_count_before: int = 0
    hp_before: int = 64
    max_hp: int = 64

    @property
    def expected_toxic_count_after(self) -> int:
        if not self.toxic_flag:
            return self.toxic_count_before
        return self.toxic_count_before + 1

    @property
    def expected_damage(self) -> int:
        if self.toxic_flag:
            return max(1, self.max_hp // 16) * self.expected_toxic_count_after
        return max(1, self.max_hp // 8)

    @property
    def expected_hp_after(self) -> int:
        return max(0, self.hp_before - self.expected_damage)


RESIDUAL_COMPONENT_SCENARIOS = (
    ResidualComponentScenario(
        scenario_id="component_player_poison_residual",
        actor="player",
        status_name="poison",
        status_byte=PSN_STATUS,
    ),
    ResidualComponentScenario(
        scenario_id="component_player_burn_residual",
        actor="player",
        status_name="burn",
        status_byte=BRN_STATUS,
    ),
    ResidualComponentScenario(
        scenario_id="component_player_toxic_residual_count2",
        actor="player",
        status_name="toxic",
        status_byte=PSN_STATUS,
        toxic_flag=True,
        toxic_count_before=2,
    ),
    ResidualComponentScenario(
        scenario_id="component_enemy_poison_residual",
        actor="enemy",
        status_name="poison",
        status_byte=PSN_STATUS,
    ),
    ResidualComponentScenario(
        scenario_id="component_enemy_toxic_residual_count2",
        actor="enemy",
        status_name="toxic",
        status_byte=PSN_STATUS,
        toxic_flag=True,
        toxic_count_before=2,
    ),
)


@dataclass(frozen=True)
class RomNormalHitResult:
    scenario_id: str
    move_accuracy: int
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
class RomStatusComponentResult:
    scenario_id: str
    move_name: str
    status_name: str
    status_before: int
    status_after: int
    effect_failed: bool
    effect_chance_rng: int
    effect_chance_consumed: int
    effect_chance_returned: bool
    target_command_returned: bool
    target_command_pc: int


@dataclass(frozen=True)
class RomDrainComponentResult:
    scenario_id: str
    move_name: str
    hp_before: int
    hp_after: int
    max_hp: int
    damage: int
    returned: bool
    post_pc: int


@dataclass(frozen=True)
class RomDrainMoveTurnResult:
    scenario_id: str
    move_name: str
    hp_before: int
    hp_after: int
    max_hp: int
    damage: int
    pp_before: int
    active_pp_after: int
    party_pp_after: int
    turns_taken_before: int
    turns_taken_after: int
    do_turn_returned: bool
    drain_returned: bool
    post_pc: int


@dataclass(frozen=True)
class RomItemRestoreComponentResult:
    scenario_id: str
    item_name: str
    hp_before: int
    hp_after: int
    max_hp: int
    table_amount: int
    get_amount_returned: bool
    restore_returned: bool
    hp_buffer3: int


@dataclass(frozen=True)
class RomFullRestoreStatusCureResult:
    scenario_id: str
    status_before: int
    status_after: int
    sub1_before: int
    sub1_after: int
    sub3_before: int
    sub3_after: int
    sub5_before: int
    sub5_after: int
    heal_status_returned: bool


@dataclass(frozen=True)
class RomPPDecrementComponentResult:
    scenario_id: str
    actor: str
    pp_before: int
    active_pp_after: int
    party_pp_after: int
    turns_taken_before: int
    turns_taken_after: int
    returned: bool
    post_pc: int


@dataclass(frozen=True)
class RomWeatherSetupComponentResult:
    scenario_id: str
    move_name: str
    weather_before: int
    weather_after: int
    weather_count_before: int
    weather_count_after: int
    mutation_observed: bool
    returned: bool
    ticks: int
    post_pc: int


@dataclass(frozen=True)
class RomSubstituteMoveTurnResult:
    scenario_id: str
    case_name: str
    hp_before: int
    hp_after: int
    max_hp: int
    substitute_before: bool
    substitute_after: bool
    substitute_hp_before: int
    substitute_hp_after: int
    pp_before: int
    active_pp_after: int
    party_pp_after: int
    turns_taken_before: int
    turns_taken_after: int
    do_turn_returned: bool
    substitute_branch_observed: bool
    substitute_returned: bool
    expected_text_symbol: str
    observed_text_symbol: str
    ticks: int
    post_pc: int


@dataclass(frozen=True)
class RomSelfHealMoveTurnResult:
    scenario_id: str
    move_name: str
    hp_before: int
    hp_after: int
    max_hp: int
    pp_before: int
    active_pp_after: int
    party_pp_after: int
    turns_taken_before: int
    turns_taken_after: int
    do_turn_returned: bool
    animation_skipped_for_hp_probe: bool
    heal_branch_observed: bool
    heal_returned: bool
    expected_text_symbol: str
    observed_text_symbol: str
    ticks: int
    post_pc: int


@dataclass(frozen=True)
class RomRestMoveTurnResult:
    scenario_id: str
    case_name: str
    hp_before: int
    hp_after: int
    max_hp: int
    status_before: int
    status_after: int
    toxic_substatus_before: bool
    toxic_substatus_after: bool
    toxic_count_before: int
    toxic_count_after: int
    pp_before: int
    active_pp_after: int
    party_pp_after: int
    turns_taken_before: int
    turns_taken_after: int
    do_turn_returned: bool
    animation_neutralized_for_hp_probe: bool
    rest_branch_observed: bool
    heal_returned: bool
    expected_text_symbol: str
    observed_text_symbol: str
    ticks: int
    post_pc: int


@dataclass(frozen=True)
class RomAfterHitItemEffectResult:
    scenario_id: str
    player_hp_before: int
    player_hp_after: int
    player_max_hp: int
    enemy_hp_before: int
    enemy_hp_after: int
    enemy_max_hp: int
    cur_damage: int
    returned: bool
    mutation_observed: bool
    ticks: int
    post_pc: int


@dataclass(frozen=True)
class RomResidualComponentResult:
    scenario_id: str
    actor: str
    status_name: str
    hp_before: int
    hp_after: int
    max_hp: int
    toxic_count_before: int
    toxic_count_after: int
    mutation_observed: bool
    returned: bool
    ticks: int
    post_pc: int


@dataclass(frozen=True)
class DifferentialResult:
    scenario_id: str
    ok: bool
    errors: tuple[str, ...]
    rom: dict[str, Any]
    headless: dict[str, Any]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "ok": self.ok,
            "errors": list(self.errors),
            "rom": self.rom,
            "headless": self.headless,
        }


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


def _read_hp_buffer(pyboy: Any, syms: dict[str, tuple[int, int]], name: str) -> int:
    low = _read_byte(pyboy, syms, name)
    high = _read_byte(pyboy, syms, name, 1)
    return (high << 8) | low


def _write_hp_buffer(pyboy: Any, syms: dict[str, tuple[int, int]], name: str, value: int) -> None:
    _write_byte(pyboy, syms, name, value & 0xFF)
    _write_byte(pyboy, syms, name, (value >> 8) & 0xFF, 1)


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
        "wPlayerToxicCount",
        "wEnemyToxicCount",
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


def _seed_rom_normal_hit(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: NormalHitScenario,
) -> None:
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
        (4, scenario.move_accuracy),
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
    for index, value in enumerate(scenario.rng_values):
        _write_byte(pyboy, syms, "wLinkBattleRNs", value, index)


def _seed_rom_status_component(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: StatusComponentScenario,
) -> None:
    _seed_common(pyboy, syms)

    _write_byte(pyboy, syms, "wBattleMonSpecies", 155)
    _write_byte(pyboy, syms, "wBattleMonLevel", 5)
    _write_byte(pyboy, syms, "wBattleMonType1", FIRE_TYPE)
    _write_byte(pyboy, syms, "wBattleMonType2", FIRE_TYPE)
    _write_byte(pyboy, syms, "wBattleMonItem", 0)
    _write_u16(pyboy, syms, "wBattleMonHP", 20)
    _write_u16(pyboy, syms, "wBattleMonMaxHP", 20)
    _write_u16(pyboy, syms, "wBattleMonSpeed", 11)

    _write_byte(pyboy, syms, "wEnemyMonSpecies", 16)
    _write_byte(pyboy, syms, "wEnemyMonLevel", 5)
    _write_byte(pyboy, syms, "wEnemyMonType1", NORMAL_TYPE)
    _write_byte(pyboy, syms, "wEnemyMonType2", NORMAL_TYPE)
    _write_byte(pyboy, syms, "wEnemyMonItem", 0)
    _write_u16(pyboy, syms, "wEnemyMonHP", 40)
    _write_u16(pyboy, syms, "wEnemyMonMaxHP", 40)
    _write_u16(pyboy, syms, "wEnemyMonSpeed", 7)

    _write_byte(pyboy, syms, "wCurPlayerMove", scenario.move_id)
    _write_byte(pyboy, syms, "wCurMoveNum", 0)
    _write_byte(pyboy, syms, "hBattleTurn", 0)
    _write_byte(pyboy, syms, "wBattleMode", 1)
    _write_byte(pyboy, syms, "wTypeModifier", 0x10)

    for offset, value in (
        (0, scenario.move_id),
        (1, 0),
        (2, 40),
        (3, scenario.move_type),
        (4, 0xFF),
        (5, 20),
        (6, scenario.chance_threshold),
    ):
        _write_byte(pyboy, syms, "wPlayerMoveStruct", value, offset)

    _write_byte(pyboy, syms, "wLinkMode", LINK_MODE)
    _write_byte(pyboy, syms, "wLinkBattleRNCount", 0)
    _write_byte(pyboy, syms, "wLinkBattleRNs", scenario.effect_chance_rng, 0)


def _seed_rom_drain_component(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: DrainComponentScenario,
) -> None:
    _seed_common(pyboy, syms)

    _write_byte(pyboy, syms, "wBattleMonSpecies", 155)
    _write_byte(pyboy, syms, "wBattleMonLevel", 5)
    _write_byte(pyboy, syms, "wBattleMonType1", FIRE_TYPE)
    _write_byte(pyboy, syms, "wBattleMonType2", FIRE_TYPE)
    _write_byte(pyboy, syms, "wBattleMonItem", 0)
    _write_u16(pyboy, syms, "wBattleMonHP", scenario.hp_before)
    _write_u16(pyboy, syms, "wBattleMonMaxHP", scenario.max_hp)
    _write_byte(pyboy, syms, "wCurPlayerMove", scenario.move_id)
    _write_byte(pyboy, syms, "wCurMoveNum", 0)
    _write_byte(pyboy, syms, "hBattleTurn", 0)
    _write_byte(pyboy, syms, "wBattleMode", 1)
    _write_u16(pyboy, syms, "wCurDamage", scenario.damage)


def _seed_rom_drain_move_turn(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: DrainMoveTurnScenario,
) -> None:
    _seed_common(pyboy, syms)

    _write_byte(pyboy, syms, "wBattleMode", 1)
    _write_byte(pyboy, syms, "wLinkMode", LINK_MODE)
    _write_byte(pyboy, syms, "hBattleTurn", 0)
    _write_byte(pyboy, syms, "wCurBattleMon", 0)
    _write_byte(pyboy, syms, "wCurPlayerMove", scenario.move_id)
    _write_byte(pyboy, syms, "wCurMoveNum", 0)

    _write_byte(pyboy, syms, "wBattleMonSpecies", 155)
    _write_byte(pyboy, syms, "wBattleMonLevel", 5)
    _write_byte(pyboy, syms, "wBattleMonType1", FIRE_TYPE)
    _write_byte(pyboy, syms, "wBattleMonType2", FIRE_TYPE)
    _write_byte(pyboy, syms, "wBattleMonItem", 0)
    _write_u16(pyboy, syms, "wBattleMonHP", scenario.hp_before)
    _write_u16(pyboy, syms, "wBattleMonMaxHP", scenario.max_hp)
    _write_u16(pyboy, syms, "wCurDamage", scenario.damage)

    _write_byte(pyboy, syms, "wEnemyMonSpecies", 16)
    _write_byte(pyboy, syms, "wEnemyMonLevel", 5)
    _write_byte(pyboy, syms, "wEnemyMonType1", NORMAL_TYPE)
    _write_byte(pyboy, syms, "wEnemyMonType2", NORMAL_TYPE)
    _write_byte(pyboy, syms, "wEnemyMonItem", 0)
    _write_u16(pyboy, syms, "wEnemyMonHP", scenario.headless_target_hp)
    _write_u16(pyboy, syms, "wEnemyMonMaxHP", 40)

    for offset, value in (
        (0, scenario.move_id),
        (1, 0),
        (2, 0),
        (3, NORMAL_TYPE),
        (4, 0xFF),
        (5, scenario.pp_before),
        (6, 0),
    ):
        _write_byte(pyboy, syms, "wPlayerMoveStruct", value, offset)
    _write_byte(pyboy, syms, "wBattleMonMoves", scenario.move_id, 0)
    _write_byte(pyboy, syms, "wPartyMon1Moves", scenario.move_id, 0)
    _write_byte(pyboy, syms, "wBattleMonPP", scenario.pp_before, 0)
    _write_byte(pyboy, syms, "wPartyMon1PP", scenario.pp_before, 0)
    _write_byte(pyboy, syms, "wPlayerTurnsTaken", 0)


def _seed_rom_item_restore_component(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: ItemRestoreComponentScenario,
) -> None:
    _seed_common(pyboy, syms)
    _write_byte(pyboy, syms, "wCurPartyMon", 0)
    _write_byte(pyboy, syms, "wCurItem", scenario.item_id)
    _write_u16(pyboy, syms, "wPartyMon1HP", scenario.hp_before)
    _write_u16(pyboy, syms, "wPartyMon1MaxHP", scenario.max_hp)
    # RestoreHealth expects max HP preloaded in the little-endian HP buffer.
    _write_hp_buffer(pyboy, syms, "wHPBuffer1", scenario.max_hp)


def _seed_rom_full_restore_status_cure(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: FullRestoreStatusCureScenario,
) -> None:
    _seed_common(pyboy, syms)
    _write_byte(pyboy, syms, "wCurItem", FULL_RESTORE_ITEM_ID)
    # IsItemUsedOnBattleMon needs wBattleMode != 0 and wCurPartyMon == wCurBattleMon.
    _write_byte(pyboy, syms, "wBattleMode", 1)
    _write_byte(pyboy, syms, "wCurPartyMon", 0)
    _write_byte(pyboy, syms, "wCurBattleMon", 0)
    _write_byte(pyboy, syms, "wBattleMonStatus", scenario.status_before)
    _write_byte(pyboy, syms, "wPlayerSubStatus1", scenario.sub1_before)
    _write_byte(pyboy, syms, "wPlayerSubStatus3", scenario.sub3_before)
    _write_byte(pyboy, syms, "wPlayerSubStatus5", scenario.sub5_before)


def _seed_rom_pp_decrement_component(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: PPDecrementComponentScenario,
) -> None:
    _seed_common(pyboy, syms)
    _write_byte(pyboy, syms, "wBattleMode", scenario.battle_mode)
    _write_byte(pyboy, syms, "wLinkMode", LINK_MODE)

    is_player = scenario.actor == "player"
    _write_byte(pyboy, syms, "hBattleTurn", 0 if is_player else 1)
    _write_byte(pyboy, syms, "wCurBattleMon", 0)
    _write_byte(pyboy, syms, "wCurOTMon", 0)

    move_struct = "wPlayerMoveStruct" if is_player else "wEnemyMoveStruct"
    active_moves = "wBattleMonMoves" if is_player else "wEnemyMonMoves"
    active_pp = "wBattleMonPP" if is_player else "wEnemyMonPP"
    cur_move = "wCurPlayerMove" if is_player else "wCurEnemyMove"
    cur_move_num = "wCurMoveNum" if is_player else "wCurEnemyMoveNum"

    for offset, value in (
        (0, TACKLE_MOVE_ID),
        (1, 0x00),  # EFFECT_NORMAL_HIT
        (2, 0),
        (3, NORMAL_TYPE),
        (4, 0xFF),
        (5, scenario.pp_before),
        (6, 0),
    ):
        _write_byte(pyboy, syms, move_struct, value, offset)
    _write_byte(pyboy, syms, cur_move, TACKLE_MOVE_ID)
    _write_byte(pyboy, syms, cur_move_num, 0)
    _write_byte(pyboy, syms, active_moves, TACKLE_MOVE_ID, 0)
    _write_byte(pyboy, syms, scenario.party_move_symbol, TACKLE_MOVE_ID, 0)
    _write_byte(pyboy, syms, active_pp, scenario.pp_before, 0)
    _write_byte(pyboy, syms, scenario.party_pp_symbol, scenario.pp_before, 0)
    _write_byte(pyboy, syms, scenario.turns_taken_symbol, 0)


def _seed_rom_weather_setup_component(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: WeatherSetupComponentScenario,
) -> None:
    _seed_common(pyboy, syms)
    _write_byte(pyboy, syms, "wBattleMode", 1)
    _write_byte(pyboy, syms, "wLinkMode", LINK_MODE)
    _write_byte(pyboy, syms, "hBattleTurn", 0)
    _write_byte(pyboy, syms, "wCurPlayerMove", scenario.move_id)
    _write_byte(pyboy, syms, "wCurMoveNum", 0)
    _write_byte(pyboy, syms, "wBattleMonMoves", scenario.move_id, 0)
    _write_byte(pyboy, syms, "wBattleMonPP", 5, 0)
    for offset, value in (
        (0, scenario.move_id),
        (1, 0),
        (2, 0),
        (3, NORMAL_TYPE),
        (4, 0xFF),
        (5, 5),
        (6, 0),
    ):
        _write_byte(pyboy, syms, "wPlayerMoveStruct", value, offset)
    _write_byte(pyboy, syms, "wBattleWeather", 0)
    _write_byte(pyboy, syms, "wWeatherCount", 0)


def _seed_rom_substitute_move_turn(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: SubstituteMoveTurnScenario,
) -> None:
    _seed_common(pyboy, syms)
    _write_byte(pyboy, syms, "wBattleMode", 1)
    _write_byte(pyboy, syms, "wLinkMode", LINK_MODE)
    _write_byte(pyboy, syms, "hBattleTurn", 0)
    _write_byte(pyboy, syms, "wCurBattleMon", 0)
    _write_byte(pyboy, syms, "wCurPlayerMove", SUBSTITUTE_MOVE_ID)
    _write_byte(pyboy, syms, "wCurMoveNum", 0)

    _write_u16(pyboy, syms, "wBattleMonHP", scenario.hp_before)
    _write_u16(pyboy, syms, "wBattleMonMaxHP", scenario.max_hp)
    _write_byte(
        pyboy,
        syms,
        "wPlayerSubStatus4",
        (1 << SUBSTATUS_SUBSTITUTE_BIT) if scenario.substitute_before else 0,
    )
    _write_byte(pyboy, syms, "wPlayerSubstituteHP", scenario.substitute_hp_before)

    for offset, value in (
        (0, SUBSTITUTE_MOVE_ID),
        (1, 0),
        (2, 0),
        (3, NORMAL_TYPE),
        (4, 0xFF),
        (5, scenario.pp_before),
        (6, 0),
    ):
        _write_byte(pyboy, syms, "wPlayerMoveStruct", value, offset)
    _write_byte(pyboy, syms, "wBattleMonMoves", SUBSTITUTE_MOVE_ID, 0)
    _write_byte(pyboy, syms, "wPartyMon1Moves", SUBSTITUTE_MOVE_ID, 0)
    _write_byte(pyboy, syms, "wBattleMonPP", scenario.pp_before, 0)
    _write_byte(pyboy, syms, "wPartyMon1PP", scenario.pp_before, 0)
    _write_byte(pyboy, syms, "wPlayerTurnsTaken", 0)


def _seed_rom_self_heal_move_turn(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: SelfHealMoveTurnScenario,
) -> None:
    _seed_common(pyboy, syms)
    _write_byte(pyboy, syms, "wBattleMode", 1)
    _write_byte(pyboy, syms, "wLinkMode", LINK_MODE)
    _write_byte(pyboy, syms, "hBattleTurn", 0)
    _write_byte(pyboy, syms, "wCurBattleMon", 0)
    _write_byte(pyboy, syms, "wCurPlayerMove", scenario.move_id)
    _write_byte(pyboy, syms, "wCurMoveNum", 0)

    _write_u16(pyboy, syms, "wBattleMonHP", scenario.hp_before)
    _write_u16(pyboy, syms, "wBattleMonMaxHP", scenario.max_hp)

    for offset, value in (
        (0, scenario.move_id),
        (1, 0),
        (2, 0),
        (3, NORMAL_TYPE),
        (4, 0xFF),
        (5, scenario.pp_before),
        (6, 0),
    ):
        _write_byte(pyboy, syms, "wPlayerMoveStruct", value, offset)
    _write_byte(pyboy, syms, "wBattleMonMoves", scenario.move_id, 0)
    _write_byte(pyboy, syms, "wPartyMon1Moves", scenario.move_id, 0)
    _write_byte(pyboy, syms, "wBattleMonPP", scenario.pp_before, 0)
    _write_byte(pyboy, syms, "wPartyMon1PP", scenario.pp_before, 0)
    _write_byte(pyboy, syms, "wPlayerTurnsTaken", 0)


def _seed_rom_rest_move_turn(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: RestMoveTurnScenario,
) -> None:
    _seed_common(pyboy, syms)
    _write_byte(pyboy, syms, "wBattleMode", 1)
    _write_byte(pyboy, syms, "wLinkMode", LINK_MODE)
    _write_byte(pyboy, syms, "hBattleTurn", 0)
    _write_byte(pyboy, syms, "wCurBattleMon", 0)
    _write_byte(pyboy, syms, "wCurPlayerMove", REST_MOVE_ID)
    _write_byte(pyboy, syms, "wCurMoveNum", 0)

    _write_u16(pyboy, syms, "wBattleMonHP", scenario.hp_before)
    _write_u16(pyboy, syms, "wBattleMonMaxHP", scenario.max_hp)
    _write_byte(pyboy, syms, "wBattleMonStatus", scenario.status_before)
    _write_byte(
        pyboy,
        syms,
        "wPlayerSubStatus5",
        (1 << SUBSTATUS_TOXIC_BIT) if scenario.toxic_flag_before else 0,
    )
    _write_byte(pyboy, syms, "wPlayerToxicCount", scenario.toxic_count_before)

    for offset, value in (
        (0, REST_MOVE_ID),
        (1, 0),
        (2, 0),
        (3, NORMAL_TYPE),
        (4, 0xFF),
        (5, scenario.pp_before),
        (6, 0),
    ):
        _write_byte(pyboy, syms, "wPlayerMoveStruct", value, offset)
    _write_byte(pyboy, syms, "wBattleMonMoves", REST_MOVE_ID, 0)
    _write_byte(pyboy, syms, "wPartyMon1Moves", REST_MOVE_ID, 0)
    _write_byte(pyboy, syms, "wBattleMonPP", scenario.pp_before, 0)
    _write_byte(pyboy, syms, "wPartyMon1PP", scenario.pp_before, 0)
    _write_byte(pyboy, syms, "wPlayerTurnsTaken", 0)


def _seed_rom_after_hit_item_effect(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: AfterHitItemEffectScenario,
) -> None:
    _seed_common(pyboy, syms)
    _write_byte(pyboy, syms, "wBattleMode", 1)
    _write_byte(pyboy, syms, "wLinkMode", LINK_MODE)
    _write_byte(pyboy, syms, "hBattleTurn", 0)
    _write_byte(pyboy, syms, "wCurBattleMon", 0)
    _write_byte(pyboy, syms, "wCurPlayerMove", TACKLE_MOVE_ID)
    _write_byte(pyboy, syms, "wCurMoveNum", 0)

    _write_byte(pyboy, syms, "wBattleMonItem", scenario.player_item_id)
    _write_byte(pyboy, syms, "wEnemyMonItem", scenario.enemy_item_id)
    _write_u16(pyboy, syms, "wBattleMonHP", scenario.player_hp_before)
    _write_u16(pyboy, syms, "wBattleMonMaxHP", scenario.player_max_hp)
    _write_u16(pyboy, syms, "wEnemyMonHP", scenario.enemy_hp_before)
    _write_u16(pyboy, syms, "wEnemyMonMaxHP", scenario.enemy_max_hp)
    _write_u16(pyboy, syms, "wCurDamage", scenario.cur_damage)
    _write_byte(pyboy, syms, "wPlayerSubStatus4", 0)
    _write_byte(pyboy, syms, "wEnemySubStatus4", 0)

    for offset, value in (
        (0, TACKLE_MOVE_ID),
        (1, 0),
        (2, 40),
        (3, NORMAL_TYPE),
        (4, 0xFF),
        (5, 35),
        (6, 0),
    ):
        _write_byte(pyboy, syms, "wPlayerMoveStruct", value, offset)


def _seed_rom_residual_component(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: ResidualComponentScenario,
) -> None:
    _seed_common(pyboy, syms)
    _write_byte(pyboy, syms, "wBattleMode", 1)
    _write_byte(pyboy, syms, "wLinkMode", LINK_MODE)
    _write_byte(pyboy, syms, "hBattleTurn", 0 if scenario.actor == "player" else 1)

    _write_u16(pyboy, syms, "wBattleMonHP", scenario.hp_before)
    _write_u16(pyboy, syms, "wBattleMonMaxHP", scenario.max_hp)
    _write_u16(pyboy, syms, "wEnemyMonHP", scenario.hp_before)
    _write_u16(pyboy, syms, "wEnemyMonMaxHP", scenario.max_hp)

    if scenario.actor == "player":
        _write_byte(pyboy, syms, "wBattleMonStatus", scenario.status_byte)
        _write_byte(
            pyboy,
            syms,
            "wPlayerSubStatus5",
            (1 << SUBSTATUS_TOXIC_BIT) if scenario.toxic_flag else 0,
        )
        _write_byte(pyboy, syms, "wPlayerToxicCount", scenario.toxic_count_before)
    else:
        _write_byte(pyboy, syms, "wEnemyMonStatus", scenario.status_byte)
        _write_byte(
            pyboy,
            syms,
            "wEnemySubStatus5",
            (1 << SUBSTATUS_TOXIC_BIT) if scenario.toxic_flag else 0,
        )
        _write_byte(pyboy, syms, "wEnemyToxicCount", scenario.toxic_count_before)


def _residual_hp(pyboy: Any, syms: dict[str, tuple[int, int]], actor: str) -> int:
    return _read_u16(pyboy, syms, "wBattleMonHP" if actor == "player" else "wEnemyMonHP")


def _residual_toxic_count(pyboy: Any, syms: dict[str, tuple[int, int]], actor: str) -> int:
    return _read_byte(pyboy, syms, "wPlayerToxicCount" if actor == "player" else "wEnemyToxicCount")


def _player_substitute_active(pyboy: Any, syms: dict[str, tuple[int, int]]) -> bool:
    return bool(_read_byte(pyboy, syms, "wPlayerSubStatus4") & (1 << SUBSTATUS_SUBSTITUTE_BIT))


def _player_toxic_substatus_active(pyboy: Any, syms: dict[str, tuple[int, int]]) -> bool:
    return bool(_read_byte(pyboy, syms, "wPlayerSubStatus5") & (1 << SUBSTATUS_TOXIC_BIT))


def _mark_hook_observed(context: dict[str, Any]) -> None:
    context["observed"] = True


def _mark_rest_got_stats_and_neutralize_animation(context: dict[str, Any]) -> None:
    context["observed"] = True
    _write_byte(context["pyboy"], context["syms"], "wPlayerMoveStruct", 0, 0)


def _call_function_with_ei_until(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    name: str,
    predicate: Any,
    *,
    budget: int,
) -> tuple[int, bool, bool, int]:
    target_bank, target_addr = syms[name]
    rf = pyboy.register_file

    pyboy.memory[EI_STUB_ADDR] = 0xFB  # ei
    pyboy.memory[EI_STUB_ADDR + 1] = 0xC3  # jp nn
    pyboy.memory[EI_STUB_ADDR + 2] = target_addr & 0xFF
    pyboy.memory[EI_STUB_ADDR + 3] = (target_addr >> 8) & 0xFF
    pyboy.memory[SENTINEL_ADDR] = 0x18
    pyboy.memory[SENTINEL_ADDR + 1] = 0xFE

    sp = int(rf.SP)
    new_sp = (sp - 2) & 0xFFFF
    pyboy.memory[new_sp] = SENTINEL_ADDR & 0xFF
    pyboy.memory[new_sp + 1] = (SENTINEL_ADDR >> 8) & 0xFF
    rf.SP = new_sp
    rf.PC = EI_STUB_ADDR

    rom_bank_sym = syms.get("hROMBank")
    if rom_bank_sym:
        pyboy.memory[rom_bank_sym[1]] = target_bank
    pyboy.memory[0x2000] = target_bank

    ticked = 0
    while ticked < budget:
        pyboy.tick(2, False, False)
        ticked += 2
        pc = int(rf.PC)
        if predicate():
            return ticked, True, pc in {SENTINEL_ADDR, SENTINEL_ADDR + 2}, pc
        if pc in {SENTINEL_ADDR, SENTINEL_ADDR + 2}:
            return ticked, False, True, pc
    return ticked, False, False, int(rf.PC)


def run_rom_normal_hit(scenario: NormalHitScenario = DEFAULT_NORMAL_HIT_SCENARIO) -> RomNormalHitResult:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    try:
        pyboy = cache.restore()
        _seed_rom_normal_hit(pyboy, syms, scenario)
        player_hp_before = _read_u16(pyboy, syms, "wBattleMonHP")
        enemy_pp_before = _read_byte(pyboy, syms, "wEnemyMonPP")
        command_returns: dict[str, bool] = {}
        for command in NORMAL_HIT_CHAIN:
            _, returned, _ = call_function_safe(pyboy, syms, command, budget=CALL_BUDGET)
            command_returns[command] = returned
        return RomNormalHitResult(
            scenario_id=scenario.rom_scenario_id,
            move_accuracy=scenario.move_accuracy,
            player_hp_before=player_hp_before,
            player_hp_after=_read_u16(pyboy, syms, "wBattleMonHP"),
            enemy_pp_before=enemy_pp_before,
            enemy_pp_after=_read_byte(pyboy, syms, "wEnemyMonPP"),
            damage=_read_u16(pyboy, syms, "wCurDamage"),
            attack_missed=bool(_read_byte(pyboy, syms, "wAttackMissed")),
            critical=bool(_read_byte(pyboy, syms, "wCriticalHit")),
            rng_values=scenario.rng_values,
            rng_consumed=_read_byte(pyboy, syms, "wLinkBattleRNCount"),
            command_returns=command_returns,
        )
    finally:
        cache.stop()


def run_rom_status_components() -> tuple[RomStatusComponentResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomStatusComponentResult] = []
    try:
        for scenario in STATUS_COMPONENT_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_status_component(pyboy, syms, scenario)
            status_before = _read_byte(pyboy, syms, "wEnemyMonStatus")
            _, effect_returned, _ = call_function_safe(
                pyboy,
                syms,
                "BattleCommand_EffectChance",
                budget=CALL_BUDGET,
            )
            _, target_returned, target_pc = call_function_safe(
                pyboy,
                syms,
                scenario.target_command,
                budget=COMPONENT_NONRETURN_CALL_BUDGET,
            )
            results.append(
                RomStatusComponentResult(
                    scenario_id=scenario.scenario_id,
                    move_name=scenario.move_name,
                    status_name=scenario.status_name,
                    status_before=status_before,
                    status_after=_read_byte(pyboy, syms, "wEnemyMonStatus"),
                    effect_failed=bool(_read_byte(pyboy, syms, "wEffectFailed")),
                    effect_chance_rng=scenario.effect_chance_rng,
                    effect_chance_consumed=_read_byte(pyboy, syms, "wLinkBattleRNCount"),
                    effect_chance_returned=effect_returned,
                    target_command_returned=target_returned,
                    target_command_pc=target_pc,
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def run_rom_drain_components() -> tuple[RomDrainComponentResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomDrainComponentResult] = []
    try:
        for scenario in DRAIN_COMPONENT_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_drain_component(pyboy, syms, scenario)
            hp_before = _read_u16(pyboy, syms, "wBattleMonHP")
            _, returned, post_pc = call_function_safe(
                pyboy,
                syms,
                "BattleCommand_DrainTarget",
                budget=COMPONENT_NONRETURN_CALL_BUDGET,
            )
            results.append(
                RomDrainComponentResult(
                    scenario_id=scenario.scenario_id,
                    move_name=scenario.move_name,
                    hp_before=hp_before,
                    hp_after=_read_u16(pyboy, syms, "wBattleMonHP"),
                    max_hp=_read_u16(pyboy, syms, "wBattleMonMaxHP"),
                    damage=_read_u16(pyboy, syms, "wCurDamage"),
                    returned=returned,
                    post_pc=post_pc,
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def run_rom_drain_move_turns() -> tuple[RomDrainMoveTurnResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomDrainMoveTurnResult] = []
    try:
        for scenario in DRAIN_MOVE_TURN_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_drain_move_turn(pyboy, syms, scenario)
            hp_before = _read_u16(pyboy, syms, "wBattleMonHP")
            turns_taken_before = _read_byte(pyboy, syms, "wPlayerTurnsTaken")

            _, do_turn_returned, _ = call_function_safe(
                pyboy,
                syms,
                "BattleCommand_DoTurn",
                budget=CALL_BUDGET,
            )
            _, drain_returned, post_pc = call_function_safe(
                pyboy,
                syms,
                "BattleCommand_DrainTarget",
                budget=COMPONENT_NONRETURN_CALL_BUDGET,
            )
            results.append(
                RomDrainMoveTurnResult(
                    scenario_id=scenario.scenario_id,
                    move_name=scenario.move_name,
                    hp_before=hp_before,
                    hp_after=_read_u16(pyboy, syms, "wBattleMonHP"),
                    max_hp=_read_u16(pyboy, syms, "wBattleMonMaxHP"),
                    damage=_read_u16(pyboy, syms, "wCurDamage"),
                    pp_before=scenario.pp_before,
                    active_pp_after=_read_byte(pyboy, syms, "wBattleMonPP"),
                    party_pp_after=_read_byte(pyboy, syms, "wPartyMon1PP"),
                    turns_taken_before=turns_taken_before,
                    turns_taken_after=_read_byte(pyboy, syms, "wPlayerTurnsTaken"),
                    do_turn_returned=do_turn_returned,
                    drain_returned=drain_returned,
                    post_pc=post_pc,
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def run_rom_full_restore_status_cures() -> tuple[RomFullRestoreStatusCureResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomFullRestoreStatusCureResult] = []
    try:
        for scenario in FULL_RESTORE_STATUS_CURE_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_full_restore_status_cure(pyboy, syms, scenario)
            status_before = _read_byte(pyboy, syms, "wBattleMonStatus")
            sub1_before = _read_byte(pyboy, syms, "wPlayerSubStatus1")
            sub3_before = _read_byte(pyboy, syms, "wPlayerSubStatus3")
            sub5_before = _read_byte(pyboy, syms, "wPlayerSubStatus5")
            # HealStatus farcalls CalcPlayerStats at the end, which depends on
            # party/stat state that this proof intentionally does not seed.
            # The status + sub-status clears happen BEFORE the farcall, so we
            # assert against those bytes regardless of whether HealStatus
            # fully returns within the call budget.
            _, heal_returned, _ = call_function_safe(
                pyboy,
                syms,
                "HealStatus",
                budget=CALL_BUDGET,
            )
            results.append(
                RomFullRestoreStatusCureResult(
                    scenario_id=scenario.scenario_id,
                    status_before=status_before,
                    status_after=_read_byte(pyboy, syms, "wBattleMonStatus"),
                    sub1_before=sub1_before,
                    sub1_after=_read_byte(pyboy, syms, "wPlayerSubStatus1"),
                    sub3_before=sub3_before,
                    sub3_after=_read_byte(pyboy, syms, "wPlayerSubStatus3"),
                    sub5_before=sub5_before,
                    sub5_after=_read_byte(pyboy, syms, "wPlayerSubStatus5"),
                    heal_status_returned=heal_returned,
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def run_rom_pp_decrement_components() -> tuple[RomPPDecrementComponentResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomPPDecrementComponentResult] = []
    try:
        for scenario in PP_DECREMENT_COMPONENT_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_pp_decrement_component(pyboy, syms, scenario)
            is_player = scenario.actor == "player"
            active_pp = "wBattleMonPP" if is_player else "wEnemyMonPP"
            turns_taken_before = _read_byte(pyboy, syms, scenario.turns_taken_symbol)
            _, returned, post_pc = call_function_safe(
                pyboy,
                syms,
                "BattleCommand_DoTurn",
                budget=CALL_BUDGET,
            )
            results.append(
                RomPPDecrementComponentResult(
                    scenario_id=scenario.scenario_id,
                    actor=scenario.actor,
                    pp_before=scenario.pp_before,
                    active_pp_after=_read_byte(pyboy, syms, active_pp),
                    party_pp_after=_read_byte(pyboy, syms, scenario.party_pp_symbol),
                    turns_taken_before=turns_taken_before,
                    turns_taken_after=_read_byte(pyboy, syms, scenario.turns_taken_symbol),
                    returned=returned,
                    post_pc=post_pc,
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def run_rom_weather_setup_components() -> tuple[RomWeatherSetupComponentResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomWeatherSetupComponentResult] = []
    try:
        for scenario in WEATHER_SETUP_COMPONENT_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_weather_setup_component(pyboy, syms, scenario)
            weather_before = _read_byte(pyboy, syms, "wBattleWeather")
            weather_count_before = _read_byte(pyboy, syms, "wWeatherCount")

            def observed_weather_setup() -> bool:
                return (
                    _read_byte(pyboy, syms, "wBattleWeather") == scenario.expected_weather
                    and _read_byte(pyboy, syms, "wWeatherCount") == 5
                )

            ticks, observed, returned, post_pc = _call_function_with_ei_until(
                pyboy,
                syms,
                scenario.command,
                observed_weather_setup,
                budget=COMPONENT_NONRETURN_CALL_BUDGET,
            )
            results.append(
                RomWeatherSetupComponentResult(
                    scenario_id=scenario.scenario_id,
                    move_name=scenario.move_name,
                    weather_before=weather_before,
                    weather_after=_read_byte(pyboy, syms, "wBattleWeather"),
                    weather_count_before=weather_count_before,
                    weather_count_after=_read_byte(pyboy, syms, "wWeatherCount"),
                    mutation_observed=observed,
                    returned=returned,
                    ticks=ticks,
                    post_pc=post_pc,
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def run_rom_substitute_move_turns() -> tuple[RomSubstituteMoveTurnResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomSubstituteMoveTurnResult] = []
    try:
        for scenario in SUBSTITUTE_MOVE_TURN_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_substitute_move_turn(pyboy, syms, scenario)
            hp_before = _read_u16(pyboy, syms, "wBattleMonHP")
            substitute_before = _player_substitute_active(pyboy, syms)
            substitute_hp_before = _read_byte(pyboy, syms, "wPlayerSubstituteHP")
            turns_taken_before = _read_byte(pyboy, syms, "wPlayerTurnsTaken")

            _, do_turn_returned, _ = call_function_safe(
                pyboy,
                syms,
                "BattleCommand_DoTurn",
                budget=CALL_BUDGET,
            )

            hook_symbol_by_text = {
                "HasSubstituteText": "BattleCommand_Substitute.already_has_sub",
                "TooWeakSubText": "BattleCommand_Substitute.too_weak_to_sub",
            }
            hook_symbol = (
                hook_symbol_by_text[scenario.expected_text_symbol]
                if scenario.expected_text_symbol
                else None
            )
            hook_context: dict[str, Any] = {"observed": False}
            if hook_symbol:
                hook_bank, hook_addr = syms[hook_symbol]
                pyboy.hook_register(hook_bank, hook_addr, _mark_hook_observed, hook_context)

            def observed_substitute_branch() -> bool:
                if scenario.expected_event_type == "substitute_create":
                    return (
                        _read_u16(pyboy, syms, "wBattleMonHP") == scenario.expected_hp_after
                        and _player_substitute_active(pyboy, syms) is scenario.expected_substitute_after
                        and _read_byte(pyboy, syms, "wPlayerSubstituteHP")
                        == scenario.expected_substitute_hp_after
                    )
                return bool(hook_context["observed"])

            try:
                ticks, branch_observed, substitute_returned, post_pc = _call_function_with_ei_until(
                    pyboy,
                    syms,
                    "BattleCommand_Substitute",
                    observed_substitute_branch,
                    budget=CALL_BUDGET,
                )
            finally:
                if hook_symbol:
                    hook_bank, hook_addr = syms[hook_symbol]
                    pyboy.hook_deregister(hook_bank, hook_addr)
            observed_text_symbol = scenario.expected_text_symbol if hook_context["observed"] else ""

            results.append(
                RomSubstituteMoveTurnResult(
                    scenario_id=scenario.scenario_id,
                    case_name=scenario.case_name,
                    hp_before=hp_before,
                    hp_after=_read_u16(pyboy, syms, "wBattleMonHP"),
                    max_hp=_read_u16(pyboy, syms, "wBattleMonMaxHP"),
                    substitute_before=substitute_before,
                    substitute_after=_player_substitute_active(pyboy, syms),
                    substitute_hp_before=substitute_hp_before,
                    substitute_hp_after=_read_byte(pyboy, syms, "wPlayerSubstituteHP"),
                    pp_before=scenario.pp_before,
                    active_pp_after=_read_byte(pyboy, syms, "wBattleMonPP"),
                    party_pp_after=_read_byte(pyboy, syms, "wPartyMon1PP"),
                    turns_taken_before=turns_taken_before,
                    turns_taken_after=_read_byte(pyboy, syms, "wPlayerTurnsTaken"),
                    do_turn_returned=do_turn_returned,
                    substitute_branch_observed=branch_observed,
                    substitute_returned=substitute_returned,
                    expected_text_symbol=scenario.expected_text_symbol,
                    observed_text_symbol=observed_text_symbol,
                    ticks=ticks,
                    post_pc=post_pc,
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def run_rom_self_heal_move_turns() -> tuple[RomSelfHealMoveTurnResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomSelfHealMoveTurnResult] = []
    try:
        for scenario in SELF_HEAL_MOVE_TURN_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_self_heal_move_turn(pyboy, syms, scenario)
            hp_before = _read_u16(pyboy, syms, "wBattleMonHP")
            turns_taken_before = _read_byte(pyboy, syms, "wPlayerTurnsTaken")

            _, do_turn_returned, _ = call_function_safe(
                pyboy,
                syms,
                "BattleCommand_DoTurn",
                budget=CALL_BUDGET,
            )
            animation_skipped_for_hp_probe = scenario.expected_event_type == "self_heal"
            if animation_skipped_for_hp_probe:
                _write_byte(pyboy, syms, "wPlayerMoveStruct", 0, 0)

            hook_symbol = "BattleCommand_Heal.hp_full" if scenario.expected_text_symbol else ""
            hook_context: dict[str, Any] = {"observed": False}
            if hook_symbol:
                hook_bank, hook_addr = syms[hook_symbol]
                pyboy.hook_register(hook_bank, hook_addr, _mark_hook_observed, hook_context)

            def observed_heal_branch() -> bool:
                if scenario.expected_event_type == "self_heal":
                    return _read_u16(pyboy, syms, "wBattleMonHP") == scenario.expected_hp_after
                return bool(hook_context["observed"])

            try:
                ticks, branch_observed, heal_returned, post_pc = _call_function_with_ei_until(
                    pyboy,
                    syms,
                    "BattleCommand_Heal",
                    observed_heal_branch,
                    budget=CALL_BUDGET,
                )
            finally:
                if hook_symbol:
                    hook_bank, hook_addr = syms[hook_symbol]
                    pyboy.hook_deregister(hook_bank, hook_addr)
            observed_text_symbol = scenario.expected_text_symbol if hook_context["observed"] else ""

            results.append(
                RomSelfHealMoveTurnResult(
                    scenario_id=scenario.scenario_id,
                    move_name=scenario.move_name,
                    hp_before=hp_before,
                    hp_after=_read_u16(pyboy, syms, "wBattleMonHP"),
                    max_hp=_read_u16(pyboy, syms, "wBattleMonMaxHP"),
                    pp_before=scenario.pp_before,
                    active_pp_after=_read_byte(pyboy, syms, "wBattleMonPP"),
                    party_pp_after=_read_byte(pyboy, syms, "wPartyMon1PP"),
                    turns_taken_before=turns_taken_before,
                    turns_taken_after=_read_byte(pyboy, syms, "wPlayerTurnsTaken"),
                    do_turn_returned=do_turn_returned,
                    animation_skipped_for_hp_probe=animation_skipped_for_hp_probe,
                    heal_branch_observed=branch_observed,
                    heal_returned=heal_returned,
                    expected_text_symbol=scenario.expected_text_symbol,
                    observed_text_symbol=observed_text_symbol,
                    ticks=ticks,
                    post_pc=post_pc,
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def run_rom_rest_move_turns() -> tuple[RomRestMoveTurnResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomRestMoveTurnResult] = []
    try:
        for scenario in REST_MOVE_TURN_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_rest_move_turn(pyboy, syms, scenario)
            hp_before = _read_u16(pyboy, syms, "wBattleMonHP")
            status_before = _read_byte(pyboy, syms, "wBattleMonStatus")
            toxic_substatus_before = _player_toxic_substatus_active(pyboy, syms)
            toxic_count_before = _read_byte(pyboy, syms, "wPlayerToxicCount")
            turns_taken_before = _read_byte(pyboy, syms, "wPlayerTurnsTaken")

            _, do_turn_returned, _ = call_function_safe(
                pyboy,
                syms,
                "BattleCommand_DoTurn",
                budget=CALL_BUDGET,
            )

            animation_neutralized = scenario.expected_event_type == "rest"
            hook_symbol = (
                "BattleCommand_Heal.got_stats"
                if animation_neutralized
                else "BattleCommand_Heal.hp_full"
            )
            hook_context: dict[str, Any] = {
                "observed": False,
                "pyboy": pyboy,
                "syms": syms,
            }
            hook_bank, hook_addr = syms[hook_symbol]
            hook_callback = (
                _mark_rest_got_stats_and_neutralize_animation
                if animation_neutralized
                else _mark_hook_observed
            )
            pyboy.hook_register(hook_bank, hook_addr, hook_callback, hook_context)

            def observed_rest_branch() -> bool:
                if scenario.expected_event_type == "rest":
                    return (
                        bool(hook_context["observed"])
                        and _read_u16(pyboy, syms, "wBattleMonHP") == scenario.expected_hp_after
                        and _read_byte(pyboy, syms, "wBattleMonStatus")
                        == scenario.expected_status_after
                        and _player_toxic_substatus_active(pyboy, syms)
                        is scenario.expected_toxic_flag_after
                    )
                return bool(hook_context["observed"])

            try:
                ticks, branch_observed, heal_returned, post_pc = _call_function_with_ei_until(
                    pyboy,
                    syms,
                    "BattleCommand_Heal",
                    observed_rest_branch,
                    budget=CALL_BUDGET,
                )
            finally:
                pyboy.hook_deregister(hook_bank, hook_addr)
            observed_text_symbol = scenario.expected_text_symbol if hook_context["observed"] else ""

            results.append(
                RomRestMoveTurnResult(
                    scenario_id=scenario.scenario_id,
                    case_name=scenario.case_name,
                    hp_before=hp_before,
                    hp_after=_read_u16(pyboy, syms, "wBattleMonHP"),
                    max_hp=_read_u16(pyboy, syms, "wBattleMonMaxHP"),
                    status_before=status_before,
                    status_after=_read_byte(pyboy, syms, "wBattleMonStatus"),
                    toxic_substatus_before=toxic_substatus_before,
                    toxic_substatus_after=_player_toxic_substatus_active(pyboy, syms),
                    toxic_count_before=toxic_count_before,
                    toxic_count_after=_read_byte(pyboy, syms, "wPlayerToxicCount"),
                    pp_before=scenario.pp_before,
                    active_pp_after=_read_byte(pyboy, syms, "wBattleMonPP"),
                    party_pp_after=_read_byte(pyboy, syms, "wPartyMon1PP"),
                    turns_taken_before=turns_taken_before,
                    turns_taken_after=_read_byte(pyboy, syms, "wPlayerTurnsTaken"),
                    do_turn_returned=do_turn_returned,
                    animation_neutralized_for_hp_probe=animation_neutralized,
                    rest_branch_observed=branch_observed,
                    heal_returned=heal_returned,
                    expected_text_symbol=scenario.expected_text_symbol,
                    observed_text_symbol=observed_text_symbol,
                    ticks=ticks,
                    post_pc=post_pc,
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def run_rom_after_hit_item_effects() -> tuple[RomAfterHitItemEffectResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomAfterHitItemEffectResult] = []
    try:
        for scenario in AFTER_HIT_ITEM_EFFECT_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_after_hit_item_effect(pyboy, syms, scenario)
            player_hp_before = _read_u16(pyboy, syms, "wBattleMonHP")
            enemy_hp_before = _read_u16(pyboy, syms, "wEnemyMonHP")

            def observed_after_hit_mutation() -> bool:
                return (
                    _read_u16(pyboy, syms, "wBattleMonHP") == scenario.expected_player_hp_after
                    and _read_u16(pyboy, syms, "wEnemyMonHP") == scenario.expected_enemy_hp_after
                )

            ticks, observed, returned, post_pc = _call_function_with_ei_until(
                pyboy,
                syms,
                "HandleLateGenAfterHitEffects_Far",
                observed_after_hit_mutation,
                budget=scenario.call_budget,
            )
            results.append(
                RomAfterHitItemEffectResult(
                    scenario_id=scenario.scenario_id,
                    player_hp_before=player_hp_before,
                    player_hp_after=_read_u16(pyboy, syms, "wBattleMonHP"),
                    player_max_hp=_read_u16(pyboy, syms, "wBattleMonMaxHP"),
                    enemy_hp_before=enemy_hp_before,
                    enemy_hp_after=_read_u16(pyboy, syms, "wEnemyMonHP"),
                    enemy_max_hp=_read_u16(pyboy, syms, "wEnemyMonMaxHP"),
                    cur_damage=_read_u16(pyboy, syms, "wCurDamage"),
                    returned=returned,
                    mutation_observed=observed,
                    ticks=ticks,
                    post_pc=post_pc,
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def run_rom_residual_components() -> tuple[RomResidualComponentResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomResidualComponentResult] = []
    try:
        for scenario in RESIDUAL_COMPONENT_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_residual_component(pyboy, syms, scenario)
            hp_before = _residual_hp(pyboy, syms, scenario.actor)
            toxic_before = _residual_toxic_count(pyboy, syms, scenario.actor)

            def observed_residual_mutation() -> bool:
                return (
                    _residual_hp(pyboy, syms, scenario.actor) == scenario.expected_hp_after
                    and _residual_toxic_count(pyboy, syms, scenario.actor)
                    == scenario.expected_toxic_count_after
                )

            ticks, observed, returned, post_pc = _call_function_with_ei_until(
                pyboy,
                syms,
                "ResidualDamage",
                observed_residual_mutation,
                budget=RESIDUAL_CALL_BUDGET,
            )
            results.append(
                RomResidualComponentResult(
                    scenario_id=scenario.scenario_id,
                    actor=scenario.actor,
                    status_name=scenario.status_name,
                    hp_before=hp_before,
                    hp_after=_residual_hp(pyboy, syms, scenario.actor),
                    max_hp=scenario.max_hp,
                    toxic_count_before=toxic_before,
                    toxic_count_after=_residual_toxic_count(pyboy, syms, scenario.actor),
                    mutation_observed=observed,
                    returned=returned,
                    ticks=ticks,
                    post_pc=post_pc,
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def run_rom_item_restore_components() -> tuple[RomItemRestoreComponentResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomItemRestoreComponentResult] = []
    try:
        for scenario in ITEM_RESTORE_COMPONENT_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_item_restore_component(pyboy, syms, scenario)
            hp_before = _read_u16(pyboy, syms, "wPartyMon1HP")
            _, get_amount_returned, _ = call_function_safe(
                pyboy,
                syms,
                "GetHealingItemAmount",
                budget=CALL_BUDGET,
            )
            rf = pyboy.register_file
            table_amount = (int(rf.D) << 8) | int(rf.E)
            _, restore_returned, _ = call_function_safe(
                pyboy,
                syms,
                "RestoreHealth",
                budget=CALL_BUDGET,
            )
            results.append(
                RomItemRestoreComponentResult(
                    scenario_id=scenario.scenario_id,
                    item_name=scenario.item_name,
                    hp_before=hp_before,
                    hp_after=_read_u16(pyboy, syms, "wPartyMon1HP"),
                    max_hp=_read_u16(pyboy, syms, "wPartyMon1MaxHP"),
                    table_amount=table_amount,
                    get_amount_returned=get_amount_returned,
                    restore_returned=restore_returned,
                    hp_buffer3=_read_hp_buffer(pyboy, syms, "wHPBuffer3"),
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def normal_hit_payload(scenario: NormalHitScenario = DEFAULT_NORMAL_HIT_SCENARIO) -> dict[str, Any]:
    return {
        "rng": {"mode": "fixed", "values": list(scenario.rng_values)},
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
                        "accuracy": scenario.move_accuracy,
                        "pp": 35,
                    }
                ],
            },
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def damaging_status_component_payload(scenario: StatusComponentScenario) -> dict[str, Any]:
    return {
        "rng": {"mode": "fixed", "values": list(scenario.headless_rng_values)},
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
                "moves": [{"name": scenario.move_name}],
            },
            "enemy": {
                "species": "PIDGEY",
                "level": 5,
                "types": ["NORMAL", "NORMAL"],
                "hp": 40,
                "max_hp": 40,
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
                        "bp": 0,
                        "priority": 0,
                        "accuracy": 255,
                        "pp": 35,
                    }
                ],
            },
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def drain_component_payload(scenario: DrainComponentScenario) -> dict[str, Any]:
    return {
        "rng": {"mode": "fixed", "values": [255, 255]},
        "state": {
            "weather": "none",
            "weather_count": 0,
            "turn": 1,
            "player": {
                "species": "CYNDAQUIL",
                "level": 5,
                "types": ["FIRE", "FIRE"],
                "hp": scenario.hp_before,
                "max_hp": scenario.max_hp,
                "stats": {
                    "attack": 10,
                    "defense": 9,
                    "speed": 11,
                    "sp_attack": 11,
                    "sp_defense": 10,
                },
                "moves": [{"name": scenario.move_name}],
            },
            "enemy": {
                "species": "PIDGEY",
                "level": 5,
                "types": ["NORMAL", "NORMAL"],
                "hp": scenario.headless_target_hp,
                "max_hp": 40,
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
                        "bp": 0,
                        "priority": 0,
                        "accuracy": 255,
                        "pp": 35,
                    }
                ],
            },
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def drain_move_turn_payload(scenario: DrainMoveTurnScenario) -> dict[str, Any]:
    return {
        "rng": {"mode": "fixed", "values": [255, 255]},
        "state": {
            "weather": "none",
            "weather_count": 0,
            "turn": 1,
            "player": {
                "species": "CYNDAQUIL",
                "level": 5,
                "types": ["FIRE", "FIRE"],
                "hp": scenario.hp_before,
                "max_hp": scenario.max_hp,
                "stats": {
                    "attack": 10,
                    "defense": 9,
                    "speed": 11,
                    "sp_attack": 11,
                    "sp_defense": 10,
                },
                "moves": [{"name": scenario.move_name, "pp": scenario.pp_before}],
            },
            "enemy": {
                "species": "PIDGEY",
                "level": 5,
                "types": ["NORMAL", "NORMAL"],
                "hp": scenario.headless_target_hp,
                "max_hp": 40,
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
                        "bp": 0,
                        "priority": 0,
                        "accuracy": 255,
                        "pp": 35,
                    }
                ],
            },
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def item_restore_component_payload(scenario: ItemRestoreComponentScenario) -> dict[str, Any]:
    return {
        "rng": {"mode": "fixed", "values": []},
        "state": {
            "weather": "none",
            "weather_count": 0,
            "turn": 1,
            "player": {
                "species": "CYNDAQUIL",
                "level": 5,
                "types": ["FIRE", "FIRE"],
                "hp": scenario.hp_before,
                "max_hp": scenario.max_hp,
                "stats": {
                    "attack": 10,
                    "defense": 9,
                    "speed": 11,
                    "sp_attack": 11,
                    "sp_defense": 10,
                },
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0}],
            },
            "enemy": {
                "species": "PIDGEY",
                "level": 5,
                "types": ["NORMAL", "NORMAL"],
                "hp": 40,
                "max_hp": 40,
                "stats": {
                    "attack": 6,
                    "defense": 6,
                    "speed": 7,
                    "sp_attack": 5,
                    "sp_defense": 5,
                },
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0}],
            },
        },
        "actions": {"player": {"type": "item", "item": scenario.item_name}, "enemy": {"type": "move", "move": 0}},
    }


def full_restore_status_cure_payload(scenario: FullRestoreStatusCureScenario) -> dict[str, Any]:
    player: dict[str, Any] = {
        "species": "CYNDAQUIL",
        "level": 5,
        "types": ["FIRE", "FIRE"],
        "hp": 20,
        "max_hp": 30,
        "stats": {
            "attack": 10,
            "defense": 9,
            "speed": 11,
            "sp_attack": 11,
            "sp_defense": 10,
        },
        "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0}],
    }
    if scenario.headless_status is not None:
        player["status"] = scenario.headless_status
    if scenario.headless_toxic_count:
        player["toxic_count"] = scenario.headless_toxic_count
    if scenario.headless_sleep_turns:
        player["sleep_turns"] = scenario.headless_sleep_turns
    return {
        "rng": {"mode": "fixed", "values": []},
        "state": {
            "weather": "none",
            "weather_count": 0,
            "turn": 1,
            "player": player,
            "enemy": {
                "species": "PIDGEY",
                "level": 5,
                "types": ["NORMAL", "NORMAL"],
                "hp": 40,
                "max_hp": 40,
                "stats": {
                    "attack": 6,
                    "defense": 6,
                    "speed": 7,
                    "sp_attack": 5,
                    "sp_defense": 5,
                },
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0}],
            },
        },
        "actions": {"player": {"type": "item", "item": "FULL_RESTORE"}, "enemy": {"type": "move", "move": 0}},
    }


def residual_component_payload(scenario: ResidualComponentScenario) -> dict[str, Any]:
    player: dict[str, Any] = {
        "species": "CYNDAQUIL",
        "level": 5,
        "types": ["FIRE", "FIRE"],
        "hp": scenario.hp_before,
        "max_hp": scenario.max_hp,
        "stats": {
            "attack": 10,
            "defense": 9,
            "speed": 11,
            "sp_attack": 11,
            "sp_defense": 10,
        },
        "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0, "pp": 35}],
    }
    enemy: dict[str, Any] = {
        "species": "PIDGEY",
        "level": 5,
        "types": ["NORMAL", "NORMAL"],
        "hp": scenario.hp_before,
        "max_hp": scenario.max_hp,
        "stats": {
            "attack": 6,
            "defense": 6,
            "speed": 7,
            "sp_attack": 5,
            "sp_defense": 5,
        },
        "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0, "pp": 35}],
    }
    actor_state = player if scenario.actor == "player" else enemy
    actor_state["status"] = scenario.status_name
    if scenario.toxic_flag:
        actor_state["toxic_count"] = scenario.toxic_count_before
    return {
        "rng": {"mode": "fixed", "values": []},
        "state": {
            "weather": "none",
            "weather_count": 0,
            "turn": 1,
            "player": player,
            "enemy": enemy,
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def pp_decrement_component_payload(scenario: PPDecrementComponentScenario) -> dict[str, Any]:
    return {
        "rng": {"mode": "fixed", "values": []},
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
                "moves": [
                    {"name": "TACKLE", "type": "NORMAL", "bp": 0, "pp": scenario.pp_before}
                ],
            },
            "enemy": {
                "species": "PIDGEY",
                "level": 5,
                "types": ["NORMAL", "NORMAL"],
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
                    {"name": "TACKLE", "type": "NORMAL", "bp": 0, "pp": scenario.pp_before}
                ],
            },
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def weather_setup_component_payload(scenario: WeatherSetupComponentScenario) -> dict[str, Any]:
    return {
        "rng": {"mode": "fixed", "values": []},
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
                "moves": [{"name": scenario.move_name, "pp": 5}],
            },
            "enemy": {
                "species": "PIDGEY",
                "level": 5,
                "types": ["NORMAL", "NORMAL"],
                "hp": 12,
                "max_hp": 12,
                "stats": {
                    "attack": 6,
                    "defense": 6,
                    "speed": 7,
                    "sp_attack": 5,
                    "sp_defense": 5,
                },
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0, "pp": 35}],
            },
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def substitute_move_turn_payload(scenario: SubstituteMoveTurnScenario) -> dict[str, Any]:
    player: dict[str, Any] = {
        "species": "CYNDAQUIL",
        "level": 5,
        "types": ["FIRE", "FIRE"],
        "hp": scenario.hp_before,
        "max_hp": scenario.max_hp,
        "stats": {
            "attack": 10,
            "defense": 9,
            "speed": 11,
            "sp_attack": 11,
            "sp_defense": 10,
        },
        "moves": [{"name": "SUBSTITUTE", "pp": scenario.pp_before}],
    }
    if scenario.substitute_before:
        player["substitute"] = True
        player["substitute_hp"] = scenario.substitute_hp_before
    return {
        "rng": {"mode": "fixed", "values": []},
        "state": {
            "weather": "none",
            "weather_count": 0,
            "turn": 1,
            "player": player,
            "enemy": {
                "species": "PIDGEY",
                "level": 5,
                "types": ["NORMAL", "NORMAL"],
                "hp": 12,
                "max_hp": 12,
                "stats": {
                    "attack": 6,
                    "defense": 6,
                    "speed": 7,
                    "sp_attack": 5,
                    "sp_defense": 5,
                },
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0, "pp": 35}],
            },
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def self_heal_move_turn_payload(scenario: SelfHealMoveTurnScenario) -> dict[str, Any]:
    return {
        "rng": {"mode": "fixed", "values": []},
        "state": {
            "weather": "none",
            "weather_count": 0,
            "turn": 1,
            "player": {
                "species": "CYNDAQUIL",
                "level": 5,
                "types": ["FIRE", "FIRE"],
                "hp": scenario.hp_before,
                "max_hp": scenario.max_hp,
                "stats": {
                    "attack": 10,
                    "defense": 9,
                    "speed": 11,
                    "sp_attack": 11,
                    "sp_defense": 10,
                },
                "moves": [{"name": scenario.move_name, "pp": scenario.pp_before}],
            },
            "enemy": {
                "species": "PIDGEY",
                "level": 5,
                "types": ["NORMAL", "NORMAL"],
                "hp": 12,
                "max_hp": 12,
                "stats": {
                    "attack": 6,
                    "defense": 6,
                    "speed": 7,
                    "sp_attack": 5,
                    "sp_defense": 5,
                },
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0, "pp": 35}],
            },
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def rest_move_turn_payload(scenario: RestMoveTurnScenario) -> dict[str, Any]:
    return {
        "rng": {"mode": "fixed", "values": []},
        "state": {
            "weather": "none",
            "weather_count": 0,
            "turn": 1,
            "player": {
                "species": "CYNDAQUIL",
                "level": 5,
                "types": ["FIRE", "FIRE"],
                "hp": scenario.hp_before,
                "max_hp": scenario.max_hp,
                "status": "toxic" if scenario.toxic_flag_before else "none",
                "toxic_count": scenario.toxic_count_before,
                "stats": {
                    "attack": 10,
                    "defense": 9,
                    "speed": 11,
                    "sp_attack": 11,
                    "sp_defense": 10,
                },
                "moves": [{"name": "REST", "pp": scenario.pp_before}],
            },
            "enemy": {
                "species": "PIDGEY",
                "level": 5,
                "types": ["NORMAL", "NORMAL"],
                "hp": 12,
                "max_hp": 12,
                "stats": {
                    "attack": 6,
                    "defense": 6,
                    "speed": 7,
                    "sp_attack": 5,
                    "sp_defense": 5,
                },
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0, "pp": 35}],
            },
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def after_hit_item_effect_payload(scenario: AfterHitItemEffectScenario) -> dict[str, Any]:
    player: dict[str, Any] = {
        "species": "PIDGEY",
        "level": 2,
        "types": ["NORMAL", "FLYING"],
        "hp": scenario.player_hp_before,
        "max_hp": scenario.player_max_hp,
        "stats": {
            "attack": 30,
            "defense": 7,
            "speed": 10,
            "sp_attack": 6,
            "sp_defense": 7,
        },
        "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40, "pp": 35}],
    }
    if scenario.player_item_name:
        player["item"] = scenario.player_item_name
    enemy: dict[str, Any] = {
        "species": "CYNDAQUIL",
        "level": 5,
        "types": ["FIRE", "FIRE"],
        "hp": scenario.enemy_hp_before,
        "max_hp": scenario.enemy_max_hp,
        "stats": {
            "attack": 10,
            "defense": 5,
            "speed": 9,
            "sp_attack": 11,
            "sp_defense": 10,
        },
        "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0, "pp": 35}],
    }
    if scenario.enemy_item_name:
        enemy["item"] = scenario.enemy_item_name
    return {
        "rng": {"mode": "fixed", "values": [255, 255]},
        "state": {
            "weather": "none",
            "weather_count": 0,
            "turn": 1,
            "player": player,
            "enemy": enemy,
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def compare_normal_hit_scenario(scenario: NormalHitScenario) -> DifferentialResult:
    rom = run_rom_normal_hit(scenario)
    report = simulate_payload(normal_hit_payload(scenario))
    outcome = report["outcomes"][0]
    normal_hit_events = [
        event
        for event in outcome["events"]
        if event.get("actor") == "enemy" and event.get("type") in {"damage", "miss"}
    ]
    errors: list[str] = []
    if len(normal_hit_events) != 1:
        errors.append(f"expected one enemy NormalHit event, got {len(normal_hit_events)}")
        damage_event: dict[str, Any] = {}
    else:
        damage_event = normal_hit_events[0]
    if rom.attack_missed:
        if damage_event.get("type") != "miss":
            errors.append(f"expected headless miss event, got {damage_event.get('type')}")
        if rom.player_hp_after != rom.player_hp_before:
            errors.append(f"ROM miss changed HP: {rom.player_hp_before}->{rom.player_hp_after}")
    else:
        if damage_event.get("type") != "damage":
            errors.append(f"expected headless damage event, got {damage_event.get('type')}")
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
    if scenario.move_accuracy != 255 and damage_event.get("accuracy_check", {}).get("threshold") != scenario.move_accuracy:
        errors.append(
            "accuracy threshold mismatch: "
            f"headless={damage_event.get('accuracy_check', {}).get('threshold')} rom={scenario.move_accuracy}"
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
    if not rom.attack_missed and rom.command_returns.get("BattleCommand_ApplyDamage", True):
        errors.append("BattleCommand_ApplyDamage unexpectedly returned; fixture expects HUD non-return after HP write")
    return DifferentialResult(
        scenario_id=scenario.scenario_id,
        ok=not errors,
        errors=tuple(errors),
        rom={
            "rom_scenario_id": rom.scenario_id,
            "move_accuracy": rom.move_accuracy,
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


def compare_normal_hit_fixed_rng() -> DifferentialResult:
    return compare_normal_hit_scenario(DEFAULT_NORMAL_HIT_SCENARIO)


def compare_normal_hit_differentials() -> tuple[DifferentialResult, ...]:
    return tuple(compare_normal_hit_scenario(scenario) for scenario in NORMAL_HIT_SCENARIOS)


def compare_item_restore_component() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_item_restore_components()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in ITEM_RESTORE_COMPONENT_SCENARIOS:
        rom = rom_results[scenario.scenario_id]
        report = simulate_payload(item_restore_component_payload(scenario))
        outcome = report["outcomes"][0]
        item_events = [
            event
            for event in outcome["events"]
            if event.get("actor") == "player"
            and event.get("type") == "item_restore"
            and event.get("item_id") == scenario.item_id
        ]
        if len(item_events) != 1:
            errors.append(f"{scenario.scenario_id}: expected one headless item event, got {len(item_events)}")
            item_event: dict[str, Any] = {}
        else:
            item_event = item_events[0]

        if item_event.get("hp_before") != scenario.hp_before or item_event.get("hp_after") != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: headless HP mismatch: "
                f"{item_event.get('hp_before')}->{item_event.get('hp_after')} "
                f"expected={scenario.hp_before}->{scenario.expected_hp_after}"
            )
        if item_event.get("heal") != scenario.expected_heal:
            errors.append(
                f"{scenario.scenario_id}: headless heal mismatch: "
                f"headless={item_event.get('heal')} expected={scenario.expected_heal}"
            )
        if outcome["state"]["player"].get("hp") != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: final player HP mismatch: "
                f"headless={outcome['state']['player'].get('hp')} expected={scenario.expected_hp_after}"
            )

        if rom.hp_before != scenario.hp_before:
            errors.append(f"{scenario.scenario_id}: ROM hp_before={rom.hp_before}, expected {scenario.hp_before}")
        if rom.hp_after != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM hp_after mismatch: "
                f"rom={rom.hp_after} expected={scenario.expected_hp_after}"
            )
        if rom.hp_buffer3 != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM wHPBuffer3 mismatch: "
                f"rom={rom.hp_buffer3} expected={scenario.expected_hp_after}"
            )
        if rom.table_amount != scenario.expected_table_amount:
            errors.append(
                f"{scenario.scenario_id}: ROM healing table mismatch: "
                f"rom={rom.table_amount} expected={scenario.expected_table_amount}"
            )
        if not rom.get_amount_returned:
            errors.append(f"{scenario.scenario_id}: GetHealingItemAmount did not return")
        if not rom.restore_returned:
            errors.append(f"{scenario.scenario_id}: RestoreHealth did not return")

        rom_report[scenario.scenario_id] = {
            "item": rom.item_name,
            "hp_before": rom.hp_before,
            "hp_after": rom.hp_after,
            "max_hp": rom.max_hp,
            "table_amount": rom.table_amount,
            "hp_buffer3": rom.hp_buffer3,
        }
        headless_results[scenario.scenario_id] = {
            "final_player_hp": outcome["state"]["player"].get("hp"),
            "item_event": item_event,
        }

    return DifferentialResult(
        scenario_id="item_restore_component_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


def compare_full_restore_status_cure() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_full_restore_status_cures()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in FULL_RESTORE_STATUS_CURE_SCENARIOS:
        rom = rom_results[scenario.scenario_id]

        # ROM side: HealStatus must clear primary status and the TOXIC /
        # NIGHTMARE / CONFUSED sub-status bits for a Full Restore application.
        if rom.status_before != scenario.status_before:
            errors.append(
                f"{scenario.scenario_id}: ROM status_before mismatch: "
                f"rom={rom.status_before} expected={scenario.status_before}"
            )
        if rom.status_after != 0:
            errors.append(
                f"{scenario.scenario_id}: ROM did not clear wBattleMonStatus: "
                f"{rom.status_before}->{rom.status_after}"
            )
        if rom.sub5_after & (1 << SUBSTATUS_TOXIC_BIT):
            errors.append(
                f"{scenario.scenario_id}: ROM did not clear SUBSTATUS_TOXIC: "
                f"sub5 {rom.sub5_before:#04x}->{rom.sub5_after:#04x}"
            )
        if rom.sub1_after & (1 << SUBSTATUS_NIGHTMARE_BIT):
            errors.append(
                f"{scenario.scenario_id}: ROM did not clear SUBSTATUS_NIGHTMARE: "
                f"sub1 {rom.sub1_before:#04x}->{rom.sub1_after:#04x}"
            )
        if rom.sub3_after & (1 << SUBSTATUS_CONFUSED_BIT):
            errors.append(
                f"{scenario.scenario_id}: ROM did not clear SUBSTATUS_CONFUSED (Full Restore is full-heal): "
                f"sub3 {rom.sub3_before:#04x}->{rom.sub3_after:#04x}"
            )

        # Headless side: the explicit FULL_RESTORE item action must clear the
        # statuses it models (status, toxic_count, sleep_turns). Confusion +
        # nightmare are not yet modeled headless-side; that's the scoped
        # boundary, not a regression.
        report = simulate_payload(full_restore_status_cure_payload(scenario))
        outcome = report["outcomes"][0]
        item_events = [
            event
            for event in outcome["events"]
            if event.get("actor") == "player"
            and event.get("type") == "item_restore"
            and event.get("item_id") == FULL_RESTORE_ITEM_ID
        ]
        if len(item_events) != 1:
            errors.append(
                f"{scenario.scenario_id}: expected one headless FULL_RESTORE item event, "
                f"got {len(item_events)}"
            )
            item_event: dict[str, Any] = {}
        else:
            item_event = item_events[0]

        player_state = outcome["state"]["player"]
        if item_event.get("status_after", "none") != "none":
            errors.append(
                f"{scenario.scenario_id}: headless status_after mismatch: "
                f"event={item_event.get('status_after')!r} expected='none'"
            )
        if player_state.get("status", "none") != "none":
            errors.append(
                f"{scenario.scenario_id}: headless final status mismatch: "
                f"state={player_state.get('status')!r} expected='none'"
            )
        if player_state.get("toxic_count", 0) != 0:
            errors.append(
                f"{scenario.scenario_id}: headless toxic_count not cleared: "
                f"state={player_state.get('toxic_count')}"
            )
        if player_state.get("sleep_turns", 0) != 0:
            errors.append(
                f"{scenario.scenario_id}: headless sleep_turns not cleared: "
                f"state={player_state.get('sleep_turns')}"
            )

        rom_report[scenario.scenario_id] = {
            "status": f"{rom.status_before:#04x}->{rom.status_after:#04x}",
            "sub1": f"{rom.sub1_before:#04x}->{rom.sub1_after:#04x}",
            "sub3": f"{rom.sub3_before:#04x}->{rom.sub3_after:#04x}",
            "sub5": f"{rom.sub5_before:#04x}->{rom.sub5_after:#04x}",
        }
        headless_results[scenario.scenario_id] = {
            "final_status": player_state.get("status", "none"),
            "final_toxic_count": player_state.get("toxic_count", 0),
            "final_sleep_turns": player_state.get("sleep_turns", 0),
            "item_event": item_event,
        }

    return DifferentialResult(
        scenario_id="full_restore_status_cure_component_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


def compare_basic_pp_decrement_component() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_pp_decrement_components()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in PP_DECREMENT_COMPONENT_SCENARIOS:
        rom = rom_results[scenario.scenario_id]
        expected_pp_after = scenario.pp_before - 1
        if rom.active_pp_after != expected_pp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM active PP mismatch: "
                f"{rom.active_pp_after} != {expected_pp_after}"
            )
        if rom.party_pp_after != expected_pp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM party/wild PP mismatch: "
                f"{rom.party_pp_after} != {expected_pp_after}"
            )
        if rom.turns_taken_after != rom.turns_taken_before + 1:
            errors.append(
                f"{scenario.scenario_id}: ROM turns-taken mismatch: "
                f"{rom.turns_taken_before}->{rom.turns_taken_after}"
            )
        if not rom.returned:
            errors.append(f"{scenario.scenario_id}: BattleCommand_DoTurn did not return")

        report = simulate_payload(pp_decrement_component_payload(scenario))
        outcome = report["outcomes"][0]
        actor_events = [
            event
            for event in outcome["events"]
            if event.get("actor") == scenario.actor and "pp_after" in event
        ]
        if len(actor_events) != 1:
            errors.append(
                f"{scenario.scenario_id}: expected one headless PP event for "
                f"{scenario.actor}, got {len(actor_events)}"
            )
            pp_event: dict[str, Any] = {}
        else:
            pp_event = actor_events[0]

        actor_state = outcome["state"][scenario.actor]
        headless_pp_after = actor_state["moves"][0]["pp"]
        if pp_event.get("pp_before") != scenario.pp_before:
            errors.append(
                f"{scenario.scenario_id}: headless pp_before mismatch: "
                f"{pp_event.get('pp_before')} != {scenario.pp_before}"
            )
        if pp_event.get("pp_after") != expected_pp_after:
            errors.append(
                f"{scenario.scenario_id}: headless event pp_after mismatch: "
                f"{pp_event.get('pp_after')} != {expected_pp_after}"
            )
        if headless_pp_after != rom.active_pp_after:
            errors.append(
                f"{scenario.scenario_id}: final PP mismatch: "
                f"headless={headless_pp_after} rom={rom.active_pp_after}"
            )

        rom_report[scenario.scenario_id] = {
            "actor": rom.actor,
            "pp_before": rom.pp_before,
            "active_pp_after": rom.active_pp_after,
            "party_pp_after": rom.party_pp_after,
            "turns_taken_before": rom.turns_taken_before,
            "turns_taken_after": rom.turns_taken_after,
            "returned": rom.returned,
            "post_pc": rom.post_pc,
        }
        headless_results[scenario.scenario_id] = {
            "final_pp": headless_pp_after,
            "pp_event": pp_event,
        }

    return DifferentialResult(
        scenario_id="basic_pp_decrement_component_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


def compare_weather_setup_component() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_weather_setup_components()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in WEATHER_SETUP_COMPONENT_SCENARIOS:
        rom = rom_results[scenario.scenario_id]
        if rom.weather_before != 0:
            errors.append(
                f"{scenario.scenario_id}: ROM weather_before={rom.weather_before}, expected 0"
            )
        if rom.weather_after != scenario.expected_weather:
            errors.append(
                f"{scenario.scenario_id}: ROM weather mismatch: "
                f"{rom.weather_after} != {scenario.expected_weather}"
            )
        if rom.weather_count_before != 0:
            errors.append(
                f"{scenario.scenario_id}: ROM weather_count_before={rom.weather_count_before}, expected 0"
            )
        if rom.weather_count_after != 5:
            errors.append(
                f"{scenario.scenario_id}: ROM weather count mismatch: {rom.weather_count_after} != 5"
            )
        if not rom.mutation_observed:
            errors.append(f"{scenario.scenario_id}: ROM weather setup mutation was not observed")

        report = simulate_payload(weather_setup_component_payload(scenario))
        outcome = report["outcomes"][0]
        setup_events = [
            event
            for event in outcome["events"]
            if event.get("actor") == "player"
            and event.get("move") == scenario.move_name
            and event.get("type") == "weather_start"
        ]
        if len(setup_events) != 1:
            errors.append(
                f"{scenario.scenario_id}: expected one headless weather_start event, "
                f"got {len(setup_events)}"
            )
            setup_event: dict[str, Any] = {}
        else:
            setup_event = setup_events[0]

        if setup_event.get("weather") != scenario.weather_name:
            errors.append(
                f"{scenario.scenario_id}: headless weather name mismatch: "
                f"{setup_event.get('weather')} != {scenario.weather_name}"
            )
        if setup_event.get("weather_after") != rom.weather_after:
            errors.append(
                f"{scenario.scenario_id}: headless weather byte mismatch: "
                f"{setup_event.get('weather_after')} != {rom.weather_after}"
            )
        if setup_event.get("weather_count_before") != rom.weather_count_before:
            errors.append(
                f"{scenario.scenario_id}: headless weather_count_before mismatch: "
                f"{setup_event.get('weather_count_before')} != {rom.weather_count_before}"
            )
        if setup_event.get("weather_count_after") != rom.weather_count_after:
            errors.append(
                f"{scenario.scenario_id}: headless weather_count_after mismatch: "
                f"{setup_event.get('weather_count_after')} != {rom.weather_count_after}"
            )
        if setup_event.get("pp_before") != 5 or setup_event.get("pp_after") != 4:
            errors.append(
                f"{scenario.scenario_id}: headless PP mismatch: "
                f"{setup_event.get('pp_before')}->{setup_event.get('pp_after')}"
            )

        rom_report[scenario.scenario_id] = {
            "move": rom.move_name,
            "weather_before": rom.weather_before,
            "weather_after": rom.weather_after,
            "weather_count_before": rom.weather_count_before,
            "weather_count_after": rom.weather_count_after,
            "mutation_observed": rom.mutation_observed,
            "returned": rom.returned,
            "ticks": rom.ticks,
            "post_pc": rom.post_pc,
        }
        headless_results[scenario.scenario_id] = {
            "weather_start_event": setup_event,
        }

    return DifferentialResult(
        scenario_id="weather_setup_component_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


def compare_selected_substitute_move_turn() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_substitute_move_turns()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in SUBSTITUTE_MOVE_TURN_SCENARIOS:
        rom = rom_results[scenario.scenario_id]
        expected_pp_after = scenario.pp_before - 1
        if not rom.do_turn_returned:
            errors.append(f"{scenario.scenario_id}: BattleCommand_DoTurn did not return")
        if not rom.substitute_branch_observed:
            errors.append(f"{scenario.scenario_id}: BattleCommand_Substitute branch was not observed")
        if rom.active_pp_after != expected_pp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM active PP mismatch: "
                f"{rom.active_pp_after} != {expected_pp_after}"
            )
        if rom.party_pp_after != expected_pp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM party PP mismatch: "
                f"{rom.party_pp_after} != {expected_pp_after}"
            )
        if rom.turns_taken_after != rom.turns_taken_before + 1:
            errors.append(
                f"{scenario.scenario_id}: ROM turns-taken mismatch: "
                f"{rom.turns_taken_before}->{rom.turns_taken_after}"
            )
        if rom.hp_before != scenario.hp_before or rom.hp_after != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM HP mismatch: "
                f"{rom.hp_before}->{rom.hp_after}, expected "
                f"{scenario.hp_before}->{scenario.expected_hp_after}"
            )
        if rom.substitute_before is not scenario.substitute_before:
            errors.append(
                f"{scenario.scenario_id}: ROM substitute_before mismatch: "
                f"{rom.substitute_before} != {scenario.substitute_before}"
            )
        if rom.substitute_after is not scenario.expected_substitute_after:
            errors.append(
                f"{scenario.scenario_id}: ROM substitute_after mismatch: "
                f"{rom.substitute_after} != {scenario.expected_substitute_after}"
            )
        if rom.substitute_hp_after != scenario.expected_substitute_hp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM substitute HP mismatch: "
                f"{rom.substitute_hp_after} != {scenario.expected_substitute_hp_after}"
            )
        if scenario.expected_text_symbol and rom.observed_text_symbol != scenario.expected_text_symbol:
            errors.append(
                f"{scenario.scenario_id}: ROM no-effect text mismatch: "
                f"{rom.observed_text_symbol} != {scenario.expected_text_symbol}"
            )

        report = simulate_payload(substitute_move_turn_payload(scenario))
        outcome = report["outcomes"][0]
        substitute_events = [
            event
            for event in outcome["events"]
            if event.get("actor") == "player" and event.get("move") == "SUBSTITUTE"
        ]
        if len(substitute_events) != 1:
            errors.append(
                f"{scenario.scenario_id}: expected one headless Substitute event, "
                f"got {len(substitute_events)}"
            )
            substitute_event: dict[str, Any] = {}
        else:
            substitute_event = substitute_events[0]

        player_state = outcome["state"]["player"]
        if substitute_event.get("type") != scenario.expected_event_type:
            errors.append(
                f"{scenario.scenario_id}: headless event type mismatch: "
                f"{substitute_event.get('type')} != {scenario.expected_event_type}"
            )
        if substitute_event.get("blocked_reason") != scenario.expected_blocked_reason:
            errors.append(
                f"{scenario.scenario_id}: headless blocked_reason mismatch: "
                f"{substitute_event.get('blocked_reason')} != {scenario.expected_blocked_reason}"
            )
        if substitute_event.get("hp_before") != rom.hp_before:
            errors.append(
                f"{scenario.scenario_id}: headless hp_before mismatch: "
                f"{substitute_event.get('hp_before')} != {rom.hp_before}"
            )
        if substitute_event.get("hp_after") != rom.hp_after:
            errors.append(
                f"{scenario.scenario_id}: headless hp_after mismatch: "
                f"{substitute_event.get('hp_after')} != {rom.hp_after}"
            )
        if substitute_event.get("substitute_before") is not rom.substitute_before:
            errors.append(
                f"{scenario.scenario_id}: headless substitute_before mismatch: "
                f"{substitute_event.get('substitute_before')} != {rom.substitute_before}"
            )
        if substitute_event.get("substitute_after") is not rom.substitute_after:
            errors.append(
                f"{scenario.scenario_id}: headless substitute_after mismatch: "
                f"{substitute_event.get('substitute_after')} != {rom.substitute_after}"
            )
        if rom.substitute_after and substitute_event.get("substitute_hp") != rom.substitute_hp_after:
            errors.append(
                f"{scenario.scenario_id}: headless substitute_hp mismatch: "
                f"{substitute_event.get('substitute_hp')} != {rom.substitute_hp_after}"
            )
        if substitute_event.get("pp_before") != rom.pp_before:
            errors.append(
                f"{scenario.scenario_id}: headless pp_before mismatch: "
                f"{substitute_event.get('pp_before')} != {rom.pp_before}"
            )
        if substitute_event.get("pp_after") != rom.active_pp_after:
            errors.append(
                f"{scenario.scenario_id}: headless pp_after mismatch: "
                f"{substitute_event.get('pp_after')} != {rom.active_pp_after}"
            )
        if player_state["hp"] != rom.hp_after:
            errors.append(
                f"{scenario.scenario_id}: final headless HP mismatch: "
                f"{player_state['hp']} != {rom.hp_after}"
            )
        if bool(player_state.get("substitute", False)) is not rom.substitute_after:
            errors.append(
                f"{scenario.scenario_id}: final headless Substitute mismatch: "
                f"{player_state.get('substitute')} != {rom.substitute_after}"
            )
        if rom.substitute_after and int(player_state.get("substitute_hp", 0) or 0) != rom.substitute_hp_after:
            errors.append(
                f"{scenario.scenario_id}: final headless substitute_hp mismatch: "
                f"{player_state.get('substitute_hp')} != {rom.substitute_hp_after}"
            )
        if player_state["moves"][0]["pp"] != rom.active_pp_after:
            errors.append(
                f"{scenario.scenario_id}: final headless PP mismatch: "
                f"{player_state['moves'][0]['pp']} != {rom.active_pp_after}"
            )

        rom_report[scenario.scenario_id] = {
            "case": rom.case_name,
            "hp": f"{rom.hp_before}->{rom.hp_after}",
            "max_hp": rom.max_hp,
            "substitute": f"{rom.substitute_before}->{rom.substitute_after}",
            "substitute_hp": f"{rom.substitute_hp_before}->{rom.substitute_hp_after}",
            "pp": f"{rom.pp_before}->{rom.active_pp_after}",
            "party_pp_after": rom.party_pp_after,
            "turns_taken": f"{rom.turns_taken_before}->{rom.turns_taken_after}",
            "do_turn_returned": rom.do_turn_returned,
            "substitute_branch_observed": rom.substitute_branch_observed,
            "substitute_returned": rom.substitute_returned,
            "expected_text_symbol": rom.expected_text_symbol,
            "observed_text_symbol": rom.observed_text_symbol,
            "ticks": rom.ticks,
            "post_pc": rom.post_pc,
        }
        headless_results[scenario.scenario_id] = {
            "substitute_event": substitute_event,
            "final_hp": player_state["hp"],
            "final_substitute": bool(player_state.get("substitute", False)),
            "final_substitute_hp": int(player_state.get("substitute_hp", 0) or 0),
            "final_pp": player_state["moves"][0]["pp"],
        }

    return DifferentialResult(
        scenario_id="selected_substitute_move_turn_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


def compare_selected_self_heal_move_turn() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_self_heal_move_turns()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in SELF_HEAL_MOVE_TURN_SCENARIOS:
        rom = rom_results[scenario.scenario_id]
        expected_pp_after = scenario.pp_before - 1
        if not rom.do_turn_returned:
            errors.append(f"{scenario.scenario_id}: BattleCommand_DoTurn did not return")
        if not rom.heal_branch_observed:
            errors.append(f"{scenario.scenario_id}: BattleCommand_Heal branch was not observed")
        if rom.active_pp_after != expected_pp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM active PP mismatch: "
                f"{rom.active_pp_after} != {expected_pp_after}"
            )
        if rom.party_pp_after != expected_pp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM party PP mismatch: "
                f"{rom.party_pp_after} != {expected_pp_after}"
            )
        if rom.turns_taken_after != rom.turns_taken_before + 1:
            errors.append(
                f"{scenario.scenario_id}: ROM turns-taken mismatch: "
                f"{rom.turns_taken_before}->{rom.turns_taken_after}"
            )
        if rom.hp_before != scenario.hp_before or rom.hp_after != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM HP mismatch: "
                f"{rom.hp_before}->{rom.hp_after}, expected "
                f"{scenario.hp_before}->{scenario.expected_hp_after}"
            )
        if scenario.expected_text_symbol and rom.observed_text_symbol != scenario.expected_text_symbol:
            errors.append(
                f"{scenario.scenario_id}: ROM no-effect branch mismatch: "
                f"{rom.observed_text_symbol} != {scenario.expected_text_symbol}"
            )

        report = simulate_payload(self_heal_move_turn_payload(scenario))
        outcome = report["outcomes"][0]
        heal_events = [
            event
            for event in outcome["events"]
            if event.get("actor") == "player" and event.get("move") == scenario.move_name
        ]
        if len(heal_events) != 1:
            errors.append(
                f"{scenario.scenario_id}: expected one headless self-heal event, "
                f"got {len(heal_events)}"
            )
            heal_event: dict[str, Any] = {}
        else:
            heal_event = heal_events[0]

        player_state = outcome["state"]["player"]
        if heal_event.get("type") != scenario.expected_event_type:
            errors.append(
                f"{scenario.scenario_id}: headless event type mismatch: "
                f"{heal_event.get('type')} != {scenario.expected_event_type}"
            )
        if heal_event.get("blocked_reason") != scenario.expected_blocked_reason:
            errors.append(
                f"{scenario.scenario_id}: headless blocked_reason mismatch: "
                f"{heal_event.get('blocked_reason')} != {scenario.expected_blocked_reason}"
            )
        if heal_event.get("raw_heal") != scenario.expected_raw_heal:
            errors.append(
                f"{scenario.scenario_id}: headless raw_heal mismatch: "
                f"{heal_event.get('raw_heal')} != {scenario.expected_raw_heal}"
            )
        if heal_event.get("heal") != scenario.expected_heal:
            errors.append(
                f"{scenario.scenario_id}: headless heal mismatch: "
                f"{heal_event.get('heal')} != {scenario.expected_heal}"
            )
        if heal_event.get("hp_before") != rom.hp_before:
            errors.append(
                f"{scenario.scenario_id}: headless hp_before mismatch: "
                f"{heal_event.get('hp_before')} != {rom.hp_before}"
            )
        if heal_event.get("hp_after") != rom.hp_after:
            errors.append(
                f"{scenario.scenario_id}: headless hp_after mismatch: "
                f"{heal_event.get('hp_after')} != {rom.hp_after}"
            )
        if heal_event.get("pp_before") != rom.pp_before:
            errors.append(
                f"{scenario.scenario_id}: headless pp_before mismatch: "
                f"{heal_event.get('pp_before')} != {rom.pp_before}"
            )
        if heal_event.get("pp_after") != rom.active_pp_after:
            errors.append(
                f"{scenario.scenario_id}: headless pp_after mismatch: "
                f"{heal_event.get('pp_after')} != {rom.active_pp_after}"
            )
        if player_state["hp"] != rom.hp_after:
            errors.append(
                f"{scenario.scenario_id}: final headless HP mismatch: "
                f"{player_state['hp']} != {rom.hp_after}"
            )
        if player_state["moves"][0]["pp"] != rom.active_pp_after:
            errors.append(
                f"{scenario.scenario_id}: final headless PP mismatch: "
                f"{player_state['moves'][0]['pp']} != {rom.active_pp_after}"
            )

        rom_report[scenario.scenario_id] = {
            "move": rom.move_name,
            "hp": f"{rom.hp_before}->{rom.hp_after}",
            "max_hp": rom.max_hp,
            "pp": f"{rom.pp_before}->{rom.active_pp_after}",
            "party_pp_after": rom.party_pp_after,
            "turns_taken": f"{rom.turns_taken_before}->{rom.turns_taken_after}",
            "do_turn_returned": rom.do_turn_returned,
            "animation_skipped_for_hp_probe": rom.animation_skipped_for_hp_probe,
            "heal_branch_observed": rom.heal_branch_observed,
            "heal_returned": rom.heal_returned,
            "expected_text_symbol": rom.expected_text_symbol,
            "observed_text_symbol": rom.observed_text_symbol,
            "ticks": rom.ticks,
            "post_pc": rom.post_pc,
        }
        headless_results[scenario.scenario_id] = {
            "self_heal_event": heal_event,
            "final_hp": player_state["hp"],
            "final_pp": player_state["moves"][0]["pp"],
        }

    return DifferentialResult(
        scenario_id="selected_self_heal_move_turn_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


def compare_selected_rest_move_turn() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_rest_move_turns()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in REST_MOVE_TURN_SCENARIOS:
        rom = rom_results[scenario.scenario_id]
        expected_pp_after = scenario.pp_before - 1
        if not rom.do_turn_returned:
            errors.append(f"{scenario.scenario_id}: BattleCommand_DoTurn did not return")
        if not rom.rest_branch_observed:
            errors.append(f"{scenario.scenario_id}: BattleCommand_Heal Rest branch was not observed")
        if rom.active_pp_after != expected_pp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM active PP mismatch: "
                f"{rom.active_pp_after} != {expected_pp_after}"
            )
        if rom.party_pp_after != expected_pp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM party PP mismatch: "
                f"{rom.party_pp_after} != {expected_pp_after}"
            )
        if rom.turns_taken_after != rom.turns_taken_before + 1:
            errors.append(
                f"{scenario.scenario_id}: ROM turns-taken mismatch: "
                f"{rom.turns_taken_before}->{rom.turns_taken_after}"
            )
        if rom.hp_before != scenario.hp_before or rom.hp_after != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM HP mismatch: "
                f"{rom.hp_before}->{rom.hp_after}, expected "
                f"{scenario.hp_before}->{scenario.expected_hp_after}"
            )
        if rom.status_before != scenario.status_before or rom.status_after != scenario.expected_status_after:
            errors.append(
                f"{scenario.scenario_id}: ROM status byte mismatch: "
                f"{rom.status_before}->{rom.status_after}, expected "
                f"{scenario.status_before}->{scenario.expected_status_after}"
            )
        if (
            rom.toxic_substatus_before is not scenario.toxic_flag_before
            or rom.toxic_substatus_after is not scenario.expected_toxic_flag_after
        ):
            errors.append(
                f"{scenario.scenario_id}: ROM toxic substatus mismatch: "
                f"{rom.toxic_substatus_before}->{rom.toxic_substatus_after}, expected "
                f"{scenario.toxic_flag_before}->{scenario.expected_toxic_flag_after}"
            )
        if scenario.expected_text_symbol and rom.observed_text_symbol != scenario.expected_text_symbol:
            errors.append(
                f"{scenario.scenario_id}: ROM no-effect branch mismatch: "
                f"{rom.observed_text_symbol} != {scenario.expected_text_symbol}"
            )

        report = simulate_payload(rest_move_turn_payload(scenario))
        outcome = report["outcomes"][0]
        rest_events = [
            event
            for event in outcome["events"]
            if event.get("actor") == "player" and event.get("move") == "REST"
        ]
        if len(rest_events) != 1:
            errors.append(
                f"{scenario.scenario_id}: expected one headless Rest event, "
                f"got {len(rest_events)}"
            )
            rest_event: dict[str, Any] = {}
        else:
            rest_event = rest_events[0]

        player_state = outcome["state"]["player"]
        if rest_event.get("type") != scenario.expected_event_type:
            errors.append(
                f"{scenario.scenario_id}: headless event type mismatch: "
                f"{rest_event.get('type')} != {scenario.expected_event_type}"
            )
        if rest_event.get("reason") != scenario.expected_reason:
            errors.append(
                f"{scenario.scenario_id}: headless reason mismatch: "
                f"{rest_event.get('reason')} != {scenario.expected_reason}"
            )
        if rest_event.get("hp_before") != rom.hp_before:
            errors.append(
                f"{scenario.scenario_id}: headless hp_before mismatch: "
                f"{rest_event.get('hp_before')} != {rom.hp_before}"
            )
        if rest_event.get("hp_after") != rom.hp_after:
            errors.append(
                f"{scenario.scenario_id}: headless hp_after mismatch: "
                f"{rest_event.get('hp_after')} != {rom.hp_after}"
            )
        if rest_event.get("status_after") != scenario.expected_headless_status_after:
            errors.append(
                f"{scenario.scenario_id}: headless status_after mismatch: "
                f"{rest_event.get('status_after')} != {scenario.expected_headless_status_after}"
            )
        if rest_event.get("sleep_turns_after") != scenario.expected_headless_sleep_turns_after:
            errors.append(
                f"{scenario.scenario_id}: headless sleep_turns_after mismatch: "
                f"{rest_event.get('sleep_turns_after')} != "
                f"{scenario.expected_headless_sleep_turns_after}"
            )
        if scenario.expected_event_type == "rest":
            if rest_event.get("toxic_count_after") != scenario.expected_headless_toxic_count_after:
                errors.append(
                    f"{scenario.scenario_id}: headless toxic_count_after mismatch: "
                    f"{rest_event.get('toxic_count_after')} != "
                    f"{scenario.expected_headless_toxic_count_after}"
                )
            if rest_event.get("heal") != scenario.expected_hp_after - scenario.hp_before:
                errors.append(
                    f"{scenario.scenario_id}: headless heal mismatch: "
                    f"{rest_event.get('heal')} != "
                    f"{scenario.expected_hp_after - scenario.hp_before}"
                )
        if rest_event.get("pp_before") != rom.pp_before:
            errors.append(
                f"{scenario.scenario_id}: headless pp_before mismatch: "
                f"{rest_event.get('pp_before')} != {rom.pp_before}"
            )
        if rest_event.get("pp_after") != rom.active_pp_after:
            errors.append(
                f"{scenario.scenario_id}: headless pp_after mismatch: "
                f"{rest_event.get('pp_after')} != {rom.active_pp_after}"
            )
        if player_state["hp"] != scenario.expected_headless_final_hp:
            errors.append(
                f"{scenario.scenario_id}: final headless HP mismatch: "
                f"{player_state['hp']} != {scenario.expected_headless_final_hp}"
            )
        if player_state["status"] != scenario.expected_headless_status_after:
            errors.append(
                f"{scenario.scenario_id}: final headless status mismatch: "
                f"{player_state['status']} != {scenario.expected_headless_status_after}"
            )
        if player_state["sleep_turns"] != scenario.expected_headless_sleep_turns_after:
            errors.append(
                f"{scenario.scenario_id}: final headless sleep_turns mismatch: "
                f"{player_state['sleep_turns']} != {scenario.expected_headless_sleep_turns_after}"
            )
        if player_state["toxic_count"] != scenario.expected_headless_toxic_count_after:
            errors.append(
                f"{scenario.scenario_id}: final headless toxic_count mismatch: "
                f"{player_state['toxic_count']} != {scenario.expected_headless_toxic_count_after}"
            )
        if player_state["moves"][0]["pp"] != rom.active_pp_after:
            errors.append(
                f"{scenario.scenario_id}: final headless PP mismatch: "
                f"{player_state['moves'][0]['pp']} != {rom.active_pp_after}"
            )

        rom_report[scenario.scenario_id] = {
            "case": rom.case_name,
            "hp": f"{rom.hp_before}->{rom.hp_after}",
            "max_hp": rom.max_hp,
            "status_byte": f"{rom.status_before}->{rom.status_after}",
            "toxic_substatus": f"{rom.toxic_substatus_before}->{rom.toxic_substatus_after}",
            "raw_toxic_count_observed": f"{rom.toxic_count_before}->{rom.toxic_count_after}",
            "pp": f"{rom.pp_before}->{rom.active_pp_after}",
            "party_pp_after": rom.party_pp_after,
            "turns_taken": f"{rom.turns_taken_before}->{rom.turns_taken_after}",
            "do_turn_returned": rom.do_turn_returned,
            "animation_neutralized_for_hp_probe": rom.animation_neutralized_for_hp_probe,
            "rest_branch_observed": rom.rest_branch_observed,
            "heal_returned": rom.heal_returned,
            "expected_text_symbol": rom.expected_text_symbol,
            "observed_text_symbol": rom.observed_text_symbol,
            "ticks": rom.ticks,
            "post_pc": rom.post_pc,
        }
        headless_results[scenario.scenario_id] = {
            "rest_event": rest_event,
            "final_hp": player_state["hp"],
            "final_status": player_state["status"],
            "final_sleep_turns": player_state["sleep_turns"],
            "final_toxic_count": player_state["toxic_count"],
            "final_pp": player_state["moves"][0]["pp"],
        }

    return DifferentialResult(
        scenario_id="selected_rest_move_turn_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


def compare_supported_after_hit_item_effects() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_after_hit_item_effects()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in AFTER_HIT_ITEM_EFFECT_SCENARIOS:
        rom = rom_results[scenario.scenario_id]
        if not rom.mutation_observed:
            errors.append(
                f"{scenario.scenario_id}: ROM after-hit mutation was not observed: "
                f"player HP {rom.player_hp_before}->{rom.player_hp_after}, "
                f"enemy HP {rom.enemy_hp_before}->{rom.enemy_hp_after}"
            )
        if rom.player_hp_after != scenario.expected_player_hp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM player HP mismatch: "
                f"{rom.player_hp_after} != {scenario.expected_player_hp_after}"
            )
        if rom.enemy_hp_after != scenario.expected_enemy_hp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM enemy HP mismatch: "
                f"{rom.enemy_hp_after} != {scenario.expected_enemy_hp_after}"
            )
        if rom.cur_damage != scenario.cur_damage:
            errors.append(
                f"{scenario.scenario_id}: ROM wCurDamage mismatch: "
                f"{rom.cur_damage} != {scenario.cur_damage}"
            )

        report = simulate_payload(after_hit_item_effect_payload(scenario))
        outcome = report["outcomes"][0]
        damage_events = [
            event
            for event in outcome["events"]
            if event.get("type") == "damage" and event.get("actor") == "player"
        ]
        if len(damage_events) != 1:
            errors.append(
                f"{scenario.scenario_id}: expected one headless player damage event, "
                f"got {len(damage_events)}"
            )
            damage_event: dict[str, Any] = {}
        else:
            damage_event = damage_events[0]
        damage_basis_must_match = "SHELL_BELL" in scenario.expected_event_items
        if damage_basis_must_match and damage_event.get("actual_damage") != scenario.cur_damage:
            errors.append(
                f"{scenario.scenario_id}: headless damage basis mismatch: "
                f"{damage_event.get('actual_damage')} != {scenario.cur_damage}"
            )

        item_events = [event for event in outcome["events"] if event.get("source_item")]
        item_names = tuple(str(event.get("source_item", "")) for event in item_events)
        item_types = tuple(str(event.get("type", "")) for event in item_events)
        item_values = tuple(
            int(event.get("heal", event.get("damage", -1)) or 0)
            for event in item_events
        )
        if item_names != scenario.expected_event_items:
            errors.append(
                f"{scenario.scenario_id}: headless item event order mismatch: "
                f"{item_names} != {scenario.expected_event_items}"
            )
        if item_types != scenario.expected_event_types:
            errors.append(
                f"{scenario.scenario_id}: headless item event types mismatch: "
                f"{item_types} != {scenario.expected_event_types}"
            )
        if item_values != scenario.expected_event_values:
            errors.append(
                f"{scenario.scenario_id}: headless item event values mismatch: "
                f"{item_values} != {scenario.expected_event_values}"
            )
        player_state = outcome["state"]["player"]
        if player_state["hp"] != rom.player_hp_after:
            errors.append(
                f"{scenario.scenario_id}: final player HP mismatch: "
                f"headless={player_state['hp']} rom_after_hit={rom.player_hp_after}"
            )

        rom_report[scenario.scenario_id] = {
            "player_hp": f"{rom.player_hp_before}->{rom.player_hp_after}",
            "player_max_hp": rom.player_max_hp,
            "enemy_hp": f"{rom.enemy_hp_before}->{rom.enemy_hp_after}",
            "enemy_max_hp": rom.enemy_max_hp,
            "cur_damage": rom.cur_damage,
            "mutation_observed": rom.mutation_observed,
            "returned": rom.returned,
            "ticks": rom.ticks,
            "post_pc": rom.post_pc,
        }
        headless_results[scenario.scenario_id] = {
            "damage_event": damage_event,
            "item_events": item_events,
            "final_player_hp": player_state["hp"],
        }

    return DifferentialResult(
        scenario_id="supported_after_hit_item_effects_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


def compare_basic_status_residual_component() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_residual_components()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in RESIDUAL_COMPONENT_SCENARIOS:
        rom = rom_results[scenario.scenario_id]
        report = simulate_payload(residual_component_payload(scenario))
        outcome = report["outcomes"][0]
        residual_events = [
            event
            for event in outcome["events"]
            if event.get("type") == "residual_damage"
            and event.get("actor") == scenario.actor
        ]
        if len(residual_events) != 1:
            errors.append(
                f"{scenario.scenario_id}: expected one headless residual event for "
                f"{scenario.actor}, got {len(residual_events)}"
            )
            residual_event: dict[str, Any] = {}
        else:
            residual_event = residual_events[0]

        actor_state = outcome["state"][scenario.actor]
        if residual_event.get("status") != scenario.status_name:
            errors.append(
                f"{scenario.scenario_id}: headless residual status mismatch: "
                f"headless={residual_event.get('status')} expected={scenario.status_name}"
            )
        if residual_event.get("damage") != scenario.expected_damage:
            errors.append(
                f"{scenario.scenario_id}: headless residual damage mismatch: "
                f"headless={residual_event.get('damage')} expected={scenario.expected_damage}"
            )
        if residual_event.get("hp_before") != scenario.hp_before:
            errors.append(
                f"{scenario.scenario_id}: headless hp_before mismatch: "
                f"headless={residual_event.get('hp_before')} expected={scenario.hp_before}"
            )
        if residual_event.get("hp_after") != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: headless hp_after mismatch: "
                f"headless={residual_event.get('hp_after')} expected={scenario.expected_hp_after}"
            )
        if residual_event.get("toxic_count_before") != scenario.toxic_count_before:
            errors.append(
                f"{scenario.scenario_id}: headless toxic_count_before mismatch: "
                f"headless={residual_event.get('toxic_count_before')} "
                f"expected={scenario.toxic_count_before}"
            )
        if residual_event.get("toxic_count_after") != scenario.expected_toxic_count_after:
            errors.append(
                f"{scenario.scenario_id}: headless toxic_count_after mismatch: "
                f"headless={residual_event.get('toxic_count_after')} "
                f"expected={scenario.expected_toxic_count_after}"
            )
        if actor_state.get("hp") != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: final headless HP mismatch: "
                f"headless={actor_state.get('hp')} expected={scenario.expected_hp_after}"
            )
        if actor_state.get("toxic_count", 0) != scenario.expected_toxic_count_after:
            errors.append(
                f"{scenario.scenario_id}: final headless toxic_count mismatch: "
                f"headless={actor_state.get('toxic_count', 0)} "
                f"expected={scenario.expected_toxic_count_after}"
            )

        if rom.hp_before != scenario.hp_before:
            errors.append(
                f"{scenario.scenario_id}: ROM hp_before mismatch: "
                f"rom={rom.hp_before} expected={scenario.hp_before}"
            )
        if rom.hp_after != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM hp_after mismatch: "
                f"rom={rom.hp_after} expected={scenario.expected_hp_after}"
            )
        if rom.toxic_count_before != scenario.toxic_count_before:
            errors.append(
                f"{scenario.scenario_id}: ROM toxic_count_before mismatch: "
                f"rom={rom.toxic_count_before} expected={scenario.toxic_count_before}"
            )
        if rom.toxic_count_after != scenario.expected_toxic_count_after:
            errors.append(
                f"{scenario.scenario_id}: ROM toxic_count_after mismatch: "
                f"rom={rom.toxic_count_after} expected={scenario.expected_toxic_count_after}"
            )
        if not rom.mutation_observed:
            errors.append(f"{scenario.scenario_id}: ROM residual mutation was not observed")

        rom_report[scenario.scenario_id] = {
            "actor": rom.actor,
            "status": rom.status_name,
            "hp_before": rom.hp_before,
            "hp_after": rom.hp_after,
            "max_hp": rom.max_hp,
            "damage": rom.hp_before - rom.hp_after,
            "toxic_count_before": rom.toxic_count_before,
            "toxic_count_after": rom.toxic_count_after,
            "mutation_observed": rom.mutation_observed,
            "returned": rom.returned,
            "ticks": rom.ticks,
            "post_pc": rom.post_pc,
        }
        headless_results[scenario.scenario_id] = {
            "final_hp": actor_state.get("hp"),
            "final_toxic_count": actor_state.get("toxic_count", 0),
            "residual_event": residual_event,
        }

    return DifferentialResult(
        scenario_id="basic_status_residual_component_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


def compare_drain_component() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_drain_components()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in DRAIN_COMPONENT_SCENARIOS:
        rom = rom_results[scenario.scenario_id]
        report = simulate_payload(drain_component_payload(scenario))
        outcome = report["outcomes"][0]
        drain_events = [
            event
            for event in outcome["events"]
            if event.get("actor") == "player"
            and event.get("move") == scenario.move_name
            and event.get("type") in {"drain_heal", "drain_heal_no_effect", "drain_no_effect"}
        ]
        damage_events = [
            event
            for event in outcome["events"]
            if event.get("actor") == "player" and event.get("move") == scenario.move_name and event.get("type") == "damage"
        ]
        if len(drain_events) != 1:
            errors.append(f"{scenario.scenario_id}: expected one headless drain event, got {len(drain_events)}")
            drain_event: dict[str, Any] = {}
        else:
            drain_event = drain_events[0]
        if len(damage_events) != 1:
            errors.append(f"{scenario.scenario_id}: expected one headless damage event, got {len(damage_events)}")
            damage_event: dict[str, Any] = {}
        else:
            damage_event = damage_events[0]

        if damage_event.get("actual_damage") != scenario.damage:
            errors.append(
                f"{scenario.scenario_id}: headless damage mismatch: "
                f"headless={damage_event.get('actual_damage')} expected={scenario.damage}"
            )
        if drain_event.get("damage_drained") != scenario.damage:
            errors.append(
                f"{scenario.scenario_id}: drain damage mismatch: "
                f"headless={drain_event.get('damage_drained')} expected={scenario.damage}"
            )
        if drain_event.get("raw_heal") != scenario.expected_raw_heal:
            errors.append(
                f"{scenario.scenario_id}: raw heal mismatch: "
                f"headless={drain_event.get('raw_heal')} expected={scenario.expected_raw_heal}"
            )
        if drain_event.get("heal") != scenario.expected_heal:
            errors.append(
                f"{scenario.scenario_id}: heal mismatch: "
                f"headless={drain_event.get('heal')} expected={scenario.expected_heal}"
            )
        if drain_event.get("hp_before") != scenario.hp_before or drain_event.get("hp_after") != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: headless HP mismatch: "
                f"{drain_event.get('hp_before')}->{drain_event.get('hp_after')} "
                f"expected={scenario.hp_before}->{scenario.expected_hp_after}"
            )
        if outcome["state"]["player"].get("hp") != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: final player HP mismatch: "
                f"headless={outcome['state']['player'].get('hp')} expected={scenario.expected_hp_after}"
            )

        if rom.hp_before != scenario.hp_before:
            errors.append(f"{scenario.scenario_id}: ROM hp_before={rom.hp_before}, expected {scenario.hp_before}")
        if rom.hp_after != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM hp_after mismatch: "
                f"rom={rom.hp_after} expected={scenario.expected_hp_after}"
            )
        if rom.damage != scenario.damage:
            errors.append(f"{scenario.scenario_id}: ROM damage={rom.damage}, expected {scenario.damage}")
        if rom.returned:
            errors.append(
                f"{scenario.scenario_id}: BattleCommand_DrainTarget unexpectedly returned; "
                "fixture expects animation/text non-return after HP write"
            )

        rom_report[scenario.scenario_id] = {
            "move": rom.move_name,
            "hp_before": rom.hp_before,
            "hp_after": rom.hp_after,
            "max_hp": rom.max_hp,
            "damage": rom.damage,
            "returned": rom.returned,
            "post_pc": rom.post_pc,
        }
        headless_results[scenario.scenario_id] = {
            "final_player_hp": outcome["state"]["player"].get("hp"),
            "rng_consumed": outcome.get("rng_consumed", []),
            "damage_event": damage_event,
            "drain_event": drain_event,
        }

    return DifferentialResult(
        scenario_id="drain_component_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


def compare_selected_drain_move_turn() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_drain_move_turns()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in DRAIN_MOVE_TURN_SCENARIOS:
        rom = rom_results[scenario.scenario_id]
        expected_pp_after = scenario.pp_before - 1
        if not rom.do_turn_returned:
            errors.append(f"{scenario.scenario_id}: BattleCommand_DoTurn did not return")
        if rom.drain_returned:
            errors.append(
                f"{scenario.scenario_id}: BattleCommand_DrainTarget unexpectedly returned; "
                "fixture expects animation/text non-return after HP write"
            )
        if rom.active_pp_after != expected_pp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM active PP mismatch: "
                f"{rom.active_pp_after} != {expected_pp_after}"
            )
        if rom.party_pp_after != expected_pp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM party PP mismatch: "
                f"{rom.party_pp_after} != {expected_pp_after}"
            )
        if rom.turns_taken_after != rom.turns_taken_before + 1:
            errors.append(
                f"{scenario.scenario_id}: ROM turns-taken mismatch: "
                f"{rom.turns_taken_before}->{rom.turns_taken_after}"
            )
        if rom.hp_before != scenario.hp_before or rom.hp_after != scenario.expected_hp_after:
            errors.append(
                f"{scenario.scenario_id}: ROM HP mismatch: "
                f"{rom.hp_before}->{rom.hp_after}, expected "
                f"{scenario.hp_before}->{scenario.expected_hp_after}"
            )
        if rom.damage != scenario.damage:
            errors.append(
                f"{scenario.scenario_id}: ROM wCurDamage mismatch: "
                f"{rom.damage} != {scenario.damage}"
            )

        report = simulate_payload(drain_move_turn_payload(scenario))
        outcome = report["outcomes"][0]
        damage_events = [
            event
            for event in outcome["events"]
            if event.get("actor") == "player"
            and event.get("move") == scenario.move_name
            and event.get("type") == "damage"
        ]
        drain_events = [
            event
            for event in outcome["events"]
            if event.get("actor") == "player"
            and event.get("move") == scenario.move_name
            and event.get("type") in {"drain_heal", "drain_heal_no_effect", "drain_no_effect"}
        ]
        if len(damage_events) != 1:
            errors.append(f"{scenario.scenario_id}: expected one headless damage event, got {len(damage_events)}")
            damage_event: dict[str, Any] = {}
        else:
            damage_event = damage_events[0]
        if len(drain_events) != 1:
            errors.append(f"{scenario.scenario_id}: expected one headless drain event, got {len(drain_events)}")
            drain_event: dict[str, Any] = {}
        else:
            drain_event = drain_events[0]

        if damage_event.get("actual_damage") != rom.damage:
            errors.append(
                f"{scenario.scenario_id}: headless damage mismatch: "
                f"{damage_event.get('actual_damage')} != {rom.damage}"
            )
        if damage_event.get("pp_before") != rom.pp_before:
            errors.append(
                f"{scenario.scenario_id}: headless pp_before mismatch: "
                f"{damage_event.get('pp_before')} != {rom.pp_before}"
            )
        if damage_event.get("pp_after") != rom.active_pp_after:
            errors.append(
                f"{scenario.scenario_id}: headless pp_after mismatch: "
                f"{damage_event.get('pp_after')} != {rom.active_pp_after}"
            )
        if drain_event.get("damage_drained") != rom.damage:
            errors.append(
                f"{scenario.scenario_id}: drain damage mismatch: "
                f"{drain_event.get('damage_drained')} != {rom.damage}"
            )
        if drain_event.get("raw_heal") != scenario.expected_raw_heal:
            errors.append(
                f"{scenario.scenario_id}: raw heal mismatch: "
                f"{drain_event.get('raw_heal')} != {scenario.expected_raw_heal}"
            )
        if drain_event.get("heal") != scenario.expected_heal:
            errors.append(
                f"{scenario.scenario_id}: heal mismatch: "
                f"{drain_event.get('heal')} != {scenario.expected_heal}"
            )
        if drain_event.get("hp_before") != rom.hp_before:
            errors.append(
                f"{scenario.scenario_id}: headless hp_before mismatch: "
                f"{drain_event.get('hp_before')} != {rom.hp_before}"
            )
        if drain_event.get("hp_after") != rom.hp_after:
            errors.append(
                f"{scenario.scenario_id}: headless hp_after mismatch: "
                f"{drain_event.get('hp_after')} != {rom.hp_after}"
            )
        player_state = outcome["state"]["player"]
        if player_state["hp"] != rom.hp_after:
            errors.append(
                f"{scenario.scenario_id}: final headless HP mismatch: "
                f"{player_state['hp']} != {rom.hp_after}"
            )
        if player_state["moves"][0]["pp"] != rom.active_pp_after:
            errors.append(
                f"{scenario.scenario_id}: final headless PP mismatch: "
                f"{player_state['moves'][0]['pp']} != {rom.active_pp_after}"
            )

        rom_report[scenario.scenario_id] = {
            "move": rom.move_name,
            "hp": f"{rom.hp_before}->{rom.hp_after}",
            "max_hp": rom.max_hp,
            "damage": rom.damage,
            "pp": f"{rom.pp_before}->{rom.active_pp_after}",
            "party_pp_after": rom.party_pp_after,
            "turns_taken": f"{rom.turns_taken_before}->{rom.turns_taken_after}",
            "do_turn_returned": rom.do_turn_returned,
            "drain_returned": rom.drain_returned,
            "post_pc": rom.post_pc,
        }
        headless_results[scenario.scenario_id] = {
            "damage_event": damage_event,
            "drain_event": drain_event,
            "final_hp": player_state["hp"],
            "final_pp": player_state["moves"][0]["pp"],
        }

    return DifferentialResult(
        scenario_id="selected_drain_move_turn_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


def compare_damaging_status_component() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_status_components()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in STATUS_COMPONENT_SCENARIOS:
        rom = rom_results[scenario.scenario_id]
        report = simulate_payload(damaging_status_component_payload(scenario))
        outcome = report["outcomes"][0]
        status_events = [
            event
            for event in outcome["events"]
            if event.get("actor") == "player"
            and event.get("move") == scenario.move_name
            and event.get("status") == scenario.status_name
            and event.get("type") in {"status_apply", "status_no_effect"}
        ]
        if len(status_events) != 1:
            errors.append(f"{scenario.scenario_id}: expected one headless status event, got {len(status_events)}")
            status_event: dict[str, Any] = {}
        else:
            status_event = status_events[0]

        expected_event_type = "status_apply" if scenario.expect_success else "status_no_effect"
        expected_status = scenario.status_name if scenario.expect_success else "none"
        if status_event.get("type") != expected_event_type:
            errors.append(
                f"{scenario.scenario_id}: event type mismatch: "
                f"headless={status_event.get('type')} expected={expected_event_type}"
            )
        if status_event.get("status_after") != expected_status:
            errors.append(
                f"{scenario.scenario_id}: status_after mismatch: "
                f"headless={status_event.get('status_after')} expected={expected_status}"
            )
        effect_check = status_event.get("effect_chance_check", {})
        if effect_check.get("threshold") != scenario.chance_threshold:
            errors.append(
                f"{scenario.scenario_id}: effect threshold mismatch: "
                f"headless={effect_check.get('threshold')} rom_seed={scenario.chance_threshold}"
            )
        if effect_check.get("raw_values") != [scenario.effect_chance_rng]:
            errors.append(
                f"{scenario.scenario_id}: effect RNG mismatch: "
                f"headless={effect_check.get('raw_values')} rom={[scenario.effect_chance_rng]}"
            )
        if bool(effect_check.get("success")) != scenario.expect_success:
            errors.append(
                f"{scenario.scenario_id}: effect success mismatch: "
                f"headless={effect_check.get('success')} expected={scenario.expect_success}"
            )
        if outcome["state"]["enemy"].get("status") != expected_status:
            errors.append(
                f"{scenario.scenario_id}: final headless target status mismatch: "
                f"headless={outcome['state']['enemy'].get('status')} expected={expected_status}"
            )

        if rom.status_before != 0:
            errors.append(f"{scenario.scenario_id}: ROM status_before={rom.status_before}, expected 0")
        if rom.status_after != scenario.expected_status_byte:
            errors.append(
                f"{scenario.scenario_id}: ROM status byte mismatch: "
                f"rom=0x{rom.status_after:02x} expected=0x{scenario.expected_status_byte:02x}"
            )
        if rom.effect_failed == scenario.expect_success:
            errors.append(
                f"{scenario.scenario_id}: ROM wEffectFailed mismatch: "
                f"rom={rom.effect_failed} expected={not scenario.expect_success}"
            )
        if rom.effect_chance_consumed != 1:
            errors.append(
                f"{scenario.scenario_id}: ROM effect chance RNG consumption mismatch: "
                f"consumed={rom.effect_chance_consumed}"
            )
        if not rom.effect_chance_returned:
            errors.append(f"{scenario.scenario_id}: BattleCommand_EffectChance did not return")
        if scenario.expect_success and rom.target_command_returned:
            errors.append(
                f"{scenario.scenario_id}: {scenario.target_command} unexpectedly returned; "
                "fixture expects animation/text non-return after status write"
            )
        if not scenario.expect_success and not rom.target_command_returned:
            errors.append(f"{scenario.scenario_id}: {scenario.target_command} did not return on effect-failed early exit")

        rom_report[scenario.scenario_id] = {
            "move": rom.move_name,
            "status": rom.status_name,
            "status_before": rom.status_before,
            "status_after": rom.status_after,
            "effect_failed": rom.effect_failed,
            "effect_chance_rng": rom.effect_chance_rng,
            "effect_chance_consumed": rom.effect_chance_consumed,
            "effect_chance_returned": rom.effect_chance_returned,
            "target_command_returned": rom.target_command_returned,
            "target_command_pc": rom.target_command_pc,
        }
        headless_results[scenario.scenario_id] = {
            "final_enemy_status": outcome["state"]["enemy"].get("status"),
            "rng_consumed": outcome.get("rng_consumed", []),
            "status_event": status_event,
        }

    return DifferentialResult(
        scenario_id="damaging_status_component_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


@dataclass(frozen=True)
class DamageVariationScenario:
    scenario_id: str
    cur_damage: int
    rng_values: tuple[int, ...]
    expected_final_damage: int
    expected_rn_consumed: int
    expected_multiplier: int | None
    expected_applied: bool


# BattleCommand_DamageVariation rotates each BattleRandom byte right, rejects any
# rotated value below 85 percent + 1 (217), then scales damage by the accepted
# 217..255 multiplier over 100 percent (255). 0/1 damage skips the whole roll.
# These cases pin the reject-then-accept RNG branching and the multiply/divide
# arithmetic against the ROM byte for byte; the simulator's
# damage_variation_results mirror is the headless oracle. The accepted multiplier
# is not a stable ROM read (hMultiplier aliases hProduct/hQuotient and is
# clobbered by Multiply/Divide), so the ROM-observable proof is the final
# wCurDamage plus the wLinkBattleRNCount consumption.
DAMAGE_VARIATION_SCENARIOS = (
    DamageVariationScenario(
        scenario_id="damage_variation_zero_damage_skips_roll",
        cur_damage=0,
        rng_values=(),
        expected_final_damage=0,
        expected_rn_consumed=0,
        expected_multiplier=None,
        expected_applied=False,
    ),
    DamageVariationScenario(
        scenario_id="damage_variation_one_damage_skips_roll",
        cur_damage=1,
        rng_values=(),
        expected_final_damage=1,
        expected_rn_consumed=0,
        expected_multiplier=None,
        expected_applied=False,
    ),
    DamageVariationScenario(
        scenario_id="damage_variation_rejects_low_byte_then_accepts_min_multiplier",
        cur_damage=100,
        rng_values=(0, 179),
        expected_final_damage=85,
        expected_rn_consumed=2,
        expected_multiplier=217,
        expected_applied=True,
    ),
    DamageVariationScenario(
        scenario_id="damage_variation_two_byte_damage_max_multiplier",
        cur_damage=300,
        rng_values=(255,),
        expected_final_damage=300,
        expected_rn_consumed=1,
        expected_multiplier=255,
        expected_applied=True,
    ),
)


@dataclass(frozen=True)
class RomDamageVariationResult:
    scenario_id: str
    cur_damage_before: int
    cur_damage_after: int
    rn_consumed: int
    returned: bool
    post_pc: int


@dataclass(frozen=True)
class MirrorDamageVariationResult:
    scenario_id: str
    final_damage: int
    multiplier: int | None
    applied: bool
    raw_values: tuple[int, ...]


def _seed_rom_damage_variation(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: DamageVariationScenario,
) -> None:
    _seed_common(pyboy, syms)
    _write_byte(pyboy, syms, "wLinkMode", LINK_MODE)
    _write_byte(pyboy, syms, "wLinkBattleRNCount", 0)
    for index, value in enumerate(scenario.rng_values):
        _write_byte(pyboy, syms, "wLinkBattleRNs", value, index)
    _write_u16(pyboy, syms, "wCurDamage", scenario.cur_damage)


def run_rom_damage_variations() -> tuple[RomDamageVariationResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomDamageVariationResult] = []
    try:
        for scenario in DAMAGE_VARIATION_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_damage_variation(pyboy, syms, scenario)
            cur_damage_before = _read_u16(pyboy, syms, "wCurDamage")
            _, returned, post_pc = call_function_safe(
                pyboy,
                syms,
                "BattleCommand_DamageVariation",
                budget=CALL_BUDGET,
            )
            results.append(
                RomDamageVariationResult(
                    scenario_id=scenario.scenario_id,
                    cur_damage_before=cur_damage_before,
                    cur_damage_after=_read_u16(pyboy, syms, "wCurDamage"),
                    rn_consumed=_read_byte(pyboy, syms, "wLinkBattleRNCount"),
                    returned=returned,
                    post_pc=post_pc,
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def run_mirror_damage_variation(scenario: DamageVariationScenario) -> MirrorDamageVariationResult:
    config = RngConfig(mode="fixed", values=scenario.rng_values)
    stream = RuntimeRng(config)
    outcomes = damage_variation_results(scenario.cur_damage, config, stream=stream)
    if len(outcomes) != 1:
        raise AssertionError(
            f"{scenario.scenario_id}: fixed-mode mirror returned {len(outcomes)} outcomes"
        )
    outcome = outcomes[0]
    return MirrorDamageVariationResult(
        scenario_id=scenario.scenario_id,
        final_damage=int(outcome["damage"]),
        multiplier=outcome["multiplier"],
        applied=bool(outcome["applied"]),
        raw_values=tuple(outcome["raw_values"]),
    )


def compare_damage_variation_component() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_damage_variations()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in DAMAGE_VARIATION_SCENARIOS:
        rom = rom_results[scenario.scenario_id]
        mirror = run_mirror_damage_variation(scenario)

        if not rom.returned:
            errors.append(f"{scenario.scenario_id}: BattleCommand_DamageVariation did not return")
        if rom.cur_damage_before != scenario.cur_damage:
            errors.append(
                f"{scenario.scenario_id}: ROM wCurDamage seed mismatch: "
                f"{rom.cur_damage_before} != {scenario.cur_damage}"
            )
        if rom.cur_damage_after != scenario.expected_final_damage:
            errors.append(
                f"{scenario.scenario_id}: ROM final damage mismatch: "
                f"{rom.cur_damage_after} != {scenario.expected_final_damage}"
            )
        if rom.rn_consumed != scenario.expected_rn_consumed:
            errors.append(
                f"{scenario.scenario_id}: ROM RNG consumption mismatch: "
                f"{rom.rn_consumed} != {scenario.expected_rn_consumed}"
            )

        if mirror.final_damage != scenario.expected_final_damage:
            errors.append(
                f"{scenario.scenario_id}: mirror final damage mismatch: "
                f"{mirror.final_damage} != {scenario.expected_final_damage}"
            )
        if mirror.multiplier != scenario.expected_multiplier:
            errors.append(
                f"{scenario.scenario_id}: mirror multiplier mismatch: "
                f"{mirror.multiplier} != {scenario.expected_multiplier}"
            )
        if mirror.applied != scenario.expected_applied:
            errors.append(
                f"{scenario.scenario_id}: mirror applied flag mismatch: "
                f"{mirror.applied} != {scenario.expected_applied}"
            )
        if len(mirror.raw_values) != scenario.expected_rn_consumed:
            errors.append(
                f"{scenario.scenario_id}: mirror RNG consumption mismatch: "
                f"{len(mirror.raw_values)} != {scenario.expected_rn_consumed}"
            )

        # The core differential: ROM and the headless mirror agree byte for byte
        # on the varied damage and on how many BattleRandom bytes were consumed.
        if rom.cur_damage_after != mirror.final_damage:
            errors.append(
                f"{scenario.scenario_id}: ROM vs mirror final damage divergence: "
                f"{rom.cur_damage_after} != {mirror.final_damage}"
            )
        if rom.rn_consumed != len(mirror.raw_values):
            errors.append(
                f"{scenario.scenario_id}: ROM vs mirror RNG consumption divergence: "
                f"{rom.rn_consumed} != {len(mirror.raw_values)}"
            )

        rom_report[scenario.scenario_id] = {
            "cur_damage": f"{rom.cur_damage_before}->{rom.cur_damage_after}",
            "rng_values": list(scenario.rng_values),
            "rn_consumed": rom.rn_consumed,
            "returned": rom.returned,
            "post_pc": rom.post_pc,
        }
        headless_results[scenario.scenario_id] = {
            "final_damage": mirror.final_damage,
            "multiplier": mirror.multiplier,
            "applied": mirror.applied,
            "raw_values": list(mirror.raw_values),
        }

    return DifferentialResult(
        scenario_id="damage_variation_component_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


@dataclass(frozen=True)
class CriticalScenario:
    scenario_id: str
    move_name: str
    move_id: int
    move_power: int
    species_name: str
    species_id: int
    item_name: str | None
    item_id: int
    focus_energy: bool
    rng_values: tuple[int, ...]
    expected_critical: bool
    expected_rn_consumed: int
    expected_level: int | None
    expected_threshold: int | None


# BattleCommand_Critical zeroes wCriticalHit, returns early (no BattleRandom) when
# move power is 0, otherwise tallies a critical level c from the user's
# species+item (Chansey/Lucky Punch or Farfetch'd/Stick force c=2 and skip the
# rest), Focus Energy (+1), a high-crit move via IsInArray over CriticalHitMoves
# (+2), and Scope Lens / HELD_CRITICAL_UP (+1). It then rolls one BattleRandom
# and crits iff raw < CriticalHitChances[c] (= [17, 32, 64, 85, 128, 128, 128]).
# Each elevated case below picks an RNG byte that crits ONLY at its level (20
# clears level-1's 32 but not level-0's 17; 40 clears level-2's 64 but not 17/32),
# so the crit outcome discriminates the tallied level. The simulator's
# critical_results / critical_level mirror is the headless oracle; the power-0
# early return lives one level up, so the mirror wrapper models it explicitly.
CRITICAL_SCENARIOS = (
    CriticalScenario(
        scenario_id="critical_power_zero_skips_roll",
        move_name="TACKLE",
        move_id=TACKLE_MOVE_ID,
        move_power=0,
        species_name="CYNDAQUIL",
        species_id=CYNDAQUIL_SPECIES,
        item_name=None,
        item_id=0,
        focus_energy=False,
        rng_values=(),
        expected_critical=False,
        expected_rn_consumed=0,
        expected_level=None,
        expected_threshold=None,
    ),
    CriticalScenario(
        scenario_id="critical_base_level_crit_min_roll",
        move_name="TACKLE",
        move_id=TACKLE_MOVE_ID,
        move_power=40,
        species_name="CYNDAQUIL",
        species_id=CYNDAQUIL_SPECIES,
        item_name=None,
        item_id=0,
        focus_energy=False,
        rng_values=(0,),
        expected_critical=True,
        expected_rn_consumed=1,
        expected_level=0,
        expected_threshold=17,
    ),
    CriticalScenario(
        scenario_id="critical_base_level_no_crit_at_threshold",
        move_name="TACKLE",
        move_id=TACKLE_MOVE_ID,
        move_power=40,
        species_name="CYNDAQUIL",
        species_id=CYNDAQUIL_SPECIES,
        item_name=None,
        item_id=0,
        focus_energy=False,
        rng_values=(17,),
        expected_critical=False,
        expected_rn_consumed=1,
        expected_level=0,
        expected_threshold=17,
    ),
    CriticalScenario(
        scenario_id="critical_focus_energy_level1_crit",
        move_name="TACKLE",
        move_id=TACKLE_MOVE_ID,
        move_power=40,
        species_name="CYNDAQUIL",
        species_id=CYNDAQUIL_SPECIES,
        item_name=None,
        item_id=0,
        focus_energy=True,
        rng_values=(20,),
        expected_critical=True,
        expected_rn_consumed=1,
        expected_level=1,
        expected_threshold=32,
    ),
    CriticalScenario(
        scenario_id="critical_scope_lens_level1_crit",
        move_name="TACKLE",
        move_id=TACKLE_MOVE_ID,
        move_power=40,
        species_name="CYNDAQUIL",
        species_id=CYNDAQUIL_SPECIES,
        item_name="SCOPE_LENS",
        item_id=ITEM_SCOPE_LENS,
        focus_energy=False,
        rng_values=(20,),
        expected_critical=True,
        expected_rn_consumed=1,
        expected_level=1,
        expected_threshold=32,
    ),
    CriticalScenario(
        scenario_id="critical_high_crit_move_level2_crit",
        move_name="SLASH",
        move_id=SLASH_MOVE_ID,
        move_power=40,
        species_name="CYNDAQUIL",
        species_id=CYNDAQUIL_SPECIES,
        item_name=None,
        item_id=0,
        focus_energy=False,
        rng_values=(40,),
        expected_critical=True,
        expected_rn_consumed=1,
        expected_level=2,
        expected_threshold=64,
    ),
    CriticalScenario(
        scenario_id="critical_lucky_punch_chansey_level2_crit",
        move_name="TACKLE",
        move_id=TACKLE_MOVE_ID,
        move_power=40,
        species_name="CHANSEY",
        species_id=CHANSEY_SPECIES,
        item_name="LUCKY_PUNCH",
        item_id=ITEM_LUCKY_PUNCH,
        focus_energy=False,
        rng_values=(40,),
        expected_critical=True,
        expected_rn_consumed=1,
        expected_level=2,
        expected_threshold=64,
    ),
)


@dataclass(frozen=True)
class RomCriticalResult:
    scenario_id: str
    critical: bool
    rn_consumed: int
    returned: bool
    post_pc: int


@dataclass(frozen=True)
class MirrorCriticalResult:
    scenario_id: str
    critical: bool
    level: int | None
    threshold: int | None
    raw_values: tuple[int, ...]


def _seed_rom_critical(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    scenario: CriticalScenario,
) -> None:
    _seed_common(pyboy, syms)

    _write_byte(pyboy, syms, "wBattleMode", 1)
    _write_byte(pyboy, syms, "hBattleTurn", 0)
    _write_byte(pyboy, syms, "wBattleMonSpecies", scenario.species_id)
    _write_byte(pyboy, syms, "wBattleMonItem", scenario.item_id)
    _write_byte(pyboy, syms, "wCurPlayerMove", scenario.move_id)
    _write_byte(pyboy, syms, "wCurMoveNum", 0)
    _write_byte(
        pyboy,
        syms,
        "wPlayerSubStatus4",
        SUBSTATUS_FOCUS_ENERGY_MASK if scenario.focus_energy else 0,
    )

    for offset, value in (
        (0, scenario.move_id),     # MOVE_ANIM (read by the high-crit IsInArray)
        (1, 0x00),                 # MOVE_EFFECT
        (2, scenario.move_power),  # MOVE_POWER (0 triggers the early return)
        (3, NORMAL_TYPE),          # MOVE_TYPE
        (4, 0xFF),                 # MOVE_ACC
        (5, 35),                   # MOVE_PP
        (6, 0),                    # MOVE_CHANCE
    ):
        _write_byte(pyboy, syms, "wPlayerMoveStruct", value, offset)

    _write_byte(pyboy, syms, "wLinkMode", LINK_MODE)
    _write_byte(pyboy, syms, "wLinkBattleRNCount", 0)
    for index, value in enumerate(scenario.rng_values):
        _write_byte(pyboy, syms, "wLinkBattleRNs", value, index)


def run_rom_criticals() -> tuple[RomCriticalResult, ...]:
    rom = find_rom("pokegold_debug")
    syms = SymbolTable.load(find_sym("pokegold_debug")).as_legacy_dict()
    cache = BootStateCache(rom)
    pyboy = cache.prime()
    results: list[RomCriticalResult] = []
    try:
        for scenario in CRITICAL_SCENARIOS:
            pyboy = cache.restore()
            _seed_rom_critical(pyboy, syms, scenario)
            _, returned, post_pc = call_function_safe(
                pyboy,
                syms,
                "BattleCommand_Critical",
                budget=CALL_BUDGET,
            )
            results.append(
                RomCriticalResult(
                    scenario_id=scenario.scenario_id,
                    critical=bool(_read_byte(pyboy, syms, "wCriticalHit")),
                    rn_consumed=_read_byte(pyboy, syms, "wLinkBattleRNCount"),
                    returned=returned,
                    post_pc=post_pc,
                )
            )
        return tuple(results)
    finally:
        cache.stop()


def _critical_mirror_attacker(scenario: CriticalScenario) -> PokemonState:
    return PokemonState(
        side="player",
        name=scenario.species_name,
        level=50,
        hp=100,
        max_hp=100,
        types=(NORMAL_TYPE, NORMAL_TYPE),
        type_names=("NORMAL", "NORMAL"),
        attack=100,
        defense=100,
        speed=100,
        sp_attack=100,
        sp_defense=100,
        item=scenario.item_id,
        focus_energy=scenario.focus_energy,
    )


def _critical_mirror_move(scenario: CriticalScenario) -> MoveState:
    return MoveState(
        name=scenario.move_name,
        effect="EFFECT_NORMAL_HIT",
        move_type=NORMAL_TYPE,
        move_type_name="NORMAL",
        bp=scenario.move_power,
    )


def run_mirror_critical(scenario: CriticalScenario) -> MirrorCriticalResult:
    if scenario.move_power == 0:
        # BattleCommand_Critical's `ret z` on zero move power: no BattleRandom,
        # no critical. critical_results assumes a damaging move, so the power-0
        # branch is modeled here rather than inside the mirror.
        return MirrorCriticalResult(
            scenario_id=scenario.scenario_id,
            critical=False,
            level=None,
            threshold=None,
            raw_values=(),
        )
    config = RngConfig(mode="fixed", values=scenario.rng_values)
    stream = RuntimeRng(config)
    outcomes = critical_results(
        _critical_mirror_attacker(scenario),
        _critical_mirror_move(scenario),
        config,
        stream=stream,
    )
    if len(outcomes) != 1:
        raise AssertionError(
            f"{scenario.scenario_id}: fixed-mode mirror returned {len(outcomes)} outcomes"
        )
    outcome = outcomes[0]
    return MirrorCriticalResult(
        scenario_id=scenario.scenario_id,
        critical=bool(outcome["critical"]),
        level=outcome["level"],
        threshold=outcome["threshold"],
        raw_values=tuple(outcome["raw_values"]),
    )


def compare_critical_component() -> DifferentialResult:
    rom_results = {result.scenario_id: result for result in run_rom_criticals()}
    errors: list[str] = []
    headless_results: dict[str, Any] = {}
    rom_report: dict[str, Any] = {}

    for scenario in CRITICAL_SCENARIOS:
        rom = rom_results[scenario.scenario_id]
        mirror = run_mirror_critical(scenario)

        if not rom.returned:
            errors.append(f"{scenario.scenario_id}: BattleCommand_Critical did not return")
        if rom.critical != scenario.expected_critical:
            errors.append(
                f"{scenario.scenario_id}: ROM wCriticalHit mismatch: "
                f"{rom.critical} != {scenario.expected_critical}"
            )
        if rom.rn_consumed != scenario.expected_rn_consumed:
            errors.append(
                f"{scenario.scenario_id}: ROM RNG consumption mismatch: "
                f"{rom.rn_consumed} != {scenario.expected_rn_consumed}"
            )

        if mirror.critical != scenario.expected_critical:
            errors.append(
                f"{scenario.scenario_id}: mirror critical mismatch: "
                f"{mirror.critical} != {scenario.expected_critical}"
            )
        if mirror.level != scenario.expected_level:
            errors.append(
                f"{scenario.scenario_id}: mirror level mismatch: "
                f"{mirror.level} != {scenario.expected_level}"
            )
        if mirror.threshold != scenario.expected_threshold:
            errors.append(
                f"{scenario.scenario_id}: mirror threshold mismatch: "
                f"{mirror.threshold} != {scenario.expected_threshold}"
            )
        if len(mirror.raw_values) != scenario.expected_rn_consumed:
            errors.append(
                f"{scenario.scenario_id}: mirror RNG consumption mismatch: "
                f"{len(mirror.raw_values)} != {scenario.expected_rn_consumed}"
            )

        # The core differential: ROM and the headless mirror agree on whether the
        # hit is critical and on how many BattleRandom bytes were consumed.
        if rom.critical != mirror.critical:
            errors.append(
                f"{scenario.scenario_id}: ROM vs mirror critical divergence: "
                f"{rom.critical} != {mirror.critical}"
            )
        if rom.rn_consumed != len(mirror.raw_values):
            errors.append(
                f"{scenario.scenario_id}: ROM vs mirror RNG consumption divergence: "
                f"{rom.rn_consumed} != {len(mirror.raw_values)}"
            )

        rom_report[scenario.scenario_id] = {
            "move": scenario.move_name,
            "item": scenario.item_name,
            "focus_energy": scenario.focus_energy,
            "rng_values": list(scenario.rng_values),
            "critical": rom.critical,
            "rn_consumed": rom.rn_consumed,
            "returned": rom.returned,
            "post_pc": rom.post_pc,
        }
        headless_results[scenario.scenario_id] = {
            "critical": mirror.critical,
            "level": mirror.level,
            "threshold": mirror.threshold,
            "raw_values": list(mirror.raw_values),
        }

    return DifferentialResult(
        scenario_id="critical_component_differential",
        ok=not errors,
        errors=tuple(errors),
        rom=rom_report,
        headless=headless_results,
    )


def run_all_differentials() -> tuple[DifferentialResult, ...]:
    return (
        *compare_normal_hit_differentials(),
        compare_damage_variation_component(),
        compare_critical_component(),
        compare_damaging_status_component(),
        compare_drain_component(),
        compare_selected_drain_move_turn(),
        compare_item_restore_component(),
        compare_full_restore_status_cure(),
        compare_basic_pp_decrement_component(),
        compare_weather_setup_component(),
        compare_selected_substitute_move_turn(),
        compare_selected_self_heal_move_turn(),
        compare_selected_rest_move_turn(),
        compare_supported_after_hit_item_effects(),
        compare_basic_status_residual_component(),
    )


def build_report(results: tuple[DifferentialResult, ...]) -> dict[str, Any]:
    failed = [result for result in results if not result.ok]
    return {
        "kind": "headless_battle_component_rom_differential",
        "schema_version": 1,
        "proof_status": "complete" if not failed else "missing_evidence",
        "scenario_count": len(results),
        "pass_count": len(results) - len(failed),
        "fail_count": len(failed),
        "missing_evidence": [
            f"{result.scenario_id}: {error}"
            for result in failed
            for error in result.errors
        ],
        "results": [result.to_jsonable() for result in results],
    }


def print_text_report(results: tuple[DifferentialResult, ...]) -> None:
    for result in results:
        if result.ok:
            if result.scenario_id.startswith("normal_hit_"):
                print(
                    f"{result.scenario_id}: PASS "
                    f"damage={result.rom['damage']} "
                    f"missed={result.rom['attack_missed']} "
                    f"critical={result.rom['critical']} "
                    f"hp={result.rom['player_hp_before']}->{result.rom['player_hp_after']} "
                    f"pp={result.rom['enemy_pp_before']}->{result.rom['enemy_pp_after']}"
                )
            else:
                print(f"{result.scenario_id}: PASS " + " ".join(result.rom.keys()))
            continue
        print(f"{result.scenario_id}: FAIL")
        for error in result.errors:
            print(f"  - {error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="print structured JSON instead of text")
    parser.add_argument("--json-out", default="", help="write structured JSON report to this path")
    args = parser.parse_args(argv)

    results = run_all_differentials()
    report = build_report(results)
    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(results)
    return 0 if report["proof_status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
