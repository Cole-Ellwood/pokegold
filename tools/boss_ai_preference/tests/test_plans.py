from __future__ import annotations

import unittest

from tools.boss_ai_preference.features import extract_plan_features
from tools.boss_ai_preference.plans import generate_plan_cards


class PlanGenerationTests(unittest.TestCase):
    def test_sleep_setup_attack_plan_is_generated_for_sleep_setup_fixture(self) -> None:
        fixture = {
            "id": "sleep_setup_fixture",
            "leader": "Tester",
            "turn": 5,
            "tags": ["sleep", "setup"],
            "state": {},
            "actions": [
                {
                    "id": "move_sleep_powder",
                    "kind": "move",
                    "name": "Sleep Powder",
                    "explanation": "Creates a setup turn if it lands.",
                    "public_tradeoff": "Strong but accuracy-dependent.",
                },
                {
                    "id": "move_swords_dance",
                    "kind": "move",
                    "name": "Swords Dance",
                    "explanation": "Can snowball after sleep creates safety.",
                    "public_tradeoff": "Greedy before sleep lands.",
                },
                {
                    "id": "move_sludge_bomb",
                    "kind": "move",
                    "name": "Sludge Bomb",
                    "explanation": "Direct damage.",
                    "public_tradeoff": "Cash pressure after setup.",
                },
            ],
        }

        plans = generate_plan_cards(fixture, max_cards=4)
        sleep_setup = next(
            plan for plan in plans if plan["shape"] == "sleep_then_setup_then_attack"
        )

        self.assertEqual(
            [step["action_id"] for step in sleep_setup["steps"][:3]],
            ["move_sleep_powder", "move_swords_dance", "move_sludge_bomb"],
        )
        self.assertIn("status_misses", sleep_setup["stop_conditions"])
        self.assertIn("target_wakes", sleep_setup["stop_conditions"])

    def test_sleep_setup_attack_plan_requires_sleep_and_setup_tags(self) -> None:
        fixture = {
            "id": "plain_status_fixture",
            "leader": "Tester",
            "turn": 5,
            "tags": ["sleep"],
            "state": {},
            "actions": [
                {
                    "id": "move_hypnosis",
                    "kind": "move",
                    "name": "Hypnosis",
                    "explanation": "Sleep pressure.",
                    "public_tradeoff": "Accuracy-dependent.",
                },
                {
                    "id": "move_curse",
                    "kind": "move",
                    "name": "Curse",
                    "explanation": "Setup-looking move.",
                    "public_tradeoff": "Not automatically a sleep setup plan.",
                },
                {
                    "id": "move_night_shade",
                    "kind": "move",
                    "name": "Night Shade",
                    "explanation": "Direct damage.",
                    "public_tradeoff": "Reliable damage.",
                },
            ],
        }

        plans = generate_plan_cards(fixture, max_cards=4)

        self.assertNotIn(
            "sleep_then_setup_then_attack",
            {plan["shape"] for plan in plans},
        )

    def test_pressure_recover_lock_plan_is_generated_for_ace_lock_fixture(self) -> None:
        fixture = {
            "id": "ace_lock_fixture",
            "leader": "Tester",
            "turn": 5,
            "tags": ["ace_preservation", "setup_lock"],
            "state": {},
            "actions": [
                {
                    "id": "move_body_slam",
                    "kind": "move",
                    "name": "Body Slam",
                    "explanation": "Safe pressure with paralysis value.",
                    "public_tradeoff": "Does not lock the ace.",
                    "damage_estimate": {
                        "low_percent": 15,
                        "high_percent": 20,
                        "target_hp": "78%",
                    },
                },
                {
                    "id": "move_rollout",
                    "kind": "move",
                    "name": "Rollout",
                    "explanation": "Risky lock-in.",
                    "public_tradeoff": "Can be punished before status.",
                },
                {
                    "id": "move_milk_drink",
                    "kind": "move",
                    "name": "Milk Drink",
                    "explanation": "Recovery after chip.",
                    "public_tradeoff": "Bad if used too early.",
                },
            ],
        }

        plans = generate_plan_cards(fixture, max_cards=4)
        pressure_plan = next(
            plan for plan in plans if plan["shape"] == "pressure_recover_then_lock"
        )

        self.assertEqual(
            [step["action_id"] for step in pressure_plan["steps"][:4]],
            ["move_body_slam", "move_body_slam", "move_milk_drink", "move_rollout"],
        )
        self.assertIn("target_statused", pressure_plan["branch_rules"][0]["if"])
        self.assertIn("target_can_punish_lock", pressure_plan["stop_conditions"])

    def test_plan_features_encode_public_lethal_threat_policy_context(self) -> None:
        fixture = {
            "id": "public_lethal_threat_fixture",
            "leader": "Tester",
            "turn": 5,
            "tags": ["ace_preservation"],
            "training_focus": "Preserve the active into a faster public threat.",
            "incoming_threats": [
                {
                    "immediacy": "active",
                    "severity": "lethal",
                    "likelihood": 99,
                    "move": "Crunch",
                }
            ],
            "actions": [
                {
                    "id": "move_surf",
                    "kind": "move",
                    "name": "Surf",
                    "explanation": "Direct damage.",
                    "public_tradeoff": "Best stay-in attack if it moves.",
                },
                {
                    "id": "switch_houndoom",
                    "kind": "switch",
                    "name": "Switch to Houndoom",
                    "explanation": "Preserve the active into public Dark pressure.",
                    "public_tradeoff": "Gives up immediate damage.",
                },
            ],
        }
        attack_plan = {
            "id": "attack_plan",
            "label": "Surf now",
            "shape": "attack_now",
            "phase": "mid",
            "horizon": 3,
            "stop_conditions": [],
            "initiation_conditions": [],
            "branch_rules": [],
            "steps": [{"action_id": "move_surf"}],
        }
        switch_plan = {
            "id": "switch_plan",
            "label": "Switch and re-score",
            "shape": "switch_preserve_then_rescore",
            "phase": "mid",
            "horizon": 3,
            "stop_conditions": [],
            "initiation_conditions": [],
            "branch_rules": [],
            "steps": [{"action_id": "switch_houndoom"}],
        }

        attack_features = extract_plan_features(fixture, attack_plan)["features"]
        switch_features = extract_plan_features(fixture, switch_plan)["features"]

        self.assertIn("plan_attack_now_under_public_lethal_threat", attack_features)
        self.assertIn(
            "plan_attack_now_under_fast_public_lethal_threat",
            attack_features,
        )
        self.assertIn(
            "plan_stays_in_under_public_major_or_lethal_threat",
            attack_features,
        )
        self.assertIn(
            "plan_switch_preserve_under_public_lethal_threat",
            switch_features,
        )
        self.assertIn(
            "plan_switch_preserve_under_fast_public_lethal_threat",
            switch_features,
        )
        self.assertNotIn("plan_stays_in_under_public_lethal_threat", switch_features)


if __name__ == "__main__":
    unittest.main()
