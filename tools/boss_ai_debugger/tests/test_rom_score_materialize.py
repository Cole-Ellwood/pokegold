from __future__ import annotations

import unittest
from pathlib import Path

from tools.boss_ai_debugger.generators import generate_scenarios
from tools.boss_ai_debugger.rom_score_materialize import (
    MOVES,
    ScenarioMaterialization,
    TYPES,
    action_id_for_slot,
    active_boss_type_patches,
    active_player_patches,
    build_fast_score_report,
    chunk_scenarios,
    empty_contribution_comparison,
    fallback_replay_controls_from_manifest,
    format_rom_score_materialization,
    hook_equivalence_summary,
    materialization_for_scenario,
    move_ids_for_scenario,
    parse_optional_spikes_layers,
    parse_spikes_layers,
    policy_verdict_from_rom_selector,
    replay_controls_from_manifest,
    score_materialization_failure_count,
    score_materialization_skip_reason,
    verdict_from_materialized_trace,
    scenario_condition_tags,
    turn_cache_miss_patches,
    validate_score_materialization_base,
)
from tools.boss_ai_preference.data import PreferenceDataError


class RomScoreMaterializeTests(unittest.TestCase):
    def test_type_constants_match_rom_type_ids(self) -> None:
        self.assertEqual(TYPES["FIRE"], 0x14)
        self.assertEqual(TYPES["WATER"], 0x15)
        self.assertEqual(TYPES["GRASS"], 0x16)
        self.assertEqual(TYPES["ELECTRIC"], 0x17)
        self.assertEqual(TYPES["PSYCHIC"], 0x18)

    def test_active_boss_water_type_patch_uses_water_id(self) -> None:
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in active_boss_type_patches(active_ghost=False)
        }

        self.assertEqual(patches[("wEnemyMonType1", 0)], TYPES["POISON"])
        self.assertEqual(patches[("wEnemyMonType2", 0)], TYPES["WATER"])

    def test_active_player_starmie_patch_uses_water_psychic_ids(self) -> None:
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in active_player_patches(active_species_prior=True)
        }

        self.assertEqual(patches[("wBattleMonType1", 0)], TYPES["WATER"])
        self.assertEqual(patches[("wBattleMonType2", 0)], TYPES["PSYCHIC"])

    def test_move_ids_map_generated_spikes_case_to_real_moves(self) -> None:
        scenario = generate_scenarios(family="spikes_spin", count=1, seed=1)[0]

        self.assertEqual(
            move_ids_for_scenario(scenario, move_name_to_id={}),
            [0xBF, 0xBC, 0x39, 0x99],
        )

    def test_move_ids_reject_boolean_explicit_move_id(self) -> None:
        scenario = {
            "moves": [
                {"id": "move_a", "move_id": True},
            ],
        }

        with self.assertRaisesRegex(PreferenceDataError, "move_id for slot 1"):
            move_ids_for_scenario(scenario, move_name_to_id={})

    def test_materialization_patches_public_spikes_and_rapid_spin_state(self) -> None:
        scenario = generate_scenarios(family="spikes_spin", count=1, seed=1)[0]
        scenario["expectation"]["condition_tags"] = [
            "spikes_layers_2",
            "active_revealed_rapid_spin",
            "foresight_identified_ghost",
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
        self.assertEqual(patches[("wEnemySubStatus1", 0)], 1 << 3)
        self.assertEqual(patches[("wPlayerUsedMoves", 0)], MOVES["RAPID_SPIN"])
        self.assertEqual(patches[("wBossAISeenPlayerSpeciesCount", 0)], 2)
        self.assertEqual(patches[("wBossAISpeciesUsedMoves", 4)], MOVES["RAPID_SPIN"])
        self.assertEqual(patches[("wBossAIPublicThreatCache", 0)], 0xFF)
        self.assertEqual(patches[("wBossAIPrimaryThreatCache", 0)], 0xFF)

    def test_turn_cache_miss_patches_mirror_boss_ai_reset_turn_caches(self) -> None:
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in turn_cache_miss_patches()
        }

        self.assertEqual(patches[("wBossAIHasKOMoveCache", 0)], 0xFF)
        self.assertEqual(patches[("wBossAIPublicThreatCache", 0)], 0xFF)
        self.assertEqual(patches[("wBossAIRevealedPriorityCache", 0)], 0xFF)
        self.assertEqual(patches[("wBossAIPrimaryThreatCache", 0)], 0xFF)
        self.assertEqual(patches[("wBossAIPublicEnemyFasterCache", 0)], 0xFF)
        self.assertEqual(patches[("wBossAILookaheadDepthCache", 0)], 0xFF)
        self.assertEqual(patches[("wBossAILastMatchupType", 0)], 0xFF)
        self.assertEqual(patches[("wBossAIShouldScoutPrereqCache", 0)], 0xFF)
        self.assertEqual(patches[("wBossAIShouldScoutMatchupValue", 0)], 0xFF)

    def test_layer_parser_uses_condition_tags(self) -> None:
        tags = {"spikes_layers_3", "active_revealed_rapid_spin"}

        self.assertEqual(parse_spikes_layers(tags), 3)

    def test_optional_layer_parser_defaults_to_zero(self) -> None:
        self.assertEqual(parse_optional_spikes_layers({"setup_window"}), 0)

    def test_scenario_condition_tags_reads_expectation(self) -> None:
        scenario = {"expectation": {"condition_tags": ["a", "b"]}}

        self.assertEqual(scenario_condition_tags(scenario), {"a", "b"})

    def test_action_id_for_slot_maps_rom_slot_index(self) -> None:
        scenario = {"moves": [{"id": "first"}, {"id": "second"}]}

        self.assertEqual(action_id_for_slot(scenario, 1), "second")
        self.assertIsNone(action_id_for_slot(scenario, 4))

    def test_fast_score_mode_uses_empty_contribution_comparison(self) -> None:
        comparison = empty_contribution_comparison()

        self.assertEqual(comparison["matched_trace_count"], 0)
        self.assertEqual(comparison["mismatch_count"], 0)
        self.assertEqual(comparison["mismatch_class_counts"], {})

    def test_hook_equivalence_summary_compares_scores_and_choice(self) -> None:
        summary = hook_equivalence_summary(
            traced_report={
                "move_scores": [20, 25],
                "chosen": {"move_id": 1, "slot_index": 0},
            },
            fast_report={
                "move_scores": [20, 26],
                "chosen": {"move_id": 2, "slot_index": 1},
            },
        )

        self.assertTrue(summary["checked"])
        self.assertFalse(summary["match"])
        self.assertFalse(summary["score_bytes_match"])
        self.assertFalse(summary["chosen_match"])

    def test_fast_score_report_includes_selector_entry_scores(self) -> None:
        report = build_fast_score_report(
            save_state=Path(__file__),
            basis={},
            values={
                "wBossAITraceChosenMove": [0x99],
                "wCurEnemyMoveNum": [3],
                "wEnemyMonMoves": [0xBF, 0xBC, 0x39, 0x99],
                "wEnemyAIMoveScores": [38, 38, 38, 28],
                "wBossAITracePreModelScores": [20, 20, 20, 20],
                "wBossAITracePostModelScores": [14, 10, 19, 28],
            },
            move_names={0x99: "EXPLOSION"},
            memory_patches=[],
            selector_entry_scores=[20, 20, 19, 28],
        )

        self.assertEqual(report["selector_entry_scores"], [20, 20, 19, 28])

    def test_materialized_verdict_uses_selector_scan_scores(self) -> None:
        scenario = {
            "id": "unit_selector_scores",
            "tier": "mid",
            "moves": [
                {"id": "best", "name": "Best"},
                {"id": "second", "name": "Second", "base_score": 25},
                {"id": "blocked_a", "name": "Blocked A", "blocked": True},
                {"id": "blocked_b", "name": "Blocked B", "blocked": True},
            ],
            "expectation": {"best_action_ids": ["best"]},
        }
        report = verdict_from_materialized_trace(
            scenario,
            ScenarioMaterialization(
                scenario_id="unit_selector_scores",
                patches=[],
                move_ids=[1, 2, 3, 4],
                layers=0,
            ),
            {
                "move_ids": [1, 2, 3, 4],
                "move_scores": [99, 99, 99, 99],
                "selector_entry_scores": [20, 25, 80, 80],
            },
            move_names={1: "BEST", 2: "SECOND", 3: "BLOCKED_A", 4: "BLOCKED_B"},
            compare_contributions=False,
        )

        self.assertTrue(report["score_bytes_match"])
        self.assertTrue(report["selector_top_match"])
        self.assertEqual(report["rom"]["final_scores"], [20, 25, 80, 80])
        self.assertEqual(report["rom"]["replay_end_scores"], [99, 99, 99, 99])

    def test_public_policy_materialization_maps_synthetic_moves(self) -> None:
        scenario = generate_scenarios(family="support_handoff", count=1, seed=9)[0]
        scenario["tier"] = "mid"

        materialization = materialization_for_scenario(
            scenario,
            move_name_to_id={},
        )
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in materialization.patches
        }

        self.assertEqual(materialization.move_ids, [0x5C, 0xE2, 0x2E, 0xBC])
        self.assertEqual(patches[("wBossAITier", 0)], 2)
        self.assertEqual(patches[("wEnemyMonMoves", 1)], 0xE2)
        self.assertEqual(patches[("wOTPartyCount", 0)], 2)

    def test_reject_reckless_prediction_keeps_active_target_vulnerable(self) -> None:
        scenario = generate_scenarios(family="prediction_mix", count=2, seed=3)[1]

        materialization = materialization_for_scenario(
            scenario,
            move_name_to_id={},
        )
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in materialization.patches
        }

        self.assertIn("worst_case_unguarded", scenario["expectation"]["condition_tags"])
        self.assertIn(
            "active_pressure_converts",
            scenario["expectation"]["condition_tags"],
        )
        self.assertEqual(patches[("wBattleMonType1", 0)], TYPES["WATER"])
        self.assertEqual(patches[("wBattleMonType2", 0)], TYPES["PSYCHIC"])

    def test_setup_bankrolled_materialization_patches_enemy_turns_taken(self) -> None:
        scenario = generate_scenarios(family="setup_heal", count=2, seed=3)[1]

        materialization = materialization_for_scenario(
            scenario,
            move_name_to_id={},
        )
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in materialization.patches
        }

        self.assertIn(
            "setup_already_bankrolled",
            scenario["expectation"]["condition_tags"],
        )
        self.assertEqual(patches[("wEnemyTurnsTaken", 0)], 1)
        self.assertEqual(patches[("wPlayerTurnsTaken", 0)], 1)
        self.assertLess(
            patches[("wEnemyMonHP", 1)],
            patches[("wEnemyMonMaxHP", 1)],
        )

    def test_resisted_explosion_case_materializes_target_window(self) -> None:
        scenario = generate_scenarios(family="cashout_board_delta", count=2, seed=23)[1]

        materialization = materialization_for_scenario(
            scenario,
            move_name_to_id={},
        )
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in materialization.patches
        }

        self.assertIn(
            "resisted_explosion_free_owner",
            scenario["expectation"]["condition_tags"],
        )
        self.assertEqual(patches[("wBattleMonHP", 1)], 22)
        self.assertEqual(patches[("wBattleMonType1", 0)], TYPES["STEEL"])
        self.assertEqual(patches[("wBattleMonType2", 0)], TYPES["GRASS"])

    def test_score_materialization_skips_switch_best_cases(self) -> None:
        scenario = generate_scenarios(family="cashout_board_delta", count=4, seed=23)[3]

        self.assertEqual(scenario["policy_case"], "sleep_plus_cashout_package")
        self.assertEqual(
            score_materialization_skip_reason(scenario),
            "expected best action is switch-only; use rom-switch-materialize",
        )

    def test_mastery_policy_materialization_maps_active_pressure_case(self) -> None:
        scenario = generate_scenarios(family="mastery_policy", count=1, seed=1)[0]

        materialization = materialization_for_scenario(
            scenario,
            move_name_to_id={},
        )

        self.assertEqual(
            materialization.move_ids,
            [0x7E, 0x5C, 0xE2, 0x99],
        )

    def test_mastery_policy_materialization_maps_support_handoff_case(self) -> None:
        scenario = generate_scenarios(family="mastery_policy", count=8, seed=1)[7]

        self.assertEqual(scenario["policy_card"], "support_handoff_after_job")

        materialization = materialization_for_scenario(
            scenario,
            move_name_to_id={},
        )

        self.assertEqual(
            materialization.move_ids,
            [0xE2, 0x2E, 0x5C, 0xBC],
        )
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in materialization.patches
        }
        self.assertEqual(patches[("wBattleMonStatus", 0)], 8)

    def test_branch_policy_materialization_maps_status_absorber(self) -> None:
        scenario = generate_scenarios(family="mastery_policy", count=2, seed=1)[1]

        self.assertEqual(scenario["policy_card"], "branch_action_after_naming")

        materialization = materialization_for_scenario(
            scenario,
            move_name_to_id={},
        )
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in materialization.patches
        }

        self.assertEqual(patches[("wBattleMonType1", 0)], TYPES["POISON"])
        self.assertEqual(patches[("wBattleMonType2", 0)], TYPES["POISON"])

    def test_cashout_policy_materialization_maps_trade_window(self) -> None:
        scenario = generate_scenarios(family="mastery_policy", count=3, seed=1)[2]

        self.assertEqual(scenario["policy_card"], "cashout_boundary")

        materialization = materialization_for_scenario(
            scenario,
            move_name_to_id={},
        )
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in materialization.patches
        }

        self.assertEqual(patches[("wBattleMonHP", 1)], 22)
        self.assertEqual(patches[("wBattleMonType1", 0)], TYPES["STEEL"])
        self.assertEqual(patches[("wBattleMonType2", 0)], TYPES["GRASS"])

    def test_hazard_policy_materialization_maps_spin_window(self) -> None:
        scenario = generate_scenarios(family="mastery_policy", count=4, seed=1)[3]

        self.assertEqual(scenario["policy_card"], "hazard_loop_spin_window")

        materialization = materialization_for_scenario(
            scenario,
            move_name_to_id={},
        )
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in materialization.patches
        }

        self.assertEqual(materialization.layers, 1)
        self.assertEqual(patches[("wPlayerUsedMoves", 0)], MOVES["RAPID_SPIN"])

    def test_cashout_materialization_patches_revealed_ghost_branch(self) -> None:
        scenario = generate_scenarios(family="cashout_board_delta", count=3, seed=11)[2]

        materialization = materialization_for_scenario(
            scenario,
            move_name_to_id={},
        )
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in materialization.patches
        }

        self.assertEqual(materialization.move_ids[:2], [0x99, 0x59])
        self.assertEqual(patches[("wBattleMonStatus", 0)], 8)
        self.assertEqual(patches[("wBossAISeenPlayerSpeciesCount", 0)], 2)
        self.assertEqual(patches[("wBossAISeenPlayerSpecies", 1)], 0x5E)
        self.assertEqual(patches[("wBossAISeenPlayerAliveMask", 0)], 0b00000011)

    def test_rom_policy_verdict_uses_observed_score_bytes(self) -> None:
        scenario = generate_scenarios(family="prediction_mix", count=2, seed=3)[1]
        rom_selector = {
            "ready": True,
            "best_slot_index": 1,
            "probabilities_by_slot": {0: 0.25, 1: 0.75, 2: 0.0, 3: 0.0},
        }

        verdict = policy_verdict_from_rom_selector(scenario, rom_selector)

        self.assertEqual(verdict["verdict"], "bad_roll")
        self.assertEqual(verdict["rolled_bad_action_ids"], ["move_reckless_prediction"])

    def test_rom_policy_verdict_allows_unrolled_tied_expected_best(self) -> None:
        scenario = {
            "id": "tie",
            "moves": [
                {"id": "a", "name": "A"},
                {"id": "b", "name": "B"},
                {"id": "c", "name": "C"},
            ],
            "expectation": {"best_action_ids": ["a", "b", "c"]},
        }
        rom_selector = {
            "ready": True,
            "best_slot_index": 0,
            "probabilities_by_slot": {0: 1.0, 1: 0.0, 2: 0.0},
        }

        verdict = policy_verdict_from_rom_selector(scenario, rom_selector)

        self.assertEqual(verdict["verdict"], "pass")
        self.assertEqual(verdict["zero_probability_best_action_ids"], ["b", "c"])

    def test_score_materialization_report_ranks_policy_items_first(self) -> None:
        report = {
            "scenario_count": 2,
            "checked_count": 2,
            "skipped_count": 0,
            "error_count": 0,
            "score_bytes_match_count": 0,
            "contribution_matched_count": 0,
            "hook_equivalence_mismatch_count": 0,
            "base_route": "koga",
            "base_state": "state",
            "button_presses": 0,
            "button_interval_frames": 0,
            "score_replay_mode": "fast_score_only",
            "materializations_per_minute": 1.0,
            "known_limits": [],
            "verdicts": [
                {
                    "scenario_id": "score_noise",
                    "status": "pass",
                    "score_bytes_match": False,
                    "contribution_comparison": {"mismatch_count": 0},
                    "hook_equivalence": {},
                    "rom_policy": {"verdict": "pass", "severity": 0},
                    "rom": {"best_action_id": "a"},
                    "python": {"best_action_id": "b"},
                },
                {
                    "scenario_id": "policy_review",
                    "status": "pass",
                    "score_bytes_match": False,
                    "contribution_comparison": {"mismatch_count": 0},
                    "hook_equivalence": {},
                    "rom_policy": {"verdict": "acceptable_top", "severity": 30},
                    "rom": {"best_action_id": "c"},
                    "python": {"best_action_id": "d"},
                },
            ],
        }

        text = format_rom_score_materialization(report, limit=2)

        self.assertLess(text.index("policy_review"), text.index("score_noise"))

    def test_score_materialization_failure_count_covers_fail_on_mismatch_cases(self) -> None:
        report = {
            "error_count": 1,
            "contribution_mismatch_count": 2,
            "hook_equivalence_mismatch_count": 3,
            "verdicts": [
                {
                    "status": "pass",
                    "family": "spikes_spin",
                    "score_bytes_match": False,
                    "rom_policy": {"severity": 0},
                },
                {
                    "status": "pass",
                    "family": "mastery_policy",
                    "score_bytes_match": False,
                    "rom_policy": {"severity": 0},
                },
                {
                    "status": "pass",
                    "family": "support_handoff",
                    "score_bytes_match": True,
                    "rom_policy": {"severity": 80},
                },
            ],
        }

        self.assertEqual(score_materialization_failure_count(report), 8)

    def test_score_materialization_failure_count_allows_broad_score_review_noise(self) -> None:
        report = {
            "error_count": 0,
            "contribution_mismatch_count": 0,
            "hook_equivalence_mismatch_count": 0,
            "verdicts": [
                {
                    "status": "pass",
                    "family": "mastery_policy",
                    "score_bytes_match": False,
                    "rom_policy": {"severity": 0},
                }
            ],
        }

        self.assertEqual(score_materialization_failure_count(report), 0)

    def test_chunk_scenarios_preserves_all_cases(self) -> None:
        scenarios = [{"id": str(index)} for index in range(7)]

        chunks = chunk_scenarios(scenarios, workers=3)

        self.assertEqual([len(chunk) for chunk in chunks], [3, 2, 2])
        self.assertEqual(
            sorted(item["id"] for chunk in chunks for item in chunk),
            [str(index) for index in range(7)],
        )

    def test_replay_controls_use_clean_score_materialization_state_when_present(self) -> None:
        controls = replay_controls_from_manifest(
            {
                "pre_choice_state": "bad_mid_ai.state",
                "score_materialization_state": ".local/tmp/clean.state",
                "score_materialization_button_presses": 5,
                "score_materialization_button_interval_frames": 45,
                "score_materialization_watch_frames": 270,
            },
            button="a",
            button_delay=8,
            watch_frames=90,
        )

        self.assertEqual(controls.base_state_field, "score_materialization_state")
        self.assertEqual(controls.button_presses, 5)
        self.assertEqual(controls.button_interval_frames, 45)
        self.assertEqual(controls.watch_frames, 270)

    def test_replay_controls_reject_pre_choice_as_primary_score_base(self) -> None:
        with self.assertRaisesRegex(
            PreferenceDataError,
            "requires score_materialization_state",
        ):
            replay_controls_from_manifest(
                {"pre_choice_state": ".local/tmp/pre_choice.state"},
                button="a",
                button_delay=8,
                watch_frames=90,
            )

    def test_score_materialization_fallback_uses_pre_choice_controls(self) -> None:
        controls = fallback_replay_controls_from_manifest(
            {
                "pre_choice_state": ".local/tmp/pre_choice.state",
                "score_materialization_state": ".local/tmp/stale_score.state",
                "choice_button": "a",
                "choice_wait_frames": 45,
            },
            button="b",
            button_delay=8,
            watch_frames=90,
        )

        self.assertIsNotNone(controls)
        assert controls is not None
        self.assertEqual(controls.base_state_field, "pre_choice_state")
        self.assertEqual(controls.button, "a")
        self.assertEqual(controls.button_presses, 1)

    def test_score_materialization_base_rejects_mid_ai_trace_scores(self) -> None:
        with self.assertRaisesRegex(PreferenceDataError, "already inside"):
            validate_score_materialization_base(
                {
                    "wBossAITraceChosenMove": [0],
                    "wBossAITraceTopMoves": [0, 0, 0],
                    "wBossAITracePreModelScores": [20, 20, 20, 0xFF],
                    "wBossAITracePostModelScores": [14, 10, 0xFF, 0xFF],
                }
            )


if __name__ == "__main__":
    unittest.main()
