from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError

from .generators import FAMILIES


Z_95 = 1.96
REVIEWABLE_VERDICTS = {
    "acceptable_top",
    "bad_roll",
    "best_never_rolled",
    "catastrophic_roll",
    "mismatch",
    "partial_best_unrolled",
    "weak_best",
}
HARD_FAILURE_VERDICTS = {
    "bad_roll",
    "best_never_rolled",
    "catastrophic_roll",
    "mismatch",
}


def build_confidence_report_from_paths(
    *,
    batch_report_path: Path,
    materialization_paths: list[Path] | None = None,
) -> dict[str, Any]:
    batch_report = read_json_object(batch_report_path)
    materializations = [
        read_json_object(path) for path in (materialization_paths or [])
    ]
    return build_confidence_report(
        batch_report,
        materialization_reports=materializations,
        source=str(batch_report_path),
    )


def build_confidence_report(
    batch_report: dict[str, Any],
    *,
    materialization_reports: list[dict[str, Any]] | None = None,
    source: str = "inline",
) -> dict[str, Any]:
    verdicts = batch_report.get("verdicts", [])
    if not isinstance(verdicts, list):
        raise PreferenceDataError("batch report must contain a verdicts list")

    family_rows = summarize_groups(
        verdicts,
        key_fn=lambda verdict: family_for_scenario_id(str(verdict.get("scenario_id", ""))),
    )
    policy_rows = summarize_groups(
        verdicts,
        key_fn=lambda verdict: list_of_strings(verdict.get("policy_tags")),
    )
    condition_rows = summarize_groups(
        verdicts,
        key_fn=lambda verdict: list_of_strings(verdict.get("condition_tags")),
    )
    materialization = summarize_materializations(materialization_reports or [])

    return {
        "schema_version": 1,
        "source": source,
        "scenario_count": int(batch_report.get("scenario_count", len(verdicts))),
        "reviewable_count": int(batch_report.get("reviewable_count", 0)),
        "verdict_counts": batch_report.get("verdict_counts", {}),
        "families": attach_materialization_counts(family_rows, materialization),
        "policy_tags": policy_rows,
        "condition_tags": condition_rows[:50],
        "materialization": materialization,
        "confidence_notes": [
            "This is a stratified generated-corpus confidence report, not proof that unsupported families have full ROM score materialization.",
            "The upper bound is a Wilson 95% upper confidence bound on reviewable or hard-failure rate within each observed stratum.",
            "ROM selector materialization proves selector behavior from patched score bytes; ROM score materialization proves observed source scoring for supported move-policy families.",
            "ROM switch materialization proves switch-dispatch proposal behavior separately from move-score materialization.",
        ],
    }


def summarize_groups(
    verdicts: list[Any],
    *,
    key_fn: Any,
) -> list[dict[str, Any]]:
    counts: dict[str, dict[str, int]] = {}
    for verdict in verdicts:
        if not isinstance(verdict, dict):
            continue
        keys = key_fn(verdict)
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            row = counts.setdefault(
                key or "unknown",
                {"scenario_count": 0, "reviewable_count": 0, "hard_failure_count": 0},
            )
            row["scenario_count"] += 1
            verdict_name = str(verdict.get("verdict", ""))
            severity = int(verdict.get("severity", 0))
            if severity > 0 or verdict_name in REVIEWABLE_VERDICTS:
                row["reviewable_count"] += 1
            if verdict_name in HARD_FAILURE_VERDICTS:
                row["hard_failure_count"] += 1

    rows = []
    for key, row in counts.items():
        scenario_count = row["scenario_count"]
        reviewable_count = row["reviewable_count"]
        hard_failure_count = row["hard_failure_count"]
        rows.append(
            {
                "key": key,
                "scenario_count": scenario_count,
                "reviewable_count": reviewable_count,
                "hard_failure_count": hard_failure_count,
                "reviewable_rate": ratio(reviewable_count, scenario_count),
                "hard_failure_rate": ratio(hard_failure_count, scenario_count),
                "reviewable_rate_95_upper": wilson_upper_bound(
                    reviewable_count,
                    scenario_count,
                ),
                "hard_failure_rate_95_upper": wilson_upper_bound(
                    hard_failure_count,
                    scenario_count,
                ),
                "confidence_grade": confidence_grade(
                    scenario_count=scenario_count,
                    hard_failure_upper=wilson_upper_bound(
                        hard_failure_count,
                        scenario_count,
                    ),
                ),
            }
        )
    return sorted(
        rows,
        key=lambda item: (
            -int(item["hard_failure_count"]),
            -int(item["reviewable_count"]),
            str(item["key"]),
        ),
    )


def summarize_materializations(reports: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, dict[str, int]] = {}
    totals = {
        "report_count": len(reports),
        "selector_checked_count": 0,
        "selector_mismatch_count": 0,
        "score_checked_count": 0,
        "score_mismatch_count": 0,
        "score_bytes_mismatch_count": 0,
        "score_policy_reviewable_count": 0,
        "score_policy_hard_failure_count": 0,
        "switch_checked_count": 0,
        "switch_policy_reviewable_count": 0,
        "switch_policy_hard_failure_count": 0,
        "score_error_count": 0,
        "switch_error_count": 0,
    }
    for report in reports:
        kind = str(report.get("kind", ""))
        verdicts = report.get("verdicts", [])
        if not isinstance(verdicts, list):
            continue
        for verdict in verdicts:
            if not isinstance(verdict, dict):
                continue
            scenario_id = str(verdict.get("scenario_id", ""))
            family = str(verdict.get("family") or family_for_scenario_id(scenario_id))
            row = by_family.setdefault(
                family,
                {
                    "selector_checked_count": 0,
                    "selector_mismatch_count": 0,
                    "score_checked_count": 0,
                    "score_mismatch_count": 0,
                    "score_bytes_mismatch_count": 0,
                    "score_policy_reviewable_count": 0,
                    "score_policy_hard_failure_count": 0,
                    "switch_checked_count": 0,
                    "switch_policy_reviewable_count": 0,
                    "switch_policy_hard_failure_count": 0,
                    "score_error_count": 0,
                    "switch_error_count": 0,
                },
            )
            if kind == "rom_selector_materialization":
                if verdict.get("status") != "skipped_unready":
                    row["selector_checked_count"] += 1
                    totals["selector_checked_count"] += 1
                    if not bool(verdict.get("agreement", False)):
                        row["selector_mismatch_count"] += 1
                        totals["selector_mismatch_count"] += 1
            elif kind == "rom_score_materialization":
                if verdict.get("status") == "pass":
                    row["score_checked_count"] += 1
                    totals["score_checked_count"] += 1
                    if not bool(verdict.get("selector_top_match", False)):
                        row["score_mismatch_count"] += 1
                        totals["score_mismatch_count"] += 1
                    if not bool(verdict.get("score_bytes_match", False)):
                        row["score_bytes_mismatch_count"] += 1
                        totals["score_bytes_mismatch_count"] += 1
                    rom_policy = verdict.get("rom_policy", {})
                    if isinstance(rom_policy, dict):
                        policy_verdict = str(rom_policy.get("verdict", ""))
                        policy_severity = int(rom_policy.get("severity", 0))
                        if policy_severity > 0 or policy_verdict in REVIEWABLE_VERDICTS:
                            row["score_policy_reviewable_count"] += 1
                            totals["score_policy_reviewable_count"] += 1
                        if policy_verdict in HARD_FAILURE_VERDICTS:
                            row["score_policy_hard_failure_count"] += 1
                            totals["score_policy_hard_failure_count"] += 1
                elif verdict.get("status") == "error":
                    row["score_error_count"] += 1
                    totals["score_error_count"] += 1
            elif kind == "rom_switch_materialization":
                if verdict.get("status") == "pass":
                    row["switch_checked_count"] += 1
                    totals["switch_checked_count"] += 1
                    rom_policy = verdict.get("rom_policy", {})
                    if isinstance(rom_policy, dict):
                        policy_verdict = str(rom_policy.get("verdict", ""))
                        policy_severity = int(rom_policy.get("severity", 0))
                        if policy_severity > 0 or policy_verdict in REVIEWABLE_VERDICTS:
                            row["switch_policy_reviewable_count"] += 1
                            totals["switch_policy_reviewable_count"] += 1
                        if policy_verdict in HARD_FAILURE_VERDICTS:
                            row["switch_policy_hard_failure_count"] += 1
                            totals["switch_policy_hard_failure_count"] += 1
                elif verdict.get("status") == "error":
                    row["switch_error_count"] += 1
                    totals["switch_error_count"] += 1

    return {
        **totals,
        "by_family": dict(sorted(by_family.items())),
    }


def attach_materialization_counts(
    family_rows: list[dict[str, Any]],
    materialization: dict[str, Any],
) -> list[dict[str, Any]]:
    by_family = materialization.get("by_family", {})
    if not isinstance(by_family, dict):
        by_family = {}
    rows = []
    for row in family_rows:
        materialized = by_family.get(row["key"], {})
        if not isinstance(materialized, dict):
            materialized = {}
        rows.append({**row, "materialization": materialized})
    return rows


def family_for_scenario_id(scenario_id: str) -> str:
    prefix = "generated_"
    if scenario_id.startswith(prefix):
        rest = scenario_id[len(prefix) :]
        for family in sorted(FAMILIES, key=len, reverse=True):
            marker = f"{family}_"
            if rest.startswith(marker):
                return family
    return "unknown"


def list_of_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def wilson_upper_bound(failures: int, total: int) -> float:
    if total <= 0:
        return 1.0
    p_hat = failures / total
    z2 = Z_95 * Z_95
    denominator = 1 + z2 / total
    center = (p_hat + z2 / (2 * total)) / denominator
    margin = (
        Z_95
        * math.sqrt((p_hat * (1 - p_hat) + z2 / (4 * total)) / total)
        / denominator
    )
    return min(1.0, center + margin)


def confidence_grade(
    *,
    scenario_count: int,
    hard_failure_upper: float,
) -> str:
    if scenario_count >= 300 and hard_failure_upper <= 0.05:
        return "strong_generated"
    if scenario_count >= 100 and hard_failure_upper <= 0.10:
        return "moderate_generated"
    return "exploratory"


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def read_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PreferenceDataError(f"{path}: expected JSON object")
    return data


def write_confidence_report_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def format_confidence_report(report: dict[str, Any], *, limit: int = 12) -> str:
    lines = [
        "Boss AI debugger confidence report",
        (
            f"source={report['source']} scenarios={report['scenario_count']} "
            f"reviewable={report['reviewable_count']}"
        ),
        "Families:",
    ]
    for row in report["families"][:limit]:
        materialized = row.get("materialization", {})
        lines.append(
            f"  {row['key']}: n={row['scenario_count']} "
            f"reviewable={row['reviewable_count']} "
            f"hard={row['hard_failure_count']} "
            f"hard95<={row['hard_failure_rate_95_upper']:.1%} "
            f"grade={row['confidence_grade']} "
            f"selector_rom={materialized.get('selector_checked_count', 0)} "
            f"score_rom={materialized.get('score_checked_count', 0)} "
            f"score_policy_review={materialized.get('score_policy_reviewable_count', 0)} "
            f"switch_rom={materialized.get('switch_checked_count', 0)} "
            f"switch_policy_review={materialized.get('switch_policy_reviewable_count', 0)}"
        )
    lines.append("Top policy tags:")
    for row in report["policy_tags"][:limit]:
        lines.append(
            f"  {row['key']}: n={row['scenario_count']} "
            f"reviewable={row['reviewable_count']} "
            f"hard={row['hard_failure_count']} "
            f"hard95<={row['hard_failure_rate_95_upper']:.1%}"
        )
    lines.append("Known limits:")
    for note in report["confidence_notes"]:
        lines.append(f"  - {note}")
    return "\n".join(lines)
