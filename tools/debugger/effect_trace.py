from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Any

from tools.damage_debugger.disasm import Instruction

from .address import AddressSpec, address_key, observed_address_key, parse_address_spec
from .catalog import ROOT
from .coverage import load_traces
from .dynamic_taint import (
    InstructionFrame,
    frame_condition_true,
    frame_flags,
    frame_register_known,
    parse_instruction_record,
    trace_records,
)
from .evidence import evidence_atom, merge_evidence_atoms
from .hardware_evidence import hardware_runtime_event_boundary
from .provenance import display_path, parse_symbol_table, resolve_path
from .reporting import load_reports
from .sm83_model import (
    CGB_VRAM_DMA_REGISTERS,
    INTERRUPT_FLAG_ADDRESS,
    INTERRUPT_VECTORS,
    SM83_MODEL_SOURCE,
    TIMER_TIMA_ADDRESS,
    TIMER_TMA_ADDRESS,
    accumulator_flag_semantics,
    add_hl_semantics,
    alu_semantics,
    cb_semantics,
    cpu_state_semantics,
    hardware_memory_bank,
    hardware_memory_bank_source,
    hardware_trigger_semantics,
    hli_hld_semantics,
    inc_dec_semantics,
    interrupt_entry_semantics,
    load_semantics,
    register_pair_inc_dec_semantics,
    sp_relative_semantics,
    stack_pop_register_value,
    stack_control_semantics,
    timer_overflow_semantics,
)


CONDITIONAL_CALLS = {0xC4: "nz", 0xCC: "z", 0xD4: "nc", 0xDC: "c"}
CONDITIONAL_RETS = {0xC0: "nz", 0xC8: "z", 0xD0: "nc", 0xD8: "c"}
CONDITIONAL_JUMPS = {0x20: "nz", 0x28: "z", 0x30: "nc", 0x38: "c", 0xC2: "nz", 0xCA: "z", 0xD2: "nc", 0xDA: "c"}
RST_TARGETS = {0xC7: 0x00, 0xCF: 0x08, 0xD7: 0x10, 0xDF: 0x18, 0xE7: 0x20, 0xEF: 0x28, 0xF7: 0x30, 0xFF: 0x38}
INDEX_REG = {0: "b", 1: "c", 2: "d", 3: "e", 4: "h", 5: "l", 6: "[hl]", 7: "a"}
CPU_STATE_OPCODES = {0x10, 0x76, 0xD9, 0xF3, 0xFB}
HARDWARE_EVENT_REQUIRED_MODELS = {
    "oam_dma",
    "cgb_vram_dma",
    "timer_tima_overflow",
    "interrupt_entry",
    "lcd_mode_edge",
    "ppu_lcd_mode",
}
def build_effect_trace_report(
    *,
    traces: tuple[str, ...] = (),
    reports: tuple[str, ...] = (),
    symbols_path: str = "pokegold.sym",
    watch_symbols: tuple[str, ...] = (),
    watch_addresses: tuple[str, ...] = (),
    watch_size: int = 1,
    out_effects: str = "",
    max_events: int = 5000,
    checkpoint_interval: int = 16,
    max_checkpoints: int = 128,
    root: Path = ROOT,
) -> dict[str, Any]:
    loaded_reports, report_errors = load_reports(reports=reports, root=root)
    discovered_traces = trace_paths_from_reports(loaded_reports)
    effective_traces = tuple(unique_list([*traces, *discovered_traces]))
    loaded_traces, trace_errors = load_traces(traces=effective_traces, root=root)
    sym_path = resolve_path(symbols_path, root=root)
    symbol_table = parse_symbol_table(sym_path) if sym_path.exists() else {}
    errors = [*report_errors, *trace_errors]
    if not effective_traces:
        errors.append("at least one --trace or trace-producing --report is required")
    if not sym_path.exists():
        errors.append(f"missing symbol file: {symbols_path}")
    if watch_size < 1:
        errors.append("--watch-size must be positive")
    if max_events < 1:
        errors.append("--max-events must be positive")
    if checkpoint_interval < 1:
        errors.append("--checkpoint-interval must be positive")
    if max_checkpoints < 1:
        errors.append("--max-checkpoints must be positive")

    watches, watch_errors = watch_specs(
        watch_symbols=watch_symbols,
        watch_addresses=watch_addresses,
        watch_size=watch_size,
        symbol_table=symbol_table,
    )
    errors.extend(watch_errors)

    events: list[dict[str, Any]] = []
    parse_errors: list[str] = []
    for loaded in loaded_traces:
        parsed_events, loaded_errors = effect_events_for_trace(
            loaded,
            watches=watches,
            max_events=max_events - len(events),
        )
        events.extend(parsed_events)
        parse_errors.extend(loaded_errors)
        if len(events) >= max_events:
            break
    hook_order_validations = hook_order_validations_from_reports(loaded_reports)
    hook_order_pre_state_proven = any(
        validation.get("passed") and validation.get("proof_status") == "runtime_observed"
        for validation in hook_order_validations
    )
    hook_order_boundary = aggregate_hook_order_boundary(hook_order_validations)
    attach_rmw_pre_state_proof(events, hook_order_validations)
    attach_observed_timer_overflow_effects(events)
    attach_hardware_side_effect_proof_gates(events)
    attach_next_frame_write_validation(events)
    refresh_watch_hits(events, watches)
    attach_effect_evidence_atoms(events)
    errors.extend(parse_errors[:20])
    write_index = build_write_index(events)
    side_effect_index = build_side_effect_index(events)
    trace_window = build_trace_window(
        loaded_traces,
        checkpoint_interval=checkpoint_interval if checkpoint_interval > 0 else 16,
        max_checkpoints=max_checkpoints if max_checkpoints > 0 else 128,
    )
    evidence_source_counts = count_effect_field_values(events, "evidence_source")
    evidence_status_counts = count_effect_field_values(events, "evidence_status")
    watch_bank_match_counts = count_watch_hit_field_values(events, "bank_match")
    output = write_effects_output(events=events, out_effects=out_effects, root=root)
    errors.extend(output.get("errors", []))
    return {
        "schema_version": 1,
        "kind": "unified_debugger_effect_trace",
        "root": str(root),
        "valid": not errors,
        "proof_status": "instruction_observed" if events else "planned_only",
        "error_count": len(errors),
        "errors": errors,
        "reports": [loaded["source"] for loaded in loaded_reports],
        "report_count": len(loaded_reports),
        "hook_order_validation_count": len(hook_order_validations),
        "hook_order_pre_state_proven": hook_order_pre_state_proven,
        "hook_order_proof_status": "runtime_observed" if hook_order_pre_state_proven else "planned_only",
        "hook_order_proof_boundary": hook_order_boundary.get("proof_boundary", ""),
        "hook_order_mechanisms": hook_order_boundary.get("hook_mechanisms", []),
        "hook_order_non_mutating_instruction_events": hook_order_boundary.get("non_mutating_instruction_events", ""),
        "hook_order_validations": hook_order_validations,
        "rmw_pre_state_sample_count": count_rmw_pre_state_samples(events),
        "rmw_pre_state_runtime_observed_count": count_rmw_pre_state_samples(events, proof_status="runtime_observed"),
        "rmw_pre_state_unvalidated_count": count_rmw_pre_state_samples(events, proof_status="planned_only"),
        "rmw_pre_state_validation_counts": count_rmw_pre_state_validation_values(events),
        "requested_traces": list(traces),
        "effective_traces": list(effective_traces),
        "trace_count": len(loaded_traces),
        "watch_symbols": list(watch_symbols),
        "watch_addresses": list(watch_addresses),
        "watch_size": watch_size,
        "checkpoint_interval": checkpoint_interval,
        "max_checkpoints": max_checkpoints,
        "watches": watches,
        "effect_event_count": len(events),
        "trace_window": trace_window,
        "trace_window_frame_count": trace_window.get("frame_count", 0),
        "trace_window_checkpoint_count": trace_window.get("checkpoint_count", 0),
        "memory_read_count": count_effects(events, "memory_read"),
        "memory_write_count": count_effects(events, "memory_write"),
        "stack_read_count": count_effects(events, "stack_read"),
        "stack_write_count": count_effects(events, "stack_write"),
        "io_read_count": count_effects(events, "io_read"),
        "io_write_count": count_effects(events, "io_write"),
        "register_write_count": count_effects(events, "register_write"),
        "control_effect_count": count_effects(events, "control_flow"),
        "unmodeled_effect_count": count_unmodeled_effects(events),
        "effect_proof_status_counts": count_effect_proof_statuses(events),
        "planned_only_effect_count": count_effects_by_proof_status(events, "planned_only"),
        "instruction_observed_effect_count": count_effects_by_proof_status(events, "instruction_observed"),
        "hardware_gated_effect_count": count_hardware_gated_effects(events),
        "hardware_runtime_event_effect_count": count_hardware_runtime_event_effects(events),
        "hardware_side_effect_count": count_side_effects(events),
        "dma_side_effect_count": count_side_effects(events, category="dma"),
        "dma_copy_read_count": count_effects(events, "dma_read"),
        "dma_copy_write_count": count_effects(events, "dma_write"),
        "bank_switch_side_effect_count": count_side_effects(events, category="banking"),
        "interrupt_entry_count": count_effects(events, "interrupt_entry"),
        "timer_overflow_count": count_effects(events, "timer_tima_overflow"),
        "timer_interrupt_request_count": count_effects(events, "timer_interrupt_request_write"),
        "watch_hit_count": count_watch_hits(events),
        "watch_read_count": count_watch_effects(events, access="read"),
        "watch_write_count": count_watch_effects(events, access="write"),
        "post_value_observed_count": count_effect_post_value_status(events),
        "post_value_match_count": count_effect_post_value_status(events, "matched"),
        "post_value_mismatch_count": count_effect_post_value_status(events, "mismatch"),
        "post_register_observed_count": count_effect_post_register_status(events),
        "post_register_match_count": count_effect_post_register_status(events, "matched"),
        "post_register_mismatch_count": count_effect_post_register_status(events, "mismatch"),
        "unmodeled_observed_change_count": count_unmodeled_observed_changes(events),
        "watch_bank_match_counts": watch_bank_match_counts,
        "bank_unverified_watch_hit_count": int(watch_bank_match_counts.get("bus_address_unverified_bank", 0)),
        "evidence_source_counts": evidence_source_counts,
        "evidence_status_counts": evidence_status_counts,
        "write_index": write_index,
        "side_effect_index": side_effect_index,
        "events": events[:max_events],
        "output": output,
        "known_limits": [
            "Effect traces are inferred from captured instruction frames; code outside the trace window is not observed.",
            "Effect traces now record CPU-visible reads/writes, byte-level values and value-source provenance for direct known writes and observed-memory read-modify-write attribution, stack transfers, IO loads/stores, control-flow, EI/DI/RETI IME changes, HALT/STOP CPU-state transitions, and common hardware-trigger side effects including OAM DMA triggers, modeled general-mode CGB VRAM DMA copies when setup writes are observed, DIV reset writes, adjacent-frame TIMA overflow reload/IF request candidates, MBC bank writes, WRAM/VRAM bank-select IO writes, PPU/audio/timer/interrupt register writes, and trace-inferred interrupt-entry stack pushes.",
            "DMA, timer-overflow, LCD-mode-edge, and interrupt-entry items are proof-gated: modeled or adjacent-frame evidence remains planned_only for strong attribution until an explicit runtime hardware-event source is attached.",
            "Register writes for memory-load and stack-pop instructions are modeled from pre-instruction frames and adjacent next-frame register snapshots when available; this is still bounded trace evidence, not complete CPU emulation.",
            "WRAM/VRAM/ROM/SRAM bank provenance is runtime-sampled when bank_state is present on instruction frames; otherwise effect tracing can carry bank state forward only from observed bank-register writes in the same captured trace window and labels that source as inferred_bank_state.",
            "OAM DMA triggers are expanded into modeled source reads and OAM writes for reverse queries; CGB VRAM general DMA is expanded only when FF51-FF55 setup writes are observed in the same trace window, while HBlank DMA and missing setup remain trigger-only. Interrupt entries are inferred only from adjacent PC/SP trace evidence. TIMA overflow reload/IF request effects are inferred only when adjacent captured pre-instruction frames observe TIMA=$FF, matching TMA reload, and the timer IF bit transition. PPU pixels, audio mixer output, and unobserved timer ticks still require richer emulator-backed capture unless those effects are present in the trace window.",
            "Trace-window checkpoints are pre-instruction register/bank/watch snapshots from the captured trace; they support modeled effect-span checks from a nearby checkpoint, not arbitrary emulator reverse execution.",
            "When adjacent captured instruction frames observe a modeled write address, the effect records whether the next pre-instruction snapshot confirmed the modeled byte value.",
            "Observed byte changes between adjacent captured frames that are not explained by a modeled write are reported as unattributed changes instead of being indexed as known writers.",
            "When an instruction is observed but required address/value registers are missing from the trace frame, the effect is reported as unmodeled_missing_register instead of silently disappearing or using default zero values.",
            "When hook-order probe reports are supplied, effect traces carry that runtime proof status so RMW byte attribution can be distinguished from unvalidated hook timing.",
            "Observed bus addresses are indexed separately from bank-qualified requested addresses so later runtime bank probes can attach exact WRAMX/SRAM/VRAM bank provenance.",
        ],
    }


def effect_events_for_trace(
    loaded: dict[str, Any],
    *,
    watches: list[dict[str, Any]],
    max_events: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    previous_instruction: Instruction | None = None
    previous_frame: InstructionFrame | None = None
    inferred_bank_state: dict[str, int] = {}
    hardware_state: dict[str, int] = {}
    for index, record in enumerate(trace_records(loaded["data"])):
        if len(events) >= max_events:
            break
        parsed = parse_instruction_record(record, default_seq=index)
        if parsed["error"]:
            errors.append(f"{loaded['source']}[{index}]: {parsed['error']}")
            continue
        instruction = parsed["instruction"]
        frame = parsed["frame"]
        inferred_bank_state = update_inferred_bank_state_from_frame(
            inferred_bank_state,
            frame,
        )
        frame = frame_with_inferred_bank_state(frame, inferred_bank_state)
        hardware_state = update_hardware_state_from_frame(hardware_state, frame)
        effects = instruction_effects(instruction, frame, hardware_state=hardware_state)
        if previous_instruction is not None and previous_frame is not None:
            effects = [
                *interrupt_entry_effects(
                    previous_instruction=previous_instruction,
                    previous_frame=previous_frame,
                    current_frame=frame,
                ),
                *effects,
            ]
        inferred_bank_state = update_inferred_bank_state_from_effects(
            inferred_bank_state,
            effects,
        )
        hardware_state = update_hardware_state_from_effects(hardware_state, effects)
        event = {
            "kind": "effect_trace_event",
            "trace_source": loaded["source"],
            "seq": int(frame.seq),
            "bank": int(frame.bank),
            "pc": int(frame.pc),
            "pc_bank_address": f"{int(frame.bank):02X}:{int(frame.pc):04X}",
            "pc_label": str(frame.pc_label),
            "opcode": int(instruction.opcode),
            "length": int(instruction.length),
            "mnemonic": str(instruction.mnemonic),
            "pre_registers": frame_registers(frame),
            "known_registers": list(frame.known_registers),
            "observed_memory": frame_observed_memory(frame),
            "effects": effects,
        }
        if frame.bank_state:
            event["bank_state"] = {key: value for key, value in frame.bank_state}
            event["bank_state_sources"] = frame_bank_state_sources(frame)
            event["bank_state_records"] = frame_bank_state_records(frame)
        event["watch_hits"] = watch_hits(effects, watches)
        events.append(event)
        previous_instruction = instruction
        previous_frame = frame
    return events, errors


def attach_next_frame_write_validation(events: list[dict[str, Any]]) -> None:
    for index, event in enumerate(events[:-1]):
        next_event = events[index + 1]
        if not adjacent_trace_events(event, next_event):
            continue
        current_observed = observed_memory_by_address(event.get("observed_memory"))
        observed = observed_memory_by_address(next_event.get("observed_memory"))
        matched = 0
        mismatched = 0
        observed_count = 0
        modeled_write_addresses: set[str] = set()
        if observed:
            for item in event.get("effects", []):
                if item.get("access") != "write":
                    continue
                address = str(item.get("address_hex", "")).upper()
                if address:
                    modeled_write_addresses.add(address)
                if not address or address not in observed:
                    continue
                observed_value = observed[address]
                status = post_value_status(
                    expected=str(item.get("value_hex", "")),
                    observed=observed_value,
                )
                item["post_value_hex"] = observed_value
                item["post_value_source"] = "next_instruction_pre_state"
                item["post_value_status"] = status
                item["post_observed_seq"] = next_event.get("seq")
                item["post_observed_pc"] = next_event.get("pc_bank_address", "")
                observed_count += 1
                if status == "matched":
                    matched += 1
                elif status == "mismatch":
                    mismatched += 1
            if observed_count:
                ensure_next_observed_state(event, next_event)
                event["post_value_validation"] = {
                    "source": "next_instruction_pre_state",
                    "observed_write_count": observed_count,
                    "matched_count": matched,
                    "mismatch_count": mismatched,
                }
            unmodeled = unmodeled_observed_changes(
                event=event,
                next_event=next_event,
                current=current_observed,
                next_observed=observed,
                modeled_write_addresses=modeled_write_addresses,
            )
            if unmodeled:
                event["unmodeled_observed_changes"] = unmodeled
                summary = event.setdefault(
                    "post_value_validation",
                    {
                        "source": "next_instruction_pre_state",
                        "observed_write_count": observed_count,
                        "matched_count": matched,
                        "mismatch_count": mismatched,
                    },
                )
                summary["unmodeled_change_count"] = len(unmodeled)
        attach_next_frame_register_validation(event, next_event)


def attach_observed_timer_overflow_effects(events: list[dict[str, Any]]) -> None:
    for index, event in enumerate(events[:-1]):
        next_event = events[index + 1]
        if not adjacent_trace_events(event, next_event):
            continue
        effects = observed_timer_overflow_effects(event, next_event)
        if not effects:
            continue
        event.setdefault("effects", []).extend(effects)
        event["timer_overflow_observation"] = {
            "source": "adjacent_instruction_pre_state",
            "next_seq": next_event.get("seq"),
            "next_pc": next_event.get("pc_bank_address", ""),
            "effect_count": len(effects),
        }


def observed_timer_overflow_effects(event: dict[str, Any], next_event: dict[str, Any]) -> list[dict[str, Any]]:
    if event_writes_any_address(event, {"FF05", "FF06", "FF07", "FF0F"}):
        return []
    current = observed_memory_by_address(event.get("observed_memory"))
    observed = observed_memory_by_address(next_event.get("observed_memory"))
    current_tima = observed_byte(current, TIMER_TIMA_ADDRESS)
    current_tma = observed_byte(current, TIMER_TMA_ADDRESS)
    current_if = observed_byte(current, INTERRUPT_FLAG_ADDRESS)
    next_tima = observed_byte(observed, TIMER_TIMA_ADDRESS)
    next_if = observed_byte(observed, INTERRUPT_FLAG_ADDRESS)
    if None in {current_tima, current_tma, current_if, next_tima, next_if}:
        return []
    model = timer_overflow_semantics()
    if not model.observed_reload_and_interrupt(
        current_tima=current_tima,
        current_tma=current_tma,
        next_tima=next_tima,
        current_if=current_if,
        next_if=next_if,
    ):
        return []
    base = {
        "category": "timer",
        "hardware_model": model.hardware_model,
        "evidence_source": "observed_adjacent_timer_overflow",
        "evidence_status": "observed_hardware_side_effect",
        "runtime_observation": "adjacent_instruction_pre_state",
        "model_source": SM83_MODEL_SOURCE,
        "trigger_address": f"{TIMER_TIMA_ADDRESS:04X}",
        "trigger_address_key": effect_address_key("timer_tima", TIMER_TIMA_ADDRESS, bank=None),
        "old_tima_hex": f"{current_tima:02X}",
        "tma_hex": f"{current_tma:02X}",
        "old_if_hex": f"{current_if:02X}",
        "new_if_hex": f"{next_if:02X}",
        "timer_interrupt_bit": model.interrupt_bit,
        "timer_interrupt_mask": f"{model.interrupt_mask:02X}",
        "modeled_from_trigger": True,
    }
    side = {
        "kind": model.side_effect_kind,
        "access": "side_effect",
        "operation": model.operation,
        **base,
    }
    reload_write = effect(
        model.reload_write_kind,
        TIMER_TIMA_ADDRESS,
        operation=model.reload_operation,
        source=memory_operand(TIMER_TMA_ADDRESS, value=current_tma, value_source="observed_memory_snapshot"),
        value=next_tima,
        value_source="observed_tma_reload",
    )
    reload_write.update(
        {
            **base,
            "old_value_hex": f"{current_tima:02X}",
            "post_value_expected_source": "adjacent_instruction_pre_state",
        }
    )
    if_write = effect(
        model.interrupt_write_kind,
        INTERRUPT_FLAG_ADDRESS,
        operation=model.interrupt_operation,
        source=memory_operand(INTERRUPT_FLAG_ADDRESS, value=current_if, value_source="observed_memory_snapshot"),
        value=next_if,
        value_source="observed_timer_interrupt_request",
    )
    if_write.update(
        {
            **base,
            "trigger_address": f"{INTERRUPT_FLAG_ADDRESS:04X}",
            "trigger_address_key": effect_address_key("timer_interrupt", INTERRUPT_FLAG_ADDRESS, bank=None),
            "old_value_hex": f"{current_if:02X}",
            "post_value_expected_source": "adjacent_instruction_pre_state",
        }
    )
    return [side, reload_write, if_write]


def attach_hardware_side_effect_proof_gates(events: list[dict[str, Any]]) -> None:
    for event in events:
        for item in dict_items(event.get("effects")):
            if not hardware_side_effect_requires_runtime_event(item):
                continue
            boundary = hardware_runtime_event_boundary(item)
            runtime_event = bool(boundary["runtime_event_present"])
            item["hardware_event_required"] = True
            item["hardware_runtime_event"] = runtime_event
            item["hardware_event_identity"] = boundary["hardware_event_identity"]
            item["hardware_event_labels"] = boundary["hardware_event_labels"]
            item["hardware_runtime_event_source_fields"] = boundary["hardware_runtime_event_source_fields"]
            item["hardware_generic_event_label_present"] = boundary["hardware_generic_event_label_present"]
            if boundary["hardware_event_types"]:
                item["hardware_event_types"] = boundary["hardware_event_types"]
            item["hardware_proof_gate"] = (
                "explicit_runtime_event_present"
                if runtime_event
                else "explicit_runtime_event_missing"
            )
            if runtime_event:
                item.setdefault("proof_status", "instruction_observed")
                continue
            item["proof_status"] = "planned_only"
            reason = hardware_side_effect_downgrade_reason(item)
            item["proof_downgrade_reason"] = reason
            if item.get("access") == "write":
                item["target_match_proof_status"] = "planned_only"


def hardware_side_effect_requires_runtime_event(item: dict[str, Any]) -> bool:
    model = str(item.get("hardware_model") or "")
    if model in HARDWARE_EVENT_REQUIRED_MODELS:
        return True
    kind = str(item.get("kind") or "")
    if kind in {
        "dma_read",
        "dma_write",
        "timer_tima_overflow",
        "timer_tima_reload_write",
        "timer_interrupt_request_write",
        "interrupt_entry",
    }:
        return True
    return False


def hardware_side_effect_downgrade_reason(item: dict[str, Any]) -> str:
    model = str(item.get("hardware_model") or item.get("kind") or "hardware_side_effect")
    return f"{model}_requires_explicit_runtime_event"


def event_writes_any_address(event: dict[str, Any], addresses: set[str]) -> bool:
    for item in event.get("effects", []):
        if item.get("access") != "write":
            continue
        if str(item.get("address_hex", "")).upper() in addresses:
            return True
    return False


def observed_byte(observed: dict[str, str], address: int) -> int | None:
    text = observed.get(f"{address & 0xFFFF:04X}")
    if not text:
        return None
    try:
        return int(str(text).replace("$", ""), 16) & 0xFF
    except ValueError:
        return None


def refresh_watch_hits(events: list[dict[str, Any]], watches: list[dict[str, Any]]) -> None:
    for event in events:
        event["watch_hits"] = watch_hits(event.get("effects", []), watches)


def ensure_next_observed_state(event: dict[str, Any], next_event: dict[str, Any]) -> None:
    event.setdefault(
        "next_observed_state",
        {
            "seq": next_event.get("seq"),
            "pc_bank_address": next_event.get("pc_bank_address", ""),
            "pc_label": next_event.get("pc_label", ""),
            "pre_registers": next_event.get("pre_registers", {}),
            "observed_memory": next_event.get("observed_memory", []),
        },
    )


def attach_next_frame_register_validation(event: dict[str, Any], next_event: dict[str, Any]) -> None:
    registers = next_event.get("pre_registers") if isinstance(next_event.get("pre_registers"), dict) else {}
    if not registers:
        return
    matched = 0
    mismatched = 0
    observed_count = 0
    for item in event.get("effects", []):
        if item.get("access") != "register_write":
            continue
        register = str(item.get("register", "")).upper()
        observed_value = observed_register_value(registers, register)
        if not register or not observed_value:
            continue
        status = post_value_status(expected=str(item.get("value_hex", "")), observed=observed_value)
        item["post_register_hex"] = observed_value
        item["post_register_source"] = "next_instruction_pre_state"
        item["post_register_status"] = status
        item["post_observed_seq"] = next_event.get("seq")
        item["post_observed_pc"] = next_event.get("pc_bank_address", "")
        observed_count += 1
        if status == "matched":
            matched += 1
        elif status == "mismatch":
            mismatched += 1
    if not observed_count:
        return
    ensure_next_observed_state(event, next_event)
    event["post_register_validation"] = {
        "source": "next_instruction_pre_state",
        "observed_register_write_count": observed_count,
        "matched_count": matched,
        "mismatch_count": mismatched,
    }


def unmodeled_observed_changes(
    *,
    event: dict[str, Any],
    next_event: dict[str, Any],
    current: dict[str, str],
    next_observed: dict[str, str],
    modeled_write_addresses: set[str],
) -> list[dict[str, Any]]:
    changes = []
    for address, old_value in sorted(current.items()):
        if address in modeled_write_addresses:
            continue
        new_value = next_observed.get(address)
        if not new_value or new_value == old_value:
            continue
        changes.append(
            {
                "address": address,
                "old_value_hex": old_value,
                "new_value_hex": new_value,
                "source": "adjacent_instruction_pre_state",
                "status": "unattributed",
                "seq": event.get("seq"),
                "pc": event.get("pc_bank_address", ""),
                "pc_label": event.get("pc_label", ""),
                "next_seq": next_event.get("seq"),
                "next_pc": next_event.get("pc_bank_address", ""),
                "next_pc_label": next_event.get("pc_label", ""),
                "message": "Observed byte changed by the next captured frame but no modeled write effect in this frame explains it.",
            }
        )
    return changes


def observed_register_value(registers: dict[str, Any], register: str) -> str:
    register = register.upper()
    if register in registers and registers.get(register) not in {None, ""}:
        return normalized_register_hex(registers.get(register), register_width(register))
    pairs = {
        "AF": ("A", "F"),
        "BC": ("B", "C"),
        "DE": ("D", "E"),
    }
    if register in pairs:
        high, low = pairs[register]
        if registers.get(high) in {None, ""} or registers.get(low) in {None, ""}:
            return ""
        return normalized_register_hex(f"{registers.get(high)}{registers.get(low)}", 4)
    return ""


def normalized_register_hex(value: Any, width: int) -> str:
    text = str(value).strip().replace("$", "").replace("0x", "").replace("0X", "").replace(" ", "")
    if not text:
        return ""
    try:
        parsed = int(text, 16)
    except ValueError:
        return ""
    mask = (1 << (width * 4)) - 1
    return f"{parsed & mask:0{width}X}"


def adjacent_trace_events(event: dict[str, Any], next_event: dict[str, Any]) -> bool:
    if str(event.get("trace_source", "")) != str(next_event.get("trace_source", "")):
        return False
    seq = int_or_none(event.get("seq"))
    next_seq = int_or_none(next_event.get("seq"))
    if seq is None or next_seq != seq + 1:
        return False
    pc = int_or_none(event.get("pc"))
    bank = int_or_none(event.get("bank"))
    length = int_or_none(event.get("length"))
    next_pc = int_or_none(next_event.get("pc"))
    next_bank = int_or_none(next_event.get("bank"))
    if pc is None or bank is None or length is None or next_pc is None or next_bank is None:
        return False
    if next_bank != bank or next_pc != ((pc + max(1, length)) & 0xFFFF):
        return False
    return not event_takes_control_flow(event)


def event_takes_control_flow(event: dict[str, Any]) -> bool:
    opcode = int_or_none(event.get("opcode"))
    if opcode is None:
        return True
    if opcode in {0xC3, 0x18, 0xE9, 0xCD, 0xC9, 0xD9, 0x76, 0x10} or opcode in RST_TARGETS:
        return True
    flags = event_flags(event)
    if flags is None:
        if opcode in CONDITIONAL_JUMPS or opcode in CONDITIONAL_CALLS or opcode in CONDITIONAL_RETS:
            return True
        return False
    if opcode in CONDITIONAL_JUMPS:
        return condition_true(CONDITIONAL_JUMPS[opcode], flags)
    if opcode in CONDITIONAL_CALLS:
        return condition_true(CONDITIONAL_CALLS[opcode], flags)
    if opcode in CONDITIONAL_RETS:
        return condition_true(CONDITIONAL_RETS[opcode], flags)
    return False


def event_flags(event: dict[str, Any]) -> int | None:
    known_registers = {str(item).upper() for item in event.get("known_registers", [])}
    if "F" not in known_registers:
        return None
    registers = event.get("pre_registers") if isinstance(event.get("pre_registers"), dict) else {}
    value = registers.get("F")
    if isinstance(value, int):
        return value & 0xFF
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return int(text.replace("$", ""), 16) & 0xFF
    except ValueError:
        return None


def observed_memory_by_address(value: Any) -> dict[str, str]:
    observed: dict[str, str] = {}
    if not isinstance(value, list):
        return observed
    for item in value:
        if not isinstance(item, dict):
            continue
        address = str(item.get("address", "")).upper()
        byte = str(item.get("value_hex", "")).upper()
        if address and byte:
            observed[address] = byte
    return observed


def post_value_status(*, expected: str, observed: str) -> str:
    if not expected:
        return "observed_without_modeled_value"
    return "matched" if expected.upper() == observed.upper() else "mismatch"


def int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def instruction_effects(
    instruction: Instruction,
    frame: InstructionFrame,
    *,
    hardware_state: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    effects = opcode_fetch_effects(instruction, frame)
    effects.extend(attach_frame_bank_state(memory_read_effects(instruction, frame), frame))
    effects.extend(attach_frame_bank_state(register_write_effects(instruction, frame), frame))
    write_effects = attach_frame_bank_state(memory_write_effects(instruction, frame), frame)
    effects.extend(write_effects)
    effects.extend(hardware_side_effects(write_effects, hardware_state=hardware_state or {}))
    effects.extend(control_effects(instruction, frame))
    return effects


def opcode_fetch_effects(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    observed_bytes = [int(instruction.opcode) & 0xFF, *[int(value) & 0xFF for value in instruction.operand]]
    out = []
    for offset in range(max(1, int(instruction.length))):
        value = observed_bytes[offset] if offset < len(observed_bytes) else None
        out.append(
            effect(
                "rom_read",
                frame.pc + offset,
                operation="opcode_fetch",
                bank=frame.bank,
                width=1,
                value=value,
            )
        )
    return out


BANK_STATE_KEYS = {
    "wram",
    "wram_raw",
    "vram",
    "vram_raw",
    "rom",
    "rom_raw",
    "loaded_rom",
    "sram",
    "sram_raw",
    "sram_enabled",
    "sram_enable_raw",
    "sram_rtc_select",
}

BANK_STATE_VALID_SPACES = {
    "wram": ("wramx",),
    "wram_raw": ("wramx",),
    "vram": ("vram",),
    "vram_raw": ("vram",),
    "rom": ("romx",),
    "rom_raw": ("romx",),
    "loaded_rom": ("romx",),
    "sram": ("sram",),
    "sram_raw": ("sram",),
    "sram_enabled": ("sram",),
    "sram_enable_raw": ("sram",),
    "sram_rtc_select": ("sram",),
}


def update_inferred_bank_state_from_frame(
    inferred: dict[str, int],
    frame: InstructionFrame,
) -> dict[str, int]:
    state = dict(inferred)
    for key, value in frame.bank_state:
        if key in BANK_STATE_KEYS:
            state[key] = int(value) & 0xFF
    return state


def frame_with_inferred_bank_state(
    frame: InstructionFrame,
    inferred: dict[str, int],
) -> InstructionFrame:
    if not inferred:
        return frame
    state = {str(key): int(value) & 0xFF for key, value in frame.bank_state}
    changed = False
    for key, value in sorted(inferred.items()):
        if key not in BANK_STATE_KEYS or key in state:
            continue
        state[key] = int(value) & 0xFF
        state[f"{key}_inferred"] = 1
        changed = True
    if not changed:
        return frame
    return replace(frame, bank_state=tuple((key, state[key]) for key in sorted(state)))


def update_inferred_bank_state_from_effects(
    inferred: dict[str, int],
    effects: list[dict[str, Any]],
) -> dict[str, int]:
    state = dict(inferred)
    for item in effects:
        if item.get("kind") not in {"memory_write", "io_write"}:
            continue
        try:
            address = int(item.get("address", -1)) & 0xFFFF
        except (TypeError, ValueError):
            continue
        value = source_operand_value(item)
        if value is None:
            continue
        apply_bank_write(state, address=address, value=value)
    return state


def update_hardware_state_from_frame(
    state: dict[str, int],
    frame: InstructionFrame,
) -> dict[str, int]:
    out = dict(state)
    for key, value in frame.bank_state:
        if key in BANK_STATE_KEYS:
            out[key] = int(value) & 0xFF
    return out


def update_hardware_state_from_effects(
    state: dict[str, int],
    effects: list[dict[str, Any]],
) -> dict[str, int]:
    out = dict(state)
    for item in effects:
        if item.get("kind") not in {"memory_write", "io_write"}:
            continue
        try:
            address = int(item.get("address", -1)) & 0xFFFF
        except (TypeError, ValueError):
            continue
        value = source_operand_value(item)
        if value is None:
            continue
        if address in CGB_VRAM_DMA_REGISTERS:
            out[CGB_VRAM_DMA_REGISTERS[address]] = value
        apply_bank_write(out, address=address, value=value)
    return out


def apply_bank_write(state: dict[str, int], *, address: int, value: int) -> None:
    address &= 0xFFFF
    value &= 0xFF
    if address == 0xFF4F:
        state["vram"] = value & 0x01
        state["vram_raw"] = value
        return
    if address == 0xFF70:
        bank = value & 0x07
        state["wram"] = bank if bank else 1
        state["wram_raw"] = value
        return
    if 0x0000 <= address <= 0x1FFF:
        state["sram_enabled"] = 1 if (value & 0x0F) == 0x0A else 0
        state["sram_enable_raw"] = value
        return
    if 0x2000 <= address <= 0x3FFF:
        bank = value & 0x7F
        state["rom"] = bank if bank else 1
        state["rom_raw"] = value
        return
    if 0x4000 <= address <= 0x5FFF:
        state["sram_raw"] = value
        if value <= 0x03:
            state["sram"] = value
            state.pop("sram_rtc_select", None)
        elif 0x08 <= value <= 0x0C:
            state["sram_rtc_select"] = value
            state.pop("sram", None)


def memory_read_effects(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    op = int(instruction.opcode)
    if op == 0x0A:
        model = load_semantics(op)
        address = pair_value_if_known(frame, "bc")
        if address is None:
            item = unmodeled_effect("unmodeled_memory_read", model.operation, missing_registers=missing_registers_for_pair(frame, "bc"), address_source=model.address_source)
            item["model_source"] = SM83_MODEL_SOURCE
            return [item]
        item = read_effect("memory_read", address, operation=model.operation, frame=frame)
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op == 0x1A:
        model = load_semantics(op)
        address = pair_value_if_known(frame, "de")
        if address is None:
            item = unmodeled_effect("unmodeled_memory_read", model.operation, missing_registers=missing_registers_for_pair(frame, "de"), address_source=model.address_source)
            item["model_source"] = SM83_MODEL_SOURCE
            return [item]
        item = read_effect("memory_read", address, operation=model.operation, frame=frame)
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op in {0x2A, 0x3A}:
        address = pair_value_if_known(frame, "hl")
        if address is None:
            return [
                unmodeled_effect(
                    "unmodeled_memory_read",
                    hli_hld_semantics(op).memory_operation,
                    missing_registers=missing_registers_for_pair(frame, "hl"),
                    address_source="hl",
                )
            ]
        item = read_effect("memory_read", address, operation=hli_hld_semantics(op).memory_operation, frame=frame)
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if 0x40 <= op <= 0x7F and op != 0x76 and INDEX_REG[op & 0x07] == "[hl]":
        model = load_semantics(op)
        address = pair_value_if_known(frame, "hl")
        if address is None:
            item = unmodeled_effect("unmodeled_memory_read", model.operation, missing_registers=missing_registers_for_pair(frame, "hl"), address_source=model.address_source)
            item["model_source"] = SM83_MODEL_SOURCE
            return [item]
        item = read_effect("memory_read", address, operation=model.operation, frame=frame)
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if 0x80 <= op <= 0xBF and INDEX_REG[op & 0x07] == "[hl]":
        address = pair_value_if_known(frame, "hl")
        if address is None:
            return [unmodeled_effect("unmodeled_memory_read", "alu a, [hl]", missing_registers=missing_registers_for_pair(frame, "hl"), address_source="hl")]
        return [read_effect("memory_read", address, operation="alu a, [hl]", frame=frame)]
    if op in {0x34, 0x35}:
        model = inc_dec_semantics(op)
        address = pair_value_if_known(frame, "hl")
        if address is None:
            item = unmodeled_effect("unmodeled_memory_read", model.operation, missing_registers=missing_registers_for_pair(frame, "hl"), address_source="hl")
            item["model_source"] = SM83_MODEL_SOURCE
            return [item]
        item = read_effect("memory_read", address, operation=model.operation, frame=frame)
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op == 0xFA:
        model = load_semantics(op)
        address = u16_from_operand(instruction)
        item = read_effect("memory_read", address, operation=model.operation, frame=frame)
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op == 0xF0 and instruction.operand:
        model = load_semantics(op)
        address = 0xFF00 + int(instruction.operand[0])
        item = read_effect("io_read", address, operation=model.operation, frame=frame)
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op == 0xF2:
        model = load_semantics(op)
        c = reg_value_if_known(frame, "c")
        if c is None:
            item = unmodeled_effect("unmodeled_io_read", model.operation, missing_registers=["C"], address_source=model.address_source)
            item["model_source"] = SM83_MODEL_SOURCE
            return [item]
        address = 0xFF00 + c
        item = read_effect("io_read", address, operation=model.operation, frame=frame)
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op == 0xCB and instruction.operand and cb_semantics(int(instruction.operand[0])).is_memory_target:
        model = cb_semantics(int(instruction.operand[0]))
        address = pair_value_if_known(frame, "hl")
        if address is None:
            item = unmodeled_effect("unmodeled_memory_read", model.operation(), missing_registers=missing_registers_for_pair(frame, "hl"), address_source="hl")
            item["model_source"] = SM83_MODEL_SOURCE
            return [item]
        item = read_effect("memory_read", address, operation=model.operation(), frame=frame)
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op in {0xC1, 0xD1, 0xE1, 0xF1}:
        sp = pair_value_if_known(frame, "sp")
        model = stack_control_semantics(op)
        if sp is None:
            return [unmodeled_effect("unmodeled_stack_read", model.stack_read_operation, missing_registers=["SP"], address_source="sp")]
        low = read_effect("stack_read", sp, operation=f"{model.stack_read_operation} low", frame=frame)
        high = read_effect("stack_read", sp + 1, operation=f"{model.stack_read_operation} high", frame=frame)
        low["model_source"] = SM83_MODEL_SOURCE
        high["model_source"] = SM83_MODEL_SOURCE
        return [
            low,
            high,
        ]
    if op in {0xC9, 0xD9} or (op in CONDITIONAL_RETS and frame_condition_true(frame, CONDITIONAL_RETS[op])):
        sp = pair_value_if_known(frame, "sp")
        model = stack_control_semantics(op)
        if sp is None:
            return [unmodeled_effect("unmodeled_stack_read", model.stack_read_operation, missing_registers=["SP"], address_source="sp")]
        low = read_effect("stack_read", sp, operation=f"{model.stack_read_operation} low", frame=frame)
        high = read_effect("stack_read", sp + 1, operation=f"{model.stack_read_operation} high", frame=frame)
        low["model_source"] = SM83_MODEL_SOURCE
        high["model_source"] = SM83_MODEL_SOURCE
        return [
            low,
            high,
        ]
    return []


def register_write_effects(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    op = int(instruction.opcode)
    if op in {0xAF, 0x97}:
        operation = "xor a" if op == 0xAF else "sub a"
        return [register_write_effect("A", operation, source_operands=[constant_operand(0, value_source="modeled_zero_idiom")], value=0, value_source="modeled_zero_idiom")]
    if op in {0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E}:
        model = load_semantics(op)
        target = model.register_target
        value = int(instruction.operand[0]) & 0xFF if instruction.operand else None
        operands = [immediate_byte_operand(value)] if value is not None else []
        item = register_write_effect(target, model.operation, source_operands=operands, value=value, value_source="instruction_operand" if value is not None else "")
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op in {0x01, 0x11, 0x21, 0x31}:
        model = load_semantics(op)
        target = model.register_target
        value = u16_from_operand(instruction)
        item = register_write_effect(target, model.operation, source_operands=[immediate_operand(value)], value=value, value_source="instruction_operand")
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op == 0xF9:
        model = load_semantics(op)
        value = pair_value_if_known(frame, "hl")
        item = register_write_effect(model.register_target, model.operation, source_operands=[register_operand(model.register_source, frame)], value=value, value_source="pre_register" if value is not None else "")
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op == 0xF8 and instruction.operand:
        return ld_hl_sp_e8_register_writes(instruction, frame)
    try:
        add_hl_semantics(op)
        return add_hl_register_writes(frame, op)
    except ValueError:
        pass
    if op == 0xE8 and instruction.operand:
        return add_sp_e8_register_writes(instruction, frame)
    if op in {0xC5, 0xD5, 0xE5, 0xF5}:
        model = stack_control_semantics(op)
        return [sp_delta_register_write(frame, model.sp_write_operation, model.sp_delta, model_source=SM83_MODEL_SOURCE)]
    if op == 0xCD or (op in CONDITIONAL_CALLS and frame_condition_true(frame, CONDITIONAL_CALLS[op])):
        model = stack_control_semantics(op)
        return [sp_delta_register_write(frame, model.sp_write_operation, model.sp_delta, model_source=SM83_MODEL_SOURCE)]
    if op in RST_TARGETS:
        model = stack_control_semantics(op)
        return [sp_delta_register_write(frame, model.sp_write_operation, model.sp_delta, model_source=SM83_MODEL_SOURCE)]
    if op in {0xC9, 0xD9} or (op in CONDITIONAL_RETS and frame_condition_true(frame, CONDITIONAL_RETS[op])):
        model = stack_control_semantics(op)
        return [sp_delta_register_write(frame, model.sp_write_operation, model.sp_delta, model_source=SM83_MODEL_SOURCE)]
    if op in {0x22, 0x32}:
        return [hli_hld_hl_writeback_effect(op, frame)]
    if 0x40 <= op <= 0x7F and op != 0x76:
        model = load_semantics(op)
        if model.target_kind == "register" and model.source_kind == "register":
            target = model.register_target
            source = model.register_source
            value = reg_value_if_known(frame, source)
            item = register_write_effect(
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
        writes = [
            register_write_effect(
                model.register_target,
                model.operation,
                source_operands=[register_operand(model.target, frame)],
                value=model.result(old_value),
                value_source="modeled_from_pre_register" if old_value is not None else "",
            ),
            register_write_effect(
                "F",
                model.flag_operation,
                source_operands=[register_operand(model.target, frame), register_operand("f", frame)],
                value=model.flags(old_value=old_value, flags=flags),
                value_source="modeled_from_pre_register" if old_value is not None and flags is not None else "",
            ),
        ]
        for item in writes:
            item["model_source"] = SM83_MODEL_SOURCE
        return writes
    try:
        model = register_pair_inc_dec_semantics(op)
    except ValueError:
        model = None
    if model is not None:
        value = pair_value_if_known(frame, model.register_pair)
        item = register_write_effect(
            model.register_pair.upper(),
            model.operation,
            source_operands=[register_operand(model.register_pair, frame)],
            value=model.updated_value(value),
            value_source="modeled_from_pre_register" if value is not None else "",
        )
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    accumulator_effects = accumulator_flag_effects(op, frame)
    if accumulator_effects:
        return accumulator_effects
    alu_effects = alu_register_write_effects(instruction, frame)
    if alu_effects:
        return alu_effects
    if op == 0x0A:
        model = load_semantics(op)
        address = pair_value_if_known(frame, "bc")
        if address is None:
            return [unknown_register_write(model.register_target, model.operation, missing_registers_for_pair(frame, "bc"), address_source=model.address_source)]
        load = register_load_from_memory(model.register_target, address, operation=model.operation, frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [load]
    if op == 0x1A:
        model = load_semantics(op)
        address = pair_value_if_known(frame, "de")
        if address is None:
            return [unknown_register_write(model.register_target, model.operation, missing_registers_for_pair(frame, "de"), address_source=model.address_source)]
        load = register_load_from_memory(model.register_target, address, operation=model.operation, frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [load]
    if op in {0x2A, 0x3A}:
        address = pair_value_if_known(frame, "hl")
        if address is None:
            return [
                unknown_register_write("A", hli_hld_load_operation(op), missing_registers_for_pair(frame, "hl"), address_source="hl"),
                hli_hld_hl_writeback_effect(op, frame),
            ]
        load = register_load_from_memory("A", address, operation=hli_hld_load_operation(op), frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [
            load,
            hli_hld_hl_writeback_effect(op, frame),
        ]
    if 0x40 <= op <= 0x7F and op != 0x76 and INDEX_REG[op & 0x07] == "[hl]":
        model = load_semantics(op)
        address = pair_value_if_known(frame, "hl")
        target = model.register_target
        if address is None:
            return [unknown_register_write(target, model.operation, missing_registers_for_pair(frame, "hl"), address_source=model.address_source)]
        load = register_load_from_memory(target, address, operation=model.operation, frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [load]
    if op == 0xFA:
        model = load_semantics(op)
        address = u16_from_operand(instruction)
        load = register_load_from_memory(model.register_target, address, operation=model.operation, frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [load]
    if op == 0xF0 and instruction.operand:
        model = load_semantics(op)
        address = 0xFF00 + int(instruction.operand[0])
        load = register_load_from_memory(model.register_target, address, operation=model.operation.replace("ld a, [n]", "ldh a, [n]"), frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [load]
    if op == 0xF2:
        model = load_semantics(op)
        c = reg_value_if_known(frame, "c")
        if c is None:
            return [unknown_register_write(model.register_target, model.operation.replace("ld a, [c]", "ldh a, [c]"), ["C"], address_source=model.address_source)]
        load = register_load_from_memory(model.register_target, 0xFF00 + c, operation=model.operation.replace("ld a, [c]", "ldh a, [c]"), frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [load]
    if op in {0x34, 0x35}:
        return [inc_dec_hl_flag_write(op, frame)]
    if op in {0xC1, 0xD1, 0xE1, 0xF1}:
        sp = pair_value_if_known(frame, "sp")
        target = {0xC1: "BC", 0xD1: "DE", 0xE1: "HL", 0xF1: "AF"}[op]
        model = stack_control_semantics(op)
        if sp is None:
            return [
                unknown_register_write(target, f"pop {target.lower()}", ["SP"], address_source="sp"),
                sp_delta_register_write(frame, model.sp_write_operation, model.sp_delta, model_source=SM83_MODEL_SOURCE),
            ]
        load = register_load_from_stack(target, sp, operation=model.register_write_operation, frame=frame)
        load["model_source"] = SM83_MODEL_SOURCE
        return [
            load,
            sp_delta_register_write(frame, model.sp_write_operation, model.sp_delta, model_source=SM83_MODEL_SOURCE),
        ]
    if op == 0xCB and instruction.operand:
        model = cb_semantics(int(instruction.operand[0]))
        target = model.target
        if model.is_memory_target:
            if model.writes_flags:
                return [cb_hl_flag_write(model.subopcode, frame)]
            return []
        if model.group == 1:
            old_value = reg_value_if_known(frame, target)
            item = register_write_effect(
                "F",
                f"{model.operation(target)} flags",
                source_operands=cb_flag_source_operands(model.subopcode, register_operand(target, frame), frame),
                value=model.flags(old_value, flags=frame_flags(frame)),
                value_source="modeled_from_pre_register" if old_value is not None and frame_flags(frame) is not None else "",
            )
            item["model_source"] = SM83_MODEL_SOURCE
            return [item]
        if model.writes_value:
            old_value = reg_value_if_known(frame, target)
            value = model.result(old_value, flags=frame_flags(frame))
            value_item = register_write_effect(
                target.upper(),
                model.operation(target),
                source_operands=[register_operand(target, frame)],
                value=value,
                value_source="modeled_from_pre_register" if value is not None else "",
            )
            value_item["model_source"] = SM83_MODEL_SOURCE
            effects = [value_item]
            if model.writes_flags:
                flag_value = model.flags(old_value, flags=frame_flags(frame))
                flag_item = register_write_effect(
                    "F",
                    f"{model.operation(target)} flags",
                    source_operands=cb_flag_source_operands(model.subopcode, register_operand(target, frame), frame),
                    value=flag_value,
                    value_source="modeled_from_pre_register" if flag_value is not None else "",
                )
                flag_item["model_source"] = SM83_MODEL_SOURCE
                effects.append(flag_item)
            return effects
    return []


def hli_hld_load_operation(opcode: int) -> str:
    return hli_hld_semantics(opcode).memory_operation


def sp_delta_register_write(frame: InstructionFrame, operation: str, delta: int, *, model_source: str = "") -> dict[str, Any]:
    sp = pair_value_if_known(frame, "sp")
    value = (sp + delta) & 0xFFFF if sp is not None else None
    item = register_write_effect(
        "SP",
        operation,
        source_operands=[register_operand("sp", frame)],
        value=value,
        value_source="modeled_from_pre_register" if value is not None else "",
    )
    if model_source:
        item["model_source"] = model_source
    return item


def ld_hl_sp_e8_register_writes(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    model = sp_relative_semantics(0xF8)
    sp = pair_value_if_known(frame, "sp")
    raw_offset = int(instruction.operand[0])
    operands = [register_operand("sp", frame), immediate_byte_operand(raw_offset)]
    writes = [
        register_write_effect(
            model.target_register,
            model.operation,
            source_operands=operands,
            value=model.result(sp=sp, raw_offset=raw_offset),
            value_source="modeled_from_pre_register" if sp is not None else "",
        ),
        register_write_effect(
            "F",
            model.flag_operation,
            source_operands=operands,
            value=model.flags(sp=sp, raw_offset=raw_offset),
            value_source="modeled_from_pre_register" if sp is not None else "",
        ),
    ]
    for item in writes:
        item["model_source"] = SM83_MODEL_SOURCE
    return writes


def add_hl_register_writes(frame: InstructionFrame, opcode: int) -> list[dict[str, Any]]:
    model = add_hl_semantics(opcode)
    hl = pair_value_if_known(frame, "hl")
    source = pair_value_if_known(frame, model.source_pair)
    flags = frame_flags(frame)
    operands = [register_operand("hl", frame), register_operand(model.source_pair, frame)]
    writes = [
        register_write_effect(
            "HL",
            model.operation,
            source_operands=operands,
            value=model.result(hl=hl, source=source),
            value_source="modeled_from_pre_register" if hl is not None and source is not None else "",
        ),
        register_write_effect(
            "F",
            model.flag_operation,
            source_operands=operands,
            value=model.flags(hl=hl, source=source, flags=flags),
            value_source="modeled_from_pre_register" if hl is not None and source is not None and flags is not None else "",
        ),
    ]
    for item in writes:
        item["model_source"] = SM83_MODEL_SOURCE
    return writes


def add_sp_e8_register_writes(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    model = sp_relative_semantics(0xE8)
    sp = pair_value_if_known(frame, "sp")
    raw_offset = int(instruction.operand[0])
    operands = [register_operand("sp", frame), immediate_byte_operand(raw_offset)]
    writes = [
        register_write_effect(
            model.target_register,
            model.operation,
            source_operands=operands,
            value=model.result(sp=sp, raw_offset=raw_offset),
            value_source="modeled_from_pre_register" if sp is not None else "",
        ),
        register_write_effect(
            "F",
            model.flag_operation,
            source_operands=operands,
            value=model.flags(sp=sp, raw_offset=raw_offset),
            value_source="modeled_from_pre_register" if sp is not None else "",
        ),
    ]
    for item in writes:
        item["model_source"] = SM83_MODEL_SOURCE
    return writes


def inc_dec_hl_flag_write(opcode: int, frame: InstructionFrame) -> dict[str, Any]:
    model = inc_dec_semantics(opcode)
    address = pair_value_if_known(frame, "hl")
    source_operands = [register_operand("hl", frame), register_operand("f", frame)]
    old_value = None
    old_value_source = ""
    if address is not None:
        old_value, old_value_source = frame_memory_sample(frame, address)
        source_operands = [
            memory_operand(address, value=old_value, value_source=old_value_source),
            register_operand("f", frame),
        ]
    item = register_write_effect(
        "F",
        model.flag_operation,
        source_operands=source_operands,
        value=model.flags(old_value=old_value, flags=frame_flags(frame)),
        value_source=modeled_value_source(old_value_source) if old_value is not None and frame_flags(frame) is not None else "",
    )
    item["model_source"] = SM83_MODEL_SOURCE
    return item


def accumulator_flag_effects(opcode: int, frame: InstructionFrame) -> list[dict[str, Any]]:
    try:
        model = accumulator_flag_semantics(opcode)
    except ValueError:
        return []
    a = reg_value_if_known(frame, "a")
    flags = frame_flags(frame)
    out: list[dict[str, Any]] = []
    if model.writes_accumulator:
        value = model.result(a=a, flags=flags)
        item = register_write_effect(
            "A",
            model.operation,
            source_operands=accumulator_model_operands(model, frame, target_register="A"),
            value=value,
            value_source="modeled_from_pre_register" if value is not None else "",
        )
        item["model_source"] = SM83_MODEL_SOURCE
        out.append(item)
    flag_value = model.flags(a=a, flags=flags)
    flag_item = register_write_effect(
        "F",
        model.flag_operation,
        source_operands=accumulator_model_operands(model, frame, target_register="F"),
        value=flag_value,
        value_source="modeled_from_pre_register" if flag_value is not None else "",
    )
    flag_item["model_source"] = SM83_MODEL_SOURCE
    out.append(flag_item)
    return out


def accumulator_model_operands(model: Any, frame: InstructionFrame, *, target_register: str) -> list[dict[str, Any]]:
    if model.opcode in {0x07, 0x0F}:
        return [register_operand("a", frame)]
    if model.opcode in {0x17, 0x1F, 0x27}:
        return [register_operand("a", frame), register_operand("f", frame)]
    if model.opcode == 0x2F and target_register == "A":
        return [register_operand("a", frame)]
    return [register_operand("f", frame)]


def hli_hld_hl_writeback_effect(opcode: int, frame: InstructionFrame) -> dict[str, Any]:
    old_hl = pair_value_if_known(frame, "hl")
    model = hli_hld_semantics(opcode)
    item = register_write_effect(
        "HL",
        model.hl_writeback_operation,
        source_operands=[register_operand("hl", frame)],
        value=model.updated_hl(old_hl),
        value_source="modeled_from_pre_register" if old_hl is not None else "",
    )
    item["model_source"] = SM83_MODEL_SOURCE
    return item


def register_load_from_memory(register: str, address: int, *, operation: str, frame: InstructionFrame) -> dict[str, Any]:
    value, value_source = frame_memory_sample(frame, address)
    return register_write_effect(
        register,
        operation,
        source_operands=[memory_operand(address, value=value, value_source=value_source)],
        value=value,
        value_source=value_source,
    )


def register_load_from_stack(register: str, address: int, *, operation: str, frame: InstructionFrame) -> dict[str, Any]:
    low, low_source = frame_memory_sample(frame, address)
    high, high_source = frame_memory_sample(frame, address + 1)
    value = stack_pop_register_value(register, low, high)
    value_source = "observed_memory_snapshot" if value is not None else ""
    return register_write_effect(
        register,
        operation,
        source_operands=[
            memory_operand(address, value=low, value_source=low_source),
            memory_operand(address + 1, value=high, value_source=high_source),
        ],
        value=value,
        value_source=value_source,
    )


def unknown_register_write(register: str, operation: str, missing_registers: list[str], *, address_source: str) -> dict[str, Any]:
    item = register_write_effect(
        register,
        operation,
        source_operands=[],
    )
    item.update(
        {
            "category": "missing_pre_register",
            "evidence_source": "instruction_frame_missing_register",
            "evidence_status": "unmodeled_missing_register",
            "address_source": address_source,
            "missing_registers": unique_list([name.upper() for name in missing_registers if name]),
            "message": "Instruction was observed and overwrites this register, but required pre-instruction address registers were not present in the trace frame.",
        }
    )
    return item


def alu_register_write_effects(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
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
        source_operands = [register_operand("a", frame), immediate_byte_operand(source_value)]
    model = alu_semantics(op)
    operation = model.operation(alu_source_label(op, instruction))
    a = reg_value_if_known(frame, "a")
    flags = frame_flags(frame)
    value = model.result(a=a, source=source_value, flags=flags)
    flag_value = model.flags(a=a, source=source_value, flags=flags)
    effects: list[dict[str, Any]] = []
    if model.group != 7:
        a_write = register_write_effect(
            "A",
            operation,
            source_operands=source_operands,
            value=value,
            value_source="modeled_from_pre_register" if value is not None else "",
        )
        a_write["model_source"] = SM83_MODEL_SOURCE
        effects.append(a_write)
    flags_write = register_write_effect(
        "F",
        f"{operation} flags",
        source_operands=source_operands,
        value=flag_value,
        value_source="modeled_from_pre_register" if flag_value is not None else "",
    )
    flags_write["model_source"] = SM83_MODEL_SOURCE
    effects.append(flags_write)
    return effects


def alu_source_label(opcode: int, instruction: Instruction) -> str:
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


def memory_write_effects(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    op = int(instruction.opcode)
    if op == 0x02:
        model = load_semantics(op)
        address = pair_value_if_known(frame, "bc")
        if address is None:
            return [unmodeled_effect("unmodeled_memory_write", model.operation, missing_registers=missing_registers_for_pair(frame, "bc"), address_source=model.address_source)]
        item = effect("memory_write", address, operation=model.operation, source=register_operand("a", frame), value=reg_value_if_known(frame, "a"))
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op == 0x12:
        model = load_semantics(op)
        address = pair_value_if_known(frame, "de")
        if address is None:
            return [unmodeled_effect("unmodeled_memory_write", model.operation, missing_registers=missing_registers_for_pair(frame, "de"), address_source=model.address_source)]
        item = effect("memory_write", address, operation=model.operation, source=register_operand("a", frame), value=reg_value_if_known(frame, "a"))
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op in {0x22, 0x32}:
        address = pair_value_if_known(frame, "hl")
        if address is None:
            return [
                unmodeled_effect(
                    "unmodeled_memory_write",
                    hli_hld_semantics(op).memory_operation,
                    missing_registers=missing_registers_for_pair(frame, "hl"),
                    address_source="hl",
                )
            ]
        item = effect(
            "memory_write",
            address,
            operation=hli_hld_semantics(op).memory_operation,
            source=register_operand("a", frame),
            value=reg_value_if_known(frame, "a"),
        )
        item["model_source"] = SM83_MODEL_SOURCE
        return [
            item
        ]
    if op == 0x36:
        model = load_semantics(op)
        address = pair_value_if_known(frame, "hl")
        if address is None:
            return [unmodeled_effect("unmodeled_memory_write", model.operation, missing_registers=missing_registers_for_pair(frame, "hl"), address_source=model.address_source)]
        value = int(instruction.operand[0]) if instruction.operand else 0
        item = effect("memory_write", address, operation=model.operation, source=immediate_operand(value), value=value)
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if 0x70 <= op <= 0x77 and op != 0x76 and INDEX_REG[op & 0x07] != "[hl]":
        model = load_semantics(op)
        source = model.register_source
        address = pair_value_if_known(frame, "hl")
        if address is None:
            return [unmodeled_effect("unmodeled_memory_write", model.operation, missing_registers=missing_registers_for_pair(frame, "hl"), address_source=model.address_source)]
        item = effect("memory_write", address, operation=model.operation, source=register_operand(source, frame), value=reg_value_if_known(frame, source))
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op in {0x34, 0x35}:
        model = inc_dec_semantics(op)
        address = pair_value_if_known(frame, "hl")
        if address is None:
            item = unmodeled_effect("unmodeled_memory_write", model.operation, missing_registers=missing_registers_for_pair(frame, "hl"), address_source="hl")
            item["model_source"] = SM83_MODEL_SOURCE
            return [item]
        old_value, old_value_source = frame_memory_sample(frame, address)
        item = effect(
            "memory_write",
            address,
            operation=model.operation,
            source=memory_operand(address, value=old_value, value_source=old_value_source),
            value=model.result(old_value),
            value_source=modeled_value_source(old_value_source),
        )
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op == 0x08:
        model = load_semantics(op)
        address = u16_from_operand(instruction)
        sp = pair_value_if_known(frame, "sp")
        low = effect("memory_write", address, operation=f"{model.operation} low", source=register_operand("sp", frame), value=sp)
        high = effect("memory_write", address + 1, operation=f"{model.operation} high", source=register_operand("sp", frame), value=sp >> 8 if sp is not None else None)
        low["model_source"] = SM83_MODEL_SOURCE
        high["model_source"] = SM83_MODEL_SOURCE
        return [low, high]
    if op == 0xEA:
        model = load_semantics(op)
        item = effect("memory_write", u16_from_operand(instruction), operation=model.operation, source=register_operand("a", frame), value=reg_value_if_known(frame, "a"))
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op == 0xE0 and instruction.operand:
        model = load_semantics(op)
        item = effect("io_write", 0xFF00 + int(instruction.operand[0]), operation=model.operation.replace("ld [n], a", "ldh [n], a"), source=register_operand("a", frame), value=reg_value_if_known(frame, "a"))
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op == 0xE2:
        model = load_semantics(op)
        c = reg_value_if_known(frame, "c")
        if c is None:
            return [unmodeled_effect("unmodeled_io_write", model.operation.replace("ld [c], a", "ldh [c], a"), missing_registers=["C"], address_source=model.address_source)]
        item = effect("io_write", 0xFF00 + c, operation=model.operation.replace("ld [c], a", "ldh [c], a"), source=register_operand("a", frame), value=reg_value_if_known(frame, "a"))
        item["model_source"] = SM83_MODEL_SOURCE
        return [item]
    if op in {0xC5, 0xD5, 0xE5, 0xF5}:
        model = stack_control_semantics(op)
        pair = model.register_pair
        low, high = register_pair_stack_components(pair)
        return stack_push_effects(
            frame,
            operation=model.stack_write_operation,
            source=register_operand(pair, frame),
            low_source=register_operand(low, frame),
            high_source=register_operand(high, frame),
            model_source=SM83_MODEL_SOURCE,
        )
    if op == 0xCD or (op in CONDITIONAL_CALLS and frame_condition_true(frame, CONDITIONAL_CALLS[op])):
        model = stack_control_semantics(op)
        return stack_push_effects(
            frame,
            operation=model.stack_write_operation,
            source=immediate_operand((frame.pc + instruction.length) & 0xFFFF),
            model_source=SM83_MODEL_SOURCE,
        )
    if op in RST_TARGETS:
        model = stack_control_semantics(op)
        return stack_push_effects(
            frame,
            operation=model.stack_write_operation,
            source=immediate_operand((frame.pc + instruction.length) & 0xFFFF),
            model_source=SM83_MODEL_SOURCE,
        )
    if op == 0xCB and instruction.operand:
        model = cb_semantics(int(instruction.operand[0]))
        if model.is_memory_target and model.writes_value:
            address = pair_value_if_known(frame, "hl")
            if address is None:
                item = unmodeled_effect("unmodeled_memory_write", model.operation(), missing_registers=missing_registers_for_pair(frame, "hl"), address_source="hl")
                item["model_source"] = SM83_MODEL_SOURCE
                return [item]
            old_value, old_value_source = frame_memory_sample(frame, address)
            item = effect(
                "memory_write",
                address,
                operation=model.operation(),
                source=memory_operand(address, value=old_value, value_source=old_value_source),
                value=model.result(old_value, flags=frame_flags(frame)),
                value_source=modeled_value_source(old_value_source),
            )
            item["model_source"] = SM83_MODEL_SOURCE
            return [item]
    return []


def control_effects(instruction: Instruction, frame: InstructionFrame) -> list[dict[str, Any]]:
    op = int(instruction.opcode)
    effects: list[dict[str, Any]] = []
    if op in {0xC3, 0x18} or (op in CONDITIONAL_JUMPS and frame_condition_true(frame, CONDITIONAL_JUMPS[op])):
        effects.append(control_effect("control_flow", "jump", target=jump_target(instruction, frame)))
    if op == 0xE9:
        target = pair_value_if_known(frame, "hl")
        if target is not None:
            effects.append(control_effect("control_flow", "jump", target=target, target_source="hl"))
        else:
            effects.append(unmodeled_effect("unmodeled_control_flow", "jump [hl]", missing_registers=missing_registers_for_pair(frame, "hl"), address_source="hl"))
    if op == 0xCD or (op in CONDITIONAL_CALLS and frame_condition_true(frame, CONDITIONAL_CALLS[op])):
        model = stack_control_semantics(op)
        item = control_effect("control_flow", model.control_operation, target=u16_from_operand(instruction))
        item["model_source"] = SM83_MODEL_SOURCE
        effects.append(item)
    if op in RST_TARGETS:
        model = stack_control_semantics(op)
        item = control_effect("control_flow", model.control_operation, target=model.rst_target if model.rst_target is not None else RST_TARGETS[op])
        item["model_source"] = SM83_MODEL_SOURCE
        effects.append(item)
    if op in {0xC9, 0xD9} or (op in CONDITIONAL_RETS and frame_condition_true(frame, CONDITIONAL_RETS[op])):
        model = stack_control_semantics(op)
        item = control_effect("control_flow", model.control_operation)
        item["model_source"] = SM83_MODEL_SOURCE
        effects.append(item)
    if op in CPU_STATE_OPCODES:
        model = cpu_state_semantics(op)
        item = control_effect(model.kind, model.operation, category=model.category, mode=model.mode)
        item["model_source"] = SM83_MODEL_SOURCE
        effects.append(item)
    return effects


def interrupt_entry_effects(
    *,
    previous_instruction: Instruction,
    previous_frame: InstructionFrame,
    current_frame: InstructionFrame,
) -> list[dict[str, Any]]:
    vector = int(current_frame.pc) & 0xFFFF
    if int(current_frame.bank) != 0 or vector not in INTERRUPT_VECTORS:
        return []
    if not frame_register_known(previous_frame, "SP") or not frame_register_known(current_frame, "SP"):
        return []
    model = interrupt_entry_semantics(vector)
    expected_sp = model.updated_sp(previous_frame.SP)
    if int(current_frame.SP) != expected_sp:
        return []
    if instruction_can_transfer_to(previous_instruction, previous_frame, vector):
        return []
    return_address = model.return_address(previous_frame.pc, previous_instruction.length)
    trigger = interrupt_entry_side_effect(
        model=model,
        previous_frame=previous_frame,
        current_frame=current_frame,
        return_address=return_address,
    )
    return [
        trigger,
        interrupt_sp_register_write(previous_frame=previous_frame, current_frame=current_frame, model=model),
        interrupt_stack_write(
            current_frame=current_frame,
            address=int(current_frame.SP),
            operation=model.stack_low_operation,
            return_address=return_address,
            model=model,
        ),
        interrupt_stack_write(
            current_frame=current_frame,
            address=(int(current_frame.SP) + 1) & 0xFFFF,
            operation=model.stack_high_operation,
            return_address=return_address,
            model=model,
        ),
    ]


def instruction_can_transfer_to(instruction: Instruction, frame: InstructionFrame, target: int) -> bool:
    target &= 0xFFFF
    for item in control_effects(instruction, frame):
        if int(item.get("target", -1)) == target:
            return True
    return False


def interrupt_entry_side_effect(
    *,
    model: Any,
    previous_frame: InstructionFrame,
    current_frame: InstructionFrame,
    return_address: int,
) -> dict[str, Any]:
    return {
        "kind": "interrupt_entry",
        "access": "side_effect",
        "category": "interrupt",
        "operation": model.operation,
        "evidence_source": "modeled_from_trace_transition",
        "evidence_status": "modeled_hardware_side_effect",
        "runtime_observation": "adjacent_instruction_frames",
        "interrupt": model.name,
        "interrupt_vector": f"{model.vector:04X}",
        "return_address": f"{return_address:04X}",
        "previous_pc": f"{int(previous_frame.bank):02X}:{int(previous_frame.pc):04X}",
        "handler_pc": f"{int(current_frame.bank):02X}:{int(current_frame.pc):04X}",
        "stack_address": f"{int(current_frame.SP) & 0xFFFF:04X}",
        "modeled_from_trace_transition": True,
        "model_source": SM83_MODEL_SOURCE,
    }


def interrupt_stack_write(
    *,
    current_frame: InstructionFrame,
    address: int,
    operation: str,
    return_address: int,
    model: Any,
) -> dict[str, Any]:
    item = effect(
        "stack_write",
        address,
        operation=operation,
        source=immediate_operand(return_address),
        value=model.stack_value(return_address, operation),
    )
    item.update(
        {
            "category": "interrupt",
            "hardware_model": "interrupt_entry",
            "evidence_source": "modeled_from_interrupt_entry_transition",
            "evidence_status": "modeled_hardware_side_effect",
            "runtime_observation": "adjacent_instruction_frames",
            "interrupt": model.name,
            "interrupt_vector": f"{model.vector:04X}",
            "handler_pc": f"{int(current_frame.bank):02X}:{int(current_frame.pc):04X}",
            "return_address": f"{return_address:04X}",
            "modeled_from_trace_transition": True,
            "model_source": SM83_MODEL_SOURCE,
        }
    )
    return item


def interrupt_sp_register_write(
    *,
    previous_frame: InstructionFrame,
    current_frame: InstructionFrame,
    model: Any,
) -> dict[str, Any]:
    item = register_write_effect(
        "SP",
        model.sp_write_operation,
        source_operands=[register_operand("sp", previous_frame)],
        value=int(current_frame.SP) & 0xFFFF,
        value_source="modeled_from_trace_transition",
    )
    item.update(
        {
            "category": "interrupt",
            "hardware_model": "interrupt_entry",
            "evidence_source": "modeled_from_interrupt_entry_transition",
            "evidence_status": "modeled_hardware_side_effect",
            "runtime_observation": "adjacent_instruction_frames",
            "interrupt": model.name,
            "interrupt_vector": f"{model.vector:04X}",
            "previous_sp": f"{int(previous_frame.SP) & 0xFFFF:04X}",
            "handler_pc": f"{int(current_frame.bank):02X}:{int(current_frame.pc):04X}",
            "modeled_from_trace_transition": True,
            "model_source": SM83_MODEL_SOURCE,
        }
    )
    return item


def register_pair_stack_components(pair: str) -> tuple[str, str]:
    return {
        "af": ("f", "a"),
        "bc": ("c", "b"),
        "de": ("e", "d"),
        "hl": ("l", "h"),
    }[pair.lower()]


def stack_push_effects(
    frame: InstructionFrame,
    *,
    operation: str,
    source: dict[str, Any],
    low_source: dict[str, Any] | None = None,
    high_source: dict[str, Any] | None = None,
    model_source: str = "",
) -> list[dict[str, Any]]:
    stack_pointer = pair_value_if_known(frame, "sp")
    if stack_pointer is None:
        return [unmodeled_effect("unmodeled_stack_write", operation, missing_registers=["SP"], address_source="sp")]
    sp = (stack_pointer - 2) & 0xFFFF
    explicit_low_source = low_source is not None
    explicit_high_source = high_source is not None
    low_source = low_source or source
    high_source = high_source or source
    value = operand_int_value(source)
    low_value = operand_int_value(low_source) if explicit_low_source else value
    high_value = operand_int_value(high_source) if explicit_high_source else (value >> 8 if value is not None else None)
    low = effect("stack_write", sp, operation=f"{operation} low", source=low_source, value=low_value if low_value is not None else value)
    high = effect(
        "stack_write",
        sp + 1,
        operation=f"{operation} high",
        source=high_source,
        value=high_value,
    )
    if model_source:
        low["model_source"] = model_source
        high["model_source"] = model_source
    return [low, high]


def unmodeled_effect(
    kind: str,
    operation: str,
    *,
    missing_registers: list[str],
    address_source: str,
) -> dict[str, Any]:
    missing = unique_list([register.upper() for register in missing_registers if register])
    return {
        "kind": kind,
        "access": "unmodeled",
        "category": "missing_pre_register",
        "operation": operation,
        "evidence_source": "instruction_frame_missing_register",
        "evidence_status": "unmodeled_missing_register",
        "runtime_observation": "instruction_frame",
        "address_source": address_source,
        "missing_registers": missing,
        "message": "Instruction was observed, but required pre-instruction register values were not present in the trace frame.",
    }


def register_write_effect(
    register: str,
    operation: str,
    *,
    source_operands: list[dict[str, Any]],
    value: int | None = None,
    value_source: str = "",
) -> dict[str, Any]:
    register = register.upper()
    width = register_width(register)
    out = {
        "kind": "register_write",
        "access": "register_write",
        "evidence_source": "modeled_from_instruction_frame",
        "evidence_status": "modeled",
        "runtime_observation": "instruction_frame",
        "register": register,
        "register_width": width,
        "operation": operation,
        "source_operands": [operand for operand in source_operands if operand],
    }
    if value is not None:
        out["value"] = int(value) & ((1 << (width * 4)) - 1)
        out["value_hex"] = f"{int(value) & ((1 << (width * 4)) - 1):0{width}X}"
        if value_source:
            out["value_source"] = value_source
    return out


def register_width(register: str) -> int:
    return 4 if register.upper() in {"AF", "BC", "DE", "HL", "SP"} else 2


def read_effect(kind: str, address: int, *, operation: str, frame: InstructionFrame) -> dict[str, Any]:
    value, value_source = frame_memory_sample(frame, address)
    return effect(kind, address, operation=operation, value=value, value_source=value_source)


def effect(
    kind: str,
    address: int,
    *,
    operation: str,
    bank: int | None = None,
    width: int = 1,
    source: dict[str, Any] | None = None,
    value: int | None = None,
    value_source: str = "",
) -> dict[str, Any]:
    address &= 0xFFFF
    out = {
        "kind": kind,
        "access": "write" if kind.endswith("_write") else "read",
        "evidence_source": "modeled_from_instruction_frame",
        "evidence_status": "modeled",
        "runtime_observation": "instruction_frame",
        "space": effect_space(kind, address),
        "bank": bank,
        "address": address,
        "address_hex": f"{address:04X}",
        "address_key": effect_address_key(kind, address, bank=bank),
        "width": width,
        "operation": operation,
    }
    if source:
        out["source_operands"] = [source]
    if value is not None:
        out["value"] = value & 0xFF
        out["value_hex"] = f"{value & 0xFF:02X}"
        source_text = value_source or operand_value_source(source)
        if source_text:
            out["value_source"] = source_text
    return out


def attach_frame_bank_state(effects: list[dict[str, Any]], frame: InstructionFrame) -> list[dict[str, Any]]:
    for item in effects:
        attach_effect_bank_state(item, frame)
        for operand in item.get("source_operands", []):
            if isinstance(operand, dict):
                attach_operand_bank_state(operand, frame)
    return effects


def attach_effect_bank_state(item: dict[str, Any], frame: InstructionFrame) -> None:
    if item.get("kind") not in {"memory_read", "memory_write", "stack_read", "stack_write"}:
        return
    try:
        address = int(item.get("address", -1)) & 0xFFFF
    except (TypeError, ValueError):
        return
    bank, source = observed_memory_bank(frame, address)
    if bank is None:
        return
    item["bank"] = bank
    item["bank_source"] = source
    item["space"] = effect_space(str(item.get("kind", "")), address, bank=bank)
    item["address_key"] = effect_address_key(str(item.get("kind", "")), address, bank=bank)
    if 0xA000 <= address <= 0xBFFF:
        sram_enabled = frame_bank_state(frame, "sram_enabled")
        if sram_enabled is not None:
            item["sram_enabled"] = sram_enabled
            item["sram_enabled_source"] = frame_bank_state_source(frame, "sram_enabled")


def attach_operand_bank_state(operand: dict[str, Any], frame: InstructionFrame) -> None:
    if operand.get("kind") != "memory":
        return
    try:
        address = int(str(operand.get("address", "")), 16) & 0xFFFF
    except ValueError:
        return
    bank, source = observed_memory_bank(frame, address)
    if bank is None:
        return
    operand["bank"] = f"{bank:02X}"
    operand["bank_source"] = source
    operand["address_key"] = address_key(f"{bank:02X}:{address:04X}")
    if 0xA000 <= address <= 0xBFFF:
        sram_enabled = frame_bank_state(frame, "sram_enabled")
        if sram_enabled is not None:
            operand["sram_enabled"] = sram_enabled
            operand["sram_enabled_source"] = frame_bank_state_source(frame, "sram_enabled")


def observed_memory_bank(frame: InstructionFrame, address: int) -> tuple[int | None, str]:
    address &= 0xFFFF
    if 0xD000 <= address <= 0xDFFF:
        bank = frame_bank_state(frame, "wram")
        return (bank, frame_bank_state_source(frame, "wram")) if bank is not None else (None, "")
    if 0x8000 <= address <= 0x9FFF:
        bank = frame_bank_state(frame, "vram")
        return (bank, frame_bank_state_source(frame, "vram")) if bank is not None else (None, "")
    if 0x4000 <= address <= 0x7FFF:
        bank = frame_bank_state(frame, "rom")
        return (bank, frame_bank_state_source(frame, "rom")) if bank is not None else (None, "")
    if 0xA000 <= address <= 0xBFFF:
        bank = frame_bank_state(frame, "sram")
        return (bank, frame_bank_state_source(frame, "sram")) if bank is not None else (None, "")
    return None, ""


def frame_bank_state(frame: InstructionFrame, name: str) -> int | None:
    for key, value in frame.bank_state:
        if key == name:
            return int(value) & 0xFF
    return None


def frame_bank_state_source(frame: InstructionFrame, name: str) -> str:
    if frame_bank_state(frame, f"{name}_inferred") is not None:
        return f"inferred_bank_state.{name}"
    return f"bank_state.{name}"


def frame_bank_state_sources(frame: InstructionFrame) -> dict[str, str]:
    return {
        key: frame_bank_state_source(frame, key)
        for key, _ in frame.bank_state
        if not str(key).endswith("_inferred")
    }


def frame_bank_state_records(frame: InstructionFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for key, value in frame.bank_state:
        name = str(key)
        if name.endswith("_inferred"):
            continue
        source = frame_bank_state_source(frame, name)
        inferred = source.startswith("inferred_bank_state.")
        valid_spaces = list(BANK_STATE_VALID_SPACES.get(name, ()))
        records.append(
            {
                "name": name,
                "value": int(value) & 0xFF,
                "value_hex": f"{int(value) & 0xFF:02X}",
                "source": source,
                "source_kind": "inferred_bank_state" if inferred else "bank_state",
                "state_kind": "inferred_from_io_write" if inferred else "runtime_observed",
                "inferred": inferred,
                "valid_for_space": valid_spaces[0] if valid_spaces else "",
                "valid_for_spaces": valid_spaces,
            }
        )
    return records


def effect_space(kind: str, address: int, *, bank: int | None = None) -> str:
    if kind == "rom_read":
        return "rom0" if address < 0x4000 else "romx"
    if kind.startswith("io_"):
        return "io"
    if kind.startswith("timer_"):
        return "io"
    if kind.startswith("stack_") and bank is None:
        return "stack"
    try:
        return parse_address_spec(f"{bank:02X}:{address:04X}" if bank is not None else f"{address:04X}").space
    except ValueError:
        return "unknown"


def effect_address_key(kind: str, address: int, *, bank: int | None) -> str:
    return observed_address_key(
        address,
        bank=bank,
        space=memory_space_for_key(address, bank=bank),
    ).key()


def memory_space_for_key(address: int, *, bank: int | None) -> str:
    try:
        return parse_address_spec(f"{bank:02X}:{address & 0xFFFF:04X}" if bank is not None else f"{address & 0xFFFF:04X}").space
    except ValueError:
        return parse_address_spec(f"{address & 0xFFFF:04X}").space


def control_effect(kind: str, operation: str, *, target: int | None = None, category: str = "", **extra: Any) -> dict[str, Any]:
    access = "control" if kind == "control_flow" else "side_effect"
    out = {
        "kind": kind,
        "access": access,
        "operation": operation,
        "evidence_source": "modeled_from_instruction_frame",
        "evidence_status": "modeled",
        "runtime_observation": "instruction_frame",
    }
    if category:
        out["category"] = category
    out.update({key: value for key, value in extra.items() if value not in {None, ""}})
    if target is not None:
        out["target"] = target & 0xFFFF
        out["target_hex"] = f"{target & 0xFFFF:04X}"
    return out


def hardware_side_effects(
    write_effects: list[dict[str, Any]],
    *,
    hardware_state: dict[str, int],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in write_effects:
        address = int(item.get("address", -1))
        kind = str(item.get("kind", ""))
        if kind in {"io_write", "memory_write"} and address >= 0xFF00:
            out.extend(io_write_side_effects(item, address=address, hardware_state=hardware_state))
        elif kind == "memory_write":
            out.extend(memory_write_side_effects(item, address=address))
    return out


def io_write_side_effects(
    item: dict[str, Any],
    *,
    address: int,
    hardware_state: dict[str, int],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for model in hardware_trigger_semantics(address):
        if model.kind == "oam_dma_trigger":
            value = source_operand_value(item)
            extra = {
                "dma_source_high": f"{value:02X}" if value is not None else "",
                "source_range": f"{value << 8:04X}-{((value << 8) + 0x9F) & 0xFFFF:04X}" if value is not None else "",
                "target_range": "FE00-FE9F",
            }
            trigger = side_effect(model.kind, model.operation, item, category=model.category, **extra)
            out.extend([trigger, *oam_dma_transfer_effects(item, source_high=value, hardware_state=hardware_state)])
            continue
        if model.kind in {"vram_dma_register_write", "vram_dma_len_mode_write"}:
            out.extend(vram_dma_side_effects(item, address=address, hardware_state=hardware_state))
            continue
        trigger = side_effect(
            model.kind,
            model.operation,
            item,
            category=model.category,
            register=model.register,
            hardware_model=model.hardware_model,
        )
        out.append(trigger)
        if model.kind == "timer_div_reset":
            out.append(timer_div_reset_write(item))
    return out

def vram_dma_side_effects(
    item: dict[str, Any],
    *,
    address: int,
    hardware_state: dict[str, int],
) -> list[dict[str, Any]]:
    model = hardware_trigger_semantics(address)[0]
    if address != 0xFF55:
        return [
            side_effect(
                model.kind,
                model.operation,
                item,
                category=model.category,
                register=model.register,
                hardware_model=model.hardware_model,
            )
        ]
    value = source_operand_value(item)
    extra: dict[str, Any] = {"register": model.register, "hardware_model": model.hardware_model}
    if value is not None:
        blocks = (value & 0x7F) + 1
        extra.update(
            {
                "mode": "hblank" if value & 0x80 else "general",
                "transfer_blocks": blocks,
                "transfer_bytes": blocks * 0x10,
                "source_value": f"{value:02X}",
            }
        )
        if value & 0x80:
            extra.update(
                {
                    "transfer_model": "blocked_hblank_runtime_evidence_required",
                    "transfer_blocked_reason": "hblank_dma_requires_ppu_mode_timing",
                }
            )
    trigger = side_effect(
        model.kind,
        model.operation,
        item,
        category=model.category,
        **extra,
    )
    return [trigger, *vram_dma_transfer_effects(trigger, hardware_state=hardware_state, control_value=value)]


def vram_dma_transfer_effects(
    trigger: dict[str, Any],
    *,
    hardware_state: dict[str, int],
    control_value: int | None,
) -> list[dict[str, Any]]:
    if control_value is None or control_value & 0x80:
        return []
    registers = vram_dma_register_values(hardware_state)
    if registers is None:
        trigger["transfer_model"] = "blocked_missing_setup_registers"
        return []
    source_start, target_start = vram_dma_bounds(registers)
    length = ((control_value & 0x7F) + 1) * 0x10
    trigger.update(
        {
            "transfer_model": "modeled_general_dma_from_observed_registers",
            "source_range": f"{source_start:04X}-{(source_start + length - 1) & 0xFFFF:04X}",
            "target_range": f"{target_start:04X}-{(target_start + length - 1) & 0xFFFF:04X}",
        }
    )
    effects: list[dict[str, Any]] = []
    target_bank = hardware_state.get("vram")
    for offset in range(length):
        source_address = (source_start + offset) & 0xFFFF
        target_address = (target_start + offset) & 0xFFFF
        read = effect(
            "dma_read",
            source_address,
            operation="CGB VRAM DMA source read",
            bank=hardware_memory_bank(hardware_state, source_address),
        )
        write = effect(
            "dma_write",
            target_address,
            operation="CGB VRAM DMA VRAM write",
            bank=target_bank,
            source=hardware_memory_operand(source_address, hardware_state=hardware_state),
        )
        for transfer in (read, write):
            transfer.update(
                {
                    "category": "dma",
                    "hardware_model": "cgb_vram_dma",
                    "evidence_source": "modeled_from_vram_dma_trigger",
                    "evidence_status": "modeled_hardware_side_effect",
                    "trigger_evidence_source": trigger.get("evidence_source", ""),
                    "trigger_kind": trigger.get("kind", ""),
                    "trigger_address": trigger.get("trigger_address", ""),
                    "trigger_address_key": trigger.get("trigger_address_key", ""),
                    "dma_offset": offset,
                    "source_range": trigger["source_range"],
                    "target_range": trigger["target_range"],
                    "transfer_model": trigger.get("transfer_model", ""),
                    "modeled_from_trigger": True,
                    "model_source": SM83_MODEL_SOURCE,
                }
            )
            if transfer.get("bank") is not None:
                transfer["bank_source"] = "bank_state.vram" if transfer is write else hardware_memory_bank_source(source_address)
        effects.extend([read, write])
    return effects


def vram_dma_register_values(hardware_state: dict[str, int]) -> dict[str, int] | None:
    keys = ("rVDMA_SRC_HIGH", "rVDMA_SRC_LOW", "rVDMA_DEST_HIGH", "rVDMA_DEST_LOW")
    if any(key not in hardware_state for key in keys):
        return None
    return {key: int(hardware_state[key]) & 0xFF for key in keys}


def vram_dma_bounds(registers: dict[str, int]) -> tuple[int, int]:
    source = ((registers["rVDMA_SRC_HIGH"] << 8) | (registers["rVDMA_SRC_LOW"] & 0xF0)) & 0xFFF0
    target = 0x8000 | ((registers["rVDMA_DEST_HIGH"] & 0x1F) << 8) | (registers["rVDMA_DEST_LOW"] & 0xF0)
    return source, target & 0x9FF0


def timer_div_reset_write(trigger: dict[str, Any]) -> dict[str, Any]:
    item = effect("timer_div_reset_write", 0xFF04, operation="DIV reset to 00", value=0)
    item.update(
        {
            "category": "timer",
            "hardware_model": "timer_div_reset",
            "evidence_source": "modeled_from_timer_div_reset",
            "evidence_status": "modeled_hardware_side_effect",
            "runtime_observation": trigger.get("runtime_observation", ""),
            "trigger_evidence_source": trigger.get("evidence_source", ""),
            "trigger_kind": trigger.get("kind", ""),
            "trigger_address": trigger.get("address_hex", ""),
            "trigger_address_key": trigger.get("address_key", ""),
            "trigger_source_operands": trigger.get("source_operands", []),
            "modeled_from_trigger": True,
            "model_source": SM83_MODEL_SOURCE,
        }
    )
    trigger_value = source_operand_value(trigger)
    if trigger_value is not None:
        item["trigger_value"] = f"{trigger_value:02X}"
    return item


def memory_write_side_effects(item: dict[str, Any], *, address: int) -> list[dict[str, Any]]:
    return [
        side_effect(model.kind, model.operation, item, category=model.category, hardware_model=model.hardware_model)
        for model in hardware_trigger_semantics(address, write_kind="memory_write")
    ]


def side_effect(kind: str, operation: str, trigger: dict[str, Any], *, category: str, **extra: Any) -> dict[str, Any]:
    out = {
        "kind": kind,
        "access": "side_effect",
        "evidence_source": "modeled_from_trigger_effect",
        "evidence_status": "modeled",
        "runtime_observation": trigger.get("runtime_observation", ""),
        "trigger_evidence_source": trigger.get("evidence_source", ""),
        "category": category,
        "operation": operation,
        "trigger_kind": trigger.get("kind", ""),
        "trigger_address": trigger.get("address_hex", ""),
        "trigger_address_key": trigger.get("address_key", ""),
        "address": trigger.get("address"),
        "address_hex": trigger.get("address_hex", ""),
        "address_key": trigger.get("address_key", ""),
        "space": trigger.get("space", ""),
        "source_operands": trigger.get("source_operands", []),
        "model_source": SM83_MODEL_SOURCE,
    }
    value = source_operand_value(trigger)
    if value is not None:
        out["source_value"] = f"{value:02X}"
    out.update(extra)
    return out


def oam_dma_transfer_effects(
    trigger: dict[str, Any],
    *,
    source_high: int | None,
    hardware_state: dict[str, int],
) -> list[dict[str, Any]]:
    if source_high is None:
        return []
    source_start = (source_high & 0xFF) << 8
    effects: list[dict[str, Any]] = []
    for offset in range(0xA0):
        source_address = (source_start + offset) & 0xFFFF
        target_address = 0xFE00 + offset
        source_bank = hardware_memory_bank(hardware_state, source_address)
        read = effect(
            "dma_read",
            source_address,
            operation="OAM DMA source read",
            bank=source_bank,
        )
        write = effect(
            "dma_write",
            target_address,
            operation="OAM DMA OAM write",
            source=hardware_memory_operand(source_address, hardware_state=hardware_state),
        )
        for item in (read, write):
            item.update(
                {
                    "category": "dma",
                    "hardware_model": "oam_dma",
                    "evidence_source": "modeled_from_oam_dma_trigger",
                    "evidence_status": "modeled_hardware_side_effect",
                    "trigger_evidence_source": trigger.get("evidence_source", ""),
                    "trigger_kind": trigger.get("kind", ""),
                    "trigger_address": trigger.get("address_hex", ""),
                    "trigger_address_key": trigger.get("address_key", ""),
                    "dma_source_high": f"{source_high & 0xFF:02X}",
                    "dma_offset": offset,
                    "source_range": f"{source_start:04X}-{(source_start + 0x9F) & 0xFFFF:04X}",
                    "target_range": "FE00-FE9F",
                    "modeled_from_trigger": True,
                    "model_source": SM83_MODEL_SOURCE,
                }
            )
            if item is read and source_bank is not None:
                item["bank_source"] = hardware_memory_bank_source(source_address)
                if 0xA000 <= source_address <= 0xBFFF and "sram_enabled" in hardware_state:
                    item["sram_enabled"] = int(hardware_state["sram_enabled"]) & 0xFF
                    item["sram_enabled_source"] = "bank_state.sram_enabled"
        effects.extend([read, write])
    return effects


def source_operand_value(effect_item: dict[str, Any]) -> int | None:
    value = effect_item.get("value")
    if value is not None:
        try:
            return int(str(value), 0) & 0xFF
        except ValueError:
            pass
    for operand in effect_item.get("source_operands", []):
        if not isinstance(operand, dict):
            continue
        value = operand.get("value")
        if value is None:
            continue
        try:
            return int(str(value), 16) & 0xFF
        except ValueError:
            continue
    return None


def jump_target(instruction: Instruction, frame: InstructionFrame) -> int:
    if int(instruction.opcode) in {0x18, 0x20, 0x28, 0x30, 0x38} and instruction.operand:
        return (frame.pc + instruction.length + signed8(int(instruction.operand[0]))) & 0xFFFF
    return u16_from_operand(instruction)


def condition_true(condition: str, flags: int) -> bool:
    z = bool(flags & 0x80)
    c = bool(flags & 0x10)
    if condition == "z":
        return z
    if condition == "nz":
        return not z
    if condition == "c":
        return c
    if condition == "nc":
        return not c
    return False


def cb_hl_operation(subopcode: int) -> str:
    return cb_semantics(subopcode).operation("[hl]")


def cb_register_operation(subopcode: int, target: str) -> str:
    return cb_semantics(subopcode).operation(target)


def cb_hl_result(subopcode: int, old_value: int | None, *, flags: int | None) -> int | None:
    return cb_semantics(subopcode).result(old_value, flags=flags)


def cb_flags(subopcode: int, old_value: int | None, *, flags: int | None) -> int | None:
    return cb_semantics(subopcode).flags(old_value, flags=flags)


def cb_flag_source_operands(subopcode: int, value_operand: dict[str, Any], frame: InstructionFrame) -> list[dict[str, Any]]:
    model = cb_semantics(subopcode)
    operands = [value_operand]
    if model.reads_carry_for_flags:
        operands.append(register_operand("f", frame))
    return operands


def cb_hl_flag_write(subopcode: int, frame: InstructionFrame) -> dict[str, Any]:
    address = pair_value_if_known(frame, "hl")
    old_value = None
    old_value_source = ""
    value_operand = register_operand("hl", frame)
    if address is not None:
        old_value, old_value_source = frame_memory_sample(frame, address)
        value_operand = memory_operand(address, value=old_value, value_source=old_value_source)
    flag_value = cb_flags(subopcode, old_value, flags=frame_flags(frame))
    item = register_write_effect(
        "F",
        f"{cb_hl_operation(subopcode)} flags",
        source_operands=cb_flag_source_operands(subopcode, value_operand, frame),
        value=flag_value,
        value_source=modeled_value_source(old_value_source) if flag_value is not None and old_value_source else "",
    )
    item["model_source"] = SM83_MODEL_SOURCE
    return item


def watch_specs(
    *,
    watch_symbols: tuple[str, ...],
    watch_addresses: tuple[str, ...],
    watch_size: int,
    symbol_table: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    watches: list[dict[str, Any]] = []
    errors: list[str] = []
    for symbol in watch_symbols:
        entry = symbol_table.get(symbol)
        if not entry:
            errors.append(f"watch symbol not found in symbols: {symbol}")
            continue
        spec = parse_address_spec(str(entry.get("bank_address") or entry.get("address")))
        watches.append(watch_spec(name=symbol, spec=spec, size=watch_size, symbol=symbol))
    for raw in watch_addresses:
        try:
            spec = parse_address_spec(raw)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        watches.append(watch_spec(name=spec.evidence(), spec=spec, size=watch_size, symbol=""))
    return unique_watch_specs(watches), errors


def watch_spec(*, name: str, spec: AddressSpec, size: int, symbol: str) -> dict[str, Any]:
    data = spec.as_dict()
    data.update({"name": name, "symbol": symbol, "size": size})
    return data


def unique_watch_specs(watches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for watch in watches:
        key = (str(watch.get("key")), int(watch.get("size", 1)))
        if key in seen:
            continue
        seen.add(key)
        out.append(watch)
    return out


def watch_hits(effects: list[dict[str, Any]], watches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for item in effects:
        if item.get("access") not in {"read", "write"}:
            continue
        address = int(item.get("address", -1))
        for watch in watches:
            start = int(watch.get("address", -2))
            size = int(watch.get("size", 1))
            if start <= address < start + size:
                bank_match = watch_bank_match_status(watch, item)
                if not bank_match:
                    continue
                match_precision = watch_match_precision(bank_match)
                hits.append(
                    {
                        "watch": watch.get("name", ""),
                        "watch_key": watch.get("key", ""),
                        "effect_key": item.get("address_key", ""),
                        "effect_bank": item.get("bank"),
                        "match_precision": match_precision,
                        "bank_match": bank_match,
                        "bank_source": item.get("bank_source", ""),
                        "target_match_proof_status": watch_target_match_proof_status(match_precision, item),
                        "effect_proof_status": str(item.get("proof_status") or "instruction_observed"),
                        "proof_downgrade_reason": watch_proof_downgrade_reason(match_precision, item),
                        "effect_evidence_source": item.get("evidence_source", ""),
                        "effect_evidence_status": item.get("evidence_status", ""),
                        "effect_proof_downgrade_reason": item.get("proof_downgrade_reason", ""),
                        "hardware_model": item.get("hardware_model", ""),
                        "hardware_event_required": item.get("hardware_event_required", False),
                        "hardware_runtime_event": item.get("hardware_runtime_event", False),
                        "hardware_event_identity": item.get("hardware_event_identity", ""),
                        "hardware_event_labels": item.get("hardware_event_labels", []),
                        "hardware_generic_event_label_present": item.get("hardware_generic_event_label_present", False),
                        "hardware_event_types": item.get("hardware_event_types", []),
                        "hardware_proof_gate": item.get("hardware_proof_gate", ""),
                        "access": item.get("access", ""),
                        "effect_kind": item.get("kind", ""),
                        "address": item.get("address_hex", ""),
                        "operation": item.get("operation", ""),
                        "value_hex": item.get("value_hex", ""),
                    }
                )
    return hits


def watch_matches_effect(watch: dict[str, Any], item: dict[str, Any]) -> bool:
    return bool(watch_bank_match_status(watch, item))


def watch_match_precision(bank_match: str) -> str:
    if bank_match == "exact":
        return "exact_address_key"
    if bank_match == "bus_address_unverified_bank":
        return "bus_address_unverified_bank"
    return "bus_address"


def watch_target_match_proof_status(match_precision: str, item: dict[str, Any] | None = None) -> str:
    if item and effect_proof_blocks_target_match(item):
        return "planned_only"
    if match_precision == "bus_address_unverified_bank":
        return "planned_only"
    return "instruction_observed"


def watch_proof_downgrade_reason(match_precision: str, item: dict[str, Any] | None = None) -> str:
    if item and effect_proof_blocks_target_match(item):
        return str(item.get("proof_downgrade_reason") or "effect_proof_status_planned_only")
    if match_precision == "bus_address_unverified_bank":
        return "bank-qualified watch matched effect by bus address without runtime bank state"
    return ""


def effect_proof_blocks_target_match(item: dict[str, Any]) -> bool:
    if str(item.get("proof_status") or "") == "planned_only":
        return True
    if item.get("hardware_event_required") and not item.get("hardware_runtime_event"):
        return True
    if str(item.get("hardware_proof_gate") or "") == "explicit_runtime_event_missing":
        return True
    return False


def watch_bank_match_status(watch: dict[str, Any], item: dict[str, Any]) -> str:
    if watch.get("bank") is None:
        return "not_required"
    watch_key = str(watch.get("key", ""))
    effect_key = str(item.get("address_key", ""))
    if watch_key and effect_key and watch_key == effect_key:
        return "exact"
    if watch.get("symbol") and not item.get("bank_source"):
        return "bus_address_unverified_bank"
    return ""


def build_write_index(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for event in events:
        for item in event.get("effects", []):
            if item.get("access") not in {"read", "write"}:
                continue
            key = str(item.get("address_key", ""))
            if not key:
                continue
            entry = index.setdefault(
                key,
                {
                    "address_key": key,
                    "space": item.get("space", ""),
                    "address": item.get("address_hex", ""),
                    "read_count": 0,
                    "write_count": 0,
                    "last_writer_seq": None,
                    "last_writer_pc": "",
                    "last_writer_trace_source": "",
                    "last_value_hex": "",
                    "history": [],
                },
            )
            if item.get("access") == "write":
                entry["write_count"] += 1
                entry["last_writer_seq"] = event.get("seq")
                entry["last_writer_pc"] = event.get("pc_bank_address", "")
                entry["last_writer_trace_source"] = event.get("trace_source", "")
                entry["last_value_hex"] = item.get("value_hex", "")
            else:
                entry["read_count"] += 1
            entry["history"].append(
                {
                    "seq": event.get("seq"),
                    "trace_source": event.get("trace_source", ""),
                    "pc": event.get("pc_bank_address", ""),
                    "pc_label": event.get("pc_label", ""),
                    "access": item.get("access"),
                    "kind": item.get("kind"),
                    "operation": item.get("operation"),
                    "address": item.get("address_hex", ""),
                    "address_key": item.get("address_key", ""),
                    "value_hex": item.get("value_hex", ""),
                    "value_source": item.get("value_source", ""),
                    "proof_status": item.get("proof_status", ""),
                    "proof_downgrade_reason": item.get("proof_downgrade_reason", ""),
                    "category": item.get("category", ""),
                    "hardware_model": item.get("hardware_model", ""),
                    "hardware_event_required": item.get("hardware_event_required", False),
                    "hardware_runtime_event": item.get("hardware_runtime_event", False),
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
                    "pre_state_validation_count": item.get("pre_state_validation_count", 0),
                    "pre_state_observation_model": item.get("pre_state_observation_model", ""),
                    "pre_state_proof_boundary": item.get("pre_state_proof_boundary", ""),
                    "pre_state_non_mutating_instruction_event": item.get("pre_state_non_mutating_instruction_event", ""),
                    "evidence_atoms": item.get("evidence_atoms", []),
                    "source_operands": item.get("source_operands", []),
                    "pre_registers": event.get("pre_registers", {}),
                    "observed_memory": event.get("observed_memory", []),
                }
            )
            entry["history"] = entry["history"][-12:]
    return sorted(index.values(), key=lambda item: (str(item.get("space", "")), str(item.get("address", ""))))


def attach_effect_evidence_atoms(events: list[dict[str, Any]]) -> None:
    for event in events:
        event["evidence_atoms"] = merge_evidence_atoms(
            event.get("evidence_atoms"),
            evidence_atom(
                claim_type="effect.instruction_event",
                origin="effect_trace",
                observation_type="instruction_frame",
                proof_status="instruction_observed",
                source_report=str(event.get("trace_source", "")),
                source_kind="instruction_trace",
                scope=effect_event_scope(event),
                subjects={
                    "symbols": [str(event.get("pc_label", ""))],
                    "addresses": [str(event.get("pc_bank_address", ""))],
                },
                precision={"frame_kind": "pre_instruction"},
                detail={"mnemonic": event.get("mnemonic", "")},
            ),
        )
        for item in event.get("effects", []):
            if not isinstance(item, dict):
                continue
            item["evidence_atoms"] = merge_evidence_atoms(
                item.get("evidence_atoms"),
                effect_item_evidence_atom(event, item),
            )


def effect_item_evidence_atom(event: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    kind = str(item.get("kind") or "effect")
    register = str(item.get("register", ""))
    address = str(item.get("address_hex") or item.get("trigger_address") or "")
    return evidence_atom(
        claim_type=f"effect.{kind}",
        origin="effect_trace",
        observation_type=str(item.get("runtime_observation") or "instruction_frame"),
        proof_status=str(item.get("proof_status") or "instruction_observed"),
        source_report=str(event.get("trace_source", "")),
        source_kind="instruction_trace",
        scope=effect_event_scope(event),
        subjects={
            "symbols": [str(event.get("pc_label", ""))],
            "addresses": [address],
            "registers": [register],
        },
        precision={
            "access": item.get("access", ""),
            "space": item.get("space", ""),
            "address_key": item.get("address_key", ""),
            "bank": item.get("bank", ""),
            "bank_source": item.get("bank_source", ""),
            "width": item.get("width", ""),
            "evidence_source": item.get("evidence_source", ""),
            "evidence_status": item.get("evidence_status", ""),
            "value_source": item.get("value_source", ""),
            "model_source": item.get("model_source", ""),
            "hardware_model": item.get("hardware_model", ""),
            "hardware_event_required": item.get("hardware_event_required", ""),
            "hardware_runtime_event": item.get("hardware_runtime_event", ""),
            "hardware_proof_gate": item.get("hardware_proof_gate", ""),
            "proof_downgrade_reason": item.get("proof_downgrade_reason", ""),
        },
        validation={
            "pre_state_sample": item.get("pre_state_sample", ""),
            "pre_state_proof_status": item.get("pre_state_proof_status", ""),
            "pre_state_validation": item.get("pre_state_validation", ""),
            "pre_state_validation_kind": item.get("pre_state_validation_kind", ""),
            "pre_state_validation_source": item.get("pre_state_validation_source", ""),
            "pre_state_observation_model": item.get("pre_state_observation_model", ""),
            "pre_state_proof_boundary": item.get("pre_state_proof_boundary", ""),
            "pre_state_non_mutating_instruction_event": item.get("pre_state_non_mutating_instruction_event", ""),
            "post_value_status": item.get("post_value_status", ""),
            "post_register_status": item.get("post_register_status", ""),
        },
        detail={
            "operation": item.get("operation", ""),
            "value_hex": item.get("value_hex", ""),
            "source_value": item.get("source_value", ""),
        },
    )


def effect_event_scope(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "seq": event.get("seq"),
        "pc": event.get("pc"),
        "pc_label": event.get("pc_label", ""),
        "pc_bank_address": event.get("pc_bank_address", ""),
        "bank": event.get("bank"),
        "trace_source": event.get("trace_source", ""),
    }


def build_side_effect_index(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for event in events:
        for item in event.get("effects", []):
            if item.get("access") != "side_effect":
                continue
            key = (str(item.get("category", "")), str(item.get("kind", "")))
            entry = index.setdefault(
                key,
                {
                    "category": key[0],
                    "kind": key[1],
                    "count": 0,
                    "last_seq": None,
                    "last_pc": "",
                    "proof_statuses": [],
                    "proof_status": "instruction_observed",
                    "triggers": [],
                },
            )
            entry["count"] += 1
            entry["last_seq"] = event.get("seq")
            entry["last_pc"] = event.get("pc_bank_address", "")
            proof = str(item.get("proof_status") or "instruction_observed")
            entry["proof_statuses"] = unique_list([*string_items(entry.get("proof_statuses")), proof])
            entry["proof_status"] = weakest_effect_proof_status(entry["proof_statuses"])
            trigger = {
                "seq": event.get("seq"),
                "pc": event.get("pc_bank_address", ""),
                "pc_label": event.get("pc_label", ""),
                "operation": item.get("operation", ""),
                "trigger_address": item.get("trigger_address", ""),
                "source_value": item.get("source_value", ""),
                "proof_status": proof,
            }
            if item.get("mode"):
                trigger["mode"] = item.get("mode", "")
            if item.get("register"):
                trigger["register"] = item.get("register", "")
            if item.get("transfer_blocks"):
                trigger["transfer_blocks"] = item.get("transfer_blocks")
            if item.get("transfer_bytes"):
                trigger["transfer_bytes"] = item.get("transfer_bytes")
            if item.get("transfer_model"):
                trigger["transfer_model"] = item.get("transfer_model", "")
            if item.get("transfer_blocked_reason"):
                trigger["transfer_blocked_reason"] = item.get("transfer_blocked_reason", "")
            if item.get("model_source"):
                trigger["model_source"] = item.get("model_source", "")
            if item.get("proof_downgrade_reason"):
                trigger["proof_downgrade_reason"] = item.get("proof_downgrade_reason", "")
            if item.get("hardware_proof_gate"):
                trigger["hardware_proof_gate"] = item.get("hardware_proof_gate", "")
            if item.get("source_range"):
                trigger["source_range"] = item.get("source_range", "")
            if item.get("target_range"):
                trigger["target_range"] = item.get("target_range", "")
            entry["triggers"].append(trigger)
            entry["triggers"] = entry["triggers"][-12:]
    return sorted(index.values(), key=lambda item: (str(item.get("category", "")), str(item.get("kind", ""))))


def build_trace_window(
    loaded_traces: list[dict[str, Any]],
    *,
    checkpoint_interval: int,
    max_checkpoints: int,
) -> dict[str, Any]:
    source_windows: list[dict[str, Any]] = []
    checkpoints: list[dict[str, Any]] = []
    parse_error_count = 0
    frame_count = 0
    for loaded in loaded_traces:
        source = str(loaded.get("source", ""))
        records = trace_records(loaded.get("data"))
        source_checkpoints: list[dict[str, Any]] = []
        source_frame_count = 0
        first_seq: int | None = None
        last_seq: int | None = None
        last_checkpoint_key: tuple[str, int] | None = None
        last_checkpoint_candidate: dict[str, Any] | None = None
        inferred_bank_state: dict[str, int] = {}
        for index, record in enumerate(records):
            parsed = parse_instruction_record(record, default_seq=index)
            if parsed["error"]:
                parse_error_count += 1
                continue
            frame = parsed["frame"]
            inferred_bank_state = update_inferred_bank_state_from_frame(
                inferred_bank_state,
                frame,
            )
            frame = frame_with_inferred_bank_state(frame, inferred_bank_state)
            effects = instruction_effects(parsed["instruction"], frame)
            inferred_bank_state = update_inferred_bank_state_from_effects(
                inferred_bank_state,
                effects,
            )
            source_frame_count += 1
            frame_count += 1
            seq = int(frame.seq)
            first_seq = seq if first_seq is None else min(first_seq, seq)
            last_seq = seq if last_seq is None else max(last_seq, seq)
            checkpoint = trace_checkpoint(source=source, record_index=index, frame=frame)
            last_checkpoint_candidate = checkpoint
            if source_frame_count == 1 or (source_frame_count - 1) % checkpoint_interval == 0:
                source_checkpoints.append(checkpoint)
                last_checkpoint_key = (source, seq)
        if (
            source_frame_count
            and last_seq is not None
            and last_checkpoint_key != (source, last_seq)
            and last_checkpoint_candidate is not None
        ):
            source_checkpoints.append(last_checkpoint_candidate)
        source_windows.append(
            {
                "source": source,
                "frame_count": source_frame_count,
                "first_seq": first_seq,
                "last_seq": last_seq,
                "checkpoint_count": len(source_checkpoints),
            }
        )
        checkpoints.extend(source_checkpoints)
    limited_checkpoints, truncated = limit_checkpoints(checkpoints, max_checkpoints=max_checkpoints)
    return {
        "schema_version": 1,
        "proof_status": "instruction_observed" if frame_count else "planned_only",
        "mode": "bounded_pre_instruction_checkpoints",
        "frame_count": frame_count,
        "source_count": len(source_windows),
        "sources": source_windows,
        "checkpoint_interval": checkpoint_interval,
        "max_checkpoints": max_checkpoints,
        "checkpoint_count": len(limited_checkpoints),
        "checkpoint_truncated": truncated,
        "parse_error_count": parse_error_count,
        "checkpoints": limited_checkpoints,
        "known_limits": [
            "Checkpoints are sampled from captured instruction frames and do not include full emulator save-state snapshots.",
            "A reverse query can check modeled effects forward from a checkpoint inside this bounded trace window, but code outside the window remains unobserved.",
        ],
    }


def trace_checkpoint(*, source: str, record_index: int, frame: InstructionFrame) -> dict[str, Any]:
    return {
        "kind": "trace_checkpoint",
        "checkpoint_kind": "pre_instruction_trace_frame",
        "checkpoint_source": "instruction_trace",
        "emulator_replay": False,
        "emulator_replay_status": "not_run",
        "source": source,
        "record_index": record_index,
        "seq": int(frame.seq),
        "bank": int(frame.bank),
        "pc": int(frame.pc),
        "pc_bank_address": f"{int(frame.bank):02X}:{int(frame.pc):04X}",
        "pc_label": str(frame.pc_label),
        "registers": frame_registers(frame),
        "bank_state": {key: value for key, value in frame.bank_state},
        "bank_state_sources": frame_bank_state_sources(frame),
        "bank_state_records": frame_bank_state_records(frame),
        "observed_memory": frame_observed_memory(frame),
    }


def frame_observed_memory(frame: InstructionFrame, *, limit: int = 16) -> list[dict[str, str]]:
    return [
        {
            "address": f"{int(address) & 0xFFFF:04X}",
            "value_hex": f"{int(value) & 0xFF:02X}",
        }
        for address, value in frame.memory[:limit]
    ]


def frame_registers(frame: InstructionFrame) -> dict[str, str]:
    return {
        "A": f"{int(frame.A) & 0xFF:02X}",
        "F": f"{int(frame.F) & 0xFF:02X}",
        "B": f"{int(frame.B) & 0xFF:02X}",
        "C": f"{int(frame.C) & 0xFF:02X}",
        "D": f"{int(frame.D) & 0xFF:02X}",
        "E": f"{int(frame.E) & 0xFF:02X}",
        "H": f"{int(frame.H) & 0xFF:02X}",
        "L": f"{int(frame.L) & 0xFF:02X}",
        "HL": f"{int(frame.HL) & 0xFFFF:04X}",
        "SP": f"{int(frame.SP) & 0xFFFF:04X}",
    }


def limit_checkpoints(checkpoints: list[dict[str, Any]], *, max_checkpoints: int) -> tuple[list[dict[str, Any]], bool]:
    if len(checkpoints) <= max_checkpoints:
        return checkpoints, False
    if max_checkpoints == 1:
        return [checkpoints[-1]], True
    head_count = max(1, max_checkpoints // 2)
    tail_count = max_checkpoints - head_count
    return [*checkpoints[:head_count], *checkpoints[-tail_count:]], True


def write_effects_output(*, events: list[dict[str, Any]], out_effects: str, root: Path) -> dict[str, Any]:
    if not out_effects:
        return {"path": "", "written": False, "record_count": len(events), "errors": []}
    path = resolve_path(out_effects, root=root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
            encoding="utf-8",
            newline="\n",
        )
    except OSError as exc:
        return {"path": display_path(path, root=root), "written": False, "record_count": len(events), "errors": [str(exc)]}
    return {"path": display_path(path, root=root), "written": True, "record_count": len(events), "errors": []}


def trace_paths_from_reports(loaded_reports: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    for loaded in loaded_reports:
        paths.extend(trace_paths_from_data(loaded.get("data")))
    return unique_list(paths)


def hook_order_validations_from_reports(loaded_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    validations: list[dict[str, Any]] = []
    for loaded in loaded_reports:
        data = loaded.get("data")
        if not isinstance(data, dict) or data.get("kind") != "unified_debugger_hook_order_probe":
            continue
        failed_checks = [
            str(check.get("id", ""))
            for check in dict_items(data.get("checks"))
            if not check.get("passed")
        ]
        validations.append(
            {
                "source": str(loaded.get("source", "")),
                "executed": bool(data.get("executed")),
                "passed": bool(data.get("passed")),
                "proof_status": str(data.get("proof_status", "planned_only")),
                "proof_boundary": str(data.get("proof_boundary", "")),
                "hook_mechanism": str(data.get("hook_mechanism", "")),
                "non_mutating_instruction_events": bool(data.get("non_mutating_instruction_events")),
                "pre_fetch_runtime_observed": bool(data.get("pre_fetch_runtime_observed")),
                "observation_count": int(data.get("observation_count", 0) or 0),
                "expected_target_count": int(data.get("expected_target_count", 0) or 0),
                "check_count": int(data.get("check_count", 0) or 0),
                "failed_checks": [item for item in failed_checks if item],
            }
        )
    return validations


def aggregate_hook_order_boundary(hook_order_validations: list[dict[str, Any]]) -> dict[str, Any]:
    if not hook_order_validations:
        return {}
    boundaries = unique_list(
        str(validation.get("proof_boundary", ""))
        for validation in hook_order_validations
        if validation.get("proof_boundary")
    )
    mechanisms = unique_list(
        str(validation.get("hook_mechanism", ""))
        for validation in hook_order_validations
        if validation.get("hook_mechanism")
    )
    non_mutating_values = {
        bool(validation.get("non_mutating_instruction_events"))
        for validation in hook_order_validations
        if "non_mutating_instruction_events" in validation
    }
    return {
        "proof_boundary": ",".join(boundaries),
        "hook_mechanisms": mechanisms,
        "non_mutating_instruction_events": all(non_mutating_values) if non_mutating_values else "",
    }


def attach_rmw_pre_state_proof(
    events: list[dict[str, Any]],
    hook_order_validations: list[dict[str, Any]],
) -> None:
    proof = rmw_pre_state_proof(hook_order_validations)
    for event in events:
        for item in dict_items(event.get("effects")):
            operand = rmw_old_byte_operand(item)
            if operand is None:
                continue
            item["pre_state_sample"] = "hook_pre_instruction"
            item["pre_state_source"] = str(operand.get("value_source", ""))
            item["pre_state_value_hex"] = str(operand.get("value", ""))
            item["pre_state_proof_status"] = proof["proof_status"]
            item["pre_state_validation"] = proof["validation"]
            item["pre_state_validation_kind"] = "hook_order_probe"
            item["pre_state_validation_count"] = len(hook_order_validations)
            item["pre_state_observation_model"] = proof["hook_mechanism"]
            item["pre_state_proof_boundary"] = proof["proof_boundary"]
            if proof["non_mutating_instruction_event"] != "":
                item["pre_state_non_mutating_instruction_event"] = proof["non_mutating_instruction_event"]
            if proof["source"]:
                item["pre_state_validation_source"] = proof["source"]
            operand["pre_state_sample"] = item["pre_state_sample"]
            operand["pre_state_proof_status"] = item["pre_state_proof_status"]
            operand["pre_state_validation"] = item["pre_state_validation"]
            operand["pre_state_observation_model"] = item["pre_state_observation_model"]
            operand["pre_state_proof_boundary"] = item["pre_state_proof_boundary"]
            if "pre_state_non_mutating_instruction_event" in item:
                operand["pre_state_non_mutating_instruction_event"] = item["pre_state_non_mutating_instruction_event"]
            if proof["source"]:
                operand["pre_state_validation_source"] = proof["source"]


def rmw_pre_state_proof(hook_order_validations: list[dict[str, Any]]) -> dict[str, Any]:
    for validation in hook_order_validations:
        if validation.get("passed") and validation.get("proof_status") == "runtime_observed":
            return {
                "proof_status": "runtime_observed",
                "validation": "hook_order_probe_passed",
                "source": str(validation.get("source", "")),
                "proof_boundary": str(validation.get("proof_boundary", "")),
                "hook_mechanism": str(validation.get("hook_mechanism", "")),
                "non_mutating_instruction_event": validation.get("non_mutating_instruction_events"),
            }
    if hook_order_validations:
        return {
            "proof_status": "planned_only",
            "validation": "hook_order_probe_not_validated",
            "source": str(hook_order_validations[0].get("source", "")),
            "proof_boundary": str(hook_order_validations[0].get("proof_boundary", "")),
            "hook_mechanism": str(hook_order_validations[0].get("hook_mechanism", "")),
            "non_mutating_instruction_event": hook_order_validations[0].get("non_mutating_instruction_events", ""),
        }
    return {
        "proof_status": "planned_only",
        "validation": "missing_hook_order_probe",
        "source": "",
        "proof_boundary": "",
        "hook_mechanism": "",
        "non_mutating_instruction_event": "",
    }


def rmw_old_byte_operand(item: dict[str, Any]) -> dict[str, Any] | None:
    if item.get("access") != "write" or item.get("kind") != "memory_write":
        return None
    operation = str(item.get("operation", "")).lower()
    if "[hl]" not in operation:
        return None
    address = str(item.get("address_hex", "")).upper()
    for operand in dict_items(item.get("source_operands")):
        if operand.get("kind") != "memory":
            continue
        if str(operand.get("address", "")).upper() != address:
            continue
        if operand.get("value") in {None, ""}:
            continue
        if operand.get("value_source") != "observed_memory_snapshot":
            continue
        return operand
    return None


def trace_paths_from_data(data: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(data, dict):
        for key in ("trace", "traces", "effective_traces"):
            paths.extend(string_items(data.get(key)))
        trace_output = data.get("trace_output")
        if isinstance(trace_output, dict):
            paths.extend(string_items(trace_output.get("path")))
        for key in ("output", "outputs", "trace_synthesis_execution"):
            paths.extend(trace_paths_from_data(data.get(key)))
        for value in data.values():
            if isinstance(value, list):
                for item in value:
                    paths.extend(trace_paths_from_data(item))
    elif isinstance(data, list):
        for item in data:
            paths.extend(trace_paths_from_data(item))
    return unique_list(path for path in paths if str(path).lower().endswith((".json", ".jsonl")))


def count_effects(events: list[dict[str, Any]], kind: str) -> int:
    return sum(1 for event in events for item in event.get("effects", []) if item.get("kind") == kind)


def count_effect_proof_statuses(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in iter_effect_items(events):
        proof = effect_item_proof_status(item)
        counts[proof] = counts.get(proof, 0) + 1
    return counts


def count_effects_by_proof_status(events: list[dict[str, Any]], proof_status: str) -> int:
    return sum(1 for item in iter_effect_items(events) if effect_item_proof_status(item) == proof_status)


def count_hardware_gated_effects(events: list[dict[str, Any]]) -> int:
    return sum(
        1
        for item in iter_effect_items(events)
        if item.get("hardware_event_required") and not item.get("hardware_runtime_event")
    )


def count_hardware_runtime_event_effects(events: list[dict[str, Any]]) -> int:
    return sum(
        1
        for item in iter_effect_items(events)
        if item.get("hardware_event_required") and item.get("hardware_runtime_event")
    )


def iter_effect_items(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for event in events
        for item in event.get("effects", [])
        if isinstance(item, dict)
    ]


def effect_item_proof_status(item: dict[str, Any]) -> str:
    return normalize_effect_proof_status(str(item.get("proof_status") or "instruction_observed"))


def count_side_effects(events: list[dict[str, Any]], *, category: str = "") -> int:
    return sum(
        1
        for event in events
        for item in event.get("effects", [])
        if item.get("access") == "side_effect" and (not category or item.get("category") == category)
    )


def count_unmodeled_effects(events: list[dict[str, Any]]) -> int:
    return sum(1 for event in events for item in event.get("effects", []) if item.get("access") == "unmodeled")


def count_rmw_pre_state_samples(events: list[dict[str, Any]], *, proof_status: str = "") -> int:
    return sum(
        1
        for event in events
        for item in event.get("effects", [])
        if item.get("pre_state_sample") == "hook_pre_instruction"
        and (not proof_status or item.get("pre_state_proof_status") == proof_status)
    )


def count_rmw_pre_state_validation_values(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        for item in event.get("effects", []):
            if item.get("pre_state_sample") != "hook_pre_instruction":
                continue
            value = str(item.get("pre_state_validation", "") or "unknown")
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def count_watch_effects(events: list[dict[str, Any]], *, access: str) -> int:
    return sum(1 for event in events for hit in event.get("watch_hits", []) if hit.get("access") == access)


def count_watch_hits(events: list[dict[str, Any]]) -> int:
    return sum(1 for event in events for _hit in event.get("watch_hits", []))


def count_watch_hit_field_values(events: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        for hit in event.get("watch_hits", []):
            value = str(hit.get(field, "") or "unknown")
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def count_effect_field_values(events: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        for item in event.get("effects", []):
            value = str(item.get(field, "") or "unknown")
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def count_effect_post_value_status(events: list[dict[str, Any]], status: str = "") -> int:
    return sum(
        1
        for event in events
        for item in event.get("effects", [])
        if item.get("post_value_status")
        and (not status or item.get("post_value_status") == status)
    )


def count_effect_post_register_status(events: list[dict[str, Any]], status: str = "") -> int:
    return sum(
        1
        for event in events
        for item in event.get("effects", [])
        if item.get("post_register_status")
        and (not status or item.get("post_register_status") == status)
    )


def count_unmodeled_observed_changes(events: list[dict[str, Any]]) -> int:
    count = 0
    for event in events:
        changes = event.get("unmodeled_observed_changes")
        if isinstance(changes, list):
            count += sum(1 for item in changes if isinstance(item, dict))
    return count


def register_operand(register: str, frame: InstructionFrame) -> dict[str, Any]:
    register = register.lower()
    width = 4 if register in {"af", "bc", "de", "hl", "sp"} else 2
    value = pair_value_if_known(frame, register) if register in {"af", "bc", "de", "hl", "sp"} else reg_value_if_known(frame, register)
    out = {"kind": "register", "name": register}
    if value is not None:
        out["value"] = f"{value:0{width}X}"
        out["value_source"] = "pre_register"
    else:
        out["value_source"] = "missing_pre_register"
    return out


def memory_operand(address: int, *, value: int | None = None, value_source: str = "") -> dict[str, Any]:
    out = {"kind": "memory", "address": f"{address & 0xFFFF:04X}"}
    if value is not None:
        out["value"] = f"{value & 0xFF:02X}"
        if value_source:
            out["value_source"] = value_source
    return out


def hardware_memory_operand(address: int, *, hardware_state: dict[str, int]) -> dict[str, Any]:
    operand = memory_operand(address)
    bank = hardware_memory_bank(hardware_state, address)
    if bank is None:
        return operand
    operand["bank"] = f"{bank & 0xFF:02X}"
    operand["bank_source"] = hardware_memory_bank_source(address)
    operand["address_key"] = address_key(f"{bank & 0xFF:02X}:{address & 0xFFFF:04X}")
    if 0xA000 <= (address & 0xFFFF) <= 0xBFFF and "sram_enabled" in hardware_state:
        operand["sram_enabled"] = int(hardware_state["sram_enabled"]) & 0xFF
        operand["sram_enabled_source"] = "bank_state.sram_enabled"
    return operand


def immediate_operand(value: int) -> dict[str, Any]:
    return {"kind": "immediate", "value": f"{value & 0xFFFF:04X}", "value_source": "instruction_operand"}


def immediate_byte_operand(value: int) -> dict[str, Any]:
    return {"kind": "immediate", "value": f"{value & 0xFF:02X}", "value_source": "instruction_operand"}


def constant_operand(value: int, *, value_source: str) -> dict[str, Any]:
    return {"kind": "immediate", "value": f"{value & 0xFF:02X}", "value_source": value_source}


def operand_value_source(operand: dict[str, Any] | None) -> str:
    if not isinstance(operand, dict):
        return ""
    return str(operand.get("value_source", ""))


def operand_int_value(operand: dict[str, Any]) -> int | None:
    value = operand.get("value")
    if value is None:
        return None
    try:
        return int(str(value), 16)
    except ValueError:
        return None


def frame_memory_value(frame: InstructionFrame, address: int) -> int | None:
    value, _source = frame_memory_sample(frame, address)
    return value


def frame_memory_sample(frame: InstructionFrame, address: int) -> tuple[int | None, str]:
    target = address & 0xFFFF
    for raw_address, value in frame.memory:
        if (int(raw_address) & 0xFFFF) == target:
            return int(value) & 0xFF, "observed_memory_snapshot"
    return None, ""


def modeled_value_source(source: str) -> str:
    return f"modeled_from_{source}" if source else "modeled_from_unknown_memory"


def reg_value(frame: InstructionFrame, register: str) -> int:
    register = register.lower()
    if register == "f":
        return int(frame.F) & 0xFF
    return int(getattr(frame, register.upper())) & 0xFF


def reg_value_if_known(frame: InstructionFrame, register: str) -> int | None:
    if not frame_register_known(frame, register):
        return None
    return reg_value(frame, register)


def pair_value(frame: InstructionFrame, pair: str) -> int:
    pair = pair.lower()
    if pair == "af":
        return ((reg_value(frame, "a") << 8) | reg_value(frame, "f")) & 0xFFFF
    if pair == "bc":
        return ((reg_value(frame, "b") << 8) | reg_value(frame, "c")) & 0xFFFF
    if pair == "de":
        return ((reg_value(frame, "d") << 8) | reg_value(frame, "e")) & 0xFFFF
    if pair == "hl":
        return int(frame.HL) & 0xFFFF
    if pair == "sp":
        return int(frame.SP) & 0xFFFF
    raise KeyError(pair)


def pair_value_if_known(frame: InstructionFrame, pair: str) -> int | None:
    pair = pair.lower()
    if pair == "af":
        return pair_value(frame, pair) if frame_register_known(frame, "A") and frame_register_known(frame, "F") else None
    if pair == "bc":
        return pair_value(frame, pair) if frame_register_known(frame, "B") and frame_register_known(frame, "C") else None
    if pair == "de":
        return pair_value(frame, pair) if frame_register_known(frame, "D") and frame_register_known(frame, "E") else None
    if pair == "hl":
        return pair_value(frame, pair) if frame_register_known(frame, "HL") or (frame_register_known(frame, "H") and frame_register_known(frame, "L")) else None
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


def u16_from_operand(instruction: Instruction) -> int:
    if len(instruction.operand) < 2:
        return 0
    return int(instruction.operand[0]) | (int(instruction.operand[1]) << 8)


def signed8(value: int) -> int:
    value &= 0xFF
    return value - 0x100 if value & 0x80 else value


def weakest_effect_proof_status(values: Any) -> str:
    order = {
        "planned_only": 0,
        "state_materialized": 1,
        "runtime_observed": 2,
        "instruction_observed": 3,
        "taint_proven": 4,
    }
    statuses = [normalize_effect_proof_status(value) for value in string_items(values)]
    return min(statuses or ["instruction_observed"], key=lambda status: order.get(status, 0))


def normalize_effect_proof_status(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "planned": "planned_only",
        "instruction": "instruction_observed",
        "runtime": "runtime_observed",
        "observed": "runtime_observed",
        "taint": "taint_proven",
    }
    text = aliases.get(text, text)
    return text if text in {
        "planned_only",
        "state_materialized",
        "runtime_observed",
        "instruction_observed",
        "taint_proven",
    } else "planned_only"


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
