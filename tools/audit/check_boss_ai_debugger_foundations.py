from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.generators import generate_scenarios
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
