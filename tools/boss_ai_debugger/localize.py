from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .rom_scenarios import evaluate_batch, load_scenario_batch


def localize_from_scenarios(path: Path) -> dict[str, Any]:
    scenarios = load_scenario_batch(path)
    report = evaluate_batch(scenarios)
    return localize_report(report, scenarios=scenarios, source=str(path))


def localize_from_report(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    return localize_report(report, scenarios=None, source=str(path))


def localize_report(
    report: dict[str, Any],
    *,
    scenarios: list[dict[str, Any]] | None,
    source: str,
) -> dict[str, Any]:
    verdicts = report.get("verdicts", [])
    reviewable = [item for item in verdicts if int(item.get("severity", 0)) > 0]
    return {
        "schema_version": 1,
        "source": source,
        "scenario_count": report.get("scenario_count"),
        "reviewable_count": len(reviewable),
        "verdict_counts": report.get("verdict_counts", {}),
        "top_policy_tags": ranked_counts(reviewable, "policy_tags"),
        "top_condition_tags": ranked_counts(reviewable, "condition_tags"),
        "top_move_delta_rules": ranked_move_delta_rules(scenarios or []),
        "likely_causes": likely_causes(reviewable, scenarios or []),
    }


def ranked_counts(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in rows:
        values = row.get(key, [])
        if isinstance(values, str):
            values = [values]
        for value in values:
            text = str(value)
            counts[text] = counts.get(text, 0) + 1
    return [
        {"value": value, "count": count}
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def ranked_move_delta_rules(scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for scenario in scenarios:
        for move in scenario.get("moves", []):
            if not isinstance(move, dict):
                continue
            for delta in move.get("deltas", []):
                if isinstance(delta, dict):
                    rule = str(delta.get("rule", "delta"))
                else:
                    rule = "delta"
                counts[rule] = counts.get(rule, 0) + 1
    return [
        {"value": value, "count": count}
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def likely_causes(
    reviewable: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    causes = []
    for item in ranked_counts(reviewable, "condition_tags")[:5]:
        causes.append(
            {
                "status": "hypothesis",
                "kind": "condition_tag",
                "value": item["value"],
                "support_count": item["count"],
                "reason": "tag is overrepresented among reviewable generated cases",
            }
        )
    for item in ranked_move_delta_rules(scenarios)[:3]:
        causes.append(
            {
                "status": "hypothesis",
                "kind": "move_delta_rule",
                "value": item["value"],
                "support_count": item["count"],
                "reason": "rule appears frequently in the analyzed scenario corpus",
            }
        )
    return causes


def format_localization_report(report: dict[str, Any]) -> str:
    lines = [
        "Boss AI localization report",
        (
            f"source={report['source']} scenarios={report.get('scenario_count')} "
            f"reviewable={report['reviewable_count']}"
        ),
    ]
    if report["likely_causes"]:
        lines.append("Likely causes:")
        for cause in report["likely_causes"][:10]:
            lines.append(
                f"  - {cause['status']} {cause['kind']}={cause['value']} "
                f"support={cause['support_count']}: {cause['reason']}"
            )
    return "\n".join(lines)


def write_localization_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
