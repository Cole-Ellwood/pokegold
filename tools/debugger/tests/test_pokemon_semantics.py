from __future__ import annotations

import unittest
from tools.damage_debugger import state as damage_state
from tools.debugger.pokemon_semantics import (
    build_grass_regrowth_report,
    build_learnset_inspection_report,
)


class PokemonSemanticsTests(unittest.TestCase):
    def test_species_id_map_ignores_unown_form_constants(self) -> None:
        by_id = damage_state.species_name_by_id()

        self.assertEqual(by_id[1], "BULBASAUR")
        self.assertEqual(by_id[16], "PIDGEY")
        self.assertEqual(by_id[201], "UNOWN")

    def test_learnset_and_grass_semantic_reports_answer_live_questions(self) -> None:
        learnset = build_learnset_inspection_report(species="GASTLY", level=14)
        regrowth = build_grass_regrowth_report(max_total_hp=300)

        self.assertTrue(learnset["valid"])
        self.assertEqual(learnset["species"], "GASTLY")
        self.assertIn("LICK", learnset["current_moves"])
        self.assertTrue(learnset["current_moves"])
        self.assertTrue(regrowth["valid"])
        self.assertEqual(regrowth["cutoffs"]["full_grass"][0], {"min_hp": 1, "max_hp": 47, "heals": 1})
        self.assertEqual(regrowth["cutoffs"]["half_grass"][0], {"min_hp": 1, "max_hp": 95, "heals": 1})
