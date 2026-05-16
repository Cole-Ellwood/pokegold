from __future__ import annotations

import unittest

from tools.boss_ai_debugger.review_queue import review_item


class ReviewQueuePriorityTests(unittest.TestCase):
    def test_newest_mastery_tags_raise_priority_and_add_strata(self) -> None:
        base = {
            "scenario_id": "base",
            "verdict": "mismatch",
            "severity": 70,
            "rom_best_probability": 0.75,
            "policy_tags": ["cashout"],
            "condition_tags": ["one_time_trade"],
            "answer_changing_information": ["whether delay lets the target reset"],
        }
        newest = {
            **base,
            "scenario_id": "newest",
            "policy_tags": ["cashout", "reversible_before_irreversible"],
            "condition_tags": [
                "one_time_trade",
                "resisted_explosion_free_owner",
                "clean_oracle_subset",
            ],
        }

        base_item = review_item(base, evidence_index={})
        newest_item = review_item(newest, evidence_index={})

        self.assertGreater(newest_item["priority_score"], base_item["priority_score"])
        self.assertIn("cashout_converter", newest_item["mastery_strata"])
        self.assertIn(
            "reversible_vs_irreversible_cashout",
            newest_item["mastery_strata"],
        )
        self.assertIn(
            "resisted_explosion_board_delta",
            newest_item["mastery_strata"],
        )
        self.assertIn("clean_oracle", newest_item["mastery_strata"])


if __name__ == "__main__":
    unittest.main()
