from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .rom_scenarios import evaluate_batch, load_scenario_batch
from .trace_replay import replay_trace_paths


def differential_from_paths(
    *,
    scenarios_path: Path | None = None,
    trace_dir: Path | None = None,
    trace_glob: str = "*_live.txt",
) -> dict[str, Any]:
    scenarios = load_scenario_batch(scenarios_path) if scenarios_path is not None else []
    trace_paths = []
    if trace_dir is not None and trace_dir.exists():
        trace_paths = sorted(trace_dir.glob(trace_glob))
    return build_differential_report(
        scenarios=scenarios,
        trace_paths=trace_paths,
        source={
            "scenarios": str(scenarios_path) if scenarios_path is not None else "",
            "trace_dir": str(trace_dir) if trace_dir is not None else "",
        },
    )


def build_differential_report(
    *,
    scenarios: list[dict[str, Any]] | None = None,
    trace_paths: list[Path] | None = None,
    source: str | dict[str, str] = "inline",
) -> dict[str, Any]:
    scenario_rows = scenarios or []
    trace_rows = trace_paths or []
    mismatches: list[dict[str, Any]] = []

    batch = evaluate_batch(scenario_rows) if scenario_rows else empty_batch_report()
    mismatches.extend(policy_mismatches(batch))

    trace_replay = replay_trace_paths(trace_rows) if trace_rows else empty_trace_report()
    mismatches.extend(trace_mismatches(trace_replay))

    class_counts: dict[str, int] = {}
    for mismatch in mismatches:
        key = mismatch["class"]
        class_counts[key] = class_counts.get(key, 0) + 1

    return {
        "schema_version": 1,
        "source": source,
        "scenario_count": len(scenario_rows),
        "trace_file_count": len(trace_rows),
        "mismatch_count": len(mismatches),
        "mismatch_class_counts": dict(sorted(class_counts.items())),
        "batch_summary": {
            "reviewable_count": batch["reviewable_count"],
            "verdict_counts": batch["verdict_counts"],
        },
        "trace_summary": {
            "checked_count": trace_replay["checked_count"],
            "failure_count": trace_replay["failure_count"],
            "agreement_rate": trace_replay["agreement_rate"],
            "exact_agreement_rate": trace_replay.get("exact_agreement_rate", 0.0),
        },
        "mismatches": sorted(
            mismatches,
            key=lambda item: (-int(item["severity"]), item["id"]),
        ),
        "known_gaps": [
            "ROM hook score-helper traces exist, but this differential report does not compare them yet.",
            "Rule-delta, missing-ROM-rule, and missing-Python-rule mismatches require contribution-trace comparison.",
            "Scenario policy mismatches are debugger expectation checks, not ROM materialized-state replays.",
        ],
    }


def policy_mismatches(batch: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for verdict in batch.get("verdicts", []):
        severity = int(verdict.get("severity", 0))
        if severity <= 0:
            continue
        result.append(
            {
                "id": f"policy:{verdict['scenario_id']}",
                "class": "policy_preference_mismatch",
                "status": "hypothesis",
                "severity": severity,
                "scenario_id": verdict["scenario_id"],
                "verdict": verdict["verdict"],
                "rom_best_action_id": verdict.get("rom_best_action_id"),
                "rom_best_probability": verdict.get("rom_best_probability"),
                "expected_best_action_ids": verdict.get("expected_best_action_ids", []),
                "expected_acceptable_action_ids": verdict.get(
                    "expected_acceptable_action_ids",
                    [],
                ),
                "reason": verdict.get("reason", ""),
                "policy_tags": verdict.get("policy_tags", []),
                "condition_tags": verdict.get("condition_tags", []),
                "evidence_refs": verdict.get("evidence_refs", []),
            }
        )
    return result


def trace_mismatches(trace_replay: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for verdict in trace_replay.get("verdicts", []):
        if verdict.get("verdict") == "mismatch":
            result.append(
                {
                    "id": f"trace:{verdict['capture_id']}",
                    "class": "selector_mismatch",
                    "status": "confirmed",
                    "severity": 100,
                    "capture_id": verdict["capture_id"],
                    "path": verdict.get("path", ""),
                    "mode": verdict.get("mode", ""),
                    "chosen_id": verdict.get("chosen_id"),
                    "expected_move_ids": verdict.get("expected_move_ids", []),
                    "reason": verdict.get("reason", ""),
                }
            )
            continue
        if verdict.get("mode") in {"none", "partial_top3"}:
            result.append(
                {
                    "id": f"trace_incomplete:{verdict['capture_id']}",
                    "class": "trace_incomplete",
                    "status": "hypothesis",
                    "severity": 20,
                    "capture_id": verdict["capture_id"],
                    "path": verdict.get("path", ""),
                    "mode": verdict.get("mode", ""),
                    "reason": verdict.get("reason", ""),
                }
            )
    return result


def empty_batch_report() -> dict[str, Any]:
    return {
        "scenario_count": 0,
        "reviewable_count": 0,
        "verdict_counts": {},
        "verdicts": [],
    }


def empty_trace_report() -> dict[str, Any]:
    return {
        "checked_count": 0,
        "failure_count": 0,
        "agreement_rate": 0.0,
        "exact_agreement_rate": 0.0,
        "verdicts": [],
    }


def format_differential_report(report: dict[str, Any], *, limit: int = 20) -> str:
    counts = " ".join(
        f"{name}={count}" for name, count in report["mismatch_class_counts"].items()
    )
    lines = [
        "Boss AI differential report",
        (
            f"scenarios={report['scenario_count']} traces={report['trace_file_count']} "
            f"mismatches={report['mismatch_count']}"
        ),
        f"classes: {counts or 'none'}",
        (
            "trace: "
            f"checked={report['trace_summary']['checked_count']} "
            f"failures={report['trace_summary']['failure_count']} "
            f"agreement={report['trace_summary']['agreement_rate']:.4%}"
        ),
    ]
    if report["mismatches"]:
        lines.extend(["", f"Top {limit} mismatches:"])
        for item in report["mismatches"][:limit]:
            lines.append(
                f"  {item['severity']:>3} {item['class']} {item['id']} "
                f"status={item['status']}"
            )
            lines.append(f"      {item.get('reason', '')}")
    lines.append("")
    lines.append("Known gaps:")
    for gap in report["known_gaps"]:
        lines.append(f"  - {gap}")
    return "\n".join(lines)


def write_differential_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
