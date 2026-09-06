from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.damage_debugger.disasm import Instruction
from tools.damage_debugger.taint import EMPTY, Sink, TaintEngine, TaintTag

from .address import parse_address_spec
from .catalog import ROOT
from .coverage import load_traces
from .explain import base_label
from .ingest import sha256_file
from .provenance import display_path, parse_symbol_table, resolve_path
from .reporting import load_reports
from .sm83_model import SM83_MODEL_SOURCE
from .effect_trace import (
    frame_with_inferred_bank_state,
    instruction_effects,
    memory_write_effects,
    observed_memory_bank,
    update_inferred_bank_state_from_effects,
    update_inferred_bank_state_from_frame,
)
from .instruction_frames import (
    InstructionFrame,
    frame_register_known,
    parse_instruction_record,
    trace_records,
    parse_int,
    dict_items,
)
from .workflow import command_is_runnable


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
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    discovered_inputs = discover_dynamic_taint_inputs(loaded_reports, root=root)
    effective_traces = tuple(unique_list([*traces, *discovered_inputs["traces"]]))
    effective_source_regs = tuple(unique_list([*source_regs, *discovered_inputs["source_regs"]]))
    effective_source_mems = tuple(unique_list([*source_mems, *discovered_inputs["source_mems"]]))
    effective_source_symbols = tuple(unique_list([*source_symbols, *discovered_inputs["source_symbols"]]))
    effective_sink_symbols = tuple(unique_list([*sink_symbols, *discovered_inputs["sink_symbols"]]))
    effective_sink_addresses = tuple(unique_list([*sink_addresses, *discovered_inputs["sink_addresses"]]))

    loaded_traces, trace_errors = load_traces(traces=effective_traces, root=root)
    sym_path = resolve_path(symbols_path, root=root)
    errors = [*report_errors, *trace_errors]
    warnings: list[str] = []
    if not effective_traces:
        errors.append("at least one --trace or trace-producing --report is required")
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
    register_sources, register_errors = parse_register_sources(effective_source_regs)
    sinks, sink_errors = parse_sinks(
        sink_symbols=effective_sink_symbols,
        sink_addresses=effective_sink_addresses,
        sink_size=sink_size,
        symbol_table=symbol_table,
    )
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
            sinks=sinks,
            symbol_table=symbol_table,
        )
        for loaded in loaded_traces
    ] if not errors else []
    warnings.extend(
        warning
        for run in trace_runs
        for warning in run.get("warnings", [])
    )
    findings = [
        finding
        for run in trace_runs
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
        for run in trace_runs
        for attribution in run.get("write_attributions", [])
    ]
    bank_uncertainty = {
        run["source"]: [warning for warning in run["warnings"] if warning.startswith("bank identity unverified")]
        for run in trace_runs
    }
    for item in [*paths, *write_attributions]:
        warnings_for_source = bank_uncertainty.get(item["source"], [])
        if warnings_for_source:
            item["confidence"] = min(item["confidence"], 0.5)
            item["evidence"].extend(warnings_for_source)
            for contributor in item["contributors"]:
                contributor["confidence"] = min(contributor["confidence"], 0.5)
    commands = build_commands(
        paths=paths,
        write_attributions=write_attributions,
        traces=effective_traces,
        sink_symbols=effective_sink_symbols,
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_dynamic_taint_report",
        "root": str(root),
        "model_source": SM83_MODEL_SOURCE,
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
        "trace_count": len(loaded_traces),
        "requested_traces": list(traces),
        "effective_traces": list(effective_traces),
        "source_count": len(register_sources) + len(source_memory),
        "sink_count": len(sinks),
        "finding_count": len(findings),
        "path_count": len(paths),
        "write_attribution_count": len(write_attributions),
        "sources": source_summary(register_sources=register_sources, source_memory=source_memory),
        "sinks": [public_sink(sink) for sink in sinks],
        "targets": targets_for_sinks(
            sinks=sinks,
            paths=paths,
            write_attributions=write_attributions,
        ),
        "trace_runs": trace_runs,
        "findings": findings[:120],
        "paths": paths,
        "write_attributions": write_attributions[:120],
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This is emulator-trace-backed SM83 byte taint over supplied instruction frames; it is only as complete as the traced instruction window.",
            "Without explicit source seeds, the report still identifies exact sink-writing instructions and source operands, but cannot claim source-to-sink taint.",
            "Unsupported opcodes are reported and clear modeled destinations rather than inventing dependencies.",
            "Use trace-instruction capture or focused subsystem replay to produce dense opcode/register traces before relying on this as final proof.",
        ],
    }


def discover_dynamic_taint_inputs(loaded_reports: list[dict[str, Any]], *, root: Path) -> dict[str, Any]:
    traces: list[str] = []
    sink_symbols: list[str] = []
    sink_addresses: list[str] = []
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
        source_regs.extend(discovered["source_regs"])
        source_mems.extend(discovered["source_mems"])
        source_symbols.extend(discovered["source_symbols"])
    return {
        "trace_candidates": trace_candidates[:24],
        "traces": unique_list(traces),
        "sink_symbols": unique_list(sink_symbols),
        "sink_addresses": unique_list(sink_addresses),
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
    validation = data.get("execution_validation") if isinstance(data.get("execution_validation"), dict) else {}
    return {
        "trace_candidates": trace_candidates,
        "traces": traces,
        "sink_symbols": unique_list(
            [
                *string_items(sink_config.get("symbols")),
                *string_items(sink_config.get("sink_symbols")),
                *string_items(validation.get("watch_symbols")),
                *watch_symbols_from_report(data),
            ]
        ),
        "sink_addresses": unique_list(
            [
                *string_items(sink_config.get("addresses")),
                *string_items(sink_config.get("sink_addresses")),
            ]
        ),
        "source_regs": unique_list(
            [
                *string_items(source_config.get("regs")),
                *string_items(source_config.get("registers")),
                *string_items(source_config.get("source_regs")),
            ]
        ),
        "source_mems": unique_list(
            [
                *string_items(source_config.get("mems")),
                *string_items(source_config.get("memory")),
                *string_items(source_config.get("source_mems")),
            ]
        ),
        "source_symbols": unique_list(
            [
                *string_items(source_config.get("symbols")),
                *string_items(source_config.get("source_symbols")),
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


def watch_symbols_from_report(data: dict[str, Any]) -> list[str]:
    out = []
    for watch in dict_items(data.get("watches")):
        out.extend(string_items(watch.get("name") or watch.get("symbol") or watch.get("watch")))
    return out


def analyze_instruction_trace(
    loaded: dict[str, Any],
    *,
    register_sources: dict[str, str],
    source_memory: dict[tuple[int, int | None], str],
    sinks: list[Sink],
    symbol_table: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    records = trace_records(loaded["data"])
    instructions: list[Instruction] = []
    frames: list[InstructionFrame] = []
    errors: list[str] = []
    for index, record in enumerate(records):
        parsed = parse_instruction_record(record, default_seq=index)
        if parsed["error"]:
            errors.append(f"{loaded['source']}[{index}]: {parsed['error']}")
            continue
        instructions.append(parsed["instruction"])
        frames.append(parsed["frame"])

    engine = TaintEngine(sinks=sinks)
    for register, origin in register_sources.items():
        engine.seed_reg(register, origin)
    # The shared engine operates on bus addresses. Select a memory view for
    # each observed bank, retaining overwritten/empty slots when switching away.
    memory = {}
    raw_sources = set()
    for (address, bank), origin in source_memory.items():
        memory[(address, bank)] = frozenset({TaintTag(origin)})
        if bank is None:
            raw_sources.add(address)
    by_pc = {(instruction.bank, instruction.pc): instruction for instruction in instructions}
    inferred = {}
    normalized_frames = []
    bank_warnings = []
    sink_banks = {sink.name: _sink_bank(sink, symbol_table) for sink in sinks}
    banked_targets = {sink.name: sink.address for sink in sinks if sink_banks[sink.name] is not None}
    banked_targets.update({origin: address for (address, bank), origin in source_memory.items() if bank is not None})
    for frame in sorted(frames, key=lambda item: int(item.seq)):
        instruction = by_pc[(frame.bank, frame.pc)]
        inferred = update_inferred_bank_state_from_frame(inferred, frame)
        frame = frame_with_inferred_bank_state(frame, inferred)
        normalized_frames.append(frame)
        engine.sinks = [sink for sink in sinks if sink_banks[sink.name] is None or observed_memory_bank(frame, sink.address)[0] in {None, sink_banks[sink.name]}]
        for name, address in banked_targets.items():
            if observed_memory_bank(frame, address)[0] is None:
                bank_warnings.append(f"bank identity unverified for {name}; bus-address taint is provisional")
        writes = _step_banked_taint(engine, instruction, frame, memory, raw_sources)
        inferred = update_inferred_bank_state_from_effects(inferred, writes)
    frames = normalized_frames
    taint_report = engine.report
    findings = [
        public_finding(finding, source=loaded["source"])
        for finding in taint_report.findings
    ]
    write_attributions = build_write_attributions(
        source=loaded["source"],
        instructions=instructions,
        frames=frames,
        sinks=sinks,
        register_sources=register_sources,
        source_memory=source_memory,
        symbol_table=symbol_table,
        taint_findings=taint_report.findings,
    )
    return {
        "source": loaded["source"],
        "model_source": SM83_MODEL_SOURCE,
        "record_count": len(records),
        "instruction_count": len(instructions),
        "frame_count": len(frames),
        "finding_count": len(findings),
        "write_attribution_count": len(write_attributions),
        "unsupported": dict(taint_report.unsupported),
        "unsupported_count": sum(int(count) for count in taint_report.unsupported.values()),
        "errors": errors,
        "warnings": [*errors[:4], *unique_list(bank_warnings)],
        "findings": findings,
        "write_attributions": write_attributions[:120],
    }


def _step_banked_taint(engine, instruction, frame, memory, raw_sources=()):
    addresses = {address for address, _bank in memory}
    view = {}
    for address in addresses:
        bank = observed_memory_bank(frame, address)[0]
        if (address, bank) in memory:
            view[address] = memory[(address, bank)]
        elif bank is None:
            view[address] = frozenset(tag for (stored_address, _), tags in memory.items() if stored_address == address for tag in tags)
        elif address in raw_sources:
            view[address] = memory.get((address, None), EMPTY)
    engine.state.memory = view
    engine.step(instruction, frame)
    writes = memory_write_effects(instruction, frame)
    # The shared byte engine treats CALL/RST as control flow. Their concrete
    # return-address writes still replace any earlier taint in those stack slots.
    for item in writes:
        if "address" in item and any(source.get("kind") == "immediate" for source in item.get("source_operands", [])):
            engine.state.set_mem(item["address"], EMPTY)
    addresses.update(engine.state.memory)
    addresses.update(int(item["address"]) for item in writes if "address" in item)
    for address in addresses:
        bank = observed_memory_bank(frame, address)[0]
        memory[(address, bank)] = engine.state.memory.get(address, EMPTY)
    return writes


def _register_transport(records, *, register, start_seq, end_seq, mbc3=False):
    """Check one observed register dependency, stopping at uncertain evidence."""
    result = {"model_source": SM83_MODEL_SOURCE, "register": register,
              "start_seq": start_seq, "end_seq": end_seq, "proof_status": "planned_only", "errors": [],
              "mapper": "MBC3" if mbc3 else "unverified",
              "scope": "Byte dependency over this recorded interval with WRAM/HRAM transport and, when identified, MBC3 register writes; this does not establish SRAM contents, the gameplay invariant, or initiating cause."}
    if register not in "ABCDEHL" or len(register) != 1 or type(start_seq) is not int or type(end_seq) is not int or not 0 <= start_seq <= end_seq:
        result["errors"].append("invalid register transport interval")
        return result
    if any(type(record.get("seq")) is not int for record in records):
        result["errors"].append("transport requires explicit integer sequence numbers")
        return result
    parsed = [parse_instruction_record(record, default_seq=index) for index, record in enumerate(records)]
    if any(item["error"] for item in parsed):
        result["errors"].append("invalid instruction records")
        return result
    window = [item for item in parsed if start_seq <= item["frame"].seq <= end_seq]
    if [item["frame"].seq for item in window] != list(range(start_seq, end_seq + 1)):
        result["errors"].append("missing, duplicated, or out-of-order transport frames")
        return result
    engine = TaintEngine()
    engine.seed_reg(register, "call_return")
    memory = {}
    written_values = {}
    initial = window[0]["frame"]
    inferred = {"rom": initial.bank} if 0x4000 <= initial.pc < 0x8000 else {}
    transfers = []
    for index, item in enumerate(window):
        frame, instruction = item["frame"], item["instruction"]
        if item["bank_state_record_conflicts"] or not (set("AFBCDEHL") | {"SP"}) <= set(frame.known_registers):
            result["errors"].append(f"missing registers or conflicting bank state at sequence {frame.seq}")
            break
        inferred = update_inferred_bank_state_from_frame(inferred, frame)
        frame = frame_with_inferred_bank_state(frame, inferred)
        if frame.seq == end_seq:
            result.update(depends_on_return=bool(engine.state.reg(register)), proof_status="taint_proven", transfers=transfers)
            break
        effects = instruction_effects(instruction, frame)
        mapper_writes = [effect for effect in effects if effect.get("access") == "write"
                         and type(effect.get("address")) is int and 0x2000 <= effect["address"] <= 0x3FFF]
        next_inferred = update_inferred_bank_state_from_effects(inferred, effects)
        following = window[index + 1]["frame"]
        if (not any(effect.get("access") == "register_write" and register in effect.get("register", "") for effect in effects)
                and register in following.known_registers and getattr(frame, register) != getattr(following, register)):
            result["errors"].append(f"unexplained register change after sequence {frame.seq}")
            break
        control = next((effect for effect in effects if effect.get("access") == "control"), None)
        target = control.get("target") if control else (frame.pc + instruction.length) & 0xFFFF
        if control and target is None and instruction.opcode in (0xC0, 0xC8, 0xC9, 0xD0, 0xD8, 0xD9):
            observed = dict(frame.memory)
            low, high = observed.get(frame.SP), observed.get((frame.SP + 1) & 0xFFFF)
            if low is not None and high is not None:
                target = low | high << 8
        target_bank = 0 if target is not None and target < 0x4000 else next_inferred.get("rom")
        if target is None or following.pc != target or target_bank is None or following.bank != target_bank:
            result["errors"].append(f"unverified control transition after sequence {frame.seq}")
            break
        uncertain = any(str(effect.get("kind", "")).startswith("unmodeled") for effect in effects)
        for effect in effects:
            address = effect.get("address")
            if type(address) is not int or effect.get("access") not in ("read", "write") or effect.get("operation") == "opcode_fetch":
                continue
            if mbc3 and effect in mapper_writes and next_inferred.get("rom") is not None:
                continue
            # MBC3 RAM enable/select and RTC latch writes do not replace CPU
            # registers or WRAM/HRAM. This does not prove a later SRAM access.
            if (mbc3 and effect.get("access") == "write" and type(effect.get("value")) is int
                    and (0 <= address < 0x2000 or 0x4000 <= address < 0x8000)):
                continue
            if not (0xC000 <= address <= 0xDFFF or 0xFF80 <= address <= 0xFFFE):
                uncertain = True  # Other buses need alias/access-timing evidence.
            if (0x4000 <= address <= 0xBFFF or 0xD000 <= address <= 0xDFFF) and observed_memory_bank(frame, address)[0] is None:
                uncertain = True
        if uncertain:
            result["errors"].append(f"unmodeled effect or unknown memory bank at sequence {frame.seq}")
            break
        if instruction.opcode in (0xC1, 0xD1, 0xE1, 0xF1):
            observed = dict(frame.memory)
            addresses = (frame.SP, (frame.SP + 1) & 0xFFFF)
            values = [observed.get(address) for address in addresses]
            if any(value is None for value in values):
                result["errors"].append(f"missing POP stack samples at sequence {frame.seq}")
                break
            # A matching loaded value alone cannot establish which write supplied it.
            # Reconcile tagged stack slots with writes in this exact bank and interval.
            for address, value in zip(addresses, values):
                key = (address, observed_memory_bank(frame, address)[0])
                if memory.get(key) and written_values.get(key) != value:
                    result["errors"].append(f"POP sample disagrees with tagged stack write at sequence {frame.seq}")
                    break
            if result["errors"]:
                break
            pair = {0xC1: "BC", 0xD1: "DE", 0xE1: "HL", 0xF1: "AF"}[instruction.opcode]
            low = values[0] & 0xF0 if pair == "AF" else values[0]
            if (not (set(pair) | {"SP"}) <= set(following.known_registers)
                    or getattr(following, pair[0]) != values[1] or getattr(following, pair[1]) != low
                    or following.SP != (frame.SP + 2) & 0xFFFF):
                result["errors"].append(f"POP result disagrees with following registers at sequence {frame.seq}")
                break
        before = bool(engine.state.reg(register))
        writes = _step_banked_taint(engine, instruction, frame, memory)
        for write in writes:
            if "address" in write:
                key = (write["address"], observed_memory_bank(frame, write["address"])[0])
                written_values[key] = write.get("value")
        inferred = next_inferred
        if engine.report.unsupported:
            result["errors"].append(f"unsupported taint instruction at sequence {frame.seq}")
            break
        if (before != bool(engine.state.reg(register)) or instruction.opcode in (0xC5, 0xD5, 0xE5, 0xF5, 0xC1, 0xD1, 0xE1, 0xF1)
                or mapper_writes or any(effect.get("access") == "register_write" and register in effect.get("register", "") for effect in effects)):
            transfers.append({"seq": frame.seq, "pc": frame.pc, "bank": frame.bank,
                              "register_depends_on_return": bool(engine.state.reg(register))})
            if mapper_writes:
                transfers[-1]["rom_bank_after"] = inferred["rom"]
    return result


def _symbol_bank(entry: dict[str, Any]) -> int | None:
    spec = parse_address_spec(f"{int(entry['bank']):02X}:{int(entry['address']):04X}")
    return spec.bank if spec.exact_key_required else None


def _symbol_matches_frame(entry: dict[str, Any], frame: InstructionFrame) -> bool:
    bank = _symbol_bank(entry)
    return bank is None or observed_memory_bank(frame, int(entry["address"]))[0] in {None, bank}


def _sink_bank(sink: Sink, symbol_table: dict[str, dict[str, Any]]) -> int | None:
    if sink.name in symbol_table:
        return _symbol_bank(symbol_table[sink.name])
    spec = parse_address_spec(sink.name)
    return spec.bank if spec.exact_key_required else None


def parse_register_sources(source_regs: tuple[str, ...]) -> tuple[dict[str, str], list[str]]:
    out: dict[str, str] = {}
    errors: list[str] = []
    for raw in source_regs:
        name, origin = split_assignment(raw)
        register = name.lower()
        if register not in {"a", "f", "b", "c", "d", "e", "h", "l"}:
            errors.append(f"unsupported source register: {name}")
            continue
        out[register] = origin or f"source_reg:{register}"
    return out, errors


def parse_memory_sources(
    *,
    source_mems: tuple[str, ...],
    source_symbols: tuple[str, ...],
    symbol_table: dict[str, dict[str, Any]],
) -> tuple[dict[tuple[int, int | None], str], list[str]]:
    out: dict[tuple[int, int | None], str] = {}
    errors: list[str] = []
    for raw in source_mems:
        address_text, origin = split_assignment(raw)
        try:
            spec = parse_address_spec(address_text)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        out[(spec.address, spec.bank if spec.exact_key_required else None)] = origin or f"source_mem:${spec.address:04X}"
    for symbol in source_symbols:
        entry = symbol_table.get(symbol)
        if not entry:
            errors.append(f"source symbol not found in symbols: {symbol}")
            continue
        out[(int(entry["address"]), _symbol_bank(entry))] = f"source_symbol:{symbol}"
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


def build_write_attributions(
    *,
    source: str,
    instructions: list[Instruction],
    frames: list[InstructionFrame],
    sinks: list[Sink],
    register_sources: dict[str, str],
    source_memory: dict[tuple[int, int | None], str],
    symbol_table: dict[str, dict[str, Any]],
    taint_findings: list[Any],
) -> list[dict[str, Any]]:
    by_pc = {(instruction.bank, instruction.pc): instruction for instruction in instructions}
    taint_by_write = {
        (int(finding.seq), int(finding.address), str(finding.sink)): list(finding.taint)
        for finding in taint_findings
    }
    attributions: list[dict[str, Any]] = []
    sink_banks = {sink.name: _sink_bank(sink, symbol_table) for sink in sinks}
    for frame in sorted(frames, key=lambda item: int(item.seq)):
        instruction = by_pc.get((frame.bank, frame.pc))
        if instruction is None:
            continue
        writes = instruction_memory_writes(instruction, frame)
        if not any(sink.contains(int(write["address"])) for sink in sinks for write in writes):
            continue
        compatible_symbols = {name: entry for name, entry in symbol_table.items() if _symbol_matches_frame(entry, frame)}
        for write in writes:
            address = int(write["address"]) & 0xFFFF
            for sink in sinks:
                if not sink.contains(address):
                    continue
                if sink_banks[sink.name] is not None and observed_memory_bank(frame, address)[0] not in {None, sink_banks[sink.name]}:
                    continue
                taint = taint_by_write.get((int(frame.seq), address, sink.name), [])
                source_operands = [
                    enrich_source_operand(
                        operand,
                        register_sources={register: origin for register, origin in register_sources.items() if origin in taint},
                        source_memory={address: origin for address, origin in source_memory.items() if origin in taint},
                        symbol_table=compatible_symbols,
                    )
                    for operand in write["source_operands"]
                    if isinstance(operand, dict)
                ]
                contributors = contributors_for_taint(taint, register_sources=register_sources, source_memory=source_memory)
                pc_label = str(frame.pc_label)
                target = sink.name
                attributions.append(
                    {
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
                        "address_symbol": symbol_for_address(address, compatible_symbols),
                        "sink_offset": address - sink.address,
                        "write_kind": str(write["kind"]),
                        "source_operands": source_operands,
                        "contributors": contributors,
                        "taint": taint,
                        "score": write_attribution_score(contributors=contributors, taint=taint),
                        "confidence": 0.9 if taint else 0.76,
                        "evidence": write_attribution_evidence(
                            seq=int(frame.seq),
                            pc=int(frame.pc),
                            mnemonic=instruction.mnemonic,
                            target=target,
                            address=address,
                            source_operands=source_operands,
                            taint=taint,
                        ),
                        "related_symbols": related_symbols_for_write(
                            target=target,
                            pc_label=pc_label,
                            address=address,
                            source_operands=source_operands,
                            symbol_table=compatible_symbols,
                        ),
                        "related_files": [],
                        "commands": commands_for_write_attribution(
                            target=target,
                            routine=base_label(pc_label) or pc_label,
                            source=source,
                        ),
                    }
                )
    return attributions


def instruction_memory_writes(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    writes = []
    for item in memory_write_effects(instruction, frame):
        if "address" not in item:
            # Incomplete frames must not turn unknown addresses into address zero.
            continue
        kind = item["operation"]
        # Keep the established report wording for these instruction families.
        if instruction.opcode in {0x22, 0x32}:
            kind = "ld [hli/hld], a"
        elif instruction.opcode == 0xCB:
            kind = "cb [hl] read-modify-write"
        operands = []
        for operand in item.get("source_operands", []):
            if operand["kind"] == "register":
                operands.append(register_operand(operand["name"], frame))
            elif operand["kind"] == "memory":
                operands.append(memory_operand(int(operand["address"], 16)))
            elif operand["kind"] == "immediate":
                # Stack writes expose the corresponding byte of the return address.
                value = item.get("value") if item["kind"] == "stack_write" else int(operand["value"], 16)
                operands.append(immediate_operand(value))
        writes.append({"address": item["address"], "kind": kind, "source_operands": operands})
    return writes


def register_operand(register: str, frame: InstructionFrame) -> dict[str, Any]:
    register = register.lower()
    required = list(register) if register in {"bc", "de", "hl"} else [register]
    if not all(frame_register_known(frame, name) for name in required):
        return {"kind": "register", "name": register}
    value = pair_value(frame, register) if register in {"bc", "de", "hl", "sp"} else reg_value(frame, register)
    width = 4 if register in {"bc", "de", "hl", "sp"} else 2
    return {
        "kind": "register",
        "name": register,
        "value": f"{value:0{width}X}",
    }


def memory_operand(address: int) -> dict[str, Any]:
    return {
        "kind": "memory",
        "address": f"{address & 0xFFFF:04X}",
    }


def immediate_operand(value: int) -> dict[str, Any]:
    return {
        "kind": "immediate",
        "value": f"{value & 0xFF:02X}",
    }


def enrich_source_operand(
    operand: dict[str, Any],
    *,
    register_sources: dict[str, str],
    source_memory: dict[tuple[int, int | None], str],
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
            origins = [origin for (source_address, _bank), origin in source_memory.items() if source_address == address]
            if origins:
                out["origin"] = origins[0]
                out["contributor"] = True
    return out


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
) -> list[str]:
    sources = ", ".join(render_source_operand(item) for item in source_operands)
    evidence = [
        f"seq={seq} pc=${pc:04X}",
        mnemonic,
        f"write {target}@${address:04X}",
    ]
    if sources:
        evidence.append(f"sources={sources}")
    if taint:
        evidence.append("taint=" + ", ".join(taint))
    return evidence


def render_source_operand(operand: dict[str, Any]) -> str:
    kind = str(operand.get("kind", "operand"))
    if kind == "register":
        text = f"register:{operand.get('name')}"
        if "value" in operand:
            text += f"=${operand['value']}"
    elif kind == "memory":
        text = f"memory:${operand.get('address')}"
    elif kind == "immediate":
        text = f"immediate:${operand.get('value')}"
    else:
        text = kind
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
    symbols = [target, base_label(pc_label), symbol_for_address(address, symbol_table)]
    for operand in source_operands:
        symbols.extend(
            [
                str(operand.get("origin", "")),
                str(operand.get("symbol", "")),
                str(operand.get("name", "")) if operand.get("kind") == "register" else "",
            ]
        )
    return unique_list(symbols)


def commands_for_write_attribution(*, target: str, routine: str, source: str) -> list[str]:
    commands = []
    if source:
        commands.append(f"python -m tools.debugger minimize --trace {source} --expect event=memory_write")
        commands.append(f"python -m tools.debugger trace-index --trace {source} --watch-symbol {target}")
    if target and not target.startswith("$"):
        commands.append(f"python -m tools.debugger explain --symbol {target}")
        commands.append(f"python -m tools.debugger replay --symbol {target}")
    if routine:
        commands.append(f"python -m tools.debugger slice --symbol {routine} --symbol {target}")
    return unique_list(commands)


def symbol_for_address(address: int, symbol_table: dict[str, dict[str, Any]]) -> str:
    for label, entry in symbol_table.items():
        if int(entry.get("address", -1)) == (address & 0xFFFF):
            return str(label)
    return ""


def reg_value(frame: InstructionFrame, register: str) -> int:
    return int(getattr(frame, register.upper())) & 0xFF


def pair_value(frame: InstructionFrame, pair: str) -> int:
    pair = pair.lower()
    if pair == "hl":
        return int(frame.HL) & 0xFFFF
    if pair == "bc":
        return ((reg_value(frame, "b") << 8) | reg_value(frame, "c")) & 0xFFFF
    if pair == "de":
        return ((reg_value(frame, "d") << 8) | reg_value(frame, "e")) & 0xFFFF
    if pair == "sp":
        return int(frame.SP) & 0xFFFF
    raise KeyError(pair)


def build_paths(
    *,
    findings: list[dict[str, Any]],
    sinks: list[Sink],
    register_sources: dict[str, str],
    source_memory: dict[tuple[int, int | None], str],
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
        paths.append(
            {
                "id": f"dynamic_taint_path_{index:04d}",
                "title": f"{', '.join(taint) or 'source'} -> {target} at {pc_label}",
                "target": target,
                "access": "dynamic_write",
                "score": 92 if contributors else 84,
                "confidence": 0.9 if contributors else 0.78,
                "source": finding.get("source", ""),
                "seq": finding.get("seq"),
                "pc": finding.get("pc"),
                "pc_label": finding.get("pc_label", ""),
                "mnemonic": finding.get("mnemonic", ""),
                "sink_address": f"{int(finding.get('address', 0)):04X}",
                "sink_size": sink.size if sink else 1,
                "taint": taint,
                "contributors": contributors,
                "steps": [
                    {
                        "role": "dynamic_instruction",
                        "code": str(finding.get("mnemonic", "")),
                        "pc_label": str(finding.get("pc_label", "")),
                        "seq": finding.get("seq"),
                    }
                ],
                "evidence": [
                    f"seq={finding.get('seq')} pc=${int(finding.get('pc', 0)):04X}",
                    str(finding.get("mnemonic", "")),
                    "taint=" + ", ".join(taint),
                ],
                "related_symbols": unique_list([target, pc_label, *[item.get("symbol", "") for item in contributors]]),
                "related_files": [],
                "commands": commands_for_path(target=target, pc_label=pc_label, source=str(finding.get("source", ""))),
            }
        )
    return paths


def contributors_for_taint(
    taint: list[str],
    *,
    register_sources: dict[str, str],
    source_memory: dict[tuple[int, int | None], str],
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
    for (address, _bank), origin in source_memory.items():
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


def public_finding(finding: Any, *, source: str) -> dict[str, Any]:
    return {
        "source": source,
        "seq": int(finding.seq),
        "pc": int(finding.pc),
        "pc_label": str(finding.pc_label),
        "mnemonic": str(finding.mnemonic),
        "sink": str(finding.sink),
        "address": int(finding.address),
        "taint": list(finding.taint),
    }


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


def source_summary(*, register_sources: dict[str, str], source_memory: dict[tuple[int, int | None], str]) -> list[dict[str, Any]]:
    return [
        {"type": "register", "register": register, "origin": origin}
        for register, origin in sorted(register_sources.items())
    ] + [
        {"type": "memory", "address": f"{address:04X}", "origin": origin}
        for (address, _bank), origin in sorted(source_memory.items(), key=lambda item: (item[0][0], -1 if item[0][1] is None else item[0][1]))
    ]


def public_sink(sink: Sink) -> dict[str, Any]:
    return {"name": sink.name, "address": f"{sink.address:04X}", "size": sink.size}


def build_commands(
    *,
    paths: list[dict[str, Any]],
    write_attributions: list[dict[str, Any]],
    traces: tuple[str, ...],
    sink_symbols: tuple[str, ...],
) -> list[str]:
    commands = []
    for trace in traces[:3]:
        commands.append(f"python -m tools.debugger trace-index --trace {trace}")
        commands.append(f"python -m tools.debugger expect --trace {trace} --expect <expectation>")
    for symbol in sink_symbols[:4]:
        commands.append(f"python -m tools.debugger watch --watch-symbol {symbol} --execute")
        commands.append(f"python -m tools.debugger taint --symbol {symbol}")
    for path in paths[:4]:
        commands.extend(path.get("commands", [])[:3])
    for attribution in write_attributions[:4]:
        commands.extend(attribution.get("commands", [])[:3])
    return unique_list(commands)[:40]


def commands_for_path(*, target: str, pc_label: str, source: str) -> list[str]:
    commands = []
    if source:
        commands.append(f"python -m tools.debugger minimize --trace {source} --expect event=memory_write")
    if target and not target.startswith("$"):
        commands.append(f"python -m tools.debugger explain --symbol {target}")
        commands.append(f"python -m tools.debugger replay --symbol {target}")
        commands.append(f"python -m tools.debugger taint --symbol {target}")
    if pc_label:
        routine = base_label(pc_label) or pc_label
        if target and not target.startswith("$"):
            commands.append(f"python -m tools.debugger trace-instructions --symbol {routine} --watch-symbol {target} --execute --out-trace .local\\tmp\\debugger_instruction_trace_{target}.jsonl")
        commands.append(f"python -m tools.debugger slice --symbol {pc_label}")
    return unique_list(commands)


def split_assignment(raw: str) -> tuple[str, str]:
    text = str(raw).strip()
    if "=" not in text:
        return text, ""
    left, right = text.split("=", 1)
    return left.strip(), right.strip()


def parse_address(value: str) -> int:
    text = str(value).strip()
    if ":" in text:
        text = text.split(":", 1)[1]
    parsed = parse_int(text)
    if parsed < 0 or parsed > 0xFFFF:
        raise ValueError(f"address out of range: {value}")
    return parsed


def default_symbol_size(symbol: str, fallback: int) -> int:
    return 2 if symbol in {"wCurDamage"} else fallback


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

# --- Instruction-frame model enrichment (reverse/time-travel cluster) ---
# Bank-state + known-register frame parsing consumed by effect_trace and the
# reverse/when-wrote/tdb verbs. Additive: master's existing taint logic and
# InstructionFrame construction are unchanged; these populate the extra frame
# fields and provide the frame predicate helpers.

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
