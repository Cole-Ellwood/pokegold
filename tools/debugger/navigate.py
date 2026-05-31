"""Deity-mode auto-navigator: self-drive pokegold to a target game state.

The navigator boots a fresh ROM with explicit zeroed in-memory SRAM/RTC, replays
a fixed *checkpoint* input log to a known reachable state, and evaluates a
target-state predicate
(``tools.debugger.state_predicate``) against live RAM every frame. The instant
the predicate is satisfied it captures a save-state + a replayable run manifest
and prints the ``predicate satisfied`` evidence marker. If the predicate is
never satisfied within the checkpoint's inputs it fails closed and reports the
nearest state it actually observed — it never claims a state it could not see,
and it never depends on a mutable ``pokegold.sav`` side file.

This is the Phase-1 self-driving slice. The checkpoint library currently covers
``new_game`` (power-on -> the New Bark bedroom, ``PLAYERS_HOUSE_2F``) and
``route29_first_wild`` (power-on -> first Route 29 wild battle). The observable
fields are deliberately narrow: map, basic battle mode, first-party count, and
the hardware RNG bytes. A predicate over an unobserved field (for example a
boss identity) parses fine but fails closed here — that is the honest
"capability not built yet" signal, not a crash.

    python -m tools.debugger navigate --to "map=PLAYERS_HOUSE_2F"
    python -m tools.debugger navigate --to "wild_battle and map=ROUTE_29"
    python -m tools.debugger navigate --verify <run-manifest.json>
    python -m tools.debugger navigate --self-test

Roadmap: ``docs/debugger_deity_mode_roadmap.md`` section 6 (Phase 1, Task 3).
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from collections import deque
import hashlib
import io
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from tools.trace import runtime as rt

from . import state_predicate
from .input_log import build_input_playback, play_inputs_for_frame
from .runtime_state import load_map_catalog

ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_DIR = ROOT / "audit" / "debugger_checkpoints"
DEFAULT_ROM = ROOT / "pokegold.gbc"
DEFAULT_SYMBOLS = ROOT / "pokegold.sym"
TRAINER_CONSTANTS = ROOT / "constants" / "trainer_constants.asm"
POKEMON_CONSTANTS = ROOT / "constants" / "pokemon_constants.asm"
EVENT_CONSTANTS = ROOT / "constants" / "event_flags.asm"
BOSS_TRACE_MANIFEST = ROOT / "audit" / "boss_ai_trace" / "live_capture_manifest.json"
ARTIFACT_DIR = ROOT / ".local" / "tmp" / "deity_nav"
BACKEND_LOCK_PATH = ARTIFACT_DIR / "pyboy_navigation.lock"

EVIDENCE_MARKER = "predicate satisfied"
# Drive this many frames past the checkpoint's scheduled inputs before failing
# closed, so a predicate satisfied a few frames after the last button still hits.
FRAME_SLACK = 300
DEFAULT_CHECKPOINT = "new_game"
ROUTE29_WILD_CHECKPOINT = "route29_first_wild"
ROUTE46_SOUTH_CHECKPOINT = "route46_south"
ROUTE30_SOUTH_CHECKPOINT = "route30_south"
MR_POKEMON_AFTER_OAK_CHECKPOINT = "mr_pokemon_after_oak"
CHERRYGROVE_RIVAL_BATTLE_CHECKPOINT = "cherrygrove_rival_battle"
CHERRYGROVE_POST_RIVAL_CHECKPOINT = "cherrygrove_post_rival"
ELMS_LAB_POST_OFFICER_CHECKPOINT = "elms_lab_post_officer"
ELMS_LAB_AFTER_AIDE_CHECKPOINT = "elms_lab_after_aide"
BOSS_AI_CHECKPOINT_PREFIX = "boss_ai_"
ISOLATED_RAM_BYTES = 0x8000
ISOLATED_RTC_BYTES = 48
SEED_BATTLE_CLEAR_TEXT_PULSES = 4
SEED_BATTLE_DRIVE_STRATEGIES: tuple[
    tuple[str, tuple[tuple[str, int, int], ...], int],
    ...,
] = (
    ("a_mash", (("a", 2, 45),), 0),
    ("move_slot_3", (("a", 2, 30), ("down", 2, 30), ("a", 2, 30)), SEED_BATTLE_CLEAR_TEXT_PULSES),
    (
        "move_slot_4_down_right",
        (("a", 2, 30), ("down", 2, 30), ("right", 2, 30), ("a", 2, 30)),
        SEED_BATTLE_CLEAR_TEXT_PULSES,
    ),
    (
        "move_slot_4_right_down",
        (("a", 2, 30), ("right", 2, 30), ("down", 2, 30), ("a", 2, 30)),
        SEED_BATTLE_CLEAR_TEXT_PULSES,
    ),
)
SEARCH_MOVE_BUTTONS = ("up", "left", "right", "down")
SEARCH_DEFAULT_MAX_STEPS = 60
SEARCH_DEFAULT_MAX_NODES = 1500
SEARCH_MOVE_HOLD_FRAMES = 16
SEARCH_MOVE_TOTAL_FRAMES = 100
SEARCH_INTERACT_BUTTONS = ("a",)
SEARCH_INTERACT_HOLD_FRAMES = 2
SEARCH_INTERACT_TOTAL_FRAMES = 30
SEARCH_WILD_RUN_TOTAL_FRAMES = 160
SEARCH_WILD_RUN_SETTLE_FRAMES = 200
SEARCH_SCRIPT_PULSE_HOLD_FRAMES = 2
SEARCH_SCRIPT_PULSE_TOTAL_FRAMES = 30
SEARCH_SCRIPT_MAX_PULSES = 240
SEARCH_TRAINER_BATTLE_MAX_PULSES = 360
SEARCH_TRAINER_BATTLE_SETTLE_PULSES = 40
WILD_RUN_MACRO = ("a", "a", "a", "down", "right", "a", "a")
BOSS_TRAINER_CLASSES = frozenset(
    {
        "FALKNER",
        "BUGSY",
        "WHITNEY",
        "MORTY",
        "PRYCE",
        "JASMINE",
        "CHUCK",
        "CLAIR",
        "BROCK",
        "MISTY",
        "LT_SURGE",
        "ERIKA",
        "JANINE",
        "SABRINA",
        "BLAINE",
        "BLUE",
        "KOGA",
        "CHAMPION",
    }
)


# --- checkpoints -------------------------------------------------------------


def load_checkpoint(name: str) -> dict[str, Any]:
    """Load a checkpoint manifest and its parsed input-log playback by id."""
    manifest_path = CHECKPOINT_DIR / f"{name}.manifest.json"
    if not manifest_path.exists() and name.startswith(BOSS_AI_CHECKPOINT_PREFIX):
        return load_boss_ai_checkpoint(name.removeprefix(BOSS_AI_CHECKPOINT_PREFIX))
    if not manifest_path.exists():
        raise FileNotFoundError(f"unknown checkpoint {name!r}: {manifest_path} not found")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    log_names = checkpoint_log_names(manifest)
    log_paths = tuple(CHECKPOINT_DIR / log_name for log_name in log_names)
    playback = build_input_playback(tuple(str(path) for path in log_paths), root=ROOT, max_events=0)
    if playback["errors"]:
        raise ValueError(f"checkpoint {name!r} input log invalid: {playback['errors']}")
    return {
        "name": name,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "log_names": log_names,
        "log_paths": log_paths,
        "playback": playback,
    }


def load_boss_ai_checkpoint(capture_id: str) -> dict[str, Any]:
    """Load a boss decision-point seed checkpoint from the live-capture manifest.

    These states are generated by ``tools.trace.boss_ai_state_factory`` through
    real map scripts, then recorded in ``audit/boss_ai_trace/live_capture_manifest.json``.
    They are seed checkpoints rather than replay-log checkpoints: the run
    manifest records the seed-state hash and source manifest so re-validation
    can still fail closed if the underlying state changes.
    """

    if not BOSS_TRACE_MANIFEST.exists():
        raise FileNotFoundError(f"missing boss AI trace manifest: {BOSS_TRACE_MANIFEST}")
    data = json.loads(BOSS_TRACE_MANIFEST.read_text(encoding="utf-8"))
    selected = None
    for entry in data.get("captures", []):
        if isinstance(entry, dict) and str(entry.get("id", "")).lower() == capture_id.lower():
            selected = entry
            break
    if selected is None:
        raise FileNotFoundError(f"unknown boss AI checkpoint {capture_id!r}")
    raw_state = selected.get("pre_choice_state") or selected.get("save_state")
    if not isinstance(raw_state, str) or not raw_state:
        raise FileNotFoundError(f"boss AI checkpoint {capture_id!r} has no seed state")
    state_path = Path(raw_state)
    if not state_path.is_absolute():
        state_path = ROOT / state_path
    if not state_path.exists():
        raise FileNotFoundError(f"boss AI checkpoint state missing: {state_path}")
    trace_rom = Path(str(data.get("trace_rom") or "pokegold_trace.gbc"))
    trace_symbols = Path(str(data.get("trace_symbols") or "pokegold_trace.sym"))
    if not trace_rom.is_absolute():
        trace_rom = ROOT / trace_rom
    if not trace_symbols.is_absolute():
        trace_symbols = ROOT / trace_symbols
    manifest = {
        "schema_version": 1,
        "kind": "deity_navigator_seed_checkpoint",
        "id": BOSS_AI_CHECKPOINT_PREFIX + capture_id.lower(),
        "description": (
            f"Boss AI decision-point seed for {selected.get('boss') or capture_id}; "
            "generated by tools.trace.boss_ai_state_factory and recorded in the live-capture manifest."
        ),
        "source_manifest": str(BOSS_TRACE_MANIFEST.relative_to(ROOT)),
        "seed_state": str(state_path.relative_to(ROOT) if state_path.is_relative_to(ROOT) else state_path),
        "seed_state_sha256": log_sha256(state_path),
        "trace_rom": str(trace_rom.relative_to(ROOT) if trace_rom.is_relative_to(ROOT) else trace_rom),
        "trace_symbols": str(trace_symbols.relative_to(ROOT) if trace_symbols.is_relative_to(ROOT) else trace_symbols),
        "capture": selected,
        "storage_seed": {
            "state_file": str(state_path.relative_to(ROOT) if state_path.is_relative_to(ROOT) else state_path),
            "source": "boss_ai_state_factory",
            "source_manifest": str(BOSS_TRACE_MANIFEST.relative_to(ROOT)),
        },
    }
    return {
        "name": manifest["id"],
        "manifest": manifest,
        "manifest_path": BOSS_TRACE_MANIFEST,
        "log_names": [],
        "log_paths": tuple(),
        "seed_state_path": state_path,
        "preferred_rom": trace_rom,
        "preferred_symbols": trace_symbols,
        "playback": {"events": [], "errors": [], "event_count": 0, "total_frames": 0, "button_sample": []},
    }


def checkpoint_log_names(manifest: dict[str, Any]) -> list[str]:
    logs = manifest.get("input_logs")
    if isinstance(logs, list) and logs:
        return [str(item) for item in logs]
    if "input_log" not in manifest:
        return []
    return [str(manifest["input_log"])]


def log_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def combined_log_sha256(paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def checkpoint_log_sha_ok(checkpoint_data: dict[str, Any], manifest: dict[str, Any] | None = None) -> bool:
    source_manifest = manifest or checkpoint_data["manifest"]
    paths = tuple(checkpoint_data["log_paths"])
    seed_state = checkpoint_data.get("seed_state_path")
    if seed_state is not None:
        expected_seed_sha = source_manifest.get("seed_state_sha256")
        return bool(expected_seed_sha) and Path(seed_state).exists() and log_sha256(Path(seed_state)) == expected_seed_sha
    if "combined_input_log_sha256" in source_manifest:
        return combined_log_sha256(paths) == source_manifest["combined_input_log_sha256"]
    if len(paths) == 1 and "input_log_sha256" in source_manifest:
        return log_sha256(paths[0]) == source_manifest["input_log_sha256"]
    expected = source_manifest.get("input_log_sha256_by_name", {})
    return bool(expected) and all(log_sha256(path) == expected.get(path.name) for path in paths)


# --- constants ---------------------------------------------------------------


def strip_asm_comment(raw: str) -> str:
    return raw.split(";", 1)[0].strip()


def parse_rgb_int(token: str) -> int:
    token = token.strip()
    if token.startswith("$"):
        return int(token[1:], 16)
    return int(token, 0)


def parse_trainer_class_names(path: Path = TRAINER_CONSTANTS) -> dict[int, str]:
    """Return trainer class id -> trainer class constant name."""
    names: dict[int, str] = {}
    class_id = 0
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = strip_asm_comment(raw).split()
        if len(parts) >= 2 and parts[0] == "trainerclass":
            names[class_id] = parts[1]
            class_id += 1
    return names


def parse_const_names(path: Path, *, default_start: int = 0) -> dict[int, str]:
    """Parse simple RGBDS ``const_def`` / ``const`` tables into id -> name."""
    names: dict[int, str] = {}
    value = default_start
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = strip_asm_comment(raw).split()
        if not parts:
            continue
        if parts[0] == "const_def":
            value = parse_rgb_int(parts[1]) if len(parts) >= 2 else 0
            continue
        if len(parts) >= 2 and parts[0] == "const":
            names[value] = parts[1]
            value += 1
    return names


def parse_pokemon_names(path: Path = POKEMON_CONSTANTS) -> dict[int, str]:
    """Return Pokemon species id -> species constant from the primary species table."""
    names: dict[int, str] = {}
    value = 0
    in_species_table = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = strip_asm_comment(raw).split()
        if not parts:
            continue
        if parts[0] == "DEF" and len(parts) >= 2 and parts[1] == "NUM_POKEMON":
            break
        if parts[0] == "const_def":
            if not in_species_table:
                value = parse_rgb_int(parts[1]) if len(parts) >= 2 else 0
                in_species_table = True
            continue
        if in_species_table and len(parts) >= 2 and parts[0] == "const":
            names[value] = parts[1]
            value += 1
    return names


def parse_event_constants(path: Path = EVENT_CONSTANTS) -> dict[str, int]:
    """Return event flag name -> bit index from constants/event_flags.asm."""

    names: dict[str, int] = {}
    value = 0
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = strip_asm_comment(raw).split()
        if not parts:
            continue
        if parts[0] == "const_def":
            value = parse_rgb_int(parts[1]) if len(parts) >= 2 else 0
            continue
        if parts[0] == "const_next" and len(parts) >= 2:
            value = parse_rgb_int(parts[1])
            continue
        if parts[0] == "const_skip":
            value += parse_rgb_int(parts[1]) if len(parts) >= 2 else 1
            continue
        if len(parts) >= 2 and parts[0] == "const":
            names[parts[1]] = value
            value += 1
    return names


# --- observation -------------------------------------------------------------


def map_const(catalog: dict[str, Any], group: int, number: int) -> str | None:
    entry = catalog.get("maps", {}).get(f"{group}:{number}")
    return entry.get("const") if isinstance(entry, dict) else None


def build_observed(
    catalog: dict[str, Any],
    group: int,
    number: int,
    *,
    x: int | None = None,
    y: int | None = None,
    battle_mode: int | None = None,
    trainer_class: int | None = None,
    trainer_id: int | None = None,
    trainer_class_name: str | None = None,
    boss: str | None = None,
    temp_wild_species: int | None = None,
    enemy_species: int | None = None,
    enemy_active: str | None = None,
    player_species: int | None = None,
    player_active: str | None = None,
    player_turns_taken: int | None = None,
    enemy_turns_taken: int | None = None,
    party_count: int | None = None,
    facing: str | None = None,
    rng: dict[str, int] | None = None,
    script_mode: int | None = None,
    script_running: int | None = None,
    event_flags: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """The flat observed dict ``state_predicate.evaluate`` consumes.

    ``group``/``number`` are kept under underscore keys for fail-closed
    messages; public predicate fields are set only when RAM exposes them.
    """
    observed: dict[str, Any] = {"_group": int(group), "_number": int(number)}
    if x is not None:
        observed["x"] = int(x)
    if y is not None:
        observed["y"] = int(y)
    const = map_const(catalog, group, number)
    if group and const:
        observed["map"] = const
    if battle_mode is not None:
        observed["_battle_mode"] = int(battle_mode)
        if int(battle_mode):
            observed["battle"] = True
        if int(battle_mode) == 1:
            observed["wild_battle"] = True
        if int(battle_mode) == 2:
            observed["trainer_battle"] = True
    if trainer_class is not None:
        observed["_trainer_class"] = int(trainer_class)
        if trainer_class_name:
            observed["trainer_class"] = trainer_class_name
    if trainer_id is not None:
        observed["_trainer_id"] = int(trainer_id)
        observed["trainer_id"] = int(trainer_id)
    if boss and int(battle_mode or 0) == 2:
        observed["boss"] = boss
    if temp_wild_species is not None:
        observed["_temp_wild_species"] = int(temp_wild_species)
    if enemy_species is not None:
        observed["_enemy_species"] = int(enemy_species)
    if enemy_active:
        observed["enemy_active"] = enemy_active
    if player_species is not None:
        observed["_player_species"] = int(player_species)
    if player_active:
        observed["player_active"] = player_active
    if player_turns_taken is not None:
        observed["_player_turns_taken"] = int(player_turns_taken)
    if enemy_turns_taken is not None:
        observed["_enemy_turns_taken"] = int(enemy_turns_taken)
    turn_counters = [
        int(value)
        for value in (player_turns_taken, enemy_turns_taken)
        if value is not None
    ]
    if turn_counters:
        # Predicate language names this "turn"; the engine keeps separate
        # player/enemy counters, and boss AI decision questions follow the
        # enemy-side turn counter before the player has necessarily acted.
        observed["turn"] = max(turn_counters)
    if party_count is not None:
        observed["_party_count"] = int(party_count)
    if facing:
        observed["facing"] = facing
    if rng is not None:
        observed["_rng"] = dict(rng)
    if script_mode is not None:
        observed["_script_mode"] = int(script_mode)
        observed["script_mode"] = int(script_mode)
    if script_running is not None:
        observed["_script_running"] = int(script_running)
        observed["script_running"] = int(script_running)
    if is_script_active_values(script_mode, script_running):
        observed["script_active"] = True
    if event_flags:
        observed["_events"] = dict(event_flags)
        for name, enabled in event_flags.items():
            if enabled:
                observed[f"event:{name}"] = True
    return observed


def observe(
    pyboy: Any,
    symbols: dict[str, Any],
    catalog: dict[str, Any],
    *,
    trainer_class_names: dict[int, str] | None = None,
    species_names: dict[int, str] | None = None,
    event_constants: dict[str, int] | None = None,
    event_names: set[str] | None = None,
) -> dict[str, Any]:
    rng = {}
    for name in ("hRandomAdd", "hRandomSub"):
        if name in symbols:
            rng[name] = rt.read_byte(pyboy, symbols[name])
    battle_mode = read_symbol_if_present(pyboy, symbols, "wBattleMode")
    raw_trainer_class = read_symbol_if_present(pyboy, symbols, "wOtherTrainerClass")
    raw_trainer_id = read_symbol_if_present(pyboy, symbols, "wOtherTrainerID")
    trainer_class = raw_trainer_class if int(battle_mode or 0) == 2 and raw_trainer_class else None
    trainer_id = raw_trainer_id if trainer_class is not None else None
    trainer_name = (trainer_class_names or {}).get(int(trainer_class or 0))
    boss = trainer_name if trainer_name in BOSS_TRAINER_CLASSES else None
    raw_enemy_species = read_symbol_if_present(pyboy, symbols, "wEnemyMonSpecies")
    raw_player_species = read_symbol_if_present(pyboy, symbols, "wBattleMonSpecies")
    enemy_species = raw_enemy_species if raw_enemy_species else None
    player_species = raw_player_species if raw_player_species else None
    return build_observed(
        catalog,
        rt.read_byte(pyboy, symbols["wMapGroup"]),
        rt.read_byte(pyboy, symbols["wMapNumber"]),
        x=read_symbol_if_present(pyboy, symbols, "wXCoord"),
        y=read_symbol_if_present(pyboy, symbols, "wYCoord"),
        battle_mode=battle_mode,
        trainer_class=trainer_class,
        trainer_id=trainer_id,
        trainer_class_name=trainer_name,
        boss=boss,
        temp_wild_species=read_symbol_if_present(pyboy, symbols, "wTempWildMonSpecies"),
        enemy_species=enemy_species,
        enemy_active=(species_names or {}).get(int(enemy_species or 0)),
        player_species=player_species,
        player_active=(species_names or {}).get(int(player_species or 0)),
        player_turns_taken=read_symbol_if_present(pyboy, symbols, "wPlayerTurnsTaken"),
        enemy_turns_taken=read_symbol_if_present(pyboy, symbols, "wEnemyTurnsTaken"),
        party_count=read_symbol_if_present(pyboy, symbols, "wPartyCount"),
        facing=facing_name(read_symbol_if_present(pyboy, symbols, "wPlayerDirection")),
        rng=rng or None,
        script_mode=read_symbol_if_present(pyboy, symbols, "wScriptMode"),
        script_running=read_symbol_if_present(pyboy, symbols, "wScriptRunning"),
        event_flags=read_event_flags(pyboy, symbols, event_constants or {}, event_names or set()),
    )


def is_script_active_values(script_mode: int | None, script_running: int | None) -> bool:
    return bool(int(script_mode or 0) or int(script_running or 0))


def is_script_active(pyboy: Any, symbols: dict[str, Any]) -> bool:
    return is_script_active_values(
        read_symbol_if_present(pyboy, symbols, "wScriptMode"),
        read_symbol_if_present(pyboy, symbols, "wScriptRunning"),
    )


def read_symbol_if_present(pyboy: Any, symbols: dict[str, Any], name: str) -> int | None:
    if name not in symbols:
        return None
    return rt.read_byte(pyboy, symbols[name])


def read_event_flags(
    pyboy: Any,
    symbols: dict[str, Any],
    event_constants: dict[str, int],
    event_names: set[str],
) -> dict[str, bool]:
    if not event_names:
        return {}
    if "wEventFlags" not in symbols:
        return {}
    base = symbols["wEventFlags"]
    observed: dict[str, bool] = {}
    for name in sorted(event_names):
        bit_index = event_constants.get(name)
        if bit_index is None:
            observed[name] = False
            continue
        value = rt.read_byte(pyboy, rt.Symbol(base.bank, base.address + bit_index // 8))
        observed[name] = bool(value & (1 << (bit_index & 7)))
    return observed


def facing_name(raw: int | None) -> str | None:
    return {
        0x00: "DOWN",
        0x04: "UP",
        0x08: "LEFT",
        0x0C: "RIGHT",
    }.get(int(raw)) if raw is not None else None


def describe_state(observed: dict[str, Any] | None) -> str:
    if not observed:
        return "no state observed"
    group, number = observed.get("_group", 0), observed.get("_number", 0)
    name = observed.get("map")
    xy = ""
    if "x" in observed and "y" in observed:
        xy = f" x={observed['x']} y={observed['y']}"
    pieces = [f"map={name} ({group}:{number}){xy}" if name else f"no map loaded ({group}:{number}){xy}"]
    battle_mode = observed.get("_battle_mode")
    if battle_mode:
        pieces.append(f"battle_mode={battle_mode}")
        if observed.get("wild_battle"):
            pieces.append("wild_battle")
        if observed.get("trainer_battle"):
            pieces.append("trainer_battle")
        trainer_class = observed.get("trainer_class")
        if trainer_class:
            pieces.append(f"trainer_class={trainer_class}")
        boss = observed.get("boss")
        if boss:
            pieces.append(f"boss={boss}")
        enemy_active = observed.get("enemy_active")
        if enemy_active:
            pieces.append(f"enemy_active={enemy_active}")
        temp_wild = observed.get("_temp_wild_species")
        if temp_wild:
            pieces.append(f"temp_wild_species=${int(temp_wild):02X}")
    return ", ".join(pieces)


def observed_signature(observed: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "map",
        "_group",
        "_number",
        "x",
        "y",
        "_battle_mode",
        "_trainer_class",
        "_trainer_id",
        "trainer_class",
        "trainer_id",
        "boss",
        "_temp_wild_species",
        "_enemy_species",
        "enemy_active",
        "_player_species",
        "player_active",
        "_player_turns_taken",
        "_enemy_turns_taken",
        "_party_count",
        "facing",
        "turn",
        "_rng",
        "_script_mode",
        "_script_running",
        "script_mode",
        "script_running",
        "script_active",
    )
    signature = {key: observed[key] for key in keys if key in observed}
    if "_events" in observed:
        signature["_events"] = dict(observed["_events"])
    for key in sorted(key for key in observed if key.startswith("event:")):
        signature[key] = observed[key]
    return signature


# --- driving -----------------------------------------------------------------


def navigate_to(
    predicate_text: str,
    *,
    checkpoint: str = "auto",
    rom: Path = DEFAULT_ROM,
    symbols_path: Path = DEFAULT_SYMBOLS,
    save_state: str | None = None,
    manifest_out: str | None = None,
    frame_slack: int = FRAME_SLACK,
) -> dict[str, Any]:
    """Replay ``checkpoint`` and stop the instant ``predicate_text`` holds.

    Raises ``PredicateError`` on a bad predicate (fail at parse, not frame
    100000). Returns an outcome dict; ``reached`` is True iff the predicate was
    satisfied, in which case a save-state + run manifest were written.
    """
    predicate = state_predicate.parse(predicate_text)
    checkpoint_name = select_checkpoint(predicate, checkpoint)
    checkpoint_data = load_checkpoint(checkpoint_name)
    if checkpoint_data.get("preferred_rom") is not None and path_matches_default(rom, DEFAULT_ROM):
        rom = Path(checkpoint_data["preferred_rom"])
    if checkpoint_data.get("preferred_symbols") is not None and path_matches_default(symbols_path, DEFAULT_SYMBOLS):
        symbols_path = Path(checkpoint_data["preferred_symbols"])
    symbols = rt.parse_symbols(symbols_path)
    for needed in ("wMapGroup", "wMapNumber"):
        if needed not in symbols:
            raise KeyError(f"symbol {needed} missing from {symbols_path}")
    catalog = load_map_catalog(root=ROOT, labels={})
    trainer_class_names = parse_trainer_class_names()
    species_names = parse_pokemon_names()
    event_names = predicate_event_names(predicate)
    event_constants = parse_event_constants() if event_names else {}
    if event_names and "wEventFlags" not in symbols:
        raise KeyError(f"symbol wEventFlags missing from {symbols_path}")
    playback = checkpoint_data["playback"]
    budget = int(playback["total_frames"]) + max(0, frame_slack)

    with navigation_backend_lock():
        pyboy = open_navigation_pyboy(rom)
        rt.disable_realtime(pyboy)
        try:
            reached_frame: int | None = None
            observed: dict[str, Any] = {}
            seed_state_path = checkpoint_data.get("seed_state_path")
            if seed_state_path is not None:
                with Path(seed_state_path).open("rb") as handle:
                    pyboy.load_state(handle)
                observed = observe(
                    pyboy,
                    symbols,
                    catalog,
                    trainer_class_names=trainer_class_names,
                    species_names=species_names,
                    event_constants=event_constants,
                    event_names=event_names,
                )
                if state_predicate.evaluate(predicate, observed).satisfied:
                    reached_frame = 0
                    return _build_outcome(
                        pyboy=pyboy,
                        predicate=predicate,
                        checkpoint_data=checkpoint_data,
                        reached_frame=reached_frame,
                        observed=observed,
                        save_state=save_state,
                        manifest_out=manifest_out,
                        rom=rom,
                        symbols_path=symbols_path,
                    )
                target_turn = predicate_target_turn(predicate)
                if target_turn is not None:
                    seed_drive = drive_seed_battle_to_turn(
                        pyboy,
                        symbols,
                        catalog,
                        trainer_class_names=trainer_class_names,
                        species_names=species_names,
                        event_constants=event_constants,
                        event_names=event_names,
                        predicate=predicate,
                        target_turn=target_turn,
                    )
                    observed = seed_drive["observed"]
                    checkpoint_data["seed_input_events"] = seed_drive["input_events"]
                    checkpoint_data["seed_input_strategy"] = seed_drive.get("strategy", "")
                    if seed_drive["reached"]:
                        return _build_outcome(
                            pyboy=pyboy,
                            predicate=predicate,
                            checkpoint_data=checkpoint_data,
                            reached_frame=seed_drive["frame"],
                            observed=observed,
                            save_state=save_state,
                            manifest_out=manifest_out,
                            rom=rom,
                            symbols_path=symbols_path,
                        )
                if not checkpoint_data["playback"]["total_frames"]:
                    return _build_outcome(
                        pyboy=pyboy,
                        predicate=predicate,
                        checkpoint_data=checkpoint_data,
                        reached_frame=None,
                        observed=observed,
                        save_state=save_state,
                        manifest_out=manifest_out,
                        rom=rom,
                        symbols_path=symbols_path,
                    )
            for frame in range(budget):
                play_inputs_for_frame(pyboy, playback, frame)
                pyboy.tick(1, False)
                observed = observe(
                    pyboy,
                    symbols,
                    catalog,
                    trainer_class_names=trainer_class_names,
                    species_names=species_names,
                    event_constants=event_constants,
                    event_names=event_names,
                )
                if state_predicate.evaluate(predicate, observed).satisfied:
                    reached_frame = frame
                    break
            return _build_outcome(
                pyboy=pyboy,
                predicate=predicate,
                checkpoint_data=checkpoint_data,
                reached_frame=reached_frame,
                observed=observed,
                save_state=save_state,
                manifest_out=manifest_out,
                rom=rom,
                symbols_path=symbols_path,
            )
        finally:
            pyboy.stop()


@contextmanager
def navigation_backend_lock():
    """Serialize PyBoy deity-navigation runs across local CLI processes."""

    BACKEND_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with BACKEND_LOCK_PATH.open("a+b") as handle:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            while True:
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as exc:
                    if getattr(exc, "errno", None) not in {13, 36}:
                        raise
                    time.sleep(0.05)
            try:
                handle.seek(0)
                handle.write(b"\0")
                handle.flush()
                handle.seek(0)
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                handle.seek(0)
                handle.write(b"\0")
                handle.flush()
                handle.seek(0)
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def open_navigation_pyboy(rom: Path) -> Any:
    """Open PyBoy with deterministic in-memory SRAM/RTC seed files.

    Deity navigation must replay from a manifest alone. Letting PyBoy read or
    write ``pokegold.sav`` makes the same input script depend on whatever a
    prior run left on disk, so navigator runs use explicit zeroed battery/RTC
    streams instead.
    """

    if not rom.exists():
        rt.fail(f"missing ROM: {rom}")
    PyBoy = rt.load_pyboy("PyBoy required for navigate")
    try:
        pyboy = PyBoy(
            str(rom),
            window="null",
            sound=False,
            log_level="ERROR",
            ram_file=io.BytesIO(bytes(ISOLATED_RAM_BYTES)),
            rtc_file=io.BytesIO(bytes(ISOLATED_RTC_BYTES)),
        )
        rtc_lock = getattr(pyboy, "rtc_lock_experimental", None)
        if rtc_lock is not None:
            rtc_lock(True)
        return pyboy
    except TypeError as exc:
        raise RuntimeError(
            "PyBoy build does not support ram_file/rtc_file isolation; "
            "refusing deity navigation instead of using mutable pokegold.sav"
        ) from exc


def path_matches_default(path: Path, default: Path) -> bool:
    try:
        return Path(path).resolve() == default.resolve()
    except OSError:
        return Path(path).name == default.name


def predicate_target_turn(predicate: state_predicate.Predicate) -> int | None:
    for clause in predicate.clauses:
        if (
            isinstance(clause, state_predicate.Comparison)
            and clause.field == "turn"
            and clause.op == "=="
            and isinstance(clause.value, int)
        ):
            return int(clause.value)
    return None


def drive_seed_battle_to_turn(
    pyboy: Any,
    symbols: dict[str, Any],
    catalog: dict[str, Any],
    *,
    trainer_class_names: dict[int, str],
    species_names: dict[int, str],
    event_constants: dict[str, int],
    event_names: set[str],
    predicate: state_predicate.Predicate,
    target_turn: int,
    max_pulses: int = 240,
) -> dict[str, Any]:
    """Advance a boss seed through simple A-button battle text/menu pulses.

    This keeps the proof input-driven after the seed checkpoint is loaded. It
    intentionally only records the inputs that were actually emitted; if the
    exact predicate is not observed, the caller fails closed with the nearest
    state.
    """

    initial_state = save_emulator_state(pyboy)
    best: dict[str, Any] | None = None
    for strategy_name, pulse_events, clear_text_pulses in SEED_BATTLE_DRIVE_STRATEGIES:
        load_emulator_state(pyboy, initial_state)
        result = drive_seed_battle_strategy(
            pyboy,
            symbols,
            catalog,
            trainer_class_names=trainer_class_names,
            species_names=species_names,
            event_constants=event_constants,
            event_names=event_names,
            predicate=predicate,
            target_turn=target_turn,
            strategy_name=strategy_name,
            pulse_events=pulse_events,
            clear_text_pulses=clear_text_pulses,
            max_pulses=max_pulses,
        )
        if result["reached"]:
            return result
        if best is None or seed_battle_progress_key(result) > seed_battle_progress_key(best):
            best = result
    if best is not None:
        return best
    return {
        "reached": False,
        "frame": 0,
        "observed": {},
        "input_events": [],
        "strategy": "",
    }


def drive_seed_battle_strategy(
    pyboy: Any,
    symbols: dict[str, Any],
    catalog: dict[str, Any],
    *,
    trainer_class_names: dict[int, str],
    species_names: dict[int, str],
    event_constants: dict[str, int],
    event_names: set[str],
    predicate: state_predicate.Predicate,
    target_turn: int,
    strategy_name: str,
    pulse_events: tuple[tuple[str, int, int], ...],
    clear_text_pulses: int,
    max_pulses: int,
) -> dict[str, Any]:
    input_events: list[dict[str, Any]] = []
    observed: dict[str, Any] = {}
    frame = 0
    for _pulse in range(1, max_pulses + 1):
        for button, hold_frames, total_frames in pulse_events:
            apply_button(pyboy, button, hold_frames=hold_frames, total_frames=total_frames)
            input_events.append(button_event(button, hold_frames, total_frames))
            frame += max(hold_frames, total_frames)
        for _ in range(clear_text_pulses):
            apply_button(pyboy, "a", hold_frames=2, total_frames=30)
            input_events.append(button_event("a", 2, 30))
            frame += 30
        observed = observe(
            pyboy,
            symbols,
            catalog,
            trainer_class_names=trainer_class_names,
            species_names=species_names,
            event_constants=event_constants,
            event_names=event_names,
        )
        if state_predicate.evaluate(predicate, observed).satisfied:
            return {
                "reached": True,
                "frame": frame,
                "observed": observed,
                "input_events": input_events,
                "strategy": strategy_name,
            }
        if int(observed.get("_battle_mode", 0) or 0) != 2:
            break
        if int(observed.get("turn", 0) or 0) > target_turn:
            break
    return {
        "reached": False,
        "frame": frame,
        "observed": observed,
        "input_events": input_events,
        "strategy": strategy_name,
    }


def seed_battle_progress_key(result: dict[str, Any]) -> tuple[int, int, int, int]:
    observed = result.get("observed", {})
    return (
        int(observed.get("turn", 0) or 0),
        int(observed.get("_enemy_turns_taken", 0) or 0),
        int(observed.get("_player_turns_taken", 0) or 0),
        int(result.get("frame", 0) or 0),
    )


def _build_outcome(
    *,
    pyboy: Any,
    predicate: state_predicate.Predicate,
    checkpoint_data: dict[str, Any],
    reached_frame: int | None,
    observed: dict[str, Any],
    save_state: str | None,
    manifest_out: str | None,
    rom: Path,
    symbols_path: Path,
) -> dict[str, Any]:
    base = {
        "predicate": predicate.describe(),
        "checkpoint": checkpoint_data["name"],
        "nearest": describe_state(observed),
    }
    if reached_frame is None:
        unmet = state_predicate.evaluate(predicate, observed).unmet
        return {**base, "reached": False, "unmet": list(unmet)}

    state_path = (
        Path(save_state)
        if save_state
        else ARTIFACT_DIR / f"{checkpoint_data['name']}__{_slug(predicate.describe())}.state"
    )
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("wb") as handle:
        pyboy.save_state(handle)

    manifest = {
        "schema_version": 1,
        "kind": "deity_navigator_run",
        "predicate": predicate.describe(),
        "checkpoint": checkpoint_data["name"],
        "checkpoint_logs": list(checkpoint_data["log_names"]),
        "checkpoint_log_sha256": combined_log_sha256(tuple(checkpoint_data["log_paths"])),
        "checkpoint_total_frames": int(checkpoint_data["playback"]["total_frames"]),
        "checkpoint_kind": checkpoint_data["manifest"].get("kind", "deity_navigator_checkpoint"),
        "checkpoint_source_manifest": str(checkpoint_data.get("manifest_path", "")),
        "reached_frame": reached_frame,
        "observed_map": observed.get("map"),
        "observed_group": observed.get("_group"),
        "observed_number": observed.get("_number"),
        "observed_signature": observed_signature(observed),
        "rng_seed": observed.get("_rng", {}),
        "storage_seed": {
            "ram_file": "zeroed_in_memory",
            "ram_bytes": ISOLATED_RAM_BYTES,
            "rtc_file": "zeroed_in_memory",
            "rtc_bytes": ISOLATED_RTC_BYTES,
            "rtc_locked": True,
        },
        "backend": "pyboy",
        "rom": str(rom),
        "symbols": str(symbols_path),
        "save_state": str(state_path),
    }
    seed_state_path = checkpoint_data.get("seed_state_path")
    if seed_state_path is not None:
        seed_state = Path(seed_state_path)
        manifest["checkpoint_seed_state"] = str(seed_state)
        manifest["checkpoint_seed_state_sha256"] = log_sha256(seed_state)
        manifest["checkpoint_log_sha256"] = ""
        manifest["seed_input_events"] = list(checkpoint_data.get("seed_input_events", []))
        manifest["seed_input_strategy"] = str(checkpoint_data.get("seed_input_strategy", ""))
    manifest_path = Path(manifest_out) if manifest_out else state_path.with_suffix(".manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        **base,
        "reached": True,
        "frame": reached_frame,
        "map": observed.get("map"),
        "map_desc": describe_state(observed),
        "observed_signature": observed_signature(observed),
        "state_path": str(state_path),
        "manifest_path": str(manifest_path),
    }


def _slug(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text).strip("_") or "state"


# --- bounded search ----------------------------------------------------------


def search_to(
    predicate_text: str,
    *,
    checkpoint: str = "auto",
    rom: Path = DEFAULT_ROM,
    symbols_path: Path = DEFAULT_SYMBOLS,
    max_steps: int = SEARCH_DEFAULT_MAX_STEPS,
    max_nodes: int = SEARCH_DEFAULT_MAX_NODES,
    search_log_out: str | None = None,
) -> dict[str, Any]:
    """Bounded checkpoint-anchored input search.

    Search uses PyBoy save-states only as temporary queue nodes. The returned
    proof is a deterministic text input log that can be appended to the chosen
    checkpoint and replayed from power-on; temporary node states are never part
    of the proof contract.
    """

    predicate = state_predicate.parse(predicate_text)
    checkpoint_name = select_checkpoint(predicate, checkpoint)
    checkpoint_data = load_checkpoint(checkpoint_name)
    symbols = rt.parse_symbols(symbols_path)
    for needed in ("wMapGroup", "wMapNumber", "wXCoord", "wYCoord"):
        if needed not in symbols:
            raise KeyError(f"symbol {needed} missing from {symbols_path}")
    catalog = load_map_catalog(root=ROOT, labels={})
    trainer_class_names = parse_trainer_class_names()
    species_names = parse_pokemon_names()
    event_names = predicate_event_names(predicate)
    event_constants = parse_event_constants() if event_names else {}
    if event_names and "wEventFlags" not in symbols:
        raise KeyError(f"symbol wEventFlags missing from {symbols_path}")

    with navigation_backend_lock():
        pyboy = open_navigation_pyboy(rom)
        rt.disable_realtime(pyboy)
        try:
            for frame in range(int(checkpoint_data["playback"]["total_frames"])):
                play_inputs_for_frame(pyboy, checkpoint_data["playback"], frame)
                pyboy.tick(1, False)
            start_observed = observe(
                pyboy,
                symbols,
                catalog,
                trainer_class_names=trainer_class_names,
                species_names=species_names,
                event_constants=event_constants,
                event_names=event_names,
            )
            start_events: list[dict[str, Any]] = []
            if not state_predicate.evaluate(predicate, start_observed).satisfied:
                start_events = apply_search_normalizers(pyboy, symbols, predicate=predicate)
            if start_events:
                start_observed = observe(
                    pyboy,
                    symbols,
                    catalog,
                    trainer_class_names=trainer_class_names,
                    species_names=species_names,
                    event_constants=event_constants,
                    event_names=event_names,
                )
            start_blob = save_emulator_state(pyboy)
            result = run_bounded_search(
                pyboy=pyboy,
                symbols=symbols,
                catalog=catalog,
                trainer_class_names=trainer_class_names,
                species_names=species_names,
                event_constants=event_constants,
                event_names=event_names,
                predicate=predicate,
                start_blob=start_blob,
                start_events=start_events,
                start_observed=start_observed,
                max_steps=max_steps,
                max_nodes=max_nodes,
            )
        finally:
            pyboy.stop()

    report = {
        "schema_version": 1,
        "kind": "deity_navigator_search",
        "predicate": predicate.describe(),
        "checkpoint": checkpoint_name,
        "checkpoint_logs": list(checkpoint_data["log_names"]),
        "checkpoint_log_sha256": combined_log_sha256(tuple(checkpoint_data["log_paths"])),
        "backend": "pyboy",
        "storage_seed": {
            "ram_file": "zeroed_in_memory",
            "ram_bytes": ISOLATED_RAM_BYTES,
            "rtc_file": "zeroed_in_memory",
            "rtc_bytes": ISOLATED_RTC_BYTES,
            "rtc_locked": True,
        },
        **result,
    }
    if report.get("reached") and search_log_out:
        log_path = Path(search_log_out)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(format_search_input_log(report), encoding="utf-8")
        report["search_log"] = str(log_path)
        report["search_log_sha256"] = log_sha256(log_path)
    return report


def run_bounded_search(
    *,
    pyboy: Any,
    symbols: dict[str, Any],
    catalog: dict[str, Any],
    trainer_class_names: dict[int, str],
    species_names: dict[int, str],
    event_constants: dict[str, int],
    event_names: set[str],
    predicate: state_predicate.Predicate,
    start_blob: bytes,
    start_events: list[dict[str, Any]],
    start_observed: dict[str, Any],
    max_steps: int,
    max_nodes: int,
) -> dict[str, Any]:
    if state_predicate.evaluate(predicate, start_observed).satisfied:
        return {
            "reached": True,
            "searched_nodes": 0,
            "steps": 0,
            "nearest": describe_state(start_observed),
            "observed_signature": observed_signature(start_observed),
            "input_events": list(start_events),
        }

    queue = deque([(start_blob, list(start_events), start_observed, 0)])
    seen = {search_state_key(start_observed)}
    searched_nodes = 0
    nearest = start_observed

    while queue and searched_nodes < max_nodes:
        blob, events, observed, depth = queue.popleft()
        searched_nodes += 1
        nearest = observed
        if depth >= max_steps:
            continue
        for button, hold_frames, total_frames in search_actions(predicate):
            load_emulator_state(pyboy, blob)
            next_events = [*events, button_event(button, hold_frames, total_frames)]
            apply_button(pyboy, button, hold_frames=hold_frames, total_frames=total_frames)
            next_observed = observe(
                pyboy,
                symbols,
                catalog,
                trainer_class_names=trainer_class_names,
                species_names=species_names,
                event_constants=event_constants,
                event_names=event_names,
            )
            if state_predicate.evaluate(predicate, next_observed).satisfied:
                return {
                    "reached": True,
                    "searched_nodes": searched_nodes,
                    "steps": depth + 1,
                    "nearest": describe_state(next_observed),
                    "observed_signature": observed_signature(next_observed),
                    "input_events": next_events,
                }
            normalizer_events = apply_search_normalizers(pyboy, symbols, predicate=predicate)
            if normalizer_events:
                next_events.extend(normalizer_events)
                next_observed = observe(
                    pyboy,
                    symbols,
                    catalog,
                    trainer_class_names=trainer_class_names,
                    species_names=species_names,
                    event_constants=event_constants,
                    event_names=event_names,
                )
                if state_predicate.evaluate(predicate, next_observed).satisfied:
                    return {
                        "reached": True,
                        "searched_nodes": searched_nodes,
                        "steps": depth + 1,
                        "nearest": describe_state(next_observed),
                        "observed_signature": observed_signature(next_observed),
                        "input_events": next_events,
                    }
            # Only inactive overworld nodes are expandable in this bounded slice.
            if int(next_observed.get("_battle_mode", 0) or 0):
                continue
            if next_observed.get("script_active"):
                continue
            key = search_state_key(next_observed)
            if key in seen:
                continue
            seen.add(key)
            queue.append((save_emulator_state(pyboy), next_events, next_observed, depth + 1))

    unmet = state_predicate.evaluate(predicate, nearest).unmet
    return {
        "reached": False,
        "searched_nodes": searched_nodes,
        "steps": max_steps,
        "nearest": describe_state(nearest),
        "unmet": list(unmet),
        "input_events": [],
    }


def search_state_key(observed: dict[str, Any]) -> tuple[Any, ...]:
    event_bits = tuple(
        sorted((key, bool(value)) for key, value in observed.items() if key.startswith("event:"))
    )
    return (
        observed.get("_group"),
        observed.get("_number"),
        observed.get("x"),
        observed.get("y"),
        observed.get("facing"),
        observed.get("_battle_mode", 0),
        event_bits,
    )


def search_actions(predicate: state_predicate.Predicate) -> tuple[tuple[str, int, int], ...]:
    actions = [
        (button, SEARCH_MOVE_HOLD_FRAMES, SEARCH_MOVE_TOTAL_FRAMES)
        for button in SEARCH_MOVE_BUTTONS
    ]
    if predicate_targets_event_state(predicate):
        actions.extend(
            (button, SEARCH_INTERACT_HOLD_FRAMES, SEARCH_INTERACT_TOTAL_FRAMES)
            for button in SEARCH_INTERACT_BUTTONS
        )
    return tuple(actions)


def save_emulator_state(pyboy: Any) -> bytes:
    handle = io.BytesIO()
    pyboy.save_state(handle)
    return handle.getvalue()


def load_emulator_state(pyboy: Any, state: bytes) -> None:
    pyboy.load_state(io.BytesIO(state))


def apply_search_normalizers(
    pyboy: Any,
    symbols: dict[str, Any],
    *,
    predicate: state_predicate.Predicate | None = None,
) -> list[dict[str, Any]]:
    """Resolve non-overworld states this search slice knows how to leave honestly."""

    battle_mode = read_symbol_if_present(pyboy, symbols, "wBattleMode")
    events: list[dict[str, Any]] = []
    if int(battle_mode or 0) == 2:
        if predicate is not None and predicate_targets_battle_state(predicate):
            return events
        return apply_trainer_battle_a_mash_normalizer(pyboy, symbols)
    if int(battle_mode or 0) == 1:
        return apply_wild_battle_normalizer(pyboy)
    if is_script_active(pyboy, symbols):
        return apply_script_a_mash_normalizer(pyboy, symbols)
    return events


def apply_wild_battle_normalizer(pyboy: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for button in WILD_RUN_MACRO:
        events.append(button_event(button, 8, SEARCH_WILD_RUN_TOTAL_FRAMES))
        apply_button(pyboy, button, hold_frames=8, total_frames=SEARCH_WILD_RUN_TOTAL_FRAMES)
    pyboy.tick(SEARCH_WILD_RUN_SETTLE_FRAMES, False)
    events.append(wait_event(SEARCH_WILD_RUN_SETTLE_FRAMES))
    return events


def apply_script_a_mash_normalizer(pyboy: Any, symbols: dict[str, Any]) -> list[dict[str, Any]]:
    """Advance active map/text scripts with legitimate A button pulses."""

    events: list[dict[str, Any]] = []
    for _ in range(SEARCH_SCRIPT_MAX_PULSES):
        if int(read_symbol_if_present(pyboy, symbols, "wBattleMode") or 0) == 2:
            break
        if not is_script_active(pyboy, symbols):
            break
        events.append(
            button_event(
                "a",
                SEARCH_SCRIPT_PULSE_HOLD_FRAMES,
                SEARCH_SCRIPT_PULSE_TOTAL_FRAMES,
            )
        )
        apply_button(
            pyboy,
            "a",
            hold_frames=SEARCH_SCRIPT_PULSE_HOLD_FRAMES,
            total_frames=SEARCH_SCRIPT_PULSE_TOTAL_FRAMES,
        )
    return events


def apply_trainer_battle_a_mash_normalizer(pyboy: Any, symbols: dict[str, Any]) -> list[dict[str, Any]]:
    """Clear a simple trainer battle with bounded, replayable A-button pulses."""

    events: list[dict[str, Any]] = []
    cleared = False
    for _ in range(SEARCH_TRAINER_BATTLE_MAX_PULSES):
        battle_mode = int(read_symbol_if_present(pyboy, symbols, "wBattleMode") or 0)
        if not battle_mode and not is_script_active(pyboy, symbols):
            cleared = True
            break
        events.append(script_a_pulse_event())
        apply_script_a_pulse(pyboy)
    if cleared:
        for _ in range(SEARCH_TRAINER_BATTLE_SETTLE_PULSES):
            events.append(script_a_pulse_event())
            apply_script_a_pulse(pyboy)
    return events


def script_a_pulse_event() -> dict[str, Any]:
    return button_event(
        "a",
        SEARCH_SCRIPT_PULSE_HOLD_FRAMES,
        SEARCH_SCRIPT_PULSE_TOTAL_FRAMES,
    )


def apply_script_a_pulse(pyboy: Any) -> None:
    apply_button(
        pyboy,
        "a",
        hold_frames=SEARCH_SCRIPT_PULSE_HOLD_FRAMES,
        total_frames=SEARCH_SCRIPT_PULSE_TOTAL_FRAMES,
    )


def predicate_targets_battle_state(predicate: state_predicate.Predicate) -> bool:
    battle_flags = {"battle", "wild_battle", "trainer_battle"}
    battle_fields = {
        "trainer_class",
        "trainer_id",
        "enemy_active",
        "player_active",
        "turn",
    }
    return any(
        (
            isinstance(clause, state_predicate.Flag)
            and clause.name in battle_flags
        )
        or (
            isinstance(clause, state_predicate.Call)
            and clause.name == "battle"
        )
        or (
            isinstance(clause, state_predicate.Comparison)
            and clause.field in battle_fields
        )
        for clause in predicate.clauses
    )


def predicate_boss_name(predicate: state_predicate.Predicate) -> str | None:
    """Return a concrete boss/trainer class requested by a predicate, if any."""

    for clause in predicate.clauses:
        if isinstance(clause, state_predicate.Call) and clause.name == "battle":
            for arg_name, op, value in clause.args:
                if arg_name == "boss" and op == "==" and str(value) in BOSS_TRAINER_CLASSES:
                    return str(value)
        if (
            isinstance(clause, state_predicate.Comparison)
            and clause.field == "trainer_class"
            and clause.op == "=="
            and str(clause.value) in BOSS_TRAINER_CLASSES
        ):
            return str(clause.value)
    return None


def predicate_event_names(predicate: state_predicate.Predicate) -> set[str]:
    return {
        str(clause.value)
        for clause in predicate.clauses
        if isinstance(clause, state_predicate.Comparison)
        and clause.field == "event"
        and clause.op in {"==", "!="}
    }


def predicate_targets_event_state(predicate: state_predicate.Predicate) -> bool:
    return bool(predicate_event_names(predicate))


def apply_button(pyboy: Any, button: str, *, hold_frames: int, total_frames: int) -> None:
    pyboy.button(button, delay=hold_frames)
    pyboy.tick(max(hold_frames, total_frames), False)


def button_event(button: str, hold_frames: int, total_frames: int) -> dict[str, Any]:
    return {
        "kind": "button",
        "button": button.upper(),
        "hold_frames": int(hold_frames),
        "total_frames": int(total_frames),
    }


def wait_event(frames: int) -> dict[str, Any]:
    return {"kind": "wait", "frames": int(frames)}


def format_search_input_log(report: dict[str, Any]) -> str:
    lines = [
        f"# Deity-navigator bounded-search extension for {report.get('predicate', '')}.",
        f"# Chained after checkpoint {report.get('checkpoint', '')}; generated by navigate --search-to.",
        "# Temporary PyBoy save-states were used only during search, not as proof.",
    ]
    for event in report.get("input_events", []):
        if event.get("kind") == "wait":
            lines.append(f"WAIT {int(event['frames'])}")
            continue
        button = str(event["button"]).upper()
        hold = int(event.get("hold_frames", 1))
        total = int(event.get("total_frames", hold))
        lines.append(f"{button} {hold}")
        remaining = total - hold
        if remaining > 0:
            lines.append(f"WAIT {remaining}")
    return "\n".join(lines) + "\n"


# --- re-validation (North-Star #4: honest synthesis) -------------------------


def verify_run(
    manifest_path: str,
    *,
    rom: Path = DEFAULT_ROM,
    symbols_path: Path = DEFAULT_SYMBOLS,
    frame_slack: int = FRAME_SLACK,
) -> dict[str, Any]:
    """Replay a run manifest's checkpoint and re-assert its predicate + map.

    Confirms (1) the checkpoint log bytes are unchanged since the run (sha) and
    (2) re-driving from the checkpoint re-satisfies the stored predicate and
    reaches the same map const — the deterministic round-trip the roadmap asks
    of every synthesized state.
    """
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("kind") != "deity_navigator_run":
        raise ValueError(f"not a navigator run manifest: {manifest_path}")
    checkpoint_data = load_checkpoint(manifest["checkpoint"])
    expected_sha = manifest.get("checkpoint_log_sha256")
    actual_combined_sha = combined_log_sha256(tuple(checkpoint_data["log_paths"]))
    legacy_single_sha = (
        log_sha256(tuple(checkpoint_data["log_paths"])[0])
        if len(tuple(checkpoint_data["log_paths"])) == 1
        else None
    )
    sha_ok = bool(expected_sha) and expected_sha in {actual_combined_sha, legacy_single_sha}
    seed_state_path = checkpoint_data.get("seed_state_path")
    if seed_state_path is not None:
        expected_seed_sha = manifest.get("checkpoint_seed_state_sha256")
        sha_ok = bool(expected_seed_sha) and log_sha256(Path(seed_state_path)) == expected_seed_sha
    outcome = navigate_to(
        manifest["predicate"],
        checkpoint=manifest["checkpoint"],
        rom=rom,
        symbols_path=symbols_path,
        frame_slack=frame_slack,
    )
    map_ok = bool(outcome.get("reached")) and outcome.get("map") == manifest.get("observed_map")
    signature = outcome.get("observed_signature")
    expected_signature = manifest.get("observed_signature")
    signature_ok = map_ok
    if isinstance(expected_signature, dict):
        signature_ok = all(signature.get(key) == value for key, value in expected_signature.items())
    frame_ok = (
        int(outcome.get("frame", -1)) == int(manifest["reached_frame"])
        if manifest.get("reached_frame") is not None and outcome.get("frame") is not None
        else True
    )
    return {
        "passed": bool(sha_ok and map_ok and signature_ok and frame_ok),
        "sha_ok": sha_ok,
        "predicate_satisfied": bool(outcome.get("reached")),
        "map_ok": map_ok,
        "signature_ok": signature_ok,
        "frame_ok": frame_ok,
        "expected_map": manifest.get("observed_map"),
        "expected_signature": expected_signature,
        "observed_signature": signature,
        "observed": outcome.get("map_desc") or outcome.get("nearest"),
    }


def select_checkpoint(predicate: state_predicate.Predicate, requested: str) -> str:
    if requested != "auto":
        return requested
    boss_name = predicate_boss_name(predicate)
    if boss_name:
        capture_id = boss_name.lower()
        if (CHECKPOINT_DIR / f"{BOSS_AI_CHECKPOINT_PREFIX}{capture_id}.manifest.json").exists():
            return f"{BOSS_AI_CHECKPOINT_PREFIX}{capture_id}"
        if BOSS_TRACE_MANIFEST.exists():
            try:
                data = json.loads(BOSS_TRACE_MANIFEST.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}
            for entry in data.get("captures", []):
                if isinstance(entry, dict) and str(entry.get("id", "")).lower() == capture_id:
                    if entry.get("pre_choice_state") or entry.get("save_state"):
                        return f"{BOSS_AI_CHECKPOINT_PREFIX}{capture_id}"
    wants_rival1 = any(
        isinstance(clause, state_predicate.Comparison)
        and clause.field == "trainer_class"
        and clause.op == "=="
        and clause.value == "RIVAL1"
        for clause in predicate.clauses
    )
    wants_trainer_battle = any(
        isinstance(clause, state_predicate.Flag)
        and clause.name == "trainer_battle"
        for clause in predicate.clauses
    )
    if (wants_rival1 or wants_trainer_battle) and (
        CHECKPOINT_DIR / f"{CHERRYGROVE_RIVAL_BATTLE_CHECKPOINT}.manifest.json"
    ).exists():
        return CHERRYGROVE_RIVAL_BATTLE_CHECKPOINT
    wants_cherrygrove_city = any(
        isinstance(clause, state_predicate.Comparison)
        and clause.field == "map"
        and clause.op == "=="
        and clause.value == "CHERRYGROVE_CITY"
        for clause in predicate.clauses
    )
    wants_idle_script = all(
        any(
            isinstance(clause, state_predicate.Comparison)
            and clause.field == field
            and clause.op == "=="
            and clause.value == 0
            for clause in predicate.clauses
        )
        for field in ("script_mode", "script_running")
    )
    if wants_cherrygrove_city and wants_idle_script and (
        CHECKPOINT_DIR / f"{CHERRYGROVE_POST_RIVAL_CHECKPOINT}.manifest.json"
    ).exists():
        return CHERRYGROVE_POST_RIVAL_CHECKPOINT
    wants_elms_lab = any(
        isinstance(clause, state_predicate.Comparison)
        and clause.field == "map"
        and clause.op == "=="
        and clause.value == "ELMS_LAB"
        for clause in predicate.clauses
    )
    if wants_elms_lab and (
        "EVENT_GAVE_MYSTERY_EGG_TO_ELM" in predicate_event_names(predicate)
        and (CHECKPOINT_DIR / f"{ELMS_LAB_AFTER_AIDE_CHECKPOINT}.manifest.json").exists()
    ):
        return ELMS_LAB_AFTER_AIDE_CHECKPOINT
    if wants_elms_lab and (
        CHECKPOINT_DIR / f"{ELMS_LAB_POST_OFFICER_CHECKPOINT}.manifest.json"
    ).exists():
        return ELMS_LAB_POST_OFFICER_CHECKPOINT
    wants_ecruteak_gym = any(
        isinstance(clause, state_predicate.Comparison)
        and clause.field == "map"
        and clause.op == "=="
        and clause.value == "ECRUTEAK_GYM"
        for clause in predicate.clauses
    )
    if wants_ecruteak_gym and BOSS_TRACE_MANIFEST.exists():
        try:
            data = json.loads(BOSS_TRACE_MANIFEST.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        for entry in data.get("captures", []):
            if isinstance(entry, dict) and str(entry.get("id", "")).lower() == "morty":
                if entry.get("pre_choice_state") or entry.get("save_state"):
                    return f"{BOSS_AI_CHECKPOINT_PREFIX}morty"
    wants_mr_pokemon_house = any(
        isinstance(clause, state_predicate.Comparison)
        and clause.field == "map"
        and clause.op == "=="
        and clause.value == "MR_POKEMONS_HOUSE"
        for clause in predicate.clauses
    )
    if wants_mr_pokemon_house and (
        CHECKPOINT_DIR / f"{MR_POKEMON_AFTER_OAK_CHECKPOINT}.manifest.json"
    ).exists():
        return MR_POKEMON_AFTER_OAK_CHECKPOINT
    wants_route30 = any(
        isinstance(clause, state_predicate.Comparison)
        and clause.field == "map"
        and clause.op == "=="
        and clause.value == "ROUTE_30"
        for clause in predicate.clauses
    )
    if wants_route30 and (CHECKPOINT_DIR / f"{ROUTE30_SOUTH_CHECKPOINT}.manifest.json").exists():
        return ROUTE30_SOUTH_CHECKPOINT
    wants_route46 = any(
        isinstance(clause, state_predicate.Comparison)
        and clause.field == "map"
        and clause.op == "=="
        and clause.value == "ROUTE_46"
        for clause in predicate.clauses
    )
    if wants_route46 and (CHECKPOINT_DIR / f"{ROUTE46_SOUTH_CHECKPOINT}.manifest.json").exists():
        return ROUTE46_SOUTH_CHECKPOINT
    wants_route29 = any(
        isinstance(clause, state_predicate.Comparison)
        and clause.field == "map"
        and clause.op == "=="
        and clause.value == "ROUTE_29"
        for clause in predicate.clauses
    )
    wants_wild = any(
        isinstance(clause, state_predicate.Flag)
        and clause.name == "wild_battle"
        for clause in predicate.clauses
    )
    if wants_route29 and wants_wild and (CHECKPOINT_DIR / f"{ROUTE29_WILD_CHECKPOINT}.manifest.json").exists():
        return ROUTE29_WILD_CHECKPOINT
    wants_any_map = any(
        isinstance(clause, state_predicate.Comparison)
        and clause.field == "map"
        and clause.op == "=="
        for clause in predicate.clauses
    )
    if predicate_targets_battle_state(predicate) and not wants_any_map and not wants_wild and BOSS_TRACE_MANIFEST.exists():
        try:
            data = json.loads(BOSS_TRACE_MANIFEST.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        for entry in data.get("captures", []):
            if isinstance(entry, dict) and str(entry.get("id", "")).lower() == "falkner":
                if entry.get("pre_choice_state") or entry.get("save_state"):
                    return f"{BOSS_AI_CHECKPOINT_PREFIX}falkner"
    return DEFAULT_CHECKPOINT


# --- pure-logic self-test (no emulator) --------------------------------------


def run_self_test() -> dict[str, Any]:
    """Verify the navigator's logic without booting PyBoy or needing a built ROM.

    Covers checkpoint parsing + byte integrity, map-catalog const resolution,
    and the predicate parse/observe/evaluate path the live drive uses — fast and
    deterministic so it can sit in the frozen selftest gate. The end-to-end
    self-drive proof lives in the deity benchmark (driver: auto), which actually
    boots PyBoy and reaches the bedroom.
    """
    checks: list[dict[str, Any]] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    checkpoint_data = load_checkpoint("new_game")
    playback = checkpoint_data["playback"]
    manifest = checkpoint_data["manifest"]

    record(
        "checkpoint_parses",
        not playback["errors"] and playback["event_count"] > 0,
        f"events={playback['event_count']} errors={playback['errors']}",
    )
    record(
        "checkpoint_buttons",
        {"A", "START"} <= set(playback["button_sample"]),
        f"button_sample={playback['button_sample']}",
    )
    actual_sha = log_sha256(tuple(checkpoint_data["log_paths"])[0])
    record(
        "checkpoint_sha",
        checkpoint_log_sha_ok(checkpoint_data),
        f"actual={actual_sha} manifest={manifest['input_log_sha256']}",
    )

    catalog = load_map_catalog(root=ROOT, labels={})
    group, number = manifest["expected_group"], manifest["expected_number"]
    const = map_const(catalog, group, number)
    record(
        "catalog_const",
        const == manifest["expected_const"],
        f"{group}:{number} -> {const} (want {manifest['expected_const']})",
    )

    predicate = state_predicate.parse(f"map={manifest['expected_const']}")
    hit = build_observed(catalog, group, number)
    record("predicate_hit", state_predicate.evaluate(predicate, hit).satisfied, f"observed={hit}")

    miss = state_predicate.evaluate(predicate, {"map": "ROUTE_29"})
    record("predicate_miss", (not miss.satisfied) and bool(miss.unmet), f"unmet={miss.unmet}")

    no_map = build_observed(catalog, 0, 0)
    record(
        "fail_closed_no_map",
        "map" not in no_map and not state_predicate.evaluate(predicate, no_map).satisfied,
        f"observed={no_map}",
    )

    unobserved = state_predicate.parse("battle(boss=MORTY) and turn==3")
    record(
        "fail_closed_unobserved",
        not state_predicate.evaluate(unobserved, hit).satisfied,
        "predicate over unobserved fields stays unsatisfied (capability not built)",
    )

    trainer_class_names = parse_trainer_class_names()
    species_names = parse_pokemon_names()
    morty_battle = build_observed(
        catalog,
        group,
        number,
        battle_mode=2,
        trainer_class=4,
        trainer_id=1,
        trainer_class_name=trainer_class_names.get(4),
        boss=trainer_class_names.get(4),
        enemy_species=0x5E,
        enemy_active=species_names.get(0x5E),
        player_species=0x9C,
        player_active=species_names.get(0x9C),
        player_turns_taken=3,
        enemy_turns_taken=3,
    )
    morty_predicate = state_predicate.parse(
        "battle(boss=MORTY) and trainer_class=MORTY and trainer_id=1 and turn==3 and enemy_active=GENGAR"
    )
    record(
        "trainer_boss_predicate_hit",
        state_predicate.evaluate(morty_predicate, morty_battle).satisfied,
        f"observed={morty_battle}",
    )
    record(
        "auto_select_boss_seed_checkpoint",
        select_checkpoint(state_predicate.parse("battle(boss=MORTY)"), "auto") == "boss_ai_morty",
        f"selected={select_checkpoint(state_predicate.parse('battle(boss=MORTY)'), 'auto')}",
    )

    route29_data = load_checkpoint(ROUTE29_WILD_CHECKPOINT)
    route29_manifest = route29_data["manifest"]
    record(
        "route29_checkpoint_sha",
        checkpoint_log_sha_ok(route29_data),
        f"logs={route29_data['log_names']}",
    )
    route_hit = build_observed(
        catalog,
        route29_manifest["expected_group"],
        route29_manifest["expected_number"],
        battle_mode=route29_manifest["expected_battle_mode"],
        temp_wild_species=route29_manifest["expected_temp_wild_species"],
        party_count=1,
        rng={"hRandomAdd": 0x00, "hRandomSub": 0x00},
    )
    route_predicate = state_predicate.parse("wild_battle and map=ROUTE_29")
    record(
        "route29_wild_predicate_hit",
        state_predicate.evaluate(route_predicate, route_hit).satisfied,
        f"observed={route_hit}",
    )
    record(
        "auto_select_route29_wild",
        select_checkpoint(route_predicate, "auto") == ROUTE29_WILD_CHECKPOINT,
        f"selected={select_checkpoint(route_predicate, 'auto')}",
    )
    record(
        "isolated_storage_seed",
        route29_manifest.get("storage_seed", {}).get("ram_file") == "zeroed_in_memory",
        f"storage_seed={route29_manifest.get('storage_seed')}",
    )
    route46_data = load_checkpoint(ROUTE46_SOUTH_CHECKPOINT)
    route46_manifest = route46_data["manifest"]
    record(
        "route46_checkpoint_sha",
        checkpoint_log_sha_ok(route46_data),
        f"logs={route46_data['log_names']}",
    )
    route46_hit = build_observed(
        catalog,
        route46_manifest["expected_group"],
        route46_manifest["expected_number"],
        x=route46_manifest["expected_x"],
        y=route46_manifest["expected_y"],
        battle_mode=route46_manifest["expected_battle_mode"],
        party_count=route46_manifest["expected_party_count"],
        rng=route46_manifest["expected_rng_at_reach"],
    )
    route46_predicate = state_predicate.parse("map=ROUTE_46 and x=7 and y=33")
    record(
        "route46_search_waypoint_predicate_hit",
        state_predicate.evaluate(route46_predicate, route46_hit).satisfied,
        f"observed={route46_hit}",
    )
    record(
        "auto_select_route46",
        select_checkpoint(state_predicate.parse("map=ROUTE_46"), "auto") == ROUTE46_SOUTH_CHECKPOINT,
        f"selected={select_checkpoint(state_predicate.parse('map=ROUTE_46'), 'auto')}",
    )
    route30_data = load_checkpoint(ROUTE30_SOUTH_CHECKPOINT)
    route30_manifest = route30_data["manifest"]
    record(
        "route30_checkpoint_sha",
        checkpoint_log_sha_ok(route30_data),
        f"logs={route30_data['log_names']}",
    )
    route30_hit = build_observed(
        catalog,
        route30_manifest["expected_group"],
        route30_manifest["expected_number"],
        x=route30_manifest["expected_x"],
        y=route30_manifest["expected_y"],
        battle_mode=route30_manifest["expected_battle_mode"],
        party_count=route30_manifest["expected_party_count"],
        rng=route30_manifest["expected_rng_at_reach"],
    )
    route30_predicate = state_predicate.parse("map=ROUTE_30 and x=6 and y=53")
    record(
        "route30_search_waypoint_predicate_hit",
        state_predicate.evaluate(route30_predicate, route30_hit).satisfied,
        f"observed={route30_hit}",
    )
    record(
        "auto_select_route30",
        select_checkpoint(state_predicate.parse("map=ROUTE_30"), "auto") == ROUTE30_SOUTH_CHECKPOINT,
        f"selected={select_checkpoint(state_predicate.parse('map=ROUTE_30'), 'auto')}",
    )
    mr_pokemon_data = load_checkpoint(MR_POKEMON_AFTER_OAK_CHECKPOINT)
    mr_pokemon_manifest = mr_pokemon_data["manifest"]
    record(
        "mr_pokemon_after_oak_checkpoint_sha",
        checkpoint_log_sha_ok(mr_pokemon_data),
        f"logs={mr_pokemon_data['log_names']}",
    )
    mr_pokemon_hit = build_observed(
        catalog,
        mr_pokemon_manifest["expected_group"],
        mr_pokemon_manifest["expected_number"],
        x=mr_pokemon_manifest["expected_x"],
        y=mr_pokemon_manifest["expected_y"],
        battle_mode=mr_pokemon_manifest["expected_battle_mode"],
        party_count=mr_pokemon_manifest["expected_party_count"],
        rng=mr_pokemon_manifest["expected_rng_at_reach"],
        script_mode=mr_pokemon_manifest["expected_script_mode"],
        script_running=mr_pokemon_manifest["expected_script_running"],
    )
    mr_pokemon_predicate = state_predicate.parse(
        "map=MR_POKEMONS_HOUSE and x=3 and y=6 and script_mode=0 and script_running=0"
    )
    record(
        "mr_pokemon_after_oak_predicate_hit",
        state_predicate.evaluate(mr_pokemon_predicate, mr_pokemon_hit).satisfied,
        f"observed={mr_pokemon_hit}",
    )
    record(
        "auto_select_mr_pokemon_house",
        select_checkpoint(state_predicate.parse("map=MR_POKEMONS_HOUSE"), "auto")
        == MR_POKEMON_AFTER_OAK_CHECKPOINT,
        f"selected={select_checkpoint(state_predicate.parse('map=MR_POKEMONS_HOUSE'), 'auto')}",
    )
    rival_data = load_checkpoint(CHERRYGROVE_RIVAL_BATTLE_CHECKPOINT)
    rival_manifest = rival_data["manifest"]
    record(
        "cherrygrove_rival_battle_checkpoint_sha",
        checkpoint_log_sha_ok(rival_data),
        f"logs={rival_data['log_names']}",
    )
    rival_hit = build_observed(
        catalog,
        rival_manifest["expected_group"],
        rival_manifest["expected_number"],
        x=rival_manifest["expected_x"],
        y=rival_manifest["expected_y"],
        battle_mode=rival_manifest["expected_battle_mode"],
        trainer_class=rival_manifest["expected_trainer_class"],
        trainer_id=rival_manifest["expected_trainer_id"],
        trainer_class_name=rival_manifest["expected_trainer_class_name"],
        enemy_species=rival_manifest["expected_enemy_species"],
        enemy_active=rival_manifest["expected_enemy_active"],
        party_count=rival_manifest["expected_party_count"],
        rng=rival_manifest["expected_rng_at_reach"],
        script_mode=rival_manifest["expected_script_mode"],
        script_running=rival_manifest["expected_script_running"],
    )
    rival_predicate = state_predicate.parse("trainer_battle and trainer_class=RIVAL1")
    record(
        "cherrygrove_rival_battle_predicate_hit",
        state_predicate.evaluate(rival_predicate, rival_hit).satisfied,
        f"observed={rival_hit}",
    )
    record(
        "auto_select_rival_trainer_battle",
        select_checkpoint(rival_predicate, "auto") == CHERRYGROVE_RIVAL_BATTLE_CHECKPOINT,
        f"selected={select_checkpoint(rival_predicate, 'auto')}",
    )
    post_rival_data = load_checkpoint(CHERRYGROVE_POST_RIVAL_CHECKPOINT)
    post_rival_manifest = post_rival_data["manifest"]
    record(
        "cherrygrove_post_rival_checkpoint_sha",
        checkpoint_log_sha_ok(post_rival_data),
        f"logs={post_rival_data['log_names']}",
    )
    post_rival_hit = build_observed(
        catalog,
        post_rival_manifest["expected_group"],
        post_rival_manifest["expected_number"],
        x=post_rival_manifest["expected_x"],
        y=post_rival_manifest["expected_y"],
        battle_mode=post_rival_manifest["expected_battle_mode"],
        enemy_species=post_rival_manifest["expected_enemy_species"],
        enemy_active=post_rival_manifest["expected_enemy_active"],
        party_count=post_rival_manifest["expected_party_count"],
        rng=post_rival_manifest["expected_rng_at_reach"],
        script_mode=post_rival_manifest["expected_script_mode"],
        script_running=post_rival_manifest["expected_script_running"],
    )
    post_rival_predicate = state_predicate.parse(
        "map=CHERRYGROVE_CITY and x=33 and y=8 and script_mode=0 and script_running=0"
    )
    record(
        "cherrygrove_post_rival_predicate_hit",
        state_predicate.evaluate(post_rival_predicate, post_rival_hit).satisfied,
        f"observed={post_rival_hit}",
    )
    record(
        "auto_select_cherrygrove_post_rival",
        select_checkpoint(post_rival_predicate, "auto") == CHERRYGROVE_POST_RIVAL_CHECKPOINT,
        f"selected={select_checkpoint(post_rival_predicate, 'auto')}",
    )
    elms_lab_data = load_checkpoint(ELMS_LAB_POST_OFFICER_CHECKPOINT)
    elms_lab_manifest = elms_lab_data["manifest"]
    record(
        "elms_lab_post_officer_checkpoint_sha",
        checkpoint_log_sha_ok(elms_lab_data),
        f"logs={elms_lab_data['log_names']}",
    )
    elms_lab_hit = build_observed(
        catalog,
        elms_lab_manifest["expected_group"],
        elms_lab_manifest["expected_number"],
        x=elms_lab_manifest["expected_x"],
        y=elms_lab_manifest["expected_y"],
        battle_mode=elms_lab_manifest["expected_battle_mode"],
        enemy_species=elms_lab_manifest["expected_enemy_species"],
        enemy_active=elms_lab_manifest["expected_enemy_active"],
        party_count=elms_lab_manifest["expected_party_count"],
        facing=elms_lab_manifest["expected_facing"],
        rng=elms_lab_manifest["expected_rng_at_reach"],
        script_mode=elms_lab_manifest["expected_script_mode"],
        script_running=elms_lab_manifest["expected_script_running"],
        event_flags=elms_lab_manifest["expected_events"],
    )
    elms_lab_predicate = state_predicate.parse(
        "event=EVENT_GOT_MYSTERY_EGG_FROM_MR_POKEMON and "
        "event=EVENT_RIVAL_CHERRYGROVE_CITY and map=ELMS_LAB and x=4 and y=3 "
        "and script_mode=0 and script_running=0"
    )
    record(
        "elms_lab_post_officer_predicate_hit",
        state_predicate.evaluate(elms_lab_predicate, elms_lab_hit).satisfied,
        f"observed={elms_lab_hit}",
    )
    record(
        "auto_select_elms_lab_post_officer",
        select_checkpoint(elms_lab_predicate, "auto") == ELMS_LAB_POST_OFFICER_CHECKPOINT,
        f"selected={select_checkpoint(elms_lab_predicate, 'auto')}",
    )
    after_aide_data = load_checkpoint(ELMS_LAB_AFTER_AIDE_CHECKPOINT)
    after_aide_manifest = after_aide_data["manifest"]
    record(
        "elms_lab_after_aide_checkpoint_sha",
        checkpoint_log_sha_ok(after_aide_data),
        f"logs={after_aide_data['log_names']}",
    )
    after_aide_hit = build_observed(
        catalog,
        after_aide_manifest["expected_group"],
        after_aide_manifest["expected_number"],
        x=after_aide_manifest["expected_x"],
        y=after_aide_manifest["expected_y"],
        battle_mode=after_aide_manifest["expected_battle_mode"],
        enemy_species=after_aide_manifest["expected_enemy_species"],
        enemy_active=after_aide_manifest["expected_enemy_active"],
        party_count=after_aide_manifest["expected_party_count"],
        facing=after_aide_manifest["expected_facing"],
        rng=after_aide_manifest["expected_rng_at_reach"],
        script_mode=after_aide_manifest["expected_script_mode"],
        script_running=after_aide_manifest["expected_script_running"],
        event_flags=after_aide_manifest["expected_events"],
    )
    after_aide_predicate = state_predicate.parse(
        "event=EVENT_GAVE_MYSTERY_EGG_TO_ELM and map=ELMS_LAB and x=4 and y=8 "
        "and script_mode=0 and script_running=0"
    )
    record(
        "elms_lab_after_aide_predicate_hit",
        state_predicate.evaluate(after_aide_predicate, after_aide_hit).satisfied,
        f"observed={after_aide_hit}",
    )
    record(
        "auto_select_elms_lab_after_aide",
        select_checkpoint(after_aide_predicate, "auto") == ELMS_LAB_AFTER_AIDE_CHECKPOINT,
        f"selected={select_checkpoint(after_aide_predicate, 'auto')}",
    )
    search_report = {
        "predicate": "map==ROUTE_46",
        "checkpoint": ROUTE29_WILD_CHECKPOINT,
        "input_events": [
            button_event("left", 16, 100),
            wait_event(12),
        ],
    }
    search_log_text = format_search_input_log(search_report)
    record(
        "search_log_formatter",
        "LEFT 16" in search_log_text and "WAIT 84" in search_log_text and "WAIT 12" in search_log_text,
        search_log_text.replace("\n", " | "),
    )

    errors = [f"{c['name']}: {c['detail']}" for c in checks if not c["ok"]]
    return {"passed": not errors, "checks": checks, "errors": errors}


# --- CLI ---------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger navigate",
        description=(
            "Self-drive pokegold to a target-state predicate from a fixed checkpoint, "
            "capturing a save-state + replayable manifest on success."
        ),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--to", metavar="PREDICATE", help="target-state predicate to self-drive to")
    mode.add_argument("--search-to", metavar="PREDICATE", help="bounded-search for a replayable input extension")
    mode.add_argument("--verify", metavar="MANIFEST", help="replay a run manifest and re-assert it")
    mode.add_argument("--self-test", action="store_true", help="pure-logic self-check (no emulator)")
    parser.add_argument("--checkpoint", default="auto", help="checkpoint id to replay (default: auto)")
    parser.add_argument("--rom", default=str(DEFAULT_ROM))
    parser.add_argument("--symbols", default=str(DEFAULT_SYMBOLS))
    parser.add_argument("--save-state", default=None, help="save-state output path (default: under .local/tmp)")
    parser.add_argument("--manifest-out", default=None, help="run-manifest output path")
    parser.add_argument("--frame-slack", type=int, default=FRAME_SLACK)
    parser.add_argument("--search-steps", type=int, default=SEARCH_DEFAULT_MAX_STEPS)
    parser.add_argument("--search-nodes", type=int, default=SEARCH_DEFAULT_MAX_NODES)
    parser.add_argument("--search-log-out", default=None, help="write the found search extension as an input log")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.self_test:
        report = run_self_test()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            for check in report["checks"]:
                print(f"  {'[ok]  ' if check['ok'] else '[FAIL]'} {check['name']} - {check['detail']}")
            print(f"navigate self-test {'PASS' if report['passed'] else 'FAIL'}")
        return 0 if report["passed"] else 1

    if args.verify:
        report = verify_run(
            args.verify, rom=Path(args.rom), symbols_path=Path(args.symbols), frame_slack=args.frame_slack
        )
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"verify {'PASS' if report['passed'] else 'FAIL'}: {report}")
        return 0 if report["passed"] else 1

    if args.search_to:
        try:
            report = search_to(
                args.search_to,
                checkpoint=args.checkpoint,
                rom=Path(args.rom),
                symbols_path=Path(args.symbols),
                max_steps=args.search_steps,
                max_nodes=args.search_nodes,
                search_log_out=args.search_log_out,
            )
        except state_predicate.PredicateError as exc:
            print(f"invalid predicate: {exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(report, indent=2))
        elif report.get("reached"):
            print(
                f"search found: {report['predicate']} from checkpoint {report['checkpoint']} "
                f"after {report['steps']} steps; nearest {report['nearest']}"
            )
            if report.get("search_log"):
                print(f"search-log: {report['search_log']}")
        else:
            print(
                f"search failed: could not reach {report['predicate']} from checkpoint {report['checkpoint']}; "
                f"nearest observed {report['nearest']}; unmet: {', '.join(report.get('unmet', []))}",
                file=sys.stderr,
            )
        return 0 if report.get("reached") else 1

    try:
        outcome = navigate_to(
            args.to,
            checkpoint=args.checkpoint,
            rom=Path(args.rom),
            symbols_path=Path(args.symbols),
            save_state=args.save_state,
            manifest_out=args.manifest_out,
            frame_slack=args.frame_slack,
        )
    except state_predicate.PredicateError as exc:
        print(f"invalid predicate: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(outcome, indent=2))
        return 0 if outcome["reached"] else 1

    if outcome["reached"]:
        print(
            f"{EVIDENCE_MARKER}: {outcome['predicate']} at frame {outcome['frame']} "
            f"[checkpoint={outcome['checkpoint']}] {outcome['map_desc']}"
        )
        print(f"save-state: {outcome['state_path']}")
        print(f"manifest:   {outcome['manifest_path']}")
        return 0

    print(
        f"could not reach {outcome['predicate']} within checkpoint {outcome['checkpoint']}; "
        f"nearest observed {outcome['nearest']}; unmet: {', '.join(outcome['unmet'])}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
