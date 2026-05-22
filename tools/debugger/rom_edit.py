from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .handoff_log import DEFAULT_STORE, ROOT, is_mutual_verified, load_rows


PASS = "pass"
FAIL = "fail"

RELEASE_SMOKE_GATE_NAME = "release_smoke"
SAVE_FORMAT_GATE_NAME = "save_format_version"
RELEASE_SMOKE_COMMAND = "python tools/audit/check_release_smoke.py"
SAVE_FORMAT_COMMAND = "python tools/audit/check_save_format_version.py"
PROTECTED_BRANCHES = frozenset(
    {
        "main",
        "master",
        "origin/main",
        "origin/master",
        "refs/heads/main",
        "refs/heads/master",
    }
)


@dataclass(frozen=True)
class GateSpec:
    name: str
    command: str

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "command": self.command}


@dataclass(frozen=True)
class GateResult:
    name: str
    status: str
    command: str = ""
    detail: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "status": self.status,
            "command": self.command,
            "detail": self.detail,
        }


def touches_ram(changed_files: Sequence[str]) -> bool:
    return any(_normalize_repo_path(path).startswith("ram/") for path in changed_files)


def required_green_gate_stack(changed_files: Sequence[str]) -> tuple[GateSpec, ...]:
    gates = [GateSpec(RELEASE_SMOKE_GATE_NAME, RELEASE_SMOKE_COMMAND)]
    if touches_ram(changed_files):
        gates.insert(0, GateSpec(SAVE_FORMAT_GATE_NAME, SAVE_FORMAT_COMMAND))
    return tuple(gates)


def decide_auto_apply(
    *,
    changed_files: Sequence[str],
    gate_results: Sequence[GateResult | Mapping[str, Any]],
    handoff_phase: str,
    handoff_rows: Sequence[dict[str, Any]] | None = None,
    handoff_store: Path = DEFAULT_STORE,
    root: Path = ROOT,
    target_branch: str = "",
    merge_target: str = "",
    push_remote: bool = False,
) -> dict[str, Any]:
    """Return the P12 full-autonomy auto-apply decision without applying edits."""

    normalized_results = tuple(_normalize_gate_result(result) for result in gate_results)
    required_gates = required_green_gate_stack(changed_files)
    blocking_reasons = _gate_blocking_reasons(required_gates, normalized_results)

    if push_remote:
        blocking_reasons.append("auto-apply refuses remote push")
    if not target_branch.strip():
        blocking_reasons.append("auto-apply requires explicit target branch")
    if _is_protected_branch(target_branch):
        blocking_reasons.append(
            f"auto-apply refuses protected target branch {target_branch!r}"
        )
    if _is_protected_branch(merge_target):
        blocking_reasons.append(
            f"auto-apply refuses auto-merge to protected branch {merge_target!r}"
        )

    rows = (
        list(handoff_rows)
        if handoff_rows is not None
        else load_rows(_resolve_store(handoff_store, root))
    )
    handoff_mutual_verified, handoff_reasons = is_mutual_verified(rows, handoff_phase)
    if not handoff_mutual_verified:
        blocking_reasons.append(
            "handoff phase is not mutual-verified: " + "; ".join(handoff_reasons)
        )

    return {
        "kind": "rom_edit_auto_apply_decision",
        "allowed": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
        "changed_files": tuple(changed_files),
        "required_gates": tuple(gate.as_dict() for gate in required_gates),
        "gate_results": tuple(result.as_dict() for result in normalized_results),
        "handoff_phase": handoff_phase,
        "handoff_mutual_verified": handoff_mutual_verified,
        "handoff_reasons": tuple(handoff_reasons),
        "target_branch": target_branch,
        "merge_target": merge_target,
        "push_remote": push_remote,
        "requires_mutual_verified": True,
    }


def _gate_blocking_reasons(
    required_gates: Sequence[GateSpec],
    gate_results: Sequence[GateResult],
) -> list[str]:
    reasons: list[str] = []
    result_by_name = {result.name: result for result in gate_results}
    for gate in required_gates:
        result = result_by_name.get(gate.name)
        if result is None:
            reasons.append(
                f"required green-gate audit {gate.name!r} has no result"
            )
            continue
        if result.status != PASS:
            detail = f": {result.detail}" if result.detail else ""
            reasons.append(
                f"required green-gate audit {gate.name!r} did not pass"
                f" (status={result.status!r}){detail}"
            )
    return reasons


def _normalize_gate_result(result: GateResult | Mapping[str, Any]) -> GateResult:
    if isinstance(result, GateResult):
        return result
    return GateResult(
        name=str(result.get("name", "")),
        status=str(result.get("status", "")),
        command=str(result.get("command", "")),
        detail=str(result.get("detail", "")),
    )


def _normalize_repo_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _is_protected_branch(branch: str) -> bool:
    return branch.strip() in PROTECTED_BRANCHES


def _resolve_store(store: Path, root: Path) -> Path:
    return store if store.is_absolute() else root / store
