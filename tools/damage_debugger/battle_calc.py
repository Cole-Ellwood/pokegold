"""All-move damage reports backed by the ROM damage oracle."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from . import matchup
from . import oracle
from . import state
from . import tables


class BattleCalcError(tables.InputError):
    """User-facing battle calculator error."""


@dataclass(frozen=True)
class MoveDamageResult:
    slot: int
    move_id: int
    move_name: str
    move_constant: str
    type_name: str
    category: str
    damage_low: int
    damage_high: int
    pct_current_low: int
    pct_current_high: int
    accuracy: int
    effect: str
    effect_chance: int
    notes: tuple[str, ...]
    battle_inputs: oracle.BattleInputs | None
    trace: list[tuple[str, int]]


@dataclass(frozen=True)
class BattleCalcReport:
    attacker: state.ExactPokemonState
    defender: state.ExactPokemonState
    context: state.BattleContext
    moves: tuple[MoveDamageResult, ...]


def move_row_for_id(move_id: int) -> tuple[str, tables.MoveRow] | None:
    if move_id == 0:
        return None
    move_name = state.move_name_by_id().get(move_id)
    if not move_name:
        return None
    move = tables.load_moves().get(move_name)
    if move is None:
        return None
    return move_name, move


PSEUDO_TYPE_CONSTANTS = {
    "PHYSICAL",
    "SPECIAL",
    "UNUSED_TYPES",
    "UNUSED_TYPES_END",
    "TYPES_END",
    "NUM_TYPES",
}


def type_name_for_id(type_id: int) -> str:
    types = tables.load_type_constants()
    for name, value in types.items():
        if (
            name not in PSEUDO_TYPE_CONSTANTS
            and value == type_id
            and value in tables.ALL_DAMAGE_TYPE_VALUES
        ):
            return name
    raise BattleCalcError(f"unknown damage type id {type_id}")


def regular_hidden_power_type_id(attacker: state.ExactPokemonState) -> int:
    types = tables.load_type_constants()
    atk_dv, def_dv, _speed_dv, _special_dv = attacker.dvs
    type_id = ((atk_dv & 0x3) << 2) | (def_dv & 0x3)
    type_id += 1
    if type_id >= types["BIRD"]:
        type_id += 1
    if type_id >= types["UNUSED_TYPES"]:
        type_id += types["UNUSED_TYPES_END"] - types["UNUSED_TYPES"]
    return type_id


def unown_hidden_power_type_ids(defender: state.ExactPokemonState) -> tuple[int, ...]:
    types = tables.load_type_constants()
    candidates: list[int] = []
    for type_name in (
        "FIGHTING",
        "FLYING",
        "POISON",
        "GROUND",
        "ROCK",
        "BUG",
        "GHOST",
        "STEEL",
        "FIRE",
        "WATER",
        "GRASS",
        "ELECTRIC",
        "PSYCHIC_TYPE",
        "ICE",
        "DRAGON",
        "DARK",
    ):
        type_id = types[type_name]
        multiplier = oracle.matchup(type_id, defender.type1)
        if defender.type2 != defender.type1:
            multiplier = multiplier * oracle.matchup(type_id, defender.type2) // 10
        if multiplier >= oracle.SUPER_EFFECTIVE:
            candidates.append(type_id)
    return tuple(candidates) or (types["PSYCHIC_TYPE"],)


def move_type_ids_for_state(
    attacker: state.ExactPokemonState,
    defender: state.ExactPokemonState,
    move: tables.MoveRow,
) -> tuple[int, ...]:
    if move.effect != "EFFECT_HIDDEN_POWER":
        return (tables.load_type_constants()[move.type_name],)
    if attacker.species == "UNOWN":
        return unown_hidden_power_type_ids(defender)
    return (regular_hidden_power_type_id(attacker),)


def base_power_for_state(attacker: state.ExactPokemonState, move: tables.MoveRow) -> int:
    if move.effect == "EFFECT_HIDDEN_POWER" and attacker.species == "UNOWN":
        return 100
    return move.bp


def is_physical_for_state(
    attacker: state.ExactPokemonState,
    move: tables.MoveRow,
    *,
    move_type: int | None = None,
) -> bool:
    types = tables.load_type_constants()
    move_type_id = types[move.type_name] if move_type is None else move_type
    if move.name == "OUTRAGE" and move_type_id in (attacker.type1, attacker.type2):
        return attacker.atk > attacker.sp_atk
    return tables.is_physical_type(move_type_id)


def battle_inputs_for_move(
    attacker: state.ExactPokemonState,
    defender: state.ExactPokemonState,
    move: tables.MoveRow,
    context: state.BattleContext,
    *,
    move_bp: int | None = None,
    move_type: int | None = None,
) -> oracle.BattleInputs:
    types = tables.load_type_constants()
    effects = tables.load_move_effect_constants()
    move_type_id = types[move.type_name] if move_type is None else move_type
    is_physical = is_physical_for_state(attacker, move, move_type=move_type_id)
    can_evolve = tables.load_can_evolve()
    return oracle.BattleInputs(
        attacker_level=attacker.level,
        move_bp=move.bp if move_bp is None else move_bp,
        move_type=move_type_id,
        is_physical=is_physical,
        attacker_atk=attacker.atk if is_physical else attacker.sp_atk,
        defender_def=defender.defense if is_physical else defender.sp_def,
        attacker_types=(attacker.type1, attacker.type2),
        defender_types=(defender.type1, defender.type2),
        user_item=attacker.item_id,
        opponent_item=defender.item_id,
        can_evolve_attacker=can_evolve.get(attacker.species, False),
        can_evolve_defender=can_evolve.get(defender.species, False),
        is_critical=context.is_critical,
        is_selfdestruct=move.effect == "EFFECT_SELFDESTRUCT",
        attacker_below_third_hp=attacker.current_hp * 3 <= attacker.max_hp,
        opponent_has_status=defender.status != 0,
        opponent_above_half_hp=defender.current_hp * 2 > defender.max_hp,
        weather=context.weather,
        move_effect=effects[move.effect],
        johto_badges=context.johto_badges,
        kanto_badges=context.kanto_badges,
        link_mode=context.link_mode,
        battle_turn=context.battle_turn,
        initial_cur_damage=context.initial_cur_damage,
        metronome_count=context.metronome_count,
    )


def category_for(
    attacker: state.ExactPokemonState,
    move: tables.MoveRow,
    *,
    move_type: int | None = None,
) -> str:
    if move.bp == 0:
        return "Status"
    return "Physical" if is_physical_for_state(attacker, move, move_type=move_type) else "Special"


def notes_for(
    attacker: state.ExactPokemonState,
    defender: state.ExactPokemonState,
    move: tables.MoveRow,
    *,
    move_type: int | None = None,
) -> tuple[str, ...]:
    notes: list[str] = []
    types = tables.load_type_constants()
    move_type_id = types[move.type_name] if move_type is None else move_type
    if move.bp == 0:
        notes.append(f"{move.accuracy}% accuracy")
        return tuple(notes)
    if move_type_id in (attacker.type1, attacker.type2):
        notes.append("STAB")
    multiplier = oracle.matchup(move_type_id, defender.type1)
    if defender.type2 != defender.type1:
        multiplier = multiplier * oracle.matchup(move_type_id, defender.type2) // 10
    if multiplier == 0:
        notes.append("immune")
    elif multiplier < 10:
        notes.append("resisted")
    elif multiplier > 10:
        notes.append("super effective")
    if move.effect_chance:
        notes.append(f"{move.effect_chance}% effect")
    return tuple(notes)


def fixed_damage_range_for_move(
    attacker: state.ExactPokemonState,
    defender: state.ExactPokemonState,
    move: tables.MoveRow,
    *,
    move_type: int | None = None,
) -> tuple[int, int, tuple[str, ...]] | None:
    if hits_type_immunity(defender, move, move_type=move_type):
        return 0, 0, ("immune",)
    if move.effect == "EFFECT_LEVEL_DAMAGE":
        return attacker.level, attacker.level, ("fixed damage: user level",)
    if move.effect == "EFFECT_STATIC_DAMAGE":
        return move.bp, move.bp, ("fixed damage",)
    if move.effect == "EFFECT_PSYWAVE":
        high = max(1, attacker.level + attacker.level // 2 - 1)
        return 1, high, ("variable fixed damage",)
    if move.effect == "EFFECT_SUPER_FANG":
        damage = max(1, defender.current_hp // 2)
        return damage, damage, ("fixed damage: half current HP",)
    return None


def ohko_damage_range_for_move(
    defender: state.ExactPokemonState,
    move: tables.MoveRow,
    *,
    move_type: int | None = None,
) -> tuple[int, int, tuple[str, ...]] | None:
    if move.effect != "EFFECT_OHKO":
        return None
    if hits_type_immunity(defender, move, move_type=move_type):
        return 0, 0, ("misses through type immunity",)
    return defender.current_hp, defender.current_hp, ("conditional OHKO; accuracy/level-gated",)


def hits_type_immunity(
    defender: state.ExactPokemonState,
    move: tables.MoveRow,
    *,
    move_type: int | None = None,
) -> bool:
    move_type_id = tables.load_type_constants()[move.type_name] if move_type is None else move_type
    if oracle.matchup(move_type_id, defender.type1) == 0:
        return True
    return defender.type2 != defender.type1 and oracle.matchup(move_type_id, defender.type2) == 0


def effect_specific_damage_range(
    attacker: state.ExactPokemonState,
    defender: state.ExactPokemonState,
    move: tables.MoveRow,
    context: state.BattleContext,
    *,
    move_type: int | None = None,
) -> tuple[int, int, tuple[str, ...], oracle.BattleInputs | None] | None:
    if move.effect in {"EFFECT_COUNTER", "EFFECT_MIRROR_COAT"}:
        if hits_type_immunity(defender, move, move_type=move_type):
            return 0, 0, ("immune",), None
        return 0, 0, ("requires previous opponent damage; not modeled",), None
    multi_hit = multi_hit_damage_range(attacker, defender, move, context, move_type=move_type)
    if multi_hit is not None:
        return multi_hit
    powers = effect_specific_powers(attacker, move)
    if powers is None:
        return None
    ranges: list[tuple[int, int]] = []
    first_inputs: oracle.BattleInputs | None = None
    for power in powers:
        if power == 0:
            ranges.append((0, 0))
            continue
        inputs = battle_inputs_for_move(
            attacker,
            defender,
            move,
            context,
            move_bp=power,
            move_type=move_type,
        )
        if first_inputs is None:
            first_inputs = inputs
        ranges.append(tables.damage_range(oracle.predict_damage(inputs)))
    notes = effect_specific_notes(move, powers)
    return min(low for low, _ in ranges), max(high for _, high in ranges), notes, first_inputs


def multi_hit_damage_range(
    attacker: state.ExactPokemonState,
    defender: state.ExactPokemonState,
    move: tables.MoveRow,
    context: state.BattleContext,
    *,
    move_type: int | None = None,
) -> tuple[int, int, tuple[str, ...], oracle.BattleInputs] | None:
    hit_range: tuple[int, int] | None = None
    note: str | None = None
    if move.effect == "EFFECT_MULTI_HIT":
        hit_range = (2, 5)
        note = "2-5 hits"
    elif move.effect in {"EFFECT_DOUBLE_HIT", "EFFECT_POISON_MULTI_HIT"}:
        hit_range = (2, 2)
        note = "2 hits"
    elif move.effect == "EFFECT_TRIPLE_KICK":
        hit_range = (1, 6)
        note = "1-3 kicks; successive kicks deal 1x/2x/3x base damage"
    if hit_range is None or note is None:
        return None
    inputs = battle_inputs_for_move(attacker, defender, move, context, move_type=move_type)
    per_hit_low, per_hit_high = tables.damage_range(oracle.predict_damage(inputs))
    low = per_hit_low * hit_range[0]
    high = per_hit_high * hit_range[1]
    return low, high, (f"{note}; per-hit range {per_hit_low}-{per_hit_high}",), inputs


def effect_specific_powers(
    attacker: state.ExactPokemonState,
    move: tables.MoveRow,
) -> tuple[int, ...] | None:
    if move.effect == "EFFECT_RETURN":
        return (max(1, attacker.happiness * 10 // 25),)
    if move.effect == "EFFECT_FRUSTRATION":
        return (max(1, (255 - attacker.happiness) * 10 // 25),)
    if move.effect == "EFFECT_REVERSAL":
        return (flail_reversal_power(attacker.current_hp, attacker.max_hp),)
    if move.effect == "EFFECT_MAGNITUDE":
        return (10, 30, 50, 70, 90, 110, 150)
    if move.effect == "EFFECT_PRESENT":
        return (0, 40, 80, 120)
    return None


def flail_reversal_power(current_hp: int, max_hp: int) -> int:
    if max_hp <= 0:
        return 20
    hp_bar_pixels = current_hp * 48 // max_hp
    for threshold, power in ((1, 200), (4, 150), (9, 100), (16, 80), (32, 40), (48, 20)):
        if threshold >= hp_bar_pixels:
            return power
    return 20


def effect_specific_notes(move: tables.MoveRow, powers: tuple[int, ...]) -> tuple[str, ...]:
    if move.effect == "EFFECT_RETURN":
        return (f"Return power {powers[0]}",)
    if move.effect == "EFFECT_FRUSTRATION":
        return (f"Frustration power {powers[0]}",)
    if move.effect == "EFFECT_REVERSAL":
        return (f"HP-scaled power {powers[0]}",)
    if move.effect == "EFFECT_MAGNITUDE":
        return ("variable power: 10-150",)
    if move.effect == "EFFECT_PRESENT":
        return ("variable power: 40-120; 20% 0-damage heal chance",)
    return ()


def calculate_move(
    attacker: state.ExactPokemonState,
    defender: state.ExactPokemonState,
    context: state.BattleContext,
    *,
    slot: int,
    move_id: int,
    include_trace: bool = False,
) -> MoveDamageResult:
    row = move_row_for_id(move_id)
    if row is None:
        return MoveDamageResult(
            slot=slot,
            move_id=move_id,
            move_name="No Move" if move_id == 0 else f"Move {move_id}",
            move_constant="NO_MOVE" if move_id == 0 else f"MOVE_{move_id:02X}",
            type_name="None",
            category="None",
            damage_low=0,
            damage_high=0,
            pct_current_low=0,
            pct_current_high=0,
            accuracy=0,
            effect="",
            effect_chance=0,
            notes=(),
            battle_inputs=None,
            trace=[],
        )
    move_constant, move = row
    display_name = tables.display_move(move)
    move_type_ids = move_type_ids_for_state(attacker, defender, move)
    variable_hidden_power = move.effect == "EFFECT_HIDDEN_POWER" and len(move_type_ids) > 1
    move_type_id = move_type_ids[0]
    move_type_name = type_name_for_id(move_type_id) if not variable_hidden_power else "VARIABLE"
    move_bp = base_power_for_state(attacker, move)
    ohko_damage = ohko_damage_range_for_move(defender, move, move_type=move_type_id)
    if ohko_damage is not None:
        damage_low, damage_high, ohko_notes = ohko_damage
        return MoveDamageResult(
            slot=slot,
            move_id=move_id,
            move_name=display_name,
            move_constant=move_constant,
            type_name=move_type_name,
            category="Conditional",
            damage_low=damage_low,
            damage_high=damage_high,
            pct_current_low=tables.pct(damage_low, defender.current_hp),
            pct_current_high=tables.pct(damage_high, defender.current_hp),
            accuracy=move.accuracy,
            effect=move.effect,
            effect_chance=move.effect_chance,
            notes=notes_for(attacker, defender, move, move_type=move_type_id) + ohko_notes,
            battle_inputs=None,
            trace=[],
        )
    if move.bp == 0:
        return MoveDamageResult(
            slot=slot,
            move_id=move_id,
            move_name=display_name,
            move_constant=move_constant,
            type_name=move_type_name,
            category="Status",
            damage_low=0,
            damage_high=0,
            pct_current_low=0,
            pct_current_high=0,
            accuracy=move.accuracy,
            effect=move.effect,
            effect_chance=move.effect_chance,
            notes=notes_for(attacker, defender, move, move_type=move_type_id),
            battle_inputs=None,
            trace=[],
        )
    if variable_hidden_power:
        ranges: list[tuple[int, int]] = []
        first_inputs: oracle.BattleInputs | None = None
        for option_type in move_type_ids:
            inputs = battle_inputs_for_move(
                attacker,
                defender,
                move,
                context,
                move_bp=move_bp,
                move_type=option_type,
            )
            if first_inputs is None:
                first_inputs = inputs
            ranges.append(tables.damage_range(oracle.predict_damage(inputs)))
        damage_low = min(low for low, _ in ranges)
        damage_high = max(high for _, high in ranges)
        return MoveDamageResult(
            slot=slot,
            move_id=move_id,
            move_name=display_name,
            move_constant=move_constant,
            type_name=move_type_name,
            category="Variable",
            damage_low=damage_low,
            damage_high=damage_high,
            pct_current_low=tables.pct(damage_low, defender.current_hp),
            pct_current_high=tables.pct(damage_high, defender.current_hp),
            accuracy=move.accuracy,
            effect=move.effect,
            effect_chance=move.effect_chance,
            notes=("Unown Hidden Power: random super-effective type",),
            battle_inputs=first_inputs,
            trace=[],
        )
    fixed_damage = fixed_damage_range_for_move(attacker, defender, move, move_type=move_type_id)
    if fixed_damage is not None:
        damage_low, damage_high, fixed_notes = fixed_damage
        return MoveDamageResult(
            slot=slot,
            move_id=move_id,
            move_name=display_name,
            move_constant=move_constant,
            type_name=move_type_name,
            category="Fixed",
            damage_low=damage_low,
            damage_high=damage_high,
            pct_current_low=tables.pct(damage_low, defender.current_hp),
            pct_current_high=tables.pct(damage_high, defender.current_hp),
            accuracy=move.accuracy,
            effect=move.effect,
            effect_chance=move.effect_chance,
            notes=fixed_notes,
            battle_inputs=None,
            trace=[],
        )
    effect_damage = effect_specific_damage_range(
        attacker,
        defender,
        move,
        context,
        move_type=move_type_id,
    )
    if effect_damage is not None:
        damage_low, damage_high, effect_notes, inputs = effect_damage
        return MoveDamageResult(
            slot=slot,
            move_id=move_id,
            move_name=display_name,
            move_constant=move_constant,
            type_name=move_type_name,
            category=category_for(attacker, move, move_type=move_type_id) if inputs is not None else "Conditional",
            damage_low=damage_low,
            damage_high=damage_high,
            pct_current_low=tables.pct(damage_low, defender.current_hp),
            pct_current_high=tables.pct(damage_high, defender.current_hp),
            accuracy=move.accuracy,
            effect=move.effect,
            effect_chance=move.effect_chance,
            notes=notes_for(attacker, defender, move, move_type=move_type_id) + effect_notes,
            battle_inputs=inputs,
            trace=[],
        )
    inputs = battle_inputs_for_move(
        attacker,
        defender,
        move,
        context,
        move_bp=move_bp,
        move_type=move_type_id,
    )
    damage_low, damage_high = tables.damage_range(oracle.predict_damage(inputs))
    trace = oracle.predict_damage_trace(inputs) if include_trace else []
    return MoveDamageResult(
        slot=slot,
        move_id=move_id,
        move_name=display_name,
        move_constant=move_constant,
        type_name=move_type_name,
        category=category_for(attacker, move, move_type=move_type_id),
        damage_low=damage_low,
        damage_high=damage_high,
        pct_current_low=tables.pct(damage_low, defender.current_hp),
        pct_current_high=tables.pct(damage_high, defender.current_hp),
        accuracy=move.accuracy,
        effect=move.effect,
        effect_chance=move.effect_chance,
        notes=notes_for(attacker, defender, move, move_type=move_type_id),
        battle_inputs=inputs,
        trace=trace,
    )


def calculate_all_moves(
    attacker: state.ExactPokemonState,
    defender: state.ExactPokemonState,
    context: state.BattleContext | None = None,
    *,
    include_trace: bool = False,
) -> BattleCalcReport:
    resolved_context = state.BattleContext() if context is None else context
    rows = tuple(
        calculate_move(
            attacker,
            defender,
            resolved_context,
            slot=index + 1,
            move_id=move_id,
            include_trace=include_trace,
        )
        for index, move_id in enumerate(attacker.moves)
    )
    return BattleCalcReport(
        attacker=attacker,
        defender=defender,
        context=resolved_context,
        moves=rows,
    )


def format_report(report: BattleCalcReport) -> str:
    attacker_item = f" ({report.attacker.item_name})" if report.attacker.item_id else ""
    header = (
        f"{tables.display_species(report.attacker.species)} L{report.attacker.level}"
        f"{attacker_item} into {tables.display_species(report.defender.species)} "
        f"L{report.defender.level} ({report.defender.current_hp}/{report.defender.max_hp} HP)"
    )
    lines = [
        header,
        "",
        f"{'Move':<11} {'Type':<9} {'Cat':<8} {'Damage':<8} {'Current HP':<10} Notes",
    ]
    for row in report.moves:
        if row.move_id == 0:
            continue
        damage = "0" if row.damage_high == 0 else f"{row.damage_low}-{row.damage_high}"
        pct = "0%" if row.damage_high == 0 else f"{row.pct_current_low}-{row.pct_current_high}%"
        notes = ", ".join(row.notes)
        type_name = row.type_name.replace("_TYPE", "").replace("_", " ").title()
        lines.append(
            f"{row.move_name:<11} {type_name:<9} {row.category:<8} {damage:<8} {pct:<10} {notes}"
        )
        if row.trace:
            lines.extend(f"  trace {step}: {damage_value}" for step, damage_value in row.trace)
    return "\n".join(lines)


def report_to_json(report: BattleCalcReport) -> str:
    rows = []
    for row in report.moves:
        item = asdict(row)
        item["battle_inputs"] = (
            asdict(row.battle_inputs) if row.battle_inputs is not None else None
        )
        rows.append(item)
    return json.dumps(
        {
            "attacker": state.state_to_json(report.attacker),
            "defender": state.state_to_json(report.defender),
            "context": state.context_to_json(report.context),
            "moves": rows,
        },
        indent=2,
        sort_keys=True,
    )


def run_source_single_move(args: argparse.Namespace) -> int:
    argv = [args.attacker, args.defender, args.move]
    if args.json:
        argv.append("--json")
    if args.trace:
        argv.append("--trace")
    return matchup.main(argv)


def run_trainer_vs_save(args: argparse.Namespace) -> BattleCalcReport:
    if not args.all_moves:
        raise BattleCalcError("--all-moves is required for trainer-vs-save battle_calc")
    attacker = state.trainer_state(args.attacker_trainer)
    defender = state.party_state_from_save(args.defender_save, args.defender_slot)
    return calculate_all_moves(attacker, defender, include_trace=args.trace)


def run_self_test() -> int:
    class FakeMemory(dict):
        def __getitem__(self, key):
            return dict.get(self, key, 0)

    class FakePyBoy:
        def __init__(self, values):
            self.memory = FakeMemory(values)

    class PostContinuePyBoy:
        def __init__(self, ready_after_ticks: int | None):
            self.memory = FakeMemory({})
            self.buttons: list[str] = []
            self.ticks = 0
            self.ready_after_ticks = ready_after_ticks

        def button(self, button_name, delay=0):
            self.buttons.append(button_name)

        def tick(self, frames, *_args):
            self.ticks += frames
            if self.ready_after_ticks is not None and self.ticks >= self.ready_after_ticks:
                self.memory[(1, 0xD000)] = 1
                self.memory[(1, 0xD001)] = 2
                self.memory[(1, 0xD002)] = 3
                self.memory[(1, 0xD003)] = state.MAPSTATUS_HANDLE

    post_continue_symbols = {
        "wPartyCount": state.trace_runtime.Symbol(1, 0xD000),
        "wMapGroup": state.trace_runtime.Symbol(1, 0xD001),
        "wMapNumber": state.trace_runtime.Symbol(1, 0xD002),
        "wMapStatus": state.trace_runtime.Symbol(1, 0xD003),
    }
    late_continue = PostContinuePyBoy(2700)
    state.boot_continue(late_continue, post_continue_symbols, max_clock_attempts=2)
    if late_continue.buttons != ["start", "a", "a", "a", "a"]:
        raise AssertionError(f"expected boot_continue to wait for loaded WRAM, got {late_continue.buttons}")
    try:
        state.boot_continue(PostContinuePyBoy(None), post_continue_symbols, max_clock_attempts=1)
    except state.StateInputError as exc:
        if "Continue did not reach" not in str(exc):
            raise AssertionError(f"expected post-Continue load failure, got {exc}") from exc
    else:
        raise AssertionError("expected unloaded Continue path to fail before saving a cache")

    try:
        state.read_party_slot_from_wram(
            FakePyBoy({(1, 0xD000): 1}),
            {
                "wPartyCount": state.trace_runtime.Symbol(1, 0xD000),
                "wPartyMons": state.trace_runtime.Symbol(1, 0xD010),
            },
            2,
        )
    except state.StateInputError as exc:
        if "out of range" not in str(exc):
            raise AssertionError(f"expected party slot range error, got {exc}") from exc
    else:
        raise AssertionError("expected out-of-range party slot to be rejected")

    attacker = state.trainer_state("FALKNER1:NOCTOWL")
    surge = state.trainer_state("LT_SURGE1:RAICHU")
    if surge.move_names != ("Agility", "Thunderbolt", "Cross Chop", "Razor Leaf"):
        raise AssertionError(f"expected Lt. Surge party row to resolve, got {surge.move_names}")
    cal = state.trainer_state("CAL2:BAYLEEF")
    if cal.species != "BAYLEEF":
        raise AssertionError(f"expected PKMNTrainerGroup resolver to find CAL2, got {cal.species}")
    kenji = state.trainer_state("KENJI1:2")
    if kenji.species != "HITMONLEE":
        raise AssertionError(f"expected BlackbeltGroup resolver to find KENJI1, got {kenji.species}")
    joey = state.trainer_state("JOEY1:RATTATA")
    if joey.move_names != ("Tackle", "Tail Whip", "No Move", "No Move"):
        raise AssertionError(f"expected level-up moves for normal trainer row, got {joey.move_names}")
    defender = state.state_from_exact_values(
        species="DROWZEE",
        level=13,
        item="NO_ITEM",
        moves=("TACKLE", "HYPNOSIS", "DISABLE", "NO_MOVE"),
        current_hp=50,
        max_hp=50,
        atk=18,
        defense=26,
        speed=16,
        sp_atk=18,
        sp_def=30,
    )
    report = calculate_all_moves(attacker, defender)
    actual = [(row.move_constant, row.damage_low, row.damage_high) for row in report.moves]
    expected = [
        ("TACKLE", 3, 4),
        ("PECK", 8, 10),
        ("CONFUSION", 4, 5),
        ("HYPNOSIS", 0, 0),
    ]
    if actual != expected:
        raise AssertionError(f"expected {expected}, got {actual}")
    rival_return = [
        row
        for row in calculate_all_moves(
            state.trainer_state("RIVAL2_1_CHIKORITA:CROBAT"),
            defender,
        ).moves
        if row.move_constant == "RETURN"
    ][0]
    if (rival_return.damage_low, rival_return.damage_high, rival_return.notes[-1]) != (
        25,
        30,
        "Return power 28",
    ):
        raise AssertionError(f"expected trainer Return power damage, got {rival_return}")
    erika_hidden_power = [
        row
        for row in calculate_all_moves(
            state.trainer_state("ERIKA1:BELLOSSOM"),
            defender,
        ).moves
        if row.move_constant == "HIDDEN_POWER"
    ][0]
    if (
        erika_hidden_power.type_name,
        erika_hidden_power.category,
        erika_hidden_power.battle_inputs.move_type if erika_hidden_power.battle_inputs else None,
    ) != ("FIRE", "Special", tables.load_type_constants()["FIRE"]):
        raise AssertionError(f"expected Erika Hidden Power Fire, got {erika_hidden_power}")
    present_attacker = state.state_from_exact_values(
        species="DELIBIRD",
        level=22,
        item="NO_ITEM",
        moves=("PRESENT", "NO_MOVE", "NO_MOVE", "NO_MOVE"),
        current_hp=50,
        max_hp=50,
        atk=45,
        defense=35,
        speed=55,
        sp_atk=25,
        sp_def=35,
    )
    present_result = calculate_all_moves(present_attacker, defender).moves[0]
    if present_result.damage_low != 0 or "0-damage heal" not in present_result.notes[-1]:
        raise AssertionError(f"expected Present heal branch in range, got {present_result}")
    magnitude = calculate_all_moves(state.trainer_state("TIMOTHY:DIGLETT"), defender).moves[0]
    if (magnitude.move_constant, magnitude.damage_low, magnitude.damage_high) != (
        "MAGNITUDE",
        7,
        102,
    ):
        raise AssertionError(f"expected Magnitude variable-power range, got {magnitude}")
    mirror_coat = calculate_all_moves(state.trainer_state("RED1:BLASTOISE"), defender).moves[3]
    if (
        mirror_coat.category != "Conditional"
        or "requires previous opponent damage" not in mirror_coat.notes[-1]
    ):
        raise AssertionError(f"expected Mirror Coat to be marked conditional, got {mirror_coat}")
    ohko = [
        row
        for row in calculate_all_moves(state.trainer_state("GAVEN1:KINGLER"), defender).moves
        if row.move_constant == "GUILLOTINE"
    ][0]
    if (
        ohko.category,
        ohko.damage_low,
        ohko.damage_high,
        ohko.battle_inputs,
        ohko.notes[-1],
    ) != (
        "Conditional",
        defender.current_hp,
        defender.current_hp,
        None,
        "conditional OHKO; accuracy/level-gated",
    ):
        raise AssertionError(f"expected Guillotine to be marked conditional OHKO, got {ohko}")
    fury_attack = [
        row
        for row in calculate_all_moves(state.trainer_state("FALKNER1:SPEAROW"), defender).moves
        if row.move_constant == "FURY_ATTACK"
    ][0]
    if (fury_attack.damage_low, fury_attack.damage_high, fury_attack.notes[-1]) != (
        4,
        15,
        "2-5 hits; per-hit range 2-3",
    ):
        raise AssertionError(f"expected Fury Attack to report 2-5 hit total damage, got {fury_attack}")
    double_kick = calculate_all_moves(state.trainer_state("YOSHI:HITMONLEE"), defender).moves[0]
    if (double_kick.move_constant, double_kick.damage_low, double_kick.damage_high) != (
        "DOUBLE_KICK",
        34,
        42,
    ):
        raise AssertionError(f"expected Double Kick to report 2-hit damage, got {double_kick}")
    twineedle_attacker = state.state_from_exact_values(
        species="BEEDRILL",
        level=20,
        item="NO_ITEM",
        moves=("TWINEEDLE", "NO_MOVE", "NO_MOVE", "NO_MOVE"),
        current_hp=60,
        max_hp=60,
        atk=50,
        defense=30,
        speed=45,
        sp_atk=25,
        sp_def=30,
    )
    twineedle = calculate_all_moves(twineedle_attacker, defender).moves[0]
    if (twineedle.move_constant, twineedle.damage_low, twineedle.damage_high) != (
        "TWINEEDLE",
        94,
        112,
    ):
        raise AssertionError(f"expected Twineedle to report 2-hit damage, got {twineedle}")
    triple_kick_attacker = state.state_from_exact_values(
        species="HITMONTOP",
        level=39,
        item="NO_ITEM",
        moves=("TRIPLE_KICK", "NO_MOVE", "NO_MOVE", "NO_MOVE"),
        current_hp=80,
        max_hp=80,
        atk=70,
        defense=60,
        speed=65,
        sp_atk=35,
        sp_def=80,
    )
    triple_kick = calculate_all_moves(triple_kick_attacker, defender).moves[0]
    if (
        triple_kick.move_constant,
        triple_kick.damage_low,
        triple_kick.damage_high,
        triple_kick.notes[-1],
    ) != (
        "TRIPLE_KICK",
        6,
        48,
        "1-3 kicks; successive kicks deal 1x/2x/3x base damage; per-hit range 6-8",
    ):
        raise AssertionError(f"expected Triple Kick to report variable total damage, got {triple_kick}")
    fixed_attacker = state.state_from_exact_values(
        species="HAUNTER",
        level=22,
        item="NO_ITEM",
        moves=("NIGHT_SHADE", "SONICBOOM", "DRAGON_RAGE", "PSYWAVE"),
        current_hp=50,
        max_hp=50,
        atk=30,
        defense=25,
        speed=45,
        sp_atk=55,
        sp_def=55,
    )
    fixed_report = calculate_all_moves(fixed_attacker, defender)
    fixed_actual = [
        (row.move_constant, row.category, row.damage_low, row.damage_high)
        for row in fixed_report.moves
    ]
    fixed_expected = [
        ("NIGHT_SHADE", "Fixed", 22, 22),
        ("SONICBOOM", "Fixed", 20, 20),
        ("DRAGON_RAGE", "Fixed", 40, 40),
        ("PSYWAVE", "Fixed", 1, 32),
    ]
    if fixed_actual != fixed_expected:
        raise AssertionError(f"expected {fixed_expected}, got {fixed_actual}")
    normal_defender = state.state_from_exact_values(
        species="RATTATA",
        level=13,
        item="NO_ITEM",
        moves=("TACKLE", "TAIL_WHIP", "NO_MOVE", "NO_MOVE"),
        current_hp=30,
        max_hp=30,
        atk=18,
        defense=14,
        speed=25,
        sp_atk=10,
        sp_def=12,
    )
    ghost_defender = state.state_from_exact_values(
        species="GASTLY",
        level=13,
        item="NO_ITEM",
        moves=("LICK", "HYPNOSIS", "NO_MOVE", "NO_MOVE"),
        current_hp=28,
        max_hp=28,
        atk=13,
        defense=12,
        speed=25,
        sp_atk=30,
        sp_def=18,
    )
    dark_defender = state.state_from_exact_values(
        species="HOUNDOUR",
        level=13,
        item="NO_ITEM",
        moves=("EMBER", "LEER", "NO_MOVE", "NO_MOVE"),
        current_hp=32,
        max_hp=32,
        atk=19,
        defense=14,
        speed=22,
        sp_atk=27,
        sp_def=19,
    )
    immune_actual = [
        (row.move_constant, row.damage_low, row.damage_high)
        for row in calculate_all_moves(fixed_attacker, normal_defender).moves[:1]
    ]
    immune_actual.extend(
        (row.move_constant, row.damage_low, row.damage_high)
        for row in calculate_all_moves(fixed_attacker, ghost_defender).moves[1:3]
    )
    super_fang_attacker = state.state_from_exact_values(
        species="RATICATE",
        level=22,
        item="NO_ITEM",
        moves=("SUPER_FANG", "NO_MOVE", "NO_MOVE", "NO_MOVE"),
        current_hp=50,
        max_hp=50,
        atk=45,
        defense=35,
        speed=55,
        sp_atk=25,
        sp_def=35,
    )
    super_fang_result = calculate_all_moves(super_fang_attacker, ghost_defender).moves[0]
    immune_actual.append((
        super_fang_result.move_constant,
        super_fang_result.damage_low,
        super_fang_result.damage_high,
    ))
    psywave_result = calculate_move(
        fixed_attacker,
        dark_defender,
        state.BattleContext(),
        slot=4,
        move_id=fixed_attacker.moves[3],
    )
    immune_actual.append((psywave_result.move_constant, psywave_result.damage_low, psywave_result.damage_high))
    immune_expected = [
        ("NIGHT_SHADE", 0, 0),
        ("SONICBOOM", 0, 0),
        ("DRAGON_RAGE", 40, 40),
        ("SUPER_FANG", 0, 0),
        ("PSYWAVE", 0, 0),
    ]
    if immune_actual != immune_expected:
        raise AssertionError(f"expected immune fixed-damage cases {immune_expected}, got {immune_actual}")
    print("PASS: battle_calc self-test")
    return 0


class BattleCalcArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        raise BattleCalcError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = BattleCalcArgumentParser(description="Query exact all-move damage from ROM data.")
    parser.add_argument("--attacker-trainer", help="TRAINER_ID[:SPECIES_OR_INDEX]")
    parser.add_argument("--defender-save", type=Path, help=".sav battery save")
    parser.add_argument("--defender-slot", type=int, default=1)
    parser.add_argument("--all-moves", action="store_true")
    parser.add_argument("--attacker", help="SPECIES:LEVEL[:trainer|player]")
    parser.add_argument("--defender", help="SPECIES:LEVEL[:trainer|player]")
    parser.add_argument("--move", help="Move for source-table single-move compatibility")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if args.self_test:
        return
    trainer_mode = args.attacker_trainer or args.defender_save or args.all_moves
    source_mode = args.attacker or args.defender or args.move
    if trainer_mode and source_mode:
        raise BattleCalcError("use either trainer-vs-save mode or source-table single-move mode")
    if trainer_mode:
        if not args.attacker_trainer:
            raise BattleCalcError("--attacker-trainer is required")
        if not args.defender_save:
            raise BattleCalcError("--defender-save is required")
        if not args.all_moves:
            raise BattleCalcError("--all-moves is required")
        if not 1 <= args.defender_slot <= 6:
            raise BattleCalcError("--defender-slot must be 1-6")
        return
    if source_mode:
        missing = [name for name in ("attacker", "defender", "move") if not getattr(args, name)]
        if missing:
            raise BattleCalcError(f"missing source-table argument(s): {', '.join(missing)}")
        return
    raise BattleCalcError("provide --self-test, trainer-vs-save args, or source-table args")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        validate_args(args)
        if args.self_test:
            return run_self_test()
        if args.attacker:
            return run_source_single_move(args)
        report = run_trainer_vs_save(args)
        print(report_to_json(report) if args.json else format_report(report))
        return 0
    except (BattleCalcError, state.StateInputError, tables.InputError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"internal error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
