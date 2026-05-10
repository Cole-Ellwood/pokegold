#!/usr/bin/env python3
"""Generate a Pokemon Showdown-style PDF of every gym leader + Elite 4 + Champion team.

This is a player-facing reference doc, not a dev artifact. The PDF includes,
for each trainer in challenge order:

  - Trainer header with type theme, badge / E4 slot, and location
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
cwd. There is no config or CLI flag — the trainer list (Johto gyms, Elite 4 +
Champion, Kanto gyms) is hard-coded near the top of this file. Edit the three
trainer-meta lists (JOHTO_GYMS / ELITE_FOUR / KANTO_GYMS) if a future hack
adds or reorders gyms.

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

def _parse_group_block(text: str, group_name: str) -> list[Mon]:
    """Parse the FIRST trainer entry inside a Group label."""
    # Find the label
    m = re.search(rf"^{re.escape(group_name)}:\s*$", text, re.MULTILINE)
    if not m:
        raise ValueError(f"group not found: {group_name}")
    start = m.end()
    # Trainer block: from `db "<NAME>@", TRAINERTYPE_*` to `db -1 ; end`
    block_re = re.compile(
        r'db\s+"[^"]*@",\s*TRAINERTYPE_(\w+)\s*\n(.*?)\n\s*db\s+-1\s*;\s*end',
        re.DOTALL,
    )
    bm = block_re.search(text, start)
    if not bm:
        raise ValueError(f"trainer block not found in {group_name}")
    ttype, body = bm.group(1), bm.group(2)
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
            moves = ["NO_MOVE"] * 4
        else:  # NORMAL
            level = int(parts[0])
            species = parts[1]
            item = "NO_ITEM"
            moves = ["NO_MOVE"] * 4
        party.append(Mon(species=species, level=level, item=item, moves=moves))
    return party


def load_trainers() -> list[Trainer]:
    text = PARTIES.read_text(encoding="utf-8")
    out: list[Trainer] = []

    for name, group, gymno, type_theme, location, badge in JOHTO_GYMS:
        out.append(Trainer(name, group, badge, type_theme, location, _parse_group_block(text, group)))
    for name, group, slot, type_theme, location in ELITE_FOUR:
        out.append(Trainer(name, group, slot, type_theme, location, _parse_group_block(text, group)))
    for name, group, gymno, type_theme, location, badge in KANTO_GYMS:
        out.append(Trainer(name, group, badge, type_theme, location, _parse_group_block(text, group)))
    return out


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


def draw_card(c: canvas.Canvas, x, y, w, h, mon: Mon, bs: BaseStats):
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
        c.circle(body_left + 3, line_y + 3, 1.4, fill=1, stroke=0)
        c.drawString(body_left + 8, line_y, label)
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
        draw_card(c, x, cur_y - card_h, col_w, card_h, mon, bs)
    # advance past last row of cards
    cur_y -= card_h + 16
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
    c.drawString(MARGIN, PAGE_H - 1.6 * inch - 60, "Gym Leaders, Elite Four & Champion teams")
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

    # add page numbers
    # (reportlab doesn't make this trivial mid-build; we re-open by adding an overlay
    # via the canvas's getPageNumber? We'll skip page numbers for now to keep the
    # PDF deterministic — the section titles already orient the reader.)

    c.save()
    print(f"wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
