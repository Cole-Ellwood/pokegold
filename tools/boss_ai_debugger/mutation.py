from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.damage_estimates import attach_damage_estimates

from .regression import ScoreAction, evaluate_corpus, format_json
from .scorer import score_action


@dataclass(frozen=True)
class Mutant:
    id: str
    target: str
    description: str
    severity: str
    scorer: ScoreAction


def scorer_mutants() -> list[Mutant]:
    return [
        remove_rule_mutant(
            "scorer.remove_coverage",
            "coverage",
            "Remove the positive public coverage contribution.",
            "medium",
        ),
        remove_rule_mutant(
            "scorer.remove_public_type_immunity_risk",
            "public_type_immunity_risk",
            "Remove the public Psychic-into-Dark immunity penalty.",
            "high",
        ),
        remove_rule_mutant(
            "scorer.remove_spikes_maxed",
            "spikes_already_maxed",
            "Remove the penalty for attempting a fourth Spikes layer.",
            "high",
        ),
        remove_rule_mutant(
            "scorer.remove_active_revealed_spinner_hazard_retention",
            "active_revealed_spinner_hazard_retention",
            "Remove revealed Rapid Spin hazard-retention discipline.",
            "high",
        ),
        Mutant(
            id="scorer.flatten_scores",
            target="scorer",
            description="Flatten every action to the neutral base score.",
            severity="high",
            scorer=flatten_score_action,
        ),
    ]


def remove_rule_mutant(
    mutant_id: str,
    rule: str,
    description: str,
    severity: str,
) -> Mutant:
    def scorer(fixture: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
        return score_with_rule_removed(fixture, action, rule)

    return Mutant(
        id=mutant_id,
        target="scorer",
        description=description,
        severity=severity,
        scorer=scorer,
    )


def score_with_rule_removed(
    fixture: dict[str, Any],
    action: dict[str, Any],
    rule: str,
) -> dict[str, Any]:
    scored = score_action(fixture, action)
    contributions = [
        dict(contribution)
        for contribution in scored["contributions"]
        if contribution["rule"] != rule
    ]
    mutated = dict(scored)
    mutated["contributions"] = contributions
    mutated["score"] = clamped_score(contributions)
    return mutated


def flatten_score_action(
    fixture: dict[str, Any],
    action: dict[str, Any],
) -> dict[str, Any]:
    scored = score_action(fixture, action)
    mutated = dict(scored)
    mutated["score"] = 50
    mutated["contributions"] = [
        {
            "rule": "mutant.flatten_scores",
            "delta": 50,
            "reason": "mutation test neutral score for every action",
        }
    ]
    return mutated


def clamped_score(contributions: list[dict[str, Any]]) -> int:
    total = sum(int(item["delta"]) for item in contributions)
    return max(0, min(100, total))


def run_scorer_mutations(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    *,
    threshold: float = 0.80,
    limit: int | None = None,
    mutants: list[Mutant] | None = None,
) -> dict[str, Any]:
    selected = mutants if mutants is not None else scorer_mutants()
    if limit is not None:
        selected = selected[:limit]

    baseline = evaluate_corpus(fixtures, labels, threshold, scorer=score_action)
    results = [
        evaluate_mutant(mutant, fixtures, labels, threshold, baseline)
        for mutant in selected
    ]
    killed = [item for item in results if item["status"] == "killed"]
    survived = [item for item in results if item["status"] == "survived"]
    not_exercised = [item for item in results if item["status"] == "not_exercised"]
    return {
        "schema_version": 1,
        "target": "scorer",
        "threshold": threshold,
        "baseline": format_json(baseline),
        "mutant_count": len(results),
        "killed_count": len(killed),
        "survived_count": len(survived),
        "not_exercised_count": len(not_exercised),
        "mutation_score": ratio(len(killed), len(results) - len(not_exercised)),
        "mutants": results,
    }


def evaluate_mutant(
    mutant: Mutant,
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    threshold: float,
    baseline: Any,
) -> dict[str, Any]:
    result = evaluate_corpus(fixtures, labels, threshold, scorer=mutant.scorer)
    changed_pairs = changed_strict_pair_count(fixtures, labels, mutant.scorer)
    killed = (
        result.strict_agreement_count < baseline.strict_agreement_count
        or result.agreement_rate < baseline.agreement_rate
        or not result.passed
    )
    if killed:
        status = "killed"
    elif changed_pairs == 0:
        status = "not_exercised"
    else:
        status = "survived"
    return {
        "id": mutant.id,
        "target": mutant.target,
        "description": mutant.description,
        "severity": mutant.severity,
        "status": status,
        "changed_strict_pair_count": changed_pairs,
        "strict_agreement_count": result.strict_agreement_count,
        "strict_label_count": result.strict_label_count,
        "agreement_rate": result.agreement_rate,
        "agreement_delta": result.agreement_rate - baseline.agreement_rate,
        "new_disagreement_count": max(
            0, len(result.disagreements) - len(baseline.disagreements)
        ),
        "sample_disagreements": [
            item.to_json() for item in result.disagreements[:5]
        ],
    }


def changed_strict_pair_count(
    fixtures: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    mutant_scorer: ScoreAction,
) -> int:
    fixtures = attach_damage_estimates(fixtures)
    fixtures_by_id = {fixture["id"]: fixture for fixture in fixtures}
    changed = 0
    for label in labels:
        if label.get("choice") not in {"a_better", "b_better"}:
            continue
        fixture = fixtures_by_id.get(label.get("fixture_id"))
        if fixture is None:
            continue
        actions_by_id = {action["id"]: action for action in fixture.get("actions", [])}
        action_a = actions_by_id.get(label.get("action_a_id"))
        action_b = actions_by_id.get(label.get("action_b_id"))
        if action_a is None or action_b is None:
            continue
        base_scores = (
            int(score_action(fixture, action_a)["score"]),
            int(score_action(fixture, action_b)["score"]),
        )
        mutant_scores = (
            int(mutant_scorer(fixture, action_a)["score"]),
            int(mutant_scorer(fixture, action_b)["score"]),
        )
        if base_scores != mutant_scores:
            changed += 1
    return changed


def format_mutation_report(report: dict[str, Any]) -> str:
    lines = [
        "Boss AI debugger mutation report",
        (
            f"target={report['target']} mutants={report['mutant_count']} "
            f"killed={report['killed_count']} survived={report['survived_count']} "
            f"not_exercised={report['not_exercised_count']} "
            f"score={report['mutation_score']:.1%}"
        ),
        (
            "baseline="
            f"{report['baseline']['strict_agreement_count']} / "
            f"{report['baseline']['strict_label_count']} "
            f"({report['baseline']['agreement_rate']:.1%})"
        ),
    ]
    for mutant in report["mutants"]:
        lines.append("")
        lines.append(
            f"- {mutant['status']} {mutant['id']} "
            f"changed_pairs={mutant['changed_strict_pair_count']} "
            f"agreement={mutant['agreement_rate']:.1%}"
        )
        lines.append(f"  {mutant['description']}")
    return "\n".join(lines)


def write_mutation_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator
