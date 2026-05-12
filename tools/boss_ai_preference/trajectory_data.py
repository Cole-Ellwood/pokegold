from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .data import (
    ALLOWED_CONFIDENCE,
    ALLOWED_LESSON_TYPES,
    ALLOWED_PUBLIC_INFO_SCOPES,
    PACKAGE_DIR,
    ROOT,
    TOOL_VERSION,
    PreferenceDataError,
    apply_optional_enum,
    apply_optional_text,
    build_v2_metadata,
    fixture_map,
    load_fixtures,
    normalize_text_tags,
)
from .boss_team import boss_team_for_fixture, boss_team_source_for_fixture


DEFAULT_TRAJECTORY_PREFERENCES_PATH = (
    PACKAGE_DIR / "labels" / "boss_ai_trajectory_preferences.jsonl"
)
DEFAULT_PLAN_DEMONSTRATIONS_PATH = (
    PACKAGE_DIR / "labels" / "boss_ai_plan_demonstrations.jsonl"
)
DEFAULT_TRAJECTORY_REPORT_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "trajectory_report.md"
)
DEFAULT_TRAJECTORY_JSON_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "trajectory_report.json"
)

ALLOWED_TRAJECTORY_CHOICES = (
    "a_better",
    "b_better",
    "both_good",
    "both_bad",
    "depends",
    "neither_best_plan_missing",
    "upstream_state_issue",
    "needs_context",
)
STRICT_TRAJECTORY_CHOICES = {"a_better", "b_better"}


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def stable_short_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def fixture_state_hash(fixture: dict[str, Any]) -> str:
    return stable_short_hash(
        {
            "id": fixture.get("id"),
            "leader": fixture.get("leader"),
            "turn": fixture.get("turn"),
            "state": fixture.get("state", {}),
            "actions": fixture.get("actions", []),
            "baseline_action_id": fixture.get("baseline_action_id"),
        }
    )


def source_team_hash_for_fixture(fixture: dict[str, Any]) -> str | None:
    source = boss_team_source_for_fixture(fixture)
    value = source.get("hash")
    return str(value) if value else None


def source_hash_metadata(fixture: dict[str, Any] | None) -> dict[str, str]:
    if fixture is None:
        return {}
    metadata = {"fixture_state_hash": fixture_state_hash(fixture)}
    source_team_hash = source_team_hash_for_fixture(fixture)
    if source_team_hash:
        metadata["source_team_hash"] = source_team_hash
    return metadata


def source_move_action_id(move_name: object) -> str:
    if not isinstance(move_name, str) or not move_name.strip():
        return ""
    slug = re.sub(r"[^a-z0-9]+", "_", move_name.strip().lower()).strip("_")
    if slug == "psychic_m":
        slug = "psychic"
    return f"move_{slug}" if slug else ""


def active_source_move_action_ids(fixture: dict[str, Any]) -> set[str]:
    for member in boss_team_for_fixture(fixture):
        if not member.get("active"):
            continue
        return {
            action_id
            for action_id in (
                source_move_action_id(move)
                for move in member.get("moves", [])
            )
            if action_id
        }
    return set()


def demonstration_action_ids_for_fixture(fixture: dict[str, Any]) -> set[str]:
    action_ids = {
        str(action.get("id"))
        for action in fixture.get("actions", [])
        if isinstance(action, dict) and action.get("id")
    }
    action_ids.update(active_source_move_action_ids(fixture))
    return action_ids


def normalize_horizon(value: Any, source: str) -> int:
    if isinstance(value, bool):
        raise PreferenceDataError(f"{source}: horizon must be an integer")
    try:
        horizon = int(value)
    except (TypeError, ValueError) as exc:
        raise PreferenceDataError(f"{source}: horizon must be an integer") from exc
    if horizon < 1 or horizon > 5:
        raise PreferenceDataError(f"{source}: horizon must be between 1 and 5")
    return horizon


def normalize_optional_text(value: Any, source: str, field_name: str) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise PreferenceDataError(f"{source}: {field_name} must be text")
    if any(ord(character) < 32 for character in value):
        raise PreferenceDataError(f"{source}: {field_name} cannot contain control characters")
    return value


def validate_plan_id(
    fixture_id: str,
    plan_id: str,
    known_plan_ids_by_fixture: dict[str, set[str]] | None,
    source: str,
    field_name: str,
) -> None:
    if known_plan_ids_by_fixture is None:
        return
    known_plan_ids = known_plan_ids_by_fixture.get(fixture_id)
    if known_plan_ids is None:
        return
    if plan_id not in known_plan_ids:
        raise PreferenceDataError(
            f"{source}: {field_name} {plan_id!r} is not generated for fixture {fixture_id!r}"
        )


def normalize_trajectory_record(
    record: Any,
    known_fixtures: dict[str, dict[str, Any]] | None,
    source: str,
    *,
    known_plan_ids_by_fixture: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise PreferenceDataError(f"{source}: trajectory preference must be an object")
    schema_version = record.get("schema_version", 1)
    if schema_version != 1:
        raise PreferenceDataError(f"{source}: schema_version must be 1")

    fixture_id = record.get("fixture_id")
    if not isinstance(fixture_id, str) or not fixture_id:
        raise PreferenceDataError(f"{source}: missing fixture_id")
    if known_fixtures is not None and fixture_id not in known_fixtures:
        raise PreferenceDataError(f"{source}: unknown fixture_id {fixture_id!r}")

    trajectory_a_id = record.get("trajectory_a_id")
    trajectory_b_id = record.get("trajectory_b_id")
    if not isinstance(trajectory_a_id, str) or not trajectory_a_id:
        raise PreferenceDataError(f"{source}: missing trajectory_a_id")
    if not isinstance(trajectory_b_id, str) or not trajectory_b_id:
        raise PreferenceDataError(f"{source}: missing trajectory_b_id")
    if trajectory_a_id == trajectory_b_id:
        raise PreferenceDataError(f"{source}: trajectory_a_id and trajectory_b_id must differ")
    validate_plan_id(
        fixture_id,
        trajectory_a_id,
        known_plan_ids_by_fixture,
        source,
        "trajectory_a_id",
    )
    validate_plan_id(
        fixture_id,
        trajectory_b_id,
        known_plan_ids_by_fixture,
        source,
        "trajectory_b_id",
    )

    choice = record.get("choice")
    if choice not in ALLOWED_TRAJECTORY_CHOICES:
        raise PreferenceDataError(
            f"{source}: choice must be one of {', '.join(ALLOWED_TRAJECTORY_CHOICES)}"
        )

    preferred_trajectory_id = record.get("preferred_trajectory_id")
    if preferred_trajectory_id is None or preferred_trajectory_id == "":
        preferred_trajectory_id = None
    elif not isinstance(preferred_trajectory_id, str):
        raise PreferenceDataError(f"{source}: preferred_trajectory_id must be text")

    if choice == "a_better":
        preferred_trajectory_id = trajectory_a_id
    elif choice == "b_better":
        preferred_trajectory_id = trajectory_b_id
    elif preferred_trajectory_id is not None:
        valid_ids = {trajectory_a_id, trajectory_b_id}
        if known_plan_ids_by_fixture is not None:
            valid_ids |= known_plan_ids_by_fixture.get(fixture_id, set())
        if preferred_trajectory_id not in valid_ids:
            raise PreferenceDataError(
                f"{source}: preferred_trajectory_id {preferred_trajectory_id!r} "
                f"is not a compared or generated plan"
            )

    horizon = normalize_horizon(record.get("horizon", 3), source)
    note = record.get("note", "")
    if note is None:
        note = ""
    if not isinstance(note, str):
        raise PreferenceDataError(f"{source}: note must be text")
    created_at = record.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        raise PreferenceDataError(f"{source}: missing created_at")

    normalized = dict(record)
    normalized["schema_version"] = 1
    normalized["fixture_id"] = fixture_id
    normalized["trajectory_a_id"] = trajectory_a_id
    normalized["trajectory_b_id"] = trajectory_b_id
    normalized["choice"] = choice
    normalized["preferred_trajectory_id"] = preferred_trajectory_id
    normalized["horizon"] = horizon
    normalized["note"] = note
    normalized["created_at"] = created_at
    normalized["branch_tags"] = normalize_text_tags(
        record.get("branch_tags", []),
        source,
        "branch_tags",
    )
    for field_name, allowed_values in (
        ("confidence", ALLOWED_CONFIDENCE),
        ("public_info_scope", ALLOWED_PUBLIC_INFO_SCOPES),
        ("lesson_type", ALLOWED_LESSON_TYPES),
    ):
        apply_optional_enum(normalized, record, source, field_name, allowed_values)
    if "condition_tags" in record:
        normalized["condition_tags"] = normalize_text_tags(
            record.get("condition_tags"),
            source,
            "condition_tags",
        )
    else:
        normalized.pop("condition_tags", None)
    if "holdout" in record:
        holdout = record.get("holdout")
        if not isinstance(holdout, bool):
            raise PreferenceDataError(f"{source}: holdout must be true or false")
        normalized["holdout"] = holdout
    else:
        normalized.pop("holdout", None)
    for field_name in (
        "source_team_hash",
        "fixture_state_hash",
        "stale_reason",
        "comparison_scope",
    ):
        apply_optional_text(normalized, record, source, field_name)
    if "compared_plan_ids" in record:
        normalized["compared_plan_ids"] = normalize_text_tags(
            record.get("compared_plan_ids"),
            source,
            "compared_plan_ids",
        )
    else:
        normalized.pop("compared_plan_ids", None)
    normalized.setdefault("tool_version", TOOL_VERSION)
    return normalized


def trajectory_key(record: dict[str, Any]) -> tuple[str, str, str]:
    trajectory_ids = sorted([record["trajectory_a_id"], record["trajectory_b_id"]])
    return (record["fixture_id"], trajectory_ids[0], trajectory_ids[1])


def load_trajectory_preferences(
    path: Path = DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    *,
    fixtures: list[dict[str, Any]] | None = None,
    known_plan_ids_by_fixture: dict[str, set[str]] | None = None,
) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    known_fixtures = fixture_map(fixtures) if fixtures is not None else None
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PreferenceDataError(f"{path}:{line_number}: invalid JSONL row: {exc}") from exc
        rows.append(
            normalize_trajectory_record(
                record,
                known_fixtures,
                f"{path}:{line_number}",
                known_plan_ids_by_fixture=known_plan_ids_by_fixture,
            )
        )
    return rows


def save_trajectory_preference(
    *,
    fixture_id: str,
    trajectory_a_id: str,
    trajectory_b_id: str,
    choice: str,
    preferred_trajectory_id: str | None = None,
    horizon: int = 3,
    confidence: str | None = None,
    public_info_scope: str | None = None,
    lesson_type: str | None = None,
    condition_tags: list[str] | None = None,
    branch_tags: list[str] | None = None,
    holdout: bool | None = None,
    comparison_scope: str | None = None,
    compared_plan_ids: list[str] | None = None,
    note: str = "",
    fixtures_path: Path | None = None,
    trajectories_path: Path = DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    known_plan_ids_by_fixture: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path) if fixtures_path is not None else load_fixtures()
    known_fixtures = fixture_map(fixtures)
    fixture = known_fixtures.get(fixture_id)
    metadata = build_v2_metadata(
        confidence=confidence,
        public_info_scope=public_info_scope,
        lesson_type=lesson_type,
        condition_tags=condition_tags,
        holdout=holdout,
    )
    record = {
        "schema_version": 1,
        "fixture_id": fixture_id,
        "trajectory_a_id": trajectory_a_id,
        "trajectory_b_id": trajectory_b_id,
        "choice": choice,
        "preferred_trajectory_id": preferred_trajectory_id,
        "horizon": horizon,
        "branch_tags": branch_tags or [],
        "comparison_scope": comparison_scope,
        "compared_plan_ids": compared_plan_ids or [],
        "note": note,
        "created_at": now_iso(),
        "tool_version": TOOL_VERSION,
        **source_hash_metadata(fixture),
        **metadata,
    }
    normalized = normalize_trajectory_record(
        record,
        known_fixtures,
        "new trajectory preference",
        known_plan_ids_by_fixture=known_plan_ids_by_fixture,
    )
    existing = load_trajectory_preferences(
        trajectories_path,
        fixtures=fixtures,
        known_plan_ids_by_fixture=known_plan_ids_by_fixture,
    )
    key = trajectory_key(normalized)
    merged = [row for row in existing if trajectory_key(row) != key]
    merged.append(normalized)
    trajectories_path.parent.mkdir(parents=True, exist_ok=True)
    with trajectories_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in merged:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return normalized


def normalize_demonstration_step(
    step: Any,
    source: str,
    valid_action_ids: set[str] | None,
) -> dict[str, Any]:
    if not isinstance(step, dict):
        raise PreferenceDataError(f"{source}: demonstration steps must be objects")
    turn = normalize_horizon(step.get("turn"), source)
    action_id = step.get("action_id")
    if not isinstance(action_id, str) or not action_id:
        raise PreferenceDataError(f"{source}: demonstration step missing action_id")
    actor = normalize_optional_text(step.get("actor"), source, "actor")
    if valid_action_ids is not None and action_id not in valid_action_ids:
        if actor not in {"boss_next_mon", "next_boss_mon", "future_boss_mon"}:
            raise PreferenceDataError(
                f"{source}: demonstration step action_id {action_id!r} is not legal"
            )
    normalized = {"turn": turn, "action_id": action_id}
    if actor:
        normalized["actor"] = actor
    return normalized


def normalize_demonstration_record(
    record: Any,
    known_fixtures: dict[str, dict[str, Any]] | None,
    source: str,
) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise PreferenceDataError(f"{source}: plan demonstration must be an object")
    schema_version = record.get("schema_version", 1)
    if schema_version != 1:
        raise PreferenceDataError(f"{source}: schema_version must be 1")
    fixture_id = record.get("fixture_id")
    if not isinstance(fixture_id, str) or not fixture_id:
        raise PreferenceDataError(f"{source}: missing fixture_id")
    fixture = known_fixtures.get(fixture_id) if known_fixtures is not None else None
    if known_fixtures is not None and fixture is None:
        raise PreferenceDataError(f"{source}: unknown fixture_id {fixture_id!r}")
    valid_action_ids = None
    if fixture is not None:
        valid_action_ids = demonstration_action_ids_for_fixture(fixture)

    demonstration_id = record.get("demonstration_id")
    if not isinstance(demonstration_id, str) or not demonstration_id:
        raise PreferenceDataError(f"{source}: missing demonstration_id")
    horizon = normalize_horizon(record.get("horizon", 3), source)
    steps = record.get("steps")
    if not isinstance(steps, list) or not steps:
        raise PreferenceDataError(f"{source}: steps must be a non-empty list")
    normalized_steps = [
        normalize_demonstration_step(step, source, valid_action_ids)
        for step in steps
    ]
    if any(step["turn"] > horizon for step in normalized_steps):
        raise PreferenceDataError(f"{source}: step turn cannot exceed horizon")

    near_tie_with = normalize_text_tags(record.get("near_tie_with", []), source, "near_tie_with")
    condition_tags = normalize_text_tags(record.get("condition_tags", []), source, "condition_tags")
    human_summary = record.get("human_summary", "")
    if not isinstance(human_summary, str) or not human_summary:
        raise PreferenceDataError(f"{source}: missing human_summary")
    created_at = record.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        raise PreferenceDataError(f"{source}: missing created_at")

    normalized = dict(record)
    normalized["schema_version"] = 1
    normalized["fixture_id"] = fixture_id
    normalized["demonstration_id"] = demonstration_id
    normalized["horizon"] = horizon
    normalized["steps"] = normalized_steps
    normalized["near_tie_with"] = near_tie_with
    normalized["condition_tags"] = condition_tags
    normalized["human_summary"] = human_summary
    normalized["created_at"] = created_at
    for field_name in ("source_team_hash", "fixture_state_hash", "stale_reason"):
        apply_optional_text(normalized, record, source, field_name)
    normalized.setdefault("tool_version", TOOL_VERSION)
    return normalized


def load_plan_demonstrations(
    path: Path = DEFAULT_PLAN_DEMONSTRATIONS_PATH,
    *,
    fixtures: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    known_fixtures = fixture_map(fixtures) if fixtures is not None else None
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PreferenceDataError(f"{path}:{line_number}: invalid JSONL row: {exc}") from exc
        rows.append(normalize_demonstration_record(record, known_fixtures, f"{path}:{line_number}"))
    return rows


def save_plan_demonstration(
    *,
    fixture_id: str,
    demonstration_id: str,
    horizon: int,
    steps: list[dict[str, Any]],
    near_tie_with: list[str] | None = None,
    condition_tags: list[str] | None = None,
    human_summary: str,
    fixtures_path: Path | None = None,
    demonstrations_path: Path = DEFAULT_PLAN_DEMONSTRATIONS_PATH,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path) if fixtures_path is not None else load_fixtures()
    known_fixtures = fixture_map(fixtures)
    fixture = known_fixtures.get(fixture_id)
    record = {
        "schema_version": 1,
        "fixture_id": fixture_id,
        "demonstration_id": demonstration_id,
        "horizon": horizon,
        "steps": steps,
        "near_tie_with": near_tie_with or [],
        "condition_tags": condition_tags or [],
        "human_summary": human_summary,
        "created_at": now_iso(),
        "tool_version": TOOL_VERSION,
        **source_hash_metadata(fixture),
    }
    normalized = normalize_demonstration_record(record, known_fixtures, "new plan demonstration")
    existing = load_plan_demonstrations(demonstrations_path, fixtures=fixtures)
    merged = [
        row
        for row in existing
        if not (
            row["fixture_id"] == normalized["fixture_id"]
            and row["demonstration_id"] == normalized["demonstration_id"]
        )
    ]
    merged.append(normalized)
    demonstrations_path.parent.mkdir(parents=True, exist_ok=True)
    with demonstrations_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in merged:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return normalized


def local_phase_for_fixture(fixture: dict[str, Any]) -> str:
    turn = fixture.get("turn")
    try:
        turn_number = int(turn)
    except (TypeError, ValueError):
        turn_number = 1
    if turn_number <= 2:
        return "early"
    if turn_number <= 8:
        return "mid"
    return "late"


def trajectory_id(record: dict[str, Any]) -> str:
    return (
        f"{record['fixture_id']}:"
        f"{record['trajectory_a_id']}:"
        f"{record['trajectory_b_id']}"
    )


def build_trajectory_report(
    fixtures: list[dict[str, Any]],
    trajectories: list[dict[str, Any]],
    demonstrations: list[dict[str, Any]],
) -> dict[str, Any]:
    fixtures_by_id = fixture_map(fixtures)
    choice_counts = Counter(row["choice"] for row in trajectories)
    lesson_counts = Counter(str(row.get("lesson_type") or "untyped") for row in trajectories)
    phase_counts: Counter[str] = Counter()
    typed_sources: dict[str, list[str]] = defaultdict(list)
    conflicts: list[dict[str, Any]] = []
    stale_rows: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)

    for row in trajectories:
        fixture = fixtures_by_id.get(row["fixture_id"], {})
        phase = local_phase_for_fixture(fixture)
        row["phase"] = phase
        phase_counts[phase] += 1
        typed_sources[str(row.get("lesson_type") or "untyped")].append(trajectory_id(row))
        by_key[trajectory_key(row)].append(row)
        current_fixture_hash = fixture_state_hash(fixture) if fixture else None
        current_team_hash = source_team_hash_for_fixture(fixture) if fixture else None
        stale_reasons: list[str] = []
        if current_fixture_hash and row.get("fixture_state_hash") not in {None, current_fixture_hash}:
            stale_reasons.append("fixture_state_hash changed")
        if current_team_hash and row.get("source_team_hash") not in {None, current_team_hash}:
            stale_reasons.append("source_team_hash changed")
        if stale_reasons:
            stale_rows.append(
                {
                    "trajectory_id": trajectory_id(row),
                    "fixture_id": row["fixture_id"],
                    "reasons": stale_reasons,
                    "stored_fixture_state_hash": row.get("fixture_state_hash"),
                    "current_fixture_state_hash": current_fixture_hash,
                    "stored_source_team_hash": row.get("source_team_hash"),
                    "current_source_team_hash": current_team_hash,
                }
            )

    for key, rows in by_key.items():
        choices = sorted({row["choice"] for row in rows})
        if len(rows) > 1 and len(choices) > 1:
            conflicts.append(
                {
                    "fixture_id": key[0],
                    "trajectory_ids": [key[1], key[2]],
                    "choices": choices,
                    "count": len(rows),
                }
            )

    demonstration_phase_counts: Counter[str] = Counter()
    for row in demonstrations:
        fixture = fixtures_by_id.get(row["fixture_id"], {})
        demonstration_phase_counts[local_phase_for_fixture(fixture)] += 1

    return {
        "generated_at": now_iso(),
        "fixture_count": len(fixtures),
        "trajectory_count": len(trajectories),
        "demonstration_count": len(demonstrations),
        "choice_counts": dict(sorted(choice_counts.items())),
        "lesson_type_counts": dict(sorted(lesson_counts.items())),
        "phase_counts": dict(sorted(phase_counts.items())),
        "demonstration_phase_counts": dict(sorted(demonstration_phase_counts.items())),
        "conflicts": conflicts,
        "stale_rows": stale_rows,
        "lesson_sources": {
            lesson_type: sorted(source_ids)
            for lesson_type, source_ids in sorted(typed_sources.items())
        },
        "trajectories": trajectories,
        "demonstrations": demonstrations,
    }


def render_trajectory_report(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Trajectory Preference Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Fixtures: {report['fixture_count']}",
        f"- Trajectory preferences: {report['trajectory_count']}",
        f"- Plan demonstrations: {report['demonstration_count']}",
        f"- Conflicting duplicate trajectory rows: {len(report['conflicts'])}",
        f"- Stale trajectory rows: {len(report.get('stale_rows', []))}",
        "",
        "## Choice Counts",
        "",
    ]
    if report["choice_counts"]:
        for choice, count in report["choice_counts"].items():
            lines.append(f"- `{choice}`: {count}")
    else:
        lines.append("No trajectory preferences have been recorded yet.")

    lines.extend(["", "## Phase Coverage", ""])
    if report["phase_counts"]:
        for phase, count in report["phase_counts"].items():
            lines.append(f"- `{phase}`: {count}")
    else:
        lines.append("No trajectory phase coverage yet.")

    lines.extend(["", "## Lesson Type Counts", ""])
    if report["lesson_type_counts"]:
        for lesson_type, count in report["lesson_type_counts"].items():
            lines.append(f"- `{lesson_type}`: {count}")
    else:
        lines.append("No typed trajectory lessons yet.")

    lines.extend(["", "## Conflicts", ""])
    if report["conflicts"]:
        for conflict in report["conflicts"]:
            choices = ", ".join(f"`{choice}`" for choice in conflict["choices"])
            plan_ids = " vs ".join(f"`{plan_id}`" for plan_id in conflict["trajectory_ids"])
            lines.append(f"- `{conflict['fixture_id']}` {plan_ids}: {choices}")
    else:
        lines.append("No conflicting duplicate trajectory rows.")

    lines.extend(["", "## Stale Rows", ""])
    if report.get("stale_rows"):
        for row in report["stale_rows"]:
            reasons = ", ".join(row["reasons"])
            lines.append(f"- `{row['trajectory_id']}`: {reasons}")
    else:
        lines.append("No trajectory rows have changed source hashes.")

    lines.extend(["", "## Recent Trajectories", ""])
    if report["trajectories"]:
        for row in report["trajectories"][-20:]:
            lines.append(
                f"- `{trajectory_id(row)}`: `{row['choice']}` "
                f"({row.get('lesson_type') or 'untyped'}, {row.get('phase')})"
            )
    else:
        lines.append("No trajectory rows yet.")
    lines.append("")
    return "\n".join(lines)


def write_trajectory_report(
    *,
    fixtures_path: Path,
    trajectories_path: Path = DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    demonstrations_path: Path = DEFAULT_PLAN_DEMONSTRATIONS_PATH,
    out_path: Path = DEFAULT_TRAJECTORY_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_TRAJECTORY_JSON_PATH,
    known_plan_ids_by_fixture: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    trajectories = load_trajectory_preferences(
        trajectories_path,
        fixtures=fixtures,
        known_plan_ids_by_fixture=known_plan_ids_by_fixture,
    )
    demonstrations = load_plan_demonstrations(demonstrations_path, fixtures=fixtures)
    report = build_trajectory_report(fixtures, trajectories, demonstrations)
    markdown = render_trajectory_report(report)

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
