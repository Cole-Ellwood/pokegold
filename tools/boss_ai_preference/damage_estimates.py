from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from tools.damage_debugger import oracle


ROOT = Path(__file__).resolve().parents[2]
MOVES_PATH = ROOT / "data" / "moves" / "moves.asm"
BASE_STATS_DIR = ROOT / "data" / "pokemon" / "base_stats"
EVOS_ATTACKS_PATH = ROOT / "data" / "pokemon" / "evos_attacks.asm"

AVERAGE_DV = 8

TYPE_IDS = {
    "NORMAL": oracle.NORMAL,
    "FIGHTING": oracle.FIGHTING,
    "FLYING": oracle.FLYING,
    "POISON": oracle.POISON,
    "GROUND": oracle.GROUND,
    "ROCK": oracle.ROCK,
    "BUG": oracle.BUG,
    "GHOST": oracle.GHOST,
    "STEEL": oracle.STEEL,
    "FIRE": oracle.FIRE,
    "WATER": oracle.WATER,
    "GRASS": oracle.GRASS,
    "ELECTRIC": oracle.ELECTRIC,
    "PSYCHIC_TYPE": oracle.PSYCHIC_TYPE,
    "ICE": oracle.ICE,
    "DRAGON": oracle.DRAGON,
    "DARK": oracle.DARK,
}

ITEM_IDS = {
    "LIFE_ORB": oracle.HELD_LIFE_ORB,
    "SOFT_SAND": oracle.HELD_SOFT_SAND,
    "SHARP_BEAK": oracle.HELD_SHARP_BEAK,
    "POISON_BARB": oracle.HELD_POISON_BARB,
    "SILVERPOWDER": oracle.HELD_SILVERPOWDER,
    "SILVER_POWDER": oracle.HELD_SILVERPOWDER,
    "MYSTIC_WATER": oracle.HELD_MYSTIC_WATER,
    "TWISTEDSPOON": oracle.HELD_TWISTEDSPOON,
    "TWISTED_SPOON": oracle.HELD_TWISTEDSPOON,
    "BLACKBELT": oracle.HELD_BLACKBELT_I,
    "BLACK_BELT": oracle.HELD_BLACKBELT_I,
    "BLACKGLASSES": oracle.HELD_BLACKGLASSES,
    "BLACK_GLASSES": oracle.HELD_BLACKGLASSES,
    "PINK_BOW": oracle.HELD_PINK_BOW,
    "POLKADOT_BOW": oracle.HELD_POLKADOT_BOW,
    "NEVERMELTICE": oracle.HELD_NEVERMELTICE,
    "NEVER_MELT_ICE": oracle.HELD_NEVERMELTICE,
    "MAGNET": oracle.HELD_MAGNET,
    "SPELL_TAG": oracle.HELD_SPELL_TAG,
    "CHOICE_BAND": oracle.HELD_CHOICE_BAND,
    "MIRACLE_SEED": oracle.HELD_MIRACLE_SEED,
    "HARD_STONE": oracle.HELD_HARD_STONE,
    "CHOICE_SPECS": oracle.HELD_CHOICE_SPECS,
    "ASSAULT_VEST": oracle.HELD_ASSAULT_VEST,
    "CHARCOAL": oracle.HELD_CHARCOAL,
    "EXPERT_BELT": oracle.HELD_EXPERT_BELT,
    "MUSCLE_BAND": oracle.HELD_MUSCLE_BAND,
    "METAL_COAT": oracle.HELD_METAL_COAT,
    "DRAGON_FANG": oracle.HELD_DRAGON_FANG,
    "WISE_GLASSES": oracle.HELD_WISE_GLASSES,
    "EVOLITE": oracle.HELD_EVOLITE,
    "EVIOLITE": oracle.HELD_EVOLITE,
    "DRAGON_SCALE": oracle.HELD_DRAGON_SCALE,
    "METRONOME": oracle.HELD_METRONOME,
}

MOVE_EFFECT_IDS = {
    "EFFECT_MULTI_HIT": oracle.EFFECT_MULTI_HIT,
    "EFFECT_CONVERSION": oracle.EFFECT_CONVERSION,
    "EFFECT_SOLARBEAM": oracle.EFFECT_SOLARBEAM,
}

WEATHER_IDS = {
    "RAIN": oracle.WEATHER_RAIN,
    "SUN": oracle.WEATHER_SUN,
    "SUNNY": oracle.WEATHER_SUN,
    "SANDSTORM": oracle.WEATHER_SANDSTORM,
}

STATIC_DAMAGE_EFFECTS = {
    "EFFECT_LEVEL_DAMAGE",
    "EFFECT_STATIC_DAMAGE",
}

MULTI_HIT_EFFECTS = {
    "EFFECT_MULTI_HIT",
    "EFFECT_POISON_MULTI_HIT",
}


@dataclass(frozen=True)
class MoveData:
    name: str
    effect: str
    power: int
    type_name: str
    type_id: int
    accuracy: int


@dataclass(frozen=True)
class PokemonData:
    hp: int
    attack: int
    defense: int
    speed: int
    special_attack: int
    special_defense: int
    type_names: tuple[str, str]
    type_ids: tuple[int, int]


def attach_damage_estimates(fixtures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    annotated = copy.deepcopy(fixtures)
    for fixture in annotated:
        state = fixture.get("state", {})
        boss = state.get("boss", {}).get("active", {})
        player = state.get("player", {}).get("active", {})
        for action in fixture.get("actions", []):
            estimate = estimate_action_damage(action, boss, player, state.get("field", {}))
            if estimate is not None:
                action["damage_estimate"] = estimate
    return annotated


def estimate_action_damage(
    action: dict[str, Any],
    attacker: dict[str, Any],
    defender: dict[str, Any],
    field: dict[str, Any],
    *,
    defender_side: str = "player",
) -> dict[str, Any] | None:
    if action.get("kind") != "move":
        return None

    move = move_data().get(move_key(action))
    if move is None or move.power <= 0:
        return None

    attacker_species = attacker.get("species")
    defender_species = defender.get("species")
    attacker_level = attacker.get("level")
    defender_level = defender.get("level")
    if not all(
        isinstance(value, str)
        for value in (attacker_species, defender_species)
    ) or not all(isinstance(value, int) for value in (attacker_level, defender_level)):
        return None

    attacker_data = pokemon_data(attacker_species)
    defender_data = pokemon_data(defender_species)
    if attacker_data is None or defender_data is None:
        return None

    defender_max_hp = estimate_stat(defender_data.hp, defender_level, hp=True)
    if move.effect in STATIC_DAMAGE_EFFECTS:
        low_damage = static_damage(move, attacker_level)
        high_damage = low_damage
        note = "fixed-damage move"
    else:
        low_damage, high_damage = variable_damage_range(
            move=move,
            attacker_data=attacker_data,
            defender_data=defender_data,
            attacker_level=attacker_level,
            defender_level=defender_level,
            attacker_item=attacker.get("item", ""),
            attacker_hp=attacker.get("hp"),
            defender_item=defender.get("item", ""),
            defender_hp=defender.get("hp"),
            defender_status=defender.get("status"),
            defender_species=defender_species,
            field=field,
            defender_side=defender_side,
        )
        note = "rough estimate"

    low_percent = percent_of_hp(low_damage, defender_max_hp)
    high_percent = percent_of_hp(high_damage, defender_max_hp)
    label = f"about {low_percent}%"
    if high_percent != low_percent:
        label = f"about {low_percent}-{high_percent}%"
    if move.effect in MULTI_HIT_EFFECTS:
        two_hit = low_damage * 2
        five_hit = high_damage * 5
        label = f"about {percent_of_hp(two_hit, defender_max_hp)}-{percent_of_hp(five_hit, defender_max_hp)}%"
        note = "rough 2-5 hit estimate"

    return {
        "label": label,
        "low_percent": low_percent,
        "high_percent": high_percent,
        "target": defender_species,
        "target_hp": defender.get("hp", "unknown"),
        "basis": note,
    }


def estimate_move_damage(
    move_name: str,
    attacker: dict[str, Any],
    defender: dict[str, Any],
    field: dict[str, Any],
    *,
    defender_side: str = "boss",
) -> dict[str, Any] | None:
    return estimate_action_damage(
        {
            "id": f"move_{move_name.lower()}",
            "kind": "move",
            "name": display_move_name(move_name),
        },
        attacker,
        defender,
        field,
        defender_side=defender_side,
    )


def variable_damage_range(
    *,
    move: MoveData,
    attacker_data: PokemonData,
    defender_data: PokemonData,
    attacker_level: int,
    defender_level: int,
    attacker_item: str,
    attacker_hp: object,
    defender_item: object,
    defender_hp: object,
    defender_status: object,
    defender_species: str,
    field: dict[str, Any],
    defender_side: str,
) -> tuple[int, int]:
    physical = effective_move_is_physical(move, attacker_data, attacker_level)
    attack_base = attacker_data.attack if physical else attacker_data.special_attack
    defense_base = defender_data.defense if physical else defender_data.special_defense
    attack = estimate_stat(attack_base, attacker_level, hp=False)
    defense = estimate_stat(defense_base, defender_level, hp=False)
    defense = apply_screen_defense_boost(
        defense,
        physical=physical,
        field=field,
        defender_side=defender_side,
    )

    inputs = oracle.BattleInputs(
        attacker_level=attacker_level,
        move_bp=move.power,
        move_type=move.type_id,
        is_physical=physical,
        attacker_atk=attack,
        defender_def=defense,
        attacker_types=attacker_data.type_ids,
        defender_types=defender_data.type_ids,
        user_item=oracle_item_id(attacker_item),
        opponent_item=oracle_item_id(defender_item),
        can_evolve_defender=species_can_evolve(defender_species),
        is_selfdestruct=move.effect == "EFFECT_SELFDESTRUCT",
        attacker_below_third_hp=is_below_hp_fraction(attacker_hp, 1, 3),
        opponent_has_status=has_status(defender_status),
        opponent_above_half_hp=is_above_hp_fraction(defender_hp, 1, 2),
        weather=weather_id(field),
        move_effect=move_effect_id(move.effect),
    )
    high = max(0, oracle.predict_damage(inputs))
    low = 0 if high == 0 else max(1, (high * 85) // 100)
    return low, high


def static_damage(move: MoveData, attacker_level: int) -> int:
    if move.effect == "EFFECT_LEVEL_DAMAGE":
        return attacker_level
    return move.power


def effective_move_is_physical(
    move: MoveData,
    attacker_data: PokemonData,
    attacker_level: int,
) -> bool:
    if move.name == "OUTRAGE" and oracle.DRAGON in attacker_data.type_ids:
        attack = estimate_stat(attacker_data.attack, attacker_level, hp=False)
        special_attack = estimate_stat(attacker_data.special_attack, attacker_level, hp=False)
        return attack > special_attack
    return move.type_id <= oracle.PHYSICAL_MAX


def apply_screen_defense_boost(
    defense: int,
    *,
    physical: bool,
    field: dict[str, Any],
    defender_side: str,
) -> int:
    screens = str(field.get("screens", "")).lower()
    side = defender_side.lower()
    if physical and f"{side} reflect active" in screens:
        return defense * 2
    if not physical and f"{side} light screen active" in screens:
        return defense * 2
    return defense


def oracle_item_id(item: object) -> int:
    return ITEM_IDS.get(normalize_item_name(item), oracle.HELD_NONE)


def weather_id(field: dict[str, Any]) -> int:
    return WEATHER_IDS.get(normalize_item_name(field.get("weather", "")), oracle.WEATHER_NONE)


def move_effect_id(effect: str) -> int:
    return MOVE_EFFECT_IDS.get(effect, oracle.EFFECT_NORMAL_HIT)


def hp_percent(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    match = re.match(r"^\s*(\d+)%\s*$", value)
    if match is None:
        return None
    return int(match.group(1))


def is_below_hp_fraction(value: object, numerator: int, denominator: int) -> bool:
    percent = hp_percent(value)
    return percent is not None and percent * denominator < numerator * 100


def is_above_hp_fraction(value: object, numerator: int, denominator: int) -> bool:
    percent = hp_percent(value)
    return percent is not None and percent * denominator > numerator * 100


def has_status(value: object) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() not in {"", "none"}


def normalize_item_name(item: object) -> str:
    return str(item).upper().replace(" ", "_").replace("-", "_")


def species_can_evolve(species: str) -> bool:
    label = species_label(species)
    if not label:
        return False
    return species_can_evolve_by_label().get(label, False)


@lru_cache(maxsize=1)
def species_can_evolve_by_label() -> dict[str, bool]:
    result: dict[str, bool] = {}
    current_label: str | None = None
    can_evolve = False
    label_pattern = re.compile(r"^([A-Za-z0-9_]+)EvosAttacks:")
    for line in EVOS_ATTACKS_PATH.read_text(encoding="utf-8").splitlines():
        label_match = label_pattern.match(line)
        if label_match:
            if current_label is not None:
                result[current_label] = can_evolve
            current_label = label_match.group(1)
            can_evolve = False
            continue
        if current_label is None:
            continue
        stripped = line.strip()
        if stripped.startswith("db 0 ; no more evolutions"):
            result[current_label] = can_evolve
            current_label = None
            can_evolve = False
            continue
        if stripped.startswith("db EVOLVE_"):
            can_evolve = True
    if current_label is not None:
        result[current_label] = can_evolve
    return result


def species_label(species: str) -> str:
    special = {
        "Farfetch D": "FarfetchD",
        "Mr. Mime": "MrMime",
        "Nidoran F": "NidoranF",
        "Nidoran M": "NidoranM",
        "Ho Oh": "HoOh",
    }
    if species in special:
        return special[species]
    return "".join(part for part in re.split(r"[^A-Za-z0-9]+", species) if part)


def estimate_stat(base: int, level: int, *, hp: bool) -> int:
    value = (((base + AVERAGE_DV) * 2) * level) // 100
    if hp:
        return value + level + 10
    return value + 5


def percent_of_hp(damage: int, hp: int) -> int:
    if damage <= 0:
        return 0
    return max(1, round((damage / hp) * 100))


def move_key(action: dict[str, Any]) -> str:
    action_id = str(action.get("id", ""))
    if action_id.startswith("move_"):
        key = action_id.removeprefix("move_").upper()
    else:
        key = str(action.get("name", "")).upper()
    return MOVE_ALIASES.get(key, key)


MOVE_ALIASES = {
    "PSYCHIC": "PSYCHIC_M",
    "PSYCHIC M": "PSYCHIC_M",
}


def display_move_name(move_name: str) -> str:
    if move_name == "PSYCHIC_M":
        return "Psychic"
    if move_name == "DOUBLESLAP":
        return "DoubleSlap"
    return move_name.replace("_", " ").title()


@lru_cache(maxsize=1)
def move_data() -> dict[str, MoveData]:
    moves: dict[str, MoveData] = {}
    pattern = re.compile(
        r"^\s*move\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*,\s*(\d+)\s*,\s*([A-Z0-9_]+)\s*,\s*(\d+)"
    )
    for line in MOVES_PATH.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if not match:
            continue
        name, effect, power, type_name, accuracy = match.groups()
        type_id = TYPE_IDS.get(type_name)
        if type_id is None:
            continue
        moves[name] = MoveData(
            name=name,
            effect=effect,
            power=int(power),
            type_name=type_name,
            type_id=type_id,
            accuracy=int(accuracy),
        )
    return moves


@lru_cache(maxsize=None)
def pokemon_data(species: str) -> PokemonData | None:
    path = BASE_STATS_DIR / f"{species_slug(species)}.asm"
    if not path.exists():
        return None
    stats: tuple[int, int, int, int, int, int] | None = None
    type_names: tuple[str, str] | None = None
    stats_pattern = re.compile(
        r"^\s*db\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)"
    )
    type_pattern = re.compile(r"^\s*db\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*;\s*type")
    for line in path.read_text(encoding="utf-8").splitlines():
        if stats is None:
            stats_match = stats_pattern.match(line)
            if stats_match:
                stats = tuple(int(value) for value in stats_match.groups())
                continue
        type_match = type_pattern.match(line)
        if type_match:
            type_names = (type_match.group(1), type_match.group(2))
            break
    if stats is None or type_names is None:
        return None
    type_ids = tuple(TYPE_IDS[name] for name in type_names)
    return PokemonData(
        hp=stats[0],
        attack=stats[1],
        defense=stats[2],
        speed=stats[3],
        special_attack=stats[4],
        special_defense=stats[5],
        type_names=type_names,
        type_ids=type_ids,
    )


SPECIES_SLUG_ALIASES = {
    "mr_mime": "mr__mime",
}


def species_slug(species: str) -> str:
    slug = species.lower().replace(".", "").replace("'", "").replace(" ", "_")
    return SPECIES_SLUG_ALIASES.get(slug, slug)
