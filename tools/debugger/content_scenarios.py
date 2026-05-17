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
from .workflow import command_is_runnable


EVENT_MACROS = {"warp_event", "coord_event", "bg_event", "object_event"}
CHANNEL_COUNT_RE = re.compile(r"^channel_count\s+(?P<count>[$0-9A-Fa-fx]+)\b")
CHANNEL_RE = re.compile(r"^channel\s+(?P<channel>[$0-9A-Fa-fx]+)\s*,\s*(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)")
MAP_STATE_WATCH_SYMBOLS = ("wMapGroup", "wMapNumber", "wXCoord", "wYCoord")
MOVEMENT_STATE_WATCH_SYMBOLS = (
    "wMovementObject",
    "wMovementDataBank",
    "wMovementDataAddress",
    "wMovementPointer",
    "wScriptMode",
)
AUDIO_STATE_WATCH_SYMBOLS = (
    "wMusicID",
    "wMusicBank",
    "wChannel1Flags1",
    "wChannel2Flags1",
    "wChannel3Flags1",
    "wChannel4Flags1",
)
ASSET_REQUEST_WATCH_SYMBOLS = (
    "wRequested2bppSource",
    "wRequested2bppDest",
    "wRequested2bppSize",
    "wRequested1bppSource",
    "wRequested1bppDest",
    "wRequested1bppSize",
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
    "asset_materialization": ("Request2bpp", "Get1bpp", "Decompress"),
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
        records.extend(records_from_source(text, source_file=normalized, seed=seed, start_index=len(records)))
        if len(records) >= max_cases:
            break
    return records[:max_cases]


def records_from_source(text: str, *, source_file: str, seed: int, start_index: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current_label = ""
    lines = text.splitlines()
    for index, raw_line in enumerate(lines, start=1):
        clean = strip_comment(raw_line).strip()
        if not clean:
            continue
        label, code = split_label(clean)
        if label and not label.startswith("."):
            current_label = label
        token = first_token(code)
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
            )
            if scenario:
                records.append(scenario)
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
                )
            )
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
            )
        )
    return records


def scenario_from_event(
    event_macro: str,
    *,
    fields: list[str],
    source_file: str,
    label: str,
    line: int,
    seed: int,
    case_index: int,
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
        )
    if event_macro == "object_event":
        trigger = {
            "x": x,
            "y": y,
            "sprite": field_at(fields, 2),
            "movement": field_at(fields, 3),
            "object_type": field_at(fields, 9),
            "script": field_at(fields, 11),
            "event_flag": field_at(fields, 12),
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
        )
    return None


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
) -> dict[str, Any]:
    scenario_id = f"content_scenario_{seed}_{case_index:04d}"
    trigger_preconditions = state_preconditions_for_scenario(
        scenario_type=scenario_type,
        source_file=source_file,
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
    scenario_type: str,
    source_file: str,
    label: str,
    trigger: dict[str, Any],
) -> list[dict[str, Any]]:
    if scenario_type.startswith("map_"):
        values = {
            "map_label": label,
            "source_file": source_file,
        }
        for key in ("x", "y", "scene", "event_type", "script", "object_type", "event_flag", "destination_map", "destination_warp"):
            if trigger.get(key) not in {"", None}:
                values[key] = trigger[key]
        return [
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
    if scenario_type == "audio_channel_block":
        return [
            {
                "id": "audio_channel_runtime",
                "surface": "content_static",
                "kind": "audio_engine_entry",
                "status": "planned",
                "values": {
                    "music_label": label,
                    "source_file": source_file,
                    "channel_count": trigger.get("channel_count", ""),
                },
                "watch_symbols": list(AUDIO_STATE_WATCH_SYMBOLS),
                "notes": [
                    "Route PlayMusic or the owning caller to this channel block before treating source checks as audio runtime proof.",
                ],
            }
        ]
    if scenario_type == "asset_materialization":
        return [
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
                "notes": [
                    "Route the appropriate graphics/data loader to this INCBIN payload before treating the scenario as runtime materialized.",
                ],
            }
        ]
    if scenario_type == "script_command_stream":
        return [
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
                "watch_symbols": ["wScriptBank", "wScriptPos", "wScriptRunning", "wScriptMode", "wScriptVar"],
                "notes": [
                    "Patch the script engine entry state so ScriptEvents starts reading from this script label.",
                    "Use RunScriptCommand instruction tracing plus wScriptPos/wScriptVar watches to prove semantic command execution.",
                ],
            }
        ]
    if scenario_type == "movement_data":
        return [
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
    return []


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
    elif scenario_type == "audio_channel_block":
        watch_symbols = list(AUDIO_STATE_WATCH_SYMBOLS)
    elif scenario_type == "asset_materialization":
        watch_symbols = list(ASSET_REQUEST_WATCH_SYMBOLS)
    elif scenario_type == "movement_data":
        watch_symbols = list(MOVEMENT_STATE_WATCH_SYMBOLS)
    else:
        watch_symbols = []
    related_symbols = unique_list([*source_symbols, *script_symbols, *trace_symbols, *watch_symbols])
    return {
        "source_symbols": unique_list(source_symbols),
        "script_symbols": unique_list(script_symbols),
        "trace_symbols": unique_list(trace_symbols),
        "watch_symbols": unique_list(watch_symbols),
        "related_symbols": related_symbols,
        "requires_positioned_state": scenario_type.startswith("map_"),
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
    if scenario_type == "audio_channel_block":
        return "audio_engine"
    if scenario_type == "asset_materialization":
        return "asset_loader"
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
    if scenario_type == "script_command_stream":
        probes.append("contains=script")
    if scenario_type == "text_block":
        probes.append("contains=text")
    if scenario_type == "movement_data":
        probes.append("contains=movement")
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
