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
    cumulative_score_a: int = 0
    cumulative_score_b: int = 0
    resolved_by: str = "first_move"


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
    cumulative_resolved: int = 0

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


def _boss_action_ids(plan: dict[str, Any]) -> list[str]:
    """All boss-actor action_ids in the plan, in turn order."""
    ids: list[str] = []
    for step in plan.get("steps", []):
        action_id = step.get("action_id")
        if not action_id:
            continue
        actor = step.get("actor")
        if actor in (None, "boss"):
            ids.append(str(action_id))
    return ids


def _plan_cumulative_score(
    fixture: dict[str, Any],
    actions: dict[str, dict[str, Any]],
    boss_action_ids: list[str],
) -> int | None:
    """Sum scorer scores for each boss action against the current fixture state.

    Returns None if any action_id is not in the fixture's action list (cannot
    score). This is a static approximation: state evolution (HP, status, party
    changes between turns) is NOT modeled. The signal is whether the plan's
    sequence of boss actions is collectively sensible by the per-action scorer,
    not a true multi-turn rollout. Used as a tiebreaker when both plans share
    their turn-1 action.
    """
    total = 0
    for action_id in boss_action_ids:
        action = actions.get(action_id)
        if action is None:
            return None
        total += int(score_action(fixture, action)["score"])
    return total


def scorer_choice_for_trajectory_pair(
    fixture: dict[str, Any],
    plan_a: dict[str, Any],
    plan_b: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Pairwise grader with first-move + cumulative-fallback.

    Returns (choice, detail) where choice is a_better / b_better / tie.
    Stage 1: extract each plan's first boss-actor step and compare via
    score_action. If they differ, the better-first-move plan wins.
    Stage 2 (tiebreaker when both plans share turn-1 action OR when turn-1
    scores tie): sum scorer scores across each plan's full boss-action
    sequence under the same fixture state. Static approximation - does not
    simulate state evolution between turns - but it discriminates plans that
    differ only at turn 2+ (e.g. "sleep then attack" vs "sleep then setup").
    """
    actions = action_map(fixture)
    step_a = _first_boss_step(plan_a)
    step_b = _first_boss_step(plan_b)
    boss_actions_a = _boss_action_ids(plan_a)
    boss_actions_b = _boss_action_ids(plan_b)
    detail: dict[str, Any] = {
        "first_move_a": (step_a or {}).get("action_id") or "",
        "first_move_b": (step_b or {}).get("action_id") or "",
        "score_a": 0,
        "score_b": 0,
        "cumulative_score_a": 0,
        "cumulative_score_b": 0,
        "boss_actions_a": boss_actions_a,
        "boss_actions_b": boss_actions_b,
        "same_first_move": False,
        "resolved_by": "first_move",
        "reason": "first-move scorer comparison",
    }
    if step_a is None or step_b is None:
        detail["reason"] = "missing boss-actor step in one or both plans"
        return "tie", detail
    move_a_id = step_a["action_id"]
    move_b_id = step_b["action_id"]
    same_first_move = move_a_id == move_b_id
    detail["same_first_move"] = same_first_move
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
    if not same_first_move and score_a != score_b:
        if score_a > score_b:
            return "a_better", detail
        return "b_better", detail

    # Tiebreaker: same first move OR equal first-move scores. Fall back to
    # cumulative scoring over each plan's full boss-action sequence.
    cumulative_a = _plan_cumulative_score(fixture, actions, boss_actions_a)
    cumulative_b = _plan_cumulative_score(fixture, actions, boss_actions_b)
    if cumulative_a is None or cumulative_b is None:
        detail["reason"] = (
            "same first-turn action and cumulative scoring failed (action_id outside fixture)"
            if same_first_move
            else "first-turn scores tied and cumulative scoring failed (action_id outside fixture)"
        )
        return "tie", detail
    detail["cumulative_score_a"] = cumulative_a
    detail["cumulative_score_b"] = cumulative_b
    detail["resolved_by"] = "cumulative_boss_actions"
    detail["reason"] = (
        "cumulative boss-action scoring (turn-1 tied or shared)"
    )
    if cumulative_a == cumulative_b:
        return "tie", detail
    if cumulative_a > cumulative_b:
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
        cumulative_score_a=int(detail.get("cumulative_score_a", 0)),
        cumulative_score_b=int(detail.get("cumulative_score_b", 0)),
        resolved_by=str(detail.get("resolved_by", "first_move")),
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
    cumulative_resolved = 0
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
        if verdict.resolved_by == "cumulative_boss_actions":
            cumulative_resolved += 1
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
        cumulative_resolved=cumulative_resolved,
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
        f"  Grader: first-move scorer comparison; cumulative boss-action tiebreaker",
        f"  Plans with shared first-turn action: {result.tie_first_moves}",
        f"  Resolved by cumulative tiebreaker: {result.cumulative_resolved}",
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
            resolved = f" via_{v.resolved_by}"
            lines.append(
                f"  {v.fixture_id}: label={v.label_choice} scorer={v.scorer_choice}{tie_marker}{resolved} "
                f"lesson={v.lesson_type}"
            )
            lines.append(
                f"    A first-move: {v.first_move_a} (score {v.score_a}) | "
                f"B first-move: {v.first_move_b} (score {v.score_b})"
            )
            if v.resolved_by == "cumulative_boss_actions":
                lines.append(
                    f"    cumulative: A={v.cumulative_score_a} B={v.cumulative_score_b}"
                )
            if v.note:
                lines.append(f"    note: {v.note[:140]}")
    else:
        lines.append("Disagreements: none")
    return "\n".join(lines)
