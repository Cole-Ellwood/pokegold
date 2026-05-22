from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
import json
from typing import Any


PROOF_STATUSES = {
    "planned_only",
    "state_materialized",
    "runtime_observed",
    "instruction_observed",
    "taint_proven",
    "mirror_passed",
    "mirror_failed",
}

PROOF_STATUS_RANK = {
    "planned_only": 0,
    "state_materialized": 1,
    "mirror_passed": 2,
    "runtime_observed": 3,
    "instruction_observed": 4,
    "taint_proven": 5,
    "mirror_failed": 5,
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


@dataclass(frozen=True)
class EvidenceAtom:
    claim_type: str
    origin: str
    observation_type: str
    proof_status: Any
    source_report: str = ""
    source_kind: str = ""
    scope: dict[str, Any] = field(default_factory=dict)
    subjects: dict[str, Any] = field(default_factory=dict)
    precision: dict[str, Any] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "claim_type": str(self.claim_type or "evidence.claim"),
            "origin": str(self.origin or ""),
            "observation_type": str(self.observation_type or ""),
            "proof_status": normalize_proof_status(self.proof_status),
            "source_report": str(self.source_report or ""),
            "source_kind": str(self.source_kind or ""),
            "scope": clean_mapping(self.scope),
            "subjects": clean_subjects(self.subjects),
            "precision": clean_mapping(self.precision),
            "validation": clean_mapping(self.validation),
            "detail": clean_mapping(self.detail),
        }


@dataclass(frozen=True)
class BankStateRecord:
    name: str
    value: int | None
    source: str
    source_kind: str
    state_kind: str
    inferred: bool
    valid_for_spaces: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        value = None if self.value is None else int(self.value) & 0xFF
        out = {
            "name": str(self.name),
            "source": str(self.source),
            "source_kind": str(self.source_kind),
            "state_kind": str(self.state_kind),
            "inferred": bool(self.inferred),
            "valid_for_space": self.valid_for_spaces[0] if self.valid_for_spaces else "",
            "valid_for_spaces": list(self.valid_for_spaces),
        }
        if value is not None:
            out["value"] = value
            out["value_hex"] = f"{value:02X}"
        return out


@dataclass(frozen=True)
class BankState:
    records: tuple[BankStateRecord, ...] = ()

    def as_records(self) -> list[dict[str, Any]]:
        return [record.as_dict() for record in self.records]

    def as_state(self) -> dict[str, int]:
        return {
            record.name: int(record.value) & 0xFF
            for record in self.records
            if record.value is not None
        }


def evidence_atom(
    *,
    claim_type: str,
    origin: str,
    observation_type: str,
    proof_status: Any,
    source_report: str = "",
    source_kind: str = "",
    scope: dict[str, Any] | None = None,
    subjects: dict[str, Any] | None = None,
    precision: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return EvidenceAtom(
        claim_type=claim_type,
        origin=origin,
        observation_type=observation_type,
        proof_status=proof_status,
        source_report=source_report,
        source_kind=source_kind,
        scope=scope or {},
        subjects=subjects or {},
        precision=precision or {},
        validation=validation or {},
        detail=detail or {},
    ).as_dict()


def bank_state_records(
    items: Iterable[tuple[str, int]],
    *,
    source_for_name: Callable[[str], str] | None = None,
    valid_spaces_by_name: dict[str, tuple[str, ...]] | None = None,
) -> list[dict[str, Any]]:
    return BankState(
        tuple(
            bank_state_record(
                name=str(name),
                value=int(value) & 0xFF,
                source=source_for_name(str(name)) if source_for_name else "",
                valid_for_spaces=(valid_spaces_by_name or BANK_STATE_VALID_SPACES).get(str(name), ()),
            )
            for name, value in items
            if not str(name).endswith("_inferred")
        )
    ).as_records()


def bank_state_record(
    *,
    name: str,
    value: int | None,
    source: str = "",
    valid_for_spaces: Iterable[str] = (),
) -> BankStateRecord:
    source_kind, state_kind, inferred = bank_state_source_semantics(name=name, value=value, source=source)
    return BankStateRecord(
        name=name,
        value=value,
        source=source,
        source_kind=source_kind,
        state_kind=state_kind,
        inferred=inferred,
        valid_for_spaces=tuple(str(space) for space in valid_for_spaces if str(space)),
    )


def bank_state_source_semantics(*, name: str, value: int | None, source: str) -> tuple[str, str, bool]:
    if name == "sram_enabled" and value == 0:
        return ("bank_state", "sram_disabled", False)
    if source.startswith("inferred_bank_state."):
        return ("inferred_bank_state", "inferred_from_io_write", True)
    if source.startswith("mapper_bank_state."):
        return ("mapper_bank_state", "mapper_derived", False)
    if source.startswith("default_bank_state."):
        return ("default_bank_state", "default", False)
    if source.startswith("bank_state."):
        return ("bank_state", "runtime_observed", False)
    return ("unknown", "unknown", False)


def normalize_proof_status(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "planned": "planned_only",
        "planning": "planned_only",
        "observed": "runtime_observed",
        "runtime": "runtime_observed",
        "instruction": "instruction_observed",
        "taint": "taint_proven",
        "mirror_pass": "mirror_passed",
        "mirror_ok": "mirror_passed",
        "mirror_fail": "mirror_failed",
    }
    text = aliases.get(text, text)
    return text if text in PROOF_STATUSES else "planned_only"


def merge_evidence_atoms(*values: Any, limit: int = 24) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for value in values:
        for atom in evidence_atoms(value):
            key = json.dumps(atom, sort_keys=True, separators=(",", ":"))
            if key in seen:
                continue
            seen.add(key)
            out.append(atom)
            if len(out) >= limit:
                return out
    return out


def proof_status_by_source_summary(items: list[dict[str, Any]]) -> dict[str, str]:
    summary: dict[str, str] = {}
    for item in items:
        per_source = item.get("proof_status_by_source")
        if not isinstance(per_source, dict):
            continue
        for key, value in per_source.items():
            source_key = str(key)
            summary[source_key] = strongest_proof_status([summary.get(source_key), value])
    return dict(sorted(summary.items()))


def bank_state_record_proof_status_by_source(atoms: Any) -> dict[str, str]:
    by_source: dict[str, str] = {}
    for atom in evidence_atoms(atoms):
        proof = normalize_proof_status(atom.get("proof_status"))
        for group, records in bank_state_record_groups(atom):
            for record in records:
                name = str(record.get("name") or "")
                source = str(record.get("source") or record.get("source_kind") or "")
                if not name or not source:
                    continue
                key = f"bank_state:{group}:{name}:{source}"
                by_source[key] = strongest_proof_status([by_source.get(key), proof])
    return dict(sorted(by_source.items()))


def bank_state_record_evidence_from_atoms(atoms: Any) -> list[str]:
    evidence: list[str] = []
    for atom in evidence_atoms(atoms):
        for group, records in bank_state_record_groups(atom):
            for record in records:
                text = format_bank_state_record_evidence(group, record)
                if text:
                    evidence.append(text)
    return unique_list(evidence)[:8]


def bank_state_record_groups(value: Any, *, group: str = "") -> list[tuple[str, list[dict[str, Any]]]]:
    groups: list[tuple[str, list[dict[str, Any]]]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            if key_text.endswith("bank_state_records"):
                records = [
                    item
                    for item in dict_items(nested)
                    if item.get("name") and item.get("state_kind")
                ]
                if records:
                    groups.append((bank_state_record_group_name(key_text), records))
                continue
            if isinstance(nested, dict | list | tuple):
                groups.extend(bank_state_record_groups(nested, group=key_text))
    elif isinstance(value, list | tuple):
        for nested in value:
            if isinstance(nested, dict | list | tuple):
                groups.extend(bank_state_record_groups(nested, group=group))
    return groups


def bank_state_record_group_name(key: str) -> str:
    text = key
    suffix = "_bank_state_records"
    if text.endswith(suffix):
        text = text[: -len(suffix)]
    if text == "bank_state_records":
        return "bank_state"
    return text.strip("_") or "bank_state"


def format_bank_state_record_evidence(group: str, record: dict[str, Any]) -> str:
    name = str(record.get("name") or "")
    if not name:
        return ""
    value = bank_state_record_value_text(record)
    pieces = [f"bank_state_record={group}:{name}"]
    if value:
        pieces[0] += f"=0x{value}"
    source = str(record.get("source") or "")
    if source:
        pieces.append(f"source={source}")
    state_kind = str(record.get("state_kind") or "")
    if state_kind:
        pieces.append(f"state={state_kind}")
    valid_for = str(record.get("valid_for_space") or "")
    if valid_for:
        pieces.append(f"valid_for={valid_for}")
    return " ".join(pieces)


def bank_state_record_value_text(record: dict[str, Any]) -> str:
    value_hex = str(record.get("value_hex") or "").strip()
    if value_hex:
        return value_hex.upper().removeprefix("0X")
    value = record.get("value")
    if value is None or value == "":
        return ""
    try:
        return f"{int(str(value), 0) & 0xFF:02X}"
    except ValueError:
        return str(value)


def strongest_proof_status(values: list[Any]) -> str:
    statuses = [normalize_proof_status(value) for value in values]
    statuses = [status for status in statuses if status]
    if not statuses:
        return "planned_only"
    return max(statuses, key=lambda status: PROOF_STATUS_RANK.get(status, 0))


def evidence_atoms(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        if value.get("claim_type") and value.get("proof_status"):
            return [normalize_atom(value)]
        return evidence_atoms(value.get("evidence_atoms"))
    if isinstance(value, list | tuple):
        out: list[dict[str, Any]] = []
        for item in value:
            out.extend(evidence_atoms(item))
        return out
    return []


def normalize_atom(atom: dict[str, Any]) -> dict[str, Any]:
    return evidence_atom(
        claim_type=str(atom.get("claim_type", "")),
        origin=str(atom.get("origin", "")),
        observation_type=str(atom.get("observation_type", "")),
        proof_status=atom.get("proof_status"),
        source_report=str(atom.get("source_report", "")),
        source_kind=str(atom.get("source_kind", "")),
        scope=atom.get("scope") if isinstance(atom.get("scope"), dict) else {},
        subjects=atom.get("subjects") if isinstance(atom.get("subjects"), dict) else {},
        precision=atom.get("precision") if isinstance(atom.get("precision"), dict) else {},
        validation=atom.get("validation") if isinstance(atom.get("validation"), dict) else {},
        detail=atom.get("detail") if isinstance(atom.get("detail"), dict) else {},
    )


def clean_subjects(subjects: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in ("symbols", "addresses", "files", "registers"):
        values = string_items(subjects.get(key))
        if values:
            out[key] = unique_list(values)
    for key, value in subjects.items():
        if key in out or key in {"symbols", "addresses", "files", "registers"}:
            continue
        cleaned = clean_value(value)
        if cleaned not in ("", None, [], {}):
            out[str(key)] = cleaned
    return out


def clean_mapping(value: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, raw in value.items():
        cleaned = clean_value(raw)
        if cleaned in ("", None, [], {}):
            continue
        out[str(key)] = cleaned
    return out


def clean_value(value: Any) -> Any:
    if isinstance(value, dict):
        return clean_mapping(value)
    if isinstance(value, list | tuple):
        return [clean_value(item) for item in value if clean_value(item) not in ("", None, [], {})]
    return value


def string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value if str(item)]
    return [str(value)] if str(value) else []


def dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list | tuple):
        return [item for item in value if isinstance(item, dict)]
    return []


def unique_list(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out
