from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError

from .rom_scenarios import evaluate_scenario, load_scenario_batch


HAZARD_POLICY_TAGS = {"hazard_retention", "rapid_spin", "spikes"}
NEAR_TIE_SCORE_GAP = 3
DEFAULT_ROUTE_HORIZON = 3
MIN_ROUTE_HORIZON = 2
MAX_ROUTE_HORIZON = 5
MULTI_TURN_FACTORS = (
    "hazards",
    "spin",
    "phazing",
    "sleep",
    "recovery",
    "self_ko",
    "ace_preservation",
)


def evaluate_route_path(
    path: Path,
    *,
    scenario_id: str | None = None,
    horizon: int = DEFAULT_ROUTE_HORIZON,
) -> dict[str, Any]:
    scenarios = load_scenario_batch(path)
    if scenario_id is not None:
        return evaluate_route_scenario(
            choose_scenario(scenarios, scenario_id),
            horizon=horizon,
        )
    if len(scenarios) == 1:
        return evaluate_route_scenario(scenarios[0], horizon=horizon)
    return evaluate_route_batch(scenarios, source=str(path), horizon=horizon)


def evaluate_route_batch(
    scenarios: list[dict[str, Any]],
    *,
    source: str = "inline",
    horizon: int = DEFAULT_ROUTE_HORIZON,
) -> dict[str, Any]:
    items = [evaluate_route_scenario(scenario, horizon=horizon) for scenario in scenarios]
    counts: dict[str, int] = {}
    observed_factors: set[str] = set()
    for item in items:
        key = str(item["classification"])
        counts[key] = counts.get(key, 0) + 1
        observed_factors.update(item["multi_turn_route"]["observed_factors"])
    return {
        "schema_version": 1,
        "source": source,
        "scenario_count": len(items),
        "multi_turn_summary": {
            "horizon": clamp_horizon(horizon),
            "implemented_factors": list(MULTI_TURN_FACTORS),
            "observed_factors": sorted(observed_factors),
        },
        "classification_counts": dict(sorted(counts.items())),
        "items": items,
    }


def evaluate_route_scenario(
    scenario: dict[str, Any],
    *,
    horizon: int = DEFAULT_ROUTE_HORIZON,
) -> dict[str, Any]:
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
        "multi_turn_route": evaluate_multi_turn_route(
            scenario,
            verdict.result,
            verdict.condition_tags,
            horizon=horizon,
        ),
        "reasons": reasons,
        "why": verdict.why,
    }


def evaluate_multi_turn_route(
    scenario: dict[str, Any],
    result: dict[str, Any],
    condition_tags: list[str],
    *,
    horizon: int,
) -> dict[str, Any]:
    bounded_horizon = clamp_horizon(horizon)
    state = initial_route_state(condition_tags)
    lines = []
    observed_factors: set[str] = set()
    for move in result.get("moves", []):
        if move.get("blocked"):
            continue
        line = project_action_line(move, state, bounded_horizon)
        observed_factors.update(line["factors"])
        lines.append(line)
    lines.sort(
        key=lambda item: (
            -int(item["route_value"]),
            int(item["final_score"]),
            str(item["action_id"]),
        )
    )
    best = lines[0] if lines else None
    return {
        "horizon": bounded_horizon,
        "implemented_factors": list(MULTI_TURN_FACTORS),
        "observed_factors": sorted(observed_factors),
        "state": state,
        "line_count": len(lines),
        "best_action_id": best["action_id"] if best else None,
        "best_route_value": best["route_value"] if best else None,
        "lines": lines,
    }


def project_action_line(
    move: dict[str, Any],
    state: dict[str, Any],
    horizon: int,
) -> dict[str, Any]:
    traits = action_traits(move)
    final_score = int(move.get("final_score", move.get("pre_lookahead_score", 80)))
    score_value = max(0, 80 - final_score)
    factors: list[str] = []
    reasons: list[str] = []
    route_value = score_value
    terminal = False

    if "hazards" in traits:
        factors.append("hazards")
        if state["spikes_layers"] >= 3:
            route_value -= 24
            reasons.append("extra Spikes turns are capped at three layers")
        else:
            value = 8 + (2 * min(horizon, 3))
            route_value += value
            reasons.append(f"hazard layer can pay over {horizon} turn(s)")
        if state["spinner_risk"] and not state["spinblocked"]:
            route_value -= 18
            factors.append("spin")
            reasons.append("public Spin line can erase hazard progress")
        elif state["spinner_risk"] and state["spinblocked"]:
            route_value += 8
            factors.append("spin")
            reasons.append("spinblock makes hazard progress stickier")

    if "spin" in traits:
        factors.append("spin")
        if state["spikes_layers"] > 0:
            route_value += 14
            reasons.append("Spin converts immediately against existing hazards")
        else:
            route_value -= 4
            reasons.append("Spin has low route value without hazards to clear")

    if "phazing" in traits:
        factors.append("phazing")
        value = 10 if state["tempo_pressure"] else 6
        route_value += value
        reasons.append("phazing can reset setup or force hazard damage")

    if "sleep" in traits:
        factors.append("sleep")
        if state["sleep_absorber"]:
            route_value -= 8
            reasons.append("sleep absorber or sleep-clause state can blank the line")
        else:
            route_value += 12
            reasons.append("sleep can buy multiple future route turns")

    if "recovery" in traits:
        factors.append("recovery")
        if state["tempo_pressure"]:
            route_value -= 7
            reasons.append("recovery under immediate pressure can lose the board")
        else:
            route_value += 9
            reasons.append("recovery preserves a future route resource")

    if "self_ko" in traits:
        factors.append("self_ko")
        terminal = True
        if state["named_converter"]:
            route_value += 16
            reasons.append("self-KO cashes out into a named converter")
        else:
            route_value -= 16
            reasons.append("self-KO ends the route without a named converter")

    if "ace_preservation" in traits or state["ace_preservation"]:
        factors.append("ace_preservation")
        if "self_ko" in traits:
            route_value -= 12
            reasons.append("ace preservation conflicts with self-KO")
        else:
            route_value += 7
            reasons.append("line preserves a future ace/resource")

    if not factors:
        reasons.append("ordinary continuation uses score value plus generic future branch")

    children = [] if terminal else continuation_branches(traits, state, horizon)
    route_value += sum(int(child["route_value_delta"]) for child in children)
    return {
        "action_id": str(move.get("action_id", "")),
        "slot": int(move.get("slot", 0)),
        "final_score": final_score,
        "route_value": route_value,
        "factors": sorted(set(factors)),
        "terminal": terminal,
        "reasons": reasons,
        "branches": children,
    }


def continuation_branches(
    traits: set[str],
    state: dict[str, Any],
    horizon: int,
) -> list[dict[str, Any]]:
    if horizon <= 1:
        return []
    branches: list[dict[str, Any]] = []
    if "hazards" in traits and state["spinner_risk"]:
        branches.append(
            branch(
                "spin_window",
                8 if state["spinblocked"] else -12,
                "next turn tests whether hazards survive Rapid Spin pressure",
            )
        )
    if "phazing" in traits:
        branches.append(
            branch(
                "forced_switch",
                5,
                "forced switch can compound hazard and matchup value",
            )
        )
    if "sleep" in traits and not state["sleep_absorber"]:
        branches.append(
            branch("sleep_turn", 6, "sleep creates a future free-turn branch")
        )
    if "recovery" in traits:
        branches.append(
            branch("resource_preserved", 4, "recovered HP remains useful later")
        )
    if not branches:
        branches.append(
            branch("position_continuation", 1, "line keeps a generic future branch")
        )
    return branches


def branch(branch_id: str, route_value_delta: int, reason: str) -> dict[str, Any]:
    return {
        "branch_id": branch_id,
        "route_value_delta": route_value_delta,
        "reason": reason,
    }


def action_traits(move: dict[str, Any]) -> set[str]:
    parts = [
        str(move.get("action_id", "")),
        str(move.get("name", "")),
    ]
    for event in move.get("events", []):
        if isinstance(event, dict):
            parts.append(str(event.get("rule", "")))
    text = " ".join(parts).lower().replace("-", "_")
    traits = set()
    if "spikes" in text or "hazard" in text:
        traits.add("hazards")
    if "rapid_spin" in text or ("spin" in text and "spikes" not in text):
        traits.add("spin")
    if any(token in text for token in ("phaz", "roar", "whirlwind", "force_switch")):
        traits.add("phazing")
    if any(token in text for token in ("sleep", "hypnosis", "spore")):
        traits.add("sleep")
    if any(token in text for token in ("recover", "recovery", "rest", "synthesis")):
        traits.add("recovery")
    if any(token in text for token in ("self_ko", "selfdestruct", "explosion", "cashout")):
        traits.add("self_ko")
    if any(token in text for token in ("ace", "preserve", "preservation")):
        traits.add("ace_preservation")
    return traits


def initial_route_state(condition_tags: list[str]) -> dict[str, Any]:
    conditions = set(condition_tags)
    spinblocked = (
        "active_ghost_spinblock" in conditions
        and "foresight_identified_ghost" not in conditions
    ) or "reserve_ghost_available" in conditions
    return {
        "spikes_layers": spikes_layers_from_conditions(conditions),
        "spinner_risk": bool(
            {
                "active_revealed_rapid_spin",
                "bench_revealed_rapid_spin",
                "active_species_spin_prior",
            }
            & conditions
        ),
        "spinblocked": spinblocked,
        "tempo_pressure": "immediate_pressure" in conditions,
        "sleep_absorber": "sleep_clause_value_preserved" in conditions,
        "named_converter": bool(
            {
                "one_time_trade_named_converter",
                "support_job_completed",
                "route_trade",
            }
            & conditions
        ),
        "ace_preservation": bool(
            {"ace_preservation", "wincon_preservation", "support_job_completed"}
            & conditions
        ),
    }


def spikes_layers_from_conditions(conditions: set[str]) -> int:
    for tag in conditions:
        prefix = "spikes_layers_"
        if tag.startswith(prefix):
            try:
                return max(0, min(3, int(tag[len(prefix) :])))
            except ValueError:
                return 0
    return 0


def clamp_horizon(horizon: int) -> int:
    return max(MIN_ROUTE_HORIZON, min(MAX_ROUTE_HORIZON, int(horizon)))


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
        (
            "multi-turn: "
            f"horizon={report['multi_turn_summary']['horizon']} "
            f"implemented={','.join(report['multi_turn_summary']['implemented_factors'])} "
            f"observed={','.join(report['multi_turn_summary']['observed_factors']) or 'none'}"
        ),
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
            f"best={','.join(item['expected_best_action_ids']) or 'none'} "
            f"multi={item['multi_turn_route']['best_action_id']}"
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
        (
            "multi-turn: "
            f"horizon={item['multi_turn_route']['horizon']} "
            f"best={item['multi_turn_route']['best_action_id']} "
            f"value={item['multi_turn_route']['best_route_value']}"
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
