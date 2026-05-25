from __future__ import annotations

import unittest

from tools.boss_ai_debugger.generators import generate_scenarios
from tools.boss_ai_debugger.rom_switch_materialize import (
    scenario_expects_switch,
    source_base_switch_threshold,
    switch_materialization_patches,
    switch_roll_frequency,
    switch_verdict_from_report,
)


class RomSwitchMaterializeTests(unittest.TestCase):
    def test_switch_sack_expectation_detects_switch_best_action(self) -> None:
        scenario = generate_scenarios(family="switch_sack", count=1, seed=1)[0]

        self.assertTrue(scenario_expects_switch(scenario))

    def test_switch_materialization_uses_public_state_patches(self) -> None:
        scenario = generate_scenarios(family="switch_sack", count=1, seed=1)[0]
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in switch_materialization_patches(scenario)
        }

        self.assertEqual(patches[("wOTPartyCount", 0)], 2)
        self.assertEqual(patches[("wPlayerUsedMoves", 0)], 0x59)
        self.assertEqual(patches[("wEnemySwitchMonParam", 0)], 0)

    def test_switch_verdict_flags_unwanted_switch(self) -> None:
        scenario = generate_scenarios(family="switch_sack", count=3, seed=2)[2]

        verdict = switch_verdict_from_report(
            scenario,
            {
                "proposed_switch": True,
                "switch_confidence": 90,
                "switch_param": 0x21,
            },
        )

        self.assertFalse(verdict["expected_switch"])
        self.assertEqual(verdict["rom_policy"]["verdict"], "mismatch")

    def test_source_base_switch_threshold_uses_shared_jasmine_class_mod(self) -> None:
        scenario = {"tier": "mid"}

        threshold = source_base_switch_threshold(scenario, base_route="shared_switch_loop")

        self.assertEqual(threshold["tier"], "mid")
        self.assertEqual(threshold["trainer_class"], "JASMINE")
        self.assertEqual(threshold["class_threshold_mod"], 4)
        self.assertEqual(threshold["threshold"], 74)

    def test_switch_roll_frequency_uses_explicit_threshold_for_exact_rate(self) -> None:
        scenario = generate_scenarios(family="switch_sack", count=1, seed=1)[0]

        roll = switch_roll_frequency(
            scenario,
            {"switch_confidence": 90},
            switch_threshold=70,
        )

        self.assertTrue(roll["threshold_exact"])
        self.assertTrue(roll["probability_exact"])
        self.assertEqual(roll["assumed_effective_threshold"], 70)
        self.assertEqual(roll["switch_chance_threshold"], 230)
        self.assertEqual(roll["switch_probability"], 230 / 256)

    def test_switch_roll_frequency_reports_untraced_bias_range(self) -> None:
        scenario = {"tier": "mid"}

        roll = switch_roll_frequency(
            scenario,
            {"switch_confidence": 90},
            base_route="shared_switch_loop",
        )

        self.assertFalse(roll["threshold_exact"])
        self.assertFalse(roll["probability_exact"])
        self.assertEqual(roll["base_threshold"], 74)
        self.assertEqual(roll["possible_effective_thresholds"], [74, 82, 84, 92])
        self.assertEqual(
            [item["switch_chance_threshold"] for item in roll["possible_switch_probabilities"]],
            [192, 141, 141, 0],
        )


if __name__ == "__main__":
    unittest.main()
