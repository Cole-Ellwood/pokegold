from __future__ import annotations

from typing import Any


def reverse_query_address_boundary_fields(result: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    requested = dict_value(result.get("requested_static_address"))
    observed = dict_value(result.get("observed_runtime_address"))
    boundary = dict_value(result.get("address_fact_boundary"))
    if requested:
        fields["requested_static_address"] = requested
    if observed:
        fields["observed_runtime_address"] = observed
    if boundary:
        fields["address_fact_boundary"] = boundary
    evidence = reverse_query_address_boundary_evidence(result)
    if evidence:
        fields["address_boundary_evidence"] = evidence
    return fields


def reverse_query_address_boundary_evidence(result: dict[str, Any]) -> list[str]:
    requested = dict_value(result.get("requested_static_address"))
    observed = dict_value(result.get("observed_runtime_address"))
    boundary = dict_value(result.get("address_fact_boundary"))
    evidence: list[str] = []
    requested_key = address_fact_key(requested)
    observed_key = address_fact_key(observed)
    if boundary:
        evidence.extend(
            [
                f"address_fact_boundary={boundary.get('kind', '')}",
                f"address_boundary_exact_runtime_address_proven={bool_text(boundary.get('exact_runtime_address_proven'))}",
                f"address_boundary_target_exact_key_required={bool_text(boundary.get('target_exact_key_required'))}",
                f"address_boundary_runtime_key_exact={bool_text(boundary.get('runtime_key_exact'))}",
                f"address_boundary_match_precision={boundary.get('match_precision', '')}",
                f"address_boundary_bank_match={boundary.get('bank_match', '')}",
            ]
        )
        ambiguous = string_items(boundary.get("ambiguous_address_keys"))
        if ambiguous:
            evidence.append(f"address_boundary_ambiguous_address_keys={','.join(ambiguous)}")
        downgrade = str(boundary.get("proof_downgrade_reason") or "")
        if downgrade:
            evidence.append(f"address_boundary_proof_downgrade_reason={downgrade}")
    if requested_key:
        evidence.append(f"requested_static_address={requested_key}")
    if observed_key:
        evidence.append(f"observed_runtime_address={observed_key}")
    return unique_list([item for item in evidence if item and not item.endswith("=")])


def reverse_query_address_boundary_addresses(result: dict[str, Any]) -> list[str]:
    requested = dict_value(result.get("requested_static_address"))
    observed = dict_value(result.get("observed_runtime_address"))
    boundary = dict_value(result.get("address_fact_boundary"))
    return unique_list(
        [
            address_fact_key(requested),
            address_fact_key(observed),
            str(result.get("matched_address_key") or ""),
            str(result.get("matched_address") or ""),
            *string_items(boundary.get("ambiguous_address_keys")),
        ]
    )


def reverse_query_address_boundary_summary(result: dict[str, Any]) -> str:
    evidence = reverse_query_address_boundary_evidence(result)
    if not evidence:
        return ""
    return " ".join(evidence[:6])


def address_fact_key(value: dict[str, Any]) -> str:
    return str(value.get("address_key") or value.get("address") or "")


def bool_text(value: Any) -> str:
    return "true" if value is True else "false"


def dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item)]
    return [str(value)] if str(value) else []


def unique_list(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        if text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out
