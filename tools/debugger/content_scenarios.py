from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .content_mirror import (
    INCBIN_RE,
    code_after_label,
    first_token,
    parse_int_literal,
    parse_movement_blocks,
    parse_script_blocks,
    parse_text_blocks,
    split_label,
    strip_comment,
    unique_list,
)
from .provenance import display_path, resolve_path
from .workflow import command_address_arg, command_is_runnable


EVENT_MACROS = {"warp_event", "coord_event", "bg_event", "object_event"}
CHANNEL_COUNT_RE = re.compile(r"^channel_count\s+(?P<count>[$0-9A-Fa-fx]+)\b")
CHANNEL_RE = re.compile(r"^channel\s+(?P<channel>[$0-9A-Fa-fx]+)\s*,\s*(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)")
COORD_RE = re.compile(r"\b(?P<macro>hlcoord|decoord)\s+(?P<x>[^,\s]+)\s*,\s*(?P<y>[^,\s]+)(?:\s*,\s*(?P<target>[A-Za-z_.$][A-Za-z0-9_.$]*))?")
AUDIO_DATA_FILES = {"cries.asm", "drumkits.asm", "sfx.asm"}
AUDIO_COMMAND_TOKENS = {
    "duty_cycle",
    "duty_cycle_pattern",
    "drum_note",
    "drum_speed",
    "intensity",
    "new_noise",
    "noise_note",
    "note",
    "note_type",
    "octave",
    "pitch_offset",
    "pitch_slide",
    "rest",
    "sound_call",
    "sound_jump",
    "sound_loop",
    "sound_ret",
    "stereo_panning",
    "tempo",
    "tempo_relative",
    "toggle_noise",
    "toggle_perfect_pitch",
    "transpose",
    "vibrato",
    "volume",
    "volume_envelope",
}
MAP_STATE_WATCH_SYMBOLS = ("wMapGroup", "wMapNumber", "wXCoord", "wYCoord")
OBJECT_COUNTER_TILE_CANDIDATES = (
    ("up", "OW_UP", "wTileUp"),
    ("down", "OW_DOWN", "wTileDown"),
    ("left", "OW_LEFT", "wTileLeft"),
    ("right", "OW_RIGHT", "wTileRight"),
)
OBJECT_TIMEOFDAY_CANDIDATES = (
    ("morn", "MORN", "MORN_HOUR"),
    ("day", "DAY", "DAY_HOUR"),
    ("nite", "NITE", "NITE_HOUR"),
)
OBJECT_TIME_WATCH_SYMBOLS = ("wTimeOfDay", "hHours")
OBJECT_LARGE_TILE_CANDIDATES = (
    ("top_left", "OW_DOWN", 0, 0),
    ("top_right", "OW_DOWN", 1, 0),
    ("bottom_left", "OW_UP", 0, 1),
    ("bottom_right", "OW_UP", 1, 1),
    ("left_top", "OW_RIGHT", 0, 0),
    ("left_bottom", "OW_RIGHT", 0, 1),
    ("right_top", "OW_LEFT", 1, 0),
    ("right_bottom", "OW_LEFT", 1, 1),
)
OBJECT_LARGE_MOVEMENT_TOKENS = {
    "SPRITEMOVEDATA_BIGDOLLSYM",
    "SPRITEMOVEDATA_BIGDOLLASYM",
    "SPRITEMOVEDATA_BIGDOLL",
}
LARGE_OBJECT_COLLISION_MODEL = "WillObjectIntersectBigObject_fixed_2x2"
LARGE_OBJECT_SIZE_SOURCE = "engine/overworld/npc_movement.asm:WillObjectIntersectBigObject"
MOVEMENT_STATE_WATCH_SYMBOLS = (
    "wMovementObject",
    "wMovementDataBank",
    "wMovementDataAddress",
    "wMovementPointer",
    "wScriptMode",
)
SCRIPT_STATE_WATCH_SYMBOLS = (
    "wScriptBank",
    "wScriptPos",
    "wScriptRunning",
    "wScriptMode",
    "wScriptVar",
)
AUDIO_STATE_WATCH_SYMBOLS = (
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
SCENARIO_TRACE_HELPERS = {
    "map_warp": ("WarpCheck", "EnterMapWarp", "ReadMapEvents"),
    "map_coord_event": ("CheckCurrentMapCoordEvents", "CheckTileEvent", "CallScript"),
    "map_bg_event": ("CheckFacingBGEvent", "CheckBGEventFlag", "CallScript"),
    "map_object_event": ("TryObjectEvent", "CheckFacingObject", "CallScript"),
    "script_command_stream": ("ScriptEvents", "RunScriptCommand", "CallScript"),
    "text_block": ("PrintText", "PrintTextboxText", "PlaceString"),
    "movement_data": ("ApplyMovement", "GetMovementData", "HandleMovementData", "WaitScriptMovement"),
    "audio_channel_block": ("PlayMusic",),
    "audio_command_stream": ("_PlayMusic", "ParseMusic", "ParseMusicCommand"),
    "asset_materialization": ("Request2bpp", "Get1bpp", "Decompress"),
    "ui_tilemap_update": UI_TILEMAP_HELPERS,
}
PROOF_STATUS_PLANNED_ONLY = "planned_only"
PROOF_STATUS_READY_TO_RUN = "ready_to_run"
PROOF_STATUS_STATE_MATERIALIZED = "state_materialized"
PROOF_STATUS_EXECUTED = "executed"
PROOF_STATUS_OBSERVED = "observed"
PROOF_STATUS_PROGRESSION = (
    PROOF_STATUS_PLANNED_ONLY,
    PROOF_STATUS_READY_TO_RUN,
    PROOF_STATUS_STATE_MATERIALIZED,
    PROOF_STATUS_EXECUTED,
    PROOF_STATUS_OBSERVED,
)
EVENT_RUNTIME_ROUTE_KIND = "event_runtime_materialization"
EVENT_RUNTIME_ROUTE_KEY = "event_runtime_materialization"
EVENT_RUNTIME_ROUTE_LEGACY_KEY = "event_runtime_materialization_route"
RUNTIME_ROUTE_PROFILES = {
    "map_position": {
        "runtime_route": "overworld_event_engine",
        "expected_proof_status": "runtime_observed",
        "required_inputs": ("rom", "symbols", "base_save_state", "scenario_manifest"),
        "expected_proof_commands": (
            "python -m tools.debugger content-state --scenario <scenario_manifest> --scenario-id <scenario_id> --execute",
            "python -m tools.debugger replay --report <content_state_report> --scenario-id <scenario_id> --execute-watch",
            "python -m tools.debugger watch --save-state <patched-state> --execute",
        ),
    },
    "script_entry": {
        "runtime_route": "script_engine",
        "expected_proof_status": "instruction_observed",
        "required_inputs": ("rom", "symbols", "base_save_state", "scenario_manifest"),
        "evidence_kinds": ("instruction_trace", "watch"),
        "expected_proof_commands": (
            "python -m tools.debugger content-state --scenario <scenario_manifest> --scenario-id <scenario_id> --execute",
            "python -m tools.debugger trace-instructions --report <content_state_report> --scenario-id <scenario_id> --symbol RunScriptCommand --execute --require-hit",
        ),
    },
    "movement_entry": {
        "runtime_route": "movement_engine",
        "expected_proof_status": "instruction_observed",
        "required_inputs": ("rom", "symbols", "base_save_state", "scenario_manifest"),
        "evidence_kinds": ("instruction_trace", "watch"),
        "expected_proof_commands": (
            "python -m tools.debugger content-state --scenario <scenario_manifest> --scenario-id <scenario_id> --execute",
            "python -m tools.debugger trace-instructions --report <content_state_report> --scenario-id <scenario_id> --symbol ApplyMovement --execute --require-hit",
        ),
    },
    "audio_engine_entry": {
        "runtime_route": "audio_engine",
        "expected_proof_status": "runtime_observed",
        "required_inputs": ("rom", "symbols", "runtime_save_state", "scenario_manifest"),
        "expected_proof_commands": (
            "python -m tools.debugger trace-instructions --scenario <scenario_manifest> --scenario-id <scenario_id> --symbol PlayMusic --execute --require-hit",
            "python -m tools.debugger audio-snapshot --save-state <runtime-state>",
            "python -m tools.debugger dynamic-taint --report <audio_trace_report>",
        ),
    },
    "asset_loader_entry": {
        "runtime_route": "asset_loader",
        "expected_proof_status": "runtime_observed",
        "required_inputs": ("rom", "symbols", "runtime_save_state", "scenario_manifest"),
        "expected_proof_commands": (
            "python -m tools.debugger trace-instructions --scenario <scenario_manifest> --scenario-id <scenario_id> --symbol Request2bpp --execute --require-hit",
            "python -m tools.debugger dynamic-taint --report <asset_trace_report>",
        ),
    },
    "ui_output_sink": {
        "runtime_route": "ui_tilemap_engine",
        "expected_proof_status": "runtime_observed",
        "required_inputs": ("rom", "symbols", "runtime_save_state", "scenario_manifest"),
        "expected_proof_commands": (
            "python -m tools.debugger trace-instructions --scenario <scenario_manifest> --scenario-id <scenario_id> --symbol PlaceString --execute --require-hit",
            "python -m tools.debugger visual-snapshot --save-state <runtime-state>",
            "python -m tools.debugger dynamic-taint --report <ui_trace_report>",
        ),
    },
}


def build_content_scenario_report(
    *,
    source_files: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    out_scenarios: str = "",
    max_cases: int = 64,
    seed: int = 1,
    root: Path = ROOT,
) -> dict[str, Any]:
    limit = max(1, int(max_cases))
    requested = tuple(unique_list([*source_files, *changed_files]))
    scenarios = content_scenario_records(
        source_files=source_files,
        changed_files=changed_files,
        max_cases=limit,
        seed=seed,
        root=root,
    )
    scenario_manifest_path = (
        display_path(resolve_path(out_scenarios, root=root), root=root)
        if out_scenarios else "<content_scenarios.jsonl>"
    )
    scenarios = attach_behavioral_probes(
        scenarios=scenarios,
        scenario_manifest_path=scenario_manifest_path,
    )
    scenario_output = write_scenario_records(records=scenarios, out_scenarios=out_scenarios, root=root)
    errors = unique_list(scenario_output.get("errors", []))
    warnings = []
    if requested and not scenarios:
        warnings.append("no content scenarios were inferred from the requested source files")
    commands = unique_list(
        command
        for scenario in scenarios
        for command in scenario_commands_for_report(scenario)
    )
    behavioral_probe_count = sum(
        len(scenario.get("behavioral_probes", []))
        for scenario in scenarios
        if isinstance(scenario, dict)
    )
    runtime_probe_count = sum(
        int(bool((scenario.get("runtime_targets") or {}).get("trace_symbols")))
        + int(bool((scenario.get("runtime_targets") or {}).get("watch_symbols")))
        for scenario in scenarios
        if isinstance(scenario, dict)
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_content_scenarios",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "requested_source_files": list(source_files),
        "changed_files": list(changed_files),
        "seed": seed,
        "max_cases": limit,
        "source_file_count": len(requested),
        "scenario_count": len(scenarios),
        "behavioral_probe_count": behavioral_probe_count,
        "runtime_probe_count": runtime_probe_count,
        "scenarios": scenarios,
        "scenario_manifest": scenario_output,
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "Content scenarios are deterministic romhack interaction/materialization cases inferred from RGBDS source.",
            "Runtime targets and behavioral probes route each scenario to replay/setup, helper trace planning, map-state watch planning, expectation, coverage, mirror, provenance, and minimization commands, but they are not a dynamic emulator execution by themselves.",
        ],
    }


def content_scenario_records(
    *,
    source_files: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    max_cases: int = 64,
    seed: int = 1,
    root: Path = ROOT,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    requested = tuple(unique_list([*source_files, *changed_files]))
    for raw_path in requested:
        path = resolve_path(raw_path, root=root)
        if not path.exists() or path.is_dir():
            continue
        normalized = display_path(path, root=root)
        text = path.read_text(encoding="utf-8", errors="replace")
        records.extend(records_from_source(text, source_file=normalized, seed=seed, start_index=len(records), root=root))
        if len(records) >= max_cases:
            break
    return records[:max_cases]


def records_from_source(text: str, *, source_file: str, seed: int, start_index: int, root: Path = ROOT) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current_label = ""
    lines = text.splitlines()
    object_event_ordinal = 0
    for index, raw_line in enumerate(lines, start=1):
        clean = strip_comment(raw_line).strip()
        if not clean:
            continue
        label, code = split_label(clean)
        if label and not label.startswith("."):
            current_label = label
        token = first_token(code)
        if token == "def_object_events":
            object_event_ordinal = 0
            continue
        if token in EVENT_MACROS:
            fields = split_macro_args(code[len(token):])
            scenario = scenario_from_event(
                token,
                fields=fields,
                source_file=source_file,
                label=current_label,
                line=index,
                seed=seed,
                case_index=start_index + len(records),
                source_object_ordinal=object_event_ordinal if token == "object_event" else None,
                root=root,
            )
            if scenario:
                records.append(scenario)
            if token == "object_event":
                object_event_ordinal += 1
            continue
        if token == "channel_count":
            block = parse_channel_block(lines, index - 1)
            if block:
                records.append(
                    scenario_record(
                        scenario_type="audio_channel_block",
                        source_file=source_file,
                        label=current_label,
                        line=index,
                        seed=seed,
                        case_index=start_index + len(records),
                        trigger={
                            "channel_count": block["expected"],
                            "channels": block["channels"],
                        },
                        expected=[
                            f"channel_count={block['expected']}",
                            f"channel_declarations={len(block['channels'])}",
                        ],
                        root=root,
                    )
                )
            continue
        for match in INCBIN_RE.finditer(clean):
            asset_path = match.group("path")
            records.append(
                scenario_record(
                    scenario_type="asset_materialization",
                    source_file=source_file,
                    label=current_label,
                    line=index,
                    seed=seed,
                    case_index=start_index + len(records),
                    trigger={"asset": asset_path},
                    expected=[f"incbin_asset={asset_path}"],
                    root=root,
                )
            )
    records.extend(
        ui_tilemap_records(
            lines,
            source_file=source_file,
            seed=seed,
            start_index=start_index + len(records),
        )
    )
    if is_audio_data_source(source_file):
        records.extend(
            audio_command_stream_records(
                lines,
                source_file=source_file,
                seed=seed,
                start_index=start_index + len(records),
            )
        )
    if should_parse_script_blocks(source_file):
        for block in parse_script_blocks(lines):
            commands = [
                str(command.get("command", ""))
                for command in dict_items(block.get("commands"))
                if command.get("command")
            ]
            label = str(block.get("label", ""))
            if not label or not commands:
                continue
            records.append(
                scenario_record(
                    scenario_type="script_command_stream",
                    source_file=source_file,
                    label=label,
                    line=int(block.get("line", 0)),
                    seed=seed,
                    case_index=start_index + len(records),
                    trigger={
                        "script": label,
                        "command_count": len(commands),
                        "commands": commands[:16],
                    },
                    expected=[
                        f"script={label}",
                        f"command_count={len(commands)}",
                        *[f"script_command={name}" for name in commands[:6]],
                    ],
                    root=root,
                )
            )
    for block in parse_text_blocks(lines):
        commands = [
            str(command.get("command", ""))
            for command in dict_items(block.get("commands"))
            if command.get("command")
        ]
        label = str(block.get("label", ""))
        if not label or not commands:
            continue
        records.append(
            scenario_record(
                scenario_type="text_block",
                source_file=source_file,
                label=label,
                line=int(block.get("line", 0)),
                seed=seed,
                case_index=start_index + len(records),
                trigger={
                    "text": label,
                    "command_count": len(commands),
                    "commands": commands[:16],
                },
                expected=[
                    f"text={label}",
                    f"command_count={len(commands)}",
                    *[f"text_command={name}" for name in commands[:6]],
                ],
                root=root,
            )
        )
    for block in parse_movement_blocks(lines):
        commands = [
            str(command.get("command", ""))
            for command in dict_items(block.get("commands"))
            if command.get("command")
        ]
        label = str(block.get("label", ""))
        if not label or not commands:
            continue
        records.append(
            scenario_record(
                scenario_type="movement_data",
                source_file=source_file,
                label=label,
                line=int(block.get("line", 0)),
                seed=seed,
                case_index=start_index + len(records),
                trigger={
                    "movement": label,
                    "command_count": len(commands),
                    "commands": commands[:16],
                },
                expected=[
                    f"movement={label}",
                    f"command_count={len(commands)}",
                    *[f"movement_command={name}" for name in commands[:6]],
                ],
                root=root,
            )
        )
    return records


def should_parse_script_blocks(source_file: str) -> bool:
    parts = [part for part in source_file.replace("\\", "/").lower().split("/") if part]
    return "audio" not in parts


def is_audio_data_source(source_file: str) -> bool:
    parts = [part for part in source_file.replace("\\", "/").lower().split("/") if part]
    if len(parts) >= 3 and parts[-3] == "audio" and parts[-2] == "music":
        return True
    return len(parts) >= 2 and parts[-2] == "audio" and parts[-1] in AUDIO_DATA_FILES


def audio_command_stream_records(
    lines: list[str],
    *,
    source_file: str,
    seed: int,
    start_index: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for block in parse_script_blocks(lines):
        commands = [
            str(command.get("command", ""))
            for command in dict_items(block.get("commands"))
            if command.get("command")
        ]
        label = str(block.get("label", ""))
        if not label or not commands:
            continue
        if not is_audio_command_stream(commands):
            continue
        records.append(
            scenario_record(
                scenario_type="audio_command_stream",
                source_file=source_file,
                label=label,
                line=int(block.get("line", 0)),
                seed=seed,
                case_index=start_index + len(records),
                trigger={
                    "stream": label,
                    "command_count": len(commands),
                    "commands": commands[:16],
                },
                expected=[
                    f"audio_stream={label}",
                    f"command_count={len(commands)}",
                    *[f"audio_command={name}" for name in commands[:6]],
                ],
            )
        )
    return records


def is_audio_command_stream(commands: list[str]) -> bool:
    command_set = set(commands)
    if "channel_count" in command_set or "channel" in command_set:
        return False
    return any(command in AUDIO_COMMAND_TOKENS for command in commands)


def scenario_from_event(
    event_macro: str,
    *,
    fields: list[str],
    source_file: str,
    label: str,
    line: int,
    seed: int,
    case_index: int,
    source_object_ordinal: int | None = None,
    root: Path = ROOT,
) -> dict[str, Any] | None:
    if len(fields) < 2:
        return None
    x = fields[0]
    y = fields[1]
    if event_macro == "warp_event":
        trigger = {
            "x": x,
            "y": y,
            "destination_map": field_at(fields, 2),
            "destination_warp": field_at(fields, 3),
        }
        expected = [
            "event_macro=warp_event",
            f"destination_map={trigger['destination_map']}",
            f"destination_warp={trigger['destination_warp']}",
        ]
        return scenario_record(
            scenario_type="map_warp",
            source_file=source_file,
            label=label,
            line=line,
            seed=seed,
            case_index=case_index,
            trigger=trigger,
            expected=expected,
            root=root,
        )
    if event_macro == "coord_event":
        trigger = {
            "x": x,
            "y": y,
            "scene": field_at(fields, 2),
            "script": field_at(fields, 3),
        }
        return scenario_record(
            scenario_type="map_coord_event",
            source_file=source_file,
            label=label,
            line=line,
            seed=seed,
            case_index=case_index,
            trigger=trigger,
            expected=["event_macro=coord_event", f"scene={trigger['scene']}", f"script={trigger['script']}"],
            root=root,
        )
    if event_macro == "bg_event":
        trigger = {
            "x": x,
            "y": y,
            "event_type": field_at(fields, 2),
            "script": field_at(fields, 3),
        }
        return scenario_record(
            scenario_type="map_bg_event",
            source_file=source_file,
            label=label,
            line=line,
            seed=seed,
            case_index=case_index,
            trigger=trigger,
            expected=["event_macro=bg_event", f"event_type={trigger['event_type']}", f"script={trigger['script']}"],
            root=root,
        )
    if event_macro == "object_event":
        object_ordinal = int(source_object_ordinal or 0)
        map_object_index = object_ordinal + 2
        trigger = {
            "x": x,
            "y": y,
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
            "map_object_index": map_object_index,
        }
        return scenario_record(
            scenario_type="map_object_event",
            source_file=source_file,
            label=label,
            line=line,
            seed=seed,
            case_index=case_index,
            trigger=trigger,
            expected=[
                "event_macro=object_event",
                f"object_type={trigger['object_type']}",
                f"script={trigger['script']}",
                f"event_flag={trigger['event_flag']}",
            ],
            root=root,
        )
    return None


def ui_tilemap_records(
    lines: list[str],
    *,
    source_file: str,
    seed: int,
    start_index: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current_label = ""
    last_coord: dict[str, Any] = {}
    for index, raw_line in enumerate(lines, start=1):
        clean = strip_comment(raw_line).strip()
        if not clean:
            continue
        label, code = split_label(clean)
        if label and not label.startswith("."):
            current_label = label
        code = code_after_label(code)
        coord = parse_coord_macro(code)
        if coord:
            last_coord = {**coord, "line": index}
        helper = first_ui_tilemap_helper(code)
        if not helper:
            continue
        scenario_label = current_label or helper
        trigger = {
            "helper": helper,
            "coord": dict(last_coord),
            "output_symbols": list(UI_OUTPUT_WATCH_SYMBOLS),
        }
        if coord and not last_coord:
            trigger["coord"] = dict(coord)
        records.append(
            scenario_record(
                scenario_type="ui_tilemap_update",
                source_file=source_file,
                label=scenario_label,
                line=index,
                seed=seed,
                case_index=start_index + len(records),
                trigger=trigger,
                expected=[
                    "ui_output=wTilemap",
                    "ui_output=wAttrmap",
                    f"ui_helper={helper}",
                ],
            )
        )
    return records


def parse_coord_macro(code: str) -> dict[str, Any]:
    match = COORD_RE.search(code)
    if not match:
        return {}
    target = match.group("target") or ("wAttrmap" if match.group("macro") == "decoord" else "wTilemap")
    return {
        "macro": match.group("macro"),
        "x": match.group("x"),
        "y": match.group("y"),
        "target": target,
    }


def first_ui_tilemap_helper(code: str) -> str:
    for helper in UI_TILEMAP_HELPERS:
        if re.search(rf"\b{re.escape(helper)}\b", code):
            return helper
    return ""


def scenario_record(
    *,
    scenario_type: str,
    source_file: str,
    label: str,
    line: int,
    seed: int,
    case_index: int,
    trigger: dict[str, Any],
    expected: list[str],
    root: Path = ROOT,
) -> dict[str, Any]:
    scenario_id = f"content_scenario_{seed}_{case_index:04d}"
    trigger_preconditions = state_preconditions_for_scenario(
        scenario_id=scenario_id,
        scenario_type=scenario_type,
        source_file=source_file,
        label=label,
        trigger=trigger,
        root=root,
    )
    outputs = output_sinks_for_scenario(
        scenario_type=scenario_type,
        label=label,
        trigger=trigger,
    )
    return {
        "id": scenario_id,
        "kind": "unified_debugger_content_scenario",
        "family": "content_static",
        "surface": "content_static",
        "scenario_type": scenario_type,
        "proof_level": "semantic_source",
        "source": "tools.debugger.content_scenarios",
        "seed": seed,
        "case_index": case_index,
        "source_file": source_file,
        "label": label,
        "line": line,
        "trigger": trigger,
        "state_preconditions": trigger_preconditions,
        "outputs": outputs,
        "expected": expected,
        "changed_files": [source_file],
        "commands": scenario_commands(source_file=source_file, scenario_id=scenario_id),
        "behavioral_probes": [],
        "known_limits": [
            "Replay requires a save state or harness that can position the player, selected map, or asset loader at the scenario trigger.",
        ],
    }


def state_preconditions_for_scenario(
    *,
    scenario_id: str,
    scenario_type: str,
    source_file: str,
    label: str,
    trigger: dict[str, Any],
    root: Path = ROOT,
) -> list[dict[str, Any]]:
    if scenario_type.startswith("map_"):
        values = {
            "map_label": label,
            "source_file": source_file,
        }
        for key in (
            "x",
            "y",
            "scene",
            "event_type",
            "script",
            "sprite",
            "movement",
            "radius_x",
            "radius_y",
            "hour_1",
            "hour_2",
            "palette",
            "object_type",
            "sight_range",
            "event_flag",
            "source_object_ordinal",
            "map_object_index",
            "destination_map",
            "destination_warp",
        ):
            if trigger.get(key) not in {"", None}:
                values[key] = trigger[key]
        large_object = object_event_movement_is_large(trigger.get("movement"), root=root)
        if scenario_type == "map_object_event" and large_object:
            values["large_object"] = True
            values["large_object_width"] = 2
            values["large_object_height"] = 2
            values["large_object_collision_model"] = LARGE_OBJECT_COLLISION_MODEL
            values["large_object_size_source"] = LARGE_OBJECT_SIZE_SOURCE
        preconditions = [
            {
                "id": f"{scenario_type}_position",
                "surface": "content_static",
                "kind": "map_position",
                "status": "planned",
                "values": values,
                "watch_symbols": list(MAP_STATE_WATCH_SYMBOLS),
                "notes": [
                    "Load or synthesize an overworld state on the source map before firing the trigger.",
                    "Use wMapGroup/wMapNumber plus wXCoord/wYCoord watches to prove the positioned state and transition.",
                ],
            }
        ]
        if scenario_type == "map_object_event":
            for suffix, direction, tile_symbol in OBJECT_COUNTER_TILE_CANDIDATES:
                preconditions.append(
                    {
                        "id": f"{scenario_type}_counter_tile_{suffix}_position",
                        "surface": "content_static",
                        "kind": "map_position",
                        "status": "planned",
                        "values": {
                            **values,
                            "counter_tile": True,
                            "counter_facing_direction": direction,
                            "counter_tile_symbol": tile_symbol,
                            "counter_tile_collision": "COLL_COUNTER",
                        },
                        "watch_symbols": unique_list([*MAP_STATE_WATCH_SYMBOLS, tile_symbol]),
                        "notes": [
                            "Load or synthesize an overworld state two tiles from the object with the intervening facing tile marked as a counter collision.",
                            "Use wMapGroup/wMapNumber, player coordinate watches, and the facing-tile collision byte to prove the positioned counter interaction before tracing TryObjectEvent.",
                        ],
                    }
                )
            if large_object:
                for suffix, direction, surface_x, surface_y in OBJECT_LARGE_TILE_CANDIDATES:
                    preconditions.append(
                        {
                            "id": f"{scenario_type}_large_object_{suffix}_position",
                            "surface": "content_static",
                            "kind": "map_position",
                            "status": "planned",
                            "values": {
                                **values,
                                "large_object": True,
                                "large_object_facing_direction": direction,
                                "large_object_surface_x": surface_x,
                                "large_object_surface_y": surface_y,
                                "large_object_width": 2,
                                "large_object_height": 2,
                                "large_object_collision_model": LARGE_OBJECT_COLLISION_MODEL,
                                "large_object_size_source": LARGE_OBJECT_SIZE_SOURCE,
                            },
                            "watch_symbols": list(MAP_STATE_WATCH_SYMBOLS),
                            "notes": [
                                "Load or synthesize an overworld state outside the selected tile of a 2x2 object footprint.",
                                "Use player coordinate/facing watches plus the object-struct BIG_OBJECT palette bit to prove IsNPCAtCoord can use big-object intersection before tracing TryObjectEvent.",
                            ],
                        }
                    )
            for suffix, timeofday, hour_constant in object_event_timeofday_candidates(trigger):
                preconditions.append(
                    {
                        "id": f"{scenario_type}_timeofday_{suffix}_position",
                        "surface": "content_static",
                        "kind": "map_position",
                        "status": "planned",
                        "values": {
                            **values,
                            "selected_timeofday": timeofday,
                            "selected_hour": hour_constant,
                            "selected_time_context_source": "source_timeofday_mask_candidate",
                        },
                        "watch_symbols": unique_list([*MAP_STATE_WATCH_SYMBOLS, *OBJECT_TIME_WATCH_SYMBOLS]),
                        "notes": [
                            "Load or synthesize an overworld state with the selected time-of-day mask candidate before firing the trigger.",
                            "Use wTimeOfDay, hHours, map state, and object-loader watches to prove CheckObjectTime consumed this exact source-declared time context.",
                        ],
                    }
                )
        return attach_event_runtime_routes(preconditions, scenario_id=scenario_id, scenario_type=scenario_type)
    if scenario_type in {"audio_channel_block", "audio_command_stream"}:
        stream_value = trigger.get("stream", "")
        values = {
            "music_label": label,
            "source_file": source_file,
            "channel_count": trigger.get("channel_count", ""),
        }
        if stream_value:
            values["stream_label"] = stream_value
            values["command_count"] = trigger.get("command_count", "")
        preconditions = [
            {
                "id": "audio_channel_runtime",
                "surface": "content_static",
                "kind": "audio_engine_entry",
                "status": "planned",
                "values": values,
                "watch_symbols": list(AUDIO_STATE_WATCH_SYMBOLS),
                "outputs": output_sinks_for_scenario(
                    scenario_type=scenario_type,
                    label=label,
                    trigger=trigger,
                ),
                "notes": [
                    "Route PlayMusic, _PlayMusic, or the owning caller to this audio data before treating source checks as audio runtime proof.",
                ],
            }
        ]
        return attach_event_runtime_routes(preconditions, scenario_id=scenario_id, scenario_type=scenario_type)
    if scenario_type == "asset_materialization":
        preconditions = [
            {
                "id": "asset_loader_runtime",
                "surface": "content_static",
                "kind": "asset_loader_entry",
                "status": "planned",
                "values": {
                    "asset": trigger.get("asset", ""),
                    "source_file": source_file,
                    "label": label,
                },
                "watch_symbols": list(ASSET_REQUEST_WATCH_SYMBOLS),
                "outputs": output_sinks_for_scenario(
                    scenario_type=scenario_type,
                    label=label,
                    trigger=trigger,
                ),
                "notes": [
                    "Route the appropriate graphics/data loader to this INCBIN payload before treating the scenario as runtime materialized.",
                ],
            }
        ]
        return attach_event_runtime_routes(preconditions, scenario_id=scenario_id, scenario_type=scenario_type)
    if scenario_type == "ui_tilemap_update":
        preconditions = [
            {
                "id": "ui_tilemap_output",
                "surface": "content_static",
                "kind": "ui_output_sink",
                "status": "planned",
                "values": {
                    "ui_label": label,
                    "source_file": source_file,
                    "helper": trigger.get("helper", ""),
                    "coord": trigger.get("coord", {}),
                },
                "watch_symbols": list(UI_OUTPUT_WATCH_SYMBOLS),
                "outputs": output_sinks_for_scenario(
                    scenario_type=scenario_type,
                    label=label,
                    trigger=trigger,
                ),
                "notes": [
                    "Trace the selected UI helper and watch tilemap/attrmap output sinks before treating source checks as UI runtime proof.",
                ],
            }
        ]
        return attach_event_runtime_routes(preconditions, scenario_id=scenario_id, scenario_type=scenario_type)
    if scenario_type == "script_command_stream":
        preconditions = [
            {
                "id": "script_engine_entry",
                "surface": "content_static",
                "kind": "script_entry",
                "status": "planned",
                "values": {
                    "script_label": trigger.get("script", label),
                    "source_file": source_file,
                    "command_count": trigger.get("command_count", ""),
                },
                "watch_symbols": list(SCRIPT_STATE_WATCH_SYMBOLS),
                "notes": [
                    "Patch the script engine entry state so ScriptEvents starts reading from this script label.",
                    "Use RunScriptCommand instruction tracing plus wScriptPos/wScriptVar watches to prove semantic command execution.",
                ],
            }
        ]
        return attach_event_runtime_routes(preconditions, scenario_id=scenario_id, scenario_type=scenario_type)
    if scenario_type == "movement_data":
        preconditions = [
            {
                "id": "movement_engine_entry",
                "surface": "content_static",
                "kind": "movement_entry",
                "status": "planned",
                "values": {
                    "movement_label": trigger.get("movement", label),
                    "source_file": source_file,
                    "command_count": trigger.get("command_count", ""),
                    "object_id": 0,
                },
                "watch_symbols": list(MOVEMENT_STATE_WATCH_SYMBOLS),
                "notes": [
                    "Patch the movement engine pointer state so movement playback can read from this movement label.",
                    "Use ApplyMovement/GetMovementData/HandleMovementData tracing plus movement WRAM watches to prove command execution.",
                ],
            }
        ]
        return attach_event_runtime_routes(preconditions, scenario_id=scenario_id, scenario_type=scenario_type)
    return []


def object_event_movement_is_large(value: Any, *, root: Path = ROOT) -> bool:
    token = str(value or "").strip().upper()
    return bool(token) and token in large_object_movement_tokens(root=root)


def object_event_timeofday_candidates(trigger: dict[str, Any]) -> list[tuple[str, str, str]]:
    hour_1 = str(trigger.get("hour_1") or "").strip().upper()
    hour_2 = str(trigger.get("hour_2") or "").strip().upper()
    if hour_1 not in {"-1", "$FF", "255"} or not hour_2 or hour_2 in {"-1", "$FF", "255"}:
        return []
    tokens = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", hour_2))
    if "ANYTIME" in tokens:
        tokens.update({"MORN", "DAY", "NITE"})
    return [
        (suffix, timeofday, hour_constant)
        for suffix, timeofday, hour_constant in OBJECT_TIMEOFDAY_CANDIDATES
        if timeofday in tokens
    ]


def large_object_movement_tokens(*, root: Path = ROOT) -> set[str]:
    tokens = set(OBJECT_LARGE_MOVEMENT_TOKENS)
    path = resolve_path("data/sprites/map_objects.asm", root=root)
    if not path.exists():
        return tokens
    current = ""
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        comment_match = re.match(r"^\s*;\s*(SPRITEMOVEDATA_[A-Za-z0-9_]+)\b", raw)
        if comment_match:
            current = comment_match.group(1).upper()
            continue
        code = strip_comment(raw).strip()
        if current and code.startswith("db ") and "BIG_OBJECT" in code.upper():
            tokens.add(current)
    return tokens


def attach_event_runtime_routes(
    preconditions: list[dict[str, Any]],
    *,
    scenario_id: str,
    scenario_type: str,
) -> list[dict[str, Any]]:
    out = []
    for precondition in preconditions:
        row = dict(precondition)
        route = event_runtime_materialization_route(
            scenario_id=scenario_id,
            scenario_type=scenario_type,
            precondition_id=str(row.get("id", "")),
            precondition_kind=str(row.get("kind", "")),
            values=row.get("values") if isinstance(row.get("values"), dict) else {},
            watch_symbols=string_items(row.get("watch_symbols")),
            outputs=dict_items(row.get("outputs")),
        )
        row[EVENT_RUNTIME_ROUTE_KEY] = route
        row[EVENT_RUNTIME_ROUTE_LEGACY_KEY] = route
        out.append(row)
    return out


def event_runtime_materialization_route(
    *,
    scenario_id: str = "",
    scenario_type: str = "",
    precondition_kind: str,
    values: dict[str, Any] | None = None,
    watch_symbols: list[str] | tuple[str, ...] = (),
    outputs: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    precondition_id: str = "",
    source_file: str = "",
    actual_proof_status: str = PROOF_STATUS_PLANNED_ONLY,
    observed_sinks: list[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    profile = RUNTIME_ROUTE_PROFILES.get(precondition_kind, {})
    runtime_route = str(profile.get("runtime_route") or runtime_route_for_scenario(scenario_type))
    values = dict(values or {})
    watch_symbols = string_items(watch_symbols)
    outputs = dict_items(outputs)
    source_file = source_file or str(values.get("source_file", ""))
    expected_proof_status = str(profile.get("expected_proof_status") or "runtime_observed")
    evidence_kinds = tuple(profile.get("evidence_kinds", ()))
    if not evidence_kinds:
        evidence_kinds = ("instruction_trace", "watch") if expected_proof_status == "instruction_observed" else ("watch",)
    expected_sinks = unique_list([*watch_symbols, *output_sink_ids(outputs)])
    return {
        "kind": EVENT_RUNTIME_ROUTE_KIND,
        "schema_version": 1,
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "precondition_id": precondition_id,
        "precondition_kind": precondition_kind,
        "source_file": source_file,
        "runtime_route": runtime_route,
        "required_inputs": list(profile.get("required_inputs", ("rom", "symbols", "scenario_manifest"))),
        "state_preconditions": [
            {
                "id": precondition_id,
                "kind": precondition_kind,
                "watch_symbols": list(watch_symbols),
                "values": values,
            }
        ],
        "expected_proof_commands": build_runtime_proof_commands(
            scenario_id=scenario_id,
            source_file=source_file,
            precondition_kind=precondition_kind,
            watch_symbols=watch_symbols,
            trace_symbols=(),
        ),
        "expected_proof_status": expected_proof_status,
        "actual_proof_status": actual_proof_status,
        "expected_sinks": expected_sinks,
        "observed_sinks": string_items(observed_sinks),
        "evidence_kinds": list(evidence_kinds),
    }


def build_runtime_proof_commands(
    *,
    scenario_id: str,
    source_file: str,
    precondition_kind: str,
    watch_symbols: list[str] | tuple[str, ...],
    trace_symbols: list[str] | tuple[str, ...],
) -> list[str]:
    profile = RUNTIME_ROUTE_PROFILES.get(precondition_kind, {})
    commands = list(profile.get("expected_proof_commands", ()))
    if commands:
        return commands
    watch_arg = " ".join(f"--watch {symbol}" for symbol in unique_list(watch_symbols))
    trace_arg = " ".join(f"--symbol {symbol}" for symbol in unique_list(trace_symbols))
    source_arg = f" --source {source_file}" if source_file else ""
    scenario_arg = f" --scenario-id {scenario_id}" if scenario_id else ""
    return unique_list(
        [
            f"python -m tools.debugger content-state{source_arg}{scenario_arg} --execute".strip(),
            f"python -m tools.debugger trace-instructions{scenario_arg} {trace_arg} --execute --require-hit".strip(),
            f"python -m tools.debugger watch{scenario_arg} {watch_arg} --execute".strip(),
        ]
    )


def output_sink_ids(outputs: list[dict[str, Any]]) -> list[str]:
    return unique_list(
        str(output.get("state_symbol") or output.get("output_symbol") or output.get("address") or output.get("watch_address") or output.get("sink_address") or "")
        for output in outputs
        if output.get("state_symbol") or output.get("output_symbol") or output.get("address") or output.get("watch_address") or output.get("sink_address")
    )


def output_sinks_for_scenario(*, scenario_type: str, label: str, trigger: dict[str, Any]) -> list[dict[str, Any]]:
    if scenario_type in {"audio_channel_block", "audio_command_stream"}:
        producer_symbol = "ParseMusicCommand" if scenario_type == "audio_command_stream" else "PlayMusic"
        common = {
            "size": 1,
            "producer_symbol": producer_symbol,
            "source_function": label or producer_symbol,
            "channel_count": trigger.get("channel_count", ""),
            "stream": trigger.get("stream", ""),
        }
        return [
            {
                "kind": "audio_engine_output",
                "state_symbol": symbol,
                **common,
            }
            for symbol in AUDIO_STATE_WATCH_SYMBOLS
        ] + [
            {
                "kind": "audio_hardware_output",
                "address": address,
                "address_label": hardware_label,
                **common,
            }
            for hardware_label, address in AUDIO_HARDWARE_OUTPUTS
        ]
    if scenario_type == "asset_materialization":
        asset_path = str(trigger.get("asset") or "")
        producer_symbol = asset_output_producer(asset_path)
        return [
            {
                "kind": "asset_request_output",
                "state_symbol": symbol,
                "size": 1,
                "producer_symbol": producer_symbol,
                "source_function": label or producer_symbol,
                "asset": asset_path,
            }
            for symbol in ASSET_REQUEST_WATCH_SYMBOLS
        ]
    if scenario_type != "ui_tilemap_update":
        return []
    helper = str(trigger.get("helper") or "PlaceString")
    coord = trigger.get("coord") if isinstance(trigger.get("coord"), dict) else {}
    return [
        {
            "kind": "ui_tilemap_output",
            "state_symbol": "wTilemap",
            "size": 1,
            "producer_symbol": helper,
            "source_function": label or helper,
            "coord": dict(coord),
        },
        {
            "kind": "ui_attrmap_output",
            "state_symbol": "wAttrmap",
            "size": 1,
            "producer_symbol": helper,
            "source_function": label or helper,
            "coord": dict(coord),
        },
    ]


def asset_output_producer(asset_path: str) -> str:
    normalized = asset_path.lower()
    if ".1bpp" in normalized:
        return "Get1bpp"
    if ".2bpp" in normalized:
        return "Request2bpp"
    return "Decompress"


def attach_behavioral_probes(
    *,
    scenarios: list[dict[str, Any]],
    scenario_manifest_path: str,
) -> list[dict[str, Any]]:
    out = []
    for scenario in scenarios:
        row = dict(scenario)
        runtime_targets = runtime_targets_for_scenario(row)
        row["runtime_targets"] = runtime_targets
        row["related_symbols"] = runtime_targets["related_symbols"]
        row["behavioral_probes"] = behavioral_probe_plan(
            scenario=row,
            scenario_manifest_path=scenario_manifest_path,
        )
        row["behavioral_probe_count"] = len(row["behavioral_probes"])
        out.append(row)
    return out


def behavioral_probe_plan(*, scenario: dict[str, Any], scenario_manifest_path: str) -> list[dict[str, Any]]:
    scenario_id = str(scenario.get("id", ""))
    source_file = str(scenario.get("source_file", ""))
    runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
    trace_symbols = string_items(runtime_targets.get("trace_symbols"))[:4]
    watch_symbols = string_items(runtime_targets.get("watch_symbols"))[:4]
    script_symbols = string_items(runtime_targets.get("script_symbols"))[:4]
    probes = [
        behavioral_probe(
            probe_id="content_source_mirror",
            phase="mirror",
            proof_level="semantic_source",
            command=f"python -m tools.debugger content-mirror --source-file {source_file}",
            reason="Check source-level map/script/asset/audio invariants for the scenario source.",
        ),
        behavioral_probe(
            probe_id="content_replay_route",
            phase="replay",
            proof_level="runtime_planned",
            command=(
                "python -m tools.debugger replay "
                f"--scenario {scenario_manifest_path} --scenario-id {scenario_id} "
                f"--changed-file {source_file}"
            ),
            reason="Route the scenario through unified replay/setup so an available save state or materializer can prove it in ROM.",
        ),
        behavioral_probe(
            probe_id="content_coverage_route",
            phase="coverage",
            proof_level="evidence_index",
            command=f"python -m tools.debugger coverage --changed-file {source_file}",
            reason="Check whether trace/report evidence already covers the scenario source file.",
        ),
        behavioral_probe(
            probe_id="content_minimize_route",
            phase="minimize",
            proof_level="counterexample_planned",
            command=(
                "python -m tools.debugger minimize "
                f"--scenario {scenario_manifest_path} --scenario-id {scenario_id} "
                f"--changed-file {source_file}"
            ),
            reason="Reduce the scenario manifest to the selected interaction/materialization case.",
        ),
        behavioral_probe(
            probe_id="content_compare_route",
            phase="compare",
            proof_level="mirror_route",
            command=f"python -m tools.debugger compare --changed-file {source_file}",
            reason="Route the source to the strongest available mirror or expectation check.",
        ),
    ]
    runtime_args = runtime_replay_args(
        scenario_manifest_path=scenario_manifest_path,
        scenario_id=scenario_id,
        source_file=source_file,
        trace_symbols=trace_symbols,
        watch_symbols=watch_symbols,
    )
    if trace_symbols or watch_symbols:
        probes.append(
            behavioral_probe(
                probe_id="content_runtime_setup_route",
                phase="setup",
                proof_level="runtime_probe_planned",
                command="python -m tools.debugger setup " + " ".join(runtime_args),
                reason="Plan concrete runtime helper and map-state watch probes for this content scenario.",
            )
        )
        probes.append(
            behavioral_probe(
                probe_id="content_runtime_trace_route",
                phase="trace",
                proof_level="runtime_probe_planned",
                command="python -m tools.debugger replay " + " ".join([*runtime_args, "--frames", "600"]),
                reason="Route the scenario through replay with executable event-engine or loader helper symbols selected for tracing.",
            )
        )
    if scenario.get("state_preconditions"):
        state_report = f".local\\tmp\\debugger_content_state_{scenario_id}.json"
        state_path = f".local\\tmp\\debugger_content_state_{scenario_id}.state"
        probes.append(
            behavioral_probe(
                probe_id="content_state_materialization_route",
                phase="setup",
                proof_level="state_patch_planned",
                command=(
                    "python -m tools.debugger content-state "
                    f"--scenario {scenario_manifest_path} --scenario-id {scenario_id} "
                    f"--json-out {state_report}"
                ),
                reason="Resolve the scenario preconditions to concrete WRAM patch evidence.",
            )
        )
        probes.append(
            behavioral_probe(
                probe_id="content_state_execution_route",
                phase="setup",
                proof_level="positioned_state_dynamic_planned",
                command=(
                    "python -m tools.debugger content-state "
                    f"--scenario {scenario_manifest_path} --scenario-id {scenario_id} "
                    "--base-save-state <base_state> "
                    f"--out-state {state_path} --execute --json-out {state_report}"
                ),
                reason="Write a positioned PyBoy state for emulator-backed replay of this content scenario.",
            )
        )
        probes.append(
            behavioral_probe(
                probe_id="content_positioned_replay_route",
                phase="replay",
                proof_level="positioned_state_dynamic_planned",
                command=(
                    "python -m tools.debugger replay "
                    f"--report {state_report} --scenario {scenario_manifest_path} "
                    f"--scenario-id {scenario_id} --execute-watch"
                ),
                reason="Replay from the generated content-state report so WRAM patches, save state, watches, and source targets stay linked.",
            )
        )
        probes.append(
            behavioral_probe(
                probe_id="content_positioned_instruction_trace_route",
                phase="trace",
                proof_level="positioned_state_instruction_proof",
                command=content_state_instruction_trace_command(
                    state_report=state_report,
                    scenario_id=scenario_id,
                ),
                reason="Capture instruction-level helper evidence from the executed content-state report and its patched save state.",
            )
        )
        output_symbols = output_symbols_for_scenario(scenario)
        output_addresses = output_addresses_for_scenario(scenario)
        if output_symbols or output_addresses:
            sink_args = " ".join(
                [
                    *[f"--sink-symbol {symbol}" for symbol in output_symbols[:4]],
                    *[f"--sink-address {command_address_arg(address)}" for address in output_addresses[:4]],
                ]
            )
            probes.append(
                behavioral_probe(
                    probe_id="content_output_dynamic_taint_route",
                    phase="taint",
                    proof_level="output_sink_dynamic_planned",
                    command=f"python -m tools.debugger dynamic-taint --report {state_report} {sink_args}",
                    reason="Use the content-state output sink report to synthesize an instruction trace and attribute writes to declared content outputs.",
                )
            )
    if watch_symbols:
        watch_args = [
            "--scenario",
            scenario_manifest_path,
            "--scenario-id",
            scenario_id,
            "--changed-file",
            source_file,
            *[
                part
                for symbol in watch_symbols
                for part in ("--watch-symbol", symbol)
            ],
        ]
        probes.append(
            behavioral_probe(
                probe_id="content_runtime_watch_route",
                phase="watch",
                proof_level="runtime_probe_planned",
                command="python -m tools.debugger replay " + " ".join(watch_args),
                reason="Plan map-state watch evidence for the scenario trigger and resulting state transition.",
            )
        )
    if script_symbols:
        symbol_args = [
            part
            for symbol in script_symbols[:3]
            for part in ("--symbol", symbol)
        ]
        probes.append(
            behavioral_probe(
                probe_id="content_script_provenance",
                phase="provenance",
                proof_level="source_to_runtime_route",
                command="python -m tools.debugger provenance " + " ".join(symbol_args),
                reason="Map scenario script labels to source references before dynamic replay.",
            )
        )
    for index, expectation in enumerate(expectation_probes_for_scenario(scenario), 1):
        probes.append(
            behavioral_probe(
                probe_id=f"content_expectation_{index:02d}",
                phase="expect",
                proof_level="semantic_source",
                command=f"python -m tools.debugger expect --source-file {source_file} --expect {expectation}",
                reason="Assert a concrete source expectation derived from the scenario trigger.",
            )
        )
    return probes


def output_symbols_for_scenario(scenario: dict[str, Any]) -> list[str]:
    return unique_list(
        str(output.get("state_symbol") or output.get("output_symbol") or "")
        for output in dict_items(scenario.get("outputs"))
        if output.get("state_symbol") or output.get("output_symbol")
    )


def output_addresses_for_scenario(scenario: dict[str, Any]) -> list[str]:
    return unique_list(
        str(output.get("address") or output.get("watch_address") or output.get("sink_address") or "")
        for output in dict_items(scenario.get("outputs"))
        if output.get("address") or output.get("watch_address") or output.get("sink_address")
    )


def runtime_targets_for_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    scenario_type = str(scenario.get("scenario_type", ""))
    trigger = scenario.get("trigger") if isinstance(scenario.get("trigger"), dict) else {}
    source_symbols = [
        symbol
        for symbol in [str(scenario.get("label", ""))]
        if looks_like_runtime_symbol(symbol)
    ]
    script_symbols = scenario_script_symbols(scenario_type=scenario_type, trigger=trigger)
    trace_symbols = [
        symbol
        for symbol in SCENARIO_TRACE_HELPERS.get(scenario_type, ())
        if looks_like_runtime_symbol(symbol)
    ]
    if scenario_type == "audio_channel_block":
        trace_symbols.extend(
            symbol
            for channel in dict_items(trigger.get("channels"))
            for symbol in [str(channel.get("label", ""))]
            if looks_like_runtime_symbol(symbol)
        )
    if scenario_type == "text_block":
        script_symbols.extend(
            symbol
            for symbol in [str(trigger.get("text", ""))]
            if looks_like_script_symbol(symbol)
        )
    if scenario_type == "movement_data":
        script_symbols.extend(
            symbol
            for symbol in [str(trigger.get("movement", ""))]
            if looks_like_script_symbol(symbol)
        )
    if scenario_type.startswith("map_"):
        watch_symbols = list(MAP_STATE_WATCH_SYMBOLS)
    elif scenario_type in {"audio_channel_block", "audio_command_stream"}:
        watch_symbols = list(AUDIO_STATE_WATCH_SYMBOLS)
    elif scenario_type == "asset_materialization":
        watch_symbols = list(ASSET_REQUEST_WATCH_SYMBOLS)
    elif scenario_type == "ui_tilemap_update":
        watch_symbols = list(UI_OUTPUT_WATCH_SYMBOLS)
    elif scenario_type == "script_command_stream":
        watch_symbols = list(SCRIPT_STATE_WATCH_SYMBOLS)
    elif scenario_type == "movement_data":
        watch_symbols = list(MOVEMENT_STATE_WATCH_SYMBOLS)
    else:
        watch_symbols = []
    for precondition in dict_items(scenario.get("state_preconditions")):
        watch_symbols.extend(string_items(precondition.get("watch_symbols")))
    related_symbols = unique_list([*source_symbols, *script_symbols, *trace_symbols, *watch_symbols])
    return {
        "source_symbols": unique_list(source_symbols),
        "script_symbols": unique_list(script_symbols),
        "trace_symbols": unique_list(trace_symbols),
        "watch_symbols": unique_list(watch_symbols),
        "related_symbols": related_symbols,
        "requires_positioned_state": bool(scenario.get("state_preconditions")),
        "runtime_route": runtime_route_for_scenario(scenario_type),
    }


def scenario_script_symbols(*, scenario_type: str, trigger: dict[str, Any]) -> list[str]:
    keys = []
    if scenario_type in {"map_coord_event", "map_bg_event", "map_object_event"}:
        keys.append("script")
    if scenario_type == "script_command_stream":
        keys.append("script")
    if scenario_type == "text_block":
        keys.append("text")
    if scenario_type == "movement_data":
        keys.append("movement")
    if scenario_type == "map_object_event":
        keys.append("object_type")
    return unique_list(
        symbol
        for key in keys
        for symbol in [str(trigger.get(key, ""))]
        if looks_like_script_symbol(symbol)
    )


def runtime_route_for_scenario(scenario_type: str) -> str:
    if scenario_type.startswith("map_"):
        return "overworld_event_engine"
    if scenario_type in {"audio_channel_block", "audio_command_stream"}:
        return "audio_engine"
    if scenario_type == "asset_materialization":
        return "asset_loader"
    if scenario_type == "ui_tilemap_update":
        return "ui_tilemap_engine"
    if scenario_type == "script_command_stream":
        return "script_engine"
    if scenario_type == "text_block":
        return "text_engine"
    if scenario_type == "movement_data":
        return "movement_engine"
    return "content_runtime"


def runtime_replay_args(
    *,
    scenario_manifest_path: str,
    scenario_id: str,
    source_file: str,
    trace_symbols: list[str],
    watch_symbols: list[str],
) -> list[str]:
    args = [
        "--scenario",
        scenario_manifest_path,
        "--scenario-id",
        scenario_id,
        "--changed-file",
        source_file,
    ]
    for symbol in trace_symbols:
        args.extend(["--symbol", symbol])
    for symbol in watch_symbols:
        args.extend(["--watch-symbol", symbol])
    return args


def content_state_instruction_trace_command(*, state_report: str, scenario_id: str) -> str:
    trace_path = f".local\\tmp\\debugger_content_trace_{scenario_id}.jsonl"
    args = [
        "--report",
        state_report,
        "--scenario-id",
        scenario_id,
        "--frames",
        "600",
        "--execute",
        "--require-hit",
        "--out-trace",
        trace_path,
    ]
    return "python -m tools.debugger trace-instructions " + " ".join(args)


def looks_like_script_symbol(value: str) -> bool:
    text = value.strip()
    if not looks_like_runtime_symbol(text):
        return False
    if text.isupper():
        return False
    if text in {"ObjectEvent"}:
        return True
    return any(char.islower() for char in text)


def looks_like_runtime_symbol(value: str) -> bool:
    text = value.strip()
    if not text or "/" in text or "\\" in text:
        return False
    if text.startswith(("$", "0x", "0X", ".", "-")):
        return False
    return text[0].isalpha() and all(char.isalnum() or char in {"_", "."} for char in text)


def string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple | set):
        return [nested for item in value for nested in string_items(item)]
    return [str(value)] if value else []


def dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]


def behavioral_probe(
    *,
    probe_id: str,
    phase: str,
    proof_level: str,
    command: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "id": probe_id,
        "phase": phase,
        "proof_level": proof_level,
        "command": command,
        "reason": reason,
        "runnable": command_is_runnable(command),
    }


def expectation_probes_for_scenario(scenario: dict[str, Any]) -> list[str]:
    probes = []
    for expected in scenario.get("expected", []):
        text = str(expected)
        if "=" not in text:
            continue
        _key, value = text.split("=", 1)
        value = value.strip()
        if not value:
            continue
        if value.isdigit():
            continue
        probes.append(f"contains={value}")
    scenario_type = str(scenario.get("scenario_type", ""))
    if scenario_type == "audio_channel_block":
        probes.append("contains=channel_count")
    if scenario_type == "audio_command_stream":
        probes.append("contains=audio_stream")
        probes.append("contains=audio_command")
    if scenario_type == "script_command_stream":
        probes.append("contains=script")
    if scenario_type == "text_block":
        probes.append("contains=text")
    if scenario_type == "movement_data":
        probes.append("contains=movement")
    if scenario_type == "ui_tilemap_update":
        probes.append("contains=wTilemap")
        probes.append("contains=hlcoord")
    return unique_list(probes)[:6]


def scenario_commands_for_report(scenario: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            *[str(command) for command in scenario.get("commands", [])],
            *[
                str(probe.get("command", ""))
                for probe in scenario.get("behavioral_probes", [])
                if isinstance(probe, dict)
            ],
        ]
    )


def scenario_commands(*, source_file: str, scenario_id: str) -> list[str]:
    return [
        f"python -m tools.debugger content-mirror --source-file {source_file}",
        f"python -m tools.debugger coverage --changed-file {source_file}",
        f"python -m tools.debugger replay --changed-file {source_file} --scenario-id {scenario_id}",
        f"python -m tools.debugger minimize --changed-file {source_file} --scenario-id {scenario_id}",
        f"python -m tools.debugger gate --changed-file {source_file}",
    ]


def parse_channel_block(lines: list[str], index: int) -> dict[str, Any] | None:
    clean = code_after_label(strip_comment(lines[index]).strip())
    match = CHANNEL_COUNT_RE.match(clean)
    if not match:
        return None
    expected = parse_int_literal(match.group("count"))
    channels = []
    for next_index in range(index + 1, len(lines)):
        next_clean = code_after_label(strip_comment(lines[next_index]).strip())
        if not next_clean:
            if channels:
                break
            continue
        channel_match = CHANNEL_RE.match(next_clean)
        if not channel_match:
            break
        channels.append(
            {
                "channel": parse_int_literal(channel_match.group("channel")),
                "label": channel_match.group("label"),
                "line": next_index + 1,
            }
        )
    return {"expected": expected, "channels": channels}


def split_macro_args(text: str) -> list[str]:
    fields = []
    current = []
    in_quote = False
    depth = 0
    for char in text.strip():
        if char == '"':
            in_quote = not in_quote
        elif not in_quote and char in "([{":
            depth += 1
        elif not in_quote and char in ")]}" and depth:
            depth -= 1
        if char == "," and not in_quote and depth == 0:
            fields.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        fields.append("".join(current).strip())
    return fields


def field_at(fields: list[str], index: int) -> str:
    return fields[index] if index < len(fields) else ""


def write_scenario_records(
    *,
    records: list[dict[str, Any]],
    out_scenarios: str,
    root: Path,
) -> dict[str, Any]:
    if not out_scenarios:
        return {"path": "", "written": False, "record_count": len(records), "errors": []}
    path = resolve_path(out_scenarios, root=root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
            encoding="utf-8",
            newline="\n",
        )
    except OSError as exc:
        return {
            "path": display_path(path, root=root),
            "written": False,
            "record_count": 0,
            "errors": [str(exc)],
        }
    return {
        "path": display_path(path, root=root),
        "written": True,
        "record_count": len(records),
        "errors": [],
    }
