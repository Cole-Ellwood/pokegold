from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .generators import generate_scenarios
from .mastery_index import build_mastery_index
from .rom_contribution_trace import (
    expected_public_read_probe_outcomes,
    resolve_rom_contribution_trace_paths,
    summarize_rom_contribution_trace_reports,
    summarize_rom_contribution_trace_summaries,
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
    rom_contribution_reports: list[dict[str, Any]] | None = None,
    changed_files: list[Path | str] | None = None,
) -> dict[str, Any]:
    rule_map = build_rule_map()
    mastery = build_mastery_index()
    scenarios = generate_scenarios(family="all", count=generated_count, seed=seed)
    contribution_summary = summarize_contribution_sources(
        rom_contribution_trace_paths=rom_contribution_trace_paths,
        rom_contribution_reports=rom_contribution_reports or [],
    )
    executed_rule_ids = set(contribution_summary["executed_rule_ids"])
    score_delta_rule_ids = set(contribution_summary["covered_rule_ids"])
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
        "uncovered_rules": uncovered_rule_summary(rule_map, executed_rule_ids),
        "score_delta_uncovered_rules": uncovered_rule_summary(
            rule_map,
            score_delta_rule_ids,
        ),
        "changed_rules": changed_rule_summary(
            rule_map,
            executed_rule_ids,
            changed_files or [],
        ),
        "coverage_targets": coverage_target_worklist(rule_map, executed_rule_ids),
        "public_read_provenance": public_read_provenance_summary(
            rule_map,
            contribution_summary,
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
            "ROM hook rule coverage is dynamic execution coverage; score-delta coverage is tracked separately because many executed rules leave scores unchanged.",
            "Generated scenario coverage is currently ROM-score-simulator coverage, not PyBoy materialized-state coverage.",
            "PyBoy trace hooks are execution hooks with configured public-input snapshots, not CPU memory-read watchpoints.",
        ],
    }


def summarize_contribution_sources(
    *,
    rom_contribution_trace_paths: list[Path] | None,
    rom_contribution_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    path_summary = summarize_rom_contribution_trace_paths(
        resolve_rom_contribution_trace_paths(rom_contribution_trace_paths)
    )
    if not rom_contribution_reports:
        return path_summary
    report_summary = summarize_rom_contribution_trace_reports(rom_contribution_reports)
    return summarize_rom_contribution_trace_summaries(
        [
            summary
            for summary in (path_summary, report_summary)
            if summary.get("available")
        ]
    )


def rule_coverage_summary(
    rule_map: dict[str, Any],
    contribution_summary: dict[str, Any],
) -> dict[str, Any]:
    by_classification: dict[str, int] = {}
    executable_rules = []
    dynamic_targets = []
    score_trace_targets = []
    provenance_targets = []
    for rule in rule_map["rules"]:
        key = str(rule["classification"])
        by_classification[key] = by_classification.get(key, 0) + 1
        if rule.get("executable", False):
            executable_rules.append(rule)
        if rule.get("dynamic_coverage_target", False):
            dynamic_targets.append(rule)
        if rule.get("score_trace_target", False):
            score_trace_targets.append(rule)
        if rule.get("requires_public_read_provenance", False):
            provenance_targets.append(rule)
    executed_rule_ids = set(contribution_summary["executed_rule_ids"])
    dynamic_uncovered = [
        rule for rule in dynamic_targets if rule["rule_id"] not in executed_rule_ids
    ]
    score_trace_uncovered = [
        rule for rule in score_trace_targets if rule["rule_id"] not in executed_rule_ids
    ]
    return {
        "mapped_rule_count": rule_map["rule_count"],
        "classification_counts": dict(sorted(by_classification.items())),
        "executable_rule_count": len(executable_rules),
        "dynamic_coverage_target_count": len(dynamic_targets),
        "dynamic_covered_rule_count": len(dynamic_targets) - len(dynamic_uncovered),
        "dynamic_uncovered_rule_count": len(dynamic_uncovered),
        "score_trace_target_count": len(score_trace_targets),
        "score_trace_covered_rule_count": (
            len(score_trace_targets) - len(score_trace_uncovered)
        ),
        "score_trace_uncovered_rule_count": len(score_trace_uncovered),
        "public_read_provenance_target_count": len(provenance_targets),
        "full_trace_rule_coverage_available": len(dynamic_uncovered) == 0,
        "score_trace_rule_coverage_available": len(score_trace_uncovered) == 0,
        "rom_hook_score_trace_available": True,
        "trace_artifact_count": contribution_summary["artifact_count"],
        "trace_event_count": contribution_summary["event_count"],
        "trace_changed_event_count": contribution_summary["changed_event_count"],
        "trace_rule_entry_count": contribution_summary["rule_entry_count"],
        "trace_predicate_branch_entry_count": contribution_summary[
            "predicate_branch_entry_count"
        ],
        "trace_predicate_public_input_snapshot_count": contribution_summary[
            "predicate_public_input_snapshot_count"
        ],
        "trace_public_read_probe_entry_count": contribution_summary[
            "public_read_probe_entry_count"
        ],
        "trace_public_read_probe_snapshot_count": contribution_summary[
            "public_read_probe_snapshot_count"
        ],
        "trace_executed_rule_count": contribution_summary["executed_rule_count"],
        "trace_covered_rule_count": contribution_summary["covered_rule_count"],
        "trace_changed_rule_count": contribution_summary["changed_rule_count"],
        "trace_executed_rule_ids": contribution_summary["executed_rule_ids"],
        "trace_covered_rule_ids": contribution_summary["covered_rule_ids"],
        "trace_changed_rule_ids": contribution_summary["changed_rule_ids"],
        "rule_coverage_basis": "dynamic_rule_execution",
        "score_delta_rule_count": contribution_summary["covered_rule_count"],
    }


def uncovered_rule_summary(
    rule_map: dict[str, Any],
    covered_rule_ids: set[str],
    *,
    limit: int = 50,
) -> dict[str, Any]:
    uncovered = [
        rule
        for rule in rule_map["rules"]
        if rule.get("dynamic_coverage_target", False)
        and rule["rule_id"] not in covered_rule_ids
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
    dynamic_rules = [
        rule for rule in rules if rule.get("dynamic_coverage_target", False)
    ]
    uncovered = [
        rule for rule in dynamic_rules if rule["rule_id"] not in covered_rule_ids
    ]
    return {
        "changed_files": normalized_files,
        "mapped_rule_count": len(rules),
        "dynamic_target_count": len(dynamic_rules),
        "covered_rule_count": len(dynamic_rules) - len(uncovered),
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
        "coverage_mode": rule.get("coverage_mode", ""),
        "score_trace_target": bool(rule.get("score_trace_target", False)),
        "expected_public_inputs": rule.get("expected_public_inputs", []),
        "suggested_generator": suggested_generator(rule),
        "recommended_trace_mode": recommended_trace_mode(rule),
    }


def coverage_target_worklist(
    rule_map: dict[str, Any],
    covered_rule_ids: set[str],
) -> dict[str, Any]:
    uncovered = [
        rule
        for rule in rule_map["rules"]
        if rule.get("dynamic_coverage_target", False)
        and rule["rule_id"] not in covered_rule_ids
    ]
    groups: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    for rule in uncovered:
        key = (
            str(rule.get("source_file", "")),
            str(rule.get("parent_label") or rule.get("source_label", "")),
            str(rule.get("classification", "")),
            suggested_generator(rule),
            recommended_trace_mode(rule),
        )
        groups.setdefault(key, []).append(rule)
    grouped = []
    for (
        source_file,
        parent_label,
        classification,
        generator,
        trace_mode,
    ), rules in sorted(groups.items()):
        grouped.append(
            {
                "source_file": source_file,
                "parent_label": parent_label,
                "classification": classification,
                "suggested_generator": generator,
                "recommended_trace_mode": trace_mode,
                "rule_count": len(rules),
                "rule_ids": [rule["rule_id"] for rule in rules],
                "first_rules": [rule_digest(rule) for rule in rules[:10]],
            }
        )
    return {
        "target_count": len(uncovered),
        "group_count": len(grouped),
        "groups": grouped,
    }


def public_read_provenance_summary(
    rule_map: dict[str, Any],
    contribution_summary: dict[str, Any],
) -> dict[str, Any]:
    expected_outcomes = expected_public_read_probe_outcomes()
    observed_probe_outcomes = set(
        contribution_summary.get("public_read_probe_outcome_counts", {})
    )
    observed_predicate_outcomes = set(
        contribution_summary.get("predicate_outcome_counts", {})
    )
    observed_outcomes = observed_probe_outcomes | observed_predicate_outcomes
    target_rules = [
        rule
        for rule in rule_map["rules"]
        if rule.get("requires_public_read_provenance", False)
    ]
    missing_outcomes = [
        outcome for outcome in expected_outcomes if outcome not in observed_outcomes
    ]
    snapshot_count = int(
        contribution_summary.get("public_read_probe_snapshot_count", 0)
    ) + int(contribution_summary.get("predicate_public_input_snapshot_count", 0))
    return {
        "available": snapshot_count > 0 and bool(observed_outcomes),
        "target_rule_count": len(target_rules),
        "expected_probe_outcome_count": len(expected_outcomes),
        "observed_probe_outcome_count": len(observed_outcomes),
        "missing_probe_outcome_count": len(missing_outcomes),
        "missing_probe_outcomes": missing_outcomes,
        "snapshot_count": snapshot_count,
        "public_read_probe_entry_count": contribution_summary.get(
            "public_read_probe_entry_count",
            0,
        ),
        "predicate_branch_entry_count": contribution_summary.get(
            "predicate_branch_entry_count",
            0,
        ),
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
    if any(token in text for token in ("switch", "pivot", "sack", "wincon")):
        return "switch_sack"
    if any(token in text for token in ("setup", "recover", "rest", "heal")):
        return "setup_heal"
    if any(token in text for token in ("predict", "receiver", "branch")):
        return "prediction_mix"
    if any(token in text for token in ("support", "handoff", "status", "phaze", "roar")):
        return "support_handoff"
    return "mastery_policy"


def recommended_trace_mode(rule: dict[str, Any]) -> str:
    if rule.get("score_trace_target", False):
        return "rom_score_materialization"
    if str(rule.get("coverage_mode", "")) == "rom_route_execution_hook":
        return "rom_route_contribution_trace"
    return "rom_contribution_trace"


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
                f"score_trace_rule_coverage={rule_map['score_trace_rule_coverage_available']} "
                f"score_trace_rules={rule_map['trace_covered_rule_count']} "
                f"executed_rules={rule_map['trace_executed_rule_count']}"
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
                f"coverage_target_groups={data['coverage_targets']['group_count']} "
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
