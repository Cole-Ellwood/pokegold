from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .data import (
    DEFAULT_FIXTURES_PATH,
    DEFAULT_LABELS_PATH,
    DEFAULT_PREFERENCES_PATH,
    load_fixtures,
    load_labels,
    load_preferences,
)
from .lessons import (
    DEFAULT_LESSONS_PATH,
    build_lesson_report,
    load_lessons,
)
from .reward_model import build_reward_model_report
from .trajectory_data import (
    DEFAULT_PLAN_DEMONSTRATIONS_PATH,
    DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    build_trajectory_report,
    load_plan_demonstrations,
    load_trajectory_preferences,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROPOSAL_REPORT_PATH = ROOT / "audit" / "boss_ai_preference" / "proposals.md"
DEFAULT_PROPOSAL_JSON_PATH = ROOT / "audit" / "boss_ai_preference" / "proposals.json"
BEHAVIOR_PROPOSAL_TYPES = {
    "hard_rule",
    "scoring_weight",
    "switch_policy",
    "sequence_policy",
    "scout_policy",
    "mixed_strategy",
}


def proposal_id(lesson_id: str, proposal_type: str) -> str:
    return f"{proposal_type}:{lesson_id}"


def source_count(lesson: dict[str, Any]) -> int:
    return len(lesson.get("source_preference_ids", []))


def source_hits(rows: list[dict[str, Any]], lesson: dict[str, Any]) -> list[dict[str, Any]]:
    sources = set(lesson.get("source_preference_ids", []))
    return [row for row in rows if row.get("preference_id") in sources]


def proposal_type_for_lesson(
    lesson: dict[str, Any],
    model_fixes: list[dict[str, Any]],
) -> str:
    lesson_type = lesson["lesson_type"]
    count = source_count(lesson)
    if lesson_type == "schema_only":
        return "schema_only"
    if lesson_type == "hard_rule":
        return "hard_rule" if count >= 1 else "needs_more_labels"
    if lesson_type == "weight_hint":
        return "scoring_weight" if model_fixes and count >= 2 else "needs_more_labels"
    if lesson_type == "switch_policy":
        return "switch_policy" if count >= 2 else "needs_more_labels"
    if lesson_type in {"sequence_policy", "scout_policy"}:
        return lesson_type if count >= 2 else "needs_more_labels"
    if lesson_type == "fixture_bug":
        return "fixture_update"
    return "needs_more_labels"


def implementation_text(proposal_type: str, lesson: dict[str, Any]) -> str:
    if proposal_type == "schema_only":
        return "Improve the preference UI/query shape; do not change ROM behavior."
    if proposal_type == "scoring_weight":
        return "Adjust an offline feature weight or produce a small scorer-diff candidate for human review."
    if proposal_type == "hard_rule":
        return "Draft a narrow ASM fail/discourage rule only after reviewing the listed examples."
    if proposal_type == "switch_policy":
        return "Review move-vs-switch arbitration and add targeted switch-action fixtures first."
    if proposal_type == "scout_policy":
        return "Generate scout/probe counterfactuals and review a narrow information-value scorer change."
    if proposal_type == "sequence_policy":
        return "Add plan/counterfactual coverage for the stop condition before any ROM change."
    if proposal_type == "fixture_update":
        return "Refresh stale fixtures against the current trainer party/moveset source."
    if proposal_type == "needs_conflict_resolution":
        return "Resolve conflicting trajectory labels before drafting any behavior change."
    return "Ask for more boundary labels before proposing a behavior change."


def verification_for(proposal_type: str) -> list[str]:
    checks = [
        "python -m tools.boss_ai_preference validate",
        "python tools\\audit\\check_boss_ai_preference.py",
    ]
    if proposal_type in {
        "hard_rule",
        "scoring_weight",
        "switch_policy",
        "sequence_policy",
        "scout_policy",
        "mixed_strategy",
    }:
        checks.extend(
            [
                "python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json",
                "python tools\\audit\\check_boss_ai_trace_invariants.py",
                "python tools\\audit\\check_boss_ai_policy_contract.py",
                "python tools\\audit\\check_boss_ai_no_cheat.py",
                "python tools\\audit\\check_boss_ai_gating.py",
                "python tools\\audit\\check_boss_ai_memory_budget.py",
            ]
        )
    return checks


def proposal_contract(proposal_type: str, blockers: list[str] | None = None) -> dict[str, Any]:
    blockers = blockers or []
    return {
        "rom_behavior_change": False,
        "requires_human_approval": True,
        "readiness": "blocked" if blockers else "manual_review",
        "blocking_reasons": blockers,
    }


def conflict_keys(trajectory_report: dict[str, Any]) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for conflict in trajectory_report.get("conflicts", []):
        ids = sorted(str(item) for item in conflict.get("trajectory_ids", []))
        if len(ids) == 2:
            keys.add((str(conflict.get("fixture_id")), ids[0], ids[1]))
    return keys


def row_conflict_key(row: dict[str, Any]) -> tuple[str, str, str]:
    ids = sorted([str(row["trajectory_a_id"]), str(row["trajectory_b_id"])])
    return (str(row["fixture_id"]), ids[0], ids[1])


def trajectory_blockers(
    row: dict[str, Any],
    phase_coverage: set[str],
    conflict_key_set: set[tuple[str, str, str]],
) -> list[str]:
    blockers: list[str] = []
    if row_conflict_key(row) in conflict_key_set:
        blockers.append("resolve conflicting trajectory choices for this plan pair")
    if row.get("choice") in {"needs_context", "upstream_state_issue"}:
        blockers.append("fixture/context issue needs a clearer source state")
    if row.get("confidence") == "low":
        blockers.append("low-confidence trajectory row")
    if row.get("choice") in {"a_better", "b_better"} and not row.get("condition_tags"):
        blockers.append("strict plan preference needs condition tags")
    if len(phase_coverage) < 2:
        blockers.append("collect the same lesson type in at least two battle phases")
    return blockers


def trajectory_proposal_type(
    row: dict[str, Any],
    phase_coverage: set[str],
    blockers: list[str],
) -> str:
    if any("conflicting" in blocker for blocker in blockers):
        return "needs_conflict_resolution"
    if blockers:
        return "needs_more_labels"
    lesson_type = str(row.get("lesson_type") or "")
    if lesson_type in {"sequence_policy", "switch_policy", "scout_policy"}:
        return lesson_type
    if lesson_type == "personality_style":
        return "mixed_strategy"
    if row.get("choice") in {"depends", "both_good"}:
        return "mixed_strategy" if len(phase_coverage) >= 2 else "needs_more_labels"
    return "needs_more_labels"


def add_trajectory_proposals(
    proposals: list[dict[str, Any]],
    trajectory_report: dict[str, Any],
) -> None:
    phases_by_type: dict[str, set[str]] = {}
    for row in trajectory_report["trajectories"]:
        lesson_type = str(row.get("lesson_type") or "untyped")
        phases_by_type.setdefault(lesson_type, set()).add(str(row.get("phase") or "unknown"))

    conflict_key_set = conflict_keys(trajectory_report)
    demonstrations_by_fixture: dict[str, list[str]] = {}
    for demo in trajectory_report.get("demonstrations", []):
        demonstrations_by_fixture.setdefault(str(demo["fixture_id"]), []).append(
            str(demo["demonstration_id"])
        )

    for row in trajectory_report["trajectories"]:
        lesson_type = str(row.get("lesson_type") or "untyped")
        phase_coverage = phases_by_type.get(lesson_type, set())
        blockers = trajectory_blockers(row, phase_coverage, conflict_key_set)
        proposal_type = trajectory_proposal_type(row, phase_coverage, blockers)
        evidence_id = (
            f"{row['fixture_id']}:{row['trajectory_a_id']}:{row['trajectory_b_id']}"
        )
        proposals.append(
            {
                "proposal_id": f"{proposal_type}:trajectory:{evidence_id}",
                "proposal_type": proposal_type,
                "lesson_id": f"trajectory:{lesson_type}",
                "title": (
                    "Use trajectory evidence for a plan-policy proposal."
                    if proposal_type != "needs_more_labels"
                    else "Collect more trajectory labels before changing behavior."
                ),
                "evidence": [evidence_id],
                "evidence_details": {
                    "choice": row["choice"],
                    "confidence": row.get("confidence", "unspecified"),
                    "condition_tags": row.get("condition_tags", []),
                    "branch_tags": row.get("branch_tags", []),
                    "phase_coverage": sorted(phase_coverage),
                    "related_demonstrations": demonstrations_by_fixture.get(
                        str(row["fixture_id"]),
                        [],
                    ),
                    "note": str(row.get("note", ""))[:240],
                },
                "improves": [],
                "risks_or_worsens": [],
                "suggested_implementation": implementation_text(proposal_type, {"lesson_type": lesson_type}),
                "required_verification": verification_for(proposal_type),
                **proposal_contract(proposal_type, blockers),
            }
        )


def build_proposal_report(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
    manual_lessons: list[dict[str, Any]],
    trajectories: list[dict[str, Any]] | None = None,
    demonstrations: list[dict[str, Any]] | None = None,
    *,
    include_trajectories: bool = True,
) -> dict[str, Any]:
    trajectories = trajectories or []
    demonstrations = demonstrations or []
    lesson_report = build_lesson_report(
        fixtures,
        labels,
        preferences,
        manual_lessons,
        trajectories if include_trajectories else [],
    )
    reward_report = build_reward_model_report(
        fixtures,
        preferences,
        trajectories,
        include_trajectories=include_trajectories,
    )
    scorer_misses = reward_report["model_correct_scorer_missed"]
    model_misses = reward_report["scorer_correct_model_missed"]

    proposals: list[dict[str, Any]] = []
    for lesson in lesson_report["lessons"]:
        if lesson["status"] == "rejected":
            continue
        fixes = source_hits(scorer_misses, lesson)
        worsens = source_hits(model_misses, lesson)
        proposal_type = proposal_type_for_lesson(lesson, fixes)
        proposals.append(
            {
                "proposal_id": proposal_id(lesson["lesson_id"], proposal_type),
                "proposal_type": proposal_type,
                "lesson_id": lesson["lesson_id"],
                "title": lesson["human_summary"],
                "evidence": lesson["source_preference_ids"],
                "improves": [row["preference_id"] for row in fixes],
                "risks_or_worsens": [row["preference_id"] for row in worsens],
                "suggested_implementation": implementation_text(proposal_type, lesson),
                "required_verification": verification_for(proposal_type),
                **proposal_contract(proposal_type),
            }
        )

    stale_rows = lesson_report["stale_direct_actions"]
    if stale_rows:
        proposals.append(
            {
                "proposal_id": "fixture_update:stale_direct_action_reanchor",
                "proposal_type": "fixture_update",
                "lesson_id": "stale_direct_action_reanchor",
                "title": "Re-anchor direct action judgments after team and moveset changes.",
                "evidence": [row["preference_id"] for row in stale_rows],
                "improves": [],
                "risks_or_worsens": [],
                "suggested_implementation": (
                    "Generate current-team replacement fixtures and add source_team_hash "
                    "before treating direct action ids as current."
                ),
                "required_verification": verification_for("fixture_update"),
                **proposal_contract("fixture_update"),
            }
        )

    trajectory_report = None
    blocked_by_conflicts = False
    stale_trajectory_count = 0
    if include_trajectories:
        trajectory_report = build_trajectory_report(fixtures, trajectories, demonstrations)
        blocked_by_conflicts = bool(trajectory_report.get("conflicts"))
        stale_trajectory_count = len(trajectory_report.get("stale_rows", []))
        add_trajectory_proposals(proposals, trajectory_report)

    type_counts: dict[str, int] = {}
    for proposal in proposals:
        type_counts[proposal["proposal_type"]] = type_counts.get(proposal["proposal_type"], 0) + 1
        if blocked_by_conflicts and proposal["proposal_type"] in BEHAVIOR_PROPOSAL_TYPES:
            proposal["readiness"] = "blocked"
            proposal.setdefault("blocking_reasons", []).append(
                "resolve trajectory conflicts before behavior review"
            )

    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "proposal_count": len(proposals),
        "proposal_type_counts": dict(sorted(type_counts.items())),
        "reward_model_holdout_accuracy": reward_report["holdout_metrics"]["accuracy"],
        "reward_model_holdout_accuracy_label": reward_report["holdout_metrics"]["accuracy_label"],
        "trajectory_count": len(trajectories),
        "trajectory_demonstration_count": len(demonstrations),
        "blocked_by_conflicts": blocked_by_conflicts,
        "stale_trajectory_count": stale_trajectory_count,
        "trajectory_report": trajectory_report,
        "proposals": proposals,
    }


def render_proposal_report(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Preference Proposal Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Proposals: {report['proposal_count']}",
        f"- Reward model holdout accuracy: {report['reward_model_holdout_accuracy_label']}",
        f"- Trajectory preferences: {report['trajectory_count']}",
        f"- Plan demonstrations: {report['trajectory_demonstration_count']}",
        f"- Blocked by trajectory conflicts: {report['blocked_by_conflicts']}",
        f"- Stale trajectory rows: {report['stale_trajectory_count']}",
        "",
        "## Proposal Type Counts",
        "",
    ]
    for proposal_type, count in report["proposal_type_counts"].items():
        lines.append(f"- `{proposal_type}`: {count}")
    lines.append("")

    for proposal in report["proposals"]:
        lines.extend(
            [
                f"## Candidate: {proposal['lesson_id']}",
                "",
                f"- Type: `{proposal['proposal_type']}`",
                f"- Readiness: `{proposal.get('readiness', 'manual_review')}`",
                f"- ROM behavior change: `{proposal.get('rom_behavior_change', False)}`",
                f"- Requires human approval: `{proposal.get('requires_human_approval', True)}`",
                f"- Summary: {proposal['title']}",
                "- Evidence:",
            ]
        )
        for item in proposal["evidence"]:
            lines.append(f"  - `{item}`")
        lines.append("- Improves:")
        if proposal["improves"]:
            for item in proposal["improves"]:
                lines.append(f"  - `{item}`")
        else:
            lines.append("  - none proven yet")
        lines.append("- Risks / worsens:")
        if proposal["risks_or_worsens"]:
            for item in proposal["risks_or_worsens"]:
                lines.append(f"  - `{item}`")
        else:
            lines.append("  - none in current reports")
        if proposal.get("blocking_reasons"):
            lines.append("- Blocking reasons:")
            for reason in proposal["blocking_reasons"]:
                lines.append(f"  - {reason}")
        lines.extend(
            [
                f"- Suggested implementation: {proposal['suggested_implementation']}",
                "- Required verification:",
            ]
        )
        for check in proposal["required_verification"]:
            lines.append(f"  - `{check}`")
        lines.append("")
    return "\n".join(lines)


def write_proposal_report(
    *,
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    trajectories_path: Path = DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    demonstrations_path: Path = DEFAULT_PLAN_DEMONSTRATIONS_PATH,
    lessons_path: Path = DEFAULT_LESSONS_PATH,
    out_path: Path = DEFAULT_PROPOSAL_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_PROPOSAL_JSON_PATH,
    include_trajectories: bool = True,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    labels = load_labels(labels_path, fixtures=fixtures)
    preferences = load_preferences(preferences_path, fixtures=fixtures)
    manual_lessons = load_lessons(lessons_path)
    trajectories = (
        load_trajectory_preferences(trajectories_path, fixtures=fixtures)
        if include_trajectories
        else []
    )
    demonstrations = (
        load_plan_demonstrations(demonstrations_path, fixtures=fixtures)
        if include_trajectories
        else []
    )
    report = build_proposal_report(
        fixtures,
        labels,
        preferences,
        manual_lessons,
        trajectories,
        demonstrations,
        include_trajectories=include_trajectories,
    )
    markdown = render_proposal_report(report)

    if str(out_path) == "-":
        print(markdown)
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8", newline="\n")

    if json_out_path is not None:
        json_out_path.parent.mkdir(parents=True, exist_ok=True)
        json_out_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return report
