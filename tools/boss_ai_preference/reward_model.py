from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.boss_ai_debugger.scorer import score_action

from .data import (
    DEFAULT_FIXTURES_PATH,
    DEFAULT_PREFERENCES_PATH,
    PreferenceDataError,
    action_map,
    fixture_map,
    load_fixtures,
    load_preferences,
)
from .features import enrich_fixtures, extract_fixture_features, extract_plan_features
from .lessons import preference_id
from .plans import generate_plan_cards
from .trajectory_data import (
    DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    STRICT_TRAJECTORY_CHOICES,
    load_trajectory_preferences,
    trajectory_id,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REWARD_MODEL_REPORT_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "reward_model_report.md"
)
DEFAULT_REWARD_MODEL_JSON_PATH = (
    ROOT / "audit" / "boss_ai_preference" / "reward_model_report.json"
)

STRICT_CHOICES = {"a_better", "b_better"}


@dataclass(frozen=True)
class PreferenceExample:
    preference_id: str
    fixture_id: str
    leader: str
    action_a_id: str
    action_b_id: str
    y: int
    split: str
    lesson_type: str
    feature_diff: dict[str, float]
    scorer_choice: str
    note: str


@dataclass(frozen=True)
class TrajectoryPreferenceExample:
    preference_id: str
    fixture_id: str
    leader: str
    trajectory_a_id: str
    trajectory_b_id: str
    y: int
    split: str
    lesson_type: str
    feature_diff: dict[str, float]
    scorer_choice: str
    note: str


def stable_holdout_id(identifier: str) -> bool:
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 5 == 0


def stable_holdout(preference: dict[str, Any]) -> bool:
    return stable_holdout_id(preference_id(preference))


def feature_rows_by_key(fixtures: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, float]]:
    rows: dict[tuple[str, str], dict[str, float]] = {}
    for fixture in enrich_fixtures(fixtures):
        for row in extract_fixture_features(fixture):
            rows[(row["fixture_id"], row["action_id"])] = row["features"]
    return rows


def plan_feature_rows_by_key(fixtures: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, float]]:
    rows: dict[tuple[str, str], dict[str, float]] = {}
    for fixture in enrich_fixtures(fixtures):
        for plan in generate_plan_cards(fixture):
            row = extract_plan_features(fixture, plan)
            rows[(row["fixture_id"], row["plan_id"])] = row["features"]
    return rows


def diff_features(
    action_a: dict[str, float],
    action_b: dict[str, float],
) -> dict[str, float]:
    keys = set(action_a) | set(action_b)
    return {
        key: round(float(action_a.get(key, 0.0)) - float(action_b.get(key, 0.0)), 4)
        for key in keys
        if action_a.get(key, 0.0) != action_b.get(key, 0.0)
    }


def scorer_choice_for_pair(
    fixture: dict[str, Any],
    action_a_id: str,
    action_b_id: str,
) -> str:
    actions = action_map(fixture)
    score_a = int(score_action(fixture, actions[action_a_id])["score"])
    score_b = int(score_action(fixture, actions[action_b_id])["score"])
    if score_a == score_b:
        return "tie"
    if score_a > score_b:
        return "a_better"
    return "b_better"


def build_examples(
    fixtures: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
) -> list[PreferenceExample]:
    fixtures_by_id = fixture_map(fixtures)
    features_by_key = feature_rows_by_key(fixtures)
    examples: list[PreferenceExample] = []

    for preference in preferences:
        if preference["choice"] not in STRICT_CHOICES:
            continue
        fixture = fixtures_by_id.get(preference["fixture_id"])
        if fixture is None:
            raise PreferenceDataError(f"unknown fixture_id {preference['fixture_id']!r}")
        action_a_id = preference["action_a_id"]
        action_b_id = preference["action_b_id"]
        try:
            features_a = features_by_key[(fixture["id"], action_a_id)]
            features_b = features_by_key[(fixture["id"], action_b_id)]
        except KeyError as exc:
            raise PreferenceDataError(
                f"fixture {fixture['id']!r}: missing features for action {exc.args[0]!r}"
            ) from exc

        split = "train"
        if preference.get("holdout") is True:
            split = "holdout"
        elif "holdout" not in preference and stable_holdout(preference):
            split = "holdout"

        examples.append(
            PreferenceExample(
                preference_id=preference_id(preference),
                fixture_id=fixture["id"],
                leader=fixture["leader"],
                action_a_id=action_a_id,
                action_b_id=action_b_id,
                y=1 if preference["choice"] == "a_better" else 0,
                split=split,
                lesson_type=str(preference.get("lesson_type") or "untyped"),
                feature_diff=diff_features(features_a, features_b),
                scorer_choice=scorer_choice_for_pair(fixture, action_a_id, action_b_id),
                note=str(preference.get("note", "")),
            )
        )
    return examples


def build_trajectory_examples(
    fixtures: list[dict[str, Any]],
    trajectories: list[dict[str, Any]],
) -> tuple[list[TrajectoryPreferenceExample], list[dict[str, Any]]]:
    fixtures_by_id = fixture_map(fixtures)
    features_by_key = plan_feature_rows_by_key(fixtures)
    examples: list[TrajectoryPreferenceExample] = []
    skipped: list[dict[str, Any]] = []

    for trajectory in trajectories:
        if trajectory["choice"] not in STRICT_TRAJECTORY_CHOICES:
            continue
        fixture = fixtures_by_id.get(trajectory["fixture_id"])
        if fixture is None:
            raise PreferenceDataError(f"unknown fixture_id {trajectory['fixture_id']!r}")
        trajectory_a_id = trajectory["trajectory_a_id"]
        trajectory_b_id = trajectory["trajectory_b_id"]
        features_a = features_by_key.get((fixture["id"], trajectory_a_id))
        features_b = features_by_key.get((fixture["id"], trajectory_b_id))
        if features_a is None or features_b is None:
            skipped.append(
                {
                    "trajectory_id": trajectory_id(trajectory),
                    "reason": "referenced plan is not generated for the current fixture",
                }
            )
            continue

        split = "train"
        if trajectory.get("holdout") is True:
            split = "holdout"
        elif "holdout" not in trajectory and stable_holdout_id(trajectory_id(trajectory)):
            split = "holdout"

        examples.append(
            TrajectoryPreferenceExample(
                preference_id=f"trajectory:{trajectory_id(trajectory)}",
                fixture_id=fixture["id"],
                leader=fixture["leader"],
                trajectory_a_id=trajectory_a_id,
                trajectory_b_id=trajectory_b_id,
                y=1 if trajectory["choice"] == "a_better" else 0,
                split=split,
                lesson_type=str(trajectory.get("lesson_type") or "untyped"),
                feature_diff=diff_features(features_a, features_b),
                scorer_choice="not_scored_by_rom",
                note=str(trajectory.get("note", "")),
            )
        )
    return examples, skipped


def sigmoid(value: float) -> float:
    if value >= 40:
        return 1.0
    if value <= -40:
        return 0.0
    return 1.0 / (1.0 + math.exp(-value))


def train_weights(
    examples: list[PreferenceExample],
    *,
    epochs: int = 500,
    learning_rate: float = 0.08,
    l2: float = 0.02,
) -> dict[str, float]:
    weights: dict[str, float] = defaultdict(float)
    if not examples:
        return {}

    for _ in range(epochs):
        gradients: dict[str, float] = defaultdict(float)
        for example in examples:
            score = sum(
                weights[name] * value
                for name, value in example.feature_diff.items()
            )
            error = sigmoid(score) - example.y
            for name, value in example.feature_diff.items():
                gradients[name] += error * value
        scale = 1.0 / len(examples)
        for name in set(weights) | set(gradients):
            gradient = gradients[name] * scale + l2 * weights[name]
            weights[name] -= learning_rate * gradient

    return {
        name: round(value, 6)
        for name, value in sorted(weights.items())
        if abs(value) >= 0.0001
    }


def model_probability(example: PreferenceExample, weights: dict[str, float]) -> float:
    score = sum(weights.get(name, 0.0) * value for name, value in example.feature_diff.items())
    return sigmoid(score)


def model_choice(example: PreferenceExample, weights: dict[str, float]) -> str:
    probability = model_probability(example, weights)
    if 0.45 <= probability <= 0.55:
        return "tie"
    return "a_better" if probability > 0.55 else "b_better"


def expected_choice(example: PreferenceExample) -> str:
    return "a_better" if example.y == 1 else "b_better"


def evaluate_examples(
    examples: list[PreferenceExample],
    weights: dict[str, float],
) -> dict[str, Any]:
    correct = 0
    by_leader: dict[str, Counter[str]] = defaultdict(Counter)
    by_lesson_type: dict[str, Counter[str]] = defaultdict(Counter)
    rows: list[dict[str, Any]] = []

    for example in examples:
        choice = model_choice(example, weights)
        expected = expected_choice(example)
        agrees = choice == expected
        if agrees:
            correct += 1
        by_leader[example.leader]["total"] += 1
        by_leader[example.leader]["correct"] += int(agrees)
        by_lesson_type[example.lesson_type]["total"] += 1
        by_lesson_type[example.lesson_type]["correct"] += int(agrees)
        rows.append(
            {
                "preference_id": example.preference_id,
                "fixture_id": example.fixture_id,
                "leader": example.leader,
                "expected": expected,
                "model_choice": choice,
                "model_probability_a": round(model_probability(example, weights), 4),
                "scorer_choice": example.scorer_choice,
                "agrees": agrees,
            }
        )

    total = len(examples)
    accuracy = round(correct / total, 4) if total else None
    return {
        "count": total,
        "correct": correct,
        "accuracy": accuracy,
        "accuracy_label": f"{accuracy:.1%}" if accuracy is not None else "n/a",
        "by_leader": summarize_counter_metrics(by_leader),
        "by_lesson_type": summarize_counter_metrics(by_lesson_type),
        "examples": rows,
    }


def summarize_counter_metrics(counters: dict[str, Counter[str]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for name, counter in sorted(counters.items()):
        total = counter["total"]
        correct = counter["correct"]
        accuracy = round(correct / total, 4) if total else None
        summary[name] = {
            "count": total,
            "correct": correct,
            "accuracy": accuracy,
            "accuracy_label": f"{accuracy:.1%}" if accuracy is not None else "n/a",
        }
    return summary


def feature_support(examples: list[PreferenceExample]) -> Counter[str]:
    support: Counter[str] = Counter()
    for example in examples:
        for name, value in example.feature_diff.items():
            if value:
                support[name] += 1
    return support


def compare_with_current_scorer(
    examples: list[PreferenceExample],
    weights: dict[str, float],
) -> dict[str, list[dict[str, Any]]]:
    model_fixes: list[dict[str, Any]] = []
    scorer_fixes: list[dict[str, Any]] = []
    for example in examples:
        expected = expected_choice(example)
        model = model_choice(example, weights)
        scorer = example.scorer_choice
        row = {
            "preference_id": example.preference_id,
            "leader": example.leader,
            "expected": expected,
            "model_choice": model,
            "scorer_choice": scorer,
            "note": example.note[:240],
        }
        if model == expected and scorer != expected:
            model_fixes.append(row)
        if scorer == expected and model != expected:
            scorer_fixes.append(row)
    return {
        "model_correct_scorer_missed": model_fixes,
        "scorer_correct_model_missed": scorer_fixes,
    }


def model_section(
    examples: list[Any],
    *,
    epochs: int,
    learning_rate: float,
    l2: float,
    skipped: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    train = [example for example in examples if example.split == "train"]
    holdout = [example for example in examples if example.split == "holdout"]
    weights = train_weights(train, epochs=epochs, learning_rate=learning_rate, l2=l2)
    support = feature_support(train)
    sorted_weights = sorted(weights.items(), key=lambda item: item[1])
    positive_weights = [(name, weight) for name, weight in sorted_weights if weight > 0]
    negative_weights = [(name, weight) for name, weight in sorted_weights if weight < 0]
    return {
        "strict_example_count": len(examples),
        "train_count": len(train),
        "holdout_count": len(holdout),
        "train_metrics": evaluate_examples(train, weights),
        "holdout_metrics": evaluate_examples(holdout, weights),
        "all_metrics": evaluate_examples(examples, weights),
        "top_positive_weights": [
            {"feature": name, "weight": weight, "support": support.get(name, 0)}
            for name, weight in positive_weights[-15:][::-1]
        ],
        "top_negative_weights": [
            {"feature": name, "weight": weight, "support": support.get(name, 0)}
            for name, weight in negative_weights[:15]
        ],
        "unstable_low_support_weights": [
            {"feature": name, "weight": weight, "support": support.get(name, 0)}
            for name, weight in sorted_weights
            if support.get(name, 0) < 2 and abs(weight) >= 0.05
        ],
        "skipped_examples": skipped or [],
    }


def build_reward_model_report(
    fixtures: list[dict[str, Any]],
    preferences: list[dict[str, Any]],
    trajectories: list[dict[str, Any]] | None = None,
    *,
    epochs: int = 500,
    learning_rate: float = 0.08,
    l2: float = 0.02,
    include_trajectories: bool = True,
) -> dict[str, Any]:
    examples = build_examples(fixtures, preferences)
    train = [example for example in examples if example.split == "train"]
    holdout = [example for example in examples if example.split == "holdout"]
    weights = train_weights(train, epochs=epochs, learning_rate=learning_rate, l2=l2)
    support = feature_support(train)
    sorted_weights = sorted(weights.items(), key=lambda item: item[1])
    positive_weights = [(name, weight) for name, weight in sorted_weights if weight > 0]
    negative_weights = [(name, weight) for name, weight in sorted_weights if weight < 0]
    comparison = compare_with_current_scorer(examples, weights)
    trajectory_section = None
    if include_trajectories:
        trajectory_examples, skipped = build_trajectory_examples(fixtures, trajectories or [])
        trajectory_section = model_section(
            trajectory_examples,
            epochs=epochs,
            learning_rate=learning_rate,
            l2=l2,
            skipped=skipped,
        )

    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "strict_example_count": len(examples),
        "train_count": len(train),
        "holdout_count": len(holdout),
        "training": {
            "epochs": epochs,
            "learning_rate": learning_rate,
            "l2": l2,
        },
        "train_metrics": evaluate_examples(train, weights),
        "holdout_metrics": evaluate_examples(holdout, weights),
        "all_metrics": evaluate_examples(examples, weights),
        "top_positive_weights": [
            {"feature": name, "weight": weight, "support": support.get(name, 0)}
            for name, weight in positive_weights[-15:][::-1]
        ],
        "top_negative_weights": [
            {"feature": name, "weight": weight, "support": support.get(name, 0)}
            for name, weight in negative_weights[:15]
        ],
        "unstable_low_support_weights": [
            {"feature": name, "weight": weight, "support": support.get(name, 0)}
            for name, weight in sorted_weights
            if support.get(name, 0) < 2 and abs(weight) >= 0.05
        ],
        "trajectory_model": trajectory_section,
        **comparison,
    }


def render_reward_model_report(report: dict[str, Any]) -> str:
    lines = [
        "# Boss AI Offline Preference Model Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Strict pairwise examples: {report['strict_example_count']}",
        f"- Train examples: {report['train_count']}",
        f"- Holdout examples: {report['holdout_count']}",
        f"- Train accuracy: {report['train_metrics']['accuracy_label']}",
        f"- Holdout accuracy: {report['holdout_metrics']['accuracy_label']}",
        "",
        "## Top Positive Features",
        "",
    ]
    for row in report["top_positive_weights"]:
        lines.append(f"- `{row['feature']}`: {row['weight']} (support {row['support']})")
    lines.extend(["", "## Top Negative Features", ""])
    for row in report["top_negative_weights"]:
        lines.append(f"- `{row['feature']}`: {row['weight']} (support {row['support']})")
    lines.extend(["", "## Model Helps Where Current Scorer Misses", ""])
    if report["model_correct_scorer_missed"]:
        for row in report["model_correct_scorer_missed"]:
            lines.append(
                f"- `{row['preference_id']}`: model {row['model_choice']}, "
                f"scorer {row['scorer_choice']}, expected {row['expected']}"
            )
    else:
        lines.append("None in the current strict corpus.")
    lines.extend(["", "## Current Scorer Helps Where Model Misses", ""])
    if report["scorer_correct_model_missed"]:
        for row in report["scorer_correct_model_missed"]:
            lines.append(
                f"- `{row['preference_id']}`: model {row['model_choice']}, "
                f"scorer {row['scorer_choice']}, expected {row['expected']}"
            )
    else:
        lines.append("None in the current strict corpus.")
    lines.extend(["", "## Unstable Low-Support Weights", ""])
    if report["unstable_low_support_weights"]:
        for row in report["unstable_low_support_weights"]:
            lines.append(f"- `{row['feature']}`: {row['weight']} (support {row['support']})")
    else:
        lines.append("No high-magnitude low-support weights.")
    if report.get("trajectory_model") is not None:
        section = report["trajectory_model"]
        lines.extend(
            [
                "",
                "## Trajectory Preference Model",
                "",
                f"- Strict trajectory examples: {section['strict_example_count']}",
                f"- Train examples: {section['train_count']}",
                f"- Holdout examples: {section['holdout_count']}",
                f"- Train accuracy: {section['train_metrics']['accuracy_label']}",
                f"- Holdout accuracy: {section['holdout_metrics']['accuracy_label']}",
                f"- Skipped strict examples: {len(section['skipped_examples'])}",
                "",
                "### Top Plan Features",
                "",
            ]
        )
        top_features = section["top_positive_weights"][:8] + section["top_negative_weights"][:8]
        if top_features:
            for row in top_features:
                lines.append(f"- `{row['feature']}`: {row['weight']} (support {row['support']})")
        else:
            lines.append("No trajectory weights yet.")
    lines.append("")
    return "\n".join(lines)


def write_reward_model_report(
    *,
    fixtures_path: Path = DEFAULT_FIXTURES_PATH,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    trajectories_path: Path = DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    out_path: Path = DEFAULT_REWARD_MODEL_REPORT_PATH,
    json_out_path: Path | None = DEFAULT_REWARD_MODEL_JSON_PATH,
    epochs: int = 500,
    learning_rate: float = 0.08,
    l2: float = 0.02,
    include_trajectories: bool = True,
) -> dict[str, Any]:
    fixtures = load_fixtures(fixtures_path)
    preferences = load_preferences(preferences_path, fixtures=fixtures)
    trajectories = (
        load_trajectory_preferences(trajectories_path, fixtures=fixtures)
        if include_trajectories
        else []
    )
    report = build_reward_model_report(
        fixtures,
        preferences,
        trajectories,
        epochs=epochs,
        learning_rate=learning_rate,
        l2=l2,
        include_trajectories=include_trajectories,
    )
    markdown = render_reward_model_report(report)

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
