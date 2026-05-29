#!/usr/bin/env python3
"""Generate a source-derived mechanics reference for helper agents."""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "agent_navigation" / "hack_mechanics_reference.md"

TYPE_CONSTANTS = ROOT / "constants" / "type_constants.asm"
TYPE_MATCHUPS = ROOT / "data" / "types" / "type_matchups.asm"
MOVE_CONSTANTS = ROOT / "constants" / "move_constants.asm"
MOVE_NAMES = ROOT / "data" / "moves" / "names.asm"
MOVE_DATA = ROOT / "data" / "moves" / "moves.asm"
MOVE_CONTACT = ROOT / "data" / "moves" / "contact_flags.asm"
MOVE_EFFECTS = ROOT / "data" / "moves" / "effects.asm"
MOVE_PRIORITIES = ROOT / "data" / "moves" / "effects_priorities.asm"
ITEM_NAMES = ROOT / "data" / "items" / "names.asm"
ITEM_ATTRIBUTES = ROOT / "data" / "items" / "attributes.asm"
BASE_STATS_DIR = ROOT / "data" / "pokemon" / "base_stats"
POKEMON_CONSTANTS = ROOT / "constants" / "pokemon_constants.asm"
STAT_MULTIPLIERS = ROOT / "data" / "battle" / "stat_multipliers.asm"

ACTIVE_TYPES = (
    "NORMAL",
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
)

TYPE_FACTOR_LABELS = {
    0: "0",
    5: "1/2",
    10: "1",
    20: "2",
}

FACTOR_CONSTANTS = {
    "NO_EFFECT": 0,
    "NOT_VERY_EFFECTIVE": 5,
    "EFFECTIVE": 10,
    "SUPER_EFFECTIVE": 20,
}

FIXED_DAMAGE_EFFECTS = {
    "EFFECT_BIDE",
    "EFFECT_COUNTER",
    "EFFECT_LEVEL_DAMAGE",
    "EFFECT_MIRROR_COAT",
    "EFFECT_OHKO",
    "EFFECT_PRESENT",
    "EFFECT_PSYWAVE",
    "EFFECT_STATIC_DAMAGE",
    "EFFECT_SUPER_FANG",
}


@dataclass(frozen=True)
class Move:
    index: int
    constant: str
    display_name: str
    effect: str
    power: int
    type_name: str
    accuracy: int
    pp: int
    effect_chance: int
    contact: str


@dataclass(frozen=True)
class ItemAttribute:
    index: int
    constant: str
    display_name: str
    price: str
    held_effect: str
    parameter: str
    property_flags: str
    pocket: str
    field_menu: str
    battle_menu: str


@dataclass(frozen=True)
class SpeciesStats:
    index: int
    species: str
    hp: int
    attack: int
    defense: int
    speed: int
    special_attack: int
    special_defense: int
    type1: str
    type2: str
    item1: str
    item2: str

    @property
    def bst(self) -> int:
        return (
            self.hp
            + self.attack
            + self.defense
            + self.speed
            + self.special_attack
            + self.special_defense
        )


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_comment(line: str) -> str:
    return line.split(";", 1)[0].strip()


def display_token(token: str) -> str:
    token = token.strip()
    token = token.removesuffix("_TYPE")
    return token.replace("__", ". ").replace("_", " ").title()


def md(text: object) -> str:
    return str(text).replace("|", "\\|")


def parse_type_constants() -> tuple[dict[str, int], int]:
    values: dict[str, int] = {}
    special_threshold: int | None = None
    current = 0
    for raw in read(TYPE_CONSTANTS).splitlines():
        code = strip_comment(raw)
        if not code:
            continue
        match = re.match(r"const_def(?:\s+(\d+))?$", code)
        if match:
            current = int(match.group(1) or 0)
            continue
        match = re.match(r"const_next\s+(\d+)$", code)
        if match:
            current = int(match.group(1))
            continue
        if code == "DEF SPECIAL EQU const_value":
            special_threshold = current
            continue
        match = re.match(r"const\s+([A-Z0-9_]+)\b", code)
        if match:
            values[match.group(1)] = current
            current += 1
    if special_threshold is None:
        raise ValueError(f"{TYPE_CONSTANTS}: missing SPECIAL threshold")
    return values, special_threshold


def parse_type_matchups() -> tuple[dict[tuple[str, str], int], dict[tuple[str, str], int]]:
    chart: dict[tuple[str, str], int] = {}
    foresight_removed: dict[tuple[str, str], int] = {}
    after_foresight_sentinel = False
    for raw in read(TYPE_MATCHUPS).splitlines():
        code = strip_comment(raw)
        if not code:
            continue
        if code == "db -2":
            after_foresight_sentinel = True
            continue
        if code == "db -1":
            break
        match = re.match(r"db\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)", code)
        if not match:
            continue
        attacker, defender, factor = match.groups()
        value = FACTOR_CONSTANTS[factor]
        chart[(attacker, defender)] = value
        if after_foresight_sentinel:
            foresight_removed[(attacker, defender)] = value
    return chart, foresight_removed


def parse_li_names(path: Path) -> list[str]:
    names: list[str] = []
    for raw in read(path).splitlines():
        match = re.search(r'li\s+"([^"]+)"', raw)
        if match:
            names.append(match.group(1))
    return names


def parse_move_constants() -> list[str]:
    constants: list[str] = []
    for raw in read(MOVE_CONSTANTS).splitlines():
        code = strip_comment(raw)
        if code.startswith("DEF NUM_ATTACKS"):
            break
        match = re.match(r"const\s+([A-Z0-9_]+)\b", code)
        if match:
            constant = match.group(1)
            if constant != "NO_MOVE":
                constants.append(constant)
    return constants


def parse_contact_flags() -> dict[str, str]:
    flags: dict[str, str] = {}
    for raw in read(MOVE_CONTACT).splitlines():
        match = re.match(r"\s*db\s+(TRUE|FALSE)\s*;\s*([A-Z0-9_]+)", raw)
        if match:
            flag, move = match.groups()
            flags[move] = "yes" if flag == "TRUE" else "no"
    return flags


def parse_moves(type_values: dict[str, int], special_threshold: int) -> list[Move]:
    constants = parse_move_constants()
    names = parse_li_names(MOVE_NAMES)
    contacts = parse_contact_flags()
    moves: list[Move] = []
    move_line = re.compile(
        r"\s*move\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*,\s*"
        r"(\d+)\s*,\s*([A-Z0-9_]+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)"
    )
    for raw in read(MOVE_DATA).splitlines():
        match = move_line.match(raw)
        if not match:
            continue
        constant, effect, power, type_name, accuracy, pp, chance = match.groups()
        index = len(moves) + 1
        expected = constants[index - 1] if index - 1 < len(constants) else constant
        if constant != expected:
            raise ValueError(
                f"{MOVE_DATA}: move row {index:02x} is {constant}, expected {expected}"
            )
        display_name = names[index - 1] if index - 1 < len(names) else display_token(constant)
        moves.append(
            Move(
                index=index,
                constant=constant,
                display_name=display_name,
                effect=effect,
                power=int(power),
                type_name=type_name,
                accuracy=int(accuracy),
                pp=int(pp),
                effect_chance=int(chance),
                contact=contacts.get(constant, "unknown"),
            )
        )
    return moves


def move_category(move: Move, type_values: dict[str, int], special_threshold: int) -> str:
    if move.power == 0:
        return "status"
    if move.effect in FIXED_DAMAGE_EFFECTS:
        return "fixed"
    if move.constant == "OUTRAGE":
        return "special*"
    type_value = type_values[move.type_name]
    return "special" if type_value >= special_threshold else "physical"


def parse_item_attributes() -> list[ItemAttribute]:
    names = ["NO ITEM", *parse_li_names(ITEM_NAMES)]
    attributes: list[ItemAttribute] = []
    pending_constant: str | None = None
    attr_line = re.compile(
        r"\s*item_attribute\s+([^,]+),\s*([A-Z0-9_]+),\s*([^,]+),\s*"
        r"([^,]+),\s*([^,]+),\s*([A-Z0-9_]+),\s*([A-Z0-9_]+)"
    )
    for raw in read(ITEM_ATTRIBUTES).splitlines():
        comment = re.match(r"\s*;\s*([A-Z0-9_$() #]+)", raw)
        if comment:
            pending_constant = comment.group(1).strip()
            if pending_constant.endswith("("):
                # `; MOON_STONE (removed YYYY-MM-DD; stub slot)` style: the
                # regex stops at the first lowercase char inside the parens
                # and captures `MOON_STONE (`. Drop the dangling open-paren.
                pending_constant = pending_constant.rsplit(" (", 1)[0]
            continue
        match = attr_line.match(raw)
        if not match:
            continue
        index = len(attributes) + 1
        price, held, param, prop, pocket, field_menu, battle_menu = [
            value.strip() for value in match.groups()
        ]
        constant = pending_constant or f"${index:02x}"
        display_name = names[index] if index < len(names) else constant
        attributes.append(
            ItemAttribute(
                index=index,
                constant=constant,
                display_name=display_name,
                price=price,
                held_effect=held,
                parameter=param,
                property_flags=prop,
                pocket=pocket,
                field_menu=field_menu,
                battle_menu=battle_menu,
            )
        )
        pending_constant = None
    return attributes


def parse_pokemon_order() -> dict[str, int]:
    order: dict[str, int] = {}
    current = 1
    for raw in read(POKEMON_CONSTANTS).splitlines():
        code = strip_comment(raw)
        if code.startswith("DEF NUM_POKEMON"):
            break
        match = re.match(r"const_def\s+(\d+)$", code)
        if match:
            current = int(match.group(1))
            continue
        match = re.match(r"const\s+([A-Z0-9_]+)\b", code)
        if match:
            order[match.group(1)] = current
            current += 1
    return order


def parse_base_stats_file(path: Path) -> SpeciesStats:
    species: str | None = None
    stats: tuple[int, int, int, int, int, int] | None = None
    types: tuple[str, str] | None = None
    items: tuple[str, str] | None = None
    for raw in read(path).splitlines():
        code = strip_comment(raw)
        if not code:
            continue
        if species is None:
            match = re.match(r"db\s+([A-Z0-9_]+)\b", code)
            if match:
                species = match.group(1)
            continue
        if stats is None:
            match = re.match(
                r"db\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)",
                code,
            )
            if match:
                stats = tuple(int(value) for value in match.groups())  # type: ignore[assignment]
            continue
        if types is None:
            match = re.match(r"db\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*$", code)
            if match:
                types = (match.group(1), match.group(2))
            continue
        if items is None:
            match = re.match(r"db\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*$", code)
            if match:
                items = (match.group(1), match.group(2))
                break
    if species is None or stats is None or types is None or items is None:
        raise ValueError(f"{path}: could not parse base stats")
    return SpeciesStats(0, species, *stats, *types, *items)


def parse_base_stats() -> list[SpeciesStats]:
    order = parse_pokemon_order()
    parsed = [parse_base_stats_file(path) for path in BASE_STATS_DIR.glob("*.asm")]
    rows: list[SpeciesStats] = []
    for row in parsed:
        index = order.get(row.species)
        if index is None:
            continue
        rows.append(
            SpeciesStats(
                index=index,
                species=row.species,
                hp=row.hp,
                attack=row.attack,
                defense=row.defense,
                speed=row.speed,
                special_attack=row.special_attack,
                special_defense=row.special_defense,
                type1=row.type1,
                type2=row.type2,
                item1=row.item1,
                item2=row.item2,
            )
        )
    return sorted(rows, key=lambda row: row.index)


def type_factor(chart: dict[tuple[str, str], int], attacker: str, defender: str) -> int:
    return chart.get((attacker, defender), 10)


def render_type_categories(type_values: dict[str, int], special_threshold: int) -> list[str]:
    physical = [
        display_token(type_name)
        for type_name in ACTIVE_TYPES
        if type_values[type_name] < special_threshold
    ]
    special = [
        display_token(type_name)
        for type_name in ACTIVE_TYPES
        if type_values[type_name] >= special_threshold
    ]
    return [
        "| Category | Types |",
        "| --- | --- |",
        f"| Physical | {', '.join(physical)} |",
        f"| Special | {', '.join(special)} |",
    ]


def render_type_chart(chart: dict[tuple[str, str], int]) -> list[str]:
    header = "| Attack \\ Defend | " + " | ".join(display_token(t) for t in ACTIVE_TYPES) + " |"
    divider = "| --- | " + " | ".join("---" for _ in ACTIVE_TYPES) + " |"
    rows = [header, divider]
    for attacker in ACTIVE_TYPES:
        cells = [
            TYPE_FACTOR_LABELS[type_factor(chart, attacker, defender)]
            for defender in ACTIVE_TYPES
        ]
        rows.append(f"| {display_token(attacker)} | " + " | ".join(cells) + " |")
    return rows


def render_move_table(
    moves: list[Move],
    type_values: dict[str, int],
    special_threshold: int,
) -> list[str]:
    rows = [
        "| ID | Move | Const | Type | Category | Power | Acc | PP | Effect | Chance | Contact |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for move in moves:
        rows.append(
            "| "
            + " | ".join(
                [
                    f"{move.index:02X}",
                    md(move.display_name),
                    f"`{move.constant}`",
                    display_token(move.type_name),
                    move_category(move, type_values, special_threshold),
                    str(move.power),
                    str(move.accuracy),
                    str(move.pp),
                    f"`{move.effect}`",
                    str(move.effect_chance),
                    move.contact,
                ]
            )
            + " |"
        )
    return rows


def render_item_table(items: list[ItemAttribute]) -> list[str]:
    rows = [
        "| ID | Item | Const/Slot | Held Effect | Param | Pocket | Field | Battle |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in items:
        rows.append(
            "| "
            + " | ".join(
                [
                    f"{item.index:02X}",
                    md(item.display_name),
                    f"`{md(item.constant)}`",
                    f"`{item.held_effect}`",
                    md(item.parameter),
                    f"`{item.pocket}`",
                    f"`{item.field_menu}`",
                    f"`{item.battle_menu}`",
                ]
            )
            + " |"
        )
    return rows


def render_species_table(species_rows: list[SpeciesStats]) -> list[str]:
    rows = [
        "| ID | Species | Types | HP | Atk | Def | Spe | SpA | SpD | BST | Wild Items |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in species_rows:
        types = display_token(row.type1)
        if row.type2 != row.type1:
            types += f"/{display_token(row.type2)}"
        rows.append(
            "| "
            + " | ".join(
                [
                    f"{row.index:03d}",
                    display_token(row.species),
                    types,
                    str(row.hp),
                    str(row.attack),
                    str(row.defense),
                    str(row.speed),
                    str(row.special_attack),
                    str(row.special_defense),
                    str(row.bst),
                    f"`{row.item1}`, `{row.item2}`",
                ]
            )
            + " |"
        )
    return rows


def render_reference() -> str:
    type_values, special_threshold = parse_type_constants()
    chart, foresight = parse_type_matchups()
    moves = parse_moves(type_values, special_threshold)
    items = parse_item_attributes()
    species_rows = parse_base_stats()

    lines: list[str] = [
        "# Hack Mechanics Reference",
        "",
        "Audience: future Codex/helper agents working in this repo.",
        "",
        "This is the fast, source-derived mechanics reference. Use it before making",
        "any claim about type matchups, move category, move data, held items, or",
        "Pokemon stats in this hack. If this doc disagrees with source, source wins",
        "and this doc must be regenerated or corrected in the same change.",
        "",
        "**Maintenance rule:** whenever a mechanics change touches a table or rule",
        "covered here, update this reference in the same commit. Prefer rerunning",
        "`python scripts/generate_hack_mechanics_reference.py` so the big tables",
        "come from source instead of memory.",
        "",
        "## Table Of Contents",
        "",
        "- [Fast Rules That Prevent Bad Guesses](#fast-rules-that-prevent-bad-guesses)",
        "- [Source Files To Trust](#source-files-to-trust)",
        "- [Physical/Special Split](#physicalspecial-split)",
        "- [Stat Math And Boosts](#stat-math-and-boosts)",
        "- [Type Matchup Chart](#type-matchup-chart)",
        "- [Dragon Type Passives](#dragon-type-passives)",
        "- [Move Effects To Check First](#move-effects-to-check-first)",
        "- [All Move Data](#all-move-data)",
        "- [Held Items And Item Attributes](#held-items-and-item-attributes)",
        "- [Pokemon Base Stats And Types](#pokemon-base-stats-and-types)",
        "- [Learnsets, TMs, Trainers, And Boss AI Data](#learnsets-tms-trainers-and-boss-ai-data)",
        "- [Fixture And Helper-Note Audit Rules](#fixture-and-helper-note-audit-rules)",
        "",
        "## Fast Rules That Prevent Bad Guesses",
        "",
        "- Dark is special. Crunch, Pursuit, Bite, Thief, Faint Attack, and Beat Up",
        "  use Special Attack unless a move has a fixed/special-case effect.",
        "- Ghost, Poison, Bug, Rock, Ground, Steel, Flying, Fighting, and Normal are",
        "  physical types.",
        "- Fire, Water, Grass, Electric, Psychic, Ice, Dragon, and Dark are special",
        "  types.",
        "- This hack keeps the Gen 2 type-based category split. Do not use modern",
        "  per-move physical/special memory.",
        "- Outrage is the special Dragon exception: Dragon-typed users run Outrage",
        "  physically only when current Attack is greater than current Special",
        "  Attack. Ties and non-Dragon users keep it special.",
        "- Dragon Dance is not plain +Atk here. Its script uses `bestattackup`, which",
        "  raises the user's current higher offensive stat, then raises Speed.",
        "  Ties raise Attack.",
        "- Stat stages multiply the already-calculated battle stat, not the base",
        "  stat. A base 100 Attack Pokemon at +2 is stronger than a base 200 Attack",
        "  Pokemon at +0 because +2 doubles the computed stat after level, DV, Stat",
        "  Exp, and the +5 floor.",
        "- Steel/Dragon Steelix does not resist Ground. Ground is super-effective on",
        "  Steel and neutral on Dragon, so Ground is 2x into Steelix.",
        "- Grass is neutral into Flying in this hack. Do not call Giga Drain resisted",
        "  into Pidgey solely because of Flying.",
        "- Fire is 2x into Ice/Ground Piloswine, not 4x.",
        "- Dark hits Steel neutrally in this hack; Ghost does no damage to Steel.",
        "- Dragon's Majesty is offensive: Dragon attackers convert type-chart",
        "  immunities to resistances for damaging non-fixed-damage moves.",
        "- Dragon's defensive passive is Imperial Scales: Dragon defenders reduce",
        "  non-super-effective hits, half Dragon by 2/3 and full Dragon by 1/2.",
        "",
        "## Source Files To Trust",
        "",
        "| Question | Source |",
        "| --- | --- |",
        "| Type constants and physical/special threshold | `constants/type_constants.asm` |",
        "| Type matchups | `data/types/type_matchups.asm` |",
        "| Move power/type/accuracy/PP/effect | `data/moves/moves.asm` |",
        "| Move effect scripts | `data/moves/effects.asm` and `engine/battle/effect_commands.asm` |",
        "| Move priority | `data/moves/effects_priorities.asm` plus `constants/battle_constants.asm` |",
        "| Contact flags | `data/moves/contact_flags.asm` |",
        "| Held item constants | `constants/item_constants.asm` |",
        "| Item attributes | `data/items/attributes.asm` |",
        "| Late-gen held item behavior | `engine/battle/late_gen_held_items.asm` |",
        "| Type passive behavior | `engine/battle/type_passive_damage_mods.asm` |",
        "| Base stats/types/wild items/TM learnsets | `data/pokemon/base_stats/*.asm` |",
        "| Level-up moves/evolutions | `data/pokemon/evos_attacks.asm` |",
        "| Trainer rosters | `data/trainers/parties.asm` |",
        "| Boss AI preference fixtures | `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json` |",
        "",
        "## Physical/Special Split",
        "",
        "The category is decided by the move type constant. Types with constants",
        f"below `SPECIAL` ({special_threshold}) are physical; types at or above it are special.",
        "",
        *render_type_categories(type_values, special_threshold),
        "",
        "Outrage exception source: `TypePassive_GetEffectiveMoveCategory_Far` in",
        "`engine/battle/type_passive_damage_mods.asm`.",
        "",
        "## Stat Math And Boosts",
        "",
        "Source: `engine/pokemon/move_mon.asm`, `engine/battle/effect_commands.asm`,",
        f"and `{STAT_MULTIPLIERS.relative_to(ROOT).as_posix()}`.",
        "",
        "Computed stats use Gen 2 DVs only. Stat Exp has been removed from this",
        "hack (every `CalcMonStats` caller passes `b=FALSE`), so no Pokemon -",
        "player or trainer - gains a stat-exp bonus:",
        "",
        "```text",
        "Non-HP = floor((2 * (base + DV)) * level / 100) + 5",
        "HP     = floor((2 * (base + HP_DV)) * level / 100) + level + 10",
        "```",
        "",
        "Battle stat stages then multiply the computed battle stat:",
        "",
        "| Stage | Multiplier | Stage | Multiplier |",
        "| --- | --- | --- | --- |",
        "| +1 | 1.5x | -1 | 0.66x |",
        "| +2 | 2.0x | -2 | 0.5x |",
        "| +3 | 2.5x | -3 | 0.4x |",
        "| +4 | 3.0x | -4 | 0.33x |",
        "| +5 | 3.5x | -5 | 0.28x |",
        "| +6 | 4.0x | -6 | 0.25x |",
        "",
        "The stored level is base-7 encoded: `BASE_STAT_LEVEL = 7` means +0,",
        "`MAX_STAT_LEVEL = 13` means +6.",
        "",
        "## Type Matchup Chart",
        "",
        "Single-type matchup values below come directly from `data/types/type_matchups.asm`.",
        "For dual types, multiply both defender columns. Foresight only removes the",
        "Normal/Fighting into Ghost immunities listed after the `db -2` sentinel.",
        "",
        *render_type_chart(chart),
        "",
        "Foresight-specific no-effect rows:",
        "",
        "| Attack | Defend | Normal Rule | With Foresight |",
        "| --- | --- | --- | --- |",
    ]

    for (attacker, defender), factor in sorted(foresight.items()):
        lines.append(
            f"| {display_token(attacker)} | {display_token(defender)} | "
            f"{TYPE_FACTOR_LABELS[factor]} | 1 |"
        )

    lines.extend(
        [
            "",
            "## Dragon Type Passives",
            "",
            "Source: `engine/battle/type_passive_damage_mods.asm`,",
            "`engine/battle/effect_commands.asm`, and",
            "`engine/battle/ai/boss_platform.asm`.",
            "",
            "- Dragon's Majesty is an offensive damage rule. If a damaging",
            "  non-fixed-damage move would hit a type-chart immunity and the attacker",
            "  has Dragon type contribution, the immunity is converted from 0x to",
            "  0.5x. Fixed-damage and special-case effects such as Super Fang,",
            "  Psywave, Counter, Mirror Coat, Bide, and Future Sight are excluded.",
            "- The boss-AI no-item type-matchup helpers mirror Dragon's Majesty for",
            "  type-only scoring: `BossAI_ApplyDragonsMajestyNoItem` converts a",
            "  Dragon attacker's immunity result to not-very-effective. Use this",
            "  when judging whether a switch is truly immune to a public Dragon-side",
            "  threat.",
            "- Imperial Scales is the Dragon defensive damage rule. If the defender has",
            "  Dragon type contribution and the final matchup is not",
            "  super-effective, damage is reduced by 2/3 for half Dragon and by",
            "  1/2 for full Dragon.",
            "",
            "## Move Effects To Check First",
            "",
            "- `DragonDance` script: `bestattackup`, then Speed up. Source:",
            "  `data/moves/effects.asm`.",
            "- `BattleCommand_BestAttackUp`: compares current Attack and Special Attack;",
            "  if SpA is greater it raises SpA, otherwise Attack. Source:",
            "  `engine/battle/effect_commands.asm`.",
            "- `CalmMind`: Special Attack +1 and Special Defense +1.",
            "- `QuiverDance`: Special Attack +1, Special Defense +1, and Speed +1.",
            "- Priority table: Protect/Endure use priority value 3; shared",
            "  `EFFECT_PRIORITY_HIT` moves use priority value 2; base priority is 1.",
            "  That means Quick Attack, Mach Punch, and ExtremeSpeed share the same",
            "  priority tier in this hack.",
            "- Thunder in rain skips the accuracy check in `BattleCommand_CheckHit`.",
            "- Sleep, freeze, burn, paralysis, Substitute, weather, hazards, and type",
            "  passives are summarized in `docs/agent_navigation/gen2_vs_modern_mechanics.md`,",
            "  but source files above are authoritative.",
            "",
            "## All Move Data",
            "",
            "`special*` means Outrage: special by Dragon type unless the Outrage",
            "exception makes it physical for a Dragon user with current Atk > SpA.",
            "`fixed` means the move's main damage is fixed/special-case and should not",
            "be reasoned about as ordinary Atk/SpA damage.",
            "",
            *render_move_table(moves, type_values, special_threshold),
            "",
            "## Held Items And Item Attributes",
            "",
            "This table is the item attribute table, not a full prose description of every",
            "engine effect. For behavior, check `engine/battle/late_gen_held_items.asm`,",
            "`engine/items/item_effects.asm`, and `engine/battle/effect_commands.asm`.",
            "",
            *render_item_table(items),
            "",
            "## Pokemon Base Stats And Types",
            "",
            "This table comes from `data/pokemon/base_stats/*.asm`. TM/HM compatibility",
            "lives in each same file after the stat/type/item rows.",
            "",
            *render_species_table(species_rows),
            "",
            "## Learnsets, TMs, Trainers, And Boss AI Data",
            "",
            "- Level-up moves and evolutions: `data/pokemon/evos_attacks.asm`.",
            "- TM/HM move list: `data/moves/tmhm_moves.asm` and",
            "  `constants/item_constants.asm`.",
            "- Per-species TM/HM compatibility: each `data/pokemon/base_stats/*.asm` file.",
            "- Trainer parties: `data/trainers/parties.asm`.",
            "- Boss AI preference fixtures: `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`.",
            "- Boss AI labels and teaching notes must use this reference when they mention",
            "  weakness, resistance, immunity, physical/special category, stat stages, or",
            "  move/item behavior.",
            "",
            "## Fixture And Helper-Note Audit Rules",
            "",
            "When editing fixtures, labels, or helper notes:",
            "",
            "1. Never write `super-effective`, `resisted`, `immune`, `physical`, or",
            "   `special` from memory. Check the tables above or the source files.",
            "2. If a fixture is about battle judgment rather than mechanics, word the",
            "   note that way. Example: Magnitude into Miltank is meaningful neutral",
            "   damage, not super-effective Ground damage.",
            "3. If a setup move changes a stat stage, describe the stage and the affected",
            "   computed battle stat. Do not describe it as doubling base stats.",
            "4. If a mechanics change touches any source listed in [Source Files To Trust]",
            "   rerun this generator and update any helper note that paraphrases the rule.",
            "5. Run `python tools/audit/check_mechanics_docs_and_fixtures.py` after fixture",
            "   or helper-doc changes that mention mechanics.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    output = args.output
    if not output.is_absolute():
        output = ROOT / output
    rendered = render_reference()

    if args.check:
        if not output.exists():
            print(f"missing generated reference: {output}", file=sys.stderr)
            return 1
        current = output.read_text(encoding="utf-8")
        if current != rendered:
            diff = difflib.unified_diff(
                current.splitlines(),
                rendered.splitlines(),
                fromfile=str(output),
                tofile="generated",
                lineterm="",
            )
            print("\n".join(diff), file=sys.stderr)
            return 1
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
