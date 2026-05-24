"""Ranked-finding orchestrator.

``rank_findings`` reads a tuple of unified-debugger JSON reports, hands each
one to its registered per-kind builder in :mod:`.builders`, calibrates each
finding's severity against ROM-surface hints, and returns a single ranked
report.

The dispatch dict (:data:`_FINDINGS_BUILDERS`) lives here so adding a new
report kind is a one-line change.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..catalog import ROOT
from .builders import (
    capability_findings,
    compare_findings,
    content_mirror_findings,
    content_scenario_findings,
    content_state_findings,
    coverage_findings,
    expectation_findings,
    explanation_findings,
    fuzz_findings,
    gate_findings,
    generation_findings,
    impact_findings,
    ingest_findings,
    instruction_trace_findings,
    investigation_findings,
    localization_findings,
    minimization_findings,
    next_step_findings,
    provenance_findings,
    replay_findings,
    runtime_state_findings,
    save_state_inspection_findings,
    setup_findings,
    slice_findings,
    state_space_findings,
    taint_findings,
    test_suggestion_findings,
    trace_index_findings,
    visualization_findings,
    watch_findings,
)
from .helpers import finding
from .severity import SEVERITY_BASE, calibrate_finding_severity


__all__ = [
    "SEVERITY_BASE",
    "display_path",
    "findings_from_report",
    "rank_findings",
    "resolve_path",
]


def rank_findings(
    *,
    reports: tuple[str, ...],
    root: Path = ROOT,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    errors: list[str] = []
    for report_path in reports:
        path = resolve_path(report_path, root=root)
        if not path.exists():
            errors.append(f"missing report: {report_path}")
            continue
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{report_path}: invalid JSON: {exc.msg}")
            continue
        findings.extend(findings_from_report(report, source=display_path(path, root=root)))

    findings = [calibrate_finding_severity(finding) for finding in findings]
    findings.sort(
        key=lambda item: (
            -int(item["severity"]),
            -float(item["confidence"]),
            item["source"],
            item["title"],
        )
    )
    return {
        "schema_version": 1,
        "kind": "unified_debugger_ranked_findings",
        "root": str(root),
        "valid": not errors,
        "report_count": len(reports),
        "error_count": len(errors),
        "errors": errors,
        "finding_count": len(findings),
        "findings": findings,
    }


def findings_from_report(report: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    kind = report.get("kind", "")
    builder = _FINDINGS_BUILDERS.get(kind)
    if builder is not None:
        return builder(report, source=source)
    return [
        finding(
            finding_type="unknown_report",
            title=f"Unsupported report kind: {kind or '<missing>'}",
            source=source,
            severity=20,
            confidence=0.2,
            evidence=[source],
            next_actions=["python -m tools.debugger ingest --changed-file <report-producer>"],
        )
    ]


def resolve_path(raw_path: str, *, root: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return root / path


def display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


_FINDINGS_BUILDERS = {
    "unified_debugger_ingest_manifest": ingest_findings,
    "unified_debugger_capability_report": capability_findings,
    "unified_debugger_watch_report": watch_findings,
    "unified_debugger_runtime_state_report": runtime_state_findings,
    "unified_debugger_save_state_inspection": save_state_inspection_findings,
    "unified_debugger_replay_plan": replay_findings,
    "unified_debugger_setup_plan": setup_findings,
    "unified_debugger_gate_plan": gate_findings,
    "unified_debugger_compare_plan": compare_findings,
    "unified_debugger_content_mirror": content_mirror_findings,
    "unified_debugger_content_scenarios": content_scenario_findings,
    "unified_debugger_content_state_materialization": content_state_findings,
    "unified_debugger_state_space": state_space_findings,
    "unified_debugger_expectation_report": expectation_findings,
    "unified_debugger_test_suggestions": test_suggestion_findings,
    "unified_debugger_provenance_report": provenance_findings,
    "unified_debugger_causal_slice": slice_findings,
    "unified_debugger_taint_report": taint_findings,
    "unified_debugger_dynamic_taint_report": taint_findings,
    "unified_debugger_causal_explanation": explanation_findings,
    "unified_debugger_localization_plan": localization_findings,
    "unified_debugger_coverage_report": coverage_findings,
    "unified_debugger_trace_index": trace_index_findings,
    "unified_debugger_instruction_trace": instruction_trace_findings,
    "unified_debugger_next_step": next_step_findings,
    "unified_debugger_minimization_plan": minimization_findings,
    "unified_debugger_generation_plan": generation_findings,
    "unified_debugger_fuzz_plan": fuzz_findings,
    "unified_debugger_impact_report": impact_findings,
    "unified_debugger_visualization": visualization_findings,
    "unified_debugger_investigation_run": investigation_findings,
}
