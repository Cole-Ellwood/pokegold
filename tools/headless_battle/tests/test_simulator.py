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
            "delegated_pre_variation_damage_plus_source_mirrored_variation",
        )
        self.assertLess(outcome["state"]["enemy"]["hp"], 18)

    def test_priority_changes_turn_order(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["moves"][0]["priority"] = 2

        report = simulate_payload(payload)

        self.assertEqual(report["outcomes"][0]["turn_order"], ["enemy", "player"])

    def test_equal_speed_tie_is_rejected_until_rng_order_is_proven(self) -> None:
        payload = scenario_template()
        payload["state"]["enemy"]["stats"]["speed"] = payload["state"]["player"]["stats"]["speed"]

        with self.assertRaisesRegex(SimulationInputError, "speed-tie logic"):
            simulate_payload(payload)

    def test_fixed_rng_values_drive_damage_variation(self) -> None:
        payload = scenario_template()
        max_roll = simulate_payload(payload)["outcomes"][0]["events"][0]
        payload["rng"] = {"mode": "fixed", "values": [179, 255]}

        report = simulate_payload(payload)

        event = report["outcomes"][0]["events"][0]
        self.assertEqual(event["damage_variation"]["raw_values"], [179])
        self.assertEqual(event["damage_variation"]["multiplier"], 217)
        self.assertLessEqual(event["damage"], max_roll["damage"])

    def test_fixed_rng_reports_exhausted_values(self) -> None:
        payload = scenario_template()
        payload["rng"] = {"mode": "fixed", "values": [255]}

        with self.assertRaisesRegex(SimulationInputError, "rng.values exhausted"):
            simulate_payload(payload)

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
        payload["state"]["enemy"]["moves"][0]["bp"] = 0

        report = simulate_payload(payload)

        multipliers = {
            outcome["events"][0]["damage_variation"]["multiplier"]
            for outcome in report["outcomes"]
        }
        self.assertEqual(report["outcome_count"], 39)
        self.assertEqual(min(multipliers), 217)
        self.assertEqual(max(multipliers), 255)

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
        self.assertIn("selected_turn_order_priority_speed", mirrored)
        self.assertIn("boss_ai_selector_from_post_score_bytes", mirrored)
        self.assertIn("RNG-consuming mechanics outside damage variation", "\n".join(report["coverage"]["out_of_scope"]))

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
