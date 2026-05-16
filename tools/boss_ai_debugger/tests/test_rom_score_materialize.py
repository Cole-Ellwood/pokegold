from __future__ import annotations

import unittest
from pathlib import Path

from tools.boss_ai_debugger.generators import generate_scenarios
from tools.boss_ai_debugger.rom_score_materialize import (
    MOVES,
    action_id_for_slot,
    build_fast_score_report,
    chunk_scenarios,
    empty_contribution_comparison,
    hook_equivalence_summary,
    materialization_for_scenario,
    move_ids_for_scenario,
    parse_optional_spikes_layers,
    parse_spikes_layers,
    policy_verdict_from_rom_selector,
    replay_controls_from_manifest,
    scenario_condition_tags,
    validate_score_materialization_base,
)
from tools.boss_ai_preference.data import PreferenceDataError


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
