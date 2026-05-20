from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tools.trace import runtime as trace_runtime

from .catalog import ROOT
from .content_scenarios import (
    EVENT_RUNTIME_ROUTE_KIND,
    EVENT_RUNTIME_ROUTE_KEY,
    EVENT_RUNTIME_ROUTE_LEGACY_KEY,
    event_runtime_materialization_route,
    field_at,
    output_sink_ids,
    split_macro_args,
)
from .ingest import sha256_file
from .localize import normalize_path
from .minimize import load_scenario_files, unique_list
from .provenance import display_path, parse_symbol_table, resolve_path
from .reporting import load_reports
from .setup_plan import collect_content_setup_scenarios, setup_scenario_id_for
from .workflow import command_address_arg, command_is_runnable


MAP_GROUP_RE = re.compile(r"^MapGroup_(?P<name>[A-Za-z0-9_]+):")
MAP_ENTRY_RE = re.compile(r"^\s*map\s+(?P<name>[A-Za-z0-9_]+)\s*,")
SCENE_VAR_RE = re.compile(r"^\s*scene_var\s+(?P<map>[A-Za-z0-9_]+)\s*,\s*(?P<symbol>[A-Za-z0-9_]+)")
SCENE_SCRIPT_RE = re.compile(r"^\s*scene_script\s+(?P<script>[A-Za-z_.$][A-Za-z0-9_.$]*)\s*,\s*(?P<const>[A-Za-z0-9_]+)")
MAP_PATCH_SYMBOLS = ("wMapGroup", "wMapNumber", "wXCoord", "wYCoord")
EVENT_ENGINE_POSITION_SYMBOLS = ("wPlayerMapX", "wPlayerMapY", "wPlayerDirection")
OW_DIRECTION_VALUES = {
    "OW_DOWN": 0,
    "OW_UP": 4,
    "OW_LEFT": 8,
    "OW_RIGHT": 12,
}
OBJECT_STRUCT_INDEX = 1
MAP_OBJECT_INDEX = 2
OBJECT_STRUCT_SYMBOL = "wObject1Struct"
MAX_OBJECT_STRUCT_INDEX = 12
MAX_MAP_OBJECT_INDEX = 15
OBJECT_STRUCT_OFFSETS = {
    "OBJECT_SPRITE": 0x00,
    "OBJECT_MAP_OBJECT_INDEX": 0x01,
    "OBJECT_MOVEMENT_TYPE": 0x03,
    "OBJECT_FLAGS1": 0x04,
    "OBJECT_FLAGS2": 0x05,
    "OBJECT_PALETTE": 0x06,
    "OBJECT_WALKING": 0x07,
    "OBJECT_DIRECTION": 0x08,
    "OBJECT_STEP_TYPE": 0x09,
    "OBJECT_FACING": 0x0D,
    "OBJECT_MAP_X": 0x10,
    "OBJECT_MAP_Y": 0x11,
    "OBJECT_LAST_MAP_X": 0x12,
    "OBJECT_LAST_MAP_Y": 0x13,
    "OBJECT_INIT_X": 0x14,
    "OBJECT_INIT_Y": 0x15,
    "OBJECT_RADIUS": 0x16,
    "OBJECT_SPRITE_X": 0x17,
    "OBJECT_SPRITE_Y": 0x18,
    "OBJECT_RANGE": 0x20,
}
OBJECT_EVENT_CONSTANT_FILES = (
    "constants/ram_constants.asm",
    "constants/misc_constants.asm",
    "constants/item_constants.asm",
    "constants/sprite_constants.asm",
    "constants/sprite_data_constants.asm",
    "constants/map_object_constants.asm",
    "constants/script_constants.asm",
    "constants/collision_constants.asm",
    "constants/event_flags.asm",
)
SPRITE_MOVEMENT_DATA_FILE = "data/sprites/map_objects.asm"
BIG_OBJECT_FLAG = 0x80
OBJECT_EVENT_BASE_CONSTANTS = {
    "SCREEN_WIDTH": 20,
    "SCREEN_HEIGHT": 18,
    "MAPOBJECT_SCREEN_WIDTH": 12,
    "MAPOBJECT_SCREEN_HEIGHT": 11,
    "SPRITE_CHRIS": 1,
    "SPRITEMOVEDATA_STANDING_DOWN": 6,
    "OBJECTTYPE_SCRIPT": 0,
    "COLL_COUNTER": 0x90,
    "DOWN": 0,
    "UP": 1,
    "LEFT": 2,
    "RIGHT": 3,
    "WONT_DELETE": 0x02,
    "FIXED_FACING": 0x04,
    "SLIDING": 0x08,
    "MOVE_ANYWHERE": 0x20,
    "EMOTE_OBJECT": 0x80,
    "LOW_PRIORITY": 0x01,
    "HIGH_PRIORITY": 0x02,
    "BOULDER_MOVING": 0x04,
    "OVERHEAD": 0x08,
    "USE_OBP1": 0x10,
    "FROZEN": 0x20,
    "OFF_SCREEN": 0x40,
    "SWIMMING": 0x20,
    "STRENGTH_BOULDER": 0x40,
    "BIG_OBJECT": BIG_OBJECT_FLAG,
}
OBJECT_EVENT_WATCH_SYMBOLS = (
    OBJECT_STRUCT_SYMBOL,
    "wMap2ObjectStructID",
    "wMap2ObjectSprite",
    "wMap2ObjectXCoord",
    "wMap2ObjectYCoord",
    "wMap2ObjectScript",
    "wMap2ObjectEventFlag",
)
MAP_OBJECT_FIELD_SUFFIXES = (
    "StructID",
    "Sprite",
    "YCoord",
    "XCoord",
    "Movement",
    "Radius",
    "Hour1",
    "Hour2",
    "Type",
    "SightRange",
    "Script",
    "EventFlag",
)
COUNTER_TILE_SYMBOLS_BY_FACING = {
    "OW_DOWN": "wTileDown",
    "OW_UP": "wTileUp",
    "OW_LEFT": "wTileLeft",
    "OW_RIGHT": "wTileRight",
}
TIMEOFDAY_SYMBOL = "wTimeOfDay"
HOURS_SYMBOL = "hHours"
TIME_OF_DAY_ORDER = ("MORN", "DAY", "NITE")
TIME_OF_DAY_HOUR_CONSTANTS = {
    "MORN": "MORN_HOUR",
    "DAY": "DAY_HOUR",
    "NITE": "NITE_HOUR",
}
TIME_OF_DAY_DEFAULT_VALUES = {
    "MORN_F": 0,
    "DAY_F": 1,
    "NITE_F": 2,
    "MORN_HOUR": 4,
    "DAY_HOUR": 10,
    "NITE_HOUR": 18,
    "MAX_HOUR": 24,
}
LARGE_OBJECT_COLLISION_MODEL = "WillObjectIntersectBigObject_fixed_2x2"
LARGE_OBJECT_SIZE_SOURCE = "engine/overworld/npc_movement.asm:WillObjectIntersectBigObject"
SCRIPT_ENTRY_PATCH_SYMBOLS = ("wScriptBank", "wScriptPos", "wScriptRunning", "wScriptMode", "wScriptStackSize")
MOVEMENT_ENTRY_PATCH_SYMBOLS = (
    "wMovementObject",
    "wMovementDataBank",
    "wMovementDataAddress",
    "wMovementPointer",
    "wScriptMode",
)
AUDIO_ENTRY_WATCH_SYMBOLS = (
    "wMusicID",
    "wMusicBank",
    "wChannel1Flags1",
    "wChannel2Flags1",
    "wChannel3Flags1",
    "wChannel4Flags1",
)
AUDIO_HARDWARE_OUTPUTS = (
    ("rAUD1SWEEP", "$FF10"),
    ("rAUD1LEN", "$FF11"),
    ("rAUD1ENV", "$FF12"),
    ("rAUD1LOW", "$FF13"),
    ("rAUD1HIGH", "$FF14"),
    ("rAUD2LEN", "$FF16"),
    ("rAUD2ENV", "$FF17"),
    ("rAUD2LOW", "$FF18"),
    ("rAUD2HIGH", "$FF19"),
    ("rAUD3ENA", "$FF1A"),
    ("rAUD3LEN", "$FF1B"),
    ("rAUD3LEVEL", "$FF1C"),
    ("rAUD3LOW", "$FF1D"),
    ("rAUD3HIGH", "$FF1E"),
    ("rAUD4LEN", "$FF20"),
    ("rAUD4ENV", "$FF21"),
    ("rAUD4POLY", "$FF22"),
    ("rAUD4GO", "$FF23"),
    ("rAUDVOL", "$FF24"),
    ("rAUDTERM", "$FF25"),
    ("rAUDENA", "$FF26"),
)
ASSET_REQUEST_WATCH_SYMBOLS = (
    "wRequested2bppSource",
    "wRequested2bppDest",
    "wRequested2bppSize",
    "wRequested1bppSource",
    "wRequested1bppDest",
    "wRequested1bppSize",
)
UI_OUTPUT_WATCH_SYMBOLS = (
    "wTilemap",
    "wAttrmap",
    "hBGMapMode",
    "hBGMapAddress",
)
UI_TILEMAP_HELPERS = (
    "PlaceString",
    "CopyBytes",
    "ByteFill",
    "LoadTilemapToTempTilemap",
    "LoadStandardFont",
    "LoadFontsExtra",
    "WaitBGMap",
    "ApplyTilemap",
)
PLAYER_OBJECT = 0x00
SCRIPT_RUNNING_MAPSCRIPT = 0xFF
SCRIPT_MODE_READ = 0x01
SCRIPT_MODE_WAIT_MOVEMENT = 0x02


def build_content_state_report(
    *,
    reports: tuple[str, ...] = (),
    scenarios: tuple[str, ...] = (),
    scenario_ids: tuple[str, ...] = (),
    rom_path: str = "pokegold.gbc",
    symbols_path: str = "pokegold.sym",
    base_save_state: str = "",
    out_state: str = "",
    execute: bool = False,
    max_scenarios: int = 8,
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    loaded_scenarios, scenario_errors = load_scenario_files(scenarios=scenarios, root=root)
    selected_scenarios = collect_content_setup_scenarios(
        loaded_reports=loaded_reports,
        loaded_scenarios=loaded_scenarios,
        scenario_ids=scenario_ids,
    )[: max(1, max_scenarios)]
    symbols = resolve_path(symbols_path, root=root)
    rom = resolve_path(rom_path, root=root)
    base_state = resolve_path(base_save_state, root=root) if base_save_state else None
    output_state = resolve_path(out_state, root=root) if out_state else None
    errors = [*report_errors, *scenario_errors]
    warnings: list[str] = []
    if not selected_scenarios:
        errors.append("no content scenarios were selected from --report, --scenario, or --scenario-id")
    if not symbols.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if execute and not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if execute and base_state is None:
        errors.append("--execute requires --base-save-state")
    if execute and base_state is not None and not base_state.exists():
        errors.append(f"missing base save state: {base_save_state}")
    if execute and output_state is None:
        errors.append("--execute requires --out-state")

    symbol_table = parse_symbol_table(symbols) if symbols.exists() else {}
    precondition_kinds = selected_precondition_kinds(selected_scenarios)
    map_index, map_errors = load_map_index(root=root) if "map_position" in precondition_kinds else ({}, [])
    scene_var_index = load_scene_var_index(root=root) if "map_position" in precondition_kinds else {}
    errors.extend(map_errors)
    materializations: list[dict[str, Any]] = []
    for scenario in selected_scenarios:
        materializations.extend(
            materializations_for_scenario(
                scenario,
                map_index=map_index,
                scene_var_index=scene_var_index,
                symbol_table=symbol_table,
                symbols_path=symbols,
                root=root,
            )
        )
    errors.extend(
        error
        for materialization in materializations
        for error in materialization.get("errors", [])
    )
    patch_count = sum(len(item.get("patches", [])) for item in materializations)
    executable = bool(materializations) and patch_count > 0 and not errors
    execution = execute_materialization(
        materializations=materializations,
        rom=rom,
        base_state=base_state,
        output_state=output_state,
        execute=execute,
        root=root,
    ) if execute and executable else skipped_execution(execute=execute, out_state=out_state)
    materializations = promote_route_after_execution(materializations=materializations, execution=execution)
    errors.extend(execution.get("errors", []))
    warnings.extend(execution.get("warnings", []))
    commands = materialization_commands(
        reports=reports,
        scenarios=scenarios,
        scenario_ids=tuple(setup_scenario_id_for(scenario) for scenario in selected_scenarios if setup_scenario_id_for(scenario)),
        rom_path=rom_path,
        symbols_path=symbols_path,
        base_save_state=base_save_state,
        out_state=out_state,
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_content_state_materialization",
        "root": str(root),
        "valid": not errors,
        "executed": bool(execute and execution.get("executed")),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "rom": display_path(rom, root=root),
        "rom_sha256": sha256_file(rom) if rom.exists() else "",
        "symbols": display_path(symbols, root=root),
        "symbols_sha256": sha256_file(symbols) if symbols.exists() else "",
        "base_save_state": display_path(base_state, root=root) if base_state is not None else "",
        "out_state": display_path(output_state, root=root) if output_state is not None else out_state,
        "save_state_delta": execution.get("save_state_delta", {}),
        "input_reports": [item["source"] for item in loaded_reports],
        "input_scenarios": [item["source"] for item in loaded_scenarios],
        "input_scenario_ids": list(scenario_ids),
        "scenario_count": len(selected_scenarios),
        "materialization_count": len(materializations),
        "patch_count": patch_count,
        "materializations": materializations,
        "execution": execution,
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This materializes content preconditions by patching known WRAM symbols on top of an existing base save state.",
            "Coord-event map-position materialization also patches the map-specific scene variable when data/maps/scenes.asm and source scene_script order resolve the scene id.",
            "BG-event map-position materialization also patches player map coordinates, facing direction, and resolvable hidden-item/conditional event flag bits when those symbols are present; this is still planned state evidence until replay/watch/trace observes the event engine consuming it.",
            "Object-event map-position materialization patches the planned player-facing side plus one visible object struct and map-object row when the needed symbols and script pointer resolve; counter-tile variants also patch one cached facing-tile collision byte; both remain planned state evidence until replay/watch/trace observes TryObjectEvent consuming them.",
            "Map-position patches prove the selected map/x/y state values are installed; they do not by themselves prove the game engine has rebuilt every derived map object structure.",
            "Movement-entry patches install the movement data pointer fields; they do not synthesize the selected object's full object struct or visibility state.",
            "Audio channel headers and audio command streams emit explicit runtime trace/watch proof routes for music WRAM and rAUD hardware registers, while asset-loader entries emit loader request watch routes; both require an owning caller or save state before they can be executed.",
            "UI output-sink entries emit tilemap/attrmap watch, instruction-trace, and dynamic-taint routes, but still require a runtime caller or save state that reaches the selected drawing helper.",
            "Use replay/watch/trace-instructions after the patched state to prove the trigger reaches the intended helper code.",
        ],
    }


def load_map_index(*, root: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    path = root / "data" / "maps" / "maps.asm"
    if not path.exists():
        return {}, [f"missing map table: {display_path(path, root=root)}"]
    index: dict[str, dict[str, Any]] = {}
    group_index = 0
    map_index = 0
    group_name = ""
    for line_no, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        group_match = MAP_GROUP_RE.match(raw.strip())
        if group_match:
            group_index += 1
            map_index = 0
            group_name = group_match.group("name")
            continue
        map_match = MAP_ENTRY_RE.match(raw)
        if not map_match or group_index <= 0:
            continue
        map_index += 1
        map_name = map_match.group("name")
        index[map_name] = {
            "map_name": map_name,
            "map_group": group_index,
            "map_number": map_index,
            "group_name": group_name,
            "source_file": display_path(path, root=root),
            "line": line_no,
        }
    return index, []


def load_scene_var_index(*, root: Path) -> dict[str, dict[str, Any]]:
    path = root / "data" / "maps" / "scenes.asm"
    if not path.exists():
        return {}
    index: dict[str, dict[str, Any]] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        match = SCENE_VAR_RE.match(strip_comment(raw))
        if not match:
            continue
        map_constant = match.group("map")
        index[normalize_map_key(map_constant)] = {
            "map_constant": map_constant,
            "scene_symbol": match.group("symbol"),
            "source_file": display_path(path, root=root),
            "line": line_no,
        }
    return index


def materializations_for_scenario(
    scenario: dict[str, Any],
    *,
    map_index: dict[str, dict[str, Any]],
    scene_var_index: dict[str, dict[str, Any]],
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> list[dict[str, Any]]:
    out = []
    scenario_id = setup_scenario_id_for(scenario)
    for precondition in dict_items(scenario.get("state_preconditions")):
        kind = str(precondition.get("kind", ""))
        if kind != "map_position":
            if kind == "script_entry":
                out.append(
                    script_entry_materialization(
                        scenario=scenario,
                        precondition=precondition,
                        scenario_id=scenario_id,
                        symbol_table=symbol_table,
                        symbols_path=symbols_path,
                        root=root,
                    )
                )
                continue
            if kind == "movement_entry":
                out.append(
                    movement_entry_materialization(
                        scenario=scenario,
                        precondition=precondition,
                        scenario_id=scenario_id,
                        symbol_table=symbol_table,
                        symbols_path=symbols_path,
                        root=root,
                    )
                )
                continue
            if kind == "audio_engine_entry":
                out.append(audio_engine_entry_materialization(scenario=scenario, precondition=precondition, scenario_id=scenario_id))
                continue
            if kind == "asset_loader_entry":
                out.append(asset_loader_entry_materialization(scenario=scenario, precondition=precondition, scenario_id=scenario_id))
                continue
            if kind == "ui_output_sink":
                out.append(ui_output_sink_materialization(scenario=scenario, precondition=precondition, scenario_id=scenario_id))
                continue
            out.append(non_patch_materialization(scenario, precondition, reason=f"unsupported precondition kind: {kind}"))
            continue
        out.append(
            map_position_materialization(
                scenario=scenario,
                precondition=precondition,
                scenario_id=scenario_id,
                map_index=map_index,
                scene_var_index=scene_var_index,
                symbol_table=symbol_table,
                symbols_path=symbols_path,
                root=root,
            )
        )
    preconditions_by_id = {
        str(precondition.get("id", "")): precondition
        for precondition in dict_items(scenario.get("state_preconditions"))
        if precondition.get("id")
    }
    return [
        attach_event_runtime_route(
            materialization,
            preconditions_by_id.get(str(materialization.get("precondition_id", "")), {}),
        )
        for materialization in out
    ]


def attach_event_runtime_route(materialization: dict[str, Any], precondition: dict[str, Any]) -> dict[str, Any]:
    row = dict(materialization)
    route = {}
    if isinstance(precondition, dict):
        route = precondition.get(EVENT_RUNTIME_ROUTE_KEY) or precondition.get(EVENT_RUNTIME_ROUTE_LEGACY_KEY) or {}
    if not isinstance(route, dict) or not route:
        route = event_runtime_materialization_route(
            scenario_id=str(row.get("scenario_id", "")),
            scenario_type=str(row.get("scenario_type", "")),
            precondition_id=str(row.get("precondition_id", "")),
            precondition_kind=str(row.get("precondition_kind", "")),
            values=row.get("values") if isinstance(row.get("values"), dict) else {},
            watch_symbols=string_items(row.get("watch_symbols")),
            outputs=dict_items(row.get("outputs")),
        )
    else:
        route = dict(route)
    if route.get("kind") == EVENT_RUNTIME_ROUTE_LEGACY_KEY or not route.get("kind"):
        route["kind"] = EVENT_RUNTIME_ROUTE_KIND
    expected_sinks = unique_list(
        [
            *string_items(route.get("expected_sinks")),
            *string_items(row.get("watch_symbols")),
            *output_sink_ids(dict_items(row.get("outputs"))),
            *[str(patch.get("symbol", "")) for patch in dict_items(row.get("patches")) if patch.get("symbol")],
        ]
    )
    actual_proof_status = materialization_actual_proof_status(row)
    observed_sinks = string_items(row.get("observed_sinks"))
    route.update(
        {
            "actual_proof_status": actual_proof_status,
            "expected_sinks": expected_sinks,
            "observed_sinks": observed_sinks,
        }
    )
    row[EVENT_RUNTIME_ROUTE_KEY] = route
    row[EVENT_RUNTIME_ROUTE_LEGACY_KEY] = route
    row["actual_proof_status"] = actual_proof_status
    row["expected_proof_status"] = str(route.get("expected_proof_status") or "runtime_observed")
    row["expected_sinks"] = expected_sinks
    row["observed_sinks"] = observed_sinks
    return row


def materialization_actual_proof_status(materialization: dict[str, Any]) -> str:
    if str(materialization.get("actual_proof_status", "")):
        return str(materialization.get("actual_proof_status"))
    if str(materialization.get("status", "")) == "ready":
        return "ready_to_run"
    return "planned_only"


def promote_route_after_execution(
    *,
    materializations: list[dict[str, Any]],
    execution: dict[str, Any],
) -> list[dict[str, Any]]:
    if not execution.get("executed"):
        return materializations
    verified = {
        patch_identity(patch)
        for patch in dict_items(execution.get("applied_patches"))
        if patch.get("verified", True)
    }
    promoted: list[dict[str, Any]] = []
    for materialization in materializations:
        row = dict(materialization)
        patches = dict_items(row.get("patches"))
        if patches and all(patch_identity(patch) in verified for patch in patches):
            observed_sinks = unique_list(
                [
                    *string_items(row.get("observed_sinks")),
                    *[str(patch.get("symbol", "")) for patch in patches if patch.get("symbol")],
                ]
            )
            row["actual_proof_status"] = "state_materialized"
            row["observed_sinks"] = observed_sinks
            route = dict(
                row.get(EVENT_RUNTIME_ROUTE_KEY)
                if isinstance(row.get(EVENT_RUNTIME_ROUTE_KEY), dict)
                else row.get(EVENT_RUNTIME_ROUTE_LEGACY_KEY)
                if isinstance(row.get(EVENT_RUNTIME_ROUTE_LEGACY_KEY), dict)
                else {}
            )
            if route.get("kind") == EVENT_RUNTIME_ROUTE_LEGACY_KEY or not route.get("kind"):
                route["kind"] = EVENT_RUNTIME_ROUTE_KIND
            route["actual_proof_status"] = "state_materialized"
            route["observed_sinks"] = observed_sinks
            row[EVENT_RUNTIME_ROUTE_KEY] = route
            row[EVENT_RUNTIME_ROUTE_LEGACY_KEY] = route
        promoted.append(row)
    return promoted


def patch_identity(patch: dict[str, Any]) -> tuple[str, str, str, str]:
    if patch.get("patch_kind") == "bit":
        return (
            str(patch.get("symbol", "")),
            str(patch.get("bank_address", "")),
            str(patch.get("bit_index", "")),
            str(patch.get("bit_operation", "")),
        )
    return (
        str(patch.get("symbol", "")),
        str(patch.get("bank_address", "")),
        str(patch.get("value_hex", "")),
        str(patch.get("value", "")),
    )


def selected_precondition_kinds(scenarios: list[dict[str, Any]]) -> set[str]:
    return {
        str(precondition.get("kind", ""))
        for scenario in scenarios
        for precondition in dict_items(scenario.get("state_preconditions"))
        if precondition.get("kind")
    }


def map_position_materialization(
    *,
    scenario: dict[str, Any],
    precondition: dict[str, Any],
    scenario_id: str,
    map_index: dict[str, dict[str, Any]],
    scene_var_index: dict[str, dict[str, Any]],
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> dict[str, Any]:
    values = precondition.get("values") if isinstance(precondition.get("values"), dict) else {}
    scenario_type = str(scenario.get("scenario_type", ""))
    map_name = map_name_for_precondition(values=values, scenario=scenario)
    map_entry = map_index.get(map_name, {})
    errors = []
    if not map_name:
        errors.append("could not infer map name from precondition map_label/source_file")
    elif not map_entry:
        errors.append(f"map not found in data/maps/maps.asm: {map_name}")
    player_context = event_engine_player_context(
        scenario_type=scenario_type,
        values=values,
        root=root,
    )
    patch_values = {
        "wMapGroup": int(map_entry.get("map_group", 0)),
        "wMapNumber": int(map_entry.get("map_number", 0)),
        "wXCoord": player_context.get("player_x", parse_int(values.get("x"))),
        "wYCoord": player_context.get("player_y", parse_int(values.get("y"))),
    }
    patches = [
        patch_record(symbol, value, symbol_table=symbol_table, symbols_path=symbols_path, root=root)
        for symbol, value in patch_values.items()
        if value is not None
    ]
    patches.extend(
        optional_patch_record(symbol, value, symbol_table=symbol_table, symbols_path=symbols_path, root=root)
        for symbol, value in {
            "wPlayerMapX": player_context.get("player_map_x"),
            "wPlayerMapY": player_context.get("player_map_y"),
            "wPlayerDirection": player_context.get("facing_direction_value"),
        }.items()
        if value is not None and symbol in symbol_table
    )
    scene_context = map_event_context_patch(
        scenario=scenario,
        values=values,
        map_name=map_name,
        scene_var_index=scene_var_index,
        symbol_table=symbol_table,
        symbols_path=symbols_path,
        root=root,
    )
    bg_context = bg_event_flag_context_patch(
        scenario_type=scenario_type,
        values=values,
        scenario=scenario,
        symbol_table=symbol_table,
        symbols_path=symbols_path,
        root=root,
    )
    object_context = object_event_object_state_patch(
        scenario_type=scenario_type,
        values=values,
        symbol_table=symbol_table,
        symbols_path=symbols_path,
        root=root,
    )
    counter_context = counter_tile_context_patch(
        scenario_type=scenario_type,
        values=values,
        symbol_table=symbol_table,
        symbols_path=symbols_path,
        root=root,
    )
    patches.extend(dict_items(scene_context.get("patch")))
    patches.extend(dict_items(bg_context.get("patch")))
    patches.extend(dict_items(object_context.get("patches")))
    patches.extend(dict_items(counter_context.get("patch")))
    errors.extend(error for patch in patches for error in patch.get("errors", []))
    errors.extend(string_items(scene_context.get("errors")))
    errors.extend(string_items(bg_context.get("errors")))
    errors.extend(string_items(object_context.get("errors")))
    errors.extend(string_items(counter_context.get("errors")))
    proof_blockers = map_position_proof_blockers(
        scenario_type=scenario_type,
        object_context=object_context,
        counter_context=counter_context,
    )
    combined_event_context = combined_map_event_context(
        scene_context=scene_context,
        bg_context=bg_context,
        object_context=object_context,
        counter_context=counter_context,
        player_context=player_context,
    )
    watch_symbols = unique_list(
        [
            *MAP_PATCH_SYMBOLS,
            *[
                symbol
                for symbol in EVENT_ENGINE_POSITION_SYMBOLS
                if symbol in symbol_table and player_context.get(event_engine_position_value_key(symbol)) is not None
            ],
            *[
                str(patch.get("base_symbol") or patch.get("symbol") or "")
                for patch in dict_items(scene_context.get("patch"))
                if patch.get("base_symbol") or patch.get("symbol")
            ],
            *[
                str(patch.get("base_symbol") or patch.get("symbol") or "")
                for patch in dict_items(bg_context.get("patch"))
                if patch.get("base_symbol") or patch.get("symbol")
            ],
            *[
                str(patch.get("base_symbol") or patch.get("symbol") or "")
                for patch in dict_items(counter_context.get("patch"))
                if patch.get("base_symbol") or patch.get("symbol")
            ],
            *[
                symbol
                for symbol in object_event_watch_symbols(object_context)
                if symbol in symbol_table and object_context.get("status") == "ready"
            ],
        ]
    )
    return {
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "precondition_id": str(precondition.get("id", "")),
        "precondition_kind": "map_position",
        "status": "ready" if not errors and patches and not proof_blockers else "blocked",
        "source_file": normalize_path(str(scenario.get("source_file") or values.get("source_file") or "")),
        "map_name": map_name,
        "map_resolution": map_entry,
        "event_context": combined_event_context,
        "player_context": player_context,
        "object_context": object_context,
        "counter_tile_context": counter_context,
        "values": dict(values),
        "patch_count": len(patches),
        "patches": patches,
        "watch_symbols": watch_symbols,
        "proof_blockers": proof_blockers,
        "errors": errors,
        "commands": [
            f"python -m tools.debugger watch --watch-symbol {symbol} --execute --save-state <patched-state>"
            for symbol in watch_symbols
        ],
        "known_limits": map_position_known_limits(scenario_type=scenario_type),
    }


def event_engine_player_context(*, scenario_type: str, values: dict[str, Any], root: Path) -> dict[str, Any]:
    target_x = parse_int(values.get("x"))
    target_y = parse_int(values.get("y"))
    if target_x is None or target_y is None:
        return {}
    player_x = target_x
    player_y = target_y
    facing_direction = ""
    if scenario_type == "map_bg_event":
        player_x, player_y, facing_direction = bg_event_player_position(
            target_x=target_x,
            target_y=target_y,
            event_type=str(values.get("event_type", "")),
        )
    facing_choice_source = ""
    if scenario_type == "map_object_event":
        if bool_value(values.get("counter_tile")):
            facing_direction = counter_tile_facing_direction(values)
            player_x, player_y = counter_tile_object_player_position(
                target_x=target_x,
                target_y=target_y,
                facing_direction=facing_direction,
            )
            facing_choice_source = "counter_tile_object_path"
        elif object_event_is_large(values=values, root=root):
            facing_direction = str(values.get("large_object_facing_direction") or "OW_UP").strip()
            if facing_direction not in OW_DIRECTION_VALUES:
                facing_direction = "OW_UP"
            surface_x = parse_int(values.get("large_object_surface_x"))
            surface_y = parse_int(values.get("large_object_surface_y"))
            if surface_x is None:
                surface_x = 0
            if surface_y is None:
                surface_y = 1
            player_x, player_y = large_object_player_position(
                target_x=target_x,
                target_y=target_y,
                surface_x=surface_x,
                surface_y=surface_y,
                facing_direction=facing_direction,
            )
            facing_choice_source = large_object_facing_choice_source(surface_x=surface_x, surface_y=surface_y, facing_direction=facing_direction)
        else:
            player_x, player_y, facing_direction = object_event_player_position(
                target_x=target_x,
                target_y=target_y,
            )
            facing_choice_source = "default_adjacent_object_tile"
    context = {
        "kind": "event_engine_player_context",
        "target_x": target_x,
        "target_y": target_y,
        "player_x": player_x,
        "player_y": player_y,
        "player_map_x": player_x + 4,
        "player_map_y": player_y + 4,
        "validation_kind": "event_engine_player_position_and_facing",
        "proof_status": "state_patch_planned",
    }
    if facing_direction:
        context["facing_direction"] = facing_direction
        context["facing_direction_value"] = OW_DIRECTION_VALUES[facing_direction]
    if facing_choice_source:
        context["facing_choice_source"] = facing_choice_source
    if scenario_type == "map_object_event" and object_event_is_large(values=values, root=root):
        context["large_object"] = True
        context["large_object_width"] = 2
        context["large_object_height"] = 2
        context["large_object_collision_model"] = str(values.get("large_object_collision_model") or LARGE_OBJECT_COLLISION_MODEL)
        context["large_object_size_source"] = str(values.get("large_object_size_source") or LARGE_OBJECT_SIZE_SOURCE)
    return context


def bg_event_player_position(*, target_x: int, target_y: int, event_type: str) -> tuple[int, int, str]:
    if event_type == "BGEVENT_DOWN":
        return target_x, target_y - 1, "OW_DOWN"
    if event_type == "BGEVENT_RIGHT":
        return target_x - 1, target_y, "OW_RIGHT"
    if event_type == "BGEVENT_LEFT":
        return target_x + 1, target_y, "OW_LEFT"
    return target_x, target_y + 1, "OW_UP"


def object_event_player_position(*, target_x: int, target_y: int) -> tuple[int, int, str]:
    return target_x, target_y + 1, "OW_UP"


def object_event_is_large(*, values: dict[str, Any], root: Path) -> bool:
    if bool_value(values.get("large_object")):
        return True
    constants = load_object_event_constants(root=root)
    movement = str(values.get("movement") or "").strip()
    attrs = sprite_movement_attributes_for_movement(movement, root=root, constants=constants)
    return bool(attrs.get("large_object"))


def object_event_viewport_visibility(
    *,
    object_x: int | None,
    object_y: int | None,
    player_x: int | None,
    player_y: int | None,
    constants: dict[str, int],
) -> dict[str, Any]:
    screen_width = int(constants.get("MAPOBJECT_SCREEN_WIDTH", 12) or 12)
    screen_height = int(constants.get("MAPOBJECT_SCREEN_HEIGHT", 11) or 11)
    context: dict[str, Any] = {
        "kind": "object_event_viewport_visibility",
        "visibility_model": "InitializeVisibleSprites_player_viewport",
        "screen_width": screen_width,
        "screen_height": screen_height,
        "object_x": object_x,
        "object_y": object_y,
        "player_x": player_x,
        "player_y": player_y,
        "proof_status": "state_patch_planned",
    }
    if None in {object_x, object_y, player_x, player_y}:
        return {**context, "visible": False, "visibility_reason": "unresolved_player_or_object_coordinates"}
    delta_x = int(object_x or 0) + 1 - int(player_x or 0)
    delta_y = int(object_y or 0) + 1 - int(player_y or 0)
    visible = 0 <= delta_x < screen_width and 0 <= delta_y < screen_height
    return {
        **context,
        "visible": visible,
        "viewport_delta_x": delta_x,
        "viewport_delta_y": delta_y,
        "visibility_reason": "inside_player_viewport" if visible else "outside_player_viewport",
    }


def large_object_player_position(
    *,
    target_x: int,
    target_y: int,
    surface_x: int,
    surface_y: int,
    facing_direction: str,
) -> tuple[int, int]:
    event_x = target_x + max(0, min(1, surface_x))
    event_y = target_y + max(0, min(1, surface_y))
    if facing_direction == "OW_DOWN":
        return event_x, event_y - 1
    if facing_direction == "OW_LEFT":
        return event_x + 1, event_y
    if facing_direction == "OW_RIGHT":
        return event_x - 1, event_y
    return event_x, event_y + 1


def large_object_facing_choice_source(*, surface_x: int, surface_y: int, facing_direction: str) -> str:
    vertical = "top" if surface_y <= 0 else "bottom"
    horizontal = "left" if surface_x <= 0 else "right"
    if facing_direction == "OW_DOWN":
        return f"large_object_top_{horizontal}_tile"
    if facing_direction == "OW_LEFT":
        return f"large_object_right_{vertical}_tile"
    if facing_direction == "OW_RIGHT":
        return f"large_object_left_{vertical}_tile"
    return f"large_object_bottom_{horizontal}_tile"


def counter_tile_facing_direction(values: dict[str, Any]) -> str:
    direction = str(values.get("counter_facing_direction") or "OW_UP").strip()
    if direction in OW_DIRECTION_VALUES:
        return direction
    return "OW_UP"


def counter_tile_object_player_position(*, target_x: int, target_y: int, facing_direction: str) -> tuple[int, int]:
    if facing_direction == "OW_DOWN":
        return target_x, target_y - 2
    if facing_direction == "OW_LEFT":
        return target_x + 2, target_y
    if facing_direction == "OW_RIGHT":
        return target_x - 2, target_y
    return target_x, target_y + 2


def bool_value(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return False


def map_position_proof_blockers(
    *,
    scenario_type: str,
    object_context: dict[str, Any],
    counter_context: dict[str, Any],
) -> list[str]:
    if scenario_type == "map_object_event":
        blockers: list[str] = []
        if object_context.get("status") != "ready":
            blockers.extend(string_items(object_context.get("proof_blockers")) or ["object_struct_not_materialized"])
        if counter_context and counter_context.get("status") != "ready":
            blockers.extend(string_items(counter_context.get("proof_blockers")) or ["counter_tile_not_materialized"])
        return unique_list(blockers)
    return []


def map_position_known_limits(*, scenario_type: str) -> list[str]:
    limits = [
        "Map-position patches install selected map/player coordinate state; replay/watch/trace must still prove the event engine consumes that state.",
    ]
    if scenario_type == "map_bg_event":
        limits.append(
            "BG event flag patches preserve the requested set/reset bit operation for wEventFlags but do not prove CheckBGEventFlag executed without replay/watch/trace evidence.",
        )
    if scenario_type == "map_object_event":
        limits.append(
            "Object events require a live object struct discoverable by IsNPCAtCoord; this materialization patches one generated visible object and still requires runtime proof that TryObjectEvent consumes it.",
        )
        limits.append(
            "Multi-object map-event materialization patches the selected source object's wMapNObject row and source-order companion map rows; object mask/event-flag and generated runtime-hour time-context filters are still planned state, while runtime occupancy and CheckObjectTime consumption still need replay/watch/trace evidence.",
        )
        limits.append(
            "Companion object materialization filters object structs through the InitializeVisibleSprites player-viewport model, but replay/watch/trace must still prove the runtime object-loader chose the same loaded set and object struct indexes.",
        )
        limits.append(
            "Large-object object-event variants patch the object struct BIG_OBJECT palette bit and player positions outside the engine-fixed 2x2 footprint; replay/watch/trace must still prove IsNPCAtCoord used the WillObjectIntersectBigObject path.",
        )
        limits.append(
            "Counter-tile object-event variants patch one cached facing-tile collision byte and require replay/watch/trace proof that CheckCounterTile reflected the target coordinates.",
        )
    return limits


def combined_map_event_context(
    *,
    scene_context: dict[str, Any],
    bg_context: dict[str, Any],
    object_context: dict[str, Any],
    counter_context: dict[str, Any],
    player_context: dict[str, Any],
) -> dict[str, Any]:
    if object_context:
        context = {**player_context, **object_context, "player_context": player_context}
        if counter_context:
            context.update(counter_tile_event_context_fields(counter_context))
            context["counter_tile_context"] = counter_context
        return context
    if bg_context:
        return {**player_context, **bg_context, "player_context": player_context}
    if scene_context:
        return scene_context
    return player_context


def counter_tile_event_context_fields(counter_context: dict[str, Any]) -> dict[str, Any]:
    return {
        key: counter_context[key]
        for key in (
            "counter_tile",
            "counter_tile_symbol",
            "counter_tile_collision",
            "counter_tile_value",
            "counter_tile_value_hex",
            "counter_facing_direction",
        )
        if key in counter_context
    }


def counter_tile_context_patch(
    *,
    scenario_type: str,
    values: dict[str, Any],
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> dict[str, Any]:
    if scenario_type != "map_object_event" or not bool_value(values.get("counter_tile")):
        return {}
    facing_direction = counter_tile_facing_direction(values)
    tile_symbol = str(values.get("counter_tile_symbol") or COUNTER_TILE_SYMBOLS_BY_FACING[facing_direction]).strip()
    collision_token = str(values.get("counter_tile_collision") or "COLL_COUNTER").strip()
    constants = load_object_event_constants(root=root)
    collision_value = constant_or_int(collision_token, constants)
    missing_symbols = [tile_symbol] if tile_symbol not in symbol_table else []
    context: dict[str, Any] = {
        "kind": "object_event_counter_tile_context",
        "counter_tile": True,
        "counter_tile_symbol": tile_symbol,
        "counter_tile_collision": collision_token,
        "counter_facing_direction": facing_direction,
        "validation_kind": "object_event_counter_tile_collision_state",
        "proof_status": "state_patch_planned",
    }
    unresolved_values = []
    if collision_value is None:
        unresolved_values.append("counter_tile_collision")
    if missing_symbols or unresolved_values:
        return {
            **context,
            "status": "blocked",
            "proof_blockers": ["counter_tile_collision_not_materialized"],
            "missing_symbols": missing_symbols,
            "unresolved_values": unresolved_values,
            "errors": [],
        }
    patch = patch_record(tile_symbol, collision_value, symbol_table=symbol_table, symbols_path=symbols_path, root=root)
    return {
        **context,
        "status": "ready",
        "counter_tile_value": int(collision_value) & 0xFF,
        "counter_tile_value_hex": f"{int(collision_value) & 0xFF:02X}",
        "patch": patch,
        "proof_blockers": [],
        "errors": [],
        "known_limits": [
            "This patches the cached facing-tile collision byte used by GetFacingTileCoord; replay/watch/trace must prove CheckCounterTile consumed it.",
        ],
    }


def bg_event_flag_context_patch(
    *,
    scenario_type: str,
    values: dict[str, Any],
    scenario: dict[str, Any],
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> dict[str, Any]:
    if scenario_type != "map_bg_event":
        return {}
    event_type = str(values.get("event_type") or "").strip()
    if event_type not in {"BGEVENT_IFSET", "BGEVENT_IFNOTSET", "BGEVENT_ITEM", "BGEVENT_COPY"}:
        return {}
    script_label = str(values.get("script") or "").strip()
    macro = bg_event_payload_for_label(
        script_label,
        source_file=normalize_path(str(scenario.get("source_file") or values.get("source_file") or "")),
        root=root,
    )
    context: dict[str, Any] = {
        "kind": "bg_event_flag_context",
        "event_type": event_type,
        "script_label": script_label,
        "validation_kind": "source_bg_event_flag_macro_and_event_flags",
        "proof_status": "state_patch_planned",
    }
    if not macro:
        context["errors"] = [f"BG event payload macro not found for label: {script_label}"]
        return context
    constants = load_object_event_constants(root=root)
    event_flag_token = str(macro.get("event_flag") or "")
    event_flag = constant_or_int(event_flag_token, constants)
    if event_flag is None:
        return {**context, **macro, "errors": [f"event flag constant not resolved: {event_flag_token}"]}
    required_state = "set" if event_type == "BGEVENT_IFSET" else "reset"
    hidden_item_value = (
        constant_or_int(macro.get("hidden_item_token"), constants)
        if macro.get("hidden_item_token") else None
    )
    patch = event_flag_patch_record(
        event_flag,
        required_state=required_state,
        symbol_table=symbol_table,
        symbols_path=symbols_path,
        root=root,
    )
    return {
        **context,
        **macro,
        "event_flag_token": event_flag_token,
        "event_flag_value": event_flag,
        "event_flag_byte_offset": event_flag // 8,
        "event_flag_bit_index": event_flag & 7,
        "event_flag_bit_mask": 1 << (event_flag & 7),
        "required_flag_state": required_state,
        "hidden_item_value": hidden_item_value if hidden_item_value is not None else "",
        "patch": patch,
        "errors": [],
    }


def bg_event_payload_for_label(script_label: str, *, source_file: str, root: Path) -> dict[str, Any]:
    if not script_label or not source_file:
        return {}
    source_path = resolve_path(source_file, root=root)
    if not source_path.exists():
        return {}
    lines = source_path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_label = False
    for line_no, raw in enumerate(lines, 1):
        clean = strip_comment(raw).strip()
        if not clean:
            continue
        label_match = re.match(r"^(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*):", clean)
        if label_match:
            label = label_match.group("label")
            if in_label and not label.startswith("."):
                return {}
            in_label = label == script_label
            clean = clean[label_match.end():].strip()
            if not clean:
                continue
        if not in_label:
            continue
        hidden = re.match(r"^hiddenitem\s+(?P<item>[^,\s]+)\s*,\s*(?P<flag>[^,\s]+)", clean)
        if hidden:
            return {
                "payload_macro": "hiddenitem",
                "hidden_item_token": hidden.group("item"),
                "event_flag": hidden.group("flag"),
                "payload_source_file": source_file,
                "payload_source_line": line_no,
            }
        conditional = re.match(r"^conditional_event\s+(?P<flag>[^,\s]+)\s*,\s*(?P<script>[^,\s]+)", clean)
        if conditional:
            return {
                "payload_macro": "conditional_event",
                "conditional_script": conditional.group("script"),
                "event_flag": conditional.group("flag"),
                "payload_source_file": source_file,
                "payload_source_line": line_no,
            }
    return {}


def map_object_index_for_values(values: dict[str, Any]) -> int:
    index = parse_int(values.get("map_object_index"))
    if index is None:
        ordinal = parse_int(values.get("source_object_ordinal"))
        index = (ordinal + 2) if ordinal is not None else MAP_OBJECT_INDEX
    return max(2, min(MAX_MAP_OBJECT_INDEX, int(index)))


def object_struct_index_for_map_object_index(map_object_index: int) -> int:
    return max(1, min(MAX_OBJECT_STRUCT_INDEX, int(map_object_index) - 1))


def object_struct_symbol_for_index(object_struct_index: int) -> str:
    return f"wObject{int(object_struct_index)}Struct"


def map_object_symbol_prefix(map_object_index: int) -> str:
    return f"wMap{int(map_object_index)}Object"


def map_object_field_symbol(map_object_index: int, suffix: str) -> str:
    return f"{map_object_symbol_prefix(map_object_index)}{suffix}"


def map_object_field_symbols(map_object_index: int) -> tuple[str, ...]:
    return tuple(map_object_field_symbol(map_object_index, suffix) for suffix in MAP_OBJECT_FIELD_SUFFIXES)


def object_event_watch_symbols(object_context: dict[str, Any]) -> list[str]:
    if not object_context:
        return list(OBJECT_EVENT_WATCH_SYMBOLS)
    return string_items(object_context.get("watch_symbols")) or object_event_watch_symbols_for_index(
        parse_int(object_context.get("map_object_index")) or MAP_OBJECT_INDEX
    )


def object_event_watch_symbols_for_index(map_object_index: int, *, object_struct_index: int | None = None) -> list[str]:
    struct_symbol = object_struct_symbol_for_index(object_struct_index or object_struct_index_for_map_object_index(map_object_index))
    return [
        struct_symbol,
        *map_object_row_watch_symbols_for_index(map_object_index),
    ]


def map_object_row_watch_symbols_for_index(map_object_index: int) -> list[str]:
    return [
        map_object_field_symbol(map_object_index, "StructID"),
        map_object_field_symbol(map_object_index, "Sprite"),
        map_object_field_symbol(map_object_index, "XCoord"),
        map_object_field_symbol(map_object_index, "YCoord"),
        map_object_field_symbol(map_object_index, "Script"),
        map_object_field_symbol(map_object_index, "EventFlag"),
    ]


def companion_objects_context_patch(
    *,
    values: dict[str, Any],
    selected_map_object_index: int,
    selected_time_context: dict[str, Any],
    constants: dict[str, int],
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
    player_x: int | None,
    player_y: int | None,
) -> dict[str, Any]:
    source_file = normalize_path(str(values.get("source_file") or ""))
    source_events = source_object_events_for_file(source_file=source_file, root=root)
    if not source_events:
        return {
            "kind": "object_event_companion_context",
            "status": "not_applicable",
            "companion_object_count": 0,
            "patches": [],
            "watch_symbols": [],
        }
    companions = [event for event in source_events if int(event.get("map_object_index", 0)) != selected_map_object_index]
    patches: list[dict[str, Any]] = []
    missing_symbols: list[str] = []
    unresolved_values: list[str] = []
    watch_symbols: list[str] = []
    companion_records: list[dict[str, Any]] = []
    offscreen_records: list[dict[str, Any]] = []
    time_filtered_records: list[dict[str, Any]] = []
    selected_object_found = False
    selected_object_struct_index: int | None = None
    selected_visibility: dict[str, Any] = {}
    next_object_struct_index = 1
    for event in source_events:
        map_object_index = int(event["map_object_index"])
        object_x = parse_int(event.get("x"))
        object_y = parse_int(event.get("y"))
        visibility = object_event_viewport_visibility(
            object_x=(object_x + 4) if object_x is not None else None,
            object_y=(object_y + 4) if object_y is not None else None,
            player_x=player_x,
            player_y=player_y,
            constants=constants,
        )
        script_label = str(event.get("script") or "")
        script_symbol = symbol_table.get(script_label)
        entry_values, entry_unresolved = object_event_entry_values(event, constants=constants, script_symbol=script_symbol)
        time_visibility = (
            object_event_time_visibility(
                entry_values=entry_values,
                selected_time_context=selected_time_context,
                constants=constants,
                symbol_table=symbol_table,
            )
            if not entry_unresolved
            else {"visible": True, "time_filter_reason": "unresolved_entry_values"}
        )
        visible = bool(visibility.get("visible")) and bool(time_visibility.get("visible"))
        if visible:
            object_struct_index = next_object_struct_index
            next_object_struct_index += 1
        else:
            object_struct_index = 0
        if map_object_index == selected_map_object_index:
            selected_object_found = True
            selected_object_struct_index = object_struct_index if visible else None
            selected_visibility = {**visibility, "time_visibility": time_visibility}
            continue
        required_symbols = list(map_object_field_symbols(map_object_index))
        object_struct_symbol = object_struct_symbol_for_index(object_struct_index) if visible else ""
        if visible:
            if object_struct_index > MAX_OBJECT_STRUCT_INDEX:
                unresolved_values.append(f"object_struct_index:{object_struct_index}")
                continue
            required_symbols.insert(0, object_struct_symbol)
        missing_symbols.extend(symbol for symbol in required_symbols if symbol not in symbol_table)
        if entry_unresolved:
            unresolved_values.extend(f"{script_label or map_object_index}:{name}" for name in entry_unresolved)
        if any(symbol not in symbol_table for symbol in required_symbols) or entry_unresolved:
            continue
        if visible:
            patches.extend(
                object_event_entry_patch_records(
                    entry_values=entry_values,
                    object_struct_symbol=object_struct_symbol,
                    object_struct_index=object_struct_index,
                    map_object_index=map_object_index,
                    symbol_table=symbol_table,
                    symbols_path=symbols_path,
                    root=root,
                )
            )
            watch_symbols.extend(object_event_watch_symbols_for_index(map_object_index, object_struct_index=object_struct_index))
            companion_records.append(
                {
                    "source_object_ordinal": event.get("source_object_ordinal", ""),
                    "map_object_index": map_object_index,
                    "object_struct_index": object_struct_index,
                    "object_struct_symbol": object_struct_symbol,
                    "script_label": script_label,
                    "object_x": entry_values["object_x"],
                    "object_y": entry_values["object_y"],
                    "visibility_reason": visibility.get("visibility_reason", ""),
                    "object_mask_context": object_event_object_mask_context(
                        entry_values=entry_values,
                        map_object_index=map_object_index,
                        symbol_table=symbol_table,
                    ),
                }
            )
            continue
        patches.extend(
            map_object_row_patch_records(
                entry_values=entry_values,
                map_object_index=map_object_index,
                map_object_struct_id=0xFF,
                symbol_table=symbol_table,
                symbols_path=symbols_path,
                root=root,
            )
        )
        time_filtered = bool(visibility.get("visible")) and not bool(time_visibility.get("visible"))
        patches.extend(
            object_event_object_mask_patch_records(
                entry_values=entry_values,
                map_object_index=map_object_index,
                object_mask_value=0xFF if time_filtered else 0,
                symbol_table=symbol_table,
                symbols_path=symbols_path,
                root=root,
            )
        )
        watch_symbols.extend(map_object_row_watch_symbols_for_index(map_object_index))
        if "wObjectMasks" in symbol_table:
            watch_symbols.append("wObjectMasks")
        if int(entry_values["event_flag"]) >= 0 and "wEventFlags" in symbol_table:
            watch_symbols.append("wEventFlags")
        record = {
            "source_object_ordinal": event.get("source_object_ordinal", ""),
            "map_object_index": map_object_index,
            "script_label": script_label,
            "object_x": entry_values["object_x"],
            "object_y": entry_values["object_y"],
            "object_mask_context": object_event_object_mask_context(
                entry_values=entry_values,
                map_object_index=map_object_index,
                symbol_table=symbol_table,
                object_mask_value=0xFF if time_filtered else 0,
            ),
        }
        if time_filtered:
            time_filtered_records.append(
                {
                    **record,
                    "visibility_reason": visibility.get("visibility_reason", ""),
                    "time_filter_reason": time_visibility.get("time_filter_reason", ""),
                    "object_time_context": time_visibility.get("object_time_context", {}),
                    "selected_time_context": selected_time_context,
                }
            )
        else:
            offscreen_records.append(
                {
                    **record,
                    "visibility_reason": visibility.get("visibility_reason", ""),
                    "viewport_delta_x": visibility.get("viewport_delta_x"),
                    "viewport_delta_y": visibility.get("viewport_delta_y"),
                }
            )
    missing_symbols = unique_list(missing_symbols)
    unresolved_values = unique_list(unresolved_values)
    return {
        "kind": "object_event_companion_context",
        "status": "ready" if not missing_symbols and not unresolved_values else "blocked",
        "validation_kind": "source_order_visible_object_occupancy_state",
        "proof_status": "state_patch_planned",
        "source_file": source_file,
        "source_object_count": len(source_events),
        "companion_object_count": len(companion_records),
        "companion_objects": companion_records,
        "offscreen_object_count": len(offscreen_records),
        "offscreen_objects": offscreen_records,
        "time_filtered_object_count": len(time_filtered_records),
        "time_filtered_objects": time_filtered_records,
        "map_row_object_count": len(companion_records) + len(offscreen_records) + len(time_filtered_records),
        "selected_object_found": selected_object_found,
        "selected_object_struct_index": selected_object_struct_index,
        "selected_visibility": selected_visibility,
        "loaded_object_count": (1 if selected_object_struct_index else 0) + len(companion_records),
        "occupancy_model": "source_order_viewport_visible_candidate",
        "visibility_model": "InitializeVisibleSprites_player_viewport",
        "patches": patches,
        "watch_symbols": unique_list(watch_symbols),
        "missing_symbols": missing_symbols,
        "unresolved_values": unresolved_values,
        "known_limits": [
            "This patches source-order visible object candidates; replay/watch/trace must prove which objects were actually loaded and collided at runtime.",
        ],
    }


def object_event_entry_values(
    values: dict[str, Any],
    *,
    constants: dict[str, int],
    script_symbol: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    target_x = parse_int(values.get("x"))
    target_y = parse_int(values.get("y"))
    unresolved: list[str] = []
    resolved = {
        "sprite": constant_or_int(values.get("sprite"), constants),
        "movement": constant_or_int(values.get("movement"), constants),
        "object_type": constant_or_int(values.get("object_type"), constants),
        "radius_x": constant_or_int(values.get("radius_x"), constants) if values.get("radius_x") not in {"", None} else 0,
        "radius_y": constant_or_int(values.get("radius_y"), constants) if values.get("radius_y") not in {"", None} else 0,
        "hour_1": constant_or_int(values.get("hour_1"), constants) if values.get("hour_1") not in {"", None} else -1,
        "hour_2": constant_or_int(values.get("hour_2"), constants) if values.get("hour_2") not in {"", None} else -1,
        "palette": constant_or_int(values.get("palette"), constants) if values.get("palette") not in {"", None} else 0,
        "sight_range": constant_or_int(values.get("sight_range"), constants) if values.get("sight_range") not in {"", None} else 0,
        "event_flag": constant_or_int(values.get("event_flag"), constants) if values.get("event_flag") not in {"", None} else -1,
    }
    for key, value in resolved.items():
        if value is None:
            unresolved.append(key)
    if target_x is None or target_y is None:
        unresolved.append("x/y")
    if script_symbol is None:
        unresolved.append("script")
    if unresolved:
        return {}, unresolved
    object_x = int(target_x or 0) + 4
    object_y = int(target_y or 0) + 4
    radius = ((int(resolved["radius_y"] or 0) & 0x0F) << 4) | (int(resolved["radius_x"] or 0) & 0x0F)
    return {
        "object_x": object_x,
        "object_y": object_y,
        "sprite": int(resolved["sprite"] or 0),
        "movement": int(resolved["movement"] or 0),
        "object_type": int(resolved["object_type"] or 0) & 0x0F,
        "palette": int(resolved["palette"] or 0) & 0x0F,
        "radius": radius,
        "hour_1": int(resolved["hour_1"]),
        "hour_2": int(resolved["hour_2"]),
        "sight_range": int(resolved["sight_range"] or 0),
        "event_flag": int(resolved["event_flag"]),
        "script_address": int(script_symbol.get("address", 0)) if script_symbol else 0,
        "script_bank": int(script_symbol.get("bank", 0)) if script_symbol else 0,
    }, []


def object_event_entry_patch_records(
    *,
    entry_values: dict[str, Any],
    object_struct_symbol: str,
    object_struct_index: int,
    map_object_index: int,
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> list[dict[str, Any]]:
    return [
        *object_struct_patch_records(
            object_struct_symbol=object_struct_symbol,
            object_x=int(entry_values["object_x"]),
            object_y=int(entry_values["object_y"]),
            sprite=int(entry_values["sprite"]),
            map_object_index=map_object_index,
            movement=int(entry_values["movement"]),
            object_direction=OW_DIRECTION_VALUES["OW_DOWN"],
            object_flags1=0,
            object_flags2=0,
            object_palette_flags=0,
            radius=int(entry_values["radius"]),
            sight_range=int(entry_values["sight_range"]),
            symbol_table=symbol_table,
            symbols_path=symbols_path,
            root=root,
        ),
        *object_event_object_mask_patch_records(
            entry_values=entry_values,
            map_object_index=map_object_index,
            symbol_table=symbol_table,
            symbols_path=symbols_path,
            root=root,
        ),
        *map_object_row_patch_records(
            entry_values=entry_values,
            map_object_index=map_object_index,
            map_object_struct_id=object_struct_index,
            symbol_table=symbol_table,
            symbols_path=symbols_path,
            root=root,
        ),
    ]


def object_event_object_mask_context(
    *,
    entry_values: dict[str, Any],
    map_object_index: int,
    symbol_table: dict[str, dict[str, Any]],
    object_mask_value: int = 0,
) -> dict[str, Any]:
    event_flag = int(entry_values["event_flag"])
    context = {
        "kind": "object_event_object_mask_context",
        "validation_kind": "object_mask_event_flag_state",
        "proof_status": "state_patch_planned",
        "map_object_index": map_object_index,
        "object_mask_symbol": f"wObjectMasks+{map_object_index}",
        "object_mask_value": int(object_mask_value) & 0xFF,
        "object_mask_required_state": "masked" if (int(object_mask_value) & 0xFF) else "unmasked",
        "object_masks_symbol_available": "wObjectMasks" in symbol_table,
        "event_flag": event_flag,
        "event_flag_required_state": "reset" if event_flag >= 0 else "not_applicable",
        "event_flag_symbol_available": event_flag < 0 or "wEventFlags" in symbol_table,
    }
    if event_flag >= 0:
        context["event_flag_byte_offset"] = event_flag // 8
        context["event_flag_bit_index"] = event_flag & 7
        context["event_flag_bit_mask"] = 1 << (event_flag & 7)
    return context


def object_event_object_mask_patch_records(
    *,
    entry_values: dict[str, Any],
    map_object_index: int,
    object_mask_value: int = 0,
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> list[dict[str, Any]]:
    patches: list[dict[str, Any]] = []
    if "wObjectMasks" in symbol_table:
        patches.append(
            patch_record(
                "wObjectMasks",
                int(object_mask_value) & 0xFF,
                symbol_table=symbol_table,
                symbols_path=symbols_path,
                root=root,
                address_offset=map_object_index,
                display_symbol=f"wObjectMasks+{map_object_index}",
            )
        )
    event_flag = int(entry_values["event_flag"])
    if event_flag >= 0 and "wEventFlags" in symbol_table:
        patches.append(
            event_flag_patch_record(
                event_flag,
                required_state="reset",
                symbol_table=symbol_table,
                symbols_path=symbols_path,
                root=root,
            )
        )
    return patches


def object_event_time_context(
    *,
    entry_values: dict[str, Any],
    symbol_table: dict[str, dict[str, Any]],
    constants: dict[str, int],
    requested_time_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    requested_time_context = requested_time_context or {}
    hour_1 = int(entry_values["hour_1"])
    hour_2 = int(entry_values["hour_2"])
    context = {
        "kind": "object_event_time_context",
        "validation_kind": "object_time_filter_state",
        "proof_status": "state_patch_planned",
        "hour_start": hour_1,
        "hour_end": hour_2,
    }
    if hour_1 < 0:
        if hour_2 >= 0:
            mask = hour_2 & 0xFF
            choices = timeofday_mask_choices(mask, constants)
            if not choices:
                return {
                    **context,
                    "time_model": "timeofday_mask_unresolved",
                    "timeofday_mask": mask,
                    "timeofday_choices": [],
                    "required_symbol": TIMEOFDAY_SYMBOL,
                    "required_symbols": [TIMEOFDAY_SYMBOL],
                    "time_symbol_available": TIMEOFDAY_SYMBOL in symbol_table,
                    "hour_symbol_available": HOURS_SYMBOL in symbol_table,
                }
            requested_choice = requested_timeofday_choice(choices, requested_time_context, constants=constants)
            if requested_timeofday_context_present(requested_time_context) and requested_choice is None:
                return {
                    **context,
                    "time_model": "timeofday_mask_unavailable",
                    "timeofday_mask": mask,
                    "timeofday_choices": choices,
                    "requested_timeofday": str(requested_time_context.get("selected_timeofday") or ""),
                    "requested_timeofday_value": parse_int(requested_time_context.get("selected_timeofday_value")),
                    "requested_hour": requested_hour_context_value(requested_time_context, constants=constants),
                    "selected_time_context_source": str(requested_time_context.get("selected_time_context_source") or "requested_time_context"),
                    "time_selection_valid": False,
                    "time_selection_error": "selected_time_context_not_allowed_by_object_mask",
                    "required_symbol": TIMEOFDAY_SYMBOL,
                    "required_symbols": [TIMEOFDAY_SYMBOL],
                    "time_symbol_available": TIMEOFDAY_SYMBOL in symbol_table,
                    "hour_symbol_available": HOURS_SYMBOL in symbol_table,
                }
            selected = requested_choice or choices[0]
            required_symbols = [TIMEOFDAY_SYMBOL]
            if "required_hour" in selected:
                required_symbols.append(HOURS_SYMBOL)
            return {
                **context,
                "time_model": "timeofday_mask",
                "timeofday_mask": mask,
                "timeofday_choices": choices,
                "required_symbol": TIMEOFDAY_SYMBOL,
                "required_symbols": required_symbols,
                "required_timeofday": selected["name"],
                "required_timeofday_value": selected["value"],
                "required_timeofday_mask": selected["mask"],
                **({"required_hour": selected["required_hour"]} if "required_hour" in selected else {}),
                "selected_time_context_source": str(
                    requested_time_context.get("selected_time_context_source")
                    or ("requested_timeofday" if requested_choice else "default_first_timeofday_choice")
                ),
                "time_selection_valid": True,
                "time_symbol_available": TIMEOFDAY_SYMBOL in symbol_table,
                "hour_symbol_available": HOURS_SYMBOL in symbol_table,
            }
        return {
            **context,
            "time_model": "always",
            "time_symbol_available": False,
        }
    requested_hour = requested_hour_context_value(requested_time_context, constants=constants)
    if requested_hour is not None and not hour_in_object_range(hour=int(requested_hour), start=hour_1, end=hour_2):
        return {
            **context,
            "time_model": "hour_range_unavailable",
            "required_symbol": HOURS_SYMBOL,
            "required_symbols": [HOURS_SYMBOL],
            "requested_hour": int(requested_hour) & 0xFF,
            "selected_time_context_source": str(requested_time_context.get("selected_time_context_source") or "requested_time_context"),
            "time_selection_valid": False,
            "time_selection_error": "selected_hour_not_allowed_by_object_range",
            "time_symbol_available": HOURS_SYMBOL in symbol_table,
        }
    required_hour = int(requested_hour) & 0xFF if requested_hour is not None else hour_1 & 0xFF
    return {
        **context,
        "time_model": "hour_range",
        "required_symbol": HOURS_SYMBOL,
        "required_symbols": [HOURS_SYMBOL],
        "required_hour": required_hour,
        "selected_time_context_source": str(
            requested_time_context.get("selected_time_context_source")
            or ("requested_hour" if requested_hour is not None else "default_hour_range_start")
        ),
        "time_selection_valid": True,
        "time_symbol_available": HOURS_SYMBOL in symbol_table,
    }


def object_event_time_visibility(
    *,
    entry_values: dict[str, Any],
    selected_time_context: dict[str, Any],
    constants: dict[str, int],
    symbol_table: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    object_time = object_event_time_context(entry_values=entry_values, symbol_table=symbol_table, constants=constants)
    time_model = object_time.get("time_model")
    if time_model not in {"hour_range", "timeofday_mask"}:
        return {
            "visible": True,
            "time_filter_reason": str(time_model or "not_time_filtered"),
            "object_time_context": object_time,
        }
    if time_model == "timeofday_mask":
        selected_timeofday = selected_timeofday_value(selected_time_context, constants=constants)
        if selected_timeofday is None:
            return {
                "visible": True,
                "time_filter_reason": "selected_timeofday_unresolved",
                "object_time_context": object_time,
            }
        visible = timeofday_mask_allows_value(
            mask=int(object_time.get("timeofday_mask", 0)),
            timeofday_value=int(selected_timeofday),
            constants=constants,
        )
        return {
            "visible": visible,
            "time_filter_reason": "timeofday_mask_contains_selected_timeofday" if visible else "timeofday_mask_excludes_selected_timeofday",
            "selected_timeofday": int(selected_timeofday),
            "object_time_context": object_time,
        }
    selected_hour = selected_hour_value(selected_time_context)
    if selected_hour is None:
        return {
            "visible": True,
            "time_filter_reason": "selected_hour_unresolved",
            "object_time_context": object_time,
        }
    visible = hour_in_object_range(
        hour=int(selected_hour),
        start=int(object_time.get("hour_start", -1)),
        end=int(object_time.get("hour_end", -1)),
    )
    return {
        "visible": visible,
        "time_filter_reason": "hour_range_contains_selected_hour" if visible else "hour_range_excludes_selected_hour",
        "selected_hour": int(selected_hour),
        "object_time_context": object_time,
    }


def selected_hour_value(selected_time_context: dict[str, Any]) -> int | None:
    selected_hour = parse_int(selected_time_context.get("required_hour"))
    return int(selected_hour) if selected_hour is not None else None


def selected_timeofday_value(selected_time_context: dict[str, Any], *, constants: dict[str, int]) -> int | None:
    selected_timeofday = parse_int(selected_time_context.get("required_timeofday_value"))
    if selected_timeofday is not None:
        return int(selected_timeofday)
    selected_hour = selected_hour_value(selected_time_context)
    if selected_hour is None:
        return None
    return timeofday_value_for_hour(int(selected_hour), constants=constants)


def requested_timeofday_choice(
    choices: list[dict[str, Any]],
    requested_time_context: dict[str, Any],
    *,
    constants: dict[str, int],
) -> dict[str, Any] | None:
    requested_name = str(requested_time_context.get("selected_timeofday") or "").strip().upper()
    if requested_name:
        for choice in choices:
            if requested_name == str(choice.get("name") or "").upper():
                return choice_with_requested_hour(choice, requested_time_context, constants=constants)
    requested_value = parse_int(requested_time_context.get("selected_timeofday_value"))
    if requested_value is None and requested_name:
        if requested_name.endswith("_F"):
            requested_value = constant_with_default(requested_name, constants)
        else:
            requested_value = constant_with_default(f"{requested_name}_F", constants)
    if requested_value is not None:
        for choice in choices:
            if int(choice.get("value", -1)) == (int(requested_value) & 0xFF):
                return choice_with_requested_hour(choice, requested_time_context, constants=constants)
        return None
    requested_hour = requested_hour_context_value(requested_time_context, constants=constants)
    if requested_hour is None:
        return None
    requested_timeofday = timeofday_value_for_hour(int(requested_hour), constants=constants)
    if requested_timeofday is None:
        return None
    for choice in choices:
        if int(choice.get("value", -1)) == int(requested_timeofday):
            selected = dict(choice)
            selected["required_hour"] = int(requested_hour) & 0xFF
            selected["requested_hour"] = int(requested_hour) & 0xFF
            return selected
    return None


def choice_with_requested_hour(
    choice: dict[str, Any],
    requested_time_context: dict[str, Any],
    *,
    constants: dict[str, int],
) -> dict[str, Any] | None:
    requested_hour = requested_hour_context_value(requested_time_context, constants=constants)
    if requested_hour is None:
        return choice
    requested_timeofday = timeofday_value_for_hour(int(requested_hour), constants=constants)
    if requested_timeofday is None or int(choice.get("value", -1)) != int(requested_timeofday):
        return None
    selected = dict(choice)
    selected["required_hour"] = int(requested_hour) & 0xFF
    selected["requested_hour"] = int(requested_hour) & 0xFF
    return selected


def requested_timeofday_context_present(requested_time_context: dict[str, Any]) -> bool:
    return any(
        requested_time_context.get(key) not in {"", None}
        for key in (
            "selected_timeofday",
            "selected_timeofday_value",
            "selected_hour",
            "required_hour",
            "requested_hour",
        )
    )


def requested_hour_context_value(requested_time_context: dict[str, Any], *, constants: dict[str, int]) -> int | None:
    for key in ("selected_hour", "required_hour", "requested_hour"):
        if requested_time_context.get(key) in {"", None}:
            continue
        value = constant_or_int(requested_time_context.get(key), constants)
        if value is not None:
            return int(value) & 0xFF
    return None


def timeofday_mask_choices(mask: int, constants: dict[str, int]) -> list[dict[str, Any]]:
    choices: list[dict[str, Any]] = []
    for name in TIME_OF_DAY_ORDER:
        mask_value = constant_with_default(name, constants)
        timeofday_value = constant_with_default(f"{name}_F", constants)
        if mask_value is None or timeofday_value is None or not (int(mask) & int(mask_value)):
            continue
        choice: dict[str, Any] = {
            "name": name,
            "mask": int(mask_value) & 0xFF,
            "value": int(timeofday_value) & 0xFF,
        }
        hour = constant_with_default(TIME_OF_DAY_HOUR_CONSTANTS[name], constants)
        if hour is not None:
            choice["required_hour"] = int(hour) & 0xFF
        choices.append(choice)
    return choices


def timeofday_mask_allows_value(*, mask: int, timeofday_value: int, constants: dict[str, int]) -> bool:
    for choice in timeofday_mask_choices(mask, constants):
        if int(choice["value"]) == (int(timeofday_value) & 0xFF):
            return True
    return False


def timeofday_value_for_hour(hour: int, *, constants: dict[str, int]) -> int | None:
    hour &= 0xFF
    morn_hour = int(constant_with_default("MORN_HOUR", constants) or 4)
    day_hour = int(constant_with_default("DAY_HOUR", constants) or 10)
    nite_hour = int(constant_with_default("NITE_HOUR", constants) or 18)
    if day_hour <= hour < nite_hour:
        return int(constant_with_default("DAY_F", constants) or 1)
    if morn_hour <= hour < day_hour:
        return int(constant_with_default("MORN_F", constants) or 0)
    return int(constant_with_default("NITE_F", constants) or 2)


def constant_with_default(name: str, constants: dict[str, int]) -> int | None:
    value = constants.get(name)
    if value is not None:
        return int(value)
    default = TIME_OF_DAY_DEFAULT_VALUES.get(name)
    return int(default) if default is not None else None


def object_event_time_watch_symbols(time_context: dict[str, Any]) -> list[str]:
    symbols: list[str] = []
    if time_context.get("time_model") == "hour_range" and time_context.get("time_symbol_available"):
        symbols.append(HOURS_SYMBOL)
    if time_context.get("time_model") == "timeofday_mask":
        if time_context.get("time_symbol_available"):
            symbols.append(TIMEOFDAY_SYMBOL)
        if time_context.get("hour_symbol_available"):
            symbols.append(HOURS_SYMBOL)
    return symbols


def hour_in_object_range(*, hour: int, start: int, end: int) -> bool:
    hour &= 0xFF
    start &= 0xFF
    end &= 0xFF
    if start == end:
        return True
    if start > end:
        return hour >= start or hour <= end
    return start <= hour <= end


def object_event_time_patch_records(
    *,
    entry_values: dict[str, Any],
    constants: dict[str, int],
    requested_time_context: dict[str, Any] | None = None,
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> list[dict[str, Any]]:
    time_context = object_event_time_context(
        entry_values=entry_values,
        symbol_table=symbol_table,
        constants=constants,
        requested_time_context=requested_time_context,
    )
    patches: list[dict[str, Any]] = []
    if time_context.get("time_model") == "hour_range" and HOURS_SYMBOL in symbol_table:
        patches.append(
            patch_record(
                HOURS_SYMBOL,
                int(time_context["required_hour"]),
                symbol_table=symbol_table,
                symbols_path=symbols_path,
                root=root,
            )
        )
    if time_context.get("time_model") == "timeofday_mask":
        if TIMEOFDAY_SYMBOL in symbol_table:
            patches.append(
                patch_record(
                    TIMEOFDAY_SYMBOL,
                    int(time_context["required_timeofday_value"]),
                    symbol_table=symbol_table,
                    symbols_path=symbols_path,
                    root=root,
                )
            )
        if "required_hour" in time_context and HOURS_SYMBOL in symbol_table:
            patches.append(
                patch_record(
                    HOURS_SYMBOL,
                    int(time_context["required_hour"]),
                    symbol_table=symbol_table,
                    symbols_path=symbols_path,
                    root=root,
                )
            )
    return patches


def map_object_row_patch_records(
    *,
    entry_values: dict[str, Any],
    map_object_index: int,
    map_object_struct_id: int,
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> list[dict[str, Any]]:
    return [
        patch_record(map_object_field_symbol(map_object_index, "StructID"), map_object_struct_id & 0xFF, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "Sprite"), int(entry_values["sprite"]), symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "YCoord"), int(entry_values["object_y"]), symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "XCoord"), int(entry_values["object_x"]), symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "Movement"), int(entry_values["movement"]), symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "Radius"), int(entry_values["radius"]), symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "Hour1"), int(entry_values["hour_1"]), symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "Hour2"), int(entry_values["hour_2"]), symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "Type"), (int(entry_values["palette"]) << 4) | int(entry_values["object_type"]), symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "SightRange"), int(entry_values["sight_range"]), symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        *word_patch_records(map_object_field_symbol(map_object_index, "Script"), int(entry_values["script_address"]), symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        *word_patch_records(map_object_field_symbol(map_object_index, "EventFlag"), int(entry_values["event_flag"]), symbol_table=symbol_table, symbols_path=symbols_path, root=root),
    ]


def source_object_events_for_file(*, source_file: str, root: Path) -> list[dict[str, Any]]:
    if not source_file:
        return []
    source_path = resolve_path(source_file, root=root)
    if not source_path.exists():
        return []
    events: list[dict[str, Any]] = []
    object_ordinal = 0
    for line_no, raw in enumerate(source_path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        clean = strip_comment(raw).strip()
        if not clean:
            continue
        if clean.startswith("def_object_events"):
            object_ordinal = 0
            continue
        if not clean.startswith("object_event"):
            continue
        fields = split_macro_args(clean[len("object_event"):])
        if len(fields) < 13:
            continue
        event = {
            "x": field_at(fields, 0),
            "y": field_at(fields, 1),
            "sprite": field_at(fields, 2),
            "movement": field_at(fields, 3),
            "radius_x": field_at(fields, 4),
            "radius_y": field_at(fields, 5),
            "hour_1": field_at(fields, 6),
            "hour_2": field_at(fields, 7),
            "palette": field_at(fields, 8),
            "object_type": field_at(fields, 9),
            "sight_range": field_at(fields, 10),
            "script": field_at(fields, 11),
            "event_flag": field_at(fields, 12),
            "source_object_ordinal": object_ordinal,
            "map_object_index": object_ordinal + 2,
            "source_file": source_file,
            "source_line": line_no,
        }
        events.append(event)
        object_ordinal += 1
    return events


def object_event_object_state_patch(
    *,
    scenario_type: str,
    values: dict[str, Any],
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> dict[str, Any]:
    if scenario_type != "map_object_event":
        return {}
    constants = load_object_event_constants(root=root)
    target_x = parse_int(values.get("x"))
    target_y = parse_int(values.get("y"))
    script_label = str(values.get("script") or "").strip()
    script_symbol = symbol_table.get(script_label)
    map_object_index = map_object_index_for_values(values)
    selected_entry_values, _selected_entry_unresolved = object_event_entry_values(values, constants=constants, script_symbol=script_symbol)
    selected_time_context = (
        object_event_time_context(
            entry_values=selected_entry_values,
            symbol_table=symbol_table,
            constants=constants,
            requested_time_context=values,
        )
        if selected_entry_values
        else {}
    )
    player_context = event_engine_player_context(scenario_type=scenario_type, values=values, root=root)
    player_x = parse_int(player_context.get("player_x"))
    player_y = parse_int(player_context.get("player_y"))
    companion_context = companion_objects_context_patch(
        values=values,
        selected_map_object_index=map_object_index,
        selected_time_context=selected_time_context,
        constants=constants,
        symbol_table=symbol_table,
        symbols_path=symbols_path,
        root=root,
        player_x=player_x,
        player_y=player_y,
    )
    object_struct_index = parse_int(companion_context.get("selected_object_struct_index")) or object_struct_index_for_map_object_index(map_object_index)
    object_struct_symbol = object_struct_symbol_for_index(object_struct_index)
    map_object_prefix = map_object_symbol_prefix(map_object_index)
    missing_symbols = [
        symbol
        for symbol in (
            object_struct_symbol,
            *map_object_field_symbols(map_object_index),
        )
        if symbol not in symbol_table
    ]
    unresolved_values = [
        name
        for name, value in {
            "sprite": constant_or_int(values.get("sprite"), constants),
            "movement": constant_or_int(values.get("movement"), constants),
            "object_type": constant_or_int(values.get("object_type"), constants),
            **optional_object_value_checks(values=values, constants=constants),
        }.items()
        if value is None
    ]
    if target_x is None or target_y is None:
        unresolved_values.append("x/y")
    if not script_label or script_symbol is None:
        unresolved_values.append("script")
    if companion_context.get("selected_object_found") and companion_context.get("selected_object_struct_index") is None:
        unresolved_values.append("selected_object_not_visible_for_player_context")
    if selected_time_context.get("time_selection_valid") is False:
        unresolved_values.append(str(selected_time_context.get("time_selection_error") or "selected_time_context"))
    missing_symbols.extend(string_items(companion_context.get("missing_symbols")))
    unresolved_values.extend(string_items(companion_context.get("unresolved_values")))
    if missing_symbols or unresolved_values:
        return {
            "kind": "object_event_object_state_context",
            "status": "blocked",
            "validation_kind": "object_event_object_struct_and_map_object_state",
            "proof_status": "state_patch_planned",
            "proof_blockers": ["object_struct_not_materialized"],
            "missing_symbols": missing_symbols,
            "unresolved_values": unresolved_values,
            "companion_context": companion_context,
        }

    sprite = int(constant_or_int(values.get("sprite"), constants) or 0)
    movement = int(constant_or_int(values.get("movement"), constants) or 0)
    object_type = int(constant_or_int(values.get("object_type"), constants) or 0) & 0x0F
    palette = int(constant_or_int(values.get("palette"), constants) or 0) & 0x0F
    radius = ((int(constant_or_int(values.get("radius_y"), constants) or 0) & 0x0F) << 4) | (
        int(constant_or_int(values.get("radius_x"), constants) or 0) & 0x0F
    )
    hour_1 = int(constant_or_int(values.get("hour_1"), constants) if values.get("hour_1") not in {"", None} else -1)
    hour_2 = int(constant_or_int(values.get("hour_2"), constants) if values.get("hour_2") not in {"", None} else -1)
    sight_range = int(constant_or_int(values.get("sight_range"), constants) or 0)
    event_flag = int(constant_or_int(values.get("event_flag"), constants) if values.get("event_flag") not in {"", None} else -1)
    object_x = (target_x or 0) + 4
    object_y = (target_y or 0) + 4
    movement_token = str(values.get("movement") or "")
    sprite_movement_attrs = sprite_movement_attributes_for_movement(movement_token, root=root, constants=constants)
    object_direction = object_direction_for_movement(movement_token, sprite_movement_attrs=sprite_movement_attrs)
    object_flags1 = int(sprite_movement_attrs.get("flags1", 0) or 0)
    object_flags2 = int(sprite_movement_attrs.get("flags2", 0) or 0)
    object_palette_flags = int(sprite_movement_attrs.get("palette_flags", 0) or 0)
    script_address = int(script_symbol.get("address", 0))
    script_bank = int(script_symbol.get("bank", 0))
    selected_entry_values = {
        "object_x": object_x,
        "object_y": object_y,
        "sprite": sprite,
        "movement": movement,
        "object_type": object_type,
        "palette": palette,
        "radius": radius,
        "hour_1": hour_1,
        "hour_2": hour_2,
        "sight_range": sight_range,
        "event_flag": event_flag,
        "script_address": script_address,
        "script_bank": script_bank,
    }
    object_mask_context = object_event_object_mask_context(
        entry_values=selected_entry_values,
        map_object_index=map_object_index,
        symbol_table=symbol_table,
    )
    object_time_context = object_event_time_context(
        entry_values=selected_entry_values,
        symbol_table=symbol_table,
        constants=constants,
        requested_time_context=values,
    )
    patches = [
        *object_struct_patch_records(
            object_struct_symbol=object_struct_symbol,
            object_x=object_x,
            object_y=object_y,
            sprite=sprite,
            map_object_index=map_object_index,
            movement=movement,
            object_direction=object_direction,
            object_flags1=object_flags1,
            object_flags2=object_flags2,
            object_palette_flags=object_palette_flags,
            radius=radius,
            sight_range=sight_range,
            symbol_table=symbol_table,
            symbols_path=symbols_path,
            root=root,
        ),
        *object_event_time_patch_records(
            entry_values=selected_entry_values,
            constants=constants,
            requested_time_context=values,
            symbol_table=symbol_table,
            symbols_path=symbols_path,
            root=root,
        ),
        *object_event_object_mask_patch_records(
            entry_values=selected_entry_values,
            map_object_index=map_object_index,
            symbol_table=symbol_table,
            symbols_path=symbols_path,
            root=root,
        ),
        patch_record(map_object_field_symbol(map_object_index, "StructID"), object_struct_index, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "Sprite"), sprite, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "YCoord"), object_y, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "XCoord"), object_x, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "Movement"), movement, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "Radius"), radius, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "Hour1"), hour_1, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "Hour2"), hour_2, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "Type"), (palette << 4) | object_type, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(map_object_field_symbol(map_object_index, "SightRange"), sight_range, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        *word_patch_records(map_object_field_symbol(map_object_index, "Script"), script_address, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        *word_patch_records(map_object_field_symbol(map_object_index, "EventFlag"), event_flag, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        *dict_items(companion_context.get("patches")),
    ]
    return {
        "kind": "object_event_object_state_context",
        "status": "ready",
        "validation_kind": "object_event_object_struct_and_map_object_state",
        "proof_status": "state_patch_planned",
        "object_struct_symbol": object_struct_symbol,
        "object_struct_index": object_struct_index,
        "map_object_index": map_object_index,
        "source_object_ordinal": max(0, map_object_index - 2),
        "map_object_symbol_prefix": map_object_prefix,
        "object_x": object_x,
        "object_y": object_y,
        "sprite": sprite,
        "movement": movement,
        "object_type": object_type,
        "sprite_movement_flags1": object_flags1,
        "sprite_movement_flags2": object_flags2,
        "sprite_movement_palette_flags": object_palette_flags,
        "large_object": bool(sprite_movement_attrs.get("large_object")),
        "large_object_width": 2 if sprite_movement_attrs.get("large_object") else 1,
        "large_object_height": 2 if sprite_movement_attrs.get("large_object") else 1,
        "large_object_collision_model": LARGE_OBJECT_COLLISION_MODEL if sprite_movement_attrs.get("large_object") else "",
        "large_object_size_source": LARGE_OBJECT_SIZE_SOURCE if sprite_movement_attrs.get("large_object") else "",
        "script_label": script_label,
        "script_bank": script_bank,
        "script_address": script_address,
        "script_bank_address": f"{script_bank:02X}:{script_address:04X}",
        "patches": patches,
        "watch_symbols": unique_list(
            [
                *object_event_watch_symbols_for_index(map_object_index, object_struct_index=object_struct_index),
                *string_items(companion_context.get("watch_symbols")),
                *(["wObjectMasks"] if object_mask_context.get("object_masks_symbol_available") else []),
                *(["wEventFlags"] if object_mask_context.get("event_flag") >= 0 and object_mask_context.get("event_flag_symbol_available") else []),
                *object_event_time_watch_symbols(object_time_context),
            ]
        ),
        "object_mask_context": object_mask_context,
        "object_time_context": object_time_context,
        "companion_context": companion_context,
        "companion_object_count": int(companion_context.get("companion_object_count", 0) or 0),
        "offscreen_object_count": int(companion_context.get("offscreen_object_count", 0) or 0),
        "map_row_object_count": int(companion_context.get("map_row_object_count", 0) or 0),
        "selected_visibility": companion_context.get("selected_visibility") or {},
        "visibility_model": companion_context.get("visibility_model", ""),
        "occupancy_model": companion_context.get("occupancy_model", ""),
        "loaded_object_count": 1 + int(companion_context.get("companion_object_count", 0) or 0),
        "proof_blockers": [],
        "errors": [],
        "known_limits": [
            "This patches one generated visible object struct and map-object row; replay/watch/trace must prove TryObjectEvent consumes it.",
        ],
    }


def object_struct_patch_records(
    *,
    object_struct_symbol: str,
    object_x: int,
    object_y: int,
    sprite: int,
    map_object_index: int,
    movement: int,
    object_direction: int,
    object_flags1: int,
    object_flags2: int,
    object_palette_flags: int,
    radius: int,
    sight_range: int,
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> list[dict[str, Any]]:
    values = {
        "OBJECT_SPRITE": sprite,
        "OBJECT_MAP_OBJECT_INDEX": map_object_index,
        "OBJECT_MOVEMENT_TYPE": movement,
        "OBJECT_FLAGS1": object_flags1,
        "OBJECT_FLAGS2": object_flags2,
        "OBJECT_PALETTE": object_palette_flags,
        "OBJECT_WALKING": 0xFF,
        "OBJECT_DIRECTION": object_direction,
        "OBJECT_STEP_TYPE": 0,
        "OBJECT_FACING": 0xFF,
        "OBJECT_MAP_X": object_x,
        "OBJECT_MAP_Y": object_y,
        "OBJECT_LAST_MAP_X": object_x,
        "OBJECT_LAST_MAP_Y": object_y,
        "OBJECT_INIT_X": object_x,
        "OBJECT_INIT_Y": object_y,
        "OBJECT_RADIUS": radius,
        "OBJECT_SPRITE_X": 0,
        "OBJECT_SPRITE_Y": 0,
        "OBJECT_RANGE": sight_range,
    }
    return [
        patch_record(
            object_struct_symbol,
            value,
            symbol_table=symbol_table,
            symbols_path=symbols_path,
            root=root,
            address_offset=OBJECT_STRUCT_OFFSETS[name],
            display_symbol=f"{object_struct_symbol}+{name}",
        )
        for name, value in values.items()
    ]


def word_patch_records(
    symbol: str,
    value: int,
    *,
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> list[dict[str, Any]]:
    value &= 0xFFFF
    return [
        patch_record(symbol, value & 0xFF, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(
            symbol,
            (value >> 8) & 0xFF,
            symbol_table=symbol_table,
            symbols_path=symbols_path,
            root=root,
            address_offset=1,
            display_symbol=f"{symbol}+1",
        ),
    ]


def event_flag_patch_record(
    event_flag: int,
    *,
    required_state: str,
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> dict[str, Any]:
    byte_offset = int(event_flag) // 8
    bit_index = int(event_flag) & 7
    bit_mask = 1 << bit_index
    value = bit_mask if required_state == "set" else 0
    patch = patch_record(
        "wEventFlags",
        value,
        symbol_table=symbol_table,
        symbols_path=symbols_path,
        root=root,
        address_offset=byte_offset,
        display_symbol=f"wEventFlags+{byte_offset}",
    )
    return {
        **patch,
        "patch_kind": "bit",
        "bit_operation": "set" if required_state == "set" else "reset",
        "bit_index": bit_index,
        "bit_mask": bit_mask,
        "event_flag": int(event_flag),
        "event_flag_byte_offset": byte_offset,
        "preserves_other_bits": True,
    }


def object_direction_for_movement(movement: str, *, sprite_movement_attrs: dict[str, Any] | None = None) -> int:
    if sprite_movement_attrs:
        initial_facing = sprite_movement_attrs.get("initial_facing")
        if isinstance(initial_facing, int):
            return (initial_facing & 0x03) << 2
    token = movement.upper()
    if token.endswith("_UP"):
        return OW_DIRECTION_VALUES["OW_UP"]
    if token.endswith("_LEFT"):
        return OW_DIRECTION_VALUES["OW_LEFT"]
    if token.endswith("_RIGHT"):
        return OW_DIRECTION_VALUES["OW_RIGHT"]
    return OW_DIRECTION_VALUES["OW_DOWN"]


def optional_object_value_checks(*, values: dict[str, Any], constants: dict[str, int]) -> dict[str, int | None]:
    return {
        key: constant_or_int(values.get(key), constants)
        for key in ("radius_x", "radius_y", "hour_1", "hour_2", "palette", "sight_range", "event_flag")
        if values.get(key) not in {"", None}
    }


def sprite_movement_attributes_for_movement(
    movement: str,
    *,
    root: Path,
    constants: dict[str, int],
) -> dict[str, Any]:
    token = str(movement or "").strip().upper()
    if not token:
        return {}
    return load_sprite_movement_attributes(root=root, constants=constants).get(token, {})


def load_sprite_movement_attributes(*, root: Path, constants: dict[str, int]) -> dict[str, dict[str, Any]]:
    path = root / SPRITE_MOVEMENT_DATA_FILE
    if not path.exists():
        return {}
    records: dict[str, dict[str, Any]] = {}
    current = ""
    fields: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        comment = raw.split(";", 1)[1].strip() if ";" in raw else ""
        if comment.startswith("SPRITEMOVEDATA_"):
            current = comment.split()[0].strip().upper()
            fields = []
            continue
        if not current:
            continue
        clean = strip_comment(raw).strip()
        if not clean.startswith("db "):
            continue
        fields.append(clean[3:].strip())
        if len(fields) < 6:
            continue
        initial_facing = sprite_movement_expr_value(fields[1], constants)
        flags1 = sprite_movement_expr_value(fields[3], constants) or 0
        flags2 = sprite_movement_expr_value(fields[4], constants) or 0
        palette_flags = sprite_movement_expr_value(fields[5], constants) or 0
        records[current] = {
            "movement_token": current,
            "movement_function": fields[0],
            "initial_facing": initial_facing,
            "action": fields[2],
            "flags1": flags1 & 0xFF,
            "flags2": flags2 & 0xFF,
            "palette_flags": palette_flags & 0xFF,
            "large_object": bool((palette_flags & BIG_OBJECT_FLAG) or "BIG_OBJECT" in fields[5].upper()),
            "source_file": SPRITE_MOVEMENT_DATA_FILE,
        }
        current = ""
        fields = []
    return records


def sprite_movement_expr_value(expr: str, constants: dict[str, int]) -> int | None:
    value = constant_expression_value(expr, constants)
    if value is not None:
        return value
    total = 0
    found = False
    for token in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", str(expr)):
        if token in constants:
            total |= int(constants[token])
            found = True
    return total if found else None


def load_object_event_constants(*, root: Path) -> dict[str, int]:
    constants: dict[str, int] = dict(OBJECT_EVENT_BASE_CONSTANTS)
    for relative in OBJECT_EVENT_CONSTANT_FILES:
        path = root / relative
        if path.exists():
            parse_constant_source(path.read_text(encoding="utf-8", errors="replace").splitlines(), constants)
    return constants


def parse_constant_source(lines: list[str], constants: dict[str, int]) -> None:
    const_value = 0
    const_inc = 1
    for raw in lines:
        line = strip_comment(raw)
        if not line:
            continue
        if line.startswith("const_def"):
            fields = line.split(maxsplit=1)
            args = split_macro_args(fields[1]) if len(fields) > 1 else []
            eval_constants = {**constants, "const_value": const_value, "const_inc": const_inc}
            const_value = constant_expression_value(args[0], eval_constants) if args else 0
            if const_value is None:
                const_value = 0
            const_inc = constant_expression_value(args[1], eval_constants) if len(args) > 1 else 1
            if const_inc is None:
                const_inc = 1
            continue
        if line.startswith("const "):
            fields = line.split()
            if len(fields) >= 2:
                constants[fields[1]] = const_value
                const_value += const_inc
            continue
        if line.startswith("shift_const "):
            fields = line.split()
            if len(fields) >= 2:
                constants[fields[1]] = 1 << const_value
                constants[f"{fields[1]}_F"] = const_value
                const_value += const_inc
            continue
        if line.startswith("const_skip"):
            fields = line.split(maxsplit=1)
            eval_constants = {**constants, "const_value": const_value, "const_inc": const_inc}
            count = constant_expression_value(fields[1], eval_constants) if len(fields) > 1 else 1
            const_value += const_inc * int(count if count is not None else 1)
            continue
        if line.startswith("const_next"):
            fields = line.split(maxsplit=1)
            if len(fields) > 1:
                eval_constants = {**constants, "const_value": const_value, "const_inc": const_inc}
                next_value = constant_expression_value(fields[1], eval_constants)
                if next_value is not None:
                    const_value = next_value
            continue
        match = re.match(r"DEF\s+(?P<name>[A-Za-z0-9_]+)\s+EQU\s+(?P<expr>.+)", line)
        if match:
            eval_constants = {**constants, "const_value": const_value, "const_inc": const_inc}
            value = constant_expression_value(match.group("expr"), eval_constants)
            if value is not None:
                constants[match.group("name")] = value


def constant_or_int(value: Any, constants: dict[str, int]) -> int | None:
    numeric = parse_int(value)
    if numeric is not None:
        return numeric
    text = str(value or "").strip()
    if not text:
        return None
    return constants.get(text)


def constant_expression_value(expr: str, constants: dict[str, int]) -> int | None:
    text = strip_comment(expr).strip()
    if not text:
        return None
    text = re.sub(r"\$([0-9A-Fa-f]+)", r"0x\1", text)

    def replace_name(match: re.Match[str]) -> str:
        name = match.group(0)
        if name in constants:
            return str(constants[name])
        return name

    text = re.sub(r"\b[A-Za-z_][A-Za-z0-9_]*\b", replace_name, text)
    if re.search(r"[^0-9xXa-fA-F+\-*/%<>()|&~\s]", text):
        return parse_int(expr)
    try:
        return int(eval(text, {"__builtins__": {}}, {}))
    except Exception:
        return parse_int(expr)


def event_engine_position_value_key(symbol: str) -> str:
    return {
        "wPlayerMapX": "player_map_x",
        "wPlayerMapY": "player_map_y",
        "wPlayerDirection": "facing_direction_value",
    }.get(symbol, "")


def map_event_context_patch(
    *,
    scenario: dict[str, Any],
    values: dict[str, Any],
    map_name: str,
    scene_var_index: dict[str, dict[str, Any]],
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> dict[str, Any]:
    scene_token = str(values.get("scene") or "").strip()
    if str(scenario.get("scenario_type", "")) != "map_coord_event" or not scene_token:
        return {}
    context: dict[str, Any] = {
        "kind": "coord_event_scene_context",
        "scene_token": scene_token,
        "validation_kind": "source_scene_var_and_scene_script_order",
        "proof_status": "state_patch_planned",
    }
    scene_var = scene_var_index.get(normalize_map_key(map_name), {})
    if not scene_var:
        context["errors"] = [f"scene variable not found in data/maps/scenes.asm for map: {map_name}"]
        return context
    scene_value = scene_value_for_token(
        scene_token,
        source_file=normalize_path(str(scenario.get("source_file") or values.get("source_file") or "")),
        root=root,
    )
    if scene_value is None:
        context["errors"] = [f"scene id not found in map scene_script declarations: {scene_token}"]
        return {**context, "scene_symbol": scene_var.get("scene_symbol", "")}
    scene_symbol = str(scene_var.get("scene_symbol", ""))
    patch = {
        **patch_record(scene_symbol, scene_value, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        "validation_kind": "source_scene_var_and_scene_script_order",
        "source_scene_token": scene_token,
        "source_scene_value": scene_value,
        "source_scene_var_file": scene_var.get("source_file", ""),
        "source_scene_var_line": scene_var.get("line", 0),
    }
    return {
        **context,
        "map_name": map_name,
        "map_constant": scene_var.get("map_constant", ""),
        "scene_symbol": scene_symbol,
        "scene_value": scene_value,
        "scene_value_hex": f"{scene_value & 0xFF:02X}",
        "scene_source_file": scene_var.get("source_file", ""),
        "scene_source_line": scene_var.get("line", 0),
        "patch": patch,
        "errors": [],
    }


def scene_value_for_token(scene_token: str, *, source_file: str, root: Path) -> int | None:
    numeric = parse_int(scene_token)
    if numeric is not None:
        return numeric & 0xFF
    if not source_file:
        return None
    source_path = resolve_path(source_file, root=root)
    if not source_path.exists():
        return None
    scene_index = 0
    for raw in source_path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = SCENE_SCRIPT_RE.match(strip_comment(raw))
        if not match:
            continue
        if match.group("const") == scene_token:
            return scene_index
        scene_index += 1
    return None


def normalize_map_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def strip_comment(line: str) -> str:
    return line.split(";", 1)[0].strip()


def script_entry_materialization(
    *,
    scenario: dict[str, Any],
    precondition: dict[str, Any],
    scenario_id: str,
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> dict[str, Any]:
    values = precondition.get("values") if isinstance(precondition.get("values"), dict) else {}
    script_label = str(values.get("script_label") or scenario.get("label") or "").strip()
    errors = []
    script_symbol = symbol_table.get(script_label)
    if not script_label:
        errors.append("could not infer script label from precondition or scenario label")
    elif script_symbol is None:
        errors.append(f"script label not found in {display_path(symbols_path, root=root)}: {script_label}")
    script_bank = int(script_symbol.get("bank", 0)) if script_symbol else 0
    script_address = int(script_symbol.get("address", 0)) if script_symbol else 0
    patches = [
        patch_record("wScriptBank", script_bank, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record("wScriptPos", script_address & 0xFF, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(
            "wScriptPos",
            (script_address >> 8) & 0xFF,
            symbol_table=symbol_table,
            symbols_path=symbols_path,
            root=root,
            address_offset=1,
            display_symbol="wScriptPos+1",
        ),
        patch_record("wScriptRunning", SCRIPT_RUNNING_MAPSCRIPT, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record("wScriptMode", SCRIPT_MODE_READ, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record("wScriptStackSize", 0, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
    ]
    errors.extend(error for patch in patches for error in patch.get("errors", []))
    return {
        "scenario_id": scenario_id,
        "scenario_type": str(scenario.get("scenario_type", "")),
        "precondition_id": str(precondition.get("id", "")),
        "precondition_kind": "script_entry",
        "status": "ready" if not errors and patches else "blocked",
        "source_file": normalize_path(str(scenario.get("source_file") or values.get("source_file") or "")),
        "script_label": script_label,
        "script_resolution": {
            "label": script_label,
            "bank": script_bank,
            "address": script_address,
            "bank_address": str(script_symbol.get("bank_address", "")) if script_symbol else "",
        },
        "values": dict(values),
        "patch_count": len(patches),
        "patches": patches,
        "errors": errors,
        "commands": [
            "python -m tools.debugger trace-instructions "
            "--symbol ScriptEvents --symbol RunScriptCommand "
            "--watch-symbol wScriptPos --watch-symbol wScriptVar "
            "--save-state <patched-state> --execute --require-hit",
            "python -m tools.debugger replay "
            f"--scenario-id {scenario_id} --save-state <patched-state> "
            "--symbol ScriptEvents --watch-symbol wScriptPos --execute-watch",
        ],
        "known_limits": [
            "This patches the same script runner WRAM fields initialized by CallScript for a selected a:hl script pointer.",
            "The patched state still needs replay or instruction tracing to prove the selected script commands execute under the surrounding map state.",
        ],
    }


def movement_entry_materialization(
    *,
    scenario: dict[str, Any],
    precondition: dict[str, Any],
    scenario_id: str,
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> dict[str, Any]:
    values = precondition.get("values") if isinstance(precondition.get("values"), dict) else {}
    movement_label = str(values.get("movement_label") or values.get("movement") or scenario.get("label") or "").strip()
    object_id = parse_int(values.get("object_id"))
    if object_id is None:
        object_id = PLAYER_OBJECT
    errors = []
    movement_symbol = symbol_table.get(movement_label)
    if not movement_label:
        errors.append("could not infer movement label from precondition or scenario label")
    elif movement_symbol is None:
        errors.append(f"movement label not found in {display_path(symbols_path, root=root)}: {movement_label}")
    movement_bank = int(movement_symbol.get("bank", 0)) if movement_symbol else 0
    movement_address = int(movement_symbol.get("address", 0)) if movement_symbol else 0
    patches = [
        patch_record("wMovementObject", object_id, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record("wMovementDataBank", movement_bank, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
        patch_record(
            "wMovementDataAddress",
            movement_address & 0xFF,
            symbol_table=symbol_table,
            symbols_path=symbols_path,
            root=root,
        ),
        patch_record(
            "wMovementDataAddress",
            (movement_address >> 8) & 0xFF,
            symbol_table=symbol_table,
            symbols_path=symbols_path,
            root=root,
            address_offset=1,
            display_symbol="wMovementDataAddress+1",
        ),
        patch_record(
            "wMovementPointer",
            movement_address & 0xFF,
            symbol_table=symbol_table,
            symbols_path=symbols_path,
            root=root,
        ),
        patch_record(
            "wMovementPointer",
            (movement_address >> 8) & 0xFF,
            symbol_table=symbol_table,
            symbols_path=symbols_path,
            root=root,
            address_offset=1,
            display_symbol="wMovementPointer+1",
        ),
        patch_record("wScriptMode", SCRIPT_MODE_WAIT_MOVEMENT, symbol_table=symbol_table, symbols_path=symbols_path, root=root),
    ]
    errors.extend(error for patch in patches for error in patch.get("errors", []))
    return {
        "scenario_id": scenario_id,
        "scenario_type": str(scenario.get("scenario_type", "")),
        "precondition_id": str(precondition.get("id", "")),
        "precondition_kind": "movement_entry",
        "status": "ready" if not errors and patches else "blocked",
        "source_file": normalize_path(str(scenario.get("source_file") or values.get("source_file") or "")),
        "movement_label": movement_label,
        "movement_resolution": {
            "label": movement_label,
            "bank": movement_bank,
            "address": movement_address,
            "bank_address": str(movement_symbol.get("bank_address", "")) if movement_symbol else "",
        },
        "values": {**dict(values), "object_id": object_id},
        "patch_count": len(patches),
        "patches": patches,
        "errors": errors,
        "commands": [
            "python -m tools.debugger trace-instructions "
            "--symbol ApplyMovement --symbol GetMovementData --symbol HandleMovementData "
            "--watch-symbol wMovementDataAddress --watch-symbol wMovementPointer --watch-symbol wMovementObject "
            "--save-state <patched-state> --execute --require-hit",
            "python -m tools.debugger replay "
            f"--scenario-id {scenario_id} --save-state <patched-state> "
            "--symbol ApplyMovement --symbol HandleMovementData --watch-symbol wMovementPointer --execute-watch",
        ],
        "known_limits": [
            "This patches the movement pointer WRAM fields initialized by GetMovementData/LoadMovementDataPointer for a selected b:hl movement pointer.",
            "The patched state does not synthesize the selected object's full object struct or visibility; replay or instruction tracing must prove movement execution in context.",
        ],
    }


def audio_engine_entry_materialization(
    *,
    scenario: dict[str, Any],
    precondition: dict[str, Any],
    scenario_id: str,
) -> dict[str, Any]:
    values = precondition.get("values") if isinstance(precondition.get("values"), dict) else {}
    music_label = str(values.get("music_label") or scenario.get("label") or "").strip()
    runtime_symbols = ["PlayMusic", "_PlayMusic", "ParseMusic", "ParseMusicCommand"]
    trace_symbols = " ".join(f"--symbol {symbol}" for symbol in runtime_symbols)
    watch_args = " ".join(f"--watch-symbol {symbol}" for symbol in AUDIO_ENTRY_WATCH_SYMBOLS)
    trace_report = f".local\\tmp\\debugger_audio_output_trace_{scenario_id}.json"
    trace_path = f".local\\tmp\\debugger_audio_output_trace_{scenario_id}.jsonl"
    output_records = materialization_outputs(
        scenario=scenario,
        precondition=precondition,
        fallback=[
            {
                "kind": "audio_engine_output",
                "state_symbol": symbol,
                "size": 1,
                "producer_symbol": "PlayMusic",
                "source_function": music_label or "PlayMusic",
            }
            for symbol in AUDIO_ENTRY_WATCH_SYMBOLS
        ] + [
            {
                "kind": "audio_hardware_output",
                "address": address,
                "address_label": hardware_label,
                "size": 1,
                "producer_symbol": "PlayMusic",
                "source_function": music_label or "PlayMusic",
            }
            for hardware_label, address in AUDIO_HARDWARE_OUTPUTS
        ],
    )
    sink_args = sink_args_for_outputs(output_records)
    watch_address_args = watch_address_args_for_outputs(output_records)
    return {
        "scenario_id": scenario_id,
        "scenario_type": str(scenario.get("scenario_type", "")),
        "precondition_id": str(precondition.get("id", "")),
        "precondition_kind": "audio_engine_entry",
        "status": "planned",
        "source_file": normalize_path(str(scenario.get("source_file") or values.get("source_file") or "")),
        "music_label": music_label,
        "values": dict(values),
        "patch_count": 0,
        "patches": [],
        "watch_symbols": list(AUDIO_ENTRY_WATCH_SYMBOLS),
        "runtime_symbols": runtime_symbols,
        "outputs": output_records,
        "errors": [],
        "notes": [
            "Audio content currently needs an owning caller or save state that invokes PlayMusic/_PlayMusic for the selected music data.",
            "The planned proof watches music id/bank and channel flags while tracing PlayMusic/_PlayMusic and ParseMusic helpers, then feeds the trace to dynamic taint.",
        ],
        "commands": [
            (
                "python -m tools.debugger trace-instructions "
                f"{trace_symbols} "
                f"{watch_args} {watch_address_args} --save-state <runtime-state> "
                f"--execute --require-hit --out-trace {trace_path} --json-out {trace_report}"
            ),
            (
                "python -m tools.debugger replay "
                f"--scenario-id {scenario_id} --save-state <runtime-state> "
                f"{trace_symbols} {watch_args} {watch_address_args} --execute-watch"
            ),
            (
                "python -m tools.debugger dynamic-taint "
                f"--report {trace_report} {sink_args}"
            ).strip(),
        ],
    }


def materialization_outputs(
    *,
    scenario: dict[str, Any],
    precondition: dict[str, Any],
    fallback: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    outputs = precondition.get("outputs") if isinstance(precondition.get("outputs"), list) else scenario.get("outputs", [])
    return [
        output
        for output in outputs
        if isinstance(output, dict)
    ] or fallback


def sink_args_for_outputs(output_records: list[dict[str, Any]]) -> str:
    symbol_args = [
        f"--sink-symbol {symbol}"
        for symbol in unique_list(str(output.get("state_symbol", "")) for output in output_records if output.get("state_symbol"))
    ]
    address_args = [
        f"--sink-address {command_address_arg(address)}"
        for address in unique_list(
            str(output.get("address") or output.get("watch_address") or output.get("sink_address") or "")
            for output in output_records
            if output.get("address") or output.get("watch_address") or output.get("sink_address")
        )
    ]
    return " ".join([*symbol_args, *address_args])


def watch_address_args_for_outputs(output_records: list[dict[str, Any]]) -> str:
    return " ".join(
        f"--watch-address {command_address_arg(address)}"
        for address in unique_list(
            str(output.get("address") or output.get("watch_address") or output.get("sink_address") or "")
            for output in output_records
            if output.get("address") or output.get("watch_address") or output.get("sink_address")
        )
    )


def asset_loader_entry_materialization(
    *,
    scenario: dict[str, Any],
    precondition: dict[str, Any],
    scenario_id: str,
) -> dict[str, Any]:
    values = precondition.get("values") if isinstance(precondition.get("values"), dict) else {}
    asset = str(values.get("asset") or "").strip()
    label = str(values.get("label") or scenario.get("label") or "").strip()
    watch_args = " ".join(f"--watch-symbol {symbol}" for symbol in ASSET_REQUEST_WATCH_SYMBOLS)
    trace_report = f".local\\tmp\\debugger_asset_output_trace_{scenario_id}.json"
    trace_path = f".local\\tmp\\debugger_asset_output_trace_{scenario_id}.jsonl"
    output_records = materialization_outputs(
        scenario=scenario,
        precondition=precondition,
        fallback=[
            {
                "kind": "asset_request_output",
                "state_symbol": symbol,
                "size": 1,
                "producer_symbol": "Request2bpp",
                "source_function": label or "Request2bpp",
                "asset": asset,
            }
            for symbol in ASSET_REQUEST_WATCH_SYMBOLS
        ],
    )
    sink_args = sink_args_for_outputs(output_records)
    return {
        "scenario_id": scenario_id,
        "scenario_type": str(scenario.get("scenario_type", "")),
        "precondition_id": str(precondition.get("id", "")),
        "precondition_kind": "asset_loader_entry",
        "status": "planned",
        "source_file": normalize_path(str(scenario.get("source_file") or values.get("source_file") or "")),
        "asset": asset,
        "label": label,
        "values": dict(values),
        "patch_count": 0,
        "patches": [],
        "watch_symbols": list(ASSET_REQUEST_WATCH_SYMBOLS),
        "runtime_symbols": ["Request2bpp", "Get1bpp", "Decompress"],
        "outputs": output_records,
        "errors": [],
        "notes": [
            "Asset content currently needs an owning graphics/data loader or save state that requests this INCBIN payload.",
            "The planned proof watches 1bpp/2bpp request queues while tracing the graphics loader helpers, then feeds the trace to dynamic taint.",
        ],
        "commands": [
            (
                "python -m tools.debugger trace-instructions "
                "--symbol Request2bpp --symbol Get1bpp --symbol Decompress "
                f"{watch_args} --save-state <runtime-state> "
                f"--execute --require-hit --out-trace {trace_path} --json-out {trace_report}"
            ),
            (
                "python -m tools.debugger replay "
                f"--scenario-id {scenario_id} --save-state <runtime-state> "
                f"--symbol Request2bpp --symbol Get1bpp --symbol Decompress {watch_args} --execute-watch"
            ),
            (
                "python -m tools.debugger dynamic-taint "
                f"--report {trace_report} {sink_args}"
            ).strip(),
        ],
    }


def ui_output_sink_materialization(
    *,
    scenario: dict[str, Any],
    precondition: dict[str, Any],
    scenario_id: str,
) -> dict[str, Any]:
    values = precondition.get("values") if isinstance(precondition.get("values"), dict) else {}
    ui_label = str(values.get("ui_label") or scenario.get("label") or "").strip()
    helper = str(values.get("helper") or "PlaceString").strip()
    runtime_symbols = unique_list([helper, *UI_TILEMAP_HELPERS])
    watch_args = " ".join(f"--watch-symbol {symbol}" for symbol in UI_OUTPUT_WATCH_SYMBOLS)
    trace_symbols = " ".join(f"--symbol {symbol}" for symbol in runtime_symbols[:8])
    trace_report = f".local\\tmp\\debugger_ui_output_trace_{scenario_id}.json"
    trace_path = f".local\\tmp\\debugger_ui_output_trace_{scenario_id}.jsonl"
    output_records = materialization_outputs(
        scenario=scenario,
        precondition=precondition,
        fallback=[
            {"kind": "ui_tilemap_output", "state_symbol": "wTilemap", "size": 1, "producer_symbol": helper, "source_function": ui_label or helper},
            {"kind": "ui_attrmap_output", "state_symbol": "wAttrmap", "size": 1, "producer_symbol": helper, "source_function": ui_label or helper},
        ],
    )
    sink_args = sink_args_for_outputs(output_records)
    watch_address_args = watch_address_args_for_outputs(output_records)
    return {
        "scenario_id": scenario_id,
        "scenario_type": str(scenario.get("scenario_type", "")),
        "precondition_id": str(precondition.get("id", "")),
        "precondition_kind": "ui_output_sink",
        "status": "planned",
        "source_file": normalize_path(str(scenario.get("source_file") or values.get("source_file") or "")),
        "ui_label": ui_label,
        "helper": helper,
        "values": dict(values),
        "patch_count": 0,
        "patches": [],
        "watch_symbols": list(UI_OUTPUT_WATCH_SYMBOLS),
        "runtime_symbols": runtime_symbols,
        "outputs": output_records,
        "errors": [],
        "notes": [
            "UI output content needs a runtime caller or save state that reaches the selected drawing helper.",
            "The planned proof watches tilemap/attrmap and BG-map control state while tracing UI tilemap helpers, then feeds the trace to dynamic taint.",
        ],
        "commands": [
            (
                "python -m tools.debugger trace-instructions "
                f"{trace_symbols} {watch_args} {watch_address_args} --save-state <runtime-state> "
                f"--execute --require-hit --out-trace {trace_path} --json-out {trace_report}"
            ).strip(),
            (
                "python -m tools.debugger replay "
                f"--scenario-id {scenario_id} --save-state <runtime-state> "
                f"{trace_symbols} {watch_args} {watch_address_args} --execute-watch"
            ).strip(),
            (
                "python -m tools.debugger dynamic-taint "
                f"--report {trace_report} {sink_args}"
            ).strip(),
        ],
    }


def optional_patch_record(
    symbol: str,
    value: int | None,
    *,
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> dict[str, Any]:
    return patch_record(symbol, value, symbol_table=symbol_table, symbols_path=symbols_path, root=root)


def patch_record(
    symbol: str,
    value: int | None,
    *,
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
    address_offset: int = 0,
    display_symbol: str = "",
) -> dict[str, Any]:
    entry = symbol_table.get(symbol)
    errors = []
    if entry is None:
        errors.append(f"symbol not found in {display_path(symbols_path, root=root)}: {symbol}")
    address = int(entry.get("address", 0)) + int(address_offset) if entry else 0
    return {
        "symbol": display_symbol or symbol,
        "base_symbol": symbol,
        "address_offset": int(address_offset),
        "value": int(value or 0) & 0xFF,
        "value_hex": f"{int(value or 0) & 0xFF:02X}",
        "bank": int(entry.get("bank", 0)) if entry else 0,
        "address": address,
        "bank_address": (
            f"{int(entry.get('bank', 0)):02X}:{address:04X}"
            if entry else ""
        ),
        "errors": errors,
    }


def non_patch_materialization(scenario: dict[str, Any], precondition: dict[str, Any], *, reason: str) -> dict[str, Any]:
    return {
        "scenario_id": setup_scenario_id_for(scenario),
        "scenario_type": str(scenario.get("scenario_type", "")),
        "precondition_id": str(precondition.get("id", "")),
        "precondition_kind": str(precondition.get("kind", "")),
        "status": "planned",
        "source_file": normalize_path(str(scenario.get("source_file", ""))),
        "values": precondition.get("values", {}) if isinstance(precondition.get("values"), dict) else {},
        "patch_count": 0,
        "patches": [],
        "errors": [],
        "notes": [reason],
        "commands": [],
    }


def execute_materialization(
    *,
    materializations: list[dict[str, Any]],
    rom: Path,
    base_state: Path | None,
    output_state: Path | None,
    execute: bool,
    root: Path,
) -> dict[str, Any]:
    if not execute:
        return skipped_execution(execute=False, out_state=display_path(output_state, root=root) if output_state else "")
    if base_state is None or output_state is None:
        return {"executed": False, "errors": ["--execute requires --base-save-state and --out-state"], "warnings": []}
    patches = [
        patch
        for materialization in materializations
        if materialization.get("status") == "ready"
        for patch in materialization.get("patches", [])
        if isinstance(patch, dict)
    ]
    pyboy = trace_runtime.open_pyboy(
        rom,
        "PyBoy is required for content state materialization. Import failed",
    )
    trace_runtime.disable_realtime(pyboy)
    try:
        with base_state.open("rb") as fh:
            pyboy.load_state(fh)
        applied = []
        for patch in patches:
            write_value = patch_write_value(pyboy, patch)
            applied_patch = {**patch, "value": write_value, "value_hex": f"{write_value:02X}"}
            write_byte(pyboy, bank=int(patch["bank"]), address=int(patch["address"]), value=write_value)
            observed = read_byte(pyboy, bank=int(patch["bank"]), address=int(patch["address"]))
            applied.append({**applied_patch, "observed": observed, "observed_hex": f"{observed:02X}", "verified": observed == write_value})
        output_state.parent.mkdir(parents=True, exist_ok=True)
        with output_state.open("wb") as fh:
            pyboy.save_state(fh)
    finally:
        stop_pyboy(pyboy)
    errors = [
        f"patch verification failed: {patch['symbol']} expected {patch['value_hex']} observed {patch['observed_hex']}"
        for patch in applied
        if not patch.get("verified")
    ]
    return {
        "executed": not errors,
        "base_save_state": display_path(base_state, root=root),
        "out_state": display_path(output_state, root=root),
        "save_state_delta": save_state_delta_summary(base_state=base_state, output_state=output_state, root=root),
        "patch_count": len(applied),
        "applied_patches": applied,
        "errors": errors,
        "warnings": [],
    }


def patch_write_value(pyboy: Any, patch: dict[str, Any]) -> int:
    if patch.get("patch_kind") != "bit":
        return int(patch["value"]) & 0xFF
    current = read_byte(pyboy, bank=int(patch["bank"]), address=int(patch["address"]))
    mask = int(patch.get("bit_mask", 0)) & 0xFF
    if patch.get("bit_operation") == "set":
        return current | mask
    return current & (~mask & 0xFF)


def save_state_delta_summary(
    *,
    base_state: Path | None,
    output_state: Path | None,
    root: Path,
    max_offsets: int = 64,
    max_samples: int = 24,
) -> dict[str, Any]:
    base_display = display_path(base_state, root=root) if base_state is not None else ""
    output_display = display_path(output_state, root=root) if output_state is not None else ""
    if base_state is None or output_state is None:
        return {
            "attempted": False,
            "proof_status": "planned_only",
            "base_save_state": base_display,
            "out_state": output_display,
            "changed_byte_count": 0,
            "changed_offsets": [],
            "samples": [],
            "errors": ["base and output save states are required for delta comparison"],
        }
    try:
        base_bytes = base_state.read_bytes()
        output_bytes = output_state.read_bytes()
    except OSError as exc:
        return {
            "attempted": True,
            "proof_status": "planned_only",
            "base_save_state": base_display,
            "out_state": output_display,
            "changed_byte_count": 0,
            "changed_offsets": [],
            "samples": [],
            "errors": [str(exc)],
        }
    changed_offsets: list[int] = []
    samples: list[dict[str, Any]] = []
    changed_count = 0
    for offset in range(max(len(base_bytes), len(output_bytes))):
        before = base_bytes[offset] if offset < len(base_bytes) else None
        after = output_bytes[offset] if offset < len(output_bytes) else None
        if before == after:
            continue
        changed_count += 1
        if len(changed_offsets) < max_offsets:
            changed_offsets.append(offset)
        if len(samples) < max_samples:
            samples.append(save_state_delta_sample(offset=offset, before=before, after=after))
    return {
        "attempted": True,
        "proof_status": "state_materialized",
        "base_save_state": base_display,
        "out_state": output_display,
        "base_size_bytes": len(base_bytes),
        "out_size_bytes": len(output_bytes),
        "size_changed": len(base_bytes) != len(output_bytes),
        "base_sha256": sha256_file(base_state),
        "out_sha256": sha256_file(output_state),
        "changed_byte_count": changed_count,
        "changed_offsets": changed_offsets,
        "changed_offsets_truncated": changed_count > len(changed_offsets),
        "sample_count": len(samples),
        "samples": samples,
        "errors": [],
    }


def save_state_delta_sample(*, offset: int, before: int | None, after: int | None) -> dict[str, Any]:
    return {
        "offset": offset,
        "offset_hex": f"{offset:06X}",
        "before": before,
        "before_hex": "" if before is None else f"{before:02X}",
        "after": after,
        "after_hex": "" if after is None else f"{after:02X}",
    }


def stop_pyboy(pyboy: Any) -> None:
    stop = getattr(pyboy, "stop", None)
    if stop is None:
        return
    try:
        stop(save=False)
    except TypeError:
        stop()


def skipped_execution(*, execute: bool, out_state: str) -> dict[str, Any]:
    return {
        "executed": False,
        "out_state": out_state,
        "patch_count": 0,
        "applied_patches": [],
        "errors": [],
        "warnings": [] if not execute else ["execution skipped because materialization was not ready"],
    }


def write_byte(pyboy: Any, *, bank: int, address: int, value: int) -> None:
    if 0xD000 <= address <= 0xDFFF and bank:
        try:
            pyboy.memory[bank, address] = value & 0xFF
            return
        except Exception:
            old_bank = int(pyboy.memory[0xFF70])
            pyboy.memory[0xFF70] = bank
            try:
                pyboy.memory[address] = value & 0xFF
            finally:
                pyboy.memory[0xFF70] = old_bank
            return
    pyboy.memory[address] = value & 0xFF


def read_byte(pyboy: Any, *, bank: int, address: int) -> int:
    if 0xD000 <= address <= 0xDFFF and bank:
        try:
            return int(pyboy.memory[bank, address])
        except Exception:
            old_bank = int(pyboy.memory[0xFF70])
            pyboy.memory[0xFF70] = bank
            try:
                return int(pyboy.memory[address])
            finally:
                pyboy.memory[0xFF70] = old_bank
    return int(pyboy.memory[address])


def materialization_commands(
    *,
    reports: tuple[str, ...],
    scenarios: tuple[str, ...],
    scenario_ids: tuple[str, ...],
    rom_path: str,
    symbols_path: str,
    base_save_state: str,
    out_state: str,
) -> list[str]:
    base_args = ["--rom", rom_path, "--symbols", symbols_path]
    for report in reports[:4]:
        base_args.extend(["--report", report])
    for scenario in scenarios[:4]:
        base_args.extend(["--scenario", scenario])
    for scenario_id in scenario_ids[:8]:
        base_args.extend(["--scenario-id", scenario_id])
    if base_save_state:
        base_args.extend(["--base-save-state", base_save_state])
    else:
        base_args.extend(["--base-save-state", "<base-state>"])
    if out_state:
        base_args.extend(["--out-state", out_state])
    else:
        base_args.extend(["--out-state", ".local\\tmp\\debugger_content_positioned.state"])
    return unique_list(
        [
            "python -m tools.debugger content-state " + " ".join(cmd_arg(arg) for arg in base_args),
            "python -m tools.debugger content-state " + " ".join(cmd_arg(arg) for arg in [*base_args, "--execute"]),
        ]
    )


def map_name_for_precondition(*, values: dict[str, Any], scenario: dict[str, Any]) -> str:
    for raw in (
        values.get("map_label"),
        scenario.get("label"),
        values.get("label"),
    ):
        text = str(raw or "")
        for suffix in ("_MapEvents", "_MapScripts", "_MapBlocks"):
            if text.endswith(suffix):
                return text[: -len(suffix)]
        if text and not any(char in text for char in "/\\"):
            return text
    source_file = normalize_path(str(values.get("source_file") or scenario.get("source_file") or ""))
    if source_file.lower().startswith("maps/") and source_file.lower().endswith(".asm"):
        return Path(source_file).stem
    return ""


def parse_int(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    if text.startswith("$"):
        try:
            return int(text[1:], 16)
        except ValueError:
            return None
    try:
        return int(text, 0)
    except ValueError:
        return None


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple | set):
        return [nested for item in value for nested in string_items(item)]
    return [str(value)] if value else []


def cmd_arg(value: str) -> str:
    text = str(value)
    if not text:
        return '""'
    if any(char.isspace() for char in text):
        return '"' + text.replace('"', '\\"') + '"'
    return text
