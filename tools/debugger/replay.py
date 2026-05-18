from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import ROOT, triage_request
from .coverage import load_traces
from .ingest import ingest_artifacts, resolve_path
from .input_log import build_input_playback
from .localize import is_watchable_symbol, normalize_path
from .reporting import load_reports
from .runtime_watch import DEFAULT_ROM, DEFAULT_SYMBOLS, build_watch_report
from .setup_plan import build_setup_plan
from .workflow import command_address_arg, command_is_runnable


SYMBOL_KEYS = {
    "callsite_rule_symbol",
    "callsite_symbol",
    "full_symbol",
    "label",
    "parent_label",
    "pc_label",
    "pc_symbol",
    "query",
    "resolved",
    "source_symbol",
    "state_symbol",
    "symbol",
    "watch",
}
SOURCE_KEYS = {"path", "source_file"}
SCENARIO_KEYS = {"id", "scenario_id", "scenario_ids", "capture_id", "trace_id"}
ADDRESS_KEYS = {"related_addresses", "watch_addresses", "sink_addresses", "watch_address", "sink_address"}
SYMPTOM_SYMBOLS = {
    "damage": "wCurDamage",
    "hp": "wCurDamage",
    "boss": "BossAI_SelectMove",
    "ai": "BossAI_SelectMove",
    "score": "wEnemyAIMoveScores",
    "switch": "BossAI_SwitchOrTryItem",
    "bank": "hROMBank",
    "farcall": "hROMBank",
}
SOURCE_EXTENSIONS = {".asm", ".inc", ".py", ".md", ".txt"}
SYMBOL_STOPWORDS = {
    "ABI",
    "Battle",
    "Boss",
    "Changed",
    "Coverage",
    "General",
    "Minimization",
    "ROM",
    "Static",
    "Suspect",
    "Uncovered",
}


def build_replay_plan(
    *,
    rom_path: str = "",
    symbols_path: str = "",
    save_state: str = "",
    input_logs: tuple[str, ...] = (),
    traces: tuple[str, ...] = (),
    scenarios: tuple[str, ...] = (),
    scenario_ids: tuple[str, ...] = (),
    reports: tuple[str, ...] = (),
    watch_symbols: tuple[str, ...] = (),
    watch_addresses: tuple[str, ...] = (),
    watch_size: int = 1,
    symbols: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symptom: str = "",
    frames: int = 300,
    context_frames: int = 12,
    execute_watch: bool = False,
    execute_trace: bool = False,
    max_targets: int = 12,
    root: Path = ROOT,
) -> dict[str, Any]:
    effective_rom = rom_path or DEFAULT_ROM
    effective_symbols = symbols_path or DEFAULT_SYMBOLS
    requested_reports = reports
    loaded_reports, report_errors = load_reports(reports=requested_reports, root=root)
    minimized_state_patch_sources = minimized_state_patch_report_sources(
        loaded_reports,
        root=root,
    )
    effective_reports = tuple(
        unique_list(
            [
                *requested_reports,
                *[
                    source["out_report"]
                    for source in minimized_state_patch_sources
                    if source.get("exists")
                ],
            ]
        )
    )
    if effective_reports != requested_reports:
        loaded_reports, report_errors = load_reports(reports=effective_reports, root=root)
    minimized_input_sources = minimized_input_log_sources(loaded_reports)
    effective_input_logs = tuple(unique_list([*input_logs, *input_logs_from_sources(minimized_input_sources)]))
    input_playback = build_input_playback(effective_input_logs, root=root, max_events=0)
    initial_manifest = ingest_artifacts(
        roms=artifact_inputs(raw_input=rom_path, effective_input=effective_rom, root=root),
        symbols=artifact_inputs(raw_input=symbols_path, effective_input=effective_symbols, root=root),
        traces=traces,
        save_states=(save_state,) if save_state else (),
        input_logs=effective_input_logs,
        scenarios=scenarios,
        changed_files=changed_files,
        root=root,
    )
    loaded_traces, trace_errors = load_traces(traces=traces, root=root)
    effective_watch_size = replay_watch_size(
        requested=watch_size,
        loaded_reports=loaded_reports,
    )
    signals = collect_replay_signals(
        manifest=initial_manifest,
        loaded_reports=loaded_reports,
        loaded_traces=loaded_traces,
        scenario_ids=scenario_ids,
        watch_symbols=watch_symbols,
        watch_addresses=watch_addresses,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
    )
    targets = build_replay_targets(signals, max_targets=max_targets)
    setup_plan = build_setup_plan(
        rom_path=effective_rom,
        symbols_path=effective_symbols,
        save_state=save_state,
        reports=effective_reports,
        scenarios=scenarios,
        scenario_ids=tuple(targets["scenario_ids"] or scenario_ids),
        changed_files=changed_files,
        symbols=tuple(targets["symbols"] or symbols),
        watch_symbols=tuple(targets["watch_symbols"] or watch_symbols),
        watch_addresses=tuple(targets["watch_addresses"] or watch_addresses),
        watch_size=effective_watch_size,
        symptom=symptom,
        frames=frames,
        root=root,
    )
    effective_save_state, selected_save_state = replay_save_state(
        setup_plan=setup_plan,
        explicit_save_state=save_state,
    )
    manifest = ingest_artifacts(
        roms=artifact_inputs(raw_input=rom_path, effective_input=effective_rom, root=root),
        symbols=artifact_inputs(raw_input=symbols_path, effective_input=effective_symbols, root=root),
        traces=traces,
        save_states=(effective_save_state,) if effective_save_state else (),
        input_logs=effective_input_logs,
        scenarios=scenarios,
        changed_files=changed_files,
        root=root,
    )
    steps = build_replay_steps(
        effective_rom=effective_rom,
        effective_symbols=effective_symbols,
        save_state=effective_save_state,
        input_logs=effective_input_logs,
        traces=traces,
        scenarios=scenarios,
        reports=effective_reports,
        changed_files=changed_files,
        symptom=symptom,
        frames=frames,
        context_frames=context_frames,
        targets=targets,
        watch_size=effective_watch_size,
    )
    watch_report = None
    watch_errors: list[str] = []
    if execute_watch:
        if not targets["watch_symbols"] and not targets["watch_addresses"]:
            watch_errors.append("no watchable replay target was found")
        else:
            try:
                watch_report = build_watch_report(
                    watch_symbols=tuple(targets["watch_symbols"]),
                    watch_addresses=tuple(targets["watch_addresses"]),
                    watch_size=effective_watch_size,
                    rom_path=effective_rom,
                    symbols_path=effective_symbols,
                    save_state=effective_save_state,
                    input_logs=effective_input_logs,
                    frames=frames,
                    context_frames=context_frames,
                    execute=True,
                    root=root,
                )
                watch_errors.extend(watch_report.get("errors", []))
            except Exception as exc:  # PyBoy/runtime setup errors must become report data.
                watch_errors.append(f"watch execution failed: {exc}")
    instruction_trace_report = None
    trace_execution_errors: list[str] = []
    if execute_trace:
        try:
            from .instruction_trace import build_instruction_trace_report

            instruction_trace_report = build_instruction_trace_report(
                function_symbols=tuple(targets["symbols"] or symbols),
                watch_symbols=tuple(targets["watch_symbols"] or watch_symbols),
                watch_addresses=tuple(targets["watch_addresses"] or watch_addresses),
                watch_size=effective_watch_size,
                reports=effective_reports,
                scenario_ids=tuple(targets["scenario_ids"] or scenario_ids),
                changed_files=changed_files,
                symptom=symptom,
                rom_path=effective_rom,
                symbols_path=effective_symbols,
                save_state=effective_save_state,
                input_logs=effective_input_logs,
                frames=frames,
                execute=True,
                require_hit=True,
                out_trace=".local\\tmp\\debugger_replay_instruction_trace.jsonl",
                root=root,
            )
            trace_execution_errors.extend(instruction_trace_report.get("errors", []))
        except Exception as exc:
            trace_execution_errors.append(f"instruction trace execution failed: {exc}")

    errors = unique_list(
        [
            *manifest.get("errors", []),
            *artifact_errors(manifest),
            *input_playback.get("errors", []),
            *report_errors,
            *trace_errors,
            *setup_plan.get("errors", []),
            *watch_errors,
            *trace_execution_errors,
        ]
    )
    warnings = unique_list(
        [
            *artifact_warnings(manifest),
            *input_playback.get("warnings", []),
            *setup_plan.get("warnings", []),
            *([] if targets["watch_symbols"] or targets["watch_addresses"] else ["no watchable symbol or address target was selected"]),
        ]
    )
    minimized_confirmation = build_minimized_input_log_confirmation(
        sources=minimized_input_sources,
        input_logs=effective_input_logs,
        input_playback=input_playback,
        execute_watch=execute_watch,
        watch_report=watch_report,
        watch_errors=watch_errors,
        steps=steps,
        targets=targets,
    )
    minimized_state_patch_confirmation = build_minimized_state_patch_confirmation(
        sources=minimized_state_patch_sources,
        reports=effective_reports,
        effective_save_state=effective_save_state,
        execute_watch=execute_watch,
        watch_report=watch_report,
        watch_errors=watch_errors,
        steps=steps,
        targets=targets,
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_replay_plan",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "rom": effective_rom,
        "symbols_path": effective_symbols,
        "save_state": save_state,
        "effective_save_state": effective_save_state,
        "input_logs": list(effective_input_logs),
        "input_playback": input_playback,
        "minimized_input_log_confirmation": minimized_confirmation,
        "minimized_state_patch_confirmation": minimized_state_patch_confirmation,
        "black_box_replay": black_box_replay_summary(
            rom_path=effective_rom,
            save_state=effective_save_state,
            input_logs=effective_input_logs,
            input_playback=input_playback,
        ),
        "save_state_discovery": {
            "selected": selected_save_state,
            "candidate_count": setup_plan.get("save_state_discovery", {}).get("candidate_count", 0),
            "candidates": setup_plan.get("save_state_discovery", {}).get("candidates", [])[:20],
        },
        "frames": frames,
        "context_frames": context_frames,
        "watch_size": effective_watch_size,
        "executed_watch": execute_watch,
        "executed_trace": execute_trace,
        "input_scenario_ids": list(scenario_ids),
        "changed_files": [normalize_path(path) for path in changed_files],
        "artifact_manifest": manifest,
        "input_reports": [item["source"] for item in loaded_reports],
        "requested_reports": list(requested_reports),
        "effective_reports": list(effective_reports),
        "minimized_state_patch_report_sources": minimized_state_patch_sources,
        "input_traces": [item["source"] for item in loaded_traces],
        "setup_plan": setup_plan,
        "signal_count": len(signals),
        "signals": signals[:160],
        "watch_symbol_count": len(targets["watch_symbols"]),
        "watch_address_count": len(targets["watch_addresses"]),
        "symbol_count": len(targets["symbols"]),
        "source_file_count": len(targets["source_files"]),
        "scenario_id_count": len(targets["scenario_ids"]),
        "replay_targets": targets,
        "phase_count": len(steps),
        "phase_steps": steps,
        "commands": unique_list(step["command"] for phase in steps for step in phase["steps"]),
        "runnable_commands": unique_list(
            step["command"]
            for phase in steps
            for step in phase["steps"]
            if step["runnable"]
        ),
        "blocked_commands": unique_list(
            step["command"]
            for phase in steps
            for step in phase["steps"]
            if not step["runnable"]
        ),
        "watch_report": watch_report,
        "instruction_trace_report": instruction_trace_report,
        "known_limits": [
            "Replay planning is generic; exact semantic reducers still live in the focused subsystem tools.",
            "Replay now reuses setup save-state discovery when reports or scenarios name an existing concrete state.",
            "Generic execution can drive frame-sampled watch polling, deterministic supported text input-log playback, and dense instruction trace capture through PyBoy with bounded context windows; it is still not reverse execution or CPU hardware watchpoints.",
            "Input-log playback supports the debugger text format documented in the input_playback report; full movie-format timing metadata is still outside this generic replay planner.",
        ],
    }


def artifact_inputs(*, raw_input: str, effective_input: str, root: Path) -> tuple[str, ...]:
    if raw_input:
        return (raw_input,)
    if effective_input and resolve_path(effective_input, root=root).exists():
        return (effective_input,)
    return ()


def black_box_replay_summary(
    *,
    rom_path: str,
    save_state: str,
    input_logs: tuple[str, ...],
    input_playback: dict[str, Any],
) -> dict[str, Any]:
    ready = bool(rom_path and save_state and input_logs and input_playback.get("valid", True))
    return {
        "ready": ready,
        "rom": rom_path,
        "save_state": save_state,
        "input_logs": list(input_logs),
        "input_log_count": len(input_logs),
        "input_playback_valid": bool(input_playback.get("valid", True)),
        "input_frame_count": int(input_playback.get("input_frame_count", 0) or 0),
        "button_event_count": int(input_playback.get("button_event_count", 0) or 0),
        "playback_total_frames": int(input_playback.get("total_frames", 0) or 0),
        "proof_status": "planned_only",
        "known_limit": (
            "Input logs are parsed into deterministic PyBoy button playback for supported text logs; "
            "runtime proof still requires executing watch/trace/mirror routes."
        ),
    }


def replay_watch_size(*, requested: int, loaded_reports: list[dict[str, Any]]) -> int:
    sizes = [positive_int(requested)]
    for loaded in loaded_reports:
        sizes.extend(report_watch_sizes(loaded.get("data", {})))
    return max([size for size in sizes if size > 0] or [1])


def report_watch_sizes(data: Any) -> list[int]:
    sizes: list[int] = []
    if isinstance(data, dict):
        for key in ("watch_size", "sink_size"):
            size = positive_int(data.get(key))
            if size:
                sizes.append(size)
        if watch_like_record(data):
            size = positive_int(data.get("size"))
            if size:
                sizes.append(size)
        for value in data.values():
            sizes.extend(report_watch_sizes(value))
    elif isinstance(data, list):
        for item in data:
            sizes.extend(report_watch_sizes(item))
    return sizes


def watch_like_record(data: dict[str, Any]) -> bool:
    if data.get("address_watch"):
        return True
    return any(key in data for key in ("watch", "watch_address", "sink_address", "raw")) and any(
        key in data for key in ("address", "bank_address", "size")
    )


def positive_int(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return number if number > 0 else 0


def replay_save_state(
    *,
    setup_plan: dict[str, Any],
    explicit_save_state: str,
) -> tuple[str, dict[str, Any]]:
    discovery = setup_plan.get("save_state_discovery", {})
    selected = discovery.get("selected", {}) if isinstance(discovery, dict) else {}
    if not isinstance(selected, dict):
        selected = {}
    if explicit_save_state:
        return explicit_save_state, selected
    if selected.get("exists") and selected.get("path"):
        return str(selected["path"]), selected
    return "", selected


def input_logs_from_reports(loaded_reports: list[dict[str, Any]]) -> list[str]:
    return input_logs_from_sources(minimized_input_log_sources(loaded_reports))


def input_logs_from_sources(sources: list[dict[str, Any]]) -> list[str]:
    return unique_list(source.get("out_input_log", "") for source in sources)


def minimized_state_patch_report_sources(
    loaded_reports: list[dict[str, Any]],
    *,
    root: Path,
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for loaded in loaded_reports:
        data = loaded.get("data") if isinstance(loaded, dict) else {}
        if not isinstance(data, dict):
            continue
        state_patch_minimization = data.get("state_patch_minimization")
        if not isinstance(state_patch_minimization, dict):
            continue
        if not (
            state_patch_minimization.get("attempted")
            and state_patch_minimization.get("preserved")
        ):
            continue
        raw_out_report = str(state_patch_minimization.get("out_report") or "").strip()
        if not raw_out_report:
            continue
        resolved = resolve_path(raw_out_report, root=root)
        sources.append(
            {
                "source_report": str(loaded.get("source") or ""),
                "out_report": normalize_path(raw_out_report),
                "exists": resolved.exists(),
                "written": bool(state_patch_minimization.get("written")),
                "original_patch_count": positive_int(state_patch_minimization.get("original_patch_count")),
                "minimized_patch_count": positive_int(state_patch_minimization.get("minimized_patch_count")),
                "removed_patch_count": positive_int(state_patch_minimization.get("removed_patch_count")),
                "watch_symbols": state_patch_confirmation_symbols(state_patch_minimization),
                "watch_addresses": state_patch_confirmation_addresses(state_patch_minimization),
                "watch_size": positive_int(state_patch_minimization.get("watch_size")),
                "source_mems": unique_list(
                    [
                        *string_items(state_patch_minimization.get("source_mems")),
                        *[
                            source_mem
                            for result in dict_items(state_patch_minimization.get("results"))
                            for source_mem in string_items(result.get("source_mems"))
                        ],
                    ]
                ),
                "commands": string_items(state_patch_minimization.get("commands"))[:8],
            }
        )
    return sources


def state_patch_confirmation_symbols(state_patch_minimization: dict[str, Any]) -> list[str]:
    symbols = [
        *string_items(state_patch_minimization.get("watch_symbols")),
        *string_items(state_patch_minimization.get("symbols")),
        *string_items(state_patch_minimization.get("source_symbols")),
    ]
    for result in dict_items(state_patch_minimization.get("results")):
        symbols.extend(string_items(result.get("semantic_watch_symbols")))
        symbols.extend(string_items(result.get("semantic_replay_watch_symbols")))
    return unique_list(symbols)


def state_patch_confirmation_addresses(state_patch_minimization: dict[str, Any]) -> list[str]:
    addresses = [
        *string_items(state_patch_minimization.get("watch_addresses")),
    ]
    for result in dict_items(state_patch_minimization.get("results")):
        addresses.extend(string_items(result.get("semantic_watch_addresses")))
        addresses.extend(string_items(result.get("semantic_replay_watch_addresses")))
    return unique_list(addresses)


def input_logs_from_data(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return []
    input_log_minimization = data.get("input_log_minimization")
    if not isinstance(input_log_minimization, dict):
        return []
    if not (
        input_log_minimization.get("attempted")
        and input_log_minimization.get("preserved")
        and input_log_minimization.get("written")
    ):
        return []
    out_input_log = str(input_log_minimization.get("out_input_log") or "")
    return [out_input_log] if out_input_log else []


def minimized_input_log_sources(loaded_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for loaded in loaded_reports:
        data = loaded.get("data") if isinstance(loaded, dict) else {}
        if not isinstance(data, dict):
            continue
        input_log_minimization = data.get("input_log_minimization")
        if not isinstance(input_log_minimization, dict):
            continue
        if not (
            input_log_minimization.get("attempted")
            and input_log_minimization.get("preserved")
            and input_log_minimization.get("written")
        ):
            continue
        out_input_log = str(input_log_minimization.get("out_input_log") or "")
        if not out_input_log:
            continue
        sources.append(
            {
                "source_report": str(loaded.get("source") or ""),
                "out_input_log": out_input_log,
                "button_sample": unique_list(string_items(input_log_minimization.get("button_sample")))[:12],
                "original_event_count": positive_int(input_log_minimization.get("original_event_count")),
                "minimized_event_count": positive_int(input_log_minimization.get("minimized_event_count")),
                "removed_event_count": positive_int(input_log_minimization.get("removed_event_count")),
                "commands": string_items(input_log_minimization.get("commands"))[:8],
            }
        )
    return sources


def build_minimized_state_patch_confirmation(
    *,
    sources: list[dict[str, Any]],
    reports: tuple[str, ...],
    effective_save_state: str,
    execute_watch: bool,
    watch_report: dict[str, Any] | None,
    watch_errors: list[str],
    steps: list[dict[str, Any]],
    targets: dict[str, Any],
) -> dict[str, Any]:
    source_reports = unique_list(source.get("source_report", "") for source in sources)
    out_reports = unique_list(source.get("out_report", "") for source in sources)
    existing_out_reports = unique_list(
        source.get("out_report", "")
        for source in sources
        if source.get("exists") and source.get("out_report") in reports
    )
    missing_out_reports = unique_list(
        source.get("out_report", "")
        for source in sources
        if not source.get("exists")
    )
    watch_data = watch_report if isinstance(watch_report, dict) else {}
    watch_hit_count = positive_int(watch_data.get("hit_count"))
    if not watch_hit_count:
        watch_hit_count = len(watch_events(watch_data))
    watch_executed = bool(execute_watch and watch_data.get("executed"))
    watch_valid = bool(watch_data.get("valid", True)) if watch_data else False
    runtime_observed = bool(
        existing_out_reports
        and watch_executed
        and watch_valid
        and not watch_errors
        and watch_hit_count > 0
    )
    status = minimized_state_patch_confirmation_status(
        attempted=bool(sources),
        has_existing_report=bool(existing_out_reports),
        execute_watch=execute_watch,
        watch_executed=watch_executed,
        watch_valid=watch_valid,
        watch_hit_count=watch_hit_count,
        watch_errors=watch_errors,
    )
    proof_status = "runtime_observed" if runtime_observed else "planned_only"
    watch_symbols = unique_list(
        [
            *string_items(targets.get("watch_symbols")),
            *[
                symbol
                for source in sources
                for symbol in string_items(source.get("watch_symbols"))
            ],
        ]
    )
    watch_addresses = unique_list(
        [
            *string_items(targets.get("watch_addresses")),
            *[
                address
                for source in sources
                for address in string_items(source.get("watch_addresses"))
            ],
        ]
    )
    evidence = minimized_state_patch_confirmation_evidence(
        source_reports=source_reports,
        out_reports=out_reports,
        existing_out_reports=existing_out_reports,
        missing_out_reports=missing_out_reports,
        effective_save_state=effective_save_state,
        execute_watch=execute_watch,
        watch_executed=watch_executed,
        watch_valid=watch_valid,
        watch_hit_count=watch_hit_count,
        watch_errors=watch_errors,
    )
    return {
        "attempted": bool(sources),
        "status": status,
        "proof_status": proof_status,
        "source_count": len(sources),
        "source_reports": source_reports,
        "out_reports": out_reports,
        "existing_out_reports": existing_out_reports,
        "missing_out_reports": missing_out_reports,
        "effective_save_state": effective_save_state,
        "execute_watch_requested": bool(execute_watch),
        "executed": watch_executed,
        "watch_valid": watch_valid,
        "watch_hit_count": watch_hit_count,
        "watch_symbols": watch_symbols,
        "watch_addresses": watch_addresses,
        "watch_errors": list(watch_errors),
        "sources": sources[:20],
        "evidence": evidence,
        "commands": minimized_state_patch_confirmation_commands(steps, sources=sources)[:10],
    }


def minimized_state_patch_confirmation_status(
    *,
    attempted: bool,
    has_existing_report: bool,
    execute_watch: bool,
    watch_executed: bool,
    watch_valid: bool,
    watch_hit_count: int,
    watch_errors: list[str],
) -> str:
    if not attempted:
        return "not_applicable"
    if not has_existing_report:
        return "minimized_report_missing"
    if watch_executed and watch_valid and not watch_errors and watch_hit_count > 0:
        return "runtime_watch_observed"
    if watch_errors:
        return "runtime_watch_failed"
    if watch_executed:
        return "runtime_watch_no_hit"
    if execute_watch:
        return "runtime_watch_not_executed"
    return "runtime_confirmation_planned"


def minimized_state_patch_confirmation_evidence(
    *,
    source_reports: list[str],
    out_reports: list[str],
    existing_out_reports: list[str],
    missing_out_reports: list[str],
    effective_save_state: str,
    execute_watch: bool,
    watch_executed: bool,
    watch_valid: bool,
    watch_hit_count: int,
    watch_errors: list[str],
) -> list[str]:
    return unique_list(
        [
            f"minimized_state_reports={','.join(out_reports)}" if out_reports else "",
            f"existing_minimized_state_reports={','.join(existing_out_reports)}" if existing_out_reports else "",
            f"missing_minimized_state_reports={','.join(missing_out_reports)}" if missing_out_reports else "",
            f"source_reports={','.join(source_reports)}" if source_reports else "",
            f"effective_save_state={effective_save_state}" if effective_save_state else "",
            f"execute_watch={bool(execute_watch)}",
            f"watch_executed={watch_executed}" if execute_watch or watch_executed else "",
            f"watch_valid={watch_valid}" if execute_watch or watch_executed else "",
            f"watch_hit_count={watch_hit_count}",
            *watch_errors[:4],
        ]
    )


def minimized_state_patch_confirmation_commands(
    steps: list[dict[str, Any]],
    *,
    sources: list[dict[str, Any]],
) -> list[str]:
    commands: list[str] = []
    for phase in dict_items(steps):
        for step in dict_items(phase.get("steps")):
            command = str(step.get("command") or "")
            if "tools.debugger watch" in command or "tools.debugger replay" in command:
                commands.append(command)
    for source in sources:
        commands.extend(string_items(source.get("commands")))
        out_report = str(source.get("out_report") or "")
        if out_report:
            commands.append(f"python -m tools.debugger replay --report {out_report} --execute-watch")
    return unique_list(commands)


def build_minimized_input_log_confirmation(
    *,
    sources: list[dict[str, Any]],
    input_logs: tuple[str, ...],
    input_playback: dict[str, Any],
    execute_watch: bool,
    watch_report: dict[str, Any] | None,
    watch_errors: list[str],
    steps: list[dict[str, Any]],
    targets: dict[str, Any],
) -> dict[str, Any]:
    source_reports = unique_list(source.get("source_report", "") for source in sources)
    source_input_logs = input_logs_from_sources(sources)
    used_input_logs = unique_list(input_log for input_log in source_input_logs if input_log in input_logs)
    button_sample = unique_list(
        [
            *string_items(input_playback.get("button_sample")),
            *[
                button
                for source in sources
                for button in string_items(source.get("button_sample"))
            ],
        ]
    )[:12]
    watch_data = watch_report if isinstance(watch_report, dict) else {}
    watch_hit_count = positive_int(watch_data.get("hit_count"))
    if not watch_hit_count:
        watch_hit_count = len(watch_events(watch_data))
    watch_executed = bool(execute_watch and watch_data.get("executed"))
    watch_valid = bool(watch_data.get("valid", True)) if watch_data else False
    runtime_observed = bool(watch_executed and watch_valid and not watch_errors and watch_hit_count > 0)
    status = minimized_input_log_confirmation_status(
        attempted=bool(sources),
        execute_watch=execute_watch,
        watch_executed=watch_executed,
        watch_valid=watch_valid,
        watch_hit_count=watch_hit_count,
        watch_errors=watch_errors,
    )
    proof_status = "runtime_observed" if runtime_observed else "planned_only"
    evidence = minimized_input_log_confirmation_evidence(
        source_reports=source_reports,
        input_logs=used_input_logs or source_input_logs,
        button_sample=button_sample,
        input_playback=input_playback,
        execute_watch=execute_watch,
        watch_executed=watch_executed,
        watch_valid=watch_valid,
        watch_hit_count=watch_hit_count,
        watch_errors=watch_errors,
    )
    return {
        "attempted": bool(sources),
        "status": status,
        "proof_status": proof_status,
        "source_count": len(sources),
        "source_reports": source_reports,
        "input_logs": used_input_logs or source_input_logs,
        "input_log_count": len(used_input_logs or source_input_logs),
        "input_playback_valid": bool(input_playback.get("valid", True)),
        "input_frame_count": positive_int(input_playback.get("input_frame_count")),
        "button_event_count": positive_int(input_playback.get("button_event_count")),
        "button_sample": button_sample,
        "execute_watch_requested": bool(execute_watch),
        "executed": watch_executed,
        "watch_valid": watch_valid,
        "watch_hit_count": watch_hit_count,
        "watch_symbols": list(targets.get("watch_symbols", [])),
        "watch_addresses": list(targets.get("watch_addresses", [])),
        "watch_errors": list(watch_errors),
        "sources": sources[:20],
        "evidence": evidence,
        "commands": minimized_input_log_confirmation_commands(steps, sources=sources)[:8],
    }


def minimized_input_log_confirmation_status(
    *,
    attempted: bool,
    execute_watch: bool,
    watch_executed: bool,
    watch_valid: bool,
    watch_hit_count: int,
    watch_errors: list[str],
) -> str:
    if not attempted:
        return "not_applicable"
    if watch_executed and watch_valid and not watch_errors and watch_hit_count > 0:
        return "runtime_watch_observed"
    if watch_errors:
        return "runtime_watch_failed"
    if watch_executed:
        return "runtime_watch_no_hit"
    if execute_watch:
        return "runtime_watch_not_executed"
    return "runtime_confirmation_planned"


def minimized_input_log_confirmation_evidence(
    *,
    source_reports: list[str],
    input_logs: list[str],
    button_sample: list[str],
    input_playback: dict[str, Any],
    execute_watch: bool,
    watch_executed: bool,
    watch_valid: bool,
    watch_hit_count: int,
    watch_errors: list[str],
) -> list[str]:
    return unique_list(
        [
            f"minimized_input_logs={','.join(input_logs)}" if input_logs else "",
            f"source_reports={','.join(source_reports)}" if source_reports else "",
            f"button_sample={','.join(button_sample)}" if button_sample else "",
            f"input_frame_count={positive_int(input_playback.get('input_frame_count'))}",
            f"button_event_count={positive_int(input_playback.get('button_event_count'))}",
            f"execute_watch={bool(execute_watch)}",
            f"watch_executed={watch_executed}" if execute_watch or watch_executed else "",
            f"watch_valid={watch_valid}" if execute_watch or watch_executed else "",
            f"watch_hit_count={watch_hit_count}",
            *watch_errors[:4],
        ]
    )


def watch_events(watch_report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        event
        for event in dict_items(watch_report.get("events"))
        if event.get("watch") or event.get("event_type") in {"watch_change", "watch_hit"}
    ]


def minimized_input_log_confirmation_commands(
    steps: list[dict[str, Any]],
    *,
    sources: list[dict[str, Any]],
) -> list[str]:
    commands: list[str] = []
    for phase in dict_items(steps):
        for step in dict_items(phase.get("steps")):
            command = str(step.get("command") or "")
            if "--input-log" in command and "tools.debugger watch" in command:
                commands.append(command)
    for source in sources:
        commands.extend(string_items(source.get("commands")))
    return unique_list(commands)


def collect_replay_signals(
    *,
    manifest: dict[str, Any],
    loaded_reports: list[dict[str, Any]],
    loaded_traces: list[dict[str, Any]],
    scenario_ids: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    watch_addresses: tuple[str, ...],
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for symbol in watch_symbols:
        signals.append(signal("explicit_watch", symbol=symbol, weight=100, source="input"))
    for address in watch_addresses:
        signals.append(signal("explicit_watch_address", address=address, weight=100, source="input"))
    for symbol in symbols:
        signals.append(signal("explicit_symbol", symbol=symbol, weight=85, source="input"))
    for scenario_id in scenario_ids:
        signals.append(signal("explicit_scenario", scenario_id=scenario_id, weight=90, source="input"))
    for path in changed_files:
        signals.append(signal("explicit_change", file=normalize_path(path), weight=80, source="input"))
    signals.extend(signals_from_symptom(symptom))
    for artifact in dict_items(manifest.get("artifacts")):
        signals.extend(signals_from_artifact(artifact))
    for loaded in loaded_reports:
        signals.extend(signals_from_data(loaded["data"], source=loaded["source"], base_weight=58))
    for loaded in loaded_traces:
        signals.extend(signals_from_data(loaded["data"], source=loaded["source"], base_weight=52))
    return merge_signals(signals)


def signals_from_artifact(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    kind = artifact.get("kind")
    path = str(artifact.get("path", ""))
    metadata = artifact.get("metadata") or {}
    if kind == "source_change" and path:
        out.append(signal("artifact_source_change", file=normalize_path(path), weight=72, source=path))
    if kind == "scenario":
        for scenario_id in string_items(metadata.get("ids_sample")):
            out.append(signal("artifact_scenario", scenario_id=scenario_id, weight=62, source=path))
    if kind == "trace":
        chosen = str(metadata.get("chosen", ""))
        if chosen:
            out.append(signal("artifact_trace_choice", note=f"chosen={chosen}", weight=35, source=path))
    return out


def signals_from_symptom(symptom: str) -> list[dict[str, Any]]:
    if not symptom:
        return []
    lowered = symptom.lower()
    out = [signal("symptom", note=symptom, weight=40, source="input")]
    for keyword, symbol_name in SYMPTOM_SYMBOLS.items():
        if keyword in lowered:
            out.append(signal("symptom_keyword", symbol=symbol_name, note=keyword, weight=55, source="input"))
    return out


def signals_from_data(data: Any, *, source: str, base_weight: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    walk_data_for_signals(data, source=source, base_weight=base_weight, out=out)
    return out


def walk_data_for_signals(data: Any, *, source: str, base_weight: int, out: list[dict[str, Any]]) -> None:
    if isinstance(data, dict):
        kind = str(data.get("kind", ""))
        if kind == "unified_debugger_watch_report":
            base_weight = max(base_weight, 76)
        if kind == "unified_debugger_impact_report":
            base_weight = max(base_weight, 70)
        if kind == "unified_debugger_content_mirror":
            out.extend(content_rom_mirror_signals(data, source=source, base_weight=max(base_weight, 86)))
        if kind == "unified_debugger_content_scenarios":
            out.extend(content_scenario_runtime_signals(data, source=source, base_weight=max(base_weight, 84)))
        if kind == "unified_debugger_fuzz_plan":
            out.extend(content_fuzz_runtime_signals(data, source=source, base_weight=max(base_weight, 82)))
        if kind == "unified_debugger_content_state_materialization":
            out.extend(content_state_materialization_signals(data, source=source, base_weight=max(base_weight, 88)))
        if kind == "unified_debugger_state_space":
            out.extend(state_space_signals(data, source=source, base_weight=max(base_weight, 88)))
        if kind == "unified_debugger_minimization_plan":
            out.extend(state_patch_minimization_signals(data, source=source, base_weight=max(base_weight, 90)))
            out.extend(input_log_minimization_signals(data, source=source, base_weight=max(base_weight, 88)))
        for key, value in data.items():
            lowered = str(key).lower()
            if lowered in SYMBOL_KEYS:
                for item in field_string_items(value):
                    if lowered in {"watch", "target"} and looks_like_address(item):
                        out.append(signal(f"report_{lowered}", address=item, weight=max(35, base_weight), source=source))
                    elif looks_like_symbol(item):
                        out.append(signal(f"report_{lowered}", symbol=item, weight=base_weight, source=source))
            elif lowered in SOURCE_KEYS:
                for item in field_string_items(value):
                    if looks_like_source_path(item):
                        out.append(signal(f"report_{lowered}", file=normalize_path(item), weight=base_weight, source=source))
            elif lowered in SCENARIO_KEYS:
                for item in field_string_items(value):
                    if lowered != "id" or is_scenario_record(data, item):
                        out.append(signal(f"report_{lowered}", scenario_id=item, weight=base_weight, source=source))
            elif lowered in {"related_symbols", "symbols"}:
                for item in string_items(value):
                    if looks_like_symbol(item):
                        out.append(signal(f"report_{lowered}", symbol=item, weight=max(30, base_weight - 8), source=source))
            elif lowered in {"related_files", "changed_files", "source_files"}:
                for item in string_items(value):
                    if looks_like_source_path(item):
                        out.append(signal(f"report_{lowered}", file=normalize_path(item), weight=max(30, base_weight - 8), source=source))
            elif lowered in ADDRESS_KEYS:
                for item in string_items(value):
                    if looks_like_address(item):
                        out.append(signal(f"report_{lowered}", address=item, weight=max(30, base_weight - 4), source=source))
            elif lowered in {"target", "address"}:
                for item in field_string_items(value):
                    if looks_like_address(item) and address_value_is_replay_target(data, lowered):
                        out.append(signal(f"report_{lowered}", address=item, weight=max(35, base_weight), source=source))
            walk_data_for_signals(value, source=source, base_weight=base_weight, out=out)
    elif isinstance(data, list):
        for item in data:
            walk_data_for_signals(item, source=source, base_weight=base_weight, out=out)


def content_rom_mirror_signals(data: dict[str, Any], *, source: str, base_weight: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for mirror in dict_items(data.get("rom_mirrors")):
        status = str(mirror.get("status", ""))
        if status not in {"passed", "failed"}:
            continue
        weight = base_weight if status == "passed" else min(100, base_weight + 10)
        note = str(mirror.get("title", mirror.get("id", "ROM mirror evidence")))
        source_file = normalize_path(str(mirror.get("source_file", "")))
        if source_file:
            out.append(signal("content_rom_mirror_file", file=source_file, note=note, weight=weight, source=source))
        for path in string_items(mirror.get("related_files")):
            if looks_like_source_path(path):
                out.append(signal("content_rom_mirror_related_file", file=path, note=note, weight=max(45, weight - 8), source=source))
        for symbol_name in string_items(mirror.get("related_symbols")):
            if looks_like_symbol(symbol_name):
                out.append(signal("content_rom_mirror_symbol", symbol=symbol_name, note=note, weight=weight, source=source))
    return out


def content_scenario_runtime_signals(data: dict[str, Any], *, source: str, base_weight: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for scenario in dict_items(data.get("scenarios")):
        out.extend(content_runtime_record_signals(scenario, source=source, base_weight=base_weight, prefix="content_scenario"))
    return out


def content_fuzz_runtime_signals(data: dict[str, Any], *, source: str, base_weight: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for campaign in dict_items(data.get("campaigns")):
        out.extend(content_fuzz_campaign_signals(campaign, source=source, base_weight=base_weight))
    for case in dict_items(data.get("fuzz_cases")):
        if not case.get("runtime_targets") and not case.get("scenario_type"):
            continue
        out.extend(content_runtime_record_signals(case, source=source, base_weight=base_weight, prefix="content_fuzz"))
    return out


def content_fuzz_campaign_signals(campaign: dict[str, Any], *, source: str, base_weight: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    note = str(campaign.get("id") or campaign.get("title") or "fuzz campaign")
    for symbol_name in string_items(campaign.get("related_symbols")):
        if looks_like_symbol(symbol_name):
            out.append(signal("content_fuzz_campaign_symbol", symbol=symbol_name, note=note, weight=min(100, base_weight + 10), source=source))
    for address in string_items(campaign.get("related_addresses")):
        if looks_like_address(address):
            out.append(signal("content_fuzz_campaign_address", address=address, note=note, weight=min(100, base_weight + 10), source=source))
    for path in string_items(campaign.get("changed_files")):
        if looks_like_source_path(path):
            out.append(signal("content_fuzz_campaign_file", file=normalize_path(path), note=note, weight=max(45, base_weight - 6), source=source))
    return out


def content_runtime_record_signals(
    record: dict[str, Any],
    *,
    source: str,
    base_weight: int,
    prefix: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    scenario_id = str(record.get("scenario_id") or record.get("id") or "")
    note = scenario_id or str(record.get("scenario_type", "content runtime"))
    source_file = normalize_path(str(record.get("source_file") or record.get("changed_file") or ""))
    if scenario_id:
        out.append(signal(f"{prefix}_id", scenario_id=scenario_id, note=note, weight=base_weight, source=source))
    if source_file:
        out.append(signal(f"{prefix}_file", file=source_file, note=note, weight=base_weight, source=source))
    runtime_targets = record.get("runtime_targets") if isinstance(record.get("runtime_targets"), dict) else {}
    for symbol_name in string_items(runtime_targets.get("watch_symbols")):
        if looks_like_symbol(symbol_name):
            out.append(signal(f"{prefix}_watch_symbol", symbol=symbol_name, note=note, weight=min(100, base_weight + 12), source=source))
    for symbol_name in string_items(runtime_targets.get("trace_symbols")):
        if looks_like_symbol(symbol_name):
            out.append(signal(f"{prefix}_trace_symbol", symbol=symbol_name, note=note, weight=min(100, base_weight + 6), source=source))
    for symbol_name in string_items(runtime_targets.get("script_symbols")):
        if looks_like_symbol(symbol_name):
            out.append(signal(f"{prefix}_script_symbol", symbol=symbol_name, note=note, weight=base_weight, source=source))
    for symbol_name in string_items(runtime_targets.get("source_symbols")):
        if looks_like_symbol(symbol_name):
            out.append(signal(f"{prefix}_source_symbol", symbol=symbol_name, note=note, weight=max(50, base_weight - 4), source=source))
    return out


def content_state_materialization_signals(data: dict[str, Any], *, source: str, base_weight: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    out_state = normalize_path(str(execution.get("out_state") or data.get("out_state") or ""))
    if out_state:
        out.append(signal("content_state_out_state", note=out_state, weight=max(45, base_weight - 20), source=source))
    for materialization in dict_items(data.get("materializations")):
        scenario_id = str(materialization.get("scenario_id", ""))
        source_file = normalize_path(str(materialization.get("source_file", "")))
        note = scenario_id or str(materialization.get("precondition_kind", "content state"))
        if scenario_id:
            out.append(signal("content_state_scenario", scenario_id=scenario_id, note=note, weight=base_weight, source=source))
        if source_file:
            out.append(signal("content_state_file", file=source_file, note=note, weight=base_weight, source=source))
        for patch in dict_items(materialization.get("patches")):
            symbol_name = str(patch.get("symbol", ""))
            if looks_like_symbol(symbol_name):
                out.append(
                    signal(
                        "content_state_patch_symbol",
                        symbol=symbol_name,
                        note=note,
                        weight=min(100, base_weight + 14),
                        source=source,
                    )
                )
    for patch in dict_items(execution.get("applied_patches")):
        symbol_name = str(patch.get("symbol", ""))
        if looks_like_symbol(symbol_name):
            out.append(
                signal(
                    "content_state_applied_patch_symbol",
                    symbol=symbol_name,
                    note=out_state or "applied content state patch",
                    weight=min(100, base_weight + 16),
                    source=source,
                )
            )
    return out


def state_space_signals(data: dict[str, Any], *, source: str, base_weight: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    out_state = normalize_path(str(execution.get("out_state") or data.get("out_state") or state_space.get("out_state") or ""))
    if out_state:
        out.append(signal("state_space_out_state", note=out_state, weight=max(45, base_weight - 20), source=source))
    for scenario_id in unique_list([str(data.get("scenario_id", "")), *string_items(state_space.get("scenario_ids"))]):
        if scenario_id:
            out.append(signal("state_space_scenario", scenario_id=scenario_id, note=scenario_id, weight=base_weight, source=source))
    for source_file in unique_list([*string_items(data.get("source_files")), *string_items(state_space.get("source_files"))]):
        if looks_like_source_path(source_file):
            out.append(signal("state_space_file", file=normalize_path(source_file), weight=base_weight, source=source))
    for symbol_name in unique_list([*string_items(data.get("watch_symbols")), *string_items(state_space.get("watch_symbols"))]):
        if looks_like_symbol(symbol_name):
            out.append(signal("state_space_watch_symbol", symbol=symbol_name, weight=min(100, base_weight + 12), source=source))
    for patch in state_space_patch_records(data):
        symbol_name = str(patch.get("base_symbol") or patch.get("symbol") or "")
        if looks_like_symbol(symbol_name):
            signal_type = "state_space_applied_patch_symbol" if patch.get("applied") else "state_space_patch_symbol"
            out.append(
                signal(
                    signal_type,
                    symbol=symbol_name,
                    note=str(patch.get("out_state") or out_state or "state-space patch"),
                    weight=min(100, base_weight + (16 if patch.get("applied") else 14)),
                    source=source,
                )
            )
        scenario_id = str(patch.get("scenario_id", ""))
        if scenario_id:
            out.append(signal("state_space_patch_scenario", scenario_id=scenario_id, weight=base_weight, source=source))
        source_file = normalize_path(str(patch.get("source_file", "")))
        if source_file:
            out.append(signal("state_space_patch_file", file=source_file, weight=base_weight, source=source))
    return out


def state_space_patch_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    return [
        *dict_items(data.get("state_patches")),
        *dict_items(state_space.get("patches")),
        *dict_items(state_space.get("state_patches")),
        *dict_items(execution.get("applied_patches")),
    ]


def state_patch_minimization_signals(data: dict[str, Any], *, source: str, base_weight: int) -> list[dict[str, Any]]:
    state_patch_minimization = data.get("state_patch_minimization")
    if not isinstance(state_patch_minimization, dict) or not state_patch_minimization.get("attempted"):
        return []
    out: list[dict[str, Any]] = []
    preserved = bool(state_patch_minimization.get("preserved"))
    weight = min(100, base_weight + 8) if preserved else base_weight
    note = (
        f"state patches {state_patch_minimization.get('original_patch_count', 0)}"
        f" -> {state_patch_minimization.get('minimized_patch_count', 0)}"
    )
    out_report = str(state_patch_minimization.get("out_report", ""))
    if out_report:
        out.append(signal("state_patch_minimized_report", note=out_report, weight=max(45, weight - 18), source=source))
    for scenario_id in string_items(state_patch_minimization.get("scenario_ids")):
        out.append(signal("state_patch_minimized_scenario", scenario_id=scenario_id, note=note, weight=weight, source=source))
    for path in string_items(state_patch_minimization.get("source_files")):
        if looks_like_source_path(path):
            out.append(signal("state_patch_minimized_file", file=normalize_path(path), note=note, weight=weight, source=source))
    for symbol_name in state_patch_minimization_related_symbols(state_patch_minimization):
        if looks_like_symbol(symbol_name):
            out.append(signal("state_patch_minimized_symbol", symbol=symbol_name, note=note, weight=weight, source=source))
    for address in state_patch_minimization_related_addresses(state_patch_minimization):
        if looks_like_address(address):
            out.append(signal("state_patch_minimized_address", address=address, note=note, weight=weight, source=source))
    return out


def input_log_minimization_signals(data: dict[str, Any], *, source: str, base_weight: int) -> list[dict[str, Any]]:
    input_log_minimization = data.get("input_log_minimization")
    if not isinstance(input_log_minimization, dict) or not input_log_minimization.get("attempted"):
        return []
    out: list[dict[str, Any]] = []
    preserved = bool(input_log_minimization.get("preserved"))
    weight = min(100, base_weight + 6) if preserved else base_weight
    out_input_log = normalize_path(str(input_log_minimization.get("out_input_log") or ""))
    if out_input_log and input_log_minimization.get("written"):
        out.append(signal("input_log_minimized_artifact", note=out_input_log, weight=weight, source=source))
    for button in string_items(input_log_minimization.get("button_sample")):
        out.append(signal("input_log_minimized_button", note=f"button={button}", weight=max(35, weight - 12), source=source))
    return out


def state_patch_minimization_related_symbols(item: dict[str, Any]) -> list[str]:
    symbols = [
        *string_items(item.get("symbols")),
        *string_items(item.get("source_symbols")),
        *string_items(item.get("watch_symbols")),
        *source_mem_origins(item),
    ]
    for result in dict_items(item.get("results")):
        symbols.extend(string_items(result.get("semantic_watch_symbols")))
        symbols.extend(string_items(result.get("semantic_replay_watch_symbols")))
        symbols.extend(source_mem_origins(result))
    return unique_list(symbols)


def state_patch_minimization_related_addresses(item: dict[str, Any]) -> list[str]:
    addresses = [
        *string_items(item.get("watch_addresses")),
        *source_mem_addresses(item),
    ]
    for result in dict_items(item.get("results")):
        addresses.extend(string_items(result.get("semantic_watch_addresses")))
        addresses.extend(string_items(result.get("semantic_replay_watch_addresses")))
        addresses.extend(source_mem_addresses(result))
    return unique_list(addresses)


def source_mem_origins(route: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            origin
            for _, origin in source_mem_parts(route)
            if origin
        ]
    )


def source_mem_addresses(route: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            address
            for address, _ in source_mem_parts(route)
            if address
        ]
    )


def source_mem_parts(route: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for value in string_items(route.get("source_mems")):
        text = str(value).strip()
        if not text:
            continue
        if "=" in text:
            address, origin = text.split("=", 1)
            out.append((address.strip(), origin.strip()))
        else:
            out.append((text, ""))
    return out


def build_replay_targets(signals: list[dict[str, Any]], *, max_targets: int) -> dict[str, Any]:
    symbol_scores: dict[str, int] = {}
    watch_scores: dict[str, int] = {}
    address_scores: dict[str, int] = {}
    file_scores: dict[str, int] = {}
    scenario_scores: dict[str, int] = {}
    for item in signals:
        weight = int(item["weight"])
        if item.get("symbol"):
            symbol = str(item["symbol"])
            if is_watchable_symbol(symbol):
                watch_scores[symbol] = watch_scores.get(symbol, 0) + weight
            else:
                symbol_scores[symbol] = symbol_scores.get(symbol, 0) + weight
        if item.get("address"):
            address = str(item["address"])
            address_scores[address] = address_scores.get(address, 0) + weight
        if item.get("file"):
            path = normalize_path(str(item["file"]))
            file_scores[path] = file_scores.get(path, 0) + weight
        if item.get("scenario_id"):
            scenario_id = str(item["scenario_id"])
            scenario_scores[scenario_id] = scenario_scores.get(scenario_id, 0) + weight
    symbols = top_keys(symbol_scores, max_targets)
    explicit_watch = [
        str(item["symbol"])
        for item in signals
        if item["type"] == "explicit_watch" and item.get("symbol")
    ]
    explicit_watch_addresses = [
        str(item["address"])
        for item in signals
        if item["type"] == "explicit_watch_address" and item.get("address")
    ]
    watch_symbols = unique_list(
        [
            *explicit_watch,
            *top_keys(watch_scores, max_targets),
            *[symbol for symbol in symbols if is_watchable_symbol(symbol)],
        ]
    )[:max_targets]
    watch_addresses = unique_list(
        [
            *explicit_watch_addresses,
            *top_keys(address_scores, max_targets),
        ]
    )[:max_targets]
    return {
        "watch_symbols": watch_symbols,
        "watch_addresses": watch_addresses,
        "symbols": symbols,
        "source_files": top_keys(file_scores, max_targets),
        "scenario_ids": top_keys(scenario_scores, max_targets),
        "symbol_scores": symbol_scores,
        "watch_symbol_scores": watch_scores,
        "watch_address_scores": address_scores,
        "source_file_scores": file_scores,
        "scenario_scores": scenario_scores,
    }


def build_replay_steps(
    *,
    effective_rom: str,
    effective_symbols: str,
    save_state: str,
    input_logs: tuple[str, ...],
    traces: tuple[str, ...],
    scenarios: tuple[str, ...],
    reports: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    frames: int,
    context_frames: int,
    targets: dict[str, Any],
    watch_size: int,
) -> list[dict[str, Any]]:
    phases: dict[str, list[dict[str, Any]]] = {
        "ingest": [],
        "setup": [],
        "reproduce": [],
        "localize": [],
        "prove": [],
        "verify": [],
    }
    add_ingest_step(phases, effective_rom, effective_symbols, save_state, input_logs, traces, scenarios, changed_files)
    add_setup_step(
        phases,
        effective_rom,
        effective_symbols,
        save_state,
        reports,
        scenarios,
        targets["scenario_ids"],
        changed_files,
        symptom,
        frames,
        targets["symbols"],
        targets["watch_symbols"],
    )
    add_watch_step(
        phases,
        effective_rom,
        effective_symbols,
        save_state,
        input_logs,
        frames,
        context_frames,
        targets["watch_symbols"],
        targets["watch_addresses"],
        watch_size,
    )
    add_instruction_trace_step(
        phases,
        effective_rom,
        effective_symbols,
        save_state,
        input_logs,
        reports,
        changed_files,
        symptom,
        frames,
        targets["symbols"],
        targets["watch_symbols"],
        targets["watch_addresses"],
        watch_size,
    )
    add_localize_step(phases, reports, targets["symbols"], targets["source_files"], symptom)
    add_coverage_step(phases, reports, traces, targets["symbols"], targets["source_files"])
    add_minimize_step(
        phases,
        reports,
        traces,
        scenarios,
        targets["symbols"],
        targets["watch_addresses"],
        targets["scenario_ids"],
        targets["source_files"],
        changed_files,
        symptom,
    )
    add_compare_step(phases, targets["symbols"], targets["source_files"], symptom)
    add_impact_step(phases, reports, targets["symbols"], targets["source_files"], symptom)
    add_report_step(phases, reports)
    add_gate_step(phases, changed_files, symptom)
    return [
        {"phase": phase, "title": phase_title(phase), "steps": unique_steps(steps)}
        for phase, steps in phases.items()
        if steps
    ]


def add_ingest_step(
    phases: dict[str, list[dict[str, Any]]],
    effective_rom: str,
    effective_symbols: str,
    save_state: str,
    input_logs: tuple[str, ...],
    traces: tuple[str, ...],
    scenarios: tuple[str, ...],
    changed_files: tuple[str, ...],
) -> None:
    args = [
        "--rom",
        cmd_arg(effective_rom),
        "--symbols",
        cmd_arg(effective_symbols),
    ]
    if save_state:
        args.extend(["--save-state", cmd_arg(save_state)])
    for input_log in input_logs:
        args.extend(["--input-log", cmd_arg(input_log)])
    for trace in traces:
        args.extend(["--trace", cmd_arg(trace)])
    for scenario in scenarios:
        args.extend(["--scenario", cmd_arg(scenario)])
    for path in changed_files:
        args.extend(["--changed-file", cmd_arg(path)])
    add_step(
        phases,
        "ingest",
        "python -m tools.debugger ingest " + " ".join(args),
        "Validate replay inputs and record hashes before trusting downstream evidence.",
    )


def add_setup_step(
    phases: dict[str, list[dict[str, Any]]],
    effective_rom: str,
    effective_symbols: str,
    save_state: str,
    reports: tuple[str, ...],
    scenarios: tuple[str, ...],
    scenario_ids: list[str],
    changed_files: tuple[str, ...],
    symptom: str,
    frames: int,
    symbols: list[str],
    watch_symbols: list[str],
) -> None:
    if not symbols and not watch_symbols and not reports and not scenarios and not changed_files and not symptom and not scenario_ids:
        return
    args = [
        "--rom",
        cmd_arg(effective_rom),
        "--symbols",
        cmd_arg(effective_symbols),
        "--frames",
        str(frames),
        "--out-scenarios",
        ".local\\tmp\\debugger_replay_setup_scenarios.jsonl",
    ]
    if save_state:
        args.extend(["--save-state", cmd_arg(save_state)])
    for report in reports[:4]:
        args.extend(["--report", cmd_arg(report)])
    for scenario in scenarios[:4]:
        args.extend(["--scenario", cmd_arg(scenario)])
    for scenario_id in scenario_ids[:8]:
        args.extend(["--scenario-id", cmd_arg(scenario_id)])
    for path in changed_files[:4]:
        args.extend(["--changed-file", cmd_arg(path)])
    if symptom:
        args.extend(["--symptom", cmd_arg(symptom)])
    for symbol in symbols[:6]:
        args.extend(["--symbol", cmd_arg(symbol)])
    for watch in watch_symbols[:6]:
        args.extend(["--watch-symbol", cmd_arg(watch)])
    add_step(
        phases,
        "setup",
        "python -m tools.debugger setup " + " ".join(args),
        "Plan the save-state, scenario, materialization, and trigger commands needed before runtime proof.",
    )


def add_watch_step(
    phases: dict[str, list[dict[str, Any]]],
    effective_rom: str,
    effective_symbols: str,
    save_state: str,
    input_logs: tuple[str, ...],
    frames: int,
    context_frames: int,
    watch_symbols: list[str],
    watch_addresses: list[str],
    watch_size: int,
) -> None:
    if not watch_symbols and not watch_addresses:
        return
    args = [
        "--rom",
        cmd_arg(effective_rom),
        "--symbols",
        cmd_arg(effective_symbols),
    ]
    if save_state:
        args.extend(["--save-state", cmd_arg(save_state)])
    for input_log in input_logs:
        args.extend(["--input-log", cmd_arg(input_log)])
    for symbol in watch_symbols:
        args.extend(["--watch-symbol", cmd_arg(symbol)])
    for address in watch_addresses:
        args.extend(["--watch-address", cmd_arg(command_address_arg(address))])
    if watch_addresses and watch_size != 1:
        args.extend(["--watch-size", str(watch_size)])
    args.extend(
        [
            "--frames",
            str(frames),
            "--context-frames",
            str(context_frames),
            "--execute",
            "--json-out",
            ".local\\tmp\\debugger_replay_watch.json",
        ]
    )
    add_step(
        phases,
        "reproduce",
        "python -m tools.debugger watch " + " ".join(args),
        "Replay the ROM from the selected state and record the first observed target changes.",
    )


def add_localize_step(
    phases: dict[str, list[dict[str, Any]]],
    reports: tuple[str, ...],
    symbols: list[str],
    source_files: list[str],
    symptom: str,
) -> None:
    args = report_args(reports)
    for symbol in symbols[:6]:
        args.extend(["--symbol", cmd_arg(symbol)])
    for path in source_files[:4]:
        args.extend(["--changed-file", cmd_arg(path)])
    if symptom:
        args.extend(["--symptom", cmd_arg(symptom)])
    if not args:
        return
    add_step(
        phases,
        "localize",
        "python -m tools.debugger localize " + " ".join(args),
        "Fold replay evidence into a ranked symbol/source suspect list.",
    )


def add_coverage_step(
    phases: dict[str, list[dict[str, Any]]],
    reports: tuple[str, ...],
    traces: tuple[str, ...],
    symbols: list[str],
    source_files: list[str],
) -> None:
    args = report_args(reports)
    for trace in traces:
        args.extend(["--trace", cmd_arg(trace)])
    for symbol in symbols[:8]:
        args.extend(["--symbol", cmd_arg(symbol)])
    for path in source_files[:5]:
        args.extend(["--changed-file", cmd_arg(path)])
    if not args:
        return
    add_step(
        phases,
        "prove",
        "python -m tools.debugger coverage " + " ".join(args),
        "Show which suspected labels and files are actually mentioned by replay or trace evidence.",
    )


def add_minimize_step(
    phases: dict[str, list[dict[str, Any]]],
    reports: tuple[str, ...],
    traces: tuple[str, ...],
    scenarios: tuple[str, ...],
    symbols: list[str],
    watch_addresses: list[str],
    scenario_ids: list[str],
    source_files: list[str],
    changed_files: tuple[str, ...],
    symptom: str,
) -> None:
    args = report_args(reports)
    for scenario in scenarios:
        args.extend(["--scenario", cmd_arg(scenario)])
    for scenario_id in scenario_ids[:4]:
        args.extend(["--scenario-id", cmd_arg(scenario_id)])
    for symbol in symbols[:5]:
        args.extend(["--symbol", cmd_arg(symbol)])
    for path in changed_files[:4]:
        args.extend(["--changed-file", cmd_arg(path)])
    if symptom:
        args.extend(["--symptom", cmd_arg(symptom)])
    trace_args: list[str] = []
    for trace in traces:
        trace_args.extend(["--trace", cmd_arg(trace)])
    for symbol in symbols[:5]:
        trace_args.extend(["--symbol", cmd_arg(symbol)])
    for address in watch_addresses[:5]:
        trace_args.extend(["--address", cmd_arg(command_address_arg(address))])
    for path in source_files[:4]:
        trace_args.extend(["--source-file", cmd_arg(path)])
    if not args and not trace_args:
        return
    if args:
        add_step(
            phases,
            "prove",
            "python -m tools.debugger minimize " + " ".join(args),
            "Reduce the replay inputs toward a minimal counterexample or subsystem reducer command.",
        )
    if trace_args:
        trace_args.extend(["--out-trace", ".local\\tmp\\debugger_replay_minimized_trace.json"])
        add_step(
            phases,
            "prove",
            "python -m tools.debugger minimize " + " ".join(trace_args),
            "Reduce captured trace evidence to the smallest subset that still mentions the replay targets.",
        )


def add_instruction_trace_step(
    phases: dict[str, list[dict[str, Any]]],
    effective_rom: str,
    effective_symbols: str,
    save_state: str,
    input_logs: tuple[str, ...],
    reports: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    frames: int,
    symbols: list[str],
    watch_symbols: list[str],
    watch_addresses: list[str],
    watch_size: int,
) -> None:
    if not symbols and not watch_symbols and not reports and not changed_files and not symptom:
        return
    args = [
        "--rom",
        cmd_arg(effective_rom),
        "--symbols",
        cmd_arg(effective_symbols),
        "--frames",
        str(frames),
    ]
    if save_state:
        args.extend(["--save-state", cmd_arg(save_state)])
    for input_log in input_logs:
        args.extend(["--input-log", cmd_arg(input_log)])
    for report in reports[:4]:
        args.extend(["--report", cmd_arg(report)])
    for path in changed_files[:4]:
        args.extend(["--changed-file", cmd_arg(path)])
    if symptom:
        args.extend(["--symptom", cmd_arg(symptom)])
    for symbol in symbols[:6]:
        args.extend(["--symbol", cmd_arg(symbol)])
    for watch in watch_symbols[:6]:
        args.extend(["--watch-symbol", cmd_arg(watch)])
    for address in watch_addresses[:6]:
        args.extend(["--watch-address", cmd_arg(command_address_arg(address))])
    if watch_addresses and watch_size != 1:
        args.extend(["--watch-size", str(watch_size)])
    args.extend(["--execute", "--out-trace", ".local\\tmp\\debugger_replay_instruction_trace.jsonl"])
    add_step(
        phases,
        "prove",
        "python -m tools.debugger trace-instructions " + " ".join(args),
        "Capture dense opcode/register evidence for dynamic-taint when replay targets resolve to executable routines.",
    )


def add_compare_step(
    phases: dict[str, list[dict[str, Any]]],
    symbols: list[str],
    source_files: list[str],
    symptom: str,
) -> None:
    args = []
    for symbol in symbols[:5]:
        args.extend(["--symbol", cmd_arg(symbol)])
    for path in source_files[:4]:
        args.extend(["--changed-file", cmd_arg(path)])
    if symptom:
        args.extend(["--symptom", cmd_arg(symptom)])
    if not args:
        return
    add_step(
        phases,
        "prove",
        "python -m tools.debugger compare " + " ".join(args),
        "Route the replay target to the strongest available ROM mirror or expectation check.",
    )


def add_impact_step(
    phases: dict[str, list[dict[str, Any]]],
    reports: tuple[str, ...],
    symbols: list[str],
    source_files: list[str],
    symptom: str,
) -> None:
    args = report_args(reports)
    for symbol in symbols[:5]:
        args.extend(["--symbol", cmd_arg(symbol)])
    for path in source_files[:4]:
        args.extend(["--changed-file", cmd_arg(path)])
    if symptom:
        args.extend(["--symptom", cmd_arg(symptom)])
    if not args:
        return
    add_step(
        phases,
        "prove",
        "python -m tools.debugger impact " + " ".join(args),
        "Prioritize the replay findings by romhack blast radius and next proof command.",
    )


def add_report_step(phases: dict[str, list[dict[str, Any]]], reports: tuple[str, ...]) -> None:
    if not reports:
        return
    args = report_args(reports)
    args.extend(["--out", ".local\\tmp\\debugger_replay_report.md"])
    add_step(
        phases,
        "prove",
        "python -m tools.debugger report " + " ".join(args),
        "Render a scan-friendly replay packet while preserving JSON reports as source of truth.",
    )


def add_gate_step(
    phases: dict[str, list[dict[str, Any]]],
    changed_files: tuple[str, ...],
    symptom: str,
) -> None:
    args = []
    for path in changed_files[:6]:
        args.extend(["--changed-file", cmd_arg(path)])
    if symptom:
        args.extend(["--symptom", cmd_arg(symptom)])
    if not args:
        return
    add_step(
        phases,
        "verify",
        "python -m tools.debugger gate " + " ".join(args),
        "Run the romhack verification gates that match this replay surface.",
    )


def add_step(phases: dict[str, list[dict[str, Any]]], phase: str, command: str, reason: str) -> None:
    phases[phase].append(
        {
            "command": command,
            "reason": reason,
            "runnable": command_is_runnable(command),
        }
    )


def signal(
    signal_type: str,
    *,
    symbol: str = "",
    address: str = "",
    file: str = "",
    scenario_id: str = "",
    note: str = "",
    weight: int,
    source: str,
) -> dict[str, Any]:
    return {
        "type": signal_type,
        "symbol": symbol,
        "address": address,
        "file": normalize_path(file) if file else "",
        "scenario_id": scenario_id,
        "note": note,
        "weight": int(weight),
        "source": source,
    }


def artifact_errors(manifest: dict[str, Any]) -> list[str]:
    errors = []
    for artifact in dict_items(manifest.get("artifacts")):
        for error in artifact.get("errors", []):
            errors.append(f"{artifact.get('kind')} {artifact.get('path')}: {error}")
    return errors


def artifact_warnings(manifest: dict[str, Any]) -> list[str]:
    warnings = []
    for artifact in dict_items(manifest.get("artifacts")):
        for warning in artifact.get("warnings", []):
            warnings.append(f"{artifact.get('kind')} {artifact.get('path')}: {warning}")
    return warnings


def phase_title(phase: str) -> str:
    return {
        "ingest": "Ingest and fingerprint replay inputs",
        "setup": "Plan ROM setup and trigger materialization",
        "reproduce": "Reproduce under the generic runtime bridge",
        "localize": "Localize suspect symbols and source files",
        "prove": "Prove, compare, minimize, and rank the behavior",
        "verify": "Verify the fix path",
    }.get(phase, phase)


def report_args(reports: tuple[str, ...]) -> list[str]:
    args: list[str] = []
    for report in reports:
        args.extend(["--report", cmd_arg(report)])
    return args


def merge_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    for item in signals:
        key = (
            str(item.get("type", "")),
            str(item.get("symbol", "")),
            str(item.get("address", "")),
            str(item.get("file", "")),
            str(item.get("scenario_id", "")),
            str(item.get("note", "")),
        )
        if key not in merged:
            merged[key] = dict(item)
            continue
        merged[key]["weight"] = max(int(merged[key]["weight"]), int(item["weight"]))
    return sorted(merged.values(), key=lambda item: (-int(item["weight"]), item["type"], item["source"]))


def unique_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for step in steps:
        command = step["command"]
        if command in seen:
            continue
        seen.add(command)
        out.append(step)
    return out


def top_keys(scores: dict[str, int], limit: int) -> list[str]:
    return [
        key
        for key, _score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]
        if key
    ]


def looks_like_symbol(value: str) -> bool:
    text = value.strip()
    if text in SYMBOL_STOPWORDS:
        return False
    if looks_like_address(text):
        return False
    if not text or "/" in text or "\\" in text:
        return False
    if text.startswith(("$", "0x", "0X", ".", "<")):
        return False
    return text[0].isalpha() and any(char.isupper() or char == "_" for char in text)


def looks_like_address(value: str) -> bool:
    text = str(value).strip()
    if not text:
        return False
    if "=" in text:
        _label, text = [part.strip() for part in text.rsplit("=", 1)]
    if text.startswith("$"):
        text = text[1:]
    if text.lower().startswith("0x"):
        text = text[2:]
    if ":" in text:
        bank, address = [part.strip().lstrip("$") for part in text.split(":", 1)]
        return is_hex(bank, 2) and is_hex(address, 4)
    return is_hex(text, 4)


def is_hex(value: str, max_length: int) -> bool:
    text = str(value).strip()
    if not text or len(text) > max_length:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in text)


def address_value_is_replay_target(container: dict[str, Any], key: str) -> bool:
    if key in {"watch", "target", "watch_address", "sink_address"}:
        return True
    return any(
        marker in container
        for marker in (
            "old_hex",
            "new_hex",
            "mnemonic",
            "source_operands",
            "write_attributions",
            "watch_addresses",
            "related_addresses",
            "sink_addresses",
            "watch_address",
            "sink_address",
            "event_type",
            "watch_size",
            "sink_size",
        )
    )


def looks_like_source_path(value: str) -> bool:
    text = normalize_path(value)
    if not text or " " in text:
        return False
    return "/" in text and Path(text).suffix.lower() in SOURCE_EXTENSIONS


def is_scenario_record(data: dict[str, Any], scenario_id: str) -> bool:
    text = str(scenario_id)
    if not text:
        return False
    kind = str(data.get("kind", "")).lower()
    if "scenario" in kind:
        return True
    if data.get("scenario_type") or data.get("family") in {"content_static", "damage", "boss_ai"}:
        return True
    return text.startswith(("content_scenario_", "debugger_generated_", "scenario_"))


def string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple | set):
        return [
            nested
            for item in value
            for nested in string_items(item)
        ]
    if isinstance(value, dict):
        return [
            nested
            for item in value.values()
            for nested in string_items(item)
        ]
    return [str(value)] if value else []


def field_string_items(value: Any) -> list[str]:
    if isinstance(value, dict):
        return []
    return string_items(value)


def dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]


def unique_list(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def cmd_arg(value: str) -> str:
    text = str(value)
    if not text:
        return '""'
    if any(char.isspace() for char in text):
        return '"' + text.replace('"', '\\"') + '"'
    return text
