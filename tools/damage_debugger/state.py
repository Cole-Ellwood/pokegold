"""Exact Pokemon state readers for damage and AI debugger reports."""

from __future__ import annotations

import hashlib
import io
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from tools.audit.trainer_parties import TrainerPartyEntry, TrainerPartyMon, parse_parties
from tools.trace import runtime as trace_runtime

from . import oracle
from . import tables


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROM = ROOT / "pokegold.gbc"
DEFAULT_SYMBOLS = ROOT / "pokegold.sym"
PARTYMON_STRUCT_LENGTH = 48
NUM_MOVES = 4
MAPSTATUS_HANDLE = 2
POST_CONTINUE_CACHE_VERSION = b"post-continue-loader-v2"
_TRAINER_PARTY_GROUPS: dict[int, str] | None = None
_LEVEL_UP_MOVES: dict[str, tuple[tuple[int, str], ...]] | None = None


class StateInputError(tables.InputError):
    """User-facing state resolution error."""


@dataclass(frozen=True)
class ExactPokemonState:
    species: str
    species_id: int
    level: int
    item_id: int
    item_name: str
    moves: tuple[int, int, int, int]
    move_names: tuple[str, str, str, str]
    current_hp: int
    max_hp: int
    atk: int
    defense: int
    speed: int
    sp_atk: int
    sp_def: int
    type1: int
    type2: int
    status: int = 0
    happiness: int = 70
    dvs: tuple[int, int, int, int] = (15, 15, 15, 15)


@dataclass(frozen=True)
class BattleContext:
    weather: int = oracle.WEATHER_NONE
    battle_turn: int = 1
    johto_badges: int = 0
    kanto_badges: int = 0
    link_mode: int = 0
    sleep_clause_active: bool = False
    attacker_stat_stages: Mapping[str, int] = field(default_factory=dict)
    defender_stat_stages: Mapping[str, int] = field(default_factory=dict)
    player_screens: int = 0
    enemy_screens: int = 0
    attacker_substatus: int = 0
    defender_substatus: int = 0
    revealed_moves: tuple[int, ...] = ()
    metronome_count: int = 0
    is_critical: bool = False
    initial_cur_damage: int = 0


@dataclass(frozen=True)
class TrainerConstant:
    trainer_id: str
    trainer_class: str
    class_id: int
    trainer_index: int


def load_species_constants() -> dict[str, int]:
    return {
        name: value
        for name, value in tables.parse_const_values(ROOT / "constants/pokemon_constants.asm").items()
        if name not in {"EGG", "NUM_POKEMON", "NUM_UNOWN"} and not name.startswith("UNOWN_")
    }


def load_move_constants() -> dict[str, int]:
    return tables.parse_const_values(ROOT / "constants/move_constants.asm")


def species_name_by_id() -> dict[int, str]:
    return {value: name for name, value in load_species_constants().items()}


def canonical_species_name(species: str) -> str:
    if re.fullmatch(r"UNOWN_[A-Z]", species):
        return "UNOWN"
    return species


def move_name_by_id() -> dict[int, str]:
    return {value: name for name, value in load_move_constants().items()}


def display_move_id(move_id: int) -> str:
    if move_id == 0:
        return "No Move"
    name = move_name_by_id().get(move_id, f"MOVE_{move_id:02X}")
    row = tables.load_moves().get(name)
    return tables.display_move(row) if row is not None else name.replace("_", " ").title()


def load_trainer_constants() -> dict[str, TrainerConstant]:
    constants: dict[str, TrainerConstant] = {}
    class_id = -1
    trainer_index = 0
    trainer_class = ""
    for raw in (ROOT / "constants/trainer_constants.asm").read_text(encoding="utf-8").splitlines():
        code = raw.split(";", 1)[0].strip()
        if not code:
            continue
        match = re.match(r"trainerclass\s+([A-Z0-9_]+)\b", code)
        if match:
            class_id += 1
            trainer_class = match.group(1)
            trainer_index = 0
            continue
        match = re.match(r"const\s+([A-Z0-9_]+)\b", code)
        if match and trainer_class:
            trainer_index += 1
            trainer_id = match.group(1)
            constants[trainer_id] = TrainerConstant(
                trainer_id=trainer_id,
                trainer_class=trainer_class,
                class_id=class_id,
                trainer_index=trainer_index,
            )
    return constants


def load_trainer_party_groups() -> dict[int, str]:
    global _TRAINER_PARTY_GROUPS
    if _TRAINER_PARTY_GROUPS is not None:
        return _TRAINER_PARTY_GROUPS
    groups: dict[int, str] = {}
    class_id = 1
    in_table = False
    for raw in (ROOT / "data/trainers/party_pointers.asm").read_text(encoding="utf-8").splitlines():
        code = raw.split(";", 1)[0].strip()
        if code == "TrainerGroups:":
            in_table = True
            continue
        if not in_table:
            continue
        if code.startswith("assert_table_length"):
            break
        match = re.match(r"dw\s+([A-Za-z0-9_]+Group)\b", code)
        if match:
            groups[class_id] = match.group(1)
            class_id += 1
    _TRAINER_PARTY_GROUPS = groups
    return groups


def parse_trainer_dvs() -> dict[str, tuple[int, int, int, int]]:
    dvs: dict[str, tuple[int, int, int, int]] = {}
    rows: list[tuple[int, int, int, int, str]] = []
    pattern = re.compile(
        r"^\s*dn\s+(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*;\s*([A-Z0-9_]+)"
    )
    for raw in (ROOT / "data/trainers/dvs.asm").read_text(encoding="utf-8").splitlines():
        match = pattern.match(raw)
        if match:
            atk, defense, speed, special, trainer_class = match.groups()
            rows.append((int(atk), int(defense), int(speed), int(special), trainer_class))
    for atk, defense, speed, special, trainer_class in rows:
        dvs[trainer_class] = (atk, defense, speed, special)
    return dvs


def dv_bytes(dvs: tuple[int, int, int, int]) -> tuple[int, int]:
    atk_dv, def_dv, speed_dv, special_dv = dvs
    return (
        ((atk_dv & 0xF) << 4) | (def_dv & 0xF),
        ((speed_dv & 0xF) << 4) | (special_dv & 0xF),
    )


def dvs_from_bytes(atk_def: int, speed_special: int) -> tuple[int, int, int, int]:
    return (
        (atk_def >> 4) & 0xF,
        atk_def & 0xF,
        (speed_special >> 4) & 0xF,
        speed_special & 0xF,
    )


def resolve_trainer_party(trainer_id: str) -> tuple[TrainerConstant, TrainerPartyEntry]:
    trainer_key = tables.normalize_name(trainer_id)
    constants = load_trainer_constants()
    if trainer_key not in constants:
        raise StateInputError(f"unknown trainer id '{trainer_id}'")
    trainer = constants[trainer_key]
    target_group = load_trainer_party_groups().get(trainer.class_id)
    if target_group is None:
        raise StateInputError(f"missing party group for trainer class {trainer.trainer_class}")
    parties = parse_parties(ROOT / "data/trainers/parties.asm")
    by_key = {(entry.group, entry.index): entry for entry in parties}
    entry = by_key.get((target_group, trainer.trainer_index))
    if entry is not None:
        return trainer, entry
    raise StateInputError(
        f"missing party row for {trainer.trainer_class} index {trainer.trainer_index}"
    )


def select_trainer_mon_index(entry: TrainerPartyEntry, selector: str | None) -> int:
    if not entry.mons:
        raise StateInputError(f"{entry.label} has no Pokemon")
    if selector is None or selector == "":
        return 0
    if selector.isdigit():
        index = int(selector)
        if not 1 <= index <= len(entry.mons):
            raise StateInputError(f"party index {index} out of range for {entry.label}")
        return index - 1
    species = tables.resolve_name(selector, tables.load_base_stats(), "species")
    matches = [(index, mon) for index, mon in enumerate(entry.mons) if mon.species == species]
    if not matches:
        raise StateInputError(f"{entry.label} has no {species}")
    if len(matches) > 1:
        raise StateInputError(f"{entry.label} has multiple {species}; use a party index")
    return matches[0][0]


def select_trainer_mon(entry: TrainerPartyEntry, selector: str | None) -> TrainerPartyMon:
    return entry.mons[select_trainer_mon_index(entry, selector)]


def trainer_state(spec: str) -> ExactPokemonState:
    parts = spec.split(":", 1)
    trainer_id = parts[0]
    selector = parts[1] if len(parts) == 2 else None
    trainer, entry = resolve_trainer_party(trainer_id)
    mon = select_trainer_mon(entry, selector)
    dvs_by_class = parse_trainer_dvs()
    dvs = dvs_by_class.get(trainer.trainer_class)
    if dvs is None:
        raise StateInputError(f"missing DVs for trainer class {trainer.trainer_class}")
    return state_from_trainer_mon(mon, trainer_dvs=dvs)


def state_from_trainer_mon(
    mon: TrainerPartyMon,
    *,
    trainer_dvs: tuple[int, int, int, int],
) -> ExactPokemonState:
    base_stats = tables.load_base_stats()
    species = tables.resolve_name(mon.species, base_stats, "species")
    row = base_stats[species]
    species_id = load_species_constants()[species]
    atk_dv, def_dv, speed_dv, special_dv = trainer_dvs
    hp_dv = ((atk_dv & 1) << 3) | ((def_dv & 1) << 2) | ((speed_dv & 1) << 1) | (special_dv & 1)
    max_hp = tables.compute_hp(row.hp, mon.level, hp_dv, 0)
    moves = move_ids_from_names(mon.moves or level_up_moves_for_species(species, mon.level))
    item_id = tables.resolve_item(mon.item or "NO_ITEM")
    types = tables.load_type_constants()
    return ExactPokemonState(
        species=species,
        species_id=species_id,
        level=mon.level,
        item_id=item_id,
        item_name=tables.display_item(item_id),
        moves=moves,
        move_names=tuple(display_move_id(move_id) for move_id in moves),
        current_hp=max_hp,
        max_hp=max_hp,
        atk=tables.compute_stat(row.atk, mon.level, atk_dv, 0, is_hp=False),
        defense=tables.compute_stat(row.def_, mon.level, def_dv, 0, is_hp=False),
        speed=tables.compute_stat(row.spe, mon.level, speed_dv, 0, is_hp=False),
        sp_atk=tables.compute_stat(row.sat, mon.level, special_dv, 0, is_hp=False),
        sp_def=tables.compute_stat(row.sdf, mon.level, special_dv, 0, is_hp=False),
        type1=types[row.type_a],
        type2=types[row.type_b],
        status=0,
        happiness=70,
        dvs=trainer_dvs,
    )


def move_ids_from_names(move_names: tuple[str, ...]) -> tuple[int, int, int, int]:
    constants = load_move_constants()
    out: list[int] = []
    for name in move_names[:NUM_MOVES]:
        key = tables.resolve_move(name) if name and name != "NO_MOVE" else "NO_MOVE"
        out.append(constants[key])
    while len(out) < NUM_MOVES:
        out.append(constants.get("NO_MOVE", 0))
    return tuple(out[:NUM_MOVES])  # type: ignore[return-value]


def load_level_up_moves() -> dict[str, tuple[tuple[int, str], ...]]:
    global _LEVEL_UP_MOVES
    if _LEVEL_UP_MOVES is not None:
        return _LEVEL_UP_MOVES
    species_order = []
    for raw in (ROOT / "constants/pokemon_constants.asm").read_text(encoding="utf-8").splitlines():
        code = raw.split(";", 1)[0].strip()
        if code.startswith("DEF NUM_POKEMON"):
            break
        match = re.match(r"const\s+([A-Z0-9_]+)\b", code)
        if match:
            species_order.append(match.group(1))
    pointer_labels = []
    for raw in (ROOT / "data/pokemon/evos_attacks_pointers.asm").read_text(encoding="utf-8").splitlines():
        match = re.match(r"\s*dw\s+([A-Za-z0-9_]+)EvosAttacks\b", raw)
        if match:
            pointer_labels.append(match.group(1))
    if len(pointer_labels) != len(species_order):
        raise StateInputError(
            f"learnset pointer/species mismatch: {len(pointer_labels)} pointers for {len(species_order)} species"
        )
    label_to_species = dict(zip(pointer_labels, species_order, strict=False))
    level_moves: dict[str, tuple[tuple[int, str], ...]] = {}
    current_label: str | None = None
    phase = "evolutions"
    moves: list[tuple[int, str]] = []
    for raw in (ROOT / "data/pokemon/evos_attacks.asm").read_text(encoding="utf-8").splitlines():
        label_match = re.match(r"^([A-Za-z0-9_]+)EvosAttacks:\s*$", raw)
        if label_match:
            if current_label is not None and current_label in label_to_species:
                level_moves[label_to_species[current_label]] = tuple(moves)
            current_label = label_match.group(1)
            phase = "evolutions"
            moves = []
            continue
        if current_label is None:
            continue
        code = raw.split(";", 1)[0].strip()
        if not code:
            continue
        if code.startswith("db 0"):
            if phase == "evolutions":
                phase = "moves"
                continue
            if current_label in label_to_species:
                level_moves[label_to_species[current_label]] = tuple(moves)
            current_label = None
            continue
        if phase != "moves" or not code.startswith("db "):
            continue
        values = [part.strip() for part in code[3:].split(",")]
        if len(values) >= 2 and values[0].isdigit():
            moves.append((int(values[0]), values[1]))
    if current_label is not None and current_label in label_to_species:
        level_moves[label_to_species[current_label]] = tuple(moves)
    _LEVEL_UP_MOVES = level_moves
    return level_moves


def level_up_moves_for_species(species: str, level: int) -> tuple[str, ...]:
    learned: list[str] = []
    for move_level, move in load_level_up_moves().get(species, ()):
        if move_level > level:
            break
        if move in learned:
            continue
        if len(learned) == NUM_MOVES:
            learned = learned[1:]
        learned.append(move)
    return tuple(learned)


def reject_unsupported_state_suffix(path: Path) -> None:
    if path.suffix.lower() == ".sgm":
        raise StateInputError(
            "VBA-M .sgm save-states are not supported yet; use .sav or PyBoy .state"
        )


def party_state_from_save(
    save_path: Path,
    slot: int,
    *,
    rom: Path = DEFAULT_ROM,
    symbols_path: Path = DEFAULT_SYMBOLS,
) -> ExactPokemonState:
    reject_unsupported_state_suffix(save_path)
    if save_path.suffix.lower() != ".sav":
        raise StateInputError(f"expected a .sav battery save, got {save_path}")
    state_path = cached_post_continue_state(save_path, rom=rom, symbols_path=symbols_path)
    return party_state_from_state(state_path, slot, rom=rom, symbols_path=symbols_path)


def party_state_from_state(
    state_path: Path,
    slot: int,
    *,
    rom: Path = DEFAULT_ROM,
    symbols_path: Path = DEFAULT_SYMBOLS,
) -> ExactPokemonState:
    reject_unsupported_state_suffix(state_path)
    if not 1 <= slot <= 6:
        raise StateInputError(f"party slot must be 1-6, got {slot}")
    if not state_path.exists():
        raise StateInputError(f"missing save-state: {state_path}")
    symbols = trace_runtime.parse_symbols(symbols_path)
    pyboy = trace_runtime.open_pyboy(rom, "PyBoy is required to read exact party state")
    trace_runtime.disable_realtime(pyboy)
    try:
        with state_path.open("rb") as fh:
            pyboy.load_state(fh)
        return read_party_slot_from_wram(pyboy, symbols, slot)
    finally:
        pyboy.stop(save=False)


def cached_post_continue_state(
    save_path: Path,
    *,
    rom: Path = DEFAULT_ROM,
    symbols_path: Path = DEFAULT_SYMBOLS,
) -> Path:
    if not save_path.exists():
        raise StateInputError(f"missing battery save: {save_path}")
    if not rom.exists():
        raise StateInputError(f"missing ROM: {rom}")
    digest = hashlib.sha256()
    digest.update(POST_CONTINUE_CACHE_VERSION)
    digest.update(save_path.read_bytes())
    digest.update(rom.read_bytes())
    cache_dir = ROOT / ".local/tmp/damage_debugger"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{digest.hexdigest()[:24]}.state"
    if cache_path.exists():
        return cache_path

    work_dir = cache_dir / f"{digest.hexdigest()[:24]}_work"
    work_dir.mkdir(parents=True, exist_ok=True)
    work_rom = work_dir / rom.name
    shutil.copy2(rom, work_rom)
    shutil.copy2(save_path, work_rom.with_suffix(work_rom.suffix + ".ram"))
    symbols = trace_runtime.parse_symbols(symbols_path)
    pyboy = trace_runtime.open_pyboy(work_rom, "PyBoy is required to read battery saves")
    trace_runtime.disable_realtime(pyboy)
    try:
        boot_continue(pyboy, symbols)
        with cache_path.open("wb") as fh:
            pyboy.save_state(fh)
    finally:
        pyboy.stop(save=False)
    return cache_path


def boot_continue(
    pyboy,
    symbols: dict[str, trace_runtime.Symbol],
    *,
    max_clock_attempts: int = 12,
) -> None:
    pyboy.tick(1800, False, False)
    for button_name in ("start", "a", "a", "a"):
        pyboy.button(button_name, delay=8)
        pyboy.tick(180, False, False)
        if post_continue_loaded(pyboy, symbols):
            return
    for _attempt in range(max_clock_attempts):
        pyboy.button("a", delay=8)
        pyboy.tick(180, False, False)
        if post_continue_loaded(pyboy, symbols):
            return
    raise StateInputError(f"Continue did not reach a loaded save state: {post_continue_status(pyboy, symbols)}")


def post_continue_loaded(pyboy, symbols: dict[str, trace_runtime.Symbol]) -> bool:
    try:
        party_count = trace_runtime.read_byte(pyboy, symbols["wPartyCount"])
        map_group = trace_runtime.read_byte(pyboy, symbols["wMapGroup"])
        map_number = trace_runtime.read_byte(pyboy, symbols["wMapNumber"])
        map_status = trace_runtime.read_byte(pyboy, symbols["wMapStatus"])
    except KeyError:
        return False
    return (
        1 <= party_count <= 6
        and map_group != 0
        and map_number != 0
        and map_status == MAPSTATUS_HANDLE
    )


def post_continue_status(pyboy, symbols: dict[str, trace_runtime.Symbol]) -> str:
    values: list[str] = []
    for name in ("wPartyCount", "wMapGroup", "wMapNumber", "wMapStatus"):
        symbol = symbols.get(name)
        if symbol is None:
            values.append(f"{name}=missing")
        else:
            values.append(f"{name}={trace_runtime.read_byte(pyboy, symbol)}")
    return ", ".join(values)


def read_party_slot_from_wram(
    pyboy,
    symbols: dict[str, trace_runtime.Symbol],
    slot: int,
) -> ExactPokemonState:
    if "wPartyCount" not in symbols:
        raise StateInputError("symbols missing wPartyCount")
    if "wPartyMons" not in symbols:
        raise StateInputError("symbols missing wPartyMons")
    party_count = trace_runtime.read_byte(pyboy, symbols["wPartyCount"])
    if not 1 <= party_count <= 6:
        raise StateInputError(f"invalid save party count {party_count}")
    if slot > party_count:
        raise StateInputError(f"party slot {slot} out of range; save has {party_count} Pokemon")
    base = symbols["wPartyMons"]
    offset = (slot - 1) * PARTYMON_STRUCT_LENGTH

    def byte(relative: int) -> int:
        return trace_runtime.read_byte(
            pyboy,
            trace_runtime.Symbol(base.bank, base.address + offset + relative),
        )

    def word_be(relative: int) -> int:
        return (byte(relative) << 8) | byte(relative + 1)

    species_id = byte(0)
    species_by_id = species_name_by_id()
    if species_id not in species_by_id:
        raise StateInputError(f"party slot {slot} has unknown species id {species_id}")
    species = canonical_species_name(species_by_id[species_id])
    base_stats = tables.load_base_stats()
    if species not in base_stats:
        raise StateInputError(f"party slot {slot} species {species} has no base stats row")
    row = base_stats[species]
    moves = tuple(byte(2 + index) for index in range(NUM_MOVES))
    move_names = tuple(display_move_id(move_id) for move_id in moves)
    item_id = byte(1)
    types = tables.load_type_constants()
    dvs = dvs_from_bytes(byte(21), byte(22))
    return ExactPokemonState(
        species=species,
        species_id=species_id,
        level=byte(31),
        item_id=item_id,
        item_name=tables.display_item(item_id),
        moves=moves,  # type: ignore[arg-type]
        move_names=move_names,  # type: ignore[arg-type]
        current_hp=word_be(34),
        max_hp=word_be(36),
        atk=word_be(38),
        defense=word_be(40),
        speed=word_be(42),
        sp_atk=word_be(44),
        sp_def=word_be(46),
        type1=types[row.type_a],
        type2=types[row.type_b],
        status=byte(32),
        happiness=byte(27),
        dvs=dvs,
    )


def state_to_json(state: ExactPokemonState) -> dict[str, object]:
    return {
        "species": state.species,
        "species_id": state.species_id,
        "level": state.level,
        "item_id": state.item_id,
        "item_name": state.item_name,
        "moves": list(state.moves),
        "move_names": list(state.move_names),
        "current_hp": state.current_hp,
        "max_hp": state.max_hp,
        "atk": state.atk,
        "defense": state.defense,
        "speed": state.speed,
        "sp_atk": state.sp_atk,
        "sp_def": state.sp_def,
        "type1": state.type1,
        "type2": state.type2,
        "status": state.status,
        "happiness": state.happiness,
        "dvs": list(state.dvs),
    }


def context_to_json(context: BattleContext) -> dict[str, object]:
    return {
        "weather": context.weather,
        "battle_turn": context.battle_turn,
        "johto_badges": context.johto_badges,
        "kanto_badges": context.kanto_badges,
        "link_mode": context.link_mode,
        "sleep_clause_active": context.sleep_clause_active,
        "attacker_stat_stages": dict(context.attacker_stat_stages),
        "defender_stat_stages": dict(context.defender_stat_stages),
        "player_screens": context.player_screens,
        "enemy_screens": context.enemy_screens,
        "attacker_substatus": context.attacker_substatus,
        "defender_substatus": context.defender_substatus,
        "revealed_moves": list(context.revealed_moves),
        "metronome_count": context.metronome_count,
        "is_critical": context.is_critical,
        "initial_cur_damage": context.initial_cur_damage,
    }


def state_from_exact_values(
    *,
    species: str,
    level: int,
    item: str,
    moves: tuple[str, str, str, str],
    current_hp: int,
    max_hp: int,
    atk: int,
    defense: int,
    speed: int,
    sp_atk: int,
    sp_def: int,
    status: int = 0,
    happiness: int = 70,
    dvs: tuple[int, int, int, int] = (15, 15, 15, 15),
) -> ExactPokemonState:
    base_stats = tables.load_base_stats()
    resolved_species = tables.resolve_name(species, base_stats, "species")
    row = base_stats[resolved_species]
    species_id = load_species_constants()[resolved_species]
    move_ids = move_ids_from_names(moves)
    item_id = tables.resolve_item(item)
    types = tables.load_type_constants()
    return ExactPokemonState(
        species=resolved_species,
        species_id=species_id,
        level=level,
        item_id=item_id,
        item_name=tables.display_item(item_id),
        moves=move_ids,
        move_names=tuple(display_move_id(move_id) for move_id in move_ids),
        current_hp=current_hp,
        max_hp=max_hp,
        atk=atk,
        defense=defense,
        speed=speed,
        sp_atk=sp_atk,
        sp_def=sp_def,
        type1=types[row.type_a],
        type2=types[row.type_b],
        status=status,
        happiness=happiness,
        dvs=dvs,
    )
