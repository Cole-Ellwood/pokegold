from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .address import (
    address_key_requires_exact_match as semantic_address_key_requires_exact_match,
    address_spec_requires_exact_key,
    command_address_text,
    parse_address_spec,
)
from .address_boundary import reverse_query_address_boundary_evidence
from .catalog import ROOT
from .evidence import evidence_atom, merge_evidence_atoms
from .effect_trace import build_effect_trace_report
from .provenance import parse_symbol_table, resolve_path
from .hardware_evidence import hardware_runtime_event_boundary
from .reporting import load_reports
from .workflow import command_is_runnable, command_option_values, command_parts


COMMAND_PLACEHOLDER_RE = re.compile(r"<[^>\s]+>")
COMMAND_INPUT_OPTIONS = (
    "--report",
    "--reports",
    "--trace",
    "--symbols",
    "--save-state",
    "--input-log",
    "--base-save-state",
    "--state",
    "--rom",
)
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
def build_reverse_query_report(
    *,
    reports: tuple[str, ...] = (),
    traces: tuple[str, ...] = (),
    symbols: tuple[str, ...] = (),
    addresses: tuple[str, ...] = (),
    symbols_path: str = "pokegold.sym",
    watch_size: int = 1,
    max_history: int = 12,
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, load_errors = load_reports(reports=reports, root=root)
    sym_path = resolve_path(symbols_path, root=root)
    symbol_table = parse_symbol_table(sym_path) if sym_path.exists() else {}
    errors = list(load_errors)
    if not sym_path.exists():
        errors.append(f"missing symbol file: {symbols_path}")
    if watch_size < 1:
        errors.append("--watch-size must be positive")
    if max_history < 1:
        errors.append("--max-history must be positive")

    targets, target_errors = query_targets(
        symbols=symbols,
        addresses=addresses,
        symbol_table=symbol_table,
    )
    errors.extend(target_errors)
    if not targets:
        errors.append("at least one --symbol or --address is required")

    effect_reports = [
        loaded
        for loaded in loaded_reports
        if loaded.get("data", {}).get("kind") == "unified_debugger_effect_trace"
    ]
    synthesized_effect_report = None
    if traces or (reports and not effect_reports):
        synthesized_effect_report = build_effect_trace_report(
            traces=traces,
            reports=tuple(report for report in reports if report),
            symbols_path=symbols_path,
            watch_symbols=symbols,
            watch_addresses=addresses,
            watch_size=watch_size,
            root=root,
        )
        if synthesized_effect_report.get("valid"):
            effect_reports.append({"source": "<synthesized-effect-trace>", "data": synthesized_effect_report})
        else:
            errors.extend(str(error) for error in synthesized_effect_report.get("errors", []))

    if not effect_reports:
        errors.append("no effect trace evidence was supplied or synthesized")

    results = [
        result
        for target in targets
        for loaded in effect_reports
        for result in reverse_query_results_for_report(
            target=target,
            source=str(loaded.get("source", "")),
            report=loaded.get("data", {}),
            max_history=max_history,
            symbols_path=symbols_path,
            watch_size=watch_size,
        )
    ]
    validation_routes = [
        route
        for result in results
        for route in dict_items(result.get("validation_routes"))
    ]
    commands = build_commands(
        targets=targets,
        reports=reports,
        traces=traces,
        symbols_path=symbols_path,
        watch_size=watch_size,
    )
    commands = unique_list([*commands, *[str(route.get("command", "")) for route in validation_routes]])
    return {
        "schema_version": 1,
        "kind": "unified_debugger_reverse_query",
        "root": str(root),
        "valid": not errors,
        "proof_status": reverse_query_proof_status(results),
        "error_count": len(errors),
        "errors": unique_list(errors),
        "symbols_path": symbols_path,
        "reports": list(reports),
        "traces": list(traces),
        "target_count": len(targets),
        "targets": targets,
        "result_count": len(results),
        "results": results,
        "validation_summary": validation_summary(results),
        "checkpoint_summary": checkpoint_summary(results),
        "bounded_effect_span_summary": bounded_effect_span_summary(results),
        "validation_route_count": len(validation_routes),
        "validation_routes": validation_routes,
        "synthesized_effect_trace": synthesized_effect_report,
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "Reverse queries over effect traces are exact only for the supplied instruction/effect window.",
            "Last-writer validation checks whether the answer is backed by a concrete effect event in that window; it is not checkpointed emulator replay.",
            "Checkpoint validation identifies the nearest pre-instruction trace checkpoint and checks modeled effects forward through the last-writer span; it is not a full emulator save-state checkpoint.",
            "Current matching uses exact bank-aware keys when available and falls back to matching the observed 16-bit bus address.",
            "DMA, PPU, timer, audio-mixer, interrupt-entry, and bank-switch side effects require richer emulator-backed effect capture before reverse queries can claim full CPU-side-effect completeness.",
        ],
    }


def query_targets(
    *,
    symbols: tuple[str, ...],
    addresses: tuple[str, ...],
    symbol_table: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    targets: list[dict[str, Any]] = []
    errors: list[str] = []
    for symbol in symbols:
        entry = symbol_table.get(symbol)
        if not entry:
            errors.append(f"symbol not found in symbols: {symbol}")
            continue
        raw = str(entry.get("bank_address") or entry.get("address"))
        try:
            spec = parse_address_spec(raw)
        except ValueError as exc:
            errors.append(f"{symbol}: {exc}")
            continue
        target = spec.as_dict()
        target.update({"type": "symbol", "symbol": symbol, "label": symbol})
        targets.append(target)
    for address in addresses:
        try:
            spec = parse_address_spec(address)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        target = spec.as_dict()
        target.update({"type": "address", "symbol": "", "label": spec.evidence()})
        targets.append(target)
    return unique_targets(targets), errors


def reverse_query_results_for_report(
    *,
    target: dict[str, Any],
    source: str,
    report: dict[str, Any],
    max_history: int,
    symbols_path: str,
    watch_size: int,
) -> list[dict[str, Any]]:
    index_matches = matching_write_index_entries(target, report.get("write_index"))
    events = dict_items(report.get("events"))
    results: list[dict[str, Any]] = []
    for entry in index_matches:
        history = entry_history(entry, events=events, max_history=max_history)
        last_write = last_history_item(history, access="write")
        validation = result_validation(
            entry=entry,
            events=events,
            last_write=last_write,
        )
        checkpoint = checkpoint_validation(
            trace_window=report.get("trace_window") if isinstance(report.get("trace_window"), dict) else {},
            validation=validation,
            last_write=last_write,
        )
        bounded_effect_span = bounded_effect_span_validation(
            entry=entry,
            events=events,
            checkpoint=checkpoint,
            last_write=last_write,
        )
        hardware_gate = hardware_side_effect_gate(last_write)
        validation_routes = result_validation_routes(
            target=target,
            source=source,
            report=report,
            validation=validation,
            symbols_path=symbols_path,
            watch_size=watch_size,
        )
        proof_status = result_proof_status(
            entry=entry,
            last_write=last_write,
            validation=validation,
            hardware_gate=hardware_gate,
        )
        result = {
            "source": source,
            "target": target,
            "matched_address_key": entry.get("address_key", ""),
            "matched_address": entry.get("address", ""),
            "match_precision": entry.get("match_precision", ""),
            "bank_match": entry.get("bank_match", ""),
            "ambiguous_address_keys": string_items(entry.get("ambiguous_address_keys")),
            "address_match": address_match_summary(target=target, entry=entry),
            "proof_downgrade_reason": entry.get("proof_downgrade_reason", ""),
            "read_count": int(entry.get("read_count", 0) or 0),
            "write_count": int(entry.get("write_count", 0) or 0),
            "last_writer_seq": entry.get("last_writer_seq"),
            "last_writer_pc": entry.get("last_writer_pc", ""),
            "last_value_hex": last_write.get("value_hex", "") if last_write else entry.get("last_value_hex", ""),
            "last_writer": last_write,
            "history": history,
            "validation": validation,
            "checkpoint_validation": checkpoint,
            "bounded_effect_span_validation": bounded_effect_span,
            "hardware_side_effect_gate": hardware_gate,
            "validation_routes": validation_routes,
            "requested_static_address": requested_static_address_fact(target),
            "observed_runtime_address": observed_runtime_address_fact(
                entry=entry,
                last_write=last_write,
                proof_status=proof_status,
            ),
            "address_fact_boundary": address_fact_boundary(
                target=target,
                entry=entry,
                proof_status=proof_status,
            ),
            "proof_status": proof_status,
            "evidence": result_evidence(target=target, entry=entry, last_write=last_write),
            "commands": result_commands(target),
        }
        result["evidence"] = [
            *reverse_query_address_boundary_evidence(result),
            *result["evidence"],
        ]
        if hardware_gate.get("requires_runtime_event") and not hardware_gate.get("runtime_event_present"):
            result["proof_downgrade_reason"] = hardware_gate.get("reason", "")
            result["evidence"].extend(hardware_gate_evidence(hardware_gate))
        result["evidence_atoms"] = reverse_query_result_evidence_atoms(result)
        results.append(result)
    return results


def reverse_query_proof_status(results: list[dict[str, Any]]) -> str:
    if any(result_has_observed_write(result) for result in results):
        return "instruction_observed"
    return "planned_only"


def reverse_query_result_evidence_atoms(result: dict[str, Any]) -> list[dict[str, Any]]:
    target = result.get("target") if isinstance(result.get("target"), dict) else {}
    last_writer = result.get("last_writer") if isinstance(result.get("last_writer"), dict) else {}
    validation = result.get("validation") if isinstance(result.get("validation"), dict) else {}
    checkpoint = result.get("checkpoint_validation") if isinstance(result.get("checkpoint_validation"), dict) else {}
    hardware_gate = (
        result.get("hardware_side_effect_gate")
        if isinstance(result.get("hardware_side_effect_gate"), dict)
        else {}
    )
    bounded_span = (
        result.get("bounded_effect_span_validation")
        if isinstance(result.get("bounded_effect_span_validation"), dict)
        else {}
    )
    return merge_evidence_atoms(
        evidence_atom(
            claim_type="reverse_query.last_writer",
            origin="reverse_query",
            observation_type="bounded_effect_window",
            proof_status=result.get("proof_status"),
            source_report=str(result.get("source", "")),
            source_kind="effect_trace",
            scope={
                "target": target.get("label") or target.get("symbol") or result.get("matched_address", ""),
                "last_writer_seq": result.get("last_writer_seq"),
                "last_writer_pc": result.get("last_writer_pc", ""),
                "checkpoint_seq": checkpoint.get("checkpoint_seq"),
                "bounded_span_start_seq": bounded_span.get("start_seq"),
                "bounded_span_end_seq": bounded_span.get("end_seq"),
            },
            subjects={
                "symbols": [str(target.get("symbol", "")), str(last_writer.get("pc_label", ""))],
                "addresses": [str(result.get("matched_address", "")), str(last_writer.get("address", ""))],
            },
            precision={
                "matched_address_key": result.get("matched_address_key", ""),
                "match_precision": result.get("match_precision", ""),
                "bank_match": result.get("bank_match", ""),
                "ambiguous_address_keys": string_items(result.get("ambiguous_address_keys")),
                "proof_downgrade_reason": result.get("proof_downgrade_reason", ""),
                "requested_static_address_key": (
                    result.get("requested_static_address", {}).get("address_key", "")
                    if isinstance(result.get("requested_static_address"), dict)
                    else ""
                ),
                "observed_runtime_address_key": (
                    result.get("observed_runtime_address", {}).get("address_key", "")
                    if isinstance(result.get("observed_runtime_address"), dict)
                    else ""
                ),
                "exact_runtime_address_proven": (
                    result.get("address_fact_boundary", {}).get("exact_runtime_address_proven", False)
                    if isinstance(result.get("address_fact_boundary"), dict)
                    else False
                ),
            },
            validation={
                "status": validation.get("status", ""),
                "proof_status": validation.get("proof_status", ""),
                "checkpoint_status": checkpoint.get("status", ""),
                "bounded_span_status": bounded_span.get("status", ""),
                "hardware_event_required": hardware_gate.get("requires_runtime_event", False),
                "hardware_runtime_event": hardware_gate.get("runtime_event_present", False),
                "hardware_proof_gate": hardware_gate.get("status", ""),
                "hardware_event_identity": hardware_gate.get("hardware_event_identity", ""),
                "hardware_generic_event_label_present": hardware_gate.get("hardware_generic_event_label_present", False),
                "hardware_event_types": hardware_gate.get("hardware_event_types", []),
            },
            detail={
                "last_value_hex": result.get("last_value_hex", ""),
                "operation": last_writer.get("operation", ""),
                "hardware_model": hardware_gate.get("hardware_model", ""),
                "proof_downgrade_reason": hardware_gate.get("reason", ""),
            },
        ),
        last_writer.get("evidence_atoms"),
    )


def result_has_observed_write(result: dict[str, Any]) -> bool:
    if result.get("proof_status") not in {None, "", "instruction_observed"}:
        return False
    return concrete_observed_write(result.get("last_writer"))


def requested_static_address_fact(target: dict[str, Any]) -> dict[str, Any]:
    return {
        "fact_type": "requested_static_address",
        "source": "query_target",
        "target_type": str(target.get("type", "")),
        "symbol": str(target.get("symbol", "")),
        "label": str(target.get("label", "")),
        "address": str(target.get("address_hex", "")),
        "address_key": str(target.get("key") or target.get("address_key") or ""),
        "space": str(target.get("space", "")),
        "bank": target.get("bank"),
        "bank_semantics": str(target.get("bank_semantics", "")),
        "bank_valid": target.get("bank_valid", True) is not False,
        "exact_key_required": target_requires_exact_key(target),
        "proof_status": "planned_only",
    }


def observed_runtime_address_fact(
    *,
    entry: dict[str, Any],
    last_write: dict[str, Any] | None,
    proof_status: str,
) -> dict[str, Any]:
    return {
        "fact_type": "observed_runtime_address",
        "source": "effect_trace.write_index",
        "address": str(entry.get("address", "")),
        "address_key": str(entry.get("address_key", "")),
        "space": str(entry.get("space", "")),
        "bank": entry.get("bank"),
        "bank_source": str(entry.get("bank_source") or (last_write or {}).get("bank_source", "")),
        "match_precision": str(entry.get("match_precision", "")),
        "bank_match": str(entry.get("bank_match", "")),
        "ambiguous_address_keys": string_items(entry.get("ambiguous_address_keys")),
        "last_writer_seq": (last_write or {}).get("seq", entry.get("last_writer_seq")),
        "last_writer_pc": str((last_write or {}).get("pc") or entry.get("last_writer_pc") or ""),
        "proof_status": proof_status,
    }


def address_fact_boundary(*, target: dict[str, Any], entry: dict[str, Any], proof_status: str) -> dict[str, Any]:
    entry_key = str(entry.get("address_key", ""))
    match_precision = str(entry.get("match_precision", ""))
    bank_match = str(entry.get("bank_match", ""))
    runtime_key_exact = address_key_requires_exact_match(entry_key)
    exact_runtime_address_proven = bool(
        proof_status == "instruction_observed"
        and (
            match_precision == "exact_address_key"
            or (match_precision == "bus_address" and bank_match == "not_required" and not runtime_key_exact)
        )
    )
    return {
        "kind": "requested_static_vs_observed_runtime_address",
        "requested_fact_type": "requested_static_address",
        "observed_fact_type": "observed_runtime_address",
        "target_exact_key_required": target_requires_exact_key(target),
        "runtime_key_exact": runtime_key_exact,
        "match_precision": match_precision,
        "bank_match": bank_match,
        "ambiguous_address_keys": string_items(entry.get("ambiguous_address_keys")),
        "exact_runtime_address_proven": exact_runtime_address_proven,
        "proof_status": proof_status,
        "proof_downgrade_reason": str(entry.get("proof_downgrade_reason", "")),
    }


def result_proof_status(
    *,
    entry: dict[str, Any],
    last_write: dict[str, Any] | None,
    validation: dict[str, Any] | None = None,
    hardware_gate: dict[str, Any] | None = None,
) -> str:
    if entry.get("match_precision") == "bus_address_unverified_bank":
        return "planned_only"
    if not concrete_observed_write(last_write):
        return "planned_only"
    if hardware_gate and hardware_gate.get("requires_runtime_event") and not hardware_gate.get("runtime_event_present"):
        return "planned_only"
    if not validation:
        return "instruction_observed"
    if validation.get("status") == "effect_event_matched":
        return "instruction_observed"
    if (
        validation.get("status") == "index_history_only"
        and validation.get("proof_status") == "instruction_observed"
    ):
        return "instruction_observed"
    return "planned_only"


def concrete_observed_write(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("access") != "write":
        return False
    if value.get("seq") in {None, ""}:
        return False
    pc = str(value.get("pc") or value.get("pc_bank_address") or value.get("last_writer_pc") or "")
    address = str(value.get("address_key") or value.get("address") or value.get("address_hex") or "")
    return bool(pc and address)


def hardware_side_effect_gate(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {
            "requires_runtime_event": False,
            "runtime_event_present": False,
            "status": "not_hardware_side_effect",
            "reason": "",
        }
    requires = hardware_side_effect_requires_runtime_event(value)
    boundary = hardware_runtime_event_boundary(value)
    runtime_event = bool(boundary["runtime_event_present"])
    model = str(value.get("hardware_model") or "")
    kind = str(value.get("kind") or "")
    reason = ""
    status = "not_required"
    if requires:
        status = "explicit_runtime_event_present" if runtime_event else "explicit_runtime_event_missing"
        if not runtime_event:
            reason = hardware_side_effect_downgrade_reason(value)
    return {
        "requires_runtime_event": requires,
        "runtime_event_present": runtime_event,
        "status": status,
        "hardware_model": model,
        "kind": kind,
        "category": str(value.get("category") or ""),
        "evidence_source": str(value.get("evidence_source") or ""),
        "evidence_status": str(value.get("evidence_status") or ""),
        "runtime_observation": str(value.get("runtime_observation") or ""),
        "hardware_event_identity": boundary["hardware_event_identity"],
        "hardware_event_labels": boundary["hardware_event_labels"],
        "hardware_runtime_event_source_fields": boundary["hardware_runtime_event_source_fields"],
        "hardware_generic_event_label_present": boundary["hardware_generic_event_label_present"],
        "hardware_event_types": boundary["hardware_event_types"],
        "reason": reason,
    }


def hardware_side_effect_requires_runtime_event(value: dict[str, Any]) -> bool:
    if bool(value.get("hardware_event_required")):
        return True
    model = str(value.get("hardware_model") or "")
    if model in HARDWARE_EVENT_REQUIRED_MODELS:
        return True
    kind = str(value.get("kind") or "")
    if kind in HARDWARE_EVENT_REQUIRED_KINDS:
        return True
    return False


def hardware_side_effect_downgrade_reason(value: dict[str, Any]) -> str:
    model = str(value.get("hardware_model") or value.get("kind") or "hardware_side_effect")
    return f"{model}_requires_explicit_runtime_event"


def hardware_gate_evidence(gate: dict[str, Any]) -> list[str]:
    return [
        item
        for item in [
            f"hardware_side_effect_gate={gate.get('status', '')}",
            f"hardware_model={gate.get('hardware_model', '')}" if gate.get("hardware_model") else "",
            f"hardware_kind={gate.get('kind', '')}" if gate.get("kind") else "",
            f"hardware_event_identity={gate.get('hardware_event_identity', '')}" if gate.get("hardware_event_identity") else "",
            (
                f"hardware_generic_event_label_present={gate.get('hardware_generic_event_label_present')}"
                if gate.get("hardware_generic_event_label_present")
                else ""
            ),
            f"proof_downgrade_reason={gate.get('reason', '')}" if gate.get("reason") else "",
        ]
        if item
    ]


def result_validation(
    *,
    entry: dict[str, Any],
    events: list[dict[str, Any]],
    last_write: dict[str, Any] | None,
) -> dict[str, Any]:
    if not last_write:
        return {
            "status": "no_observed_write",
            "validated": False,
            "proof_status": "planned_only",
            "message": "No write to this target was observed in the supplied effect window.",
        }
    if not concrete_observed_write(last_write):
        return {
            "status": "index_incomplete",
            "validated": False,
            "proof_status": "planned_only",
            "message": "The compact effect index reports a write count, but no concrete write history/event item was supplied.",
        }
    event_match = matching_event_write(entry=entry, events=events, last_write=last_write)
    if event_match:
        return {
            "status": "effect_event_matched",
            "validated": True,
            "proof_status": "instruction_observed",
            "history_trusted": True,
            "seq": event_match.get("seq"),
            "pc": event_match.get("pc_bank_address", ""),
            "trace_source": event_match.get("trace_source", ""),
            "effect_evidence_source": last_write.get("evidence_source", ""),
            "effect_evidence_status": last_write.get("evidence_status", ""),
            "runtime_observation": last_write.get("runtime_observation", ""),
            "history_source": last_write.get("history_source", ""),
            "effect_trace_schema_version": last_write.get("effect_trace_schema_version", ""),
            "message": "Last-writer answer is backed by a concrete write effect in the supplied trace window.",
        }
    history_trusted = trusted_compact_history(last_write)
    return {
        "status": "index_history_only",
        "validated": False,
        "proof_status": "instruction_observed" if history_trusted else "planned_only",
        "history_trusted": history_trusted,
        "effect_evidence_source": last_write.get("evidence_source", ""),
        "effect_evidence_status": last_write.get("evidence_status", ""),
        "runtime_observation": last_write.get("runtime_observation", ""),
        "history_source": last_write.get("history_source", ""),
        "effect_trace_schema_version": last_write.get("effect_trace_schema_version", ""),
        "message": (
            "Last-writer answer comes from trusted compact effect-index history; the full event body was not supplied."
            if history_trusted
            else (
                "Last-writer answer comes from compact effect-index history without trusted evidence atoms "
                "or source markers; the full event body was not supplied."
            )
        ),
    }


def trusted_compact_history(value: dict[str, Any]) -> bool:
    if merge_evidence_atoms(value.get("evidence_atoms")):
        return True
    if str(value.get("history_source") or "") == "effect_trace.write_index":
        return True
    schema_version = value.get("effect_trace_schema_version")
    if schema_version not in (None, ""):
        return True
    return False


def matching_event_write(
    *,
    entry: dict[str, Any],
    events: list[dict[str, Any]],
    last_write: dict[str, Any],
) -> dict[str, Any] | None:
    target_seq = last_write.get("seq")
    target_pc = str(last_write.get("pc", ""))
    target_operation = str(last_write.get("operation", ""))
    target_value = str(last_write.get("value_hex", ""))
    for event in events:
        if target_seq is not None and event.get("seq") != target_seq:
            continue
        if target_pc and str(event.get("pc_bank_address", "")) != target_pc:
            continue
        for item in dict_items(event.get("effects")):
            if item.get("access") != "write":
                continue
            if not effect_matches_entry(entry, item):
                continue
            if target_operation and str(item.get("operation", "")) != target_operation:
                continue
            if target_value and str(item.get("value_hex", "")) != target_value:
                continue
            return event
    return None


def validation_summary(results: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "effect_event_matched": 0,
        "index_history_only": 0,
        "index_incomplete": 0,
        "no_observed_write": 0,
        "other": 0,
    }
    for result in results:
        status = str(result.get("validation", {}).get("status", ""))
        if status in summary:
            summary[status] += 1
        else:
            summary["other"] += 1
    return summary


def checkpoint_summary(results: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "ambiguous_checkpoint_source": 0,
        "checkpoint_before_writer": 0,
        "checkpoint_at_writer": 0,
        "no_prior_checkpoint": 0,
        "no_trace_window": 0,
        "no_observed_write": 0,
        "other": 0,
    }
    for result in results:
        status = str(result.get("checkpoint_validation", {}).get("status", ""))
        if status in summary:
            summary[status] += 1
        else:
            summary["other"] += 1
    return summary


def bounded_effect_span_summary(results: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "effect_span_consistent": 0,
        "effect_span_mismatch": 0,
        "no_checkpoint": 0,
        "no_observed_write": 0,
        "no_write_in_span": 0,
        "unknown_final_value": 0,
        "other": 0,
    }
    for result in results:
        status = str(result.get("bounded_effect_span_validation", {}).get("status", ""))
        if status in summary:
            summary[status] += 1
        else:
            summary["other"] += 1
    return summary


def checkpoint_validation(
    *,
    trace_window: dict[str, Any],
    validation: dict[str, Any],
    last_write: dict[str, Any] | None,
) -> dict[str, Any]:
    if not last_write:
        return {
            "status": "no_observed_write",
            **checkpoint_base_fields(checkpointed=False),
            "proof_status": "planned_only",
            "message": "No observed write is available to place in a trace-window checkpoint span.",
        }
    if not trace_window or not dict_items(trace_window.get("checkpoints")):
        return {
            "status": "no_trace_window",
            **checkpoint_base_fields(checkpointed=False),
            "proof_status": "planned_only",
            "message": "The effect report did not include trace-window checkpoints.",
        }
    seq = parse_int(last_write.get("seq"))
    if seq is None:
        return {
            "status": "no_prior_checkpoint",
            **checkpoint_base_fields(checkpointed=False),
            "proof_status": "planned_only",
            "message": "The last write does not carry a sequence number that can be aligned to checkpoints.",
        }
    trace_source = str(last_write.get("trace_source") or validation.get("trace_source") or "")
    checkpoint = nearest_checkpoint(trace_window, seq=seq, trace_source=trace_source)
    if not checkpoint:
        ambiguous_sources = checkpoint_source_ambiguity(trace_window, seq=seq, trace_source=trace_source)
        if ambiguous_sources:
            return {
                "status": "ambiguous_checkpoint_source",
                **checkpoint_base_fields(checkpointed=False),
                "proof_status": "planned_only",
                "trace_source": trace_source,
                "last_writer_seq": seq,
                "checkpoint_sources": ambiguous_sources,
                "message": "Multiple checkpoint trace sources could bound this writer, so no checkpoint span was claimed.",
            }
        return {
            "status": "no_prior_checkpoint",
            **checkpoint_base_fields(checkpointed=False),
            "proof_status": "planned_only",
            "trace_source": trace_source,
            "last_writer_seq": seq,
            "message": "No checkpoint at or before the last writer was retained for this trace window.",
        }
    checkpoint_seq = parse_int(checkpoint.get("seq"))
    status = "checkpoint_at_writer" if checkpoint_seq == seq else "checkpoint_before_writer"
    proof_status = "instruction_observed" if validation.get("proof_status") == "instruction_observed" else "planned_only"
    replay_fields = checkpoint_emulator_replay_fields(checkpoint)
    modeled_effect_span = {
        "source": checkpoint.get("source", ""),
        "from_seq": checkpoint_seq,
        "to_seq": seq,
        "instruction_span": (seq - checkpoint_seq + 1) if checkpoint_seq is not None else None,
        "validation_engine": "modeled_effect_span",
    }
    return {
        "status": status,
        **checkpoint_base_fields(checkpointed=True),
        **replay_fields,
        "proof_status": proof_status,
        "trace_source": trace_source or checkpoint.get("source", ""),
        "last_writer_seq": seq,
        "checkpoint": compact_checkpoint(checkpoint),
        "modeled_effect_span": modeled_effect_span,
        "replay_span": modeled_effect_span,
        "legacy_replay_span": True,
        "message": (
            "Last-writer answer is inside a bounded trace-window span whose modeled effects can be checked "
            "forward from the nearest retained pre-instruction trace checkpoint."
        ),
    }


def nearest_checkpoint(trace_window: dict[str, Any], *, seq: int, trace_source: str) -> dict[str, Any] | None:
    candidates = []
    for checkpoint in dict_items(trace_window.get("checkpoints")):
        checkpoint_seq = parse_int(checkpoint.get("seq"))
        if checkpoint_seq is None or checkpoint_seq > seq:
            continue
        if trace_source and str(checkpoint.get("source", "")) != trace_source:
            continue
        candidates.append(checkpoint)
    if candidates and not trace_source:
        sources = {str(item.get("source", "")) for item in candidates}
        if len(sources) > 1:
            return None
    return max(candidates, key=lambda item: parse_int(item.get("seq")) or -1) if candidates else None


def checkpoint_source_ambiguity(trace_window: dict[str, Any], *, seq: int, trace_source: str) -> list[str]:
    if trace_source:
        return []
    sources = set()
    for checkpoint in dict_items(trace_window.get("checkpoints")):
        checkpoint_seq = parse_int(checkpoint.get("seq"))
        if checkpoint_seq is None or checkpoint_seq > seq:
            continue
        sources.add(str(checkpoint.get("source", "")))
    return sorted(sources) if len(sources) > 1 else []


def checkpoint_base_fields(*, checkpointed: bool) -> dict[str, Any]:
    return {
        "checkpointed": checkpointed,
        "trace_checkpointed": checkpointed,
        "validation_kind": "trace_window_checkpoint",
        "checkpoint_kind": "pre_instruction_trace_checkpoint",
        "emulator_replay": False,
        "emulator_replay_status": "not_run",
        "emulator_replay_validation": emulator_replay_not_run_validation(),
    }


def emulator_replay_not_run_validation() -> dict[str, Any]:
    return {
        "attempted": False,
        "status": "not_run",
        "engine": "emulator",
        "replay_kind": "emulator_save_state",
        "reason": "no emulator save-state checkpoint was supplied",
    }


def checkpoint_emulator_replay_fields(checkpoint: dict[str, Any]) -> dict[str, Any]:
    validation = checkpoint_emulator_replay_validation(checkpoint)
    status = str(validation.get("status") or checkpoint.get("emulator_replay_status") or "not_run")
    attempted = bool(validation.get("attempted")) or bool(checkpoint.get("emulator_replay")) or status not in {
        "",
        "not_run",
    }
    return {
        "emulator_replay": attempted and status != "not_run",
        "emulator_replay_status": status,
        "emulator_replay_validation": validation,
    }


def checkpoint_emulator_replay_validation(checkpoint: dict[str, Any]) -> dict[str, Any]:
    supplied = checkpoint.get("emulator_replay_validation")
    if isinstance(supplied, dict) and supplied:
        validation = dict(supplied)
        validation.setdefault("attempted", bool(checkpoint.get("emulator_replay")))
        validation.setdefault("status", checkpoint.get("emulator_replay_status", "unknown") or "unknown")
        validation.setdefault("engine", "emulator")
        validation.setdefault("replay_kind", "emulator_save_state")
        return validation
    if checkpoint.get("emulator_replay") or str(checkpoint.get("emulator_replay_status") or "") not in {"", "not_run"}:
        return {
            "attempted": bool(checkpoint.get("emulator_replay")),
            "status": str(checkpoint.get("emulator_replay_status") or "unknown"),
            "engine": "emulator",
            "replay_kind": "emulator_save_state",
            "source": checkpoint.get("source", ""),
            "checkpoint_kind": checkpoint.get("checkpoint_kind", ""),
        }
    return emulator_replay_not_run_validation()


def modeled_effect_span_base_fields() -> dict[str, Any]:
    return {
        "validation_kind": "modeled_effect_span",
        "validation_engine": "modeled_effect_span",
        "emulator_replay": False,
        "emulator_replay_status": "not_run",
        "emulator_replay_validation": emulator_replay_not_run_validation(),
    }


def bounded_effect_span_validation(
    *,
    entry: dict[str, Any],
    events: list[dict[str, Any]],
    checkpoint: dict[str, Any],
    last_write: dict[str, Any] | None,
) -> dict[str, Any]:
    if not last_write:
        return {
            "status": "no_observed_write",
            "validated": False,
            "consistent": False,
            **modeled_effect_span_base_fields(),
            "proof_status": "planned_only",
            "message": "No observed write is available for bounded effect-span validation.",
        }
    if not checkpoint.get("checkpointed"):
        return {
            "status": "no_checkpoint",
            "validated": False,
            "consistent": False,
            **modeled_effect_span_base_fields(),
            "proof_status": "planned_only",
            "message": "No retained checkpoint bounds this last-writer answer.",
        }
    if isinstance(checkpoint.get("modeled_effect_span"), dict):
        span = checkpoint["modeled_effect_span"]
    else:
        span = checkpoint.get("replay_span") if isinstance(checkpoint.get("replay_span"), dict) else {}
    from_seq = parse_int(span.get("from_seq"))
    to_seq = parse_int(span.get("to_seq"))
    if from_seq is None or to_seq is None:
        return {
            "status": "no_checkpoint",
            "validated": False,
            "consistent": False,
            **modeled_effect_span_base_fields(),
            "proof_status": "planned_only",
            "message": "Checkpoint effect span is missing a sequence boundary.",
        }
    trace_source = str(span.get("source") or checkpoint.get("trace_source") or "")
    checkpoint_context = bounded_span_checkpoint_context(checkpoint)
    writes: list[dict[str, Any]] = []
    read_count = 0
    final_value = ""
    for event in events:
        event_seq = parse_int(event.get("seq"))
        if event_seq is None or event_seq < from_seq or event_seq > to_seq:
            continue
        if trace_source and str(event.get("trace_source", "")) != trace_source:
            continue
        for item in dict_items(event.get("effects")):
            if not effect_matches_entry(entry, item):
                continue
            access = str(item.get("access", ""))
            if access == "read":
                read_count += 1
                continue
            if access != "write":
                continue
            write = {
                "seq": event_seq,
                "pc": event.get("pc_bank_address", ""),
                "pc_label": event.get("pc_label", ""),
                "operation": item.get("operation", ""),
                "address": item.get("address_hex", ""),
                "address_key": item.get("address_key", ""),
                "value_hex": item.get("value_hex", ""),
                "value_source": item.get("value_source", ""),
                "evidence_source": item.get("evidence_source", ""),
                "evidence_status": item.get("evidence_status", ""),
                "runtime_observation": item.get("runtime_observation", ""),
                "model_source": item.get("model_source", ""),
                "bank": item.get("bank"),
                "bank_source": item.get("bank_source", ""),
                "space": item.get("space", ""),
                "sram_enabled": item.get("sram_enabled"),
                "sram_enabled_source": item.get("sram_enabled_source", ""),
                "post_value_hex": item.get("post_value_hex", ""),
                "post_value_source": item.get("post_value_source", ""),
                "post_value_status": item.get("post_value_status", ""),
                "post_observed_seq": item.get("post_observed_seq"),
                "post_observed_pc": item.get("post_observed_pc", ""),
                "pre_registers": event.get("pre_registers", {}),
                "observed_memory": event.get("observed_memory", []),
                "bank_state": event.get("bank_state", {}),
                "bank_state_sources": event.get("bank_state_sources", {}),
                "bank_state_records": event.get("bank_state_records", []),
            }
            writes.append(write)
            if write["value_hex"]:
                final_value = str(write["value_hex"])
    expected_value = str(last_write.get("value_hex", ""))
    if not writes:
        return {
            "status": "no_write_in_span",
            "validated": False,
            "consistent": False,
            **modeled_effect_span_base_fields(),
            "proof_status": "planned_only",
            "trace_source": trace_source,
            "from_seq": from_seq,
            "to_seq": to_seq,
            "read_count": read_count,
            "write_count": 0,
            **checkpoint_context,
            "message": "The checkpoint-to-writer span did not contain a modeled write to this target.",
        }
    if not expected_value or not final_value:
        return {
            "status": "unknown_final_value",
            "validated": False,
            "consistent": False,
            **modeled_effect_span_base_fields(),
            "proof_status": "instruction_observed",
            "trace_source": trace_source,
            "from_seq": from_seq,
            "to_seq": to_seq,
            "read_count": read_count,
            "write_count": len(writes),
            "writes": writes[-8:],
            **checkpoint_context,
            "message": "The checkpoint-to-writer span contains the target write, but the final byte value is unknown.",
        }
    matched = final_value.upper() == expected_value.upper()
    return {
        "status": "effect_span_consistent" if matched else "effect_span_mismatch",
        "validated": False,
        "consistent": matched,
        **modeled_effect_span_base_fields(),
        "proof_status": "instruction_observed" if matched else "planned_only",
        "trace_source": trace_source,
        "from_seq": from_seq,
        "to_seq": to_seq,
        "instruction_span": to_seq - from_seq + 1,
        "read_count": read_count,
        "write_count": len(writes),
        "final_value_hex": final_value,
        "expected_value_hex": expected_value,
        "writes": writes[-8:],
        **checkpoint_context,
        "message": (
            "Modeled effects in the checkpoint-to-writer span are consistent with the reported final byte."
            if matched
            else "Modeled effects in the checkpoint-to-writer span are inconsistent with the reported final byte."
        ),
    }


def bounded_span_checkpoint_context(checkpoint: dict[str, Any]) -> dict[str, Any]:
    snapshot = checkpoint.get("checkpoint") if isinstance(checkpoint.get("checkpoint"), dict) else {}
    return {
        "checkpoint_kind": snapshot.get("checkpoint_kind", ""),
        "checkpoint_source": snapshot.get("checkpoint_source", ""),
        "checkpoint_emulator_replay": bool(snapshot.get("emulator_replay", False)),
        "checkpoint_emulator_replay_status": snapshot.get("emulator_replay_status", ""),
        "checkpoint_emulator_replay_validation": snapshot.get("emulator_replay_validation", {}),
        "checkpoint_pc": snapshot.get("pc", ""),
        "checkpoint_pc_label": snapshot.get("pc_label", ""),
        "checkpoint_bank_state": snapshot.get("bank_state", {}),
        "checkpoint_bank_state_sources": snapshot.get("bank_state_sources", {}),
        "checkpoint_bank_state_records": snapshot.get("bank_state_records", []),
        "checkpoint_registers": snapshot.get("registers", {}),
        "checkpoint_observed_memory": snapshot.get("observed_memory", []),
    }


def effect_matches_entry(entry: dict[str, Any], item: dict[str, Any]) -> bool:
    item_key = str(item.get("address_key", ""))
    entry_key = str(entry.get("address_key", ""))
    if item_key and entry_key and item_key == entry_key:
        return True
    if address_key_requires_exact_match(entry_key):
        return False
    return str(item.get("address_hex", "")).upper() == str(entry.get("address", "")).upper()


def compact_checkpoint(checkpoint: dict[str, Any]) -> dict[str, Any]:
    data = {
        "kind": checkpoint.get("kind", "trace_checkpoint"),
        "checkpoint_kind": checkpoint.get("checkpoint_kind", "pre_instruction_trace_frame"),
        "checkpoint_source": checkpoint.get("checkpoint_source", "instruction_trace"),
        "emulator_replay": bool(checkpoint.get("emulator_replay", False)),
        "emulator_replay_status": checkpoint.get("emulator_replay_status", "not_run"),
        "source": checkpoint.get("source", ""),
        "seq": checkpoint.get("seq"),
        "pc": checkpoint.get("pc_bank_address", ""),
        "pc_label": checkpoint.get("pc_label", ""),
        "registers": checkpoint.get("registers", {}),
        "bank_state": checkpoint.get("bank_state", {}),
        "bank_state_sources": checkpoint.get("bank_state_sources", {}),
        "bank_state_records": checkpoint.get("bank_state_records", []),
        "observed_memory": checkpoint.get("observed_memory", []),
    }
    replay_validation = checkpoint_emulator_replay_validation(checkpoint)
    if replay_validation.get("attempted") or replay_validation.get("status") not in {"", "not_run"}:
        data["emulator_replay_validation"] = replay_validation
    return data


def result_validation_routes(
    *,
    target: dict[str, Any],
    source: str,
    report: dict[str, Any],
    validation: dict[str, Any],
    symbols_path: str,
    watch_size: int,
) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    target_id = safe_target_id(target)
    query_args = target_query_args(target)
    watch_args = target_watch_args(target)
    if source and not source.startswith("<"):
        add_validation_route(
            routes,
            route_id="rerun_reverse_query",
            phase="validate",
            title="Re-run reverse query against the supplied effect report",
            command=" ".join(
                [
                    "python -m tools.debugger reverse-query",
                    "--report",
                    quote_arg(source),
                    "--symbols",
                    quote_arg(symbols_path),
                    *query_args,
                    "--watch-size",
                    str(watch_size),
                    "--json-out",
                    quote_arg(f".local\\tmp\\reverse_query_{target_id}.json"),
                ]
            ),
            produces=f".local\\tmp\\reverse_query_{target_id}.json",
            proof_status=str(validation.get("proof_status") or "planned_only"),
        )
    traces = unique_list(report.get("effective_traces") or report.get("requested_traces") or [])
    if traces:
        effect_out = f".local\\tmp\\reverse_query_{target_id}_effect_trace.json"
        effect_command = [
            "python -m tools.debugger effect-trace",
            "--symbols",
            quote_arg(symbols_path),
        ]
        for trace in traces[:4]:
            effect_command.extend(["--trace", quote_arg(trace)])
        effect_command.extend(watch_args)
        effect_command.extend(["--watch-size", str(watch_size), "--json-out", quote_arg(effect_out)])
        add_validation_route(
            routes,
            route_id="regenerate_effect_trace",
            phase="validate",
            title="Regenerate effect evidence from the original instruction trace",
            command=" ".join(effect_command),
            produces=effect_out,
            proof_status="instruction_observed",
        )
        add_validation_route(
            routes,
            route_id="rerun_reverse_query_from_regenerated_effect",
            phase="validate",
            title="Re-run reverse query against regenerated effect evidence",
            command=" ".join(
                [
                    "python -m tools.debugger reverse-query",
                    "--report",
                    quote_arg(effect_out),
                    "--symbols",
                    quote_arg(symbols_path),
                    *query_args,
                    "--watch-size",
                    str(watch_size),
                    "--json-out",
                    quote_arg(f".local\\tmp\\reverse_query_{target_id}_validated.json"),
                ]
            ),
            produces=f".local\\tmp\\reverse_query_{target_id}_validated.json",
            proof_status=str(validation.get("proof_status") or "planned_only"),
        )
    if not routes:
        add_validation_route(
            routes,
            route_id="capture_effect_trace",
            phase="validate",
            title="Capture an instruction trace before validating this reverse query",
            command=" ".join(
                [
                    "python -m tools.debugger trace-instructions",
                    "--save-state",
                    "<runtime-state>",
                    *watch_args,
                    "--out-trace",
                    "<instruction-trace.jsonl>",
                ]
            ),
            produces="<instruction-trace.jsonl>",
            proof_status="planned_only",
        )
    return routes


def add_validation_route(
    routes: list[dict[str, Any]],
    *,
    route_id: str,
    phase: str,
    title: str,
    command: str,
    produces: str,
    proof_status: str,
) -> None:
    runnable = command_is_runnable(command)
    status = "ready" if runnable else "planned"
    route_proof_status = "planned_only"
    routes.append(
        {
            "id": route_id,
            "phase": phase,
            "title": title,
            "command": command,
            "produces": produces,
            "runnable": runnable,
            "status": status,
            "proof_status": route_proof_status,
            "expected_proof_status": proof_status,
            "command_spec": validation_route_command_spec(
                command=command,
                produces=produces,
                runnable=runnable,
                status=status,
                actual_proof_status=route_proof_status,
                expected_proof_status=proof_status,
            ),
        }
    )


def validation_route_command_spec(
    *,
    command: str,
    produces: str,
    runnable: bool,
    status: str,
    actual_proof_status: str,
    expected_proof_status: str,
) -> dict[str, Any]:
    placeholders = command_placeholders(command)
    return {
        "kind": "command_spec",
        "schema_version": 1,
        "rendered": command,
        "argv": command_parts(command),
        "runnable": runnable,
        "status": status,
        "has_placeholders": bool(placeholders),
        "placeholders": placeholders,
        "required_inputs": command_required_inputs(command, placeholders=placeholders),
        "expected_outputs": [produces] if produces else [],
        "actual_proof_status": actual_proof_status,
        "expected_proof_status": expected_proof_status,
        "trust_checks": command_trust_checks(
            has_placeholders=bool(placeholders),
            runnable=runnable,
        ),
    }


def command_placeholders(command: str) -> list[str]:
    return unique_list(COMMAND_PLACEHOLDER_RE.findall(str(command)))


def command_required_inputs(command: str, *, placeholders: list[str]) -> list[str]:
    values = list(placeholders)
    for option in COMMAND_INPUT_OPTIONS:
        values.extend(command_option_values(command, option))
    return unique_list([value for value in values if value])


def command_trust_checks(*, has_placeholders: bool, runnable: bool) -> list[str]:
    checks: list[str] = []
    if has_placeholders:
        checks.append("placeholders must be replaced before execution")
    else:
        checks.append("command string parsed without placeholders")
    checks.append(
        "command_is_runnable accepted rendered command"
        if runnable
        else "command_is_runnable rejected rendered command"
    )
    checks.append("expected_proof_status describes the rerun target, not current evidence")
    return checks


def target_query_args(target: dict[str, Any]) -> list[str]:
    symbol = str(target.get("symbol") or "")
    if symbol:
        return ["--symbol", quote_arg(symbol)]
    return ["--address", command_address_text(target.get("cli") or target.get("address_hex") or "")]


def target_watch_args(target: dict[str, Any]) -> list[str]:
    symbol = str(target.get("symbol") or "")
    if symbol:
        return ["--watch-symbol", quote_arg(symbol)]
    return ["--watch-address", command_address_text(target.get("cli") or target.get("address_hex") or "")]


def safe_target_id(target: dict[str, Any]) -> str:
    text = str(target.get("symbol") or target.get("cli") or target.get("address_hex") or "target")
    out = []
    for char in text:
        out.append(char.lower() if char.isalnum() else "_")
    compact = "".join(out).strip("_")
    return compact[:48] or "target"


def matching_write_index_entries(target: dict[str, Any], raw_index: Any) -> list[dict[str, Any]]:
    entries = dict_items(raw_index)
    target_key = str(target.get("key", ""))
    target_address = str(target.get("address_hex", ""))
    exact = [entry for entry in entries if str(entry.get("address_key", "")) == target_key]
    if exact:
        return [
            matched_index_entry(
                entry,
                match_precision="exact_address_key" if target_requires_exact_key(target) else "bus_address",
                bank_match="exact" if target_requires_exact_key(target) else "not_required",
            )
            for entry in exact
        ]
    if target_requires_exact_key(target):
        return []
    bus_matches = [
        entry
        for entry in entries
        if str(entry.get("address", "")).upper() == target_address.upper()
    ]
    return annotate_bus_address_matches(bus_matches)


def annotate_bus_address_matches(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bank_qualified_keys = sorted({
        str(entry.get("address_key", ""))
        for entry in entries
        if address_key_requires_exact_match(str(entry.get("address_key", "")))
    })
    ambiguous_runtime_bank = len(bank_qualified_keys) > 1
    out: list[dict[str, Any]] = []
    for entry in entries:
        key = str(entry.get("address_key", ""))
        if address_key_requires_exact_match(key):
            out.append(
                matched_index_entry(
                    entry,
                    match_precision="bus_address_unverified_bank",
                    bank_match="ambiguous_runtime_bank" if ambiguous_runtime_bank else "bus_address_unverified_bank",
                    ambiguous_address_keys=bank_qualified_keys if ambiguous_runtime_bank else [],
                    proof_downgrade_reason=(
                        "unbanked target matched multiple bank-qualified runtime keys"
                        if ambiguous_runtime_bank
                        else "unbanked target matched a bank-qualified runtime key by bus address"
                    ),
                )
            )
        else:
            out.append(
                matched_index_entry(
                    entry,
                    match_precision="bus_address",
                    bank_match="not_required",
                    ambiguous_address_keys=[],
                )
            )
    return out


def matched_index_entry(
    entry: dict[str, Any],
    *,
    match_precision: str,
    bank_match: str,
    ambiguous_address_keys: list[str] | None = None,
    proof_downgrade_reason: str = "",
) -> dict[str, Any]:
    copied = dict(entry)
    copied["match_precision"] = match_precision
    copied["bank_match"] = bank_match
    copied["ambiguous_address_keys"] = unique_list(ambiguous_address_keys or [])
    copied["proof_downgrade_reason"] = proof_downgrade_reason
    return copied


def address_match_summary(*, target: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_address": str(target.get("address_hex", "")),
        "target_address_key": str(target.get("key") or target.get("address_key") or ""),
        "target_exact_key_required": target_requires_exact_key(target),
        "matched_address": str(entry.get("address", "")),
        "matched_address_key": str(entry.get("address_key", "")),
        "match_precision": str(entry.get("match_precision", "")),
        "bank_match": str(entry.get("bank_match", "")),
        "ambiguous_address_keys": string_items(entry.get("ambiguous_address_keys")),
        "proof_downgrade_reason": str(entry.get("proof_downgrade_reason", "")),
    }


def entry_history(entry: dict[str, Any], *, events: list[dict[str, Any]], max_history: int) -> list[dict[str, Any]]:
    address_key = str(entry.get("address_key", ""))
    address = str(entry.get("address", "")).upper()
    exact_key_required = address_key_requires_exact_match(address_key)
    history: list[dict[str, Any]] = []
    for event in events:
        for item in dict_items(event.get("effects")):
            item_key = str(item.get("address_key", ""))
            item_address = str(item.get("address_hex", "")).upper()
            if item_key != address_key and (exact_key_required or item_address != address):
                continue
            if item.get("access") not in {"read", "write"}:
                continue
            history.append(
                {
                    "seq": event.get("seq"),
                    "trace_source": event.get("trace_source", ""),
                    "pc": event.get("pc_bank_address", ""),
                    "pc_label": event.get("pc_label", ""),
                    "access": item.get("access", ""),
                    "kind": item.get("kind", ""),
                    "operation": item.get("operation", ""),
                    "address": item.get("address_hex", ""),
                    "address_key": item.get("address_key", ""),
                    "space": item.get("space", ""),
                    "bank": item.get("bank"),
                    "value_hex": item.get("value_hex", ""),
                    "value_source": item.get("value_source", ""),
                    "proof_status": item.get("proof_status", ""),
                    "proof_downgrade_reason": item.get("proof_downgrade_reason", ""),
                    "category": item.get("category", ""),
                    "hardware_model": item.get("hardware_model", ""),
                    "hardware_event_required": item.get("hardware_event_required", False),
                    "hardware_runtime_event": item.get("hardware_runtime_event", False),
                    "hardware_event_observed": item.get("hardware_event_observed", False),
                    "hardware_event_identity": item.get("hardware_event_identity", ""),
                    "hardware_event_labels": item.get("hardware_event_labels", []),
                    "hardware_runtime_event_source_fields": item.get("hardware_runtime_event_source_fields", []),
                    "hardware_generic_event_label_present": item.get("hardware_generic_event_label_present", False),
                    "hardware_event_type": item.get("hardware_event_type", ""),
                    "hardware_event_types": item.get("hardware_event_types", []),
                    "hardware_proof_gate": item.get("hardware_proof_gate", ""),
                    "evidence_source": item.get("evidence_source", ""),
                    "evidence_status": item.get("evidence_status", ""),
                    "runtime_observation": item.get("runtime_observation", ""),
                    "pre_state_sample": item.get("pre_state_sample", ""),
                    "pre_state_source": item.get("pre_state_source", ""),
                    "pre_state_value_hex": item.get("pre_state_value_hex", ""),
                    "pre_state_proof_status": item.get("pre_state_proof_status", ""),
                    "pre_state_validation": item.get("pre_state_validation", ""),
                    "pre_state_validation_kind": item.get("pre_state_validation_kind", ""),
                    "pre_state_validation_source": item.get("pre_state_validation_source", ""),
                    "pre_state_observation_model": item.get("pre_state_observation_model", ""),
                    "pre_state_proof_boundary": item.get("pre_state_proof_boundary", ""),
                    "pre_state_non_mutating_instruction_event": item.get("pre_state_non_mutating_instruction_event", ""),
                    "evidence_atoms": item.get("evidence_atoms", []),
                    "source_operands": item.get("source_operands", []),
                    "pre_registers": event.get("pre_registers", {}),
                    "observed_memory": event.get("observed_memory", []),
                }
            )
    if not history:
        history = normalize_index_history(entry, max_history=max_history)
    return history[-max_history:]


def normalize_index_history(entry: dict[str, Any], *, max_history: int) -> list[dict[str, Any]]:
    address = str(entry.get("address", "")).upper()
    address_key = str(entry.get("address_key", ""))
    normalized: list[dict[str, Any]] = []
    for item in dict_items(entry.get("history"))[-max_history:]:
        copied = dict(item)
        copied.setdefault("address", address)
        copied.setdefault("address_key", address_key)
        copied.setdefault("space", entry.get("space", ""))
        copied.setdefault("bank", entry.get("bank"))
        copied.setdefault("trace_source", entry.get("last_writer_trace_source", ""))
        copied.setdefault("source_operands", [])
        copied.setdefault("value_source", "")
        copied.setdefault("proof_status", "")
        copied.setdefault("proof_downgrade_reason", "")
        copied.setdefault("category", "")
        copied.setdefault("hardware_model", "")
        copied.setdefault("hardware_event_required", False)
        copied.setdefault("hardware_runtime_event", False)
        copied.setdefault("hardware_event_observed", False)
        copied.setdefault("hardware_event_identity", "")
        copied.setdefault("hardware_event_labels", [])
        copied.setdefault("hardware_runtime_event_source_fields", [])
        copied.setdefault("hardware_generic_event_label_present", False)
        copied.setdefault("hardware_event_type", "")
        copied.setdefault("hardware_event_types", [])
        copied.setdefault("hardware_proof_gate", "")
        copied.setdefault("pc_label", "")
        copied.setdefault("evidence_source", "")
        copied.setdefault("evidence_status", "")
        copied.setdefault("runtime_observation", "")
        if copied.get("history_source") in (None, ""):
            copied["history_source"] = entry.get("history_source", "")
        if copied.get("effect_trace_schema_version") in (None, ""):
            copied["effect_trace_schema_version"] = entry.get("effect_trace_schema_version", "")
        copied.setdefault("pre_state_sample", "")
        copied.setdefault("pre_state_source", "")
        copied.setdefault("pre_state_value_hex", "")
        copied.setdefault("pre_state_proof_status", "")
        copied.setdefault("pre_state_validation", "")
        copied.setdefault("pre_state_validation_kind", "")
        copied.setdefault("pre_state_validation_source", "")
        copied.setdefault("pre_state_observation_model", "")
        copied.setdefault("pre_state_proof_boundary", "")
        copied.setdefault("pre_state_non_mutating_instruction_event", "")
        normalized.append(copied)
    return normalized


def target_requires_exact_key(target: dict[str, Any]) -> bool:
    return address_spec_requires_exact_key(target)


def address_key_requires_exact_match(key: str) -> bool:
    return semantic_address_key_requires_exact_match(key)


def result_evidence(*, target: dict[str, Any], entry: dict[str, Any], last_write: dict[str, Any] | None) -> list[str]:
    evidence = [
        f"target={target.get('label', '')}",
        f"address={entry.get('address', '')}",
        f"address_key={entry.get('address_key', '')}",
        f"reads={entry.get('read_count', 0)}",
        f"writes={entry.get('write_count', 0)}",
        f"last_writer={last_write.get('pc', '') if last_write else entry.get('last_writer_pc', '')}",
        f"operation={last_write.get('operation', '') if last_write else ''}",
    ]
    if entry.get("match_precision"):
        evidence.append(f"match_precision={entry.get('match_precision', '')}")
    if entry.get("bank_match"):
        evidence.append(f"bank_match={entry.get('bank_match', '')}")
    ambiguous_address_keys = string_items(entry.get("ambiguous_address_keys"))
    if ambiguous_address_keys:
        evidence.append(f"ambiguous_address_keys={','.join(ambiguous_address_keys)}")
    if entry.get("proof_downgrade_reason"):
        evidence.append(f"proof_downgrade_reason={entry.get('proof_downgrade_reason', '')}")
    value_hex = str(last_write.get("value_hex", "") if last_write else entry.get("last_value_hex", ""))
    if value_hex:
        evidence.append(f"value=0x{value_hex}")
    value_source = str(last_write.get("value_source", "") if last_write else "")
    if value_source:
        evidence.append(f"value_source={value_source}")
    if last_write and last_write.get("proof_status"):
        evidence.append(f"effect_proof_status={last_write.get('proof_status', '')}")
    if last_write and last_write.get("hardware_model"):
        evidence.append(f"hardware_model={last_write.get('hardware_model', '')}")
    if last_write and last_write.get("hardware_event_required"):
        evidence.append(f"hardware_event_required={last_write.get('hardware_event_required')}")
    if last_write and last_write.get("hardware_runtime_event") not in {None, ""}:
        evidence.append(f"hardware_runtime_event={last_write.get('hardware_runtime_event')}")
    if last_write and last_write.get("hardware_event_identity"):
        evidence.append(f"hardware_event_identity={last_write.get('hardware_event_identity')}")
    if last_write and last_write.get("hardware_generic_event_label_present"):
        evidence.append(
            f"hardware_generic_event_label_present={last_write.get('hardware_generic_event_label_present')}"
        )
    if last_write and last_write.get("hardware_proof_gate"):
        evidence.append(f"hardware_proof_gate={last_write.get('hardware_proof_gate', '')}")
    if last_write and last_write.get("pre_state_sample"):
        evidence.extend(
            item
            for item in [
                f"pre_state_sample={last_write.get('pre_state_sample', '')}",
                f"pre_state_value=0x{last_write.get('pre_state_value_hex', '')}"
                if last_write.get("pre_state_value_hex")
                else "",
                f"pre_state_proof={last_write.get('pre_state_proof_status', '')}"
                if last_write.get("pre_state_proof_status")
                else "",
                f"pre_state_validation={last_write.get('pre_state_validation', '')}"
                if last_write.get("pre_state_validation")
                else "",
                f"pre_state_validation_source={last_write.get('pre_state_validation_source', '')}"
                if last_write.get("pre_state_validation_source")
                else "",
                f"pre_state_observation_model={last_write.get('pre_state_observation_model', '')}"
                if last_write.get("pre_state_observation_model")
                else "",
                f"pre_state_proof_boundary={last_write.get('pre_state_proof_boundary', '')}"
                if last_write.get("pre_state_proof_boundary")
                else "",
                f"pre_state_non_mutating_instruction_event={last_write.get('pre_state_non_mutating_instruction_event')}"
                if last_write.get("pre_state_non_mutating_instruction_event") not in {None, ""}
                else "",
            ]
            if item
        )
    if last_write:
        evidence.extend(pre_register_evidence(last_write.get("pre_registers")))
        evidence.extend(observed_memory_evidence(last_write.get("observed_memory")))
    return evidence


def pre_register_evidence(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    return [
        f"pre_{name}={value.get(name)}"
        for name in ("A", "F", "HL", "SP")
        if value.get(name) not in {None, ""}
    ]


def observed_memory_evidence(value: Any) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    evidence = []
    for item in value[:4]:
        if not isinstance(item, dict):
            continue
        address = str(item.get("address", ""))
        value_hex = str(item.get("value_hex", ""))
        if address and value_hex:
            evidence.append(f"observed_memory={address}:0x{value_hex}")
    return evidence


def result_commands(target: dict[str, Any]) -> list[str]:
    address = command_address_text(target.get("cli") or target.get("address_hex") or "")
    symbol = str(target.get("symbol") or "")
    commands = []
    if address:
        commands.append(f"python -m tools.debugger trace-index --address {address}")
        commands.append(f"python -m tools.debugger dynamic-taint --trace <instruction-trace.jsonl> --sink-address {address}")
    if symbol:
        commands.append(f"python -m tools.debugger explain --symbol {symbol}")
        commands.append(f"python -m tools.debugger slice --symbol {symbol}")
    return unique_list(commands)


def build_commands(
    *,
    targets: list[dict[str, Any]],
    reports: tuple[str, ...],
    traces: tuple[str, ...],
    symbols_path: str,
    watch_size: int,
) -> list[str]:
    commands = []
    if traces:
        base = ["python -m tools.debugger effect-trace"]
        for trace in traces[:4]:
            base.extend(["--trace", quote_arg(trace)])
        base.extend(["--symbols", quote_arg(symbols_path)])
        for target in targets[:6]:
            if target.get("symbol"):
                base.extend(["--watch-symbol", quote_arg(str(target["symbol"]))])
            elif target.get("cli"):
                base.extend(["--watch-address", command_address_text(target["cli"])])
        if watch_size != 1:
            base.extend(["--watch-size", str(watch_size)])
        commands.append(" ".join(base))
    for report in reports[:4]:
        commands.append(f"python -m tools.debugger rank --report {quote_arg(report)}")
    for target in targets[:6]:
        commands.extend(result_commands(target))
    return unique_list(commands)


def last_history_item(history: list[dict[str, Any]], *, access: str) -> dict[str, Any] | None:
    for item in reversed(history):
        if item.get("access") == access:
            return item
    return None


def parse_int(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    try:
        return int(str(value), 0)
    except ValueError:
        return None


def unique_targets(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for target in targets:
        key = str(target.get("key", "")) + ":" + str(target.get("symbol", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(target)
    return out


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list | tuple):
        return [item for item in value if isinstance(item, dict)]
    return []


def string_items(value: Any) -> list[str]:
    if isinstance(value, list | tuple | set):
        return unique_list(str(item) for item in value if str(item))
    if value in {None, ""}:
        return []
    return [str(value)]


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


def quote_arg(value: Any) -> str:
    text = str(value)
    if not text:
        return '""'
    if any(char.isspace() for char in text):
        return '"' + text.replace('"', '\\"') + '"'
    return text
