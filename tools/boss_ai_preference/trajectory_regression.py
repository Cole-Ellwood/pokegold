from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from tools.boss_ai_debugger.scorer import score_action

from .data import (
    DEFAULT_FIXTURES_PATH,
    PreferenceDataError,
    action_map,
    fixture_map,
    load_fixtures,
)
from .plans import generate_plan_cards
from .trajectory_data import (
    DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    load_trajectory_preferences,
)

STRICT_PAIRWISE_CHOICES = {"a_better", "b_better"}


@dataclass
class TrajectoryVerdict:
    fixture_id: str
    trajectory_a_id: str
    trajectory_b_id: str
    label_choice: str
    scorer_choice: str
    first_move_a: str
    first_move_b: str
    score_a: int
    score_b: int
    same_first_move: bool
    note: str
    agrees: bool
    lesson_type: str


@dataclass
class TrajectoryRegressionResult:
    generated_at: str
    threshold: float
    strict_label_count: int
    strict_agreement_count: int
    skipped: dict[str, int]
    disagreements: list[TrajectoryVerdict]
    tie_first_moves: int
    by_lesson_type: dict[str, dict[str, int]]

    @property
    def agreement_rate(self) -> float:
        if self.strict_label_count == 0:
            return 1.0
        return self.strict_agreement_count / self.strict_label_count

    @property
    def passed(self) -> bool:
        return self.agreement_rate >= self.threshold


def _plans_by_id(fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {plan["id"]: plan for plan in generate_plan_cards(fixture)}


def _first_boss_step(plan: dict[str, Any]) -> dict[str, Any] | None:
    for step in plan.get("steps", []):
        action_id = step.get("action_id")
        if not action_id:
            continue
        actor = step.get("actor")
        if actor in (None, "boss"):
            return step
    return None


def scorer_choice_for_trajectory_pair(
    fixture: dict[str, Any],
    plan_a: dict[str, Any],
    plan_b: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """First-move pairwise grader.

    Returns (choice, detail) where choice is a_better / b_better / tie.
    The Python scorer scores per-action; this grader extracts each plan's
    first boss-actor step and compares those action scores. If both plans
    start with the same action, returns tie (the first-move grader cannot
    discriminate; multi-turn would be required).
    """
    actions = action_map(fixture)
    step_a = _first_boss_step(plan_a)
    step_b = _first_boss_step(plan_b)
    detail: dict[str, Any] = {
        "first_move_a": (step_a or {}).get("action_id") or "",
        "first_move_b": (step_b or {}).get("action_id") or "",
        "score_a": 0,
        "score_b": 0,
        "same_first_move": False,
        "reason": "first-move scorer comparison",
    }
    if step_a is None or step_b is None:
        detail["reason"] = "missing boss-actor step in one or both plans"
        return "tie", detail
    move_a_id = step_a["action_id"]
    move_b_id = step_b["action_id"]
    if move_a_id == move_b_id:
        detail["same_first_move"] = True
        detail["reason"] = "same first-turn action; first-move grader cannot discriminate"
        return "tie", detail
    action_a = actions.get(move_a_id)
    action_b = actions.get(move_b_id)
    if action_a is None or action_b is None:
        missing = move_a_id if action_a is None else move_b_id
        detail["reason"] = f"action {missing!r} not in fixture action list"
        return "tie", detail
    score_a = int(score_action(fixture, action_a)["score"])
    score_b = int(score_action(fixture, action_b)["score"])
    detail["score_a"] = score_a
    detail["score_b"] = score_b
    if score_a == score_b:
        return "tie", detail
    if score_a > score_b:
        return "a_better", detail
    return "b_better", detail


def evaluate_trajectory_label(
    fixture: dict[str, Any],
    label: dict[str, Any],
    plans_cache: dict[str, dict[str, Any]] | None = None,
) -> TrajectoryVerdict:
    plans = plans_cache if plans_cache is not None else _plans_by_id(fixture)
    plan_a_id = label["trajectory_a_id"]
    plan_b_id = label["trajectory_b_id"]
    try:
        plan_a = plans[plan_a_id]
        plan_b = plans[plan_b_id]
    except KeyError as exc:
        raise PreferenceDataError(
            f"fixture {fixture['id']!r}: plan_id {exc.args[0]!r} is not generated for the current fixture"
        ) from exc
    scorer_choice, detail = scorer_choice_for_trajectory_pair(fixture, plan_a, plan_b)
    return TrajectoryVerdict(
        fixture_id=label["fixture_id"],
        trajectory_a_id=plan_a_id,
        trajectory_b_id=plan_b_id,
        label_choice=label["choice"],
        scorer_choice=scorer_choice,
        first_move_a=str(detail["first_move_a"]),
        first_move_b=str(detail["first_move_b"]),
        score_a=int(detail["score_a"]),
        score_b=int(detail["score_b"]),
        same_first_move=bool(detail["same_first_move"]),
        note=str(label.get("note", "")),
        agrees=scorer_choice == label["choice"],
        lesson_type=str(label.get("lesson_type") or "untyped"),
    )


def evaluate_trajectory_corpus(
    fixtures: list[dict[str, Any]],
    trajectory_labels: list[dict[str, Any]],
    threshold: float = 0.8,
) -> TrajectoryRegressionResult:
    fixtures_by_id = fixture_map(fixtures)
    plans_cache_by_fixture: dict[str, dict[str, dict[str, Any]]] = {}
    skipped: Counter[str] = Counter()
    disagreements: list[TrajectoryVerdict] = []
    strict_label_count = 0
    strict_agreement_count = 0
    tie_first_moves = 0
    by_lesson_type: dict[str, Counter[str]] = {}

    for label in trajectory_labels:
        choice = label["choice"]
        if choice not in STRICT_PAIRWISE_CHOICES:
            skipped[choice] += 1
            continue
        fixture_id = label["fixture_id"]
        try:
            fixture = fixtures_by_id[fixture_id]
        except KeyError as exc:
            raise PreferenceDataError(f"unknown fixture_id {fixture_id!r}") from exc
        if fixture_id not in plans_cache_by_fixture:
            plans_cache_by_fixture[fixture_id] = _plans_by_id(fixture)
        verdict = evaluate_trajectory_label(
            fixture, label, plans_cache_by_fixture[fixture_id]
        )
        strict_label_count += 1
        lesson_counter = by_lesson_type.setdefault(verdict.lesson_type, Counter())
        lesson_counter["total"] += 1
        if verdict.same_first_move:
            tie_first_moves += 1
        if verdict.agrees:
            strict_agreement_count += 1
            lesson_counter["agree"] += 1
        else:
            disagreements.append(verdict)

    summary_by_lesson = {
        lt: {
            "total": int(counter.get("total", 0)),
            "agree": int(counter.get("agree", 0)),
        }
        for lt, counter in sorted(by_lesson_type.items())
    }

    return TrajectoryRegressionResult(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        threshold=threshold,
        strict_label_count=strict_label_count,
        strict_agreement_count=strict_agreement_count,
        skipped=dict(sorted(skipped.items())),
        disagreements=disagreements,
        tie_first_moves=tie_first_moves,
        by_lesson_type=summary_by_lesson,
    )


def run_trajectory_regression(
    fixtures_path: Any = DEFAULT_FIXTURES_PATH,
    trajectories_path: Any = DEFAULT_TRAJECTORY_PREFERENCES_PATH,
    threshold: float = 0.8,
) -> TrajectoryRegressionResult:
    fixtures = load_fixtures(fixtures_path)
    trajectories = load_trajectory_preferences(trajectories_path)
    return evaluate_trajectory_corpus(fixtures, trajectories, threshold=threshold)


def format_result(result: TrajectoryRegressionResult) -> str:
    lines = [
        f"Trajectory preference regression: "
        f"{result.strict_agreement_count} / {result.strict_label_count} strict pairwise labels agree "
        f"({result.agreement_rate * 100:.1f}%)",
        f"  PASS threshold: {result.threshold:.2f}",
        f"  Grader: first-move scorer comparison (tie when both plans share turn-1 action)",
        f"  Ties from shared first move: {result.tie_first_moves}",
    ]
    if result.skipped:
        parts = " ".join(f"{k}={v}" for k, v in sorted(result.skipped.items()))
        lines.append(f"  Skipped {sum(result.skipped.values())} non-strict labels ({parts})")
    if result.by_lesson_type:
        lines.append("  By lesson type:")
        for lt, stats in result.by_lesson_type.items():
            total = stats.get("total", 0)
            agree = stats.get("agree", 0)
            rate = (agree / total * 100) if total else 0.0
            lines.append(f"    {lt}: {agree}/{total} ({rate:.1f}%)")
    lines.append("")
    if result.disagreements:
        lines.append(f"Disagreements ({len(result.disagreements)}):")
        for v in result.disagreements[:50]:
            tie_marker = " [SAME_TURN1]" if v.same_first_move else ""
            lines.append(
                f"  {v.fixture_id}: label={v.label_choice} scorer={v.scorer_choice}{tie_marker} "
                f"lesson={v.lesson_type}"
            )
            lines.append(
                f"    A first-move: {v.first_move_a} (score {v.score_a}) | "
                f"B first-move: {v.first_move_b} (score {v.score_b})"
            )
            if v.note:
                lines.append(f"    note: {v.note[:140]}")
    else:
        lines.append("Disagreements: none")
    return "\n".join(lines)
