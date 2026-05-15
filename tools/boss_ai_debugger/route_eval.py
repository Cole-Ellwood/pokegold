from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError

from .rom_scenarios import evaluate_scenario, load_scenario_batch


HAZARD_POLICY_TAGS = {"hazard_retention", "rapid_spin", "spikes"}
NEAR_TIE_SCORE_GAP = 3


def evaluate_route_path(
    path: Path,
    *,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    scenarios = load_scenario_batch(path)
    if scenario_id is not None:
        return evaluate_route_scenario(choose_scenario(scenarios, scenario_id))
    if len(scenarios) == 1:
        return evaluate_route_scenario(scenarios[0])
    return evaluate_route_batch(scenarios, source=str(path))


def evaluate_route_batch(
    scenarios: list[dict[str, Any]],
    *,
    source: str = "inline",
) -> dict[str, Any]:
    items = [evaluate_route_scenario(scenario) for scenario in scenarios]
    counts: dict[str, int] = {}
    for item in items:
        key = str(item["classification"])
        counts[key] = counts.get(key, 0) + 1
    return {
        "schema_version": 1,
        "source": source,
        "scenario_count": len(items),
        "classification_counts": dict(sorted(counts.items())),
        "items": items,
    }


def evaluate_route_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    verdict = evaluate_scenario(scenario)
    score_gap = expected_best_score_gap(verdict.result, verdict.expected_best_action_ids)
    near_tie = score_gap is not None and score_gap <= NEAR_TIE_SCORE_GAP
    family_tags = route_family_tags(
        verdict.policy_tags,
        verdict.condition_tags,
        verdict.lesson_type,
    )
    classification, route_bucket, confidence, reasons = classify_verdict(
        verdict=verdict.verdict,
        lesson_type=verdict.lesson_type,
        has_answer_changing_info=bool(verdict.answer_changing_information),
        near_tie=near_tie,
        rolled_bad=bool(verdict.rolled_bad_action_ids),
        rolled_catastrophic=bool(verdict.rolled_catastrophic_action_ids),
    )
    return {
        "schema_version": 1,
        "scenario_id": verdict.scenario_id,
        "classification": classification,
        "route_bucket": route_bucket,
        "confidence": confidence,
        "route_family_tags": family_tags,
        "near_tie": near_tie,
        "expected_best_score_gap": score_gap,
        "verdict": verdict.verdict,
        "severity": verdict.severity,
        "rom_best_action_id": verdict.rom_best_action_id,
        "rom_best_probability": verdict.rom_best_probability,
        "expected_best_action_ids": verdict.expected_best_action_ids,
        "expected_acceptable_action_ids": verdict.expected_acceptable_action_ids,
        "rolled_bad_action_ids": verdict.rolled_bad_action_ids,
        "rolled_catastrophic_action_ids": verdict.rolled_catastrophic_action_ids,
        "zero_probability_best_action_ids": verdict.zero_probability_best_action_ids,
        "policy_tags": verdict.policy_tags,
        "condition_tags": verdict.condition_tags,
        "lesson_type": verdict.lesson_type,
        "evidence_refs": verdict.evidence_refs,
        "answer_changing_information": verdict.answer_changing_information,
        "reasons": reasons,
        "why": verdict.why,
    }


def classify_verdict(
    *,
    verdict: str,
    lesson_type: str,
    has_answer_changing_info: bool,
    near_tie: bool,
    rolled_bad: bool,
    rolled_catastrophic: bool,
) -> tuple[str, str, str, list[str]]:
    reasons = [f"one-turn verdict is {verdict}"]
    if verdict == "pass":
        return (
            "route_pass",
            "pass",
            "high",
            [*reasons, "expected route is top and clears the probability floor"],
        )

    if verdict == "needs_expectation":
        return (
            "route_missing_expectation",
            "needs_context",
            "high",
            [*reasons, "scenario has no expected route labels"],
        )

    if verdict == "no_rom_choice":
        return (
            "route_no_legal_choice",
            "actually_bad",
            "high",
            [*reasons, "ROM selector has no legal route below blocked score"],
        )

    if verdict == "catastrophic_roll" or rolled_catastrophic:
        return (
            "route_catastrophic",
            "actually_bad",
            "high",
            [*reasons, "ROM can choose a route marked catastrophic"],
        )

    if verdict == "bad_roll" or rolled_bad:
        return (
            "route_bad_roll",
            "actually_bad",
            "high",
            [*reasons, "ROM can choose a route marked bad"],
        )

    if verdict == "best_never_rolled":
        return (
            "route_expected_unreachable",
            "actually_bad",
            "high",
            [*reasons, "expected route has zero selector probability"],
        )

    if verdict == "partial_best_unrolled":
        bucket = "acceptable_near_tie" if near_tie else "needs_context"
        confidence = "medium" if near_tie else "high"
        return (
            "route_partial_unreachable",
            bucket,
            confidence,
            [*reasons, "some expected-best routes have zero selector probability"],
        )

    if verdict == "acceptable_top":
        bucket = "acceptable_near_tie" if near_tie else "needs_context"
        reason = (
            "acceptable top route is within the near-tie score gap"
            if near_tie
            else "acceptable top route still needs longer route review"
        )
        return (
            "route_acceptable_but_review",
            bucket,
            "medium",
            [*reasons, reason],
        )

    if verdict == "weak_best":
        bucket = "acceptable_near_tie" if near_tie else "needs_context"
        return (
            "route_weak_best",
            bucket,
            "medium",
            [*reasons, "expected route is top but below its probability floor"],
        )

    if verdict == "mismatch":
        if near_tie:
            return (
                "route_wrong_top",
                "acceptable_near_tie",
                "medium",
                [*reasons, "expected route is within the near-tie score gap"],
            )
        if has_answer_changing_info and lesson_type != "hard_rule":
            return (
                "route_wrong_top",
                "needs_context",
                "medium",
                [*reasons, "answer-changing fields say route context can change the call"],
            )
        return (
            "route_wrong_top",
            "actually_bad",
            "medium",
            [*reasons, "ROM top route is outside expected best and acceptable sets"],
        )

    return (
        "route_wrong_top",
        "needs_context",
        "low",
        [*reasons, "unrecognized verdict; keep it reviewable"],
    )


def expected_best_score_gap(
    result: dict[str, Any],
    expected_best_ids: list[str],
) -> int | None:
    if not result.get("ready") or not expected_best_ids:
        return None
    best_score = result.get("best_score")
    if best_score is None:
        return None
    score_by_action = {
        str(move["action_id"]): int(move["final_score"])
        for move in result.get("moves", [])
    }
    expected_scores = [
        score_by_action[action_id]
        for action_id in expected_best_ids
        if action_id in score_by_action
    ]
    if not expected_scores:
        return None
    return min(expected_scores) - int(best_score)


def route_family_tags(
    policy_tags: list[str],
    condition_tags: list[str],
    lesson_type: str,
) -> list[str]:
    tags = set(policy_tags)
    conditions = set(condition_tags)
    result: list[str] = []
    if "selector_surface" in tags:
        result.append("selector_surface")
    if tags & HAZARD_POLICY_TAGS:
        result.append("hazard_route")
    if "spikes_layers_3" in conditions:
        result.append("spikes_capped")
    if "active_revealed_rapid_spin" in conditions:
        result.append("active_spinner_risk")
    if (
        "active_ghost_spinblock" in conditions
        and "foresight_identified_ghost" not in conditions
    ):
        result.append("spinblocked")
    if {"active_ghost_spinblock", "foresight_identified_ghost"} <= conditions:
        result.append("foresight_breaks_spinblock")
    if "immediate_pressure" in conditions:
        result.append("tempo_pressure")
    if lesson_type:
        result.append(str(lesson_type))
    return result


def choose_scenario(
    scenarios: list[dict[str, Any]],
    scenario_id: str,
) -> dict[str, Any]:
    for scenario in scenarios:
        if scenario.get("id") == scenario_id or scenario.get("scenario_id") == scenario_id:
            return scenario
    raise PreferenceDataError(f"scenario id {scenario_id!r} not found")


def format_route_eval_report(report: dict[str, Any]) -> str:
    if "items" not in report:
        return format_route_eval_item(report)
    counts = " ".join(
        f"{name}={count}" for name, count in report["classification_counts"].items()
    )
    lines = [
        "Boss AI route evaluation",
        f"source={report['source']} scenarios={report['scenario_count']}",
        f"classifications: {counts or 'none'}",
        "",
        "Top route-context items:",
    ]
    review_items = [
        item for item in report["items"] if item["classification"] != "route_pass"
    ][:20]
    if not review_items:
        lines.append("  none")
        return "\n".join(lines)
    for item in review_items:
        probability = float(item["rom_best_probability"])
        lines.append(
            f"  {item['classification']} {item['scenario_id']} "
            f"verdict={item['verdict']} rom={item['rom_best_action_id']}({probability:.1%}) "
            f"best={','.join(item['expected_best_action_ids']) or 'none'}"
        )
        lines.append(f"      {'; '.join(item['reasons'])}")
    return "\n".join(lines)


def format_route_eval_item(item: dict[str, Any]) -> str:
    lines = [
        "Boss AI route evaluation",
        (
            f"{item['scenario_id']} classification={item['classification']} "
            f"bucket={item['route_bucket']} confidence={item['confidence']} "
            f"verdict={item['verdict']}"
        ),
        (
            f"rom={item['rom_best_action_id']}({item['rom_best_probability']:.1%}) "
            f"best={','.join(item['expected_best_action_ids']) or 'none'} "
            f"gap={item['expected_best_score_gap']}"
        ),
        "reasons:",
    ]
    for reason in item["reasons"]:
        lines.append(f"  - {reason}")
    if item["route_family_tags"]:
        lines.append("route tags:")
        for cue in item["route_family_tags"][:8]:
            lines.append(f"  - {cue}")
    if item["answer_changing_information"]:
        lines.append("changes answer if:")
        for cue in item["answer_changing_information"][:8]:
            lines.append(f"  - {cue}")
    return "\n".join(lines)


def write_route_eval_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
