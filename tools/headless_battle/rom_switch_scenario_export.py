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
    "toxic": 1 << 3,  # same primary status byte as poison; sub5 TOXIC bit distinguishes
}
# Sleep packs the sleep_turns counter (1..7) into the status byte directly,
# so it's handled by a dedicated branch in _status_byte_for and is not in
# STATUS_STRING_TO_BYTE.
OVERRIDABLE_STATUSES = frozenset({*STATUS_STRING_TO_BYTE, "sleep"})
SCREENS_SAFEGUARD_BIT = 2  # matches constants/battle_constants.asm SCREENS_SAFEGUARD
SCREENS_SPIKES_MASK = 0b11  # matches constants/battle_constants.asm SCREENS_SPIKES_MASK (bits 0-1)
SUBSTATUS_TOXIC_BIT = 0  # matches constants/battle_constants.asm SUBSTATUS_TOXIC (first const in sub5)
SUBSTATUS_SUBSTITUTE_BIT = 4  # matches constants/battle_constants.asm SUBSTATUS_SUBSTITUTE (sub4)
MAX_SPIKE_LAYERS = 3  # matches BattleCommand_Spikes guard: cp 3 / jr nc, .failed


def _status_byte_for(mon: PokemonState) -> int:
    if mon.status == "sleep":
        # ROM packs the sleep counter into bits 0-2 of the status byte
        # (SLP_MASK = %111). parse_state populates sleep_turns when
        # status=sleep, so we trust it's in range and mask defensively.
        return mon.sleep_turns & 0b111
    return STATUS_STRING_TO_BYTE[mon.status]


def _sub5_byte_for(mon: PokemonState) -> int:
    byte = 0
    if mon.status == "toxic" or mon.toxic_count > 0:
        byte |= 1 << SUBSTATUS_TOXIC_BIT
    return byte


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
    unrevealed_player_moves: bool = False,
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
    Set ``unrevealed_player_moves=True`` when the disputed state is before
    the active player's first attack; this clears both current and per-species
    revealed-move mirrors in the materializer.
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
        _assert_no_field_state(battle_state)
    else:
        _assert_overridable_active(battle_state.player, side="player")
        _assert_overridable_active(battle_state.enemy, side="enemy")
        _assert_overridable_enemy_bench(battle_state.enemy_bench)
        _assert_overridable_field_state(battle_state)
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
    if unrevealed_player_moves:
        overrides = scenario.setdefault("overrides", {})
        overrides["player_used_moves"] = [0, 0, 0, 0]
        overrides["species_used_moves"] = [0] * 24
    return scenario


def _board_to_overrides(battle_state: BattleState) -> dict[str, Any]:
    bench_lead = battle_state.enemy_bench[0]
    overrides: dict[str, Any] = {
        "player_species": species_id_for(battle_state.player.name),
        "player_type1": battle_state.player.types[0],
        "player_type2": battle_state.player.types[1],
        "player_hp": battle_state.player.hp,
        "player_max_hp": battle_state.player.max_hp,
        "player_status": _status_byte_for(battle_state.player),
        "player_item": battle_state.player.item,
        "enemy_species": species_id_for(battle_state.enemy.name),
        "enemy_type1": battle_state.enemy.types[0],
        "enemy_type2": battle_state.enemy.types[1],
        "enemy_hp": battle_state.enemy.hp,
        "enemy_max_hp": battle_state.enemy.max_hp,
        "enemy_status": _status_byte_for(battle_state.enemy),
        "enemy_item": battle_state.enemy.item,
        "enemy_bench_species": species_id_for(bench_lead.name),
        "enemy_bench_hp": bench_lead.hp,
        "enemy_bench_max_hp": bench_lead.max_hp,
    }
    if battle_state.weather or battle_state.weather_count:
        overrides["weather"] = battle_state.weather
        overrides["weather_count"] = battle_state.weather_count
    # Slice C-environment+spikes: screens byte combines spike-layer count
    # (bits 0-1, value 0..3) with the SAFEGUARD bit (bit 2). Emit when EITHER
    # side has spikes > 0 OR safeguard active so the base state's existing
    # screens byte is preserved when both are default.
    player_screens = _screens_byte(
        battle_state.player_spikes, battle_state.player_safeguard
    )
    if player_screens:
        overrides["player_screens"] = player_screens
    enemy_screens = _screens_byte(
        battle_state.enemy_spikes, battle_state.enemy_safeguard
    )
    if enemy_screens:
        overrides["enemy_screens"] = enemy_screens
    # sub5 toxic bit only emitted when needed; emitting 0 would unconditionally
    # patch wPlayerSubStatus5 / wEnemySubStatus5 which the base state may have
    # used for other sub-status bits this slice doesn't model.
    player_sub5 = _sub5_byte_for(battle_state.player)
    if player_sub5:
        overrides["player_sub5"] = player_sub5
    enemy_sub5 = _sub5_byte_for(battle_state.enemy)
    if enemy_sub5:
        overrides["enemy_sub5"] = enemy_sub5
    # Slice C-stages: emit per-side stat stages [atk, def, spd, sat, sdf] only
    # when any stage differs from +0 so default boards remain byte-stable
    # against the trace ROM.
    player_stages = _stat_stages_for(battle_state.player)
    if any(player_stages):
        overrides["player_stat_stages"] = list(player_stages)
    enemy_stages = _stat_stages_for(battle_state.enemy)
    if any(enemy_stages):
        overrides["enemy_stat_stages"] = list(enemy_stages)
    # Slice C-substitute: SUBSTATUS_SUBSTITUTE bit on sub4 + substitute_hp byte
    # emitted only when caller has an active Substitute. Defaults (no Substitute)
    # leave the base state's sub4 / substitute_hp bytes untouched.
    if battle_state.player.substitute:
        overrides["player_sub4"] = 1 << SUBSTATUS_SUBSTITUTE_BIT
    if battle_state.enemy.substitute:
        overrides["enemy_sub4"] = 1 << SUBSTATUS_SUBSTITUTE_BIT
    if battle_state.player.substitute_hp:
        overrides["player_substitute_hp"] = battle_state.player.substitute_hp
    if battle_state.enemy.substitute_hp:
        overrides["enemy_substitute_hp"] = battle_state.enemy.substitute_hp
    return overrides


def _stat_stages_for(mon: PokemonState) -> tuple[int, int, int, int, int]:
    return (
        mon.attack_stage,
        mon.defense_stage,
        mon.speed_stage,
        mon.sp_attack_stage,
        mon.sp_defense_stage,
    )


def _screens_byte(spike_layers: int, safeguard: bool) -> int:
    # Spike layers occupy bits 0-1 (value 0..3) per move_effects/spikes.asm
    # and constants/battle_constants.asm SCREENS_SPIKES_MASK. SAFEGUARD is
    # bit 2 per SCREENS_SAFEGUARD. Headless simulator already clamps spike
    # layers to MAX_SPIKE_LAYERS in parse_spikes_layers, so we mask defensively.
    return (spike_layers & SCREENS_SPIKES_MASK) | (
        (1 << SCREENS_SAFEGUARD_BIT) if safeguard else 0
    )


def _assert_overridable_active(mon: PokemonState, *, side: str) -> None:
    if mon.status not in OVERRIDABLE_STATUSES:
        raise SimulationInputError(
            f"rom_switch_scenario_export: {side}.status={mon.status!r} not in "
            f"{sorted(OVERRIDABLE_STATUSES)}; sleep/toxic need slice C-sleep / C-toxic"
        )
    # mon.item is now patched in slice C-environment via overrides.player_item /
    # overrides.enemy_item, so non-zero held items are allowed in override mode.
    # Stat stages are now patched in slice C-stages via overrides.player_stat_stages /
    # overrides.enemy_stat_stages, so non-zero stages are allowed here.
    # Substitute is now patched in slice C-substitute via overrides.player_sub4 /
    # overrides.enemy_sub4 (SUBSTATUS_SUBSTITUTE bit) plus overrides.player_substitute_hp /
    # overrides.enemy_substitute_hp, so an active Substitute is allowed.
    # toxic_count and sleep_turns are now patched in slice C-toxic-sleep via
    # the sub5 / status byte overrides, so they're allowed.


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


def _assert_overridable_field_state(state: BattleState) -> None:
    # Slice C-environment patches weather (wBattleWeather + wWeatherCount) and
    # screens (wPlayerScreens / wEnemyScreens SAFEGUARD bit) via overrides.
    # Slice C-spikes packs spike layers (0..3) into bits 0-1 of the same screens
    # byte, so non-zero spike layers are now allowed and emit the combined
    # screens byte through _board_to_overrides. parse_spikes_layers already
    # clamps to MAX_SPIKE_LAYERS upstream.
    if state.player_spikes > MAX_SPIKE_LAYERS or state.enemy_spikes > MAX_SPIKE_LAYERS:
        # Defensive: parse_spikes_layers should catch this earlier, but the
        # exporter can be called with a raw BattleState dict that bypasses
        # parse_state's validation.
        raise SimulationInputError(
            f"rom_switch_scenario_export: spike layers exceed {MAX_SPIKE_LAYERS} "
            f"(player={state.player_spikes}, enemy={state.enemy_spikes})"
        )


def _derive_hp_tags(player: PokemonState, enemy: PokemonState) -> set[str]:
    tags: set[str] = set()
    if enemy.hp <= DEFENSIVE_SACK_HP_THRESHOLD:
        tags.add("defensive_sack_owner")
    if player.hp <= ACTIVE_PRESSURE_HP_THRESHOLD:
        tags.add("active_pressure_converts")
    return tags
