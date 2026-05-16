from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.rom_scenarios import (
    apply_score_delta,
    format_simulation,
    select_from_score_bytes,
    select_move,
)


class RomScenarioTests(unittest.TestCase):
    def test_score_delta_uses_rom_low_score_direction(self) -> None:
        self.assertEqual(apply_score_delta(20, -7), 13)
        self.assertEqual(apply_score_delta(3, -7), 1)
        self.assertEqual(apply_score_delta(78, 7), 79)
        self.assertEqual(apply_score_delta(80, -7), 80)

    def test_equal_scores_roll_only_first_two_slots(self) -> None:
        result = select_move(
            {
                "id": "tie",
                "tier": "late",
                "moves": [
                    {"id": "a", "name": "A"},
                    {"id": "b", "name": "B"},
                    {"id": "c", "name": "C"},
                    {"id": "d", "name": "D"},
                ],
            }
        )

        self.assertEqual(result["best_action_id"], "a")
        self.assertEqual(result["second_action_id"], "b")
        self.assertAlmostEqual(result["probabilities"]["a"], 186 / 256)
        self.assertAlmostEqual(result["probabilities"]["b"], 70 / 256)
        self.assertEqual(result["probabilities"]["c"], 0.0)
        self.assertEqual(result["probabilities"]["d"], 0.0)
        self.assertIn("Selectable but never rolled: c, d", format_simulation(result))

    def test_lookahead_negative_delta_encourages(self) -> None:
        result = select_move(
            {
                "id": "lookahead",
                "tier": "mid",
                "moves": [
                    {
                        "id": "setup",
                        "name": "Setup",
                        "lookahead_delta": -3,
                    },
                    {
                        "id": "attack",
                        "name": "Attack",
                        "lookahead_delta": 2,
                    },
                ],
            }
        )

        moves = {move["action_id"]: move for move in result["moves"]}
        self.assertEqual(moves["setup"]["final_score"], 17)
        self.assertEqual(moves["attack"]["final_score"], 22)
        self.assertEqual(result["best_action_id"], "setup")

    def test_lookahead_evaluates_candidates_within_max_score_swing(self) -> None:
        result = select_move(
            {
                "id": "lookahead_swing",
                "tier": "late",
                "moves": [
                    {"id": "best_now", "name": "Best Now", "lookahead_delta": 18},
                    {
                        "id": "could_leapfrog",
                        "name": "Could Leapfrog",
                        "deltas": [{"rule": "pre_score", "delta": 8}],
                        "lookahead_delta": 18,
                    },
                    {"id": "outside", "name": "Outside", "blocked": True},
                ],
            }
        )

        moves = {move["action_id"]: move for move in result["moves"]}

        self.assertTrue(moves["could_leapfrog"]["lookahead_applied"])
        self.assertEqual(moves["could_leapfrog"]["final_score"], 46)

    def test_blocked_moves_are_not_selected(self) -> None:
        result = select_move(
            {
                "id": "blocked",
                "tier": "late",
                "moves": [
                    {"id": "blocked", "name": "Blocked", "blocked": True},
                    {"id": "legal", "name": "Legal"},
                ],
            }
        )

        self.assertEqual(result["best_action_id"], "legal")
        self.assertEqual(result["probabilities"]["blocked"], 0.0)
        self.assertEqual(result["probabilities"]["legal"], 1.0)

    def test_selector_replay_stops_at_first_blank_move(self) -> None:
        result = select_from_score_bytes(
            scenario_id="blank",
            tier="late",
            move_ids=[10, 0, 11, 12],
            scores=[30, 20, 1, 1],
        )

        self.assertEqual(result["possible_slot_indices"], [0])
        self.assertEqual(result["possible_move_ids"], [10])

    def test_selector_replay_equal_scores_only_rolls_first_two_slots(self) -> None:
        result = select_from_score_bytes(
            scenario_id="equal",
            tier="late",
            move_ids=[10, 11, 12, 13],
            scores=[20, 20, 20, 20],
        )

        self.assertEqual(result["best_move_id"], 10)
        self.assertEqual(result["second_move_id"], 11)
        self.assertEqual(result["possible_slot_indices"], [0, 1])
        self.assertEqual(result["possible_move_ids"], [10, 11])

    def test_cli_builtin_runs(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = debugger_main(["simulate", "--builtin", "all_equal_late"])

        self.assertEqual(code, 0)
        self.assertIn("Selectable but never rolled: slot3, slot4", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
