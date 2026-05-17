from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.damage_debugger.disasm import Instruction, walk_function
from tools.trace import runtime as trace_runtime

from .catalog import ROOT
from .explain import base_label
from .ingest import sha256_file
from .provenance import display_path, parse_symbol_table, resolve_path
from .reporting import load_reports
from .runtime_watch import (
    DEFAULT_ROM,
    DEFAULT_SYMBOLS,
    build_watch_spec,
    bytes_hex,
    read_watch_bytes,
    register_snapshot,
    render_pc,
)
from .setup_plan import save_state_candidate, select_save_state, unique_candidates
from .workflow import command_is_runnable


SOURCE_EXTENSIONS = {".asm", ".inc"}
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
LABEL_RE = re.compile(r"^\s*(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*):{1,2}")
SIGNAL_WEIGHT = {
    "explicit_function": 120,
    "explicit_watch": 120,
    "explicit_watch_from_symbol": 110,
    "explicit_sink": 115,
    "watch_hit_function": 108,
    "watch_hit_symbol": 112,
    "dynamic_taint_function": 104,
    "dynamic_taint_target": 106,
    "trace_index_function": 88,
    "trace_index_state": 76,
    "instruction_report_function": 90,
    "instruction_report_watch": 94,
    "content_runtime_function": 98,
    "content_runtime_watch": 100,
    "content_state_function": 102,
    "content_state_watch": 104,
    "source_label": 72,
    "symptom_watch": 68,
}

CONTENT_STATE_TRACE_HELPERS = {
    "map_warp": ("WarpCheck", "EnterMapWarp", "ReadMapEvents"),
    "map_coord_event": ("CheckCurrentMapCoordEvents", "CheckTileEvent", "CallScript"),
    "map_bg_event": ("CheckFacingBGEvent", "CheckBGEventFlag", "CallScript"),
    "map_object_event": ("TryObjectEvent", "CheckFacingObject", "CallScript"),
    "script_entry": ("ScriptEvents", "RunScriptCommand", "CallScript"),
    "movement_entry": ("ApplyMovement", "GetMovementData", "HandleMovementData", "WaitScriptMovement"),
}


@dataclass(frozen=True)
class SymbolRef:
    bank: int
    address: int


class SymbolTableAdapter:
    def __init__(self, symbol_table: dict[str, dict[str, Any]]):
        self.symbol_table = symbol_table

    def __getitem__(self, name: str) -> SymbolRef:
        entry = self.symbol_table[name]
        return SymbolRef(bank=int(entry["bank"]), address=int(entry["address"]))

    def labels_in(self, bank: int) -> list[tuple[int, str]]:
        return sorted(
            (int(entry["address"]), label)
            for label, entry in self.symbol_table.items()
            if int(entry["bank"]) == int(bank)
        )


class RomImage:
    def __init__(self, data: bytes):
        self.data = data

    def read_byte(self, bank: int, address: int) -> int:
        offset = rom_offset(bank=bank, address=address)
        if offset < 0 or offset >= len(self.data):
            raise IndexError(f"ROM read outside image: {bank:02X}:{address:04X}")
        return int(self.data[offset])


def build_instruction_trace_report(
    *,
    function_symbols: tuple[str, ...] = (),
    watch_symbols: tuple[str, ...] = (),
    reports: tuple[str, ...] = (),
    scenario_ids: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    symptom: str = "",
    sink_symbols: tuple[str, ...] = (),
    rom_path: str = DEFAULT_ROM,
    symbols_path: str = DEFAULT_SYMBOLS,
    save_state: str = "",
    frames: int = 300,
    max_bytes: int = 0x800,
    max_frames: int = 50_000,
    max_functions: int = 12,
    execute: bool = False,
    require_hit: bool = False,
    out_trace: str = "",
    root: Path = ROOT,
) -> dict[str, Any]:
    rom = resolve_path(rom_path, root=root)
    sym = resolve_path(symbols_path, root=root)
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    save_state_candidates = discover_instruction_trace_save_states(
        loaded_reports=loaded_reports,
        scenario_ids=scenario_ids,
        explicit_save_state=save_state,
        root=root,
    )
    selected_save_state = select_save_state(save_state_candidates)
    effective_save_state = save_state or str(selected_save_state.get("path", ""))
    save = resolve_path(effective_save_state, root=root) if effective_save_state else None
    errors: list[str] = []
    warnings: list[str] = []
    errors.extend(report_errors)
    if frames < 0:
        errors.append("--frames must be non-negative")
    if max_bytes < 1:
        errors.append("--max-bytes must be positive")
    if max_frames < 1:
        errors.append("--max-frames must be positive")
    if max_functions < 1:
        errors.append("--max-functions must be positive")
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if save is not None and not save.exists():
        errors.append(f"missing save-state: {effective_save_state}")

    symbol_table = parse_symbol_table(sym) if sym.exists() else {}
    selection = select_trace_targets(
        function_symbols=function_symbols,
        watch_symbols=(*watch_symbols, *sink_symbols),
        loaded_reports=loaded_reports,
        scenario_ids=scenario_ids,
        changed_files=changed_files,
        symptom=symptom,
        symbol_table=symbol_table,
        max_functions=max(1, max_functions),
        root=root,
    ) if symbol_table else empty_selection(function_symbols=function_symbols, watch_symbols=(*watch_symbols, *sink_symbols))
    selected_functions = tuple(selection["function_symbols"])
    selected_watches = tuple(selection["watch_symbols"])
    if not selected_functions and not errors:
        errors.append(
            "no traceable function symbol was selected; provide --symbol, --report with PC labels, --changed-file, or a symptom/source that resolves to code"
        )
    watches = [
        build_watch_spec(symbol, symbol_table, symbols_path=sym, root=root)
        for symbol in selected_watches
    ] if sym.exists() else []
    for watch in watches:
        if not watch["found"]:
            errors.append(f"watch symbol not found in symbols: {watch['name']}")

    plans: list[dict[str, Any]] = []
    rom_image = RomImage(rom.read_bytes()) if rom.exists() else None
    if rom_image is not None and symbol_table:
        for symbol in selected_functions:
            plan, plan_errors = plan_function_trace(
                symbol,
                rom_image=rom_image,
                symbol_table=symbol_table,
                max_bytes=max_bytes,
            )
            plans.append(plan)
            errors.extend(plan_errors)

    captured_records: list[dict[str, Any]] = []
    trace_output = {"path": display_path(resolve_path(out_trace, root=root), root=root) if out_trace else "", "written": False, "record_count": 0, "errors": []}
    if execute and not errors:
        captured_records, capture_errors = execute_instruction_trace(
            rom=rom,
            save_state=save,
            plans=plans,
            watches=watches,
            symbol_table=symbol_table,
            symbols_path=sym,
            frames=frames,
            max_frames=max_frames,
        )
        errors.extend(capture_errors)
        trace_output = write_trace_output(records=captured_records, out_trace=out_trace, root=root)
        errors.extend(trace_output.get("errors", []))
    elif out_trace and not execute:
        warnings.append("--out-trace is only written with --execute")
    execution_validation = build_execution_validation(
        execute=execute,
        require_hit=require_hit,
        plans=plans,
        watches=watches,
        records=captured_records,
        max_frames=max_frames,
    )
    warnings.extend(execution_validation["warnings"])
    errors.extend(execution_validation["errors"])

    commands = build_commands(
        function_symbols=function_symbols,
        selected_function_symbols=selected_functions,
        watch_symbols=selected_watches,
        reports=reports,
        scenario_ids=scenario_ids,
        changed_files=changed_files,
        symptom=symptom,
        rom_path=rom_path,
        symbols_path=symbols_path,
        save_state=effective_save_state,
        frames=frames,
        require_hit=require_hit,
        out_trace=out_trace,
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_instruction_trace",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "rom": display_path(rom, root=root),
        "rom_sha256": sha256_file(rom) if rom.exists() else "",
        "symbols": display_path(sym, root=root),
        "symbols_sha256": sha256_file(sym) if sym.exists() else "",
        "save_state": display_path(save, root=root) if save is not None else "",
        "input_save_state": save_state,
        "effective_save_state": display_path(save, root=root) if save is not None else "",
        "save_state_discovery": {
            "candidate_count": len(save_state_candidates),
            "selected": selected_save_state,
            "candidates": save_state_candidates[:20],
        },
        "executed": execute,
        "frames": frames,
        "max_bytes": max_bytes,
        "max_frames": max_frames,
        "max_functions": max_functions,
        "require_hit": require_hit,
        "input_reports": [item["source"] for item in loaded_reports],
        "input_scenario_ids": list(scenario_ids),
        "changed_files": [display_path(resolve_path(path, root=root), root=root) for path in changed_files],
        "symptom": symptom,
        "target_selection": selection,
        "function_count": len(plans),
        "instruction_count": sum(int(plan.get("instruction_count", 0)) for plan in plans),
        "watch_count": len(watches),
        "captured_frame_count": len(captured_records),
        "functions": plans,
        "watches": watches,
        "execution_validation": execution_validation,
        "trace_output": trace_output,
        "sample_records": captured_records[:12],
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "Instruction capture is hook-based over selected function bodies, not whole-CPU reverse execution.",
            "The static plan follows decoded function bodies from the ROM image; runtime capture records only instructions that actually execute during the frame window.",
            "Automatic target selection picks likely trace windows from reports, changed source labels, and symptoms; confirm broad or ambiguous selections before using them as final proof.",
            "Feed the emitted JSONL to dynamic-taint for byte-level causal paths from chosen sources to watched sinks.",
        ],
    }


def discover_instruction_trace_save_states(
    *,
    loaded_reports: list[dict[str, Any]],
    scenario_ids: tuple[str, ...],
    explicit_save_state: str,
    root: Path,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if explicit_save_state:
        candidates.append(
            save_state_candidate(
                path=explicit_save_state,
                source="input",
                key="save_state",
                scenario_id="",
                explicit=True,
                root=root,
            )
        )
    for loaded in loaded_reports:
        data = loaded.get("data", {})
        if not isinstance(data, dict):
            continue
        if str(data.get("kind", "")) != "unified_debugger_content_state_materialization":
            continue
        if not content_state_execution_succeeded(data):
            continue
        scenario_id = selected_content_state_scenario_id(data, scenario_ids=scenario_ids)
        if scenario_id is None:
            continue
        out_state, key = content_state_report_out_state(data)
        if not out_state:
            continue
        candidates.append(
            save_state_candidate(
                path=out_state,
                source=str(loaded.get("source", "report")),
                key=key,
                scenario_id=scenario_id,
                explicit=False,
                preferred=True,
                root=root,
            )
        )
    return sorted(
        unique_candidates(candidates),
        key=lambda item: (
            not bool(item.get("explicit")),
            not bool(item.get("preferred")),
            not bool(item.get("exists")),
            str(item.get("source", "")),
            str(item.get("path", "")),
        ),
    )


def content_state_execution_succeeded(report: dict[str, Any]) -> bool:
    execution = report.get("execution") if isinstance(report.get("execution"), dict) else {}
    return report.get("executed") is True or execution.get("executed") is True


def selected_content_state_scenario_id(report: dict[str, Any], *, scenario_ids: tuple[str, ...]) -> str | None:
    selected_ids = {str(item) for item in scenario_ids if item}
    report_id = str(report.get("scenario_id") or report.get("id") or "")
    first_id = report_id
    for materialization in dict_items(report.get("materializations")):
        scenario_id = str(materialization.get("scenario_id") or materialization.get("id") or "")
        if scenario_id and not first_id:
            first_id = scenario_id
        if selected_ids and scenario_id in selected_ids:
            return scenario_id
    if selected_ids:
        return report_id if report_id in selected_ids else None
    return first_id


def content_state_report_out_state(report: dict[str, Any]) -> tuple[str, str]:
    execution = report.get("execution") if isinstance(report.get("execution"), dict) else {}
    execution_out_state = str(execution.get("out_state") or "")
    if execution_out_state:
        return execution_out_state, "execution.out_state"
    return str(report.get("out_state") or ""), "out_state"


def select_trace_targets(
    *,
    function_symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    loaded_reports: list[dict[str, Any]],
    scenario_ids: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    symbol_table: dict[str, dict[str, Any]],
    max_functions: int,
    root: Path,
) -> dict[str, Any]:
    signals: list[dict[str, Any]] = []
    for symbol in function_symbols:
        signal_type = "explicit_function" if is_traceable_function(symbol, symbol_table) else "explicit_watch_from_symbol"
        signals.append(trace_signal(signal_type, symbol=symbol, source="input"))
    for symbol in watch_symbols:
        signals.append(trace_signal("explicit_watch", symbol=symbol, source="input"))
    for loaded in loaded_reports:
        signals.extend(signals_from_report(loaded["data"], source=loaded["source"], scenario_ids=scenario_ids))
    for path in changed_files:
        signals.extend(signals_from_source_file(path, symbol_table=symbol_table, root=root))
    signals.extend(signals_from_symptom(symptom))

    function_scores: dict[str, int] = {}
    watch_scores: dict[str, int] = {}
    for item in signals:
        symbol = base_label(str(item.get("symbol", "")))
        if not symbol:
            continue
        weight = int(item.get("weight", 0))
        if item.get("role") == "function" or is_traceable_function(symbol, symbol_table):
            if is_traceable_function(symbol, symbol_table):
                function_scores[symbol] = function_scores.get(symbol, 0) + weight
        if item.get("role") == "watch" or is_watch_symbol(symbol, symbol_table):
            if is_watch_symbol(symbol, symbol_table):
                watch_scores[symbol] = watch_scores.get(symbol, 0) + weight

    selected_functions = top_symbols(function_scores, limit=max_functions)
    selected_watches = top_symbols(watch_scores, limit=max(24, len(watch_scores)))
    return {
        "active": bool(selected_functions or selected_watches or signals),
        "function_symbols": selected_functions,
        "watch_symbols": selected_watches,
        "function_scores": function_scores,
        "watch_scores": watch_scores,
        "signals": signals[:160],
    }


def empty_selection(*, function_symbols: tuple[str, ...], watch_symbols: tuple[str, ...]) -> dict[str, Any]:
    return {
        "active": bool(function_symbols or watch_symbols),
        "function_symbols": list(function_symbols),
        "watch_symbols": list(watch_symbols),
        "function_scores": {},
        "watch_scores": {},
        "signals": [],
    }


def signals_from_report(report: dict[str, Any], *, source: str, scenario_ids: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    kind = str(report.get("kind", ""))
    out: list[dict[str, Any]] = []
    if kind == "unified_debugger_watch_report":
        for event in dict_items(report.get("events")):
            routine = base_label(str(event.get("pc_label", "")))
            if routine:
                out.append(trace_signal("watch_hit_function", symbol=routine, role="function", source=source))
            watch = str(event.get("watch", ""))
            if watch:
                out.append(trace_signal("watch_hit_symbol", symbol=watch, role="watch", source=source))
            source_cause = event.get("source_cause")
            if isinstance(source_cause, dict):
                cause_routine = base_label(str(source_cause.get("routine", "")))
                if cause_routine:
                    out.append(trace_signal("watch_hit_function", symbol=cause_routine, role="function", source=source))
        for watch in dict_items(report.get("watches")):
            watch_name = str(watch.get("name", ""))
            if watch_name:
                out.append(trace_signal("explicit_watch", symbol=watch_name, role="watch", source=source))
    elif kind == "unified_debugger_dynamic_taint_report":
        for path in dict_items(report.get("paths")):
            routine = base_label(str(path.get("pc_label", "")))
            if routine:
                out.append(trace_signal("dynamic_taint_function", symbol=routine, role="function", source=source))
            target = str(path.get("target", ""))
            if target:
                out.append(trace_signal("dynamic_taint_target", symbol=target, role="watch", source=source))
        for sink in dict_items(report.get("sinks")):
            name = str(sink.get("name", ""))
            if name:
                out.append(trace_signal("dynamic_taint_target", symbol=name, role="watch", source=source))
    elif kind == "unified_debugger_trace_index":
        for event in dict_items(report.get("events")):
            for key in ("pc_symbol", "source_symbol"):
                symbol = base_label(str(event.get(key, "")))
                if symbol:
                    out.append(trace_signal("trace_index_function", symbol=symbol, role="function", source=source))
            state = str(event.get("state_symbol", ""))
            if state:
                out.append(trace_signal("trace_index_state", symbol=state, role="watch", source=source))
        for path in dict_items(report.get("causal_paths")):
            for symbol in string_items(path.get("related_symbols")):
                out.append(trace_signal("trace_index_function", symbol=base_label(symbol), role="function", source=source))
    elif kind == "unified_debugger_instruction_trace":
        for function in dict_items(report.get("functions")):
            symbol = str(function.get("symbol", ""))
            if symbol:
                out.append(trace_signal("instruction_report_function", symbol=symbol, role="function", source=source))
        for watch in dict_items(report.get("watches")):
            symbol = str(watch.get("name", ""))
            if symbol:
                out.append(trace_signal("instruction_report_watch", symbol=symbol, role="watch", source=source))
    elif kind == "unified_debugger_content_scenarios":
        for scenario in dict_items(report.get("scenarios")):
            if content_scenario_selected(scenario, scenario_ids=scenario_ids):
                out.extend(signals_from_content_scenario(scenario, source=source))
    elif kind == "unified_debugger_content_scenario":
        if content_scenario_selected(report, scenario_ids=scenario_ids):
            out.extend(signals_from_content_scenario(report, source=source))
    elif kind == "unified_debugger_content_state_materialization":
        for materialization in dict_items(report.get("materializations")):
            if content_scenario_selected(materialization, scenario_ids=scenario_ids):
                out.extend(signals_from_content_state_materialization(materialization, source=source))
    else:
        collect_generic_report_signals(report, source=source, out=out)
    return [item for item in out if item.get("symbol")]


def signals_from_content_scenario(scenario: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    runtime_targets = scenario.get("runtime_targets") if isinstance(scenario.get("runtime_targets"), dict) else {}
    for symbol in string_items(runtime_targets.get("trace_symbols")):
        out.append(trace_signal("content_runtime_function", symbol=symbol, role="function", source=source))
    for symbol in string_items(runtime_targets.get("watch_symbols")):
        out.append(trace_signal("content_runtime_watch", symbol=symbol, role="watch", source=source))
    for precondition in dict_items(scenario.get("state_preconditions")):
        for symbol in string_items(precondition.get("watch_symbols")):
            out.append(trace_signal("content_runtime_watch", symbol=symbol, role="watch", source=source))
    return out


def content_scenario_selected(scenario: dict[str, Any], *, scenario_ids: tuple[str, ...]) -> bool:
    if not scenario_ids:
        return True
    selected_ids = {str(item) for item in scenario_ids}
    scenario_id = str(scenario.get("id") or scenario.get("scenario_id") or "")
    return scenario_id in selected_ids


def signals_from_content_state_materialization(materialization: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    precondition_kind = str(materialization.get("precondition_kind", ""))
    scenario_type = str(materialization.get("scenario_type", ""))
    helper_keys = (scenario_type, precondition_kind)
    for key in helper_keys:
        for symbol in CONTENT_STATE_TRACE_HELPERS.get(key, ()):
            out.append(trace_signal("content_state_function", symbol=symbol, role="function", source=source))
    for patch in dict_items(materialization.get("patches")):
        symbol = str(patch.get("base_symbol") or patch.get("symbol") or "")
        if symbol:
            out.append(trace_signal("content_state_watch", symbol=symbol, role="watch", source=source))
    if precondition_kind == "script_entry":
        out.append(trace_signal("content_state_watch", symbol="wScriptVar", role="watch", source=source))
    return out


def collect_generic_report_signals(data: Any, *, source: str, out: list[dict[str, Any]]) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            lowered = str(key).lower()
            if lowered in {"pc_label", "pc_symbol", "source_symbol", "routine", "function"}:
                for symbol in string_items(value):
                    out.append(trace_signal("trace_index_function", symbol=base_label(symbol), role="function", source=source))
            elif lowered in {"watch", "target", "sink", "state_symbol"}:
                for symbol in string_items(value):
                    out.append(trace_signal("trace_index_state", symbol=symbol, role="watch", source=source))
            collect_generic_report_signals(value, source=source, out=out)
    elif isinstance(data, list):
        for item in data:
            collect_generic_report_signals(item, source=source, out=out)


def signals_from_source_file(
    raw_path: str,
    *,
    symbol_table: dict[str, dict[str, Any]],
    root: Path,
) -> list[dict[str, Any]]:
    path = resolve_path(raw_path, root=root)
    if not path.exists() or path.suffix.lower() not in SOURCE_EXTENSIONS:
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    out: list[dict[str, Any]] = []
    current_global = ""
    for line in lines:
        match = LABEL_RE.match(line)
        if not match:
            continue
        raw_label = match.group("label")
        if raw_label.startswith("."):
            label = f"{current_global}{raw_label}" if current_global else raw_label.lstrip(".")
        else:
            current_global = raw_label
            label = raw_label
        if is_traceable_function(label, symbol_table):
            out.append(trace_signal("source_label", symbol=label, role="function", source=display_path(path, root=root)))
    return out


def signals_from_symptom(symptom: str) -> list[dict[str, Any]]:
    lowered = symptom.lower()
    return [
        trace_signal("symptom_watch", symbol=symbol, role="watch", source="symptom")
        for keyword, symbol in SYMPTOM_SYMBOLS.items()
        if keyword in lowered
    ]


def trace_signal(signal_type: str, *, symbol: str, source: str, role: str = "") -> dict[str, Any]:
    return {
        "type": signal_type,
        "role": role,
        "symbol": base_label(str(symbol)) or str(symbol),
        "source": source,
        "weight": SIGNAL_WEIGHT.get(signal_type, 40),
    }


def plan_function_trace(
    symbol: str,
    *,
    rom_image: RomImage,
    symbol_table: dict[str, dict[str, Any]],
    max_bytes: int,
) -> tuple[dict[str, Any], list[str]]:
    if symbol not in symbol_table:
        return empty_plan(symbol), [f"function symbol not found in symbols: {symbol}"]
    adapter = SymbolTableAdapter(symbol_table)
    try:
        instructions = walk_function(
            rom_image.read_byte,
            adapter,
            symbol,
            max_bytes=max_bytes,
        )
    except Exception as exc:
        return empty_plan(symbol), [f"{symbol}: instruction plan failed: {exc}"]
    return {
        "symbol": symbol,
        "bank": int(symbol_table[symbol]["bank"]),
        "address": int(symbol_table[symbol]["address"]),
        "bank_address": symbol_table[symbol]["bank_address"],
        "instruction_count": len(instructions),
        "hook_count": len(instructions),
        "instructions": [public_instruction(instruction, function=symbol, symbol_table=symbol_table) for instruction in instructions],
    }, []


def execute_instruction_trace(
    *,
    rom: Path,
    save_state: Path | None,
    plans: list[dict[str, Any]],
    watches: list[dict[str, Any]],
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    frames: int,
    max_frames: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    pyboy = trace_runtime.open_pyboy(
        rom,
        "PyBoy is required for unified instruction tracing. Import failed",
    )
    trace_runtime.disable_realtime(pyboy)
    records: list[dict[str, Any]] = []
    hooked: list[tuple[int, int]] = []
    errors: list[str] = []
    try:
        setattr(runtime_instruction_record, "seq", 0)
        if save_state is not None:
            with save_state.open("rb") as fh:
                pyboy.load_state(fh)
        for plan in plans:
            for instruction in plan.get("instructions", []):
                bank = int(instruction["bank"])
                pc = int(instruction["pc"])

                def make_callback(row: dict[str, Any], function: str):
                    def callback(_ctx: Any) -> None:
                        if len(records) >= max_frames:
                            return
                        records.append(runtime_instruction_record(
                            pyboy=pyboy,
                            instruction=row,
                            function=function,
                            watches=watches,
                        ))
                    return callback

                pyboy.hook_register(bank, pc, make_callback(instruction, str(plan["symbol"])), None)
                hooked.append((bank, pc))
        pyboy.tick(frames, False, False)
    except Exception as exc:
        errors.append(f"instruction trace capture failed: {exc}")
    finally:
        for bank, pc in hooked:
            try:
                pyboy.hook_deregister(bank, pc)
            except Exception:
                pass
        try:
            pyboy.stop(save=False)
        except TypeError:
            pyboy.stop()
    return records, errors


def runtime_instruction_record(
    *,
    pyboy: Any,
    instruction: dict[str, Any],
    function: str,
    watches: list[dict[str, Any]],
) -> dict[str, Any]:
    registers = register_snapshot(pyboy)
    regs = {
        name: parse_hex_register(registers.get(f"register_{name.lower()}", "0"))
        for name in ("A", "F", "B", "C", "D", "E", "H", "L", "SP", "PC")
    }
    regs["HL"] = ((regs["H"] & 0xFF) << 8) | (regs["L"] & 0xFF)
    seq = int(getattr(runtime_instruction_record, "seq", 0))
    setattr(runtime_instruction_record, "seq", seq + 1)
    return {
        "kind": "sm83_instruction_trace_frame",
        "event_type": "instruction",
        "seq": seq,
        "function": function,
        "bank": int(instruction["bank"]),
        "pc": int(instruction["pc"]),
        "pc_bank_address": instruction["bank_address"],
        "pc_label": instruction["pc_label"],
        "opcode": int(instruction["opcode"]),
        "operand": list(instruction.get("operand", [])),
        "length": int(instruction["length"]),
        "mnemonic": instruction["mnemonic"],
        "regs": regs,
        "registers": registers,
        "watch_values": {
            watch["name"]: bytes_hex(read_watch_bytes(pyboy, watch))
            for watch in watches
            if watch.get("found")
        },
    }


def build_execution_validation(
    *,
    execute: bool,
    require_hit: bool,
    plans: list[dict[str, Any]],
    watches: list[dict[str, Any]],
    records: list[dict[str, Any]],
    max_frames: int,
) -> dict[str, Any]:
    planned_functions = [
        str(plan.get("symbol", ""))
        for plan in plans
        if plan.get("symbol")
    ]
    hit_functions = unique_list(
        str(record.get("function", ""))
        for record in records
        if record.get("function")
    )
    hit_function_set = set(hit_functions)
    missing_functions = [
        symbol
        for symbol in planned_functions
        if execute and symbol not in hit_function_set
    ]
    watch_symbols = [
        str(watch.get("name", ""))
        for watch in watches
        if watch.get("found") and watch.get("name")
    ]
    hook_count = sum(int(plan.get("hook_count", 0)) for plan in plans)
    captured_frame_count = len(records)
    warnings: list[str] = []
    errors: list[str] = []

    if require_hit and not execute:
        warnings.append("--require-hit is only enforced with --execute")
    if execute and hook_count and captured_frame_count == 0:
        message = (
            "instruction trace executed but none of the selected hooks fired; "
            "the save state, frame window, or selected targets do not reach the planned routines"
        )
        if require_hit:
            errors.append(message)
        else:
            warnings.append(message)
    if execute and captured_frame_count and missing_functions:
        warnings.append(
            "instruction trace did not hit every selected function: "
            + ", ".join(missing_functions[:12])
        )
    if execute and captured_frame_count >= max_frames:
        warnings.append(
            "instruction trace reached --max-frames; rerun with a larger limit if the causal path may continue"
        )

    return {
        "attempted": execute,
        "required": require_hit,
        "planned_function_count": len(planned_functions),
        "planned_hook_count": hook_count,
        "captured_frame_count": captured_frame_count,
        "captured_function_count": len(hit_functions),
        "hit": bool(hit_functions),
        "hit_function_symbols": hit_functions,
        "missing_function_symbols": missing_functions,
        "watch_symbols": watch_symbols,
        "watch_count": len(watch_symbols),
        "trace_record_limit_hit": execute and captured_frame_count >= max_frames,
        "ready_for_dynamic_taint": execute and captured_frame_count > 0 and bool(watch_symbols),
        "warnings": warnings,
        "errors": errors,
    }


def write_trace_output(*, records: list[dict[str, Any]], out_trace: str, root: Path) -> dict[str, Any]:
    if not out_trace:
        return {"path": "", "written": False, "record_count": len(records), "errors": []}
    path = resolve_path(out_trace, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
        newline="\n",
    )
    return {"path": display_path(path, root=root), "written": True, "record_count": len(records), "errors": []}


def public_instruction(instruction: Instruction, *, function: str, symbol_table: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "function": function,
        "bank": instruction.bank,
        "pc": instruction.pc,
        "bank_address": f"{instruction.bank:02X}:{instruction.pc:04X}",
        "pc_label": render_pc(symbol_table, instruction.bank, instruction.pc),
        "opcode": instruction.opcode,
        "operand": list(instruction.operand),
        "length": instruction.length,
        "mnemonic": instruction.mnemonic,
    }


def empty_plan(symbol: str) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "bank": None,
        "address": None,
        "bank_address": "",
        "instruction_count": 0,
        "hook_count": 0,
        "instructions": [],
    }


def build_commands(
    *,
    function_symbols: tuple[str, ...],
    selected_function_symbols: tuple[str, ...],
    watch_symbols: tuple[str, ...],
    reports: tuple[str, ...],
    scenario_ids: tuple[str, ...],
    changed_files: tuple[str, ...],
    symptom: str,
    rom_path: str,
    symbols_path: str,
    save_state: str,
    frames: int,
    require_hit: bool,
    out_trace: str,
) -> list[str]:
    trace_path = out_trace or ".local\\tmp\\debugger_instruction_trace.jsonl"
    args = ["--rom", cmd_arg(rom_path), "--symbols", cmd_arg(symbols_path), "--frames", str(frames)]
    if save_state:
        args.extend(["--save-state", cmd_arg(save_state)])
    for report in reports:
        args.extend(["--report", cmd_arg(report)])
    for scenario_id in scenario_ids:
        args.extend(["--scenario-id", cmd_arg(scenario_id)])
    for path in changed_files:
        args.extend(["--changed-file", cmd_arg(path)])
    if symptom:
        args.extend(["--symptom", cmd_arg(symptom)])
    for symbol in selected_function_symbols or function_symbols:
        args.extend(["--symbol", cmd_arg(symbol)])
    for watch in watch_symbols:
        args.extend(["--watch-symbol", cmd_arg(watch)])
    if require_hit:
        args.append("--require-hit")
    args.extend(["--execute", "--out-trace", cmd_arg(trace_path)])
    commands = ["python -m tools.debugger trace-instructions " + " ".join(args)]
    commands.append(f"python -m tools.debugger trace-index --trace {trace_path}")
    commands.append(f"python -m tools.debugger minimize --trace {trace_path} --expect event=control_flow")
    for watch in watch_symbols[:4]:
        commands.append(f"python -m tools.debugger dynamic-taint --trace {trace_path} --sink-symbol {watch} --source-reg <register-or-origin>")
        commands.append(f"python -m tools.debugger expect --trace {trace_path} --expect contains={watch}")
    return unique_list(commands)


def rom_offset(*, bank: int, address: int) -> int:
    if address < 0x4000:
        return address
    return (int(bank) * 0x4000) + (int(address) - 0x4000)


def parse_hex_register(value: str) -> int:
    text = str(value or "0").strip()
    if not text:
        return 0
    return int(text, 16)


def is_traceable_function(symbol: str, symbol_table: dict[str, dict[str, Any]]) -> bool:
    entry = symbol_table.get(base_label(str(symbol)) or str(symbol))
    if not entry:
        return False
    address = int(entry["address"])
    return 0 <= address < 0x8000


def is_watch_symbol(symbol: str, symbol_table: dict[str, dict[str, Any]]) -> bool:
    entry = symbol_table.get(base_label(str(symbol)) or str(symbol))
    if not entry:
        return False
    address = int(entry["address"])
    return address >= 0x8000


def top_symbols(scores: dict[str, int], *, limit: int) -> list[str]:
    return [
        symbol
        for symbol, _score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]
        if symbol
    ]


def dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, dict)]


def string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple | set):
        return [nested for item in value for nested in string_items(item)]
    if isinstance(value, dict):
        return [nested for item in value.values() for nested in string_items(item)]
    return [str(value)] if value else []


def cmd_arg(value: str) -> str:
    text = str(value)
    if not text:
        return '""'
    if any(char.isspace() for char in text):
        return json.dumps(text)
    return text


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
