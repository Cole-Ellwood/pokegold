from __future__ import annotations

from typing import Any

from .evidence import evidence_atom, normalize_proof_status


SCHEMA_VERSION = 1
KIND = "runtime_event_envelope"

EVENT_KINDS = {
    "instruction",
    "watch_change",
    "control_flow",
    "memory_effect",
    "memory_read",
    "memory_write",
    "dynamic_write",
    "hardware_event",
    "rng_draw",
    "script_vm",
    "text_menu",
}
OBSERVATION_TYPES = {
    "frame_sample",
    "instruction_pre_state",
    "modeled_effect",
    "explicit_hardware_event",
    "inferred_from_report_fields",
    "planned_only",
}


def runtime_event_envelope(
    *,
    event_kind: str,
    source_kind: str,
    payload: dict[str, Any] | None = None,
    source_report: str = "",
    seq: int | None = None,
    frame: int | None = None,
    pc_bank_address: str = "",
    pc_label: str = "",
    proof_status: Any = "planned_only",
    observation_type: str = "planned_only",
    scope: dict[str, Any] | None = None,
    subjects: dict[str, Any] | None = None,
    precision: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event_kind = normalize_event_kind(event_kind)
    observation_type = normalize_observation_type(observation_type)
    proof = normalize_proof_status(proof_status)
    source_kind = str(source_kind or "")
    source_report = str(source_report or "")
    event: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "event_kind": event_kind,
        "source_kind": source_kind,
        "source_report": source_report,
        "seq": seq,
        "frame": frame,
        "pc_bank_address": str(pc_bank_address or ""),
        "pc_label": str(pc_label or ""),
        "proof_status": proof,
        "observation_type": observation_type,
        "scope": clean_dict(scope),
        "subjects": clean_dict(subjects),
        "precision": clean_dict(precision),
        "validation": clean_dict(validation),
        "payload": dict(payload or {}),
    }
    event["evidence_atom"] = evidence_atom(
        claim_type=f"runtime_event.{event_kind}",
        origin=source_kind,
        observation_type=observation_type,
        proof_status=proof,
        source_report=source_report,
        source_kind=source_kind,
        scope=event["scope"],
        subjects=event["subjects"],
        precision=event["precision"],
        validation=event["validation"],
        detail={"pc_bank_address": event["pc_bank_address"], "pc_label": event["pc_label"]},
    )
    return event


def instruction_record_event(
    record: dict[str, Any],
    *,
    source_report: str = "",
) -> dict[str, Any]:
    bank = optional_int(record.get("bank"))
    pc = optional_int(record.get("pc"))
    pc_bank_address = ""
    if bank is not None and pc is not None:
        pc_bank_address = f"{bank:02X}:{pc:04X}"
    return runtime_event_envelope(
        event_kind="instruction",
        source_kind=str(record.get("kind") or "instruction_trace"),
        source_report=source_report,
        seq=optional_int(record.get("seq")),
        frame=optional_int(record.get("frame")),
        pc_bank_address=pc_bank_address,
        pc_label=str(record.get("label") or record.get("pc_label") or ""),
        proof_status="instruction_observed",
        observation_type="instruction_pre_state",
        scope={"backend": record.get("backend", "")},
        subjects={
            "addresses": [pc_bank_address] if pc_bank_address else [],
            "registers": sorted(str(key) for key in dict_value(record.get("registers")).keys()),
        },
        precision={"timing": "pre_instruction_hook"},
        validation={"native_record_kind": record.get("kind", "")},
        payload=record,
    )


def inferred_trace_index_event(
    record: dict[str, Any],
    *,
    source_report: str = "",
) -> dict[str, Any]:
    event_type = str(record.get("event_type") or record.get("kind") or "control_flow")
    return runtime_event_envelope(
        event_kind=event_type,
        source_kind="trace_index",
        source_report=source_report,
        seq=optional_int(record.get("seq")),
        frame=optional_int(record.get("frame")),
        pc_bank_address=str(record.get("pc_bank_address") or record.get("address") or ""),
        pc_label=str(record.get("label") or ""),
        proof_status=record.get("proof_status") or "runtime_observed",
        observation_type="inferred_from_report_fields",
        scope={"inferred": True},
        subjects={"symbols": [record.get("symbol", "")]},
        precision={"source": "field_inference"},
        validation={"native_event_type": event_type},
        payload=record,
    )


def hardware_event_required(
    *,
    event_kind: str,
    reason: str,
    source_kind: str = "runtime_trace",
    source_report: str = "",
) -> dict[str, Any]:
    return runtime_event_envelope(
        event_kind=event_kind,
        source_kind=source_kind,
        source_report=source_report,
        proof_status="planned_only",
        observation_type="planned_only",
        validation={"hardware_event_required": True, "reason": reason},
        payload={"reason": reason},
    )


def normalize_event_kind(value: str) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if text in EVENT_KINDS:
        return text
    aliases = {
        "instruction_trace": "instruction",
        "write_attribution": "dynamic_write",
        "write": "memory_write",
        "read": "memory_read",
        "effect": "memory_effect",
        "apu": "hardware_event",
        "dma": "hardware_event",
        "interrupt": "hardware_event",
    }
    return aliases.get(text, "hardware_event" if text.endswith("_event") else "control_flow")


def normalize_observation_type(value: str) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return text if text in OBSERVATION_TYPES else "planned_only"


def optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(str(value), 0)
    except (TypeError, ValueError):
        return None


def dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def clean_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {str(key): child for key, child in value.items() if child not in (None, "", [], {})}
