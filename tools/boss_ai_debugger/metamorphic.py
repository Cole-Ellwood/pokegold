from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .generators import generate_scenarios
from .rom_scenarios import evaluate_scenario, select_move


@dataclass(frozen=True)
class MetamorphicResult:
    relation: str
    passed: bool
    reason: str
    scenario_id: str
    details: dict[str, Any]


def run_metamorphic_suite(*, generated: int = 0, seed: int = 1) -> dict[str, Any]:
    results = [
        relation_equal_scores_roll_first_two(),
        relation_blocked_scores_have_zero_probability(),
        relation_third_slot_tied_second_never_rolls(),
        relation_revealed_spin_discourages_extra_spikes(),
        relation_unrevealed_spin_keeps_spikes_live(),
        relation_ghost_spinblock_softens_revealed_spin_panic(),
    ]
    if generated:
        results.extend(generated_scenario_relations(generated=generated, seed=seed))

    failures = [result for result in results if not result.passed]
    return {
        "schema_version": 1,
        "generated": generated,
        "seed": seed,
        "relation_count": len(results),
        "pass_count": len(results) - len(failures),
        "failure_count": len(failures),
        "passed": not failures,
        "results": [result_to_json(result) for result in results],
    }


def relation_equal_scores_roll_first_two() -> MetamorphicResult:
    scenario = {
        "id": "metamorphic_equal_scores",
        "tier": "late",
        "moves": [
            {"id": "slot1", "name": "Slot 1"},
            {"id": "slot2", "name": "Slot 2"},
            {"id": "slot3", "name": "Slot 3"},
            {"id": "slot4", "name": "Slot 4"},
        ],
    }
    result = select_move(scenario)
    probabilities = result["probabilities"]
    passed = (
        result["best_action_id"] == "slot1"
        and result["second_action_id"] == "slot2"
        and probabilities["slot3"] == 0.0
        and probabilities["slot4"] == 0.0
    )
    return MetamorphicResult(
        "equal_scores_roll_first_two",
        passed,
        "equal score selector surface must only roll first and second slots",
        scenario["id"],
        {"probabilities": probabilities},
    )


def relation_blocked_scores_have_zero_probability() -> MetamorphicResult:
    scenario = {
        "id": "metamorphic_blocked_score",
        "tier": "late",
        "moves": [
            {"id": "blocked", "name": "Blocked", "blocked": True},
            {"id": "live", "name": "Live Move"},
        ],
    }
    result = select_move(scenario)
    passed = result["probabilities"]["blocked"] == 0.0 and result["best_action_id"] == "live"
    return MetamorphicResult(
        "blocked_scores_have_zero_probability",
        passed,
        "scores >= 80 must be unselectable regardless of slot order",
        scenario["id"],
        {"probabilities": result["probabilities"]},
    )


def relation_third_slot_tied_second_never_rolls() -> MetamorphicResult:
    scenario = {
        "id": "metamorphic_third_slot_tied_second",
        "tier": "late",
        "moves": [
            {"id": "best", "name": "Best", "deltas": [{"rule": "best", "delta": -1}]},
            {"id": "second_a", "name": "Second A"},
            {"id": "second_b", "name": "Second B"},
        ],
    }
    result = select_move(scenario)
    passed = (
        result["best_action_id"] == "best"
        and result["second_action_id"] == "second_a"
        and result["probabilities"]["second_b"] == 0.0
    )
    return MetamorphicResult(
        "third_slot_tied_second_never_rolls",
        passed,
        "the selector ignores later tied second-best slots",
        scenario["id"],
        {"probabilities": result["probabilities"]},
    )


def relation_revealed_spin_discourages_extra_spikes() -> MetamorphicResult:
    scenario = spikes_boundary_scenario(
        "metamorphic_revealed_spin_extra_spikes",
        layers=2,
        active_revealed_spin=True,
        active_ghost=False,
    )
    result = select_move(scenario)
    passed = result["best_action_id"] == "move_sludge_bomb"
    return MetamorphicResult(
        "revealed_spin_discourages_extra_spikes",
        passed,
        "active revealed Rapid Spin should make a live damage line beat extra Spikes",
        scenario["id"],
        {"best_action_id": result["best_action_id"], "scores": score_map(result)},
    )


def relation_unrevealed_spin_keeps_spikes_live() -> MetamorphicResult:
    scenario = spikes_boundary_scenario(
        "metamorphic_unrevealed_spin_keeps_spikes",
        layers=2,
        active_revealed_spin=False,
        active_ghost=False,
    )
    result = select_move(scenario)
    passed = result["best_action_id"] == "move_spikes"
    return MetamorphicResult(
        "unrevealed_spin_keeps_spikes_live",
        passed,
        "spinner capability without revealed Rapid Spin should not suppress third-layer Spikes",
        scenario["id"],
        {"best_action_id": result["best_action_id"], "scores": score_map(result)},
    )


def relation_ghost_spinblock_softens_revealed_spin_panic() -> MetamorphicResult:
    scenario = spikes_boundary_scenario(
        "metamorphic_ghost_spinblock_softens_spin",
        layers=2,
        active_revealed_spin=True,
        active_ghost=True,
    )
    result = select_move(scenario)
    passed = result["best_action_id"] == "move_spikes"
    return MetamorphicResult(
        "ghost_spinblock_softens_revealed_spin_panic",
        passed,
        "active non-Foresighted Ghost spinblock should keep Spikes live into revealed Spin",
        scenario["id"],
        {"best_action_id": result["best_action_id"], "scores": score_map(result)},
    )


def generated_scenario_relations(*, generated: int, seed: int) -> list[MetamorphicResult]:
    scenarios = generate_scenarios(family="all", count=generated, seed=seed)
    results: list[MetamorphicResult] = []
    for scenario in scenarios:
        verdict = evaluate_scenario(scenario)
        catastrophic = bool(verdict.rolled_catastrophic_action_ids)
        results.append(
            MetamorphicResult(
                "generated_no_catastrophic_rolls",
                not catastrophic,
                "generated smoke scenarios should not roll catastrophic actions",
                verdict.scenario_id,
                {
                    "verdict": verdict.verdict,
                    "rolled_catastrophic_action_ids": verdict.rolled_catastrophic_action_ids,
                },
            )
        )
    return results


def spikes_boundary_scenario(
    scenario_id: str,
    *,
    layers: int,
    active_revealed_spin: bool,
    active_ghost: bool,
) -> dict[str, Any]:
    risk_delta = 0
    if active_revealed_spin:
        risk_delta += 18
        if active_ghost:
            risk_delta -= 12
    return {
        "id": scenario_id,
        "tier": "late",
        "moves": [
            {
                "id": "move_spikes",
                "name": "Spikes",
                "deltas": [
                    {"rule": "third_spikes_layer_pressure", "delta": -12 if layers == 2 else -7},
                    {"rule": "public_spin_risk", "delta": risk_delta},
                ],
            },
            {
                "id": "move_sludge_bomb",
                "name": "Sludge Bomb",
                "deltas": [{"rule": "live_damage", "delta": -3}],
            },
            {"id": "move_surf", "name": "Surf"},
            {"id": "move_explosion", "name": "Explosion"},
        ],
    }


def score_map(result: dict[str, Any]) -> dict[str, int]:
    return {move["action_id"]: int(move["final_score"]) for move in result["moves"]}


def result_to_json(result: MetamorphicResult) -> dict[str, Any]:
    return {
        "relation": result.relation,
        "passed": result.passed,
        "reason": result.reason,
        "scenario_id": result.scenario_id,
        "details": result.details,
    }


def format_metamorphic_report(report: dict[str, Any]) -> str:
    status = "passed" if report["passed"] else "failed"
    lines = [
        f"Boss AI metamorphic suite {status}.",
        (
            f"relations={report['relation_count']} pass={report['pass_count']} "
            f"failures={report['failure_count']}"
        ),
    ]
    failures = [result for result in report["results"] if not result["passed"]]
    if failures:
        lines.append("")
        lines.append("Failures:")
        for result in failures[:20]:
            lines.append(
                f"  - {result['relation']} {result['scenario_id']}: {result['reason']}"
            )
            lines.append(f"    details={result['details']}")
    return "\n".join(lines)


def write_metamorphic_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
