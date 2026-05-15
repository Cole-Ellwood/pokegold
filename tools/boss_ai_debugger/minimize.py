from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .counterfactuals import choose_scenario
from .rom_scenarios import evaluate_scenario, load_scenario_batch


PRESERVED_EXPECTATION_KEYS = {
    "best_action_ids",
    "acceptable_action_ids",
    "bad_action_ids",
    "catastrophic_action_ids",
    "min_best_probability",
}


def minimize_scenario_path(
    path: Path,
    *,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    scenario = choose_scenario(load_scenario_batch(path), scenario_id)
    return minimize_scenario(scenario)


def minimize_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    baseline = evaluate_scenario(scenario)
    minimized = copy.deepcopy(scenario)
    removed_fields: list[str] = []
    removed_actions: list[str] = []

    for key in ("notes", "generator", "family", "seed", "case_index"):
        if key not in minimized:
            continue
        trial = copy.deepcopy(minimized)
        trial.pop(key, None)
        if preserves_verdict(trial, baseline):
            minimized = trial
            removed_fields.append(key)

    expectation = minimized.get("expectation")
    if isinstance(expectation, dict):
        for key in list(expectation):
            if key in PRESERVED_EXPECTATION_KEYS:
                continue
            trial = copy.deepcopy(minimized)
            trial["expectation"].pop(key, None)
            if preserves_verdict(trial, baseline):
                minimized = trial
                removed_fields.append(f"expectation.{key}")

    for action_id in removable_action_ids(minimized, baseline):
        trial = copy.deepcopy(minimized)
        trial["moves"] = [
            move for move in trial.get("moves", [])
            if isinstance(move, dict) and move.get("id") != action_id
        ]
        if trial.get("moves") and preserves_verdict(trial, baseline):
            minimized = trial
            removed_actions.append(action_id)

    final = evaluate_scenario(minimized)
    return {
        "schema_version": 1,
        "scenario_id": baseline.scenario_id,
        "baseline_verdict": baseline.verdict,
        "final_verdict": final.verdict,
        "preserved": final.verdict == baseline.verdict
        and final.rom_best_action_id == baseline.rom_best_action_id,
        "removed_fields": removed_fields,
        "removed_actions": removed_actions,
        "original_move_count": len(scenario.get("moves", [])),
        "minimized_move_count": len(minimized.get("moves", [])),
        "minimized_scenario": minimized,
    }


def removable_action_ids(scenario: dict[str, Any], baseline: Any) -> list[str]:
    protected = {
        baseline.rom_best_action_id,
        *baseline.expected_best_action_ids,
        *baseline.expected_acceptable_action_ids,
        *baseline.rolled_bad_action_ids,
        *baseline.rolled_catastrophic_action_ids,
    }
    result = []
    for move in scenario.get("moves", []):
        if not isinstance(move, dict):
            continue
        action_id = str(move.get("id", ""))
        if action_id and action_id not in protected:
            result.append(action_id)
    return result


def preserves_verdict(scenario: dict[str, Any], baseline: Any) -> bool:
    try:
        verdict = evaluate_scenario(scenario)
    except Exception:
        return False
    return (
        verdict.verdict == baseline.verdict
        and verdict.rom_best_action_id == baseline.rom_best_action_id
        and verdict.expected_best_action_ids == baseline.expected_best_action_ids
    )


def format_minimized_report(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "Boss AI minimization report",
            (
                f"{report['scenario_id']} verdict={report['baseline_verdict']} "
                f"preserved={report['preserved']}"
            ),
            (
                f"moves {report['original_move_count']} -> {report['minimized_move_count']} "
                f"removed_actions={','.join(report['removed_actions']) or 'none'}"
            ),
            f"removed_fields={','.join(report['removed_fields']) or 'none'}",
        ]
    )


def write_minimized_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
