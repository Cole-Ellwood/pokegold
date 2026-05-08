from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_FIXTURES_PATH = PACKAGE_DIR / "fixtures" / "boss_ai_preference_fixtures.json"
DEFAULT_LABELS_PATH = PACKAGE_DIR / "labels" / "boss_ai_labels.jsonl"
DEFAULT_PREFERENCES_PATH = PACKAGE_DIR / "labels" / "boss_ai_pairwise_preferences.jsonl"
DEFAULT_REPORT_PATH = ROOT / "audit" / "boss_ai_preference" / "latest_report.md"
DEFAULT_JSON_REPORT_PATH = ROOT / "audit" / "boss_ai_preference" / "latest_report.json"

TOOL_VERSION = "boss-ai-preference-v0"
ALLOWED_LABELS = (
    "best",
    "good",
    "bad",
    "cheap",
    "scary_good",
    "needs_context",
)

NEGATIVE_BASELINE_LABELS = {"bad", "cheap"}

ALLOWED_PAIRWISE_CHOICES = (
    "a_better",
    "b_better",
    "both_good",
    "both_bad",
    "other_better",
    "needs_context",
)

ALLOWED_REASON_TAGS = (
    "uses_public_info",
    "misses_public_threat",
    "keeps_tempo",
    "too_greedy",
    "scary_pressure",
    "fits_boss_style",
    "reduces_risk",
    "too_passive",
    "calculated_risk",
)


class PreferenceDataError(ValueError):
    """Raised when fixtures or labels do not match the tool's data contract."""


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PreferenceDataError(f"{path}: invalid JSON: {exc}") from exc


def load_fixtures(path: Path = DEFAULT_FIXTURES_PATH) -> list[dict[str, Any]]:
    data = read_json(path)
    errors = validate_fixture_data(data)
    if errors:
        raise PreferenceDataError("\n".join(errors))
    return list(data["fixtures"])


def validate_fixture_data(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["fixture file root must be an object"]
    if data.get("schema_version") != 1:
        errors.append("fixture file schema_version must be 1")
    fixtures = data.get("fixtures")
    if not isinstance(fixtures, list):
        return [*errors, "fixture file must contain a fixtures list"]

    seen_fixture_ids: set[str] = set()
    for index, fixture in enumerate(fixtures):
        prefix = f"fixtures[{index}]"
        if not isinstance(fixture, dict):
            errors.append(f"{prefix}: fixture must be an object")
            continue
        fixture_id = fixture.get("id")
        if not isinstance(fixture_id, str) or not fixture_id:
            errors.append(f"{prefix}: missing id")
        elif fixture_id in seen_fixture_ids:
            errors.append(f"{prefix}: duplicate id {fixture_id!r}")
        else:
            seen_fixture_ids.add(fixture_id)

        for key in ("leader", "state", "actions"):
            if key not in fixture:
                errors.append(f"{prefix}: missing {key}")
        if not isinstance(fixture.get("state"), dict):
            errors.append(f"{prefix}: state must be an object")

        actions = fixture.get("actions")
        if not isinstance(actions, list) or not actions:
            errors.append(f"{prefix}: actions must be a non-empty list")
            continue

        seen_action_ids: set[str] = set()
        for action_index, action in enumerate(actions):
            action_prefix = f"{prefix}.actions[{action_index}]"
            if not isinstance(action, dict):
                errors.append(f"{action_prefix}: action must be an object")
                continue
            action_id = action.get("id")
            if not isinstance(action_id, str) or not action_id:
                errors.append(f"{action_prefix}: missing id")
            elif action_id in seen_action_ids:
                errors.append(f"{action_prefix}: duplicate id {action_id!r}")
            else:
                seen_action_ids.add(action_id)
            if not isinstance(action.get("name"), str) or not action.get("name"):
                errors.append(f"{action_prefix}: missing name")
            if not isinstance(action.get("kind"), str) or not action.get("kind"):
                errors.append(f"{action_prefix}: missing kind")
            if not isinstance(action.get("explanation"), str) or not action.get("explanation"):
                errors.append(f"{action_prefix}: missing explanation")

        baseline_action_id = fixture.get("baseline_action_id")
        if baseline_action_id is not None and baseline_action_id not in seen_action_ids:
            errors.append(f"{prefix}: baseline_action_id {baseline_action_id!r} is not an action")
    return errors


def fixture_map(fixtures: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {fixture["id"]: fixture for fixture in fixtures}


def action_map(fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {action["id"]: action for action in fixture["actions"]}


def load_labels(
    path: Path = DEFAULT_LABELS_PATH,
    *,
    fixtures: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    known_fixtures = fixture_map(fixtures) if fixtures is not None else None
    labels: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PreferenceDataError(f"{path}:{line_number}: invalid JSONL row: {exc}") from exc
        labels.append(normalize_label_record(record, known_fixtures, f"{path}:{line_number}"))
    return labels


def load_preferences(
    path: Path = DEFAULT_PREFERENCES_PATH,
    *,
    fixtures: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    known_fixtures = fixture_map(fixtures) if fixtures is not None else None
    preferences: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PreferenceDataError(f"{path}:{line_number}: invalid JSONL row: {exc}") from exc
        preferences.append(
            normalize_preference_record(record, known_fixtures, f"{path}:{line_number}")
        )
    return preferences


def normalize_label_record(
    record: Any,
    known_fixtures: dict[str, dict[str, Any]] | None,
    source: str,
) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise PreferenceDataError(f"{source}: label record must be an object")
    fixture_id = record.get("fixture_id")
    action_id = record.get("action_id")
    label = record.get("label")
    if not isinstance(fixture_id, str) or not fixture_id:
        raise PreferenceDataError(f"{source}: missing fixture_id")
    if not isinstance(action_id, str) or not action_id:
        raise PreferenceDataError(f"{source}: missing action_id")
    if label not in ALLOWED_LABELS:
        raise PreferenceDataError(
            f"{source}: label must be one of {', '.join(ALLOWED_LABELS)}"
        )
    if known_fixtures is not None:
        fixture = known_fixtures.get(fixture_id)
        if fixture is None:
            raise PreferenceDataError(f"{source}: unknown fixture_id {fixture_id!r}")
        if action_id not in action_map(fixture):
            raise PreferenceDataError(
                f"{source}: action_id {action_id!r} is not in fixture {fixture_id!r}"
            )

    rank = record.get("rank")
    if rank is not None:
        if isinstance(rank, bool):
            raise PreferenceDataError(f"{source}: rank must be an integer")
        try:
            rank = int(rank)
        except (TypeError, ValueError) as exc:
            raise PreferenceDataError(f"{source}: rank must be an integer") from exc
        if rank < 1:
            raise PreferenceDataError(f"{source}: rank must be >= 1")

    note = record.get("note", "")
    if note is None:
        note = ""
    if not isinstance(note, str):
        raise PreferenceDataError(f"{source}: note must be text")

    created_at = record.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        raise PreferenceDataError(f"{source}: missing created_at")

    normalized = dict(record)
    normalized["fixture_id"] = fixture_id
    normalized["action_id"] = action_id
    normalized["label"] = label
    normalized["rank"] = rank
    normalized["note"] = note
    normalized.setdefault("state_version", 1)
    normalized.setdefault("tool_version", TOOL_VERSION)
    return normalized


def normalize_preference_record(
    record: Any,
    known_fixtures: dict[str, dict[str, Any]] | None,
    source: str,
) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise PreferenceDataError(f"{source}: preference record must be an object")
    fixture_id = record.get("fixture_id")
    action_a_id = record.get("action_a_id")
    action_b_id = record.get("action_b_id")
    choice = record.get("choice")
    if not isinstance(fixture_id, str) or not fixture_id:
        raise PreferenceDataError(f"{source}: missing fixture_id")
    if not isinstance(action_a_id, str) or not action_a_id:
        raise PreferenceDataError(f"{source}: missing action_a_id")
    if not isinstance(action_b_id, str) or not action_b_id:
        raise PreferenceDataError(f"{source}: missing action_b_id")
    if action_a_id == action_b_id:
        raise PreferenceDataError(f"{source}: action_a_id and action_b_id must differ")
    if choice not in ALLOWED_PAIRWISE_CHOICES:
        raise PreferenceDataError(
            f"{source}: choice must be one of {', '.join(ALLOWED_PAIRWISE_CHOICES)}"
        )

    valid_action_ids: set[str] | None = None
    if known_fixtures is not None:
        known_fixture = known_fixtures.get(fixture_id)
        if known_fixture is None:
            raise PreferenceDataError(f"{source}: unknown fixture_id {fixture_id!r}")
        valid_action_ids = set(action_map(known_fixture))
        for key, action_id in (
            ("action_a_id", action_a_id),
            ("action_b_id", action_b_id),
        ):
            if action_id not in valid_action_ids:
                raise PreferenceDataError(
                    f"{source}: {key} {action_id!r} is not in fixture {fixture_id!r}"
                )

    preferred_action_id = record.get("preferred_action_id")
    if preferred_action_id is None or preferred_action_id == "":
        preferred_action_id = None
    elif not isinstance(preferred_action_id, str):
        raise PreferenceDataError(f"{source}: preferred_action_id must be text")
    elif valid_action_ids is not None and preferred_action_id not in valid_action_ids:
        raise PreferenceDataError(
            f"{source}: preferred_action_id {preferred_action_id!r} is not in fixture {fixture_id!r}"
        )

    if choice == "a_better":
        preferred_action_id = action_a_id
    elif choice == "b_better":
        preferred_action_id = action_b_id
    elif choice == "other_better" and preferred_action_id is None:
        raise PreferenceDataError(f"{source}: other_better requires preferred_action_id")

    reason_tags = normalize_reason_tags(record.get("reason_tags", []), source, "reason_tags")
    action_tags = normalize_action_tags(
        record.get("action_tags", {}),
        valid_action_ids,
        source,
    )
    for action_id in (action_a_id, action_b_id, preferred_action_id):
        if action_id is not None:
            action_tags.setdefault(action_id, [])

    unknown_tags = sorted(
        {
            tag
            for tags in [reason_tags, *action_tags.values()]
            for tag in tags
            if tag not in ALLOWED_REASON_TAGS
        }
    )
    if unknown_tags:
        raise PreferenceDataError(
            f"{source}: unknown reason_tags {', '.join(unknown_tags)}"
        )

    note = record.get("note", "")
    if note is None:
        note = ""
    if not isinstance(note, str):
        raise PreferenceDataError(f"{source}: note must be text")

    created_at = record.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        raise PreferenceDataError(f"{source}: missing created_at")

    state_version = record.get("state_version", 1)
    if isinstance(state_version, bool):
        raise PreferenceDataError(f"{source}: state_version must be an integer")
    try:
        state_version = int(state_version)
    except (TypeError, ValueError) as exc:
        raise PreferenceDataError(f"{source}: state_version must be an integer") from exc
    if state_version < 1:
        raise PreferenceDataError(f"{source}: state_version must be >= 1")

    normalized = dict(record)
    normalized["fixture_id"] = fixture_id
    normalized["state_version"] = state_version
    normalized["action_a_id"] = action_a_id
    normalized["action_b_id"] = action_b_id
    normalized["choice"] = choice
    normalized["preferred_action_id"] = preferred_action_id
    normalized["reason_tags"] = reason_tags
    normalized["action_tags"] = action_tags
    normalized["note"] = note
    normalized.setdefault("tool_version", TOOL_VERSION)
    return normalized


def normalize_reason_tags(value: Any, source: str, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(tag, str) for tag in value):
        raise PreferenceDataError(f"{source}: {field_name} must be a list of text tags")
    return sorted(set(value))


def normalize_action_tags(
    value: Any,
    valid_action_ids: set[str] | None,
    source: str,
) -> dict[str, list[str]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise PreferenceDataError(f"{source}: action_tags must be an object")
    normalized: dict[str, list[str]] = {}
    for action_id, tags in value.items():
        if not isinstance(action_id, str) or not action_id:
            raise PreferenceDataError(f"{source}: action_tags keys must be action ids")
        if valid_action_ids is not None and action_id not in valid_action_ids:
            raise PreferenceDataError(
                f"{source}: action_tags key {action_id!r} is not in fixture"
            )
        normalized[action_id] = normalize_reason_tags(tags, source, f"action_tags.{action_id}")
    return dict(sorted(normalized.items()))


def append_label(
    *,
    fixture_id: str,
    action_id: str,
    label: str,
    rank: int | None = None,
    note: str = "",
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    known_fixtures = fixture_map(fixtures)
    record = {
        "fixture_id": fixture_id,
        "state_version": 1,
        "action_id": action_id,
        "label": label,
        "rank": rank,
        "note": note,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "tool_version": TOOL_VERSION,
    }
    normalized = normalize_label_record(record, known_fixtures, "new label")
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    with labels_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(normalized, sort_keys=True) + "\n")
    return normalized


def save_preference(
    *,
    fixture_id: str,
    action_a_id: str,
    action_b_id: str,
    choice: str,
    preferred_action_id: str | None = None,
    reason_tags: list[str] | None = None,
    action_tags: dict[str, list[str]] | None = None,
    note: str = "",
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    known_fixtures = fixture_map(fixtures)
    record = {
        "fixture_id": fixture_id,
        "state_version": 1,
        "action_a_id": action_a_id,
        "action_b_id": action_b_id,
        "choice": choice,
        "preferred_action_id": preferred_action_id,
        "reason_tags": reason_tags or [],
        "action_tags": action_tags or {},
        "note": note,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "tool_version": TOOL_VERSION,
    }
    normalized = normalize_preference_record(record, known_fixtures, "new preference")
    preferences_path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_preferences(preferences_path, fixtures=fixtures)
    key = preference_key(normalized)
    merged = [
        preference
        for preference in existing
        if preference_key(preference) != key
    ]
    merged.append(normalized)
    with preferences_path.open("w", encoding="utf-8", newline="\n") as handle:
        for preference in merged:
            handle.write(json.dumps(preference, sort_keys=True) + "\n")
    return normalized


append_preference = save_preference


def preference_key(preference: dict[str, Any]) -> tuple[str, str, str]:
    action_ids = sorted([preference["action_a_id"], preference["action_b_id"]])
    return (
        preference["fixture_id"],
        action_ids[0],
        action_ids[1],
    )


def preference_disagrees_with_baseline(
    preference: dict[str, Any],
    baseline_action_id: str | None,
) -> bool:
    if not baseline_action_id:
        return False
    if preference["choice"] == "both_bad":
        return baseline_action_id in {
            preference["action_a_id"],
            preference["action_b_id"],
        }
    preferred_action_id = preference.get("preferred_action_id")
    return preferred_action_id is not None and preferred_action_id != baseline_action_id


def build_report(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    preferences: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    preferences = preferences or []
    by_fixture: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_fixture_action: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for label in labels:
        by_fixture[label["fixture_id"]].append(label)
        by_fixture_action[(label["fixture_id"], label["action_id"])].append(label)
    preferences_by_fixture: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for preference in preferences:
        preferences_by_fixture[preference["fixture_id"]].append(preference)

    conflicts: list[dict[str, Any]] = []
    for (fixture_id, action_id), records in sorted(by_fixture_action.items()):
        label_values = {record["label"] for record in records}
        rank_values = {record.get("rank") for record in records}
        if len(records) > 1 and (len(label_values) > 1 or len(rank_values) > 1):
            conflicts.append(
                {
                    "fixture_id": fixture_id,
                    "action_id": action_id,
                    "labels": sorted(label_values),
                    "ranks": sorted(value for value in rank_values if value is not None),
                    "count": len(records),
                }
            )

    fixture_reports: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    for fixture in fixtures:
        fixture_id = fixture["id"]
        records = by_fixture.get(fixture_id, [])
        preference_records = preferences_by_fixture.get(fixture_id, [])
        baseline_action_id = fixture.get("baseline_action_id")
        best_action_ids = sorted(
            {
                record["action_id"]
                for record in records
                if record["label"] == "best" or record.get("rank") == 1
            }
        )
        baseline_negative = any(
            record["action_id"] == baseline_action_id
            and record["label"] in NEGATIVE_BASELINE_LABELS
            for record in records
        )
        disagrees = bool(
            baseline_action_id
            and (
                (best_action_ids and baseline_action_id not in best_action_ids)
                or baseline_negative
                or any(
                    preference_disagrees_with_baseline(preference, baseline_action_id)
                    for preference in preference_records
                )
            )
        )
        item = {
            "fixture_id": fixture_id,
            "leader": fixture["leader"],
            "label_count": len(records),
            "preference_count": len(preference_records),
            "baseline_action_id": baseline_action_id,
            "best_action_ids": best_action_ids,
            "disagrees_with_baseline": disagrees,
            "tags": fixture.get("tags", []),
            "training_focus": fixture.get("training_focus", ""),
        }
        fixture_reports.append(item)
        if disagrees:
            disagreements.append(item)

    label_counts = Counter(record["label"] for record in labels)
    preference_counts = Counter(record["choice"] for record in preferences)
    return {
        "tool_version": TOOL_VERSION,
        "fixture_count": len(fixtures),
        "label_count": len(labels),
        "preference_count": len(preferences),
        "labeled_fixture_count": sum(1 for item in fixture_reports if item["label_count"]),
        "preferenced_fixture_count": sum(
            1 for item in fixture_reports if item["preference_count"]
        ),
        "feedback_fixture_count": sum(
            1
            for item in fixture_reports
            if item["label_count"] or item["preference_count"]
        ),
        "label_counts": dict(sorted(label_counts.items())),
        "preference_counts": dict(sorted(preference_counts.items())),
        "conflicts": conflicts,
        "disagreements": disagreements,
        "fixtures": fixture_reports,
    }


def render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Preference Report",
        "",
        f"Generated by `{report['tool_version']}`.",
        "",
        "## Summary",
        "",
        f"- Fixtures: {report['fixture_count']}",
        f"- Labels: {report['label_count']}",
        f"- Pairwise preferences: {report['preference_count']}",
        f"- Labeled fixtures: {report['labeled_fixture_count']} / {report['fixture_count']}",
        f"- Preferenced fixtures: {report['preferenced_fixture_count']} / {report['fixture_count']}",
        f"- Baseline disagreements: {len(report['disagreements'])}",
        f"- Conflicting duplicate labels: {len(report['conflicts'])}",
        "",
    ]
    if report["label_counts"]:
        lines.extend(["## Label Counts", ""])
        for label, count in report["label_counts"].items():
            lines.append(f"- `{label}`: {count}")
        lines.append("")
    else:
        lines.extend(
            [
                "## Label Counts",
                "",
                "No labels have been recorded yet.",
                "",
            ]
        )

    if report["preference_counts"]:
        lines.extend(["## Pairwise Preference Counts", ""])
        for choice, count in report["preference_counts"].items():
            lines.append(f"- `{choice}`: {count}")
        lines.append("")
    else:
        lines.extend(
            [
                "## Pairwise Preference Counts",
                "",
                "No pairwise preferences have been recorded yet.",
                "",
            ]
        )

    lines.extend(["## Disagreements", ""])
    if report["disagreements"]:
        for item in report["disagreements"]:
            best = ", ".join(f"`{action}`" for action in item["best_action_ids"]) or "none"
            lines.append(
                f"- `{item['fixture_id']}` ({item['leader']}): baseline "
                f"`{item['baseline_action_id']}`, best {best}"
            )
    else:
        lines.append("No labeled fixture currently disagrees with its baseline action.")
    lines.append("")

    lines.extend(["## Conflicts", ""])
    if report["conflicts"]:
        for conflict in report["conflicts"]:
            labels = ", ".join(f"`{label}`" for label in conflict["labels"])
            ranks = ", ".join(str(rank) for rank in conflict["ranks"]) or "none"
            lines.append(
                f"- `{conflict['fixture_id']}` / `{conflict['action_id']}`: "
                f"{conflict['count']} labels, labels {labels}, ranks {ranks}"
            )
    else:
        lines.append("No conflicting duplicate labels.")
    lines.append("")

    lines.extend(["## Fixture Coverage", ""])
    for item in report["fixtures"]:
        status = "feedback" if item["label_count"] or item["preference_count"] else "unlabeled"
        lines.append(
            f"- `{item['fixture_id']}` ({item['leader']}): {status}, "
            f"{item['label_count']} label(s), {item['preference_count']} preference(s). "
            f"Focus: {item['training_focus']}"
        )
    lines.append("")
    return "\n".join(lines)


def write_report(
    *,
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    labels_path: Path = DEFAULT_LABELS_PATH,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    out_path: Path = DEFAULT_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_JSON_REPORT_PATH,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    labels = load_labels(labels_path, fixtures=fixtures)
    preferences = load_preferences(preferences_path, fixtures=fixtures)
    report = build_report(fixtures, labels, preferences)
    markdown = render_markdown_report(report)

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
