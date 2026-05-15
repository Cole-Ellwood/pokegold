from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError

from .rom_scenarios import evaluate_batch, load_scenario_batch


HIGH_VALUE_VERDICTS = {
    "catastrophic_roll": 100,
    "bad_roll": 90,
    "best_never_rolled": 80,
    "mismatch": 70,
    "partial_best_unrolled": 55,
    "weak_best": 45,
    "acceptable_top": 25,
}


def build_review_queue_from_scenarios(
    scenarios_path: Path,
    *,
    expectations_path: Path | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    scenarios = load_scenario_batch(scenarios_path, expectations_path)
    report = evaluate_batch(scenarios)
    return build_review_queue(report, limit=limit, source=str(scenarios_path))


def build_review_queue_from_report(path: Path, *, limit: int = 50) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return build_review_queue(data, limit=limit, source=str(path))


def build_review_queue(
    report: dict[str, Any],
    *,
    limit: int = 50,
    source: str = "",
) -> dict[str, Any]:
    if limit < 0:
        raise PreferenceDataError("limit must be non-negative")
    verdicts = report.get("verdicts")
    if not isinstance(verdicts, list):
        raise PreferenceDataError("review queue input must contain verdicts")

    items = [review_item(item) for item in verdicts if int(item.get("severity", 0)) > 0]
    items.sort(
        key=lambda item: (
            -int(item["priority_score"]),
            -int(item["severity"]),
            str(item["scenario_id"]),
        )
    )
    top = items[:limit]
    return {
        "schema_version": 1,
        "source": source,
        "input_scenario_count": report.get("scenario_count"),
        "input_reviewable_count": len(items),
        "limit": limit,
        "returned_count": len(top),
        "items": top,
    }


def review_item(verdict: dict[str, Any]) -> dict[str, Any]:
    severity = int(verdict.get("severity", 0))
    verdict_name = str(verdict.get("verdict", ""))
    policy_tags = string_list(verdict.get("policy_tags"))
    condition_tags = string_list(verdict.get("condition_tags"))
    evidence_refs = string_list(verdict.get("evidence_refs"))
    answer_changing_information = string_list(verdict.get("answer_changing_information"))
    rom_probability = float(verdict.get("rom_best_probability", 0.0))
    priority_score = (
        HIGH_VALUE_VERDICTS.get(verdict_name, severity)
        + severity
        + min(20, len(policy_tags) * 3)
        + min(20, len(condition_tags))
        + (10 if answer_changing_information else 0)
        + int(rom_probability * 10)
    )
    return {
        "scenario_id": str(verdict.get("scenario_id", "")),
        "verdict": verdict_name,
        "severity": severity,
        "priority_score": priority_score,
        "rom_best_action_id": verdict.get("rom_best_action_id"),
        "rom_best_probability": rom_probability,
        "expected_best_action_ids": string_list(verdict.get("expected_best_action_ids")),
        "expected_acceptable_action_ids": string_list(
            verdict.get("expected_acceptable_action_ids")
        ),
        "rolled_bad_action_ids": string_list(verdict.get("rolled_bad_action_ids")),
        "rolled_catastrophic_action_ids": string_list(
            verdict.get("rolled_catastrophic_action_ids")
        ),
        "policy_tags": policy_tags,
        "condition_tags": condition_tags,
        "lesson_type": str(verdict.get("lesson_type", "")),
        "confidence": str(verdict.get("confidence", "")),
        "reason": str(verdict.get("reason", "")),
        "why": str(verdict.get("why", "")),
        "answer_changing_information": answer_changing_information,
        "evidence_refs": evidence_refs,
    }


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def format_review_queue(queue: dict[str, Any]) -> str:
    lines = [
        "Boss AI debugger review queue",
        (
            f"source={queue.get('source') or 'inline'} "
            f"reviewable={queue['input_reviewable_count']} "
            f"returned={queue['returned_count']} limit={queue['limit']}"
        ),
    ]
    if not queue["items"]:
        lines.append("Top review items: none")
        return "\n".join(lines)

    lines.append("")
    lines.append("Top review items:")
    for item in queue["items"]:
        tags = ",".join(item["policy_tags"]) or "untagged"
        probability = float(item["rom_best_probability"])
        lines.append(
            f"  {item['priority_score']:>3} {item['verdict']} "
            f"{item['scenario_id']} rom={item['rom_best_action_id']}({probability:.1%}) "
            f"best={','.join(item['expected_best_action_ids']) or 'none'} tags={tags}"
        )
        lines.append(f"      {item['reason']}")
        if item["why"]:
            lines.append(f"      policy: {item['why']}")
        if item["answer_changing_information"]:
            lines.append(
                "      changes answer if: "
                + "; ".join(item["answer_changing_information"])
            )
        if item["evidence_refs"]:
            lines.append("      refs: " + "; ".join(item["evidence_refs"][:3]))
    return "\n".join(lines)


def write_review_queue(queue: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(queue, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
