from __future__ import annotations

from typing import Any


PROOF_GRADE_HARDWARE_RUNTIME_EVIDENCE = {
    "non_mutating_event_recorder",
    "runtime_hardware_event_observed",
}
GENERIC_HARDWARE_EVENT_LABELS = {
    "emulator_hardware_event",
    "hardware_event_observed",
}
HARDWARE_EVIDENCE_LABEL_FIELDS = (
    "evidence_source",
    "evidence_status",
    "runtime_observation",
    "event_source",
    "recorder_kind",
    "source_kind",
)


def hardware_runtime_event_boundary(value: dict[str, Any]) -> dict[str, Any]:
    labels_by_field = hardware_evidence_labels_by_field(value)
    labels = sorted({label for values in labels_by_field.values() for label in values})
    generic_label_present = bool(set(labels) & GENERIC_HARDWARE_EVENT_LABELS) or bool(
        value.get("hardware_event_observed")
    )
    non_mutating_recorder = bool(value.get("non_mutating_event_recorder")) or any(
        label == "non_mutating_event_recorder" for label in labels
    )
    explicit_label = next(
        (label for label in labels if label in PROOF_GRADE_HARDWARE_RUNTIME_EVIDENCE),
        "",
    )
    runtime_flag = bool(value.get("hardware_runtime_event"))
    runtime_event_present = runtime_flag or non_mutating_recorder or bool(explicit_label)
    if non_mutating_recorder:
        identity = "non_mutating_event_recorder"
    elif runtime_flag:
        identity = "hardware_runtime_event_flag"
    elif explicit_label:
        identity = explicit_label
    elif generic_label_present:
        identity = "generic_hardware_event_label"
    else:
        identity = ""
    return {
        "runtime_event_present": runtime_event_present,
        "hardware_event_identity": identity,
        "hardware_event_labels": labels,
        "hardware_runtime_event_source_fields": sorted(labels_by_field),
        "hardware_generic_event_label_present": generic_label_present,
        "hardware_event_types": sorted(hardware_event_types(value)),
    }


def hardware_evidence_labels_by_field(value: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for field in HARDWARE_EVIDENCE_LABEL_FIELDS:
        labels = string_values(value.get(field))
        if labels:
            out[field] = labels
    return out


def hardware_event_types(value: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for key in ("hardware_event_type", "hardware_event_types", "event_type", "event_types"):
        out.update(string_values(value.get(key)))
    return out


def string_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str) and not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [str(key) for key, enabled in value.items() if enabled]
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value if item not in {None, ""}]
    return [str(value)]
