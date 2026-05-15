from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.coverage_report import build_coverage_report
from tools.boss_ai_debugger.differential import build_differential_report
from tools.boss_ai_debugger.generators import generate_scenarios
from tools.boss_ai_debugger.mastery_index import build_mastery_index
from tools.boss_ai_debugger.review_queue import build_review_queue
from tools.boss_ai_debugger.rom_scenarios import evaluate_batch
from tools.boss_ai_debugger.rom_selector_materialize import (
    DEFAULT_BASE_ROUTE,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_WATCH_FRAMES,
    run_rom_selector_materialization,
)
from tools.boss_ai_debugger.rom_score_materialize import (
    DEFAULT_BASE_ROUTE as DEFAULT_SCORE_BASE_ROUTE,
    DEFAULT_WATCH_FRAMES as DEFAULT_SCORE_WATCH_FRAMES,
    run_rom_score_materialization,
)
from tools.boss_ai_debugger.rule_map import (
    DEFAULT_RULE_MAP_PATH,
    build_rule_map,
    compare_rule_maps,
)
from tools.boss_ai_debugger.state_schema import (
    DEFAULT_TRACE_DIR,
    validate_fixtures_file,
    validate_trace_dir,
)


REPORT_PATH = ROOT / ".local" / "tmp" / "boss_ai_debugger" / "roadmap_audit.json"
MIN_SCENARIOS_PER_MINUTE_DONE = 1_000_000
MIN_REVIEWABLE_PER_MINUTE_DONE = 1_000_000
MIN_ROM_BACKED_REPLAY_PER_MINUTE_DONE = 10_000


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit whether the Boss AI debugger state-of-the-art roadmap is truly done."
        )
    )
    parser.add_argument("--generated-count", type=int, default=120)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--json-out", type=Path, default=REPORT_PATH)
    parser.add_argument(
        "--check-rom-selector-materialization",
        action="store_true",
        help="also run the PyBoy-backed generated selector materialization smoke",
    )
    parser.add_argument(
        "--check-rom-score-materialization",
        action="store_true",
        help="also run the PyBoy-backed generated score-model materialization smoke",
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="write the report and exit zero even when roadmap readiness is incomplete",
    )
    args = parser.parse_args()

    report = build_roadmap_audit(
        generated_count=args.generated_count,
        seed=args.seed,
        check_rom_selector_materialization=args.check_rom_selector_materialization,
        check_rom_score_materialization=args.check_rom_score_materialization,
    )
    write_json(report, args.json_out)
    print(format_roadmap_audit(report))
    print(f"wrote {display_path(args.json_out)}")
    if report["ready"] or args.allow_incomplete:
        return 0
    return 1


def build_roadmap_audit(
    *,
    generated_count: int = 120,
    seed: int = 1,
    check_rom_selector_materialization: bool = False,
    check_rom_score_materialization: bool = False,
) -> dict[str, Any]:
    evidence = collect_evidence(
        generated_count=generated_count,
        seed=seed,
        check_rom_selector_materialization=check_rom_selector_materialization,
        check_rom_score_materialization=check_rom_score_materialization,
    )
    items = roadmap_items(evidence)
    status_counts = count_statuses(items)
    blocking_gaps = [
        gap
        for item in items
        for gap in item["gaps"]
        if item["status"] != "complete"
    ]
    return {
        "schema_version": 1,
        "objective": (
            "Make the Boss AI debugger ROM-accurate, high-throughput, "
            "mastery-aware, and safe to trust after Boss AI edits."
        ),
        "ready": all(item["status"] == "complete" for item in items),
        "status_counts": status_counts,
        "blocking_gap_count": len(blocking_gaps),
        "blocking_gaps": blocking_gaps,
        "items": items,
        "evidence": evidence_summary(evidence),
    }


def collect_evidence(
    *,
    generated_count: int,
    seed: int,
    check_rom_selector_materialization: bool,
    check_rom_score_materialization: bool,
) -> dict[str, Any]:
    fixture_report = validate_fixtures_file()
    trace_report = validate_trace_dir(DEFAULT_TRACE_DIR)
    rule_map = build_rule_map()
    rule_map_errors = compare_rule_maps(rule_map, DEFAULT_RULE_MAP_PATH)
    coverage = build_coverage_report(
        generated_count=generated_count,
        seed=seed,
    )
    trace_paths = sorted(DEFAULT_TRACE_DIR.glob("*_live.txt"))
    differential = build_differential_report(
        trace_paths=trace_paths,
        source="roadmap_audit",
    )
    mastery = build_mastery_index()
    scenarios = generate_scenarios(
        family="all",
        count=generated_count,
        seed=seed,
    )
    batch = evaluate_batch(scenarios)
    queue = build_review_queue(batch, limit=50, max_per_lesson=2)
    selector_materialization = maybe_run_selector_materialization(
        scenarios,
        enabled=check_rom_selector_materialization,
    )
    score_materialization = maybe_run_score_materialization(
        scenarios,
        enabled=check_rom_score_materialization,
    )
    return {
        "generated_count": generated_count,
        "seed": seed,
        "scenarios": scenarios,
        "fixture_report": fixture_report,
        "trace_report": trace_report,
        "rule_map": rule_map,
        "rule_map_errors": rule_map_errors,
        "coverage": coverage,
        "differential": differential,
        "mastery": mastery,
        "batch": batch,
        "queue": queue,
        "selector_materialization": selector_materialization,
        "score_materialization": score_materialization,
    }


def roadmap_items(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    coverage = evidence["coverage"]
    differential = evidence["differential"]
    batch = evidence["batch"]
    queue = evidence["queue"]

    return [
        item(
            "canonical_state_schema",
            "Canonical state schema",
            complete=(
                evidence["fixture_report"]["valid"]
                and evidence["trace_report"]["valid"]
            ),
            evidence=[
                (
                    f"fixture_schema_valid={evidence['fixture_report']['valid']} "
                    f"trace_schema_valid={evidence['trace_report']['valid']}"
                ),
                (
                    "schema_checked="
                    f"{evidence['fixture_report']['checked_count'] + evidence['trace_report']['checked_count']}"
                ),
            ],
            gaps=[],
            refs=[
                "tools/boss_ai_debugger/state_schema.py",
                "tools/boss_ai_debugger/README.md",
            ],
        ),
        item(
            "rule_id_source_map",
            "Rule id and source map",
            complete=(
                evidence["rule_map"]["rule_count"] > 0
                and not evidence["rule_map_errors"]
            ),
            evidence=[
                f"mapped_rules={evidence['rule_map']['rule_count']}",
                f"rule_map_errors={len(evidence['rule_map_errors'])}",
            ],
            gaps=evidence["rule_map_errors"],
            refs=[
                "tools/boss_ai_debugger/rule_map.py",
                "audit/boss_ai_debugger/rule_map.json",
            ],
        ),
        status_item(
            "rom_score_contribution_trace",
            "ROM score contribution trace",
            status=score_trace_status(coverage),
            evidence=[
                (
                    "rom_hook_score_trace="
                    f"{coverage['rule_map']['rom_hook_score_trace_available']}"
                ),
                f"trace_events={coverage['rule_map']['trace_event_count']}",
                f"trace_rule_entries={coverage['rule_map']['trace_rule_entry_count']}",
                (
                    "trace_predicate_branches="
                    f"{coverage['rule_map']['trace_predicate_branch_entry_count']}"
                ),
                f"trace_executed_rules={coverage['rule_map']['trace_executed_rule_count']}",
                f"trace_covered_rules={coverage['rule_map']['trace_covered_rule_count']}",
                (
                    "full_trace_rule_coverage="
                    f"{coverage['rule_map']['full_trace_rule_coverage_available']}"
                ),
            ],
            gaps=score_trace_gaps(coverage),
            refs=[
                "tools/boss_ai_debugger/rom_contribution_trace.py",
                "audit/boss_ai_debugger/rom_contribution_trace_smoke.json",
            ],
        ),
        status_item(
            "rom_python_differential",
            "ROM/Python differential runner",
            status=differential_status(differential),
            evidence=[
                f"selector_trace_checked={differential['trace_summary']['checked_count']}",
                f"selector_trace_failures={differential['trace_summary']['failure_count']}",
                (
                    "selector_exact_agreement="
                    f"{differential['trace_summary']['exact_agreement_rate']:.4%}"
                ),
                (
                    "contribution_matched="
                    f"{differential['contribution_comparison']['matched_trace_count']}"
                ),
            ],
            gaps=differential_gaps(differential),
            refs=["tools/boss_ai_debugger/differential.py"],
        ),
        item(
            "deterministic_scenario_generators",
            "Deterministic scenario generators",
            complete=scenarios_have_identity(evidence),
            evidence=[
                f"generated_count={evidence['generated_count']}",
                f"state_hashes={count_scenarios_with_key(evidence, 'state_hash')}",
                f"rom_hashes={count_scenarios_with_key(evidence, 'rom_sha256')}",
                f"symbol_hashes={count_scenarios_with_key(evidence, 'symbols_sha256')}",
            ],
            gaps=scenario_identity_gaps(evidence),
            refs=["tools/boss_ai_debugger/generators.py"],
        ),
        status_item(
            "coverage_guided_generation",
            "Coverage-guided generation",
            status=coverage_guided_status(coverage),
            evidence=[
                f"mapped_rules={coverage['rule_map']['mapped_rule_count']}",
                f"uncovered_rules={coverage['uncovered_rules']['uncovered_rule_count']}",
                (
                    "suggested_generator_counts="
                    f"{coverage['uncovered_rules']['suggested_generator_counts']}"
                ),
            ],
            gaps=coverage_guided_gaps(coverage),
            refs=["tools/boss_ai_debugger/coverage_report.py"],
        ),
        item(
            "mastery_policy_coverage",
            "Mastery policy coverage",
            complete=(
                coverage["mastery"]["generated_policy_card_coverage_count"]
                == coverage["mastery"]["policy_card_count"]
                and coverage["mastery"]["policy_card_missing_positive_count"] == 0
                and coverage["mastery"]["policy_card_missing_negative_count"] == 0
            ),
            evidence=[
                (
                    "policy_cards="
                    f"{coverage['mastery']['generated_policy_card_coverage_count']}/"
                    f"{coverage['mastery']['policy_card_count']}"
                ),
                (
                    "missing_positive="
                    f"{coverage['mastery']['policy_card_missing_positive_count']}"
                ),
                (
                    "missing_negative="
                    f"{coverage['mastery']['policy_card_missing_negative_count']}"
                ),
            ],
            gaps=[],
            refs=[
                "tools/boss_ai_debugger/mastery_index.py",
                "tools/boss_ai_debugger/review_queue.py",
            ],
        ),
        item(
            "active_review_queue",
            "Active review queue",
            complete=(
                queue["input_reviewable_count"] == batch["reviewable_count"]
                and queue["returned_count"] <= 50
            ),
            evidence=[
                f"reviewable={batch['reviewable_count']}",
                f"queue_inputs={queue['input_reviewable_count']}",
                f"queue_returned={queue['returned_count']}",
            ],
            gaps=[],
            refs=["tools/boss_ai_debugger/review_queue.py"],
        ),
        status_item(
            "debugger_performance_targets",
            "Debugger performance targets",
            status=performance_status(batch),
            evidence=[
                f"scenarios_per_minute={batch['scenarios_per_minute']:.0f}",
                f"reviewable_per_minute={batch['reviewable_per_minute']:.0f}",
                f"target_scenarios_per_minute={MIN_SCENARIOS_PER_MINUTE_DONE}",
                f"target_reviewable_per_minute={MIN_REVIEWABLE_PER_MINUTE_DONE}",
                f"target_rom_backed_replay_per_minute={MIN_ROM_BACKED_REPLAY_PER_MINUTE_DONE}",
            ],
            gaps=performance_gaps(batch),
            refs=["tools/audit/check_boss_ai_debugger_performance.py"],
        ),
        status_item(
            "rom_selector_materialized_generated_scenarios",
            "ROM selector-materialized generated scenarios",
            status=selector_materialization_status(evidence),
            evidence=[
                selector_materialization_evidence(evidence),
                "generated final score bytes are patched at BossAI_SelectMove.first_pass",
            ],
            gaps=selector_materialization_gaps(evidence),
            refs=[
                "tools/boss_ai_debugger/rom_selector_materialize.py",
            ],
        ),
        status_item(
            "rom_score_materialized_generated_scenarios",
            "ROM score-model materialized generated scenarios",
            status=score_materialization_status(evidence),
            evidence=[
                score_materialization_evidence(evidence),
                "generated scenario WRAM is patched before BossAI_ApplyMoveModel.ScoreMove",
            ],
            gaps=score_materialization_gaps(evidence),
            refs=[
                "tools/boss_ai_debugger/rom_score_materialize.py",
                "tools/boss_ai_debugger/differential.py",
                "tools/boss_ai_debugger/rom_contribution_trace.py",
            ],
        ),
        status_item(
            "dynamic_public_read_provenance",
            "Dynamic public-read provenance",
            status=provenance_status(coverage),
            evidence=[
                "rule-map public_reads are static hints",
                (
                    "predicate_branch_entries="
                    f"{coverage['rule_map']['trace_predicate_branch_entry_count']}"
                ),
                "ROM trace known limits say selected branch labels are traced, but dynamic memory-read slicing is absent",
            ],
            gaps=provenance_gaps(coverage),
            refs=[
                "tools/boss_ai_debugger/rule_map.py",
                "tools/boss_ai_debugger/rom_contribution_trace.py",
            ],
        ),
        status_item(
            "analysis_tooling",
            "Mismatch analysis tooling",
            status="complete",
            evidence=[
                "counterfactuals, minimization, localization, mutation, and invariant modules exist",
                "foundation audit exercises each analysis family",
            ],
            gaps=[],
            refs=[
                "tools/boss_ai_debugger/counterfactuals.py",
                "tools/boss_ai_debugger/minimize.py",
                "tools/boss_ai_debugger/localize.py",
                "tools/boss_ai_debugger/mutation.py",
                "tools/boss_ai_debugger/invariants.py",
            ],
        ),
        status_item(
            "multi_turn_route_evaluation",
            "Multi-turn route evaluation",
            status="partial",
            evidence=[
                "route-eval classifies one-turn scenario outcomes",
                "full 2-5 turn branch search is not implemented",
            ],
            gaps=[
                (
                    "Extend route evaluation from one-turn classification to 2-5 "
                    "turn branch search with hazards, spin, phazing, sleep, recovery, "
                    "self-KO, and ace preservation."
                )
            ],
            refs=["tools/boss_ai_debugger/route_eval.py"],
        ),
        status_item(
            "change_adaptation_suite",
            "Changed-AI adaptation suite",
            status="partial",
            evidence=[
                "run-suite --profile changed-ai exists and can optionally refresh one contribution trace",
                "the suite does not rebuild ROMs or refresh the full live trace corpus",
            ],
            gaps=[
                (
                    "Make changed-ai rebuild ROMs, refresh relevant live traces, "
                    "materialize touched-rule generated scenarios, and diff behavior "
                    "against the previous run."
                )
            ],
            refs=[
                "tools/boss_ai_debugger/run_store.py",
                "docs/boss_ai_debugger_changed_ai_suite.md",
            ],
        ),
        status_item(
            "final_one_command_definition_of_done",
            "One-command final definition of done",
            status="partial",
            evidence=[
                "foundation and changed-AI suite commands exist",
                "full score waterfalls and ROM-backed generated diff are not complete",
            ],
            gaps=[
                (
                    "Combine exact replay, full score waterfalls, rule coverage diff, "
                    "targeted generated stress, hidden-info checks, minimized "
                    "mismatches, counterfactuals, mastery refs, top review queue, "
                    "behavior diff, and reproducible metadata into one green gate."
                )
            ],
            refs=[
                "docs/boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md"
            ],
        ),
    ]


def item(
    item_id: str,
    title: str,
    *,
    complete: bool,
    evidence: list[str],
    gaps: list[str],
    refs: list[str],
) -> dict[str, Any]:
    return status_item(
        item_id,
        title,
        status="complete" if complete else "missing",
        evidence=evidence,
        gaps=gaps or ([f"{title} is not complete."] if not complete else []),
        refs=refs,
    )


def status_item(
    item_id: str,
    title: str,
    *,
    status: str,
    evidence: list[str],
    gaps: list[str],
    refs: list[str],
) -> dict[str, Any]:
    if status not in {"complete", "partial", "missing"}:
        raise ValueError(f"unknown status {status!r}")
    return {
        "id": item_id,
        "title": title,
        "status": status,
        "evidence": evidence,
        "gaps": gaps,
        "refs": refs,
    }


def score_trace_status(coverage: dict[str, Any]) -> str:
    if coverage["rule_map"]["trace_event_count"] == 0:
        return "missing"
    if not coverage["rule_map"]["full_trace_rule_coverage_available"]:
        return "partial"
    if coverage["uncovered_rules"]["uncovered_rule_count"]:
        return "partial"
    return "complete"


def score_trace_gaps(coverage: dict[str, Any]) -> list[str]:
    gaps = []
    if coverage["rule_map"]["trace_event_count"] == 0:
        gaps.append("No ROM score contribution events are available.")
    if not coverage["rule_map"]["full_trace_rule_coverage_available"]:
        gaps.append(
            "False predicate paths and dynamic public-read provenance are not traced."
        )
    if coverage["uncovered_rules"]["uncovered_rule_count"]:
        gaps.append(
            "Only "
            f"{coverage['rule_map']['trace_covered_rule_count']} / "
            f"{coverage['rule_map']['mapped_rule_count']} mapped rule ids have "
            "ROM contribution trace coverage."
        )
    return gaps


def provenance_status(coverage: dict[str, Any]) -> str:
    if coverage["rule_map"]["trace_predicate_branch_entry_count"] > 0:
        return "partial"
    return "missing"


def provenance_gaps(coverage: dict[str, Any]) -> list[str]:
    gaps = []
    if coverage["rule_map"]["trace_predicate_branch_entry_count"] == 0:
        gaps.append("No selected public-info predicate branch labels were observed.")
    gaps.append(
        "Trace actual public memory reads and false predicate outcomes so "
        "public-info legality is proven per event instead of inferred from "
        "rule metadata and selected branch labels."
    )
    return gaps


def differential_status(differential: dict[str, Any]) -> str:
    if differential["trace_summary"]["checked_count"] == 0:
        return "missing"
    if differential["trace_summary"]["failure_count"]:
        return "missing"
    if differential["contribution_comparison"]["matched_trace_count"] == 0:
        return "partial"
    if differential["contribution_comparison"]["mismatch_count"]:
        return "partial"
    return "complete"


def differential_gaps(differential: dict[str, Any]) -> list[str]:
    gaps = []
    if differential["trace_summary"]["failure_count"]:
        gaps.append("Selector trace replay has failures.")
    if differential["contribution_comparison"]["matched_trace_count"] == 0:
        gaps.append(
            "No ROM and Python contribution traces share trace ids in the default audit."
        )
    gaps.extend(differential.get("known_gaps", []))
    return gaps


def scenarios_have_identity(evidence: dict[str, Any]) -> bool:
    expected = evidence["generated_count"]
    return (
        count_scenarios_with_key(evidence, "state_hash") == expected
        and count_scenarios_with_key(evidence, "rom_sha256") == expected
        and count_scenarios_with_key(evidence, "symbols_sha256") == expected
    )


def count_scenarios_with_key(evidence: dict[str, Any], key: str) -> int:
    return sum(1 for scenario in evidence["scenarios"] if scenario.get(key))


def scenario_identity_gaps(evidence: dict[str, Any]) -> list[str]:
    gaps = []
    expected = evidence["generated_count"]
    for key in ("state_hash", "rom_sha256", "symbols_sha256"):
        actual = count_scenarios_with_key(evidence, key)
        if actual != expected:
            gaps.append(f"{actual} / {expected} generated scenarios include {key}.")
    return gaps


def coverage_guided_status(coverage: dict[str, Any]) -> str:
    if coverage["rule_map"]["mapped_rule_count"] == 0:
        return "missing"
    if coverage["uncovered_rules"]["uncovered_rule_count"] == 0:
        return "complete"
    return "partial"


def coverage_guided_gaps(coverage: dict[str, Any]) -> list[str]:
    uncovered = coverage["uncovered_rules"]["uncovered_rule_count"]
    if uncovered == 0:
        return []
    return [
        (
            f"{uncovered} mapped rule ids have no ROM contribution coverage; "
            "targeted generators currently suggest families but do not close the "
            "rule-id coverage loop automatically."
        )
    ]


def performance_status(batch: dict[str, Any]) -> str:
    if batch["scenarios_per_minute"] >= MIN_SCENARIOS_PER_MINUTE_DONE and (
        batch["reviewable_count"] == 0
        or batch["reviewable_per_minute"] >= MIN_REVIEWABLE_PER_MINUTE_DONE
    ):
        return "partial"
    return "partial"


def performance_gaps(batch: dict[str, Any]) -> list[str]:
    gaps = []
    if batch["scenarios_per_minute"] < MIN_SCENARIOS_PER_MINUTE_DONE:
        gaps.append(
            "Non-ROM generated scenario triage is below the final "
            f"{MIN_SCENARIOS_PER_MINUTE_DONE:,}/minute target: "
            f"{batch['scenarios_per_minute']:.0f}/minute observed."
        )
    if (
        batch["reviewable_count"] > 0
        and batch["reviewable_per_minute"] < MIN_REVIEWABLE_PER_MINUTE_DONE
    ):
        gaps.append(
            "Reviewable checks are below the final "
            f"{MIN_REVIEWABLE_PER_MINUTE_DONE:,}/minute target: "
            f"{batch['reviewable_per_minute']:.0f}/minute observed."
        )
    gaps.append(
        f"ROM-backed generated decision replay has no proven {MIN_ROM_BACKED_REPLAY_PER_MINUTE_DONE:,}/minute gate yet."
    )
    return gaps


def count_statuses(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"complete": 0, "partial": 0, "missing": 0}
    for item_data in items:
        counts[item_data["status"]] += 1
    return counts


def evidence_summary(evidence: dict[str, Any]) -> dict[str, Any]:
    coverage = evidence["coverage"]
    differential = evidence["differential"]
    batch = evidence["batch"]
    queue = evidence["queue"]
    return {
        "generated_count": evidence["generated_count"],
        "seed": evidence["seed"],
        "fixture_schema_valid": evidence["fixture_report"]["valid"],
        "trace_schema_valid": evidence["trace_report"]["valid"],
        "rule_count": evidence["rule_map"]["rule_count"],
        "rule_map_error_count": len(evidence["rule_map_errors"]),
        "mapped_rule_count": coverage["rule_map"]["mapped_rule_count"],
        "trace_covered_rule_count": coverage["rule_map"]["trace_covered_rule_count"],
        "trace_executed_rule_count": coverage["rule_map"]["trace_executed_rule_count"],
        "trace_rule_entry_count": coverage["rule_map"]["trace_rule_entry_count"],
        "trace_predicate_branch_entry_count": coverage["rule_map"][
            "trace_predicate_branch_entry_count"
        ],
        "uncovered_rule_count": coverage["uncovered_rules"]["uncovered_rule_count"],
        "full_trace_rule_coverage_available": coverage["rule_map"][
            "full_trace_rule_coverage_available"
        ],
        "policy_card_count": coverage["mastery"]["policy_card_count"],
        "policy_card_missing_positive_count": coverage["mastery"][
            "policy_card_missing_positive_count"
        ],
        "policy_card_missing_negative_count": coverage["mastery"][
            "policy_card_missing_negative_count"
        ],
        "selector_trace_checked_count": differential["trace_summary"]["checked_count"],
        "selector_trace_failure_count": differential["trace_summary"]["failure_count"],
        "selector_exact_agreement_rate": differential["trace_summary"][
            "exact_agreement_rate"
        ],
        "contribution_matched_trace_count": differential[
            "contribution_comparison"
        ]["matched_trace_count"],
        "selector_materialization": evidence["selector_materialization"],
        "score_materialization": evidence["score_materialization"],
        "scenarios_per_minute": batch["scenarios_per_minute"],
        "reviewable_per_minute": batch["reviewable_per_minute"],
        "reviewable_count": batch["reviewable_count"],
        "queue_returned_count": queue["returned_count"],
    }


def format_roadmap_audit(report: dict[str, Any]) -> str:
    lines = [
        "Boss AI debugger roadmap audit",
        f"ready={report['ready']} status_counts={report['status_counts']}",
        f"blocking_gaps={report['blocking_gap_count']}",
    ]
    lines.append("")
    lines.append("Items:")
    for item_data in report["items"]:
        lines.append(
            f"  - {item_data['status']}: {item_data['id']} - {item_data['title']}"
        )
        for gap in item_data["gaps"][:2]:
            lines.append(f"      gap: {gap}")
    if report["blocking_gaps"]:
        lines.append("")
        lines.append("Top blocking gaps:")
        for gap in report["blocking_gaps"][:8]:
            lines.append(f"  - {gap}")
    return "\n".join(lines)


def maybe_run_selector_materialization(
    scenarios: list[dict[str, Any]],
    *,
    enabled: bool,
) -> dict[str, Any]:
    if not enabled:
        return {
            "available": False,
            "checked": False,
            "reason": "not requested; pass --check-rom-selector-materialization to run it",
        }
    selector_scenarios = [
        scenario
        for scenario in scenarios
        if scenario.get("family") == "selector_edges"
    ][:4]
    if not selector_scenarios:
        return {
            "available": False,
            "checked": False,
            "reason": "no selector_edges scenarios available in generated sample",
        }
    try:
        report = run_rom_selector_materialization(
            selector_scenarios,
            base_route=DEFAULT_BASE_ROUTE,
            manifest_path=DEFAULT_MANIFEST_PATH,
            watch_frames=DEFAULT_WATCH_FRAMES,
            source="roadmap_audit",
        )
    except Exception as exc:
        return {
            "available": False,
            "checked": True,
            "reason": str(exc),
        }
    return {
        "available": report["mismatch_count"] == 0 and report["checked_count"] > 0,
        "checked": True,
        "checked_count": report["checked_count"],
        "mismatch_count": report["mismatch_count"],
        "agreement_rate": report["agreement_rate"],
        "materializations_per_minute": report["materializations_per_minute"],
        "known_limits": report["known_limits"],
    }


def selector_materialization_status(evidence: dict[str, Any]) -> str:
    data = evidence["selector_materialization"]
    if not data.get("checked"):
        return "partial"
    if data.get("available"):
        return "complete"
    return "missing"


def selector_materialization_evidence(evidence: dict[str, Any]) -> str:
    data = evidence["selector_materialization"]
    if not data.get("checked"):
        return str(data.get("reason", "selector materialization not checked"))
    if not data.get("available"):
        return f"selector materialization unavailable: {data.get('reason', '')}"
    return (
        f"selector_checked={data['checked_count']} "
        f"mismatches={data['mismatch_count']} "
        f"agreement={data['agreement_rate']:.4%} "
        f"rate={data['materializations_per_minute']:.0f}/min"
    )


def selector_materialization_gaps(evidence: dict[str, Any]) -> list[str]:
    data = evidence["selector_materialization"]
    if not data.get("checked"):
        return [
            (
                "ROM selector materialization exists but was not run in this audit; "
                "use --check-rom-selector-materialization when PyBoy and states are available."
            )
        ]
    if data.get("available"):
        return []
    return [str(data.get("reason", "ROM selector materialization failed"))]


def maybe_run_score_materialization(
    scenarios: list[dict[str, Any]],
    *,
    enabled: bool,
) -> dict[str, Any]:
    if not enabled:
        return {
            "available": False,
            "checked": False,
            "reason": "not requested; pass --check-rom-score-materialization to run it",
        }
    score_scenarios = score_materialization_scenarios(scenarios, limit=3)
    if not score_scenarios:
        return {
            "available": False,
            "checked": False,
            "reason": "no spikes_spin scenarios available in generated sample",
        }
    try:
        report = run_rom_score_materialization(
            score_scenarios,
            base_route=DEFAULT_SCORE_BASE_ROUTE,
            manifest_path=DEFAULT_MANIFEST_PATH,
            watch_frames=DEFAULT_SCORE_WATCH_FRAMES,
            source="roadmap_audit",
        )
    except Exception as exc:
        return {
            "available": False,
            "checked": True,
            "reason": str(exc),
        }
    return {
        "available": (
            report["checked_count"] > 0
            and report["error_count"] == 0
            and report["contribution_matched_count"] > 0
        ),
        "checked": True,
        "checked_count": report["checked_count"],
        "error_count": report["error_count"],
        "score_bytes_match_count": report["score_bytes_match_count"],
        "selector_top_match_count": report["selector_top_match_count"],
        "contribution_matched_count": report["contribution_matched_count"],
        "contribution_mismatch_count": report["contribution_mismatch_count"],
        "materializations_per_minute": report["materializations_per_minute"],
        "known_limits": report["known_limits"],
    }


def score_materialization_status(evidence: dict[str, Any]) -> str:
    data = evidence["score_materialization"]
    if not data.get("checked"):
        return "partial"
    if data.get("available"):
        return "complete"
    return "missing"


def score_materialization_evidence(evidence: dict[str, Any]) -> str:
    data = evidence["score_materialization"]
    if not data.get("checked"):
        return str(data.get("reason", "score materialization not checked"))
    if not data.get("available"):
        return f"score materialization unavailable: {data.get('reason', '')}"
    return (
        f"score_checked={data['checked_count']} "
        f"errors={data['error_count']} "
        f"score_matches={data['score_bytes_match_count']} "
        f"contribution_matched={data['contribution_matched_count']} "
        f"contribution_mismatches={data['contribution_mismatch_count']} "
        f"rate={data['materializations_per_minute']:.0f}/min"
    )


def score_materialization_gaps(evidence: dict[str, Any]) -> list[str]:
    data = evidence["score_materialization"]
    if not data.get("checked"):
        return [
            (
                "ROM score materialization exists but was not run in this audit; "
                "use --check-rom-score-materialization when PyBoy and states are available."
            )
        ]
    if data.get("available"):
        return []
    return [str(data.get("reason", "ROM score materialization failed"))]


def score_materialization_scenarios(
    scenarios: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    candidates = [
        scenario
        for scenario in scenarios
        if scenario.get("family") == "spikes_spin"
    ]

    def priority(scenario: dict[str, Any]) -> tuple[int, str]:
        expectation = scenario.get("expectation", {})
        tags = (
            set(expectation.get("condition_tags", []))
            if isinstance(expectation, dict)
            else set()
        )
        active_revealed = "active_revealed_rapid_spin" in tags
        risky_layer = "spikes_layers_1" in tags or "spikes_layers_2" in tags
        return (0 if active_revealed and risky_layer else 1, str(scenario.get("id", "")))

    return sorted(candidates, key=priority)[:limit]


def write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
