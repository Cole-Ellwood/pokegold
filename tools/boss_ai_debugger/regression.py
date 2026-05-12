from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from tools.boss_ai_preference.data import PreferenceDataError, action_map, fixture_map
from tools.boss_ai_preference.damage_estimates import attach_damage_estimates

from .scorer import score_action


ScoreAction = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]

STRICT_CHOICES = {"a_better", "b_better"}


@dataclass(frozen=True)
class LabelVerdict:
    fixture_id: str
    action_a_id: str
    action_b_id: str
    label_choice: str
    scorer_choice: str
    scorer_scores: dict[str, int]
    label_note: str
    agrees: bool

    def to_json(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "action_a_id": self.action_a_id,
            "action_b_id": self.action_b_id,
            "label_choice": self.label_choice,
            "scorer_choice": self.scorer_choice,
            "scorer_scores": self.scorer_scores,
            "label_note": self.label_note,
        }


@dataclass(frozen=True)
class RegressionResult:
    generated_at: str
    threshold: float
    strict_label_count: int
    strict_agreement_count: int
    skipped: dict[str, int]
    disagreements: list[LabelVerdict]
    rank_metrics: dict[str, Any] | None = None

    @property
    def agreement_rate(self) -> float:
        if self.strict_label_count == 0:
            return 1.0
        return self.strict_agreement_count / self.strict_label_count

    @property
    def passed(self) -> bool:
        return self.agreement_rate >= self.threshold


def evaluate_label(
    fixture: dict[str, Any],
    label: dict[str, Any],
    scorer: ScoreAction = score_action,
) -> LabelVerdict:
    actions_by_id = action_map(fixture)
    action_a_id = label["action_a_id"]
    action_b_id = label["action_b_id"]
    try:
        action_a = actions_by_id[action_a_id]
        action_b = actions_by_id[action_b_id]
    except KeyError as exc:
        missing = exc.args[0]
        raise PreferenceDataError(
            f"fixture {fixture['id']!r}: action_id {missing!r} is not in fixture"
        ) from exc

    score_a = int(scorer(fixture, action_a)["score"])
    score_b = int(scorer(fixture, action_b)["score"])
    if score_a == score_b:
        scorer_choice = "tie"
    elif score_a > score_b:
        scorer_choice = "a_better"
    else:
        scorer_choice = "b_better"

    label_choice = label["choice"]
    return LabelVerdict(
        fixture_id=label["fixture_id"],
        action_a_id=action_a_id,
        action_b_id=action_b_id,
        label_choice=label_choice,
        scorer_choice=scorer_choice,
        scorer_scores={action_a_id: score_a, action_b_id: score_b},
        label_note=str(label.get("note", "")),
        agrees=scorer_choice == label_choice,
    )


def evaluate_corpus(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    threshold: float,
    scorer: ScoreAction = score_action,
    rank_labels: list[dict[str, Any]] | None = None,
) -> RegressionResult:
    fixtures = attach_damage_estimates(fixtures)
    fixtures_by_id = fixture_map(fixtures)
    skipped: Counter[str] = Counter()
    disagreements: list[LabelVerdict] = []
    strict_label_count = 0
    strict_agreement_count = 0

    for label in labels:
        choice = label["choice"]
        if choice not in STRICT_CHOICES:
            skipped[choice] += 1
            continue

        fixture_id = label["fixture_id"]
        try:
            fixture = fixtures_by_id[fixture_id]
        except KeyError as exc:
            raise PreferenceDataError(f"unknown fixture_id {fixture_id!r}") from exc

        strict_label_count += 1
        verdict = evaluate_label(fixture, label, scorer)
        if verdict.agrees:
            strict_agreement_count += 1
        else:
            disagreements.append(verdict)

    rank_metrics = None
    if rank_labels is not None:
        rank_metrics = evaluate_rank_labels(fixtures, rank_labels, scorer)

    return RegressionResult(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        threshold=threshold,
        strict_label_count=strict_label_count,
        strict_agreement_count=strict_agreement_count,
        skipped=dict(sorted(skipped.items())),
        disagreements=disagreements,
        rank_metrics=rank_metrics,
    )


def evaluate_rank_labels(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    scorer: ScoreAction = score_action,
) -> dict[str, Any]:
    fixtures_by_id = fixture_map(fixtures)
    labels_by_fixture: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for label in labels:
        if label.get("rank") is not None:
            labels_by_fixture[label["fixture_id"]].append(label)

    mismatches: list[dict[str, Any]] = []
    label_count = 0
    for fixture_id, fixture_labels in sorted(labels_by_fixture.items()):
        fixture = fixtures_by_id.get(fixture_id)
        if fixture is None:
            raise PreferenceDataError(f"unknown fixture_id {fixture_id!r}")

        scored_actions = [
            {
                "action_id": action["id"],
                "score": int(scorer(fixture, action)["score"]),
            }
            for action in fixture["actions"]
        ]
        scored_actions.sort(key=lambda item: (-item["score"], item["action_id"]))
        scorer_positions = {
            item["action_id"]: position
            for position, item in enumerate(scored_actions, start=1)
        }

        for label in fixture_labels:
            label_count += 1
            action_id = label["action_id"]
            scorer_position = scorer_positions.get(action_id)
            if scorer_position is None:
                raise PreferenceDataError(
                    f"fixture {fixture_id!r}: action_id {action_id!r} is not in fixture"
                )
            label_rank = int(label["rank"])
            if scorer_position == label_rank:
                continue
            mismatches.append(
                {
                    "fixture_id": fixture_id,
                    "action_id": action_id,
                    "label_rank": label_rank,
                    "scorer_rank": scorer_position,
                }
            )

    return {
        "label_count": label_count,
        "position_mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def format_summary(result: RegressionResult, *, quiet: bool = False) -> str:
    lines = [
        "Boss AI preference regression: "
        f"{result.strict_agreement_count} / {result.strict_label_count} "
        f"strict pairwise labels agree ({result.agreement_rate:.1%})",
        f"  PASS threshold: {result.threshold:.2f}",
    ]
    skipped_total = sum(result.skipped.values())
    if result.skipped:
        skipped_counts = " ".join(
            f"{choice}={count}" for choice, count in result.skipped.items()
        )
        lines.append(
            f"  Skipped {skipped_total} non-strict labels ({skipped_counts})"
        )
    else:
        lines.append("  Skipped 0 non-strict labels")

    if result.rank_metrics is not None:
        lines.append(
            "  Rank labels: "
            f"{result.rank_metrics['position_mismatch_count']} / "
            f"{result.rank_metrics['label_count']} position mismatches"
        )

    if not result.disagreements:
        lines.extend(["", "Disagreements: none"])
        return "\n".join(lines)

    lines.extend(["", "Disagreements:"])
    if quiet:
        lines.append(f"  {len(result.disagreements)} disagreement(s)")
        return "\n".join(lines)

    for verdict in result.disagreements:
        score_a = verdict.scorer_scores[verdict.action_a_id]
        score_b = verdict.scorer_scores[verdict.action_b_id]
        preferred_id = (
            verdict.action_a_id
            if verdict.label_choice == "a_better"
            else verdict.action_b_id
        )
        other_id = (
            verdict.action_b_id
            if verdict.label_choice == "a_better"
            else verdict.action_a_id
        )
        lines.extend(
            [
                f"  {verdict.fixture_id}",
                "    label: "
                f"{verdict.label_choice} "
                f"({preferred_id} > {other_id})",
                "    scorer: "
                f"{verdict.action_a_id}={score_a} "
                f"{verdict.action_b_id}={score_b} -> {verdict.scorer_choice}",
            ]
        )
        if verdict.label_note:
            lines.append(f"    note: {json.dumps(verdict.label_note)}")
    return "\n".join(lines)


def format_json(result: RegressionResult) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": result.generated_at,
        "threshold": result.threshold,
        "strict_label_count": result.strict_label_count,
        "strict_agreement_count": result.strict_agreement_count,
        "agreement_rate": result.agreement_rate,
        "skipped": result.skipped,
        "disagreements": [item.to_json() for item in result.disagreements],
    }
    if result.rank_metrics is not None:
        report["rank_metrics"] = result.rank_metrics
    return report


def write_json_report(result: RegressionResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(format_json(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def exit_code_for_result(result: RegressionResult) -> int:
    return 0 if result.passed else 1
