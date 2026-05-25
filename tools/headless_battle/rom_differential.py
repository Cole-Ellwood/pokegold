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
BODY_SLAM_MOVE_ID = 0x22
EMBER_MOVE_ID = 0x34
SLUDGE_MOVE_ID = 0x7C
ABSORB_MOVE_ID = 0x47
GIGA_DRAIN_MOVE_ID = 0xCA
FULL_RESTORE_ITEM_ID = 0x0E
MAX_POTION_ITEM_ID = 0x0F
HYPER_POTION_ITEM_ID = 0x10
POTION_ITEM_ID = 0x12
NORMAL_TYPE = 0x00
POISON_TYPE = 0x03
FLYING_TYPE = 0x02
FIRE_TYPE = 0x14
LINK_MODE = 1
FIXED_RNG_VALUES = (255, 255)
CALL_BUDGET = 50_000
COMPONENT_NONRETURN_CALL_BUDGET = 500
PSN_STATUS = 1 << 3
BRN_STATUS = 1 << 4
PAR_STATUS = 1 << 6
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


def main() -> int:
    normal_result = compare_normal_hit_fixed_rng()
    status_result = compare_damaging_status_component()
    drain_result = compare_drain_component()
    item_result = compare_item_restore_component()
    if normal_result.ok:
        print(
            "normal_hit_fixed_rng_differential: PASS "
            f"damage={normal_result.rom['damage']} "
            f"hp={normal_result.rom['player_hp_before']}->{normal_result.rom['player_hp_after']} "
            f"pp={normal_result.rom['enemy_pp_before']}->{normal_result.rom['enemy_pp_after']}"
        )
    else:
        print("normal_hit_fixed_rng_differential: FAIL")
        for error in normal_result.errors:
            print(f"  - {error}")
    if status_result.ok:
        print(
            "damaging_status_component_differential: PASS "
            + " ".join(status_result.rom.keys())
        )
    else:
        print("damaging_status_component_differential: FAIL")
        for error in status_result.errors:
            print(f"  - {error}")
    if drain_result.ok:
        print("drain_component_differential: PASS " + " ".join(drain_result.rom.keys()))
    else:
        print("drain_component_differential: FAIL")
        for error in drain_result.errors:
            print(f"  - {error}")
    if item_result.ok:
        print("item_restore_component_differential: PASS " + " ".join(item_result.rom.keys()))
    else:
        print("item_restore_component_differential: FAIL")
        for error in item_result.errors:
            print(f"  - {error}")
    return 0 if normal_result.ok and status_result.ok and drain_result.ok and item_result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
