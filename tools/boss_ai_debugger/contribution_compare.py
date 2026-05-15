from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError

from .rom_contribution_trace import load_rom_contribution_trace
from .rom_scenarios import select_move


PYTHON_RULE_ID_MAP = {
    "lookahead": "move.apply_lookahead_to_top_move_candidates",
}


def python_contribution_report_from_scenarios(
    scenarios: list[dict[str, Any]],
) -> dict[str, Any]:
    traces = [python_trace_from_scenario(scenario) for scenario in scenarios]
    return build_python_report(traces, source="scenario_batch")


def python_trace_from_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    result = select_move(scenario)
    events = []
    for move in result.get("moves", []):
        slot = int(move["slot"])
        for score_event in move.get("events", []):
            delta = score_event.get("delta")
            rule_id = python_rule_id(str(score_event["rule"]))
            events.append(
                {
                    "event_type": "score_delta",
                    "rule_id": rule_id,
                    "operation": "python_score_delta",
                    "delta": int(delta) if delta is not None else 0,
                    "changed": delta not in {None, 0},
                    "score_before": int(score_event["before"]),
                    "score_after": int(score_event["after"]),
                    "candidate": {
                        "kind": "move",
                        "slot": slot,
                        "slot_index": slot - 1,
                        "action_id": str(move["action_id"]),
                        "move_name": str(move["name"]),
                    },
                    "source": {
                        "rule_id": rule_id,
                        "python_rule": str(score_event["rule"]),
                        "source": "python_scenario",
                        "note": str(score_event.get("note", "")),
                    },
                }
            )
    return {
        "trace_id": str(result["scenario_id"]),
        "scenario_id": str(result["scenario_id"]),
        "source": "python_scenario",
        "event_count": len(events),
        "changed_event_count": len([event for event in events if event["changed"]]),
        "events": events,
    }


def build_python_report(
    traces: list[dict[str, Any]],
    *,
    source: str,
) -> dict[str, Any]:
    event_count = sum(int(trace.get("event_count", 0)) for trace in traces)
    changed_event_count = sum(
        int(trace.get("changed_event_count", 0)) for trace in traces
    )
    rule_ids = sorted(
        {
            str(event.get("rule_id", ""))
            for trace in traces
            for event in trace.get("events", [])
            if event.get("rule_id")
        }
    )
    return {
        "schema_version": 1,
        "source": "python_scenario_contributions",
        "input_source": source,
        "trace_count": len(traces),
        "event_count": event_count,
        "changed_event_count": changed_event_count,
        "covered_rule_count": len(rule_ids),
        "covered_rule_ids": rule_ids,
        "traces": traces,
    }


def load_python_contribution_report(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PreferenceDataError(f"missing Python contribution trace: {path}") from exc
    if not isinstance(data, dict):
        raise PreferenceDataError(f"Python contribution trace is not an object: {path}")
    if data.get("source") == "python_scenario_contributions":
        return data
    if data.get("source") == "python_scenario":
        return build_python_report(
            [decision_trace_to_python_trace(data)],
            source=str(path),
        )
    raise PreferenceDataError(f"unsupported Python contribution trace source: {path}")


def decision_trace_to_python_trace(trace: dict[str, Any]) -> dict[str, Any]:
    events = []
    for item in trace.get("events", []):
        if item.get("event_type") != "score_rule":
            continue
        attrs = item.get("attributes", {})
        if not isinstance(attrs, dict):
            continue
        slot = int(attrs.get("slot", 0))
        delta = attrs.get("delta")
        rule_id = python_rule_id(str(attrs.get("rule_id") or attrs.get("rule", "")))
        events.append(
            {
                "event_type": "score_delta",
                "rule_id": rule_id,
                "operation": "python_score_delta",
                "delta": int(delta) if delta is not None else 0,
                "changed": delta not in {None, 0},
                "score_before": int(attrs.get("before", 0)),
                "score_after": int(attrs.get("after", 0)),
                "candidate": {
                    "kind": "move",
                    "slot": slot,
                    "slot_index": slot - 1,
                    "action_id": str(attrs.get("candidate_id", "")),
                    "move_name": str(attrs.get("candidate_id", "")),
                },
                "source": {
                    "rule_id": rule_id,
                    "python_rule": str(attrs.get("rule_id") or attrs.get("rule", "")),
                    "source": "python_decision_trace",
                    "note": str(attrs.get("note", "")),
                },
            }
        )
    return {
        "trace_id": str(trace.get("trace_id") or trace.get("scenario_id", "")),
        "scenario_id": str(trace.get("scenario_id", "")),
        "source": "python_scenario",
        "event_count": len(events),
        "changed_event_count": len([event for event in events if event["changed"]]),
        "events": events,
    }


def write_python_contribution_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_rom_contribution_reports(paths: list[Path]) -> list[dict[str, Any]]:
    return [load_rom_contribution_trace(path) for path in paths if path.exists()]


def load_python_contribution_reports(paths: list[Path] | None) -> list[dict[str, Any]]:
    if not paths:
        return []
    return [load_python_contribution_report(path) for path in paths if path.exists()]


def compare_contribution_reports(
    *,
    rom_reports: list[dict[str, Any]],
    python_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    rom_by_id = collect_rom_events(rom_reports)
    python_by_id = collect_python_events(python_reports)
    matched_ids = sorted(set(rom_by_id) & set(python_by_id))
    mismatches = []
    for trace_id in matched_ids:
        mismatches.extend(
            compare_trace_events(
                trace_id,
                rom_events=rom_by_id[trace_id],
                python_events=python_by_id[trace_id],
            )
        )

    class_counts: dict[str, int] = {}
    for mismatch in mismatches:
        key = mismatch["class"]
        class_counts[key] = class_counts.get(key, 0) + 1

    return {
        "schema_version": 1,
        "rom_trace_count": len(rom_by_id),
        "python_trace_count": len(python_by_id),
        "matched_trace_count": len(matched_ids),
        "matched_trace_ids": matched_ids,
        "unmatched_rom_trace_ids": sorted(set(rom_by_id) - set(python_by_id)),
        "unmatched_python_trace_ids": sorted(set(python_by_id) - set(rom_by_id)),
        "mismatch_count": len(mismatches),
        "mismatch_class_counts": dict(sorted(class_counts.items())),
        "mismatches": sorted(
            mismatches,
            key=lambda item: (-int(item["severity"]), item["id"]),
        ),
        "known_limits": [
            "Contribution comparison only runs for matching trace ids.",
            "Only changed score events are compared; false predicate paths are not traced yet.",
            "Candidate matching currently uses move slot plus rule id.",
        ],
    }


def collect_rom_events(
    reports: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    by_id: dict[str, list[dict[str, Any]]] = {}
    for report in reports:
        trace_id = rom_trace_id(report)
        for event in report.get("events", []):
            if not isinstance(event, dict) or not event.get("changed"):
                continue
            normalized = normalize_rom_event(event)
            if not normalized["rule_id"]:
                continue
            by_id.setdefault(trace_id, []).append(normalized)
    return by_id


def collect_python_events(
    reports: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    by_id: dict[str, list[dict[str, Any]]] = {}
    for report in reports:
        for trace in report.get("traces", []):
            trace_id = str(trace.get("trace_id") or trace.get("scenario_id", ""))
            if not trace_id:
                continue
            for event in trace.get("events", []):
                if not isinstance(event, dict) or not event.get("changed"):
                    continue
                normalized = normalize_python_event(event)
                if not normalized["rule_id"]:
                    continue
                by_id.setdefault(trace_id, []).append(normalized)
    return by_id


def compare_trace_events(
    trace_id: str,
    *,
    rom_events: list[dict[str, Any]],
    python_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rom_groups = aggregate_events(rom_events)
    python_groups = aggregate_events(python_events)
    mismatches = []
    for key in sorted(set(rom_groups) - set(python_groups)):
        event = rom_groups[key]
        mismatches.append(
            contribution_mismatch(
                trace_id,
                "missing_python_rule",
                key,
                severity=85,
                reason="ROM applied a changed score rule with no matching Python event",
                rom=event,
                python=None,
            )
        )
    for key in sorted(set(python_groups) - set(rom_groups)):
        event = python_groups[key]
        mismatches.append(
            contribution_mismatch(
                trace_id,
                "missing_rom_rule",
                key,
                severity=85,
                reason="Python applied a changed score rule with no matching ROM event",
                rom=None,
                python=event,
            )
        )
    for key in sorted(set(rom_groups) & set(python_groups)):
        rom = rom_groups[key]
        python = python_groups[key]
        if rom["total_delta"] == python["total_delta"]:
            continue
        mismatches.append(
            contribution_mismatch(
                trace_id,
                "rule_delta_mismatch",
                key,
                severity=90,
                reason="ROM and Python applied different total score deltas",
                rom=rom,
                python=python,
            )
        )
    return mismatches


def aggregate_events(
    events: list[dict[str, Any]],
) -> dict[tuple[str, int], dict[str, Any]]:
    grouped: dict[tuple[str, int], dict[str, Any]] = {}
    for event in events:
        key = contribution_key(event)
        existing = grouped.get(key)
        if existing is None:
            grouped[key] = {
                "rule_id": event["rule_id"],
                "slot_index": event["slot_index"],
                "candidate": event["candidate"],
                "event_count": 1,
                "total_delta": int(event["delta"]),
                "operations": {event["operation"]: 1},
            }
            continue
        existing["event_count"] += 1
        existing["total_delta"] += int(event["delta"])
        operations = existing["operations"]
        operations[event["operation"]] = operations.get(event["operation"], 0) + 1
    return grouped


def contribution_key(event: dict[str, Any]) -> tuple[str, int]:
    return (str(event["rule_id"]), int(event["slot_index"]))


def contribution_mismatch(
    trace_id: str,
    mismatch_class: str,
    key: tuple[str, int],
    *,
    severity: int,
    reason: str,
    rom: dict[str, Any] | None,
    python: dict[str, Any] | None,
) -> dict[str, Any]:
    rule_id, slot_index = key
    return {
        "id": f"contribution:{trace_id}:{mismatch_class}:{rule_id}:{slot_index}",
        "class": mismatch_class,
        "status": "confirmed",
        "severity": severity,
        "trace_id": trace_id,
        "rule_id": rule_id,
        "slot_index": slot_index,
        "reason": reason,
        "rom": rom,
        "python": python,
    }


def normalize_rom_event(event: dict[str, Any]) -> dict[str, Any]:
    candidate = event.get("candidate", {})
    source = event.get("source", {})
    return {
        "rule_id": str(source.get("rule_id", "")),
        "slot_index": int(candidate.get("slot_index", -1)),
        "candidate": {
            "kind": str(candidate.get("kind", "")),
            "slot_index": int(candidate.get("slot_index", -1)),
            "move_id": int(candidate.get("move_id", 0)),
            "move_name": str(candidate.get("move_name", "")),
        },
        "operation": str(event.get("operation", "")),
        "delta": int(event.get("delta", 0)),
    }


def normalize_python_event(event: dict[str, Any]) -> dict[str, Any]:
    candidate = event.get("candidate", {})
    return {
        "rule_id": str(event.get("rule_id", "")),
        "slot_index": int(candidate.get("slot_index", -1)),
        "candidate": {
            "kind": str(candidate.get("kind", "")),
            "slot_index": int(candidate.get("slot_index", -1)),
            "action_id": str(candidate.get("action_id", "")),
            "move_name": str(candidate.get("move_name", "")),
        },
        "operation": str(event.get("operation", "")),
        "delta": int(event.get("delta", 0)),
    }


def rom_trace_id(report: dict[str, Any]) -> str:
    explicit = report.get("trace_id")
    if explicit:
        return str(explicit)
    save_state = str(report.get("save_state", ""))
    if save_state.startswith("scenario:"):
        return save_state.split(":", 1)[1]
    if report.get("boss_route"):
        return f"route:{report['boss_route']}"
    return save_state


def format_python_contribution_report(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "Boss AI Python contribution trace",
            (
                f"traces={report['trace_count']} events={report['event_count']} "
                f"changed={report['changed_event_count']} "
                f"rules={report['covered_rule_count']}"
            ),
        ]
    )


def python_rule_id(rule: str) -> str:
    if "." in rule:
        return rule
    return PYTHON_RULE_ID_MAP.get(rule, rule)
