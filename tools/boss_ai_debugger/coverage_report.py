from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .generators import generate_scenarios
from .mastery_index import build_mastery_index, write_mastery_index
from .rom_contribution_trace import (
    resolve_rom_contribution_trace_paths,
    summarize_rom_contribution_trace_paths,
)
from .rule_map import build_rule_map


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COVERAGE_PATH = ROOT / "audit" / "boss_ai_debugger" / "coverage_report.json"


def build_coverage_report(
    *,
    generated_count: int = 250,
    seed: int = 1,
    rom_contribution_trace_paths: list[Path] | None = None,
) -> dict[str, Any]:
    rule_map = build_rule_map()
    mastery = build_mastery_index()
    write_mastery_index(mastery)
    scenarios = generate_scenarios(family="all", count=generated_count, seed=seed)
    contribution_summary = summarize_rom_contribution_trace_paths(
        resolve_rom_contribution_trace_paths(rom_contribution_trace_paths)
    )
    generator_evidence = sorted(
        {
            ref.replace("/", "\\")
            for scenario in scenarios
            for ref in scenario.get("expectation", {}).get("evidence_refs", [])
        }
    )
    policy_card_paths = [card["path"] for card in mastery["policy_cards"]]
    covered_policy_cards = [
        path for path in policy_card_paths if path in generator_evidence
    ]
    uncovered_policy_cards = [
        path for path in policy_card_paths if path not in generator_evidence
    ]

    return {
        "schema_version": 1,
        "generated_count": generated_count,
        "seed": seed,
        "rule_map": rule_coverage_summary(rule_map, contribution_summary),
        "rom_contribution_trace": contribution_summary,
        "mastery": {
            "policy_card_count": mastery["policy_card_count"],
            "source_policy_count": mastery["source_policy_count"],
            "quick_test_count": mastery["quick_test_count"],
            "review_count": mastery["review_count"],
            "generated_policy_card_coverage_count": len(covered_policy_cards),
            "generated_policy_card_coverage_rate": ratio(
                len(covered_policy_cards), len(policy_card_paths)
            ),
            "covered_policy_cards": covered_policy_cards,
            "uncovered_policy_cards": uncovered_policy_cards,
        },
        "generated": {
            "policy_tag_counts": count_expectation_values(scenarios, "policy_tags"),
            "condition_tag_counts": count_expectation_values(scenarios, "condition_tags"),
            "evidence_refs": generator_evidence,
        },
        "known_gaps": [
            "ROM hook score-helper coverage is not full rule coverage because false predicates and dynamic read provenance are not traced yet.",
            "Generated scenario coverage is currently ROM-score-simulator coverage, not PyBoy materialized-state coverage.",
        ],
    }


def rule_coverage_summary(
    rule_map: dict[str, Any],
    contribution_summary: dict[str, Any],
) -> dict[str, Any]:
    by_classification: dict[str, int] = {}
    for rule in rule_map["rules"]:
        key = str(rule["classification"])
        by_classification[key] = by_classification.get(key, 0) + 1
    return {
        "mapped_rule_count": rule_map["rule_count"],
        "classification_counts": dict(sorted(by_classification.items())),
        "full_trace_rule_coverage_available": False,
        "rom_hook_score_trace_available": True,
        "trace_artifact_count": contribution_summary["artifact_count"],
        "trace_event_count": contribution_summary["event_count"],
        "trace_changed_event_count": contribution_summary["changed_event_count"],
        "trace_covered_rule_count": contribution_summary["covered_rule_count"],
        "trace_changed_rule_count": contribution_summary["changed_rule_count"],
        "trace_covered_rule_ids": contribution_summary["covered_rule_ids"],
        "trace_changed_rule_ids": contribution_summary["changed_rule_ids"],
    }


def count_expectation_values(scenarios: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for scenario in scenarios:
        values = scenario.get("expectation", {}).get(key, [])
        if isinstance(values, str):
            values = [values]
        for value in values:
            text = str(value)
            counts[text] = counts.get(text, 0) + 1
    return dict(sorted(counts.items()))


def write_coverage_report(data: dict[str, Any], path: Path = DEFAULT_COVERAGE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def format_coverage_report(data: dict[str, Any]) -> str:
    mastery = data["mastery"]
    rule_map = data["rule_map"]
    return "\n".join(
        [
            "Boss AI debugger coverage report",
            (
                f"mapped_rules={rule_map['mapped_rule_count']} "
                f"full_trace_rule_coverage={rule_map['full_trace_rule_coverage_available']} "
                f"score_trace_rules={rule_map['trace_covered_rule_count']}"
            ),
            (
                f"policy_cards={mastery['policy_card_count']} "
                f"generated_covered={mastery['generated_policy_card_coverage_count']} "
                f"coverage={mastery['generated_policy_card_coverage_rate']:.1%}"
            ),
            (
                "known_gaps="
                + "; ".join(data["known_gaps"])
            ),
        ]
    )


def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
