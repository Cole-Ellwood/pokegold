from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError

from .rom_scenarios import (
    BLOCKED_SCORE,
    MIN_SELECTABLE_SCORE,
    evaluate_scenario,
    load_scenario_batch,
    select_move,
)


def explain_counterfactuals_for_path(
    path: Path,
    *,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    scenarios = load_scenario_batch(path)
    scenario = choose_scenario(scenarios, scenario_id)
    return explain_counterfactuals(scenario)


def explain_counterfactuals(scenario: dict[str, Any]) -> dict[str, Any]:
    verdict = evaluate_scenario(scenario)
    selector = select_move(scenario)
    score_by_action = {
        move["action_id"]: int(move["final_score"])
        for move in selector.get("moves", [])
    }
    slot_by_action = {
        move["action_id"]: int(move["slot"])
        for move in selector.get("moves", [])
    }
    best_score = int(selector.get("best_score", 80)) if selector.get("ready") else 80
    best_slot = slot_by_action.get(selector.get("best_action_id"), 99)
    score_flips = [
        score_flip_for_action(
            action_id,
            score_by_action,
            slot_by_action,
            best_score=best_score,
            best_slot=best_slot,
        )
        for action_id in verdict.expected_best_action_ids
    ]
    return {
        "schema_version": 1,
        "scenario_id": verdict.scenario_id,
        "verdict": verdict.verdict,
        "severity": verdict.severity,
        "rom_best_action_id": verdict.rom_best_action_id,
        "rom_best_probability": verdict.rom_best_probability,
        "expected_best_action_ids": verdict.expected_best_action_ids,
        "score_by_action": score_by_action,
        "score_flips_to_expected_best": score_flips,
        "smallest_score_flip": smallest_score_flip(score_flips),
        "condition_tags": verdict.condition_tags,
        "policy_tags": verdict.policy_tags,
        "public_fact_counterfactuals": public_fact_counterfactuals(verdict.condition_tags),
        "answer_changing_information": verdict.answer_changing_information,
        "evidence_refs": verdict.evidence_refs,
        "why": verdict.why,
    }


def score_flip_for_action(
    action_id: str,
    score_by_action: dict[str, int],
    slot_by_action: dict[str, int],
    *,
    best_score: int,
    best_slot: int,
) -> dict[str, Any]:
    if action_id not in score_by_action:
        return {
            "action_id": action_id,
            "available": False,
            "reason": "expected action is not present in scenario moves",
        }
    score = score_by_action[action_id]
    slot = slot_by_action[action_id]
    if score >= BLOCKED_SCORE:
        return {
            "action_id": action_id,
            "available": False,
            "current_score": score,
            "reason": "expected action is blocked from BossAI_SelectMove",
        }
    if score < best_score or (score == best_score and slot < best_slot):
        required_delta = 0
        target_score = score
        reason = "action already beats current ROM best by score/slot ordering"
    else:
        target_score = best_score if slot < best_slot else best_score - 1
        if target_score < MIN_SELECTABLE_SCORE:
            return {
                "action_id": action_id,
                "available": False,
                "current_score": score,
                "reason": "score floor prevents passing current ROM best by score/slot ordering",
            }
        required_delta = target_score - score
        reason = (
            "tie current ROM best from an earlier slot"
            if slot < best_slot
            else "lower expected action below current ROM best score"
        )
    return {
        "action_id": action_id,
        "available": True,
        "current_score": score,
        "target_score": target_score,
        "required_delta": required_delta,
        "reason": reason,
    }


def smallest_score_flip(flips: list[dict[str, Any]]) -> dict[str, Any] | None:
    available = [flip for flip in flips if flip.get("available")]
    if not available:
        return None
    return min(available, key=lambda item: abs(int(item.get("required_delta", 0))))


def public_fact_counterfactuals(condition_tags: list[str]) -> list[str]:
    suggestions: list[str] = []
    tags = set(condition_tags)
    if has_hazard_tags(tags):
        if "active_revealed_rapid_spin" in tags:
            suggestions.append("If Rapid Spin were not publicly revealed, extra Spikes should become more live.")
        else:
            suggestions.append("If active Rapid Spin becomes publicly revealed, hazard-retention risk should increase.")
        if "active_ghost_spinblock" in tags and "foresight_identified_ghost" not in tags:
            suggestions.append("If the Ghost spinblock is identified by Foresight, spin panic should return.")
        elif "active_ghost_spinblock" not in tags:
            suggestions.append("If the boss active is a non-Foresighted Ghost, revealed Spin should matter less.")
        if "immediate_pressure" in tags:
            suggestions.append("If immediate pressure is removed, a hazard turn should become easier to justify.")
        else:
            suggestions.append("If immediate pressure appears, slow hazard work should be discounted.")
        if "spikes_layers_3" in tags:
            suggestions.append("If the stack had fewer than three layers, Spikes would no longer be a failing fourth click.")
    if "named_receiver_branch" in tags:
        suggestions.append("If the named receiver is no longer public-supported, branch-punish moves should fall toward the safe default.")
    if "branch_punish_available" in tags:
        suggestions.append("If coverage or handoff no longer beats the branch, the visible-active line should regain priority.")
    if "status_absorber_named" in tags:
        suggestions.append("If the absorber is removed or already statused, generic status becomes less likely to be blanked.")
    if "support_job_completed" in tags:
        suggestions.append("If the support job is not actually complete, repeating support may be route progress instead of a handoff miss.")
    if "named_next_board_owner" in tags:
        suggestions.append("If no safe next-board owner can be named, switch or handoff should lose route value.")
    if "safe_entry_available" in tags:
        suggestions.append("If the entry path is unsafe, a switch, sack, or handoff should be discounted.")
    if "setup_window" in tags:
        suggestions.append("If the receiver can phaze, Haze, recover, or KO before the boost converts, setup should be discounted.")
    if "setup_already_bankrolled" in tags:
        suggestions.append("If no attack or recovery route converts from the current boosts, one more setup turn can become live again.")
    if "recovery_preserves_route" in tags:
        suggestions.append("If restored HP does not change the next route owner, recovery should fall below pressure or handoff.")
    if "prediction_branch_supported" in tags:
        suggestions.append("If the branch is only possible rather than public-supported, prediction should fall below the safe line.")
    if "prediction_branch_possible_only" in tags:
        suggestions.append("If public switch evidence upgrades the branch to strong-prior, a bounded prediction can become acceptable.")
    if "worst_case_guarded" in tags:
        suggestions.append("If the miss cost becomes unguarded, the prediction should no longer be top.")
    if "worst_case_unguarded" in tags:
        suggestions.append("If the worst-case miss still preserves the route, the prediction can be re-priced as a mixed branch.")
    if not suggestions:
        suggestions.append("Change the public route owner, converter, or reset branch and re-score the expected best action.")
    return suggestions


def has_hazard_tags(tags: set[str]) -> bool:
    return bool(
        {"active_revealed_rapid_spin", "bench_revealed_rapid_spin", "spikes_spin"}
        & tags
    ) or any(tag.startswith("spikes_layers_") for tag in tags)


def choose_scenario(
    scenarios: list[dict[str, Any]],
    scenario_id: str | None,
) -> dict[str, Any]:
    if not scenarios:
        raise PreferenceDataError("no scenarios found")
    if scenario_id is None:
        return scenarios[0]
    for scenario in scenarios:
        if scenario.get("id") == scenario_id or scenario.get("scenario_id") == scenario_id:
            return scenario
    raise PreferenceDataError(f"scenario id {scenario_id!r} not found")


def format_counterfactual_report(report: dict[str, Any]) -> str:
    lines = [
        "Boss AI counterfactual report",
        (
            f"{report['scenario_id']} verdict={report['verdict']} "
            f"rom={report['rom_best_action_id']}({report['rom_best_probability']:.1%})"
        ),
    ]
    flip = report.get("smallest_score_flip")
    if flip:
        lines.append(
            "smallest score flip: "
            f"{flip['action_id']} {flip['current_score']} -> {flip['target_score']} "
            f"delta={flip['required_delta']:+d}"
        )
    if report["public_fact_counterfactuals"]:
        lines.append("public fact flips:")
        for item in report["public_fact_counterfactuals"]:
            lines.append(f"  - {item}")
    if report["why"]:
        lines.append(f"policy: {report['why']}")
    return "\n".join(lines)


def write_counterfactual_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
