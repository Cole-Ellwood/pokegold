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
    item_payload = scenario_template()
    item_payload["state"]["player"]["hp"] = 5
    item_payload["state"]["player"]["max_hp"] = 32
    item_payload["state"]["player"]["status"] = "poison"
    item_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    item_payload["actions"]["player"] = {"type": "item", "item": "POTION"}
    item_events = simulate_payload(item_payload)["outcomes"][0]["events"]
    if (
        [event.get("type") for event in item_events[:2]] != ["item_restore", "residual_damage"]
        or item_events[0].get("heal") != 20
        or item_events[1].get("damage") != 4
    ):
        print(
            f"Headless battle simulator audit FAILED: explicit item restore mismatch: {item_events}",
            file=sys.stderr,
        )
        return 1
    full_restore_payload = scenario_template()
    full_restore_payload["state"]["player"]["hp"] = 10
    full_restore_payload["state"]["player"]["max_hp"] = 30
    full_restore_payload["state"]["player"]["status"] = "toxic"
    full_restore_payload["state"]["player"]["toxic_count"] = 3
    full_restore_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    full_restore_payload["actions"]["player"] = {"type": "item", "item": "FULL_RESTORE"}
    full_restore_outcome = simulate_payload(full_restore_payload)["outcomes"][0]
    if (
        full_restore_outcome["events"][0].get("type") != "item_restore"
        or full_restore_outcome["events"][0].get("status_after") != "none"
        or full_restore_outcome["state"]["player"].get("status") != "none"
        or full_restore_outcome["state"]["player"].get("toxic_count") != 0
    ):
        print(
            f"Headless battle simulator audit FAILED: full restore mismatch: {full_restore_outcome}",
            file=sys.stderr,
        )
        return 1
    print("explicit_active_hp_restore_items: PASS potion_then_residual full_restore_cures")
    weather_payload = scenario_template()
    weather_payload["state"]["player"]["moves"] = [{"name": "RAIN_DANCE"}]
    weather_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    weather_outcome = simulate_payload(weather_payload)["outcomes"][0]
    weather_events = weather_outcome["events"]
    weather_start = [event for event in weather_events if event.get("type") == "weather_start"]
    weather_tick = [event for event in weather_events if event.get("type") == "weather_continue"]
    if (
        len(weather_start) != 1
        or weather_start[0].get("weather") != "rain"
        or weather_start[0].get("weather_count_after") != 5
        or len(weather_tick) != 1
        or weather_tick[0].get("weather_count_after") != 4
        or weather_outcome["state"].get("weather_count") != 4
    ):
        print(
            f"Headless battle simulator audit FAILED: weather setup mismatch: {weather_outcome}",
            file=sys.stderr,
        )
        return 1
    print("selected_weather_setup_moves: PASS rain_dance_countdown")
    stage_payload = scenario_template()
    stage_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    stage_baseline_damage = simulate_payload(stage_payload)["outcomes"][0]["events"][0]["pre_variation_damage"]
    stage_payload["state"]["player"]["stat_stages"] = {"attack": 2}
    stage_report = simulate_payload(stage_payload)
    stage_damage = stage_report["outcomes"][0]["events"][0]["pre_variation_damage"]
    if stage_damage <= stage_baseline_damage:
        print(
            f"Headless battle simulator audit FAILED: attack stage did not raise damage: {stage_report}",
            file=sys.stderr,
        )
        return 1
    speed_stage_payload = scenario_template()
    speed_stage_payload["state"]["player"]["stats"]["speed"] = 10
    speed_stage_payload["state"]["enemy"]["stats"]["speed"] = 12
    speed_stage_payload["state"]["player"]["stat_stages"] = {"speed": 1}
    speed_stage_payload["state"]["player"]["moves"][0]["bp"] = 0
    speed_stage_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    speed_stage_report = simulate_payload(speed_stage_payload)
    speed_stage_outcome = speed_stage_report["outcomes"][0]
    speed_stage_check = speed_stage_outcome["turn_orders"][0].get("turn_order_check", {})
    if (
        speed_stage_outcome.get("turn_order") != ["player", "enemy"]
        or speed_stage_check.get("effective_speeds") != {"player": 15, "enemy": 12}
    ):
        print(
            f"Headless battle simulator audit FAILED: speed stage mismatch: {speed_stage_report}",
            file=sys.stderr,
        )
        return 1
    print("explicit_stat_stage_state: PASS attack_stage_damage speed_stage_order")
    stat_move_payload = scenario_template()
    stat_move_payload["state"]["player"]["moves"] = [{"name": "GROWL"}]
    stat_move_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    stat_move_report = simulate_payload(stat_move_payload)
    stat_move_event = stat_move_report["outcomes"][0]["events"][0]
    if (
        stat_move_event.get("type") != "stat_stage_change"
        or stat_move_event.get("move") != "GROWL"
        or stat_move_report["outcomes"][0]["state"]["enemy"]["stat_stages"].get("attack") != -1
    ):
        print(
            f"Headless battle simulator audit FAILED: stat stage move mismatch: {stat_move_report}",
            file=sys.stderr,
        )
        return 1
    screech_payload = scenario_template()
    screech_payload["state"]["player"]["moves"] = [{"name": "SCREECH"}]
    screech_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    screech_payload["rng"] = {"mode": "fixed", "values": [255]}
    screech_event = simulate_payload(screech_payload)["outcomes"][0]["events"][0]
    if screech_event.get("type") != "miss" or screech_event.get("accuracy_check", {}).get("threshold") != 216:
        print(
            f"Headless battle simulator audit FAILED: stat stage move miss mismatch: {screech_event}",
            file=sys.stderr,
        )
        return 1
    print("selected_stat_stage_only_moves: PASS growl_attack_down screech_miss")
    calm_payload = scenario_template()
    calm_payload["state"]["player"]["moves"] = [{"name": "CALM_MIND"}]
    calm_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    calm_report = simulate_payload(calm_payload)
    calm_event = calm_report["outcomes"][0]["events"][0]
    if (
        calm_event.get("type") != "stat_stage_change"
        or [(row.get("stat"), row.get("stage_after")) for row in calm_event.get("changes", [])]
        != [("sp_attack", 1), ("sp_defense", 1)]
    ):
        print(
            f"Headless battle simulator audit FAILED: Calm Mind mismatch: {calm_report}",
            file=sys.stderr,
        )
        return 1
    dance_payload = scenario_template()
    dance_payload["state"]["player"]["stats"]["attack"] = 10
    dance_payload["state"]["player"]["stats"]["sp_attack"] = 20
    dance_payload["state"]["player"]["moves"] = [{"name": "DRAGON_DANCE"}]
    dance_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    dance_event = simulate_payload(dance_payload)["outcomes"][0]["events"][0]
    if (
        dance_event.get("type") != "stat_stage_change"
        or [(row.get("stat"), row.get("stage_after")) for row in dance_event.get("changes", [])]
        != [("sp_attack", 1), ("speed", 1)]
    ):
        print(
            f"Headless battle simulator audit FAILED: Dragon Dance bestattack mismatch: {dance_event}",
            file=sys.stderr,
        )
        return 1
    print("selected_multi_stat_setup_moves: PASS calm_mind dragon_dance_bestattack")
    burn_hit_payload = scenario_template()
    burn_hit_payload["state"]["player"]["moves"] = [{"name": "EMBER"}]
    burn_hit_payload["state"]["enemy"]["types"] = ["NORMAL", "NORMAL"]
    burn_hit_payload["state"]["enemy"]["hp"] = 40
    burn_hit_payload["state"]["enemy"]["max_hp"] = 40
    burn_hit_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    burn_hit_payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}
    burn_hit_events = simulate_payload(burn_hit_payload)["outcomes"][0]["events"]
    burn_hit_event = burn_hit_events[1]
    if (
        burn_hit_event.get("type") != "status_apply"
        or burn_hit_event.get("status") != "burn"
        or burn_hit_event.get("effect_chance_check", {}).get("threshold") != 25
    ):
        print(
            f"Headless battle simulator audit FAILED: damaging burn secondary mismatch: {burn_hit_events}",
            file=sys.stderr,
        )
        return 1
    poison_hit_payload = scenario_template()
    poison_hit_payload["state"]["player"]["moves"] = [{"name": "SLUDGE"}]
    poison_hit_payload["state"]["enemy"]["hp"] = 48
    poison_hit_payload["state"]["enemy"]["max_hp"] = 48
    poison_hit_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    poison_hit_payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}
    poison_hit_events = simulate_payload(poison_hit_payload)["outcomes"][0]["events"]
    poison_hit_event = poison_hit_events[1]
    if (
        poison_hit_event.get("type") != "status_apply"
        or poison_hit_event.get("status") != "poison"
        or poison_hit_event.get("effect_chance_check", {}).get("threshold") != 76
        or poison_hit_events[-1].get("type") != "residual_damage"
    ):
        print(
            f"Headless battle simulator audit FAILED: damaging poison secondary mismatch: {poison_hit_events}",
            file=sys.stderr,
        )
        return 1
    paralysis_hit_payload = scenario_template()
    paralysis_hit_payload["state"]["player"]["moves"] = [{"name": "BODY_SLAM"}]
    paralysis_hit_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    paralysis_hit_payload["rng"] = {"mode": "fixed", "values": [255, 255, 0, 255]}
    paralysis_hit_event = simulate_payload(paralysis_hit_payload)["outcomes"][0]["events"][1]
    if (
        paralysis_hit_event.get("type") != "status_apply"
        or paralysis_hit_event.get("status") != "paralyze"
        or paralysis_hit_event.get("effect_chance_check", {}).get("threshold") != 76
    ):
        print(
            f"Headless battle simulator audit FAILED: damaging paralysis secondary mismatch: {paralysis_hit_event}",
            file=sys.stderr,
        )
        return 1
    print("selected_damaging_status_secondaries: PASS ember_burn sludge_poison body_slam_paralyze")
    drain_payload = scenario_template()
    drain_payload["state"]["player"]["hp"] = 5
    drain_payload["state"]["player"]["max_hp"] = 40
    drain_payload["state"]["player"]["moves"] = [{"name": "GIGA_DRAIN"}]
    drain_payload["state"]["enemy"]["hp"] = 40
    drain_payload["state"]["enemy"]["max_hp"] = 40
    drain_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    drain_payload["rng"] = {"mode": "fixed", "values": [255, 255]}
    drain_events = simulate_payload(drain_payload)["outcomes"][0]["events"]
    drain_damage = drain_events[0]
    drain_event = drain_events[1]
    if (
        drain_event.get("type") != "drain_heal"
        or drain_event.get("damage_drained") != drain_damage.get("actual_damage")
        or drain_event.get("raw_heal") != max(1, drain_damage.get("actual_damage") // 2)
        or drain_event.get("heal") != drain_event.get("raw_heal")
    ):
        print(
            f"Headless battle simulator audit FAILED: drain move mismatch: {drain_events}",
            file=sys.stderr,
        )
        return 1
    min_drain_payload = scenario_template()
    min_drain_payload["state"]["player"]["hp"] = 5
    min_drain_payload["state"]["player"]["max_hp"] = 40
    min_drain_payload["state"]["player"]["moves"] = [{"name": "ABSORB"}]
    min_drain_payload["state"]["enemy"]["hp"] = 1
    min_drain_payload["state"]["enemy"]["max_hp"] = 40
    min_drain_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    min_drain_payload["rng"] = {"mode": "fixed", "values": [255, 255]}
    min_drain_event = simulate_payload(min_drain_payload)["outcomes"][0]["events"][1]
    if (
        min_drain_event.get("type") != "drain_heal"
        or min_drain_event.get("damage_drained") != 1
        or min_drain_event.get("heal") != 1
    ):
        print(
            f"Headless battle simulator audit FAILED: minimum drain mismatch: {min_drain_event}",
            file=sys.stderr,
        )
        return 1
    miss_drain_payload = scenario_template()
    miss_drain_payload["state"]["player"]["hp"] = 5
    miss_drain_payload["state"]["player"]["max_hp"] = 40
    miss_drain_payload["state"]["player"]["moves"] = [{"name": "GIGA_DRAIN", "accuracy": 1}]
    miss_drain_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    miss_drain_payload["rng"] = {"mode": "fixed", "values": [255, 255, 255]}
    miss_drain_events = simulate_payload(miss_drain_payload)["outcomes"][0]["events"]
    if miss_drain_events[0].get("type") != "miss" or any(
        event.get("type", "").startswith("drain") for event in miss_drain_events
    ):
        print(
            f"Headless battle simulator audit FAILED: drain miss mismatch: {miss_drain_events}",
            file=sys.stderr,
        )
        return 1
    print("selected_drain_moves: PASS giga_drain_half_damage absorb_min_one miss_no_heal")
    sleep_payload = scenario_template()
    sleep_payload["state"]["player"]["moves"] = [{"name": "SLEEP_POWDER"}]
    sleep_payload["state"]["enemy"]["moves"] = [{"name": "TACKLE"}]
    sleep_payload["rng"] = {"mode": "fixed", "values": [0, 0]}
    sleep_outcome = simulate_payload(sleep_payload)["outcomes"][0]
    sleep_event = sleep_outcome["events"][0]
    sleep_denied = sleep_outcome["events"][1]
    if (
        sleep_event.get("type") != "status_apply"
        or sleep_event.get("status") != "sleep"
        or sleep_event.get("sleep_turns_after") != 3
        or sleep_denied.get("type") != "fast_asleep"
        or sleep_denied.get("sleep_turns_after") != 2
    ):
        print(
            f"Headless battle simulator audit FAILED: sleep status mismatch: {sleep_outcome}",
            file=sys.stderr,
        )
        return 1
    wake_payload = scenario_template()
    wake_payload["state"]["player"]["status"] = "sleep"
    wake_payload["state"]["player"]["sleep_turns"] = 1
    wake_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    wake_payload["rng"] = {"mode": "fixed", "values": [255, 255]}
    wake_events = simulate_payload(wake_payload)["outcomes"][0]["events"]
    if wake_events[0].get("type") != "woke_up" or wake_events[1].get("type") != "damage":
        print(
            f"Headless battle simulator audit FAILED: sleep wake/action mismatch: {wake_events}",
            file=sys.stderr,
        )
        return 1
    print("selected_sleep_status_moves: PASS sleep_powder_duration fast_asleep wake_action")
    poison_cure_payload = scenario_template()
    poison_cure_payload["state"]["player"]["moves"] = [{"name": "POISONPOWDER"}]
    poison_cure_payload["state"]["enemy"]["item"] = "PSNCUREBERRY"
    poison_cure_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    poison_cure_outcome = simulate_payload(poison_cure_payload)["outcomes"][0]
    poison_cure_events = poison_cure_outcome["events"]
    if (
        [event.get("type") for event in poison_cure_events[:2]] != ["status_apply", "held_status_cure"]
        or poison_cure_events[1].get("source_item") != "PSNCUREBERRY"
        or poison_cure_outcome["state"]["enemy"].get("status") != "none"
        or poison_cure_outcome["state"]["enemy"].get("item") != 0
        or any(event.get("type") == "residual_damage" for event in poison_cure_events)
    ):
        print(
            f"Headless battle simulator audit FAILED: held poison cure mismatch: {poison_cure_outcome}",
            file=sys.stderr,
        )
        return 1
    paralysis_cure_payload = scenario_template()
    paralysis_cure_payload["state"]["player"]["moves"] = [{"name": "THUNDER_WAVE"}]
    paralysis_cure_payload["state"]["enemy"]["item"] = "PRZCUREBERRY"
    paralysis_cure_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    paralysis_cure_outcome = simulate_payload(paralysis_cure_payload)["outcomes"][0]
    paralysis_cure_events = paralysis_cure_outcome["events"]
    if (
        [event.get("type") for event in paralysis_cure_events[:2]] != ["status_apply", "held_status_cure"]
        or paralysis_cure_events[1].get("source_item") != "PRZCUREBERRY"
        or paralysis_cure_outcome["state"]["enemy"].get("status") != "none"
        or paralysis_cure_outcome["state"]["enemy"].get("item") != 0
    ):
        print(
            f"Headless battle simulator audit FAILED: held paralysis cure mismatch: {paralysis_cure_outcome}",
            file=sys.stderr,
        )
        return 1
    burn_cure_payload = scenario_template()
    burn_cure_payload["state"]["player"]["moves"] = [{"name": "EMBER"}]
    burn_cure_payload["state"]["enemy"]["types"] = ["NORMAL", "NORMAL"]
    burn_cure_payload["state"]["enemy"]["item"] = "ICE_BERRY"
    burn_cure_payload["state"]["enemy"]["hp"] = 40
    burn_cure_payload["state"]["enemy"]["max_hp"] = 40
    burn_cure_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    burn_cure_payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}
    burn_cure_outcome = simulate_payload(burn_cure_payload)["outcomes"][0]
    burn_cure_events = burn_cure_outcome["events"]
    if (
        [event.get("type") for event in burn_cure_events[1:3]] != ["status_apply", "held_status_cure"]
        or burn_cure_events[2].get("source_item") != "ICE_BERRY"
        or burn_cure_outcome["state"]["enemy"].get("status") != "none"
        or burn_cure_outcome["state"]["enemy"].get("item") != 0
    ):
        print(
            f"Headless battle simulator audit FAILED: held burn cure mismatch: {burn_cure_outcome}",
            file=sys.stderr,
        )
        return 1
    sleep_cure_payload = scenario_template()
    sleep_cure_payload["state"]["player"]["moves"] = [{"name": "SLEEP_POWDER"}]
    sleep_cure_payload["state"]["enemy"]["item"] = "MINT_BERRY"
    sleep_cure_payload["rng"] = {"mode": "fixed", "values": [0, 0, 255, 255, 0]}
    sleep_cure_outcome = simulate_payload(sleep_cure_payload)["outcomes"][0]
    sleep_cure_events = sleep_cure_outcome["events"]
    if (
        [event.get("type") for event in sleep_cure_events[:3]] != ["status_apply", "held_status_cure", "damage"]
        or sleep_cure_events[1].get("source_item") != "MINT_BERRY"
        or sleep_cure_outcome["state"]["enemy"].get("status") != "none"
        or sleep_cure_outcome["state"]["enemy"].get("sleep_turns") != 0
        or sleep_cure_outcome["state"]["enemy"].get("item") != 0
    ):
        print(
            f"Headless battle simulator audit FAILED: held sleep cure mismatch: {sleep_cure_outcome}",
            file=sys.stderr,
        )
        return 1
    miracle_payload = scenario_template()
    miracle_payload["state"]["player"]["moves"] = [{"name": "TOXIC"}]
    miracle_payload["state"]["enemy"]["item"] = "MIRACLEBERRY"
    miracle_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    miracle_outcome = simulate_payload(miracle_payload)["outcomes"][0]
    miracle_events = miracle_outcome["events"]
    if (
        [event.get("type") for event in miracle_events[:2]] != ["status_apply", "held_status_cure"]
        or miracle_events[1].get("source_item") != "MIRACLEBERRY"
        or miracle_events[1].get("cured_status") != "toxic"
        or miracle_outcome["state"]["enemy"].get("status") != "none"
        or miracle_outcome["state"]["enemy"].get("toxic_count") != 0
    ):
        print(
            f"Headless battle simulator audit FAILED: MiracleBerry toxic cure mismatch: {miracle_outcome}",
            file=sys.stderr,
        )
        return 1
    print("selected_held_status_cures: PASS psn_cure prz_cure burn_cure sleep_cure miracle_toxic")
    sleep_safeguard_payload = scenario_template()
    sleep_safeguard_payload["state"]["player"]["moves"] = [{"name": "SLEEP_POWDER"}]
    sleep_safeguard_payload["state"]["enemy"]["safeguard"] = True
    sleep_safeguard_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    sleep_safeguard_payload["rng"] = {"mode": "fixed", "values": [0]}
    sleep_safeguard_outcome = simulate_payload(sleep_safeguard_payload)["outcomes"][0]
    sleep_safeguard_event = sleep_safeguard_outcome["events"][0]
    if (
        sleep_safeguard_event.get("type") != "status_no_effect"
        or sleep_safeguard_event.get("blocked_reason") != "safeguard"
        or sleep_safeguard_event.get("sleep_duration") is not None
        or sleep_safeguard_outcome.get("rng_consumed") != [0]
    ):
        print(
            f"Headless battle simulator audit FAILED: sleep safeguard mismatch: {sleep_safeguard_outcome}",
            file=sys.stderr,
        )
        return 1
    poison_substitute_payload = scenario_template()
    poison_substitute_payload["state"]["player"]["moves"] = [{"name": "POISONPOWDER"}]
    poison_substitute_payload["state"]["enemy"]["substitute"] = True
    poison_substitute_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    poison_substitute_event = simulate_payload(poison_substitute_payload)["outcomes"][0]["events"][0]
    if poison_substitute_event.get("type") != "status_no_effect" or poison_substitute_event.get("blocked_reason") != "substitute":
        print(
            f"Headless battle simulator audit FAILED: poison substitute mismatch: {poison_substitute_event}",
            file=sys.stderr,
        )
        return 1
    burn_safeguard_payload = scenario_template()
    burn_safeguard_payload["state"]["player"]["moves"] = [{"name": "EMBER"}]
    burn_safeguard_payload["state"]["enemy"]["safeguard"] = True
    burn_safeguard_payload["state"]["enemy"]["types"] = ["NORMAL", "NORMAL"]
    burn_safeguard_payload["state"]["enemy"]["hp"] = 40
    burn_safeguard_payload["state"]["enemy"]["max_hp"] = 40
    burn_safeguard_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    burn_safeguard_payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}
    burn_safeguard_events = simulate_payload(burn_safeguard_payload)["outcomes"][0]["events"]
    if (
        burn_safeguard_events[0].get("type") != "damage"
        or burn_safeguard_events[1].get("type") != "status_no_effect"
        or burn_safeguard_events[1].get("blocked_reason") != "safeguard"
        or burn_safeguard_events[1].get("effect_chance_check", {}).get("success") is not True
    ):
        print(
            f"Headless battle simulator audit FAILED: damaging safeguard mismatch: {burn_safeguard_events}",
            file=sys.stderr,
        )
        return 1
    print("selected_safeguard_substitute_blockers: PASS sleep_safeguard poison_substitute burn_safeguard")
    create_substitute_payload = scenario_template()
    create_substitute_payload["state"]["player"]["moves"] = [{"name": "SUBSTITUTE"}]
    create_substitute_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    create_substitute_outcome = simulate_payload(create_substitute_payload)["outcomes"][0]
    create_substitute_event = create_substitute_outcome["events"][0]
    if (
        create_substitute_event.get("type") != "substitute_create"
        or create_substitute_event.get("hp_before") != 16
        or create_substitute_event.get("hp_after") != 12
        or create_substitute_event.get("substitute_hp") != 4
        or create_substitute_outcome["state"]["player"].get("substitute_hp") != 4
    ):
        print(
            f"Headless battle simulator audit FAILED: Substitute create mismatch: {create_substitute_outcome}",
            file=sys.stderr,
        )
        return 1
    weak_substitute_payload = scenario_template()
    weak_substitute_payload["state"]["player"]["moves"] = [{"name": "SUBSTITUTE"}]
    weak_substitute_payload["state"]["player"]["hp"] = 4
    weak_substitute_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    weak_substitute_event = simulate_payload(weak_substitute_payload)["outcomes"][0]["events"][0]
    if (
        weak_substitute_event.get("type") != "substitute_no_effect"
        or weak_substitute_event.get("blocked_reason") != "too_weak"
    ):
        print(
            f"Headless battle simulator audit FAILED: Substitute weak failure mismatch: {weak_substitute_event}",
            file=sys.stderr,
        )
        return 1
    print("selected_substitute_move: PASS create_hp_cost too_weak_no_effect")
    damaging_substitute_payload = scenario_template()
    damaging_substitute_payload["state"]["enemy"]["substitute"] = True
    damaging_substitute_payload["state"]["enemy"]["substitute_hp"] = 40
    damaging_substitute_outcome = simulate_payload(damaging_substitute_payload)["outcomes"][0]
    damaging_substitute_event = damaging_substitute_outcome["events"][0]
    if (
        damaging_substitute_event.get("type") != "damage"
        or damaging_substitute_event.get("damage_target") != "substitute"
        or damaging_substitute_event.get("actual_damage") != 0
        or damaging_substitute_event.get("target_hp_before") != damaging_substitute_event.get("target_hp_after")
        or damaging_substitute_outcome["state"]["enemy"].get("substitute_hp") >= 40
    ):
        print(
            f"Headless battle simulator audit FAILED: damaging substitute routing mismatch: {damaging_substitute_outcome}",
            file=sys.stderr,
        )
        return 1
    secondary_substitute_payload = scenario_template()
    secondary_substitute_payload["state"]["player"]["moves"] = [{"name": "EMBER"}]
    secondary_substitute_payload["state"]["enemy"]["substitute"] = True
    secondary_substitute_payload["state"]["enemy"]["substitute_hp"] = 1
    secondary_substitute_payload["state"]["enemy"]["types"] = ["NORMAL", "NORMAL"]
    secondary_substitute_payload["state"]["enemy"]["hp"] = 40
    secondary_substitute_payload["state"]["enemy"]["max_hp"] = 40
    secondary_substitute_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    secondary_substitute_payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}
    secondary_substitute_outcome = simulate_payload(secondary_substitute_payload)["outcomes"][0]
    secondary_substitute_events = secondary_substitute_outcome["events"]
    if (
        secondary_substitute_events[0].get("damage_target") != "substitute"
        or secondary_substitute_events[0].get("substitute_broke") is not True
        or secondary_substitute_events[1].get("type") != "status_no_effect"
        or secondary_substitute_events[1].get("blocked_reason") != "substitute"
        or secondary_substitute_events[1].get("effect_chance_check", {}).get("raw_values") != []
        or secondary_substitute_outcome.get("rng_consumed") != [255, 255]
    ):
        print(
            f"Headless battle simulator audit FAILED: damaging secondary substitute ordering mismatch: {secondary_substitute_outcome}",
            file=sys.stderr,
        )
        return 1
    drain_substitute_payload = scenario_template()
    drain_substitute_payload["state"]["player"]["moves"] = [{"name": "GIGA_DRAIN"}]
    drain_substitute_payload["state"]["player"]["hp"] = 5
    drain_substitute_payload["state"]["player"]["max_hp"] = 40
    drain_substitute_payload["state"]["enemy"]["substitute"] = True
    drain_substitute_payload["state"]["enemy"]["substitute_hp"] = 10
    drain_substitute_payload["state"]["enemy"]["hp"] = 40
    drain_substitute_payload["state"]["enemy"]["max_hp"] = 40
    drain_substitute_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    drain_substitute_payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}
    drain_substitute_outcome = simulate_payload(drain_substitute_payload)["outcomes"][0]
    drain_substitute_event = drain_substitute_outcome["events"][0]
    if (
        drain_substitute_event.get("type") != "miss"
        or drain_substitute_event.get("accuracy_check", {}).get("reason") != "drain_blocked_by_substitute"
        or drain_substitute_event.get("accuracy_check", {}).get("raw_values") != []
        or drain_substitute_outcome.get("rng_consumed") != [255]
        or drain_substitute_outcome["state"]["enemy"].get("substitute_hp") != 10
    ):
        print(
            f"Headless battle simulator audit FAILED: drain substitute miss mismatch: {drain_substitute_outcome}",
            file=sys.stderr,
        )
        return 1
    print("selected_substitute_hp_routing: PASS hp_buffer break secondary_no_effectchance_rng drain_checkhit_miss")
    rest_payload = scenario_template()
    rest_payload["state"]["player"]["hp"] = 10
    rest_payload["state"]["player"]["max_hp"] = 40
    rest_payload["state"]["player"]["status"] = "toxic"
    rest_payload["state"]["player"]["toxic_count"] = 2
    rest_payload["state"]["player"]["moves"] = [{"name": "REST"}]
    rest_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    rest_event = simulate_payload(rest_payload)["outcomes"][0]["events"][0]
    if (
        rest_event.get("type") != "rest"
        or rest_event.get("hp_after") != 40
        or rest_event.get("status_after") != "sleep"
        or rest_event.get("sleep_turns_after") != 3
        or rest_event.get("toxic_count_after") != 0
    ):
        print(
            f"Headless battle simulator audit FAILED: Rest mismatch: {rest_event}",
            file=sys.stderr,
        )
        return 1
    print("selected_rest_move: PASS rest_full_hp_sleep_counter")
    heal_payload = scenario_template()
    heal_payload["state"]["player"]["hp"] = 10
    heal_payload["state"]["player"]["max_hp"] = 40
    heal_payload["state"]["player"]["moves"] = [{"name": "RECOVER"}]
    heal_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    heal_event = simulate_payload(heal_payload)["outcomes"][0]["events"][0]
    if (
        heal_event.get("type") != "self_heal"
        or heal_event.get("move") != "RECOVER"
        or heal_event.get("heal") != 20
        or heal_event.get("hp_after") != 30
    ):
        print(
            f"Headless battle simulator audit FAILED: self-heal move mismatch: {heal_event}",
            file=sys.stderr,
        )
        return 1
    print("selected_self_heal_moves: PASS recover_half_hp")
    poison_payload = scenario_template()
    poison_payload["state"]["player"]["moves"] = [{"name": "POISONPOWDER"}]
    poison_payload["state"]["enemy"]["hp"] = 32
    poison_payload["state"]["enemy"]["max_hp"] = 32
    poison_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    poison_outcome = simulate_payload(poison_payload)["outcomes"][0]
    poison_event = poison_outcome["events"][0]
    poison_residual = poison_outcome["events"][-1]
    if (
        poison_event.get("type") != "status_apply"
        or poison_event.get("status") != "poison"
        or poison_outcome["state"]["enemy"].get("status") != "poison"
        or poison_residual.get("type") != "residual_damage"
        or poison_residual.get("damage") != 4
    ):
        print(
            f"Headless battle simulator audit FAILED: poison status move mismatch: {poison_outcome}",
            file=sys.stderr,
        )
        return 1
    toxic_payload = scenario_template()
    toxic_payload["state"]["player"]["moves"] = [{"name": "TOXIC"}]
    toxic_payload["state"]["enemy"]["hp"] = 48
    toxic_payload["state"]["enemy"]["max_hp"] = 48
    toxic_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    toxic_outcome = simulate_payload(toxic_payload)["outcomes"][0]
    toxic_event = toxic_outcome["events"][0]
    toxic_residual = toxic_outcome["events"][-1]
    if (
        toxic_event.get("type") != "status_apply"
        or toxic_event.get("status") != "toxic"
        or toxic_event.get("toxic_count_after") != 0
        or toxic_residual.get("toxic_count_after") != 1
        or toxic_residual.get("damage") != 3
    ):
        print(
            f"Headless battle simulator audit FAILED: toxic status move mismatch: {toxic_outcome}",
            file=sys.stderr,
        )
        return 1
    print("selected_poison_status_moves: PASS poisonpowder_residual toxic_count")
    paralysis_payload = scenario_template()
    paralysis_payload["state"]["player"]["moves"] = [{"name": "THUNDER_WAVE"}]
    paralysis_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    paralysis_outcome = simulate_payload(paralysis_payload)["outcomes"][0]
    paralysis_event = paralysis_outcome["events"][0]
    if (
        paralysis_event.get("type") != "status_apply"
        or paralysis_event.get("status") != "paralyze"
        or paralysis_outcome["state"]["enemy"].get("status") != "paralyze"
    ):
        print(
            f"Headless battle simulator audit FAILED: paralysis status move mismatch: {paralysis_outcome}",
            file=sys.stderr,
        )
        return 1
    full_para_payload = scenario_template()
    full_para_payload["state"]["player"]["stats"]["speed"] = 80
    full_para_payload["state"]["player"]["status"] = "paralyze"
    full_para_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    full_para_payload["rng"] = {"mode": "fixed", "values": [0]}
    full_para_outcome = simulate_payload(full_para_payload)["outcomes"][0]
    full_para_event = full_para_outcome["events"][0]
    if (
        full_para_event.get("type") != "fully_paralyzed"
        or full_para_event.get("pp_after") != full_para_event.get("pp_before")
        or full_para_outcome["state"]["player"]["moves"][0].get("pp") != 35
    ):
        print(
            f"Headless battle simulator audit FAILED: full paralysis mismatch: {full_para_outcome}",
            file=sys.stderr,
        )
        return 1
    print("selected_paralysis_status_moves: PASS thunder_wave full_paralysis_no_pp")
    fighting_para_payload = scenario_template()
    fighting_para_payload["state"]["player"]["stats"]["speed"] = 80
    fighting_para_payload["state"]["player"]["types"] = ["FIGHTING", "FIGHTING"]
    fighting_para_payload["state"]["player"]["status"] = "paralyze"
    fighting_para_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    fighting_para_payload["rng"] = {"mode": "fixed", "values": [40, 255, 255, 0]}
    fighting_para_outcome = simulate_payload(fighting_para_payload)["outcomes"][0]
    fighting_para_check = fighting_para_outcome["turn_orders"][0].get("turn_order_check", {})
    if (
        fighting_para_outcome["events"][0].get("type") != "damage"
        or fighting_para_check.get("effective_speeds", {}).get("player") != 40
    ):
        print(
            "Headless battle simulator audit FAILED: type-passive paralysis modifier mismatch: "
            f"{fighting_para_outcome}",
            file=sys.stderr,
        )
        return 1
    print("type_passive_paralysis_modifiers: PASS mono_fighting_threshold_and_speed")
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
    selector_move_payload["rng"] = {"mode": "fixed", "values": [200, 255, 255, 255]}
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
    switch_roll_payload = scenario_template()
    switch_roll_payload["state"]["player"]["moves"][0]["bp"] = 0
    switch_roll_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    switch_roll_payload["state"]["enemy"]["bench"] = [
        {
            "name": "GENGAR",
            "hp": 30,
            "max_hp": 30,
            "types": ["GHOST", "POISON"],
            "moves": [{"name": "LICK", "type": "GHOST", "bp": 20}],
        }
    ]
    switch_roll_payload["actions"]["enemy"] = {
        "type": "boss_ai_switch_roll",
        "candidate_bench_index": 0,
        "confidence": 90,
        "threshold": 70,
        "fallback": {"type": "move", "move": 0},
    }
    switch_roll_payload["rng"] = {"mode": "fixed", "values": [0]}
    switch_roll_outcome = simulate_payload(switch_roll_payload)["outcomes"][0]
    switch_roll_event = switch_roll_outcome["events"][0]
    if (
        switch_roll_event.get("type") != "boss_ai_switch_roll"
        or switch_roll_event.get("selected_action") != "switch"
        or switch_roll_event.get("switch_chance_threshold") != 230
        or switch_roll_event.get("raw_values") != [0]
        or switch_roll_outcome["events"][1].get("type") != "switch"
        or switch_roll_outcome["state"]["enemy"].get("name") != "GENGAR"
    ):
        print(
            f"Headless battle simulator audit FAILED: Boss AI switch roll mismatch: {switch_roll_outcome}",
            file=sys.stderr,
        )
        return 1
    switch_roll_no_roll = scenario_template()
    switch_roll_no_roll["state"]["player"]["moves"][0]["bp"] = 0
    switch_roll_no_roll["state"]["enemy"]["moves"][0]["bp"] = 0
    switch_roll_no_roll["state"]["enemy"]["bench"] = switch_roll_payload["state"]["enemy"]["bench"]
    switch_roll_no_roll["actions"]["enemy"] = {
        "type": "boss_ai_switch_roll",
        "candidate_bench_index": 0,
        "confidence": 69,
        "threshold": 70,
        "fallback": {"type": "move", "move": 0},
    }
    switch_roll_no_roll["rng"] = {"mode": "fixed", "values": [0]}
    no_roll_outcome = simulate_payload(switch_roll_no_roll)["outcomes"][0]
    no_roll_event = no_roll_outcome["events"][0]
    if (
        no_roll_event.get("selected_action") != "stay"
        or no_roll_event.get("switch_chance_threshold") != 0
        or no_roll_event.get("raw_values") != []
        or no_roll_outcome.get("rng_consumed") != []
    ):
        print(
            f"Headless battle simulator audit FAILED: Boss AI no-roll stay mismatch: {no_roll_outcome}",
            file=sys.stderr,
        )
        return 1
    switch_roll_exhaustive = scenario_template()
    switch_roll_exhaustive["state"]["player"]["moves"][0]["bp"] = 0
    switch_roll_exhaustive["state"]["enemy"]["moves"][0]["bp"] = 0
    switch_roll_exhaustive["state"]["enemy"]["bench"] = switch_roll_payload["state"]["enemy"]["bench"]
    switch_roll_exhaustive["actions"]["enemy"] = {
        "type": "boss_ai_switch_roll",
        "candidate_bench_index": 0,
        "confidence": 80,
        "threshold": 70,
        "fallback": {"type": "move", "move": 0},
    }
    switch_roll_exhaustive["rng"] = {"mode": "exhaustive"}
    switch_roll_report = simulate_payload(switch_roll_exhaustive)
    if (
        switch_roll_report.get("outcome_count") != 2
        or {outcome["events"][0].get("selected_action") for outcome in switch_roll_report["outcomes"]}
        != {"switch", "stay"}
    ):
        print(
            f"Headless battle simulator audit FAILED: exhaustive Boss AI switch roll mismatch: {switch_roll_report}",
            file=sys.stderr,
        )
        return 1
    print("boss_ai_switch_roll: PASS fixed_switch no_roll_stay exhaustive_switch_or_stay")
    wild_payload = scenario_template()
    wild_payload["state"]["player"]["moves"][0]["bp"] = 0
    wild_payload["state"]["enemy"]["moves"] = [
        {"name": "TACKLE", "type": "NORMAL", "bp": 0, "pp": 0},
        {"name": "EMBER", "type": "FIRE", "bp": 40, "pp": 1},
    ]
    wild_payload["actions"]["enemy"] = {"type": "wild_random_move"}
    wild_payload["rng"] = {"mode": "fixed", "values": [0, 1, 255, 255, 255]}
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
    spikes_payload = scenario_template()
    spikes_payload["state"]["player"]["moves"] = [
        {"name": "SPIKES"},
        {"name": "TACKLE", "type": "NORMAL", "bp": 0},
    ]
    spikes_payload["state"]["enemy"]["hp"] = 40
    spikes_payload["state"]["enemy"]["max_hp"] = 40
    spikes_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    spikes_payload["state"]["enemy"]["bench"] = [
        {
            "name": "ENEMY_RESERVE",
            "hp": 40,
            "max_hp": 40,
            "types": ["NORMAL", "NORMAL"],
            "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0}],
        }
    ]
    spikes_payload.pop("actions")
    spikes_payload["turns"] = [
        {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
        {"player": {"type": "move", "move": 1}, "enemy": {"type": "switch", "bench_index": 0}},
    ]
    spikes_outcome = simulate_payload(spikes_payload)["outcomes"][0]
    spikes_events = spikes_outcome["events"]
    spikes_set = [event for event in spikes_events if event.get("type") == "spikes_set"]
    entry_damage = [event for event in spikes_events if event.get("type") == "entry_hazard_damage"]
    if (
        len(spikes_set) != 1
        or spikes_set[0].get("layers_after") != 1
        or len(entry_damage) != 1
        or entry_damage[0].get("damage") != 5
        or spikes_outcome["state"]["enemy"].get("hp") != 35
    ):
        print(
            f"Headless battle simulator audit FAILED: Spikes entry mismatch: {spikes_outcome}",
            file=sys.stderr,
        )
        return 1
    print("selected_spikes_entry_damage: PASS layer_then_switch_chip")
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
    repeat_payload = scenario_template()
    repeat_payload["state"]["enemy"]["hp"] = 1
    repeat_payload["state"]["enemy"]["max_hp"] = 1
    repeat_payload["state"]["enemy"]["moves"][0]["bp"] = 0
    repeat_payload["state"]["enemy"]["bench"] = [
        {
            "name": "ENEMY_RESERVE",
            "hp": 1,
            "max_hp": 1,
            "types": ["NORMAL", "NORMAL"],
            "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0}],
        }
    ]
    repeat_payload.pop("actions")
    repeat_payload["repeat"] = {
        "max_turns": 5,
        "actions": {
            "player": {"type": "move", "move": 0},
            "enemy": {"type": "auto_replace_or", "action": {"type": "move", "move": 0}},
        },
    }
    repeat_report = simulate_payload(repeat_payload)
    repeat_outcome = repeat_report["outcomes"][0]
    if (
        not repeat_outcome.get("battle_over")
        or repeat_outcome.get("turns_simulated") != 2
        or [event.get("type") for event in repeat_outcome["events"]]
        != ["damage", "auto_replacement_choice", "replacement", "damage"]
    ):
        print(
            f"Headless battle simulator audit FAILED: repeat plan mismatch: {repeat_report}",
            file=sys.stderr,
        )
        return 1
    print("repeat_plan_auto_replace_or: PASS turns_simulated=2")
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
