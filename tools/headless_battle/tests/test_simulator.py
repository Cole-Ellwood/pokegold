from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.headless_battle.__main__ import main
from tools.headless_battle.simulator import (
    REPORT_KIND,
    SimulationInputError,
    scenario_template,
    simulate_payload,
)


class HeadlessBattleSimulatorTests(unittest.TestCase):
    def test_template_runs_one_selected_turn(self) -> None:
        report = simulate_payload(scenario_template())

        self.assertEqual(report["kind"], REPORT_KIND)
        self.assertEqual(report["outcome_count"], 1)
        outcome = report["outcomes"][0]
        self.assertEqual(outcome["turn_order"], ["player", "enemy"])
        self.assertEqual(outcome["events"][0]["type"], "damage")
        self.assertEqual(
            outcome["events"][0]["proof_status"],
            "delegated_pre_variation_damage_plus_source_mirrored_critical_variation_accuracy",
        )
        self.assertLess(outcome["state"]["enemy"]["hp"], 18)

    def test_selected_moves_decrement_pp_once(self) -> None:
        report = simulate_payload(scenario_template())

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["pp_before"], 35)
        self.assertEqual(outcome["events"][0]["pp_after"], 34)
        self.assertEqual(outcome["events"][1]["pp_before"], 35)
        self.assertEqual(outcome["events"][1]["pp_after"], 34)
        self.assertEqual(outcome["state"]["player"]["moves"][0]["pp"], 34)
        self.assertEqual(outcome["state"]["enemy"]["moves"][0]["pp"], 34)

    def test_zero_pp_selected_move_is_out_of_scope_until_struggle(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["pp"] = 0

        with self.assertRaisesRegex(SimulationInputError, "has no PP; Struggle is out of scope"):
            simulate_payload(payload)

    def test_rocky_helmet_recoils_contact_attacker(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["max_hp"] = 30
        payload["state"]["player"]["hp"] = 30
        payload["state"]["enemy"]["item"] = "ROCKY_HELMET"
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        recoil = next(event for event in events if event.get("source_item") == "ROCKY_HELMET")
        self.assertEqual(recoil["type"], "after_hit_recoil")
        self.assertEqual(recoil["damage"], 5)
        self.assertEqual(recoil["hp_before"], 30)
        self.assertEqual(recoil["hp_after"], 25)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 25)

    def test_rocky_helmet_ignores_noncontact_move(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0] = {"name": "EMBER", "type": "FIRE", "bp": 40}
        payload["state"]["enemy"]["item"] = "ROCKY_HELMET"
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        self.assertFalse(
            any(event.get("source_item") == "ROCKY_HELMET" for event in report["outcomes"][0]["events"])
        )

    def test_shell_bell_heals_from_damage_done(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["item"] = "SHELL_BELL"
        payload["state"]["player"]["hp"] = 10
        payload["state"]["player"]["max_hp"] = 30
        payload["state"]["enemy"]["hp"] = 30
        payload["state"]["enemy"]["max_hp"] = 30
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}

        report = simulate_payload(payload)

        heal = next(event for event in report["outcomes"][0]["events"] if event.get("source_item") == "SHELL_BELL")
        damage = report["outcomes"][0]["events"][0]["damage"]
        self.assertEqual(heal["type"], "after_hit_heal")
        self.assertEqual(heal["raw_heal"], max(1, damage // 8))
        self.assertEqual(heal["hp_after"], 10 + heal["heal"])

    def test_life_orb_recoils_after_damage(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["item"] = "LIFE_ORB"
        payload["state"]["player"]["hp"] = 30
        payload["state"]["player"]["max_hp"] = 30
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        recoil = next(event for event in report["outcomes"][0]["events"] if event.get("source_item") == "LIFE_ORB")
        self.assertEqual(recoil["type"], "after_hit_recoil")
        self.assertEqual(recoil["damage"], 3)
        self.assertEqual(recoil["hp_before"], 30)
        self.assertEqual(recoil["hp_after"], 27)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 27)

    def test_priority_changes_turn_order(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["moves"][0]["priority"] = 2

        report = simulate_payload(payload)

        self.assertEqual(report["outcomes"][0]["turn_order"], ["enemy", "player"])

    def test_fixed_speed_tie_rng_changes_turn_order(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["stats"]["speed"] = payload["state"]["player"]["stats"]["speed"]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [0, 255, 255, 0]}

        player_first = simulate_payload(payload)
        payload["rng"] = {"mode": "fixed", "values": [128, 255, 255, 0]}
        enemy_first = simulate_payload(payload)

        self.assertEqual(player_first["outcomes"][0]["turn_order"], ["player", "enemy"])
        self.assertEqual(enemy_first["outcomes"][0]["turn_order"], ["enemy", "player"])
        self.assertEqual(player_first["outcomes"][0]["turn_orders"][0]["turn_order_check"]["raw_values"], [0])
        self.assertEqual(enemy_first["outcomes"][0]["turn_orders"][0]["turn_order_check"]["raw_values"], [128])

    def test_fixed_rng_values_drive_damage_variation(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["state"]["player"]["moves"][0]["accuracy"] = 242
        max_roll = simulate_payload(payload)["outcomes"][0]["events"][0]
        payload["rng"] = {"mode": "fixed", "values": [255, 179, 0]}

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["critical_check"]["raw_values"], [255])
        self.assertEqual(event["accuracy_check"]["raw_values"], [0])
        self.assertEqual(event["damage_variation"]["raw_values"], [179])
        self.assertEqual(event["damage_variation"]["multiplier"], 217)
        self.assertLessEqual(event["damage"], max_roll["damage"])

    def test_fixed_rng_reports_exhausted_values(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["state"]["player"]["moves"][0]["accuracy"] = 242
        payload["rng"] = {"mode": "fixed", "values": [255]}

        with self.assertRaisesRegex(SimulationInputError, "rng.values exhausted"):
            simulate_payload(payload)

    def test_fixed_accuracy_miss_skips_damage(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["state"]["player"]["moves"][0]["accuracy"] = 242
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 255]}

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "miss")
        self.assertEqual(event["critical_check"]["raw_values"], [255])
        self.assertEqual(event["damage_variation"]["raw_values"], [255])
        self.assertEqual(event["accuracy_check"]["threshold"], 242)
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["hp"], 18)

    def test_fixed_critical_hit_boosts_pre_variation_damage(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [0, 255, 0]}
        critical = simulate_payload(payload)["outcomes"][0]["events"][0]
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}

        normal = simulate_payload(payload)["outcomes"][0]["events"][0]

        self.assertTrue(critical["critical_check"]["critical"])
        self.assertFalse(normal["critical_check"]["critical"])
        self.assertGreater(critical["pre_variation_damage"], normal["pre_variation_damage"])

    def test_sample_rng_returns_requested_sample_count(self) -> None:
        payload = scenario_template()
        payload["rng"] = {"mode": "sample", "samples": 3, "seed": 7}

        report = simulate_payload(payload)

        self.assertEqual(report["outcome_count"], 3)
        self.assertEqual([outcome["sample_index"] for outcome in report["outcomes"]], [0, 1, 2])
        self.assertTrue(all(outcome["rng_consumed"] for outcome in report["outcomes"]))

    def test_exhaustive_rng_branches_damage_variation(self) -> None:
        payload = scenario_template()
        payload["rng"] = {"mode": "exhaustive"}
        payload["state"]["player"]["moves"][0]["accuracy"] = 255
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        multipliers = {
            outcome["events"][0]["damage_variation"]["multiplier"]
            for outcome in report["outcomes"]
        }
        critical_values = {
            outcome["events"][0]["critical_check"]["critical"]
            for outcome in report["outcomes"]
        }
        self.assertEqual(report["outcome_count"], 78)
        self.assertEqual(critical_values, {False, True})
        self.assertEqual(min(multipliers), 217)
        self.assertEqual(max(multipliers), 255)

    def test_exhaustive_accuracy_adds_miss_branch(self) -> None:
        payload = scenario_template()
        payload["rng"] = {"mode": "exhaustive"}
        payload["state"]["player"]["moves"][0]["accuracy"] = 242
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        self.assertEqual(report["outcome_count"], 156)
        self.assertEqual(sum(1 for outcome in report["outcomes"] if outcome["events"][0]["type"] == "miss"), 78)

    def test_exhaustive_speed_tie_branches_turn_order(self) -> None:
        payload = scenario_template()
        payload["rng"] = {"mode": "exhaustive"}
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["stats"]["speed"] = payload["state"]["player"]["stats"]["speed"]

        report = simulate_payload(payload)

        self.assertEqual(report["outcome_count"], 2)
        self.assertEqual(
            {tuple(outcome["turn_order"]) for outcome in report["outcomes"]},
            {("player", "enemy"), ("enemy", "player")},
        )

    def test_poison_residual_applies_after_actor_move(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "poison"
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        residual = next(event for event in events if event["type"] == "residual_damage")
        self.assertEqual(residual["actor"], "player")
        self.assertEqual(residual["status"], "poison")
        self.assertEqual(residual["damage"], 2)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 14)

    def test_toxic_residual_increments_counter(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "toxic"
        payload["state"]["player"]["toxic_count"] = 1
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        residual = next(event for event in report["outcomes"][0]["events"] if event["type"] == "residual_damage")
        self.assertEqual(residual["toxic_count_before"], 1)
        self.assertEqual(residual["toxic_count_after"], 2)
        self.assertEqual(residual["damage"], 2)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["toxic_count"], 2)

    def test_residual_faint_skips_later_action(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 1
        payload["state"]["player"]["status"] = "burn"
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        self.assertEqual([event["type"] for event in events], ["damage", "residual_damage"])
        self.assertTrue(report["outcomes"][0]["battle_over"])
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 0)

    def test_player_switch_takes_enemy_attack_on_new_active(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["bench"] = [
            {
                "name": "RESERVE",
                "hp": 30,
                "max_hp": 30,
                "types": ["NORMAL", "NORMAL"],
                "stats": {"attack": 10, "defense": 10, "speed": 9, "sp_attack": 10, "sp_defense": 10},
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
            }
        ]
        payload["actions"]["player"] = {"type": "switch", "bench_index": 0}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual([event["type"] for event in outcome["events"]], ["switch", "damage"])
        self.assertEqual(outcome["turn_order"], ["player", "enemy"])
        self.assertEqual(outcome["state"]["player"]["name"], "RESERVE")
        self.assertLess(outcome["state"]["player"]["hp"], 30)
        self.assertEqual(outcome["state"]["player_bench"][0]["name"], "PIDGEY")
        self.assertEqual(outcome["state"]["player_bench"][0]["hp"], 16)

    def test_enemy_switch_takes_player_attack_on_new_active(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "ENEMY_RESERVE",
                "hp": 30,
                "max_hp": 30,
                "types": ["NORMAL", "NORMAL"],
                "stats": {"attack": 10, "defense": 10, "speed": 8, "sp_attack": 10, "sp_defense": 10},
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
            }
        ]
        payload["actions"]["enemy"] = {"type": "switch", "bench_index": 0}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual([event["type"] for event in outcome["events"]], ["switch", "damage"])
        self.assertEqual(outcome["turn_order"], ["enemy", "player"])
        self.assertEqual(outcome["state"]["enemy"]["name"], "ENEMY_RESERVE")
        self.assertLess(outcome["state"]["enemy"]["hp"], 30)
        self.assertEqual(outcome["state"]["enemy_bench"][0]["name"], "CYNDAQUIL")

    def test_replacement_after_ko_allows_next_selected_turn(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["hp"] = 1
        payload["state"]["enemy"]["max_hp"] = 1
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "ENEMY_RESERVE",
                "hp": 1,
                "max_hp": 1,
                "types": ["NORMAL", "NORMAL"],
                "stats": {"attack": 10, "defense": 10, "speed": 8, "sp_attack": 10, "sp_defense": 10},
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0}],
            }
        ]
        payload["turns"] = [
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
            {"enemy": {"type": "replace", "bench_index": 0}},
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
        ]
        payload.pop("actions")

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertTrue(outcome["battle_over"])
        self.assertEqual([event["type"] for event in outcome["events"]], ["damage", "replacement", "damage"])
        self.assertEqual([event["turn"] for event in outcome["events"]], [1, 1, 2])
        self.assertEqual(outcome["turns_simulated"], 2)
        self.assertEqual(outcome["state"]["enemy"]["name"], "ENEMY_RESERVE")
        self.assertEqual(outcome["state"]["enemy"]["hp"], 0)

    def test_enemy_auto_replace_prefers_super_effective_candidate(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["types"] = ["FIRE", "FIRE"]
        payload["state"]["enemy"]["hp"] = 0
        payload["state"]["enemy"]["bench"] = [
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
        payload["actions"]["enemy"] = {"type": "auto_replace"}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        choice = next(event for event in outcome["events"] if event["type"] == "auto_replacement_choice")
        self.assertEqual(choice["selected_bench_index"], 1)
        self.assertEqual(choice["reason"], "candidate_super_effective_move")
        self.assertEqual(outcome["state"]["enemy"]["name"], "WATER_RESERVE")

    def test_enemy_auto_replace_avoids_player_super_effective_candidate(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["types"] = ["FIRE", "FIRE"]
        payload["state"]["enemy"]["hp"] = 0
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "GRASS_RESERVE",
                "hp": 20,
                "max_hp": 20,
                "types": ["GRASS", "GRASS"],
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
            },
            {
                "name": "NEUTRAL_RESERVE",
                "hp": 20,
                "max_hp": 20,
                "types": ["NORMAL", "NORMAL"],
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
            },
        ]
        payload["actions"]["enemy"] = {"type": "auto_replace"}

        report = simulate_payload(payload)

        choice = next(event for event in report["outcomes"][0]["events"] if event["type"] == "auto_replacement_choice")
        self.assertEqual(choice["selected_bench_index"], 1)
        self.assertEqual(choice["reason"], "not_player_discouraged")

    def test_enemy_auto_replace_keeps_mutual_pressure_candidate_acceptable(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["types"] = ["FIRE", "FIRE"]
        payload["state"]["enemy"]["hp"] = 0
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "MUTUAL_PRESSURE",
                "hp": 20,
                "max_hp": 20,
                "types": ["GRASS", "GRASS"],
                "moves": [{"name": "ROCK_HIT", "type": "ROCK", "bp": 40}],
            },
            {
                "name": "BAD_RESERVE",
                "hp": 20,
                "max_hp": 20,
                "types": ["BUG", "BUG"],
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
            },
        ]
        payload["actions"]["enemy"] = {"type": "auto_replace"}

        report = simulate_payload(payload)

        choice = next(event for event in report["outcomes"][0]["events"] if event["type"] == "auto_replacement_choice")
        self.assertEqual(choice["selected_bench_index"], 0)
        self.assertEqual(choice["reason"], "not_player_discouraged")
        self.assertTrue(choice["candidate_evaluations"][0]["candidate_has_super_effective_move"])
        self.assertTrue(choice["candidate_evaluations"][0]["opponent_has_super_effective_type"])

    def test_enemy_auto_replace_random_fallback_rejects_invalid_slots(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["types"] = ["FIRE", "FIRE"]
        payload["state"]["enemy"]["hp"] = 0
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "GRASS_RESERVE",
                "hp": 20,
                "max_hp": 20,
                "types": ["GRASS", "GRASS"],
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
            },
            {
                "name": "BUG_RESERVE",
                "hp": 20,
                "max_hp": 20,
                "types": ["BUG", "BUG"],
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
            },
        ]
        payload["actions"]["enemy"] = {"type": "auto_replace"}
        payload["rng"] = {"mode": "fixed", "values": [5, 1]}

        report = simulate_payload(payload)

        choice = next(event for event in report["outcomes"][0]["events"] if event["type"] == "auto_replacement_choice")
        self.assertEqual(choice["selected_bench_index"], 1)
        self.assertEqual(choice["reason"], "random_fallback")
        self.assertEqual(choice["raw_values"], [5, 1])

    def test_enemy_auto_replace_exhaustive_fallback_branches_legal_slots(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["types"] = ["FIRE", "FIRE"]
        payload["state"]["enemy"]["hp"] = 0
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "GRASS_RESERVE",
                "hp": 20,
                "max_hp": 20,
                "types": ["GRASS", "GRASS"],
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
            },
            {
                "name": "BUG_RESERVE",
                "hp": 20,
                "max_hp": 20,
                "types": ["BUG", "BUG"],
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
            },
        ]
        payload["actions"]["enemy"] = {"type": "auto_replace"}
        payload["rng"] = {"mode": "exhaustive"}

        report = simulate_payload(payload)

        selected_slots = {
            next(event for event in outcome["events"] if event["type"] == "auto_replacement_choice")[
                "selected_bench_index"
            ]
            for outcome in report["outcomes"]
        }
        self.assertEqual(report["outcome_count"], 2)
        self.assertEqual(selected_slots, {0, 1})

    def test_repeat_plan_auto_replace_or_runs_until_battle_over(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["hp"] = 1
        payload["state"]["enemy"]["max_hp"] = 1
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "ENEMY_RESERVE",
                "hp": 1,
                "max_hp": 1,
                "types": ["NORMAL", "NORMAL"],
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 0}],
            }
        ]
        payload.pop("actions")
        payload["repeat"] = {
            "max_turns": 5,
            "actions": {
                "player": {"type": "move", "move": 0},
                "enemy": {"type": "auto_replace_or", "action": {"type": "move", "move": 0}},
            },
        }

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertTrue(outcome["battle_over"])
        self.assertEqual(report["turn_count"], 5)
        self.assertEqual(outcome["turns_simulated"], 2)
        self.assertEqual(
            [event["type"] for event in outcome["events"]],
            ["damage", "auto_replacement_choice", "replacement", "damage"],
        )
        self.assertEqual([event["turn"] for event in outcome["events"]], [1, 1, 1, 2])
        self.assertEqual(outcome["state"]["enemy"]["hp"], 0)

    def test_turns_list_progresses_hp_across_selected_turns(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["turns"] = [
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
        ]
        payload.pop("actions")

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        damage_events = [event for event in outcome["events"] if event["type"] == "damage"]
        self.assertEqual(report["turn_count"], 2)
        self.assertEqual(outcome["turns_simulated"], 2)
        self.assertEqual([row["turn"] for row in outcome["turn_orders"]], [1, 2])
        self.assertEqual([event["turn"] for event in damage_events], [1, 2])
        self.assertLess(outcome["state"]["enemy"]["hp"], 18)
        self.assertEqual(outcome["state"]["turn"], 3)

    def test_planned_turns_stop_after_battle_over(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["hp"] = 1
        payload["state"]["enemy"]["max_hp"] = 1
        payload["turns"] = [
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
        ]
        payload.pop("actions")

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertTrue(outcome["battle_over"])
        self.assertEqual(outcome["turns_simulated"], 1)
        self.assertEqual([event["turn"] for event in outcome["events"]], [1])
        self.assertEqual(outcome["state"]["enemy"]["hp"], 0)

    def test_boss_ai_selector_action_reuses_score_bytes(self) -> None:
        payload = scenario_template()
        payload["actions"]["enemy"] = {
            "type": "boss_ai_selector",
            "scenario_id": "unit_selector",
            "tier": "late",
            "move_ids": [33, 52, 0, 0],
            "scores": [20, 30, 80, 80],
        }

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][1]
        self.assertEqual(event["type"], "boss_ai_select_move")
        self.assertTrue(event["selector"]["ready"])
        self.assertEqual(event["selector"]["best_slot_index"], 0)

    def test_boss_ai_selector_move_executes_selected_second_slot(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["moves"] = [
            {"name": "TACKLE", "type": "NORMAL", "bp": 0},
            {"name": "EMBER", "type": "FIRE", "bp": 40},
        ]
        payload["actions"]["enemy"] = {
            "type": "boss_ai_selector_move",
            "scenario_id": "unit_selector_execute",
            "tier": "late",
            "move_ids": [33, 52, 0, 0],
            "scores": [20, 21, 80, 80],
        }
        payload["rng"] = {"mode": "fixed", "values": [200, 255, 255]}

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        self.assertEqual(events[0]["type"], "boss_ai_select_move")
        self.assertEqual(events[0]["selected_slot_index"], 1)
        self.assertEqual(events[0]["selected_move"], "EMBER")
        self.assertEqual(events[0]["selector_check"]["raw_values"], [200])
        self.assertEqual(events[2]["type"], "damage")
        self.assertEqual(events[2]["actor"], "enemy")
        self.assertEqual(events[2]["move"], "EMBER")

    def test_exhaustive_boss_ai_selector_move_branches_best_and_second(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["moves"] = [
            {"name": "TACKLE", "type": "NORMAL", "bp": 0},
            {"name": "EMBER", "type": "FIRE", "bp": 0},
        ]
        payload["actions"]["enemy"] = {
            "type": "boss_ai_selector_move",
            "scenario_id": "unit_selector_exhaustive",
            "tier": "late",
            "move_ids": [33, 52, 0, 0],
            "scores": [20, 21, 80, 80],
        }
        payload["rng"] = {"mode": "exhaustive"}

        report = simulate_payload(payload)

        self.assertEqual(report["outcome_count"], 2)
        selected_slots = {
            outcome["events"][0]["selected_slot_index"]
            for outcome in report["outcomes"]
        }
        self.assertEqual(selected_slots, {0, 1})
        raw_ranges = {
            tuple(outcome["events"][0]["selector_check"]["raw_range"])
            for outcome in report["outcomes"]
        }
        self.assertEqual(raw_ranges, {(0, 185), (186, 255)})

    def test_wild_random_move_rejects_zero_pp_slot_then_executes(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["moves"] = [
            {"name": "TACKLE", "type": "NORMAL", "bp": 0, "pp": 0},
            {"name": "EMBER", "type": "FIRE", "bp": 40, "pp": 1},
        ]
        payload["actions"]["enemy"] = {"type": "wild_random_move"}
        payload["rng"] = {"mode": "fixed", "values": [0, 1, 255, 255]}

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        self.assertEqual(events[0]["type"], "wild_random_move")
        self.assertEqual(events[0]["selected_slot_index"], 1)
        self.assertEqual(events[0]["selector_check"]["raw_values"], [0, 1])
        self.assertEqual(events[2]["type"], "damage")
        self.assertEqual(events[2]["move"], "EMBER")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["moves"][1]["pp"], 0)

    def test_exhaustive_wild_random_move_branches_legal_slots(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["moves"] = [
            {"name": "TACKLE", "type": "NORMAL", "bp": 0, "pp": 1},
            {"name": "EMBER", "type": "FIRE", "bp": 0, "pp": 1},
            {"name": "WATER_GUN", "type": "WATER", "bp": 0, "pp": 0},
        ]
        payload["actions"]["enemy"] = {"type": "wild_random_move"}
        payload["rng"] = {"mode": "exhaustive"}

        report = simulate_payload(payload)

        self.assertEqual(report["outcome_count"], 2)
        selected_slots = {
            outcome["events"][0]["selected_slot_index"]
            for outcome in report["outcomes"]
        }
        self.assertEqual(selected_slots, {0, 1})

    def test_item_action_potion_heals_before_enemy_move(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 5
        payload["state"]["player"]["max_hp"] = 30
        payload["actions"]["player"] = {"type": "item", "item": "POTION"}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["turn_order"], ["player", "enemy"])
        self.assertEqual(outcome["events"][0]["type"], "item_restore")
        self.assertEqual(outcome["events"][0]["actor"], "player")
        self.assertEqual(outcome["events"][0]["heal"], 20)
        self.assertEqual(outcome["events"][0]["hp_after"], 25)
        self.assertEqual(outcome["events"][1]["type"], "damage")
        self.assertLess(outcome["state"]["player"]["hp"], 25)
        self.assertGreater(outcome["state"]["player"]["hp"], 5)

    def test_item_action_hyper_potion_caps_at_max_hp(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 90
        payload["state"]["player"]["max_hp"] = 100
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["actions"]["player"] = {"type": "item", "item": "HYPER_POTION"}

        report = simulate_payload(payload)

        item_event = report["outcomes"][0]["events"][0]
        self.assertEqual(item_event["type"], "item_restore")
        self.assertEqual(item_event["hp_restore_amount"], 200)
        self.assertEqual(item_event["heal"], 10)
        self.assertEqual(item_event["hp_after"], 100)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 100)

    def test_full_restore_heals_hp_and_cures_status(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 10
        payload["state"]["player"]["max_hp"] = 30
        payload["state"]["player"]["status"] = "toxic"
        payload["state"]["player"]["toxic_count"] = 3
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["actions"]["player"] = {"type": "item", "item": "FULL_RESTORE"}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        item_event = outcome["events"][0]
        self.assertEqual(item_event["type"], "item_restore")
        self.assertEqual(item_event["heal"], 20)
        self.assertEqual(item_event["status_before"], "toxic")
        self.assertEqual(item_event["status_after"], "none")
        self.assertEqual(item_event["toxic_count_after"], 0)
        self.assertFalse(any(event["type"] == "residual_damage" for event in outcome["events"]))
        self.assertEqual(outcome["state"]["player"]["hp"], 30)
        self.assertEqual(outcome["state"]["player"]["status"], "none")
        self.assertEqual(outcome["state"]["player"]["toxic_count"], 0)

    def test_item_action_applies_actor_residual_after_item(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 5
        payload["state"]["player"]["max_hp"] = 32
        payload["state"]["player"]["status"] = "poison"
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["actions"]["player"] = {"type": "item", "item": "POTION"}

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        self.assertEqual([event["type"] for event in events[:2]], ["item_restore", "residual_damage"])
        self.assertEqual(events[1]["actor"], "player")
        self.assertEqual(events[1]["damage"], 4)
        self.assertEqual(events[1]["hp_after"], 21)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 21)

    def test_enemy_item_action_runs_before_player_move(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["hp"] = 1
        payload["state"]["enemy"]["max_hp"] = 30
        payload["actions"]["enemy"] = {"type": "item", "item": "POTION"}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["turn_order"], ["enemy", "player"])
        self.assertEqual(outcome["events"][0]["type"], "item_restore")
        self.assertEqual(outcome["events"][0]["actor"], "enemy")
        self.assertEqual(outcome["events"][0]["hp_after"], 21)
        self.assertEqual(outcome["events"][1]["type"], "damage")

    def test_item_action_rejects_no_effect_restore(self) -> None:
        payload = scenario_template()
        payload["actions"]["player"] = {"type": "item", "item": "MAX_POTION"}

        with self.assertRaisesRegex(SimulationInputError, "has no effect"):
            simulate_payload(payload)

    def test_attack_stage_changes_damage(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        baseline = simulate_payload(payload)["outcomes"][0]["events"][0]["pre_variation_damage"]
        payload["state"]["player"]["stat_stages"] = {"attack": 2}

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertGreater(event["pre_variation_damage"], baseline)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["stat_stages"]["attack"], 2)

    def test_critical_uses_unmodified_damage_stats_when_defense_stage_is_higher(self) -> None:
        baseline = scenario_template()
        baseline["state"]["enemy"]["moves"][0]["bp"] = 0
        baseline["rng"] = {"mode": "fixed", "values": [0, 255, 0]}
        baseline_damage = simulate_payload(baseline)["outcomes"][0]["events"][0]["pre_variation_damage"]
        staged = scenario_template()
        staged["state"]["enemy"]["moves"][0]["bp"] = 0
        staged["state"]["player"]["stat_stages"] = {"attack": -6}
        staged["state"]["enemy"]["stat_stages"] = {"defense": 6}
        staged["rng"] = {"mode": "fixed", "values": [0, 255, 0]}

        report = simulate_payload(staged)

        event = report["outcomes"][0]["events"][0]
        self.assertTrue(event["critical_check"]["critical"])
        self.assertEqual(event["pre_variation_damage"], baseline_damage)

    def test_speed_stage_changes_turn_order(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 10
        payload["state"]["enemy"]["stats"]["speed"] = 12
        payload["state"]["player"]["stat_stages"] = {"speed": 1}
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["turn_order"], ["player", "enemy"])
        check = outcome["turn_orders"][0]["turn_order_check"]
        self.assertEqual(check["reason"], "modified_speed")
        self.assertEqual(check["effective_speeds"], {"player": 15, "enemy": 12})

    def test_switch_resets_stat_stages(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stat_stages"] = {"attack": 2}
        payload["state"]["player"]["bench"] = [
            {
                "name": "RESERVE",
                "hp": 30,
                "max_hp": 30,
                "types": ["NORMAL", "NORMAL"],
                "stat_stages": {"speed": 6},
                "stats": {"attack": 10, "defense": 10, "speed": 9, "sp_attack": 10, "sp_defense": 10},
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
            }
        ]
        payload["actions"]["player"] = {"type": "switch", "bench_index": 0}
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["state"]["player"]["name"], "RESERVE")
        self.assertEqual(outcome["state"]["player"]["stat_stages"]["speed"], 0)
        self.assertEqual(outcome["state"]["player_bench"][0]["stat_stages"]["attack"], 0)

    def test_accuracy_and_evasion_stages_are_out_of_scope(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stat_stages"] = {"accuracy": 1}

        with self.assertRaisesRegex(SimulationInputError, "accuracy/evasion stages"):
            simulate_payload(payload)

    def test_report_exposes_proof_boundary(self) -> None:
        report = simulate_payload(scenario_template())

        byte_proven = {row["id"] for row in report["coverage"]["byte_proven"]}
        mirrored = {row["id"] for row in report["coverage"]["source_mirrored_pending_differential"]}
        self.assertIn("damage_core_pre_variation", byte_proven)
        self.assertIn("damage_variation_rng_branching", mirrored)
        self.assertIn("basic_move_accuracy_rng", mirrored)
        self.assertIn("basic_critical_hit_rng", mirrored)
        self.assertIn("basic_status_residual", mirrored)
        self.assertIn("basic_pp_decrement", mirrored)
        self.assertIn("supported_after_hit_item_effects", mirrored)
        self.assertIn("explicit_active_hp_restore_items", mirrored)
        self.assertIn("selected_turn_order_priority_speed", mirrored)
        self.assertIn("explicit_stat_stage_state", mirrored)
        self.assertIn("repeat_plan_auto_replace_or", mirrored)
        self.assertIn("selected_switch_and_replacement", mirrored)
        self.assertIn("auto_replacement_choice_basic_type_chart", mirrored)
        self.assertIn("boss_ai_selector_from_post_score_bytes", mirrored)
        self.assertIn("boss_ai_selector_move_execution", mirrored)
        self.assertIn("wild_random_move_choice", mirrored)
        self.assertIn(
            "RNG-consuming mechanics outside speed ties/Boss AI selector choice/wild random move choice/auto-replace fallback/critical hits/accuracy/damage variation",
            "\n".join(report["coverage"]["out_of_scope"]),
        )

    def test_cli_json_out(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenario = Path(tmp) / "scenario.json"
            out = Path(tmp) / "report.json"
            scenario.write_text(json.dumps(scenario_template()), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                code = main(["--scenario", str(scenario), "--json-out", str(out)])

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], REPORT_KIND)


if __name__ == "__main__":
    unittest.main()
