"""Headless board -> rom-switch-materialize scenario exporter (slice A).

Slice A from ``docs/headless_to_rom_switch_materialize_scoping.md``:
convert a headless ``BattleState`` (or a state-shaped dict) into a
``family=switch_sack`` scenario dict that ``rom-switch-materialize``
can run.

This exporter is intentionally strict. The materializer's
``switch_materialization_patches`` hardcodes the fixture (Starmie vs
Qwilfish with Gengar on the bench, types overridden, no status /
screens / items, etc.), so we reject any headless board that does not
already match that fixture instead of silently mapping it onto a
different ROM situation. Out-of-fixture boards need slice B (a
parameterized materializer) or slice C (a full board materializer).

The two HP-driven condition tags are the only board-derived inputs:

- ``defensive_sack_owner`` when enemy HP <= ``DEFENSIVE_SACK_HP_THRESHOLD``
- ``active_pressure_converts`` when player HP <= ``ACTIVE_PRESSURE_HP_THRESHOLD``

Callers can pass additional tags (``wincon_preservation`` etc) via
``extra_tags`` and a custom ``policy_case`` label.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterable

from tools.boss_ai_debugger.role_packages import parse_species_order
from tools.headless_battle.simulator import (
    BattleState,
    PokemonState,
    SimulationInputError,
    parse_state,
)


FIXTURE_PLAYER_NAME = "STARMIE"
FIXTURE_PLAYER_TYPES = ("GROUND", "GROUND")
FIXTURE_ENEMY_NAME = "QWILFISH"
FIXTURE_ENEMY_TYPES = ("POISON", "WATER")
FIXTURE_ENEMY_BENCH_NAME = "GENGAR"
DEFENSIVE_SACK_HP_THRESHOLD = 30
ACTIVE_PRESSURE_HP_THRESHOLD = 30
ALLOWED_TIERS = frozenset({"early", "mid", "late"})
ALLOWED_HELD_ITEM = 0  # oracle.HELD_NONE; matches wEnemyMonItem = NO_ITEM in the fixture
ALLOWED_STATUS = "none"
ALLOWED_STAT_STAGES = (0, 0, 0, 0, 0)
DEFAULT_POLICY_CASE = "exported_headless_board"
# Status strings that slice C-status can materialize. Sleep needs the
# sleep_turns counter packed into the status byte (slice C-sleep), and
# toxic needs the SUBSTATUS_TOXIC bit in wPlayerSubStatus5/wEnemySubStatus5
# (slice C-toxic) -- both deferred.
STATUS_STRING_TO_BYTE = {
    "none": 0,
    "burn": 1 << 4,
    "poison": 1 << 3,
    "paralyze": 1 << 6,
}
OVERRIDABLE_STATUSES = frozenset(STATUS_STRING_TO_BYTE)


@lru_cache(maxsize=1)
def _species_name_to_id() -> dict[str, int]:
    # parse_species_order returns 251 species in id-1-indexed order.
    order = parse_species_order()
    return {name.upper(): index + 1 for index, name in enumerate(order)}


def species_id_for(name: str) -> int:
    table = _species_name_to_id()
    try:
        return table[name.upper()]
    except KeyError as exc:
        raise SimulationInputError(
            f"rom_switch_scenario_export: unknown species name {name!r}; "
            "pass an integer species id directly via overrides if needed"
        ) from exc


def headless_to_switch_sack_scenario(
    state: BattleState | dict[str, Any],
    *,
    scenario_id: str = "exported",
    tier: str = "mid",
    extra_tags: Iterable[str] | None = None,
    policy_case: str | None = None,
    accept_overrides: bool = False,
) -> dict[str, Any]:
    """Return a ``family=switch_sack`` scenario dict from a headless board.

    By default (``accept_overrides=False``), the board must match the
    hardcoded fixture in ``switch_materialization_patches``
    (Starmie/Qwilfish/Gengar, no statuses, no weather, etc.) and the
    exporter raises ``SimulationInputError`` with a specific reason
    when it does not. This is slice A (fixture-match-or-reject).

    With ``accept_overrides=True`` (slice B), the exporter emits an
    ``overrides`` dict in the scenario carrying the board's actual
    species/types/HP for the player active, enemy active, and enemy
    bench[0]. The materializer picks these up. Other constraints
    (no status / weather / spikes / safeguard / item / stat stages /
    substitute) still apply because slice B does not patch those WRAM
    fields. Slice C (full board materialization) is future work.
    """
    if tier not in ALLOWED_TIERS:
        raise SimulationInputError(
            f"rom_switch_scenario_export: tier {tier!r} not in {sorted(ALLOWED_TIERS)}"
        )
    battle_state = state if isinstance(state, BattleState) else parse_state(state)
    if not accept_overrides:
        _assert_fixture_active(battle_state.player, side="player")
        _assert_fixture_active(battle_state.enemy, side="enemy")
        _assert_fixture_enemy_bench(battle_state.enemy_bench)
    else:
        _assert_overridable_active(battle_state.player, side="player")
        _assert_overridable_active(battle_state.enemy, side="enemy")
        _assert_overridable_enemy_bench(battle_state.enemy_bench)
    _assert_no_field_state(battle_state)
    tags = _derive_hp_tags(battle_state.player, battle_state.enemy)
    if extra_tags is not None:
        for tag in extra_tags:
            tags.add(str(tag))
    tags.add("switch_sack")
    scenario: dict[str, Any] = {
        "id": scenario_id,
        "family": "switch_sack",
        "tier": tier,
        "expectation": {
            "condition_tags": sorted(tags),
        },
        "moves": [],
        "policy_case": policy_case or DEFAULT_POLICY_CASE,
        "notes": [
            "exported from headless BattleState by tools.headless_battle.rom_switch_scenario_export"
        ],
        "exporter": {
            "name": "headless_to_switch_sack_scenario",
            "fixture_domain": (
                "parameterized_overrides" if accept_overrides else "starmie_vs_qwilfish_gengar_bench"
            ),
            "player_hp": battle_state.player.hp,
            "enemy_hp": battle_state.enemy.hp,
        },
    }
    if accept_overrides:
        scenario["overrides"] = _board_to_overrides(battle_state)
    return scenario


def _board_to_overrides(battle_state: BattleState) -> dict[str, Any]:
    bench_lead = battle_state.enemy_bench[0]
    return {
        "player_species": species_id_for(battle_state.player.name),
        "player_type1": battle_state.player.types[0],
        "player_type2": battle_state.player.types[1],
        "player_hp": battle_state.player.hp,
        "player_max_hp": battle_state.player.max_hp,
        "player_status": STATUS_STRING_TO_BYTE[battle_state.player.status],
        "enemy_species": species_id_for(battle_state.enemy.name),
        "enemy_type1": battle_state.enemy.types[0],
        "enemy_type2": battle_state.enemy.types[1],
        "enemy_hp": battle_state.enemy.hp,
        "enemy_max_hp": battle_state.enemy.max_hp,
        "enemy_status": STATUS_STRING_TO_BYTE[battle_state.enemy.status],
        "enemy_bench_species": species_id_for(bench_lead.name),
        "enemy_bench_hp": bench_lead.hp,
        "enemy_bench_max_hp": bench_lead.max_hp,
    }


def _assert_overridable_active(mon: PokemonState, *, side: str) -> None:
    if mon.status not in OVERRIDABLE_STATUSES:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side}.status={mon.status!r} not in "
            f"{sorted(OVERRIDABLE_STATUSES)}; sleep/toxic need slice C-sleep / C-toxic"
        )
    if mon.item != ALLOWED_HELD_ITEM:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side}.item={mon.item}; "
            "slice B does not patch held-item WRAM fields"
        )
    stages = (
        mon.attack_stage,
        mon.defense_stage,
        mon.speed_stage,
        mon.sp_attack_stage,
        mon.sp_defense_stage,
    )
    if stages != ALLOWED_STAT_STAGES:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side}.stat_stages={stages}; "
            "slice B does not patch stat-stage WRAM fields"
        )
    if mon.substitute or mon.substitute_hp:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side} has Substitute active; slice B does not model it"
        )
    if mon.toxic_count:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side}.toxic_count={mon.toxic_count}; "
            "slice B does not model toxic counters"
        )
    if mon.sleep_turns:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side}.sleep_turns={mon.sleep_turns}; "
            "slice B does not model sleep counters"
        )


def _assert_overridable_enemy_bench(bench: tuple[PokemonState, ...]) -> None:
    if not bench:
        raise SimulationInputError(
            "rom_switch_scenario_export: enemy bench is empty; "
            "slice B still needs a living bench[0] target"
        )
    if bench[0].hp <= 0:
        raise SimulationInputError(
            "rom_switch_scenario_export: enemy bench[0] is fainted; "
            "slice B still needs a living bench[0] target"
        )


def _assert_fixture_active(mon: PokemonState, *, side: str) -> None:
    expected_name = FIXTURE_PLAYER_NAME if side == "player" else FIXTURE_ENEMY_NAME
    expected_types = FIXTURE_PLAYER_TYPES if side == "player" else FIXTURE_ENEMY_TYPES
    actual_name = mon.name.upper()
    if actual_name != expected_name:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side}.name={actual_name!r}; "
            f"fixture requires {expected_name!r} (slice A is fixture-match-or-reject)"
        )
    actual_types = tuple(t.upper() for t in mon.type_names)
    if actual_types != expected_types:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side}.types={actual_types}; "
            f"fixture requires {expected_types}"
        )
    if mon.status != ALLOWED_STATUS:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side}.status={mon.status!r}; "
            f"fixture has no primary status (wBattleMonStatus/wEnemyMonStatus = 0)"
        )
    if mon.item != ALLOWED_HELD_ITEM:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side}.item={mon.item}; "
            "fixture has wEnemyMonItem = NO_ITEM (slice A does not model held items)"
        )
    stages = (
        mon.attack_stage,
        mon.defense_stage,
        mon.speed_stage,
        mon.sp_attack_stage,
        mon.sp_defense_stage,
    )
    if stages != ALLOWED_STAT_STAGES:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side}.stat_stages={stages}; "
            "fixture does not model stat stages"
        )
    if mon.substitute or mon.substitute_hp:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side} has Substitute active; fixture does not model it"
        )
    if mon.toxic_count:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side}.toxic_count={mon.toxic_count}; "
            "fixture does not model toxic counters"
        )
    if mon.sleep_turns:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side}.sleep_turns={mon.sleep_turns}; "
            "fixture does not model sleep counters"
        )


def _assert_fixture_enemy_bench(bench: tuple[PokemonState, ...]) -> None:
    if not bench:
        raise SimulationInputError(
            "rom_switch_scenario_export: enemy bench is empty; "
            f"fixture requires bench[0] = {FIXTURE_ENEMY_BENCH_NAME!r} (wincon)"
        )
    bench_lead = bench[0]
    if bench_lead.name.upper() != FIXTURE_ENEMY_BENCH_NAME:
        raise SimulationInputError(
            f"rom_switch_scenario_export: enemy bench[0]={bench_lead.name!r}; "
            f"fixture requires {FIXTURE_ENEMY_BENCH_NAME!r}"
        )
    if bench_lead.hp <= 0:
        raise SimulationInputError(
            "rom_switch_scenario_export: enemy bench[0] is fainted; "
            "fixture requires a living wincon target"
        )


def _assert_no_field_state(state: BattleState) -> None:
    if state.weather != 0 or state.weather_count != 0:
        raise SimulationInputError(
            f"rom_switch_scenario_export: weather={state.weather} count={state.weather_count}; "
            "fixture does not model weather"
        )
    if state.player_safeguard or state.enemy_safeguard:
        raise SimulationInputError(
            "rom_switch_scenario_export: a Safeguard is active; fixture does not model it"
        )
    if state.player_spikes or state.enemy_spikes:
        raise SimulationInputError(
            f"rom_switch_scenario_export: spikes player={state.player_spikes} "
            f"enemy={state.enemy_spikes}; fixture does not model hazards"
        )


def _derive_hp_tags(player: PokemonState, enemy: PokemonState) -> set[str]:
    tags: set[str] = set()
    if enemy.hp <= DEFENSIVE_SACK_HP_THRESHOLD:
        tags.add("defensive_sack_owner")
    if player.hp <= ACTIVE_PRESSURE_HP_THRESHOLD:
        tags.add("active_pressure_converts")
    return tags
