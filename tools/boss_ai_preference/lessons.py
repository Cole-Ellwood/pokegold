from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .data import (
    ALLOWED_LESSON_TYPES,
    DEFAULT_FIXTURES_PATH,
    DEFAULT_LABELS_PATH,
    DEFAULT_PREFERENCES_PATH,
    PACKAGE_DIR,
    PreferenceDataError,
    load_fixtures,
    load_labels,
    load_preferences,
)
from .trajectory_data import (
    DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    load_trajectory_preferences,
    trajectory_id,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LESSONS_PATH = PACKAGE_DIR / "labels" / "boss_ai_lessons.jsonl"
DEFAULT_LESSON_REPORT_PATH = ROOT / "audit" / "boss_ai_preference" / "lesson_report.md"
DEFAULT_LESSON_JSON_PATH = ROOT / "audit" / "boss_ai_preference" / "lesson_report.json"

ALLOWED_LESSON_STATUSES = ("candidate", "accepted", "rejected", "needs_more_labels")
ALLOWED_DIRECTIONS = ("encourage", "discourage", "mixed", "review")


def preference_id(preference: dict[str, Any]) -> str:
    return (
        f"{preference['fixture_id']}:"
        f"{preference['action_a_id']}:"
        f"{preference['action_b_id']}"
    )


def normalize_lesson_record(record: Any, source: str) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise PreferenceDataError(f"{source}: lesson record must be an object")
    lesson_id = record.get("lesson_id")
    if not isinstance(lesson_id, str) or not lesson_id:
        raise PreferenceDataError(f"{source}: missing lesson_id")
    status = record.get("status", "candidate")
    if status not in ALLOWED_LESSON_STATUSES:
        raise PreferenceDataError(
            f"{source}: status must be one of {', '.join(ALLOWED_LESSON_STATUSES)}"
        )
    lesson_type = record.get("lesson_type")
    if lesson_type not in ALLOWED_LESSON_TYPES:
        raise PreferenceDataError(
            f"{source}: lesson_type must be one of {', '.join(ALLOWED_LESSON_TYPES)}"
        )
    direction = record.get("expected_direction", "review")
    if direction not in ALLOWED_DIRECTIONS:
        raise PreferenceDataError(
            f"{source}: expected_direction must be one of {', '.join(ALLOWED_DIRECTIONS)}"
        )
    source_ids = record.get("source_preference_ids", [])
    if not isinstance(source_ids, list) or any(not isinstance(item, str) for item in source_ids):
        raise PreferenceDataError(f"{source}: source_preference_ids must be a list of text")
    applies_to = record.get("applies_to", {})
    if not isinstance(applies_to, dict):
        raise PreferenceDataError(f"{source}: applies_to must be an object")
    summary = record.get("human_summary", "")
    if not isinstance(summary, str) or not summary:
        raise PreferenceDataError(f"{source}: missing human_summary")
    rom_target = record.get("rom_target", "")
    if not isinstance(rom_target, str):
        raise PreferenceDataError(f"{source}: rom_target must be text")

    normalized = dict(record)
    normalized["lesson_id"] = lesson_id
    normalized["status"] = status
    normalized["lesson_type"] = lesson_type
    normalized["expected_direction"] = direction
    normalized["source_preference_ids"] = sorted(set(source_ids))
    normalized["applies_to"] = applies_to
    normalized["human_summary"] = summary
    normalized["rom_target"] = rom_target
    return normalized


def load_lessons(path: Path = DEFAULT_LESSONS_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lessons: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PreferenceDataError(f"{path}:{line_number}: invalid JSONL row: {exc}") from exc
        lessons.append(normalize_lesson_record(record, f"{path}:{line_number}"))
    return lessons


def note_matches(preference: dict[str, Any], *patterns: str) -> bool:
    note = str(preference.get("note", "")).lower()
    return any(re.search(pattern, note) for pattern in patterns)


def lesson_template(
    lesson_id: str,
    *,
    lesson_type: str,
    expected_direction: str,
    human_summary: str,
    applies_to: dict[str, Any],
    rom_target: str,
) -> dict[str, Any]:
    return {
        "lesson_id": lesson_id,
        "status": "candidate",
        "lesson_type": lesson_type,
        "expected_direction": expected_direction,
        "source_preference_ids": [],
        "applies_to": applies_to,
        "rom_target": rom_target,
        "human_summary": human_summary,
    }


LESSON_TEMPLATES = {
    "single_debuff_then_attack": lesson_template(
        "single_debuff_then_attack",
        lesson_type="sequence_policy",
        expected_direction="mixed",
        applies_to={
            "move_properties": ["accuracy_debuff"],
            "excluded_when": ["debuff_already_landed", "target_can_switch_reset"],
        },
        rom_target="engine/battle/ai/scoring.asm",
        human_summary=(
            "One accuracy debuff can be correct when direct chip is worthless, "
            "but repeated debuffs lose value because switching clears them."
        ),
    ),
    "setup_requires_damage_race": lesson_template(
        "setup_requires_damage_race",
        lesson_type="weight_hint",
        expected_direction="encourage",
        applies_to={
            "move_properties": ["setup"],
            "required_when": ["boss_faster_or_survives", "setup_changes_ko_math"],
            "excluded_when": ["setup_loses_same_damage_race"],
        },
        rom_target="tools/boss_ai_preference/reward_model.py",
        human_summary=(
            "Setup is good when it keeps or improves the damage race, not merely "
            "because setup is boss-flavored."
        ),
    ),
    "resisted_ramp_lock_opener": lesson_template(
        "resisted_ramp_lock_opener",
        lesson_type="hard_rule",
        expected_direction="discourage",
        applies_to={
            "move_properties": ["ramp_lock"],
            "target_properties": ["resists_move", "physically_bulky"],
            "excluded_when": ["ko_confirmed", "target_paralyzed", "already_locked"],
        },
        rom_target="engine/battle/ai/scoring.asm",
        human_summary=(
            "Do not start a resisted ramp-lock sequence when it does not KO and "
            "the target can punish or switch."
        ),
    ),
    "sleep_pressure_clause_gated": lesson_template(
        "sleep_pressure_clause_gated",
        lesson_type="hard_rule",
        expected_direction="encourage",
        applies_to={
            "move_properties": ["sleep"],
            "required_when": ["sleep_clause_free", "target_not_statused"],
            "excluded_when": ["sleep_clause_occupied", "safeguard", "substitute"],
        },
        rom_target="engine/battle/ai/scoring.asm",
        human_summary=(
            "Sleep is strong legal pressure, but fail states and Sleep Clause "
            "must gate it before taste scoring runs."
        ),
    ),
    "immediate_ko_over_slow_plan": lesson_template(
        "immediate_ko_over_slow_plan",
        lesson_type="weight_hint",
        expected_direction="encourage",
        applies_to={
            "move_properties": ["damaging"],
            "required_when": ["ko_confirmed_or_near_confirmed"],
            "discourage_instead": ["slow_chip", "recovery", "status_setup"],
        },
        rom_target="tools/boss_ai_preference/reward_model.py",
        human_summary=(
            "A guaranteed or near-guaranteed KO should dominate slow chip, "
            "status, or recovery when the target can punish passivity."
        ),
    ),
    "other_better_means_action_pool_gap": lesson_template(
        "other_better_means_action_pool_gap",
        lesson_type="schema_only",
        expected_direction="review",
        applies_to={
            "choice": ["other_better"],
            "required_ui": ["full_action_list", "switch_actions", "plan_actions"],
        },
        rom_target="tools/boss_ai_preference/app.py",
        human_summary=(
            "Several labels say the best answer is outside the displayed pair, "
            "so V2 queries must include switch and plan actions."
        ),
    ),
    "hidden_coverage_probe_before_ace_setup": lesson_template(
        "hidden_coverage_probe_before_ace_setup",
        lesson_type="scout_policy",
        expected_direction="mixed",
        applies_to={
            "threat_properties": ["hidden_coverage_plausible", "4x_or_major_hit"],
            "encourage": ["information_probe", "safe_scout", "ace_preservation"],
            "discourage": ["greedy_setup_before_probe"],
        },
        rom_target="engine/battle/ai/scoring.asm",
        human_summary=(
            "Hidden coverage suspicion can make scouting or probing better than "
            "greedy setup, especially before committing an ace."
        ),
    ),
    "sacrifice_switch_mixed_strategy": lesson_template(
        "sacrifice_switch_mixed_strategy",
        lesson_type="personality_style",
        expected_direction="mixed",
        applies_to={
            "move_properties": ["explosion", "destiny_bond"],
            "near_ties": ["sacrifice", "safe_switch", "clean_switch_after_faint"],
        },
        rom_target="engine/battle/ai/POLICY_DESIGN.md",
        human_summary=(
            "Sacrifice, switch, and attack can be near-tie spots where the AI "
            "should preserve variety instead of becoming deterministic."
        ),
    ),
    "trajectory_sequence_policy_boundary": lesson_template(
        "trajectory_sequence_policy_boundary",
        lesson_type="sequence_policy",
        expected_direction="mixed",
        applies_to={
            "plan_properties": ["setup", "status", "lock", "repeat_until"],
            "required_when": ["explicit_human_trajectory_preference"],
            "excluded_when": ["stop_condition_reached"],
        },
        rom_target="tools/boss_ai_preference/plans.py",
        human_summary=(
            "Multi-turn labels should teach bounded setup/status/lock lines with explicit "
            "branch and stop conditions instead of raw move weights."
        ),
    ),
    "trajectory_switch_preserve_boundary": lesson_template(
        "trajectory_switch_preserve_boundary",
        lesson_type="switch_policy",
        expected_direction="mixed",
        applies_to={
            "plan_properties": ["switch_preserve", "clean_switch"],
            "required_when": ["preserve_value_exceeds_tempo_loss"],
            "excluded_when": ["switch_in_bad_fit"],
        },
        rom_target="tools/boss_ai_preference/proposals.py",
        human_summary=(
            "Trajectory labels should distinguish useful preservation switches from "
            "passive switching that gives up the fight."
        ),
    ),
    "trajectory_scout_probe_boundary": lesson_template(
        "trajectory_scout_probe_boundary",
        lesson_type="scout_policy",
        expected_direction="mixed",
        applies_to={
            "plan_properties": ["probe", "public_belief", "hidden_coverage_plausible"],
            "required_when": ["ace_commitment_is_risky"],
            "excluded_when": ["threat_is_revealed_and_damage_wins_now"],
        },
        rom_target="tools/boss_ai_preference/rollouts.py",
        human_summary=(
            "Trajectory labels should teach when one scout/probe turn is worth more "
            "than immediate ace commitment."
        ),
    ),
}


def candidate_lesson_ids(preference: dict[str, Any]) -> set[str]:
    lesson_ids: set[str] = set()
    choice = preference["choice"]
    note = str(preference.get("note", "")).lower()
    action_text = f"{preference['action_a_id']} {preference['action_b_id']}".lower()
    tags = {
        tag
        for tags in preference.get("action_tags", {}).values()
        for tag in tags
    }

    if note_matches(preference, r"sand attack", r"debuff", r"switch.*clear"):
        lesson_ids.add("single_debuff_then_attack")
    if (
        any(
            move in action_text
            for move in ("swords_dance", "agility", "dragon_dance", "double_team")
        )
        or note_matches(preference, r"swords dance", r"\bagility\b", r"setup opportunity")
    ):
        lesson_ids.add("setup_requires_damage_race")
    if (
        "rollout" in action_text
        or "roll out" in note
        or "rollout" in note
        or "ramp" in note
    ):
        lesson_ids.add("resisted_ramp_lock_opener")
    if note_matches(preference, r"sleep", r"hypnosis"):
        lesson_ids.add("sleep_pressure_clause_gated")
    if note_matches(preference, r"ko", r"kill", r"300%", r"outdamaged", r"straight up kills"):
        lesson_ids.add("immediate_ko_over_slow_plan")
    if choice == "other_better":
        lesson_ids.add("other_better_means_action_pool_gap")
    if "hidden" in preference["fixture_id"] or note_matches(
        preference,
        r"\bhidden\b",
        r"\bprobe\b",
        r"\bscout\b",
    ):
        lesson_ids.add("hidden_coverage_probe_before_ace_setup")
    if note_matches(preference, r"explosion", r"destiny bond", r"sacrifice", r"switch it up", r"close in scoring"):
        lesson_ids.add("sacrifice_switch_mixed_strategy")
    if {"too_passive", "misses_public_threat"} & tags and note_matches(preference, r"recover", r"toxic"):
        lesson_ids.add("immediate_ko_over_slow_plan")

    return lesson_ids


def trajectory_lesson_ids(trajectory: dict[str, Any]) -> set[str]:
    lesson_ids: set[str] = set()
    lesson_type = trajectory.get("lesson_type")
    plan_text = (
        f"{trajectory['trajectory_a_id']} {trajectory['trajectory_b_id']} "
        f"{trajectory.get('note', '')} "
        f"{' '.join(trajectory.get('condition_tags', []))} "
        f"{' '.join(trajectory.get('branch_tags', []))}"
    ).lower()
    if lesson_type == "switch_policy" or "switch" in plan_text or "preserve" in plan_text:
        lesson_ids.add("trajectory_switch_preserve_boundary")
    if lesson_type == "scout_policy" or "scout" in plan_text or "probe" in plan_text:
        lesson_ids.add("trajectory_scout_probe_boundary")
    if (
        lesson_type == "sequence_policy"
        or "setup" in plan_text
        or "then" in plan_text
        or "repeat" in plan_text
        or "status" in plan_text
    ):
        lesson_ids.add("trajectory_sequence_policy_boundary")
    return lesson_ids


def derive_candidate_lessons(
    preferences: list[dict[str, Any]],
    trajectories: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    lessons = {lesson_id: copy_lesson(template) for lesson_id, template in LESSON_TEMPLATES.items()}
    used: set[str] = set()
    for preference in preferences:
        for lesson_id in candidate_lesson_ids(preference):
            lessons[lesson_id]["source_preference_ids"].append(preference_id(preference))
            used.add(lesson_id)
    for trajectory in trajectories or []:
        for lesson_id in trajectory_lesson_ids(trajectory):
            lessons[lesson_id]["source_preference_ids"].append(
                f"trajectory:{trajectory_id(trajectory)}"
            )
            used.add(lesson_id)

    output: list[dict[str, Any]] = []
    for lesson_id in sorted(used):
        lesson = lessons[lesson_id]
        lesson["source_preference_ids"] = sorted(set(lesson["source_preference_ids"]))
        output.append(normalize_lesson_record(lesson, f"derived:{lesson_id}"))
    return output


def copy_lesson(lesson: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(lesson))


def merge_lessons(
    derived_lessons: list[dict[str, Any]],
    manual_lessons: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged = {lesson["lesson_id"]: lesson for lesson in derived_lessons}
    for lesson in manual_lessons:
        existing = merged.get(lesson["lesson_id"])
        if existing is None:
            merged[lesson["lesson_id"]] = lesson
            continue
        combined = dict(existing)
        combined.update(lesson)
        combined["source_preference_ids"] = sorted(
            set(existing["source_preference_ids"]) | set(lesson["source_preference_ids"])
        )
        merged[lesson["lesson_id"]] = normalize_lesson_record(
            combined,
            f"manual:{lesson['lesson_id']}",
        )
    return [merged[lesson_id] for lesson_id in sorted(merged)]


def stale_direct_actions(preferences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stale: list[dict[str, Any]] = []
    for preference in preferences:
        reasons: list[str] = []
        if "source_team_hash" not in preference:
            reasons.append("missing source_team_hash")
        if preference.get("lesson_type") == "stale_direct_action":
            reasons.append(preference.get("stale_reason", "marked stale_direct_action"))
        if reasons:
            stale.append(
                {
                    "preference_id": preference_id(preference),
                    "fixture_id": preference["fixture_id"],
                    "choice": preference["choice"],
                    "reasons": reasons,
                    "portable_note": str(preference.get("note", ""))[:240],
                }
            )
    return stale


def build_lesson_report(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
    manual_lessons: list[dict[str, Any]],
    trajectories: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    trajectories = trajectories or []
    derived = derive_candidate_lessons(preferences, trajectories)
    lessons = merge_lessons(derived, manual_lessons)
    fixture_leaders = {fixture["id"]: fixture["leader"] for fixture in fixtures}
    leader_coverage: dict[str, Counter[str]] = defaultdict(Counter)
    type_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    for lesson in lessons:
        type_counts[lesson["lesson_type"]] += 1
        status_counts[lesson["status"]] += 1
        for source_id in lesson["source_preference_ids"]:
            fixture_id = source_id.split(":", 1)[0]
            leader_coverage[fixture_leaders.get(fixture_id, "unknown")] += Counter(
                {lesson["lesson_id"]: 1}
            )

    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "fixture_count": len(fixtures),
        "label_count": len(labels),
        "preference_count": len(preferences),
        "trajectory_count": len(trajectories),
        "manual_lesson_count": len(manual_lessons),
        "derived_lesson_count": len(derived),
        "lesson_count": len(lessons),
        "lesson_type_counts": dict(sorted(type_counts.items())),
        "lesson_status_counts": dict(sorted(status_counts.items())),
        "leader_coverage": {
            leader: dict(counter)
            for leader, counter in sorted(leader_coverage.items())
        },
        "stale_direct_actions": stale_direct_actions(preferences),
        "lessons": lessons,
    }


def render_lesson_report(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Structured Lesson Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Pairwise preferences: {report['preference_count']}",
        f"- Trajectory preferences: {report['trajectory_count']}",
        f"- Derived lessons: {report['derived_lesson_count']}",
        f"- Manual lesson overrides: {report['manual_lesson_count']}",
        f"- Stale direct-action rows: {len(report['stale_direct_actions'])}",
        "",
        "## Lesson Type Counts",
        "",
    ]
    for lesson_type, count in report["lesson_type_counts"].items():
        lines.append(f"- `{lesson_type}`: {count}")
    lines.extend(["", "## Lessons", ""])
    for lesson in report["lessons"]:
        sources = ", ".join(f"`{source}`" for source in lesson["source_preference_ids"])
        lines.extend(
            [
                f"### {lesson['lesson_id']}",
                "",
                f"- Status: `{lesson['status']}`",
                f"- Type: `{lesson['lesson_type']}`",
                f"- Direction: `{lesson['expected_direction']}`",
                f"- ROM target: `{lesson['rom_target'] or 'none'}`",
                f"- Summary: {lesson['human_summary']}",
                f"- Sources: {sources or 'none'}",
                "",
            ]
        )
    lines.extend(["## Stale Direct Actions", ""])
    if report["stale_direct_actions"]:
        for row in report["stale_direct_actions"]:
            reasons = ", ".join(row["reasons"])
            lines.append(f"- `{row['preference_id']}`: {reasons}")
    else:
        lines.append("No stale direct-action rows.")
    lines.append("")
    return "\n".join(lines)


def write_lesson_report(
    *,
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    trajectories_path: Path | None = DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    lessons_path: Path = DEFAULT_LESSONS_PATH,
    out_path: Path = DEFAULT_LESSON_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_LESSON_JSON_PATH,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    labels = load_labels(labels_path, fixtures=fixtures)
    preferences = load_preferences(preferences_path, fixtures=fixtures)
    trajectories = (
        load_trajectory_preferences(trajectories_path, fixtures=fixtures)
        if trajectories_path is not None
        else []
    )
    manual_lessons = load_lessons(lessons_path)
    report = build_lesson_report(fixtures, labels, preferences, manual_lessons, trajectories)
    markdown = render_lesson_report(report)

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
