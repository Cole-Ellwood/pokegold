from __future__ import annotations

import unittest
from tools.debugger.repro_recipes import build_repro_recipe_report


class ReproRecipeTests(unittest.TestCase):
    def test_repro_recipe_exposes_first_wild_route29_capture_path(self) -> None:
        report = build_repro_recipe_report(ids=("first-wild-route29",))
        recipe = report["recipes"][0]
        commands = "\n".join(recipe["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(recipe["id"], "first-wild-route29")
        self.assertIn("--reset-sentinel", commands)
        self.assertIn("wram-bank-hazards", commands)
        self.assertIn("route29-before-grass.state", commands)

    def test_repro_recipe_exposes_trainer_evolution_resume_path(self) -> None:
        report = build_repro_recipe_report(ids=("trainer-battle-evolution-resume",))
        recipe = report["recipes"][0]
        commands = "\n".join(recipe["commands"])

        self.assertTrue(report["valid"])
        self.assertEqual(recipe["bug_class"], "post_battle_script_resume")
        self.assertIn("state-inspect", commands)
        self.assertIn("script-resume-gate", commands)
        self.assertIn("wSeenTrainerBank", commands)
        self.assertIn("EvolveAfterBattle", commands)
