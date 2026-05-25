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
    exhaustive_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    exhaustive_report = simulate_payload(exhaustive_payload)
    if exhaustive_report.get("outcome_count") != 39:
        print(
            "Headless battle simulator audit FAILED: exhaustive damage variation "
            f"expected 39 outcomes, got {exhaustive_report.get('outcome_count')}",
            file=sys.stderr,
        )
        return 1
    print("damage_variation_exhaustive: PASS outcomes=39")
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
