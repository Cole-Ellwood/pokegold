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
    pp_payload = scenario_template()
    pp_report = simulate_payload(pp_payload)
    pp_outcome = pp_report["outcomes"][0]
    if (
        pp_outcome["state"]["player"]["moves"][0].get("pp") != 34
        or pp_outcome["state"]["enemy"]["moves"][0].get("pp") != 34
    ):
        print(f"Headless battle simulator audit FAILED: PP decrement mismatch: {pp_outcome}", file=sys.stderr)
        return 1
    print("basic_pp_decrement: PASS pp=35->34")
    after_hit_payload = scenario_template()
    after_hit_payload["state"]["player"]["max_hp"] = 30
    after_hit_payload["state"]["player"]["hp"] = 30
    after_hit_payload["state"]["enemy"]["item"] = "ROCKY_HELMET"
    after_hit_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    after_hit_report = simulate_payload(after_hit_payload)
    after_hit_events = after_hit_report["outcomes"][0]["events"]
    rocky_events = [event for event in after_hit_events if event.get("source_item") == "ROCKY_HELMET"]
    if len(rocky_events) != 1 or rocky_events[0].get("damage") != 5:
        print(
            f"Headless battle simulator audit FAILED: Rocky Helmet mismatch: {after_hit_events}",
            file=sys.stderr,
        )
        return 1
    shell_payload = scenario_template()
    shell_payload["state"]["player"]["item"] = "SHELL_BELL"
    shell_payload["state"]["player"]["hp"] = 10
    shell_payload["state"]["player"]["max_hp"] = 30
    shell_payload["state"]["enemy"]["hp"] = 30
    shell_payload["state"]["enemy"]["max_hp"] = 30
    shell_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    shell_payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}
    shell_events = simulate_payload(shell_payload)["outcomes"][0]["events"]
    shell_items = [event for event in shell_events if event.get("source_item") == "SHELL_BELL"]
    if (
        len(shell_items) != 1
        or shell_items[0].get("type") != "after_hit_heal"
        or shell_items[0].get("heal", 0) <= 0
    ):
        print(
            f"Headless battle simulator audit FAILED: Shell Bell mismatch: {shell_events}",
            file=sys.stderr,
        )
        return 1
    life_payload = scenario_template()
    life_payload["state"]["player"]["item"] = "LIFE_ORB"
    life_payload["state"]["player"]["max_hp"] = 30
    life_payload["state"]["player"]["hp"] = 30
    life_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    life_events = simulate_payload(life_payload)["outcomes"][0]["events"]
    life_items = [event for event in life_events if event.get("source_item") == "LIFE_ORB"]
    if len(life_items) != 1 or life_items[0].get("damage") != 3:
        print(
            f"Headless battle simulator audit FAILED: Life Orb mismatch: {life_events}",
            file=sys.stderr,
        )
        return 1
    print("supported_after_hit_items: PASS rocky=5 shell_heal>0 life=3")
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
    selector_move_payload = scenario_template()
    selector_move_payload["state"]["player"]["moves"][0]["bp"] = 0
    selector_move_payload["state"]["enemy"]["moves"] = [
        {"name": "TACKLE", "type": "NORMAL", "bp": 0},
        {"name": "EMBER", "type": "FIRE", "bp": 40},
    ]
    selector_move_payload["actions"]["enemy"] = {
        "type": "boss_ai_selector_move",
        "scenario_id": "headless_audit_selector_execute",
        "tier": "late",
        "move_ids": [33, 52, 0, 0],
        "scores": [20, 21, 80, 80],
    }
    selector_move_payload["rng"] = {"mode": "fixed", "values": [200, 255, 255]}
    selector_move_report = simulate_payload(selector_move_payload)
    selector_move_events = selector_move_report["outcomes"][0]["events"]
    if (
        selector_move_events[0].get("selected_slot_index") != 1
        or selector_move_events[-1].get("move") != "EMBER"
    ):
        print(
            f"Headless battle simulator audit FAILED: selector execution mismatch: {selector_move_events}",
            file=sys.stderr,
        )
        return 1
    print("boss_ai_selector_execution: PASS raw=200 selected=EMBER")
    wild_payload = scenario_template()
    wild_payload["state"]["player"]["moves"][0]["bp"] = 0
    wild_payload["state"]["enemy"]["moves"] = [
        {"name": "TACKLE", "type": "NORMAL", "bp": 0, "pp": 0},
        {"name": "EMBER", "type": "FIRE", "bp": 40, "pp": 1},
    ]
    wild_payload["actions"]["enemy"] = {"type": "wild_random_move"}
    wild_payload["rng"] = {"mode": "fixed", "values": [0, 1, 255, 255]}
    wild_report = simulate_payload(wild_payload)
    wild_events = wild_report["outcomes"][0]["events"]
    if (
        wild_events[0].get("type") != "wild_random_move"
        or wild_events[0].get("selected_slot_index") != 1
        or wild_events[-1].get("move") != "EMBER"
    ):
        print(
            f"Headless battle simulator audit FAILED: wild random move mismatch: {wild_events}",
            file=sys.stderr,
        )
        return 1
    print("wild_random_move_choice: PASS rejected_slot=0 selected=EMBER")
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
    switch_payload = scenario_template()
    switch_payload["state"]["player"]["bench"] = [
        {
            "name": "RESERVE",
            "hp": 30,
            "max_hp": 30,
            "types": ["NORMAL", "NORMAL"],
            "stats": {"attack": 10, "defense": 10, "speed": 9, "sp_attack": 10, "sp_defense": 10},
            "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
        }
    ]
    switch_payload["actions"]["player"] = {"type": "switch", "bench_index": 0}
    switch_report = simulate_payload(switch_payload)
    switch_outcome = switch_report["outcomes"][0]
    if (
        [event.get("type") for event in switch_outcome["events"]] != ["switch", "damage"]
        or switch_outcome["state"]["player"]["name"] != "RESERVE"
    ):
        print(
            f"Headless battle simulator audit FAILED: selected switch mismatch: {switch_outcome}",
            file=sys.stderr,
        )
        return 1
    replacement_payload = scenario_template()
    replacement_payload["state"]["enemy"]["hp"] = 1
    replacement_payload["state"]["enemy"]["max_hp"] = 1
    replacement_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    replacement_payload["state"]["enemy"]["bench"] = [
        {
            "name": "ENEMY_RESERVE",
            "hp": 1,
            "max_hp": 1,
            "types": ["NORMAL", "NORMAL"],
            "stats": {"attack": 10, "defense": 10, "speed": 8, "sp_attack": 10, "sp_defense": 10},
            "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0}],
        }
    ]
    replacement_payload.pop("actions")
    replacement_payload["turns"] = [
        {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
        {"enemy": {"type": "replace", "bench_index": 0}},
        {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    ]
    replacement_report = simulate_payload(replacement_payload)
    replacement_events = [event.get("type") for event in replacement_report["outcomes"][0]["events"]]
    if replacement_events != ["damage", "replacement", "damage"]:
        print(
            f"Headless battle simulator audit FAILED: replacement mismatch: {replacement_report}",
            file=sys.stderr,
        )
        return 1
    print("selected_switch_and_replacement: PASS switch_then_replace")
    auto_replace_payload = scenario_template()
    auto_replace_payload["state"]["player"]["types"] = ["FIRE", "FIRE"]
    auto_replace_payload["state"]["enemy"]["hp"] = 0
    auto_replace_payload["state"]["enemy"]["bench"] = [
        {
            "name": "NEUTRAL_RESERVE",
            "hp": 20,
            "max_hp": 20,
            "types": ["NORMAL", "NORMAL"],
            "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
        },
        {
            "name": "WATER_RESERVE",
            "hp": 20,
            "max_hp": 20,
            "types": ["WATER", "WATER"],
            "moves": [{"name": "WATER_GUN", "type": "WATER", "bp": 40}],
        },
    ]
    auto_replace_payload["actions"]["enemy"] = {"type": "auto_replace"}
    auto_replace_report = simulate_payload(auto_replace_payload)
    auto_replace_events = auto_replace_report["outcomes"][0]["events"]
    auto_replace_choices = [
        event for event in auto_replace_events
        if event.get("type") == "auto_replacement_choice"
    ]
    if (
        len(auto_replace_choices) != 1
        or auto_replace_choices[0].get("selected_bench_index") != 1
        or auto_replace_choices[0].get("reason") != "candidate_super_effective_move"
    ):
        print(
            f"Headless battle simulator audit FAILED: auto replacement mismatch: {auto_replace_report}",
            file=sys.stderr,
        )
        return 1
    print("auto_replacement_choice_basic_type_chart: PASS selected=WATER_RESERVE")
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
