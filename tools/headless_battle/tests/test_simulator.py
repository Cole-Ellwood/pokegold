from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.headless_battle.__main__ import main
from tools.headless_battle.rom_diff import (
    CRITICAL_DIFFERENTIAL_CASES,
    LeftoversDifferentialCase,
    ParalysisTurnDifferentialCase,
    SleepTurnDifferentialCase,
    TURN_ORDER_DIFFERENTIAL_CASES,
    python_accuracy_result,
    python_critical_result,
    python_damage_variation_result,
    python_flinch_turn_result,
    python_freeze_turn_result,
    python_leftovers_result,
    python_paralysis_turn_result,
    python_residual_status_result,
    python_sleep_turn_result,
    python_status_speed_result,
    python_turn_order_result,
    FlinchTurnDifferentialCase,
    FreezeTurnDifferentialCase,
    ResidualStatusDifferentialCase,
    StatusSpeedDifferentialCase,
)
from tools.headless_battle.simulator import (
    SimulationInputError,
    format_text,
    scenario_template,
    simulate_payload,
)


class HeadlessBattleSimulatorTests(unittest.TestCase):
    def test_fixed_rng_runs_one_turn_with_oracle_damage(self) -> None:
        payload = scenario_template()
        report = simulate_payload(payload)

        self.assertEqual(report["kind"], "headless_battle_turn_simulation")
        self.assertEqual(report["outcome_count"], 1)
        self.assertEqual(report["summary"]["weight_basis"], "outcome_count")
        outcome = report["outcomes"][0]
        self.assertEqual(outcome["turn_order"], ["player", "enemy"])
        self.assertIsNone(outcome["rng_weight"])
        self.assertEqual([row["source"] for row in outcome["rng_trace"]], ["critical_hit", "damage_variation"])
        damage_event = outcome["events"][0]
        self.assertEqual(damage_event["type"], "damage")
        self.assertFalse(damage_event["critical_hit"])
        self.assertEqual(damage_event["pre_variation_damage"], 4)
        self.assertEqual(damage_event["damage"], 4)
        self.assertEqual(outcome["state"]["enemy"]["hp"], 14)

    def test_exhaustive_rng_branches_damage_variation(self) -> None:
        payload = scenario_template()
        payload["rng"] = {"mode": "exhaustive"}
        report = simulate_payload(payload)

        self.assertEqual(report["outcome_count"], 78)
        damages = sorted({outcome["events"][0]["damage"] for outcome in report["outcomes"]})
        self.assertEqual(damages, [3, 4, 5, 6])
        self.assertEqual(report["outcomes"][0]["branch_path"][1]["source"], "critical_hit")
        self.assertEqual(report["outcomes"][0]["branch_path"][2]["source"], "damage_variation")

    def test_sample_rng_honors_sample_count(self) -> None:
        payload = scenario_template()
        payload["rng"] = {"mode": "sample", "seed": 7, "samples": 3}
        report = simulate_payload(payload)

        self.assertEqual(report["outcome_count"], 3)
        self.assertEqual([outcome["sample_index"] for outcome in report["outcomes"]], [0, 1, 2])
        self.assertTrue(all(outcome["outcome_id"].startswith("sample") for outcome in report["outcomes"]))

    def test_fixed_rng_can_miss_on_accuracy(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["accuracy"] = 128
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 128]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "miss")
        self.assertEqual(outcome["state"]["enemy"]["hp"], 18)
        self.assertEqual([row["source"] for row in outcome["rng_trace"]], ["critical_hit", "damage_variation", "accuracy"])
        self.assertFalse(outcome["rng_trace"][2]["hit"])

    def test_damage_variation_consumes_rng_before_accuracy(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["accuracy"] = 128
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 0]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "damage")
        self.assertEqual(outcome["events"][0]["damage"], 4)
        self.assertEqual([row["source"] for row in outcome["rng_trace"]], ["critical_hit", "damage_variation", "accuracy"])

    def test_burn_residual_applies_after_actor_action(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "burn"
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        residual = [event for event in outcome["events"] if event["type"] == "residual_status_damage"]
        self.assertEqual(len(residual), 1)
        self.assertEqual(residual[0]["actor"], "player")
        self.assertEqual(residual[0]["status"], "burn")
        self.assertEqual(residual[0]["damage"], 2)
        self.assertEqual(outcome["state"]["player"]["hp"], 14)

    def test_toxic_residual_increments_counter_and_can_faint(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 3
        payload["state"]["player"]["status"] = "toxic"
        payload["state"]["player"]["toxic_count"] = 2
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        residual = [event for event in outcome["events"] if event["type"] == "residual_status_damage"][0]
        self.assertEqual(residual["damage"], 3)
        self.assertEqual(residual["toxic_count_before"], 2)
        self.assertEqual(residual["toxic_count_after"], 3)
        self.assertTrue(residual["fainted"])
        self.assertEqual(outcome["state"]["player"]["hp"], 0)
        self.assertTrue(outcome["battle_over"])

    def test_residual_skips_when_damage_already_fainted_target(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "poison"
        payload["state"]["enemy"]["hp"] = 4
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertNotIn("residual_status_damage", [event["type"] for event in outcome["events"]])
        self.assertEqual(outcome["state"]["player"]["hp"], 16)

    def test_leftovers_heals_between_turns(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 8
        payload["state"]["player"]["item"] = "LEFTOVERS"
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        heal = [event for event in outcome["events"] if event["type"] == "between_turn_heal"][0]
        self.assertEqual(heal["actor"], "player")
        self.assertEqual(heal["item"], "LEFTOVERS")
        self.assertEqual(heal["healed"], 1)
        self.assertEqual(outcome["state"]["player"]["hp"], 9)

    def test_leftovers_skips_when_forced_switch_prompt_pending(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 8
        payload["state"]["player"]["item"] = "LEFTOVERS"
        payload["state"]["enemy"]["hp"] = 4
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertNotIn("between_turn_heal", [event["type"] for event in outcome["events"]])
        self.assertEqual(outcome["state"]["player"]["hp"], 8)

    def test_paralysis_can_block_move_before_damage_rng(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "paralysis"
        payload["rng"] = {"mode": "fixed", "values": [0]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "turn_blocked")
        self.assertEqual(outcome["events"][0]["reason"], "fully_paralyzed")
        self.assertEqual(outcome["events"][0]["threshold"], 63)
        self.assertEqual(outcome["state"]["enemy"]["hp"], 18)
        self.assertEqual([row["source"] for row in outcome["rng_trace"]], ["paralysis"])

    def test_paralysis_passes_then_damage_uses_later_rng(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "paralysis"
        payload["rng"] = {"mode": "fixed", "values": [63, 255, 255]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "damage")
        self.assertEqual(outcome["events"][0]["damage"], 4)
        self.assertEqual(
            [row["source"] for row in outcome["rng_trace"]],
            ["paralysis", "critical_hit", "damage_variation"],
        )

    def test_paralysis_speed_recalculation_affects_turn_order(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "paralysis"
        payload["state"]["player"]["stats"]["speed"] = 100
        payload["state"]["enemy"]["stats"]["speed"] = 30
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 63, 255, 255]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["turn_order"], ["enemy", "player"])
        self.assertEqual([event["actor"] for event in outcome["events"] if event["type"] == "damage"], ["enemy", "player"])

    def test_electric_speed_passive_affects_turn_order(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 40
        payload["state"]["enemy"]["stats"]["speed"] = 40
        payload["state"]["enemy"]["types"] = ["ELECTRIC", "NORMAL"]
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 255, 255]}
        report = simulate_payload(payload)

        self.assertEqual(report["outcomes"][0]["turn_order"], ["enemy", "player"])

    def test_exhaustive_paralysis_reports_block_probability(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "paralysis"
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["rng"] = {"mode": "exhaustive"}
        report = simulate_payload(payload)

        self.assertEqual(report["outcome_count"], 2)
        blocked = [outcome for outcome in report["outcomes"] if outcome["events"][0]["type"] == "turn_blocked"][0]
        self.assertEqual(blocked["rng_weight"]["reduced"], [63, 256])
        self.assertAlmostEqual(report["summary"]["event_type_rates"]["turn_blocked"]["rate"], 63 / 256)

    def test_sleep_blocks_and_decrements_counter(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "sleep"
        payload["state"]["player"]["sleep_turns"] = 2
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "turn_blocked")
        self.assertEqual(outcome["events"][0]["reason"], "fast_asleep")
        self.assertEqual(outcome["state"]["player"]["status"], "sleep")
        self.assertEqual(outcome["state"]["player"]["sleep_turns"], 1)
        self.assertEqual(outcome["state"]["enemy"]["hp"], 18)

    def test_sleep_wake_allows_move(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "sleep"
        payload["state"]["player"]["sleep_turns"] = 1
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "status_woke_up")
        self.assertEqual(outcome["events"][1]["type"], "damage")
        self.assertEqual(outcome["state"]["player"]["status"], "none")
        self.assertEqual(outcome["state"]["player"]["sleep_turns"], 0)

    def test_freeze_blocks_move_before_damage_rng(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "freeze"
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "turn_blocked")
        self.assertEqual(outcome["events"][0]["reason"], "frozen_solid")
        self.assertEqual(outcome["state"]["player"]["status"], "freeze")
        self.assertEqual(outcome["state"]["enemy"]["hp"], 18)
        self.assertEqual(outcome["rng_trace"], [])

    def test_freeze_thaw_move_bypasses_checkturn_without_clearing_status(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "freeze"
        payload["state"]["player"]["moves"] = [
            {"name": "FLAME_WHEEL", "type": "FIRE", "bp": 60, "accuracy": 255, "effect": "normal_hit"}
        ]
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "status_check")
        self.assertEqual(outcome["events"][0]["reason"], "thaw_move_bypasses_freeze")
        self.assertEqual(outcome["events"][1]["type"], "damage")
        self.assertEqual(outcome["state"]["player"]["status"], "freeze")

    def test_flinch_blocks_once_and_clears_flag(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["volatile"]["flinched"] = True
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "turn_blocked")
        self.assertEqual(outcome["events"][0]["reason"], "flinched")
        self.assertFalse(outcome["state"]["player"]["volatile"]["flinched"])
        self.assertEqual(outcome["state"]["enemy"]["hp"], 18)
        self.assertEqual(outcome["rng_trace"], [])

    def test_freeze_blocks_before_flinch_without_clearing_flinch(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["status"] = "freeze"
        payload["state"]["player"]["volatile"]["flinched"] = True
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["reason"], "frozen_solid")
        self.assertTrue(outcome["state"]["player"]["volatile"]["flinched"])

    def test_accuracy_stage_modifiers_reduce_perfect_accuracy_to_rng_check(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stages"] = {"accuracy": -1}
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 191]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "miss")
        self.assertEqual(outcome["events"][0]["effective_accuracy"], 191)
        self.assertEqual(outcome["events"][0]["accuracy_level"], 6)
        self.assertEqual(outcome["rng_trace"][2]["threshold"], 191)

    def test_always_hit_source_move_ignores_accuracy_stages(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = ["SWIFT"]
        payload["state"]["player"]["stages"] = {"accuracy": -6}
        payload["state"]["enemy"]["stages"] = {"evasion": 6}
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "damage")
        self.assertEqual(outcome["events"][0]["effective_accuracy"], 255)
        self.assertEqual([row["source"] for row in outcome["rng_trace"]], ["critical_hit", "damage_variation"])
        self.assertEqual(outcome["state"]["player"]["moves"][0]["effect"], "always_hit")

    def test_brightpowder_reduces_accuracy_after_stage_math(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["item"] = "BRIGHTPOWDER"
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 235]}
        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["type"], "miss")
        self.assertEqual(event["effective_accuracy"], 235)
        self.assertEqual(event["accuracy_override"], "brightpowder")

    def test_x_accuracy_forces_hit_without_accuracy_rng(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["accuracy"] = 1
        payload["state"]["player"]["volatile"] = {"x_accuracy": True}
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "damage")
        self.assertEqual(outcome["events"][0]["accuracy_override"], "x_accuracy")
        self.assertEqual([row["source"] for row in outcome["rng_trace"]], ["critical_hit", "damage_variation"])

    def test_lock_on_forces_hit_and_clears_target_flag(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["accuracy"] = 1
        payload["state"]["enemy"]["volatile"] = {"lock_on": True}
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "damage")
        self.assertEqual(outcome["events"][0]["accuracy_override"], "lock_on")
        self.assertFalse(outcome["state"]["enemy"]["volatile"]["lock_on"])

    def test_protect_blocks_before_lock_on_and_keeps_lock_on_flag(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["volatile"] = {"protect": True, "lock_on": True}
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        event = outcome["events"][0]
        self.assertEqual(event["type"], "miss")
        self.assertEqual(event["reason"], "target_protected")
        self.assertEqual(event["accuracy_override"], "protect")
        self.assertTrue(outcome["state"]["enemy"]["volatile"]["lock_on"])

    def test_thunder_in_rain_forces_hit_without_accuracy_rng(self) -> None:
        payload = scenario_template()
        payload["state"]["weather"] = "rain"
        payload["state"]["player"]["moves"] = ["THUNDER"]
        payload["state"]["player"]["stages"] = {"accuracy": -6}
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        event = outcome["events"][0]
        self.assertEqual(event["type"], "damage")
        self.assertEqual(event["accuracy_override"], "thunder_rain")
        self.assertEqual([row["source"] for row in outcome["rng_trace"]], ["critical_hit", "damage_variation"])

    def test_flying_target_blocks_tackle_without_accuracy_rng(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["volatile"] = {"flying": True}
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        event = outcome["events"][0]
        self.assertEqual(event["type"], "miss")
        self.assertEqual(event["reason"], "target_flying")
        self.assertEqual(event["accuracy_override"], "semi_invulnerable")
        self.assertEqual([row["source"] for row in outcome["rng_trace"]], ["critical_hit", "damage_variation"])

    def test_gust_can_hit_flying_target(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = ["GUST"]
        payload["state"]["enemy"]["volatile"] = {"flying": True}
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "damage")
        self.assertIsNone(outcome["events"][0]["accuracy_override"])
        self.assertEqual(outcome["events"][0]["damage_effect"], "double_flying_damage")

    def test_earthquake_hits_underground_target(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = ["EARTHQUAKE"]
        payload["state"]["enemy"]["volatile"] = {"underground": True}
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "damage")
        self.assertIsNone(outcome["events"][0]["accuracy_override"])
        self.assertEqual(outcome["events"][0]["damage_effect"], "double_underground_damage")

    def test_lock_on_ground_exception_misses_flying_target_and_clears_lock_on(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = ["EARTHQUAKE"]
        payload["state"]["enemy"]["volatile"] = {"lock_on": True, "flying": True}
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        event = outcome["events"][0]
        self.assertEqual(event["type"], "miss")
        self.assertEqual(event["reason"], "target_flying")
        self.assertTrue(event["target_lock_on_cleared"])
        self.assertFalse(outcome["state"]["enemy"]["volatile"]["lock_on"])

    def test_exhaustive_accuracy_branches_hit_and_miss(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["accuracy"] = 128
        payload["rng"] = {"mode": "exhaustive"}
        report = simulate_payload(payload)

        event_types = {outcome["events"][0]["type"] for outcome in report["outcomes"]}
        self.assertEqual(event_types, {"damage", "miss"})
        self.assertEqual(report["outcome_count"], 156)
        accuracy_traces = [
            trace
            for outcome in report["outcomes"]
            for trace in outcome["rng_trace"]
            if trace["source"] == "accuracy"
        ]
        self.assertTrue(all("raw_count" in trace for trace in accuracy_traces))

    def test_exhaustive_report_declares_distinct_outcome_classes(self) -> None:
        payload = scenario_template()
        payload["rng"] = {"mode": "exhaustive"}
        report = simulate_payload(payload)

        self.assertEqual(report["rng"]["exhaustive_kind"], "distinct_outcome_classes")
        self.assertIn("raw_count", report["outcomes"][0]["rng_trace"][0])
        self.assertEqual(report["outcomes"][0]["rng_weight"]["denominator"], 9984)

    def test_exhaustive_weights_sum_to_probability_mass(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["accuracy"] = 128
        payload["rng"] = {"mode": "exhaustive"}
        report = simulate_payload(payload)

        self.assertAlmostEqual(
            sum(outcome["rng_weight"]["probability"] for outcome in report["outcomes"]),
            1.0,
        )
        miss = next(outcome for outcome in report["outcomes"] if outcome["events"][0]["type"] == "miss")
        self.assertEqual(miss["rng_weight"]["reduced"], [17, 19968])
        self.assertEqual(report["summary"]["weight_basis"], "rng_weight")
        self.assertAlmostEqual(report["summary"]["event_type_rates"]["miss"]["rate"], 0.5)
        self.assertAlmostEqual(report["summary"]["event_type_rates"]["damage"]["rate"], 0.5)

    def test_text_output_includes_exhaustive_branch_probability(self) -> None:
        payload = scenario_template()
        payload["rng"] = {"mode": "exhaustive"}
        text = format_text(simulate_payload(payload))

        self.assertIn("p=", text)
        self.assertIn("event rates:", text)

    def test_status_move_accuracy_remains_out_of_scope(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["state"]["player"]["moves"][0]["accuracy"] = 128
        payload["rng"] = {"mode": "fixed", "values": [128]}
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["type"], "unsupported_noop")
        self.assertEqual(outcome["events"][0]["proof_status"], "out_of_scope")
        self.assertEqual(outcome["rng_trace"], [])

    def test_species_and_move_shorthand_fill_source_tables(self) -> None:
        payload = {
            "rng": {"mode": "fixed", "values": [255, 255]},
            "state": {
                "player": {"species": "CYNDAQUIL", "level": 5, "moves": ["TACKLE"]},
                "enemy": {"species": "PIDGEY", "level": 2, "moves": ["LEER"]},
            },
            "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
        }

        report = simulate_payload(payload)
        player = report["outcomes"][0]["state"]["player"]

        self.assertEqual(player["name"], "CYNDAQUIL")
        self.assertEqual(player["max_hp"], 20)
        self.assertEqual(player["types"], ["FIRE", "FIRE"])
        self.assertEqual(player["moves"][0]["move_id"], 0x21)
        self.assertEqual(player["moves"][0]["accuracy"], 255)

    def test_source_move_shorthand_fills_priority(self) -> None:
        payload = {
            "rng": {"mode": "fixed", "values": [255, 255]},
            "state": {
                "player": {
                    "species": "CYNDAQUIL",
                    "level": 5,
                    "stats": {"speed": 1},
                    "moves": ["QUICK_ATTACK"],
                },
                "enemy": {
                    "species": "PIDGEY",
                    "level": 2,
                    "stats": {"speed": 99},
                    "moves": ["LEER"],
                },
            },
            "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
        }

        report = simulate_payload(payload)

        self.assertEqual(report["outcomes"][0]["turn_order"], ["player", "enemy"])
        self.assertEqual(report["outcomes"][0]["state"]["player"]["moves"][0]["priority"], 2)

    def test_rocky_helmet_recoils_contact_attacker(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["item"] = "ROCKY_HELMET"

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual([event["type"] for event in outcome["events"][:2]], ["damage", "after_hit_recoil"])
        recoil = outcome["events"][1]
        self.assertEqual(recoil["item"], "ROCKY_HELMET")
        self.assertEqual(recoil["damage"], 2)
        self.assertEqual(outcome["state"]["player"]["hp"], 14)

    def test_rocky_helmet_ignores_noncontact_move(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"] = ["EMBER"]
        payload["state"]["enemy"]["item"] = "ROCKY_HELMET"

        report = simulate_payload(payload)

        self.assertNotIn("after_hit_recoil", [event["type"] for event in report["outcomes"][0]["events"]])

    def test_shell_bell_heals_user_after_damage(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 10
        payload["state"]["player"]["item"] = "SHELL_BELL"

        report = simulate_payload(payload)

        heal = next(event for event in report["outcomes"][0]["events"] if event["type"] == "after_hit_heal")
        self.assertEqual(heal["item"], "SHELL_BELL")
        self.assertEqual(heal["healed"], 1)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 11)

    def test_life_orb_recoils_user_after_damage(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["item"] = "LIFE_ORB"

        report = simulate_payload(payload)

        recoil = next(event for event in report["outcomes"][0]["events"] if event["type"] == "after_hit_recoil")
        self.assertEqual(recoil["item"], "LIFE_ORB")
        self.assertEqual(recoil["damage"], 1)
        self.assertEqual(report["outcomes"][0]["state"]["player"]["hp"], 15)

    def test_after_hit_recoil_can_stop_remaining_target_move(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 1
        payload["state"]["player"]["max_hp"] = 6
        payload["state"]["enemy"]["item"] = "ROCKY_HELMET"
        payload["state"]["enemy"]["moves"] = ["TACKLE"]

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["state"]["player"]["hp"], 0)
        self.assertEqual(outcome["events"][-1]["type"], "skip")
        self.assertEqual(outcome["events"][-1]["reason"], "target_already_fainted")

    def test_choice_scarf_modifies_turn_order_speed(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 20
        payload["state"]["enemy"]["stats"]["speed"] = 14
        payload["state"]["enemy"]["item"] = "CHOICE_SCARF"

        report = simulate_payload(payload)

        self.assertEqual(report["outcomes"][0]["turn_order"], ["enemy", "player"])

    def test_quick_claw_fixed_rng_can_override_speed(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 5
        payload["state"]["enemy"]["stats"]["speed"] = 99
        payload["state"]["player"]["item"] = "QUICK_CLAW"
        payload["rng"] = {"mode": "fixed", "values": [0, 255, 255]}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["turn_order"], ["player", "enemy"])
        self.assertEqual(outcome["rng_trace"][0]["source"], "quick_claw")
        self.assertTrue(outcome["rng_trace"][0]["activated"])

    def test_quick_claw_fixed_rng_falls_back_to_speed_on_fail(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 5
        payload["state"]["enemy"]["stats"]["speed"] = 99
        payload["state"]["player"]["item"] = "QUICK_CLAW"
        payload["rng"] = {"mode": "fixed", "values": [60, 255, 255]}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["turn_order"], ["enemy", "player"])
        self.assertEqual(outcome["rng_trace"][0]["source"], "quick_claw")
        self.assertFalse(outcome["rng_trace"][0]["activated"])

    def test_both_quick_claw_default_role_checks_enemy_then_player(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 99
        payload["state"]["enemy"]["stats"]["speed"] = 5
        payload["state"]["player"]["item"] = "QUICK_CLAW"
        payload["state"]["enemy"]["item"] = "QUICK_CLAW"
        payload["rng"] = {"mode": "fixed", "values": [60, 0, 255, 255]}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["turn_order"], ["player", "enemy"])
        self.assertEqual([trace["side"] for trace in outcome["rng_trace"][:2]], ["enemy", "player"])

    def test_exhaustive_quick_claw_branches_activation_and_fallback(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["stats"]["speed"] = 5
        payload["state"]["enemy"]["stats"]["speed"] = 99
        payload["state"]["player"]["item"] = "QUICK_CLAW"
        payload["rng"] = {"mode": "exhaustive"}

        report = simulate_payload(payload)

        orders = {tuple(outcome["turn_order"]) for outcome in report["outcomes"]}
        self.assertEqual(orders, {("player", "enemy"), ("enemy", "player")})
        quick_traces = [
            trace
            for outcome in report["outcomes"]
            for trace in outcome["rng_trace"]
            if trace["source"] == "quick_claw"
        ]
        self.assertEqual(sorted({trace["raw_count"] for trace in quick_traces}), [60, 196])

    def test_selected_switch_runs_before_move_and_updates_bench(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["bench"] = [
            {
                "name": "RATTATA",
                "level": 5,
                "hp": 20,
                "max_hp": 20,
                "types": ["NORMAL"],
                "stats": {"attack": 11, "defense": 9, "speed": 12, "sp_attack": 8, "sp_defense": 8},
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40, "accuracy": 255}],
            }
        ]
        payload["state"]["player"]["item"] = "MUSCLE_BAND"
        payload["state"]["player"]["can_evolve"] = True
        payload["state"]["enemy"]["moves"][0] = {"name": "TACKLE", "type": "NORMAL", "bp": 40, "accuracy": 255}
        payload["actions"] = {"player": {"type": "switch", "bench": 0}, "enemy": {"type": "move", "move": 0}}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["turn_order"], ["player", "enemy"])
        self.assertEqual([event["type"] for event in outcome["events"]], ["switch", "damage"])
        self.assertEqual(outcome["events"][0]["from"], "PIDGEY")
        self.assertEqual(outcome["events"][0]["to"], "RATTATA")
        self.assertEqual(outcome["events"][1]["target"], "player")
        self.assertEqual(outcome["state"]["player"]["name"], "RATTATA")
        self.assertEqual(outcome["state"]["player"]["bench"][0]["name"], "PIDGEY")
        self.assertNotEqual(outcome["state"]["player"]["bench"][0]["item"], 0)
        self.assertTrue(outcome["state"]["player"]["bench"][0]["can_evolve"])
        self.assertLess(outcome["state"]["player"]["hp"], 20)

    def test_double_switch_uses_player_first_source_mirror(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["bench"] = [
            {
                "name": "RATTATA",
                "level": 5,
                "hp": 20,
                "max_hp": 20,
                "types": ["NORMAL"],
                "stats": {"attack": 11, "defense": 9, "speed": 12, "sp_attack": 8, "sp_defense": 8},
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40, "accuracy": 255}],
            }
        ]
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "TOTODILE",
                "level": 5,
                "hp": 21,
                "max_hp": 21,
                "types": ["WATER"],
                "stats": {"attack": 12, "defense": 11, "speed": 10, "sp_attack": 9, "sp_defense": 10},
                "moves": [{"name": "SCRATCH", "type": "NORMAL", "bp": 40, "accuracy": 255}],
            }
        ]
        payload["actions"] = {"player": {"type": "switch", "bench": 0}, "enemy": {"type": "switch", "bench": 0}}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["turn_order"], ["player", "enemy"])
        self.assertEqual([event["type"] for event in outcome["events"]], ["switch", "switch"])
        self.assertEqual(outcome["state"]["player"]["name"], "RATTATA")
        self.assertEqual(outcome["state"]["enemy"]["name"], "TOTODILE")

    def test_switch_to_fainted_bench_is_rejected(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["bench"] = [
            {
                "name": "RATTATA",
                "level": 5,
                "hp": 0,
                "max_hp": 20,
                "types": ["NORMAL"],
                "stats": {"attack": 11, "defense": 9, "speed": 12, "sp_attack": 8, "sp_defense": 8},
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40, "accuracy": 255}],
            }
        ]
        payload["actions"] = {"player": {"type": "switch", "bench": 0}, "enemy": {"type": "move", "move": 0}}

        with self.assertRaisesRegex(SimulationInputError, "fainted Pokemon"):
            simulate_payload(payload)

    def test_fainted_active_with_living_bench_is_rejected_as_forced_switch_prompt(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 0
        payload["state"]["player"]["bench"] = [
            {
                "name": "RATTATA",
                "level": 5,
                "hp": 20,
                "max_hp": 20,
                "types": ["NORMAL"],
                "stats": {"attack": 11, "defense": 9, "speed": 12, "sp_attack": 8, "sp_defense": 8},
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40, "accuracy": 255}],
            }
        ]
        payload["actions"] = {"player": {"type": "switch", "bench": 0}, "enemy": {"type": "move", "move": 0}}

        with self.assertRaisesRegex(SimulationInputError, "forced post-KO switch prompts"):
            simulate_payload(payload)

    def test_forced_switch_phase_can_replace_fainted_active(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["hp"] = 0
        payload["state"]["player"]["bench"] = [
            {
                "name": "RATTATA",
                "level": 5,
                "hp": 20,
                "max_hp": 20,
                "types": ["NORMAL"],
                "stats": {"attack": 11, "defense": 9, "speed": 12, "sp_attack": 8, "sp_defense": 8},
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40, "accuracy": 255}],
            }
        ]
        payload["actions"] = {"player": {"type": "switch", "bench": 0}, "enemy": {"type": "wait"}}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertFalse(outcome["battle_over"])
        self.assertFalse(outcome["requires_forced_switch"])
        self.assertEqual(outcome["turn_order"], ["player"])
        self.assertEqual(outcome["events"][0]["type"], "switch")
        self.assertEqual(outcome["state"]["player"]["name"], "RATTATA")

    def test_wait_outside_forced_switch_phase_is_rejected(self) -> None:
        payload = scenario_template()
        payload["actions"] = {"player": {"type": "wait"}, "enemy": {"type": "move", "move": 0}}

        with self.assertRaisesRegex(SimulationInputError, "wait actions are only valid"):
            simulate_payload(payload)

    def test_ko_with_living_bench_marks_forced_switch_required(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["hp"] = 4
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "TOTODILE",
                "level": 5,
                "hp": 21,
                "max_hp": 21,
                "types": ["WATER"],
                "stats": {"attack": 12, "defense": 11, "speed": 10, "sp_attack": 9, "sp_defense": 10},
                "moves": [{"name": "SCRATCH", "type": "NORMAL", "bp": 40, "accuracy": 255}],
            }
        ]
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertFalse(outcome["battle_over"])
        self.assertTrue(outcome["requires_forced_switch"])
        self.assertEqual(outcome["forced_switch_sides"], ["enemy"])

    def test_forced_switch_phase_can_follow_ko_in_turn_sequence(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["hp"] = 4
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "TOTODILE",
                "level": 5,
                "hp": 21,
                "max_hp": 21,
                "types": ["WATER"],
                "stats": {"attack": 12, "defense": 11, "speed": 9, "sp_attack": 9, "sp_defense": 10},
                "moves": [{"name": "SCRATCH", "type": "NORMAL", "bp": 40, "accuracy": 255}],
            }
        ]
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        payload["turns"] = [
            {"actions": {"player": {"move": 0}, "enemy": {"move": 0}}},
            {"actions": {"player": {"type": "wait"}, "enemy": {"type": "switch", "bench": 0}}},
        ]
        payload.pop("actions")

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["state"]["enemy"]["name"], "TOTODILE")
        self.assertEqual(outcome["state"]["enemy"]["bench"][0]["name"], "CYNDAQUIL")
        self.assertFalse(outcome["requires_forced_switch"])
        self.assertEqual([event["type"] for event in outcome["events"]], ["damage", "skip", "switch"])

    def test_extra_turn_after_ko_with_living_bench_is_rejected(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["hp"] = 4
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "TOTODILE",
                "level": 5,
                "hp": 21,
                "max_hp": 21,
                "types": ["WATER"],
                "stats": {"attack": 12, "defense": 11, "speed": 10, "sp_attack": 9, "sp_defense": 10},
                "moves": [{"name": "SCRATCH", "type": "NORMAL", "bp": 40, "accuracy": 255}],
            }
        ]
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        payload["turns"] = [
            {"actions": {"player": {"move": 0}, "enemy": {"move": 0}}},
            {"actions": {"player": {"move": 0}, "enemy": {"move": 0}}},
        ]
        payload.pop("actions")

        with self.assertRaisesRegex(SimulationInputError, "forced post-KO switch prompts"):
            simulate_payload(payload)

    def test_json_state_can_round_trip_consumed_item_and_can_evolve_fields(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["item"] = "MUSCLE_BAND"
        payload["state"]["player"]["can_evolve"] = True
        first = simulate_payload(payload)
        state = first["outcomes"][0]["state"]

        replay_payload = {
            "rng": {"mode": "fixed", "values": [255, 255]},
            "state": state,
            "actions": {"player": {"move": 0}, "enemy": {"move": 0}},
        }
        replay = simulate_payload(replay_payload)

        self.assertTrue(state["player"]["can_evolve"])
        self.assertNotEqual(state["player"]["item"], 0)
        self.assertEqual(replay["outcome_count"], 1)

    def test_boss_ai_selector_fixed_rng_can_choose_second_slot(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["moves"] = [
            {"name": "TACKLE", "move_id": 33, "type": "NORMAL", "bp": 40, "accuracy": 255},
            {"name": "EMBER", "move_id": 52, "type": "FIRE", "bp": 40, "accuracy": 255},
        ]
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 255, 255, 255]}
        payload["actions"] = {
            "player": {"type": "move", "move": 0},
            "enemy": {
                "type": "boss_ai_selector",
                "scenario_id": "unit_selector",
                "tier": "late",
                "move_ids": [33, 52, 0, 0],
                "scores": [20, 20, 80, 80],
                "move_names": ["TACKLE", "EMBER", "", ""],
            },
        }

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        selector_event = outcome["events"][0]
        self.assertEqual(selector_event["type"], "boss_ai_select_move")
        self.assertEqual(selector_event["selected_slot_index"], 1)
        self.assertEqual(selector_event["move"], "EMBER")
        self.assertEqual(outcome["rng_trace"][0]["source"], "boss_ai_selector")
        enemy_damage = [event for event in outcome["events"] if event.get("actor") == "enemy" and event["type"] == "damage"][0]
        self.assertEqual(enemy_damage["move"], "EMBER")

    def test_boss_ai_selector_exhaustive_branches_best_and_second_slots(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["moves"] = [
            {"name": "TACKLE", "move_id": 33, "type": "NORMAL", "bp": 0, "accuracy": 255},
            {"name": "EMBER", "move_id": 52, "type": "FIRE", "bp": 0, "accuracy": 255},
            {"name": "WATER_GUN", "move_id": 55, "type": "WATER", "bp": 0, "accuracy": 255},
        ]
        payload["rng"] = {"mode": "exhaustive"}
        payload["actions"] = {
            "player": {"type": "move", "move": 0},
            "enemy": {
                "type": "boss_ai_selector",
                "scenario_id": "unit_selector_exhaustive",
                "tier": "late",
                "move_ids": [33, 52, 55, 0],
                "scores": [20, 20, 20, 80],
            },
        }

        report = simulate_payload(payload)

        self.assertEqual(report["outcome_count"], 2)
        selected = {outcome["events"][0]["selected_slot_index"] for outcome in report["outcomes"]}
        self.assertEqual(selected, {0, 1})
        raw_counts = sorted(
            trace["raw_count"]
            for outcome in report["outcomes"]
            for trace in outcome["rng_trace"]
            if trace["source"] == "boss_ai_selector"
        )
        self.assertEqual(raw_counts, [70, 186])

    def test_boss_ai_selector_rejects_move_id_mismatch(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["moves"][0]["move_id"] = 33
        payload["actions"] = {
            "player": {"type": "move", "move": 0},
            "enemy": {
                "type": "boss_ai_selector",
                "scenario_id": "unit_selector_mismatch",
                "tier": "late",
                "move_ids": [52, 0, 0, 0],
                "scores": [20, 80, 80, 80],
            },
        }

        with self.assertRaisesRegex(SimulationInputError, "does not match"):
            simulate_payload(payload)

    def test_boss_ai_switch_policy_fixed_rng_can_commit_switch(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "TOTODILE",
                "level": 5,
                "hp": 21,
                "max_hp": 21,
                "types": ["WATER"],
                "stats": {"attack": 12, "defense": 11, "speed": 9, "sp_attack": 9, "sp_defense": 10},
                "moves": [{"name": "SCRATCH", "type": "NORMAL", "bp": 40, "accuracy": 255}],
            }
        ]
        payload["rng"] = {"mode": "fixed", "values": [229]}
        payload["actions"] = {
            "player": {"type": "move", "move": 0},
            "enemy": {
                "type": "boss_ai_switch_policy",
                "scenario_id": "unit_switch_policy",
                "candidate_bench": 0,
                "confidence": 80,
                "tier": "late",
                "trainer_class": "JASMINE",
                "threshold": 60,
                "fallback_move": 0,
            },
        }

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        policy_event = outcome["events"][0]
        self.assertEqual(policy_event["type"], "boss_ai_switch_policy")
        self.assertEqual(policy_event["decision"], "switch")
        self.assertEqual(policy_event["roll_threshold"], 230)
        self.assertEqual(outcome["rng_trace"][0]["source"], "boss_ai_switch_roll")
        self.assertEqual(outcome["events"][1]["type"], "switch")
        self.assertEqual(outcome["state"]["enemy"]["name"], "TOTODILE")

    def test_boss_ai_switch_policy_exhaustive_reports_switch_frequency(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "TOTODILE",
                "level": 5,
                "hp": 21,
                "max_hp": 21,
                "types": ["WATER"],
                "stats": {"attack": 12, "defense": 11, "speed": 9, "sp_attack": 9, "sp_defense": 10},
                "moves": [{"name": "SCRATCH", "type": "NORMAL", "bp": 40, "accuracy": 255}],
            }
        ]
        payload["rng"] = {"mode": "exhaustive"}
        payload["actions"] = {
            "player": {"type": "move", "move": 0},
            "enemy": {
                "type": "boss_ai_switch_policy",
                "candidate_bench": 0,
                "confidence": 80,
                "tier": "late",
                "fallback_move": 0,
            },
        }

        report = simulate_payload(payload)

        self.assertEqual(report["outcome_count"], 2)
        decisions = {outcome["events"][0]["decision"] for outcome in report["outcomes"]}
        self.assertEqual(decisions, {"switch", "stay"})
        raw_counts = sorted(
            trace["raw_count"]
            for outcome in report["outcomes"]
            for trace in outcome["rng_trace"]
            if trace["source"] == "boss_ai_switch_roll"
        )
        self.assertEqual(raw_counts, [26, 230])
        rates = report["summary"]["boss_ai_switch_policy_rates"]
        self.assertAlmostEqual(rates["enemy:switch:TOTODILE"]["rate"], 230 / 256)
        self.assertAlmostEqual(rates["enemy:stay:TOTODILE"]["rate"], 26 / 256)

    def test_boss_ai_switch_policy_anti_loop_can_force_stay_without_rng(self) -> None:
        payload = scenario_template()
        payload["state"]["player"]["moves"][0]["bp"] = 0
        payload["state"]["enemy"]["bench"] = [
            {
                "name": "TOTODILE",
                "level": 5,
                "hp": 21,
                "max_hp": 21,
                "types": ["WATER"],
                "stats": {"attack": 12, "defense": 11, "speed": 9, "sp_attack": 9, "sp_defense": 10},
                "moves": [{"name": "SCRATCH", "type": "NORMAL", "bp": 40, "accuracy": 255}],
            }
        ]
        payload["rng"] = {"mode": "fixed", "values": []}
        payload["actions"] = {
            "player": {"type": "move", "move": 0},
            "enemy": {
                "type": "boss_ai_switch_policy",
                "candidate_bench": 0,
                "confidence": 80,
                "tier": "late",
                "anti_loop": True,
                "fallback_move": 0,
            },
        }

        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertEqual(outcome["events"][0]["decision"], "stay")
        self.assertEqual(outcome["events"][0]["threshold"], 110)
        self.assertEqual(outcome["events"][0]["reason"], "confidence_below_threshold")
        self.assertEqual(outcome["rng_trace"], [])
        self.assertEqual(outcome["state"]["enemy"]["name"], "CYNDAQUIL")

    def test_rng_config_rejects_ignored_fields(self) -> None:
        payload = scenario_template()
        payload["rng"] = {"mode": "sample", "values": [1], "seed": 1}
        with self.assertRaisesRegex(SimulationInputError, "rng.values"):
            simulate_payload(payload)

        payload = scenario_template()
        payload["rng"] = {"mode": "fixed", "values": [255], "seed": 1}
        with self.assertRaisesRegex(SimulationInputError, "rng.seed"):
            simulate_payload(payload)

        payload = scenario_template()
        payload["rng"] = {"mode": "exhaustive", "samples": 2}
        with self.assertRaisesRegex(SimulationInputError, "rng.samples"):
            simulate_payload(payload)

    def test_turn_sequence_advances_state_with_continuous_rng(self) -> None:
        payload = scenario_template()
        payload["rng"] = {"mode": "fixed", "values": [255, 255, 255, 255]}
        payload["turns"] = [
            {"actions": {"player": {"move": 0}, "enemy": {"move": 0}}},
            {"actions": {"player": {"move": 0}, "enemy": {"move": 0}}},
        ]
        payload.pop("actions")
        report = simulate_payload(payload)

        self.assertEqual(report["turn_count"], 2)
        self.assertEqual(report["outcome_count"], 1)
        outcome = report["outcomes"][0]
        damage_events = [event for event in outcome["events"] if event["type"] == "damage"]
        self.assertEqual([event["turn"] for event in damage_events], [1, 2])
        self.assertEqual(outcome["state"]["turn"], 3)
        self.assertEqual(outcome["state"]["enemy"]["hp"], 10)
        self.assertEqual(len(outcome["rng_trace"]), 4)

    def test_turn_sequence_stops_after_faint(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["hp"] = 4
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        payload["turns"] = [
            {"actions": {"player": {"move": 0}, "enemy": {"move": 0}}},
            {"actions": {"player": {"move": 0}, "enemy": {"move": 0}}},
        ]
        payload.pop("actions")
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        self.assertTrue(outcome["battle_over"])
        self.assertEqual(outcome["battle_over_reason"], "enemy_fainted")
        self.assertEqual(outcome["events"][-1]["type"], "battle_over")
        self.assertEqual(outcome["events"][-1]["turn"], 2)

    def test_turn_sequence_appends_single_battle_over_for_extra_turns(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["hp"] = 4
        payload["rng"] = {"mode": "fixed", "values": [255, 255]}
        payload["turns"] = [
            {"actions": {"player": {"move": 0}, "enemy": {"move": 0}}},
            {"actions": {"player": {"move": 0}, "enemy": {"move": 0}}},
            {"actions": {"player": {"move": 0}, "enemy": {"move": 0}}},
        ]
        payload.pop("actions")
        report = simulate_payload(payload)

        outcome = report["outcomes"][0]
        battle_over_events = [event for event in outcome["events"] if event["type"] == "battle_over"]
        self.assertEqual(len(battle_over_events), 1)
        self.assertEqual(len(outcome["turns"]), 1)

    def test_exhaustive_speed_tie_branches_turn_order(self) -> None:
        payload = scenario_template()
        payload["rng"] = {"mode": "exhaustive"}
        payload["state"]["enemy"]["stats"]["speed"] = payload["state"]["player"]["stats"]["speed"]
        # Both moves are status/no-op so this isolates the speed-tie branch count.
        payload["state"]["player"]["moves"][0]["bp"] = 0
        report = simulate_payload(payload)

        orders = {tuple(outcome["turn_order"]) for outcome in report["outcomes"]}
        self.assertEqual(orders, {("player", "enemy"), ("enemy", "player")})
        self.assertEqual(report["outcome_count"], 2)

    def test_report_exposes_proof_boundary(self) -> None:
        report = simulate_payload(scenario_template())

        byte_proven_ids = {row["id"] for row in report["coverage"]["byte_proven"]}
        self.assertIn("damage_core_pre_variation", byte_proven_ids)
        self.assertIn("damage_variation", byte_proven_ids)
        self.assertIn("critical_hit_chance", byte_proven_ids)
        self.assertIn("turn_order_priority_speed_default_role", byte_proven_ids)
        self.assertIn("turn_order_quick_claw_choice_scarf_default_role", byte_proven_ids)
        self.assertIn("supported_damage_move_accuracy_modifiers_overrides_semivulnerable_weather_and_sure_hit", byte_proven_ids)
        self.assertIn("after_hit_rocky_shell_life_orb", byte_proven_ids)
        self.assertIn("post_variation_double_flying_underground_damage", byte_proven_ids)
        self.assertIn("residual_status_hp_mutation", byte_proven_ids)
        self.assertIn("leftovers_hp_mutation", byte_proven_ids)
        self.assertIn("paralysis_checkturn_text_path", byte_proven_ids)
        self.assertIn("status_speed_recalculation", byte_proven_ids)
        self.assertIn("sleep_checkturn_text_path", byte_proven_ids)
        self.assertIn("freeze_checkturn_text_path", byte_proven_ids)
        self.assertIn("flinch_checkturn_text_path", byte_proven_ids)
        mirrored_ids = {row["id"] for row in report["coverage"]["source_mirrored_pending_differential"]}
        self.assertNotIn("damage_variation", mirrored_ids)
        self.assertNotIn("turn_order_priority_speed", mirrored_ids)
        self.assertIn("selected_switch_actions", mirrored_ids)
        self.assertIn("explicit_forced_switch_phases", mirrored_ids)
        self.assertIn("boss_ai_selector_from_post_score_bytes", mirrored_ids)
        self.assertIn("boss_ai_switch_policy_from_final_confidence", mirrored_ids)
        self.assertIn("residual_status_turn_timing", mirrored_ids)
        self.assertIn("leftovers_between_turn_timing", mirrored_ids)
        self.assertIn("paralysis_turn_blocking_timing", mirrored_ids)
        self.assertIn("turn_order_status_adjusted_speed_inputs", mirrored_ids)
        self.assertIn("sleep_turn_counter_timing", mirrored_ids)
        self.assertIn("freeze_turn_blocking_timing", mirrored_ids)
        self.assertIn("flinch_turn_blocking_timing", mirrored_ids)
        self.assertIn("Boss AI score-model generation from live battle state and Boss AI switch candidate/confidence generation", report["coverage"]["out_of_scope"])

    def test_python_damage_variation_result_tracks_consumed_rng(self) -> None:
        result = python_damage_variation_result(4, [0, 255])

        self.assertEqual(result["damage"], 4)
        self.assertEqual(result["rng_count"], 2)
        self.assertEqual([step["accepted"] for step in result["rng_trace"]], [False, True])

    def test_python_accuracy_result_matches_rom_minimum_accuracy(self) -> None:
        hit = python_accuracy_result(0, [0])
        miss = python_accuracy_result(0, [1])

        self.assertTrue(hit["hit"])
        self.assertFalse(miss["hit"])
        self.assertEqual(hit["rng_count"], 1)

    def test_python_accuracy_result_applies_stage_modifiers(self) -> None:
        miss = python_accuracy_result(255, [191], accuracy_level=6)

        self.assertFalse(miss["hit"])
        self.assertEqual(miss["rng_trace"][0]["threshold"], 191)

    def test_python_critical_result_matches_threshold_boundaries(self) -> None:
        base_crit = python_critical_result(
            next(row for row in CRITICAL_DIFFERENTIAL_CASES if row.name == "base_raw_zero_crits")
        )
        slash_miss = python_critical_result(
            next(row for row in CRITICAL_DIFFERENTIAL_CASES if row.name == "slash_threshold_64_misses")
        )
        zero_power = python_critical_result(
            next(row for row in CRITICAL_DIFFERENTIAL_CASES if row.name == "zero_power_consumes_no_rng")
        )

        self.assertTrue(base_crit["critical"])
        self.assertEqual(base_crit["rng_count"], 1)
        self.assertFalse(slash_miss["critical"])
        self.assertEqual(slash_miss["rng_trace"][0]["threshold"], 64)
        self.assertFalse(zero_power["critical"])
        self.assertEqual(zero_power["rng_count"], 0)

    def test_python_turn_order_result_tracks_consumed_rng(self) -> None:
        case = next(row for row in TURN_ORDER_DIFFERENTIAL_CASES if row.name == "default_role_speed_tie_enemy_rng")
        result = python_turn_order_result(case)

        self.assertEqual(result["order"], ["enemy", "player"])
        self.assertEqual(result["rng_count"], 1)

    def test_python_residual_status_result_matches_toxic_counter(self) -> None:
        case = ResidualStatusDifferentialCase("toxic", "player", "toxic", 40, 64, toxic_count=2)
        result = python_residual_status_result(case)

        self.assertEqual(result["damage"], 12)
        self.assertEqual(result["hp"], 28)
        self.assertEqual(result["toxic_count"], 3)

    def test_python_leftovers_result_clamps_at_max_hp(self) -> None:
        case = LeftoversDifferentialCase("leftovers", "player", 63, 64)
        result = python_leftovers_result(case)

        self.assertEqual(result["healed"], 1)
        self.assertEqual(result["hp"], 64)

    def test_python_paralysis_turn_result_matches_fighting_thresholds(self) -> None:
        half = python_paralysis_turn_result(
            ParalysisTurnDifferentialCase("half", "player", 50, ("FIGHTING", "NORMAL"))
        )
        full = python_paralysis_turn_result(
            ParalysisTurnDifferentialCase("full", "player", 38, ("FIGHTING", "FIGHTING"))
        )

        self.assertTrue(half["blocked"])
        self.assertEqual(half["threshold"], 51)
        self.assertFalse(full["blocked"])
        self.assertEqual(full["threshold"], 38)

    def test_python_sleep_turn_result_decrements_and_wakes(self) -> None:
        asleep = python_sleep_turn_result(SleepTurnDifferentialCase("asleep", "player", 2))
        awake = python_sleep_turn_result(SleepTurnDifferentialCase("wake", "player", 1))

        self.assertTrue(asleep["blocked"])
        self.assertEqual(asleep["sleep_turns_after"], 1)
        self.assertFalse(awake["blocked"])
        self.assertEqual(awake["status_after"], "none")

    def test_python_freeze_turn_result_blocks_and_bypasses_thaw_moves(self) -> None:
        frozen = python_freeze_turn_result(FreezeTurnDifferentialCase("frozen", "player", 0x21, "TACKLE"))
        thaw_move = python_freeze_turn_result(
            FreezeTurnDifferentialCase("flame_wheel", "player", 0xAC, "FLAME_WHEEL")
        )

        self.assertTrue(frozen["blocked"])
        self.assertEqual(frozen["reason"], "frozen_solid")
        self.assertFalse(thaw_move["blocked"])
        self.assertEqual(thaw_move["reason"], "thaw_move_bypasses_freeze")
        self.assertEqual(thaw_move["status_after"], "freeze")

    def test_python_flinch_turn_result_clears_flag(self) -> None:
        result = python_flinch_turn_result(FlinchTurnDifferentialCase("flinched", "player"))

        self.assertTrue(result["blocked"])
        self.assertFalse(result["flinched_after"])

    def test_python_status_speed_result_matches_type_passive_fractions(self) -> None:
        electric = python_status_speed_result(
            StatusSpeedDifferentialCase("electric", "player", 40, "none", ("ELECTRIC", "ELECTRIC"))
        )
        paralyzed = python_status_speed_result(
            StatusSpeedDifferentialCase("paralyzed", "player", 100, "paralysis", ("FIGHTING", "NORMAL"))
        )

        self.assertEqual(electric["speed"], 42)
        self.assertEqual(paralyzed["speed"], 37)

    def test_cli_json_out(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenario = Path(tmp) / "scenario.json"
            out = Path(tmp) / "report.json"
            scenario.write_text(json.dumps(scenario_template()), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                code = main(["--scenario", str(scenario), "--json-out", str(out)])

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "headless_battle_turn_simulation")
            self.assertEqual(data["outcome_count"], 1)


if __name__ == "__main__":
    unittest.main()
