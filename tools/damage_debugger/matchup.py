"""Quick matchup damage queries backed by the damage oracle."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Sequence

from . import oracle
from .oracle import BattleInputs, predict_damage, predict_damage_trace


ROOT = Path(__file__).resolve().parents[2]
# Mid is pinned to the Koga Crobat fixture stats: Alakazam L44 has 140 HP
# and 78 Defense, producing the verified 71-84 Wing Attack range.
GRINDS = {
    "low": (8, 0),
    "mid": (13, 50),
    "high": (15, 60),
    "max": (15, 64),
}
TRAINER_IV_STATEEXP = (8, 0)


class InputError(Exception):
    """User-facing CLI input error."""


@dataclass(frozen=True)
class BaseStatsRow:
    species: str
    hp: int
    atk: int
    def_: int
    spe: int
    sat: int
    sdf: int
    type_a: str
    type_b: str


@dataclass(frozen=True)
class MoveRow:
    name: str
    effect: str
    bp: int
    type_name: str
    accuracy: int
    pp: int
    effect_chance: int


@dataclass(frozen=True)
class PokemonArg:
    species: str
    level: int
    role: str


@dataclass(frozen=True)
class MatchupResult:
    attacker: PokemonArg
    defender: PokemonArg
    attacker_row: BaseStatsRow
    defender_row: BaseStatsRow
    move: MoveRow
    move_display: str
    user_item: int
    opponent_item: int
    user_item_display: str
    opponent_item_display: str
    user_item_constant: str
    opponent_item_constant: str
    user_grind: str
    defender_grind: str
    defender_hp_percent: int
    attacker_types: tuple[str, str]
    defender_types: tuple[str, str]
    attacker_stat: int
    defender_stat: int
    attacker_max_hp: int
    attacker_current_hp: int
    defender_max_hp: int
    defender_current_hp: int
    move_bp: int
    move_type_name: str
    is_physical: bool
    battle_turn: str
    weather: str
    is_critical: bool
    attacker_below_third_hp: bool
    opponent_has_status: bool
    opponent_above_half_hp: bool
    attacker_can_evolve: bool
    defender_can_evolve: bool
    johto_badges: int
    kanto_badges: int
    link_mode: int
    initial_cur_damage: int
    metronome_count: int
    damage_low: int
    damage_high: int
    crit_low: int
    crit_high: int
    trace: list[tuple[str, int]]


_BASE_STATS: dict[str, BaseStatsRow] | None = None
_MOVES: dict[str, MoveRow] | None = None
_TYPE_CONSTANTS: dict[str, int] | None = None
_MOVE_EFFECTS: dict[str, int] | None = None
_WEATHER_CONSTANTS: dict[str, int] | None = None
_ITEM_LOOKUP: dict[str, int] | None = None
_ITEM_NAMES: dict[int, str] | None = None
_ITEM_CONSTANTS: dict[str, int] | None = None
_CAN_EVOLVE: dict[str, bool] | None = None
_MOVE_DISPLAY_NAMES: dict[str, str] | None = None
_MOVE_ALIASES: dict[str, str] | None = None

ALL_DAMAGE_TYPE_VALUES = {
    oracle.NORMAL,
    oracle.FIGHTING,
    oracle.FLYING,
    oracle.POISON,
    oracle.GROUND,
    oracle.ROCK,
    oracle.BUG,
    oracle.GHOST,
    oracle.STEEL,
    oracle.FIRE,
    oracle.WATER,
    oracle.GRASS,
    oracle.ELECTRIC,
    oracle.PSYCHIC_TYPE,
    oracle.ICE,
    oracle.DRAGON,
    oracle.DARK,
}


def _normalize_name(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^A-Z0-9]+", "_", value.upper())).strip("_")


def _collapse_key(value: str) -> str:
    return _normalize_name(value).replace("_", "")


def _read(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _asm_int(value: str) -> int:
    return int("0x" + value[1:], 16) if value.startswith("$") else int(value, 0)


def _arg_int(value: str) -> int:
    try:
        return _asm_int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid integer '{value}'") from exc


def _parse_const_values(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    value: int | None = None
    for raw in _read(path):
        code = raw.split(";", 1)[0].strip()
        if not code:
            continue
        parts = code.split()
        if parts[0] == "const_def":
            value = _asm_int(parts[1]) if len(parts) > 1 else 0
            continue
        if value is None:
            continue
        if parts[0] == "const_next":
            value = _asm_int(parts[1])
            continue
        if parts[0] == "const_skip":
            value += _asm_int(parts[1]) if len(parts) > 1 else 1
            continue
        if parts[0] == "const":
            out[parts[1]] = value
            value += 1
            continue
        m = re.match(r"DEF\s+([A-Z0-9_]+)\s+EQU\s+const_value\b", code)
        if m:
            out[m.group(1)] = value
    return out


def _resolve_name(value: str, table: dict[str, object], label: str) -> str:
    key = _normalize_name(value)
    if key in table:
        return key
    collapsed = _collapse_key(value)
    matches = [name for name in table if name.replace("_", "") == collapsed]
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise InputError(f"ambiguous {label} '{value}': {', '.join(sorted(matches))}")
    raise InputError(f"unknown {label} '{value}'")


def _add_lookup(lookup: dict[str, int], alias: str, item_id: int) -> None:
    key = _normalize_name(alias)
    previous = lookup.get(key)
    if previous is not None and previous != item_id:
        return
    lookup[key] = item_id


def _add_move_alias(aliases: dict[str, str], alias: str, move_name: str) -> None:
    key = _normalize_name(alias)
    previous = aliases.get(key)
    if previous is not None and previous != move_name:
        aliases[key] = ""
        return
    aliases[key] = move_name


def _load_base_stats() -> dict[str, BaseStatsRow]:
    global _BASE_STATS
    if _BASE_STATS is not None:
        return _BASE_STATS
    rows: dict[str, BaseStatsRow] = {}
    stats_pat = re.compile(r"^\s*db\s+(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)")
    type_pat = re.compile(r"^\s*db\s+([A-Z0-9_]+),\s*([A-Z0-9_]+)\s*;\s*type\b")
    species_pat = re.compile(r"^\s*db\s+([A-Z0-9_]+)\s*;")
    for path in sorted((ROOT / "data/pokemon/base_stats").glob("*.asm")):
        species: str | None = None
        stats: tuple[int, int, int, int, int, int] | None = None
        types: tuple[str, str] | None = None
        for line in _read(path):
            if species is None:
                m = species_pat.match(line)
                if m:
                    species = m.group(1)
                    continue
            if stats is None:
                m = stats_pat.match(line)
                if m:
                    stats = tuple(int(x) for x in m.groups())
                    continue
            if types is None:
                m = type_pat.match(line)
                if m:
                    types = (m.group(1), m.group(2))
        if species is None or stats is None or types is None or species in {"EGG", "DUMMY"}:
            continue
        rows[species] = BaseStatsRow(species, *stats, *types)
    _BASE_STATS = rows
    return rows


def _load_moves() -> dict[str, MoveRow]:
    global _MOVES
    if _MOVES is not None:
        return _MOVES
    rows: dict[str, MoveRow] = {}
    pat = re.compile(
        r"^\s*move\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*,\s*(\d+)\s*,\s*"
        r"([A-Z0-9_]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)"
    )
    for line in _read(ROOT / "data/moves/moves.asm"):
        m = pat.match(line)
        if not m:
            continue
        name, effect, bp, type_name, accuracy, pp, chance = m.groups()
        rows[name] = MoveRow(name, effect, int(bp), type_name, int(accuracy), int(pp), int(chance))
    _MOVES = rows
    return rows


def _load_type_constants() -> dict[str, int]:
    global _TYPE_CONSTANTS
    if _TYPE_CONSTANTS is None:
        _TYPE_CONSTANTS = _parse_const_values(ROOT / "constants/type_constants.asm")
    return _TYPE_CONSTANTS


def _load_move_effect_constants() -> dict[str, int]:
    global _MOVE_EFFECTS
    if _MOVE_EFFECTS is None:
        _MOVE_EFFECTS = _parse_const_values(ROOT / "constants/move_effect_constants.asm")
    return _MOVE_EFFECTS


def _load_weather_constants() -> dict[str, int]:
    global _WEATHER_CONSTANTS
    if _WEATHER_CONSTANTS is None:
        _WEATHER_CONSTANTS = _parse_const_values(ROOT / "constants/battle_constants.asm")
    return _WEATHER_CONSTANTS


def _load_item_constants() -> dict[str, int]:
    global _ITEM_CONSTANTS
    if _ITEM_CONSTANTS is None:
        _ITEM_CONSTANTS = _parse_const_values(ROOT / "constants/item_constants.asm")
    return _ITEM_CONSTANTS


def _load_item_names() -> dict[int, str]:
    global _ITEM_NAMES
    if _ITEM_NAMES is not None:
        return _ITEM_NAMES
    names: dict[int, str] = {0: "NONE"}
    item_id = 1
    in_names = False
    for line in _read(ROOT / "data/items/names.asm"):
        if line.strip() == "ItemNames::":
            in_names = True
            continue
        if not in_names:
            continue
        if "assert_list_length NUM_ITEMS" in line:
            break
        m = re.match(r'\s*li\s+"([^"]+)"', line)
        if m:
            names[item_id] = m.group(1)
            item_id += 1
    _ITEM_NAMES = names
    return names


def _load_held_item_constants() -> dict[str, int]:
    global _ITEM_LOOKUP
    if _ITEM_LOOKUP is not None:
        return _ITEM_LOOKUP
    item_constants = _load_item_constants()
    item_names = _load_item_names()
    lookup: dict[str, int] = {}
    _add_lookup(lookup, "none", 0)
    _add_lookup(lookup, "no_item", 0)
    _add_lookup(lookup, "held_none", 0)
    for item_name, item_id in item_constants.items():
        if item_id in item_names:
            _add_lookup(lookup, item_names[item_id], item_id)
        _add_lookup(lookup, item_name, item_id)

    item_id = 1
    current_item: str | None = None
    for line in _read(ROOT / "data/items/attributes.asm"):
        stripped = line.strip()
        if stripped.startswith("; "):
            current_item = stripped[2:].split()[0]
            continue
        if not stripped.startswith("item_attribute"):
            continue
        parts = [part.strip() for part in stripped[len("item_attribute") :].split(",")]
        held_effect = parts[1] if len(parts) > 1 else "HELD_NONE"
        if current_item and held_effect != "HELD_NONE":
            _add_lookup(lookup, f"HELD_{current_item}", item_id)
            if item_id in item_names:
                _add_lookup(lookup, f"HELD_{item_names[item_id]}", item_id)
        current_item = None
        item_id += 1

    if "EVOLITE" in lookup:
        _add_lookup(lookup, "eviolite", lookup["EVOLITE"])
        _add_lookup(lookup, "held_eviolite", lookup["EVOLITE"])

    _ITEM_LOOKUP = lookup
    return lookup


def _load_can_evolve() -> dict[str, bool]:
    global _CAN_EVOLVE
    if _CAN_EVOLVE is not None:
        return _CAN_EVOLVE
    species_order: list[str] = []
    in_species_constants = False
    for raw in _read(ROOT / "constants/pokemon_constants.asm"):
        code = raw.split(";", 1)[0].strip()
        if code.startswith("const_def 1"):
            in_species_constants = True
            continue
        if not in_species_constants:
            continue
        if code.startswith("DEF NUM_POKEMON"):
            break
        m = re.match(r"const\s+([A-Z0-9_]+)\b", code)
        if m:
            species_order.append(m.group(1))
    labels = [
        re.match(r"\s*dw\s+([A-Za-z0-9_]+EvosAttacks)\b", line).group(1)
        for line in _read(ROOT / "data/pokemon/evos_attacks_pointers.asm")
        if re.match(r"\s*dw\s+([A-Za-z0-9_]+EvosAttacks)\b", line)
    ]
    if len(labels) != len(species_order):
        raise InputError(
            f"evolution pointer/species mismatch: {len(labels)} pointers for {len(species_order)} species"
        )
    label_to_species = dict(zip(labels, species_order))
    out: dict[str, bool] = {species: False for species in species_order}
    current_label: str | None = None
    for line in _read(ROOT / "data/pokemon/evos_attacks.asm"):
        label = re.match(r"^([A-Za-z0-9_]+EvosAttacks):\s*$", line)
        if label:
            current_label = label.group(1)
            continue
        if current_label is None:
            continue
        code = line.split(";", 1)[0].strip()
        if not code:
            continue
        species = label_to_species.get(current_label)
        if code == "db 0":
            current_label = None
            continue
        if species and code.startswith("db EVOLVE_"):
            out[species] = True
    _CAN_EVOLVE = out
    return out


def _load_move_display_names() -> dict[str, str]:
    global _MOVE_DISPLAY_NAMES
    if _MOVE_DISPLAY_NAMES is not None:
        return _MOVE_DISPLAY_NAMES
    move_ids = {
        value: name
        for name, value in _parse_const_values(ROOT / "constants/move_constants.asm").items()
        if name != "NO_MOVE"
    }
    out: dict[str, str] = {}
    move_id = 1
    in_names = False
    for line in _read(ROOT / "data/moves/names.asm"):
        if line.strip() == "MoveNames::":
            in_names = True
            continue
        if not in_names:
            continue
        if "assert_list_length" in line:
            break
        m = re.match(r'\s*li\s+"([^"]+)"', line)
        if m and move_id in move_ids:
            out[move_ids[move_id]] = m.group(1).title()
            move_id += 1
    _MOVE_DISPLAY_NAMES = out
    return out


def _load_move_aliases() -> dict[str, str]:
    global _MOVE_ALIASES
    if _MOVE_ALIASES is not None:
        return _MOVE_ALIASES
    aliases: dict[str, str] = {}
    for move_name in _load_moves():
        _add_move_alias(aliases, move_name, move_name)
    for move_name, display_name in _load_move_display_names().items():
        _add_move_alias(aliases, display_name, move_name)
    _MOVE_ALIASES = aliases
    return aliases


def compute_stat(base: int, level: int, iv: int, statexp_term: int, is_hp: bool) -> int:
    """Gen 2 stat formula used for player/trainer profile inputs."""
    inner = ((base + iv) * 2 + statexp_term) * level // 100
    return inner + level + 10 if is_hp else inner + 5


def _parse_pokemon_arg(value: str, default_role: str, table: dict[str, BaseStatsRow]) -> PokemonArg:
    parts = value.split(":")
    if len(parts) not in {2, 3}:
        raise InputError(f"bad Pokemon '{value}': expected SPECIES:LEVEL[:role]")
    species = _resolve_name(parts[0], table, "species")
    try:
        level = int(parts[1])
    except ValueError as exc:
        raise InputError(f"bad level '{parts[1]}' for {species}") from exc
    if not 1 <= level <= 100:
        raise InputError(f"bad level '{level}' for {species}: expected 1-100")
    role = parts[2].lower() if len(parts) == 3 else default_role
    if role not in {"trainer", "player"}:
        raise InputError(f"bad role '{role}' for {species}: expected trainer or player")
    return PokemonArg(species, level, role)


def _profile(role: str, grind: str) -> tuple[int, int]:
    if role == "trainer":
        return TRAINER_IV_STATEEXP
    return GRINDS[grind]


def _resolve_move(value: str) -> str:
    aliases = _load_move_aliases()
    key = _normalize_name(value)
    if key in aliases:
        move_name = aliases[key]
        if move_name:
            return move_name
        raise InputError(f"ambiguous move '{value}'")
    collapsed = _collapse_key(value)
    matches = [(alias, move_name) for alias, move_name in aliases.items() if alias.replace("_", "") == collapsed]
    move_names = {move_name for _, move_name in matches if move_name}
    if len(move_names) == 1:
        return move_names.pop()
    if matches:
        raise InputError(f"ambiguous move '{value}': {', '.join(sorted(alias for alias, _ in matches))}")
    raise InputError(f"unknown move '{value}'")


def _resolve_type_name(value: str) -> str:
    types = _load_type_constants()
    key = _normalize_name(value)
    if key == "PSYCHIC":
        key = "PSYCHIC_TYPE"
    if key in types and types[key] in ALL_DAMAGE_TYPE_VALUES:
        return key
    collapsed = key.replace("_TYPE", "").replace("_", "")
    matches = [
        name
        for name, type_id in types.items()
        if type_id in ALL_DAMAGE_TYPE_VALUES and name.replace("_TYPE", "").replace("_", "") == collapsed
    ]
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise InputError(f"ambiguous type '{value}': {', '.join(sorted(matches))}")
    raise InputError(f"unknown type '{value}'")


def _resolve_type_pair(value: str | None, default_a: str, default_b: str) -> tuple[str, str]:
    if value is None:
        return default_a, default_b
    parts = [part.strip() for part in re.split(r"[,/]", value) if part.strip()]
    if len(parts) == 1:
        type_name = _resolve_type_name(parts[0])
        return type_name, type_name
    if len(parts) == 2:
        return _resolve_type_name(parts[0]), _resolve_type_name(parts[1])
    raise InputError(f"bad type pair '{value}': expected TYPE or TYPE,TYPE")


def _resolve_current_hp(exact_hp: int | None, percent: int, max_hp: int, label: str) -> int:
    if exact_hp is None:
        return max(1, max_hp * percent // 100)
    if not 1 <= exact_hp <= max_hp:
        raise InputError(f"{label} current HP must be 1-{max_hp}, got {exact_hp}")
    return exact_hp


def _validate_range(value: int, label: str, low: int, high: int) -> None:
    if not low <= value <= high:
        raise InputError(f"{label} must be {low}-{high}, got {value}")


def _resolve_item(value: str) -> int:
    lookup = _load_held_item_constants()
    key = _normalize_name(value)
    if key in lookup:
        return lookup[key]
    collapsed = _collapse_key(value)
    matches = [(name, item_id) for name, item_id in lookup.items() if name.replace("_", "") == collapsed]
    item_ids = {item_id for _, item_id in matches}
    if len(item_ids) == 1:
        return item_ids.pop()
    if matches:
        raise InputError(f"ambiguous item '{value}': {', '.join(sorted(name for name, _ in matches))}")
    raise InputError(f"unknown item '{value}'")


def _canonical_item_constant(item_id: int) -> str:
    if item_id == 0:
        return "HELD_NONE"
    constants = _load_item_constants()
    reverse = {value: name for name, value in constants.items()}
    name = reverse.get(item_id, f"ITEM_{item_id:02X}")
    if name == "METRONOME_ITEM":
        name = "METRONOME"
    return f"HELD_{name}"


def _display_item(item_id: int) -> str:
    if item_id == 0:
        return "no item"
    return _load_item_names().get(item_id, _canonical_item_constant(item_id)).title()


def _display_species(species: str) -> str:
    return species.replace("__", " ").replace("_", " ").title()


def _display_move(move: MoveRow) -> str:
    return _load_move_display_names().get(move.name, move.name.replace("_", " ").title())


def _weather_to_int(weather: str) -> int:
    constants = _load_weather_constants()
    if weather == "none":
        return constants["WEATHER_NONE"]
    key = f"WEATHER_{weather.upper()}"
    if key not in constants:
        raise InputError(f"unknown weather '{weather}'")
    return constants[key]


def _turn_to_int(turn: str, attacker_role: str) -> tuple[int, str]:
    resolved = "enemy" if turn == "auto" and attacker_role == "trainer" else turn
    resolved = "player" if resolved == "auto" else resolved
    return (1 if resolved == "enemy" else 0), resolved


def _is_physical_move(
    move: MoveRow,
    attacker: BaseStatsRow,
    attacker_types: tuple[str, str],
    level: int,
    iv: int,
    statexp: int,
    types: dict[str, int],
) -> bool:
    if move.name == "OUTRAGE" and types["DRAGON"] in (types[attacker_types[0]], types[attacker_types[1]]):
        atk = compute_stat(attacker.atk, level, iv, statexp, is_hp=False)
        sat = compute_stat(attacker.sat, level, iv, statexp, is_hp=False)
        return atk > sat
    return types[move.type_name] <= oracle.PHYSICAL_MAX


def _pct(part: int, whole: int) -> int:
    return (part * 100 + whole // 2) // whole if whole else 0


def _damage_range(max_damage: int) -> tuple[int, int]:
    return max_damage * 217 // 255, max_damage


def run_matchup(args: argparse.Namespace) -> MatchupResult:
    base_stats = _load_base_stats()
    moves = _load_moves()
    types = _load_type_constants()
    effects = _load_move_effect_constants()

    attacker = _parse_pokemon_arg(args.attacker, "trainer", base_stats)
    defender = _parse_pokemon_arg(args.defender, "player", base_stats)
    move_name = _resolve_move(args.move)
    move = moves[move_name]
    atk_row = base_stats[attacker.species]
    def_row = base_stats[defender.species]
    atk_iv, atk_statexp = _profile(attacker.role, args.user_grind)
    def_iv, def_statexp = _profile(defender.role, args.defender_grind)
    attacker_types = _resolve_type_pair(args.attacker_types, atk_row.type_a, atk_row.type_b)
    defender_types = _resolve_type_pair(args.defender_types, def_row.type_a, def_row.type_b)
    move_type_name = _resolve_type_name(args.move_type) if args.move_type else move.type_name
    if args.category == "physical":
        is_physical = True
    elif args.category == "special":
        is_physical = False
    else:
        is_physical = _is_physical_move(move, atk_row, attacker_types, attacker.level, atk_iv, atk_statexp, types)
        if args.move_type:
            is_physical = types[move_type_name] <= oracle.PHYSICAL_MAX
    move_bp = args.move_bp if args.move_bp is not None else move.bp

    attacker_stat = args.attacker_stat if args.attacker_stat is not None else compute_stat(
        atk_row.atk if is_physical else atk_row.sat, attacker.level, atk_iv, atk_statexp, False
    )
    defender_stat = args.defender_stat if args.defender_stat is not None else compute_stat(
        def_row.def_ if is_physical else def_row.sdf, defender.level, def_iv, def_statexp, False
    )
    attacker_max_hp = compute_stat(atk_row.hp, attacker.level, atk_iv, atk_statexp, True)
    defender_max_hp = compute_stat(def_row.hp, defender.level, def_iv, def_statexp, True)
    attacker_current_hp = _resolve_current_hp(args.attacker_current_hp, args.attacker_hp, attacker_max_hp, "attacker")
    defender_current_hp = _resolve_current_hp(args.defender_current_hp, args.defender_hp, defender_max_hp, "defender")
    user_item = _resolve_item(args.user_item)
    opponent_item = _resolve_item(args.opponent_item)
    battle_turn_int, battle_turn = _turn_to_int(args.turn, attacker.role)
    can_evolve = _load_can_evolve()
    attacker_can_evolve = can_evolve.get(attacker.species, False) if args.attacker_can_evolve is None else args.attacker_can_evolve
    defender_can_evolve = can_evolve.get(defender.species, False) if args.defender_can_evolve is None else args.defender_can_evolve

    inp = BattleInputs(
        attacker_level=attacker.level,
        move_bp=move_bp,
        move_type=types[move_type_name],
        is_physical=is_physical,
        attacker_atk=attacker_stat,
        defender_def=defender_stat,
        attacker_types=(types[attacker_types[0]], types[attacker_types[1]]),
        defender_types=(types[defender_types[0]], types[defender_types[1]]),
        user_item=user_item,
        opponent_item=opponent_item,
        can_evolve_attacker=attacker_can_evolve,
        can_evolve_defender=defender_can_evolve,
        is_critical=args.crit,
        is_selfdestruct=move.effect == "EFFECT_SELFDESTRUCT",
        attacker_below_third_hp=args.attacker_below_third_hp or attacker_current_hp * 3 <= attacker_max_hp,
        opponent_has_status=args.opponent_status,
        opponent_above_half_hp=defender_current_hp * 2 > defender_max_hp,
        weather=_weather_to_int(args.weather),
        move_effect=effects[move.effect],
        johto_badges=args.johto_badges,
        kanto_badges=args.kanto_badges,
        link_mode=args.link_mode,
        battle_turn=battle_turn_int,
        initial_cur_damage=args.initial_cur_damage,
        metronome_count=args.metronome_count,
    )
    damage_low, damage_high = _damage_range(predict_damage(inp))
    crit_low, crit_high = _damage_range(predict_damage(replace(inp, is_critical=True)))
    trace = predict_damage_trace(inp) if args.trace else []

    return MatchupResult(
        attacker=attacker,
        defender=defender,
        attacker_row=atk_row,
        defender_row=def_row,
        move=move,
        move_display=_display_move(move),
        user_item=user_item,
        opponent_item=opponent_item,
        user_item_display=_display_item(user_item),
        opponent_item_display=_display_item(opponent_item),
        user_item_constant=_canonical_item_constant(user_item),
        opponent_item_constant=_canonical_item_constant(opponent_item),
        user_grind=args.user_grind,
        defender_grind=args.defender_grind,
        defender_hp_percent=args.defender_hp,
        attacker_types=attacker_types,
        defender_types=defender_types,
        attacker_stat=attacker_stat,
        defender_stat=defender_stat,
        attacker_max_hp=attacker_max_hp,
        attacker_current_hp=attacker_current_hp,
        defender_max_hp=defender_max_hp,
        defender_current_hp=defender_current_hp,
        move_bp=move_bp,
        move_type_name=move_type_name,
        is_physical=is_physical,
        battle_turn=battle_turn,
        weather=args.weather,
        is_critical=args.crit,
        attacker_below_third_hp=inp.attacker_below_third_hp,
        opponent_has_status=inp.opponent_has_status,
        opponent_above_half_hp=inp.opponent_above_half_hp,
        attacker_can_evolve=attacker_can_evolve,
        defender_can_evolve=defender_can_evolve,
        johto_badges=args.johto_badges,
        kanto_badges=args.kanto_badges,
        link_mode=args.link_mode,
        initial_cur_damage=args.initial_cur_damage,
        metronome_count=args.metronome_count,
        damage_low=damage_low,
        damage_high=damage_high,
        crit_low=crit_low,
        crit_high=crit_high,
        trace=trace,
    )


def _ko_label(low: int, high: int, hp: int) -> str:
    if low >= hp:
        return "GUARANTEED"
    if high < hp:
        return "NEVER"
    return "POSSIBLE"


def _ko_detail(low: int, high: int, hp: int) -> str:
    label = _ko_label(low, high, hp)
    if label == "GUARANTEED":
        return f"low roll = {_pct(low, hp)}%"
    if label == "NEVER":
        return f"max roll = {_pct(high, hp)}%"
    return f"rolls = {_pct(low, hp)}-{_pct(high, hp)}%"


def format_text(result: MatchupResult) -> str:
    atk_desc = f"{_display_species(result.attacker.species)} L{result.attacker.level} {result.attacker.role}"
    if result.user_item:
        atk_desc = f"{atk_desc}, {result.user_item_display}"
    def_bits = [
        _display_species(result.defender.species),
        f"L{result.defender.level}",
        f"{result.defender_grind}-grind" if result.defender.role == "player" else "trainer",
        f"{result.defender_hp_percent}% HP",
    ]
    lines = [
        f"{result.move_display} ({atk_desc}) vs {' '.join(def_bits[:2])} ({', '.join(def_bits[2:])})",
        f"  damage roll:     {result.damage_low}-{result.damage_high}  (low: {result.damage_low}, max: {result.damage_high})",
        f"  % of full HP:    {_pct(result.damage_low, result.defender_max_hp)}-{_pct(result.damage_high, result.defender_max_hp)}%  (max HP = {result.defender_max_hp})",
        f"  % of current HP: {_pct(result.damage_low, result.defender_current_hp)}-{_pct(result.damage_high, result.defender_current_hp)}%  (current HP = {result.defender_current_hp})",
        f"  KO at current HP: {_ko_label(result.damage_low, result.damage_high, result.defender_current_hp)}  ({_ko_detail(result.damage_low, result.damage_high, result.defender_current_hp)})",
        f"  KO at full HP:    {_ko_label(result.damage_low, result.damage_high, result.defender_max_hp)}  ({_ko_detail(result.damage_low, result.damage_high, result.defender_max_hp)})",
    ]
    if not result.is_critical:
        lines.append(
            f"  crit (x2 base):   {result.crit_low}-{result.crit_high}  "
            f"(full HP: {_pct(result.crit_low, result.defender_max_hp)}-{_pct(result.crit_high, result.defender_max_hp)}%, "
            f"current: {_pct(result.crit_low, result.defender_current_hp)}-{_pct(result.crit_high, result.defender_current_hp)}%)"
        )
    state_bits = []
    if result.attacker_below_third_hp:
        state_bits.append("attacker <= 1/3 HP")
    if result.opponent_has_status:
        state_bits.append("defender statused")
    if result.metronome_count:
        state_bits.append(f"metronome count {result.metronome_count}")
    if result.initial_cur_damage:
        state_bits.append(f"initial damage {result.initial_cur_damage}")
    if result.johto_badges or result.kanto_badges or result.link_mode:
        state_bits.append(
            f"badges J:{result.johto_badges:#04x} K:{result.kanto_badges:#04x} link:{result.link_mode:#04x}"
        )
    if state_bits:
        lines.append(f"  state: {'; '.join(state_bits)}")
    if result.trace:
        lines.append("  trace:")
        lines.extend(f"    {step}: {damage}" for step, damage in result.trace)
    return "\n".join(lines)


def _types_for(row: BaseStatsRow) -> list[str]:
    return [row.type_a, row.type_b]


def format_json(result: MatchupResult) -> str:
    data: dict[str, object] = {
        "matchup": {
            "attacker": {
                "species": result.attacker.species,
                "level": result.attacker.level,
                "role": result.attacker.role,
                "atk_stat": result.attacker_stat,
                "types": list(result.attacker_types),
                "max_hp": result.attacker_max_hp,
                "current_hp": result.attacker_current_hp,
            },
            "defender": {
                "species": result.defender.species,
                "level": result.defender.level,
                "role": result.defender.role,
                "def_stat": result.defender_stat,
                "types": list(result.defender_types),
                "max_hp": result.defender_max_hp,
                "current_hp": result.defender_current_hp,
            },
            "move": {
                "name": result.move.name,
                "bp": result.move_bp,
                "type": result.move_type_name,
                "source_bp": result.move.bp,
                "source_type": result.move.type_name,
                "is_physical": result.is_physical,
            },
            "items": {"user": result.user_item_constant, "opponent": result.opponent_item_constant},
            "weather": result.weather,
            "crit": result.is_critical,
            "battle_turn": result.battle_turn,
            "state": {
                "attacker_below_third_hp": result.attacker_below_third_hp,
                "opponent_has_status": result.opponent_has_status,
                "opponent_above_half_hp": result.opponent_above_half_hp,
                "attacker_can_evolve": result.attacker_can_evolve,
                "defender_can_evolve": result.defender_can_evolve,
                "johto_badges": result.johto_badges,
                "kanto_badges": result.kanto_badges,
                "link_mode": result.link_mode,
                "initial_cur_damage": result.initial_cur_damage,
                "metronome_count": result.metronome_count,
            },
        },
        "result": {
            "damage_low": result.damage_low,
            "damage_high": result.damage_high,
            "pct_of_current_hp_low": _pct(result.damage_low, result.defender_current_hp),
            "pct_of_current_hp_high": _pct(result.damage_high, result.defender_current_hp),
            "pct_of_max_hp_low": _pct(result.damage_low, result.defender_max_hp),
            "pct_of_max_hp_high": _pct(result.damage_high, result.defender_max_hp),
            "ko_at_current_hp_guaranteed": result.damage_low >= result.defender_current_hp,
            "ko_at_max_hp_guaranteed": result.damage_low >= result.defender_max_hp,
            "crit_damage_low": result.crit_low,
            "crit_damage_high": result.crit_high,
        },
    }
    if result.trace:
        data["trace"] = [{"step": step, "damage": damage} for step, damage in result.trace]
    return json.dumps(data, indent=2)


class MatchupArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        raise InputError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = MatchupArgumentParser(description="Query ROM-true damage for one attacker/move/defender matchup.")
    parser.add_argument("attacker", nargs="?", help="SPECIES:LEVEL[:trainer|player], default role trainer")
    parser.add_argument("defender", nargs="?", help="SPECIES:LEVEL[:trainer|player], default role player")
    parser.add_argument("move", nargs="?", help="Move constant or display name")
    parser.add_argument("--user-item", default="none", help="Attacker item name or HELD_* alias")
    parser.add_argument("--opponent-item", default="none", help="Defender item name or HELD_* alias")
    parser.add_argument("--user-grind", choices=sorted(GRINDS), default="mid")
    parser.add_argument("--defender-grind", choices=sorted(GRINDS), default="mid")
    parser.add_argument("--attacker-hp", type=int, default=100, metavar="PERCENT")
    parser.add_argument("--defender-hp", type=int, default=100, metavar="PERCENT")
    parser.add_argument("--attacker-current-hp", type=_arg_int, metavar="HP")
    parser.add_argument("--defender-current-hp", type=_arg_int, metavar="HP")
    parser.add_argument("--attacker-stat", type=_arg_int, help="Exact attack/special-attack stat consumed by damage")
    parser.add_argument("--defender-stat", type=_arg_int, help="Exact defense/special-defense stat consumed by damage")
    parser.add_argument("--attacker-types", help="Exact attacker type pair: TYPE or TYPE,TYPE")
    parser.add_argument("--defender-types", help="Exact defender type pair: TYPE or TYPE,TYPE")
    parser.add_argument("--move-bp", type=_arg_int, help="Exact effective move base power")
    parser.add_argument("--move-type", help="Exact effective move type")
    parser.add_argument("--category", choices=("auto", "physical", "special"), default="auto")
    parser.add_argument("--attacker-below-third-hp", action="store_true", help="Force the Fire low-HP passive flag")
    parser.add_argument("--opponent-status", action="store_true", help="Defender has any major status")
    parser.add_argument("--metronome-count", type=_arg_int, default=0)
    parser.add_argument("--initial-cur-damage", type=_arg_int, default=0)
    parser.add_argument("--johto-badges", type=_arg_int, default=0, metavar="MASK")
    parser.add_argument("--kanto-badges", type=_arg_int, default=0, metavar="MASK")
    parser.add_argument("--link-mode", type=_arg_int, default=0, metavar="VALUE")
    parser.add_argument("--attacker-can-evolve", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--defender-can-evolve", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--crit", action="store_true", help="Force critical-hit damage")
    parser.add_argument("--weather", choices=("none", "rain", "sun", "sandstorm"), default="none")
    parser.add_argument("--turn", choices=("auto", "player", "enemy"), default="auto")
    parser.add_argument("--json", action="store_true", help="Emit stable JSON output")
    parser.add_argument("--trace", action="store_true", help="Show oracle step-boundary damage")
    parser.add_argument("--self-test", action="store_true", help="Run pinned loader and matchup regression checks")
    return parser


def _validate_args(args: argparse.Namespace) -> None:
    if args.self_test:
        return
    missing = [name for name in ("attacker", "defender", "move") if getattr(args, name) is None]
    if missing:
        raise InputError(f"missing required argument(s): {', '.join(missing)}")
    if not 1 <= args.attacker_hp <= 100:
        raise InputError("--attacker-hp must be 1-100")
    if not 1 <= args.defender_hp <= 100:
        raise InputError("--defender-hp must be 1-100")
    if args.move_bp is not None:
        _validate_range(args.move_bp, "--move-bp", 0, 255)
    if args.attacker_stat is not None:
        _validate_range(args.attacker_stat, "--attacker-stat", 1, 999)
    if args.defender_stat is not None:
        _validate_range(args.defender_stat, "--defender-stat", 1, 999)
    _validate_range(args.metronome_count, "--metronome-count", 0, 5)
    _validate_range(args.initial_cur_damage, "--initial-cur-damage", 0, 0xFFFF)
    _validate_range(args.johto_badges, "--johto-badges", 0, 0xFF)
    _validate_range(args.kanto_badges, "--kanto-badges", 0, 0xFF)
    _validate_range(args.link_mode, "--link-mode", 0, 0xFF)


def _run_case(argv: Sequence[str], expected: tuple[int, int]) -> None:
    args = build_parser().parse_args(list(argv))
    _validate_args(args)
    result = run_matchup(args)
    actual = (result.damage_low, result.damage_high)
    if actual != expected:
        raise AssertionError(
            f"{' '.join(argv)} expected damage {expected[0]}-{expected[1]}, "
            f"got {actual[0]}-{actual[1]}"
        )


def run_self_test() -> int:
    base = _load_base_stats()
    moves = _load_moves()
    items = _load_held_item_constants()
    types = _load_type_constants()
    can_evolve = _load_can_evolve()
    assert base["CROBAT"] == BaseStatsRow("CROBAT", 100, 120, 105, 130, 70, 80, "POISON", "FLYING")
    assert moves["WING_ATTACK"].bp == 80 and moves["WING_ATTACK"].type_name == "FLYING"
    assert items["SHARP_BEAK"] == oracle.HELD_SHARP_BEAK
    assert items["HELD_SHARP_BEAK"] == oracle.HELD_SHARP_BEAK
    assert types["PSYCHIC_TYPE"] == oracle.PSYCHIC_TYPE
    assert can_evolve["SQUIRTLE"] is True
    assert can_evolve["AMPHAROS"] is False

    cases = (
        (
            ("CROBAT:44:trainer", "ALAKAZAM:44:player", "WING_ATTACK", "--user-item", "sharp_beak", "--defender-grind", "mid", "--defender-hp", "51"),
            (71, 84),
        ),
        (("PIKACHU:20:trainer", "SQUIRTLE:20:trainer", "TACKLE"), (11, 13)),
        (("SUICUNE:42:player", "DRAGONITE:42:trainer", "SURF", "--user-grind", "max"), (18, 22)),
        (("AMPHAROS:40:trainer", "PILOSWINE:40:trainer", "THUNDER"), (33, 39)),
        (("MACHAMP:50:trainer", "BLASTOISE:50:trainer", "KARATE_CHOP", "--user-item", "choice_band"), (87, 103)),
        (("ALAKAZAM:44:trainer", "CROBAT:44:player", "Psychic"), (59, 70)),
        (("CHARIZARD:50:trainer", "VENUSAUR:50:player", "FLAMETHROWER", "--attacker-current-hp", "50"), (106, 125)),
        (("MACHAMP:50:trainer", "BLASTOISE:50:trainer", "KARATE_CHOP", "--user-item", "metronome", "--metronome-count", "3"), (91, 108)),
        (("AMPHAROS:40:trainer", "PILOSWINE:40:player", "HIDDEN_POWER", "--move-type", "Ice", "--move-bp", "70", "--category", "special"), (21, 25)),
        (("GENGAR:50:trainer", "BLASTOISE:50:trainer", "SHADOW_BALL", "--opponent-status"), (54, 64)),
        (("PIKACHU:20:player", "SQUIRTLE:20:trainer", "TACKLE", "--turn", "player", "--johto-badges", "0x4"), (15, 18)),
        (("PIKACHU:20:trainer", "SQUIRTLE:20:trainer", "TACKLE", "--opponent-item", "eviolite"), (7, 9)),
    )
    for argv, expected in cases:
        _run_case(argv, expected)
    print("PASS: matchup CLI self-test")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        _validate_args(args)
        if args.self_test:
            return run_self_test()
        result = run_matchup(args)
        print(format_json(result) if args.json else format_text(result))
        return 0
    except InputError as exc:
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
