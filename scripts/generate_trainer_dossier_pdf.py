#!/usr/bin/env python3
"""Generate a Pokemon Showdown-style PDF of every notable trainer team.

This is a player-facing reference doc, not a dev artifact. The PDF covers:

  - Johto gym leaders (8)
  - Elite Four + Champion (5)
  - Kanto gym leaders (8)
  - Silver — every Rival fight, with the three starter-pick branches
  - Team Rocket admins (Petrel / Proton / Ariana / Archer) — Mahogany +
    Radio Tower fights, no grunts
  - Red — Mt. Silver Summit

Each trainer is rendered with:

  - Header with type theme, badge / fight slot, and location
  - Per-Pokemon card (Showdown team-builder style) with:
      * Name, level, held item
      * Type pills (Showdown colour palette)
      * Full 4-move set
      * Six base stats with horizontal bars + numeric values (HP/Atk/Def/SpA/SpD/Spe)
      * Base stat total

Reads (everything is parsed live from source — no committed JSON):
  data/trainers/parties.asm
  data/pokemon/base_stats/<species>.asm

Writes:
  docs/trainer_dossier.pdf

Usage (from repo root, Windows or WSL):

    # one-time install of the two non-stdlib deps
    python -m pip install reportlab Pillow

    # regenerate the PDF
    python scripts/generate_trainer_dossier_pdf.py

The script auto-resolves repo root from its own location, so it works from any
cwd. There is no config or CLI flag — the trainer list is hard-coded near the
top of this file. Edit the meta lists (JOHTO_GYMS / ELITE_FOUR / KANTO_GYMS /
RIVAL_FIGHTS / ROCKET_ADMINS / RED_FIGHT) if a future hack adds or reorders
trainers.

When to re-run:
  - Any party change in data/trainers/parties.asm for the listed trainers.
  - Any base-stat change in data/pokemon/base_stats/ for a species used.
  - Cosmetic tweaks to layout (card sizes, colours) — edit and re-run.

The PDF is plain Python + reportlab; rebuilding does not require a ROM build.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
PARTIES = ROOT / "data" / "trainers" / "parties.asm"
BASE_STATS_DIR = ROOT / "data" / "pokemon" / "base_stats"
TRAINER_DVS = ROOT / "data" / "trainers" / "dvs.asm"
EVOS_ATTACKS = ROOT / "data" / "pokemon" / "evos_attacks.asm"
OUT_PDF = ROOT / "docs" / "trainer_dossier.pdf"

# ---------------------------------------------------------------- meta tables

JOHTO_GYMS = [
    ("Falkner",  "FalknerGroup",  1, "Flying",   "Violet City",     "Zephyr Badge"),
    ("Bugsy",    "BugsyGroup",    2, "Bug",      "Azalea Town",     "Hive Badge"),
    ("Whitney",  "WhitneyGroup",  3, "Normal",   "Goldenrod City",  "Plain Badge"),
    ("Morty",    "MortyGroup",    4, "Ghost",    "Ecruteak City",   "Fog Badge"),
    ("Chuck",    "ChuckGroup",    5, "Fighting", "Cianwood City",   "Storm Badge"),
    ("Jasmine",  "JasmineGroup",  6, "Steel",    "Olivine City",    "Mineral Badge"),
    ("Pryce",    "PryceGroup",    7, "Ice",      "Mahogany Town",   "Glacier Badge"),
    ("Clair",    "ClairGroup",    8, "Dragon",   "Blackthorn City", "Rising Badge"),
]

ELITE_FOUR = [
    ("Will",   "WillGroup",     "E4-1",      "Psychic",  "Indigo Plateau"),
    ("Koga",   "KogaGroup",     "E4-2",      "Poison",   "Indigo Plateau"),
    ("Bruno",  "BrunoGroup",    "E4-3",      "Fighting", "Indigo Plateau"),
    ("Karen",  "KarenGroup",    "E4-4",      "Dark",     "Indigo Plateau"),
    ("Lance",  "ChampionGroup", "Champion",  "Dragon",   "Indigo Plateau"),
]

KANTO_GYMS = [
    ("Brock",     "BrockGroup",    9,  "Rock",     "Pewter City",     "Boulder Badge"),
    ("Misty",     "MistyGroup",    10, "Water",    "Cerulean City",   "Cascade Badge"),
    ("Lt. Surge", "LtSurgeGroup",  11, "Electric", "Vermilion City",  "Thunder Badge"),
    ("Erika",     "ErikaGroup",    12, "Grass",    "Celadon City",    "Rainbow Badge"),
    ("Janine",    "JanineGroup",   13, "Poison",   "Fuchsia City",    "Soul Badge"),
    ("Sabrina",   "SabrinaGroup",  14, "Psychic",  "Saffron City",    "Marsh Badge"),
    ("Blaine",    "BlaineGroup",   15, "Fire",     "Seafoam Islands", "Volcano Badge"),
    ("Blue",      "BlueGroup",     16, "Various",  "Viridian City",   "Earth Badge"),
]

# Rival (Silver) fights. Each entry is a single fight; for each one the parties
# file holds three consecutive trainer entries (one per starter the player picked).
# Convention: parties.asm entry order is (1) Bayleef line / (2) Quilava line /
# (3) Croconaw line, which corresponds to player picking Totodile / Chikorita /
# Cyndaquil respectively (Silver always picks the type-advantageous starter).
# fight_no is the global index across both groups, used in the fight title.
RIVAL_FIGHTS = [
    # (group_name, fight_idx_in_group, fight_no, label, location)
    ("Rival1Group", 1, 1, "Cherrygrove City",        "Cherrygrove City — intro scout"),
    ("Rival1Group", 2, 2, "Azalea Town",             "Azalea Town — outside Slowpoke Well"),
    ("Rival1Group", 3, 3, "Burned Tower",            "Burned Tower 1F"),
    ("Rival1Group", 4, 4, "Goldenrod Underground",   "Underground Path — Switch Room"),
    ("Rival1Group", 5, 5, "Victory Road",            "Victory Road — pre-Lance"),
    ("Rival2Group", 1, 6, "Mt. Moon Square",         "Mt. Moon — post-Lance, first Kanto fight"),
    ("Rival2Group", 2, 7, "Indigo Plateau",          "Indigo Plateau Pokecenter 1F — pre-Mt. Silver"),
]

# Team Rocket admins. Vanilla GS doesn't print Petrel/Proton/Ariana/Archer names
# in script text; the names below are the HGSS-canonical attributions, inferred
# from signature Pokemon and dialog ("I'm a fortress" → Petrel) and confirmed
# against fight order. If wrong, edit this table — nothing else relies on it.
ROCKET_ADMINS = [
    # (group, member_idx, admin_name, fight_label, location, type_theme)
    ("ExecutiveMGroup", 4, "Proton", "Mahogany Hideout B3F",
        "Team Rocket Hideout — Mahogany Town, B3F", "Poison"),
    ("ExecutiveFGroup", 2, "Ariana", "Mahogany Hideout B2F",
        "Team Rocket Hideout — Mahogany Town, B2F", "Poison"),
    ("ExecutiveMGroup", 3, "Petrel", "Radio Tower 5F (disguised)",
        "Goldenrod Radio Tower 5F — disguised as the Director", "Poison"),
    ("ExecutiveMGroup", 1, "Archer", "Radio Tower 5F",
        "Goldenrod Radio Tower 5F — Rocket leader", "Dark"),
    ("ExecutiveFGroup", 1, "Ariana", "Radio Tower 5F",
        "Goldenrod Radio Tower 5F — second confrontation", "Poison"),
    ("ExecutiveMGroup", 2, "Petrel", "Radio Tower 4F",
        "Goldenrod Radio Tower 4F — \"I'm the Rocket fortress\"", "Poison"),
]

# Red — the Champion at Mt. Silver Summit. Single fight.
RED_FIGHT = ("RedGroup", 1, "Red", "Mt. Silver Summit",
             "Mt. Silver — Silver Cave, Summit", "Various")

TYPE_COLORS = {
    "Normal":   "#A8A878",
    "Fire":     "#F08030",
    "Water":    "#6890F0",
    "Grass":    "#78C850",
    "Electric": "#F8D030",
    "Ice":      "#98D8D8",
    "Fighting": "#C03028",
    "Poison":   "#A040A0",
    "Ground":   "#E0C068",
    "Flying":   "#A890F0",
    "Psychic":  "#F85888",
    "Bug":      "#A8B820",
    "Rock":     "#B8A038",
    "Ghost":    "#705898",
    "Dragon":   "#7038F8",
    "Dark":     "#705848",
    "Steel":    "#B8B8D0",
    "Various":  "#68A090",
}

# --------------------------------------------------------------- name helpers

def title_case_constant(name: str) -> str:
    """ARIADOS -> Ariados, MR__MIME -> Mr. Mime, HO_OH -> Ho-Oh, etc."""
    if name == "MR__MIME": return "Mr. Mime"
    if name == "HO_OH": return "Ho-Oh"
    if name == "FARFETCH_D": return "Farfetch'd"
    if name == "NIDORAN_F": return "Nidoran F"
    if name == "NIDORAN_M": return "Nidoran M"
    if name == "PORYGON2": return "Porygon2"
    return " ".join(part.capitalize() for part in name.split("_") if part)


def title_case_move(name: str) -> str:
    """THUNDERBOLT -> Thunderbolt, DRAGON_DANCE -> Dragon Dance, PSYCHIC_M -> Psychic."""
    if name == "PSYCHIC_M": return "Psychic"
    if name == "NO_MOVE": return "—"
    if name == "DOUBLEEDGE": return "Double-Edge"
    if name == "DOUBLE_EDGE": return "Double-Edge"
    if name == "HI_JUMP_KICK": return "Hi Jump Kick"
    if name == "FAINT_ATTACK": return "Faint Attack"
    if name == "DOUBLESLAP": return "Doubleslap"
    if name == "EXTREMESPEED": return "Extreme Speed"
    if name == "SOLARBEAM": return "SolarBeam"
    if name == "DRAGONBREATH": return "DragonBreath"
    if name == "THUNDERPUNCH": return "ThunderPunch"
    if name == "FIRE_BLAST": return "Fire Blast"
    if name == "ICE_BEAM": return "Ice Beam"
    if name == "ICE_PUNCH": return "Ice Punch"
    if name == "FIRE_PUNCH": return "Fire Punch"
    if name == "MACH_PUNCH": return "Mach Punch"
    if name == "FOCUS_PUNCH": return "Focus Punch"
    if name == "QUICK_ATTACK": return "Quick Attack"
    if name == "WING_ATTACK": return "Wing Attack"
    if name == "ROCK_SLIDE": return "Rock Slide"
    if name == "STEEL_WING": return "Steel Wing"
    if name == "IRON_TAIL": return "Iron Tail"
    if name == "RAPID_SPIN": return "Rapid Spin"
    if name == "SLUDGE_BOMB": return "Sludge Bomb"
    if name == "GIGA_DRAIN": return "Giga Drain"
    if name == "LEECH_SEED": return "Leech Seed"
    if name == "LEECH_LIFE": return "Leech Life"
    if name == "SLEEP_POWDER": return "Sleep Powder"
    if name == "STUN_SPORE": return "Stun Spore"
    if name == "SUNNY_DAY": return "Sunny Day"
    if name == "RAIN_DANCE": return "Rain Dance"
    if name == "DRAGON_DANCE": return "Dragon Dance"
    if name == "QUIVER_DANCE": return "Quiver Dance"
    if name == "SWORDS_DANCE": return "Swords Dance"
    if name == "BATON_PASS": return "Baton Pass"
    if name == "PAIN_SPLIT": return "Pain Split"
    if name == "DESTINY_BOND": return "Destiny Bond"
    if name == "MEAN_LOOK": return "Mean Look"
    if name == "PERISH_SONG": return "Perish Song"
    if name == "DREAM_EATER": return "Dream Eater"
    if name == "FUTURE_SIGHT": return "Future Sight"
    if name == "MORNING_SUN": return "Morning Sun"
    if name == "SHADOW_BALL": return "Shadow Ball"
    if name == "NIGHT_SHADE": return "Night Shade"
    if name == "TRI_ATTACK": return "Tri Attack"
    if name == "BODY_SLAM": return "Body Slam"
    if name == "DRILL_PECK": return "Drill Peck"
    if name == "FURY_ATTACK": return "Fury Attack"
    if name == "FURY_CUTTER": return "Fury Cutter"
    if name == "SAND_ATTACK": return "Sand Attack"
    if name == "STRING_SHOT": return "String Shot"
    if name == "POISON_STING": return "Poison Sting"
    if name == "MILK_DRINK": return "Milk Drink"
    if name == "THUNDER_WAVE": return "Thunder Wave"
    if name == "LIGHT_SCREEN": return "Light Screen"
    if name == "SLEEP_TALK": return "Sleep Talk"
    if name == "PURSUIT": return "Pursuit"
    if name == "VITAL_THROW": return "Vital Throw"
    if name == "CROSS_CHOP": return "Cross Chop"
    if name == "SPIDER_WEB": return "Spider Web"
    if name == "MUD_SLAP": return "Mud-Slap"
    if name == "ZAP_CANNON": return "Zap Cannon"
    if name == "DYNAMICPUNCH": return "DynamicPunch"
    if name == "HYPER_BEAM": return "Hyper Beam"
    if name == "LOVELY_KISS": return "Lovely Kiss"
    if name == "RAZOR_LEAF": return "Razor Leaf"
    if name == "DOUBLE_TEAM": return "Double Team"
    if name == "HYDRO_PUMP": return "Hydro Pump"
    return " ".join(part.capitalize() for part in name.split("_") if part)


def title_case_item(name: str) -> str:
    if name == "NO_ITEM": return "—"
    if name == "TWISTEDSPOON": return "TwistedSpoon"
    if name == "SILVERPOWDER": return "SilverPowder"
    if name == "NEVERMELTICE": return "NeverMeltIce"
    if name == "BLACKBELT_I": return "Black Belt"
    if name == "BLACKGLASSES": return "BlackGlasses"
    if name == "MIRACLEBERRY": return "MiracleBerry"
    if name == "MYSTERYBERRY": return "MysteryBerry"
    if name == "PSNCUREBERRY": return "PsnCureBerry"
    if name == "PRZCUREBERRY": return "PrzCureBerry"
    if name == "BURNT_BERRY": return "Burnt Berry"
    if name == "ICE_BERRY": return "Ice Berry"
    if name == "MINT_BERRY": return "Mint Berry"
    if name == "BERRY": return "Berry"
    if name == "GOLD_BERRY": return "Gold Berry"
    if name == "FOCUS_BAND": return "Focus Band"
    if name == "FOCUS_SASH": return "Focus Sash"
    if name == "EXPERT_BELT": return "Expert Belt"
    if name == "MUSCLE_BAND": return "Muscle Band"
    if name == "WISE_GLASSES": return "Wise Glasses"
    if name == "QUICK_CLAW": return "Quick Claw"
    if name == "SHARP_BEAK": return "Sharp Beak"
    if name == "HARD_STONE": return "Hard Stone"
    if name == "ROCKY_HELMET": return "Rocky Helmet"
    if name == "MYSTIC_WATER": return "Mystic Water"
    if name == "DRAGON_FANG": return "Dragon Fang"
    if name == "METAL_COAT": return "Metal Coat"
    if name == "DRAGON_SCALE": return "Dragon Scale"
    if name == "SPELL_TAG": return "Spell Tag"
    if name == "SOFT_SAND": return "Soft Sand"
    if name == "AIR_BALLOON": return "Air Balloon"
    if name == "SCOPE_LENS": return "Scope Lens"
    if name == "LIFE_ORB": return "Life Orb"
    if name == "CHOICE_BAND": return "Choice Band"
    if name == "CHOICE_SPECS": return "Choice Specs"
    if name == "CHOICE_SCARF": return "Choice Scarf"
    if name == "EVOLITE": return "Evolite"
    return " ".join(part.capitalize() for part in name.split("_") if part)


TYPE_PRINT = {
    "PSYCHIC_TYPE": "Psychic",
    "NORMAL": "Normal", "FIRE": "Fire", "WATER": "Water", "GRASS": "Grass",
    "ELECTRIC": "Electric", "ICE": "Ice", "FIGHTING": "Fighting", "POISON": "Poison",
    "GROUND": "Ground", "FLYING": "Flying", "BUG": "Bug", "ROCK": "Rock",
    "GHOST": "Ghost", "DRAGON": "Dragon", "DARK": "Dark", "STEEL": "Steel",
    "BIRD": "Flying",
}

# ---------------------------------------------------------------- data models

@dataclass
class Mon:
    species: str           # constant, e.g. DRAGONITE
    level: int
    item: str              # constant
    moves: list[str]       # constants

@dataclass
class Trainer:
    display_name: str
    group_name: str        # e.g. "FalknerGroup"
    badge_or_title: str    # e.g. "Zephyr Badge" / "E4-1" / "Champion"
    type_theme: str
    location: str
    party: list[Mon]
    hp_type: str | None = None  # resolved Hidden Power type, e.g. "Fire"


@dataclass
class RivalFight:
    """One Silver fight, with the three starter-pick branches collapsed.

    shared_party holds the 0..5 mons that are identical across all three
    starter branches; starter_variants holds the three sixth-slot Pokemon
    (one per player starter pick), in the order:
      [Bayleef line, Quilava line, Croconaw line]
    which corresponds to the player having picked Totodile / Chikorita /
    Cyndaquil respectively (Silver always picks the type counter).
    """
    fight_no: int           # 1..7 across both Rival1Group and Rival2Group
    label: str              # "Cherrygrove City"
    location: str           # full location string for header subtitle
    shared_party: list[Mon]
    starter_variants: list[Mon]    # always exactly 3 (Bayleef/Quilava/Croconaw)
    hp_type: str | None = None

@dataclass
class BaseStats:
    hp: int
    atk: int
    defn: int
    spe: int                # speed (4th in file)
    spa: int                # special attack (5th in file)
    spd: int                # special defense (6th in file)
    types: tuple[str, str]

# ---------------------------------------------------------- parties.asm parser

_BLOCK_RE = re.compile(
    r'db\s+"[^"]*@",\s*TRAINERTYPE_(\w+)\s*\n(.*?)\n\s*db\s+-1\s*;\s*end',
    re.DOTALL,
)


# Level-up move computation -- needed for TRAINERTYPE_NORMAL and TRAINERTYPE_ITEM
# trainers that don't list explicit moves. The engine fills these in by walking
# the species' EvosAttacks level-up table; see engine/pokemon/evolve.asm:484
# `FillMoves`. Algorithm: walk entries in source order, learn each move at
# lvl <= current; if 4 slots full, FIFO-evict the oldest (engine's `ShiftMoves`).
# Skip duplicates.

_LEVELUP_CACHE: dict[str, list[tuple[int, str]]] = {}
_EVOS_TEXT: str | None = None


def _evos_text() -> str:
    global _EVOS_TEXT
    if _EVOS_TEXT is None:
        _EVOS_TEXT = EVOS_ATTACKS.read_text(encoding="utf-8")
    return _EVOS_TEXT


def _species_to_evos_label(species: str) -> str:
    if species == "MR__MIME": return "MrMimeEvosAttacks"
    if species == "HO_OH": return "HoOhEvosAttacks"
    if species == "FARFETCH_D": return "FarfetchDEvosAttacks"
    if species == "NIDORAN_F": return "NidoranFEvosAttacks"
    if species == "NIDORAN_M": return "NidoranMEvosAttacks"
    if species == "PORYGON2": return "Porygon2EvosAttacks"
    return "".join(p.capitalize() for p in species.split("_") if p) + "EvosAttacks"


_LEVELUP_LINE_RE = re.compile(r"^\s*db\s+(\d+),\s*([A-Z][A-Z0-9_]*)\s*(?:;.*)?$")


def _load_levelup_table(species: str) -> list[tuple[int, str]]:
    """Parse the species' EvosAttacks block into [(level, move), ...].

    Skips evolution-marker lines (`db EVOLVE_*, ..., SPECIES`) because their
    first arg is a constant name, not a number, so the regex won't match. Also
    skips the `db 0` sentinels that terminate the evolutions / level-up lists
    (no comma → no match)."""
    if species in _LEVELUP_CACHE:
        return _LEVELUP_CACHE[species]
    text = _evos_text()
    label = _species_to_evos_label(species)
    m = re.search(rf"^{re.escape(label)}:\s*$", text, re.MULTILINE)
    if not m:
        raise ValueError(f"EvosAttacks label not found: {label}")
    start = m.end()
    next_m = re.search(r"^\w+EvosAttacks:\s*$", text[start:], re.MULTILINE)
    end = start + next_m.start() if next_m else len(text)
    moves: list[tuple[int, str]] = []
    for line in text[start:end].splitlines():
        ml = _LEVELUP_LINE_RE.match(line)
        if not ml:
            continue
        level = int(ml.group(1))
        move = ml.group(2)
        moves.append((level, move))
    _LEVELUP_CACHE[species] = moves
    return moves


def compute_levelup_moves(species: str, level: int) -> list[str]:
    """Return the four moves a wild-style mon of this species would have at
    this level. Mirrors engine/pokemon/evolve.asm:484 FillMoves.
    Always returns exactly 4 entries, padded with NO_MOVE."""
    slots: list[str] = []
    for lvl, mv in _load_levelup_table(species):
        if lvl > level or mv in slots:
            continue
        if len(slots) < 4:
            slots.append(mv)
        else:
            slots = slots[1:] + [mv]   # FIFO evict oldest
    while len(slots) < 4:
        slots.append("NO_MOVE")
    return slots


def _parse_trainer_body(ttype: str, body: str) -> list[Mon]:
    party: list[Mon] = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        if not line.startswith("db"):
            continue
        # Strip 'db ' prefix and any trailing comment
        payload = re.sub(r";.*$", "", line[2:]).strip().rstrip(",")
        parts = [p.strip() for p in payload.split(",")]
        if ttype == "ITEM_MOVES":
            level = int(parts[0])
            species = parts[1]
            item = parts[2]
            moves = parts[3:7]
            while len(moves) < 4:
                moves.append("NO_MOVE")
        elif ttype == "MOVES":
            level = int(parts[0])
            species = parts[1]
            item = "NO_ITEM"
            moves = parts[2:6]
            while len(moves) < 4:
                moves.append("NO_MOVE")
        elif ttype == "ITEM":
            level = int(parts[0])
            species = parts[1]
            item = parts[2]
            moves = compute_levelup_moves(species, level)
        else:  # NORMAL
            level = int(parts[0])
            species = parts[1]
            item = "NO_ITEM"
            moves = compute_levelup_moves(species, level)
        party.append(Mon(species=species, level=level, item=item, moves=moves))
    return party


def _parse_group_blocks(text: str, group_name: str) -> list[list[Mon]]:
    """All trainer entries inside a Group label, in source order."""
    m = re.search(rf"^{re.escape(group_name)}:\s*$", text, re.MULTILINE)
    if not m:
        raise ValueError(f"group not found: {group_name}")
    start = m.end()
    # Bound the search to the next *Group: label so we don't bleed into the
    # next group's entries.
    next_m = re.search(r"^\w+Group:\s*$", text[start:], re.MULTILINE)
    end = start + next_m.start() if next_m else len(text)
    region = text[start:end]
    return [
        _parse_trainer_body(bm.group(1), bm.group(2))
        for bm in _BLOCK_RE.finditer(region)
    ]


def _parse_group_block(text: str, group_name: str, member_idx: int = 1) -> list[Mon]:
    """The Nth (1-based) trainer entry inside a Group label."""
    parties = _parse_group_blocks(text, group_name)
    if not (1 <= member_idx <= len(parties)):
        raise ValueError(
            f"member {member_idx} out of range for {group_name} "
            f"(has {len(parties)} entries)"
        )
    return parties[member_idx - 1]


def load_trainers() -> list[Trainer]:
    text = PARTIES.read_text(encoding="utf-8")
    dvs = load_trainer_dvs()
    out: list[Trainer] = []

    def _build(name, group, badge_or_slot, type_theme, location):
        return Trainer(
            display_name=name,
            group_name=group,
            badge_or_title=badge_or_slot,
            type_theme=type_theme,
            location=location,
            party=_parse_group_block(text, group),
            hp_type=resolve_hp_type_for_group(group, dvs),
        )

    for name, group, _gymno, type_theme, location, badge in JOHTO_GYMS:
        out.append(_build(name, group, badge, type_theme, location))
    for name, group, slot, type_theme, location in ELITE_FOUR:
        out.append(_build(name, group, slot, type_theme, location))
    for name, group, _gymno, type_theme, location, badge in KANTO_GYMS:
        out.append(_build(name, group, badge, type_theme, location))
    return out


def load_rival_fights() -> list[RivalFight]:
    """All seven Silver fights, with starter branches collapsed per fight."""
    text = PARTIES.read_text(encoding="utf-8")
    dvs = load_trainer_dvs()
    out: list[RivalFight] = []
    for group, fight_idx, fight_no, label, location in RIVAL_FIGHTS:
        parties = _parse_group_blocks(text, group)
        # Each fight is three consecutive entries (Bayleef/Quilava/Croconaw).
        base = (fight_idx - 1) * 3
        if base + 3 > len(parties):
            raise ValueError(
                f"{group} fight {fight_idx} needs entries {base+1}..{base+3} "
                f"but only {len(parties)} present"
            )
        branches = parties[base:base + 3]
        # Starter is always the LAST mon; non-starter mons are identical.
        shared = branches[0][:-1]
        starters = [b[-1] for b in branches]
        # Sanity: assert non-starter slots are identical across branches.
        for b in branches[1:]:
            if b[:-1] != shared:
                raise ValueError(
                    f"{group} fight {fight_idx}: non-starter slots differ "
                    f"between starter branches; assumption broken"
                )
        out.append(RivalFight(
            fight_no=fight_no,
            label=label,
            location=location,
            shared_party=shared,
            starter_variants=starters,
            hp_type=resolve_hp_type_for_group(group, dvs),
        ))
    return out


def load_rocket_admins() -> list[Trainer]:
    """The six Team Rocket admin (non-grunt) fights, in challenge order."""
    text = PARTIES.read_text(encoding="utf-8")
    out: list[Trainer] = []
    for group, member_idx, admin_name, fight_label, location, type_theme in ROCKET_ADMINS:
        party = _parse_group_block(text, group, member_idx=member_idx)
        out.append(Trainer(
            display_name=admin_name,
            group_name=group,
            badge_or_title=fight_label,
            type_theme=type_theme,
            location=location,
            party=party,
            hp_type=None,  # admins don't run Hidden Power in this hack
        ))
    return out


def load_red() -> Trainer:
    """The Red fight at Mt. Silver Summit."""
    text = PARTIES.read_text(encoding="utf-8")
    group, member_idx, name, fight_label, location, type_theme = RED_FIGHT
    party = _parse_group_block(text, group, member_idx=member_idx)
    return Trainer(
        display_name=name,
        group_name=group,
        badge_or_title=fight_label,
        type_theme=type_theme,
        location=location,
        party=party,
        hp_type=None,
    )


# Hidden Power type resolution -------------------------------------------------

# In Gen 2: HP type = ((atk_DV & 3) << 2) | (def_DV & 3), indexed into:
HP_TYPE_TABLE = [
    "Fighting", "Flying", "Poison", "Ground",
    "Rock", "Bug", "Ghost", "Steel",
    "Fire", "Water", "Grass", "Electric",
    "Psychic", "Ice", "Dragon", "Dark",
]

# Group label -> trainer-class constant in dvs.asm.
# Most map by stripping "Group" and uppercasing; LtSurgeGroup needs the
# underscore between LT and SURGE, ChampionGroup is LANCE-but-class-CHAMPION.
_GROUP_TO_CLASS_OVERRIDE = {
    "LtSurgeGroup": "LT_SURGE",
    "ChampionGroup": "CHAMPION",
    "ExecutiveMGroup": "EXECUTIVEM",
    "ExecutiveFGroup": "EXECUTIVEF",
}


def group_to_class(group: str) -> str:
    if group in _GROUP_TO_CLASS_OVERRIDE:
        return _GROUP_TO_CLASS_OVERRIDE[group]
    base = group.removesuffix("Group")
    # CamelCase -> SNAKE_CASE: insert _ before each interior uppercase
    out = []
    for i, ch in enumerate(base):
        if i > 0 and ch.isupper() and not base[i - 1].isupper():
            out.append("_")
        out.append(ch.upper())
    return "".join(out)


def load_trainer_dvs() -> dict[str, tuple[int, int, int, int]]:
    """Parse data/trainers/dvs.asm into {class_name: (atk, def, spd, spc)}."""
    text = TRAINER_DVS.read_text(encoding="utf-8")
    out: dict[str, tuple[int, int, int, int]] = {}
    # Lines look like: `dn 14, 8, 8, 8 ; ERIKA — comment`
    line_re = re.compile(
        r"^\s*dn\s+(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*;\s*([A-Z][A-Z0-9_]*)",
        re.MULTILINE,
    )
    for m in line_re.finditer(text):
        atk, defn, spd, spc, klass = m.groups()
        out[klass] = (int(atk), int(defn), int(spd), int(spc))
    return out


def resolve_hp_type_for_group(
    group: str,
    dvs: dict[str, tuple[int, int, int, int]],
) -> str | None:
    klass = group_to_class(group)
    if klass not in dvs:
        return None
    atk, defn, _spd, _spc = dvs[klass]
    idx = ((atk & 3) << 2) | (defn & 3)
    return HP_TYPE_TABLE[idx]


# ------------------------------------------------------- base_stats parser

_BASE_STATS_CACHE: dict[str, BaseStats] = {}

# Map species constant -> file basename (lowercase, double-underscore for MR__MIME etc).
def _species_to_filename(species: str) -> str:
    return species.lower() + ".asm"


def load_base_stats(species: str) -> BaseStats:
    if species in _BASE_STATS_CACHE:
        return _BASE_STATS_CACHE[species]
    path = BASE_STATS_DIR / _species_to_filename(species)
    text = path.read_text(encoding="utf-8")
    # 1st db line after header is stats
    nums_re = re.compile(r"db\s+(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*$",
                         re.MULTILINE)
    m = nums_re.search(text)
    if not m:
        raise ValueError(f"no stat line in {path}")
    hp, atk, defn, spe, spa, spd = (int(x) for x in m.groups())

    type_re = re.compile(r"db\s+(\w+),\s*(\w+)\s*;\s*type", re.IGNORECASE)
    tm = type_re.search(text)
    if not tm:
        raise ValueError(f"no type line in {path}")
    types = (TYPE_PRINT.get(tm.group(1), tm.group(1).title()),
             TYPE_PRINT.get(tm.group(2), tm.group(2).title()))
    bs = BaseStats(hp, atk, defn, spe, spa, spd, types)
    _BASE_STATS_CACHE[species] = bs
    return bs


# ---------------------------------------------------------------- pdf render

# Layout constants
PAGE_W, PAGE_H = letter
MARGIN = 0.4 * inch

CARD_PADDING = 8
CARD_GAP_Y = 5

DARK_BG = colors.HexColor("#2A2A33")
PANEL_BG = colors.HexColor("#F4F4F8")
CARD_BG = colors.HexColor("#FFFFFF")
TEXT_DARK = colors.HexColor("#1F2126")
TEXT_MUTED = colors.HexColor("#5A6068")
ACCENT_LINE = colors.HexColor("#D9DCE3")
BAR_TRACK = colors.HexColor("#E6E8EE")

STAT_COLOR = colors.HexColor("#5C84F4")  # blue, like Showdown


def _hex(c: str) -> colors.Color:
    return colors.HexColor(c)


def luminance(hexc: str) -> float:
    h = hexc.lstrip("#")
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    return 0.299 * r + 0.587 * g + 0.114 * b


def text_on(hexc: str) -> colors.Color:
    return colors.white if luminance(hexc) < 0.55 else _hex("#1F2126")


def draw_type_pill(c: canvas.Canvas, x, y, type_name: str, font_size=7.5, h=12):
    label = type_name.upper()
    color = TYPE_COLORS.get(type_name, "#888888")
    text_w = c.stringWidth(label, "Helvetica-Bold", font_size)
    pad = 5
    w = text_w + pad * 2
    c.setFillColor(_hex(color))
    c.roundRect(x, y, w, h, 2, fill=1, stroke=0)
    c.setFillColor(text_on(color))
    c.setFont("Helvetica-Bold", font_size)
    c.drawString(x + pad, y + 3.5, label)
    return w


def draw_stat_row(c: canvas.Canvas, x, y, label, value, max_value, w_total=180, label_w=22, val_w=24, bar_h=6):
    bar_x = x + label_w
    bar_w = w_total - label_w - val_w - 4
    # label
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x, y, label)
    # bar track
    c.setFillColor(BAR_TRACK)
    c.roundRect(bar_x, y - 1, bar_w, bar_h, 1.5, fill=1, stroke=0)
    # bar fill (capped at 200, like showdown)
    pct = max(0.05, min(1.0, value / float(max_value)))
    c.setFillColor(STAT_COLOR)
    c.roundRect(bar_x, y - 1, bar_w * pct, bar_h, 1.5, fill=1, stroke=0)
    # value text on the right
    c.setFillColor(TEXT_DARK)
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(x + w_total, y, str(value))


def draw_card(c: canvas.Canvas, x, y, w, h, mon: Mon, bs: BaseStats, hp_type: str | None = None):
    # card background + border
    c.setFillColor(CARD_BG)
    c.setStrokeColor(ACCENT_LINE)
    c.setLineWidth(0.6)
    c.roundRect(x, y, w, h, 6, fill=1, stroke=1)

    # left padding line accent (type 1 color)
    accent = TYPE_COLORS.get(bs.types[0], "#888888")
    c.setFillColor(_hex(accent))
    c.rect(x, y, 4, h, fill=1, stroke=0)

    inner_x = x + CARD_PADDING + 4
    inner_y_top = y + h - CARD_PADDING

    # name + level
    name = title_case_constant(mon.species)
    c.setFillColor(TEXT_DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inner_x, inner_y_top - 11, name)

    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 8.5)
    c.drawString(inner_x, inner_y_top - 22, f"Lv. {mon.level}")

    # type pills, right-aligned to card
    types_to_draw = list(dict.fromkeys(bs.types))  # dedupe single-type
    pill_widths = [c.stringWidth(t.upper(), "Helvetica-Bold", 7.5) + 10 for t in types_to_draw]
    gap = 4
    total_pill = sum(pill_widths) + gap * (len(pill_widths) - 1)
    cur_x = x + w - CARD_PADDING - total_pill
    for t, pw in zip(types_to_draw, pill_widths):
        draw_type_pill(c, cur_x, inner_y_top - 12, t, font_size=7.5, h=12)
        cur_x += pw + gap

    # item line
    item_text = title_case_item(mon.item)
    c.setFillColor(TEXT_DARK)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(inner_x, inner_y_top - 34, "Item:")
    c.setFont("Helvetica", 7.5)
    c.drawString(inner_x + 22, inner_y_top - 34, item_text)

    # divider
    c.setStrokeColor(ACCENT_LINE)
    c.setLineWidth(0.4)
    c.line(inner_x, inner_y_top - 40, x + w - CARD_PADDING, inner_y_top - 40)

    # ----- moves (left half) and stats (right half)
    body_top = inner_y_top - 46
    body_left = inner_x
    body_right = x + w - CARD_PADDING
    mid = body_left + (body_right - body_left) * 0.46

    # Moves header
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(body_left, body_top, "MOVES")
    # Moves list
    line_y = body_top - 11
    c.setFont("Helvetica", 8.5)
    c.setFillColor(TEXT_DARK)
    for mv in mon.moves:
        if mv == "NO_MOVE":
            continue
        label = title_case_move(mv)
        c.setFillColor(TEXT_DARK)
        c.circle(body_left + 3, line_y + 3, 1.4, fill=1, stroke=0)
        c.drawString(body_left + 8, line_y, label)
        if mv == "HIDDEN_POWER" and hp_type:
            text_w = c.stringWidth(label, "Helvetica", 8.5)
            draw_type_pill(c, body_left + 8 + text_w + 4, line_y - 1, hp_type, font_size=6, h=9)
            # Restore canvas font/fill state so subsequent move lines aren't bold-on-color.
            c.setFont("Helvetica", 8.5)
            c.setFillColor(TEXT_DARK)
        line_y -= 10

    # Stats header
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(mid, body_top, "BASE STATS")

    stats_x = mid
    stats_w = body_right - mid
    sy = body_top - 11

    rows = [
        ("HP",  bs.hp),
        ("Atk", bs.atk),
        ("Def", bs.defn),
        ("SpA", bs.spa),
        ("SpD", bs.spd),
        ("Spe", bs.spe),
    ]
    bar_max = 200
    for label, val in rows:
        draw_stat_row(c, stats_x, sy, label, val, bar_max, w_total=stats_w, bar_h=5)
        sy -= 10

    # total at bottom (inside card)
    total = bs.hp + bs.atk + bs.defn + bs.spa + bs.spd + bs.spe
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(stats_x, sy + 1, "TOTAL")
    c.setFillColor(TEXT_DARK)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawRightString(stats_x + stats_w, sy + 1, str(total))


def draw_trainer_header(c: canvas.Canvas, x, y, w, h, t: Trainer):
    color = TYPE_COLORS.get(t.type_theme, "#444444")
    c.setFillColor(_hex(color))
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)

    # White-on-color text
    c.setFillColor(text_on(color))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x + 14, y + h - 22, t.display_name.upper())

    # subtitle row: badge | type | location
    c.setFont("Helvetica", 9)
    sub = [t.badge_or_title, f"{t.type_theme} type", t.location]
    c.drawString(x + 14, y + 8, "  •  ".join(sub))

    # right-side party-size pill, vertically centered
    party_label = f"{len(t.party)} POKÉMON"
    pill_h = 14
    pw = c.stringWidth(party_label, "Helvetica-Bold", 8.5) + 14
    pill_y = y + (h - pill_h) / 2
    c.setFillColor(colors.white)
    c.roundRect(x + w - pw - 14, pill_y, pw, pill_h, 7, fill=1, stroke=0)
    c.setFillColor(_hex(color))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x + w - pw - 14 + 7, pill_y + 4, party_label)


def draw_section_title(c: canvas.Canvas, y, title, subtitle=""):
    c.setFillColor(TEXT_DARK)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(MARGIN, y, title)
    if subtitle:
        c.setFillColor(TEXT_MUTED)
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN, y - 14, subtitle)
    c.setStrokeColor(ACCENT_LINE)
    c.setLineWidth(0.6)
    c.line(MARGIN, y - 22, PAGE_W - MARGIN, y - 22)


# ---------------------------------------------------------- page composition

def render_trainer(c: canvas.Canvas, t: Trainer, top_y: float) -> float:
    """Render a trainer block starting at top_y (top edge). Returns next-block top_y."""
    # Header
    HEADER_H = 44
    draw_trainer_header(c, MARGIN, top_y - HEADER_H, PAGE_W - 2 * MARGIN, HEADER_H, t)
    cur_y = top_y - HEADER_H - 8

    # Cards: 2 columns, dynamic rows
    avail_w = PAGE_W - 2 * MARGIN
    col_gap = 10
    col_w = (avail_w - col_gap) / 2.0
    card_h = 128

    # walk the party
    for i, mon in enumerate(t.party):
        col = i % 2
        if col == 0 and i > 0:
            cur_y -= card_h + CARD_GAP_Y
        x = MARGIN + col * (col_w + col_gap)
        bs = load_base_stats(mon.species)
        draw_card(c, x, cur_y - card_h, col_w, card_h, mon, bs, hp_type=t.hp_type)
    # advance past last row of cards
    cur_y -= card_h + 16
    return cur_y


# ---- Rival fight rendering ---------------------------------------------------

# In Gen 2, Silver always picks the type-counter starter to whatever the player
# chose. Parties.asm orders the three branches Bayleef / Quilava / Croconaw
# (Silver's mon), which corresponds to the player having picked Totodile /
# Chikorita / Cyndaquil respectively.
PLAYER_PICKS = [
    "If you picked TOTODILE",
    "If you picked CHIKORITA",
    "If you picked CYNDAQUIL",
]


def draw_rival_fight_header(c: canvas.Canvas, x, y, w, h, f: RivalFight) -> None:
    color = TYPE_COLORS["Dark"]   # Silver leans dark/anti-hero in this hack
    c.setFillColor(_hex(color))
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x + 14, y + h - 22, f"SILVER  ·  FIGHT {f.fight_no}")

    c.setFont("Helvetica", 9)
    sub = [f.label, f.location]
    c.drawString(x + 14, y + 8, "  •  ".join(sub))

    # Right pill: shared mons + 1 (the starter-variant slot)
    party_label = f"{len(f.shared_party) + 1} POKÉMON"
    pill_h = 14
    pw = c.stringWidth(party_label, "Helvetica-Bold", 8.5) + 14
    pill_y = y + (h - pill_h) / 2
    c.setFillColor(colors.white)
    c.roundRect(x + w - pw - 14, pill_y, pw, pill_h, 7, fill=1, stroke=0)
    c.setFillColor(_hex(color))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x + w - pw - 14 + 7, pill_y + 4, party_label)


def render_rival_fight(c: canvas.Canvas, f: RivalFight, top_y: float) -> float:
    """Render one rival fight: shared mons in 2-col + starter variants in 3-col."""
    HEADER_H = 44
    draw_rival_fight_header(c, MARGIN, top_y - HEADER_H,
                            PAGE_W - 2 * MARGIN, HEADER_H, f)
    cur_y = top_y - HEADER_H - 8

    avail_w = PAGE_W - 2 * MARGIN
    col_gap = 10
    col_w_2 = (avail_w - col_gap) / 2.0
    col_w_3 = (avail_w - 2 * col_gap) / 3.0
    card_h = 128

    # Shared mons (2-col)
    for i, mon in enumerate(f.shared_party):
        col = i % 2
        if col == 0 and i > 0:
            cur_y -= card_h + CARD_GAP_Y
        x = MARGIN + col * (col_w_2 + col_gap)
        bs = load_base_stats(mon.species)
        draw_card(c, x, cur_y - card_h, col_w_2, card_h, mon, bs, hp_type=f.hp_type)
    if f.shared_party:
        cur_y -= card_h + CARD_GAP_Y

    # Starter-slot subheader band
    cur_y -= 4
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(MARGIN, cur_y - 9,
                 "STARTER SLOT — Silver always picks the type-counter starter")
    cur_y -= 16

    # "If you picked X" labels in a row
    for i, pick in enumerate(PLAYER_PICKS):
        x = MARGIN + i * (col_w_3 + col_gap)
        c.setFillColor(TEXT_MUTED)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(x, cur_y - 9, pick)
    cur_y -= 14

    # Three starter cards (3-col)
    for i, mon in enumerate(f.starter_variants):
        x = MARGIN + i * (col_w_3 + col_gap)
        bs = load_base_stats(mon.species)
        draw_card(c, x, cur_y - card_h, col_w_3, card_h, mon, bs, hp_type=f.hp_type)
    cur_y -= card_h + 16
    return cur_y


def render_rivals_section(c: canvas.Canvas,
                          fights: list[RivalFight],
                          cur_y: float) -> float:
    if cur_y < PAGE_H - MARGIN - 30:
        cur_y -= 14
    draw_section_title(c, cur_y, "SILVER — RIVAL FIGHTS",
                       "Seven encounters from Cherrygrove City to Indigo Plateau. "
                       "The sixth slot varies with your starter pick.")
    cur_y -= 36
    for f in fights:
        shared_rows = (len(f.shared_party) + 1) // 2
        needed = (44 + 8
                  + shared_rows * 128 + max(0, shared_rows - 1) * CARD_GAP_Y
                  + 4 + 16    # starter-slot subheader band
                  + 14        # pick-label row
                  + 128 + 16)  # variant cards + bottom gap
        if not fits(cur_y, needed):
            c.showPage()
            cur_y = PAGE_H - MARGIN
        cur_y = render_rival_fight(c, f, cur_y)
    return cur_y


def fits(top_y: float, needed_h: float) -> bool:
    return top_y - needed_h >= MARGIN


def render_section(c: canvas.Canvas, title: str, subtitle: str, trainers: list[Trainer], cur_y: float) -> float:
    # Section title
    if cur_y < PAGE_H - MARGIN - 30:
        cur_y -= 14
    draw_section_title(c, cur_y, title, subtitle)
    cur_y -= 36
    for t in trainers:
        # estimate trainer block height (header + gap + rows*card + gap*(rows-1) + tail)
        rows = (len(t.party) + 1) // 2
        needed = 44 + 8 + rows * 128 + max(0, rows - 1) * CARD_GAP_Y + 16
        if not fits(cur_y, needed):
            c.showPage()
            cur_y = PAGE_H - MARGIN
        cur_y = render_trainer(c, t, cur_y)
    return cur_y


def draw_cover_page(c: canvas.Canvas):
    # Background
    c.setFillColor(_hex("#1B1D24"))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Title block
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 32)
    c.drawString(MARGIN, PAGE_H - 1.6 * inch, "POKÉMON GOLD")
    c.setFillColor(_hex("#F8D030"))
    c.drawString(MARGIN, PAGE_H - 1.6 * inch - 36, "Hack — Trainer Dossier")
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 12)
    c.drawString(MARGIN, PAGE_H - 1.6 * inch - 60,
                 "Gym Leaders · Elite Four · Champion · Rival · Team Rocket Admins · Red")
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(_hex("#A0A6B0"))
    c.drawString(MARGIN, PAGE_H - 1.6 * inch - 80,
                 "Levels, items, movesets and base stats — generated from source.")

    # Type legend across the bottom of cover
    legend_y = MARGIN + 1.0 * inch
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN, legend_y + 80, "Type colour legend")
    types_to_show = [
        "Normal", "Fire", "Water", "Grass", "Electric", "Ice",
        "Fighting", "Poison", "Ground", "Flying", "Psychic",
        "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel",
    ]
    cell_w = 86
    cell_h = 18
    cols = 4
    for idx, t in enumerate(types_to_show):
        cx = MARGIN + (idx % cols) * (cell_w + 6)
        cy = legend_y + 60 - (idx // cols) * (cell_h + 4)
        draw_type_pill(c, cx, cy, t, font_size=8, h=cell_h)
    # footer
    c.setFillColor(_hex("#A0A6B0"))
    c.setFont("Helvetica", 9)
    c.drawString(MARGIN, MARGIN, "Built from data/trainers/parties.asm + data/pokemon/base_stats/")
    c.showPage()


def draw_page_footer(c: canvas.Canvas, page_no: int):
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 8)
    c.drawRightString(PAGE_W - MARGIN, MARGIN / 2, f"{page_no}")


def main() -> None:
    trainers = load_trainers()

    c = canvas.Canvas(str(OUT_PDF), pagesize=letter)
    c.setTitle("Pokemon Gold Hack — Trainer Dossier")
    c.setAuthor("Pokemon Gold Hack")

    # Cover page
    draw_cover_page(c)

    # Johto gyms
    cur_y = PAGE_H - MARGIN
    cur_y = render_section(c, "JOHTO GYM LEADERS",
                           "The first eight badges, in challenge order.",
                           trainers[:8], cur_y)

    # E4 + Champion
    c.showPage()
    cur_y = PAGE_H - MARGIN
    cur_y = render_section(c, "ELITE FOUR & CHAMPION",
                           "Indigo Plateau — five consecutive battles, no swaps between.",
                           trainers[8:13], cur_y)

    # Kanto gyms
    c.showPage()
    cur_y = PAGE_H - MARGIN
    cur_y = render_section(c, "KANTO GYM LEADERS",
                           "Post-game gauntlet across Kanto.",
                           trainers[13:], cur_y)

    # Silver — rival fights (with starter-branch handling)
    c.showPage()
    cur_y = PAGE_H - MARGIN
    cur_y = render_rivals_section(c, load_rival_fights(), cur_y)

    # Team Rocket admins (no grunts)
    c.showPage()
    cur_y = PAGE_H - MARGIN
    cur_y = render_section(c, "TEAM ROCKET ADMINS",
                           "Six non-grunt fights — Petrel, Proton, Ariana, Archer "
                           "across Mahogany Hideout and Goldenrod Radio Tower.",
                           load_rocket_admins(), cur_y)

    # Red
    c.showPage()
    cur_y = PAGE_H - MARGIN
    cur_y = render_section(c, "MT. SILVER — RED",
                           "The hidden Champion. Single fight, Silver Cave summit.",
                           [load_red()], cur_y)

    # add page numbers
    # (reportlab doesn't make this trivial mid-build; we re-open by adding an overlay
    # via the canvas's getPageNumber? We'll skip page numbers for now to keep the
    # PDF deterministic — the section titles already orient the reader.)

    c.save()
    print(f"wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
