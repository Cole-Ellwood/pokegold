from __future__ import annotations

import unittest

from tools.boss_ai_debugger.generators import generate_scenarios
from tools.boss_ai_debugger.rom_score_materialize import (
    MOVES,
    action_id_for_slot,
    materialization_for_scenario,
    move_ids_for_scenario,
    parse_spikes_layers,
    scenario_condition_tags,
)


class RomScoreMaterializeTests(unittest.TestCase):
    def test_move_ids_map_generated_spikes_case_to_real_moves(self) -> None:
        scenario = generate_scenarios(family="spikes_spin", count=1, seed=1)[0]

        self.assertEqual(
            move_ids_for_scenario(scenario, move_name_to_id={}),
            [0xBF, 0xBC, 0x39, 0x99],
        )

    def test_materialization_patches_public_spikes_and_rapid_spin_state(self) -> None:
        scenario = generate_scenarios(family="spikes_spin", count=1, seed=1)[0]
        scenario["expectation"]["condition_tags"] = [
            "spikes_layers_2",
            "active_revealed_rapid_spin",
            "bench_revealed_rapid_spin",
        ]

        materialization = materialization_for_scenario(
            scenario,
            move_name_to_id={},
        )
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in materialization.patches
        }

        self.assertEqual(patches[("wPlayerScreens", 0)], 2)
        self.assertEqual(patches[("wPlayerUsedMoves", 0)], MOVES["RAPID_SPIN"])
        self.assertEqual(patches[("wBossAISeenPlayerSpeciesCount", 0)], 2)
        self.assertEqual(patches[("wBossAISpeciesUsedMoves", 4)], MOVES["RAPID_SPIN"])

    def test_layer_parser_uses_condition_tags(self) -> None:
        tags = {"spikes_layers_3", "active_revealed_rapid_spin"}

        self.assertEqual(parse_spikes_layers(tags), 3)

    def test_scenario_condition_tags_reads_expectation(self) -> None:
        scenario = {"expectation": {"condition_tags": ["a", "b"]}}

        self.assertEqual(scenario_condition_tags(scenario), {"a", "b"})

    def test_action_id_for_slot_maps_rom_slot_index(self) -> None:
        scenario = {"moves": [{"id": "first"}, {"id": "second"}]}

        self.assertEqual(action_id_for_slot(scenario, 1), "second")
        self.assertIsNone(action_id_for_slot(scenario, 4))


if __name__ == "__main__":
    unittest.main()
