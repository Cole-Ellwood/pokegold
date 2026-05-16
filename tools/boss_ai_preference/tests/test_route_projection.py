from __future__ import annotations

import unittest

from tools.boss_ai_preference.route_projection import (
    STRUCTURAL_CONTINUATION_BONUS,
    STRUCTURAL_INVALID_PENALTY,
    is_self_ko_action,
    is_switch_action,
    project_plan_route,
)


def _fixture(actions: list[dict]) -> dict:
    return {"id": "synthetic_fixture", "actions": actions}


def _plan(plan_id: str, steps: list[dict]) -> dict:
    return {"id": plan_id, "steps": steps}


class RoutePredicatesTests(unittest.TestCase):
    def test_self_ko_by_action_id(self) -> None:
        self.assertTrue(is_self_ko_action({"id": "move_explosion"}))
        self.assertTrue(is_self_ko_action({"id": "move_self_destruct"}))
        self.assertTrue(is_self_ko_action({"id": "move_memento"}))

    def test_self_ko_by_action_name(self) -> None:
        self.assertTrue(is_self_ko_action({"id": "move_x", "name": "Explosion"}))
        self.assertTrue(is_self_ko_action({"id": "move_y", "name": "Healing Wish"}))

    def test_self_ko_negative(self) -> None:
        self.assertFalse(is_self_ko_action({"id": "move_earthquake"}))
        self.assertFalse(is_self_ko_action({"id": "move_thunder", "name": "Thunder"}))

    def test_switch_by_kind(self) -> None:
        self.assertTrue(is_switch_action({"id": "switch_kingdra", "kind": "switch"}))

    def test_switch_by_id_prefix(self) -> None:
        self.assertTrue(is_switch_action({"id": "switch_omastar"}))
        self.assertTrue(is_switch_action({"id": "swap_anything"}))

    def test_switch_negative(self) -> None:
        self.assertFalse(is_switch_action({"id": "move_explosion"}))


class RouteProjectionTests(unittest.TestCase):
    def test_two_explosions_same_actor_flagged_invalid(self) -> None:
        fixture = _fixture(
            [
                {"id": "move_explosion", "kind": "move", "name": "Explosion"},
            ]
        )
        plan = _plan(
            "plan_attack_now",
            [
                {"actor": None, "action_id": "move_explosion"},
                {"actor": None, "action_id": "move_explosion"},
            ],
        )
        projection = project_plan_route(fixture, plan)
        self.assertFalse(projection["structural_valid"])
        self.assertEqual(len(projection["invalid_post_steps"]), 1)
        self.assertEqual(
            projection["route_value_delta"], -STRUCTURAL_INVALID_PENALTY
        )
        self.assertIn("self_ko_trade", projection["factors"])

    def test_explosion_then_boss_next_mon_is_valid_and_bonused(self) -> None:
        fixture = _fixture(
            [
                {"id": "move_explosion", "kind": "move", "name": "Explosion"},
            ]
        )
        plan = _plan(
            "plan_sacrifice_trade",
            [
                {"actor": None, "action_id": "move_explosion"},
                {"actor": "boss_next_mon", "action_id": "move_explosion"},
            ],
        )
        projection = project_plan_route(fixture, plan)
        self.assertTrue(projection["structural_valid"])
        self.assertEqual(projection["invalid_post_steps"], [])
        self.assertTrue(projection["honest_continuation"])
        self.assertEqual(
            projection["route_value_delta"], STRUCTURAL_CONTINUATION_BONUS
        )
        self.assertIn("self_ko_trade", projection["factors"])
        self.assertIn("honest_continuation", projection["factors"])

    def test_switch_then_same_actor_flagged_invalid(self) -> None:
        fixture = _fixture(
            [
                {"id": "switch_kingdra", "kind": "switch", "name": "Switch to Kingdra"},
                {"id": "move_thunder", "kind": "move", "name": "Thunder"},
            ]
        )
        plan = _plan(
            "plan_switch_then_continue_same_mon",
            [
                {"actor": None, "action_id": "switch_kingdra"},
                {"actor": None, "action_id": "move_thunder"},
            ],
        )
        projection = project_plan_route(fixture, plan)
        self.assertFalse(projection["structural_valid"])
        self.assertIn("switch_pivot", projection["factors"])

    def test_switch_then_boss_next_mon_is_valid(self) -> None:
        fixture = _fixture(
            [
                {"id": "switch_kingdra", "kind": "switch", "name": "Switch to Kingdra"},
                {"id": "move_thunder", "kind": "move", "name": "Thunder"},
            ]
        )
        plan = _plan(
            "plan_switch_then_attack",
            [
                {"actor": None, "action_id": "switch_kingdra"},
                {"actor": "boss_next_mon", "action_id": "move_thunder"},
            ],
        )
        projection = project_plan_route(fixture, plan)
        self.assertTrue(projection["structural_valid"])
        self.assertTrue(projection["honest_continuation"])

    def test_non_terminator_then_same_actor_is_fine(self) -> None:
        fixture = _fixture(
            [
                {"id": "move_curse", "kind": "move", "name": "Curse"},
                {"id": "move_earthquake", "kind": "move", "name": "Earthquake"},
            ]
        )
        plan = _plan(
            "plan_curse_then_earthquake",
            [
                {"actor": None, "action_id": "move_curse"},
                {"actor": None, "action_id": "move_earthquake"},
            ],
        )
        projection = project_plan_route(fixture, plan)
        self.assertTrue(projection["structural_valid"])
        self.assertEqual(projection["route_value_delta"], 0)
        self.assertEqual(projection["factors"], [])


if __name__ == "__main__":
    unittest.main()
