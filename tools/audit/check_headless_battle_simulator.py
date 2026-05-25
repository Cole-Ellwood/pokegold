from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.rom_scenarios import select_from_score_bytes
from tools.headless_battle.simulator import scenario_template, simulate_payload, run_self_test


def main() -> int:
    try:
        run_self_test()
    except Exception as exc:
        print(f"Headless battle simulator audit FAILED: self-test failed: {exc}", file=sys.stderr)
        return 1
    print("simulator_self_test: PASS")
    selector = select_from_score_bytes(
        scenario_id="headless_audit_selector",
        tier="late",
        move_ids=[33, 52, 0, 0],
        scores=[20, 30, 80, 80],
    )
    if not selector.get("ready") or selector.get("best_slot_index") != 0:
        print(f"Headless battle simulator audit FAILED: selector replay mismatch: {selector}", file=sys.stderr)
        return 1
    print("boss_ai_selector_reuse: PASS best_slot=0")
    exhaustive_payload = scenario_template()
    exhaustive_payload["rng"] = {"mode": "exhaustive"}
    exhaustive_payload["state"]["player"]["moves"][0]["accuracy"] = 255
    exhaustive_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    exhaustive_report = simulate_payload(exhaustive_payload)
    if exhaustive_report.get("outcome_count") != 78:
        print(
            "Headless battle simulator audit FAILED: exhaustive damage variation "
            f"expected 78 critical/damage-variation outcomes, got {exhaustive_report.get('outcome_count')}",
            file=sys.stderr,
        )
        return 1
    critical_values = {
        outcome["events"][0]["critical_check"]["critical"]
        for outcome in exhaustive_report["outcomes"]
    }
    if critical_values != {False, True}:
        print(
            f"Headless battle simulator audit FAILED: critical branches missing: {critical_values}",
            file=sys.stderr,
        )
        return 1
    print("damage_variation_exhaustive: PASS outcomes=78 includes_critical=True")
    speed_tie_payload = scenario_template()
    speed_tie_payload["rng"] = {"mode": "exhaustive"}
    speed_tie_payload["state"]["player"]["moves"][0]["bp"] = 0
    speed_tie_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    speed_tie_payload["state"]["enemy"]["stats"]["speed"] = speed_tie_payload["state"]["player"]["stats"]["speed"]
    speed_tie_report = simulate_payload(speed_tie_payload)
    orders = {tuple(outcome["turn_order"]) for outcome in speed_tie_report["outcomes"]}
    if speed_tie_report.get("outcome_count") != 2 or orders != {("player", "enemy"), ("enemy", "player")}:
        print(
            f"Headless battle simulator audit FAILED: speed-tie branches mismatch: {speed_tie_report}",
            file=sys.stderr,
        )
        return 1
    print("speed_tie_exhaustive: PASS outcomes=2")
    multi_turn_payload = scenario_template()
    multi_turn_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    multi_turn_payload.pop("actions")
    multi_turn_payload["turns"] = [
        {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
        {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    ]
    multi_turn_report = simulate_payload(multi_turn_payload)
    outcome = multi_turn_report["outcomes"][0]
    if outcome.get("turns_simulated") != 2 or [row["turn"] for row in outcome.get("turn_orders", [])] != [1, 2]:
        print(
            f"Headless battle simulator audit FAILED: multi-turn progression mismatch: {outcome}",
            file=sys.stderr,
        )
        return 1
    print("multi_turn_selected_actions: PASS turns=2")
    miss_payload = scenario_template()
    miss_payload["state"]["player"]["moves"][0]["accuracy"] = 242
    miss_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    miss_payload["rng"] = {"mode": "fixed", "values": [255, 255, 255]}
    miss_report = simulate_payload(miss_payload)
    miss_event = miss_report["outcomes"][0]["events"][0]
    if miss_event.get("type") != "miss" or miss_event.get("accuracy_check", {}).get("threshold") != 242:
        print(
            f"Headless battle simulator audit FAILED: accuracy miss mismatch: {miss_event}",
            file=sys.stderr,
        )
        return 1
    print("basic_accuracy_miss: PASS threshold=242 raw=255")
    crit_payload = scenario_template()
    crit_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    crit_payload["rng"] = {"mode": "fixed", "values": [0, 255, 0]}
    crit_event = simulate_payload(crit_payload)["outcomes"][0]["events"][0]
    if not crit_event.get("critical_check", {}).get("critical"):
        print(
            f"Headless battle simulator audit FAILED: fixed critical mismatch: {crit_event}",
            file=sys.stderr,
        )
        return 1
    print("basic_critical_hit: PASS raw=0")
    poison_payload = scenario_template()
    poison_payload["state"]["player"]["status"] = "poison"
    poison_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    poison_report = simulate_payload(poison_payload)
    residual_events = [
        event for event in poison_report["outcomes"][0]["events"]
        if event.get("type") == "residual_damage"
    ]
    if (
        len(residual_events) != 1
        or residual_events[0].get("status") != "poison"
        or residual_events[0].get("damage") != 2
    ):
        print(
            f"Headless battle simulator audit FAILED: poison residual mismatch: {poison_report}",
            file=sys.stderr,
        )
        return 1
    print("basic_status_residual: PASS poison_damage=2")
    proc = subprocess.run(
        [sys.executable, "-m", "tools.damage_debugger.clobber_smoke"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
    if proc.returncode != 0:
        print("Headless battle simulator audit FAILED: damage oracle smoke failed.", file=sys.stderr)
        return 1
    print("Headless battle simulator audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
