from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import ROOT, triage_request
from .coverage import load_traces
from .ingest import ingest_artifacts, resolve_path
from .localize import is_watchable_symbol, normalize_path
from .reporting import load_reports
from .runtime_watch import DEFAULT_ROM, DEFAULT_SYMBOLS, build_watch_report
from .setup_plan import build_setup_plan
from .workflow import command_is_runnable


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
SCENARIO_KEYS = {"id", "scenario_id", "capture_id", "trace_id"}
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
    traces: tuple[str, ...] = (),
    scenarios: tuple[str, ...] = (),
    scenario_ids: tuple[str, ...] = (),
    reports: tuple[str, ...] = (),
    watch_symbols: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symptom: str = "",
    frames: int = 300,
    context_frames: int = 12,
    execute_watch: bool = False,
    max_targets: int = 12,
    root: Path = ROOT,
) -> dict[str, Any]:
    effective_rom = rom_path or DEFAULT_ROM
    effective_symbols = symbols_path or DEFAULT_SYMBOLS
    initial_manifest = ingest_artifacts(
        roms=artifact_inputs(raw_input=rom_path, effective_input=effective_rom, root=root),
        symbols=artifact_inputs(raw_input=symbols_path, effective_input=effective_symbols, root=root),
        traces=traces,
        save_states=(save_state,) if save_state else (),
        scenarios=scenarios,
        changed_files=changed_files,
        root=root,
    )
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    loaded_traces, trace_errors = load_traces(traces=traces, root=root)
    signals = collect_replay_signals(
        manifest=initial_manifest,
        loaded_reports=loaded_reports,
        loaded_traces=loaded_traces,
        scenario_ids=scenario_ids,
        watch_symbols=watch_symbols,
        symbols=symbols,
        changed_files=changed_files,
        symptom=symptom,
    )
    targets = build_replay_targets(signals, max_targets=max_targets)
    setup_plan = build_setup_plan(
        rom_path=effective_rom,
        symbols_path=effective_symbols,
        save_state=save_state,
        reports=reports,
        scenarios=scenarios,
        scenario_ids=tuple(targets["scenario_ids"] or scenario_ids),
        changed_files=changed_files,
        symbols=tuple(targets["symbols"] or symbols),
        watch_symbols=tuple(targets["watch_symbols"] or watch_symbols),
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
        scenarios=scenarios,
        changed_files=changed_files,
        root=root,
    )
    steps = build_replay_steps(
        effective_rom=effective_rom,
        effective_symbols=effective_symbols,
        save_state=effective_save_state,
        traces=traces,
        scenarios=scenarios,
        reports=reports,
        changed_files=changed_files,
        symptom=symptom,
        frames=frames,
        context_frames=context_frames,
        targets=targets,
    )
    watch_report = None
    watch_errors: list[str] = []
    if execute_watch:
        if not targets["watch_symbols"]:
            watch_errors.append("no watchable replay target was found")
        else:
            try:
                watch_report = build_watch_report(
                    watch_symbols=tuple(targets["watch_symbols"]),
                    rom_path=effective_rom,
                    symbols_path=effective_symbols,
                    save_state=effective_save_state,
                    frames=frames,
                    context_frames=context_frames,
                    execute=True,
                    root=root,
                )
                watch_errors.extend(watch_report.get("errors", []))
            except Exception as exc:  # PyBoy/runtime setup errors must become report data.
                watch_errors.append(f"watch execution failed: {exc}")

    errors = unique_list(
        [
            *manifest.get("errors", []),
            *artifact_errors(manifest),
            *report_errors,
            *trace_errors,
            *setup_plan.get("errors", []),
            *watch_errors,
        ]
    )
    warnings = unique_list(
        [
            *artifact_warnings(manifest),
            *setup_plan.get("warnings", []),
            *([] if targets["watch_symbols"] else ["no watchable symbol target was selected"]),
        ]
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
        "save_state_discovery": {
            "selected": selected_save_state,
            "candidate_count": setup_plan.get("save_state_discovery", {}).get("candidate_count", 0),
            "candidates": setup_plan.get("save_state_discovery", {}).get("candidates", [])[:20],
        },
        "frames": frames,
        "context_frames": context_frames,
        "executed_watch": execute_watch,
        "input_scenario_ids": list(scenario_ids),
        "artifact_manifest": manifest,
        "input_reports": [item["source"] for item in loaded_reports],
        "input_traces": [item["source"] for item in loaded_traces],
        "setup_plan": setup_plan,
        "signal_count": len(signals),
        "signals": signals[:160],
        "watch_symbol_count": len(targets["watch_symbols"]),
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
        "known_limits": [
            "Replay planning is generic; exact semantic reducers still live in the focused subsystem tools.",
            "Replay now reuses setup save-state discovery when reports or scenarios name an existing concrete state.",
            "Generic execution currently drives forward frame-sampled watch polling through PyBoy with bounded context windows, not reverse execution or CPU hardware watchpoints.",
        ],
    }


def artifact_inputs(*, raw_input: str, effective_input: str, root: Path) -> tuple[str, ...]:
    if raw_input:
        return (raw_input,)
    if effective_input and resolve_path(effective_input, root=root).exists():
        return (effective_input,)
    return ()


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


def collect_replay_signals(
    *,
    manifest: dict[str, Any],
    loaded_reports: list[dict[str, Any]],
    loaded_traces: list[dict[str, Any]],
    scenario_ids: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    symbols: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for symbol in watch_symbols:
        signals.append(signal("explicit_watch", symbol=symbol, weight=100, source="input"))
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
        if kind == "unified_debugger_content_state_materialization":
            out.extend(content_state_materialization_signals(data, source=source, base_weight=max(base_weight, 88)))
        for key, value in data.items():
            lowered = str(key).lower()
            if lowered in SYMBOL_KEYS:
                for item in field_string_items(value):
                    if looks_like_symbol(item):
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
        scenario_id = str(scenario.get("id") or scenario.get("scenario_id") or "")
        note = scenario_id or str(scenario.get("scenario_type", "content scenario"))
        source_file = normalize_path(str(scenario.get("source_file", "")))
        if scenario_id:
            out.append(signal("content_scenario_id", scenario_id=scenario_id, note=note, weight=base_weight, source=source))
        if source_file:
            out.append(signal("content_scenario_file", file=source_file, note=note, weight=base_weight, source=source))
        runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
        for symbol_name in string_items(runtime_targets.get("watch_symbols")):
            if looks_like_symbol(symbol_name):
                out.append(signal("content_scenario_watch_symbol", symbol=symbol_name, note=note, weight=min(100, base_weight + 12), source=source))
        for symbol_name in string_items(runtime_targets.get("trace_symbols")):
            if looks_like_symbol(symbol_name):
                out.append(signal("content_scenario_trace_symbol", symbol=symbol_name, note=note, weight=min(100, base_weight + 6), source=source))
        for symbol_name in string_items(runtime_targets.get("script_symbols")):
            if looks_like_symbol(symbol_name):
                out.append(signal("content_scenario_script_symbol", symbol=symbol_name, note=note, weight=base_weight, source=source))
        for symbol_name in string_items(runtime_targets.get("source_symbols")):
            if looks_like_symbol(symbol_name):
                out.append(signal("content_scenario_source_symbol", symbol=symbol_name, note=note, weight=max(50, base_weight - 4), source=source))
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


def build_replay_targets(signals: list[dict[str, Any]], *, max_targets: int) -> dict[str, Any]:
    symbol_scores: dict[str, int] = {}
    watch_scores: dict[str, int] = {}
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
    watch_symbols = unique_list(
        [
            *explicit_watch,
            *top_keys(watch_scores, max_targets),
            *[symbol for symbol in symbols if is_watchable_symbol(symbol)],
        ]
    )[:max_targets]
    return {
        "watch_symbols": watch_symbols,
        "symbols": symbols,
        "source_files": top_keys(file_scores, max_targets),
        "scenario_ids": top_keys(scenario_scores, max_targets),
        "symbol_scores": symbol_scores,
        "watch_symbol_scores": watch_scores,
        "source_file_scores": file_scores,
        "scenario_scores": scenario_scores,
    }


def build_replay_steps(
    *,
    effective_rom: str,
    effective_symbols: str,
    save_state: str,
    traces: tuple[str, ...],
    scenarios: tuple[str, ...],
    reports: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    frames: int,
    context_frames: int,
    targets: dict[str, Any],
) -> list[dict[str, Any]]:
    phases: dict[str, list[dict[str, Any]]] = {
        "ingest": [],
        "setup": [],
        "reproduce": [],
        "localize": [],
        "prove": [],
        "verify": [],
    }
    add_ingest_step(phases, effective_rom, effective_symbols, save_state, traces, scenarios, changed_files)
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
    add_watch_step(phases, effective_rom, effective_symbols, save_state, frames, context_frames, targets["watch_symbols"])
    add_instruction_trace_step(
        phases,
        effective_rom,
        effective_symbols,
        save_state,
        reports,
        changed_files,
        symptom,
        frames,
        targets["symbols"],
        targets["watch_symbols"],
    )
    add_localize_step(phases, reports, targets["symbols"], targets["source_files"], symptom)
    add_coverage_step(phases, reports, traces, targets["symbols"], targets["source_files"])
    add_minimize_step(
        phases,
        reports,
        traces,
        scenarios,
        targets["symbols"],
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
    frames: int,
    context_frames: int,
    watch_symbols: list[str],
) -> None:
    if not watch_symbols:
        return
    args = [
        "--rom",
        cmd_arg(effective_rom),
        "--symbols",
        cmd_arg(effective_symbols),
    ]
    if save_state:
        args.extend(["--save-state", cmd_arg(save_state)])
    for symbol in watch_symbols:
        args.extend(["--watch-symbol", cmd_arg(symbol)])
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
    reports: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    frames: int,
    symbols: list[str],
    watch_symbols: list[str],
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
    file: str = "",
    scenario_id: str = "",
    note: str = "",
    weight: int,
    source: str,
) -> dict[str, Any]:
    return {
        "type": signal_type,
        "symbol": symbol,
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
    merged: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for item in signals:
        key = (
            str(item.get("type", "")),
            str(item.get("symbol", "")),
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
    if not text or "/" in text or "\\" in text:
        return False
    if text.startswith(("$", "0x", "0X", ".", "<")):
        return False
    return text[0].isalpha() and any(char.isupper() or char == "_" for char in text)


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
        return json.dumps(text)
    return text
