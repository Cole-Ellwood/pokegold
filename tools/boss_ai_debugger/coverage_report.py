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
    changed_files: list[Path | str] | None = None,
) -> dict[str, Any]:
    rule_map = build_rule_map()
    mastery = build_mastery_index()
    write_mastery_index(mastery)
    scenarios = generate_scenarios(family="all", count=generated_count, seed=seed)
    contribution_summary = summarize_rom_contribution_trace_paths(
        resolve_rom_contribution_trace_paths(rom_contribution_trace_paths)
    )
    covered_rule_ids = set(contribution_summary["covered_rule_ids"])
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
    policy_card_requirements = policy_card_requirement_coverage(
        policy_card_paths,
        scenarios,
    )

    return {
        "schema_version": 1,
        "generated_count": generated_count,
        "seed": seed,
        "rule_map": rule_coverage_summary(rule_map, contribution_summary),
        "uncovered_rules": uncovered_rule_summary(rule_map, covered_rule_ids),
        "changed_rules": changed_rule_summary(
            rule_map,
            covered_rule_ids,
            changed_files or [],
        ),
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
            "policy_card_requirement_coverage": policy_card_requirements,
            "policy_card_missing_positive_count": len(
                policy_card_requirements["missing_positive"]
            ),
            "policy_card_missing_negative_count": len(
                policy_card_requirements["missing_negative"]
            ),
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


def uncovered_rule_summary(
    rule_map: dict[str, Any],
    covered_rule_ids: set[str],
    *,
    limit: int = 50,
) -> dict[str, Any]:
    uncovered = [
        rule for rule in rule_map["rules"] if rule["rule_id"] not in covered_rule_ids
    ]
    generator_counts = count_generators(uncovered)
    return {
        "uncovered_rule_count": len(uncovered),
        "uncovered_rule_ids": [rule["rule_id"] for rule in uncovered],
        "first_uncovered_rules": [rule_digest(rule) for rule in uncovered[:limit]],
        "suggested_generator_counts": generator_counts,
    }


def changed_rule_summary(
    rule_map: dict[str, Any],
    covered_rule_ids: set[str],
    changed_files: list[Path | str],
) -> dict[str, Any]:
    normalized_files = sorted({normalize_repo_path(path) for path in changed_files})
    rules = [
        rule
        for rule in rule_map["rules"]
        if normalize_repo_path(rule["source_file"]) in normalized_files
    ]
    uncovered = [rule for rule in rules if rule["rule_id"] not in covered_rule_ids]
    return {
        "changed_files": normalized_files,
        "mapped_rule_count": len(rules),
        "covered_rule_count": len(rules) - len(uncovered),
        "uncovered_rule_count": len(uncovered),
        "uncovered_rules": [rule_digest(rule) for rule in uncovered],
        "suggested_generator_counts": count_generators(uncovered),
    }


def rule_digest(rule: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule_id": rule["rule_id"],
        "classification": rule["classification"],
        "source_file": rule["source_file"],
        "source_label": rule["source_label"],
        "line": rule["line"],
        "suggested_generator": suggested_generator(rule),
    }


def count_generators(rules: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rule in rules:
        generator = suggested_generator(rule)
        counts[generator] = counts.get(generator, 0) + 1
    return dict(sorted(counts.items()))


def suggested_generator(rule: dict[str, Any]) -> str:
    text = " ".join(
        [
            str(rule.get("rule_id", "")),
            str(rule.get("source_label", "")),
            " ".join(str(item) for item in rule.get("public_reads", [])),
        ]
    ).lower()
    if any(token in text for token in ("spikes", "rapid_spin", "rapidspin", "ghost")):
        return "spikes_spin"
    if any(token in text for token in ("select_move", "selector", "score")):
        return "selector_edges"
    return "mastery_policy"


def normalize_repo_path(path: Path | str) -> str:
    text = str(path).replace("/", "\\")
    marker = "\\pokemon gold hack\\"
    lowered = text.lower()
    if marker in lowered:
        index = lowered.index(marker) + len(marker)
        return text[index:]
    return text.strip(".\\")


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


def policy_card_requirement_coverage(
    policy_card_paths: list[str],
    scenarios: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = []
    for path in policy_card_paths:
        matching = [
            scenario
            for scenario in scenarios
            if path in normalized_evidence_refs(scenario)
        ]
        positive = [
            scenario["id"]
            for scenario in matching
            if scenario_expectation_list(scenario, "best_action_ids")
        ]
        negative = [
            scenario["id"]
            for scenario in matching
            if scenario_expectation_list(scenario, "bad_action_ids")
            or scenario_expectation_list(scenario, "catastrophic_action_ids")
        ]
        rows.append(
            {
                "policy_card": path,
                "scenario_count": len(matching),
                "positive_scenario_count": len(positive),
                "negative_scenario_count": len(negative),
                "positive_examples": positive[:5],
                "negative_examples": negative[:5],
                "has_positive": bool(positive),
                "has_negative": bool(negative),
            }
        )
    return {
        "cards": rows,
        "missing_positive": [
            row["policy_card"] for row in rows if not row["has_positive"]
        ],
        "missing_negative": [
            row["policy_card"] for row in rows if not row["has_negative"]
        ],
    }


def normalized_evidence_refs(scenario: dict[str, Any]) -> set[str]:
    refs = scenario.get("expectation", {}).get("evidence_refs", [])
    if isinstance(refs, str):
        refs = [refs]
    return {str(ref).replace("/", "\\") for ref in refs}


def scenario_expectation_list(scenario: dict[str, Any], key: str) -> list[Any]:
    value = scenario.get("expectation", {}).get(key, [])
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


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
                "policy_card_missing="
                f"positive:{mastery['policy_card_missing_positive_count']} "
                f"negative:{mastery['policy_card_missing_negative_count']}"
            ),
            (
                f"uncovered_rules={data['uncovered_rules']['uncovered_rule_count']} "
                f"changed_uncovered={data['changed_rules']['uncovered_rule_count']}"
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
