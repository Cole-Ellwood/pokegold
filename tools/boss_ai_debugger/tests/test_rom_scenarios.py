from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.rom_scenarios import (
    AI_TIER_EARLY,
    AI_TIER_LATE,
    AI_TIER_MID,
    apply_score_delta,
    adjusted_best_roll_threshold,
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
        self.assertAlmostEqual(result["probabilities"]["a"], 154 / 256)
        self.assertAlmostEqual(result["probabilities"]["b"], 102 / 256)
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

    def test_early_tier_keeps_base_level_planning_without_lookahead(self) -> None:
        result = select_move(
            {
                "id": "early_no_lookahead",
                "tier": "early",
                "moves": [
                    {"id": "setup", "name": "Setup", "lookahead_delta": -6},
                    {"id": "attack", "name": "Attack", "lookahead_delta": 6},
                ],
            }
        )

        moves = {move["action_id"]: move for move in result["moves"]}
        self.assertEqual(moves["setup"]["final_score"], 20)
        self.assertEqual(moves["attack"]["final_score"], 20)
        self.assertFalse(moves["setup"]["lookahead_applied"])
        self.assertFalse(moves["attack"]["lookahead_applied"])

    def test_mid_and_late_tiers_apply_lookahead_to_same_state(self) -> None:
        base_scenario = {
            "id": "tiered_lookahead",
            "moves": [
                {"id": "setup", "name": "Setup", "lookahead_delta": -6},
                {"id": "attack", "name": "Attack", "lookahead_delta": 6},
            ],
        }

        for tier in ("mid", "late"):
            scenario = {**base_scenario, "tier": tier}
            result = select_move(scenario)
            moves = {move["action_id"]: move for move in result["moves"]}

            self.assertEqual(moves["setup"]["final_score"], 14)
            self.assertEqual(moves["attack"]["final_score"], 26)
            self.assertTrue(moves["setup"]["lookahead_applied"])
            self.assertTrue(moves["attack"]["lookahead_applied"])
            self.assertEqual(result["best_action_id"], "setup")

    def test_tiered_selector_confidence_is_observable_on_same_scores(self) -> None:
        scenario = {
            "id": "same_scores_tier_confidence",
            "lookahead": False,
            "moves": [
                {"id": "best", "name": "Best", "base_score": 17},
                {"id": "second", "name": "Second", "base_score": 20},
            ],
        }

        early = select_move({**scenario, "tier": "early"})
        mid = select_move({**scenario, "tier": "mid"})
        late = select_move({**scenario, "tier": "late"})

        self.assertEqual(early["best_roll_threshold"], 192)
        self.assertEqual(mid["best_roll_threshold"], 212)
        self.assertEqual(late["best_roll_threshold"], 224)
        self.assertLess(
            early["probabilities"]["best"],
            mid["probabilities"]["best"],
        )
        self.assertLess(
            mid["probabilities"]["best"],
            late["probabilities"]["best"],
        )

    def test_adjusted_best_roll_threshold_tiers_are_monotonic(self) -> None:
        for gap in (3, 6):
            early = adjusted_best_roll_threshold(AI_TIER_EARLY, gap)
            mid = adjusted_best_roll_threshold(AI_TIER_MID, gap)
            late = adjusted_best_roll_threshold(AI_TIER_LATE, gap)

            self.assertLess(early, mid)
            self.assertLess(mid, late)

    def test_adjusted_best_roll_threshold_keeps_near_ties_mixed(self) -> None:
        for tier in (AI_TIER_EARLY, AI_TIER_MID, AI_TIER_LATE):
            for gap in (0, 1, 2):
                self.assertEqual(adjusted_best_roll_threshold(tier, gap), 154)

    def test_late_prediction_branch_bias_prices_receiver_coverage(self) -> None:
        scenario = {
            "id": "prediction_branch_supported",
            "tier": "late",
            "expectation": {
                "condition_tags": [
                    "prediction_branch_supported",
                    "prediction_ev_positive",
                ],
            },
            "moves": [
                {
                    "id": "move_obvious_stab",
                    "name": "Obvious Active STAB",
                    "deltas": [{"rule": "beats visible active only", "delta": -6}],
                },
                {
                    "id": "move_receiver_coverage",
                    "name": "Prediction Receiver Coverage",
                    "deltas": [{"rule": "branch coverage underweighted", "delta": -2}],
                    "lookahead_delta": -2,
                },
                {
                    "id": "move_status_script",
                    "name": "Status Script",
                },
            ],
        }

        result = select_move(scenario)
        moves = {move["action_id"]: move for move in result["moves"]}

        self.assertEqual(result["best_action_id"], "move_receiver_coverage")
        self.assertLess(
            moves["move_receiver_coverage"]["pre_lookahead_score"],
            moves["move_obvious_stab"]["pre_lookahead_score"],
        )
        self.assertEqual(moves["move_status_script"]["pre_lookahead_score"], 28)
        self.assertTrue(
            any(
                event["rule"] == "move.apply_move_model.apply_prediction_branch_bias"
                for event in moves["move_receiver_coverage"]["events"]
            )
        )

    def test_mid_tier_does_not_apply_late_prediction_branch_bias(self) -> None:
        scenario = {
            "id": "prediction_branch_supported_mid",
            "tier": "mid",
            "expectation": {
                "condition_tags": [
                    "prediction_branch_supported",
                    "prediction_ev_positive",
                ],
            },
            "moves": [
                {
                    "id": "move_obvious_stab",
                    "name": "Obvious Active STAB",
                    "deltas": [{"rule": "beats visible active only", "delta": -6}],
                },
                {
                    "id": "move_receiver_coverage",
                    "name": "Prediction Receiver Coverage",
                    "deltas": [{"rule": "branch coverage underweighted", "delta": -2}],
                    "lookahead_delta": -2,
                },
            ],
        }

        result = select_move(scenario)
        moves = {move["action_id"]: move for move in result["moves"]}

        self.assertEqual(result["best_action_id"], "move_obvious_stab")
        self.assertFalse(
            any(
                event["rule"] == "move.apply_move_model.apply_prediction_branch_bias"
                for event in moves["move_receiver_coverage"]["events"]
            )
        )

    def test_setup_discipline_stops_extra_setup_when_attack_converts(self) -> None:
        result = select_move(
            {
                "id": "setup_cashout",
                "tier": "mid",
                "expectation": {
                    "condition_tags": [
                        "active_pressure_converts",
                        "setup_already_bankrolled",
                    ],
                },
                "moves": [
                    {
                        "id": "move_more_setup",
                        "name": "More Curse",
                        "deltas": [{"rule": "setup identity", "delta": -5}],
                    },
                    {
                        "id": "move_cashout_attack",
                        "name": "Cashout Attack",
                        "deltas": [{"rule": "attack converts", "delta": -3}],
                        "lookahead_delta": -2,
                    },
                ],
            }
        )

        moves = {move["action_id"]: move for move in result["moves"]}

        self.assertEqual(result["best_action_id"], "move_cashout_attack")
        self.assertGreater(
            moves["move_more_setup"]["pre_lookahead_score"],
            moves["move_cashout_attack"]["pre_lookahead_score"],
        )

    def test_public_status_absorber_discourages_status(self) -> None:
        result = select_move(
            {
                "id": "status_absorber",
                "tier": "mid",
                "expectation": {
                    "condition_tags": ["status_absorber_named"],
                },
                "moves": [
                    {
                        "id": "move_generic_status",
                        "name": "Generic Toxic",
                        "deltas": [{"rule": "status identity", "delta": -6}],
                    },
                    {
                        "id": "move_absorber_coverage",
                        "name": "Absorber Coverage",
                        "deltas": [{"rule": "coverage", "delta": -2}],
                    },
                ],
            }
        )

        moves = {move["action_id"]: move for move in result["moves"]}

        self.assertEqual(result["best_action_id"], "move_absorber_coverage")
        self.assertEqual(moves["move_generic_status"]["pre_lookahead_score"], 80)
        self.assertTrue(moves["move_generic_status"]["blocked"])

    def test_support_handoff_bias_stops_repeat_support(self) -> None:
        result = select_move(
            {
                "id": "support_done",
                "tier": "mid",
                "expectation": {
                    "condition_tags": ["support_job_completed"],
                },
                "moves": [
                    {
                        "id": "move_repeat_support",
                        "name": "Repeat Support",
                        "deltas": [{"rule": "support identity", "delta": -5}],
                    },
                    {
                        "id": "move_handoff_converter",
                        "name": "Handoff Converter",
                        "deltas": [{"rule": "converter", "delta": -2}],
                        "lookahead_delta": -2,
                    },
                ],
            }
        )

        self.assertEqual(result["best_action_id"], "move_handoff_converter")

    def test_reversible_cashout_bias_demotes_boom_now(self) -> None:
        result = select_move(
            {
                "id": "cashout",
                "tier": "mid",
                "expectation": {
                    "condition_tags": ["reversible_before_irreversible"],
                },
                "moves": [
                    {
                        "id": "move_boom_now",
                        "name": "Explosion Now",
                        "deltas": [{"rule": "old boom score", "delta": -7}],
                    },
                    {
                        "id": "move_reversible_branch_cover",
                        "name": "Earthquake Branch Cover",
                        "deltas": [{"rule": "coverage", "delta": -2}],
                        "lookahead_delta": -2,
                    },
                ],
            }
        )

        self.assertEqual(result["best_action_id"], "move_reversible_branch_cover")

    def test_possible_only_prediction_demotes_reckless_read(self) -> None:
        result = select_move(
            {
                "id": "reckless_prediction",
                "tier": "mid",
                "expectation": {
                    "condition_tags": ["prediction_branch_possible_only"],
                },
                "moves": [
                    {
                        "id": "move_safe_active_ko",
                        "name": "Safe Active KO",
                        "deltas": [{"rule": "visible KO", "delta": -6}],
                    },
                    {
                        "id": "move_reckless_prediction",
                        "name": "Reckless Prediction Coverage",
                        "deltas": [{"rule": "speculative payoff", "delta": -7}],
                        "lookahead_delta": 2,
                    },
                ],
            }
        )

        self.assertEqual(result["best_action_id"], "move_safe_active_ko")

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
        self.assertEqual(result["best_roll_threshold"], 154)
        self.assertAlmostEqual(result["probabilities_by_slot"][0], 154 / 256)
        self.assertAlmostEqual(result["probabilities_by_slot"][1], 102 / 256)

    def test_selector_replay_tier_confidence_starts_at_gap_three(self) -> None:
        early = select_from_score_bytes(
            scenario_id="gap_three_early",
            tier="early",
            move_ids=[10, 11, 12, 13],
            scores=[20, 23, 40, 40],
        )
        mid = select_from_score_bytes(
            scenario_id="gap_three_mid",
            tier="mid",
            move_ids=[10, 11, 12, 13],
            scores=[20, 23, 40, 40],
        )
        late = select_from_score_bytes(
            scenario_id="gap_three_late",
            tier="late",
            move_ids=[10, 11, 12, 13],
            scores=[20, 23, 40, 40],
        )

        self.assertEqual(early["best_roll_threshold"], 192)
        self.assertEqual(mid["best_roll_threshold"], 212)
        self.assertEqual(late["best_roll_threshold"], 224)

    def test_cli_builtin_runs(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = debugger_main(["simulate", "--builtin", "all_equal_late"])

        self.assertEqual(code, 0)
        self.assertIn("Selectable but never rolled: slot3, slot4", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
