from __future__ import annotations

import unittest

from tools.boss_ai_debugger.generators import generate_scenarios
from tools.boss_ai_debugger.rom_switch_materialize import (
    scenario_expects_switch,
    switch_materialization_patches,
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


if __name__ == "__main__":
    unittest.main()
