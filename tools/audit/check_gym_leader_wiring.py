#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEADERS_FILE = ROOT / "data" / "trainers" / "leaders.asm"
AI_TIERS_FILE = ROOT / "data" / "trainers" / "ai_tiers.asm"
PARTIES_FILE = ROOT / "data" / "trainers" / "parties.asm"
PARTY_POINTERS_FILE = ROOT / "data" / "trainers" / "party_pointers.asm"
TRAINER_ATTRIBUTES_FILE = ROOT / "data" / "trainers" / "attributes.asm"
TRAINER_CLASS_NAMES_FILE = ROOT / "data" / "trainers" / "class_names.asm"
TRAINER_DVS_FILE = ROOT / "data" / "trainers" / "dvs.asm"
TRAINER_PICS_FILE = ROOT / "data" / "trainers" / "pic_pointers.asm"
TRAINER_PALETTES_FILE = ROOT / "data" / "trainers" / "palettes.asm"
TRAINER_ENCOUNTER_MUSIC_FILE = ROOT / "data" / "trainers" / "encounter_music.asm"
TRAINER_CONSTANTS_FILE = ROOT / "constants" / "trainer_constants.asm"
POKEMON_CONSTANTS_FILE = ROOT / "constants" / "pokemon_constants.asm"
MOVE_CONSTANTS_FILE = ROOT / "constants" / "move_constants.asm"
ITEM_CONSTANTS_FILE = ROOT / "constants" / "item_constants.asm"
EVENT_FLAGS_FILE = ROOT / "constants" / "event_flags.asm"
ENGINE_FLAGS_FILE = ROOT / "constants" / "engine_flags.asm"
POKEMON_BASE_STATS_FILE = ROOT / "data" / "pokemon" / "base_stats.asm"
POKEMON_NAMES_FILE = ROOT / "data" / "pokemon" / "names.asm"
MOVE_DATA_FILE = ROOT / "data" / "moves" / "moves.asm"
MOVE_NAMES_FILE = ROOT / "data" / "moves" / "names.asm"
MOVE_DESCRIPTIONS_FILE = ROOT / "data" / "moves" / "descriptions.asm"
ITEM_ATTRIBUTES_DATA_FILE = ROOT / "data" / "items" / "attributes.asm"
ITEM_NAMES_FILE = ROOT / "data" / "items" / "names.asm"
ITEM_DESCRIPTIONS_FILE = ROOT / "data" / "items" / "descriptions.asm"
MAP_CONSTANTS_FILE = ROOT / "constants" / "map_constants.asm"
MAPS_FILE = ROOT / "data" / "maps" / "maps.asm"
MAP_ATTRIBUTES_FILE = ROOT / "data" / "maps" / "attributes.asm"
MAP_SCRIPTS_FILE = ROOT / "data" / "maps" / "scripts.asm"
MAP_BLOCKS_FILE = ROOT / "data" / "maps" / "blocks.asm"


@dataclass(frozen=True)
class Leader:
    name: str
    map_file: str
    script_label: str
    trainer_class: str
    trainer_id: str
    party_group: str
    beat_event: str
    sprite: str
    leader_table: str


@dataclass(frozen=True)
class PartyMon:
    level: int
    species: str
    item: str
    moves: tuple[str, str, str, str]


@dataclass(frozen=True)
class PartyEntry:
    group: str
    trainer_type: str
    mons: tuple[PartyMon, ...]


@dataclass(frozen=True)
class TrainerEventRef:
    map_file: str
    trainer_label: str
    trainer_class: str
    trainer_id: str


LEADERS = (
    Leader(
        "Falkner",
        "maps/VioletGym.asm",
        "VioletGymFalknerScript",
        "FALKNER",
        "FALKNER1",
        "FalknerGroup",
        "EVENT_BEAT_FALKNER",
        "SPRITE_FALKNER",
        "GymLeaders",
    ),
    Leader(
        "Bugsy",
        "maps/AzaleaGym.asm",
        "AzaleaGymBugsyScript",
        "BUGSY",
        "BUGSY1",
        "BugsyGroup",
        "EVENT_BEAT_BUGSY",
        "SPRITE_BUGSY",
        "GymLeaders",
    ),
    Leader(
        "Whitney",
        "maps/GoldenrodGym.asm",
        "GoldenrodGymWhitneyScript",
        "WHITNEY",
        "WHITNEY1",
        "WhitneyGroup",
        "EVENT_BEAT_WHITNEY",
        "SPRITE_WHITNEY",
        "GymLeaders",
    ),
    Leader(
        "Morty",
        "maps/EcruteakGym.asm",
        "EcruteakGymMortyScript",
        "MORTY",
        "MORTY1",
        "MortyGroup",
        "EVENT_BEAT_MORTY",
        "SPRITE_MORTY",
        "GymLeaders",
    ),
    Leader(
        "Chuck",
        "maps/CianwoodGym.asm",
        "CianwoodGymChuckScript",
        "CHUCK",
        "CHUCK1",
        "ChuckGroup",
        "EVENT_BEAT_CHUCK",
        "SPRITE_CHUCK",
        "GymLeaders",
    ),
    Leader(
        "Jasmine",
        "maps/OlivineGym.asm",
        "OlivineGymJasmineScript",
        "JASMINE",
        "JASMINE1",
        "JasmineGroup",
        "EVENT_BEAT_JASMINE",
        "SPRITE_JASMINE",
        "GymLeaders",
    ),
    Leader(
        "Pryce",
        "maps/MahoganyGym.asm",
        "MahoganyGymPryceScript",
        "PRYCE",
        "PRYCE1",
        "PryceGroup",
        "EVENT_BEAT_PRYCE",
        "SPRITE_PRYCE",
        "GymLeaders",
    ),
    Leader(
        "Clair",
        "maps/BlackthornGym1F.asm",
        "BlackthornGymClairScript",
        "CLAIR",
        "CLAIR1",
        "ClairGroup",
        "EVENT_BEAT_CLAIR",
        "SPRITE_CLAIR",
        "GymLeaders",
    ),
    Leader(
        "Brock",
        "maps/PewterGym.asm",
        "PewterGymBrockScript",
        "BROCK",
        "BROCK1",
        "BrockGroup",
        "EVENT_BEAT_BROCK",
        "SPRITE_BROCK",
        "KantoGymLeaders",
    ),
    Leader(
        "Misty",
        "maps/CeruleanGym.asm",
        "CeruleanGymMistyScript",
        "MISTY",
        "MISTY1",
        "MistyGroup",
        "EVENT_BEAT_MISTY",
        "SPRITE_MISTY",
        "KantoGymLeaders",
    ),
    Leader(
        "Lt. Surge",
        "maps/VermilionGym.asm",
        "VermilionGymSurgeScript",
        "LT_SURGE",
        "LT_SURGE1",
        "LtSurgeGroup",
        "EVENT_BEAT_LTSURGE",
        "SPRITE_SURGE",
        "KantoGymLeaders",
    ),
    Leader(
        "Erika",
        "maps/CeladonGym.asm",
        "CeladonGymErikaScript",
        "ERIKA",
        "ERIKA1",
        "ErikaGroup",
        "EVENT_BEAT_ERIKA",
        "SPRITE_ERIKA",
        "KantoGymLeaders",
    ),
    Leader(
        "Janine",
        "maps/FuchsiaGym.asm",
        "FuchsiaGymJanineScript",
        "JANINE",
        "JANINE1",
        "JanineGroup",
        "EVENT_BEAT_JANINE",
        "SPRITE_JANINE",
        "KantoGymLeaders",
    ),
    Leader(
        "Sabrina",
        "maps/SaffronGym.asm",
        "SaffronGymSabrinaScript",
        "SABRINA",
        "SABRINA1",
        "SabrinaGroup",
        "EVENT_BEAT_SABRINA",
        "SPRITE_SABRINA",
        "KantoGymLeaders",
    ),
    Leader(
        "Blaine",
        "maps/SeafoamGym.asm",
        "SeafoamGymBlaineScript",
        "BLAINE",
        "BLAINE1",
        "BlaineGroup",
        "EVENT_BEAT_BLAINE",
        "SPRITE_BLAINE",
        "KantoGymLeaders",
    ),
    Leader(
        "Blue",
        "maps/ViridianGym.asm",
        "ViridianGymBlueScript",
        "BLUE",
        "BLUE1",
        "BlueGroup",
        "EVENT_BEAT_BLUE",
        "SPRITE_BLUE",
        "KantoGymLeaders",
    ),
)

TOP_LEVEL_LABEL_RE = re.compile(r"^[A-Za-z0-9_]+:\s*$")
CLASS_ENTRY_RE = re.compile(r"^\s*db\s+([A-Z0-9_]+|-1)\s*(?:;.*)?$")
AI_TIER_RE = re.compile(
    r"^\s*db\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*,\s*(AI_TIER_[A-Z]+)\s*(?:;.*)?$"
)
GROUP_RE = re.compile(r"^([A-Za-z0-9_]+Group):\s*$")
TRAINER_RE = re.compile(r'^\s*db\s+"[^"]*@",\s*(TRAINERTYPE_[A-Z_]+)\s*(?:;.*)?$')
DB_RE = re.compile(r"^\s*db\s+(.+?)\s*(?:;.*)?$")
CONST_RE = re.compile(r"^\s*const\s+([A-Z0-9_]+)\b")
CONST_DEF_RE = re.compile(r"^\s*const_def(?:\s+(\$[0-9a-fA-F]+|[0-9]+))?\b")
ADD_TMHM_RE = re.compile(r"^\s*add_(tm|hm)\s+([A-Z0-9_]+)\b")
TRAINERCLASS_RE = re.compile(r"^\s*trainerclass\s+([A-Z0-9_]+)\b")
PARTY_POINTER_RE = re.compile(r"^\s*dw\s+([A-Za-z0-9_]+Group)\s*(?:;.*)?$")
CLASS_NAME_RE = re.compile(r'^\s*li\s+"([^"]+)"\s*$')
ATTRIBUTE_DB_RE = re.compile(r"^\s*db\s+(.+?)\s*(?:;.*)?$")
ATTRIBUTE_DW_RE = re.compile(r"^\s*dw\s+(.+?)\s*(?:;.*)?$")
DV_RE = re.compile(
    r"^\s*dn\s+([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*(?:;.*)?$"
)
PIC_RE = re.compile(r"^\s*dba_pic\s+([A-Za-z0-9_]+)\s*(?:;.*)?$")
PALETTE_RE = re.compile(r'^\s*INCBIN\s+"([^"]+\.gbcpal)",\s*middle_colors\s*(?:;.*)?$')
MUSIC_RE = re.compile(r"^\s*db\s+(MUSIC_[A-Z0-9_]+)\s*(?:;.*)?$")
INCLUDE_RE = re.compile(r'^\s*INCLUDE\s+"([^"]+)"\s*$')
BASE_STATS_SPECIES_RE = re.compile(r"^\s*db\s+([A-Z0-9_]+)\s*;")
MOVE_DATA_RE = re.compile(r"^\s*move\s+([A-Z0-9_]+)\s*,")
ITEM_ATTRIBUTE_RE = re.compile(r"^\s*item_attribute\b")
LI_ROW_RE = re.compile(r'^\s*li\s+"')
DNAME_ROW_RE = re.compile(r'^\s*dname\s+"')
DW_ROW_RE = re.compile(r"^\s*dw\s+[A-Za-z0-9_]+")
MAP_CONST_RE = re.compile(r"^\s*map_const\s+([A-Z0-9_]+),\s*([0-9]+),\s*([0-9]+)")
MAP_ATTRIBUTE_RE = re.compile(r"^\s*map_attributes\s+([A-Za-z0-9_]+),\s*([A-Z0-9_]+),")
BLOCK_LABEL_RE = re.compile(r"^([A-Za-z0-9_]+)_Blocks:\s*$")
BLOCK_INCBIN_RE = re.compile(r'^\s*INCBIN\s+"([^"]+\.blk)"\s*$')
TRAINER_MACRO_RE = re.compile(
    r"^\s*trainer\s+([A-Z0-9_]+),\s*([A-Z0-9_]+),\s*(EVENT_BEAT_[A-Z0-9_]+)\b"
)
SET_BEAT_EVENT_RE = re.compile(r"^\s*setevent\s+(EVENT_BEAT_[A-Z0-9_]+)\b")

LEADER_PALETTES = {
    "FALKNER": "gfx/trainers/falkner.gbcpal",
    "BUGSY": "gfx/trainers/bugsy.gbcpal",
    "WHITNEY": "gfx/trainers/whitney.gbcpal",
    "MORTY": "gfx/trainers/morty.gbcpal",
    "CHUCK": "gfx/trainers/chuck.gbcpal",
    "JASMINE": "gfx/trainers/jasmine.gbcpal",
    "PRYCE": "gfx/trainers/pryce.gbcpal",
    "CLAIR": "gfx/trainers/clair.gbcpal",
    "BROCK": "gfx/trainers/brock.gbcpal",
    "MISTY": "gfx/trainers/misty.gbcpal",
    "LT_SURGE": "gfx/trainers/lt_surge.gbcpal",
    "ERIKA": "gfx/trainers/erika.gbcpal",
    "JANINE": "gfx/trainers/janine.gbcpal",
    "SABRINA": "gfx/trainers/sabrina.gbcpal",
    "BLAINE": "gfx/trainers/blaine.gbcpal",
    "BLUE": "gfx/trainers/blue.gbcpal",
}

LEADER_PICS = {
    "FALKNER": "FalknerPic",
    "BUGSY": "BugsyPic",
    "WHITNEY": "WhitneyPic",
    "MORTY": "MortyPic",
    "CHUCK": "ChuckPic",
    "JASMINE": "JasminePic",
    "PRYCE": "PrycePic",
    "CLAIR": "ClairPic",
    "BROCK": "BrockPic",
    "MISTY": "MistyPic",
    "LT_SURGE": "LtSurgePic",
    "ERIKA": "ErikaPic",
    "JANINE": "JaninePic",
    "SABRINA": "SabrinaPic",
    "BLAINE": "BlainePic",
    "BLUE": "BluePic",
}

LEADER_BADGE_FLAGS = {
    "FALKNER": "ENGINE_ZEPHYRBADGE",
    "BUGSY": "ENGINE_HIVEBADGE",
    "WHITNEY": "ENGINE_PLAINBADGE",
    "MORTY": "ENGINE_FOGBADGE",
    "CHUCK": "ENGINE_STORMBADGE",
    "JASMINE": "ENGINE_MINERALBADGE",
    "PRYCE": "ENGINE_GLACIERBADGE",
    "CLAIR": "ENGINE_RISINGBADGE",
    "BROCK": "ENGINE_BOULDERBADGE",
    "MISTY": "ENGINE_CASCADEBADGE",
    "LT_SURGE": "ENGINE_THUNDERBADGE",
    "ERIKA": "ENGINE_RAINBOWBADGE",
    "JANINE": "ENGINE_SOULBADGE",
    "SABRINA": "ENGINE_MARSHBADGE",
    "BLAINE": "ENGINE_VOLCANOBADGE",
    "BLUE": "ENGINE_EARTHBADGE",
}

LEADER_REWARDS = {
    "FALKNER": ("EVENT_GOT_TM31_MUD_SLAP", "TM_VOUCHER"),
    "BUGSY": ("EVENT_GOT_TM49_FURY_CUTTER", "TM_VOUCHER"),
    "WHITNEY": ("EVENT_GOT_TM45_ATTRACT", "TM_VOUCHER"),
    "MORTY": ("EVENT_GOT_TM30_SHADOW_BALL", "TM_VOUCHER"),
    "CHUCK": ("EVENT_GOT_TM01_DYNAMICPUNCH", "TM_VOUCHER"),
    "JASMINE": ("EVENT_GOT_TM23_IRON_TAIL", "TM_VOUCHER"),
    "PRYCE": ("EVENT_GOT_TM16_ICY_WIND", "TM_VOUCHER"),
    "CLAIR": ("EVENT_GOT_TM24_DRAGONBREATH", "TM_VOUCHER"),
    "ERIKA": ("EVENT_GOT_TM19_GIGA_DRAIN", "TM_GIGA_DRAIN"),
    "JANINE": ("EVENT_GOT_TM06_TOXIC", "TM_TOXIC"),
}

CLAIR_BADGE_ROUTE_FILE = ROOT / "maps" / "DragonsDenB1F.asm"
CLAIR_BADGE_ROUTE_LABEL = "DragonsDenB1FDragonFangScript"
LEADERS_WITHOUT_STATUES = {"BLAINE"}


def fail(failures: list[str], message: str) -> None:
    failures.append(message)


def read_text(path: Path, failures: list[str]) -> str:
    if not path.exists():
        fail(failures, f"missing file: {path.relative_to(ROOT)}")
        return ""
    return path.read_text(encoding="utf-8")


def find_script_block(text: str, label: str) -> str | None:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == f"{label}:":
            start = index
            break
    if start is None:
        return None

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if TOP_LEVEL_LABEL_RE.match(lines[index]) and lines[index].strip() != f"{label}:":
            end = index
            break
    return "\n".join(lines[start:end])


def ordered_positions(block: str, needles: list[str]) -> list[int | None]:
    return [block.find(needle) if needle in block else None for needle in needles]


def parse_class_list(text: str, label: str) -> set[str]:
    classes: set[str] = set()
    in_list = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == f"{label}:":
            in_list = True
            continue
        if not in_list:
            continue
        if not line or line.startswith(";"):
            continue
        if line.endswith(":"):
            return classes
        match = CLASS_ENTRY_RE.match(raw_line)
        if not match:
            return classes
        value = match.group(1)
        if value == "-1":
            return classes
        classes.add(value)
    return classes


def parse_ai_tiers(text: str) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for raw_line in text.splitlines():
        match = AI_TIER_RE.match(raw_line)
        if match:
            trainer_class, trainer_id, _tier = match.groups()
            pairs.add((trainer_class, trainer_id))
    return pairs


def parse_constant_names(text: str, *, include_tmhm: bool = False) -> set[str]:
    constants: set[str] = set()
    for raw_line in text.splitlines():
        match = CONST_RE.match(raw_line)
        if match:
            constants.add(match.group(1))
            continue
        if include_tmhm:
            tmhm_match = ADD_TMHM_RE.match(raw_line)
            if tmhm_match:
                prefix = tmhm_match.group(1).upper()
                constants.add(f"{prefix}_{tmhm_match.group(2)}")
    return constants


def parse_constant_indexes(text: str, *, include_tmhm: bool = False) -> dict[str, int]:
    constants: dict[str, int] = {}
    index = 0
    for raw_line in text.splitlines():
        const_def_match = CONST_DEF_RE.match(raw_line)
        if const_def_match:
            value = const_def_match.group(1)
            if value is None:
                index = 0
            elif value.startswith("$"):
                index = int(value[1:], 16)
            else:
                index = int(value, 10)
            continue

        match = CONST_RE.match(raw_line)
        if match:
            constants[match.group(1)] = index
            index += 1
            continue

        if include_tmhm:
            tmhm_match = ADD_TMHM_RE.match(raw_line)
            if tmhm_match:
                prefix = tmhm_match.group(1).upper()
                constants[f"{prefix}_{tmhm_match.group(2)}"] = index
                index += 1
    return constants


def parse_base_stat_species(text: str, failures: list[str]) -> set[str]:
    species: set[str] = set()
    for raw_line in text.splitlines():
        match = INCLUDE_RE.match(raw_line)
        if not match:
            continue
        include_path = ROOT / match.group(1)
        include_text = read_text(include_path, failures)
        if not include_text:
            continue
        species_match = BASE_STATS_SPECIES_RE.search(include_text)
        if species_match is None:
            fail(failures, f"base stats include lacks species row: {include_path.relative_to(ROOT)}")
            continue
        species.add(species_match.group(1))
    return species


def parse_move_data(text: str) -> set[str]:
    moves: set[str] = set()
    for raw_line in text.splitlines():
        match = MOVE_DATA_RE.match(raw_line)
        if match:
            moves.add(match.group(1))
    return moves


def count_rows(text: str, row_re: re.Pattern[str]) -> int:
    return sum(1 for raw_line in text.splitlines() if row_re.match(raw_line))


def map_name(leader: Leader) -> str:
    return Path(leader.map_file).stem


def map_constant_name(name: str) -> str:
    with_word_breaks = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", name)
    with_word_breaks = re.sub(r"(?<=[a-z])(?=[A-Z0-9])", "_", with_word_breaks)
    with_word_breaks = re.sub(r"(?<=[0-9])(?=[A-Za-z])", "_", with_word_breaks)
    with_word_breaks = re.sub(r"_(\d)_([FB])$", r"_\1\2", with_word_breaks)
    return with_word_breaks.upper()


def parse_map_constants(text: str) -> dict[str, tuple[int, int]]:
    constants: dict[str, tuple[int, int]] = {}
    for raw_line in text.splitlines():
        match = MAP_CONST_RE.match(raw_line)
        if match:
            map_id, width, height = match.groups()
            constants[map_id] = (int(width, 10), int(height, 10))
    return constants


def parse_map_rows(text: str) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped.startswith("map "):
            continue
        tokens = split_tokens(stripped[len("map ") :])
        if len(tokens) >= 8:
            rows[tokens[0]] = tokens
    return rows


def parse_map_attributes(text: str) -> dict[str, str]:
    attributes: dict[str, str] = {}
    for raw_line in text.splitlines():
        match = MAP_ATTRIBUTE_RE.match(raw_line)
        if match:
            name, map_id = match.groups()
            attributes[name] = map_id
    return attributes


def parse_script_includes(text: str) -> set[str]:
    includes: set[str] = set()
    for raw_line in text.splitlines():
        match = INCLUDE_RE.match(raw_line)
        if match:
            includes.add(match.group(1))
    return includes


def parse_block_resources(text: str) -> dict[str, str]:
    resources: dict[str, str] = {}
    current_map: str | None = None
    for raw_line in text.splitlines():
        label_match = BLOCK_LABEL_RE.match(raw_line)
        if label_match:
            current_map = label_match.group(1)
            continue
        incbin_match = BLOCK_INCBIN_RE.match(raw_line)
        if incbin_match and current_map is not None:
            resources[current_map] = incbin_match.group(1)
            current_map = None
    return resources


def parse_object_constants(text: str) -> set[str]:
    constants: set[str] = set()
    in_object_constants = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "object_const_def":
            in_object_constants = True
            continue
        if not in_object_constants:
            continue
        if line.endswith("_MapScripts:"):
            return constants
        match = CONST_RE.match(raw_line)
        if match:
            constants.add(match.group(1))
    return constants


def parse_object_events(text: str) -> list[list[str]]:
    events: list[list[str]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped.startswith("object_event "):
            continue
        tokens = split_tokens(stripped[len("object_event ") :])
        events.append(tokens)
    return events


def parse_set_beat_events(block: str) -> list[str]:
    events: list[str] = []
    for raw_line in block.splitlines():
        match = SET_BEAT_EVENT_RE.match(raw_line)
        if match:
            events.append(match.group(1))
    return events


def parse_trainer_event_refs() -> dict[str, list[TrainerEventRef]]:
    refs: dict[str, list[TrainerEventRef]] = {}
    for map_path in (ROOT / "maps").glob("*.asm"):
        text = map_path.read_text(encoding="utf-8")
        object_events = parse_object_events(text)
        object_trainer_labels = {
            tokens[11] for tokens in object_events if len(tokens) >= 12 and tokens[9] == "OBJECTTYPE_TRAINER"
        }
        object_script_labels = {
            tokens[11] for tokens in object_events if len(tokens) >= 12 and tokens[9] == "OBJECTTYPE_SCRIPT"
        }
        current_label: str | None = None
        for raw_line in text.splitlines():
            label_match = TOP_LEVEL_LABEL_RE.match(raw_line)
            if label_match:
                current_label = raw_line.split(":", 1)[0]
                continue
            trainer_match = TRAINER_MACRO_RE.match(raw_line)
            if trainer_match and current_label is not None:
                trainer_class, trainer_id, event = trainer_match.groups()
                if current_label not in object_trainer_labels:
                    continue
                refs.setdefault(event, []).append(
                    TrainerEventRef(
                        map_file=str(map_path.relative_to(ROOT)).replace("\\", "/"),
                        trainer_label=current_label,
                        trainer_class=trainer_class,
                        trainer_id=trainer_id,
                    )
                )

        for label in object_script_labels:
            block = find_script_block(text, label)
            if block is None or "loadtrainer " not in block or "startbattle" not in block:
                continue
            event_matches = parse_set_beat_events(block)
            if len(event_matches) != 1:
                continue
            loadtrainer_match = re.search(r"\bloadtrainer\s+([A-Z0-9_]+),\s*([A-Z0-9_]+)", block)
            if loadtrainer_match is None:
                continue
            trainer_class, trainer_id = loadtrainer_match.groups()
            refs.setdefault(event_matches[0], []).append(
                TrainerEventRef(
                    map_file=str(map_path.relative_to(ROOT)).replace("\\", "/"),
                    trainer_label=label,
                    trainer_class=trainer_class,
                    trainer_id=trainer_id,
                )
            )
    return refs


def parse_trainer_class_order(text: str) -> list[str]:
    classes: list[str] = []
    for raw_line in text.splitlines():
        match = TRAINERCLASS_RE.match(raw_line)
        if match:
            trainer_class = match.group(1)
            if trainer_class != "TRAINER_NONE":
                classes.append(trainer_class)
    return classes


def parse_party_pointer_table(text: str) -> list[str]:
    in_table = False
    groups: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "TrainerGroups:":
            in_table = True
            continue
        if not in_table:
            continue
        if not line or line.startswith(";") or line.startswith("table_width"):
            continue
        if line.startswith("assert_table_length"):
            return groups
        match = PARTY_POINTER_RE.match(raw_line)
        if not match:
            continue
        groups.append(match.group(1))
    return groups


def build_trainer_group_map(
    trainer_classes: list[str],
    party_pointer_groups: list[str],
    failures: list[str],
) -> dict[str, str]:
    if len(trainer_classes) != len(party_pointer_groups):
        fail(
            failures,
            "trainer class/pointer table length mismatch: "
            f"classes={len(trainer_classes)} pointers={len(party_pointer_groups)}",
        )
    return dict(zip(trainer_classes, party_pointer_groups))


def parse_class_names(text: str) -> list[str]:
    names: list[str] = []
    for raw_line in text.splitlines():
        match = CLASS_NAME_RE.match(raw_line)
        if match:
            names.append(match.group(1))
    return names


def parse_trainer_attributes(text: str) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    pending: list[str] = []
    in_table = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "TrainerClassAttributes:":
            in_table = True
            continue
        if not in_table:
            continue
        if not line or line.startswith(";") or line.startswith("table_width"):
            continue
        if line.startswith("assert_table_length"):
            break
        db_match = ATTRIBUTE_DB_RE.match(raw_line)
        dw_match = ATTRIBUTE_DW_RE.match(raw_line)
        if db_match:
            pending.append(db_match.group(1).strip())
        elif dw_match:
            pending.append(dw_match.group(1).strip())
        if len(pending) == 4:
            rows.append((pending[0], pending[1], pending[2], pending[3]))
            pending = []
    return rows


def parse_dvs(text: str) -> list[tuple[int, int, int, int]]:
    rows: list[tuple[int, int, int, int]] = []
    for raw_line in text.splitlines():
        match = DV_RE.match(raw_line)
        if match:
            rows.append(tuple(int(value) for value in match.groups()))
    return rows


def parse_pic_pointers(text: str) -> list[str]:
    pics: list[str] = []
    for raw_line in text.splitlines():
        match = PIC_RE.match(raw_line)
        if match:
            pics.append(match.group(1))
    return pics


def parse_palette_paths(text: str) -> list[str]:
    paths: list[str] = []
    for raw_line in text.splitlines():
        match = PALETTE_RE.match(raw_line)
        if match:
            paths.append(match.group(1))
    return paths


def parse_encounter_music(text: str) -> list[str]:
    music: list[str] = []
    for raw_line in text.splitlines():
        match = MUSIC_RE.match(raw_line)
        if match:
            music.append(match.group(1))
    return music


def require_table_index[T](
    table: list[T],
    index: int,
    table_name: str,
    leader: Leader,
    failures: list[str],
) -> T | None:
    if not 0 <= index < len(table):
        fail(
            failures,
            f"{leader.name}: {table_name} missing index {index} for {leader.trainer_class}",
        )
        return None
    return table[index]


def check_class_support_tables(
    leader: Leader,
    trainer_class_index: dict[str, int],
    class_names: list[str],
    trainer_attributes: list[tuple[str, str, str, str]],
    dvs: list[tuple[int, int, int, int]],
    pics: list[str],
    palettes: list[str],
    encounter_music: list[str],
    item_constants: set[str],
    failures: list[str],
) -> None:
    class_index = trainer_class_index.get(leader.trainer_class)
    if class_index is None:
        fail(failures, f"{leader.name}: missing trainer class index for {leader.trainer_class}")
        return
    table_index = class_index - 1

    class_name = require_table_index(class_names, table_index, "TrainerClassNames", leader, failures)
    if class_name != "LEADER":
        fail(failures, f"{leader.name}: class name is `{class_name}`, expected `LEADER`")

    attributes = require_table_index(
        trainer_attributes,
        table_index,
        "TrainerClassAttributes",
        leader,
        failures,
    )
    if attributes is not None:
        items_raw, reward_raw, ai_flags, context_flags = attributes
        items = [token.strip() for token in items_raw.split(",")]
        if len(items) != 2:
            fail(failures, f"{leader.name}: trainer item attribute row is malformed: `{items_raw}`")
        for item in items:
            if item not in item_constants:
                fail(failures, f"{leader.name}: trainer item attribute uses unknown item `{item}`")
        try:
            reward = int(reward_raw, 10)
        except ValueError:
            reward = 0
        if reward <= 0:
            fail(failures, f"{leader.name}: trainer base reward must be positive, found `{reward_raw}`")
        if "AI_BASIC" not in ai_flags or "AI_SMART" not in ai_flags:
            fail(failures, f"{leader.name}: trainer AI flags lack AI_BASIC or AI_SMART: `{ai_flags}`")
        if "CONTEXT_USE" not in context_flags or "SWITCH_SOMETIMES" not in context_flags:
            fail(failures, f"{leader.name}: context flags lack CONTEXT_USE/SWITCH_SOMETIMES: `{context_flags}`")

    dv_row = require_table_index(dvs, table_index, "TrainerClassDVs", leader, failures)
    if dv_row is not None:
        for value in dv_row:
            if not 0 <= value <= 15:
                fail(failures, f"{leader.name}: DV value out of nybble range: {dv_row}")

    pic = require_table_index(pics, table_index, "TrainerPicPointers", leader, failures)
    expected_pic = LEADER_PICS[leader.trainer_class]
    if pic != expected_pic:
        fail(failures, f"{leader.name}: pic pointer is `{pic}`, expected `{expected_pic}`")

    palette = require_table_index(
        palettes,
        class_index,
        "TrainerPalettes",
        leader,
        failures,
    )
    expected_palette = LEADER_PALETTES[leader.trainer_class]
    if palette != expected_palette:
        fail(failures, f"{leader.name}: palette path is `{palette}`, expected `{expected_palette}`")
    elif not (ROOT / palette).exists():
        fail(failures, f"{leader.name}: palette file missing: {palette}")

    music = require_table_index(
        encounter_music,
        class_index,
        "TrainerEncounterMusic",
        leader,
        failures,
    )
    if music is not None and not music.startswith("MUSIC_"):
        fail(failures, f"{leader.name}: malformed encounter music `{music}`")


def split_tokens(raw_db_payload: str) -> list[str]:
    return [token.strip() for token in raw_db_payload.split(",")]


def parse_party_entries(text: str) -> dict[str, list[PartyEntry]]:
    entries: dict[str, list[PartyEntry]] = {}
    current_group: str | None = None
    active_type: str | None = None
    active_mons: list[PartyMon] = []

    for raw_line in text.splitlines():
        group_match = GROUP_RE.match(raw_line)
        if group_match:
            if current_group is not None and active_type is not None:
                entries.setdefault(current_group, []).append(
                    PartyEntry(current_group, active_type, tuple(active_mons))
                )
            current_group = group_match.group(1)
            active_type = None
            active_mons = []
            continue

        if current_group is None:
            continue

        trainer_match = TRAINER_RE.match(raw_line)
        if trainer_match:
            if active_type is not None:
                entries.setdefault(current_group, []).append(
                    PartyEntry(current_group, active_type, tuple(active_mons))
                )
            active_type = trainer_match.group(1)
            active_mons = []
            continue

        if active_type is None:
            continue

        db_match = DB_RE.match(raw_line)
        if not db_match:
            continue
        tokens = split_tokens(db_match.group(1))
        if not tokens:
            continue
        if tokens[0] == "-1":
            entries.setdefault(current_group, []).append(
                PartyEntry(current_group, active_type, tuple(active_mons))
            )
            active_type = None
            active_mons = []
            continue

        if active_type != "TRAINERTYPE_ITEM_MOVES":
            active_mons.append(PartyMon(0, "", "", ("", "", "", "")))
            continue
        if len(tokens) != 7:
            active_mons.append(PartyMon(0, "", "", ("", "", "", "")))
            continue
        try:
            level = int(tokens[0], 10)
        except ValueError:
            level = 0
        active_mons.append(
            PartyMon(
                level=level,
                species=tokens[1],
                item=tokens[2],
                moves=(tokens[3], tokens[4], tokens[5], tokens[6]),
            )
        )

    if current_group is not None and active_type is not None:
        entries.setdefault(current_group, []).append(
            PartyEntry(current_group, active_type, tuple(active_mons))
        )
    return entries


def trainer_id_declared(text: str, trainer_class: str, trainer_id: str) -> bool:
    class_line = f"trainerclass {trainer_class}"
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith(class_line):
            for following in lines[index + 1 :]:
                stripped = following.strip()
                if stripped.startswith("trainerclass "):
                    return False
                if stripped == f"const {trainer_id}":
                    return True
            return False
    return False


def party_group_has_item_moves(text: str, group: str) -> bool:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == f"{group}:":
            for following in lines[index + 1 : index + 10]:
                if following.strip().endswith("Group:"):
                    return False
                if "TRAINERTYPE_ITEM_MOVES" in following:
                    return True
            return False
    return False


def check_party_data(
    leader: Leader,
    party_entries: dict[str, list[PartyEntry]],
    pokemon_constants: set[str],
    item_constants: set[str],
    move_constants: set[str],
    trainer_group_map: dict[str, str],
    failures: list[str],
) -> None:
    mapped_group = trainer_group_map.get(leader.trainer_class)
    if mapped_group != leader.party_group:
        fail(
            failures,
            f"{leader.name}: TrainerGroups maps {leader.trainer_class} to {mapped_group}, "
            f"expected {leader.party_group}",
        )

    entries = party_entries.get(leader.party_group, [])
    if len(entries) != 1:
        fail(
            failures,
            f"{leader.name}: expected exactly one party entry in {leader.party_group}, found {len(entries)}",
        )
        return

    entry = entries[0]
    if entry.trainer_type != "TRAINERTYPE_ITEM_MOVES":
        fail(
            failures,
            f"{leader.name}: expected TRAINERTYPE_ITEM_MOVES, found {entry.trainer_type}",
        )
        return
    if not 1 <= len(entry.mons) <= 6:
        fail(
            failures,
            f"{leader.name}: party size must be 1-6 mons, found {len(entry.mons)}",
        )

    for slot, mon in enumerate(entry.mons, start=1):
        if not 1 <= mon.level <= 100:
            fail(failures, f"{leader.name}: slot {slot} has invalid level {mon.level}")
        if mon.species not in pokemon_constants:
            fail(failures, f"{leader.name}: slot {slot} unknown species `{mon.species}`")
        if mon.item not in item_constants or mon.item == "NO_ITEM":
            fail(failures, f"{leader.name}: slot {slot} invalid held item `{mon.item}`")
        for move_slot, move in enumerate(mon.moves, start=1):
            if move not in move_constants or move == "NO_MOVE":
                fail(
                    failures,
                    f"{leader.name}: slot {slot} move {move_slot} invalid move `{move}`",
                )


def check_item_resource(
    owner: str,
    item: str,
    item_indexes: dict[str, int],
    item_attribute_count: int,
    item_name_count: int,
    item_description_count: int,
    failures: list[str],
) -> None:
    item_index = item_indexes.get(item)
    if item_index is None:
        fail(failures, f"{owner}: missing item constant index for `{item}`")
        return
    if item_index == 0:
        fail(failures, f"{owner}: resource check got non-resource item `{item}`")
        return
    resource_index = item_index - 1
    if resource_index >= item_attribute_count:
        fail(failures, f"{owner}: item `{item}` lacks ItemAttributes row")
    if resource_index >= item_name_count:
        fail(failures, f"{owner}: item `{item}` lacks ItemNames row")
    if resource_index >= item_description_count:
        fail(failures, f"{owner}: item `{item}` lacks ItemDescriptions row")


def check_battle_resources(
    leader: Leader,
    party_entries: dict[str, list[PartyEntry]],
    pokemon_indexes: dict[str, int],
    pokemon_base_stat_species: set[str],
    pokemon_name_count: int,
    move_indexes: dict[str, int],
    move_data: set[str],
    move_name_count: int,
    move_description_count: int,
    item_indexes: dict[str, int],
    item_attribute_count: int,
    item_name_count: int,
    item_description_count: int,
    failures: list[str],
) -> None:
    entries = party_entries.get(leader.party_group, [])
    if len(entries) != 1:
        return

    for slot, mon in enumerate(entries[0].mons, start=1):
        owner = f"{leader.name} slot {slot}"
        species_index = pokemon_indexes.get(mon.species)
        if species_index is None:
            fail(failures, f"{owner}: missing species constant index for `{mon.species}`")
        elif species_index - 1 >= pokemon_name_count:
            fail(failures, f"{owner}: species `{mon.species}` lacks PokemonNames row")
        if mon.species not in pokemon_base_stat_species:
            fail(failures, f"{owner}: species `{mon.species}` lacks BaseData row")

        check_item_resource(
            owner,
            mon.item,
            item_indexes,
            item_attribute_count,
            item_name_count,
            item_description_count,
            failures,
        )

        for move_slot, move in enumerate(mon.moves, start=1):
            move_owner = f"{owner} move {move_slot}"
            move_index = move_indexes.get(move)
            if move_index is None:
                fail(failures, f"{move_owner}: missing move constant index for `{move}`")
                continue
            if move_index == 0:
                fail(failures, f"{move_owner}: resource check got non-resource move `{move}`")
                continue
            resource_index = move_index - 1
            if move not in move_data:
                fail(failures, f"{move_owner}: move `{move}` lacks Moves row")
            if resource_index >= move_name_count:
                fail(failures, f"{move_owner}: move `{move}` lacks MoveNames row")
            if resource_index >= move_description_count:
                fail(failures, f"{move_owner}: move `{move}` lacks MoveDescriptions row")

    reward = LEADER_REWARDS.get(leader.trainer_class)
    if reward is not None:
        _reward_event, reward_item = reward
        check_item_resource(
            f"{leader.name} reward",
            reward_item,
            item_indexes,
            item_attribute_count,
            item_name_count,
            item_description_count,
            failures,
        )


def check_map_resources(
    leader: Leader,
    map_constants: dict[str, tuple[int, int]],
    map_rows: dict[str, list[str]],
    map_attributes: dict[str, str],
    map_script_includes: set[str],
    map_block_resources: dict[str, str],
    event_constants: set[str],
    failures: list[str],
) -> None:
    name = map_name(leader)
    map_id = map_constant_name(name)
    map_path = ROOT / leader.map_file
    text = read_text(map_path, failures)
    if not text:
        return

    if leader.map_file not in map_script_includes:
        fail(failures, f"{leader.name}: map script file is not included: {leader.map_file}")

    dimensions = map_constants.get(map_id)
    if dimensions is None:
        fail(failures, f"{leader.name}: missing map_const for {map_id}")
        width_blocks = height_blocks = 0
    else:
        width_blocks, height_blocks = dimensions

    attr_map_id = map_attributes.get(name)
    if attr_map_id != map_id:
        fail(failures, f"{leader.name}: map_attributes id is `{attr_map_id}`, expected `{map_id}`")

    row = map_rows.get(name)
    if row is None:
        fail(failures, f"{leader.name}: missing MapGroup map row for {name}")
    else:
        if row[2] != "INDOOR":
            fail(failures, f"{leader.name}: map environment is `{row[2]}`, expected `INDOOR`")
        if row[4] != "MUSIC_GYM":
            fail(failures, f"{leader.name}: map music is `{row[4]}`, expected `MUSIC_GYM`")
        if row[5] != "TRUE":
            fail(failures, f"{leader.name}: gym map phone-service flag is `{row[5]}`, expected `TRUE`")

    block_path = map_block_resources.get(name)
    expected_block_path = f"maps/{name}.blk"
    if block_path != expected_block_path:
        fail(failures, f"{leader.name}: block resource is `{block_path}`, expected `{expected_block_path}`")
    elif not (ROOT / block_path).exists():
        fail(failures, f"{leader.name}: block file missing: {block_path}")

    if f"{name}_MapScripts:" not in text:
        fail(failures, f"{leader.name}: missing {name}_MapScripts label")
    if f"{name}_MapEvents:" not in text:
        fail(failures, f"{leader.name}: missing {name}_MapEvents label")
    if "def_object_events" not in text:
        fail(failures, f"{leader.name}: map lacks def_object_events")

    object_suffix = leader.trainer_class.split("_")[-1]
    object_constants = parse_object_constants(text)
    if not any(value.endswith(f"_{object_suffix}") for value in object_constants):
        fail(failures, f"{leader.name}: object_const_def lacks a leader object ending in _{object_suffix}")

    matching_events = []
    for tokens in parse_object_events(text):
        if len(tokens) < 13:
            continue
        if (
            tokens[2] == leader.sprite
            and tokens[9] == "OBJECTTYPE_SCRIPT"
            and tokens[11] == leader.script_label
        ):
            matching_events.append(tokens)

    if len(matching_events) != 1:
        fail(failures, f"{leader.name}: expected one leader object_event, found {len(matching_events)}")
        return

    event = matching_events[0]
    try:
        object_x = int(event[0], 10)
        object_y = int(event[1], 10)
    except ValueError:
        fail(failures, f"{leader.name}: leader object_event has nonnumeric coordinates")
        return
    if dimensions is not None:
        if not 0 <= object_x < width_blocks * 2:
            fail(failures, f"{leader.name}: leader object x={object_x} outside map width {width_blocks * 2}")
        if not 0 <= object_y < height_blocks * 2:
            fail(failures, f"{leader.name}: leader object y={object_y} outside map height {height_blocks * 2}")

    visibility_event = event[12]
    if visibility_event != "-1" and visibility_event not in event_constants:
        fail(failures, f"{leader.name}: leader object visibility event is unknown: {visibility_event}")


def check_map_script(leader: Leader, failures: list[str]) -> None:
    map_path = ROOT / leader.map_file
    text = read_text(map_path, failures)
    if not text:
        return

    block = find_script_block(text, leader.script_label)
    if block is None:
        fail(failures, f"{leader.name}: missing script {leader.script_label} in {leader.map_file}")
        return

    required_snippets = [
        "winlosstext",
        f"loadtrainer {leader.trainer_class}, {leader.trainer_id}",
        "startbattle",
        "reloadmapafterbattle",
        f"setevent {leader.beat_event}",
    ]
    for snippet in required_snippets:
        if snippet not in block:
            fail(failures, f"{leader.name}: script missing `{snippet}`")

    positions = ordered_positions(block, required_snippets)
    if all(position is not None for position in positions):
        ordered = sorted(position for position in positions if position is not None)
        if positions != ordered:
            fail(failures, f"{leader.name}: script battle commands are out of expected order")

    object_event_re = re.compile(
        rf"object_event\b.*\b{leader.sprite}\b.*\bOBJECTTYPE_SCRIPT\b.*\b{leader.script_label}\b"
    )
    if not object_event_re.search(text):
        fail(
            failures,
            f"{leader.name}: no object_event wires {leader.sprite} to {leader.script_label}",
        )


def check_gym_trainer_sweep(
    leader: Leader,
    event_constants: set[str],
    trainer_event_refs: dict[str, list[TrainerEventRef]],
    trainer_constants_text: str,
    failures: list[str],
) -> None:
    map_path = ROOT / leader.map_file
    text = read_text(map_path, failures)
    if not text:
        return
    block = find_script_block(text, leader.script_label)
    if block is None:
        return

    sweep_events = [
        event
        for event in parse_set_beat_events(block)
        if event != leader.beat_event
    ]
    for event in sweep_events:
        if event not in event_constants:
            fail(failures, f"{leader.name}: sweep event constant is missing: {event}")
            continue

        refs = trainer_event_refs.get(event, [])
        if not refs:
            fail(failures, f"{leader.name}: sweep event `{event}` has no trainer object/script reference")
            continue

        for ref in refs:
            if not trainer_id_declared(trainer_constants_text, ref.trainer_class, ref.trainer_id):
                fail(
                    failures,
                    f"{leader.name}: sweep event `{event}` references undeclared trainer "
                    f"{ref.trainer_class}, {ref.trainer_id} in {ref.map_file}",
                )


def check_leader_aftermath(
    leader: Leader,
    event_constants: set[str],
    engine_flags: set[str],
    item_constants: set[str],
    clair_badge_route_text: str,
    failures: list[str],
) -> None:
    map_path = ROOT / leader.map_file
    text = read_text(map_path, failures)
    if not text:
        return
    block = find_script_block(text, leader.script_label)
    if block is None:
        return

    if leader.beat_event not in event_constants:
        fail(failures, f"{leader.name}: beat event constant is missing: {leader.beat_event}")

    badge_flag = LEADER_BADGE_FLAGS[leader.trainer_class]
    if badge_flag not in engine_flags:
        fail(failures, f"{leader.name}: badge flag constant is missing: {badge_flag}")

    if f"checkflag {badge_flag}" not in text:
        fail(failures, f"{leader.name}: map/statue never checks badge flag `{badge_flag}`")
    if leader.trainer_class not in LEADERS_WITHOUT_STATUES:
        trainer_name_call = f"gettrainername STRING_BUFFER_4, {leader.trainer_class}, {leader.trainer_id}"
        if trainer_name_call not in text:
            fail(failures, f"{leader.name}: gym statue lacks `{trainer_name_call}`")

    if leader.trainer_class == "CLAIR":
        if f"checkflag {badge_flag}" not in block:
            fail(failures, f"{leader.name}: leader script does not branch on `{badge_flag}`")
        clair_block = find_script_block(clair_badge_route_text, CLAIR_BADGE_ROUTE_LABEL)
        if clair_block is None:
            fail(failures, f"Clair: missing badge route script {CLAIR_BADGE_ROUTE_LABEL}")
        else:
            required_clair_route = [
                "giveitem DRAGON_FANG",
                "writetext DragonShrinePlayerReceivedRisingBadgeText",
                f"setflag {badge_flag}",
                "specialphonecall SPECIALCALL_MASTERBALL",
            ]
            for snippet in required_clair_route:
                if snippet not in clair_block:
                    fail(failures, f"Clair: Dragon's Den badge route missing `{snippet}`")
    elif f"setflag {badge_flag}" not in block:
        fail(failures, f"{leader.name}: leader aftermath never sets `{badge_flag}`")

    reward = LEADER_REWARDS.get(leader.trainer_class)
    if reward is None:
        return

    reward_event, reward_item = reward
    if reward_event not in event_constants:
        fail(failures, f"{leader.name}: reward event constant is missing: {reward_event}")
    if reward_item not in item_constants:
        fail(failures, f"{leader.name}: reward item constant is missing: {reward_item}")

    reward_snippets = [
        f"checkevent {reward_event}",
        f"verbosegiveitem {reward_item}",
        f"setevent {reward_event}",
    ]
    for snippet in reward_snippets:
        if snippet not in block:
            fail(failures, f"{leader.name}: reward flow missing `{snippet}`")

    positions = ordered_positions(block, reward_snippets)
    if all(position is not None for position in positions):
        ordered = sorted(position for position in positions if position is not None)
        if positions != ordered:
            fail(failures, f"{leader.name}: reward gate/give/set commands are out of order")


def main() -> int:
    failures: list[str] = []

    leaders_text = read_text(LEADERS_FILE, failures)
    ai_tiers_text = read_text(AI_TIERS_FILE, failures)
    parties_text = read_text(PARTIES_FILE, failures)
    party_pointers_text = read_text(PARTY_POINTERS_FILE, failures)
    trainer_attributes_text = read_text(TRAINER_ATTRIBUTES_FILE, failures)
    trainer_class_names_text = read_text(TRAINER_CLASS_NAMES_FILE, failures)
    trainer_dvs_text = read_text(TRAINER_DVS_FILE, failures)
    trainer_pics_text = read_text(TRAINER_PICS_FILE, failures)
    trainer_palettes_text = read_text(TRAINER_PALETTES_FILE, failures)
    trainer_encounter_music_text = read_text(TRAINER_ENCOUNTER_MUSIC_FILE, failures)
    trainer_constants_text = read_text(TRAINER_CONSTANTS_FILE, failures)
    pokemon_constants_text = read_text(POKEMON_CONSTANTS_FILE, failures)
    move_constants_text = read_text(MOVE_CONSTANTS_FILE, failures)
    item_constants_text = read_text(ITEM_CONSTANTS_FILE, failures)
    event_flags_text = read_text(EVENT_FLAGS_FILE, failures)
    engine_flags_text = read_text(ENGINE_FLAGS_FILE, failures)
    pokemon_base_stats_text = read_text(POKEMON_BASE_STATS_FILE, failures)
    pokemon_names_text = read_text(POKEMON_NAMES_FILE, failures)
    move_data_text = read_text(MOVE_DATA_FILE, failures)
    move_names_text = read_text(MOVE_NAMES_FILE, failures)
    move_descriptions_text = read_text(MOVE_DESCRIPTIONS_FILE, failures)
    item_attributes_data_text = read_text(ITEM_ATTRIBUTES_DATA_FILE, failures)
    item_names_text = read_text(ITEM_NAMES_FILE, failures)
    item_descriptions_text = read_text(ITEM_DESCRIPTIONS_FILE, failures)
    map_constants_text = read_text(MAP_CONSTANTS_FILE, failures)
    maps_text = read_text(MAPS_FILE, failures)
    map_attributes_text = read_text(MAP_ATTRIBUTES_FILE, failures)
    map_scripts_text = read_text(MAP_SCRIPTS_FILE, failures)
    map_blocks_text = read_text(MAP_BLOCKS_FILE, failures)
    clair_badge_route_text = read_text(CLAIR_BADGE_ROUTE_FILE, failures)

    leader_tables = {
        "GymLeaders": parse_class_list(leaders_text, "GymLeaders"),
        "KantoGymLeaders": parse_class_list(leaders_text, "KantoGymLeaders"),
    }
    ai_tier_pairs = parse_ai_tiers(ai_tiers_text)
    party_entries = parse_party_entries(parties_text)
    trainer_classes = parse_trainer_class_order(trainer_constants_text)
    trainer_class_index = {
        trainer_class: index
        for index, trainer_class in enumerate(trainer_classes, start=1)
    }
    trainer_group_map = build_trainer_group_map(
        trainer_classes,
        parse_party_pointer_table(party_pointers_text),
        failures,
    )
    class_names = parse_class_names(trainer_class_names_text)
    trainer_attributes = parse_trainer_attributes(trainer_attributes_text)
    trainer_dvs = parse_dvs(trainer_dvs_text)
    trainer_pics = parse_pic_pointers(trainer_pics_text)
    trainer_palettes = parse_palette_paths(trainer_palettes_text)
    trainer_encounter_music = parse_encounter_music(trainer_encounter_music_text)
    pokemon_constants = parse_constant_names(pokemon_constants_text)
    move_constants = parse_constant_names(move_constants_text)
    item_constants = parse_constant_names(item_constants_text, include_tmhm=True)
    event_constants = parse_constant_names(event_flags_text)
    engine_flags = parse_constant_names(engine_flags_text)
    pokemon_indexes = parse_constant_indexes(pokemon_constants_text)
    move_indexes = parse_constant_indexes(move_constants_text)
    item_indexes = parse_constant_indexes(item_constants_text, include_tmhm=True)
    pokemon_base_stat_species = parse_base_stat_species(pokemon_base_stats_text, failures)
    pokemon_name_count = count_rows(pokemon_names_text, DNAME_ROW_RE)
    move_data = parse_move_data(move_data_text)
    move_name_count = count_rows(move_names_text, LI_ROW_RE)
    move_description_count = count_rows(move_descriptions_text, DW_ROW_RE)
    item_attribute_count = count_rows(item_attributes_data_text, ITEM_ATTRIBUTE_RE)
    item_name_count = count_rows(item_names_text, LI_ROW_RE)
    item_description_count = count_rows(item_descriptions_text, DW_ROW_RE)
    map_constants = parse_map_constants(map_constants_text)
    map_rows = parse_map_rows(maps_text)
    map_attributes = parse_map_attributes(map_attributes_text)
    map_script_includes = parse_script_includes(map_scripts_text)
    map_block_resources = parse_block_resources(map_blocks_text)
    trainer_event_refs = parse_trainer_event_refs()

    for leader in LEADERS:
        check_map_resources(
            leader,
            map_constants,
            map_rows,
            map_attributes,
            map_script_includes,
            map_block_resources,
            event_constants,
            failures,
        )
        check_map_script(leader, failures)
        check_gym_trainer_sweep(
            leader,
            event_constants,
            trainer_event_refs,
            trainer_constants_text,
            failures,
        )
        check_leader_aftermath(
            leader,
            event_constants,
            engine_flags,
            item_constants,
            clair_badge_route_text,
            failures,
        )
        check_party_data(
            leader,
            party_entries,
            pokemon_constants,
            item_constants,
            move_constants,
            trainer_group_map,
            failures,
        )
        check_battle_resources(
            leader,
            party_entries,
            pokemon_indexes,
            pokemon_base_stat_species,
            pokemon_name_count,
            move_indexes,
            move_data,
            move_name_count,
            move_description_count,
            item_indexes,
            item_attribute_count,
            item_name_count,
            item_description_count,
            failures,
        )
        check_class_support_tables(
            leader,
            trainer_class_index,
            class_names,
            trainer_attributes,
            trainer_dvs,
            trainer_pics,
            trainer_palettes,
            trainer_encounter_music,
            item_constants,
            failures,
        )

        if leader.trainer_class not in leader_tables.get(leader.leader_table, set()):
            fail(
                failures,
                f"{leader.name}: {leader.trainer_class} missing from {leader.leader_table}",
            )
        if (leader.trainer_class, leader.trainer_id) not in ai_tier_pairs:
            fail(
                failures,
                f"{leader.name}: missing AI tier for {leader.trainer_class}, {leader.trainer_id}",
            )
        if not trainer_id_declared(trainer_constants_text, leader.trainer_class, leader.trainer_id):
            fail(
                failures,
                f"{leader.name}: missing trainer constant {leader.trainer_class}, {leader.trainer_id}",
            )
        if not party_group_has_item_moves(parties_text, leader.party_group):
            fail(
                failures,
                f"{leader.name}: {leader.party_group} missing TRAINERTYPE_ITEM_MOVES party",
            )

    if failures:
        for failure in failures:
            print(f"ERROR|{failure}", file=sys.stderr)
        print(f"FAIL|gym_leaders={len(LEADERS)}|issues={len(failures)}", file=sys.stderr)
        return 1

    print(
        "OK|gym_leaders=16|map_scripts=true|object_events=true|"
        "trainer_group_pointers=true|leader_tables=true|ai_tiers=true|"
        "party_groups=true|party_tokens=true|class_support_tables=true|"
        "badge_reward_aftermath=true|battle_resources=true|map_resources=true|"
        "gym_trainer_sweep=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
