from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
PUBLIC_ONLY_SCOPE = "public_only"

ALLOWED_PROOF_STATUSES = {
    "exact_rom_proof",
    "mirror_proof",
    "static_mirror_only",
    "emulator_evidence",
    "unreachable",
    "unsupported",
    "budget_blocked",
    "missing_evidence",
    "missing_proof_artifact",
}
ALLOWED_SURFACE_FACT_BUCKETS = {
    "boss_ai",
    "battle",
    "damage",
    "script_vm",
    "map",
    "menu",
    "graphics",
    "audio",
    "save_rtc",
    "bank",
    "content",
    "runtime",
    "link_serial",
}
REQUIRED_IDENTITY_FIELDS = (
    "rom_sha256",
    "symbols_sha256",
    "map_sha256",
    "rule_map_sha256",
    "source_tree_sha256",
    "dirty_diff_hash",
)
ALLOWED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "kind",
    "surface",
    "class_id",
    "class_fingerprint",
    "identity",
    "raw_state_provenance",
    "reachable_proof",
    "checkpoint",
    "rng_assumptions",
    "rtc_assumptions",
    "backend",
    "public_info_scope",
    "public_facts",
    "known_to_engine_facts",
    "hidden_facts",
    "legal_exception_facts",
    "surface_facts",
    "proof_status",
    "missing_evidence",
    "blocking_gaps",
    "known_limits",
    "minimization",
    "source_refs",
    "valid",
    "validation_errors",
}
HIDDEN_FIELD_RE = re.compile(r"(^|_)(hidden|private|selected|current_input|current_turn_input)(_|$)")


def build_canonical_state_class(
    *,
    surface: str,
    identity: dict[str, Any],
    public_facts: dict[str, Any] | None = None,
    surface_facts: dict[str, Any] | None = None,
    backend: str = "static",
    proof_status: str = "missing_evidence",
    raw_state_provenance: dict[str, Any] | None = None,
    reachable_proof: dict[str, Any] | None = None,
    checkpoint: dict[str, Any] | None = None,
    rng_assumptions: dict[str, Any] | None = None,
    rtc_assumptions: dict[str, Any] | None = None,
    known_to_engine_facts: dict[str, Any] | None = None,
    hidden_facts: dict[str, Any] | None = None,
    legal_exception_facts: dict[str, Any] | None = None,
    public_info_scope: str = PUBLIC_ONLY_SCOPE,
    missing_evidence: list[str] | tuple[str, ...] | None = None,
    blocking_gaps: list[str] | tuple[str, ...] | None = None,
    known_limits: list[str] | tuple[str, ...] | None = None,
    minimization: dict[str, Any] | None = None,
    source_refs: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "kind": "canonical_state_class",
        "surface": surface,
        "class_id": "",
        "class_fingerprint": "",
        "identity": normalize_jsonable(identity),
        "raw_state_provenance": normalize_jsonable(raw_state_provenance or {}),
        "reachable_proof": normalize_jsonable(reachable_proof or {}),
        "checkpoint": normalize_jsonable(checkpoint or {}),
        "rng_assumptions": normalize_jsonable(rng_assumptions or {}),
        "rtc_assumptions": normalize_jsonable(rtc_assumptions or {}),
        "backend": backend,
        "public_info_scope": public_info_scope,
        "public_facts": normalize_jsonable(public_facts or {}),
        "known_to_engine_facts": normalize_jsonable(known_to_engine_facts or {}),
        "hidden_facts": normalize_jsonable(hidden_facts or {}),
        "legal_exception_facts": normalize_jsonable(legal_exception_facts or {}),
        "surface_facts": normalize_jsonable(surface_facts or {}),
        "proof_status": proof_status,
        "missing_evidence": list(missing_evidence or ()),
        "blocking_gaps": list(blocking_gaps or ()),
        "known_limits": list(known_limits or ()),
        "minimization": normalize_jsonable(minimization or {}),
        "source_refs": list(source_refs or ()),
    }
    validation_errors = validate_canonical_state_class(record)
    if not validation_errors:
        fingerprint = class_fingerprint(record)
        record["class_fingerprint"] = fingerprint
        record["class_id"] = "csc_" + fingerprint[:20]
        validation_errors = validate_canonical_state_class(record)
    record["valid"] = not validation_errors
    record["validation_errors"] = validation_errors
    return record


def validate_canonical_state_class(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    unknown_fields = sorted(set(record) - ALLOWED_TOP_LEVEL_FIELDS)
    if unknown_fields:
        errors.append("unknown top-level fields: " + ", ".join(unknown_fields))
    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    if record.get("kind") != "canonical_state_class":
        errors.append("kind must be canonical_state_class")
    if not isinstance(record.get("surface"), str) or not record.get("surface"):
        errors.append("surface must be a non-empty string")
    identity = record.get("identity")
    if not isinstance(identity, dict):
        errors.append("identity must be an object")
    else:
        for field in REQUIRED_IDENTITY_FIELDS:
            value = identity.get(field)
            if not isinstance(value, str) or not value:
                errors.append(f"identity.{field} must be a non-empty string")
    proof_status = record.get("proof_status")
    if proof_status not in ALLOWED_PROOF_STATUSES:
        errors.append(f"proof_status must be one of {sorted(ALLOWED_PROOF_STATUSES)}")
    surface_facts = record.get("surface_facts")
    if not isinstance(surface_facts, dict):
        errors.append("surface_facts must be an object")
    else:
        bad_buckets = sorted(set(surface_facts) - ALLOWED_SURFACE_FACT_BUCKETS)
        if bad_buckets:
            errors.append("unsupported surface_facts buckets: " + ", ".join(bad_buckets))
    for field in (
        "public_facts",
        "known_to_engine_facts",
        "hidden_facts",
        "legal_exception_facts",
        "rng_assumptions",
        "rtc_assumptions",
        "raw_state_provenance",
        "reachable_proof",
        "checkpoint",
        "minimization",
    ):
        if not isinstance(record.get(field), dict):
            errors.append(f"{field} must be an object")
    for field in ("missing_evidence", "blocking_gaps", "known_limits", "source_refs"):
        if not isinstance(record.get(field), list):
            errors.append(f"{field} must be a list")
    if record.get("public_info_scope") == PUBLIC_ONLY_SCOPE:
        if record.get("hidden_facts"):
            errors.append("public_only classes must not include hidden_facts")
        errors.extend(hidden_public_fact_errors(record.get("public_facts", {}), "public_facts"))
    class_id = record.get("class_id")
    fingerprint = record.get("class_fingerprint")
    if class_id or fingerprint:
        expected = class_fingerprint(record)
        if fingerprint != expected:
            errors.append("class_fingerprint does not match normalized class facts")
        if class_id != "csc_" + expected[:20]:
            errors.append("class_id does not match normalized class facts")
    return errors


def hidden_public_fact_errors(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if HIDDEN_FIELD_RE.search(str(key)):
                errors.append(f"{child_path}: hidden/private fact in public-only class")
            errors.extend(hidden_public_fact_errors(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(hidden_public_fact_errors(child, f"{path}[{index}]"))
    return errors


def class_fingerprint(record: dict[str, Any]) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "surface": record.get("surface", ""),
        "identity": record.get("identity", {}),
        "backend": record.get("backend", ""),
        "public_info_scope": record.get("public_info_scope", ""),
        "public_facts": record.get("public_facts", {}),
        "known_to_engine_facts": record.get("known_to_engine_facts", {}),
        "legal_exception_facts": record.get("legal_exception_facts", {}),
        "surface_facts": record.get("surface_facts", {}),
        "rng_assumptions": record.get("rng_assumptions", {}),
        "rtc_assumptions": record.get("rtc_assumptions", {}),
    }
    encoded = json.dumps(normalize_jsonable(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest().upper()


def normalize_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): normalize_jsonable(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (list, tuple)):
        return [normalize_jsonable(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    return value


def stable_json_hash(value: Any) -> str:
    encoded = json.dumps(normalize_jsonable(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest().upper()
