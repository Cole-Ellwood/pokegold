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
        payload["rng"] = {"mode": "fixed", "values": [200, 255, 255, 255]}

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
        payload["rng"] = {"mode": "fixed", "values": [0, 1, 255, 255, 255]}

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

    def test_stat_stage_move_lowers_target_attack(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "GROWL"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        event = outcome["events"][0]
        self.assertEqual(event["type"], "stat_stage_change")
        self.assertEqual(event["move"], "GROWL")
        self.assertEqual(event["target"], "enemy")
        self.assertEqual(event["changes"][0]["stat"], "attack")
        self.assertEqual(event["changes"][0]["stage_after"], -1)
        self.assertEqual(event["pp_before"], 40)
        self.assertEqual(event["pp_after"], 39)
        self.assertEqual(outcome["state"]["enemy"]["stat_stages"]["attack"], -1)

    def test_stat_stage_move_uses_accuracy_check_for_lowering_move(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "SCREECH"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255]}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        event = outcome["events"][0]
        self.assertEqual(event["type"], "miss")
        self.assertEqual(event["move"], "SCREECH")
        self.assertEqual(event["accuracy_check"]["threshold"], 216)
        self.assertEqual(outcome["state"]["enemy"]["stat_stages"]["defense"], 0)

    def test_stat_stage_move_raises_actor_speed_and_changes_next_turn_order(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 10
        payload["state"]["enemy"]["stats"]["speed"] = 12
        payload["state"]["player"]["moves"] = [{"name": "AGILITY"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload.pop("actions")
        payload["turns"] = [
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
        ]

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        agility = next(event for event in outcome["events"] if event.get("move") == "AGILITY")
        self.assertEqual(agility["type"], "stat_stage_change")
        self.assertEqual(agility["changes"][0]["stat"], "speed")
        self.assertEqual(agility["changes"][0]["stage_after"], 2)
        self.assertEqual(outcome["turn_orders"][0]["order"], ["enemy", "player"])
        self.assertEqual(outcome["turn_orders"][1]["order"], ["player", "enemy"])

    def test_stat_stage_move_reports_no_effect_at_cap(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stat_stages"] = {"attack": 6}
        payload["state"]["player"]["moves"] = [{"name": "SWORDS_DANCE"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "stat_stage_no_effect")
        self.assertEqual(event["blocked_changes"][0]["stat"], "attack")
        self.assertEqual(event["blocked_changes"][0]["stage_before"], 6)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["stat_stages"]["attack"], 6)

    def test_calm_mind_raises_special_attack_and_defense(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "CALM_MIND"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        event = outcome["events"][0]
        self.assertEqual(event["type"], "stat_stage_change")
        self.assertEqual(event["move"], "CALM_MIND")
        self.assertEqual(
            [(row["stat"], row["stage_after"]) for row in event["changes"]],
            [("sp_attack", 1), ("sp_defense", 1)],
        )
        self.assertEqual(event["pp_before"], 20)
        self.assertEqual(event["pp_after"], 19)
        self.assertEqual(outcome["state"]["player"]["stat_stages"]["sp_attack"], 1)
        self.assertEqual(outcome["state"]["player"]["stat_stages"]["sp_defense"], 1)

    def test_quiver_dance_raises_speed_and_changes_next_turn_order(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 10
        payload["state"]["enemy"]["stats"]["speed"] = 12
        payload["state"]["player"]["moves"] = [{"name": "QUIVER_DANCE"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload.pop("actions")
        payload["turns"] = [
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
        ]

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        quiver = next(event for event in outcome["events"] if event.get("move") == "QUIVER_DANCE")
        self.assertEqual(
            [(row["stat"], row["stage_after"]) for row in quiver["changes"]],
            [("sp_attack", 1), ("sp_defense", 1), ("speed", 1)],
        )
        self.assertEqual(outcome["turn_orders"][0]["order"], ["enemy", "player"])
        self.assertEqual(outcome["turn_orders"][1]["order"], ["player", "enemy"])

    def test_dragon_dance_raises_best_attack_and_speed(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["attack"] = 20
        payload["state"]["player"]["stats"]["sp_attack"] = 10
        payload["state"]["player"]["moves"] = [{"name": "DRAGON_DANCE"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(
            [(row["stat"], row["stage_after"]) for row in event["changes"]],
            [("attack", 1), ("speed", 1)],
        )

    def test_dragon_dance_uses_special_attack_when_higher(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["attack"] = 10
        payload["state"]["player"]["stats"]["sp_attack"] = 20
        payload["state"]["player"]["moves"] = [{"name": "DRAGON_DANCE"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(
            [(row["stat"], row["stage_after"]) for row in event["changes"]],
            [("sp_attack", 1), ("speed", 1)],
        )

    def test_damaging_secondary_burn_applies_after_damage(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "EMBER"}]
        payload["state"]["enemy"]["types"] = ["NORMAL", "NORMAL"]
        payload["state"]["enemy"]["hp"] = 40
        payload["state"]["enemy"]["max_hp"] = 40
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        damage = events[0]
        burn = events[1]
        self.assertEqual(damage["type"], "damage")
        self.assertEqual(burn["type"], "status_apply")
        self.assertEqual(burn["move"], "EMBER")
        self.assertEqual(burn["status"], "burn")
        self.assertEqual(burn["effect_chance_check"]["threshold"], 25)
        self.assertEqual(burn["effect_chance_check"]["raw_values"], [0])
        self.assertEqual(burn["target_hp_after_damage"], damage["target_hp_after"])
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "burn")

    def test_damaging_secondary_effect_chance_failure_does_not_status(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "EMBER"}]
        payload["state"]["enemy"]["types"] = ["NORMAL", "NORMAL"]
        payload["state"]["enemy"]["hp"] = 40
        payload["state"]["enemy"]["max_hp"] = 40
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 255]}

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][1]
        self.assertEqual(event["type"], "status_no_effect")
        self.assertEqual(event["blocked_reason"], "effect_chance_failed")
        self.assertEqual(event["effect_chance_check"]["raw_values"], [255])
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "none")

    def test_damaging_secondary_safeguard_blocks_after_effect_chance(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "EMBER"}]
        payload["state"]["enemy"]["safeguard"] = True
        payload["state"]["enemy"]["types"] = ["NORMAL", "NORMAL"]
        payload["state"]["enemy"]["hp"] = 40
        payload["state"]["enemy"]["max_hp"] = 40
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        damage, status = outcome["events"][0], outcome["events"][1]
        self.assertEqual(damage["type"], "damage")
        self.assertLess(damage["target_hp_after"], damage["target_hp_before"])
        self.assertEqual(status["type"], "status_no_effect")
        self.assertEqual(status["blocked_reason"], "safeguard")
        self.assertEqual(status["effect_chance_check"]["success"], True)
        self.assertEqual(outcome["state"]["enemy"]["status"], "none")

    def test_damaging_move_into_substitute_is_out_of_scope(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["substitute"] = True

        with self.assertRaisesRegex(SimulationInputError, "Substitute is out of scope"):
            simulate_payload(payload)

    def test_damaging_secondary_poison_applies_and_residual_ticks(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "SLUDGE"}]
        payload["state"]["enemy"]["hp"] = 48
        payload["state"]["enemy"]["max_hp"] = 48
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        poison = next(event for event in events if event.get("type") == "status_apply")
        residual = events[-1]
        self.assertEqual(poison["status"], "poison")
        self.assertEqual(poison["effect_chance_check"]["threshold"], 76)
        self.assertEqual(residual["type"], "residual_damage")
        self.assertEqual(residual["status"], "poison")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "poison")

    def test_damaging_secondary_paralysis_changes_next_turn_order(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 10
        payload["state"]["enemy"]["stats"]["speed"] = 12
        payload["state"]["enemy"]["hp"] = 80
        payload["state"]["enemy"]["max_hp"] = 80
        payload["state"]["player"]["moves"] = [{"name": "BODY_SLAM"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload.pop("actions")
        payload["turns"] = [
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
        ]
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 0, 255, 255, 255, 255]}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        paralyze = next(event for event in outcome["events"] if event.get("type") == "status_apply")
        self.assertEqual(paralyze["status"], "paralyze")
        self.assertEqual(paralyze["effect_chance_check"]["threshold"], 76)
        self.assertEqual(outcome["turn_orders"][0]["order"], ["enemy", "player"])
        self.assertEqual(outcome["turn_orders"][1]["order"], ["player", "enemy"])

    def test_damaging_secondary_held_status_cure_consumes_item(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "EMBER"}]
        payload["state"]["enemy"]["types"] = ["NORMAL", "NORMAL"]
        payload["state"]["enemy"]["item"] = "ICE_BERRY"
        payload["state"]["enemy"]["hp"] = 40
        payload["state"]["enemy"]["max_hp"] = 40
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        event = events[1]
        cure = events[2]
        self.assertEqual(event["type"], "status_apply")
        self.assertEqual(event["status"], "burn")
        self.assertEqual(cure["type"], "held_status_cure")
        self.assertEqual(cure["source_item"], "ICE_BERRY")
        self.assertEqual(cure["cured_status"], "burn")
        self.assertEqual(cure["proof_status"], "source_mirrored_selected_held_status_cure_active")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "none")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["item"], 0)

    def test_drain_move_heals_half_actual_damage(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 5
        payload["state"]["player"]["max_hp"] = 40
        payload["state"]["player"]["moves"] = [{"name": "GIGA_DRAIN"}, {"name": "TACKLE", "bp": 0}]
        payload["state"]["enemy"]["hp"] = 40
        payload["state"]["enemy"]["max_hp"] = 40
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        damage = events[0]
        drain = events[1]
        self.assertEqual(drain["type"], "drain_heal")
        self.assertEqual(drain["move"], "GIGA_DRAIN")
        self.assertEqual(drain["damage_drained"], damage["actual_damage"])
        self.assertEqual(drain["raw_heal"], max(1, damage["actual_damage"] // 2))
        self.assertEqual(drain["heal"], drain["raw_heal"])
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 5 + drain["heal"])

    def test_drain_move_heals_at_least_one_from_one_damage(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 5
        payload["state"]["player"]["max_hp"] = 40
        payload["state"]["player"]["moves"] = [{"name": "ABSORB"}]
        payload["state"]["enemy"]["hp"] = 1
        payload["state"]["enemy"]["max_hp"] = 40
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}

        report = simulate_payload(payload)

        drain = report["outcomes"][0]["events"][1]
        self.assertEqual(drain["type"], "drain_heal")
        self.assertEqual(drain["damage_drained"], 1)
        self.assertEqual(drain["raw_heal"], 1)
        self.assertEqual(drain["heal"], 1)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 6)

    def test_drain_move_healing_caps_at_max_hp(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 39
        payload["state"]["player"]["max_hp"] = 40
        payload["state"]["player"]["moves"] = [{"name": "MEGA_DRAIN"}]
        payload["state"]["enemy"]["hp"] = 40
        payload["state"]["enemy"]["max_hp"] = 40
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}

        report = simulate_payload(payload)

        drain = report["outcomes"][0]["events"][1]
        self.assertEqual(drain["type"], "drain_heal")
        self.assertGreater(drain["raw_heal"], 0)
        self.assertEqual(drain["heal"], 1)
        self.assertEqual(drain["hp_after"], 40)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 40)

    def test_drain_move_miss_does_not_heal(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 5
        payload["state"]["player"]["max_hp"] = 40
        payload["state"]["player"]["moves"] = [{"name": "GIGA_DRAIN", "accuracy": 1}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 255]}

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        self.assertEqual(events[0]["type"], "miss")
        self.assertFalse(any(event["type"].startswith("drain") for event in events))
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 5)

    def test_drain_move_healed_hp_carries_to_next_turn(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 5
        payload["state"]["player"]["max_hp"] = 40
        payload["state"]["player"]["moves"] = [{"name": "GIGA_DRAIN"}, {"name": "TACKLE", "bp": 0}]
        payload["state"]["enemy"]["hp"] = 40
        payload["state"]["enemy"]["max_hp"] = 40
        payload.pop("actions")
        payload["turns"] = [
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
        ]
        payload["state"]["enemy"]["moves"] = [{"name": "TACKLE", "bp": 0}, {"name": "TACKLE"}]
        payload["turns"][1]["player"] = {"type": "move", "move": 1}
        payload["turns"][1]["enemy"] = {"type": "move", "move": 1}
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 255, 255]}

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        drain = next(event for event in events if event["type"] == "drain_heal")
        enemy_damage = [event for event in events if event.get("actor") == "enemy" and event["type"] == "damage"][0]
        self.assertEqual(enemy_damage["target_hp_before"], drain["hp_after"])

    def test_sleep_status_move_applies_duration_and_denies_target_action(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "SLEEP_POWDER"}]
        payload["state"]["enemy"]["moves"] = [{"name": "TACKLE"}]
        payload["rng"] = {"mode": "fixed", "values": [0, 0]}

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        sleep = events[0]
        denied = events[1]
        self.assertEqual(sleep["type"], "status_apply")
        self.assertEqual(sleep["status"], "sleep")
        self.assertEqual(sleep["sleep_turns_after"], 3)
        self.assertEqual(sleep["sleep_duration"]["denied_actions"], 2)
        self.assertEqual(denied["type"], "fast_asleep")
        self.assertEqual(denied["sleep_turns_after"], 2)
        self.assertEqual(denied["pp_before"], denied["pp_after"])
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "sleep")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["sleep_turns"], 2)

    def test_sleep_status_exhaustive_branches_three_durations(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "SPORE"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "exhaustive"}

        report = simulate_payload(payload)

        self.assertEqual(report["outcome_count"], 3)
        durations = {
            outcome["events"][0]["sleep_duration"]["sleep_turns"]
            for outcome in report["outcomes"]
        }
        self.assertEqual(durations, {3, 4, 5})

    def test_sleep_status_safeguard_blocks_before_duration_rng(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "SLEEP_POWDER"}]
        payload["state"]["enemy"]["safeguard"] = True
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [0]}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        event = outcome["events"][0]
        self.assertEqual(event["type"], "status_no_effect")
        self.assertEqual(event["blocked_reason"], "safeguard")
        self.assertIsNone(event["sleep_duration"])
        self.assertEqual(outcome["rng_consumed"], [0])
        self.assertEqual(outcome["state"]["enemy"]["status"], "none")

    def test_sleep_status_safeguard_wins_over_substitute(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "SLEEP_POWDER"}]
        payload["state"]["enemy"]["safeguard"] = True
        payload["state"]["enemy"]["substitute"] = True
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [0]}

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "status_no_effect")
        self.assertEqual(event["blocked_reason"], "safeguard")

    def test_sleep_wake_turn_continues_selected_move(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "sleep"
        payload["state"]["player"]["sleep_turns"] = 1
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        self.assertEqual(events[0]["type"], "woke_up")
        self.assertEqual(events[0]["status_after"], "none")
        self.assertEqual(events[1]["type"], "damage")
        self.assertEqual(events[1]["actor"], "player")
        self.assertEqual(report["outcomes"][0]["state"]["player"]["status"], "none")

    def test_sleep_denial_does_not_decrement_pp(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "sleep"
        payload["state"]["player"]["sleep_turns"] = 3
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "fast_asleep")
        self.assertEqual(event["sleep_turns_after"], 2)
        self.assertEqual(event["pp_before"], 35)
        self.assertEqual(event["pp_after"], 35)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["moves"][0]["pp"], 35)

    def test_sleep_status_healing_berry_consumes_item_and_allows_action(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "SLEEP_POWDER"}]
        payload["state"]["enemy"]["item"] = "MINT_BERRY"
        payload["rng"] = {"mode": "fixed", "values": [0, 0, 255, 255, 0]}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        events = outcome["events"]
        self.assertEqual([event["type"] for event in events[:3]], ["status_apply", "held_status_cure", "damage"])
        self.assertEqual(events[0]["status"], "sleep")
        self.assertEqual(events[0]["sleep_turns_after"], 3)
        self.assertEqual(events[1]["source_item"], "MINT_BERRY")
        self.assertEqual(events[1]["cured_status"], "sleep")
        self.assertEqual(events[1]["sleep_turns_after"], 0)
        self.assertEqual(events[2]["actor"], "enemy")
        self.assertEqual(outcome["state"]["enemy"]["status"], "none")
        self.assertEqual(outcome["state"]["enemy"]["sleep_turns"], 0)
        self.assertEqual(outcome["state"]["enemy"]["item"], 0)
        self.assertEqual(outcome["state"]["enemy"]["moves"][0]["pp"], 34)

    def test_rest_sets_sleep_counter_and_full_hp(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 5
        payload["state"]["player"]["max_hp"] = 40
        payload["state"]["player"]["status"] = "toxic"
        payload["state"]["player"]["toxic_count"] = 2
        payload["state"]["player"]["moves"] = [{"name": "REST"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        state = report["outcomes"][0]["state"]["player"]
        self.assertEqual(event["type"], "rest")
        self.assertEqual(event["hp_after"], 40)
        self.assertEqual(event["status_before"], "toxic")
        self.assertEqual(event["status_after"], "sleep")
        self.assertEqual(event["sleep_turns_after"], 3)
        self.assertEqual(event["toxic_count_after"], 0)
        self.assertEqual(state["hp"], 40)
        self.assertEqual(state["status"], "sleep")
        self.assertEqual(state["sleep_turns"], 3)
        self.assertEqual(state["toxic_count"], 0)

    def test_rest_at_full_hp_reports_no_effect(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "REST"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "rest_no_effect")
        self.assertEqual(event["reason"], "hp_full")
        self.assertEqual(report["outcomes"][0]["state"]["player"]["status"], "none")

    def test_self_heal_move_restores_half_max_hp(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 10
        payload["state"]["player"]["max_hp"] = 40
        payload["state"]["player"]["moves"] = [{"name": "RECOVER"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "self_heal")
        self.assertEqual(event["move"], "RECOVER")
        self.assertEqual(event["raw_heal"], 20)
        self.assertEqual(event["heal"], 20)
        self.assertEqual(event["hp_before"], 10)
        self.assertEqual(event["hp_after"], 30)
        self.assertEqual(event["pp_before"], 20)
        self.assertEqual(event["pp_after"], 19)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 30)

    def test_self_heal_move_caps_at_max_hp(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 35
        payload["state"]["player"]["max_hp"] = 40
        payload["state"]["player"]["moves"] = [{"name": "MILK_DRINK"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "self_heal")
        self.assertEqual(event["move"], "MILK_DRINK")
        self.assertEqual(event["raw_heal"], 20)
        self.assertEqual(event["heal"], 5)
        self.assertEqual(event["hp_after"], 40)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 40)

    def test_self_heal_move_reports_no_effect_at_full_hp(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 40
        payload["state"]["player"]["max_hp"] = 40
        payload["state"]["player"]["moves"] = [{"name": "SOFTBOILED"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "self_heal_no_effect")
        self.assertEqual(event["move"], "SOFTBOILED")
        self.assertEqual(event["blocked_reason"], "hp_full")
        self.assertEqual(event["heal"], 0)
        self.assertEqual(event["pp_before"], 10)
        self.assertEqual(event["pp_after"], 9)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 40)

    def test_self_heal_move_applies_actor_residual_after_turn(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 10
        payload["state"]["player"]["max_hp"] = 40
        payload["state"]["player"]["status"] = "poison"
        payload["state"]["player"]["moves"] = [{"name": "RECOVER"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        self.assertEqual([event["type"] for event in events[:2]], ["self_heal", "residual_damage"])
        self.assertEqual(events[0]["hp_after"], 30)
        self.assertEqual(events[1]["damage"], 5)
        self.assertEqual(events[1]["hp_after"], 25)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 25)

    def test_rest_is_supported_once_sleep_is_modeled(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 10
        payload["state"]["player"]["max_hp"] = 40
        payload["state"]["player"]["moves"] = [{"name": "REST"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "rest")
        self.assertEqual(event["move"], "REST")
        self.assertEqual(event["proof_status"], "source_mirrored_selected_rest_move")
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 40)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["status"], "sleep")

    def test_poison_status_move_applies_poison_and_residual(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "POISONPOWDER"}]
        payload["state"]["enemy"]["hp"] = 32
        payload["state"]["enemy"]["max_hp"] = 32
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        self.assertEqual(events[0]["type"], "status_apply")
        self.assertEqual(events[0]["move"], "POISONPOWDER")
        self.assertEqual(events[0]["status"], "poison")
        self.assertEqual(events[0]["status_before"], "none")
        self.assertEqual(events[0]["status_after"], "poison")
        self.assertEqual(events[0]["pp_before"], 35)
        self.assertEqual(events[0]["pp_after"], 34)
        self.assertEqual(events[-1]["type"], "residual_damage")
        self.assertEqual(events[-1]["actor"], "enemy")
        self.assertEqual(events[-1]["damage"], 4)
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "poison")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["hp"], 28)

    def test_toxic_status_move_sets_toxic_count_for_first_residual_tick(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "TOXIC"}]
        payload["state"]["enemy"]["hp"] = 48
        payload["state"]["enemy"]["max_hp"] = 48
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        events = report["outcomes"][0]["events"]
        toxic = events[0]
        residual = events[-1]
        self.assertEqual(toxic["type"], "status_apply")
        self.assertEqual(toxic["status"], "toxic")
        self.assertEqual(toxic["toxic_count_after"], 0)
        self.assertEqual(toxic["pp_before"], 10)
        self.assertEqual(toxic["pp_after"], 9)
        self.assertEqual(residual["type"], "residual_damage")
        self.assertEqual(residual["status"], "toxic")
        self.assertEqual(residual["damage"], 3)
        self.assertEqual(residual["toxic_count_before"], 0)
        self.assertEqual(residual["toxic_count_after"], 1)
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "toxic")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["toxic_count"], 1)

    def test_poison_status_move_uses_accuracy_check(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "POISON_GAS"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255]}

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "miss")
        self.assertEqual(event["move"], "POISON_GAS")
        self.assertEqual(event["accuracy_check"]["threshold"], 140)
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "none")

    def test_poison_status_move_reports_no_effect_on_poison_type(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "POISONPOWDER"}]
        payload["state"]["enemy"]["types"] = ["POISON", "POISON"]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "status_no_effect")
        self.assertEqual(event["blocked_reason"], "poison_type")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "none")

    def test_poison_status_move_reports_no_effect_on_type_immunity(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "TOXIC"}]
        payload["state"]["enemy"]["types"] = ["STEEL", "STEEL"]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "status_no_effect")
        self.assertEqual(event["blocked_reason"], "type_immunity")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "none")

    def test_poison_status_move_reports_no_effect_on_existing_status(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "TOXIC"}]
        payload["state"]["enemy"]["status"] = "burn"
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "status_no_effect")
        self.assertEqual(event["blocked_reason"], "already_statused")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "burn")

    def test_poison_status_healing_berry_consumes_item(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "POISONPOWDER"}]
        payload["state"]["enemy"]["item"] = "PSNCUREBERRY"
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        events = outcome["events"]
        self.assertEqual(events[0]["type"], "status_apply")
        self.assertEqual(events[0]["status"], "poison")
        self.assertEqual(events[1]["type"], "held_status_cure")
        self.assertEqual(events[1]["source_item"], "PSNCUREBERRY")
        self.assertEqual(events[1]["cured_status"], "poison")
        self.assertEqual(events[1]["toxic_count_after"], 0)
        self.assertEqual(outcome["state"]["enemy"]["status"], "none")
        self.assertEqual(outcome["state"]["enemy"]["toxic_count"], 0)
        self.assertEqual(outcome["state"]["enemy"]["item"], 0)
        self.assertFalse(any(event["type"] == "residual_damage" for event in events))

    def test_poison_status_substitute_blocks(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "POISONPOWDER"}]
        payload["state"]["enemy"]["substitute"] = True
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "status_no_effect")
        self.assertEqual(event["blocked_reason"], "substitute")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "none")

    def test_miracleberry_cures_toxic_status_move(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "TOXIC"}]
        payload["state"]["enemy"]["item"] = "MIRACLEBERRY"
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        cure = outcome["events"][1]
        self.assertEqual(cure["type"], "held_status_cure")
        self.assertEqual(cure["source_item"], "MIRACLEBERRY")
        self.assertEqual(cure["cured_status"], "toxic")
        self.assertEqual(outcome["state"]["enemy"]["status"], "none")
        self.assertEqual(outcome["state"]["enemy"]["toxic_count"], 0)
        self.assertEqual(outcome["state"]["enemy"]["item"], 0)

    def test_paralysis_status_move_applies_paralysis(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "THUNDER_WAVE"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "status_apply")
        self.assertEqual(event["move"], "THUNDER_WAVE")
        self.assertEqual(event["status"], "paralyze")
        self.assertEqual(event["status_before"], "none")
        self.assertEqual(event["status_after"], "paralyze")
        self.assertEqual(event["pp_before"], 20)
        self.assertEqual(event["pp_after"], 19)
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "paralyze")

    def test_paralysis_status_healing_berry_consumes_item(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "THUNDER_WAVE"}]
        payload["state"]["enemy"]["item"] = "PRZCUREBERRY"
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        events = outcome["events"]
        self.assertEqual(events[0]["type"], "status_apply")
        self.assertEqual(events[0]["status"], "paralyze")
        self.assertEqual(events[1]["type"], "held_status_cure")
        self.assertEqual(events[1]["source_item"], "PRZCUREBERRY")
        self.assertEqual(events[1]["cured_status"], "paralyze")
        self.assertEqual(outcome["state"]["enemy"]["status"], "none")
        self.assertEqual(outcome["state"]["enemy"]["item"], 0)

    def test_paralysis_status_safeguard_blocks(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "THUNDER_WAVE"}]
        payload["state"]["enemy"]["safeguard"] = True
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "status_no_effect")
        self.assertEqual(event["blocked_reason"], "safeguard")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "none")

    def test_paralysis_status_move_uses_accuracy_check(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "STUN_SPORE"}]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255]}

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "miss")
        self.assertEqual(event["move"], "STUN_SPORE")
        self.assertEqual(event["accuracy_check"]["threshold"], 191)
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "none")

    def test_paralysis_status_move_reports_no_effect_on_type_immunity(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "THUNDER_WAVE"}]
        payload["state"]["enemy"]["types"] = ["GROUND", "GROUND"]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "status_no_effect")
        self.assertEqual(event["blocked_reason"], "type_immunity")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "none")

    def test_glare_reports_no_effect_on_ghost_immunity(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "GLARE"}]
        payload["state"]["enemy"]["types"] = ["GHOST", "GHOST"]
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "status_no_effect")
        self.assertEqual(event["blocked_reason"], "type_immunity")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "none")

    def test_paralysis_status_move_reports_no_effect_on_existing_status(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = [{"name": "THUNDER_WAVE"}]
        payload["state"]["enemy"]["status"] = "poison"
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "status_no_effect")
        self.assertEqual(event["blocked_reason"], "already_statused")
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["status"], "poison")

    def test_paralysis_speed_changes_next_turn_order(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 40
        payload["state"]["enemy"]["stats"]["speed"] = 80
        payload["state"]["player"]["moves"] = [
            {"name": "THUNDER_WAVE"},
            {"name": "TACKLE", "type": "NORMAL", "bp": 40},
        ]
        payload["state"]["enemy"]["hp"] = 100
        payload["state"]["enemy"]["max_hp"] = 100
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload.pop("actions")
        payload["turns"] = [
            {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
            {"player": {"type": "move", "move": 1}, "enemy": {"type": "move", "move": 0}},
        ]

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["turn_orders"][0]["order"], ["enemy", "player"])
        self.assertEqual(outcome["turn_orders"][1]["order"], ["player", "enemy"])
        self.assertEqual(outcome["turn_orders"][1]["turn_order_check"]["effective_speeds"]["enemy"], 20)

    def test_full_paralysis_skips_move_before_pp_decrement(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 80
        payload["state"]["player"]["status"] = "paralyze"
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [0]}

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "fully_paralyzed")
        self.assertEqual(event["paralysis_check"]["threshold"], 63)
        self.assertEqual(event["paralysis_check"]["raw_values"], [0])
        self.assertEqual(event["pp_before"], 35)
        self.assertEqual(event["pp_after"], 35)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["moves"][0]["pp"], 35)
        self.assertEqual(report["outcomes"][0]["state"]["enemy"]["hp"], 18)

    def test_full_paralysis_high_roll_allows_move(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 80
        payload["state"]["player"]["status"] = "paralyze"
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 255, 0]}

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "damage")
        self.assertEqual(event["critical_check"]["raw_values"], [255])
        self.assertEqual(report["outcomes"][0]["state"]["player"]["moves"][0]["pp"], 34)

    def test_fighting_type_passive_reduces_full_paralysis_odds(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 80
        payload["state"]["player"]["types"] = ["FIGHTING", "FIGHTING"]
        payload["state"]["player"]["status"] = "paralyze"
        payload["state"]["enemy"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "fixed", "values": [40, 255, 255, 0]}

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "damage")
        self.assertEqual(report["outcomes"][0]["turn_orders"][0]["turn_order_check"]["effective_speeds"]["player"], 40)

        payload["rng"] = {"mode": "fixed", "values": [37]}
        blocked = simulate_payload(payload)
        blocked_event = blocked["outcomes"][0]["events"][0]
        self.assertEqual(blocked_event["type"], "fully_paralyzed")
        self.assertEqual(blocked_event["paralysis_check"]["threshold"], 38)

    def test_partial_fighting_paralysis_speed_fraction(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 80
        payload["state"]["enemy"]["stats"]["speed"] = 31
        payload["state"]["player"]["types"] = ["FIGHTING", "NORMAL"]
        payload["state"]["player"]["status"] = "paralyze"
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        check = report["outcomes"][0]["turn_orders"][0]["turn_order_check"]
        self.assertEqual(check["effective_speeds"]["player"], 30)
        self.assertEqual(report["outcomes"][0]["turn_order"], ["enemy", "player"])

    def test_electric_type_passive_boosts_speed_before_paralysis_fraction(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 80
        payload["state"]["enemy"]["stats"]["speed"] = 20
        payload["state"]["player"]["types"] = ["ELECTRIC", "ELECTRIC"]
        payload["state"]["player"]["status"] = "paralyze"
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        check = report["outcomes"][0]["turn_orders"][0]["turn_order_check"]
        self.assertEqual(check["effective_speeds"]["player"], 21)
        self.assertEqual(report["outcomes"][0]["turn_order"], ["player", "enemy"])

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
        self.assertIn("selected_stat_stage_only_moves", mirrored)
        self.assertIn("selected_multi_stat_setup_moves", mirrored)
        self.assertIn("selected_damaging_status_secondaries", mirrored)
        self.assertIn("selected_drain_moves", mirrored)
        self.assertIn("selected_sleep_status_moves", mirrored)
        self.assertIn("selected_rest_move", mirrored)
        self.assertIn("selected_held_status_cures", mirrored)
        self.assertIn("selected_safeguard_substitute_blockers", mirrored)
        self.assertIn("selected_self_heal_moves", mirrored)
        self.assertIn("selected_poison_status_moves", mirrored)
        self.assertIn("selected_paralysis_status_moves", mirrored)
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
