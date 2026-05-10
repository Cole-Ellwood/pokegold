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
    attacker_stat: int
    defender_stat: int
    defender_max_hp: int
    defender_current_hp: int
    is_physical: bool
    battle_turn: str
    weather: str
    is_critical: bool
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


def _normalize_name(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^A-Z0-9]+", "_", value.upper())).strip("_")


def _collapse_key(value: str) -> str:
    return _normalize_name(value).replace("_", "")


def _read(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _asm_int(value: str) -> int:
    return int("0x" + value[1:], 16) if value.startswith("$") else int(value, 0)


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
    species_order = [
        name
        for name, item_id in sorted(
            _parse_const_values(ROOT / "constants/pokemon_constants.asm").items(),
            key=lambda pair: pair[1],
        )
        if item_id > 0
    ]
    labels = [
        re.match(r"\s*dw\s+([A-Za-z0-9_]+EvosAttacks)\b", line).group(1)
        for line in _read(ROOT / "data/pokemon/evos_attacks_pointers.asm")
        if re.match(r"\s*dw\s+([A-Za-z0-9_]+EvosAttacks)\b", line)
    ]
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
    if weather == "hail":
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
    level: int,
    iv: int,
    statexp: int,
    types: dict[str, int],
) -> bool:
    if move.name == "OUTRAGE" and types["DRAGON"] in (types[attacker.type_a], types[attacker.type_b]):
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
    move_name = _resolve_name(args.move, moves, "move")
    move = moves[move_name]
    atk_row = base_stats[attacker.species]
    def_row = base_stats[defender.species]
    atk_iv, atk_statexp = _profile(attacker.role, args.user_grind)
    def_iv, def_statexp = _profile(defender.role, args.defender_grind)
    is_physical = _is_physical_move(move, atk_row, attacker.level, atk_iv, atk_statexp, types)

    attacker_stat = compute_stat(atk_row.atk if is_physical else atk_row.sat, attacker.level, atk_iv, atk_statexp, False)
    defender_stat = compute_stat(def_row.def_ if is_physical else def_row.sdf, defender.level, def_iv, def_statexp, False)
    defender_max_hp = compute_stat(def_row.hp, defender.level, def_iv, def_statexp, True)
    defender_current_hp = max(1, defender_max_hp * args.defender_hp // 100)
    user_item = _resolve_item(args.user_item)
    opponent_item = _resolve_item(args.opponent_item)
    battle_turn_int, battle_turn = _turn_to_int(args.turn, attacker.role)
    can_evolve = _load_can_evolve()

    inp = BattleInputs(
        attacker_level=attacker.level,
        move_bp=move.bp,
        move_type=types[move.type_name],
        is_physical=is_physical,
        attacker_atk=attacker_stat,
        defender_def=defender_stat,
        attacker_types=(types[atk_row.type_a], types[atk_row.type_b]),
        defender_types=(types[def_row.type_a], types[def_row.type_b]),
        user_item=user_item,
        opponent_item=opponent_item,
        can_evolve_attacker=can_evolve.get(attacker.species, False),
        can_evolve_defender=can_evolve.get(defender.species, False),
        is_critical=args.crit,
        is_selfdestruct=move.effect == "EFFECT_SELFDESTRUCT",
        opponent_above_half_hp=defender_current_hp * 2 > defender_max_hp,
        weather=_weather_to_int(args.weather),
        move_effect=effects[move.effect],
        battle_turn=battle_turn_int,
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
        attacker_stat=attacker_stat,
        defender_stat=defender_stat,
        defender_max_hp=defender_max_hp,
        defender_current_hp=defender_current_hp,
        is_physical=is_physical,
        battle_turn=battle_turn,
        weather=args.weather,
        is_critical=args.crit,
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
                "types": _types_for(result.attacker_row),
            },
            "defender": {
                "species": result.defender.species,
                "level": result.defender.level,
                "role": result.defender.role,
                "def_stat": result.defender_stat,
                "types": _types_for(result.defender_row),
                "max_hp": result.defender_max_hp,
                "current_hp": result.defender_current_hp,
            },
            "move": {
                "name": result.move.name,
                "bp": result.move.bp,
                "type": result.move.type_name,
                "is_physical": result.is_physical,
            },
            "items": {"user": result.user_item_constant, "opponent": result.opponent_item_constant},
            "weather": result.weather,
            "crit": result.is_critical,
            "battle_turn": result.battle_turn,
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
    parser.add_argument("--defender-hp", type=int, default=100, metavar="PERCENT")
    parser.add_argument("--crit", action="store_true", help="Force critical-hit damage")
    parser.add_argument("--weather", choices=("none", "rain", "sun", "sandstorm", "hail"), default="none")
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
    if not 1 <= args.defender_hp <= 100:
        raise InputError("--defender-hp must be 1-100")


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
    assert base["CROBAT"] == BaseStatsRow("CROBAT", 100, 120, 105, 130, 70, 80, "POISON", "FLYING")
    assert moves["WING_ATTACK"].bp == 80 and moves["WING_ATTACK"].type_name == "FLYING"
    assert items["SHARP_BEAK"] == oracle.HELD_SHARP_BEAK
    assert items["HELD_SHARP_BEAK"] == oracle.HELD_SHARP_BEAK
    assert types["PSYCHIC_TYPE"] == oracle.PSYCHIC_TYPE

    cases = (
        (
            ("CROBAT:44:trainer", "ALAKAZAM:44:player", "WING_ATTACK", "--user-item", "sharp_beak", "--defender-grind", "mid", "--defender-hp", "51"),
            (71, 84),
        ),
        (("PIKACHU:20:trainer", "SQUIRTLE:20:trainer", "TACKLE"), (11, 13)),
        (("SUICUNE:42:player", "DRAGONITE:42:trainer", "SURF", "--user-grind", "max"), (18, 22)),
        (("AMPHAROS:40:trainer", "PILOSWINE:40:trainer", "THUNDER"), (33, 39)),
        (("MACHAMP:50:trainer", "BLASTOISE:50:trainer", "KARATE_CHOP", "--user-item", "choice_band"), (87, 103)),
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
