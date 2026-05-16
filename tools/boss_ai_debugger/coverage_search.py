from __future__ import annotations

import json
import random
from copy import deepcopy
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError

from .generators import generate_scenarios, stamp_scenario, write_jsonl
from .rom_scenarios import evaluate_batch, load_scenario_batch


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COVERAGE_SEARCH_REPORT = (
    ROOT / "audit" / "boss_ai_debugger" / "coverage_search_report.json"
)
DEFAULT_COVERAGE_SEARCH_SCENARIOS = (
    ROOT / ".local" / "tmp" / "boss_ai_debugger" / "coverage_search_scenarios.jsonl"
)

TARGET_FAMILIES = (
    "spikes_spin",
    "switch_sack",
    "setup_heal",
    "prediction_mix",
    "support_handoff",
    "cashout_board_delta",
    "mastery_policy",
)

PUBLIC_MUTATIONS = (
    "tier_mid",
    "tier_late",
    "promote_branch_punish",
    "promote_cashout_guard",
    "promote_recovery_reset",
    "promote_setup_denial",
    "promote_handoff",
    "penalize_status_into_shield",
    "penalize_unsupported_spin",
    "prefer_reversible_before_irreversible",
    "price_resisted_explosion_board_delta",
    "penalize_explosion_into_immunity",
    "promote_typed_status_absorber",
    "promote_pass_receiver_survival",
    "price_sleep_cashout_package",
)


def run_coverage_guided_search(
    *,
    seed_scenarios: list[dict[str, Any]],
    rounds: int,
    per_seed: int,
    seed: int,
    generated_count: int = 0,
    keep: int = 100,
) -> dict[str, Any]:
    if rounds < 0:
        raise PreferenceDataError("rounds must be non-negative")
    if per_seed < 0:
        raise PreferenceDataError("per-seed must be non-negative")
    if generated_count < 0:
        raise PreferenceDataError("generated-count must be non-negative")
    if keep < 0:
        raise PreferenceDataError("keep must be non-negative")

    rng = random.Random(seed)
    seeds = list(seed_scenarios)
    candidates: list[dict[str, Any]] = []
    if generated_count:
        candidates.extend(generate_scenarios(family="all", count=generated_count, seed=seed))

    frontier = list(seeds)
    for round_index in range(rounds):
        next_frontier: list[dict[str, Any]] = []
        for scenario in frontier:
            for mutation_index in range(per_seed):
                mutation = rng.choice(PUBLIC_MUTATIONS)
                mutated = mutate_scenario(
                    scenario,
                    mutation=mutation,
                    round_index=round_index,
                    mutation_index=mutation_index,
                    seed=seed,
                )
                candidates.append(mutated)
                next_frontier.append(mutated)
        frontier = choose_frontier(next_frontier, limit=max(len(seeds), 1))

    batch = evaluate_batch(candidates) if candidates else empty_batch_report()
    selected = select_interesting_scenarios(candidates, batch, keep=keep)
    report = build_search_report(
        seeds=seeds,
        candidates=candidates,
        selected=selected,
        batch=batch,
        rounds=rounds,
        per_seed=per_seed,
        seed=seed,
        generated_count=generated_count,
    )
    return {"scenarios": selected, "report": report}


def run_coverage_guided_search_from_path(
    scenarios_path: Path,
    *,
    rounds: int,
    per_seed: int,
    seed: int,
    generated_count: int,
    keep: int,
) -> dict[str, Any]:
    seeds = load_scenario_batch(scenarios_path)
    return run_coverage_guided_search(
        seed_scenarios=seeds,
        rounds=rounds,
        per_seed=per_seed,
        seed=seed,
        generated_count=generated_count,
        keep=keep,
    )


def mutate_scenario(
    scenario: dict[str, Any],
    *,
    mutation: str,
    round_index: int,
    mutation_index: int,
    seed: int,
) -> dict[str, Any]:
    mutated = deepcopy(scenario)
    parent_id = str(scenario.get("id", scenario.get("scenario_id", "scenario")))
    mutated["id"] = (
        f"{parent_id}__cg_{seed}_{round_index:02d}_{mutation_index:02d}_{mutation}"
    )
    mutated["generator"] = "boss-ai-debugger-coverage-search-v1"
    mutated["coverage_search"] = {
        "parent_id": parent_id,
        "mutation": mutation,
        "round": round_index,
        "mutation_index": mutation_index,
        "seed": seed,
        "public_info_only": True,
    }

    if mutation == "tier_mid":
        mutated["tier"] = "mid"
    elif mutation == "tier_late":
        mutated["tier"] = "late"
    elif mutation == "promote_branch_punish":
        apply_rule_delta(mutated, "coverage.branch.named_receiver_punish", -3, include=("coverage", "handoff", "switch"))
        add_condition(mutated, "coverage_named_receiver_branch")
    elif mutation == "promote_cashout_guard":
        apply_rule_delta(mutated, "coverage.cashout.named_absorber_guard", 5, include=("explosion", "self-destruct", "destiny"))
        apply_rule_delta(mutated, "coverage.cashout.low_value_sack", -2, include=("switch",))
        add_condition(mutated, "coverage_cashout_absorber_guard")
    elif mutation == "promote_recovery_reset":
        apply_rule_delta(mutated, "coverage.recovery.reset_denial", -4, include=("recover", "rest"))
        add_condition(mutated, "coverage_recovery_reset")
    elif mutation == "promote_setup_denial":
        apply_rule_delta(mutated, "coverage.setup.denied_by_public_phaze", 4, include=("curse", "growth", "agility", "swords"))
        apply_rule_delta(mutated, "coverage.setup.phaze_or_attack", -2, include=("roar", "whirlwind", "explosion"))
        add_condition(mutated, "coverage_setup_denial")
    elif mutation == "promote_handoff":
        apply_rule_delta(mutated, "coverage.handoff.counter_owner", -3, include=("switch", "baton pass", "roar", "whirlwind"))
        add_condition(mutated, "coverage_counter_owner_handoff")
    elif mutation == "penalize_status_into_shield":
        apply_rule_delta(mutated, "coverage.status.protected_target", 6, include=("toxic", "hypnosis", "sleep", "thunder wave", "stun spore"))
        add_condition(mutated, "coverage_protected_status_target")
    elif mutation == "penalize_unsupported_spin":
        apply_rule_delta(mutated, "coverage.spin.unsolved_spinblock_or_reset", 5, include=("rapid spin",))
        add_condition(mutated, "coverage_unsupported_spin")
    elif mutation == "prefer_reversible_before_irreversible":
        apply_rule_delta(mutated, "coverage.cashout.premature_irreversible", 5, include=("explosion", "self-destruct", "destiny", "boom"))
        apply_rule_delta(mutated, "coverage.cashout.reversible_branch_cover", -3, include=("earthquake", "coverage", "handoff", "switch", "branch cover"))
        add_policy(mutated, "reversible_before_irreversible")
        add_condition(mutated, "coverage_reversible_before_irreversible")
    elif mutation == "price_resisted_explosion_board_delta":
        apply_rule_delta(mutated, "coverage.cashout.resisted_trade_free_owner", -4, include=("explosion", "self-destruct", "boom"))
        apply_rule_delta(mutated, "coverage.cashout.active_damage_misses_receiver", 2, include=("earthquake", "damage", "stab", "active"))
        add_policy(mutated, "resisted_explosion_board_delta")
        add_condition(mutated, "coverage_resisted_explosion_free_owner")
    elif mutation == "penalize_explosion_into_immunity":
        apply_rule_delta(mutated, "coverage.cashout.revealed_immunity_guard", 8, include=("explosion", "self-destruct", "destiny", "boom"))
        apply_rule_delta(mutated, "coverage.cashout.preserve_or_cover_immunity", -2, include=("earthquake", "coverage", "handoff", "switch", "preserve"))
        add_policy(mutated, "reversible_before_irreversible")
        add_condition(mutated, "coverage_cashout_immunity_guard")
    elif mutation == "promote_typed_status_absorber":
        apply_rule_delta(mutated, "coverage.absorber.typed_status_absorber", -3, include=("absorber", "switch", "handoff", "guard"))
        apply_rule_delta(mutated, "coverage.absorber.generic_wall_overused", 3, include=("generic", "wall", "valuable"))
        add_policy(mutated, "typed_status_absorber")
        add_condition(mutated, "coverage_typed_status_absorber")
    elif mutation == "promote_pass_receiver_survival":
        apply_rule_delta(mutated, "coverage.pass.receiver_survival", -3, include=("baton pass", "pass", "reflect", "phaze", "roar", "whirlwind"))
        apply_rule_delta(mutated, "coverage.pass.hits_only_passer", 3, include=("damage", "active", "stab"))
        add_policy(mutated, "pass_receiver_survival")
        add_condition(mutated, "coverage_pass_receiver_survival")
    elif mutation == "price_sleep_cashout_package":
        apply_rule_delta(mutated, "coverage.package.sleep_cashout_guard", -3, include=("guard", "switch", "sack", "absorber"))
        apply_rule_delta(mutated, "coverage.package.exposes_key_owner", 4, include=("damage", "setup", "valuable", "wincon"))
        add_policy(mutated, "sleep_plus_cashout_package")
        add_policy(mutated, "role_package_ledger")
        add_condition(mutated, "coverage_sleep_plus_cashout_package")
    else:
        raise PreferenceDataError(f"unknown coverage mutation {mutation!r}")

    add_policy(mutated, "coverage_guided")
    return restamp(mutated)


def apply_rule_delta(
    scenario: dict[str, Any],
    rule: str,
    delta: int,
    *,
    include: tuple[str, ...],
) -> None:
    for move in scenario.get("moves", []):
        if not isinstance(move, dict):
            continue
        surface = f"{move.get('id', '')} {move.get('name', '')} {move.get('kind', '')}".lower()
        if not any(token in surface for token in include):
            continue
        deltas = list(move.get("deltas", []))
        deltas.append({"rule": rule, "delta": delta})
        move["deltas"] = deltas


def add_policy(scenario: dict[str, Any], tag: str) -> None:
    expectation = scenario.setdefault("expectation", {})
    tags = set(expectation.get("policy_tags", []))
    tags.add(tag)
    expectation["policy_tags"] = sorted(tags)


def add_condition(scenario: dict[str, Any], tag: str) -> None:
    expectation = scenario.setdefault("expectation", {})
    tags = set(expectation.get("condition_tags", []))
    tags.add(tag)
    expectation["condition_tags"] = sorted(tags)


def choose_frontier(scenarios: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    if len(scenarios) <= limit:
        return scenarios
    report = evaluate_batch(scenarios)
    severity = {
        item["scenario_id"]: int(item["severity"])
        for item in report["verdicts"]
    }
    return sorted(
        scenarios,
        key=lambda item: (-severity.get(str(item.get("id")), 0), str(item.get("id"))),
    )[:limit]


def select_interesting_scenarios(
    scenarios: list[dict[str, Any]],
    batch: dict[str, Any],
    *,
    keep: int,
) -> list[dict[str, Any]]:
    if keep == 0:
        return []
    by_id = {str(scenario.get("id")): scenario for scenario in scenarios}
    selected: list[dict[str, Any]] = []
    seen_tags: set[str] = set()
    for verdict in batch.get("verdicts", []):
        scenario = by_id.get(str(verdict["scenario_id"]))
        if scenario is None:
            continue
        tags = set(verdict.get("policy_tags", [])) | set(verdict.get("condition_tags", []))
        novelty = tags - seen_tags
        if int(verdict.get("severity", 0)) > 0 or novelty:
            selected.append(scenario)
            seen_tags.update(tags)
        if len(selected) >= keep:
            break
    return selected


def build_search_report(
    *,
    seeds: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    batch: dict[str, Any],
    rounds: int,
    per_seed: int,
    seed: int,
    generated_count: int,
) -> dict[str, Any]:
    selected_ids = {str(scenario.get("id")) for scenario in selected}
    selected_verdicts = [
        item for item in batch.get("verdicts", []) if item["scenario_id"] in selected_ids
    ]
    return {
        "schema_version": 1,
        "seed": seed,
        "rounds": rounds,
        "per_seed": per_seed,
        "generated_count": generated_count,
        "seed_scenario_count": len(seeds),
        "candidate_count": len(candidates),
        "selected_count": len(selected),
        "batch_summary": {
            "scenario_count": batch["scenario_count"],
            "reviewable_count": batch["reviewable_count"],
            "verdict_counts": batch["verdict_counts"],
            "policy_tag_counts": batch["policy_tag_counts"],
        },
        "candidate_policy_tag_counts": count_candidate_tags(candidates, "policy_tags"),
        "candidate_condition_tag_counts": count_candidate_tags(candidates, "condition_tags"),
        "selected_verdicts": selected_verdicts[:50],
        "target_families": list(TARGET_FAMILIES),
        "mutations": list(PUBLIC_MUTATIONS),
        "public_info_boundary": (
            "coverage search mutates only debugger-visible policy tags, tier, and "
            "candidate score deltas; it does not add opponent hidden moves, PP, "
            "held items, current input, or hidden bench facts"
        ),
    }


def count_candidate_tags(scenarios: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for scenario in scenarios:
        expectation = scenario.get("expectation", {})
        if not isinstance(expectation, dict):
            continue
        for tag in expectation.get(key, []):
            text = str(tag)
            counts[text] = counts.get(text, 0) + 1
    return dict(sorted(counts.items()))


def restamp(scenario: dict[str, Any]) -> dict[str, Any]:
    cleaned = {
        key: value
        for key, value in scenario.items()
        if key not in {"state_hash", "rom_sha256", "symbols_sha256", "rom", "symbols"}
    }
    return stamp_scenario(cleaned)


def empty_batch_report() -> dict[str, Any]:
    return {
        "scenario_count": 0,
        "reviewable_count": 0,
        "verdict_counts": {},
        "policy_tag_counts": {},
        "verdicts": [],
    }


def write_coverage_search_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_coverage_search_scenarios(scenarios: list[dict[str, Any]], path: Path) -> None:
    write_jsonl(scenarios, path)


def format_coverage_search_report(report: dict[str, Any]) -> str:
    batch = report["batch_summary"]
    verdicts = " ".join(
        f"{name}={count}" for name, count in batch["verdict_counts"].items()
    )
    tags = " ".join(
        f"{name}={count}" for name, count in batch["policy_tag_counts"].items()
    )
    return "\n".join(
        [
            "Boss AI coverage-guided search",
            (
                f"seeds={report['seed_scenario_count']} candidates={report['candidate_count']} "
                f"selected={report['selected_count']} reviewable={batch['reviewable_count']}"
            ),
            f"verdicts: {verdicts or 'none'}",
            f"review tags: {tags or 'none'}",
        ]
    )
