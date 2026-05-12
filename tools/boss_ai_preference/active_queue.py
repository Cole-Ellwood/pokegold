from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.boss_ai_debugger.scorer import inspect_fixture

from .data import (
    DEFAULT_FIXTURES_PATH,
    DEFAULT_LABELS_PATH,
    DEFAULT_PREFERENCES_PATH,
    load_fixtures,
    load_labels,
    load_preferences,
    preference_key,
)
from .features import enrich_fixtures, extract_fixture_features


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ACTIVE_QUEUE_PATH = ROOT / "audit" / "boss_ai_preference" / "active_queue.md"
DEFAULT_ACTIVE_QUEUE_JSON_PATH = ROOT / "audit" / "boss_ai_preference" / "active_queue.json"
DEFAULT_TRACE_DIR = ROOT / "audit" / "boss_ai_trace"

BOUNDARY_TAGS = {
    "ace_preservation": "ace_preservation",
    "hidden_coverage": "scout_policy",
    "setup": "sequence_policy",
    "setup_lock": "sequence_policy",
    "sleep": "hard_rule",
    "status": "weight_hint",
    "switching": "switch_policy",
    "tempo": "weight_hint",
}
STRICT_CHOICES = {"a_better", "b_better"}


def comparison_pair(fixture: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    actions = fixture.get("actions", [])
    baseline = next(
        (action for action in actions if action.get("id") == fixture.get("baseline_action_id")),
        actions[0] if actions else None,
    )
    challenger = next(
        (action for action in actions if baseline and action.get("id") != baseline.get("id")),
        None,
    )
    return baseline, challenger


def pairwise_choice_from_scores(
    action_a_id: str,
    action_b_id: str,
    scores: dict[str, int],
) -> str:
    score_a = scores.get(action_a_id, 0)
    score_b = scores.get(action_b_id, 0)
    if score_a == score_b:
        return "tie"
    if score_a > score_b:
        return "a_better"
    return "b_better"


def preference_by_pair(preferences: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {preference_key(preference): preference for preference in preferences}


def score_fixture_candidate(
    fixture: dict[str, Any],
    inspection: dict[str, Any],
    pair_preference: dict[str, Any] | None,
    leader_feedback_count: int,
    rare_feature_count: int,
) -> dict[str, Any]:
    priority = 0
    reasons: list[str] = []
    teaches: set[str] = set()
    top_actions = inspection["actions"][:2]

    if len(top_actions) >= 2:
        margin = int(top_actions[0]["score"]) - int(top_actions[1]["score"])
        if margin <= 3:
            priority += 3
            reasons.append(f"current scorer top two actions are close (margin {margin})")
        elif margin <= 8:
            priority += 2
            reasons.append(f"current scorer has modest uncertainty (margin {margin})")

    if pair_preference is not None:
        scores = {action["action_id"]: int(action["score"]) for action in inspection["actions"]}
        scorer_choice = pairwise_choice_from_scores(
            pair_preference["action_a_id"],
            pair_preference["action_b_id"],
            scores,
        )
        if pair_preference["choice"] in STRICT_CHOICES and scorer_choice != pair_preference["choice"]:
            priority += 4
            reasons.append(
                "current scorer disagrees with an existing strict user preference "
                f"({scorer_choice} vs {pair_preference['choice']})"
            )
        if pair_preference["choice"] == "other_better":
            priority += 2
            reasons.append("existing preference says the compared pair omitted the best action")
            teaches.add("switch_policy")
        if "source_team_hash" not in pair_preference:
            priority += 2
            reasons.append("existing row predates team-hash anchoring after the roster changes")
        if pair_preference.get("confidence") == "high" and pair_preference.get("lesson_type"):
            priority -= 3
            reasons.append("existing row is already high-confidence and typed")
    else:
        priority += 1
        reasons.append("no pairwise preference has been recorded for this comparison")

    for tag in fixture.get("tags", []):
        lesson = BOUNDARY_TAGS.get(str(tag))
        if lesson:
            priority += 3 if lesson in {"sequence_policy", "switch_policy", "scout_policy"} else 2
            teaches.add(lesson)

    if leader_feedback_count == 0:
        priority += 2
        reasons.append(f"{fixture['leader']} has no current preference feedback")
    elif leader_feedback_count < 2:
        priority += 1
        reasons.append(f"{fixture['leader']} is still under-covered")

    if rare_feature_count:
        priority += 1
        reasons.append(f"contains {rare_feature_count} rare feature(s) in the current corpus")

    if not reasons:
        reasons.append("coverage candidate from the current fixture pool")

    return {
        "candidate_id": fixture["id"],
        "source": "fixture",
        "fixture_id": fixture["id"],
        "leader": fixture["leader"],
        "priority": priority,
        "reasons": reasons,
        "teaches": sorted(teaches),
        "top_actions": top_actions,
        "existing_preference": pair_preference,
    }


def build_fixture_candidates(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    enriched = enrich_fixtures(fixtures)
    preferences_by_pair = preference_by_pair(preferences)
    leader_feedback: Counter[str] = Counter()
    for record in [*labels, *preferences]:
        leader = next(
            (fixture["leader"] for fixture in fixtures if fixture["id"] == record["fixture_id"]),
            "",
        )
        if leader:
            leader_feedback[leader] += 1

    feature_support: Counter[str] = Counter()
    features_by_fixture: dict[str, list[dict[str, Any]]] = {}
    for fixture in enriched:
        rows = extract_fixture_features(fixture)
        features_by_fixture[fixture["id"]] = rows
        for row in rows:
            for name, value in row["features"].items():
                if value:
                    feature_support[name] += 1

    candidates: list[dict[str, Any]] = []
    for fixture in enriched:
        action_a, action_b = comparison_pair(fixture)
        pair_preference = None
        if action_a and action_b:
            pair_preference = preferences_by_pair.get(
                (fixture["id"], *sorted([action_a["id"], action_b["id"]]))
            )
        rare_feature_count = sum(
            1
            for row in features_by_fixture[fixture["id"]]
            for name, value in row["features"].items()
            if value and feature_support[name] <= 2
        )
        candidates.append(
            score_fixture_candidate(
                fixture,
                inspect_fixture(fixture),
                pair_preference,
                leader_feedback[fixture["leader"]],
                rare_feature_count,
            )
        )
    return candidates


def parse_trace_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def build_trace_candidates(trace_dir: Path = DEFAULT_TRACE_DIR) -> list[dict[str, Any]]:
    if not trace_dir.exists():
        return []
    candidates: list[dict[str, Any]] = []
    for path in sorted(trace_dir.glob("*_live.txt")):
        values = parse_trace_file(path)
        notes = values.get("notes", "")
        top_moves = values.get("top_moves", "")
        priority = 2
        reasons = ["live trace capture should periodically feed the review queue"]
        teaches: set[str] = set()
        if "," in top_moves:
            priority += 2
            reasons.append(f"trace has multiple top moves: {top_moves}")
        lowered_notes = notes.lower()
        if "switch" in lowered_notes:
            priority += 2
            teaches.add("switch_policy")
        if "hidden" in lowered_notes or "probe" in lowered_notes:
            priority += 2
            teaches.add("scout_policy")
        if "ko" in lowered_notes or "avoidance" in lowered_notes:
            priority += 1
            teaches.add("weight_hint")
        candidates.append(
            {
                "candidate_id": f"trace:{path.stem}",
                "source": "trace_capture",
                "fixture_id": None,
                "leader": values.get("boss", path.stem),
                "priority": priority,
                "reasons": reasons,
                "teaches": sorted(teaches),
                "trace_path": str(path.relative_to(ROOT)),
                "chosen": values.get("chosen", ""),
                "top_moves": top_moves,
                "notes": notes,
            }
        )
    return candidates


def build_active_queue(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
    *,
    trace_dir: Path = DEFAULT_TRACE_DIR,
    limit: int = 20,
) -> dict[str, Any]:
    candidates = [
        *build_fixture_candidates(fixtures, labels, preferences),
        *build_trace_candidates(trace_dir),
    ]
    candidates.sort(key=lambda item: (-int(item["priority"]), item["candidate_id"]))
    for index, candidate in enumerate(candidates, start=1):
        candidate["rank"] = index
    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "candidate_count": len(candidates),
        "returned_count": min(limit, len(candidates)),
        "candidates": candidates[:limit],
    }


def render_active_queue(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Active Preference Queue",
        "",
        f"Generated: {report['generated_at']}",
        "",
        f"Showing {report['returned_count']} / {report['candidate_count']} candidate(s).",
        "",
    ]
    for candidate in report["candidates"]:
        teaches = ", ".join(f"`{tag}`" for tag in candidate.get("teaches", [])) or "none"
        lines.extend(
            [
                f"## {candidate['rank']}. {candidate['candidate_id']}",
                "",
                f"- Source: `{candidate['source']}`",
                f"- Leader: {candidate['leader']}",
                f"- Priority: {candidate['priority']}",
                f"- Teaches: {teaches}",
                "- Reasons:",
            ]
        )
        for reason in candidate["reasons"]:
            lines.append(f"  - {reason}")
        if candidate["source"] == "fixture":
            top = ", ".join(
                f"{action['name']}={action['score']}"
                for action in candidate.get("top_actions", [])
            )
            lines.append(f"- Current scorer top actions: {top}")
        else:
            lines.append(f"- Trace: `{candidate.get('trace_path')}`")
            lines.append(f"- Chosen: {candidate.get('chosen') or 'unknown'}")
            lines.append(f"- Top moves: {candidate.get('top_moves') or 'unknown'}")
        lines.append("")
    return "\n".join(lines)


def write_active_queue(
    *,
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    out_path: Path = DEFAULT_ACTIVE_QUEUE_PATH,
    json_out_path: Path | None = DEFAULT_ACTIVE_QUEUE_JSON_PATH,
    trace_dir: Path = DEFAULT_TRACE_DIR,
    limit: int = 20,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    labels = load_labels(labels_path, fixtures=fixtures)
    preferences = load_preferences(preferences_path, fixtures=fixtures)
    report = build_active_queue(
        fixtures,
        labels,
        preferences,
        trace_dir=trace_dir,
        limit=limit,
    )
    markdown = render_active_queue(report)

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
