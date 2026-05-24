"""Shared source-table helpers for damage debugger tools.

This module intentionally wraps the existing matchup loaders first, rather
than moving a thousand lines at once. New tools should import from here; once
the call sites have settled, the private parser implementations can be moved
out of `matchup.py` mechanically.
"""

from __future__ import annotations

from pathlib import Path

from . import matchup
from . import oracle


ROOT = Path(__file__).resolve().parents[2]

InputError = matchup.InputError
BaseStatsRow = matchup.BaseStatsRow
MoveRow = matchup.MoveRow
PokemonArg = matchup.PokemonArg

GRINDS = matchup.GRINDS
TRAINER_IV_STATEEXP = matchup.TRAINER_IV_STATEEXP
ALL_DAMAGE_TYPE_VALUES = matchup.ALL_DAMAGE_TYPE_VALUES


def normalize_name(value: str) -> str:
    return matchup._normalize_name(value)


def collapse_key(value: str) -> str:
    return matchup._collapse_key(value)


def asm_int(value: str) -> int:
    return matchup._asm_int(value)


def parse_const_values(path: Path) -> dict[str, int]:
    return matchup._parse_const_values(path)


def load_base_stats() -> dict[str, BaseStatsRow]:
    return matchup._load_base_stats()


def load_moves() -> dict[str, MoveRow]:
    return matchup._load_moves()


def load_type_constants() -> dict[str, int]:
    return matchup._load_type_constants()


def load_move_effect_constants() -> dict[str, int]:
    return matchup._load_move_effect_constants()


def load_weather_constants() -> dict[str, int]:
    return matchup._load_weather_constants()


def load_item_constants() -> dict[str, int]:
    return matchup._load_item_constants()


def load_item_names() -> dict[int, str]:
    return matchup._load_item_names()


def load_held_item_constants() -> dict[str, int]:
    return matchup._load_held_item_constants()


def load_can_evolve() -> dict[str, bool]:
    return matchup._load_can_evolve()


def load_move_display_names() -> dict[str, str]:
    return matchup._load_move_display_names()


def resolve_name(value: str, table: dict[str, object], label: str) -> str:
    return matchup._resolve_name(value, table, label)


def resolve_move(value: str) -> str:
    return matchup._resolve_move(value)


def resolve_item(value: str) -> int:
    return matchup._resolve_item(value)


def resolve_type_name(value: str) -> str:
    return matchup._resolve_type_name(value)


def resolve_type_pair(
    value: str | None,
    default_a: str,
    default_b: str,
) -> tuple[str, str]:
    return matchup._resolve_type_pair(value, default_a, default_b)


def canonical_item_constant(item_id: int) -> str:
    return matchup._canonical_item_constant(item_id)


def display_item(item_id: int) -> str:
    return matchup._display_item(item_id)


def display_species(species: str) -> str:
    return matchup._display_species(species)


def display_move(move: MoveRow) -> str:
    return matchup._display_move(move)


def weather_to_int(weather: str) -> int:
    return matchup._weather_to_int(weather)


def compute_stat(base: int, level: int, iv: int, statexp_term: int, is_hp: bool) -> int:
    return matchup.compute_stat(base, level, iv, statexp_term, is_hp)


def compute_hp(base: int, level: int, iv: int, statexp_term: int) -> int:
    return compute_stat(base, level, iv, statexp_term, is_hp=True)


def is_physical_type(type_id: int) -> bool:
    return type_id <= oracle.PHYSICAL_MAX


def is_physical_move(
    move: MoveRow,
    attacker: BaseStatsRow,
    attacker_types: tuple[str, str],
    level: int,
    iv: int,
    statexp: int,
    types: dict[str, int] | None = None,
) -> bool:
    return matchup._is_physical_move(
        move,
        attacker,
        attacker_types,
        level,
        iv,
        statexp,
        load_type_constants() if types is None else types,
    )


def damage_range(max_damage: int) -> tuple[int, int]:
    return matchup._damage_range(max_damage)


def pct(part: int, whole: int) -> int:
    return matchup._pct(part, whole)
