from __future__ import annotations

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
    return {
        "schema_version": 1,
        "claim_type": str(claim_type or "evidence.claim"),
        "origin": str(origin or ""),
        "observation_type": str(observation_type or ""),
        "proof_status": normalize_proof_status(proof_status),
        "source_report": str(source_report or ""),
        "source_kind": str(source_kind or ""),
        "scope": clean_mapping(scope or {}),
        "subjects": clean_subjects(subjects or {}),
        "precision": clean_mapping(precision or {}),
        "validation": clean_mapping(validation or {}),
        "detail": clean_mapping(detail or {}),
    }


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
