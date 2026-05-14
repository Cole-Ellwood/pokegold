from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .benchmark_harvest import build_benchmark_harvest_report, build_benchmark_label_queue
from .boss_team import boss_team_source_for_fixture
from .data import (
    DEFAULT_FIXTURES_PATH,
    DEFAULT_LABELS_PATH,
    DEFAULT_PREFERENCES_PATH,
    ROOT,
    load_fixtures,
    load_labels,
    load_preferences,
)
from .lessons import DEFAULT_LESSONS_PATH, load_lessons
from .plan_queue import build_plan_queue
from .proposals import build_proposal_report
from .reward_model import build_reward_model_report
from .trajectory_data import (
    DEFAULT_PLAN_DEMONSTRATIONS_PATH,
    DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    build_trajectory_report,
    load_plan_demonstrations,
    load_trajectory_preferences,
)


DEFAULT_FINAL_REPORT_PATH = ROOT / "audit" / "boss_ai_preference" / "final_report.md"
DEFAULT_FINAL_JSON_PATH = ROOT / "audit" / "boss_ai_preference" / "final_report.json"


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def plan_pair_key(fixture_id: str, plan_a_id: str, plan_b_id: str) -> tuple[str, str, str]:
    plan_ids = sorted([plan_a_id, plan_b_id])
    return (fixture_id, plan_ids[0], plan_ids[1])


def required_plan_pairs(candidate: dict[str, Any]) -> set[tuple[str, str, str]]:
    plans = candidate.get("plans", [])[:4]
    pairs: set[tuple[str, str, str]] = set()
    for left, plan_a in enumerate(plans):
        for plan_b in plans[left + 1 :]:
            pairs.add(plan_pair_key(candidate["fixture_id"], plan_a["id"], plan_b["id"]))
    return pairs


def saved_plan_pairs(trajectories: list[dict[str, Any]]) -> set[tuple[str, str, str]]:
    return {
        plan_pair_key(row["fixture_id"], row["trajectory_a_id"], row["trajectory_b_id"])
        for row in trajectories
    }


def fixture_phase(fixture: dict[str, Any]) -> str:
    try:
        turn = int(fixture.get("turn", 1))
    except (TypeError, ValueError):
        turn = 1
    if turn <= 2:
        return "early"
    if turn <= 8:
        return "mid"
    return "late"


def build_party_anchor_report(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for fixture in fixtures:
        source = boss_team_source_for_fixture(fixture)
        rows.append(
            {
                "fixture_id": fixture["id"],
                "leader": fixture["leader"],
                **source,
            }
        )
    missing = [row for row in rows if not row["exact"]]
    return {
        "exact_count": len(rows) - len(missing),
        "missing_exact_count": len(missing),
        "missing_exact": missing,
    }


def build_plan_pair_coverage(
    plan_queue: dict[str, Any],
    trajectories: list[dict[str, Any]],
) -> dict[str, Any]:
    saved = saved_plan_pairs(trajectories)
    rows: list[dict[str, Any]] = []
    for candidate in plan_queue["candidates"]:
        required = required_plan_pairs(candidate)
        covered = required & saved
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "fixture_id": candidate["fixture_id"],
                "leader": candidate["leader"],
                "phase": candidate["phase"],
                "required_pairs": len(required),
                "covered_pairs": len(covered),
                "complete": bool(required) and len(covered) == len(required),
            }
        )
    incomplete = [row for row in rows if not row["complete"]]
    return {
        "candidate_count": len(rows),
        "complete_count": len(rows) - len(incomplete),
        "incomplete_count": len(incomplete),
        "incomplete": incomplete[:20],
    }


def build_final_report(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
    manual_lessons: list[dict[str, Any]],
    trajectories: list[dict[str, Any]],
    demonstrations: list[dict[str, Any]],
) -> dict[str, Any]:
    phase_counts = Counter(fixture_phase(fixture) for fixture in fixtures)
    trajectory_fixtures = {row["fixture_id"] for row in trajectories}
    trajectory_phase_counts = Counter(
        fixture_phase(fixture)
        for fixture in fixtures
        if fixture["id"] in trajectory_fixtures
    )
    leader_trajectory_counts: dict[str, int] = defaultdict(int)
    fixtures_by_id = {fixture["id"]: fixture for fixture in fixtures}
    for row in trajectories:
        fixture = fixtures_by_id.get(row["fixture_id"])
        if fixture:
            leader_trajectory_counts[fixture["leader"]] += 1

    trajectory_report = build_trajectory_report(fixtures, trajectories, demonstrations)
    reward_report = build_reward_model_report(
        fixtures,
        preferences,
        trajectories,
        include_trajectories=True,
    )
    proposal_report = build_proposal_report(
        fixtures,
        labels,
        preferences,
        manual_lessons,
        trajectories,
        demonstrations,
        include_trajectories=True,
    )
    plan_queue = build_plan_queue(
        fixtures,
        labels,
        preferences,
        trajectories,
        demonstrations,
        limit=200,
    )
    party_anchor_report = build_party_anchor_report(fixtures)
    plan_pair_coverage = build_plan_pair_coverage(plan_queue, trajectories)
    benchmark_harvest = build_benchmark_harvest_report(fixtures, preferences)
    benchmark_label_queue = build_benchmark_label_queue(fixtures, preferences, limit=20)
    trajectory_model = reward_report.get("trajectory_model") or {}

    gates = {
        "no_trajectory_conflicts": not trajectory_report["conflicts"],
        "no_stale_trajectory_rows": not trajectory_report.get("stale_rows"),
        "has_holdout_pairwise_examples": reward_report["holdout_count"] > 0,
        "has_holdout_trajectory_examples": bool(trajectory_model.get("holdout_count", 0)),
        "all_fixtures_have_exact_party_anchor": party_anchor_report["missing_exact_count"] == 0,
        "top_plan_pairs_are_fully_labeled": plan_pair_coverage["incomplete_count"] == 0,
        "proposals_are_not_conflict_blocked": not proposal_report["blocked_by_conflicts"],
    }
    return {
        "generated_at": now_iso(),
        "fixture_count": len(fixtures),
        "label_count": len(labels),
        "pairwise_preference_count": len(preferences),
        "trajectory_count": len(trajectories),
        "demonstration_count": len(demonstrations),
        "fixture_phase_counts": dict(sorted(phase_counts.items())),
        "trajectory_phase_counts": dict(sorted(trajectory_phase_counts.items())),
        "leader_trajectory_counts": dict(sorted(leader_trajectory_counts.items())),
        "party_anchor_report": party_anchor_report,
        "plan_pair_coverage": plan_pair_coverage,
        "benchmark_harvest": {
            "complete_candidate_count": benchmark_harvest["complete_candidate_count"],
            "partial_candidate_count": benchmark_harvest["partial_candidate_count"],
            "missing_counts": benchmark_harvest["missing_counts"],
        },
        "benchmark_label_queue": {
            "request_count": benchmark_label_queue["request_count"],
            "one_label_completion_count": benchmark_label_queue[
                "one_label_completion_count"
            ],
        },
        "trajectory_conflict_count": len(trajectory_report["conflicts"]),
        "stale_trajectory_count": len(trajectory_report.get("stale_rows", [])),
        "reward_model_holdout_accuracy": reward_report["holdout_metrics"]["accuracy_label"],
        "trajectory_model_holdout_accuracy": (
            trajectory_model["holdout_metrics"]["accuracy_label"]
            if trajectory_model
            else "n/a"
        ),
        "proposal_count": proposal_report["proposal_count"],
        "proposal_type_counts": proposal_report["proposal_type_counts"],
        "gates": gates,
        "ready_for_rom_scoring_review": all(gates.values()),
    }


def render_final_report(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Preference Final Readiness Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Fixtures: {report['fixture_count']}",
        f"- Pairwise preferences: {report['pairwise_preference_count']}",
        f"- Trajectory preferences: {report['trajectory_count']}",
        f"- Plan demonstrations: {report['demonstration_count']}",
        f"- Ready for ROM scoring review: `{report['ready_for_rom_scoring_review']}`",
        "",
        "## Readiness Gates",
        "",
    ]
    for gate, passed in report["gates"].items():
        lines.append(f"- `{gate}`: {passed}")

    lines.extend(
        [
            "",
            "## Coverage",
            "",
            f"- Fixture phases: `{report['fixture_phase_counts']}`",
            f"- Trajectory phases: `{report['trajectory_phase_counts']}`",
            f"- Exact party anchors: {report['party_anchor_report']['exact_count']} / {report['fixture_count']}",
            f"- Incomplete top plan-card questions: {report['plan_pair_coverage']['incomplete_count']}",
            f"- Complete benchmark candidates: {report['benchmark_harvest']['complete_candidate_count']}",
            f"- Partial benchmark candidates: {report['benchmark_harvest']['partial_candidate_count']}",
            f"- One-label benchmark completions: {report['benchmark_label_queue']['one_label_completion_count']} / {report['benchmark_label_queue']['request_count']}",
            f"- Trajectory conflicts: {report['trajectory_conflict_count']}",
            f"- Stale trajectory rows: {report['stale_trajectory_count']}",
            f"- Pairwise holdout accuracy: {report['reward_model_holdout_accuracy']}",
            f"- Trajectory holdout accuracy: {report['trajectory_model_holdout_accuracy']}",
            "",
            "## Leader Trajectory Coverage",
            "",
        ]
    )
    if report["leader_trajectory_counts"]:
        for leader, count in report["leader_trajectory_counts"].items():
            lines.append(f"- `{leader}`: {count}")
    else:
        lines.append("No trajectory labels yet.")

    lines.extend(["", "## Incomplete Plan Questions", ""])
    if report["plan_pair_coverage"]["incomplete"]:
        for row in report["plan_pair_coverage"]["incomplete"]:
            lines.append(
                f"- `{row['fixture_id']}`: {row['covered_pairs']} / "
                f"{row['required_pairs']} shown plan pairs covered"
            )
    else:
        lines.append("All returned plan-card questions have complete shown-pair coverage.")

    lines.extend(["", "## Proposal Types", ""])
    if report["proposal_type_counts"]:
        for proposal_type, count in report["proposal_type_counts"].items():
            lines.append(f"- `{proposal_type}`: {count}")
    else:
        lines.append("No proposals yet.")
    lines.append("")
    return "\n".join(lines)


def write_final_report(
    *,
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    trajectories_path: Path = DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    demonstrations_path: Path = DEFAULT_PLAN_DEMONSTRATIONS_PATH,
    lessons_path: Path = DEFAULT_LESSONS_PATH,
    out_path: Path = DEFAULT_FINAL_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_FINAL_JSON_PATH,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    labels = load_labels(labels_path, fixtures=fixtures)
    preferences = load_preferences(preferences_path, fixtures=fixtures)
    manual_lessons = load_lessons(lessons_path)
    trajectories = load_trajectory_preferences(trajectories_path, fixtures=fixtures)
    demonstrations = load_plan_demonstrations(demonstrations_path, fixtures=fixtures)
    report = build_final_report(
        fixtures,
        labels,
        preferences,
        manual_lessons,
        trajectories,
        demonstrations,
    )
    markdown = render_final_report(report)
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
