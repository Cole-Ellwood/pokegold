from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from .data import (
    DEFAULT_FIXTURES_PATH,
    DEFAULT_PREFERENCES_PATH,
    ROOT,
    action_map,
    load_fixtures,
    load_preferences,
)


DEFAULT_BENCHMARK_HARVEST_REPORT_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "fixture_benchmark_harvest.md"
)
DEFAULT_BENCHMARK_HARVEST_JSON_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "fixture_benchmark_harvest.json"
)
DEFAULT_BENCHMARK_LABEL_QUEUE_REPORT_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "benchmark_label_queue.md"
)
DEFAULT_BENCHMARK_LABEL_QUEUE_JSON_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "benchmark_label_queue.json"
)

STRICT_CHOICES = {"a_better", "b_better", "other_better"}
NEGATIVE_ACTION_TAGS = {"misses_public_threat", "too_greedy", "too_passive"}
ACCEPTABLE_ACTION_TAGS = {"calculated_risk", "keeps_tempo", "reduces_risk", "scary_pressure"}
MISSING_LABEL_PRIORITY = ("acceptable", "single_best", "best", "catastrophic")


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def action_label(action_id: str, actions_by_id: dict[str, dict[str, Any]]) -> str:
    action = actions_by_id.get(action_id)
    if not action:
        return action_id
    name = str(action.get("name") or action_id)
    return f"{name} (`{action_id}`)"


def add_score(
    stats: dict[str, dict[str, Any]],
    action_id: str,
    score: int,
    preference_id: str,
) -> None:
    row = stats[action_id]
    row["score"] += score
    row["preference_ids"].append(preference_id)
    if score > 0:
        row["wins"] += 1
    elif score < 0:
        row["losses"] += 1


def preference_id(row: dict[str, Any], index: int) -> str:
    return (
        f"{row['fixture_id']}:{index}:"
        f"{row['action_a_id']}:{row['action_b_id']}:{row['choice']}"
    )


def add_action_tags(
    stats: dict[str, dict[str, Any]],
    preference: dict[str, Any],
) -> None:
    for action_id, tags in preference.get("action_tags", {}).items():
        stats[action_id]["tags"].update(tags)


def harvest_fixture(
    fixture: dict[str, Any],
    preferences: list[dict[str, Any]],
) -> dict[str, Any]:
    actions_by_id = action_map(fixture)
    stats: dict[str, dict[str, Any]] = {
        action_id: {
            "score": 0,
            "wins": 0,
            "losses": 0,
            "tags": Counter(),
            "preference_ids": [],
        }
        for action_id in actions_by_id
    }
    contextual_actions: set[str] = set()
    compared_actions: set[str] = set()
    strict_count = 0

    for index, preference in enumerate(preferences, start=1):
        pref_id = preference_id(preference, index)
        choice = preference["choice"]
        add_action_tags(stats, preference)
        compared_actions.update([preference["action_a_id"], preference["action_b_id"]])

        if choice == "a_better":
            strict_count += 1
            add_score(stats, preference["action_a_id"], 2, pref_id)
            add_score(stats, preference["action_b_id"], -2, pref_id)
        elif choice == "b_better":
            strict_count += 1
            add_score(stats, preference["action_b_id"], 2, pref_id)
            add_score(stats, preference["action_a_id"], -2, pref_id)
        elif choice == "other_better":
            strict_count += 1
            preferred = preference.get("preferred_action_id")
            if preferred:
                add_score(stats, preferred, 2, pref_id)
            for action_id in (preference["action_a_id"], preference["action_b_id"]):
                tags = set(preference.get("action_tags", {}).get(action_id, []))
                add_score(stats, action_id, -2 if tags & NEGATIVE_ACTION_TAGS else -1, pref_id)
        elif choice in {"both_good", "needs_context"}:
            contextual_actions.update([preference["action_a_id"], preference["action_b_id"]])

    scored = {
        action_id: {
            "action_id": action_id,
            "name": actions_by_id[action_id].get("name", action_id),
            "kind": actions_by_id[action_id].get("kind", ""),
            "explanation": actions_by_id[action_id].get("explanation", ""),
            "public_tradeoff": actions_by_id[action_id].get("public_tradeoff", ""),
            "score": int(row["score"]),
            "wins": int(row["wins"]),
            "losses": int(row["losses"]),
            "tags": dict(sorted(row["tags"].items())),
            "preference_ids": sorted(set(row["preference_ids"])),
        }
        for action_id, row in stats.items()
    }

    max_score = max((row["score"] for row in scored.values()), default=0)
    best = [
        action_id
        for action_id, row in scored.items()
        if row["score"] == max_score and row["score"] > 0
    ]
    catastrophic = [
        action_id
        for action_id, row in scored.items()
        if row["score"] <= -2 or set(row["tags"]) & NEGATIVE_ACTION_TAGS
    ]
    acceptable = [
        action_id
        for action_id, row in scored.items()
        if action_id not in best
        and action_id not in catastrophic
        and (
            action_id in contextual_actions
            or bool(set(row["tags"]) & ACCEPTABLE_ACTION_TAGS)
            or (action_id in compared_actions and row["score"] >= -1)
        )
    ]

    missing: list[str] = []
    if not best:
        missing.append("best")
    if not acceptable:
        missing.append("acceptable")
    if not catastrophic:
        missing.append("catastrophic")
    if len(best) != 1:
        missing.append("single_best")

    lesson_types = sorted(
        {
            str(preference.get("lesson_type"))
            for preference in preferences
            if preference.get("lesson_type")
        }
    )
    condition_tags = sorted(
        {
            tag
            for preference in preferences
            for tag in preference.get("condition_tags", [])
        }
    )

    return {
        "fixture_id": fixture["id"],
        "leader": fixture["leader"],
        "turn": fixture.get("turn"),
        "tags": list(fixture.get("tags", [])),
        "training_focus": fixture.get("training_focus", ""),
        "preference_count": len(preferences),
        "strict_preference_count": strict_count,
        "lesson_types": lesson_types,
        "condition_tags": condition_tags,
        "complete": not missing,
        "missing": missing,
        "best_action_ids": best,
        "acceptable_action_ids": acceptable,
        "catastrophic_action_ids": catastrophic,
        "actions": [
            scored[action_id]
            for action_id in sorted(
                scored,
                key=lambda item: (-scored[item]["score"], item),
            )
        ],
    }


def build_benchmark_harvest_report(
    fixtures: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
) -> dict[str, Any]:
    preferences_by_fixture: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for preference in preferences:
        preferences_by_fixture[preference["fixture_id"]].append(preference)

    rows = [
        harvest_fixture(fixture, preferences_by_fixture[fixture["id"]])
        for fixture in fixtures
        if preferences_by_fixture.get(fixture["id"])
    ]
    complete = [row for row in rows if row["complete"]]
    missing_counts = Counter(reason for row in rows for reason in row["missing"])
    lesson_counts = Counter(
        lesson for row in rows for lesson in row.get("lesson_types", [])
    )

    return {
        "generated_at": now_iso(),
        "fixture_count": len(fixtures),
        "preference_count": len(preferences),
        "feedback_fixture_count": len(rows),
        "complete_candidate_count": len(complete),
        "partial_candidate_count": len(rows) - len(complete),
        "missing_counts": dict(sorted(missing_counts.items())),
        "lesson_type_counts": dict(sorted(lesson_counts.items())),
        "complete_candidates": complete,
        "partial_candidates": [row for row in rows if not row["complete"]],
    }


def format_action_ids(action_ids: list[str], row: dict[str, Any]) -> str:
    actions_by_id = {action["action_id"]: action for action in row["actions"]}
    if not action_ids:
        return "-"
    return ", ".join(
        f"{actions_by_id[action_id]['name']} (`{action_id}`)"
        for action_id in action_ids
    )


def action_names_by_id(row: dict[str, Any]) -> dict[str, str]:
    return {action["action_id"]: str(action["name"]) for action in row["actions"]}


def action_display(row: dict[str, Any], action_id: str | None) -> str:
    if not action_id:
        return "-"
    return f"{action_names_by_id(row).get(action_id, action_id)} (`{action_id}`)"


def unclassified_action_ids(row: dict[str, Any]) -> list[str]:
    classified = {
        *row["best_action_ids"],
        *row["acceptable_action_ids"],
        *row["catastrophic_action_ids"],
    }
    actions = [
        action for action in row["actions"] if action["action_id"] not in classified
    ]
    actions.sort(
        key=lambda action: (
            -acceptability_probe_score(action),
            -int(action["score"]),
            str(action["action_id"]),
        )
    )
    return [action["action_id"] for action in actions]


def acceptability_probe_score(action: dict[str, Any]) -> int:
    tags = set(action.get("tags", {}))
    text = " ".join(
        str(action.get(key, ""))
        for key in ("name", "kind", "explanation", "public_tradeoff")
    ).lower()
    score = 0
    if tags & ACCEPTABLE_ACTION_TAGS:
        score += 5
    if action.get("kind") == "switch":
        score += 3
    if text_contains_any(text, ("preserve", "resist", "coverage", "safe", "sensible")):
        score += 2
    if text_contains_any(text, ("greedy", "too greedy", "risky", "fails")):
        score -= 3
    return score


def text_contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def first_available(action_ids: list[str]) -> str | None:
    return action_ids[0] if action_ids else None


def build_label_request(row: dict[str, Any]) -> dict[str, Any]:
    missing = list(row["missing"])
    best = list(row["best_action_ids"])
    acceptable = list(row["acceptable_action_ids"])
    catastrophic = list(row["catastrophic_action_ids"])
    unclassified = unclassified_action_ids(row)
    primary_missing = next(
        label for label in MISSING_LABEL_PRIORITY if label in missing
    )

    review_type = primary_missing
    action_a_id: str | None = None
    action_b_id: str | None = None
    question = ""
    completion_effect = "clarifies benchmark labels"

    if primary_missing == "acceptable":
        action_a_id = first_available(best) or first_available(acceptable)
        action_b_id = first_available(unclassified)
        if action_b_id:
            question = (
                f"Can {action_display(row, action_b_id)} be an acceptable "
                f"alternative to {action_display(row, action_a_id)}, or should it "
                "stay outside the benchmark's acceptable set?"
            )
        else:
            question = (
                "No unclassified action remains. Decide whether an existing "
                "catastrophic label is overbroad, add a contextual exception, "
                "or create a separate benchmark variant with a real acceptable "
                "alternative."
            )
        if missing == ["acceptable"] and action_a_id and action_b_id:
            completion_effect = "one acceptable label would complete this candidate"
        else:
            completion_effect = (
                "requires a new contextual exception or benchmark variant"
            )
    elif primary_missing in {"single_best", "best"}:
        candidates = [*best, *acceptable, *unclassified]
        action_a_id = first_available(candidates)
        action_b_id = candidates[1] if len(candidates) > 1 else None
        question = (
            f"Which move should be the single best label: "
            f"{action_display(row, action_a_id)} or "
            f"{action_display(row, action_b_id)}?"
        )
        completion_effect = "chooses the benchmark's single best move"
    elif primary_missing == "catastrophic":
        action_a_id = first_available(best) or first_available(acceptable)
        action_b_id = first_available(unclassified)
        question = (
            f"Is {action_display(row, action_b_id)} catastrophic from this "
            f"state, or merely worse than {action_display(row, action_a_id)}?"
        )
        completion_effect = "identifies the benchmark's catastrophe branch"

    can_complete_with_one_label = (
        missing == ["acceptable"]
        and primary_missing == "acceptable"
        and bool(action_a_id and action_b_id)
    )
    priority_score = (
        (100 if can_complete_with_one_label else 0)
        + int(row["strict_preference_count"]) * 5
        - len(missing) * 10
    )

    return {
        "fixture_id": row["fixture_id"],
        "leader": row["leader"],
        "turn": row.get("turn"),
        "training_focus": row.get("training_focus", ""),
        "missing": missing,
        "review_type": review_type,
        "priority_score": priority_score,
        "can_complete_with_one_label": can_complete_with_one_label,
        "completion_effect": completion_effect,
        "question": question,
        "action_a_id": action_a_id,
        "action_b_id": action_b_id,
        "best_action_ids": best,
        "acceptable_action_ids": acceptable,
        "catastrophic_action_ids": catastrophic,
        "unclassified_action_ids": unclassified,
        "current_best": format_action_ids(best, row),
        "current_acceptable": format_action_ids(acceptable, row),
        "current_catastrophic": format_action_ids(catastrophic, row),
        "suggested_command_template": (
            "python -m tools.boss_ai_preference prefer "
            f"--fixture-id {row['fixture_id']} "
            f"--action-a-id {action_a_id or '<action-a>'} "
            f"--action-b-id {action_b_id or '<action-b>'} "
            "--choice <a_better|b_better|both_good|needs_context|other_better> "
            "--note \"<why this label is right>\""
        ),
    }


def build_benchmark_label_queue(
    fixtures: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
    limit: int = 20,
) -> dict[str, Any]:
    harvest = build_benchmark_harvest_report(fixtures, preferences)
    requests = [
        build_label_request(row)
        for row in harvest["partial_candidates"]
        if row.get("missing")
    ]
    requests.sort(
        key=lambda row: (
            -int(row["priority_score"]),
            len(row["missing"]),
            str(row["fixture_id"]),
        )
    )

    return {
        "generated_at": now_iso(),
        "fixture_count": harvest["fixture_count"],
        "feedback_fixture_count": harvest["feedback_fixture_count"],
        "complete_candidate_count": harvest["complete_candidate_count"],
        "partial_candidate_count": harvest["partial_candidate_count"],
        "missing_counts": harvest["missing_counts"],
        "one_label_completion_count": sum(
            1 for row in requests if row["can_complete_with_one_label"]
        ),
        "request_count": len(requests),
        "returned_count": min(limit, len(requests)),
        "requests": requests[:limit],
    }


def render_benchmark_label_queue(report: dict[str, Any]) -> str:
    lines = [
        "# Benchmark Label Queue",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Fixtures: {report['fixture_count']}",
        f"- Fixtures with feedback: {report['feedback_fixture_count']}",
        f"- Complete benchmark candidates: {report['complete_candidate_count']}",
        f"- Partial candidates: {report['partial_candidate_count']}",
        f"- One-label completions available: {report['one_label_completion_count']}",
        f"- Missing label pieces: `{report['missing_counts']}`",
        f"- Returned requests: {report['returned_count']} / {report['request_count']}",
        "",
        "## Requests",
        "",
    ]
    for index, row in enumerate(report["requests"], start=1):
        lines.extend(
            [
                f"### {index}. `{row['fixture_id']}`",
                "",
                f"- Leader / turn: {row['leader']} / {row['turn']}",
                f"- Missing: `{row['missing']}`",
                f"- Review type: `{row['review_type']}`",
                f"- Completion effect: {row['completion_effect']}",
                f"- Current best: {row['current_best']}",
                f"- Current acceptable: {row['current_acceptable']}",
                f"- Current catastrophic: {row['current_catastrophic']}",
                f"- Question: {row['question']}",
                f"- Command template: `{row['suggested_command_template']}`",
                "",
            ]
        )
    return "\n".join(lines)


def write_benchmark_label_queue(
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    out_path: Path = DEFAULT_BENCHMARK_LABEL_QUEUE_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_BENCHMARK_LABEL_QUEUE_JSON_PATH,
    limit: int = 20,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    report = build_benchmark_label_queue(
        fixtures,
        load_preferences(preferences_path, fixtures=fixtures),
        limit=limit,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_benchmark_label_queue(report),
        encoding="utf-8",
        newline="\n",
    )
    if json_out_path is not None:
        json_out_path.parent.mkdir(parents=True, exist_ok=True)
        json_out_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return report


def render_benchmark_harvest_report(report: dict[str, Any]) -> str:
    lines = [
        "# Fixture-Derived Benchmark Harvest",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Fixtures: {report['fixture_count']}",
        f"- Pairwise preferences: {report['preference_count']}",
        f"- Fixtures with feedback: {report['feedback_fixture_count']}",
        f"- Complete benchmark candidates: {report['complete_candidate_count']}",
        f"- Partial candidates: {report['partial_candidate_count']}",
        f"- Missing label pieces: `{report['missing_counts']}`",
        f"- Lesson types: `{report['lesson_type_counts']}`",
        "",
        "## Complete Candidates",
        "",
        "| Fixture | Best | Acceptable | Catastrophic | Lesson Types |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["complete_candidates"]:
        lines.append(
            "| "
            f"`{row['fixture_id']}` | "
            f"{format_action_ids(row['best_action_ids'], row)} | "
            f"{format_action_ids(row['acceptable_action_ids'], row)} | "
            f"{format_action_ids(row['catastrophic_action_ids'], row)} | "
            f"{', '.join(row['lesson_types']) or '-'} |"
        )

    lines.extend(
        [
            "",
            "## Partial Candidates",
            "",
            "| Fixture | Missing | Best | Acceptable | Catastrophic |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["partial_candidates"][:30]:
        lines.append(
            "| "
            f"`{row['fixture_id']}` | "
            f"{', '.join(row['missing'])} | "
            f"{format_action_ids(row['best_action_ids'], row)} | "
            f"{format_action_ids(row['acceptable_action_ids'], row)} | "
            f"{format_action_ids(row['catastrophic_action_ids'], row)} |"
        )
    return "\n".join(lines)


def write_benchmark_harvest_report(
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    out_path: Path = DEFAULT_BENCHMARK_HARVEST_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_BENCHMARK_HARVEST_JSON_PATH,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    preferences = load_preferences(preferences_path, fixtures=fixtures)
    report = build_benchmark_harvest_report(fixtures, preferences)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_benchmark_harvest_report(report),
        encoding="utf-8",
        newline="\n",
    )
    if json_out_path is not None:
        json_out_path.parent.mkdir(parents=True, exist_ok=True)
        json_out_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return report
