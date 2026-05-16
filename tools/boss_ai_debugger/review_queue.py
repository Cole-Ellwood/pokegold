from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError

from .mastery_index import build_mastery_index
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

MASTERY_TAG_BONUS = {
    "hazard_retention": 10,
    "rapid_spin": 10,
    "spikes": 10,
    "branch_action": 10,
    "receiver_pricing": 10,
    "cashout": 10,
    "route_converter": 10,
    "switch_sack": 10,
    "setup_timing": 10,
    "recovery_timing": 10,
    "support_handoff": 10,
    "reset_loop_denial": 10,
    "prediction_mix": 10,
    "public_info_gate": 10,
    "role_package_ledger": 25,
    "reversible_before_irreversible": 35,
    "resisted_explosion_board_delta": 35,
    "sleep_plus_cashout_package": 30,
    "typed_status_absorber": 25,
    "pass_receiver_survival": 25,
    "clean_oracle_subset": 20,
    "reversible_line_covers_active_and_branch": 20,
    "resisted_explosion_free_owner": 20,
    "cashout_immunity_guard": 20,
    "low_value_absorber_available": 15,
}


def build_review_queue_from_scenarios(
    scenarios_path: Path,
    *,
    expectations_path: Path | None = None,
    limit: int = 50,
    max_per_lesson: int = 5,
) -> dict[str, Any]:
    scenarios = load_scenario_batch(scenarios_path, expectations_path)
    report = evaluate_batch(scenarios)
    return build_review_queue(
        report,
        limit=limit,
        max_per_lesson=max_per_lesson,
        source=str(scenarios_path),
    )


def build_review_queue_from_report(
    path: Path,
    *,
    limit: int = 50,
    max_per_lesson: int = 5,
) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return build_review_queue(
        data,
        limit=limit,
        max_per_lesson=max_per_lesson,
        source=str(path),
    )


def build_review_queue(
    report: dict[str, Any],
    *,
    limit: int = 50,
    max_per_lesson: int = 5,
    source: str = "",
) -> dict[str, Any]:
    if limit < 0:
        raise PreferenceDataError("limit must be non-negative")
    if max_per_lesson < 0:
        raise PreferenceDataError("max_per_lesson must be non-negative")
    verdicts = report.get("verdicts")
    if not isinstance(verdicts, list):
        raise PreferenceDataError("review queue input must contain verdicts")

    evidence_index = mastery_evidence_index()
    items = [
        review_item(item, evidence_index=evidence_index)
        for item in verdicts
        if int(item.get("severity", 0)) > 0
    ]
    items.sort(
        key=lambda item: (
            -int(item["priority_score"]),
            -int(item["severity"]),
            str(item["scenario_id"]),
        )
    )
    top = select_diverse_items(items, limit=limit, max_per_lesson=max_per_lesson)
    return {
        "schema_version": 1,
        "source": source,
        "input_scenario_count": report.get("scenario_count"),
        "input_reviewable_count": len(items),
        "limit": limit,
        "max_per_lesson": max_per_lesson,
        "returned_count": len(top),
        "items": top,
    }


def review_item(
    verdict: dict[str, Any],
    *,
    evidence_index: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
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
        + mastery_tag_priority(policy_tags, condition_tags)
    )
    strata = mastery_strata(policy_tags, condition_tags)
    digest = evidence_digest(evidence_refs, evidence_index or {})
    return {
        "scenario_id": str(verdict.get("scenario_id", "")),
        "verdict": verdict_name,
        "severity": severity,
        "priority_score": priority_score,
        "mastery_strata": strata,
        "newest_mastery_strata": strata,
        "lesson_key": lesson_key(policy_tags, evidence_refs),
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
        "evidence_digest": digest,
        "next_action": next_action_hint(
            verdict_name,
            rom_best=verdict.get("rom_best_action_id"),
            expected_best=string_list(verdict.get("expected_best_action_ids")),
            evidence_digest=digest,
            answer_changing_information=answer_changing_information,
        ),
    }


def mastery_tag_priority(policy_tags: list[str], condition_tags: list[str]) -> int:
    tags = set(policy_tags) | set(condition_tags)
    return min(70, sum(MASTERY_TAG_BONUS.get(tag, 0) for tag in tags))


def mastery_strata(
    policy_tags: list[str],
    condition_tags: list[str],
) -> list[str]:
    tags = set(policy_tags) | set(condition_tags)
    strata = []
    if "hazard_retention" in tags or "rapid_spin" in tags or "spikes" in tags:
        strata.append("hazard_spin_reset")
    if "branch_action" in tags or "receiver_pricing" in tags:
        strata.append("branch_receiver_pricing")
    if "cashout" in tags or "route_converter" in tags:
        strata.append("cashout_converter")
    if "switch_sack" in tags or "switching" in tags or "defensive_sack" in tags:
        strata.append("switch_sack_preservation")
    if "setup_timing" in tags or "setup" in tags or "recovery_timing" in tags:
        strata.append("setup_recovery_timing")
    if "support_handoff" in tags or "reset_loop_denial" in tags:
        strata.append("support_handoff_reset_denial")
    if "prediction_mix" in tags or "prediction" in tags:
        strata.append("prediction_risk_control")
    if "reversible_before_irreversible" in tags or "reversible_line_covers_active_and_branch" in tags:
        strata.append("reversible_vs_irreversible_cashout")
    if "resisted_explosion_board_delta" in tags or "resisted_explosion_free_owner" in tags:
        strata.append("resisted_explosion_board_delta")
    if "role_package_ledger" in tags or "sleep_plus_cashout_package" in tags:
        strata.append("role_package_reveal")
    if "typed_status_absorber" in tags:
        strata.append("typed_status_absorber")
    if "pass_receiver_survival" in tags:
        strata.append("pass_receiver_survival")
    if "clean_oracle_subset" in tags:
        strata.append("clean_oracle")
    return strata


def select_diverse_items(
    items: list[dict[str, Any]],
    *,
    limit: int,
    max_per_lesson: int,
) -> list[dict[str, Any]]:
    if limit == 0:
        return []
    if max_per_lesson == 0:
        return items[:limit]

    selected: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    lesson_counts: dict[str, int] = {}
    for item in items:
        lesson = str(item["lesson_key"])
        if lesson_counts.get(lesson, 0) < max_per_lesson:
            selected.append(item)
            lesson_counts[lesson] = lesson_counts.get(lesson, 0) + 1
            if len(selected) == limit:
                return selected
        else:
            deferred.append(item)

    selected_ids = {id(item) for item in selected}
    for item in [*deferred, *items]:
        if len(selected) == limit:
            break
        if id(item) in selected_ids:
            continue
        selected.append(item)
        selected_ids.add(id(item))
    return selected


def mastery_evidence_index() -> dict[str, dict[str, Any]]:
    index = build_mastery_index()
    by_path: dict[str, dict[str, Any]] = {}
    for card in index["policy_cards"]:
        path = str(card["path"])
        by_path[path] = card
        by_path[path.replace("\\", "/")] = card
    return by_path


def evidence_digest(
    evidence_refs: list[str],
    evidence_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    digests = []
    for ref in evidence_refs:
        card = evidence_index.get(ref) or evidence_index.get(ref.replace("/", "\\"))
        if card is None:
            continue
        digests.append(
            {
                "path": card["path"],
                "title": card["title"],
                "status": card["status"],
                "use_when": card["use_when"],
                "default_summary": compact_text(card.get("default", []), limit=240),
                "worst_branch": compact_text(card.get("worst_branch", ""), limit=180),
                "evidence_count": len(card.get("evidence", [])),
            }
        )
    return digests


def compact_text(value: Any, *, limit: int) -> str:
    if isinstance(value, list):
        text = " ".join(str(item) for item in value)
    else:
        text = str(value)
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def lesson_key(policy_tags: list[str], evidence_refs: list[str]) -> str:
    for ref in evidence_refs:
        if "\\policy_cards\\" in ref or "/policy_cards/" in ref:
            return ref.replace("/", "\\")
    if policy_tags:
        return "tag:" + policy_tags[0]
    return "untagged"


def next_action_hint(
    verdict: str,
    *,
    rom_best: Any,
    expected_best: list[str],
    evidence_digest: list[dict[str, Any]],
    answer_changing_information: list[str],
) -> str:
    policy = evidence_digest[0]["title"] if evidence_digest else "the cited policy"
    if answer_changing_information:
        return "Check the answer-changing fact first: " + answer_changing_information[0]
    if verdict in {"bad_roll", "catastrophic_roll"}:
        return f"Verify whether ROM should remove probability from {rom_best} under {policy}."
    if verdict in {"mismatch", "best_never_rolled", "partial_best_unrolled"}:
        wanted = ",".join(expected_best) or "the expected line"
        return f"Compare ROM top {rom_best} against {wanted} using {policy}."
    if verdict == "weak_best":
        return f"Decide whether the near-tie probability is acceptable under {policy}."
    if verdict == "acceptable_top":
        return f"Decide whether acceptable top {rom_best} should become expected-best."
    return f"Review against {policy}."


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
        if item.get("mastery_strata"):
            lines.append("      strata: " + ",".join(item["mastery_strata"]))
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
        if item["evidence_digest"]:
            digest = item["evidence_digest"][0]
            lines.append(
                f"      evidence: {digest['title']} - {digest['default_summary']}"
            )
        lines.append(f"      next: {item['next_action']}")
    return "\n".join(lines)


def write_review_queue(queue: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(queue, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
