from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .active_queue import DEFAULT_TRACE_DIR, build_active_queue
from .data import (
    DEFAULT_FIXTURES_PATH,
    DEFAULT_LABELS_PATH,
    DEFAULT_PREFERENCES_PATH,
    ROOT,
    load_fixtures,
    load_labels,
    load_preferences,
)
from .plans import generate_plan_cards, phase_for_fixture
from .rollouts import DEFAULT_ROLLOUT_MODE, normalize_rollout_mode
from .trajectory_data import (
    DEFAULT_PLAN_DEMONSTRATIONS_PATH,
    DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    build_trajectory_report,
    load_plan_demonstrations,
    load_trajectory_preferences,
    render_trajectory_report,
)


DEFAULT_PLAN_QUEUE_PATH = ROOT / "audit" / "boss_ai_preference" / "plan_queue.md"
DEFAULT_PLAN_QUEUE_JSON_PATH = ROOT / "audit" / "boss_ai_preference" / "plan_queue.json"
DEFAULT_COACH_REPORT_PATH = ROOT / "audit" / "boss_ai_preference" / "coach_report.md"
DEFAULT_COACH_JSON_PATH = ROOT / "audit" / "boss_ai_preference" / "coach_report.json"

PLAN_SHAPE_TEACHES = {
    "attack_now": "tempo",
    "setup_once_then_attack": "sequence_policy",
    "status_once_then_attack": "sequence_policy",
    "speed_control_then_attack": "sequence_policy",
    "scout_probe_then_commit": "scout_policy",
    "switch_preserve_then_rescore": "switch_policy",
    "sacrifice_trade_for_clean_switch": "mixed_strategy",
    "commit_lock_only_if_safe": "sequence_policy",
    "recover_until_safe": "late_resource_policy",
}
SEQUENCE_WORDS = {
    "then",
    "next turn",
    "after",
    "repeat",
    "until",
    "setup",
    "set up",
    "scout",
    "preserve",
    "switch",
}


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def fixture_by_id(fixtures: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {fixture["id"]: fixture for fixture in fixtures}


def trajectory_rows_by_fixture(trajectories: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trajectory in trajectories:
        rows[trajectory["fixture_id"]].append(trajectory)
    return rows


def preference_notes_for_fixture(
    fixture_id: str,
    preferences: list[dict[str, Any]],
) -> list[str]:
    return [
        str(preference.get("note", ""))
        for preference in preferences
        if preference.get("fixture_id") == fixture_id and preference.get("note")
    ]


def notes_mention_sequence(notes: list[str]) -> bool:
    lowered = " ".join(notes).lower()
    return any(word in lowered for word in SEQUENCE_WORDS)


def plan_shape_counts(trajectories: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in trajectories:
        for plan_id in (row["trajectory_a_id"], row["trajectory_b_id"]):
            parts = plan_id.split("_")
            for shape in PLAN_SHAPE_TEACHES:
                if shape in plan_id:
                    counter[shape] += 1
                    break
            else:
                if len(parts) > 3:
                    counter["_".join(parts[2:4])] += 1
    return counter


def high_confidence_trajectory_fixture_ids(trajectories: list[dict[str, Any]]) -> set[str]:
    return {
        trajectory["fixture_id"]
        for trajectory in trajectories
        if trajectory.get("confidence") == "high"
        and trajectory.get("lesson_type")
        and trajectory.get("choice") in {"a_better", "b_better", "both_good", "depends"}
    }


def priority_for_plan_question(
    fixture: dict[str, Any],
    active_candidate: dict[str, Any] | None,
    plans: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
    trajectories: list[dict[str, Any]],
    demonstrations: list[dict[str, Any]],
    shape_support: Counter[str],
) -> tuple[int, list[str], list[str]]:
    priority = int(active_candidate.get("priority", 0)) if active_candidate else 1
    reasons: list[str] = []
    teaches: set[str] = set()

    if active_candidate is not None:
        reasons.extend(active_candidate.get("reasons", [])[:2])
        teaches.update(active_candidate.get("teaches", []))

    shapes = [str(plan.get("shape")) for plan in plans]
    for shape in shapes:
        teaches.add(PLAN_SHAPE_TEACHES.get(shape, shape))
    if len(set(shapes)) >= 3:
        priority += 2
        reasons.append("generated plan cards cover several different plan shapes")
    if any(shape in {"setup_once_then_attack", "status_once_then_attack"} for shape in shapes):
        priority += 3
        reasons.append("top candidate set includes setup/status sequencing")
    if "switch_preserve_then_rescore" in shapes:
        priority += 3
        reasons.append("candidate set includes move-vs-switch preservation")
    if "scout_probe_then_commit" in shapes:
        priority += 3
        reasons.append("candidate set includes hidden-info scout/probe timing")
    if "sacrifice_trade_for_clean_switch" in shapes:
        priority += 2
        reasons.append("candidate set includes a late-game trade or sacrifice line")

    notes = preference_notes_for_fixture(fixture["id"], preferences)
    if notes_mention_sequence(notes):
        priority += 4
        reasons.append("old preference notes mention a multi-turn line")

    fixture_tags = {str(tag) for tag in fixture.get("tags", [])}
    if fixture_tags & {"hidden_coverage", "prediction"}:
        priority += 3
        reasons.append("fixture tags include a hidden coverage or speed boundary")
    if fixture_tags & {"setup", "setup_lock", "status", "sleep"}:
        priority += 3
        reasons.append("fixture tags point at a sequence-policy boundary")
    if fixture_tags & {"ace_preservation", "switching", "sacrifice"}:
        priority += 2
        reasons.append("fixture tags point at resource preservation")

    existing_rows = trajectory_rows_by_fixture(trajectories).get(fixture["id"], [])
    if any(row.get("confidence") == "high" for row in existing_rows):
        priority -= 3
        reasons.append("fixture already has high-confidence trajectory feedback")
    if any(row.get("fixture_id") == fixture["id"] for row in demonstrations):
        priority += 5
        reasons.append("human demonstrated a missing plan that still needs integration")
        teaches.add("demo_needs_integration")
    if any(shape_support.get(shape, 0) >= 3 for shape in shapes):
        priority -= 2
        reasons.append("similar plan shapes already have trajectory coverage")

    if not reasons:
        reasons.append("generated from the current active preference queue")
    return priority, reasons, sorted(teaches)


def candidate_from_active_queue(
    fixture: dict[str, Any],
    active_candidate: dict[str, Any] | None,
    plans: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
    trajectories: list[dict[str, Any]],
    demonstrations: list[dict[str, Any]],
    shape_support: Counter[str],
) -> dict[str, Any]:
    priority, reasons, teaches = priority_for_plan_question(
        fixture,
        active_candidate,
        plans,
        preferences,
        trajectories,
        demonstrations,
        shape_support,
    )
    return {
        "candidate_id": f"plan:{fixture['id']}",
        "source": "plan_queue",
        "fixture_id": fixture["id"],
        "leader": fixture["leader"],
        "phase": phase_for_fixture(fixture),
        "priority": priority,
        "reasons": reasons,
        "teaches": teaches,
        "plans": plans,
    }


def build_plan_queue(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
    trajectories: list[dict[str, Any]],
    demonstrations: list[dict[str, Any]],
    *,
    trace_dir: Path = DEFAULT_TRACE_DIR,
    limit: int = 20,
    rollout_mode: str = DEFAULT_ROLLOUT_MODE,
) -> dict[str, Any]:
    mode = normalize_rollout_mode(rollout_mode)
    fixtures_by_id = fixture_by_id(fixtures)
    active_queue = build_active_queue(
        fixtures,
        labels,
        preferences,
        trace_dir=trace_dir,
        limit=max(limit * 2, 20),
    )
    active_by_fixture = {
        candidate["fixture_id"]: candidate
        for candidate in active_queue["candidates"]
        if candidate.get("source") == "fixture" and candidate.get("fixture_id")
    }
    shape_support = plan_shape_counts(trajectories)
    candidates: list[dict[str, Any]] = []
    for fixture in fixtures:
        plans = generate_plan_cards(fixture, rollout_mode=mode)
        if len(plans) < 2:
            continue
        candidates.append(
            candidate_from_active_queue(
                fixture,
                active_by_fixture.get(fixture["id"]),
                plans,
                preferences,
                trajectories,
                demonstrations,
                shape_support,
            )
        )

    candidates.sort(key=lambda item: (-int(item["priority"]), item["fixture_id"]))
    for index, candidate in enumerate(candidates, start=1):
        candidate["rank"] = index

    return {
        "generated_at": now_iso(),
        "rollout_mode": mode,
        "candidate_count": len(candidates),
        "returned_count": min(limit, len(candidates)),
        "trajectory_count": len(trajectories),
        "demonstration_count": len(demonstrations),
        "candidates": candidates[:limit],
        "active_queue_source_count": active_queue["returned_count"],
    }


def render_plan_queue(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Multi-Turn Plan Queue",
        "",
        f"Generated: {report['generated_at']}",
        f"Rollout mode: `{report['rollout_mode']}`",
        "",
        "## Summary",
        "",
        f"- Showing: {report['returned_count']} / {report['candidate_count']}",
        f"- Existing trajectory preferences: {report['trajectory_count']}",
        f"- Existing plan demonstrations: {report['demonstration_count']}",
        "",
    ]
    for candidate in report["candidates"]:
        teaches = ", ".join(f"`{tag}`" for tag in candidate.get("teaches", [])) or "none"
        lines.extend(
            [
                f"## {candidate['rank']}. {candidate['fixture_id']}",
                "",
                f"- Leader: {candidate['leader']}",
                f"- Phase: `{candidate['phase']}`",
                f"- Priority: {candidate['priority']}",
                f"- Teaches: {teaches}",
                "- Reasons:",
            ]
        )
        for reason in candidate["reasons"]:
            lines.append(f"  - {reason}")
        lines.append("- Plan cards:")
        for plan in candidate["plans"]:
            stops = ", ".join(f"`{condition}`" for condition in plan["stop_conditions"])
            assumptions = "; ".join(str(item) for item in plan.get("assumptions", [])[:3])
            lines.append(
                f"  - `{plan['id']}`: {plan['label']} "
                f"({plan['shape']}; stops: {stops})"
            )
            if assumptions:
                lines.append(f"    - Rollout assumptions: {assumptions}")
        lines.append("")
    return "\n".join(lines)


def write_plan_queue(
    *,
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    trajectories_path: Path = DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    demonstrations_path: Path = DEFAULT_PLAN_DEMONSTRATIONS_PATH,
    out_path: Path = DEFAULT_PLAN_QUEUE_PATH,
    json_out_path: Path | None = DEFAULT_PLAN_QUEUE_JSON_PATH,
    trace_dir: Path = DEFAULT_TRACE_DIR,
    limit: int = 20,
    rollout_mode: str = DEFAULT_ROLLOUT_MODE,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    labels = load_labels(labels_path, fixtures=fixtures)
    preferences = load_preferences(preferences_path, fixtures=fixtures)
    trajectories = load_trajectory_preferences(trajectories_path, fixtures=fixtures)
    demonstrations = load_plan_demonstrations(demonstrations_path, fixtures=fixtures)
    report = build_plan_queue(
        fixtures,
        labels,
        preferences,
        trajectories,
        demonstrations,
        trace_dir=trace_dir,
        limit=limit,
        rollout_mode=rollout_mode,
    )
    markdown = render_plan_queue(report)

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


def build_coach_report(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
    trajectories: list[dict[str, Any]],
    demonstrations: list[dict[str, Any]],
    *,
    trace_dir: Path = DEFAULT_TRACE_DIR,
    limit: int = 20,
    rollout_mode: str = DEFAULT_ROLLOUT_MODE,
) -> dict[str, Any]:
    plan_queue = build_plan_queue(
        fixtures,
        labels,
        preferences,
        trajectories,
        demonstrations,
        trace_dir=trace_dir,
        limit=limit,
        rollout_mode=rollout_mode,
    )
    trajectory_report = build_trajectory_report(fixtures, trajectories, demonstrations)
    phase_needs = {
        phase
        for phase in ("early", "mid", "late")
        if trajectory_report["phase_counts"].get(phase, 0) == 0
    }
    top_shapes: Counter[str] = Counter()
    for candidate in plan_queue["candidates"]:
        for plan in candidate["plans"]:
            top_shapes[str(plan["shape"])] += 1
    return {
        "generated_at": now_iso(),
        "rollout_mode": plan_queue["rollout_mode"],
        "plan_queue": plan_queue,
        "trajectory_report": trajectory_report,
        "top_plan_shapes": dict(top_shapes.most_common(12)),
        "phase_needs": sorted(phase_needs),
        "next_review_count": min(10, plan_queue["returned_count"]),
    }


def render_coach_report(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Coach Report",
        "",
        f"Generated: {report['generated_at']}",
        f"Rollout mode: `{report['rollout_mode']}`",
        "",
        "## Summary",
        "",
        f"- Plan questions ready: {report['plan_queue']['returned_count']}",
        f"- Trajectory preferences: {report['trajectory_report']['trajectory_count']}",
        f"- Plan demonstrations: {report['trajectory_report']['demonstration_count']}",
        f"- Suggested next review count: {report['next_review_count']}",
        "",
        "## Phase Needs",
        "",
    ]
    if report["phase_needs"]:
        for phase in report["phase_needs"]:
            lines.append(f"- `{phase}` needs trajectory labels")
    else:
        lines.append("Early, mid, and late phases all have at least one trajectory label.")

    lines.extend(["", "## Common Generated Plan Shapes", ""])
    for shape, count in report["top_plan_shapes"].items():
        lines.append(f"- `{shape}`: {count}")

    lines.extend(["", "## Top Coach Questions", ""])
    for candidate in report["plan_queue"]["candidates"][:10]:
        top_plans = " vs ".join(plan["label"] for plan in candidate["plans"][:2])
        lines.append(
            f"- `{candidate['fixture_id']}` ({candidate['leader']}, {candidate['phase']}): "
            f"{top_plans}"
        )
    lines.extend(["", "## Trajectory Details", ""])
    lines.append(render_trajectory_report(report["trajectory_report"]))
    return "\n".join(lines)


def write_coach_report(
    *,
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    trajectories_path: Path = DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    demonstrations_path: Path = DEFAULT_PLAN_DEMONSTRATIONS_PATH,
    out_path: Path = DEFAULT_COACH_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_COACH_JSON_PATH,
    trace_dir: Path = DEFAULT_TRACE_DIR,
    limit: int = 20,
    rollout_mode: str = DEFAULT_ROLLOUT_MODE,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    labels = load_labels(labels_path, fixtures=fixtures)
    preferences = load_preferences(preferences_path, fixtures=fixtures)
    trajectories = load_trajectory_preferences(trajectories_path, fixtures=fixtures)
    demonstrations = load_plan_demonstrations(demonstrations_path, fixtures=fixtures)
    report = build_coach_report(
        fixtures,
        labels,
        preferences,
        trajectories,
        demonstrations,
        trace_dir=trace_dir,
        limit=limit,
        rollout_mode=rollout_mode,
    )
    markdown = render_coach_report(report)

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
