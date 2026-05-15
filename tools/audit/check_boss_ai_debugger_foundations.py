from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.coverage_report import build_coverage_report
from tools.boss_ai_debugger.counterfactuals import explain_counterfactuals
from tools.boss_ai_debugger.decision_trace import decision_trace_for_scenario
from tools.boss_ai_debugger.differential import build_differential_report
from tools.boss_ai_debugger.generators import generate_scenarios
from tools.boss_ai_debugger.invariants import mine_invariants
from tools.boss_ai_debugger.localize import localize_report
from tools.boss_ai_debugger.mastery_index import build_mastery_index
from tools.boss_ai_debugger.metamorphic import run_metamorphic_suite
from tools.boss_ai_debugger.minimize import minimize_scenario
from tools.boss_ai_debugger.mutation import remove_rule_mutant, run_scorer_mutations
from tools.boss_ai_debugger.review_queue import build_review_queue
from tools.boss_ai_debugger.rom_scenarios import evaluate_batch
from tools.boss_ai_debugger.route_eval import evaluate_route_batch
from tools.boss_ai_debugger.rule_map import (
    DEFAULT_RULE_MAP_PATH,
    build_rule_map,
    compare_rule_maps,
)
from tools.boss_ai_debugger.state_schema import (
    DEFAULT_TRACE_DIR,
    format_validation_report,
    validate_fixtures_file,
    validate_trace_dir,
)


ROM_CONTRIBUTION_TRACE_SMOKE = (
    ROOT / "audit" / "boss_ai_debugger" / "rom_contribution_trace_smoke.json"
)


def main() -> int:
    fixture_report = validate_fixtures_file()
    trace_report = validate_trace_dir(DEFAULT_TRACE_DIR)
    rule_map = build_rule_map()
    rule_errors = compare_rule_maps(rule_map, DEFAULT_RULE_MAP_PATH)

    scenarios = generate_scenarios(family="all", count=100, seed=1)
    batch = evaluate_batch(scenarios)
    queue = build_review_queue(batch, limit=20)
    metamorphic = run_metamorphic_suite(generated=25, seed=1)
    mastery = build_mastery_index()
    coverage = build_coverage_report(generated_count=100, seed=1)
    reviewable = [
        verdict for verdict in batch["verdicts"] if int(verdict.get("severity", 0)) > 0
    ]
    analysis_scenario = next(
        (
            scenario
            for scenario in scenarios
            if any(verdict["scenario_id"] == scenario["id"] for verdict in reviewable)
        ),
        scenarios[0],
    )
    decision_trace = decision_trace_for_scenario(analysis_scenario)
    counterfactual = explain_counterfactuals(analysis_scenario)
    minimized = minimize_scenario(analysis_scenario)
    localized = localize_report(batch, scenarios=scenarios, source="foundation_audit")
    route_eval = evaluate_route_batch(scenarios, source="foundation_audit")
    differential = build_differential_report(
        scenarios=scenarios,
        trace_paths=sorted(DEFAULT_TRACE_DIR.glob("*_live.txt")),
        source="foundation_audit",
    )
    invariants = mine_invariants(
        scenarios=scenarios,
        trace_paths=sorted(DEFAULT_TRACE_DIR.glob("*_live.txt")),
    )
    mutation = run_scorer_mutations(
        [mutation_fixture()],
        [mutation_label()],
        mutants=[
            remove_rule_mutant(
                "audit.remove_coverage",
                "coverage",
                "Remove coverage.",
                "medium",
            )
        ],
    )
    rom_contribution_trace = load_rom_contribution_trace_smoke()

    errors: list[str] = []
    if not fixture_report["valid"]:
        errors.extend(fixture_report["errors"])
    if not trace_report["valid"]:
        errors.extend(trace_report["errors"])
    errors.extend(rule_errors)
    if batch["scenario_count"] != 100:
        errors.append("generated smoke batch did not evaluate 100 scenarios")
    if queue["input_reviewable_count"] != batch["reviewable_count"]:
        errors.append("review queue did not preserve reviewable count")
    if not metamorphic["passed"]:
        errors.append("metamorphic suite reported failures")
    if mastery["policy_card_count"] == 0:
        errors.append("mastery index found no policy cards")
    if coverage["mastery"]["policy_card_count"] != mastery["policy_card_count"]:
        errors.append("coverage report mastery policy-card count mismatch")
    if coverage["rule_map"]["trace_covered_rule_count"] == 0:
        errors.append("coverage report did not aggregate ROM contribution rules")
    if coverage["uncovered_rules"]["uncovered_rule_count"] == 0:
        errors.append("coverage report did not expose uncovered mapped rules")
    if (
        coverage["mastery"]["generated_policy_card_coverage_count"]
        != coverage["mastery"]["policy_card_count"]
    ):
        errors.append("generated scenarios do not cover every mastery policy card")
    if coverage["mastery"]["policy_card_missing_positive_count"] != 0:
        errors.append("generated scenarios are missing positive policy-card coverage")
    if coverage["mastery"]["policy_card_missing_negative_count"] != 0:
        errors.append("generated scenarios are missing negative policy-card coverage")
    if not counterfactual["score_flips_to_expected_best"]:
        errors.append("counterfactual analysis did not report expected-best score flips")
    if decision_trace["event_count"] == 0:
        errors.append("decision trace did not report events")
    if not any(
        event["event_type"] == "selector" for event in decision_trace["events"]
    ):
        errors.append("decision trace did not include selector event")
    if not minimized["preserved"]:
        errors.append("minimization did not preserve verdict")
    if not localized["likely_causes"]:
        errors.append("localization did not report likely causes")
    if route_eval["scenario_count"] != len(scenarios):
        errors.append("route evaluation did not classify every generated scenario")
    if not route_eval["classification_counts"]:
        errors.append("route evaluation did not report classification counts")
    if differential["scenario_count"] != len(scenarios):
        errors.append("differential report did not include every generated scenario")
    if "known_gaps" not in differential:
        errors.append("differential report did not preserve known gaps")
    if differential["rom_contribution_summary"]["covered_rule_count"] == 0:
        errors.append("differential report did not summarize ROM contribution rules")
    if differential["contribution_comparison"]["rom_trace_count"] == 0:
        errors.append("differential report did not load ROM contribution traces")
    if invariants["candidate_count"] == 0:
        errors.append("invariant miner did not produce candidates")
    if mutation["killed_count"] != 1:
        errors.append("mutation smoke did not kill the coverage-removal mutant")
    if rom_contribution_trace["event_count"] == 0:
        errors.append("ROM contribution trace smoke has no score events")
    if rom_contribution_trace["changed_event_count"] == 0:
        errors.append("ROM contribution trace smoke has no changed score events")

    if errors:
        print("Boss AI debugger foundation audit failed.")
        for error in errors[:20]:
            print(f"  - {error}")
        if len(errors) > 20:
            print(f"  ... {len(errors) - 20} more")
        return 1

    print("Boss AI debugger foundation audit passed.")
    print(format_validation_report(fixture_report))
    print(format_validation_report(trace_report))
    print(
        "Rule map: "
        f"{rule_map['rule_count']} rules, stored artifact matches current source."
    )
    print(
        "Generated smoke: "
        f"{batch['scenario_count']} scenarios, "
        f"{batch['reviewable_count']} reviewable, "
        f"{batch['scenarios_per_minute']:.0f}/min."
    )
    print(
        "Metamorphic: "
        f"{metamorphic['pass_count']} / {metamorphic['relation_count']} relations passed."
    )
    print(
        "Mastery coverage: "
        f"{coverage['mastery']['generated_policy_card_coverage_count']} / "
        f"{coverage['mastery']['policy_card_count']} policy cards covered by generated refs; "
        f"missing_pos={coverage['mastery']['policy_card_missing_positive_count']}; "
        f"missing_neg={coverage['mastery']['policy_card_missing_negative_count']}; "
        f"score_trace_rules={coverage['rule_map']['trace_covered_rule_count']}; "
        f"uncovered_rules={coverage['uncovered_rules']['uncovered_rule_count']}; "
        f"full_trace_rule_coverage={coverage['rule_map']['full_trace_rule_coverage_available']}."
    )
    print(
        "Analysis tools: "
        f"decision_events={decision_trace['event_count']}, "
        f"counterfactual={counterfactual['scenario_id']}, "
        f"minimized_preserved={minimized['preserved']}, "
        f"likely_causes={len(localized['likely_causes'])}."
    )
    print(
        "Trust tools: "
        f"invariant_candidates={invariants['candidate_count']}, "
        f"invariant_violations={invariants['violation_count']}, "
        f"mutants_killed={mutation['killed_count']} / {mutation['mutant_count']}."
    )
    print(
        "Route eval: "
        f"{route_eval['scenario_count']} scenarios, "
        f"classifications={route_eval['classification_counts']}."
    )
    print(
        "Differential: "
        f"{differential['mismatch_count']} mismatches, "
        f"classes={differential['mismatch_class_counts']}, "
        f"score_trace_rules={differential['rom_contribution_summary']['covered_rule_count']}, "
        f"contribution_matched={differential['contribution_comparison']['matched_trace_count']}."
    )
    print(
        "ROM contribution trace: "
        f"{rom_contribution_trace['event_count']} events, "
        f"{rom_contribution_trace['changed_event_count']} changed."
    )
    return 0


def load_rom_contribution_trace_smoke() -> dict:
    if not ROM_CONTRIBUTION_TRACE_SMOKE.exists():
        return {"event_count": 0, "changed_event_count": 0}
    data = json.loads(ROM_CONTRIBUTION_TRACE_SMOKE.read_text(encoding="utf-8"))
    return {
        "event_count": int(data.get("event_count", 0)),
        "changed_event_count": int(data.get("changed_event_count", 0)),
    }


def mutation_fixture() -> dict:
    return {
        "id": "foundation_mutation_fixture",
        "leader": "Tester",
        "state": {},
        "actions": [
            {
                "id": "move_crunch",
                "kind": "move",
                "name": "Crunch",
                "explanation": "coverage move",
                "public_tradeoff": "punish visible pressure",
            },
            {
                "id": "move_tackle",
                "kind": "move",
                "name": "Tackle",
                "explanation": "plain move",
                "public_tradeoff": "neutral",
            },
        ],
    }


def mutation_label() -> dict:
    return {
        "fixture_id": "foundation_mutation_fixture",
        "state_version": 1,
        "action_a_id": "move_crunch",
        "action_b_id": "move_tackle",
        "choice": "a_better",
        "preferred_action_id": "move_crunch",
        "reason_tags": [],
        "action_tags": {"move_crunch": [], "move_tackle": []},
        "note": "foundation audit label",
        "created_at": "2026-05-15T00:00:00+00:00",
        "tool_version": "boss-ai-preference-v0",
    }


if __name__ == "__main__":
    raise SystemExit(main())
