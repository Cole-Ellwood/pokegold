#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.debugger.report_envelope import build_report_envelope, sha256_file
from tools.boss_ai_debugger.universe import (
    EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID,
    build_boss_ai_universe_report,
)


BENCHMARK_DIR = ROOT / "audit" / "boss_ai_debugger" / "god_level_benchmark"
DEFAULT_QUESTIONS = BENCHMARK_DIR / "questions.jsonl"
DEFAULT_OUT = ROOT / ".local" / "tmp" / "boss_ai_debugger" / "god_level_benchmark.json"
PROMOTED_CHANGED_AI_SUMMARY = ROOT / "audit" / "boss_ai_debugger" / "deity_benchmark" / "artifacts" / "changed_ai_dry_run.json"
PRE_CHOICE_REPLAY_ARTIFACT = Path("audit/boss_ai_debugger/god_level_benchmark/artifacts/pre_choice_replay.json")
PRE_CHOICE_REPLAY_KNOWN_GAP = "pre-choice replay remains a separate audit until trace timing is stable."
PRE_CHOICE_REPLAY_BLOCKER = "changed_ai_pre_choice_replay_separate_audit"
PRE_CHOICE_REPLAY_EVIDENCE_ID = "boss_ai_pre_choice_replay.exact_match_corpus"
LIVE_CAPTURE_MANIFEST = Path("audit/boss_ai_trace/live_capture_manifest.json")
SCORE_MATERIALIZATION_TARGETED_KNOWN_GAP = "changed-ai suite materializes a targeted generated score batch, not all touched-rule generated scenarios."
SCORE_MATERIALIZATION_TARGETED_BLOCKER = "changed_ai_score_materialization_targeted_batch_only"
SCORE_MATERIALIZATION_FULL_ARTIFACT = Path("audit/boss_ai_debugger/god_level_benchmark/artifacts/changed_ai_score_materialization_full_fast.json")
SCORE_MATERIALIZATION_FULL_EVIDENCE_ID = "boss_ai_changed_ai_score_materialization.full_candidate_corpus"
CONTRIBUTION_COMPARISON_TRACE_ID_KNOWN_GAP = "ROM/Python contribution traces are compared only when trace ids match."
CONTRIBUTION_COMPARISON_TRACE_ID_BLOCKER = "changed_ai_contribution_comparison_trace_id_only"
CONTRIBUTION_COMPARISON_TRACE_ID_EVIDENCE_ID = "boss_ai_changed_ai_contribution_comparison.generated_trace_ids_matched"
CONTRIBUTION_REFRESH_SINGLE_ROUTE_KNOWN_GAP = "changed-ai suite refreshes one ROM contribution route, not the full live trace corpus."
CONTRIBUTION_REFRESH_SINGLE_ROUTE_BLOCKER = "changed_ai_contribution_refresh_single_route_only"
CONTRIBUTION_REFRESH_SCOPE_ARTIFACT = Path("audit/boss_ai_debugger/god_level_benchmark/artifacts/changed_ai_contribution_refresh_scope.json")
CONTRIBUTION_REFRESH_SCOPE_EVIDENCE_ID = "boss_ai_changed_ai_contribution_refresh.full_route_corpus"

REQUIRED_FIELDS = (
    "id",
    "requirement",
    "surface",
    "status",
    "blocking_gaps",
    "next_command",
    "disproof_standard",
)

COUNT_FIELDS = (
    "missing_reachable_label_count",
    "missing_rule_count",
    "missing_branch_count",
    "missing_public_read_count",
    "missing_class_id_count",
    "missing_proof_artifact_count",
    "missing_materialization_path_count",
    "missing_witness_role_count",
)

RULE_TARGET_CLASS_EVIDENCE_ID = "boss_ai_rule_target_canonical_class_ids.validated"
UNIVERSE_LABEL_EVIDENCE_ID = "boss_ai_universe_reachable_labels_classified.validated"
MATERIALIZATION_PATH_EVIDENCE_ID = "boss_ai_rule_target_materialization_paths.available"
GENERATED_SCENARIO_CLASS_EVIDENCE_ID = "boss_ai_generated_scenario_class_ids.validated"
MATERIALIZER_VERDICT_CLASS_EVIDENCE_ID = "boss_ai_materializer_verdict_class_id_passthrough.validated"
LIVE_TRACE_CLASS_EVIDENCE_ID = "boss_ai_live_trace_class_ids.validated"
CONTRIBUTION_TRACE_CLASS_EVIDENCE_ID = "boss_ai_contribution_trace_class_ids.validated"
CHANGED_AI_RUN_METADATA_EVIDENCE_ID = "boss_ai_changed_ai_run_metadata.reported"

CHANGED_AI_KNOWN_GAP_BLOCKERS = {
    "changed-ai suite records ROM rebuild as skipped unless explicitly requested.": "changed_ai_rom_rebuild_skipped",
    "changed-ai suite ROM rebuild command failed.": "changed_ai_rom_rebuild_failed",
    "changed-ai suite records live trace refresh as skipped unless explicitly requested.": "changed_ai_live_trace_refresh_skipped",
    "changed-ai suite live trace refresh command failed.": "changed_ai_live_trace_refresh_failed",
    "changed-ai suite ingests existing ROM contribution trace artifacts but does not refresh them.": "changed_ai_rom_contribution_trace_not_refreshed",
    CONTRIBUTION_REFRESH_SINGLE_ROUTE_KNOWN_GAP: CONTRIBUTION_REFRESH_SINGLE_ROUTE_BLOCKER,
    "changed-ai suite records generated score materialization as skipped unless explicitly requested.": "changed_ai_rom_score_materialization_skipped",
    SCORE_MATERIALIZATION_TARGETED_KNOWN_GAP: SCORE_MATERIALIZATION_TARGETED_BLOCKER,
    CONTRIBUTION_COMPARISON_TRACE_ID_KNOWN_GAP: CONTRIBUTION_COMPARISON_TRACE_ID_BLOCKER,
    PRE_CHOICE_REPLAY_KNOWN_GAP: PRE_CHOICE_REPLAY_BLOCKER,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def today_stamp() -> str:
    return datetime.now().date().isoformat()


def load_questions(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
            rows.append(row)
    if not rows:
        raise SystemExit(f"{path}: no God-level benchmark questions")
    return rows


def row_errors(row: dict[str, Any], *, root: Path) -> list[str]:
    errors = [f"missing required field {field}" for field in REQUIRED_FIELDS if field not in row]
    if row.get("status") not in {"complete", "missing_evidence", "unsupported", "blocked"}:
        errors.append(f"status must fail closed or be complete, got {row.get('status')!r}")
    if row.get("status") == "complete" and row.get("blocking_gaps"):
        errors.append("complete rows must not carry blocking_gaps")
    if row.get("status") == "complete" and row.get("missing_evidence"):
        errors.append("complete rows must not carry missing_evidence")
    if row.get("status") == "complete":
        closed_ids = row.get("closed_evidence_ids", [])
        artifacts = row.get("evidence_artifacts", [])
        if not isinstance(closed_ids, list) or not closed_ids:
            errors.append("complete rows must declare closed_evidence_ids")
        if not isinstance(artifacts, list) or not artifacts:
            errors.append("complete rows must declare evidence_artifacts")
        for artifact in artifacts if isinstance(artifacts, list) else []:
            artifact_path = root / str(artifact)
            if not artifact_path.exists():
                errors.append(f"complete row evidence artifact missing: {artifact}")
    return errors


def build_god_report(
    *,
    questions_path: Path = DEFAULT_QUESTIONS,
    root: Path = ROOT,
    include_universe: bool = True,
    universe_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = load_questions(questions_path if questions_path.is_absolute() else root / questions_path)
    question_results = []
    blocking_gaps: list[str] = []
    schema_errors: list[str] = []
    counters = {field: 0 for field in COUNT_FIELDS}
    closed_evidence_ids = ["boss_ai_god_gate.schema_checked"]
    raw_class_adoption = boss_ai_raw_class_adoption_status() if include_universe else {
        "ready": False,
        "generated_scenario_class_adoption": {"ready": False},
        "live_trace_class_adoption": {"ready": False},
        "contribution_trace_class_adoption": {"ready": False},
        "closed_evidence_ids": [],
        "blocking_gaps": [],
    }
    if raw_class_adoption["ready"]:
        closed_evidence_ids.extend(str(item) for item in raw_class_adoption["closed_evidence_ids"])
    changed_ai_suite = changed_ai_god_suite_status(root)
    if changed_ai_suite.get("partial_evidence_ready"):
        closed_evidence_ids.extend(str(item) for item in changed_ai_suite.get("closed_evidence_ids", []))
    universe: dict[str, Any] | None = None
    if include_universe:
        try:
            universe = universe_report if universe_report is not None else build_boss_ai_universe_report(root=root)
        except Exception as exc:  # noqa: BLE001
            schema_errors.append(f"boss_ai_universe: {type(exc).__name__}: {exc}")
    for row in rows:
        row = effective_question_row(
            row,
            raw_class_adoption=raw_class_adoption,
            universe=universe,
            root=root,
            changed_ai_suite=changed_ai_suite,
        )
        errors = row_errors(row, root=root)
        if errors:
            schema_errors.extend(f"{row.get('id', '<unknown>')}: {error}" for error in errors)
        if row.get("status") == "complete":
            closed_evidence_ids.extend(str(item) for item in row.get("closed_evidence_ids", []))
        for field in COUNT_FIELDS:
            counters[field] += int(row.get(field, 0) or 0)
        row_gaps = [str(item) for item in row.get("blocking_gaps", [])]
        blocking_gaps.extend(row_gaps)
        status = "FAIL" if row.get("status") != "complete" or errors else "PASS"
        question_results.append(
            {
                "id": str(row.get("id", "")),
                "requirement": str(row.get("requirement", "")),
                "surface": str(row.get("surface", "")),
                "status": status,
                "proof_status": str(row.get("status", "")),
                "blocking_gaps": row_gaps,
                "next_command": str(row.get("next_command", "")),
                "disproof_standard": str(row.get("disproof_standard", "")),
            }
        )
    failed = [item for item in question_results if item["status"] != "PASS"]
    canonical_class_coverage = canonical_class_coverage_status(None)
    if include_universe:
        blocking_gaps.extend(str(item) for item in raw_class_adoption["blocking_gaps"])
        if universe is not None:
            canonical_class_coverage = canonical_class_coverage_status(universe)
            if canonical_class_coverage["ready"]:
                closed_evidence_ids.append(RULE_TARGET_CLASS_EVIDENCE_ID)
            else:
                blocking_gaps.extend(str(item) for item in canonical_class_coverage["blocking_gaps"])
            witness_catalog_status = exhaustive_witness_catalog_status(universe)
            if witness_catalog_status["ready"]:
                closed_evidence_ids.append(EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID)
            elif witness_catalog_status["available"]:
                blocking_gaps.extend(str(item) for item in witness_catalog_status["blocking_gaps"])
            universe_counters = universe.get("counters", {})
            if not isinstance(universe_counters, dict):
                schema_errors.append("boss_ai_universe: counters must be an object")
            else:
                for field in COUNT_FIELDS:
                    counters[field] += int(universe_counters.get(field, 0) or 0)
            blocking_gaps.extend(str(item) for item in universe.get("blocking_gaps", []))
            if universe.get("proof_status") != "complete":
                blocking_gaps.append("boss_ai_universe_not_complete")
    closed_evidence_ids = list(dict.fromkeys(closed_evidence_ids))
    god_ready = (
        not failed
        and not schema_errors
        and not blocking_gaps
        and all(value == 0 for value in counters.values())
    )
    envelope = build_report_envelope(
        kind="boss_ai_debugger_god_gate",
        command="python tools\\audit\\check_boss_ai_debugger_god.py",
        inputs={"questions": str(questions_path)},
        backend="pyboy_plus_static",
        proof_status="complete" if god_ready else "missing_evidence",
        missing_evidence=sorted(set(blocking_gaps + schema_errors)),
        blocking_gaps=sorted(set(blocking_gaps + schema_errors)),
        known_limits=[
            "This is the God-level skeleton gate. It is red until exhaustive Boss AI proof artifacts, public-read provenance, materialization coverage, and the proof DB land.",
        ],
        closed_evidence_ids=closed_evidence_ids,
        repro_command="python tools\\audit\\check_boss_ai_debugger_god.py --baseline --read-only",
        disproof_standard=[
            "Every reachable Boss AI label, rule, branch, public read, class id, proof artifact, and materialization path is present.",
            "No unsupported or missing row can pass green.",
        ],
        root=root,
    )
    envelope.update(
        {
            "generated_at": utc_now(),
            "questions_path": repo_rel(root, questions_path if questions_path.is_absolute() else root / questions_path),
            "boss_ai_god_ready": god_ready,
            "question_count": len(question_results),
            "questions_failed": len(failed),
            "schema_errors": schema_errors,
            "counters": counters,
            "questions": question_results,
            "boss_ai_universe": summarize_universe_for_gate(universe),
            "canonical_class_coverage": canonical_class_coverage,
            "generated_scenario_class_adoption": raw_class_adoption["generated_scenario_class_adoption"],
            "live_trace_class_adoption": raw_class_adoption["live_trace_class_adoption"],
            "contribution_trace_class_adoption": raw_class_adoption["contribution_trace_class_adoption"],
            "raw_class_adoption": raw_class_adoption,
            "changed_ai_god_suite": changed_ai_suite,
        }
    )
    return envelope


def effective_question_row(
    row: dict[str, Any],
    *,
    raw_class_adoption: dict[str, Any],
    universe: dict[str, Any] | None,
    root: Path,
    changed_ai_suite: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if row.get("id") == "boss_ai_universe_extractor" and universe_labels_classified(universe):
        out = dict(row)
        stale_gaps = {
            "boss_ai_universe_has_unmapped_reachable_labels",
            "boss_ai_universe_has_labels_without_rule_ids",
        }
        out["blocking_gaps"] = [
            gap for gap in out.get("blocking_gaps", []) if gap not in stale_gaps
        ]
        out["missing_evidence"] = [
            gap for gap in out.get("missing_evidence", []) if gap not in stale_gaps
        ]
        out["missing_reachable_label_count"] = 0
        out["missing_rule_count"] = 0
        if not out["blocking_gaps"] and not out.get("missing_evidence"):
            out["status"] = "complete"
            out["closed_evidence_ids"] = [UNIVERSE_LABEL_EVIDENCE_ID]
            out["evidence_artifacts"] = ["audit/boss_ai_debugger/rule_map.json"]
        out["requirement"] = str(out.get("requirement", "")) + " Current label inventory maps reachable rule labels and parent-owned implementation labels without claiming proof coverage."
        return out
    if row.get("id") == "boss_ai_rom_materialization_paths" and universe_materialization_paths_available(universe):
        out = dict(row)
        stale_gaps = {"boss_ai_all_class_materialization_paths_not_available"}
        out["blocking_gaps"] = [
            gap for gap in out.get("blocking_gaps", []) if gap not in stale_gaps
        ]
        out["missing_evidence"] = [
            gap for gap in out.get("missing_evidence", []) if gap not in stale_gaps
        ]
        out["missing_materialization_path_count"] = 0
        if not out["blocking_gaps"] and not out.get("missing_evidence"):
            out["status"] = "complete"
            out["closed_evidence_ids"] = [MATERIALIZATION_PATH_EVIDENCE_ID]
            out["evidence_artifacts"] = ["audit/boss_ai_debugger/coverage_report.json"]
        out["requirement"] = str(out.get("requirement", "")) + " Current rule-target classes have materializer commands; missing ROM proof artifacts and stale-basis proof DB work remain blockers elsewhere."
        return out
    if row.get("id") == "boss_ai_exhaustive_class_generator" and exhaustive_witness_inventory_available(universe):
        out = dict(row)
        stale_gaps = {"boss_ai_exhaustive_class_generator_not_implemented"}
        current_gaps = [
            str(gap) for gap in out.get("blocking_gaps", []) if gap not in stale_gaps
        ]
        inventory = universe.get("exhaustive_class_witness_inventory", {}) if isinstance(universe, dict) else {}
        concrete_gaps = [
            str(gap) for gap in inventory.get("blocking_gaps", []) if str(gap)
        ]
        catalog_status = exhaustive_witness_catalog_status(universe)
        if not concrete_gaps and inventory.get("ready") and catalog_status.get("ready"):
            out["blocking_gaps"] = []
            out["missing_evidence"] = []
            out["status"] = "complete"
            out["closed_evidence_ids"] = [EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID]
            out["missing_proof_artifact_count"] = 0
            out["evidence_artifacts"] = [
                "audit/boss_ai_debugger/god_level_benchmark/artifacts/counterfactual_witness_materializations"
            ]
            out["requirement"] = str(out.get("requirement", "")) + " Current universe has ROM-proven witness roles for every required class."
            return out
        if not concrete_gaps:
            concrete_gaps = ["boss_ai_exhaustive_class_generator_completion_not_declared"]
        out["blocking_gaps"] = list(dict.fromkeys([*current_gaps, *concrete_gaps]))
        out["missing_evidence"] = list(out["blocking_gaps"])
        out["status"] = "missing_evidence"
        out["requirement"] = str(out.get("requirement", "")) + " Current universe output inventories required witness roles without claiming the generator or proofs exist."
        return out
    if row.get("id") == "boss_ai_changed_ai_god_suite":
        status = changed_ai_suite if changed_ai_suite is not None else changed_ai_god_suite_status(root)
        out = dict(row)
        stale_gaps = {"changed_ai_god_suite_not_implemented"}
        current_gaps = [
            str(gap) for gap in out.get("blocking_gaps", []) if gap not in stale_gaps
        ]
        concrete_gaps = [str(gap) for gap in status.get("blocking_gaps", [])]
        out["blocking_gaps"] = list(dict.fromkeys([*current_gaps, *concrete_gaps]))
        out["missing_evidence"] = list(out["blocking_gaps"])
        out["status"] = "missing_evidence"
        out["changed_ai_run_id"] = str(status.get("run_id", ""))
        out["changed_ai_metadata_path"] = str(status.get("metadata_path", ""))
        out["changed_ai_known_gaps"] = list(status.get("known_gaps", []))
        out["changed_ai_unmapped_known_gaps"] = list(status.get("unmapped_known_gaps", []))
        out["closed_evidence_ids"] = list(status.get("closed_evidence_ids", []))
        out["evidence_artifacts"] = list(status.get("evidence_artifacts", []))
        if status.get("ready") and not out["blocking_gaps"]:
            out["status"] = "complete"
            out["missing_evidence"] = []
            out["missing_proof_artifact_count"] = 0
            out["requirement"] = str(out.get("requirement", "")) + " Current changed-AI metadata has complete companion evidence for every declared known gap."
            return out
        out["requirement"] = str(out.get("requirement", "")) + " Current run metadata is consumed as partial evidence; remaining blockers come from the changed-AI run's own known gaps."
        return out
    if row.get("id") != "boss_ai_canonical_classes" or not raw_class_adoption.get("ready"):
        return row
    out = dict(row)
    out["status"] = "complete"
    out["blocking_gaps"] = []
    out["missing_evidence"] = []
    out["missing_class_id_count"] = 0
    out["closed_evidence_ids"] = list(raw_class_adoption.get("closed_evidence_ids", []))
    out["evidence_artifacts"] = [
        "audit/boss_ai_trace/live_capture_manifest.json",
        "audit/boss_ai_debugger/rom_contribution_trace_smoke.json",
    ]
    out["requirement"] = str(out.get("requirement", "")) + " Current supported raw trace surfaces carry canonical class ids; full public-state completeness remains a known limit."
    return out


def changed_ai_god_suite_status(root: Path = ROOT) -> dict[str, Any]:
    status: dict[str, Any] = {
        "available": False,
        "partial_evidence_ready": False,
        "ready": False,
        "metadata_path": "",
        "evidence_source": "",
        "run_id": "",
        "created_at": "",
        "changed_file_count": 0,
        "scenario_count": 0,
        "present_artifact_count": 0,
        "missing_artifact_count": 0,
        "known_gaps": [],
        "unmapped_known_gaps": [],
        "blocking_gaps": ["changed_ai_run_metadata_missing"],
        "closed_evidence_ids": [],
        "evidence_artifacts": [],
    }
    found = changed_ai_metadata_evidence(root)
    if found is None:
        return status
    metadata_path, metadata, promoted_summary = found
    pre_choice_replay = pre_choice_replay_artifact_status(root)
    score_materialization = changed_ai_score_materialization_full_status(root, metadata)
    contribution_trace_id = changed_ai_contribution_trace_id_status(root, metadata)
    contribution_refresh_scope = changed_ai_contribution_refresh_scope_status(root, metadata)
    status["available"] = True
    status["metadata_path"] = repo_rel(root, metadata_path)
    status["evidence_source"] = "promoted_deity_summary" if promoted_summary else "latest_changed_ai_run_metadata"
    status["pre_choice_replay"] = pre_choice_replay
    status["score_materialization_full"] = score_materialization
    status["contribution_trace_id_comparison"] = contribution_trace_id
    status["contribution_refresh_scope"] = contribution_refresh_scope
    status["run_id"] = str(metadata.get("run_id", ""))
    status["created_at"] = str(metadata.get("created_at", ""))
    changed_files = metadata.get("changed_files", [])
    if isinstance(changed_files, list):
        status["changed_file_count"] = len(changed_files)
    batch = metadata.get("batch_summary", {})
    if isinstance(batch, dict):
        status["scenario_count"] = int(batch.get("scenario_count", 0) or 0)
    if promoted_summary and status["scenario_count"] == 0:
        targeted = promoted_summary.get("targeted_generators", {})
        if isinstance(targeted, dict):
            status["scenario_count"] = int(targeted.get("scenario_count", 0) or 0)
    artifact_paths = changed_ai_artifact_paths(metadata)
    artifact_paths.extend(promoted_summary_artifact_paths(promoted_summary))
    artifact_paths = list(dict.fromkeys(artifact_paths))
    present_artifacts = [path for path in artifact_paths if (root / path).exists()]
    missing_artifacts = [path for path in artifact_paths if not (root / path).exists()]
    status["present_artifact_count"] = len(present_artifacts)
    status["missing_artifact_count"] = len(missing_artifacts)
    status["evidence_artifacts"] = [status["metadata_path"], *[path.as_posix() for path in present_artifacts[:8]]]
    if pre_choice_replay.get("ready") and pre_choice_replay.get("artifact_path"):
        status["evidence_artifacts"].append(str(pre_choice_replay["artifact_path"]))
    if score_materialization.get("coverage_ready") and score_materialization.get("artifact_path"):
        status["evidence_artifacts"].append(str(score_materialization["artifact_path"]))
    if contribution_trace_id.get("ready"):
        status["evidence_artifacts"].extend(
            str(path) for path in contribution_trace_id.get("evidence_artifacts", [])
        )
    if contribution_refresh_scope.get("ready") and contribution_refresh_scope.get("artifact_path"):
        status["evidence_artifacts"].append(str(contribution_refresh_scope["artifact_path"]))
    known_gaps = [
        str(item)
        for item in metadata.get("known_gaps", [])
        if isinstance(item, str) and item.strip()
    ]
    blockers = []
    unmapped = []
    resolved_known_gaps = []
    for gap in known_gaps:
        if gap == PRE_CHOICE_REPLAY_KNOWN_GAP and pre_choice_replay.get("ready"):
            resolved_known_gaps.append(gap)
            continue
        if gap == SCORE_MATERIALIZATION_TARGETED_KNOWN_GAP and score_materialization.get("coverage_ready"):
            resolved_known_gaps.append(gap)
            continue
        if gap == CONTRIBUTION_COMPARISON_TRACE_ID_KNOWN_GAP and contribution_trace_id.get("ready"):
            resolved_known_gaps.append(gap)
            continue
        if gap == CONTRIBUTION_REFRESH_SINGLE_ROUTE_KNOWN_GAP and contribution_refresh_scope.get("ready"):
            resolved_known_gaps.append(gap)
            continue
        blocker = CHANGED_AI_KNOWN_GAP_BLOCKERS.get(gap)
        if blocker:
            blockers.append(blocker)
        else:
            blockers.append("changed_ai_known_gap_unmapped")
            unmapped.append(gap)
    validation = metadata.get("validation", {})
    validation_ready = isinstance(validation, dict) and validation.get("valid") is True
    has_artifact_hashes = isinstance(metadata.get("artifact_hashes"), dict) and bool(metadata.get("artifact_hashes"))
    summary_ready = True
    if promoted_summary:
        hash_basis = promoted_summary.get("hash_basis", {})
        summary_ready = (
            promoted_summary.get("kind") == "boss_ai_deity_changed_ai_summary"
            and promoted_summary.get("status") == "changed_ai_summary_ready"
            and isinstance(hash_basis, dict)
            and hash_basis.get("ready") is True
        )
    partial_evidence_ready = (
        metadata.get("profile") == "changed-ai"
        and validation_ready
        and status["scenario_count"] > 0
        and status["present_artifact_count"] > 0
        and has_artifact_hashes
        and summary_ready
    )
    if not partial_evidence_ready:
        blockers.append("changed_ai_run_metadata_incomplete")
    if status["missing_artifact_count"]:
        blockers.append("changed_ai_run_metadata_references_missing_artifacts")
    changed_ai_completion_ready = (
        partial_evidence_ready
        and pre_choice_replay.get("ready")
        and score_materialization.get("coverage_ready")
        and contribution_trace_id.get("ready")
        and contribution_refresh_scope.get("ready")
        and status["missing_artifact_count"] == 0
    )
    if not blockers and not changed_ai_completion_ready:
        blockers.append("changed_ai_god_suite_completion_not_declared")
    status["known_gaps"] = known_gaps
    status["resolved_known_gaps"] = resolved_known_gaps
    status["unmapped_known_gaps"] = unmapped
    status["partial_evidence_ready"] = partial_evidence_ready
    status["closed_evidence_ids"] = [CHANGED_AI_RUN_METADATA_EVIDENCE_ID] if partial_evidence_ready else []
    if partial_evidence_ready and pre_choice_replay.get("ready"):
        status["closed_evidence_ids"].append(PRE_CHOICE_REPLAY_EVIDENCE_ID)
    if partial_evidence_ready and score_materialization.get("coverage_ready"):
        status["closed_evidence_ids"].append(SCORE_MATERIALIZATION_FULL_EVIDENCE_ID)
    if partial_evidence_ready and contribution_trace_id.get("ready"):
        status["closed_evidence_ids"].append(CONTRIBUTION_COMPARISON_TRACE_ID_EVIDENCE_ID)
    if partial_evidence_ready and contribution_refresh_scope.get("ready"):
        status["closed_evidence_ids"].append(CONTRIBUTION_REFRESH_SCOPE_EVIDENCE_ID)
    status["completion_ready"] = changed_ai_completion_ready and not blockers
    status["blocking_gaps"] = sorted(set(blockers))
    status["ready"] = status["completion_ready"]
    return status


def pre_choice_replay_artifact_status(root: Path = ROOT) -> dict[str, Any]:
    status: dict[str, Any] = {
        "available": False,
        "ready": False,
        "artifact_path": PRE_CHOICE_REPLAY_ARTIFACT.as_posix(),
        "closed_evidence_id": PRE_CHOICE_REPLAY_EVIDENCE_ID,
        "capture_count": 0,
        "exact_count": 0,
        "exact_match_count": 0,
        "minimum_exact_captures": 0,
        "exact_agreement_rate": 0.0,
        "blocking_gaps": [],
    }
    artifact_path = root / PRE_CHOICE_REPLAY_ARTIFACT
    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        status["blocking_gaps"].append("boss_ai_pre_choice_replay_artifact_missing")
        return status
    except (OSError, json.JSONDecodeError):
        status["blocking_gaps"].append("boss_ai_pre_choice_replay_artifact_unreadable")
        return status
    if not isinstance(artifact, dict):
        status["blocking_gaps"].append("boss_ai_pre_choice_replay_artifact_malformed")
        return status
    status["available"] = True
    status["capture_count"] = int(artifact.get("capture_count", 0) or 0)
    status["exact_count"] = int(artifact.get("exact_count", 0) or 0)
    status["exact_match_count"] = int(artifact.get("exact_match_count", 0) or 0)
    status["minimum_exact_captures"] = int(artifact.get("minimum_exact_captures", 0) or 0)
    status["exact_agreement_rate"] = float(artifact.get("exact_agreement_rate", 0.0) or 0.0)
    blockers: list[str] = []
    if artifact.get("kind") != "boss_ai_pre_choice_replay_audit":
        blockers.append("boss_ai_pre_choice_replay_artifact_wrong_kind")
    if artifact.get("proof_status") != "complete":
        blockers.append("boss_ai_pre_choice_replay_not_complete")
    if artifact.get("missing_evidence"):
        blockers.append("boss_ai_pre_choice_replay_missing_evidence")
    if artifact.get("blocking_gaps"):
        blockers.append("boss_ai_pre_choice_replay_blocking_gaps")
    closed_ids = artifact.get("closed_evidence_ids", [])
    if not isinstance(closed_ids, list) or PRE_CHOICE_REPLAY_EVIDENCE_ID not in closed_ids:
        blockers.append("boss_ai_pre_choice_replay_closed_evidence_missing")
    checked_count = int(artifact.get("checked_count", 0) or 0)
    failure_count = int(artifact.get("failure_count", 0) or 0)
    partial_count = int(artifact.get("partial_count", 0) or 0)
    if status["capture_count"] <= 0 or checked_count != status["capture_count"]:
        blockers.append("boss_ai_pre_choice_replay_capture_count_mismatch")
    if failure_count:
        blockers.append("boss_ai_pre_choice_replay_failures_present")
    if partial_count:
        blockers.append("boss_ai_pre_choice_replay_partial_captures_present")
    if status["exact_count"] != status["capture_count"]:
        blockers.append("boss_ai_pre_choice_replay_exact_count_mismatch")
    if status["exact_match_count"] != status["exact_count"]:
        blockers.append("boss_ai_pre_choice_replay_exact_match_mismatch")
    if status["minimum_exact_captures"] <= 0 or status["exact_count"] < status["minimum_exact_captures"]:
        blockers.append("boss_ai_pre_choice_replay_minimum_exact_not_met")
    minimum_agreement = float(artifact.get("minimum_agreement", 0.0) or 0.0)
    if minimum_agreement <= 0.0 or status["exact_agreement_rate"] < minimum_agreement:
        blockers.append("boss_ai_pre_choice_replay_minimum_agreement_not_met")

    manifest_path = root / LIVE_CAPTURE_MANIFEST
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        manifest = None
        blockers.append("boss_ai_pre_choice_replay_manifest_unreadable")
    state_basis = artifact.get("state_basis", {})
    if not isinstance(state_basis, dict):
        state_basis = {}
        blockers.append("boss_ai_pre_choice_replay_state_basis_missing")
    expected_manifest_hash = sha256_file(manifest_path, root=root)
    if state_basis.get("manifest_sha256") != expected_manifest_hash:
        blockers.append("boss_ai_pre_choice_replay_manifest_hash_stale")
    if isinstance(manifest, dict):
        manifest_rom_hash = str(manifest.get("trace_rom_sha256", "")).upper()
        manifest_symbols_hash = str(manifest.get("trace_symbols_sha256", "")).upper()
        if str(artifact.get("rom_sha256", "")).upper() != manifest_rom_hash:
            blockers.append("boss_ai_pre_choice_replay_rom_hash_stale")
        if str(artifact.get("symbols_sha256", "")).upper() != manifest_symbols_hash:
            blockers.append("boss_ai_pre_choice_replay_symbols_hash_stale")
    status["blocking_gaps"] = sorted(set(blockers))
    status["ready"] = status["available"] and not status["blocking_gaps"]
    return status


def changed_ai_contribution_trace_id_status(root: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    status: dict[str, Any] = {
        "available": False,
        "ready": False,
        "closed_evidence_id": CONTRIBUTION_COMPARISON_TRACE_ID_EVIDENCE_ID,
        "differential_path": "",
        "rom_score_materialization_path": "",
        "evidence_artifacts": [],
        "rom_trace_count": 0,
        "python_trace_count": 0,
        "matched_trace_count": 0,
        "materialized_trace_count": 0,
        "unmatched_python_trace_count": 0,
        "non_scenario_unmatched_rom_trace_ids": [],
        "generated_unmatched_rom_trace_ids": [],
        "missing_materialized_trace_ids": [],
        "mismatch_count": 0,
        "class_id_mismatch_count": 0,
        "missing_class_id_count": 0,
        "blocking_gaps": [],
    }
    differential_rel = changed_ai_metadata_artifact_path(metadata, "differential")
    materialization_rel = changed_ai_metadata_artifact_path(metadata, "rom_score_materialization")
    if differential_rel is None:
        status["blocking_gaps"].append("changed_ai_contribution_comparison_differential_missing")
    if materialization_rel is None:
        status["blocking_gaps"].append("changed_ai_contribution_comparison_materialization_missing")
    if status["blocking_gaps"]:
        return status

    differential_path = root / differential_rel
    materialization_path = root / materialization_rel
    status["differential_path"] = repo_rel(root, differential_path)
    status["rom_score_materialization_path"] = repo_rel(root, materialization_path)
    status["evidence_artifacts"] = [
        status["differential_path"],
        status["rom_score_materialization_path"],
    ]
    if not differential_path.exists():
        status["blocking_gaps"].append("changed_ai_contribution_comparison_differential_missing")
    if not materialization_path.exists():
        status["blocking_gaps"].append("changed_ai_contribution_comparison_materialization_missing")
    if status["blocking_gaps"]:
        return status

    try:
        differential = json.loads(differential_path.read_text(encoding="utf-8"))
        materialization = json.loads(materialization_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        status["blocking_gaps"].append("changed_ai_contribution_comparison_artifact_unreadable")
        return status
    if not isinstance(differential, dict) or not isinstance(materialization, dict):
        status["blocking_gaps"].append("changed_ai_contribution_comparison_artifact_malformed")
        return status
    comparison = differential.get("contribution_comparison", {})
    if not isinstance(comparison, dict):
        status["blocking_gaps"].append("changed_ai_contribution_comparison_missing")
        return status

    matched_ids = string_values(comparison.get("matched_trace_ids", []))
    unmatched_rom_ids = string_values(comparison.get("unmatched_rom_trace_ids", []))
    unmatched_python_ids = string_values(comparison.get("unmatched_python_trace_ids", []))
    materialized_ids = changed_ai_materialized_contribution_trace_ids(materialization)
    generated_unmatched = sorted(
        trace_id
        for trace_id in unmatched_rom_ids
        if trace_id.startswith("generated_")
    )
    non_scenario_unmatched = sorted(
        trace_id
        for trace_id in unmatched_rom_ids
        if not trace_id.startswith("generated_")
    )
    missing_materialized = sorted(set(materialized_ids) - set(matched_ids))

    status["available"] = True
    status["rom_trace_count"] = int(comparison.get("rom_trace_count", 0) or 0)
    status["python_trace_count"] = int(comparison.get("python_trace_count", 0) or 0)
    status["matched_trace_count"] = int(comparison.get("matched_trace_count", 0) or 0)
    status["materialized_trace_count"] = len(materialized_ids)
    status["unmatched_python_trace_count"] = len(unmatched_python_ids)
    status["non_scenario_unmatched_rom_trace_ids"] = non_scenario_unmatched
    status["generated_unmatched_rom_trace_ids"] = generated_unmatched
    status["missing_materialized_trace_ids"] = missing_materialized
    status["mismatch_count"] = int(comparison.get("mismatch_count", 0) or 0)
    status["class_id_mismatch_count"] = int(comparison.get("class_id_mismatch_count", 0) or 0)
    status["missing_class_id_count"] = int(comparison.get("missing_class_id_count", 0) or 0)

    if not materialized_ids:
        status["blocking_gaps"].append("changed_ai_contribution_comparison_no_materialized_traces")
    if missing_materialized:
        status["blocking_gaps"].append("changed_ai_contribution_comparison_materialized_trace_ids_unmatched")
    if generated_unmatched:
        status["blocking_gaps"].append("changed_ai_contribution_comparison_generated_rom_trace_ids_unmatched")
    if status["class_id_mismatch_count"]:
        status["blocking_gaps"].append("changed_ai_contribution_comparison_class_ids_mismatch")
    if status["missing_class_id_count"]:
        status["blocking_gaps"].append("changed_ai_contribution_comparison_class_ids_missing")
    status["ready"] = not status["blocking_gaps"]
    return status


def changed_ai_materialized_contribution_trace_ids(materialization: dict[str, Any]) -> list[str]:
    traces = materialization.get("traces", [])
    if not isinstance(traces, list):
        return []
    ids = []
    for trace in traces:
        if not isinstance(trace, dict):
            continue
        trace_id = str(trace.get("trace_id") or trace.get("scenario_id") or "")
        if trace_id:
            ids.append(trace_id)
    return sorted(set(ids))


def changed_ai_contribution_refresh_scope_status(root: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    status: dict[str, Any] = {
        "available": False,
        "ready": False,
        "artifact_path": CONTRIBUTION_REFRESH_SCOPE_ARTIFACT.as_posix(),
        "closed_evidence_id": CONTRIBUTION_REFRESH_SCOPE_EVIDENCE_ID,
        "expected_route_count": 0,
        "refreshed_route_count": 0,
        "expected_route_ids": [],
        "refreshed_route_ids": [],
        "missing_route_ids": [],
        "extra_route_ids": [],
        "missing_trace_artifacts": [],
        "bad_trace_artifacts": [],
        "route_trace_count": 0,
        "route_class_id_count": 0,
        "route_event_count": 0,
        "route_changed_event_count": 0,
        "blocking_gaps": [],
    }
    artifact_path = root / CONTRIBUTION_REFRESH_SCOPE_ARTIFACT
    expected_routes = changed_ai_expected_contribution_route_ids(root)
    status["expected_route_ids"] = expected_routes
    status["expected_route_count"] = len(expected_routes)
    if not expected_routes:
        status["blocking_gaps"].append("changed_ai_contribution_refresh_no_expected_routes")
        return status
    metadata_status = changed_ai_contribution_refresh_scope_from_metadata(
        root,
        metadata,
        expected_routes=expected_routes,
    )
    if metadata_status.get("ready"):
        return metadata_status
    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        status["blocking_gaps"].append("changed_ai_contribution_refresh_scope_artifact_missing")
        return status
    except (OSError, json.JSONDecodeError):
        status["blocking_gaps"].append("changed_ai_contribution_refresh_scope_artifact_unreadable")
        return status
    if not isinstance(artifact, dict):
        status["blocking_gaps"].append("changed_ai_contribution_refresh_scope_artifact_malformed")
        return status
    status["available"] = True

    blockers = []
    if artifact.get("kind") != "boss_ai_changed_ai_contribution_refresh_scope":
        blockers.append("changed_ai_contribution_refresh_scope_wrong_kind")
    state_basis = artifact.get("state_basis", {})
    if not isinstance(state_basis, dict):
        state_basis = {}
        blockers.append("changed_ai_contribution_refresh_scope_state_basis_missing")
    manifest_path = root / LIVE_CAPTURE_MANIFEST
    if state_basis.get("manifest_path") != LIVE_CAPTURE_MANIFEST.as_posix():
        blockers.append("changed_ai_contribution_refresh_scope_manifest_path_mismatch")
    if state_basis.get("manifest_sha256") != sha256_file(manifest_path, root=root):
        blockers.append("changed_ai_contribution_refresh_scope_manifest_hash_stale")

    artifact_expected = string_values(artifact.get("expected_route_ids", []))
    refreshed_routes = string_values(artifact.get("refreshed_route_ids", []))
    status["refreshed_route_ids"] = refreshed_routes
    status["refreshed_route_count"] = len(refreshed_routes)
    missing_routes = sorted(set(expected_routes) - set(refreshed_routes))
    extra_routes = sorted(set(refreshed_routes) - set(expected_routes))
    status["missing_route_ids"] = missing_routes
    status["extra_route_ids"] = extra_routes
    if artifact_expected != expected_routes:
        blockers.append("changed_ai_contribution_refresh_scope_expected_routes_stale")
    if missing_routes:
        blockers.append("changed_ai_contribution_refresh_scope_missing_routes")
    if extra_routes:
        blockers.append("changed_ai_contribution_refresh_scope_extra_routes")

    trace_artifacts = artifact.get("trace_artifacts", [])
    if not isinstance(trace_artifacts, list):
        trace_artifacts = []
        blockers.append("changed_ai_contribution_refresh_scope_trace_artifacts_malformed")
    trace_by_route = {
        str(item.get("boss_route", "")): item
        for item in trace_artifacts
        if isinstance(item, dict) and item.get("boss_route")
    }
    if sorted(trace_by_route) != sorted(refreshed_routes):
        blockers.append("changed_ai_contribution_refresh_scope_trace_route_mismatch")
    missing_trace_artifacts = []
    bad_trace_artifacts = []
    route_trace_count = 0
    route_class_id_count = 0
    route_event_count = 0
    route_changed_event_count = 0
    for route_id in expected_routes:
        trace_ref = trace_by_route.get(route_id, {})
        path_value = trace_ref.get("artifact", "") if isinstance(trace_ref, dict) else ""
        path = root / metadata_path_item(str(path_value)) if path_value else root / "__missing_contribution_trace__"
        if not path.exists():
            missing_trace_artifacts.append(str(path_value) or route_id)
            continue
        try:
            trace = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            bad_trace_artifacts.append(repo_rel(root, path))
            continue
        if not isinstance(trace, dict) or not route_contribution_trace_matches_manifest(
            trace,
            route_id=route_id,
            state_basis=state_basis,
        ):
            bad_trace_artifacts.append(repo_rel(root, path))
            continue
        route_trace_count += 1
        if trace.get("class_id"):
            route_class_id_count += 1
        route_event_count += int(trace.get("event_count", 0) or 0)
        route_changed_event_count += int(trace.get("changed_event_count", 0) or 0)
    status["missing_trace_artifacts"] = missing_trace_artifacts
    status["bad_trace_artifacts"] = bad_trace_artifacts
    status["route_trace_count"] = route_trace_count
    status["route_class_id_count"] = route_class_id_count
    status["route_event_count"] = route_event_count
    status["route_changed_event_count"] = route_changed_event_count
    if missing_trace_artifacts:
        blockers.append("changed_ai_contribution_refresh_scope_missing_trace_artifacts")
    if bad_trace_artifacts:
        blockers.append("changed_ai_contribution_refresh_scope_bad_trace_artifacts")
    if route_trace_count != len(expected_routes):
        blockers.append("changed_ai_contribution_refresh_scope_trace_count_mismatch")
    if route_class_id_count != len(expected_routes):
        blockers.append("changed_ai_contribution_refresh_scope_class_ids_missing")
    status["blocking_gaps"] = sorted(set(blockers))
    status["ready"] = status["available"] and not status["blocking_gaps"]
    return status


def changed_ai_contribution_refresh_scope_from_metadata(
    root: Path,
    metadata: dict[str, Any],
    *,
    expected_routes: list[str],
) -> dict[str, Any]:
    status: dict[str, Any] = {
        "available": False,
        "ready": False,
        "artifact_path": "metadata:rom_contribution_traces",
        "closed_evidence_id": CONTRIBUTION_REFRESH_SCOPE_EVIDENCE_ID,
        "expected_route_count": len(expected_routes),
        "refreshed_route_count": 0,
        "expected_route_ids": expected_routes,
        "refreshed_route_ids": [],
        "missing_route_ids": [],
        "extra_route_ids": [],
        "missing_trace_artifacts": [],
        "bad_trace_artifacts": [],
        "route_trace_count": 0,
        "route_class_id_count": 0,
        "route_event_count": 0,
        "route_changed_event_count": 0,
        "blocking_gaps": [],
    }
    artifacts = metadata.get("artifacts", {})
    trace_values = artifacts.get("rom_contribution_traces") if isinstance(artifacts, dict) else None
    if not isinstance(trace_values, list) or not trace_values:
        status["blocking_gaps"].append("changed_ai_contribution_refresh_metadata_traces_missing")
        return status
    manifest_path = root / LIVE_CAPTURE_MANIFEST
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        status["blocking_gaps"].append("changed_ai_contribution_refresh_manifest_unreadable")
        return status
    state_basis = {
        "manifest_path": LIVE_CAPTURE_MANIFEST.as_posix(),
        "manifest_sha256": sha256_file(manifest_path, root=root),
        "changed_ai_run_id": str(metadata.get("run_id", "")),
        "trace_rom_sha256": str(manifest.get("trace_rom_sha256", "")) if isinstance(manifest, dict) else "",
        "trace_symbols_sha256": str(manifest.get("trace_symbols_sha256", "")) if isinstance(manifest, dict) else "",
    }
    trace_by_route: dict[str, Path] = {}
    missing_trace_artifacts = []
    bad_trace_artifacts = []
    for value in trace_values:
        if not isinstance(value, str) or not value:
            continue
        path = root / metadata_path_item(value)
        if not path.exists():
            missing_trace_artifacts.append(value)
            continue
        try:
            trace = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            bad_trace_artifacts.append(repo_rel(root, path))
            continue
        if not isinstance(trace, dict):
            bad_trace_artifacts.append(repo_rel(root, path))
            continue
        route_id = str(trace.get("boss_route", ""))
        if route_id in expected_routes:
            trace_by_route[route_id] = path
    refreshed_routes = sorted(trace_by_route)
    status["refreshed_route_ids"] = refreshed_routes
    status["refreshed_route_count"] = len(refreshed_routes)
    status["missing_route_ids"] = sorted(set(expected_routes) - set(refreshed_routes))
    status["extra_route_ids"] = sorted(set(refreshed_routes) - set(expected_routes))
    route_trace_count = 0
    route_class_id_count = 0
    route_event_count = 0
    route_changed_event_count = 0
    for route_id in expected_routes:
        path = trace_by_route.get(route_id)
        if path is None:
            continue
        try:
            trace = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            bad_trace_artifacts.append(repo_rel(root, path))
            continue
        if not isinstance(trace, dict) or not route_contribution_trace_matches_manifest(
            trace,
            route_id=route_id,
            state_basis=state_basis,
        ):
            bad_trace_artifacts.append(repo_rel(root, path))
            continue
        route_trace_count += 1
        if trace.get("class_id"):
            route_class_id_count += 1
        route_event_count += int(trace.get("event_count", 0) or 0)
        route_changed_event_count += int(trace.get("changed_event_count", 0) or 0)
    status["missing_trace_artifacts"] = missing_trace_artifacts
    status["bad_trace_artifacts"] = bad_trace_artifacts
    status["route_trace_count"] = route_trace_count
    status["route_class_id_count"] = route_class_id_count
    status["route_event_count"] = route_event_count
    status["route_changed_event_count"] = route_changed_event_count
    blockers = []
    if status["missing_route_ids"]:
        blockers.append("changed_ai_contribution_refresh_scope_missing_routes")
    if status["extra_route_ids"]:
        blockers.append("changed_ai_contribution_refresh_scope_extra_routes")
    if missing_trace_artifacts:
        blockers.append("changed_ai_contribution_refresh_scope_missing_trace_artifacts")
    if bad_trace_artifacts:
        blockers.append("changed_ai_contribution_refresh_scope_bad_trace_artifacts")
    if route_trace_count != len(expected_routes):
        blockers.append("changed_ai_contribution_refresh_scope_trace_count_mismatch")
    if route_class_id_count != len(expected_routes):
        blockers.append("changed_ai_contribution_refresh_scope_class_ids_missing")
    status["available"] = True
    status["blocking_gaps"] = sorted(set(blockers))
    status["ready"] = not status["blocking_gaps"]
    return status


def changed_ai_expected_contribution_route_ids(root: Path) -> list[str]:
    try:
        from tools.trace.boss_ai_state_factory import ROUTES
    except Exception:  # noqa: BLE001
        return []
    manifest_path = root / LIVE_CAPTURE_MANIFEST
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    captures = manifest.get("captures", [])
    if not isinstance(captures, list):
        return []
    route_ids = []
    for capture_row in captures:
        if not isinstance(capture_row, dict):
            continue
        route_id = str(capture_row.get("id", ""))
        if route_id in ROUTES:
            route_ids.append(route_id)
    return route_ids


def route_contribution_trace_matches_manifest(
    trace: dict[str, Any],
    *,
    route_id: str,
    state_basis: dict[str, Any],
) -> bool:
    basis = trace.get("trace_basis", {})
    canonical = trace.get("canonical_state_class", {})
    return (
        trace.get("source") == "trace_rom_pyboy_hooks"
        and trace.get("boss_route") == route_id
        and basis.get("trace_rom_sha256") == state_basis.get("trace_rom_sha256")
        and basis.get("trace_symbols_sha256") == state_basis.get("trace_symbols_sha256")
        and bool(trace.get("class_id"))
        and isinstance(canonical, dict)
        and canonical.get("valid") is True
    )


def changed_ai_score_materialization_full_status(
    root: Path,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    status: dict[str, Any] = {
        "available": False,
        "coverage_ready": False,
        "artifact_path": SCORE_MATERIALIZATION_FULL_ARTIFACT.as_posix(),
        "closed_evidence_id": SCORE_MATERIALIZATION_FULL_EVIDENCE_ID,
        "expected_scenario_count": 0,
        "expected_checked_count": 0,
        "expected_skipped_count": 0,
        "materialized_scenario_count": 0,
        "checked_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "score_bytes_match_count": 0,
        "score_bytes_mismatch_count": 0,
        "selector_top_match_count": 0,
        "missing_scenario_ids": [],
        "extra_scenario_ids": [],
        "bad_skip_reason_ids": [],
        "bad_status_ids": [],
        "missing_class_id_ids": [],
        "blocking_gaps": [],
    }
    expected = changed_ai_score_materialization_expected_rows(root, metadata)
    expected_ids = list(expected)
    expected_checked_ids = [
        scenario_id for scenario_id, skip_reason in expected.items() if skip_reason is None
    ]
    expected_skipped = {
        scenario_id: skip_reason
        for scenario_id, skip_reason in expected.items()
        if skip_reason is not None
    }
    status["expected_scenario_count"] = len(expected_ids)
    status["expected_checked_count"] = len(expected_checked_ids)
    status["expected_skipped_count"] = len(expected_skipped)
    if not expected_ids:
        status["blocking_gaps"].append("changed_ai_score_materialization_no_expected_scenarios")
        return status
    artifact_path = root / SCORE_MATERIALIZATION_FULL_ARTIFACT
    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        status["blocking_gaps"].append("changed_ai_score_materialization_full_artifact_missing")
        return status
    except (OSError, json.JSONDecodeError):
        status["blocking_gaps"].append("changed_ai_score_materialization_full_artifact_unreadable")
        return status
    if not isinstance(artifact, dict):
        status["blocking_gaps"].append("changed_ai_score_materialization_full_artifact_malformed")
        return status
    status["available"] = True
    if artifact.get("kind") != "rom_score_materialization":
        status["blocking_gaps"].append("changed_ai_score_materialization_full_wrong_kind")
    status["materialized_scenario_count"] = int(artifact.get("scenario_count", 0) or 0)
    status["checked_count"] = int(artifact.get("checked_count", 0) or 0)
    status["skipped_count"] = int(artifact.get("skipped_count", 0) or 0)
    status["error_count"] = int(artifact.get("error_count", 0) or 0)
    status["score_bytes_match_count"] = int(artifact.get("score_bytes_match_count", 0) or 0)
    status["selector_top_match_count"] = int(artifact.get("selector_top_match_count", 0) or 0)
    verdicts = artifact.get("verdicts", [])
    if not isinstance(verdicts, list):
        verdicts = []
        status["blocking_gaps"].append("changed_ai_score_materialization_full_verdicts_malformed")
    materialized_ids = []
    verdict_by_id: dict[str, dict[str, Any]] = {}
    for verdict in verdicts:
        if not isinstance(verdict, dict) or not verdict.get("scenario_id"):
            continue
        scenario_id = str(verdict["scenario_id"])
        materialized_ids.append(scenario_id)
        verdict_by_id[scenario_id] = verdict
    expected_set = set(expected_ids)
    materialized_set = set(materialized_ids)
    missing = sorted(expected_set - materialized_set)
    extra = sorted(materialized_set - expected_set)
    bad_skip_reason_ids = []
    bad_status_ids = []
    missing_class_id_ids = []
    for scenario_id in expected_checked_ids:
        verdict = verdict_by_id.get(scenario_id)
        if not verdict:
            continue
        if verdict.get("status") != "pass":
            bad_status_ids.append(scenario_id)
        if not verdict.get("class_id") or not verdict.get("class_fingerprint"):
            missing_class_id_ids.append(scenario_id)
    for scenario_id, expected_reason in expected_skipped.items():
        verdict = verdict_by_id.get(scenario_id)
        if not verdict:
            continue
        if verdict.get("status") != "skipped":
            bad_status_ids.append(scenario_id)
            continue
        if str(verdict.get("reason", "")) != str(expected_reason):
            bad_skip_reason_ids.append(scenario_id)
    status["missing_scenario_ids"] = missing[:20]
    status["extra_scenario_ids"] = extra[:20]
    status["bad_skip_reason_ids"] = bad_skip_reason_ids[:20]
    status["bad_status_ids"] = bad_status_ids[:20]
    status["missing_class_id_ids"] = missing_class_id_ids[:20]
    if missing:
        status["blocking_gaps"].append("changed_ai_score_materialization_full_missing_scenarios")
    if extra:
        status["extra_scenario_ids"] = extra[:20]
    if bad_status_ids:
        status["blocking_gaps"].append("changed_ai_score_materialization_full_bad_status")
    if bad_skip_reason_ids:
        status["blocking_gaps"].append("changed_ai_score_materialization_full_bad_skip_reason")
    if missing_class_id_ids:
        status["blocking_gaps"].append("changed_ai_score_materialization_full_class_ids_missing")
    if len(materialized_ids) != len(materialized_set):
        status["blocking_gaps"].append("changed_ai_score_materialization_full_duplicate_scenarios")
    if status["materialized_scenario_count"] < len(expected_ids):
        status["blocking_gaps"].append("changed_ai_score_materialization_full_count_mismatch")
    if status["checked_count"] < len(expected_checked_ids):
        status["blocking_gaps"].append("changed_ai_score_materialization_full_checked_count_mismatch")
    if status["skipped_count"] < len(expected_skipped):
        status["blocking_gaps"].append("changed_ai_score_materialization_full_skipped_count_mismatch")
    if status["error_count"]:
        status["blocking_gaps"].append("changed_ai_score_materialization_full_errors")
    status["score_bytes_mismatch_count"] = max(
        0,
        len(expected_checked_ids) - status["score_bytes_match_count"],
    )
    status["blocking_gaps"] = sorted(set(status["blocking_gaps"]))
    status["coverage_ready"] = status["available"] and not status["blocking_gaps"]
    return status


def changed_ai_score_materialization_expected_rows(
    root: Path,
    metadata: dict[str, Any],
) -> dict[str, str | None]:
    artifacts = metadata.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return {}
    scenarios_value = artifacts.get("scenarios")
    if not isinstance(scenarios_value, str) or not scenarios_value:
        return {}
    scenarios_path = root / metadata_path_item(scenarios_value)
    try:
        scenarios = [
            json.loads(line)
            for line in scenarios_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, json.JSONDecodeError):
        return {}
    from tools.boss_ai_debugger.rom_score_materialize import (
        SUPPORTED_FAMILIES,
        score_materialization_skip_reason,
    )

    rows: dict[str, str | None] = {}
    for scenario in scenarios:
        if not isinstance(scenario, dict) or not scenario.get("id"):
            continue
        if scenario.get("family") not in SUPPORTED_FAMILIES:
            rows[str(scenario["id"])] = "unsupported scenario family"
        else:
            rows[str(scenario["id"])] = score_materialization_skip_reason(scenario)
    return rows


def changed_ai_metadata_evidence(root: Path) -> tuple[Path, dict[str, Any], dict[str, Any] | None] | None:
    summary_path = root / PROMOTED_CHANGED_AI_SUMMARY.relative_to(ROOT)
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        summary = None
    if isinstance(summary, dict):
        metadata = summary.get("changed_ai_run", {})
        if isinstance(metadata, dict) and metadata.get("profile") == "changed-ai":
            return summary_path, metadata, summary

    candidates: list[tuple[str, str, Path, dict[str, Any]]] = []
    runs_dir = root / "audit" / "boss_ai_debugger" / "runs"
    for metadata_path in runs_dir.glob("*/metadata.json"):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if metadata.get("profile") != "changed-ai":
            continue
        created_at = str(metadata.get("created_at", ""))
        run_id = str(metadata.get("run_id", metadata_path.parent.name))
        candidates.append((created_at, run_id, metadata_path, metadata))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1], item[2].as_posix()))
    _, _, metadata_path, metadata = candidates[-1]
    return metadata_path, metadata, None


def changed_ai_artifact_paths(metadata: dict[str, Any]) -> list[Path]:
    artifacts = metadata.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return []
    paths: list[Path] = []
    for value in artifacts.values():
        values = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, str) and item:
                paths.append(metadata_path_item(item))
    return paths


def changed_ai_metadata_artifact_path(metadata: dict[str, Any], key: str) -> Path | None:
    artifacts = metadata.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return None
    value = artifacts.get(key)
    if not isinstance(value, str) or not value:
        return None
    return metadata_path_item(value)


def promoted_summary_artifact_paths(summary: dict[str, Any] | None) -> list[Path]:
    if not isinstance(summary, dict):
        return []
    paths = []
    for key in ("targeted_generators", "review_queue"):
        section = summary.get(key, {})
        if isinstance(section, dict) and isinstance(section.get("artifact"), str):
            paths.append(metadata_path_item(str(section["artifact"])))
    hash_basis = summary.get("hash_basis", {})
    if isinstance(hash_basis, dict) and isinstance(hash_basis.get("manifest_path"), str):
        paths.append(metadata_path_item(str(hash_basis["manifest_path"])))
    return paths


def metadata_path_item(value: str) -> Path:
    return Path(value.replace("\\", "/"))


def string_values(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]


def universe_labels_classified(universe: dict[str, Any] | None) -> bool:
    if not isinstance(universe, dict):
        return False
    counters = universe.get("counters", {})
    if not isinstance(counters, dict):
        return False
    return (
        int(counters.get("missing_reachable_label_count", 0) or 0) == 0
        and int(counters.get("missing_rule_count", 0) or 0) == 0
    )


def universe_materialization_paths_available(universe: dict[str, Any] | None) -> bool:
    if not isinstance(universe, dict):
        return False
    counters = universe.get("counters", {})
    rows = universe.get("canonical_class_rows", [])
    if not isinstance(counters, dict) or not isinstance(rows, list) or not rows:
        return False
    if int(counters.get("missing_materialization_path_count", 0) or 0) != 0:
        return False
    return all(isinstance(row, dict) and bool(row.get("materializer_command")) for row in rows)


def exhaustive_witness_inventory_available(universe: dict[str, Any] | None) -> bool:
    if not isinstance(universe, dict):
        return False
    inventory = universe.get("exhaustive_class_witness_inventory")
    if not isinstance(inventory, dict):
        return False
    return isinstance(inventory.get("role_names"), list)


def exhaustive_witness_catalog_status(universe: dict[str, Any] | None) -> dict[str, Any]:
    status: dict[str, Any] = {
        "available": False,
        "ready": False,
        "blocking_gaps": [],
        "errors": [],
    }
    if not isinstance(universe, dict):
        return status
    catalog = universe.get("exhaustive_class_witness_catalog")
    if not isinstance(catalog, dict):
        return status
    status["available"] = True
    if catalog.get("kind") != "boss_ai_exhaustive_class_witness_catalog":
        status["errors"].append(f"unexpected witness catalog kind: {catalog.get('kind', '')}")
    inventory = universe.get("exhaustive_class_witness_inventory", {})
    inventory_missing = 0
    inventory_satisfied = 0
    if isinstance(inventory, dict):
        inventory_missing = int(inventory.get("missing_witness_role_count", 0) or 0)
        inventory_satisfied = int(inventory.get("satisfied_witness_role_count", 0) or 0)
    if catalog.get("proof_status") != "catalog_only":
        status["errors"].append("witness catalog proof_status must be catalog_only")
    if inventory_missing > 0 and catalog.get("proof_complete") is True:
        status["errors"].append("witness catalog must not claim proof_complete while inventory is red")
    if inventory_missing == 0 and catalog.get("proof_complete") is not True:
        status["errors"].append("witness catalog must claim proof_complete when inventory is fully proven")
    does_not_close = set(string_values(catalog.get("does_not_close", [])))
    if "boss_ai_exhaustive_class_witness_roles_missing" not in does_not_close:
        status["errors"].append("witness catalog must leave witness proof role gap open")
    closed_ids = set(string_values(catalog.get("closed_evidence_ids", [])))
    if EXHAUSTIVE_WITNESS_CATALOG_EVIDENCE_ID not in closed_ids:
        status["errors"].append("witness catalog missing narrow closed evidence id")
    if any("proofs" in item or "complete" in item for item in closed_ids):
        status["errors"].append("witness catalog closed evidence ids must not imply proof completion")

    rows = catalog.get("catalog_rows", [])
    if not isinstance(rows, list):
        rows = []
        status["errors"].append("witness catalog rows must be a list")
    required_count = int(catalog.get("required_witness_role_count", 0) or 0)
    cataloged_count = int(catalog.get("cataloged_witness_class_count", 0) or 0)
    if required_count <= 0:
        status["errors"].append("witness catalog has no required witness roles")
    if len(rows) != required_count or cataloged_count != required_count:
        status["errors"].append("witness catalog row count does not match required witness roles")
    if int(catalog.get("missing_witness_class_count", 0) or 0) != 0:
        status["errors"].append("witness catalog has missing generated classes")
    if int(catalog.get("invalid_witness_class_count", 0) or 0) != 0:
        status["errors"].append("witness catalog has invalid generated classes")
    if int(catalog.get("duplicate_class_id_count", 0) or 0) != 0:
        status["errors"].append("witness catalog has duplicate class ids")

    if int(catalog.get("missing_rom_proof_role_count", 0) or 0) != inventory_missing:
        status["errors"].append("witness catalog missing proof count does not match inventory")
    if int(catalog.get("rom_proven_witness_role_count", 0) or 0) != inventory_satisfied:
        status["errors"].append("witness catalog proven proof count does not match inventory")
    if inventory_missing > 0 and "boss_ai_exhaustive_class_witness_roles_missing" not in catalog.get("blocking_gaps", []):
        status["errors"].append("witness catalog must carry witness-role blocker while proofs are missing")

    seen: set[tuple[str, str]] = set()
    class_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            status["errors"].append("witness catalog row is not an object")
            continue
        key = (str(row.get("rule_id", "")), str(row.get("witness_role", "")))
        if not key[0] or key[1] not in {
            "positive",
            "negative",
            "boundary",
            "public_read_provenance",
            "counterfactual_flip",
        }:
            status["errors"].append("witness catalog row has invalid rule/role key")
        if key in seen:
            status["errors"].append(f"duplicate witness catalog row: {key[0]}:{key[1]}")
        seen.add(key)
        class_id = str(row.get("witness_class_id", "") or "")
        if not class_id:
            status["errors"].append(f"witness catalog row missing class id: {key[0]}:{key[1]}")
        elif class_id in class_ids:
            status["errors"].append(f"duplicate witness class id: {class_id}")
        class_ids.add(class_id)
        if row.get("canonical_state_class_valid") is not True:
            status["errors"].append(f"witness catalog row has invalid canonical class: {key[0]}:{key[1]}")
        if row.get("status") == "cataloged_missing_rom_proof":
            if row.get("proof_status") in {"complete", "exact_rom_proof"}:
                status["errors"].append(f"catalog-only witness row claims proof: {key[0]}:{key[1]}")
            if "rom_backed_witness_proof" not in string_values(row.get("missing_evidence", [])):
                status["errors"].append(f"catalog-only witness row missing proof gap: {key[0]}:{key[1]}")
            if "boss_ai_exhaustive_class_witness_roles_missing" not in string_values(row.get("blocking_gaps", [])):
                status["errors"].append(f"catalog-only witness row missing blocker: {key[0]}:{key[1]}")
        elif row.get("status") == "rom_proven":
            if int(row.get("observed_evidence_count", 0) or 0) <= 0:
                status["errors"].append(f"ROM-proven witness row lacks evidence: {key[0]}:{key[1]}")
        else:
            status["errors"].append(f"witness catalog row has invalid status: {key[0]}:{key[1]}")

    if status["errors"]:
        status["blocking_gaps"] = ["boss_ai_exhaustive_witness_class_catalog_invalid"]
    status["ready"] = status["available"] and not status["errors"]
    return status


def canonical_class_coverage_status(universe: dict[str, Any] | None) -> dict[str, Any]:
    status: dict[str, Any] = {
        "available": universe is not None,
        "ready": False,
        "class_row_count": 0,
        "valid_class_id_count": 0,
        "missing_class_id_count": 0,
        "invalid_class_id_count": 0,
        "first_problem_rows": [],
        "closed_evidence_id": RULE_TARGET_CLASS_EVIDENCE_ID,
        "blocking_gaps": [],
    }
    if universe is None:
        return status
    rows = universe.get("canonical_class_rows", [])
    if not isinstance(rows, list):
        status["blocking_gaps"].append("boss_ai_rule_target_canonical_class_rows_malformed")
        return status
    status["class_row_count"] = len(rows)
    for row in rows:
        if not isinstance(row, dict):
            status["invalid_class_id_count"] += 1
            if len(status["first_problem_rows"]) < 10:
                status["first_problem_rows"].append({"error": "row is not an object"})
            continue
        has_class_id = bool(row.get("class_id"))
        valid = row.get("canonical_state_class_valid") is True and not row.get("canonical_state_class_errors")
        if has_class_id and valid:
            status["valid_class_id_count"] += 1
            continue
        if not has_class_id:
            status["missing_class_id_count"] += 1
        else:
            status["invalid_class_id_count"] += 1
        if len(status["first_problem_rows"]) < 10:
            status["first_problem_rows"].append(
                {
                    "rule_id": row.get("rule_id", ""),
                    "class_id": row.get("class_id", ""),
                    "canonical_state_class_valid": row.get("canonical_state_class_valid", False),
                    "canonical_state_class_errors": row.get("canonical_state_class_errors", []),
                }
            )
    if status["class_row_count"] == 0:
        status["missing_class_id_count"] = max(1, status["missing_class_id_count"])
        status["blocking_gaps"].append("boss_ai_rule_target_canonical_class_ids_missing")
    if status["missing_class_id_count"]:
        status["blocking_gaps"].append("boss_ai_rule_target_canonical_class_ids_missing")
    if status["invalid_class_id_count"]:
        status["blocking_gaps"].append("boss_ai_rule_target_canonical_class_ids_invalid")
    status["blocking_gaps"] = sorted(set(status["blocking_gaps"]))
    status["ready"] = (
        status["class_row_count"] > 0
        and status["missing_class_id_count"] == 0
        and status["invalid_class_id_count"] == 0
    )
    return status


def generated_scenario_class_adoption_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "available": False,
        "ready": False,
        "scenario_checked": "",
        "class_id": "",
        "materializer_verdicts_checked": [],
        "blocking_gaps": [],
    }
    try:
        from tools.boss_ai_debugger.generators import generate_scenarios
        from tools.boss_ai_debugger.rom_score_materialize import skipped_verdict as score_skipped
        from tools.boss_ai_debugger.rom_selector_materialize import skipped_unready_verdict
        from tools.boss_ai_debugger.rom_switch_materialize import skipped_verdict as switch_skipped

        scenario = generate_scenarios(family="selector_edges", count=1, seed=1)[0]
        status["available"] = True
        status["scenario_checked"] = str(scenario.get("id", ""))
        status["class_id"] = str(scenario.get("class_id", ""))
        canonical = scenario.get("canonical_state_class")
        if not scenario.get("class_id") or not isinstance(canonical, dict):
            status["blocking_gaps"].append("boss_ai_generated_scenario_class_ids_missing")
        elif canonical.get("valid") is not True:
            status["blocking_gaps"].append("boss_ai_generated_scenario_class_ids_invalid")
        elif scenario.get("class_id") != canonical.get("class_id"):
            status["blocking_gaps"].append("boss_ai_generated_scenario_class_id_mismatch")

        verdicts = [
            skipped_unready_verdict(scenario, {"probabilities": {}}),
            score_skipped(scenario, "schema probe"),
            switch_skipped(scenario, "schema probe"),
        ]
        for verdict in verdicts:
            status["materializer_verdicts_checked"].append(str(verdict.get("status", "")))
            if verdict.get("class_id") != scenario.get("class_id"):
                status["blocking_gaps"].append("boss_ai_materializer_verdict_class_id_passthrough_missing")
                break
    except Exception as exc:  # noqa: BLE001
        status["blocking_gaps"].append(f"boss_ai_generated_scenario_class_probe_failed:{type(exc).__name__}")
    status["blocking_gaps"] = sorted(set(status["blocking_gaps"]))
    status["ready"] = status["available"] and not status["blocking_gaps"]
    return status


def live_trace_class_adoption_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "available": False,
        "ready": False,
        "trace_checked_count": 0,
        "class_id_count": 0,
        "blocking_gaps": [],
    }
    try:
        from tools.boss_ai_debugger.state_schema import DEFAULT_TRACE_DIR, validate_trace_dir

        report = validate_trace_dir(DEFAULT_TRACE_DIR)
        status["available"] = True
        status["trace_checked_count"] = int(report.get("checked_count", 0))
        status["class_id_count"] = int(report.get("class_id_count", 0))
        if not report.get("valid"):
            status["blocking_gaps"].append("boss_ai_live_trace_schema_invalid")
        if status["trace_checked_count"] <= 0:
            status["blocking_gaps"].append("boss_ai_live_trace_class_ids_missing")
        elif status["class_id_count"] != status["trace_checked_count"]:
            status["blocking_gaps"].append("boss_ai_live_trace_class_ids_incomplete")
    except Exception as exc:  # noqa: BLE001
        status["blocking_gaps"].append(f"boss_ai_live_trace_class_probe_failed:{type(exc).__name__}")
    status["blocking_gaps"] = sorted(set(status["blocking_gaps"]))
    status["ready"] = status["available"] and not status["blocking_gaps"]
    return status


def contribution_trace_class_adoption_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "available": False,
        "ready": False,
        "rom_artifact_count": 0,
        "rom_class_id_count": 0,
        "python_class_id_count": 0,
        "comparison_class_id_mismatch_count": 0,
        "comparison_missing_class_id_count": 0,
        "blocking_gaps": [],
    }
    try:
        from tools.boss_ai_debugger.contribution_compare import (
            compare_contribution_reports,
            python_contribution_report_from_scenarios,
        )
        from tools.boss_ai_debugger.generators import generate_scenarios
        from tools.boss_ai_debugger.rom_contribution_trace import (
            resolve_rom_contribution_trace_paths,
            stamp_rom_contribution_trace_class,
            summarize_rom_contribution_trace_paths,
        )

        rom_paths = resolve_rom_contribution_trace_paths(None)
        rom_summary = summarize_rom_contribution_trace_paths(rom_paths)
        status["available"] = True
        status["rom_artifact_count"] = int(rom_summary.get("artifact_count", 0))
        status["rom_class_id_count"] = int(rom_summary.get("class_id_count", 0))
        if status["rom_artifact_count"] <= 0:
            status["blocking_gaps"].append("boss_ai_rom_contribution_trace_artifacts_missing")
        elif status["rom_class_id_count"] != status["rom_artifact_count"]:
            status["blocking_gaps"].append("boss_ai_rom_contribution_trace_class_ids_incomplete")

        scenario = generate_scenarios(family="mastery_policy", count=1, seed=1)[0]
        python_report = python_contribution_report_from_scenarios([scenario])
        status["python_class_id_count"] = int(python_report.get("class_id_count", 0))
        if status["python_class_id_count"] != 1:
            status["blocking_gaps"].append("boss_ai_python_contribution_trace_class_ids_missing")
        rule_id = "move.apply_lookahead_to_top_move_candidates"
        rom_report = {
            "schema_version": 1,
            "source": "trace_rom_pyboy_hooks",
            "trace_id": scenario["id"],
            "scenario_id": scenario["id"],
            "save_state": f"scenario:{scenario['id']}",
            "trace_basis": {},
            "chosen": {},
            "move_ids": [],
            "move_scores": [],
            "pre_model_scores": [],
            "post_model_scores": [],
            "selector_entry_scores": [],
            "events": [
                {
                    "changed": True,
                    "operation": "python_score_delta",
                    "delta": 3,
                    "candidate": {"kind": "move", "slot_index": 0, "move_id": 1},
                    "source": {"rule_id": rule_id},
                }
            ],
            "event_count": 1,
            "changed_event_count": 1,
            "rule_entries": [],
            "predicate_branch_entries": [],
            "public_read_probe_entries": [],
            "known_limits": [],
            "decision_class_id": scenario["class_id"],
        }
        stamp_rom_contribution_trace_class(rom_report)
        comparison = compare_contribution_reports(
            rom_reports=[rom_report],
            python_reports=[python_report],
        )
        status["comparison_class_id_mismatch_count"] = int(
            comparison.get("class_id_mismatch_count", 0)
        )
        status["comparison_missing_class_id_count"] = int(
            comparison.get("missing_class_id_count", 0)
        )
        if int(comparison.get("matched_trace_count", 0)) != 1:
            status["blocking_gaps"].append("boss_ai_contribution_trace_class_comparison_unmatched")
        if status["comparison_missing_class_id_count"]:
            status["blocking_gaps"].append("boss_ai_contribution_trace_class_ids_missing_in_comparison")
        if status["comparison_class_id_mismatch_count"]:
            status["blocking_gaps"].append("boss_ai_contribution_trace_class_ids_mismatch")
    except Exception as exc:  # noqa: BLE001
        status["blocking_gaps"].append(f"boss_ai_contribution_trace_class_probe_failed:{type(exc).__name__}")
    status["blocking_gaps"] = sorted(set(status["blocking_gaps"]))
    status["ready"] = status["available"] and not status["blocking_gaps"]
    return status


def boss_ai_raw_class_adoption_status() -> dict[str, Any]:
    generated = generated_scenario_class_adoption_status()
    live = live_trace_class_adoption_status()
    contribution = contribution_trace_class_adoption_status()
    blocking_gaps = [
        *generated.get("blocking_gaps", []),
        *live.get("blocking_gaps", []),
        *contribution.get("blocking_gaps", []),
    ]
    closed: list[str] = []
    if generated.get("ready"):
        closed.extend([GENERATED_SCENARIO_CLASS_EVIDENCE_ID, MATERIALIZER_VERDICT_CLASS_EVIDENCE_ID])
    if live.get("ready"):
        closed.append(LIVE_TRACE_CLASS_EVIDENCE_ID)
    if contribution.get("ready"):
        closed.append(CONTRIBUTION_TRACE_CLASS_EVIDENCE_ID)
    return {
        "ready": generated.get("ready") and live.get("ready") and contribution.get("ready"),
        "closed_evidence_ids": closed,
        "blocking_gaps": sorted(set(str(item) for item in blocking_gaps)),
        "generated_scenario_class_adoption": generated,
        "live_trace_class_adoption": live,
        "contribution_trace_class_adoption": contribution,
    }


def summarize_universe_for_gate(universe: dict[str, Any] | None) -> dict[str, Any]:
    if universe is None:
        return {"available": False}
    surface_rows = list(universe.get("surface_rows", []))
    class_rows = list(universe.get("canonical_class_rows", []))
    witness_inventory = universe.get("exhaustive_class_witness_inventory", {})
    witness_catalog = universe.get("exhaustive_class_witness_catalog", {})
    witness_summary: dict[str, Any] = {"available": False}
    if isinstance(witness_inventory, dict):
        witness_summary = {
            "available": True,
            "ready": bool(witness_inventory.get("ready", False)),
            "role_names": list(witness_inventory.get("role_names", [])),
            "rule_count": int(witness_inventory.get("rule_count", 0) or 0),
            "missing_witness_role_count": int(
                witness_inventory.get("missing_witness_role_count", 0) or 0
            ),
            "satisfied_witness_role_count": int(
                witness_inventory.get("satisfied_witness_role_count", 0) or 0
            ),
            "status_counts": dict(witness_inventory.get("status_counts", {})),
            "blocking_gaps": list(witness_inventory.get("blocking_gaps", [])),
            "first_satisfied_roles": list(witness_inventory.get("first_satisfied_roles", []))[:10],
            "first_missing_roles": list(witness_inventory.get("first_missing_roles", []))[:10],
        }
    witness_catalog_summary: dict[str, Any] = {"available": False}
    if isinstance(witness_catalog, dict):
        witness_catalog_summary = {
            "available": True,
            "ready": bool(witness_catalog.get("ready", False)),
            "catalog_complete": bool(witness_catalog.get("catalog_complete", False)),
            "proof_complete": bool(witness_catalog.get("proof_complete", False)),
            "proof_status": str(witness_catalog.get("proof_status", "")),
            "closed_evidence_ids": list(witness_catalog.get("closed_evidence_ids", [])),
            "rule_count": int(witness_catalog.get("rule_count", 0) or 0),
            "required_witness_role_count": int(
                witness_catalog.get("required_witness_role_count", 0) or 0
            ),
            "required_witness_class_count": int(
                witness_catalog.get("required_witness_class_count", 0) or 0
            ),
            "not_applicable_role_count": int(
                witness_catalog.get("not_applicable_role_count", 0) or 0
            ),
            "cataloged_witness_class_count": int(
                witness_catalog.get("cataloged_witness_class_count", 0) or 0
            ),
            "generated_witness_class_count": int(
                witness_catalog.get("generated_witness_class_count", 0) or 0
            ),
            "rom_proven_witness_role_count": int(
                witness_catalog.get("rom_proven_witness_role_count", 0) or 0
            ),
            "missing_rom_proof_role_count": int(
                witness_catalog.get("missing_rom_proof_role_count", 0) or 0
            ),
            "missing_witness_class_count": int(
                witness_catalog.get("missing_witness_class_count", 0) or 0
            ),
            "invalid_witness_class_count": int(
                witness_catalog.get("invalid_witness_class_count", 0) or 0
            ),
            "duplicate_class_id_count": int(
                witness_catalog.get("duplicate_class_id_count", 0) or 0
            ),
            "role_counts": dict(witness_catalog.get("role_counts", {})),
            "status_counts": dict(witness_catalog.get("status_counts", {})),
            "blocking_gaps": list(witness_catalog.get("blocking_gaps", [])),
            "does_not_close": list(witness_catalog.get("does_not_close", [])),
        }
    return {
        "available": True,
        "proof_status": universe.get("proof_status", ""),
        "rule_count": universe.get("rule_count", 0),
        "reachable_label_count": universe.get("reachable_label_count", 0),
        "unmapped_label_count": universe.get("unmapped_label_count", 0),
        "dynamic_uncovered_rule_count": universe.get("dynamic_uncovered_rule_count", 0),
        "missing_public_read_provenance_count": universe.get("missing_public_read_provenance_count", 0),
        "counters": universe.get("counters", {}),
        "blocking_gaps": list(universe.get("blocking_gaps", [])),
        "next_command": universe.get("next_command", ""),
        "exhaustive_class_witness_inventory": witness_summary,
        "exhaustive_class_witness_catalog": witness_catalog_summary,
        "first_unmapped_surfaces": [
            row
            for row in surface_rows
            if isinstance(row, dict) and row.get("reachable_status") == "reachable_unmapped_label"
        ][:10],
        "first_missing_class_rows": [
            row
            for row in class_rows
            if isinstance(row, dict) and not row.get("class_id")
        ][:10],
    }


def write_outputs(report: dict[str, Any], *, out: Path, markdown_out: Path | None) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    if markdown_out is not None:
        markdown_out.parent.mkdir(parents=True, exist_ok=True)
        markdown_out.write_text(format_markdown(report), encoding="utf-8", newline="\n")


def format_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Debugger God Gate Baseline",
        "",
        f"- Generated: {report['generated_at']}",
        f"- boss_ai_god_ready: `{report['boss_ai_god_ready']}`",
        f"- proof_status: `{report['proof_status']}`",
        f"- questions_failed: `{report['questions_failed']}`",
        "",
        "## Counters",
        "",
    ]
    for key, value in report["counters"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Questions", "", "| id | status | proof | next |", "| --- | --- | --- | --- |"])
    for row in report["questions"]:
        lines.append(f"| {row['id']} | {row['status']} | {row['proof_status']} | `{row['next_command']}` |")
    return "\n".join(lines) + "\n"


def format_text(report: dict[str, Any]) -> str:
    lines = [
        "Boss AI debugger God gate",
        f"boss_ai_god_ready={report['boss_ai_god_ready']} proof_status={report['proof_status']}",
        f"questions={report['question_count']} failed={report['questions_failed']}",
    ]
    lines.append("counters=" + ", ".join(f"{key}={value}" for key, value in report["counters"].items()))
    if report["blocking_gaps"]:
        lines.extend(["", "Top blockers:"])
        for gap in report["blocking_gaps"][:8]:
            lines.append(f"  - {gap}")
    return "\n".join(lines)


def run_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        questions = root / "questions.jsonl"
        questions.write_text(
            json.dumps(
                {
                    "id": "synthetic_missing",
                    "requirement": "synthetic missing class",
                    "surface": "boss_ai",
                    "status": "missing_evidence",
                    "blocking_gaps": ["missing synthetic class"],
                    "next_command": "python synthetic",
                    "disproof_standard": "synthetic",
                    "missing_class_id_count": 1,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        report = build_god_report(questions_path=questions, root=ROOT, include_universe=False)
    failures = []
    if report["boss_ai_god_ready"]:
        failures.append("synthetic missing row should keep God gate red")
    if report["counters"]["missing_class_id_count"] != 1:
        failures.append("missing_class_id_count did not aggregate")
    if report["questions_failed"] != 1:
        failures.append("failed question count did not aggregate")
    if failures:
        print("SELF-TEST FAIL:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SELF-TEST PASS: Boss AI God skeleton fails closed on missing evidence.")
    return 0


def repo_rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Boss AI God-level fail-closed gate skeleton.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--read-only", action="store_true", help="do not write baseline artifacts")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--no-universe", action="store_true", help="skip generated Boss AI universe packet")
    parser.add_argument("--universe-json", type=Path, help="consume a prebuilt Boss AI universe packet")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--markdown-out", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.self_test:
        return run_self_test()
    universe_report = None
    if args.universe_json is not None:
        universe_report = json.loads(args.universe_json.read_text(encoding="utf-8"))
    report = build_god_report(
        questions_path=args.questions,
        include_universe=not args.no_universe,
        universe_report=universe_report,
    )
    out = args.out
    markdown_out = args.markdown_out
    if args.baseline:
        stamp = today_stamp()
        if args.out == DEFAULT_OUT:
            out = BENCHMARK_DIR / f"baseline_{stamp}.json"
        if markdown_out is None:
            markdown_out = BENCHMARK_DIR / f"baseline_{stamp}.md"
    if not args.read_only and (args.baseline or args.out != DEFAULT_OUT or args.markdown_out is not None):
        write_outputs(report, out=out, markdown_out=markdown_out)
        report["json_out"] = str(out)
        if markdown_out is not None:
            report["markdown_out"] = str(markdown_out)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_text(report))
        if report.get("json_out"):
            print(f"json_out={report['json_out']}")
        if report.get("markdown_out"):
            print(f"markdown_out={report['markdown_out']}")
    return 0 if report["boss_ai_god_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
