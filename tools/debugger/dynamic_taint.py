from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.damage_debugger.disasm import Instruction, render_mnemonic
from tools.damage_debugger.taint import Sink, TaintEngine

from .address import (
    address_key,
    address_key_requires_exact_match,
    address_spec_requires_exact_key,
    parse_address_int,
    parse_address_spec,
)
from .catalog import ROOT
from .coverage import load_traces
from .evidence import evidence_atom, evidence_atoms, merge_evidence_atoms, normalize_proof_status
from .explain import base_label
from .hardware_evidence import hardware_runtime_event_boundary
from .ingest import sha256_file
from .provenance import display_path, parse_symbol_table, resolve_path
from .reporting import load_reports
from .sm83_model import (
    CONDITIONAL_CALLS,
    CONDITIONAL_RETS,
    REGISTER_INDEX_TARGETS as INDEX_REG,
    RST_TARGETS,
    SM83_MODEL_SOURCE,
    accumulator_flag_semantics,
    add_hl_semantics,
    alu_semantics,
    cb_semantics,
    hli_hld_semantics,
    inc_dec_semantics,
    load_semantics,
    register_pair_inc_dec_semantics,
    sp_relative_semantics,
    stack_pop_component_value,
    stack_pop_register_value,
    stack_control_semantics,
)
from .workflow import (
    command_address_arg,
    command_is_runnable,
    command_option_values as workflow_command_option_values,
    command_parts as workflow_command_parts,
)


REGISTER_FIELDS = ("A", "F", "B", "C", "D", "E", "H", "L", "HL", "SP")
PROOF_STATUS_RANK = {
    "planned_only": 0,
    "state_materialized": 1,
    "mirror_passed": 2,
    "runtime_observed": 3,
    "instruction_observed": 4,
    "taint_proven": 5,
    "mirror_failed": 5,
}
HARDWARE_EVENT_REQUIRED_MODELS = {
    "oam_dma",
    "cgb_vram_dma",
    "timer_tima_overflow",
    "interrupt_entry",
    "lcd_mode_edge",
    "ppu_lcd_mode",
}
HARDWARE_EVENT_REQUIRED_KINDS = {
    "dma_read",
    "dma_write",
    "timer_tima_overflow",
    "timer_tima_reload_write",
    "timer_interrupt_request_write",
    "interrupt_entry",
}
OUTPUT_CONTAINER_KEYS = {
    "output",
    "outputs",
    "observed_output",
    "observed_outputs",
    "expected_output",
    "expected_outputs",
    "result_output",
    "result_outputs",
}
OUTPUT_SYMBOL_KEYS = {
    "output_symbol",
    "output_symbols",
    "output_state_symbol",
    "output_state_symbols",
    "output_watch_symbol",
    "output_watch_symbols",
    "result_symbol",
    "result_symbols",
}
OUTPUT_ADDRESS_KEYS = {
    "output_address",
    "output_addresses",
    "output_watch_address",
    "output_watch_addresses",
    "result_address",
    "result_addresses",
}
OUTPUT_SOURCE_SYMBOL_KEYS = {
    "input_symbol",
    "input_symbols",
    "source_state_symbol",
    "source_state_symbols",
    "source_mem_symbol",
    "source_mem_symbols",
}
OUTPUT_SOURCE_MEM_KEYS = {
    "input_address",
    "input_addresses",
    "source_address",
    "source_addresses",
    "source_mem",
    "source_mems",
}
OUTPUT_SOURCE_REG_KEYS = {"source_reg", "source_regs", "input_reg", "input_regs"}


@dataclass(frozen=True)
class InstructionFrame:
    seq: int
    bank: int
    pc: int
    pc_label: str
    A: int = 0
    F: int = 0
    B: int = 0
    C: int = 0
    D: int = 0
    E: int = 0
    H: int = 0
    L: int = 0
    HL: int = 0
    SP: int = 0
    memory: tuple[tuple[int, int], ...] = ()
    bank_state: tuple[tuple[str, int], ...] = ()
    bank_state_sources: tuple[tuple[str, str], ...] = ()
    known_registers: tuple[str, ...] = ()


def build_dynamic_taint_report(
    *,
    traces: tuple[str, ...] = (),
    reports: tuple[str, ...] = (),
    symbols_path: str = "pokegold.sym",
    source_regs: tuple[str, ...] = (),
    source_mems: tuple[str, ...] = (),
    source_symbols: tuple[str, ...] = (),
    sink_symbols: tuple[str, ...] = (),
    sink_addresses: tuple[str, ...] = (),
    sink_size: int = 1,
    max_paths: int = 40,
    execute_synthesis: bool = False,
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    effect_reports = effect_trace_reports_from_loaded(loaded_reports)
    discovered_inputs = discover_dynamic_taint_inputs(loaded_reports, root=root)
    effective_traces = tuple(unique_list([*traces, *discovered_inputs["traces"]]))
    effective_source_regs = tuple(unique_list([*source_regs, *discovered_inputs["source_regs"]]))
    effective_source_mems = tuple(unique_list([*source_mems, *discovered_inputs["source_mems"]]))
    effective_source_symbols = tuple(unique_list([*source_symbols, *discovered_inputs["source_symbols"]]))
    effective_sink_symbols = tuple(unique_list([*sink_symbols, *discovered_inputs["sink_symbols"]]))
    effective_sink_addresses = tuple(unique_sink_addresses([*sink_addresses, *discovered_inputs["sink_addresses"]]))
    effective_sink_size = effective_report_sink_size(
        requested=sink_size,
        discovered_sizes=discovered_inputs.get("sink_sizes", []),
        has_raw_sinks=bool(effective_sink_addresses),
    )
    trace_synthesis_plan = build_trace_synthesis_plan(
        loaded_reports=loaded_reports,
        reports=reports,
        sink_symbols=effective_sink_symbols,
        sink_addresses=effective_sink_addresses,
        source_regs=effective_source_regs,
        source_mems=effective_source_mems,
        source_symbols=effective_source_symbols,
        sink_size=effective_sink_size,
        symbols_path=symbols_path,
        trace_needed=not bool(effective_traces or effect_reports),
        root=root,
    )
    synthesis_execution = execute_trace_synthesis_plan(
        trace_synthesis_plan=trace_synthesis_plan,
        loaded_reports=loaded_reports,
        symbols_path=symbols_path,
        execute=execute_synthesis and not bool(effective_traces),
        root=root,
    )
    effective_traces = tuple(unique_list([*effective_traces, *synthesis_execution.get("traces", [])]))

    loaded_traces, trace_errors = load_traces(traces=effective_traces, root=root)
    sym_path = resolve_path(symbols_path, root=root)
    errors = [*report_errors, *trace_errors, *string_items(synthesis_execution.get("errors"))]
    warnings: list[str] = []
    if not effective_traces and not effect_reports:
        if trace_synthesis_plan["route_count"]:
            if execute_synthesis:
                errors.append("trace synthesis executed but did not produce a usable instruction trace")
            else:
                warnings.append(
                    "no instruction trace was supplied; emitting trace/save-state synthesis routes before dynamic taint can run"
                )
        else:
            errors.append("at least one --trace or trace-producing --report is required")
    warnings.extend(string_items(synthesis_execution.get("warnings")))
    if sink_size < 1:
        errors.append("--sink-size must be positive")
    if max_paths < 1:
        errors.append("--max-paths must be positive")

    symbol_table: dict[str, dict[str, Any]] = {}
    if sym_path.exists():
        symbol_table = parse_symbol_table(sym_path)
    else:
        errors.append(f"missing symbol file: {symbols_path}")

    source_memory, source_errors = parse_memory_sources(
        source_mems=effective_source_mems,
        source_symbols=effective_source_symbols,
        symbol_table=symbol_table,
    )
    source_address_specs = source_address_spec_records(
        source_mems=effective_source_mems,
        source_symbols=effective_source_symbols,
        symbol_table=symbol_table,
    )
    register_sources, register_errors = parse_register_sources(effective_source_regs)
    sinks, sink_errors = parse_sinks(
        sink_symbols=effective_sink_symbols,
        sink_addresses=effective_sink_addresses,
        sink_size=effective_sink_size,
        symbol_table=symbol_table,
    )
    sink_address_specs = sink_address_spec_records(
        sink_symbols=effective_sink_symbols,
        sink_addresses=effective_sink_addresses,
        sink_size=effective_sink_size,
        symbol_table=symbol_table,
    )
    annotate_sink_address_specs(sinks, sink_address_specs)
    address_precision = address_precision_report(
        source_address_specs=source_address_specs,
        sink_address_specs=sink_address_specs,
    )
    warnings.extend(address_precision["warnings"])
    errors.extend([*source_errors, *register_errors, *sink_errors])
    if not register_sources and not source_memory:
        warnings.append(
            "no taint sources supplied; reporting exact sink writes without source-to-sink taint paths"
        )
    if not sinks:
        errors.append("at least one --sink-symbol, --sink-address, or report-discovered sink is required")

    trace_runs = [
        analyze_instruction_trace(
            loaded,
            register_sources=register_sources,
            source_memory=source_memory,
            source_address_specs=source_address_specs,
            sinks=sinks,
            symbol_table=symbol_table,
        )
        for loaded in loaded_traces
    ] if not errors else []
    effect_trace_runs = [
        analyze_effect_trace_report(
            loaded,
            register_sources=register_sources,
            source_memory=source_memory,
            source_address_specs=source_address_specs,
            sinks=sinks,
            symbol_table=symbol_table,
        )
        for loaded in effect_reports
    ] if not errors else []
    warnings.extend(
        warning
        for run in [*trace_runs, *effect_trace_runs]
        for warning in run.get("warnings", [])
    )
    bank_state_record_conflicts = [
        conflict
        for run in trace_runs
        for conflict in dict_items(run.get("bank_state_record_conflicts"))
    ]
    warnings.extend(bank_state_record_conflict_warnings(bank_state_record_conflicts))
    findings = [
        finding
        for run in [*trace_runs, *effect_trace_runs]
        for finding in run.get("findings", [])
    ]
    paths = build_paths(
        findings=findings,
        sinks=sinks,
        register_sources=register_sources,
        source_memory=source_memory,
        max_paths=max_paths,
    )
    write_attributions = [
        attribution
        for run in [*trace_runs, *effect_trace_runs]
        for attribution in run.get("write_attributions", [])
    ]
    unmodeled_write_diagnostics = [
        diagnostic
        for run in trace_runs
        for diagnostic in run.get("unmodeled_write_diagnostics", [])
    ]
    commands = build_commands(
        paths=paths,
        write_attributions=write_attributions,
        traces=effective_traces,
        effect_reports=tuple(str(loaded.get("source", "")) for loaded in effect_reports),
        sink_symbols=effective_sink_symbols,
        sink_addresses=effective_sink_addresses,
        sink_size=effective_sink_size,
        trace_synthesis_plan=trace_synthesis_plan,
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_dynamic_taint_report",
        "root": str(root),
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "symbols_path": display_path(sym_path, root=root),
        "symbols_sha256": sha256_file(sym_path) if sym_path.exists() else "",
        "reports": [loaded["source"] for loaded in loaded_reports],
        "report_count": len(loaded_reports),
        "input_discovery": discovered_inputs,
        "trace_synthesis_plan": trace_synthesis_plan,
        "trace_synthesis_execution": synthesis_execution,
        "trace_synthesis_executed": bool(synthesis_execution.get("attempted")),
        "trace_synthesis_route_count": trace_synthesis_plan["route_count"],
        "trace_count": len(loaded_traces),
        "effect_trace_report_count": len(effect_reports),
        "requested_traces": list(traces),
        "effective_traces": list(effective_traces),
        "source_count": len(register_sources) + len(source_memory),
        "sink_count": len(sinks),
        "sink_size": effective_sink_size,
        "source_address_specs": source_address_specs,
        "sink_address_specs": sink_address_specs,
        "address_precision": address_precision,
        "finding_count": len(findings),
        "path_count": len(paths),
        "write_attribution_count": len(write_attributions),
        "unmodeled_write_diagnostic_count": len(unmodeled_write_diagnostics),
        "bank_state_record_conflict_count": len(bank_state_record_conflicts),
        "bank_state_record_conflicts": bank_state_record_conflicts[:80],
        "sources": source_summary(register_sources=register_sources, source_memory=source_memory),
        "sinks": [public_sink(sink) for sink in sinks],
        "targets": targets_for_sinks(
            sinks=sinks,
            paths=paths,
            write_attributions=write_attributions,
        ),
        "trace_runs": trace_runs,
        "effect_trace_runs": effect_trace_runs,
        "findings": findings[:120],
        "paths": paths,
        "write_attributions": write_attributions[:120],
        "unmodeled_write_diagnostics": unmodeled_write_diagnostics[:120],
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This is emulator-trace-backed SM83 byte taint over supplied instruction frames or effect-trace reports; it is only as complete as the traced instruction/effect window.",
            "Without explicit source seeds, the report still identifies exact sink-writing instructions and source operands, but cannot claim source-to-sink taint.",
            "Raw bank-qualified source and sink addresses are preserved as AddressSpec records; taint propagation still uses the observed 16-bit bus address until runtime bank evidence is attached.",
            "Unsupported opcodes are reported and clear modeled destinations rather than inventing dependencies.",
            "Use trace-instruction capture, effect-trace capture, or focused subsystem replay to produce dense observed evidence before relying on this as final proof.",
        ],
    }


def effect_trace_reports_from_loaded(loaded_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        loaded
        for loaded in loaded_reports
        if loaded.get("data", {}).get("kind") == "unified_debugger_effect_trace"
    ]


def discover_dynamic_taint_inputs(loaded_reports: list[dict[str, Any]], *, root: Path) -> dict[str, Any]:
    traces: list[str] = []
    sink_symbols: list[str] = []
    sink_addresses: list[str] = []
    sink_sizes: list[int] = []
    source_regs: list[str] = []
    source_mems: list[str] = []
    source_symbols: list[str] = []
    trace_candidates: list[dict[str, Any]] = []
    for loaded in loaded_reports:
        data = loaded.get("data")
        if not isinstance(data, dict):
            continue
        discovered = discover_dynamic_taint_inputs_from_report(
            data,
            source=str(loaded.get("source", "")),
            report_path=loaded.get("path"),
            root=root,
        )
        trace_candidates.extend(discovered["trace_candidates"])
        traces.extend(discovered["traces"])
        sink_symbols.extend(discovered["sink_symbols"])
        sink_addresses.extend(discovered["sink_addresses"])
        sink_sizes.extend(int(size) for size in discovered["sink_sizes"])
        source_regs.extend(discovered["source_regs"])
        source_mems.extend(discovered["source_mems"])
        source_symbols.extend(discovered["source_symbols"])
    return {
        "trace_candidates": trace_candidates[:24],
        "traces": unique_list(traces),
        "sink_symbols": unique_list(sink_symbols),
        "sink_addresses": unique_sink_addresses(sink_addresses),
        "sink_sizes": unique_ints(sink_sizes),
        "source_regs": unique_list(source_regs),
        "source_mems": unique_list(source_mems),
        "source_symbols": unique_list(source_symbols),
    }


def discover_dynamic_taint_inputs_from_report(
    data: dict[str, Any],
    *,
    source: str,
    report_path: Any,
    root: Path,
) -> dict[str, Any]:
    traces: list[str] = []
    trace_candidates: list[dict[str, Any]] = []
    for raw_path, written, key in dynamic_taint_trace_candidates(data):
        path = resolve_report_artifact_path(str(raw_path), report_path=report_path, root=root)
        trace_candidates.append(
            {
                "source": source,
                "raw_path": raw_path,
                "path": path,
                "key": key,
                "written": written,
                "selected": bool(path and written),
            }
        )
        if path and written:
            traces.append(path)

    source_config = data.get("dynamic_taint_sources") if isinstance(data.get("dynamic_taint_sources"), dict) else {}
    sink_config = data.get("dynamic_taint_sinks") if isinstance(data.get("dynamic_taint_sinks"), dict) else {}
    kind = str(data.get("kind", ""))
    validation = data.get("execution_validation") if isinstance(data.get("execution_validation"), dict) else {}
    validation_watch_sinks = split_symbol_and_address_sinks(validation.get("watch_symbols"))
    validation_watch_addresses = string_items(validation.get("watch_addresses"))
    report_watch_sinks = watch_sinks_from_report(data)
    if kind == "unified_debugger_effect_trace":
        related_sinks = {"symbols": [], "addresses": []}
    else:
        related_sinks = related_sinks_from_report(data)
    output_inputs = output_taint_inputs_from_report(data)
    state_patch_minimization = state_patch_minimization_inputs(data)
    sink_sizes = sink_sizes_from_report(data, sink_config=sink_config)
    return {
        "trace_candidates": trace_candidates,
        "traces": traces,
        "sink_symbols": unique_list(
            [
                *string_items(sink_config.get("symbols")),
                *string_items(sink_config.get("sink_symbols")),
                *validation_watch_sinks["symbols"],
                *report_watch_sinks["symbols"],
                *state_patch_symbols_from_report(data),
                *state_patch_minimization["sink_symbols"],
                *related_sinks["symbols"],
                *output_inputs["sink_symbols"],
            ]
        ),
        "sink_addresses": unique_sink_addresses(
            [
                *string_items(sink_config.get("addresses")),
                *string_items(sink_config.get("sink_addresses")),
                *validation_watch_sinks["addresses"],
                *validation_watch_addresses,
                *report_watch_sinks["addresses"],
                *state_patch_minimization["sink_addresses"],
                *related_sinks["addresses"],
                *output_inputs["sink_addresses"],
            ]
        ),
        "sink_sizes": unique_ints([*sink_sizes, *state_patch_minimization["sink_sizes"], *output_inputs["sink_sizes"]]),
        "source_regs": unique_list(
            [
                *string_items(source_config.get("regs")),
                *string_items(source_config.get("registers")),
                *string_items(source_config.get("source_regs")),
                *output_inputs["source_regs"],
            ]
        ),
        "source_mems": unique_list(
            [
                *string_items(source_config.get("mems")),
                *string_items(source_config.get("memory")),
                *string_items(source_config.get("source_mems")),
                *state_patch_source_mems_from_report(data),
                *state_patch_minimization["source_mems"],
                *output_inputs["source_mems"],
            ]
        ),
        "source_symbols": unique_list(
            [
                *string_items(source_config.get("symbols")),
                *string_items(source_config.get("source_symbols")),
                *output_inputs["source_symbols"],
            ]
        ),
    }


def dynamic_taint_trace_candidates(data: dict[str, Any]) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    trace_output = data.get("trace_output") if isinstance(data.get("trace_output"), dict) else {}
    if trace_output.get("path"):
        out.append((str(trace_output.get("path", "")), bool(trace_output.get("written")), "trace_output.path"))
    evidence_minimization = data.get("evidence_minimization") if isinstance(data.get("evidence_minimization"), dict) else {}
    if evidence_minimization.get("out_trace"):
        out.append(
            (
                str(evidence_minimization.get("out_trace", "")),
                bool(evidence_minimization.get("written", True)),
                "evidence_minimization.out_trace",
            )
        )
    for key in ("out_trace", "trace"):
        if isinstance(data.get(key), str) and data.get(key):
            out.append((str(data[key]), True, key))
    return out


def resolve_report_artifact_path(raw_path: str, *, report_path: Any, root: Path) -> str:
    if not raw_path:
        return ""
    path = Path(raw_path)
    if path.is_absolute():
        return display_path(path, root=root)
    candidates = []
    if isinstance(report_path, Path):
        candidates.append(report_path.parent / path)
    candidates.append(root / path)
    for candidate in candidates:
        if candidate.exists():
            return display_path(candidate, root=root)
    return raw_path


def watch_sinks_from_report(data: dict[str, Any]) -> dict[str, list[str]]:
    symbols: list[str] = []
    addresses: list[str] = []
    top_level_watch_sinks = split_symbol_and_address_sinks(data.get("watch_symbols"))
    symbols.extend(top_level_watch_sinks["symbols"])
    addresses.extend(top_level_watch_sinks["addresses"])
    addresses.extend(string_items(data.get("watch_addresses")))
    for watch in dict_items(data.get("watches")):
        value = str(watch.get("name") or watch.get("symbol") or watch.get("watch") or "")
        address = sink_address_from_watch(watch, value)
        if address:
            addresses.append(address)
        else:
            symbols.extend(string_items(value))
    for event in dict_items(data.get("events")):
        value = str(event.get("watch") or "")
        address = sink_address_from_watch(event, value)
        if address:
            addresses.append(address)
        else:
            symbols.extend(string_items(value))
    return {
        "symbols": unique_list(symbols),
        "addresses": unique_sink_addresses(addresses),
    }


def watch_symbols_from_report(data: dict[str, Any]) -> list[str]:
    return watch_sinks_from_report(data)["symbols"]


def watch_addresses_from_report(data: dict[str, Any]) -> list[str]:
    return watch_sinks_from_report(data)["addresses"]


def related_sinks_from_report(data: dict[str, Any]) -> dict[str, list[str]]:
    symbols: list[str] = []
    addresses: list[str] = []
    collect_related_sinks(data, symbols=symbols, addresses=addresses)
    return {
        "symbols": unique_list(symbols),
        "addresses": unique_sink_addresses(addresses),
    }


def collect_related_sinks(value: Any, *, symbols: list[str], addresses: list[str]) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if lowered in {"related_addresses", "watch_addresses", "sink_addresses"}:
                for address in string_items(nested):
                    if sink_address_candidate(address):
                        addresses.append(address)
            elif lowered in {"address", "bank_address", "watch_address", "sink_address"}:
                for address in string_items(nested):
                    if sink_address_candidate(address):
                        addresses.append(address)
            elif lowered in {"state_symbol", "watch_symbol", "sink_symbol"}:
                for symbol in string_items(nested):
                    if symbol and not sink_address_candidate(symbol):
                        symbols.append(base_label(symbol) or symbol)
            elif lowered == "related_symbols":
                for symbol in string_items(nested):
                    normalized = base_label(symbol) or symbol
                    if looks_like_state_symbol(normalized):
                        symbols.append(normalized)
            collect_related_sinks(nested, symbols=symbols, addresses=addresses)
    elif isinstance(value, list | tuple):
        for item in value:
            collect_related_sinks(item, symbols=symbols, addresses=addresses)


def output_taint_inputs_from_report(data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, list[Any]] = {
        "sink_symbols": [],
        "sink_addresses": [],
        "sink_sizes": [],
        "source_regs": [],
        "source_mems": [],
        "source_symbols": [],
    }
    collect_output_taint_inputs(data, out=out, in_output=False)
    return {
        "sink_symbols": unique_list(str(item) for item in out["sink_symbols"] if item),
        "sink_addresses": unique_sink_addresses(out["sink_addresses"]),
        "sink_sizes": unique_ints(out["sink_sizes"]),
        "source_regs": unique_list(str(item) for item in out["source_regs"] if item),
        "source_mems": unique_list(str(item) for item in out["source_mems"] if item),
        "source_symbols": unique_list(str(item) for item in out["source_symbols"] if item),
    }


def collect_output_taint_inputs(value: Any, *, out: dict[str, list[Any]], in_output: bool) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if lowered in OUTPUT_CONTAINER_KEYS:
                collect_output_taint_inputs(nested, out=out, in_output=True)
                continue
            if lowered in OUTPUT_SYMBOL_KEYS or (in_output and lowered in {"symbol", "state_symbol", "watch_symbol", "sink_symbol"}):
                for symbol in string_items(nested):
                    normalized = base_label(symbol) or symbol
                    if normalized and not sink_address_candidate(normalized):
                        out["sink_symbols"].append(normalized)
                    else:
                        out["sink_addresses"].append(normalized)
            elif lowered in OUTPUT_ADDRESS_KEYS or (in_output and lowered in {"address", "bank_address", "watch_address", "sink_address"}):
                for address in string_items(nested):
                    if sink_address_candidate(address):
                        out["sink_addresses"].append(address)
            elif lowered in {"output_size", "output_watch_size", "sink_size", "watch_size", "size"} and in_output:
                size = positive_int(nested)
                if size:
                    out["sink_sizes"].append(size)
            elif lowered in OUTPUT_SOURCE_REG_KEYS:
                out["source_regs"].extend(string_items(nested))
            elif lowered in OUTPUT_SOURCE_MEM_KEYS:
                for address in string_items(nested):
                    if sink_address_candidate(address):
                        out["source_mems"].append(address)
            elif lowered in OUTPUT_SOURCE_SYMBOL_KEYS or (in_output and lowered in {"input_symbol", "source_state_symbol", "source_mem_symbol"}):
                for symbol in string_items(nested):
                    normalized = base_label(symbol) or symbol
                    if looks_like_state_symbol(normalized):
                        out["source_symbols"].append(normalized)
            collect_output_taint_inputs(nested, out=out, in_output=in_output)
    elif isinstance(value, list | tuple):
        for item in value:
            collect_output_taint_inputs(item, out=out, in_output=in_output)


def looks_like_state_symbol(symbol: str) -> bool:
    text = str(symbol).strip()
    return len(text) >= 2 and text[0] in {"w", "h", "s", "v", "r"} and text[1].isupper()


def sink_sizes_from_report(data: dict[str, Any], *, sink_config: dict[str, Any]) -> list[int]:
    sizes: list[int] = []
    for value in (
        sink_config.get("size"),
        sink_config.get("sink_size"),
        data.get("sink_size"),
        data.get("watch_size"),
    ):
        size = positive_int(value)
        if size:
            sizes.append(size)
    validation = data.get("execution_validation") if isinstance(data.get("execution_validation"), dict) else {}
    size = positive_int(validation.get("watch_size"))
    if size:
        sizes.append(size)
    for watch in dict_items(data.get("watches")):
        if watch.get("address_watch"):
            size = positive_int(watch.get("size") or watch.get("watch_size"))
            if size:
                sizes.append(size)
    for event in dict_items(data.get("events")):
        if sink_address_from_watch(event, str(event.get("watch") or "")):
            size = positive_int(event.get("watch_size") or event.get("size"))
            if size:
                sizes.append(size)
    sizes.extend(related_sink_sizes_from_report(data))
    return unique_ints(sizes)


def related_sink_sizes_from_report(data: dict[str, Any]) -> list[int]:
    sizes: list[int] = []
    collect_related_sink_sizes(data, sizes=sizes)
    return unique_ints(sizes)


def collect_related_sink_sizes(value: Any, *, sizes: list[int]) -> None:
    if isinstance(value, dict):
        if mapping_has_raw_sink(value):
            for key in ("sink_size", "watch_size", "size"):
                size = positive_int(value.get(key))
                if size:
                    sizes.append(size)
        for nested in value.values():
            collect_related_sink_sizes(nested, sizes=sizes)
    elif isinstance(value, list | tuple):
        for item in value:
            collect_related_sink_sizes(item, sizes=sizes)


def mapping_has_raw_sink(value: dict[str, Any]) -> bool:
    for key in ("related_addresses", "watch_addresses", "sink_addresses"):
        if any(sink_address_candidate(address) for address in string_items(value.get(key))):
            return True
    for key in ("address", "bank_address", "watch_address", "sink_address", "raw", "watch"):
        if any(sink_address_candidate(address) for address in string_items(value.get(key))):
            return True
    return False


def effective_report_sink_size(*, requested: int, discovered_sizes: Any, has_raw_sinks: bool) -> int:
    if not has_raw_sinks:
        return requested
    sizes = [requested, *[size for size in unique_ints(discovered_sizes) if size > 0]]
    return max(sizes) if sizes else requested


def split_symbol_and_address_sinks(value: Any) -> dict[str, list[str]]:
    symbols: list[str] = []
    addresses: list[str] = []
    for item in string_items(value):
        address = sink_address_candidate(item)
        if address:
            addresses.append(address)
        else:
            symbols.append(item)
    return {
        "symbols": unique_list(symbols),
        "addresses": unique_sink_addresses(addresses),
    }


def sink_address_from_watch(watch: dict[str, Any], value: str) -> str:
    if watch.get("address_watch"):
        raw = str(watch.get("raw") or value)
        return sink_address_candidate(raw) or sink_address_candidate(str(watch.get("bank_address") or "")) or raw
    return sink_address_candidate(value)


def sink_address_candidate(value: str) -> str:
    text = str(value).strip()
    if not text:
        return ""
    if "=" in text:
        text = text.split("=", 1)[1].strip()
    has_address_marker = (
        text.startswith("$")
        or text.startswith(("0x", "0X"))
        or ":" in text
        or (len(text) == 4 and all(char in "0123456789abcdefABCDEF" for char in text))
    )
    if not has_address_marker:
        return ""
    try:
        parse_address(text)
    except ValueError:
        return ""
    return text


def state_patch_symbols_from_report(data: dict[str, Any]) -> list[str]:
    out = []
    for patch in dict_items(data.get("state_patches")):
        out.extend(string_items(patch.get("base_symbol") or patch.get("symbol")))
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    for patch in [*dict_items(state_space.get("patches")), *dict_items(state_space.get("state_patches"))]:
        out.extend(string_items(patch.get("base_symbol") or patch.get("symbol")))
    for materialization in dict_items(data.get("materializations")):
        for patch in dict_items(materialization.get("patches")):
            out.extend(string_items(patch.get("base_symbol") or patch.get("symbol")))
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    for patch in dict_items(execution.get("applied_patches")):
        out.extend(string_items(patch.get("base_symbol") or patch.get("symbol")))
    return unique_list(base_label(symbol) or symbol for symbol in out)


def state_patch_source_mems_from_report(data: dict[str, Any]) -> list[str]:
    return unique_list(
        source
        for patch in state_patch_records_from_report(data)
        for source in state_patch_source_mem_specs([patch])
    )


def state_patch_records_from_report(data: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    out.extend(dict_items(data.get("state_patches")))
    state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
    out.extend(dict_items(state_space.get("patches")))
    out.extend(dict_items(state_space.get("state_patches")))
    for materialization in dict_items(data.get("materializations")):
        out.extend(dict_items(materialization.get("patches")))
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    out.extend(dict_items(execution.get("applied_patches")))
    return out


def state_patch_source_mem_specs(patches: list[dict[str, Any]]) -> list[str]:
    sources: list[str] = []
    for patch in patches:
        address = state_patch_address_text(patch)
        if not address:
            continue
        origin = str(patch.get("base_symbol") or patch.get("symbol") or "").strip()
        if origin:
            sources.append(f"{address}={origin}")
        else:
            sources.append(address)
    return unique_list(sources)


def state_patch_address_text(patch: dict[str, Any]) -> str:
    bank_address = str(patch.get("bank_address", "")).strip()
    if bank_address:
        return bank_address
    address = patch.get("address")
    if isinstance(address, int):
        return f"{address & 0xFFFF:04X}"
    text = str(address or "").strip()
    return text


def state_patch_minimization_inputs(data: dict[str, Any]) -> dict[str, list[Any]]:
    minimization = data.get("state_patch_minimization")
    if not isinstance(minimization, dict) or not minimization.get("attempted"):
        return {
            "sink_symbols": [],
            "sink_addresses": [],
            "sink_sizes": [],
            "source_mems": [],
        }
    return {
        "sink_symbols": state_patch_minimization_related_symbols(minimization),
        "sink_addresses": state_patch_minimization_related_addresses(minimization),
        "sink_sizes": [size for size in [positive_int(minimization.get("watch_size"))] if size],
        "source_mems": state_patch_minimization_source_mems(minimization),
    }


def state_patch_minimization_related_symbols(item: dict[str, Any]) -> list[str]:
    symbols = [
        *string_items(item.get("watch_symbols")),
        *string_items(item.get("semantic_watch_symbols")),
    ]
    for _address, origin in source_mem_parts(item):
        if origin:
            symbols.append(origin)
    for result in dict_items(item.get("results")):
        symbols.extend(string_items(result.get("semantic_watch_symbols")))
        for _address, origin in source_mem_parts(result):
            if origin:
                symbols.append(origin)
    return unique_list(base_label(symbol) or symbol for symbol in symbols if symbol)


def state_patch_minimization_related_addresses(item: dict[str, Any]) -> list[str]:
    addresses = [
        *string_items(item.get("watch_addresses")),
        *[address for address, _origin in source_mem_parts(item)],
    ]
    for result in dict_items(item.get("results")):
        addresses.extend(string_items(result.get("semantic_watch_addresses")))
        addresses.extend(string_items(result.get("semantic_replay_watch_addresses")))
        addresses.extend(address for address, _origin in source_mem_parts(result))
    return unique_sink_addresses(addresses)


def state_patch_minimization_source_mems(item: dict[str, Any]) -> list[str]:
    source_mems = string_items(item.get("source_mems"))
    for result in dict_items(item.get("results")):
        source_mems.extend(string_items(result.get("source_mems")))
    return unique_list(source_mems)


def state_patch_minimization_source_symbols(item: dict[str, Any]) -> list[str]:
    symbols = string_items(item.get("source_symbols"))
    for result in dict_items(item.get("results")):
        symbols.extend(string_items(result.get("source_symbols")))
    return unique_list(base_label(symbol) or symbol for symbol in symbols if symbol)


def source_mem_parts(item: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for raw in string_items(item.get("source_mems")):
        text = str(raw).strip()
        if not text:
            continue
        if "=" in text:
            address, origin = text.split("=", 1)
            out.append((address.strip(), origin.strip()))
        else:
            out.append((text, ""))
    return out


def build_trace_synthesis_plan(
    *,
    loaded_reports: list[dict[str, Any]],
    reports: tuple[str, ...],
    sink_symbols: tuple[str, ...],
    sink_addresses: tuple[str, ...],
    source_regs: tuple[str, ...],
    source_mems: tuple[str, ...],
    source_symbols: tuple[str, ...],
    sink_size: int,
    symbols_path: str,
    trace_needed: bool,
    root: Path,
) -> dict[str, Any]:
    if not trace_needed:
        return {
            "attempted": False,
            "reason": "instruction trace input is already available",
            "route_count": 0,
            "routes": [],
            "commands": [],
        }
    if not loaded_reports:
        return {
            "attempted": False,
            "reason": "no reports were supplied for trace/save-state synthesis",
            "route_count": 0,
            "routes": [],
            "commands": [],
        }
    routes = [
        route
        for loaded in loaded_reports
        for route in trace_synthesis_routes_for_report(
            loaded,
            sink_symbols=sink_symbols,
            sink_addresses=sink_addresses,
            source_regs=source_regs,
            source_mems=source_mems,
            source_symbols=source_symbols,
            sink_size=sink_size,
            symbols_path=symbols_path,
            root=root,
        )
    ]
    commands = unique_list(command for route in routes for command in route.get("commands", []))
    return {
        "attempted": True,
        "input_reports": list(reports),
        "route_count": len(routes),
        "routes": routes[:24],
        "commands": commands[:80],
    }


def execute_trace_synthesis_plan(
    *,
    trace_synthesis_plan: dict[str, Any],
    loaded_reports: list[dict[str, Any]],
    symbols_path: str,
    execute: bool,
    root: Path,
) -> dict[str, Any]:
    if not execute:
        return {
            "attempted": False,
            "reason": "execution was not requested",
            "route_count": int(trace_synthesis_plan.get("route_count", 0)),
            "executed_route_count": 0,
            "traces": [],
            "reports": [],
            "errors": [],
            "warnings": [],
            "routes": [],
        }
    reports_by_source = {str(loaded.get("source", "")): loaded for loaded in loaded_reports}
    results = [
        execute_trace_synthesis_route(
            route,
            loaded_report=reports_by_source.get(str(route.get("source_report", ""))),
            symbols_path=symbols_path,
            root=root,
        )
        for route in dict_items(trace_synthesis_plan.get("routes"))
    ]
    return {
        "attempted": True,
        "route_count": int(trace_synthesis_plan.get("route_count", 0)),
        "executed_route_count": len([result for result in results if result.get("attempted")]),
        "successful_route_count": len([result for result in results if result.get("trace_written")]),
        "traces": unique_list(result.get("trace_output", "") for result in results if result.get("trace_written")),
        "reports": unique_list(result.get("trace_report", "") for result in results if result.get("trace_report_written")),
        "errors": unique_list(error for result in results for error in string_items(result.get("errors"))),
        "warnings": unique_list(warning for result in results for warning in string_items(result.get("warnings"))),
        "routes": results[:24],
    }


def execute_trace_synthesis_route(
    route: dict[str, Any],
    *,
    loaded_report: dict[str, Any] | None,
    symbols_path: str,
    root: Path,
) -> dict[str, Any]:
    if loaded_report is None or not isinstance(loaded_report.get("data"), dict):
        return {
            "attempted": False,
            "route_id": str(route.get("id", "")),
            "errors": [f"missing source report for trace synthesis: {route.get('source_report', '')}"],
            "warnings": [],
        }
    if route.get("source_kind") == "unified_debugger_compare_plan":
        return {
            "attempted": False,
            "route_id": str(route.get("id", "")),
            "source_report": str(route.get("source_report", "")),
            "trace_written": False,
            "trace_report_written": False,
            "errors": [],
            "warnings": [
                "compare-plan trace synthesis requires running the route materialization and trace commands in order"
            ],
            "commands": list(route.get("commands", [])),
        }
    source_report = str(route.get("source_report", ""))
    trace_source_report = source_report
    materialization_result: dict[str, Any] | None = None
    if route.get("state_status") == "materialization-planned":
        materialization_result = execute_materialization_for_trace_synthesis(
            route,
            loaded_report=loaded_report,
            symbols_path=symbols_path,
            root=root,
        )
        if not materialization_result.get("valid"):
            return {
                "attempted": True,
                "route_id": str(route.get("id", "")),
                "materialization": materialization_result,
                "trace_written": False,
                "trace_report_written": False,
                "errors": string_items(materialization_result.get("errors")),
                "warnings": string_items(materialization_result.get("warnings")),
            }
        trace_source_report = str(materialization_result.get("report", trace_source_report))
    trace_result = execute_instruction_trace_for_synthesis(
        report=trace_source_report,
        route=route,
        symbols_path=symbols_path,
        root=root,
    )
    return {
        "attempted": True,
        "route_id": str(route.get("id", "")),
        "source_report": source_report,
        "trace_source_report": trace_source_report,
        "materialization": materialization_result,
        **trace_result,
    }


def execute_materialization_for_trace_synthesis(
    route: dict[str, Any],
    *,
    loaded_report: dict[str, Any],
    symbols_path: str,
    root: Path,
) -> dict[str, Any]:
    data = loaded_report["data"]
    kind = str(data.get("kind", ""))
    if kind == "unified_debugger_content_state_materialization":
        from .content_state import execute_materialization

        out_state = resolve_path(str(route.get("materialized_state", "")), root=root)
        base_state_text = str(data.get("base_save_state") or "")
        base_state = resolve_path(base_state_text, root=root) if base_state_text else None
        rom = resolve_path(str(data.get("rom") or "pokegold.gbc"), root=root)
        execution = execute_materialization(
            materializations=dict_items(data.get("materializations")),
            rom=rom,
            base_state=base_state,
            output_state=out_state,
            execute=True,
            root=root,
        )
        out = {
            **data,
            "executed": bool(execution.get("executed")),
            "out_state": str(execution.get("out_state", "")),
            "execution": execution,
        }
        report_path = resolve_path(str(route.get("materialized_report", "")), root=root)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
        return {
            "valid": bool(execution.get("executed")),
            "report": display_path(report_path, root=root),
            "out_state": str(execution.get("out_state", "")),
            "errors": list(execution.get("errors", [])),
            "warnings": list(execution.get("warnings", [])),
        }
    if kind == "unified_debugger_state_space":
        from .state_space import execute_state_space

        state_space = data.get("state_space") if isinstance(data.get("state_space"), dict) else {}
        out_state = resolve_path(str(route.get("materialized_state", "")), root=root)
        base_state_text = str(data.get("base_save_state") or state_space.get("base_save_state") or "")
        base_state = resolve_path(base_state_text, root=root) if base_state_text else None
        rom = resolve_path(str(data.get("rom") or "pokegold.gbc"), root=root)
        execution = execute_state_space(
            patches=dict_items(state_space.get("patches")),
            rom=rom,
            base_state=base_state,
            output_state=out_state,
            execute=True,
            root=root,
        )
        out = copy_report_with_state_space_execution(data, execution)
        report_path = resolve_path(str(route.get("materialized_report", "")), root=root)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
        return {
            "valid": bool(execution.get("executed")),
            "report": display_path(report_path, root=root),
            "out_state": str(execution.get("out_state", "")),
            "errors": list(execution.get("errors", [])),
            "warnings": list(execution.get("warnings", [])),
        }
    return {
        "valid": False,
        "errors": [f"unsupported trace synthesis materialization source: {kind or '<unknown>'}"],
        "warnings": [],
    }


def copy_report_with_state_space_execution(data: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
    copied = json.loads(json.dumps(data))
    copied["executed"] = bool(execution.get("executed"))
    copied["out_state"] = str(execution.get("out_state", ""))
    copied["execution"] = execution
    state_space = copied.setdefault("state_space", {})
    if isinstance(state_space, dict):
        state_space["out_state"] = str(execution.get("out_state", ""))
        state_space["patches"] = list(execution.get("applied_patches") or state_space.get("patches") or [])
        state_space["patch_count"] = len(state_space["patches"])
    return copied


def execute_instruction_trace_for_synthesis(
    *,
    report: str,
    route: dict[str, Any],
    symbols_path: str,
    root: Path,
) -> dict[str, Any]:
    from .instruction_trace import build_instruction_trace_report

    trace_report_path = resolve_path(str(route.get("trace_report", "")), root=root)
    trace = build_instruction_trace_report(
        reports=(report,),
        save_state=str(route.get("save_state", "")),
        sink_symbols=tuple(string_items(route.get("sink_symbols"))),
        watch_addresses=tuple(string_items(route.get("sink_addresses"))),
        watch_size=max(1, int(route.get("sink_size") or 1)),
        symbols_path=symbols_path,
        rom_path=str(route.get("rom") or "pokegold.gbc"),
        execute=True,
        require_hit=True,
        out_trace=str(route.get("trace_output", "")),
        root=root,
    )
    trace_report_path.parent.mkdir(parents=True, exist_ok=True)
    trace_report_path.write_text(json.dumps(trace, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    trace_output = trace.get("trace_output") if isinstance(trace.get("trace_output"), dict) else {}
    return {
        "trace_report": display_path(trace_report_path, root=root),
        "trace_report_written": True,
        "trace_output": str(trace_output.get("path", "")),
        "trace_written": bool(trace_output.get("written")) and int(trace_output.get("record_count", 0)) > 0,
        "trace_record_count": int(trace_output.get("record_count", 0)),
        "valid": bool(trace.get("valid")),
        "errors": list(trace.get("errors", [])),
        "warnings": list(trace.get("warnings", [])),
    }


def trace_synthesis_routes_for_report(
    loaded: dict[str, Any],
    *,
    sink_symbols: tuple[str, ...],
    sink_addresses: tuple[str, ...],
    source_regs: tuple[str, ...],
    source_mems: tuple[str, ...],
    source_symbols: tuple[str, ...],
    sink_size: int,
    symbols_path: str,
    root: Path,
) -> list[dict[str, Any]]:
    data = loaded.get("data")
    if not isinstance(data, dict):
        return []
    source = str(loaded.get("source", ""))
    kind = str(data.get("kind", ""))
    if kind == "unified_debugger_compare_plan":
        compare_routes = compare_plan_trace_synthesis_routes(
            data,
            source=source,
            sink_symbols=sink_symbols,
            sink_addresses=sink_addresses,
            source_regs=source_regs,
            source_mems=source_mems,
            source_symbols=source_symbols,
            sink_size=sink_size,
            symbols_path=symbols_path,
        )
        if compare_routes:
            return compare_routes
    if kind == "unified_debugger_minimization_plan":
        minimization_routes = state_patch_minimization_trace_synthesis_routes(
            data,
            source=source,
            sink_symbols=sink_symbols,
            sink_addresses=sink_addresses,
            source_regs=source_regs,
            source_mems=source_mems,
            source_symbols=source_symbols,
            sink_size=sink_size,
            symbols_path=symbols_path,
        )
        if minimization_routes:
            return minimization_routes
    sinks = unique_list([*sink_symbols, *state_patch_symbols_from_report(data), *watch_symbols_from_report(data)])
    addresses = unique_sink_addresses([*sink_addresses, *watch_addresses_from_report(data)])
    if not sinks and not addresses:
        return []
    route_id = "trace_synthesis_" + safe_name(Path(source).stem or kind or "report")
    safe_source = safe_name(Path(source).stem or "report")
    out_trace = f".local\\tmp\\debugger_dynamic_taint_{safe_source}.jsonl"
    trace_report = f".local\\tmp\\debugger_dynamic_taint_{safe_source}_instruction_trace.json"
    trace_source_report = source
    materialization_commands: list[str] = []
    materialized_report = ""
    materialized_state = ""
    state_status = trace_state_status(data)
    save_state = ""
    selected_save_state = trace_synthesis_selected_save_state(
        data,
        source=source,
        root=root,
    )
    if selected_save_state:
        save_state = str(selected_save_state.get("path", ""))
        if state_status == "requires-setup-or-save-state-discovery":
            state_status = "save-state-ready"
    if (
        kind == "unified_debugger_content_state_materialization"
        and not content_state_executed(data)
        and content_state_has_patches(data)
    ):
        materialized_report = f".local\\tmp\\debugger_dynamic_taint_{safe_source}_content_state.json"
        materialized_state = f".local\\tmp\\debugger_dynamic_taint_{safe_source}.state"
        save_state = materialized_state
        materialization_commands.append(
            "python -m tools.debugger content-state "
            f"--report {quote_arg(source)} --symbols {quote_arg(symbols_path)} "
            f"--base-save-state {quote_arg(str(data.get('base_save_state') or '<base-state>'))} "
            f"--out-state {materialized_state} "
            f"--execute --json-out {materialized_report}"
        )
        trace_source_report = materialized_report
        state_status = "materialization-planned"
    elif kind == "unified_debugger_state_space" and not state_space_executed(data):
        patch_specs = string_items(data.get("patch_specs"))
        if patch_specs:
            materialized_report = f".local\\tmp\\debugger_dynamic_taint_{safe_source}_state_space.json"
            materialized_state = f".local\\tmp\\debugger_dynamic_taint_{safe_source}.state"
            save_state = materialized_state
            patch_args = " ".join(f"--patch {quote_arg(spec)}" for spec in patch_specs)
            materialization_commands.append(
                "python -m tools.debugger state-space "
                f"{patch_args} --symbols {quote_arg(symbols_path)} "
                f"--base-save-state {quote_arg(str(data.get('base_save_state') or '<base-state>'))} "
                f"--out-state {materialized_state} "
                f"--execute --json-out {materialized_report}"
            )
            trace_source_report = materialized_report
            state_status = "materialization-planned"
    trace_command = instruction_trace_command(
        report=trace_source_report,
        symbols_path=symbols_path,
        function_symbols=(),
        sink_symbols=tuple(sinks),
        sink_addresses=tuple(addresses),
        sink_size=sink_size,
        save_state=save_state,
        out_trace=out_trace,
        out_report=trace_report,
    )
    dynamic_taint_command = dynamic_taint_followup_command(
        trace_report=trace_report,
        source_regs=source_regs,
        source_mems=source_mems,
        source_symbols=source_symbols,
        sink_symbols=tuple(sinks),
        sink_addresses=tuple(addresses),
        sink_size=sink_size,
        symbols_path=symbols_path,
    )
    commands = [*materialization_commands, trace_command, dynamic_taint_command]
    return [
        {
            "id": route_id,
            "source_report": source,
            "source_kind": kind,
            "state_status": state_status,
            "sink_symbols": list(sinks),
            "sink_addresses": list(addresses),
            "sink_size": sink_size,
            "source_regs": list(source_regs),
            "source_mems": list(source_mems),
            "source_symbols": list(source_symbols),
            "function_symbols": [],
            "save_state": save_state,
            "selected_save_state": selected_save_state,
            "materialized_report": materialized_report,
            "materialized_state": materialized_state,
            "rom": str(data.get("rom") or data.get("rom_path") or "pokegold.gbc"),
            "trace_report": trace_report,
            "trace_output": out_trace,
            "commands": commands,
        }
    ]


def state_patch_minimization_trace_synthesis_routes(
    data: dict[str, Any],
    *,
    source: str,
    sink_symbols: tuple[str, ...],
    sink_addresses: tuple[str, ...],
    source_regs: tuple[str, ...],
    source_mems: tuple[str, ...],
    source_symbols: tuple[str, ...],
    sink_size: int,
    symbols_path: str,
) -> list[dict[str, Any]]:
    minimization = data.get("state_patch_minimization")
    if not isinstance(minimization, dict) or not minimization.get("attempted"):
        return []
    inputs = state_patch_minimization_inputs(data)
    sinks = unique_list([*sink_symbols, *inputs["sink_symbols"]])
    addresses = unique_sink_addresses([*sink_addresses, *inputs["sink_addresses"]])
    if not sinks and not addresses:
        return []
    source_mem_specs = tuple(unique_list([*source_mems, *inputs["source_mems"]]))
    function_symbols = tuple(state_patch_minimization_source_symbols(minimization))
    safe_source = safe_name(Path(source).stem or "minimization")
    trace_source_report = str(minimization.get("out_report") or source)
    out_trace = f".local\\tmp\\debugger_dynamic_taint_{safe_source}_state_patch_minimization.jsonl"
    trace_report = f".local\\tmp\\debugger_dynamic_taint_{safe_source}_state_patch_minimization_instruction_trace.json"
    trace_command = instruction_trace_command(
        report=trace_source_report,
        symbols_path=symbols_path,
        function_symbols=function_symbols,
        sink_symbols=tuple(sinks),
        sink_addresses=tuple(addresses),
        sink_size=sink_size,
        save_state="",
        out_trace=out_trace,
        out_report=trace_report,
    )
    dynamic_taint_command = dynamic_taint_followup_command(
        trace_report=trace_report,
        source_regs=source_regs,
        source_mems=source_mem_specs,
        source_symbols=source_symbols,
        sink_symbols=tuple(sinks),
        sink_addresses=tuple(addresses),
        sink_size=sink_size,
        symbols_path=symbols_path,
    )
    return [
        {
            "id": f"trace_synthesis_{safe_source}_state_patch_minimization",
            "source_report": source,
            "trace_source_report": trace_source_report,
            "source_kind": "unified_debugger_minimization_plan",
            "state_status": "minimized-state-report-route" if minimization.get("out_report") else trace_state_status(data),
            "sink_symbols": list(sinks),
            "sink_addresses": list(addresses),
            "sink_size": sink_size,
            "source_regs": list(source_regs),
            "source_mems": list(source_mem_specs),
            "source_symbols": list(source_symbols),
            "function_symbols": list(function_symbols),
            "save_state": "",
            "selected_save_state": {},
            "materialized_report": "",
            "materialized_state": "",
            "rom": str(data.get("rom") or data.get("rom_path") or "pokegold.gbc"),
            "trace_report": trace_report,
            "trace_output": out_trace,
            "commands": [trace_command, dynamic_taint_command],
        }
    ]


def compare_plan_trace_synthesis_routes(
    data: dict[str, Any],
    *,
    source: str,
    sink_symbols: tuple[str, ...],
    sink_addresses: tuple[str, ...],
    source_regs: tuple[str, ...],
    source_mems: tuple[str, ...],
    source_symbols: tuple[str, ...],
    sink_size: int,
    symbols_path: str,
) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    safe_source = safe_name(Path(source).stem or "compare")
    for match in dict_items(data.get("matches")):
        materialization_commands = string_items(match.get("materialization_commands"))
        trace_commands = [
            ensure_trace_command_defaults(command, symbols_path=symbols_path)
            for command in materialization_commands
            if command_tool(command) == "trace-instructions" and command_option_value(command, "--out-trace")
        ]
        if not trace_commands:
            continue
        match_related_sinks = related_sinks_from_report(match)
        match_sinks = unique_list(
            [
                *sink_symbols,
                *match_related_sinks["symbols"],
                *command_watch_symbols(materialization_commands),
            ]
        )
        match_addresses = unique_sink_addresses(
            [
                *sink_addresses,
                *match_related_sinks["addresses"],
                *command_watch_addresses(materialization_commands),
            ]
        )
        if not match_sinks and not match_addresses:
            continue
        match_id = safe_name(str(match.get("id") or "match"))
        for index, trace_command in enumerate(trace_commands[:6]):
            out_trace = command_option_value(trace_command, "--out-trace")
            scenario_ids = unique_list(
                [
                    *command_option_values(trace_command, "--scenario-id"),
                    *string_items(match.get("scenario_ids")),
                ]
            )
            setup_commands = compare_setup_commands_for_trace(
                materialization_commands,
                scenario_ids=scenario_ids,
                symbols_path=symbols_path,
            )
            trace_report = command_option_value(trace_command, "--json-out")
            if not trace_report:
                trace_report = f".local\\tmp\\debugger_dynamic_taint_{safe_source}_{match_id}_{index}_instruction_trace.json"
            dynamic_taint_command = dynamic_taint_trace_followup_command(
                trace=out_trace,
                source_regs=source_regs,
                source_mems=source_mems,
                source_symbols=source_symbols,
                sink_symbols=tuple(match_sinks),
                sink_addresses=tuple(match_addresses),
                sink_size=sink_size,
                symbols_path=symbols_path,
            )
            commands = unique_list([*setup_commands, trace_command, dynamic_taint_command])
            routes.append(
                {
                    "id": f"trace_synthesis_{safe_source}_{match_id}_{index}",
                    "source_report": source,
                    "source_kind": "unified_debugger_compare_plan",
                    "match_id": str(match.get("id") or ""),
                    "state_status": compare_route_state_status(setup_commands),
                    "scenario_ids": scenario_ids,
                    "sink_symbols": list(match_sinks),
                    "sink_addresses": list(match_addresses),
                    "sink_size": sink_size,
                    "save_state": first_command_option_value(setup_commands, "--out-state"),
                    "selected_save_state": {},
                    "materialized_report": first_command_option_value(setup_commands, "--json-out"),
                    "materialized_state": first_command_option_value(setup_commands, "--out-state"),
                    "rom": str(data.get("rom") or data.get("rom_path") or "pokegold.gbc"),
                    "trace_report": trace_report,
                    "trace_output": out_trace,
                    "materialization_commands": setup_commands,
                    "commands": commands,
                }
            )
    return routes


def compare_setup_commands_for_trace(
    commands: list[str],
    *,
    scenario_ids: list[str],
    symbols_path: str,
) -> list[str]:
    setup_tools = {"content-state", "state-space"}
    setup_commands: list[str] = []
    for command in commands:
        if command_tool(command) not in setup_tools:
            continue
        command_scenarios = command_option_values(command, "--scenario-id")
        if scenario_ids and command_scenarios and not set(scenario_ids).intersection(command_scenarios):
            continue
        setup_commands.append(ensure_command_option(command, "--symbols", symbols_path))
    return unique_list(setup_commands)


def compare_route_state_status(setup_commands: list[str]) -> str:
    if not setup_commands:
        return "trace-command-ready"
    if any("<base_state>" in command or "<base-state>" in command for command in setup_commands):
        return "requires-base-save-state"
    if any("--execute" in command_parts(command) for command in setup_commands):
        return "scenario-materialization-planned"
    return "requires-content-state-execution"


def trace_state_status(data: dict[str, Any]) -> str:
    kind = str(data.get("kind", ""))
    if kind == "unified_debugger_content_state_materialization":
        return "ready" if content_state_executed(data) else "requires-content-state-execution"
    if kind == "unified_debugger_state_space":
        return "ready" if state_space_executed(data) else "requires-state-space-execution"
    if kind == "unified_debugger_instruction_trace":
        return "rerun-instruction-trace"
    return "requires-setup-or-save-state-discovery"


def trace_synthesis_selected_save_state(
    data: dict[str, Any],
    *,
    source: str,
    root: Path,
) -> dict[str, Any]:
    candidates = trace_synthesis_save_state_candidates(
        data,
        source=source,
        scenario_id=str(data.get("scenario_id", "")),
        root=root,
    )
    for candidate in candidates:
        if candidate.get("exists"):
            return candidate
    return {}


def trace_synthesis_save_state_candidates(
    value: Any,
    *,
    source: str,
    scenario_id: str,
    root: Path,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if isinstance(value, dict):
        local_scenario_id = str(value.get("scenario_id") or scenario_id)
        for key, nested in value.items():
            key_text = str(key)
            if isinstance(nested, str) and save_state_key(key_text) and save_state_path(nested):
                resolved = resolve_path(nested, root=root)
                candidates.append(
                    {
                        "path": display_path(resolved, root=root),
                        "raw_path": nested,
                        "source": source,
                        "key": key_text,
                        "scenario_id": local_scenario_id,
                        "exists": resolved.exists(),
                    }
                )
            candidates.extend(
                trace_synthesis_save_state_candidates(
                    nested,
                    source=source,
                    scenario_id=local_scenario_id,
                    root=root,
                )
            )
    elif isinstance(value, list):
        for item in value:
            candidates.extend(
                trace_synthesis_save_state_candidates(
                    item,
                    source=source,
                    scenario_id=scenario_id,
                    root=root,
                )
            )
    return unique_save_state_candidates(candidates)


def save_state_key(key: str) -> bool:
    lowered = key.lower()
    return lowered == "state" or lowered.endswith("_state") or "save_state" in lowered


def save_state_path(value: str) -> bool:
    text = value.strip()
    if not text or text.startswith(("route:", "scenario:")):
        return False
    suffix = Path(text).suffix.lower()
    return suffix in {".state", ".sgm", ".sav"} or "/" in text or "\\" in text


def unique_save_state_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for candidate in candidates:
        key = (
            str(candidate.get("path", "")),
            str(candidate.get("source", "")),
            str(candidate.get("scenario_id", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(candidate)
    return out


def content_state_executed(data: dict[str, Any]) -> bool:
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    return data.get("executed") is True or execution.get("executed") is True


def content_state_has_patches(data: dict[str, Any]) -> bool:
    return any(
        bool(materialization.get("patches"))
        for materialization in dict_items(data.get("materializations"))
    )


def state_space_executed(data: dict[str, Any]) -> bool:
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
    return data.get("executed") is True or execution.get("executed") is True


def instruction_trace_command(
    *,
    report: str,
    symbols_path: str,
    function_symbols: tuple[str, ...],
    sink_symbols: tuple[str, ...],
    sink_addresses: tuple[str, ...],
    sink_size: int,
    save_state: str,
    out_trace: str,
    out_report: str,
) -> str:
    args = [
        "trace-instructions",
        "--report",
        quote_arg(report),
        "--symbols",
        quote_arg(symbols_path),
        "--execute",
        "--require-hit",
        "--out-trace",
        quote_arg(out_trace),
        "--json-out",
        quote_arg(out_report),
    ]
    if save_state:
        args.extend(["--save-state", quote_arg(save_state)])
    for symbol in function_symbols[:6]:
        args.extend(["--symbol", quote_arg(symbol)])
    for symbol in sink_symbols[:6]:
        args.extend(["--sink-symbol", quote_arg(symbol)])
    for address in sink_addresses[:6]:
        args.extend(["--watch-address", quote_arg(command_address_arg(address))])
    if sink_addresses and sink_size != 1:
        args.extend(["--watch-size", str(sink_size)])
    return "python -m tools.debugger " + " ".join(args)


def dynamic_taint_followup_command(
    *,
    trace_report: str,
    source_regs: tuple[str, ...],
    source_mems: tuple[str, ...],
    source_symbols: tuple[str, ...],
    sink_symbols: tuple[str, ...],
    sink_addresses: tuple[str, ...],
    sink_size: int,
    symbols_path: str,
) -> str:
    args = ["dynamic-taint", "--report", quote_arg(trace_report), "--symbols", quote_arg(symbols_path)]
    for source in source_regs[:6]:
        args.extend(["--source-reg", quote_arg(source)])
    for source in source_mems[:6]:
        args.extend(["--source-mem", quote_arg(source)])
    for source in source_symbols[:6]:
        args.extend(["--source-symbol", quote_arg(source)])
    for sink in sink_symbols[:6]:
        args.extend(["--sink-symbol", quote_arg(sink)])
    for address in sink_addresses[:4]:
        args.extend(["--sink-address", quote_arg(command_address_arg(address))])
    if sink_addresses and sink_size != 1:
        args.extend(["--sink-size", str(sink_size)])
    return "python -m tools.debugger " + " ".join(args)


def dynamic_taint_trace_followup_command(
    *,
    trace: str,
    source_regs: tuple[str, ...],
    source_mems: tuple[str, ...],
    source_symbols: tuple[str, ...],
    sink_symbols: tuple[str, ...],
    sink_addresses: tuple[str, ...],
    sink_size: int,
    symbols_path: str,
) -> str:
    args = ["dynamic-taint", "--trace", quote_arg(trace), "--symbols", quote_arg(symbols_path)]
    for source in source_regs[:6]:
        args.extend(["--source-reg", quote_arg(source)])
    for source in source_mems[:6]:
        args.extend(["--source-mem", quote_arg(source)])
    for source in source_symbols[:6]:
        args.extend(["--source-symbol", quote_arg(source)])
    for sink in sink_symbols[:6]:
        args.extend(["--sink-symbol", quote_arg(sink)])
    for address in sink_addresses[:4]:
        args.extend(["--sink-address", quote_arg(command_address_arg(address))])
    if sink_addresses and sink_size != 1:
        args.extend(["--sink-size", str(sink_size)])
    return "python -m tools.debugger " + " ".join(args)


def command_tool(command: str) -> str:
    parts = command_parts(command)
    for index, part in enumerate(parts[:-1]):
        if part == "tools.debugger":
            return parts[index + 1]
    return ""


def command_parts(command: str) -> list[str]:
    return workflow_command_parts(command)


def command_option_value(command: str, option: str) -> str:
    values = command_option_values(command, option)
    return values[0] if values else ""


def first_command_option_value(commands: list[str], option: str) -> str:
    for command in commands:
        value = command_option_value(command, option)
        if value:
            return value
    return ""


def command_option_values(command: str, option: str) -> list[str]:
    return unique_list(workflow_command_option_values(command, option))


def command_has_option(command: str, option: str) -> bool:
    parts = command_parts(command)
    return option in parts or any(part.startswith(option + "=") for part in parts)


def ensure_command_option(command: str, option: str, value: str) -> str:
    if command_has_option(command, option) or not value:
        return command
    return f"{command} {option} {quote_arg(value)}"


def ensure_command_flag(command: str, flag: str) -> str:
    return command if flag in command_parts(command) else f"{command} {flag}"


def ensure_trace_command_defaults(command: str, *, symbols_path: str) -> str:
    with_symbols = ensure_command_option(command, "--symbols", symbols_path)
    with_execute = ensure_command_flag(with_symbols, "--execute")
    return ensure_command_flag(with_execute, "--require-hit")


def command_watch_symbols(commands: list[str]) -> list[str]:
    symbols: list[str] = []
    for command in commands:
        for option in ("--watch-symbol", "--sink-symbol"):
            symbols.extend(base_label(symbol) or symbol for symbol in command_option_values(command, option))
    return unique_list(symbols)


def command_watch_addresses(commands: list[str]) -> list[str]:
    addresses: list[str] = []
    for command in commands:
        for option in ("--watch-address", "--sink-address"):
            for address in command_option_values(command, option):
                candidate = sink_address_candidate(address)
                if candidate:
                    addresses.append(candidate)
    return unique_sink_addresses(addresses)


def analyze_instruction_trace(
    loaded: dict[str, Any],
    *,
    register_sources: dict[str, str],
    source_memory: dict[int, str],
    source_address_specs: list[dict[str, Any]],
    sinks: list[Sink],
    symbol_table: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    records = trace_records(loaded["data"])
    instructions: list[Instruction] = []
    frames: list[InstructionFrame] = []
    errors: list[str] = []
    bank_state_record_conflicts: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        parsed = parse_instruction_record(record, default_seq=index)
        if parsed["error"]:
            errors.append(f"{loaded['source']}[{index}]: {parsed['error']}")
            continue
        instructions.append(parsed["instruction"])
        frames.append(parsed["frame"])
        for conflict in dict_items(parsed.get("bank_state_record_conflicts")):
            bank_state_record_conflicts.append(
                {
                    "source": loaded["source"],
                    "record_index": index,
                    **conflict,
                }
            )

    trace_sinks = instruction_trace_sinks(sinks, frames=frames)
    trace_source_memory = instruction_trace_source_memory(
        source_memory=source_memory,
        source_address_specs=source_address_specs,
    )
    precision_warnings = instruction_trace_precision_warnings(
        sinks=sinks,
        trace_sinks=trace_sinks,
        source_memory=source_memory,
        trace_source_memory=trace_source_memory,
        source_address_specs=source_address_specs,
    )

    engine = TaintEngine(sinks=trace_sinks)
    for register, origin in register_sources.items():
        engine.seed_reg(register, origin)
    for address, origin in trace_source_memory.items():
        engine.seed_mem(address, origin)
    taint_report = engine.run(instructions, frames)
    frame_by_seq = {int(frame.seq): frame for frame in frames}
    sink_by_name = {sink.name: sink for sink in trace_sinks}
    engine_findings: list[dict[str, Any]] = []
    for finding in taint_report.findings:
        match = instruction_taint_finding_match(
            finding,
            frame_by_seq=frame_by_seq,
            sink_by_name=sink_by_name,
        )
        if match:
            engine_findings.append(public_finding(finding, source=loaded["source"], match=match))
    write_attributions = build_write_attributions(
        source=loaded["source"],
        instructions=instructions,
        frames=frames,
        sinks=trace_sinks,
        register_sources=register_sources,
        source_memory=trace_source_memory,
        source_address_specs=source_address_specs,
        symbol_table=symbol_table,
        taint_findings=taint_report.findings,
    )
    unmodeled_write_diagnostics = build_unmodeled_write_diagnostics(
        source=loaded["source"],
        instructions=instructions,
        frames=frames,
    )
    findings = reconcile_instruction_trace_findings(engine_findings, write_attributions)
    return {
        "source": loaded["source"],
        "record_count": len(records),
        "instruction_count": len(instructions),
        "frame_count": len(frames),
        "finding_count": len(findings),
        "write_attribution_count": len(write_attributions),
        "unmodeled_write_diagnostic_count": len(unmodeled_write_diagnostics),
        "bank_state_record_conflict_count": len(bank_state_record_conflicts),
        "skipped_bank_exact_sink_count": len(sinks) - len(trace_sinks),
        "skipped_bank_exact_source_count": len(source_memory) - len(trace_source_memory),
        "unsupported": dict(taint_report.unsupported),
        "unsupported_count": sum(int(count) for count in taint_report.unsupported.values()),
        "errors": errors,
        "warnings": [*errors[:4], *precision_warnings],
        "bank_state_record_conflicts": bank_state_record_conflicts[:80],
        "findings": findings,
        "write_attributions": write_attributions[:120],
        "unmodeled_write_diagnostics": unmodeled_write_diagnostics[:120],
    }


def reconcile_instruction_trace_findings(
    engine_findings: list[dict[str, Any]],
    write_attributions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    attribution_findings = instruction_findings_from_write_attributions(write_attributions)
    attribution_keys = {instruction_finding_key(finding) for finding in attribution_findings}
    findings = list(attribution_findings)
    for finding in engine_findings:
        if instruction_finding_key(finding) in attribution_keys:
            continue
        findings.append(finding)
    return sorted(findings, key=lambda item: (positive_int(item.get("seq")), positive_int(item.get("address"))))


def instruction_findings_from_write_attributions(write_attributions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for attribution in write_attributions:
        taint = string_items(attribution.get("taint"))
        contributors = dict_items(attribution.get("contributors"))
        if not taint or not contributors:
            continue
        proof_status = write_attribution_finding_proof_status(attribution)
        proof_downgrade_reason = str(attribution.get("proof_downgrade_reason", ""))
        if not attribution.get("proof_status") and not evidence_atoms(attribution.get("evidence_atoms")):
            proof_downgrade_reason = (
                proof_downgrade_reason
                or "missing_explicit_write_attribution_proof_status"
            )
        findings.append(
            {
                "source": str(attribution.get("source", "")),
                "source_kind": "instruction_trace_write_attribution",
                "seq": positive_int(attribution.get("seq")),
                "pc": positive_int(attribution.get("pc")),
                "pc_label": str(attribution.get("pc_label", "")),
                "mnemonic": str(attribution.get("mnemonic", "")),
                "sink": str(attribution.get("sink") or attribution.get("target") or ""),
                "address": positive_int(attribution.get("address")),
                "address_key": str(attribution.get("address_key", "")),
                "match_precision": str(attribution.get("match_precision", "")),
                "bank_match": str(attribution.get("bank_match", "")),
                "bank_source": str(attribution.get("bank_source", "")),
                "proof_downgrade_reason": proof_downgrade_reason,
                "taint": taint,
                "proof_status": proof_status,
                "evidence_atoms": merge_evidence_atoms(attribution.get("evidence_atoms")),
                "evidence": string_items(attribution.get("evidence")),
            }
        )
    return findings


def write_attribution_finding_proof_status(attribution: dict[str, Any]) -> str:
    if attribution.get("proof_status"):
        return normalize_proof_status(attribution.get("proof_status"))
    atom_statuses = [
        normalize_proof_status(atom.get("proof_status"))
        for atom in evidence_atoms(attribution.get("evidence_atoms"))
    ]
    if atom_statuses:
        return min(atom_statuses, key=lambda status: PROOF_STATUS_RANK.get(status, 0))
    return "planned_only"


def instruction_finding_key(finding: dict[str, Any]) -> tuple[int, int, str]:
    return (
        positive_int(finding.get("seq")),
        positive_int(finding.get("address")),
        str(finding.get("sink", "")),
    )


def instruction_trace_sinks(sinks: list[Sink], *, frames: list[InstructionFrame]) -> list[Sink]:
    return [
        sink
        for sink in sinks
        if not bool(getattr(sink, "bank_exact_required", False))
        or any(instruction_frame_address_key(frame, sink.address) == str(getattr(sink, "address_key", "")) for frame in frames)
    ]


def instruction_trace_source_memory(
    *,
    source_memory: dict[int, str],
    source_address_specs: list[dict[str, Any]],
) -> dict[int, str]:
    exact_key_addresses = {
        positive_int(record.get("address")) & 0xFFFF
        for record in source_address_specs
        if address_spec_requires_exact_key(record)
    }
    allowed_addresses = {
        positive_int(record.get("address")) & 0xFFFF
        for record in source_address_specs
        if not address_spec_requires_exact_key(record)
    }
    return {
        address: origin
        for address, origin in source_memory.items()
        if address not in exact_key_addresses or address in allowed_addresses
    }


def instruction_trace_precision_warnings(
    *,
    sinks: list[Sink],
    trace_sinks: list[Sink],
    source_memory: dict[int, str],
    trace_source_memory: dict[int, str],
    source_address_specs: list[dict[str, Any]],
) -> list[str]:
    warnings: list[str] = []
    trace_sink_ids = {id(sink) for sink in trace_sinks}
    skipped_sinks = [
        sink.name
        for sink in sinks
        if bool(getattr(sink, "bank_exact_required", False)) and id(sink) not in trace_sink_ids
    ]
    if skipped_sinks:
        warnings.append(
            "instruction trace skipped raw banked sinks requiring exact address_key; use effect-trace evidence for: "
            + ", ".join(skipped_sinks[:6])
        )
    if len(trace_source_memory) != len(source_memory):
        skipped_sources = [
            str(record.get("evidence") or record.get("raw") or record.get("origin") or "")
            for record in source_address_specs
            if raw_address_is_banked(record) and not record.get("symbol")
        ]
        warnings.append(
            "instruction trace skipped raw banked source memory requiring exact address_key; use effect-trace evidence for: "
            + ", ".join(item for item in skipped_sources[:6] if item)
        )
    return warnings


def analyze_effect_trace_report(
    loaded: dict[str, Any],
    *,
    register_sources: dict[str, str],
    source_memory: dict[int, str],
    source_address_specs: list[dict[str, Any]],
    sinks: list[Sink],
    symbol_table: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    data = loaded.get("data") if isinstance(loaded.get("data"), dict) else {}
    events = dict_items(data.get("events"))
    findings: list[dict[str, Any]] = []
    write_attributions: list[dict[str, Any]] = []
    errors: list[str] = []
    register_state: dict[str, dict[str, Any]] = {}
    for event in sorted(events, key=lambda item: positive_int(item.get("seq"))):
        for effect_item in dict_items(event.get("effects")):
            if effect_item.get("access") == "register_write":
                update_register_state_from_effect(
                    register_state,
                    loaded=loaded,
                    event=event,
                    effect_item=effect_item,
                    register_sources=register_sources,
                    source_memory=source_memory,
                    source_address_specs=source_address_specs,
                    symbol_table=symbol_table,
                )
                continue
            if effect_item.get("access") != "write":
                continue
            address = effect_item_address(effect_item)
            if address < 0:
                errors.append(f"{loaded['source']}: effect write is missing an address")
                continue
            for sink in sinks:
                match = effect_sink_match(sink, effect_item=effect_item, address=address)
                if not match:
                    continue
                source_operands = [
                    enrich_source_operand(
                        operand,
                        register_sources=register_sources,
                        source_memory=source_memory,
                        source_address_specs=source_address_specs,
                        symbol_table=symbol_table,
                    )
                    for operand in dict_items(effect_item.get("source_operands"))
                ]
                provenance_operands, register_provenance = register_provenance_for_operands(
                    source_operands,
                    register_state=register_state,
                )
                source_operands = [*source_operands, *provenance_operands]
                contributors = contributors_for_operands(source_operands)
                taint = unique_list(contributor.get("symbol", "") for contributor in contributors)
                if contributors:
                    findings.append(effect_taint_finding(
                        loaded=loaded,
                        event=event,
                        effect_item=effect_item,
                        sink=sink,
                        address=address,
                        match=match,
                        taint=taint,
                    ))
                write_attributions.append(effect_write_attribution(
                    loaded=loaded,
                    event=event,
                    effect_item=effect_item,
                    sink=sink,
                    address=address,
                    match=match,
                    source_operands=source_operands,
                    contributors=contributors,
                    taint=taint,
                    register_provenance=register_provenance,
                    symbol_table=symbol_table,
                ))
    return {
        "source": loaded["source"],
        "report_kind": "unified_debugger_effect_trace",
        "effect_event_count": len(events),
        "finding_count": len(findings),
        "write_attribution_count": len(write_attributions),
        "errors": errors,
        "warnings": errors[:4],
        "findings": findings,
        "write_attributions": write_attributions[:120],
    }


def update_register_state_from_effect(
    register_state: dict[str, dict[str, Any]],
    *,
    loaded: dict[str, Any],
    event: dict[str, Any],
    effect_item: dict[str, Any],
    register_sources: dict[str, str],
    source_memory: dict[int, str],
    source_address_specs: list[dict[str, Any]],
    symbol_table: dict[str, dict[str, Any]],
) -> None:
    register = str(effect_item.get("register", "")).lower()
    if not register:
        return
    source_operands = [
        enrich_source_operand(
            operand,
            register_sources=register_sources,
            source_memory=source_memory,
            source_address_specs=source_address_specs,
            symbol_table=symbol_table,
        )
        for operand in dict_items(effect_item.get("source_operands"))
    ]
    provenance_operands, register_provenance = register_provenance_for_operands(
        source_operands,
        register_state=register_state,
    )
    source_operands = [*source_operands, *provenance_operands]
    contributors = contributors_for_operands(source_operands)
    record = {
        "source": loaded.get("source", ""),
        "seq": event.get("seq"),
        "pc": event.get("pc_bank_address", ""),
        "pc_label": event.get("pc_label", ""),
        "operation": effect_item.get("operation", ""),
        "model_source": effect_item.get("model_source", ""),
        "register": register,
        "value_hex": effect_item.get("value_hex", ""),
        "value_source": effect_item.get("value_source", ""),
        "source_operands": source_operands,
        "register_provenance": register_provenance,
        "contributors": contributors,
        "taint": unique_list(contributor.get("symbol", "") for contributor in contributors),
        "proof_status": "instruction_observed",
    }
    clear_register_aliases(register_state, register)
    for alias, alias_record in register_alias_records(register, record):
        register_state[alias] = alias_record


PAIR_COMPONENTS = {
    "af": ("a", "f"),
    "bc": ("b", "c"),
    "de": ("d", "e"),
    "hl": ("h", "l"),
}
COMPONENT_PAIRS = {
    component: pair
    for pair, components in PAIR_COMPONENTS.items()
    for component in components
}


def clear_register_aliases(register_state: dict[str, dict[str, Any]], register: str) -> None:
    register = register.lower()
    stale = {register}
    stale.update(PAIR_COMPONENTS.get(register, ()))
    pair = COMPONENT_PAIRS.get(register)
    if pair:
        stale.add(pair)
    for alias in stale:
        register_state.pop(alias, None)


def register_aliases(register: str) -> list[str]:
    register = register.lower()
    aliases = [register]
    aliases.extend(PAIR_COMPONENTS.get(register, ()))
    return unique_list(aliases)


def register_alias_records(register: str, record: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    register = register.lower()
    if register not in PAIR_COMPONENTS:
        return [(register, record)]
    records: list[tuple[str, dict[str, Any]]] = [(register, record)]
    component_records = split_pair_component_records(register, record)
    for component in PAIR_COMPONENTS[register]:
        records.append((component, component_records.get(component, record)))
    return records


def split_pair_component_records(register: str, record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    components = PAIR_COMPONENTS.get(register.lower())
    if not components:
        return {}
    operation = str(record.get("operation", "")).lower()
    operands = dict_items(record.get("source_operands"))
    if not operation.startswith("pop ") or len(operands) < 2:
        return {}
    high, low = components
    low_value = stack_pop_component_value(register, low, operand_int_value(operands[0]))
    high_value = stack_pop_component_value(register, high, operand_int_value(operands[1]))
    return {
        low: component_register_record(
            record,
            register=low,
            source_operands=[operands[0]],
            operation=f"{operation} low",
            value=low_value,
        ),
        high: component_register_record(
            record,
            register=high,
            source_operands=[operands[1]],
            operation=f"{operation} high",
            value=high_value,
        ),
    }


def component_register_record(
    record: dict[str, Any],
    *,
    register: str,
    source_operands: list[dict[str, Any]],
    operation: str,
    value: int | None = None,
) -> dict[str, Any]:
    copied = dict(record)
    contributors = contributors_for_operands(source_operands)
    copied["register"] = register
    copied["operation"] = operation
    copied["source_operands"] = source_operands
    copied["contributors"] = contributors
    copied["taint"] = unique_list(contributor.get("symbol", "") for contributor in contributors)
    source_value = f"{value & 0xFF:02X}" if value is not None else (source_operands[0].get("value") if source_operands else "")
    if source_value:
        copied["value_hex"] = str(source_value)
        copied["value_source"] = str(source_operands[0].get("value_source", copied.get("value_source", "")))
    else:
        copied["value_hex"] = ""
    return copied


def register_provenance_for_operands(
    source_operands: list[dict[str, Any]],
    *,
    register_state: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    derived_operands: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    for operand in source_operands:
        if operand.get("kind") != "register":
            continue
        register = str(operand.get("name", "")).lower()
        record = register_state.get(register)
        if not record:
            continue
        summary = register_provenance_summary(register=register, record=record)
        operand["register_provenance"] = summary
        provenance.append(summary)
        for source_operand in dict_items(record.get("source_operands")):
            derived = dict(source_operand)
            derived["via_register"] = register
            derived["via_register_write_seq"] = record.get("seq")
            derived["via_register_write_pc"] = record.get("pc", "")
            derived_operands.append(derived)
    return unique_operand_records(derived_operands), unique_register_provenance(provenance)


def register_provenance_summary(*, register: str, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "register": register,
        "source": str(record.get("source", "")),
        "seq": record.get("seq"),
        "pc": str(record.get("pc", "")),
        "pc_label": str(record.get("pc_label", "")),
        "operation": str(record.get("operation", "")),
        "model_source": str(record.get("model_source", "")),
        "value_hex": str(record.get("value_hex", "")),
        "value_source": str(record.get("value_source", "")),
        "taint": string_items(record.get("taint")),
        "proof_status": str(record.get("proof_status", "instruction_observed")),
    }


def unique_operand_records(operands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for operand in operands:
        key = (
            str(operand.get("kind", "")),
            str(operand.get("address_key") or operand.get("address") or operand.get("name") or ""),
            str(operand.get("origin", "")),
            str(operand.get("via_register", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(operand)
    return out


def unique_register_provenance(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        key = (str(item.get("register", "")), str(item.get("seq", "")), str(item.get("pc", "")))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def effect_item_address(effect_item: dict[str, Any]) -> int:
    try:
        return parse_int(effect_item.get("address", effect_item.get("address_hex", "")))
    except (TypeError, ValueError):
        try:
            return parse_address(str(effect_item.get("address_hex", "")))
        except ValueError:
            return -1


def effect_taint_finding(
    *,
    loaded: dict[str, Any],
    event: dict[str, Any],
    effect_item: dict[str, Any],
    sink: Sink,
    address: int,
    match: dict[str, Any],
    taint: list[str],
) -> dict[str, Any]:
    proof_status = match_proof_status(match)
    return {
        "source": loaded["source"],
        "source_kind": "effect_trace_report",
        "seq": positive_int(event.get("seq")),
        "pc": positive_int(event.get("pc")),
        "pc_label": str(event.get("pc_label") or event.get("pc_bank_address") or ""),
        "mnemonic": str(event.get("mnemonic") or effect_item.get("operation") or ""),
        "sink": sink.name,
        "address": address & 0xFFFF,
        "address_key": str(effect_item.get("address_key", "")),
        "match_precision": str(match.get("match_precision", "")),
        "bank_match": str(match.get("bank_match", "")),
        "bank_source": str(match.get("bank_source", "")),
        "proof_downgrade_reason": str(match.get("proof_downgrade_reason", "")),
        "taint": taint,
        "effect_evidence_source": str(effect_item.get("evidence_source", "")),
        "effect_evidence_status": str(effect_item.get("evidence_status", "")),
        "runtime_observation": str(effect_item.get("runtime_observation", "")),
        "proof_status": proof_status,
        "evidence": match_evidence(match),
    }


def effect_write_attribution(
    *,
    loaded: dict[str, Any],
    event: dict[str, Any],
    effect_item: dict[str, Any],
    sink: Sink,
    address: int,
    match: dict[str, Any],
    source_operands: list[dict[str, Any]],
    contributors: list[dict[str, Any]],
    taint: list[str],
    symbol_table: dict[str, dict[str, Any]],
    register_provenance: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    pc_label = str(event.get("pc_label") or event.get("pc_bank_address") or "")
    mnemonic = str(event.get("mnemonic") or effect_item.get("operation") or "")
    target = sink.name
    value_hex = str(effect_item.get("value_hex", ""))
    value_source = str(effect_item.get("value_source", ""))
    proof_status = match_proof_status(match)
    attribution = {
        "id": f"effect_write_{positive_int(event.get('seq')):04d}_{address & 0xFFFF:04X}",
        "source": loaded["source"],
        "target": target,
        "access": "effect_write",
        "seq": positive_int(event.get("seq")),
        "pc": positive_int(event.get("pc")),
        "pc_label": pc_label,
        "mnemonic": mnemonic,
        "sink": sink.name,
        "sink_address": f"{sink.address:04X}",
        "address": f"{address & 0xFFFF:04X}",
        "address_key": str(effect_item.get("address_key", "")),
        "match_precision": str(match.get("match_precision", "")),
        "bank_match": str(match.get("bank_match", "")),
        "bank_source": str(match.get("bank_source", "")),
        "proof_downgrade_reason": str(match.get("proof_downgrade_reason", "")),
        "address_symbol": symbol_for_address(address, symbol_table),
        "sink_offset": (address & 0xFFFF) - sink.address,
        "write_kind": str(effect_item.get("kind") or effect_item.get("operation") or ""),
        "model_source": str(effect_item.get("model_source", "")),
        "effect_evidence_source": str(effect_item.get("evidence_source", "")),
        "effect_evidence_status": str(effect_item.get("evidence_status", "")),
        "runtime_observation": str(effect_item.get("runtime_observation", "")),
        "source_operands": source_operands,
        "register_provenance": register_provenance or [],
        "contributors": contributors,
        "taint": taint,
        "score": write_attribution_score(contributors=contributors, taint=taint),
        "confidence": 0.91 if taint else 0.78,
        "proof_status": proof_status,
        "evidence_atoms": merge_evidence_atoms(
            dynamic_write_attribution_evidence_atom(
                claim_type="dynamic_taint.write_attribution",
                source=str(loaded.get("source", "")),
                source_kind="effect_trace_report",
                proof_status=proof_status,
                target=target,
                seq=positive_int(event.get("seq")),
                pc=positive_int(event.get("pc")),
                pc_label=pc_label,
                mnemonic=mnemonic,
                address=address,
                sink_size=sink.size,
                contributors=contributors,
                taint=taint,
                precision={
                    "write_kind": str(effect_item.get("kind") or effect_item.get("operation") or ""),
                    "address_key": str(effect_item.get("address_key", "")),
                    "match_precision": str(match.get("match_precision", "")),
                    "bank_match": str(match.get("bank_match", "")),
                    "bank_source": str(match.get("bank_source", "")),
                    "proof_downgrade_reason": str(match.get("proof_downgrade_reason", "")),
                    "effect_evidence_source": str(effect_item.get("evidence_source", "")),
                    "effect_evidence_status": str(effect_item.get("evidence_status", "")),
                    "runtime_observation": str(effect_item.get("runtime_observation", "")),
                    "model_source": str(effect_item.get("model_source", "")),
                    "value_source": value_source,
                },
            ),
            effect_item.get("evidence_atoms"),
        ),
        "evidence": write_attribution_evidence(
            seq=positive_int(event.get("seq")),
            pc=positive_int(event.get("pc")),
            mnemonic=mnemonic,
            target=target,
            address=address,
            source_operands=source_operands,
            taint=taint,
            register_provenance=register_provenance or [],
            value_hex=value_hex,
            value_source=value_source,
            match=match,
        ),
        "related_symbols": related_symbols_for_write(
            target=target,
            pc_label=pc_label,
            address=address,
            source_operands=source_operands,
            symbol_table=symbol_table,
        ),
        "related_addresses": related_addresses_for_write(target=target, address=address, sink=sink),
        "related_files": [],
        "sink_size": sink.size,
        "commands": commands_for_effect_write_attribution(
            target=target,
            source=str(loaded.get("source", "")),
            address=address,
            sink_size=sink.size,
        ),
    }
    if value_hex:
        attribution["value_hex"] = value_hex
        if value_source:
            attribution["value_source"] = value_source
    return attribution


def dynamic_write_attribution_evidence_atom(
    *,
    claim_type: str,
    source: str,
    source_kind: str,
    proof_status: str,
    target: str,
    seq: int,
    pc: int,
    pc_label: str,
    mnemonic: str,
    address: int,
    sink_size: int,
    contributors: list[dict[str, Any]],
    taint: list[str],
    precision: dict[str, Any],
) -> dict[str, Any]:
    return evidence_atom(
        claim_type=claim_type,
        origin="dynamic_taint",
        observation_type=source_kind,
        proof_status=proof_status,
        source_report=source,
        source_kind=source_kind,
        scope={
            "seq": seq,
            "pc": pc,
            "pc_label": pc_label,
        },
        subjects={
            "symbols": [target, pc_label, *[item.get("symbol", "") for item in contributors]],
            "addresses": [target_address(target), f"{address & 0xFFFF:04X}"],
        },
        precision={
            **precision,
            "sink_size": sink_size,
        },
        validation={
            "taint_count": len(taint),
            "contributor_count": len(contributors),
        },
        detail={
            "mnemonic": mnemonic,
            "taint": taint,
        },
    )


def parse_instruction_record(record: dict[str, Any], *, default_seq: int) -> dict[str, Any]:
    try:
        seq = parse_int(record.get("seq", record.get("index", default_seq)))
        bank = parse_int(record.get("bank", record.get("pc_bank", 0)))
        pc = parse_int(record.get("pc", 0))
        opcode = parse_int(record.get("opcode", record.get("op", "")))
    except ValueError as exc:
        return {"error": str(exc), "instruction": None, "frame": None}
    if opcode < 0 or opcode > 0xFF:
        return {"error": f"opcode out of byte range: {opcode}", "instruction": None, "frame": None}
    operand = parse_operand(record.get("operand", record.get("operands", record.get("operand_bytes", []))))
    if operand is None:
        return {"error": "operand must be a byte list or hex string", "instruction": None, "frame": None}
    mnemonic = str(record.get("mnemonic") or render_mnemonic(opcode, operand))
    registers = parse_registers(record)
    pc_label = str(record.get("pc_label") or record.get("label") or f"${bank:02X}:{pc:04X}")
    instruction = Instruction(
        bank=bank,
        pc=pc,
        opcode=opcode,
        operand=operand,
        length=max(1, 1 + len(operand)),
        mnemonic=mnemonic,
    )
    frame = InstructionFrame(
        seq=seq,
        bank=bank,
        pc=pc,
        pc_label=pc_label,
        A=registers["A"],
        F=registers["F"],
        B=registers["B"],
        C=registers["C"],
        D=registers["D"],
        E=registers["E"],
        H=registers["H"],
        L=registers["L"],
        HL=registers["HL"],
        SP=registers["SP"],
        memory=parse_raw_watch_memory(record),
        bank_state=parse_bank_state(record),
        bank_state_sources=parse_bank_state_sources(record),
        known_registers=parse_known_registers(record),
    )
    return {
        "error": "",
        "instruction": instruction,
        "frame": frame,
        "bank_state_record_conflicts": bank_state_record_conflicts(
            record,
            seq=seq,
            bank=bank,
            pc=pc,
            pc_label=pc_label,
        ),
    }


def trace_records(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("instructions", "frames", "events", "trace", "records"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if "opcode" in data and "pc" in data:
            return [data]
    return []


def parse_registers(record: dict[str, Any]) -> dict[str, int]:
    nested = record.get("regs") if isinstance(record.get("regs"), dict) else {}
    nested_registers = record.get("registers") if isinstance(record.get("registers"), dict) else {}
    merged = {**nested, **nested_registers, **record}
    out = {name: parse_int(register_value(merged, name), default=0) for name in REGISTER_FIELDS}
    if not out["HL"]:
        out["HL"] = ((out["H"] & 0xFF) << 8) | (out["L"] & 0xFF)
    if not out["H"] and out["HL"]:
        out["H"] = (out["HL"] >> 8) & 0xFF
    if not out["L"] and out["HL"]:
        out["L"] = out["HL"] & 0xFF
    return out


def parse_known_registers(record: dict[str, Any]) -> tuple[str, ...]:
    nested = record.get("regs") if isinstance(record.get("regs"), dict) else {}
    nested_registers = record.get("registers") if isinstance(record.get("registers"), dict) else {}
    sources = (nested, nested_registers, record)
    known: set[str] = set()
    for name in REGISTER_FIELDS:
        for source in sources:
            if register_is_present(source, name):
                known.add(name)
                break
    return tuple(sorted(known))


def register_is_present(data: dict[str, Any], name: str) -> bool:
    return any(key in data for key in (name, name.lower(), f"register_{name.lower()}"))


def parse_raw_watch_memory(record: dict[str, Any]) -> tuple[tuple[int, int], ...]:
    out: dict[int, int] = {}
    parse_watch_value_specs_memory(record, out=out)
    values = record.get("watch_values")
    if not isinstance(values, dict):
        return tuple(sorted(out.items()))
    for raw_key, raw_value in values.items():
        try:
            spec = parse_address_spec(raw_key)
        except ValueError:
            continue
        if spec.bank is not None:
            continue
        bytes_value = parse_hex_byte_string(raw_value)
        if not bytes_value:
            continue
        for offset, byte in enumerate(bytes_value):
            out[(spec.address + offset) & 0xFFFF] = byte
    return tuple(sorted(out.items()))


def parse_watch_value_specs_memory(record: dict[str, Any], *, out: dict[int, int]) -> None:
    values = record.get("watch_values") if isinstance(record.get("watch_values"), dict) else {}
    for item in dict_items(record.get("watch_value_specs")):
        bank = watch_value_spec_bank(item)
        try:
            address = parse_int(item.get("address"))
        except ValueError:
            continue
        if not watch_value_spec_observed_on_bus(record, address=address, bank=bank):
            continue
        value = item.get("value_hex") or values.get(str(item.get("name", "")))
        bytes_value = parse_hex_byte_string(value)
        if not bytes_value:
            continue
        for offset, byte in enumerate(bytes_value):
            out[(address + offset) & 0xFFFF] = byte


def watch_value_spec_observed_on_bus(record: dict[str, Any], *, address: int, bank: int | None) -> bool:
    if bank is None:
        return True
    address &= 0xFFFF
    state = bank_state_mapping(record)
    if 0xD000 <= address <= 0xDFFF:
        return bank_state_value(state, "wram") == bank
    if 0x8000 <= address <= 0x9FFF:
        return bank_state_value(state, "vram") == bank
    if 0x4000 <= address <= 0x7FFF:
        return bank_state_value(state, "rom") == bank
    if 0xA000 <= address <= 0xBFFF:
        enabled = bank_state_value(state, "sram_enabled")
        return enabled != 0 and bank_state_value(state, "sram") == bank
    return bank == 0


def bank_state_value(state: dict[str, Any], key: str) -> int | None:
    value = state.get(key)
    if value in {None, ""}:
        return None
    try:
        return parse_int(value)
    except ValueError:
        return None


def watch_value_spec_bank(item: dict[str, Any]) -> int | None:
    value = item.get("bank")
    if value in {None, ""}:
        return None
    try:
        return parse_int(value)
    except ValueError:
        return None


def parse_hex_byte_string(value: Any) -> tuple[int, ...]:
    text = str(value).strip().replace(" ", "").replace("_", "")
    if text.startswith(("0x", "0X")):
        text = text[2:]
    if not text or len(text) % 2:
        return ()
    try:
        return tuple(int(text[index : index + 2], 16) for index in range(0, len(text), 2))
    except ValueError:
        return ()


def parse_bank_state(record: dict[str, Any]) -> tuple[tuple[str, int], ...]:
    state = bank_state_mapping(record)
    out: dict[str, int] = {}
    for key in ("wram", "wram_raw", "vram", "vram_raw", "rom", "loaded_rom", "sram", "sram_enabled"):
        value = state.get(key, record.get(f"{key}_bank"))
        if value in {None, ""}:
            continue
        try:
            out[key] = normalize_bank_state_value(key, parse_int(value))
        except ValueError:
            continue
    if "wram" not in out and "wram_raw" in out:
        out["wram"] = normalize_bank_state_value("wram", out["wram_raw"])
    if "vram" not in out and "vram_raw" in out:
        out["vram"] = normalize_bank_state_value("vram", out["vram_raw"])
    return tuple(sorted(out.items()))


def bank_state_mapping(record: dict[str, Any]) -> dict[str, Any]:
    out = dict(record.get("bank_state")) if isinstance(record.get("bank_state"), dict) else {}
    for item in dict_items(record.get("bank_state_records")):
        name = str(item.get("name") or "")
        if not name or name.endswith("_inferred") or name in out:
            continue
        value = parsed_bank_state_record_value(item.get("value"), value_hex=item.get("value_hex"))
        if value is None:
            continue
        out[name] = value
    return out


def bank_state_record_conflicts(
    record: dict[str, Any],
    *,
    seq: int,
    bank: int,
    pc: int,
    pc_label: str,
) -> list[dict[str, Any]]:
    legacy = record.get("bank_state")
    if not isinstance(legacy, dict):
        return []
    conflicts: list[dict[str, Any]] = []
    for item in dict_items(record.get("bank_state_records")):
        name = str(item.get("name") or "")
        if not name or name.endswith("_inferred") or name not in legacy:
            continue
        legacy_value = parsed_bank_state_record_value(legacy.get(name))
        typed_value = parsed_bank_state_record_value(item.get("value"), value_hex=item.get("value_hex"))
        if legacy_value is None or typed_value is None:
            continue
        legacy_value = normalize_bank_state_value(name, legacy_value)
        typed_value = normalize_bank_state_value(name, typed_value)
        if legacy_value == typed_value:
            continue
        conflicts.append(
            {
                "key": name,
                "legacy_value": legacy_value,
                "typed_value": typed_value,
                "typed_source": str(item.get("source") or ""),
                "typed_state_kind": str(item.get("state_kind") or ""),
                "conflict_kind": "value_mismatch",
                "frame_pc": f"{bank & 0xFF:02X}:{pc & 0xFFFF:04X}",
                "seq": seq,
                "pc_label": pc_label,
                "proof_action": "preferred_legacy_for_backward_compat",
            }
        )
    return conflicts


def parsed_bank_state_record_value(value: Any, *, value_hex: Any = None) -> int | None:
    raw = value
    if (raw is None or raw == "") and value_hex is not None and value_hex != "":
        raw = f"0x{value_hex}"
    if raw is None or raw == "":
        return None
    try:
        return parse_int(raw)
    except ValueError:
        return None


def bank_state_record_conflict_warnings(conflicts: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for conflict in conflicts[:8]:
        warnings.append(
            "bank_state_record_conflict "
            f"key={conflict.get('key', '')} "
            f"legacy={conflict.get('legacy_value', '')} "
            f"typed={conflict.get('typed_value', '')} "
            f"frame={conflict.get('frame_pc', '')} "
            f"action={conflict.get('proof_action', '')}"
        )
    return warnings


def parse_bank_state_sources(record: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    out: dict[str, str] = {}
    raw_sources = record.get("bank_state_sources")
    if isinstance(raw_sources, dict):
        out.update({str(key): str(value) for key, value in raw_sources.items() if str(value)})
    for item in dict_items(record.get("bank_state_records")):
        name = str(item.get("name") or "")
        source = str(item.get("source") or "")
        if name and source and name not in out:
            out[name] = source
    return tuple(sorted(out.items()))


def normalize_bank_state_value(key: str, value: int) -> int:
    value &= 0xFF
    if key == "wram":
        bank = value & 0x07
        return bank if bank else 1
    if key == "vram":
        return value & 0x01
    if key == "rom":
        bank = value & 0x7F
        return bank if bank else 1
    return value


def register_value(data: dict[str, Any], name: str) -> Any:
    for key in (name, name.lower(), f"register_{name.lower()}"):
        if key in data:
            return data[key]
    return 0


def parse_register_sources(source_regs: tuple[str, ...]) -> tuple[dict[str, str], list[str]]:
    out: dict[str, str] = {}
    errors: list[str] = []
    for raw in source_regs:
        name, origin = split_assignment(raw)
        register = name.lower()
        if register not in {"a", "f", "b", "c", "d", "e", "h", "l", "af", "bc", "de", "hl", "sp"}:
            errors.append(f"unsupported source register: {name}")
            continue
        out[register] = origin or f"source_reg:{register}"
    return out, errors


def parse_memory_sources(
    *,
    source_mems: tuple[str, ...],
    source_symbols: tuple[str, ...],
    symbol_table: dict[str, dict[str, Any]],
) -> tuple[dict[int, str], list[str]]:
    out: dict[int, str] = {}
    errors: list[str] = []
    for raw in source_mems:
        address_text, origin = split_assignment(raw)
        try:
            spec = parse_address_spec(address_text)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        source_origin = origin or f"source_mem:{spec.evidence()}"
        if spec.bank is not None and spec.address in out:
            continue
        out[spec.address] = source_origin
    for symbol in source_symbols:
        entry = symbol_table.get(symbol)
        if not entry:
            errors.append(f"source symbol not found in symbols: {symbol}")
            continue
        out[int(entry["address"])] = f"source_symbol:{symbol}"
    return out, errors


def parse_sinks(
    *,
    sink_symbols: tuple[str, ...],
    sink_addresses: tuple[str, ...],
    sink_size: int,
    symbol_table: dict[str, dict[str, Any]],
) -> tuple[list[Sink], list[str]]:
    sinks: list[Sink] = []
    errors: list[str] = []
    for symbol in sink_symbols:
        entry = symbol_table.get(symbol)
        if not entry:
            errors.append(f"sink symbol not found in symbols: {symbol}")
            continue
        sinks.append(Sink(symbol, int(entry["address"]), default_symbol_size(symbol, sink_size)))
    for raw in sink_addresses:
        name, _origin = split_assignment(raw)
        try:
            spec = parse_address_spec(name)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        sinks.append(Sink(spec.evidence(), spec.address, sink_size))
    return sinks, errors


def annotate_sink_address_specs(sinks: list[Sink], records: list[dict[str, Any]]) -> None:
    records_by_name: dict[str, dict[str, Any]] = {}
    for record in records:
        name = str(record.get("symbol") or record.get("evidence") or "")
        if name and name not in records_by_name:
            records_by_name[name] = record
    for sink in sinks:
        record = records_by_name.get(sink.name)
        if not record:
            continue
        setattr(sink, "address_key", str(record.get("key", "")))
        setattr(sink, "address_evidence", str(record.get("evidence", "")))
        setattr(sink, "bank_exact_required", address_spec_requires_exact_key(record))


def source_address_spec_records(
    *,
    source_mems: tuple[str, ...],
    source_symbols: tuple[str, ...],
    symbol_table: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for raw in source_mems:
        address_text, origin = split_assignment(raw)
        try:
            spec = parse_address_spec(address_text)
        except ValueError:
            continue
        record = spec.as_dict()
        record["origin"] = origin or f"source_mem:{spec.evidence()}"
        records.append(record)
    for symbol in source_symbols:
        entry = symbol_table.get(symbol)
        if not entry:
            continue
        raw = str(entry.get("bank_address") or f"{int(entry.get('address', 0)):04X}")
        try:
            spec = parse_address_spec(raw)
        except ValueError:
            continue
        record = spec.as_dict()
        record["origin"] = f"source_symbol:{symbol}"
        record["symbol"] = symbol
        records.append(record)
    return unique_address_records(records)


def sink_address_spec_records(
    *,
    sink_symbols: tuple[str, ...],
    sink_addresses: tuple[str, ...],
    sink_size: int,
    symbol_table: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for symbol in sink_symbols:
        entry = symbol_table.get(symbol)
        if not entry:
            continue
        raw = str(entry.get("bank_address") or f"{int(entry.get('address', 0)):04X}")
        try:
            spec = parse_address_spec(raw)
        except ValueError:
            continue
        record = spec.as_dict()
        record["symbol"] = symbol
        record["size"] = default_symbol_size(symbol, sink_size)
        records.append(record)
    for raw in sink_addresses:
        name, _origin = split_assignment(raw)
        try:
            spec = parse_address_spec(name)
        except ValueError:
            continue
        record = spec.as_dict()
        record["size"] = sink_size
        records.append(record)
    return unique_address_records(records)


def unique_address_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        key = str(record.get("key", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(record)
    return out


def address_precision_report(
    *,
    source_address_specs: list[dict[str, Any]],
    sink_address_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    raw_banked_inputs = [
        address_precision_item(record, role="source")
        for record in source_address_specs
        if raw_address_is_banked(record) and not record.get("symbol")
    ]
    raw_banked_inputs.extend(
        address_precision_item(record, role="sink")
        for record in sink_address_specs
        if raw_address_is_banked(record) and not record.get("symbol")
    )
    warnings = []
    if raw_banked_inputs:
        warnings.append(
            "bank-qualified raw source/sink addresses are retained in AddressSpec records, "
            "but dynamic taint currently matches traced memory through the observed 16-bit bus address; "
            "attach runtime bank evidence before claiming bank-exact provenance"
        )
    return {
        "engine_address_model": "bus_16bit",
        "bank_exact": not raw_banked_inputs,
        "raw_banked_input_count": len(raw_banked_inputs),
        "raw_banked_inputs": raw_banked_inputs[:20],
        "warnings": warnings,
    }


def raw_address_is_banked(record: dict[str, Any]) -> bool:
    raw = str(record.get("raw", ""))
    return ":" in raw and record.get("bank") is not None


def address_precision_item(record: dict[str, Any], *, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "raw": str(record.get("raw", "")),
        "space": str(record.get("space", "")),
        "bank": record.get("bank"),
        "address": str(record.get("address_hex", "")),
        "cli": str(record.get("cli", "")),
        "evidence": str(record.get("evidence", "")),
        "key": str(record.get("key", "")),
    }


def build_unmodeled_write_diagnostics(
    *,
    source: str,
    instructions: list[Instruction],
    frames: list[InstructionFrame],
) -> list[dict[str, Any]]:
    by_pc = {(instruction.bank, instruction.pc): instruction for instruction in instructions}
    diagnostics: list[dict[str, Any]] = []
    for frame in sorted(frames, key=lambda item: int(item.seq)):
        instruction = by_pc.get((frame.bank, frame.pc))
        if instruction is None:
            continue
        diagnostics.extend(
            unmodeled_write_diagnostic(source=source, instruction=instruction, frame=frame, **item)
            for item in instruction_unmodeled_write_diagnostics(instruction, frame)
        )
    return diagnostics


def build_write_attributions(
    *,
    source: str,
    instructions: list[Instruction],
    frames: list[InstructionFrame],
    sinks: list[Sink],
    register_sources: dict[str, str],
    source_memory: dict[int, str],
    source_address_specs: list[dict[str, Any]] | None = None,
    symbol_table: dict[str, dict[str, Any]],
    taint_findings: list[Any],
) -> list[dict[str, Any]]:
    by_pc = {(instruction.bank, instruction.pc): instruction for instruction in instructions}
    taint_by_write = {
        (int(finding.seq), int(finding.address), str(finding.sink)): list(finding.taint)
        for finding in taint_findings
    }
    attributions: list[dict[str, Any]] = []
    register_state: dict[str, dict[str, Any]] = {}
    for frame in sorted(frames, key=lambda item: int(item.seq)):
        instruction = by_pc.get((frame.bank, frame.pc))
        if instruction is None:
            continue
        for write in instruction_memory_writes(instruction, frame):
            address = int(write["address"]) & 0xFFFF
            for sink in sinks:
                match = instruction_sink_match(sink, frame=frame, address=address)
                if not match:
                    continue
                taint = taint_by_write.get((int(frame.seq), address, sink.name), [])
                value_hex = str(write.get("value_hex", ""))
                value_source = str(write.get("value_source", ""))
                proof_status = match_proof_status(match)
                source_operands = [
                    enrich_source_operand(
                        operand,
                        register_sources=register_sources,
                        source_memory=source_memory,
                        source_address_specs=source_address_specs or [],
                        symbol_table=symbol_table,
                    )
                    for operand in write["source_operands"]
                    if isinstance(operand, dict)
                ]
                provenance_operands, register_provenance = register_provenance_for_operands(
                    source_operands,
                    register_state=register_state,
                )
                source_operands = [*source_operands, *provenance_operands]
                contributors = contributors_for_operands(source_operands)
                contributor_taint = unique_list(contributor.get("symbol", "") for contributor in contributors)
                taint = unique_list([*taint, *contributor_taint])
                pc_label = str(frame.pc_label)
                target = sink.name
                attribution = {
                    "id": f"dynamic_write_{len(attributions) + 1:04d}",
                    "source": source,
                    "target": target,
                    "access": "dynamic_write",
                    "seq": int(frame.seq),
                    "pc": int(frame.pc),
                    "pc_label": pc_label,
                    "mnemonic": instruction.mnemonic,
                    "sink": sink.name,
                    "sink_address": f"{sink.address:04X}",
                    "address": f"{address:04X}",
                    "address_key": str(match.get("address_key", "")),
                    "match_precision": str(match.get("match_precision", "")),
                    "bank_match": str(match.get("bank_match", "")),
                    "bank_source": str(match.get("bank_source", "")),
                    "proof_downgrade_reason": str(match.get("proof_downgrade_reason", "")),
                    "address_symbol": symbol_for_address(address, symbol_table),
                    "sink_offset": address - sink.address,
                    "write_kind": str(write["kind"]),
                    "model_source": str(write.get("model_source", "")),
                    "source_operands": source_operands,
                    "register_provenance": register_provenance,
                    "contributors": contributors,
                    "taint": taint,
                    "score": write_attribution_score(contributors=contributors, taint=taint),
                    "confidence": 0.9 if taint else 0.76,
                    "proof_status": proof_status,
                    "evidence_atoms": [
                        dynamic_write_attribution_evidence_atom(
                            claim_type="dynamic_taint.write_attribution",
                            source=source,
                            source_kind="instruction_trace_write_attribution",
                            proof_status=proof_status,
                            target=target,
                            seq=int(frame.seq),
                            pc=int(frame.pc),
                            pc_label=pc_label,
                            mnemonic=instruction.mnemonic,
                            address=address,
                            sink_size=sink.size,
                            contributors=contributors,
                            taint=taint,
                            precision={
                                "write_kind": str(write["kind"]),
                                "address_key": str(match.get("address_key", "")),
                                "match_precision": str(match.get("match_precision", "")),
                                "bank_match": str(match.get("bank_match", "")),
                                "bank_source": str(match.get("bank_source", "")),
                                "proof_downgrade_reason": str(match.get("proof_downgrade_reason", "")),
                                "model_source": str(write.get("model_source", "")),
                                "value_source": value_source,
                            },
                        )
                    ],
                    "evidence": write_attribution_evidence(
                        seq=int(frame.seq),
                        pc=int(frame.pc),
                        mnemonic=instruction.mnemonic,
                        target=target,
                        address=address,
                        source_operands=source_operands,
                        taint=taint,
                        register_provenance=register_provenance,
                        value_hex=value_hex,
                        value_source=value_source,
                        match=match,
                    ),
                    "related_symbols": related_symbols_for_write(
                        target=target,
                        pc_label=pc_label,
                        address=address,
                        source_operands=source_operands,
                        symbol_table=symbol_table,
                    ),
                    "related_addresses": related_addresses_for_write(target=target, address=address, sink=sink),
                    "related_files": [],
                    "sink_size": sink.size,
                    "commands": commands_for_write_attribution(
                        target=target,
                        routine=base_label(pc_label) or pc_label,
                        source=source,
                        sink_size=sink.size,
                    ),
                }
                if value_hex:
                    attribution["value_hex"] = value_hex
                    if value_source:
                        attribution["value_source"] = value_source
                attributions.append(attribution)
        update_direct_register_state(
            register_state,
            source=source,
            instruction=instruction,
            frame=frame,
            register_sources=register_sources,
            source_memory=source_memory,
            source_address_specs=source_address_specs or [],
            symbol_table=symbol_table,
        )
    return attributions


def update_direct_register_state(
    register_state: dict[str, dict[str, Any]],
    *,
    source: str,
    instruction: Instruction,
    frame: InstructionFrame,
    register_sources: dict[str, str],
    source_memory: dict[int, str],
    source_address_specs: list[dict[str, Any]],
    symbol_table: dict[str, dict[str, Any]],
) -> None:
    event = {
        "seq": int(frame.seq),
        "pc_bank_address": f"{int(frame.bank):02X}:{int(frame.pc):04X}",
        "pc_label": str(frame.pc_label),
    }
    loaded = {"source": source}
    for effect_item in instruction_register_writes_for_attribution(instruction, frame):
        update_register_state_from_effect(
            register_state,
            loaded=loaded,
            event=event,
            effect_item=effect_item,
            register_sources=register_sources,
            source_memory=source_memory,
            source_address_specs=source_address_specs,
            symbol_table=symbol_table,
        )


def instruction_register_writes_for_attribution(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    op = int(instruction.opcode)
    if op in {0xAF, 0x97}:
        operation = "xor a" if op == 0xAF else "sub a"
        return [register_write_record("A", operation, source_operands=[immediate_operand(0)], value=0, value_source="modeled_zero_idiom")]
    if op in {0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E}:
        model = load_semantics(op)
        target = model.register_target
        value = int(instruction.operand[0]) & 0xFF if instruction.operand else None
        operands = [immediate_operand(value)] if value is not None else []
        item = register_write_record(target, model.operation, source_operands=operands, value=value, value_source="instruction_immediate" if value is not None else "")
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op in {0x01, 0x11, 0x21, 0x31}:
        model = load_semantics(op)
        target = model.register_target
        value = u16_from_operand(instruction)
        item = register_write_record(target, model.operation, source_operands=[immediate_word_operand(value)], value=value, value_source="instruction_immediate")
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op == 0xF9:
        model = load_semantics(op)
        value = pair_value_if_known(frame, "hl")
        item = register_write_record(model.register_target, model.operation, source_operands=[register_operand(model.register_source, frame)], value=value, value_source="pre_register" if value is not None else "")
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op == 0xF8 and instruction.operand:
        return ld_hl_sp_e8_register_records(instruction, frame)
    try:
        add_hl_semantics(op)
        return add_hl_register_records(frame, op)
    except ValueError:
        pass
    if op == 0xE8 and instruction.operand:
        return add_sp_e8_register_records(instruction, frame)
    if op in {0xC5, 0xD5, 0xE5, 0xF5}:
        model = stack_control_semantics(op)
        return [sp_delta_register_record(frame, model.sp_write_operation, model.sp_delta, model_source=SM83_MODEL_SOURCE)]
    if op == 0xCD or (op in CONDITIONAL_CALLS and frame_condition_true(frame, CONDITIONAL_CALLS[op])):
        model = stack_control_semantics(op)
        return [sp_delta_register_record(frame, model.sp_write_operation, model.sp_delta, model_source=SM83_MODEL_SOURCE)]
    if op in RST_TARGETS:
        model = stack_control_semantics(op)
        return [sp_delta_register_record(frame, model.sp_write_operation, model.sp_delta, model_source=SM83_MODEL_SOURCE)]
    if op in {0xC9, 0xD9} or (op in CONDITIONAL_RETS and frame_condition_true(frame, CONDITIONAL_RETS[op])):
        model = stack_control_semantics(op)
        return [sp_delta_register_record(frame, model.sp_write_operation, model.sp_delta, model_source=SM83_MODEL_SOURCE)]
    try:
        model = register_pair_inc_dec_semantics(op)
    except ValueError:
        model = None
    if model is not None:
        value = pair_value_if_known(frame, model.register_pair)
        item = register_write_record(
            model.register_pair.upper(),
            model.operation,
            source_operands=[register_operand(model.register_pair, frame)],
            value=model.updated_value(value),
            value_source="modeled_from_pre_register" if value is not None else "",
        )
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op in {0x22, 0x32}:
        return [hli_hld_hl_writeback_record(op, frame)]
    if 0x40 <= op <= 0x7F and op != 0x76:
        model = load_semantics(op)
        if model.target_kind == "register" and model.source_kind == "register":
            target = model.register_target
            source = model.register_source
            value = reg_value_if_known(frame, source)
            item = register_write_record(
                target,
                model.operation,
                source_operands=[register_operand(source, frame)],
                value=value,
                value_source="pre_register" if value is not None else "",
            )
            item["model_source"] = SM83_MODEL_SOURCE
            return [item]
    try:
        model = inc_dec_semantics(op)
    except ValueError:
        model = None
    if model is not None and not model.is_memory_target:
        old_value = reg_value_if_known(frame, model.target)
        flags = frame_flags(frame)
        records = [
            register_write_record(
                model.register_target,
                model.operation,
                source_operands=[register_operand(model.target, frame)],
                value=model.result(old_value),
                value_source="modeled_from_pre_register" if old_value is not None else "",
            ),
            register_write_record(
                "F",
                model.flag_operation,
                source_operands=[register_operand(model.target, frame), register_operand("f", frame)],
                value=model.flags(old_value=old_value, flags=flags),
                value_source="modeled_from_pre_register" if old_value is not None and flags is not None else "",
            ),
        ]
        for record in records:
            record["model_source"] = SM83_MODEL_SOURCE
        return records
    accumulator_records = accumulator_register_write_records(op, frame)
    if accumulator_records:
        return accumulator_records
    alu_records = alu_register_write_records(instruction, frame)
    if alu_records:
        return alu_records
    if op == 0x0A:
        model = load_semantics(op)
        address = pair_value_if_known(frame, "bc")
        if address is None:
            return [unknown_direct_register_write(model.register_target, model.operation)]
        load = register_load_record(model.register_target, address, operation=model.operation, frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [load]
    if op == 0x1A:
        model = load_semantics(op)
        address = pair_value_if_known(frame, "de")
        if address is None:
            return [unknown_direct_register_write(model.register_target, model.operation)]
        load = register_load_record(model.register_target, address, operation=model.operation, frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [load]
    if op in {0x2A, 0x3A}:
        address = pair_value_if_known(frame, "hl")
        if address is None:
            return [
                unknown_direct_register_write("A", hli_hld_load_operation(op)),
                hli_hld_hl_writeback_record(op, frame),
            ]
        load = register_load_record("A", address, operation=hli_hld_load_operation(op), frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [
            load,
            hli_hld_hl_writeback_record(op, frame),
        ]
    if 0x40 <= op <= 0x7F and op != 0x76 and INDEX_REG[op & 0x07] == "[hl]":
        model = load_semantics(op)
        target = model.register_target
        address = pair_value_if_known(frame, "hl")
        if address is None:
            return [unknown_direct_register_write(target, model.operation)]
        load = register_load_record(target, address, operation=model.operation, frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [load]
    if op == 0xFA:
        model = load_semantics(op)
        load = register_load_record(model.register_target, u16_from_operand(instruction), operation=model.operation, frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [load]
    if op == 0xF0 and instruction.operand:
        model = load_semantics(op)
        load = register_load_record(model.register_target, 0xFF00 + int(instruction.operand[0]), operation=model.operation.replace("ld a, [n]", "ldh a, [n]"), frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [load]
    if op == 0xF2:
        model = load_semantics(op)
        c = reg_value_if_known(frame, "c")
        if c is None:
            return [unknown_direct_register_write(model.register_target, model.operation.replace("ld a, [c]", "ldh a, [c]"))]
        load = register_load_record(model.register_target, 0xFF00 + c, operation=model.operation.replace("ld a, [c]", "ldh a, [c]"), frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [load]
    if op in {0xC1, 0xD1, 0xE1, 0xF1}:
        model = stack_control_semantics(op)
        target = model.register_pair.upper()
        sp = pair_value_if_known(frame, "sp")
        if sp is None:
            return [
                unknown_direct_register_write(target, model.register_write_operation),
                sp_delta_register_record(frame, model.sp_write_operation, model.sp_delta, model_source=SM83_MODEL_SOURCE),
            ]
        low, low_source = frame_memory_sample(frame, sp)
        high, high_source = frame_memory_sample(frame, sp + 1)
        value = stack_pop_register_value(model.register_pair, low, high)
        value_source = "observed_memory_snapshot" if value is not None else ""
        register_write = register_write_record(
            target,
            model.register_write_operation,
            source_operands=[
                memory_operand(sp, value=low, value_source=low_source),
                memory_operand(sp + 1, value=high, value_source=high_source),
            ],
            value=value,
            value_source=value_source,
        )
        register_write["model_source"] = SM83_MODEL_SOURCE
        return [
            register_write,
            sp_delta_register_record(frame, model.sp_write_operation, model.sp_delta, model_source=SM83_MODEL_SOURCE),
        ]
    if op == 0xCB and instruction.operand:
        return cb_register_write_records(int(instruction.operand[0]), frame)
    return []


def ld_hl_sp_e8_register_records(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    model = sp_relative_semantics(0xF8)
    sp = pair_value_if_known(frame, "sp")
    raw_offset = int(instruction.operand[0])
    operands = [register_operand("sp", frame), immediate_operand(raw_offset)]
    records = [
        register_write_record(
            model.target_register,
            model.operation,
            source_operands=operands,
            value=model.result(sp=sp, raw_offset=raw_offset),
            value_source="modeled_from_pre_register" if sp is not None else "",
        ),
        register_write_record(
            "F",
            model.flag_operation,
            source_operands=operands,
            value=model.flags(sp=sp, raw_offset=raw_offset),
            value_source="modeled_from_pre_register" if sp is not None else "",
        ),
    ]
    for record in records:
        record["model_source"] = SM83_MODEL_SOURCE
    return records


def add_hl_register_records(frame: InstructionFrame, opcode: int) -> list[dict[str, Any]]:
    model = add_hl_semantics(opcode)
    hl = pair_value_if_known(frame, "hl")
    source = pair_value_if_known(frame, model.source_pair)
    flags = frame_flags(frame)
    operands = [register_operand("hl", frame), register_operand(model.source_pair, frame)]
    records = [
        register_write_record(
            "HL",
            model.operation,
            source_operands=operands,
            value=model.result(hl=hl, source=source),
            value_source="modeled_from_pre_register" if hl is not None and source is not None else "",
        ),
        register_write_record(
            "F",
            model.flag_operation,
            source_operands=operands,
            value=model.flags(hl=hl, source=source, flags=flags),
            value_source="modeled_from_pre_register" if hl is not None and source is not None and flags is not None else "",
        ),
    ]
    for record in records:
        record["model_source"] = SM83_MODEL_SOURCE
    return records


def add_sp_e8_register_records(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    model = sp_relative_semantics(0xE8)
    sp = pair_value_if_known(frame, "sp")
    raw_offset = int(instruction.operand[0])
    operands = [register_operand("sp", frame), immediate_operand(raw_offset)]
    records = [
        register_write_record(
            model.target_register,
            model.operation,
            source_operands=operands,
            value=model.result(sp=sp, raw_offset=raw_offset),
            value_source="modeled_from_pre_register" if sp is not None else "",
        ),
        register_write_record(
            "F",
            model.flag_operation,
            source_operands=operands,
            value=model.flags(sp=sp, raw_offset=raw_offset),
            value_source="modeled_from_pre_register" if sp is not None else "",
        ),
    ]
    for record in records:
        record["model_source"] = SM83_MODEL_SOURCE
    return records


def sp_delta_register_record(frame: InstructionFrame, operation: str, delta: int, *, model_source: str = "") -> dict[str, Any]:
    sp = pair_value_if_known(frame, "sp")
    record = register_write_record(
        "SP",
        operation,
        source_operands=[register_operand("sp", frame)],
        value=(sp + delta) & 0xFFFF if sp is not None else None,
        value_source="modeled_from_pre_register" if sp is not None else "",
    )
    if model_source:
        record["model_source"] = model_source
    return record


def hli_hld_load_operation(opcode: int) -> str:
    return hli_hld_semantics(opcode).memory_operation


def hli_hld_hl_writeback_record(opcode: int, frame: InstructionFrame) -> dict[str, Any]:
    value = pair_value_if_known(frame, "hl")
    model = hli_hld_semantics(opcode)
    record = register_write_record(
        "HL",
        model.hl_writeback_operation,
        source_operands=[register_operand("hl", frame)],
        value=model.updated_hl(value),
        value_source="modeled_from_pre_register" if value is not None else "",
    )
    record["model_source"] = SM83_MODEL_SOURCE
    return record


def alu_register_write_records(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    op = int(instruction.opcode)
    source_operands: list[dict[str, Any]] = []
    source_value: int | None = None
    if 0x80 <= op <= 0xBF:
        source = INDEX_REG[op & 0x07]
        source_operands = [register_operand("a", frame)]
        if source == "[hl]":
            address = pair_value_if_known(frame, "hl")
            if address is not None:
                value, value_source = frame_memory_sample(frame, address)
                source_operands.append(memory_operand(address, value=value, value_source=value_source))
                source_value = value
        else:
            source_operands.append(register_operand(source, frame))
            source_value = reg_value_if_known(frame, source)
    else:
        if not instruction.operand:
            return []
        try:
            model = alu_semantics(op)
        except ValueError:
            return []
        source_value = int(instruction.operand[0]) & 0xFF
        source_operands = [register_operand("a", frame), immediate_operand(source_value)]
    model = alu_semantics(op)
    a = reg_value_if_known(frame, "a")
    flags = frame_flags(frame)
    operation = model.operation(alu_source_label(op))
    records: list[dict[str, Any]] = []
    if model.group != 7:
        value = model.result(a=a, source=source_value, flags=flags)
        a_write = register_write_record(
            "A",
            operation,
            source_operands=source_operands,
            value=value,
            value_source="modeled_from_pre_register" if value is not None else "",
        )
        a_write["model_source"] = SM83_MODEL_SOURCE
        records.append(a_write)
    flag_value = model.flags(a=a, source=source_value, flags=flags)
    flags_write = register_write_record(
        "F",
        f"{operation} flags",
        source_operands=source_operands,
        value=flag_value,
        value_source="modeled_from_pre_register" if flag_value is not None else "",
    )
    flags_write["model_source"] = SM83_MODEL_SOURCE
    records.append(flags_write)
    return records


def alu_source_label(opcode: int) -> str:
    if 0x80 <= opcode <= 0xBF:
        return INDEX_REG[opcode & 0x07]
    return "n"


def flag_byte(
    *,
    zero: bool = False,
    subtract: bool = False,
    half: bool = False,
    carry: bool = False,
) -> int:
    return (
        (0x80 if zero else 0)
        | (0x40 if subtract else 0)
        | (0x20 if half else 0)
        | (0x10 if carry else 0)
    )


def accumulator_register_write_records(opcode: int, frame: InstructionFrame) -> list[dict[str, Any]]:
    try:
        model = accumulator_flag_semantics(opcode)
    except ValueError:
        return []
    a = reg_value_if_known(frame, "a")
    flags = frame_flags(frame)
    records: list[dict[str, Any]] = []
    if model.writes_accumulator:
        value = model.result(a=a, flags=flags)
        item = register_write_record(
            "A",
            model.operation,
            source_operands=accumulator_model_operands(model, frame, target_register="A"),
            value=value,
            value_source="modeled_from_pre_register" if value is not None else "",
        )
        item["model_source"] = SM83_MODEL_SOURCE
        records.append(item)
    flag_value = model.flags(a=a, flags=flags)
    flag_item = register_write_record(
        "F",
        model.flag_operation,
        source_operands=accumulator_model_operands(model, frame, target_register="F"),
        value=flag_value,
        value_source="modeled_from_pre_register" if flag_value is not None else "",
    )
    flag_item["model_source"] = SM83_MODEL_SOURCE
    records.append(flag_item)
    return records


def accumulator_model_operands(model: Any, frame: InstructionFrame, *, target_register: str) -> list[dict[str, Any]]:
    if model.opcode in {0x07, 0x0F}:
        return [register_operand("a", frame)]
    if model.opcode in {0x17, 0x1F, 0x27}:
        return [register_operand("a", frame), register_operand("f", frame)]
    if model.opcode == 0x2F and target_register == "A":
        return [register_operand("a", frame)]
    return [register_operand("f", frame)]


def cb_register_write_records(subopcode: int, frame: InstructionFrame) -> list[dict[str, Any]]:
    model = cb_semantics(subopcode)
    target = model.target
    if model.is_memory_target:
        if not model.writes_flags:
            return []
        return [cb_hl_flag_write_record(model.subopcode, frame)]
    old_value = reg_value_if_known(frame, target)
    if model.group == 1:
        item = register_write_record(
            "F",
            f"{model.operation(target)} flags",
            source_operands=cb_flag_source_operands(model.subopcode, register_operand(target, frame), frame),
            value=model.flags(old_value, flags=frame_flags(frame)),
            value_source="modeled_from_pre_register" if old_value is not None and frame_flags(frame) is not None else "",
        )
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if not model.writes_value:
        return []
    value = model.result(old_value, flags=frame_flags(frame))
    value_item = register_write_record(
        target.upper(),
        model.operation(target),
        source_operands=[register_operand(target, frame)],
        value=value,
        value_source="modeled_from_pre_register" if value is not None else "",
    )
    value_item["model_source"] = SM83_MODEL_SOURCE
    records = [value_item]
    if model.writes_flags:
        flag_value = model.flags(old_value, flags=frame_flags(frame))
        flag_item = register_write_record(
            "F",
            f"{model.operation(target)} flags",
            source_operands=cb_flag_source_operands(model.subopcode, register_operand(target, frame), frame),
            value=flag_value,
            value_source="modeled_from_pre_register" if flag_value is not None else "",
        )
        flag_item["model_source"] = SM83_MODEL_SOURCE
        records.append(flag_item)
    return records


def cb_flag_source_operands(subopcode: int, value_operand: dict[str, Any], frame: InstructionFrame) -> list[dict[str, Any]]:
    model = cb_semantics(subopcode)
    operands = [value_operand]
    if model.reads_carry_for_flags:
        operands.append(register_operand("f", frame))
    return operands


def cb_hl_flag_write_record(subopcode: int, frame: InstructionFrame) -> dict[str, Any]:
    address = pair_value_if_known(frame, "hl")
    old_value = None
    old_value_source = ""
    value_operand = register_operand("hl", frame)
    if address is not None:
        old_value, old_value_source = frame_memory_sample(frame, address)
        value_operand = memory_operand(address, value=old_value, value_source=old_value_source)
    flag_value = cb_flags(subopcode, old_value, flags=frame_flags(frame))
    item = register_write_record(
        "F",
        f"{cb_register_operation(subopcode, '[hl]')} flags",
        source_operands=cb_flag_source_operands(subopcode, value_operand, frame),
        value=flag_value,
        value_source=modeled_value_source(old_value_source) if flag_value is not None and old_value_source else "",
    )
    item["model_source"] = SM83_MODEL_SOURCE
    return item


def register_load_record(register: str, address: int, *, operation: str, frame: InstructionFrame) -> dict[str, Any]:
    value, value_source = frame_memory_sample(frame, address)
    return register_write_record(
        register,
        operation,
        source_operands=[memory_operand(address, value=value, value_source=value_source)],
        value=value,
        value_source=value_source,
    )


def register_write_record(
    register: str,
    operation: str,
    *,
    source_operands: list[dict[str, Any]],
    value: int | None = None,
    value_source: str = "",
) -> dict[str, Any]:
    register = register.upper()
    width = 4 if register in {"AF", "BC", "DE", "HL", "SP"} else 2
    out = {
        "access": "register_write",
        "register": register,
        "operation": operation,
        "source_operands": [operand for operand in source_operands if operand],
    }
    if value is not None:
        mask = (1 << (width * 4)) - 1
        out["value_hex"] = f"{int(value) & mask:0{width}X}"
        if value_source:
            out["value_source"] = value_source
    return out


def unknown_direct_register_write(register: str, operation: str) -> dict[str, Any]:
    return {
        "access": "register_write",
        "register": register.upper(),
        "operation": operation,
        "source_operands": [],
        "evidence_status": "unmodeled_missing_register",
    }


def instruction_memory_writes(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    op = instruction.opcode
    if op == 0x02:
        model = load_semantics(op)
        address = pair_value_if_known(frame, "bc")
        if address is None:
            return []
        return [
            memory_write(
                address,
                model.operation,
                register_operand("a", frame),
                value=reg_value_if_known(frame, "a"),
                value_source="pre_register",
                model_source=SM83_MODEL_SOURCE,
            )
        ]
    if op == 0x12:
        model = load_semantics(op)
        address = pair_value_if_known(frame, "de")
        if address is None:
            return []
        return [
            memory_write(
                address,
                model.operation,
                register_operand("a", frame),
                value=reg_value_if_known(frame, "a"),
                value_source="pre_register",
                model_source=SM83_MODEL_SOURCE,
            )
        ]
    if op in {0x22, 0x32}:
        address = pair_value_if_known(frame, "hl")
        if address is None:
            return []
        model = hli_hld_semantics(op)
        return [
            memory_write(
                address,
                model.memory_operation,
                register_operand("a", frame),
                value=reg_value_if_known(frame, "a"),
                value_source="pre_register",
                model_source=SM83_MODEL_SOURCE,
            )
        ]
    if op == 0x36:
        model = load_semantics(op)
        address = pair_value_if_known(frame, "hl")
        if address is None:
            return []
        value = instruction.operand[0] if instruction.operand else 0
        return [
            memory_write(
                address,
                model.operation,
                immediate_operand(value),
                value=value,
                value_source="instruction_immediate",
                model_source=SM83_MODEL_SOURCE,
            )
        ]
    if 0x70 <= op <= 0x77 and op != 0x76:
        model = load_semantics(op)
        if model.source_kind == "memory":
            return []
        source = model.register_source
        address = pair_value_if_known(frame, "hl")
        if address is None:
            return []
        return [
            memory_write(
                address,
                model.operation,
                register_operand(source, frame),
                value=reg_value_if_known(frame, source),
                value_source="pre_register",
                model_source=SM83_MODEL_SOURCE,
            )
        ]
    if op in {0x34, 0x35}:
        model = inc_dec_semantics(op)
        address = pair_value_if_known(frame, "hl")
        if address is None:
            return []
        old_value, old_value_source = frame_memory_sample(frame, address)
        return [
            memory_write(
                address,
                model.operation,
                memory_operand(address, value=old_value, value_source=old_value_source),
                value=model.result(old_value),
                value_source=modeled_value_source(old_value_source),
                model_source=SM83_MODEL_SOURCE,
            )
        ]
    if op == 0x08:
        model = load_semantics(op)
        address = u16_from_operand(instruction)
        sp = pair_value_if_known(frame, "sp")
        return [
            memory_write(
                address,
                f"{model.operation} low",
                register_operand("sp", frame),
                value=sp,
                value_source="pre_register",
                model_source=SM83_MODEL_SOURCE,
            ),
            memory_write(
                address + 1,
                f"{model.operation} high",
                register_operand("sp", frame),
                value=sp >> 8 if sp is not None else None,
                value_source="pre_register",
                model_source=SM83_MODEL_SOURCE,
            ),
        ]
    if op == 0xEA:
        model = load_semantics(op)
        return [
            memory_write(
                u16_from_operand(instruction),
                model.operation,
                register_operand("a", frame),
                value=reg_value_if_known(frame, "a"),
                value_source="pre_register",
                model_source=SM83_MODEL_SOURCE,
            )
        ]
    if op == 0xE0 and instruction.operand:
        model = load_semantics(op)
        return [
            memory_write(
                0xFF00 + int(instruction.operand[0]),
                model.operation.replace("ld [n], a", "ldh [n], a"),
                register_operand("a", frame),
                value=reg_value_if_known(frame, "a"),
                value_source="pre_register",
                model_source=SM83_MODEL_SOURCE,
            )
        ]
    if op == 0xE2:
        model = load_semantics(op)
        c = reg_value_if_known(frame, "c")
        if c is None:
            return []
        return [
            memory_write(
                0xFF00 + c,
                model.operation.replace("ld [c], a", "ldh [c], a"),
                register_operand("a", frame),
                value=reg_value_if_known(frame, "a"),
                value_source="pre_register",
                model_source=SM83_MODEL_SOURCE,
            )
        ]
    if op in {0xC5, 0xD5, 0xE5, 0xF5}:
        model = stack_control_semantics(op)
        pair = model.register_pair
        low, high = register_pair_stack_components(pair)
        return stack_push_writes(
            frame,
            operation=model.stack_write_operation,
            source=register_operand(pair, frame),
            low_source=register_operand(low, frame),
            high_source=register_operand(high, frame),
            value_source="pre_register",
            model_source=SM83_MODEL_SOURCE,
        )
    if op == 0xCD or (op in CONDITIONAL_CALLS and frame_condition_true(frame, CONDITIONAL_CALLS[op])):
        model = stack_control_semantics(op)
        return stack_push_writes(
            frame,
            operation=model.stack_write_operation,
            source=immediate_word_operand(
                (frame.pc + instruction.length) & 0xFFFF,
                value_source="modeled_return_address",
            ),
            value_source="modeled_return_address",
            model_source=SM83_MODEL_SOURCE,
        )
    if op in RST_TARGETS:
        model = stack_control_semantics(op)
        return stack_push_writes(
            frame,
            operation=model.stack_write_operation,
            source=immediate_word_operand(
                (frame.pc + instruction.length) & 0xFFFF,
                value_source="modeled_return_address",
            ),
            value_source="modeled_return_address",
            model_source=SM83_MODEL_SOURCE,
        )
    if op == 0xCB and instruction.operand:
        model = cb_semantics(int(instruction.operand[0]))
        if model.is_memory_target and model.writes_value:
            address = pair_value_if_known(frame, "hl")
            if address is None:
                return []
            old_value, old_value_source = frame_memory_sample(frame, address)
            return [
                memory_write(
                    address,
                    model.operation(),
                    memory_operand(address, value=old_value, value_source=old_value_source),
                    value=model.result(old_value, flags=frame_flags(frame)),
                    value_source=modeled_value_source(old_value_source),
                    model_source=SM83_MODEL_SOURCE,
                )
            ]
    return []


def instruction_unmodeled_write_diagnostics(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    op = instruction.opcode
    if op == 0x02 and pair_value_if_known(frame, "bc") is None:
        model = load_semantics(op)
        return [unmodeled_write_model(model.operation, address_source=model.address_source, missing=missing_registers_for_pair(frame, "bc"))]
    if op == 0x12 and pair_value_if_known(frame, "de") is None:
        model = load_semantics(op)
        return [unmodeled_write_model(model.operation, address_source=model.address_source, missing=missing_registers_for_pair(frame, "de"))]
    if op in {0x22, 0x32} and pair_value_if_known(frame, "hl") is None:
        model = hli_hld_semantics(op)
        return [unmodeled_write_model(model.memory_operation, address_source="hl", missing=missing_registers_for_pair(frame, "hl"))]
    if op == 0x36 and pair_value_if_known(frame, "hl") is None:
        model = load_semantics(op)
        return [unmodeled_write_model(model.operation, address_source=model.address_source, missing=missing_registers_for_pair(frame, "hl"))]
    if 0x70 <= op <= 0x77 and op != 0x76:
        model = load_semantics(op)
        if model.source_kind != "memory" and pair_value_if_known(frame, "hl") is None:
            return [unmodeled_write_model(model.operation, address_source=model.address_source, missing=missing_registers_for_pair(frame, "hl"))]
    if op in {0x34, 0x35} and pair_value_if_known(frame, "hl") is None:
        model = inc_dec_semantics(op)
        return [unmodeled_write_model(model.operation, address_source=model.address_source, missing=missing_registers_for_pair(frame, "hl"))]
    if op == 0xE2 and reg_value_if_known(frame, "c") is None:
        model = load_semantics(op)
        return [
            unmodeled_write_model(
                model.operation.replace("ld [c], a", "ldh [c], a"),
                kind="unmodeled_io_write",
                address_source=model.address_source,
                missing=["C"],
            )
        ]
    if op == 0xCB and instruction.operand:
        model = cb_semantics(int(instruction.operand[0]))
        if model.is_memory_target and model.writes_value and pair_value_if_known(frame, "hl") is None:
            return [unmodeled_write_model(model.operation(), address_source="hl", missing=missing_registers_for_pair(frame, "hl"))]
    return []


def unmodeled_write_model(
    operation: str,
    *,
    address_source: str,
    missing: list[str],
    kind: str = "unmodeled_memory_write",
) -> dict[str, Any]:
    return {
        "kind": kind,
        "operation": operation,
        "address_source": address_source,
        "missing_registers": unique_list(register.upper() for register in missing if register),
    }


def unmodeled_write_diagnostic(
    *,
    source: str,
    instruction: Instruction,
    frame: InstructionFrame,
    kind: str,
    operation: str,
    address_source: str,
    missing_registers: list[str],
) -> dict[str, Any]:
    missing = unique_list(register.upper() for register in missing_registers if register)
    proof_status = "instruction_observed"
    target_match_proof_status = "planned_only"
    attribution_status = "unresolved_missing_register"
    pc_label = str(frame.pc_label)
    diagnostic = {
        "source": source,
        "source_kind": "instruction_trace_unmodeled_write",
        "kind": kind,
        "access": "unmodeled",
        "category": "missing_pre_register",
        "seq": int(frame.seq),
        "pc": int(frame.pc),
        "pc_bank_address": f"{int(frame.bank):02X}:{int(frame.pc):04X}",
        "pc_label": pc_label,
        "mnemonic": instruction.mnemonic,
        "operation": operation,
        "model_source": SM83_MODEL_SOURCE,
        "evidence_source": "instruction_frame_missing_register",
        "evidence_status": "unmodeled_missing_register",
        "runtime_observation": "instruction_frame",
        "address_source": address_source,
        "missing_registers": missing,
        "proof_status": proof_status,
        "target_match_proof_status": target_match_proof_status,
        "attribution_status": attribution_status,
        "message": "Instruction was observed, but required pre-instruction address registers were not present in the trace frame.",
        "related_symbols": unique_list([base_label(pc_label) or pc_label]),
        "related_addresses": [],
        "commands": [
            f"python -m tools.debugger effect-trace --trace {quote_arg(source)} --watch-address <sink>",
            f"python -m tools.debugger trace-instructions --trace {quote_arg(source)} --out-trace <dense-trace.jsonl>",
        ],
    }
    diagnostic["evidence"] = [
        f"seq={diagnostic['seq']}",
        f"pc={diagnostic['pc_bank_address']}",
        f"operation={operation}",
        f"missing={','.join(missing)}" if missing else "",
        f"address_source={address_source}" if address_source else "",
        "effect_proof_status=instruction_observed",
        f"target_match_proof_status={target_match_proof_status}",
        f"attribution_status={attribution_status}",
    ]
    diagnostic["evidence_atoms"] = [
        dynamic_unmodeled_write_evidence_atom(
            source=source,
            proof_status=proof_status,
            seq=int(frame.seq),
            pc=int(frame.pc),
            pc_label=pc_label,
            mnemonic=instruction.mnemonic,
            operation=operation,
            address_source=address_source,
            missing_registers=missing,
            target_match_proof_status=target_match_proof_status,
            attribution_status=attribution_status,
        )
    ]
    return diagnostic


def dynamic_unmodeled_write_evidence_atom(
    *,
    source: str,
    proof_status: str,
    seq: int,
    pc: int,
    pc_label: str,
    mnemonic: str,
    operation: str,
    address_source: str,
    missing_registers: list[str],
    target_match_proof_status: str,
    attribution_status: str,
) -> dict[str, Any]:
    return evidence_atom(
        claim_type="dynamic_taint.unmodeled_write",
        origin="dynamic_taint",
        observation_type="instruction_trace_unmodeled_write",
        proof_status=proof_status,
        source_report=source,
        source_kind="instruction_trace_unmodeled_write",
        scope={
            "seq": seq,
            "pc": pc,
            "pc_label": pc_label,
        },
        subjects={
            "symbols": [pc_label],
            "addresses": [],
        },
        precision={
            "address_source": address_source,
            "missing_registers": missing_registers,
            "target_match_proof_status": target_match_proof_status,
        },
        validation={
            "attribution_status": attribution_status,
            "evidence_status": "unmodeled_missing_register",
        },
        detail={
            "mnemonic": mnemonic,
            "operation": operation,
        },
    )


def stack_push_writes(
    frame: InstructionFrame,
    *,
    operation: str,
    source: dict[str, Any],
    value_source: str,
    low_source: dict[str, Any] | None = None,
    high_source: dict[str, Any] | None = None,
    model_source: str = "",
) -> list[dict[str, Any]]:
    stack_pointer = pair_value_if_known(frame, "sp")
    if stack_pointer is None:
        return []
    sp = (stack_pointer - 2) & 0xFFFF
    explicit_low_source = low_source is not None
    explicit_high_source = high_source is not None
    low_source = low_source or source
    high_source = high_source or source
    value = operand_int_value(source)
    low_value = operand_int_value(low_source) if explicit_low_source else value
    high_value = operand_int_value(high_source) if explicit_high_source else (value >> 8 if value is not None else None)
    return [
        memory_write(
            sp,
            f"{operation} low",
            low_source,
            value=low_value if low_value is not None else value,
            value_source=value_source,
            model_source=model_source,
        ),
        memory_write(
            sp + 1,
            f"{operation} high",
            high_source,
            value=high_value,
            value_source=value_source,
            model_source=model_source,
        ),
    ]


def register_pair_stack_components(pair: str) -> tuple[str, str]:
    return {
        "af": ("f", "a"),
        "bc": ("c", "b"),
        "de": ("e", "d"),
        "hl": ("l", "h"),
    }[pair.lower()]


def memory_write(
    address: int,
    kind: str,
    *source_operands: dict[str, Any],
    value: int | None = None,
    value_source: str = "",
    model_source: str = "",
) -> dict[str, Any]:
    out = {
        "address": address & 0xFFFF,
        "kind": kind,
        "source_operands": [operand for operand in source_operands if operand],
    }
    if model_source:
        out["model_source"] = model_source
    if value is not None:
        out["value"] = int(value) & 0xFF
        out["value_hex"] = f"{int(value) & 0xFF:02X}"
        if value_source:
            out["value_source"] = value_source
    return out


def register_operand(register: str, frame: InstructionFrame) -> dict[str, Any]:
    register = register.lower()
    width = 4 if register in {"af", "bc", "de", "hl", "sp"} else 2
    value = pair_value_if_known(frame, register) if register in {"af", "bc", "de", "hl", "sp"} else reg_value_if_known(frame, register)
    out = {
        "kind": "register",
        "name": register,
    }
    if value is not None:
        out["value"] = f"{value:0{width}X}"
        out["value_source"] = "pre_register"
    else:
        out["value_source"] = "missing_pre_register"
    return out


def memory_operand(address: int, *, value: int | None = None, value_source: str = "") -> dict[str, Any]:
    out = {
        "kind": "memory",
        "address": f"{address & 0xFFFF:04X}",
    }
    if value is not None:
        out["value"] = f"{value & 0xFF:02X}"
        if value_source:
            out["value_source"] = value_source
    return out


def immediate_operand(value: int) -> dict[str, Any]:
    return {
        "kind": "immediate",
        "value": f"{value & 0xFF:02X}",
        "value_source": "instruction_immediate",
    }


def immediate_word_operand(value: int, *, value_source: str = "instruction_immediate") -> dict[str, Any]:
    return {
        "kind": "immediate",
        "value": f"{value & 0xFFFF:04X}",
        "value_source": value_source,
    }


def enrich_source_operand(
    operand: dict[str, Any],
    *,
    register_sources: dict[str, str],
    source_memory: dict[int, str],
    source_address_specs: list[dict[str, Any]] | None = None,
    symbol_table: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    out = dict(operand)
    if out.get("kind") == "register":
        register = str(out.get("name", "")).lower()
        if register in register_sources:
            out["origin"] = register_sources[register]
            out["contributor"] = True
    elif out.get("kind") == "memory":
        try:
            address = parse_address(str(out.get("address", "")))
        except ValueError:
            address = -1
        if address >= 0:
            symbol = symbol_for_address(address, symbol_table)
            if symbol:
                out["symbol"] = symbol
            origin = source_origin_for_operand(
                address=address,
                operand=out,
                source_memory=source_memory,
                source_address_specs=source_address_specs or [],
            )
            if origin:
                out["origin"] = origin
                out["contributor"] = True
    return out


def source_origin_for_operand(
    *,
    address: int,
    operand: dict[str, Any],
    source_memory: dict[int, str],
    source_address_specs: list[dict[str, Any]],
) -> str:
    records = [
        record
        for record in source_address_specs
        if positive_int(record.get("address")) == (address & 0xFFFF)
    ]
    if not records:
        return source_memory.get(address, "")
    operand_key = str(operand.get("address_key") or "")
    if not operand_key:
        try:
            operand_key = address_key(str(operand.get("bank_address") or operand.get("address") or ""))
        except ValueError:
            operand_key = ""
    if operand_key:
        for record in records:
            if operand_key == str(record.get("key", "")):
                return str(record.get("origin", "")) or source_memory.get(address, "")
    for record in records:
        if address_spec_requires_exact_key(record):
            continue
        return str(record.get("origin", "")) or source_memory.get(address, "")
    return ""


def effect_sink_match(sink: Sink, *, effect_item: dict[str, Any], address: int) -> dict[str, Any] | None:
    if not sink.contains(address):
        return None
    effect_key = str(effect_item.get("address_key", ""))
    sink_key = str(getattr(sink, "address_key", ""))
    if bool(getattr(sink, "bank_exact_required", False)):
        if effect_key and sink_key and effect_key == sink_key:
            return address_match_record(
                address_key=effect_key,
                match_precision="exact_address_key",
                bank_match="exact",
                bank_source=str(effect_item.get("bank_source", "")),
                effect_proof_status=str(effect_item.get("proof_status", "")),
                effect_proof_downgrade_reason=str(effect_item.get("proof_downgrade_reason", "")),
                **effect_hardware_match_fields(effect_item),
            )
        return None
    if address_key_requires_exact_match(effect_key):
        return address_match_record(
            address_key=effect_key,
            match_precision="bus_address_unverified_bank",
            bank_match="bus_address_unverified_bank",
            bank_source=str(effect_item.get("bank_source", "")),
            proof_downgrade_reason="unbanked sink matched a bank-qualified runtime key by bus address",
            effect_proof_status=str(effect_item.get("proof_status", "")),
            effect_proof_downgrade_reason=str(effect_item.get("proof_downgrade_reason", "")),
            **effect_hardware_match_fields(effect_item),
        )
    return address_match_record(
        address_key=effect_key,
        match_precision="bus_address",
        bank_match="not_required",
        bank_source=str(effect_item.get("bank_source", "")),
        effect_proof_status=str(effect_item.get("proof_status", "")),
        effect_proof_downgrade_reason=str(effect_item.get("proof_downgrade_reason", "")),
        **effect_hardware_match_fields(effect_item),
    )


def sink_matches_effect(sink: Sink, *, effect_item: dict[str, Any], address: int) -> bool:
    return bool(effect_sink_match(sink, effect_item=effect_item, address=address))


def taint_finding_matches_instruction_sink(
    finding: Any,
    *,
    frame_by_seq: dict[int, InstructionFrame],
    sink_by_name: dict[str, Sink],
) -> bool:
    return bool(instruction_taint_finding_match(finding, frame_by_seq=frame_by_seq, sink_by_name=sink_by_name))


def instruction_taint_finding_match(
    finding: Any,
    *,
    frame_by_seq: dict[int, InstructionFrame],
    sink_by_name: dict[str, Sink],
) -> dict[str, Any] | None:
    sink = sink_by_name.get(str(finding.sink))
    frame = frame_by_seq.get(int(finding.seq))
    if sink is None or frame is None:
        return None
    return instruction_sink_match(sink, frame=frame, address=int(finding.address))


def sink_matches_instruction_address(sink: Sink, *, frame: InstructionFrame, address: int) -> bool:
    return bool(instruction_sink_match(sink, frame=frame, address=address))


def instruction_sink_match(sink: Sink, *, frame: InstructionFrame, address: int) -> dict[str, Any] | None:
    if not sink.contains(address):
        return None
    observed_key = instruction_frame_address_key(frame, address)
    bank_source = instruction_frame_memory_bank_source(frame, address)
    if not bool(getattr(sink, "bank_exact_required", False)):
        if address_key_requires_exact_match(observed_key):
            return address_match_record(
                address_key=observed_key,
                match_precision="bus_address_unverified_bank",
                bank_match="bus_address_unverified_bank",
                bank_source=bank_source,
                proof_downgrade_reason="unbanked sink matched a bank-qualified runtime key by bus address",
            )
        return address_match_record(
            address_key=observed_key,
            match_precision="bus_address",
            bank_match="not_required",
            bank_source=bank_source,
        )
    sink_key = str(getattr(sink, "address_key", ""))
    if sink_key and observed_key == sink_key:
        return address_match_record(
            address_key=observed_key,
            match_precision="exact_address_key",
            bank_match="exact",
            bank_source=bank_source,
        )
    return None


def address_match_record(
    *,
    address_key: str,
    match_precision: str,
    bank_match: str,
    bank_source: str = "",
    proof_downgrade_reason: str = "",
    effect_proof_status: str = "",
    effect_proof_downgrade_reason: str = "",
    hardware_model: str = "",
    hardware_event_required: bool = False,
    hardware_runtime_event: bool = False,
    hardware_event_identity: str = "",
    hardware_event_labels: list[str] | None = None,
    hardware_generic_event_label_present: bool = False,
    hardware_proof_gate: str = "",
) -> dict[str, Any]:
    return {
        "address_key": address_key,
        "match_precision": match_precision,
        "bank_match": bank_match,
        "bank_source": bank_source,
        "proof_downgrade_reason": proof_downgrade_reason,
        "effect_proof_status": effect_proof_status,
        "effect_proof_downgrade_reason": effect_proof_downgrade_reason,
        "hardware_model": hardware_model,
        "hardware_event_required": hardware_event_required,
        "hardware_runtime_event": hardware_runtime_event,
        "hardware_event_identity": hardware_event_identity,
        "hardware_event_labels": hardware_event_labels or [],
        "hardware_generic_event_label_present": hardware_generic_event_label_present,
        "hardware_proof_gate": hardware_proof_gate,
    }


def effect_hardware_match_fields(effect_item: dict[str, Any]) -> dict[str, Any]:
    required = effect_requires_hardware_runtime_event(effect_item)
    boundary = hardware_runtime_event_boundary(effect_item)
    runtime_event = bool(boundary["runtime_event_present"])
    return {
        "hardware_model": str(effect_item.get("hardware_model", "")),
        "hardware_event_required": required,
        "hardware_runtime_event": runtime_event,
        "hardware_event_identity": str(boundary.get("hardware_event_identity", "")),
        "hardware_event_labels": list(boundary.get("hardware_event_labels", [])),
        "hardware_generic_event_label_present": bool(boundary.get("hardware_generic_event_label_present")),
        "hardware_proof_gate": (
            str(effect_item.get("hardware_proof_gate", ""))
            or ("explicit_runtime_event_present" if required and runtime_event else "")
            or ("explicit_runtime_event_missing" if required else "")
        ),
    }


def effect_requires_hardware_runtime_event(effect_item: dict[str, Any]) -> bool:
    if bool(effect_item.get("hardware_event_required")):
        return True
    if str(effect_item.get("hardware_model", "")) in HARDWARE_EVENT_REQUIRED_MODELS:
        return True
    if str(effect_item.get("kind", "")) in HARDWARE_EVENT_REQUIRED_KINDS:
        return True
    return False


def match_proof_status(match: dict[str, Any]) -> str:
    if match.get("match_precision") == "bus_address_unverified_bank":
        return "planned_only"
    if match.get("hardware_event_required") and not match.get("hardware_runtime_event"):
        return "planned_only"
    if str(match.get("hardware_proof_gate", "")) == "explicit_runtime_event_missing":
        return "planned_only"
    if str(match.get("effect_proof_status", "")) == "planned_only":
        return "planned_only"
    return "instruction_observed"


def match_evidence(match: dict[str, Any]) -> list[str]:
    return unique_list(
        [
            f"address_key={match.get('address_key', '')}" if match.get("address_key") else "",
            f"match_precision={match.get('match_precision', '')}" if match.get("match_precision") else "",
            f"bank_match={match.get('bank_match', '')}" if match.get("bank_match") else "",
            f"bank_source={match.get('bank_source', '')}" if match.get("bank_source") else "",
            f"proof_downgrade_reason={match.get('proof_downgrade_reason', '')}"
            if match.get("proof_downgrade_reason")
            else "",
            f"effect_proof_status={match.get('effect_proof_status', '')}"
            if match.get("effect_proof_status")
            else "",
            f"effect_proof_downgrade_reason={match.get('effect_proof_downgrade_reason', '')}"
            if match.get("effect_proof_downgrade_reason")
            else "",
            f"hardware_model={match.get('hardware_model', '')}" if match.get("hardware_model") else "",
            f"hardware_event_required={match.get('hardware_event_required')}" if match.get("hardware_event_required") else "",
            (
                f"hardware_runtime_event={match.get('hardware_runtime_event')}"
                if match.get("hardware_event_required")
                else ""
            ),
            f"hardware_event_identity={match.get('hardware_event_identity', '')}" if match.get("hardware_event_identity") else "",
            (
                f"hardware_generic_event_label_present={match.get('hardware_generic_event_label_present')}"
                if match.get("hardware_generic_event_label_present")
                else ""
            ),
            f"hardware_proof_gate={match.get('hardware_proof_gate', '')}" if match.get("hardware_proof_gate") else "",
        ]
    )


def instruction_frame_address_key(frame: InstructionFrame, address: int) -> str:
    bank = instruction_frame_memory_bank(frame, address)
    if bank is None:
        return address_key(f"{address & 0xFFFF:04X}")
    return address_key(f"{bank:02X}:{address & 0xFFFF:04X}")


def instruction_frame_memory_bank_source(frame: InstructionFrame, address: int) -> str:
    address &= 0xFFFF
    if 0xD000 <= address <= 0xDFFF and instruction_frame_bank_state(frame, "wram") is not None:
        return instruction_frame_bank_state_source(frame, "wram") or "bank_state.wram"
    if 0x8000 <= address <= 0x9FFF and instruction_frame_bank_state(frame, "vram") is not None:
        return instruction_frame_bank_state_source(frame, "vram") or "bank_state.vram"
    if 0x4000 <= address <= 0x7FFF and instruction_frame_bank_state(frame, "rom") is not None:
        return instruction_frame_bank_state_source(frame, "rom") or "bank_state.rom"
    if 0xA000 <= address <= 0xBFFF and instruction_frame_bank_state(frame, "sram") is not None:
        return instruction_frame_bank_state_source(frame, "sram") or "bank_state.sram"
    return ""


def instruction_frame_memory_bank(frame: InstructionFrame, address: int) -> int | None:
    address &= 0xFFFF
    if 0xD000 <= address <= 0xDFFF:
        return instruction_frame_bank_state(frame, "wram")
    if 0x8000 <= address <= 0x9FFF:
        return instruction_frame_bank_state(frame, "vram")
    if 0x4000 <= address <= 0x7FFF:
        return instruction_frame_bank_state(frame, "rom")
    if 0xA000 <= address <= 0xBFFF:
        return instruction_frame_bank_state(frame, "sram")
    return None


def instruction_frame_bank_state(frame: InstructionFrame, key: str) -> int | None:
    for item_key, value in frame.bank_state:
        if item_key == key:
            return int(value) & 0xFF
    return None


def instruction_frame_bank_state_source(frame: InstructionFrame, key: str) -> str:
    for item_key, source in frame.bank_state_sources:
        if item_key == key:
            return source
    return ""


def contributors_for_operands(source_operands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    contributors = []
    for operand in source_operands:
        if not operand.get("contributor"):
            continue
        if operand.get("kind") == "register":
            contributors.append(
                {
                    "symbol": str(operand.get("origin", operand.get("name", ""))),
                    "relation": "register_feeds_sink_write",
                    "register": str(operand.get("name", "")),
                    "value": str(operand.get("value", "")),
                    "confidence": 0.9,
                }
            )
        elif operand.get("kind") == "memory":
            contributors.append(
                {
                    "symbol": str(operand.get("origin", operand.get("symbol", ""))),
                    "relation": "memory_feeds_sink_write",
                    "address": str(operand.get("address", "")),
                    "confidence": 0.88,
                }
            )
    return contributors


def write_attribution_score(*, contributors: list[dict[str, Any]], taint: list[str]) -> int:
    if taint:
        return 90
    if contributors:
        return 84
    return 72


def write_attribution_evidence(
    *,
    seq: int,
    pc: int,
    mnemonic: str,
    target: str,
    address: int,
    source_operands: list[dict[str, Any]],
    taint: list[str],
    register_provenance: list[dict[str, Any]] | None = None,
    value_hex: str = "",
    value_source: str = "",
    match: dict[str, Any] | None = None,
) -> list[str]:
    sources = ", ".join(render_source_operand(item) for item in source_operands)
    evidence = [
        f"seq={seq} pc=${pc:04X}",
        mnemonic,
        f"write {target}@${address:04X}",
    ]
    if value_hex:
        evidence.append(f"value=0x{value_hex}")
    if value_source:
        evidence.append(f"value_source={value_source}")
    if sources:
        evidence.append(f"sources={sources}")
    evidence.extend(match_evidence(match or {}))
    for item in register_provenance or []:
        evidence.append(
            "register_provenance="
            + ",".join(
                part
                for part in [
                    f"{item.get('register', '')}@{item.get('pc', '')}",
                    str(item.get("operation", "")),
                    f"value=0x{item.get('value_hex', '')}" if item.get("value_hex") else "",
                    "taint=" + "/".join(string_items(item.get("taint"))) if item.get("taint") else "",
                ]
                if part
            )
        )
    if taint:
        evidence.append("taint=" + ", ".join(taint))
    return evidence


def render_source_operand(operand: dict[str, Any]) -> str:
    kind = str(operand.get("kind", "operand"))
    if kind == "register":
        text = f"register:{operand.get('name')}=${operand.get('value')}"
    elif kind == "memory":
        text = f"memory:${operand.get('address')}"
    elif kind == "immediate":
        text = f"immediate:${operand.get('value')}"
    else:
        text = kind
    address_key_value = str(operand.get("address_key", ""))
    if address_key_value:
        text += f" key={address_key_value}"
    value_source = str(operand.get("value_source", ""))
    if value_source:
        text += f" value_source={value_source}"
    bank = str(operand.get("bank", ""))
    if bank:
        text += f" bank={bank}"
    bank_source = str(operand.get("bank_source", ""))
    if bank_source:
        text += f" bank_source={bank_source}"
    if operand.get("sram_enabled") is not None:
        text += f" sram_enabled={operand.get('sram_enabled')}"
    sram_enabled_source = str(operand.get("sram_enabled_source", ""))
    if sram_enabled_source:
        text += f" sram_enabled_source={sram_enabled_source}"
    via_register = str(operand.get("via_register", ""))
    if via_register:
        text += f" via_register={via_register}"
    via_seq = operand.get("via_register_write_seq")
    if via_seq not in {None, ""}:
        text += f" via_register_write_seq={via_seq}"
    origin = str(operand.get("origin", ""))
    if origin:
        text += f" origin={origin}"
    symbol = str(operand.get("symbol", ""))
    if symbol and symbol != origin:
        text += f" symbol={symbol}"
    return text


def related_symbols_for_write(
    *,
    target: str,
    pc_label: str,
    address: int,
    source_operands: list[dict[str, Any]],
    symbol_table: dict[str, dict[str, Any]],
) -> list[str]:
    symbols = [target if not target_address(target) else "", base_label(pc_label), symbol_for_address(address, symbol_table)]
    for operand in source_operands:
        symbols.extend(
            [
                str(operand.get("origin", "")),
                str(operand.get("symbol", "")),
                str(operand.get("name", "")) if operand.get("kind") == "register" else "",
            ]
        )
    return unique_list(symbols)


def commands_for_write_attribution(*, target: str, routine: str, source: str, sink_size: int) -> list[str]:
    commands = []
    address = target_address(target)
    watch_size_arg = f" --watch-size {sink_size}" if address and sink_size != 1 else ""
    if source:
        source_arg = quote_arg(source)
        command_address = command_address_arg(address)
        expect = f"event=memory_write,address={command_address}" if address else "event=memory_write"
        commands.append(f"python -m tools.debugger minimize --trace {source_arg} --expect {expect}")
        if address:
            commands.append(f"python -m tools.debugger trace-index --trace {source_arg} --address {command_address}")
        else:
            commands.append(f"python -m tools.debugger trace-index --trace {source_arg} --watch-symbol {target}")
    if address:
        commands.append(f"python -m tools.debugger localize --address {command_address_arg(address)}{watch_size_arg}")
        commands.append(f"python -m tools.debugger replay --watch-address {command_address_arg(target)}{watch_size_arg}")
    elif target:
        commands.append(f"python -m tools.debugger explain --symbol {target}")
        commands.append(f"python -m tools.debugger replay --symbol {target}")
    if routine:
        if address:
            commands.append(f"python -m tools.debugger slice --symbol {routine}")
        else:
            commands.append(f"python -m tools.debugger slice --symbol {routine} --symbol {target}")
    return unique_list(commands)


def commands_for_effect_write_attribution(*, target: str, source: str, address: int, sink_size: int) -> list[str]:
    commands = []
    address_text = command_address_arg(f"{address & 0xFFFF:04X}")
    sink_size_arg = f" --sink-size {sink_size}" if sink_size != 1 else ""
    watch_size_arg = f" --watch-size {sink_size}" if sink_size != 1 else ""
    if source:
        commands.append(f"python -m tools.debugger reverse-query --report {quote_arg(source)} --address {address_text}")
        commands.append(f"python -m tools.debugger dynamic-taint --report {quote_arg(source)} --sink-address {address_text}{sink_size_arg}")
        if target and not target_address(target):
            commands.append(f"python -m tools.debugger reverse-query --report {quote_arg(source)} --symbol {target}")
    commands.append(f"python -m tools.debugger localize --address {address_text}{watch_size_arg}")
    if target and not target_address(target):
        commands.append(f"python -m tools.debugger explain --symbol {target}")
    return unique_list(commands)


def related_addresses_for_write(*, target: str, address: int, sink: Sink) -> list[str]:
    return unique_list(
        [
            target_address(target),
            f"{int(sink.address):04X}",
            f"{int(address):04X}",
        ]
    )


def symbol_for_address(address: int, symbol_table: dict[str, dict[str, Any]]) -> str:
    for label, entry in symbol_table.items():
        if int(entry.get("address", -1)) == (address & 0xFFFF):
            return str(label)
    return ""


def operand_int_value(operand: dict[str, Any]) -> int | None:
    value = operand.get("value")
    if value is None:
        return None
    try:
        return int(str(value), 16)
    except ValueError:
        return None


def frame_memory_sample(frame: InstructionFrame, address: int) -> tuple[int | None, str]:
    target = address & 0xFFFF
    for raw_address, value in frame.memory:
        if (int(raw_address) & 0xFFFF) == target:
            return int(value) & 0xFF, "observed_memory_snapshot"
    return None, ""


def modeled_value_source(source: str) -> str:
    return f"modeled_from_{source}" if source else "modeled_from_unknown_memory"


def cb_hl_operation(subopcode: int) -> str:
    return cb_semantics(subopcode).operation("[hl]")


def cb_register_operation(subopcode: int, target: str) -> str:
    return cb_semantics(subopcode).operation(target)


def cb_hl_result(subopcode: int, old_value: int | None, *, flags: int | None) -> int | None:
    return cb_semantics(subopcode).result(old_value, flags=flags)


def cb_flags(subopcode: int, old_value: int | None, *, flags: int | None) -> int | None:
    return cb_semantics(subopcode).flags(old_value, flags=flags)


def reg_value(frame: InstructionFrame, register: str) -> int:
    return int(getattr(frame, register.upper())) & 0xFF


def reg_value_if_known(frame: InstructionFrame, register: str) -> int | None:
    register = register.upper()
    if not frame_register_known(frame, register):
        return None
    return reg_value(frame, register)


def pair_value(frame: InstructionFrame, pair: str) -> int:
    pair = pair.lower()
    if pair == "af":
        return ((reg_value(frame, "a") << 8) | reg_value(frame, "f")) & 0xFFFF
    if pair == "hl":
        return int(frame.HL) & 0xFFFF
    if pair == "bc":
        return ((reg_value(frame, "b") << 8) | reg_value(frame, "c")) & 0xFFFF
    if pair == "de":
        return ((reg_value(frame, "d") << 8) | reg_value(frame, "e")) & 0xFFFF
    if pair == "sp":
        return int(frame.SP) & 0xFFFF
    raise KeyError(pair)


def pair_value_if_known(frame: InstructionFrame, pair: str) -> int | None:
    pair = pair.lower()
    if pair == "af":
        return pair_value(frame, pair) if frame_register_known(frame, "A") and frame_register_known(frame, "F") else None
    if pair == "hl":
        return pair_value(frame, pair) if frame_register_known(frame, "HL") or (frame_register_known(frame, "H") and frame_register_known(frame, "L")) else None
    if pair == "bc":
        return pair_value(frame, pair) if frame_register_known(frame, "B") and frame_register_known(frame, "C") else None
    if pair == "de":
        return pair_value(frame, pair) if frame_register_known(frame, "D") and frame_register_known(frame, "E") else None
    if pair == "sp":
        return pair_value(frame, pair) if frame_register_known(frame, "SP") else None
    raise KeyError(pair)


def missing_registers_for_pair(frame: InstructionFrame, pair: str) -> list[str]:
    pair = pair.lower()
    if pair == "hl":
        if frame_register_known(frame, "HL") or (frame_register_known(frame, "H") and frame_register_known(frame, "L")):
            return []
        return ["HL"]
    pairs = {
        "af": ("A", "F"),
        "bc": ("B", "C"),
        "de": ("D", "E"),
        "sp": ("SP",),
    }
    return [register for register in pairs.get(pair, ()) if not frame_register_known(frame, register)]


def frame_register_known(frame: InstructionFrame, register: str) -> bool:
    known = set(frame.known_registers)
    register = register.upper()
    if register in known:
        return True
    if register in {"H", "L"} and "HL" in known:
        return True
    return False


def condition_true(condition: str, flags: int) -> bool:
    zero = bool(flags & 0x80)
    carry = bool(flags & 0x10)
    return {
        "nz": not zero,
        "z": zero,
        "nc": not carry,
        "c": carry,
    }[condition]


def frame_condition_true(frame: InstructionFrame, condition: str) -> bool:
    flags = frame_flags(frame)
    return flags is not None and condition_true(condition, flags)


def frame_flags(frame: InstructionFrame) -> int | None:
    if not frame_register_known(frame, "F"):
        return None
    return int(frame.F) & 0xFF


def u16_from_operand(instruction: Instruction) -> int:
    if len(instruction.operand) < 2:
        return 0
    return int(instruction.operand[0]) | (int(instruction.operand[1]) << 8)


def build_paths(
    *,
    findings: list[dict[str, Any]],
    sinks: list[Sink],
    register_sources: dict[str, str],
    source_memory: dict[int, str],
    max_paths: int,
) -> list[dict[str, Any]]:
    sink_by_name = {sink.name: sink for sink in sinks}
    paths = []
    for index, finding in enumerate(findings[:max_paths], 1):
        taint = [str(item) for item in finding.get("taint", [])]
        contributors = contributors_for_taint(
            taint,
            register_sources=register_sources,
            source_memory=source_memory,
        )
        sink = sink_by_name.get(str(finding.get("sink", "")))
        target = str(finding.get("sink", "sink"))
        pc_label = base_label(str(finding.get("pc_label", ""))) or str(finding.get("pc_label", ""))
        source = str(finding.get("source", ""))
        source_kind = str(finding.get("source_kind", "instruction_trace"))
        evidence_source_proof = str(finding.get("proof_status") or "planned_only")
        address = int(finding.get("address", 0))
        commands = (
            commands_for_effect_write_attribution(
                target=target,
                source=source,
                address=address,
                sink_size=sink.size if sink else 1,
            )
            if finding.get("source_kind") == "effect_trace_report"
            else commands_for_path(
                target=target,
                pc_label=pc_label,
                source=source,
                sink_size=sink.size if sink else 1,
            )
        )
        evidence = dynamic_path_evidence(
            finding=finding,
            taint=taint,
            source_kind=source_kind,
            evidence_source_proof=evidence_source_proof,
        )
        proof_status = dynamic_path_proof_status(
            taint=taint,
            evidence_source_proof=evidence_source_proof,
        )
        paths.append(
            {
                "id": f"dynamic_taint_path_{index:04d}",
                "title": f"{', '.join(taint) or 'source'} -> {target} at {pc_label}",
                "target": target,
                "access": "dynamic_write",
                "source_kind": source_kind,
                "score": 92 if contributors else 84,
                "confidence": 0.9 if contributors else 0.78,
                "source": source,
                "seq": finding.get("seq"),
                "pc": finding.get("pc"),
                "pc_label": finding.get("pc_label", ""),
                "mnemonic": finding.get("mnemonic", ""),
                "sink_address": f"{address:04X}",
                "sink_size": sink.size if sink else 1,
                "address_key": str(finding.get("address_key", "")),
                "match_precision": str(finding.get("match_precision", "")),
                "bank_match": str(finding.get("bank_match", "")),
                "bank_source": str(finding.get("bank_source", "")),
                "proof_downgrade_reason": str(finding.get("proof_downgrade_reason", "")),
                "taint": taint,
                "contributors": contributors,
                "proof_status": proof_status,
                "evidence_source_proof_status": evidence_source_proof,
                "steps": [
                    {
                        "role": source_kind,
                        "code": str(finding.get("mnemonic", "")),
                        "pc_label": str(finding.get("pc_label", "")),
                        "seq": finding.get("seq"),
                        "proof_status": evidence_source_proof,
                    }
                ],
                "evidence": evidence,
                "evidence_atoms": merge_evidence_atoms(
                    dynamic_path_evidence_atom(
                        target=target,
                        source=source,
                        source_kind=source_kind,
                        proof_status=proof_status,
                        evidence_source_proof=evidence_source_proof,
                        finding=finding,
                        address=address,
                        taint=taint,
                        contributors=contributors,
                    ),
                    finding.get("evidence_atoms"),
                ),
                "related_symbols": unique_list(
                    [
                        target if not target_address(target) else "",
                        pc_label,
                        *[item.get("symbol", "") for item in contributors],
                    ]
                ),
                "related_addresses": unique_list([target_address(target), f"{address:04X}"]),
                "related_files": [],
                "commands": commands,
            }
        )
    return paths


def dynamic_path_evidence_atom(
    *,
    target: str,
    source: str,
    source_kind: str,
    proof_status: str,
    evidence_source_proof: str,
    finding: dict[str, Any],
    address: int,
    taint: list[str],
    contributors: list[dict[str, Any]],
) -> dict[str, Any]:
    return evidence_atom(
        claim_type="dynamic_taint.path",
        origin="dynamic_taint",
        observation_type=source_kind,
        proof_status=proof_status,
        source_report=source,
        source_kind=source_kind,
        scope={
            "seq": finding.get("seq"),
            "pc": finding.get("pc"),
            "pc_label": finding.get("pc_label", ""),
        },
        subjects={
            "symbols": [target, str(finding.get("pc_label", "")), *[item.get("symbol", "") for item in contributors]],
            "addresses": [target_address(target), f"{address & 0xFFFF:04X}"],
        },
        precision={
            "evidence_source_proof_status": evidence_source_proof,
            "sink_size": finding.get("sink_size", ""),
            "address_key": finding.get("address_key", ""),
            "match_precision": finding.get("match_precision", ""),
            "bank_match": finding.get("bank_match", ""),
            "bank_source": finding.get("bank_source", ""),
            "proof_downgrade_reason": finding.get("proof_downgrade_reason", ""),
        },
        validation={
            "taint_count": len(taint),
            "contributor_count": len(contributors),
        },
        detail={
            "mnemonic": finding.get("mnemonic", ""),
            "taint": taint,
        },
    )


def dynamic_path_evidence(
    *,
    finding: dict[str, Any],
    taint: list[str],
    source_kind: str,
    evidence_source_proof: str,
) -> list[str]:
    return unique_list(
        [
            f"seq={finding.get('seq')} pc=${int(finding.get('pc', 0)):04X}",
            str(finding.get("mnemonic", "")),
            f"source_kind={source_kind}",
            f"evidence_source_proof_status={evidence_source_proof}",
            *string_items(finding.get("evidence")),
            "taint=" + ", ".join(taint),
        ]
    )


def dynamic_path_proof_status(*, taint: list[str], evidence_source_proof: str) -> str:
    if not taint:
        return evidence_source_proof or "instruction_observed"
    if evidence_source_proof in {"instruction_observed", "runtime_observed", "taint_proven"}:
        return "taint_proven"
    return evidence_source_proof or "planned_only"


def contributors_for_taint(
    taint: list[str],
    *,
    register_sources: dict[str, str],
    source_memory: dict[int, str],
) -> list[dict[str, Any]]:
    contributors = []
    for register, origin in register_sources.items():
        if origin in taint:
            contributors.append(
                {
                    "symbol": origin,
                    "relation": "register_taints_sink",
                    "register": register,
                    "confidence": 0.92,
                }
            )
    for address, origin in source_memory.items():
        if origin in taint:
            contributors.append(
                {
                    "symbol": origin,
                    "relation": "memory_taints_sink",
                    "address": f"{address:04X}",
                    "confidence": 0.9,
                }
            )
    return contributors


def public_finding(finding: Any, *, source: str, match: dict[str, Any] | None = None) -> dict[str, Any]:
    match = match or {}
    proof_status = match_proof_status(match) if match else "planned_only"
    data = {
        "source": source,
        "source_kind": "instruction_trace_taint_engine",
        "seq": int(finding.seq),
        "pc": int(finding.pc),
        "pc_label": str(finding.pc_label),
        "mnemonic": str(finding.mnemonic),
        "sink": str(finding.sink),
        "address": int(finding.address),
        "address_key": str(match.get("address_key", "")),
        "match_precision": str(match.get("match_precision", "")),
        "bank_match": str(match.get("bank_match", "")),
        "bank_source": str(match.get("bank_source", "")),
        "proof_downgrade_reason": str(match.get("proof_downgrade_reason", "")),
        "taint": list(finding.taint),
        "proof_status": proof_status,
        "evidence": match_evidence(match),
    }
    return data


def targets_for_sinks(
    *,
    sinks: list[Sink],
    paths: list[dict[str, Any]],
    write_attributions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    paths_by_target: dict[str, list[dict[str, Any]]] = {}
    for path in paths:
        paths_by_target.setdefault(str(path.get("target", "")), []).append(path)
    writes_by_target: dict[str, list[dict[str, Any]]] = {}
    for attribution in write_attributions:
        writes_by_target.setdefault(str(attribution.get("target", "")), []).append(attribution)
    targets = []
    for sink in sinks:
        target_paths = paths_by_target.get(sink.name, [])
        target_writes = writes_by_target.get(sink.name, [])
        contributors = [
            contributor
            for path in target_paths
            for contributor in path.get("contributors", [])
            if isinstance(contributor, dict)
        ] + [
            contributor
            for attribution in target_writes
            for contributor in attribution.get("contributors", [])
            if isinstance(contributor, dict)
        ]
        targets.append(
            {
                "symbol": sink.name,
                "found": True,
                "sink_count": max(len(target_paths), len(target_writes)),
                "write_attribution_count": len(target_writes),
                "contributor_count": len(contributors),
                "sinks": [
                    {
                        "routine": base_label(str(path.get("pc_label", ""))),
                        "source_file": "",
                        "access": "dynamic_write",
                        "line": None,
                    }
                    for path in target_paths[:8]
                ] + [
                    {
                        "routine": base_label(str(attribution.get("pc_label", ""))),
                        "source_file": "",
                        "access": "dynamic_write",
                        "line": None,
                    }
                    for attribution in target_writes[:8]
                ],
                "reverse_writes": target_writes[:8],
                "contributors": contributors[:16],
            }
        )
    return targets


def source_summary(*, register_sources: dict[str, str], source_memory: dict[int, str]) -> list[dict[str, Any]]:
    return [
        {"type": "register", "register": register, "origin": origin}
        for register, origin in sorted(register_sources.items())
    ] + [
        {"type": "memory", "address": f"{address:04X}", "origin": origin}
        for address, origin in sorted(source_memory.items())
    ]


def public_sink(sink: Sink) -> dict[str, Any]:
    data = {"name": sink.name, "address": f"{sink.address:04X}", "size": sink.size}
    address_key_value = str(getattr(sink, "address_key", ""))
    if address_key_value:
        data["address_key"] = address_key_value
        data["bank_exact_required"] = bool(getattr(sink, "bank_exact_required", False))
    return data


def build_commands(
    *,
    paths: list[dict[str, Any]],
    write_attributions: list[dict[str, Any]],
    traces: tuple[str, ...],
    effect_reports: tuple[str, ...],
    sink_symbols: tuple[str, ...],
    sink_addresses: tuple[str, ...],
    sink_size: int,
    trace_synthesis_plan: dict[str, Any],
) -> list[str]:
    commands = list(trace_synthesis_plan.get("commands", []))
    for report in effect_reports[:4]:
        for address in sink_addresses[:4]:
            commands.append(
                f"python -m tools.debugger reverse-query --report {quote_arg(report)} --address {command_address_arg(address)}"
            )
        for symbol in sink_symbols[:4]:
            commands.append(f"python -m tools.debugger reverse-query --report {quote_arg(report)} --symbol {symbol}")
    for trace in traces[:3]:
        trace_arg = quote_arg(trace)
        commands.append(f"python -m tools.debugger trace-index --trace {trace_arg}")
        commands.append(f"python -m tools.debugger expect --trace {trace_arg} --expect <expectation>")
        for address in sink_addresses[:4]:
            command_address = command_address_arg(address)
            commands.append(f"python -m tools.debugger trace-index --trace {trace_arg} --address {command_address}")
            commands.append(f"python -m tools.debugger minimize --trace {trace_arg} --expect event=memory_write,address={command_address}")
    for symbol in sink_symbols[:4]:
        commands.append(f"python -m tools.debugger watch --watch-symbol {symbol} --execute")
        commands.append(f"python -m tools.debugger taint --symbol {symbol}")
    watch_size_arg = f" --watch-size {sink_size}" if sink_size != 1 else ""
    for address in sink_addresses[:4]:
        command_address = command_address_arg(address)
        commands.append(f"python -m tools.debugger localize --address {command_address}{watch_size_arg}")
        commands.append(f"python -m tools.debugger setup --watch-address {command_address}{watch_size_arg}")
        commands.append(f"python -m tools.debugger replay --watch-address {command_address}{watch_size_arg} --execute-watch")
        commands.append(f"python -m tools.debugger watch --watch-address {command_address}{watch_size_arg} --execute")
    for path in paths[:4]:
        commands.extend(path.get("commands", [])[:3])
    for attribution in write_attributions[:4]:
        commands.extend(attribution.get("commands", [])[:3])
    return unique_list(commands)[:40]


def commands_for_path(*, target: str, pc_label: str, source: str, sink_size: int) -> list[str]:
    commands = []
    address = target_address(target)
    watch_size_arg = f" --watch-size {sink_size}" if address and sink_size != 1 else ""
    if source:
        source_arg = quote_arg(source)
        command_address = command_address_arg(address)
        expect = f"event=memory_write,address={command_address}" if address else "event=memory_write"
        commands.append(f"python -m tools.debugger minimize --trace {source_arg} --expect {expect}")
        if address:
            commands.append(f"python -m tools.debugger trace-index --trace {source_arg} --address {command_address}")
    if address:
        commands.append(f"python -m tools.debugger localize --address {command_address_arg(address)}{watch_size_arg}")
        commands.append(f"python -m tools.debugger replay --watch-address {command_address_arg(target)}{watch_size_arg}")
    elif target:
        commands.append(f"python -m tools.debugger explain --symbol {target}")
        commands.append(f"python -m tools.debugger replay --symbol {target}")
        commands.append(f"python -m tools.debugger taint --symbol {target}")
    if pc_label:
        routine = base_label(pc_label) or pc_label
        if target and not address:
            commands.append(f"python -m tools.debugger trace-instructions --symbol {routine} --watch-symbol {target} --execute --out-trace .local\\tmp\\debugger_instruction_trace_{target}.jsonl")
        commands.append(f"python -m tools.debugger slice --symbol {pc_label}")
    return unique_list(commands)


def target_address(target: str) -> str:
    text = str(target).strip()
    if not text:
        return ""
    return sink_address_candidate(text)


def split_assignment(raw: str) -> tuple[str, str]:
    text = str(raw).strip()
    if "=" not in text:
        return text, ""
    left, right = text.split("=", 1)
    return left.strip(), right.strip()


def quote_arg(value: Any) -> str:
    text = str(value)
    if not text:
        return '""'
    if any(char.isspace() for char in text):
        return '"' + text.replace('"', '\\"') + '"'
    return text


def safe_name(value: Any) -> str:
    text = str(value)
    out = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in text)
    return out.strip("_") or "report"


def parse_operand(value: Any) -> bytes | None:
    if value is None or value == "":
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, int):
        return bytes([value & 0xFF])
    if isinstance(value, list | tuple):
        try:
            return bytes(parse_int(item) & 0xFF for item in value)
        except ValueError:
            return None
    if isinstance(value, str):
        text = value.strip().replace("$", "").replace("0x", "").replace("0X", "")
        text = text.replace(",", " ").replace("[", "").replace("]", "")
        parts = [part for part in text.split() if part]
        if len(parts) > 1:
            try:
                return bytes(parse_int(part) & 0xFF for part in parts)
            except ValueError:
                return None
        if len(text) % 2:
            text = "0" + text
        try:
            return bytes(int(text[index : index + 2], 16) for index in range(0, len(text), 2))
        except ValueError:
            return None
    return None


def parse_address(value: str) -> int:
    return parse_address_spec(value).address


def parse_int(value: Any, *, default: int | None = None) -> int:
    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError("missing integer value")
    return parse_address_int(value)


def default_symbol_size(symbol: str, fallback: int) -> int:
    return 2 if symbol in {"wCurDamage"} else fallback


def positive_int(value: Any) -> int:
    try:
        parsed = parse_int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list | tuple):
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


def unique_ints(values: Any) -> list[int]:
    out: list[int] = []
    seen: set[int] = set()
    for value in values:
        size = positive_int(value)
        if not size or size in seen:
            continue
        seen.add(size)
        out.append(size)
    return out


def unique_sink_addresses(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        address_text = sink_address_candidate(text) or text
        key = address_key(address_text).upper()
        if key in seen:
            continue
        seen.add(key)
        out.append(address_text)
    return out
