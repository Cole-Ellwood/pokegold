from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.coverage_report import build_coverage_report
from tools.boss_ai_debugger.counterfactuals import explain_counterfactuals
from tools.boss_ai_debugger.generators import generate_scenarios
from tools.boss_ai_debugger.localize import localize_report
from tools.boss_ai_debugger.mastery_index import build_mastery_index
from tools.boss_ai_debugger.metamorphic import run_metamorphic_suite
from tools.boss_ai_debugger.minimize import minimize_scenario
from tools.boss_ai_debugger.review_queue import build_review_queue
from tools.boss_ai_debugger.rom_scenarios import evaluate_batch
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
    counterfactual = explain_counterfactuals(analysis_scenario)
    minimized = minimize_scenario(analysis_scenario)
    localized = localize_report(batch, scenarios=scenarios, source="foundation_audit")

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
    if not counterfactual["score_flips_to_expected_best"]:
        errors.append("counterfactual analysis did not report expected-best score flips")
    if not minimized["preserved"]:
        errors.append("minimization did not preserve verdict")
    if not localized["likely_causes"]:
        errors.append("localization did not report likely causes")

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
        f"full_trace_rule_coverage={coverage['rule_map']['full_trace_rule_coverage_available']}."
    )
    print(
        "Analysis tools: "
        f"counterfactual={counterfactual['scenario_id']}, "
        f"minimized_preserved={minimized['preserved']}, "
        f"likely_causes={len(localized['likely_causes'])}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
