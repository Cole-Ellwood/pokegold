from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.trace import runtime as trace_runtime

from .catalog import ROOT
from .content_state import read_byte, save_state_delta_summary, stop_pyboy, write_byte
from .localize import normalize_path
from .minimize import unique_list
from .provenance import display_path, parse_symbol_table, resolve_path
from .workflow import command_is_runnable


def build_state_space_report(
    *,
    patches: tuple[str, ...] = (),
    watch_symbols: tuple[str, ...] = (),
    scenario_id: str = "",
    source_files: tuple[str, ...] = (),
    symptom: str = "",
    rom_path: str = "pokegold.gbc",
    symbols_path: str = "pokegold.sym",
    base_save_state: str = "",
    out_state: str = "",
    execute: bool = False,
    report_path: str = "",
    root: Path = ROOT,
) -> dict[str, Any]:
    symbols = resolve_path(symbols_path, root=root)
    rom = resolve_path(rom_path, root=root)
    base_state = resolve_path(base_save_state, root=root) if base_save_state else None
    output_state = resolve_path(out_state, root=root) if out_state else None
    errors: list[str] = []
    warnings: list[str] = []

    if not patches:
        errors.append("at least one --patch SYMBOL=VALUE is required")
    if not symbols.exists():
        errors.append(f"missing symbols: {symbols_path}")
        symbol_table: dict[str, dict[str, Any]] = {}
    else:
        symbol_table = parse_symbol_table(symbols)
    if execute and not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if execute and base_state is None:
        errors.append("--execute requires --base-save-state")
    if execute and base_state is not None and not base_state.exists():
        errors.append(f"missing base save state: {base_save_state}")
    if execute and output_state is None:
        errors.append("--execute requires --out-state")

    patch_records, patch_errors = build_patch_records(
        patches=patches,
        symbol_table=symbol_table,
        symbols_path=symbols,
        scenario_id=scenario_id,
        source_file=normalize_path(source_files[0]) if source_files else "",
        out_state=display_path(output_state, root=root) if output_state is not None else out_state,
        root=root,
    )
    errors.extend(patch_errors)

    execution = execute_state_space(
        patches=patch_records,
        rom=rom,
        base_state=base_state,
        output_state=output_state,
        execute=execute,
        root=root,
    ) if execute and not errors else skipped_execution(execute=execute, out_state=out_state)
    errors.extend(execution.get("errors", []))
    warnings.extend(execution.get("warnings", []))

    report_ref = display_path(resolve_path(report_path, root=root), root=root) if report_path else "<state-space.json>"
    effective_out_state = str(execution.get("out_state") or out_state or "<patched-state>")
    final_patches = [
        {
            **patch,
            "executed": bool(execution.get("executed")),
            "applied": bool(patch.get("applied", False)),
            "actual_proof_status": patch_actual_proof_status(patch=patch, executed=bool(execution.get("executed"))),
            "expected_proof_status": str(patch.get("expected_proof_status") or "runtime_observed"),
            "expected_sinks": patch_expected_sinks(patch),
            "observed_sinks": patch_observed_sinks(patch, executed=bool(execution.get("executed"))),
        }
        for patch in (execution.get("applied_patches") or patch_records)
    ]
    expected_sinks = unique_list(
        sink
        for patch in final_patches
        for sink in patch.get("expected_sinks", [])
        if sink
    )
    observed_sinks = unique_list(
        sink
        for patch in final_patches
        for sink in patch.get("observed_sinks", [])
        if sink
    )
    actual_proof_status = aggregate_actual_proof_status(final_patches)
    commands = state_space_commands(
        patch_specs=patches,
        patch_records=patch_records,
        report_ref=report_ref,
        watch_symbols=tuple(unique_list([*watch_symbols, *[patch["base_symbol"] for patch in patch_records if patch.get("base_symbol")]])),
        scenario_id=scenario_id,
        source_files=source_files,
        base_save_state=base_save_state,
        out_state=effective_out_state,
        symbols_path=symbols_path,
        rom_path=rom_path,
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_state_space",
        "root": str(root),
        "valid": not errors,
        "executed": bool(execution.get("executed")),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "rom": display_path(rom, root=root),
        "symbols": display_path(symbols, root=root),
        "base_save_state": display_path(base_state, root=root) if base_state is not None else "",
        "out_state": display_path(output_state, root=root) if output_state is not None else out_state,
        "save_state_delta": execution.get("save_state_delta", {}),
        "scenario_id": scenario_id,
        "source_files": [normalize_path(path) for path in source_files],
        "symptom": symptom,
        "patch_specs": list(patches),
        "patch_count": len(final_patches),
        "watch_symbols": tuple_to_list(unique_list([*watch_symbols, *[patch["base_symbol"] for patch in final_patches if patch.get("base_symbol")]])),
        "actual_proof_status": actual_proof_status,
        "expected_proof_status": "runtime_observed",
        "expected_sinks": expected_sinks,
        "observed_sinks": observed_sinks,
        "state_space": {
            "scenario_ids": [scenario_id] if scenario_id else [],
            "source_files": [normalize_path(path) for path in source_files],
            "symptom": symptom,
            "patches": final_patches,
            "patch_count": len(final_patches),
            "watch_symbols": tuple_to_list(unique_list([*watch_symbols, *[patch["base_symbol"] for patch in final_patches if patch.get("base_symbol")]])),
            "actual_proof_status": actual_proof_status,
            "expected_proof_status": "runtime_observed",
            "expected_sinks": expected_sinks,
            "observed_sinks": observed_sinks,
            "base_save_state": display_path(base_state, root=root) if base_state is not None else "",
            "out_state": display_path(output_state, root=root) if output_state is not None else out_state,
            "save_state_delta": execution.get("save_state_delta", {}),
        },
        "execution": execution,
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This patches explicit WRAM bytes onto an existing save state; it does not synthesize every surrounding engine precondition.",
            "Use watch, replay, instruction tracing, expectations, and minimization against the emitted report before treating a state-space hypothesis as proven behavior.",
        ],
    }


def build_patch_records(
    *,
    patches: tuple[str, ...],
    symbol_table: dict[str, dict[str, Any]],
    symbols_path: Path,
    scenario_id: str,
    source_file: str,
    out_state: str,
    root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for raw in patches:
        specs, spec_errors = parse_patch_spec(raw)
        errors.extend(spec_errors)
        for spec in specs:
            record = patch_record(
                spec["base_symbol"],
                int(spec["value"]),
                symbol_table=symbol_table,
                symbols_path=symbols_path,
                root=root,
                address_offset=int(spec["address_offset"]),
                display_symbol=str(spec["symbol"]),
            )
            record.update(
                {
                    "scenario_id": scenario_id,
                    "source_file": source_file,
                    "out_state": out_state,
                    "status": "planned",
                    "materialization_status": "planned",
                    "executed": False,
                    "applied": False,
                    "actual_proof_status": "planned_only" if record.get("errors") else "ready_to_run",
                    "expected_proof_status": "runtime_observed",
                    "expected_sinks": [str(record.get("symbol", ""))] if record.get("symbol") else [],
                    "observed_sinks": [],
                    "patch_spec": raw,
                }
            )
            errors.extend(record.get("errors", []))
            records.append(record)
    return records, unique_list(errors)


def parse_patch_spec(raw: str) -> tuple[list[dict[str, Any]], list[str]]:
    text = raw.strip()
    if "=" not in text:
        return [], [f"invalid patch spec, expected SYMBOL=VALUE: {raw}"]
    left, right = (part.strip() for part in text.split("=", 1))
    if not left or not right:
        return [], [f"invalid patch spec, expected SYMBOL=VALUE: {raw}"]
    base_symbol, start_offset, display_symbol, symbol_errors = parse_patch_symbol(left)
    values, value_errors = parse_patch_values(right, raw=raw)
    specs = [
        {
            "symbol": display_symbol if index == 0 else f"{base_symbol}+{start_offset + index}",
            "base_symbol": base_symbol,
            "address_offset": start_offset + index,
            "value": value,
        }
        for index, value in enumerate(values)
    ]
    return specs, [*symbol_errors, *value_errors]


def parse_patch_symbol(text: str) -> tuple[str, int, str, list[str]]:
    if "+" not in text:
        return text, 0, text, []
    symbol, raw_offset = (part.strip() for part in text.split("+", 1))
    if not symbol or not raw_offset:
        return symbol or text, 0, text, [f"invalid patch symbol offset: {text}"]
    try:
        offset = int(raw_offset, 0)
    except ValueError:
        return symbol, 0, text, [f"invalid patch symbol offset: {text}"]
    if offset < 0:
        return symbol, 0, text, [f"patch symbol offset must be nonnegative: {text}"]
    return symbol, offset, text, []


def parse_patch_values(text: str, *, raw: str) -> tuple[list[int], list[str]]:
    values: list[int] = []
    errors: list[str] = []
    for piece in text.split(","):
        item = piece.strip()
        if not item:
            errors.append(f"empty byte value in patch spec: {raw}")
            continue
        try:
            value = int(item, 0)
        except ValueError:
            errors.append(f"invalid byte value in patch spec: {raw}")
            continue
        if not 0 <= value <= 0xFF:
            errors.append(f"byte value out of range in patch spec: {raw}")
            continue
        values.append(value)
    if not values and not errors:
        errors.append(f"invalid patch spec, expected at least one byte value: {raw}")
    return values, errors


def patch_record(
    symbol: str,
    value: int,
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
        "value": int(value),
        "value_hex": f"{int(value):02X}",
        "bank": int(entry.get("bank", 0)) if entry else 0,
        "address": address,
        "bank_address": (
            f"{int(entry.get('bank', 0)):02X}:{address:04X}"
            if entry else ""
        ),
        "errors": errors,
    }


def execute_state_space(
    *,
    patches: list[dict[str, Any]],
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
    pyboy = trace_runtime.open_pyboy(
        rom,
        "PyBoy is required for generic state-space materialization. Import failed",
    )
    trace_runtime.disable_realtime(pyboy)
    try:
        with base_state.open("rb") as fh:
            pyboy.load_state(fh)
        applied = []
        for patch in patches:
            write_byte(pyboy, bank=int(patch["bank"]), address=int(patch["address"]), value=int(patch["value"]))
            observed = read_byte(pyboy, bank=int(patch["bank"]), address=int(patch["address"]))
            applied.append(
                {
                    **patch,
                    "observed": observed,
                    "observed_hex": f"{observed:02X}",
                    "verified": observed == int(patch["value"]),
                    "executed": True,
                    "applied": True,
                    "status": "applied",
                    "materialization_status": "applied",
                    "actual_proof_status": "state_materialized" if observed == int(patch["value"]) else "planned_only",
                    "expected_proof_status": str(patch.get("expected_proof_status") or "runtime_observed"),
                    "expected_sinks": patch_expected_sinks(patch),
                    "observed_sinks": patch_expected_sinks(patch) if observed == int(patch["value"]) else [],
                    "out_state": display_path(output_state, root=root),
                }
            )
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


def skipped_execution(*, execute: bool, out_state: str) -> dict[str, Any]:
    return {
        "executed": False,
        "out_state": out_state,
        "patch_count": 0,
        "applied_patches": [],
        "errors": [],
        "warnings": [] if not execute else ["execution skipped because the state-space report was not ready"],
    }


def patch_expected_sinks(patch: dict[str, Any]) -> list[str]:
    existing = patch.get("expected_sinks")
    return unique_list(
        [
            *([str(item) for item in existing if item] if isinstance(existing, list) else []),
            str(patch.get("symbol", "")),
        ]
    )


def patch_observed_sinks(patch: dict[str, Any], *, executed: bool) -> list[str]:
    if isinstance(patch.get("observed_sinks"), list) and patch.get("observed_sinks"):
        return [str(item) for item in patch.get("observed_sinks", []) if item]
    if executed and bool(patch.get("verified", patch.get("applied", False))):
        return patch_expected_sinks(patch)
    return []


def patch_actual_proof_status(*, patch: dict[str, Any], executed: bool) -> str:
    explicit = str(patch.get("actual_proof_status") or "")
    if explicit:
        return explicit
    if executed and bool(patch.get("verified", patch.get("applied", False))):
        return "state_materialized"
    if patch.get("errors"):
        return "planned_only"
    return "ready_to_run"


def aggregate_actual_proof_status(patches: list[dict[str, Any]]) -> str:
    statuses = {str(patch.get("actual_proof_status") or "planned_only") for patch in patches}
    if not statuses:
        return "planned_only"
    if statuses == {"state_materialized"}:
        return "state_materialized"
    if "ready_to_run" in statuses and statuses <= {"ready_to_run", "state_materialized"}:
        return "ready_to_run"
    return "planned_only"


def state_space_commands(
    *,
    patch_specs: tuple[str, ...],
    patch_records: list[dict[str, Any]],
    report_ref: str,
    watch_symbols: tuple[str, ...],
    scenario_id: str,
    source_files: tuple[str, ...],
    base_save_state: str,
    out_state: str,
    symbols_path: str,
    rom_path: str,
) -> list[str]:
    patch_args = " ".join(f"--patch {spec}" for spec in patch_specs)
    scenario_cli_arg = f" --scenario-id {scenario_id}" if scenario_id else ""
    scenario_expect_arg = f",scenario={scenario_id}" if scenario_id else ""
    source_args = " ".join(f"--source-file {normalize_path(path)}" for path in source_files)
    base_arg = f"--base-save-state {base_save_state}" if base_save_state else "--base-save-state <base-state>"
    out_arg = f"--out-state {out_state}" if out_state and out_state != "<patched-state>" else "--out-state <patched-state>"
    watch_args = " ".join(f"--watch-symbol {symbol}" for symbol in watch_symbols[:8])
    first_record = patch_records[0] if patch_records else {}
    first_symbol = str(first_record.get("base_symbol") or first_record.get("symbol") or "<symbol>")
    first_value = (
        "0x" + str(first_record["value_hex"])
        if first_record.get("value_hex") else "<value>"
    )
    execute_minimize_arg = (
        " --execute-state-patches"
        if base_save_state and out_state and out_state != "<patched-state>"
        else ""
    )
    commands = [
        (
            "python -m tools.debugger state-space "
            f"{patch_args} {source_args} --symbols {symbols_path} --rom {rom_path} "
            f"{base_arg} {out_arg} --execute --json-out {report_ref}"
        ).strip(),
        f"python -m tools.debugger expect --report {report_ref} --expect state-patch={first_symbol}{scenario_expect_arg},value={first_value}",
        f"python -m tools.debugger replay --report {report_ref}{scenario_cli_arg} --save-state {out_state} --execute-watch",
        f"python -m tools.debugger watch {watch_args} --save-state {out_state} --execute",
        f"python -m tools.debugger trace-instructions --report {report_ref}{scenario_cli_arg} {watch_args} --save-state {out_state} --execute --require-hit",
        f"python -m tools.debugger minimize --report {report_ref} --expect state-patch={first_symbol}{scenario_expect_arg},value={first_value}{execute_minimize_arg} --out-state-report .local\\tmp\\debugger_state_space_minimized.json",
        f"python -m tools.debugger compare --report {report_ref}",
        f"python -m tools.debugger impact --report {report_ref}",
        f"python -m tools.debugger visualize --report {report_ref}",
    ]
    return unique_list(" ".join(command.split()) for command in commands if command.strip())


def tuple_to_list(values: list[str]) -> list[str]:
    return list(values)
