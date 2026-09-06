"""Independent diagnosis scoring; a green packet is not a solved bug.

The existing EvidenceAtom and report envelope carry a diagnosis.root_cause
claim. The evaluator owns the hidden accepted locations, current input basis,
assistance log, and replay verifier. Never obtain those from the submission.
The verifier must execute/check evidence, not copy report validation booleans.
This initial scorer handles one initiating cause per case; multi-cause cases
remain unsupported rather than receiving partial credit.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any


BASIS_FIELDS = (
    "rom_sha256", "symbols_sha256", "source_tree_sha256", "backend", "state_basis",
)
REPLAY_CHECKS = (
    "failure_reproduced", "causal_chain_replayed", "alternatives_rejected",
    "minimized_reproducer_replayed", "regression_failed_broken",
    "regression_passed_control",
)


def score_diagnosis(
    report: Mapping[str, Any],
    *,
    expected_basis: Mapping[str, Any],
    accepted_causes: Sequence[Mapping[str, Any]],
    verify_replay: Callable[[Mapping[str, Any]], Mapping[str, bool]],
    assistance_events: Sequence[str],
) -> dict[str, Any]:
    """Score an explicit causal claim against evaluator-owned ground truth.

    An empty accepted_causes list denotes a clean/ambiguous control, not an
    undiscovered bug. Reject missing/stale identity and wrong locations before
    replay. Missing checks, truthy strings, and submission-provided success
    markers cannot pass the independent replay gate.
    """
    atoms = report.get("evidence_atoms", [])
    claims = [atom for atom in atoms if isinstance(atom, dict)
              and atom.get("claim_type") == "diagnosis.root_cause"] if isinstance(atoms, list) else []
    problems: list[str] = []
    if not accepted_causes:
        if claims:
            problems.append("root_cause_claim_on_unconfirmed_or_clean_control")
    elif not claims:
        problems.append("no_root_cause_claim")
    else:
        if len(claims) != 1:
            problems.append("one_initiating_cause_required")
        for key in BASIS_FIELDS:
            expected = expected_basis.get(key)
            if expected in (None, "", "unknown", {}) or report.get(key) != expected:
                problems.append(f"missing_or_stale_{key}")
        if report.get("proof_status") != "complete":
            problems.append("incomplete_proof")
        if not report.get("repro_command"):
            problems.append("missing_repro_command")
        for claim in claims:
            if claim.get("proof_status") not in ("instruction_observed", "taint_proven"):
                problems.append("root_cause_not_instruction_observed")
            precision = claim.get("precision", {})
            location = {
                key: precision.get(key) for key in
                ("source_file", "source_symbol", "source_line")
            } if isinstance(precision, dict) else {}
            if location not in accepted_causes:
                problems.append("cause_location_mismatch")
            detail = claim.get("detail", {})
            if not isinstance(detail, dict):
                detail = {}
            for key in ("invariant", "causal_chain", "reproducer", "regression",
                        "scope", "uncertainty"):
                if not detail.get(key):
                    problems.append(f"missing_{key}")
        if not problems:
            try:
                checks = verify_replay(report)
            except Exception as exc:
                problems.append(f"replay_failed: {exc}")
            else:
                for key in REPLAY_CHECKS:
                    if not isinstance(checks, Mapping) or checks.get(key) is not True:
                        problems.append(key)
    solved = bool(accepted_causes) and not problems
    return {
        "solved": solved,
        "autonomous": solved and not assistance_events,
        "control_passed": not accepted_causes and not problems,
        "false_proven_claim": bool(claims) and bool(problems),
        "assistance_events": list(assistance_events),
        "problems": list(dict.fromkeys(problems)),
    }
