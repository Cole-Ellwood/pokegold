from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.damage_debugger.disasm import Instruction, render_mnemonic
from tools.damage_debugger.taint import Sink, TaintEngine

from .address import parse_address_spec
from .catalog import ROOT
from .coverage import load_traces
from .explain import base_label
from .ingest import sha256_file
from .provenance import display_path, parse_symbol_table, resolve_path
from .reporting import load_reports
from .workflow import command_is_runnable


REGISTER_FIELDS = ("A", "F", "B", "C", "D", "E", "H", "L", "HL", "SP")
INDEX_REG = {0: "b", 1: "c", 2: "d", 3: "e", 4: "h", 5: "l", 6: "[hl]", 7: "a"}


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
    source_memory: dict[int, str],
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
    for address, origin in source_memory.items():
        engine.seed_mem(address, origin)
    taint_report = engine.run(instructions, frames)
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
        "record_count": len(records),
        "instruction_count": len(instructions),
        "frame_count": len(frames),
        "finding_count": len(findings),
        "write_attribution_count": len(write_attributions),
        "unsupported": dict(taint_report.unsupported),
        "unsupported_count": sum(int(count) for count in taint_report.unsupported.values()),
        "errors": errors,
        "warnings": [*errors[:4]],
        "findings": findings,
        "write_attributions": write_attributions[:120],
    }


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
            record, seq=seq, bank=bank, pc=pc, pc_label=pc_label
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
) -> tuple[dict[int, str], list[str]]:
    out: dict[int, str] = {}
    errors: list[str] = []
    for raw in source_mems:
        address_text, origin = split_assignment(raw)
        try:
            address = parse_address(address_text)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        out[address] = origin or f"source_mem:${address:04X}"
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
            address = parse_address(name)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        sinks.append(Sink(f"${address:04X}", address, sink_size))
    return sinks, errors


def build_write_attributions(
    *,
    source: str,
    instructions: list[Instruction],
    frames: list[InstructionFrame],
    sinks: list[Sink],
    register_sources: dict[str, str],
    source_memory: dict[int, str],
    symbol_table: dict[str, dict[str, Any]],
    taint_findings: list[Any],
) -> list[dict[str, Any]]:
    by_pc = {(instruction.bank, instruction.pc): instruction for instruction in instructions}
    taint_by_write = {
        (int(finding.seq), int(finding.address), str(finding.sink)): list(finding.taint)
        for finding in taint_findings
    }
    attributions: list[dict[str, Any]] = []
    for frame in sorted(frames, key=lambda item: int(item.seq)):
        instruction = by_pc.get((frame.bank, frame.pc))
        if instruction is None:
            continue
        for write in instruction_memory_writes(instruction, frame):
            address = int(write["address"]) & 0xFFFF
            for sink in sinks:
                if not sink.contains(address):
                    continue
                taint = taint_by_write.get((int(frame.seq), address, sink.name), [])
                source_operands = [
                    enrich_source_operand(
                        operand,
                        register_sources=register_sources,
                        source_memory=source_memory,
                        symbol_table=symbol_table,
                    )
                    for operand in write["source_operands"]
                    if isinstance(operand, dict)
                ]
                contributors = contributors_for_operands(source_operands)
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
                        "address_symbol": symbol_for_address(address, symbol_table),
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
                            symbol_table=symbol_table,
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
    op = instruction.opcode
    if op == 0x02:
        return [memory_write(pair_value(frame, "bc"), "ld [bc], a", register_operand("a", frame))]
    if op == 0x12:
        return [memory_write(pair_value(frame, "de"), "ld [de], a", register_operand("a", frame))]
    if op in {0x22, 0x32}:
        return [memory_write(pair_value(frame, "hl"), "ld [hli/hld], a", register_operand("a", frame))]
    if op == 0x36:
        value = instruction.operand[0] if instruction.operand else 0
        return [memory_write(pair_value(frame, "hl"), "ld [hl], n", immediate_operand(value))]
    if 0x70 <= op <= 0x77 and op != 0x76:
        source = INDEX_REG[op & 0x07]
        if source == "[hl]":
            return []
        return [memory_write(pair_value(frame, "hl"), f"ld [hl], {source}", register_operand(source, frame))]
    if op in {0x34, 0x35}:
        address = pair_value(frame, "hl")
        kind = "inc [hl]" if op == 0x34 else "dec [hl]"
        return [memory_write(address, kind, memory_operand(address))]
    if op == 0x08:
        address = u16_from_operand(instruction)
        return [
            memory_write(address, "ld [nn], sp low", register_operand("sp", frame)),
            memory_write(address + 1, "ld [nn], sp high", register_operand("sp", frame)),
        ]
    if op == 0xEA:
        return [memory_write(u16_from_operand(instruction), "ld [nn], a", register_operand("a", frame))]
    if op == 0xE0 and instruction.operand:
        return [memory_write(0xFF00 + int(instruction.operand[0]), "ldh [n], a", register_operand("a", frame))]
    if op == 0xE2:
        return [memory_write(0xFF00 + reg_value(frame, "c"), "ldh [c], a", register_operand("a", frame))]
    if op == 0xCB and instruction.operand:
        target = INDEX_REG[int(instruction.operand[0]) & 0x07]
        if target == "[hl]":
            sub = int(instruction.operand[0])
            group = (sub >> 6) & 0x03
            if group in {0, 2, 3}:
                address = pair_value(frame, "hl")
                return [memory_write(address, "cb [hl] read-modify-write", memory_operand(address))]
    return []


def memory_write(address: int, kind: str, *source_operands: dict[str, Any]) -> dict[str, Any]:
    return {
        "address": address & 0xFFFF,
        "kind": kind,
        "source_operands": [operand for operand in source_operands if operand],
    }


def register_operand(register: str, frame: InstructionFrame) -> dict[str, Any]:
    register = register.lower()
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
    source_memory: dict[int, str],
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
            if address in source_memory:
                out["origin"] = source_memory[address]
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
        text = f"register:{operand.get('name')}=${operand.get('value')}"
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


def source_summary(*, register_sources: dict[str, str], source_memory: dict[int, str]) -> list[dict[str, Any]]:
    return [
        {"type": "register", "register": register, "origin": origin}
        for register, origin in sorted(register_sources.items())
    ] + [
        {"type": "memory", "address": f"{address:04X}", "origin": origin}
        for address, origin in sorted(source_memory.items())
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
    text = str(value).strip()
    if ":" in text:
        text = text.split(":", 1)[1]
    parsed = parse_int(text)
    if parsed < 0 or parsed > 0xFFFF:
        raise ValueError(f"address out of range: {value}")
    return parsed


def parse_int(value: Any, *, default: int | None = None) -> int:
    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError("missing integer value")
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text.startswith("$"):
        return int(text[1:], 16)
    if text.startswith(("0x", "0X")):
        return int(text, 16)
    if any(char in "ABCDEFabcdef" for char in text):
        return int(text, 16)
    return int(text, 10)


def default_symbol_size(symbol: str, fallback: int) -> int:
    return 2 if symbol in {"wCurDamage"} else fallback


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

# --- Instruction-frame model enrichment (reverse/time-travel cluster) ---
# Bank-state + known-register frame parsing consumed by effect_trace and the
# reverse/when-wrote/tdb verbs. Additive: master's existing taint logic and
# InstructionFrame construction are unchanged; these populate the extra frame
# fields and provide the frame predicate helpers.

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
