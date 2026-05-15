from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError

from .rom_scenarios import evaluate_scenario, load_scenario_batch, select_move


def decision_trace_from_path(
    path: Path,
    *,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    scenarios = load_scenario_batch(path)
    scenario = choose_scenario(scenarios, scenario_id)
    return decision_trace_for_scenario(scenario)


def decision_trace_for_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    result = select_move(scenario)
    verdict = evaluate_scenario(scenario)
    trace_id = str(result["scenario_id"])
    events = [
        event(
            trace_id,
            "decision",
            "",
            "state_load",
            {
                "source": "python_scenario",
                "tier": result["tier"],
                "candidate_count": len(result.get("moves", [])),
            },
        )
    ]

    for move in result.get("moves", []):
        candidate_span = f"candidate:{move['slot']}"
        events.append(
            event(
                trace_id,
                candidate_span,
                "decision",
                "candidate",
                {
                    "candidate_id": move["action_id"],
                    "candidate_name": move["name"],
                    "slot": move["slot"],
                    "initial_score": move["initial_score"],
                    "pre_lookahead_score": move["pre_lookahead_score"],
                    "final_score": move["final_score"],
                    "blocked": move["blocked"],
                },
            )
        )
        for index, score_event in enumerate(move.get("events", []), start=1):
            events.append(
                event(
                    trace_id,
                    f"{candidate_span}:score:{index}",
                    candidate_span,
                    "score_rule",
                    {
                        "candidate_id": move["action_id"],
                        "slot": move["slot"],
                        "rule": score_event["rule"],
                        "before": score_event["before"],
                        "delta": score_event["delta"],
                        "after": score_event["after"],
                        "note": score_event["note"],
                        "source": "python_scenario",
                    },
                )
            )

    selector_attrs = {
        "ready": result.get("ready", False),
        "best_action_id": result.get("best_action_id"),
        "second_action_id": result.get("second_action_id"),
        "best_score": result.get("best_score"),
        "second_score": result.get("second_score"),
        "gap": result.get("gap"),
        "best_roll_threshold": result.get("best_roll_threshold"),
        "probabilities": result.get("probabilities", {}),
    }
    events.append(event(trace_id, "selector", "decision", "selector", selector_attrs))
    events.append(
        event(
            trace_id,
            "policy_check",
            "decision",
            "policy_check",
            {
                "verdict": verdict.verdict,
                "severity": verdict.severity,
                "expected_best_action_ids": verdict.expected_best_action_ids,
                "expected_acceptable_action_ids": verdict.expected_acceptable_action_ids,
                "rolled_bad_action_ids": verdict.rolled_bad_action_ids,
                "rolled_catastrophic_action_ids": verdict.rolled_catastrophic_action_ids,
                "reason": verdict.reason,
            },
        )
    )

    return {
        "schema_version": 1,
        "trace_id": trace_id,
        "source": "python_scenario",
        "scenario_id": verdict.scenario_id,
        "event_count": len(events),
        "events": events,
        "known_limits": [
            "This is a Python scenario score waterfall, not a ROM scoring trace.",
            "Use rom-contribution-trace for ROM score-helper deltas; dynamic public-read evidence still requires future memory-read slicing.",
        ],
    }


def event(
    trace_id: str,
    span_id: str,
    parent_span_id: str,
    event_type: str,
    attributes: dict[str, Any],
) -> dict[str, Any]:
    return {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "event_type": event_type,
        "attributes": attributes,
    }


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


def format_decision_trace(trace: dict[str, Any], *, limit: int = 40) -> str:
    lines = [
        "Boss AI decision trace",
        (
            f"scenario={trace['scenario_id']} source={trace['source']} "
            f"events={trace['event_count']}"
        ),
        "",
        f"First {limit} events:",
    ]
    for item in trace["events"][:limit]:
        attrs = item["attributes"]
        if item["event_type"] == "score_rule":
            lines.append(
                f"  score_rule {attrs['candidate_id']} {attrs['rule']}: "
                f"{attrs['before']} {attrs['delta']} -> {attrs['after']}"
            )
        elif item["event_type"] == "candidate":
            lines.append(
                f"  candidate {attrs['slot']} {attrs['candidate_id']}: "
                f"{attrs['initial_score']} -> {attrs['pre_lookahead_score']} -> "
                f"{attrs['final_score']}"
            )
        elif item["event_type"] == "selector":
            lines.append(
                f"  selector best={attrs['best_action_id']} "
                f"second={attrs['second_action_id']} threshold={attrs['best_roll_threshold']}"
            )
        elif item["event_type"] == "policy_check":
            lines.append(
                f"  policy_check verdict={attrs['verdict']} severity={attrs['severity']}"
            )
        else:
            lines.append(f"  {item['event_type']} {item['span_id']}")
    lines.append("")
    lines.append("Known limits:")
    for gap in trace["known_limits"]:
        lines.append(f"  - {gap}")
    return "\n".join(lines)


def write_decision_trace_json(trace: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(trace, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
