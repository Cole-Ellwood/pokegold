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
    output_sink_ids,
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
MAP_PATCH_SYMBOLS = ("wMapGroup", "wMapNumber", "wXCoord", "wYCoord")
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
    errors.extend(map_errors)
    materializations: list[dict[str, Any]] = []
    for scenario in selected_scenarios:
        materializations.extend(
            materializations_for_scenario(
                scenario,
                map_index=map_index,
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


def materializations_for_scenario(
    scenario: dict[str, Any],
    *,
    map_index: dict[str, dict[str, Any]],
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
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    root: Path,
) -> dict[str, Any]:
    values = precondition.get("values") if isinstance(precondition.get("values"), dict) else {}
    map_name = map_name_for_precondition(values=values, scenario=scenario)
    map_entry = map_index.get(map_name, {})
    errors = []
    if not map_name:
        errors.append("could not infer map name from precondition map_label/source_file")
    elif not map_entry:
        errors.append(f"map not found in data/maps/maps.asm: {map_name}")
    patch_values = {
        "wMapGroup": int(map_entry.get("map_group", 0)),
        "wMapNumber": int(map_entry.get("map_number", 0)),
        "wXCoord": parse_int(values.get("x")),
        "wYCoord": parse_int(values.get("y")),
    }
    patches = [
        patch_record(symbol, value, symbol_table=symbol_table, symbols_path=symbols_path, root=root)
        for symbol, value in patch_values.items()
        if value is not None
    ]
    errors.extend(error for patch in patches for error in patch.get("errors", []))
    return {
        "scenario_id": scenario_id,
        "scenario_type": str(scenario.get("scenario_type", "")),
        "precondition_id": str(precondition.get("id", "")),
        "precondition_kind": "map_position",
        "status": "ready" if not errors and patches else "blocked",
        "source_file": normalize_path(str(scenario.get("source_file") or values.get("source_file") or "")),
        "map_name": map_name,
        "map_resolution": map_entry,
        "values": dict(values),
        "patch_count": len(patches),
        "patches": patches,
        "errors": errors,
        "commands": [
            f"python -m tools.debugger watch --watch-symbol {symbol} --execute --save-state <patched-state>"
            for symbol in MAP_PATCH_SYMBOLS
        ],
    }


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
            write_byte(pyboy, bank=int(patch["bank"]), address=int(patch["address"]), value=int(patch["value"]))
            observed = read_byte(pyboy, bank=int(patch["bank"]), address=int(patch["address"]))
            applied.append({**patch, "observed": observed, "observed_hex": f"{observed:02X}", "verified": observed == int(patch["value"])})
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
