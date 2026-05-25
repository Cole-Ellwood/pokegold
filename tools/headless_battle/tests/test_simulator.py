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

    def test_report_exposes_proof_boundary(self) -> None:
        report = simulate_payload(scenario_template())

        byte_proven = {row["id"] for row in report["coverage"]["byte_proven"]}
        mirrored = {row["id"] for row in report["coverage"]["source_mirrored_pending_differential"]}
        self.assertIn("damage_core_pre_variation", byte_proven)
        self.assertIn("damage_variation_rng_branching", mirrored)
        self.assertIn("basic_move_accuracy_rng", mirrored)
        self.assertIn("basic_critical_hit_rng", mirrored)
        self.assertIn("basic_status_residual", mirrored)
        self.assertIn("selected_turn_order_priority_speed", mirrored)
        self.assertIn("boss_ai_selector_from_post_score_bytes", mirrored)
        self.assertIn("RNG-consuming mechanics outside speed ties/critical hits/accuracy/damage variation", "\n".join(report["coverage"]["out_of_scope"]))

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
