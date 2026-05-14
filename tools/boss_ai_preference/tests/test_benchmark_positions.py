from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.boss_ai_preference.benchmark_positions import (
    ALLOWED_BENCHMARK_SPLITS,
    REQUIRED_OPPONENT_TIERS,
    REQUIRED_OUTCOME_LABELS,
    build_benchmark_mutation_report,
    build_benchmark_policy_answers,
    build_benchmark_report,
    choose_benchmark_policy_move,
    load_benchmark_answers,
    load_benchmark_oracles,
    load_benchmarks,
    validate_oracle_data,
    validate_policy_answer_data,
    validate_public_card_data,
    write_benchmark_mutation_report,
    write_benchmark_policy_answers,
    write_benchmark_report,
)


class BenchmarkPositionTests(unittest.TestCase):
    def test_default_benchmarks_load(self) -> None:
        benchmarks = load_benchmarks()
        oracles = load_benchmark_oracles()

        self.assertEqual(len(benchmarks), 44)
        self.assertEqual(len(oracles), 44)

    def test_initial_and_holdout_snapshot_coverage_is_present(self) -> None:
        benchmarks = load_benchmarks()
        ids = {benchmark["id"] for benchmark in benchmarks}
        profiles = {benchmark["mechanics_profile"] for benchmark in benchmarks}
        splits = {benchmark["split"] for benchmark in benchmarks}

        self.assertIn("vanilla_gsc", profiles)
        self.assertIn("romhack_gym_leader_lab", profiles)
        self.assertEqual(splits, ALLOWED_BENCHMARK_SPLITS)
        self.assertIn("vanilla_gsc_sleep_setup_disruption_001", ids)
        self.assertIn("romhack_spikes_third_layer_janine_001", ids)
        self.assertIn("romhack_spikes_fourth_click_janine_001", ids)
        self.assertIn("romhack_explosion_route_trade_brock_001", ids)
        self.assertIn("romhack_defensive_answer_preservation_pryce_001", ids)
        self.assertIn("vanilla_gsc_sleep_clause_blocked_holdout_001", ids)
        self.assertIn("romhack_spikes_public_spinner_holdout_001", ids)
        self.assertIn("romhack_spikes_maxed_explosion_conversion_holdout_001", ids)
        self.assertIn("romhack_explosion_blocked_by_protect_holdout_001", ids)
        self.assertIn("romhack_defensive_answer_unavailable_holdout_001", ids)
        self.assertIn(
            "fixture_chuck_poliwrath_vs_pidgeotto_ice_punch_001", ids
        )
        self.assertIn("fixture_janine_qwilfish_third_spikes_layer_001", ids)
        self.assertIn(
            "fixture_mechanics_snorlax_full_hp_rest_status_fail_001", ids
        )
        self.assertIn(
            "fixture_brock_golem_vs_vaporeon_explosion_question_001", ids
        )
        self.assertIn("long_battle_sleep_disruption_after_miss_001", ids)
        self.assertIn("long_battle_rest_tempo_unforced_001", ids)
        self.assertIn("romhack_spinblock_damage_context_001", ids)
        self.assertIn("vanilla_gsc_phazing_timing_mirror_001", ids)
        self.assertIn("vanilla_gsc_pp_phaze_loop_save_final_whirlwind_001", ids)
        self.assertIn("external_gsc_sleeping_lax_curse_window_001", ids)
        self.assertIn("vanilla_gsc_opening_electric_double_switch_spikes_001", ids)
        self.assertIn("external_gsc_forretress_explosion_on_quagsire_001", ids)
        self.assertIn("external_gsc_vaporeon_vs_restdtalk_snorlax_001", ids)
        self.assertIn("external_gsc_golem_late_rapid_spin_001", ids)
        self.assertIn("fixture_will_slowbro_vs_houndoom_fast_dark_001", ids)
        self.assertIn("fixture_koga_ariados_vs_typhlosion_fire_spikes_001", ids)
        self.assertIn(
            "fixture_bugsy_scyther_vs_geodude_safe_swords_dance_001", ids
        )
        self.assertIn(
            "fixture_chuck_poliwrath_vs_alakazam_psychic_pivot_001", ids
        )
        self.assertIn("fixture_morty_haunter_vs_noctowl_sleep_line_001", ids)
        self.assertIn("fixture_falkner_pidgeotto_vs_geodude_scout_probe_001", ids)
        self.assertIn("fixture_pryce_cloyster_vs_quilava_fire_pivot_001", ids)
        self.assertIn("fixture_bugsy_scyther_vs_quilava_fire_setup_001", ids)
        self.assertIn("fixture_whitney_miltank_vs_geodude_rollout_lock_001", ids)
        self.assertIn("fixture_karen_crobat_vs_dragonite_toxic_clock_001", ids)
        self.assertIn("fixture_koga_crobat_vs_alakazam_immediate_ko_001", ids)
        self.assertIn("fixture_jasmine_skarmory_vs_machoke_focus_energy_001", ids)
        self.assertIn(
            "fixture_morty_misdreavus_vs_typhlosion_perish_route_001", ids
        )
        self.assertIn("fixture_whitney_clefairy_vs_bayleef_encore_reflect_001", ids)
        self.assertIn(
            "fixture_jasmine_magneton_vs_quilava_speed_control_001", ids
        )
        self.assertIn("fixture_misty_starmie_vs_meganium_recover_tempo_001", ids)
        self.assertIn("fixture_clair_dragonair_vs_suicune_hidden_ice_001", ids)
        self.assertIn("fixture_bugsy_ariados_vs_pidgey_status_clock_001", ids)
        self.assertIn(
            "external_gsc_forretress_vs_curselax_status_before_hazards_001",
            ids,
        )
        self.assertIn("fixture_morty_gengar_vs_kadabra_destiny_bond_001", ids)

    def test_public_cards_do_not_expose_oracle_labels(self) -> None:
        benchmarks = load_benchmarks()
        oracles = load_benchmark_oracles()
        oracle_ids = {row["id"] for row in oracles}

        for benchmark in benchmarks:
            with self.subTest(benchmark=benchmark["id"]):
                self.assertIn(benchmark["id"], oracle_ids)
                self.assertIn("position_snapshot", benchmark)
                self.assertIn("candidate_moves_public", benchmark)
                self.assertNotIn("candidate_moves", benchmark)
                self.assertNotIn("catastrophe_branch", benchmark)
                self.assertNotIn("information_that_changes_answer", benchmark)
                self.assertNotIn("arbitration", benchmark)
                opponent_tiers = set(benchmark["public_opponent_model"])
                self.assertLessEqual(REQUIRED_OPPONENT_TIERS, opponent_tiers)
                for move in benchmark["candidate_moves_public"]:
                    self.assertNotIn("label", move)
                    self.assertNotIn("reason", move)

    def test_hidden_oracles_require_move_labels_and_explanations(self) -> None:
        oracles = load_benchmark_oracles()

        for row in oracles:
            with self.subTest(benchmark=row["id"]):
                oracle = row["oracle"]

                self.assertLessEqual(REQUIRED_OUTCOME_LABELS, set(oracle))
                for label in REQUIRED_OUTCOME_LABELS:
                    self.assertTrue(oracle[label])
                self.assertTrue(oracle["catastrophe_branches"][0]["trigger"])
                self.assertTrue(oracle["catastrophe_branches"][0]["consequence"])
                self.assertTrue(oracle["answer_changing_information"])

    def test_validator_rejects_missing_labels_and_opponent_tiers(self) -> None:
        public_data = {
            "schema_version": 1,
            "cards": [
                {
                    "id": "invalid_policy_position",
                    "version": 1,
                    "split": "seed",
                    "mechanics_profile": "vanilla_gsc",
                    "source_refs": ["unit-test"],
                    "tags": ["sleep"],
                    "position_snapshot": {},
                    "candidate_moves_public": [
                        {"id": "move_sleep_powder", "label": "best"}
                    ],
                    "required_answer_fields": ["chosen_move_id"],
                    "hidden_info_visible_to_policy": {},
                    "public_opponent_model": {},
                }
            ],
        }
        oracle_data = {
            "schema_version": 1,
            "oracles": [
                {
                    "id": "invalid_policy_position",
                    "oracle": {
                        "best": ["move_sleep_powder"],
                        "acceptable": [],
                        "catastrophic": [],
                    },
                }
            ],
        }

        public_errors = validate_public_card_data(public_data)
        oracle_errors = validate_oracle_data(oracle_data)

        self.assertTrue(
            any("oracle label field leaked" in error for error in public_errors)
        )
        self.assertTrue(
            any("missing oracle field(s)" in error for error in oracle_errors)
        )

    def test_report_without_answers_is_a_contract_not_policy_pass(self) -> None:
        report = build_benchmark_report(load_benchmarks(), load_benchmark_oracles())

        self.assertTrue(report["benchmark_contract_ready"])
        self.assertFalse(report["policy_evaluated"])
        self.assertFalse(report["policy_passes"])
        self.assertEqual(
            report["split_counts"],
            {"fixture_harvest": 24, "holdout": 15, "seed": 5},
        )
        self.assertEqual(report["outcome_counts"], {"unanswered": 44})
        self.assertEqual(
            report["outcomes_by_split"],
            {
                "fixture_harvest": {"unanswered": 24},
                "holdout": {"unanswered": 15},
                "seed": {"unanswered": 5},
            },
        )

    def test_report_scores_best_acceptable_and_catastrophic_answers(self) -> None:
        benchmarks = load_benchmarks()

        best_report = build_benchmark_report(
            benchmarks,
            load_benchmark_oracles(),
            answers={
                "vanilla_gsc_sleep_setup_disruption_001": "move_sleep_powder",
                "romhack_spikes_third_layer_janine_001": "move_spikes",
                "romhack_spikes_fourth_click_janine_001": "move_sludge_bomb",
                "romhack_explosion_route_trade_brock_001": "move_explosion",
                "romhack_defensive_answer_preservation_pryce_001": "switch_piloswine",
                "vanilla_gsc_sleep_clause_blocked_holdout_001": "move_sludge_bomb",
                "romhack_spikes_public_spinner_holdout_001": "move_explosion",
                "romhack_spikes_maxed_explosion_conversion_holdout_001": "move_explosion",
                "romhack_explosion_blocked_by_protect_holdout_001": "switch_omastar",
                "romhack_defensive_answer_unavailable_holdout_001": "move_thunder_wave",
                "fixture_chuck_poliwrath_vs_pidgeotto_ice_punch_001": "switch_sudowoodo",
                "fixture_janine_qwilfish_third_spikes_layer_001": "move_spikes",
                "fixture_mechanics_snorlax_full_hp_rest_status_fail_001": "move_body_slam",
                "fixture_brock_golem_vs_vaporeon_explosion_question_001": "move_explosion",
                "long_battle_sleep_disruption_after_miss_001": "move_sleep_powder",
                "long_battle_rest_tempo_unforced_001": "move_body_slam",
                "romhack_spinblock_damage_context_001": "move_thunderbolt",
                "vanilla_gsc_phazing_timing_mirror_001": "move_rock_slide",
                "vanilla_gsc_pp_phaze_loop_save_final_whirlwind_001": "move_rest",
                "external_gsc_sleeping_lax_curse_window_001": "move_curse",
                "vanilla_gsc_opening_electric_double_switch_spikes_001": "switch_cloyster",
                "external_gsc_forretress_explosion_on_quagsire_001": "move_explosion",
                "external_gsc_vaporeon_vs_restdtalk_snorlax_001": "move_surf",
                "external_gsc_golem_late_rapid_spin_001": "move_rapid_spin",
                "fixture_will_slowbro_vs_houndoom_fast_dark_001": "switch_houndoom",
                "fixture_koga_ariados_vs_typhlosion_fire_spikes_001": "switch_tentacruel",
                "fixture_bugsy_scyther_vs_geodude_safe_swords_dance_001": "move_swords_dance",
                "fixture_chuck_poliwrath_vs_alakazam_psychic_pivot_001": "switch_umbreon",
                "fixture_morty_haunter_vs_noctowl_sleep_line_001": "move_hypnosis",
                "fixture_falkner_pidgeotto_vs_geodude_scout_probe_001": "move_sand_attack",
                "fixture_pryce_cloyster_vs_quilava_fire_pivot_001": "switch_slowking",
                "fixture_bugsy_scyther_vs_quilava_fire_setup_001": "move_swords_dance",
                "fixture_whitney_miltank_vs_geodude_rollout_lock_001": "move_body_slam",
                "fixture_karen_crobat_vs_dragonite_toxic_clock_001": "move_toxic",
                "fixture_koga_crobat_vs_alakazam_immediate_ko_001": "move_wing_attack",
                "fixture_jasmine_skarmory_vs_machoke_focus_energy_001": "move_toxic",
                "fixture_morty_misdreavus_vs_typhlosion_perish_route_001": "move_perish_song",
                "fixture_whitney_clefairy_vs_bayleef_encore_reflect_001": "move_encore",
                "fixture_jasmine_magneton_vs_quilava_speed_control_001": "move_thunder_wave",
                "fixture_misty_starmie_vs_meganium_recover_tempo_001": "move_psychic",
                "fixture_clair_dragonair_vs_suicune_hidden_ice_001": "switch_kingdra",
                "fixture_bugsy_ariados_vs_pidgey_status_clock_001": "move_toxic",
                "external_gsc_forretress_vs_curselax_status_before_hazards_001": "move_toxic",
                "fixture_morty_gengar_vs_kadabra_destiny_bond_001": "move_shadow_ball",
            },
        )
        mixed_report = build_benchmark_report(
            benchmarks,
            load_benchmark_oracles(),
            answers={
                "vanilla_gsc_sleep_setup_disruption_001": "move_sludge_bomb",
                "romhack_spikes_third_layer_janine_001": "switch_tentacruel",
                "romhack_spikes_fourth_click_janine_001": "missing_move",
            },
        )

        self.assertTrue(best_report["policy_passes"])
        self.assertEqual(best_report["outcome_counts"], {"best": 44})
        self.assertFalse(mixed_report["policy_passes"])
        self.assertEqual(
            mixed_report["outcome_counts"],
            {
                "acceptable": 1,
                "catastrophic": 1,
                "unanswered": 41,
                "unknown_move": 1,
            },
        )

    def test_write_benchmark_report_writes_markdown_and_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "benchmarks.md"
            json_out_path = Path(tmpdir) / "benchmarks.json"

            report = write_benchmark_report(
                out_path=out_path,
                json_out_path=json_out_path,
            )

            self.assertEqual(report["benchmark_count"], 44)
            self.assertIn(
                "State-Transition Benchmark Report",
                out_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                '"benchmark_count": 44',
                json_out_path.read_text(encoding="utf-8"),
            )

    def test_baseline_policy_passes_initial_state_transition_benchmarks(self) -> None:
        benchmarks = load_benchmarks()
        policy = build_benchmark_policy_answers(benchmarks)
        answers = {
            row["benchmark_id"]: row["chosen_move_id"]
            for row in policy["answers"]
        }
        report = build_benchmark_report(
            benchmarks,
            load_benchmark_oracles(),
            answers=answers,
        )

        self.assertTrue(report["policy_evaluated"])
        self.assertTrue(report["policy_passes"])
        self.assertEqual(report["outcome_counts"], {"best": 44})
        self.assertEqual(
            report["split_passes"],
            {"fixture_harvest": True, "holdout": True, "seed": True},
        )

    def test_write_policy_answers_round_trips_into_report(self) -> None:
        benchmarks = load_benchmarks()
        with TemporaryDirectory() as tmpdir:
            answers_path = Path(tmpdir) / "policy_answers.json"

            policy = write_benchmark_policy_answers(out_path=answers_path)
            answers = load_benchmark_answers(answers_path)
            report = build_benchmark_report(
                benchmarks,
                load_benchmark_oracles(),
                answers=answers,
            )

            self.assertEqual(len(policy["answers"]), 44)
            self.assertEqual(len(answers), 44)
            self.assertTrue(report["policy_passes"])
            self.assertFalse(validate_policy_answer_data(policy))
            for row in policy["answers"]:
                self.assertTrue(row["current_win_conditions"])
                self.assertTrue(row["irreplaceable_pieces"])
                self.assertTrue(row["catastrophe_branches"])
                self.assertTrue(row["answer_changing_information"])
                self.assertTrue(row["rules_fired"])

    def test_policy_answer_validator_rejects_empty_route_fields(self) -> None:
        data = {
            "schema_version": 1,
            "generated_at": "2026-05-13T00:00:00+00:00",
            "policy_name": "unit_test_policy",
            "answers": [
                {
                    "benchmark_id": "unit_test_card",
                    "policy_version": "unit_test_policy",
                    "mechanics_profile_seen": "vanilla_gsc",
                    "state_hash": "sha256:abc",
                    "decision_status": "action",
                    "chosen_move_id": "move_spikes",
                    "confidence": 0.5,
                    "candidate_ranking": [{"action": "move_spikes", "rank": 1}],
                    "current_win_conditions": [],
                    "irreplaceable_pieces": [],
                    "catastrophe_branches": [],
                    "answer_changing_information": [],
                    "rules_fired": [],
                }
            ],
        }

        errors = validate_policy_answer_data(data)

        self.assertTrue(
            any("current_win_conditions must be non-empty" in error for error in errors)
        )
        self.assertTrue(
            any("irreplaceable_pieces must be non-empty" in error for error in errors)
        )

    def test_baseline_policy_reacts_to_answer_changing_information(self) -> None:
        benchmarks = {benchmark["id"]: benchmark for benchmark in load_benchmarks()}

        blocked_sleep = deepcopy(
            benchmarks["vanilla_gsc_sleep_setup_disruption_001"]
        )
        blocked_sleep["position_snapshot"]["field"]["sleep_clause"] = "occupied"
        self.assertEqual(
            choose_benchmark_policy_move(blocked_sleep)["chosen_move_id"],
            "move_sludge_bomb",
        )

        maxed_spikes = deepcopy(
            benchmarks["romhack_spikes_third_layer_janine_001"]
        )
        maxed_spikes["position_snapshot"]["field"]["player_side_spikes_layers"] = 3
        self.assertNotEqual(
            choose_benchmark_policy_move(maxed_spikes)["chosen_move_id"],
            "move_spikes",
        )

        protect_explosion = deepcopy(
            benchmarks["romhack_explosion_route_trade_brock_001"]
        )
        protect_explosion["position_snapshot"]["opponent_active"]["revealed_moves"] = [
            "Surf",
            "Protect",
        ]
        self.assertEqual(
            choose_benchmark_policy_move(protect_explosion)["chosen_move_id"],
            "switch_omastar",
        )

        missing_pivot = deepcopy(
            benchmarks["romhack_defensive_answer_preservation_pryce_001"]
        )
        missing_pivot["position_snapshot"]["boss_bench"] = ["Cloyster", "Slowking"]
        self.assertEqual(
            choose_benchmark_policy_move(missing_pivot)["chosen_move_id"],
            "move_thunder_wave",
        )

        full_hp_rest = deepcopy(
            benchmarks["fixture_mechanics_snorlax_full_hp_rest_status_fail_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(full_hp_rest)["chosen_move_id"],
            "move_body_slam",
        )

        missing_sudowoodo = deepcopy(
            benchmarks["fixture_chuck_poliwrath_vs_pidgeotto_ice_punch_001"]
        )
        missing_sudowoodo["position_snapshot"]["boss_bench"] = [
            "Hitmontop",
            "Hitmonlee",
            "Umbreon",
        ]
        self.assertEqual(
            choose_benchmark_policy_move(missing_sudowoodo)["chosen_move_id"],
            "move_ice_punch",
        )

        spinblock = deepcopy(
            benchmarks["romhack_spinblock_damage_context_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(spinblock)["chosen_move_id"],
            "move_thunderbolt",
        )
        spinblock["position_snapshot"]["boss_active"]["hp"] = "38%"
        spinblock["position_snapshot"]["boss_active"]["current_hp"] = 52
        band = spinblock["position_snapshot"]["damage_bands"][
            "opponent_psychic_vs_boss_active"
        ]
        band["defender_current_hp"] = 52
        band["ko_at_current_hp"] = "guaranteed"
        spinblock["public_opponent_model"]["immediate_punish"] = (
            "Starmie is faster and Psychic is a guaranteed KO into the current "
            "Gengar HP before Thunderbolt can fire."
        )
        self.assertEqual(
            choose_benchmark_policy_move(spinblock)["chosen_move_id"],
            "switch_raikou",
        )

        phazing = deepcopy(
            benchmarks["vanilla_gsc_phazing_timing_mirror_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(phazing)["chosen_move_id"],
            "move_rock_slide",
        )
        phazing["position_snapshot"]["mechanics"]["boss_phaze_order"] = (
            "after_opponent_phaze"
        )
        phazing["position_snapshot"]["boss_active"]["speed_relation"] = (
            "slower_than_opponent_within_negative_priority"
        )
        self.assertEqual(
            choose_benchmark_policy_move(phazing)["chosen_move_id"],
            "move_roar",
        )

        pp_endgame = deepcopy(
            benchmarks["vanilla_gsc_pp_phaze_loop_save_final_whirlwind_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(pp_endgame)["chosen_move_id"],
            "move_rest",
        )
        pp_endgame["position_snapshot"]["mechanics"]["immediate_setup_route"] = True
        pp_endgame["position_snapshot"]["opponent_active"]["boosts"] = {
            "atk": 3,
            "def": 3,
            "spe": -3,
        }
        pp_endgame["public_opponent_model"]["immediate_punish"] = (
            "Snorlax is already boosted enough that one more unchecked turn "
            "creates an unanswerable Curse route; spending the final Whirlwind "
            "PP is now justified."
        )
        self.assertEqual(
            choose_benchmark_policy_move(pp_endgame)["chosen_move_id"],
            "move_whirlwind",
        )

        sleep_window = deepcopy(
            benchmarks["external_gsc_sleeping_lax_curse_window_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(sleep_window)["chosen_move_id"],
            "move_curse",
        )
        sleep_window["position_snapshot"]["opponent_active"]["status"] = "none"
        sleep_window["position_snapshot"]["mechanics"]["sleep_window_available"] = False
        sleep_window["public_opponent_model"]["immediate_punish"] = (
            "Snorlax is awake and can attack immediately, so Curse no longer "
            "gets the free setup window that changed the KO math."
        )
        self.assertEqual(
            choose_benchmark_policy_move(sleep_window)["chosen_move_id"],
            "move_earthquake",
        )

        opening_bid = deepcopy(
            benchmarks["vanilla_gsc_opening_electric_double_switch_spikes_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(opening_bid)["chosen_move_id"],
            "switch_cloyster",
        )
        opening_bid["position_snapshot"]["mechanics"][
            "double_switch_spikes_window"
        ] = False
        opening_bid["position_snapshot"]["mechanics"]["opening_reveal_value"] = False
        opening_bid["position_snapshot"]["mechanics"][
            "opening_direct_pressure_needed"
        ] = True
        opening_bid["position_snapshot"]["mechanics"]["opponent_switch_incentive"] = (
            "low"
        )
        opening_bid["public_opponent_model"]["immediate_punish"] = (
            "Cloyster is not forced out and can stay to set Spikes; "
            "double-switching now gives the opponent the hazard turn for free."
        )
        self.assertEqual(
            choose_benchmark_policy_move(opening_bid)["chosen_move_id"],
            "move_thunder",
        )

        real_boom = deepcopy(
            benchmarks["external_gsc_forretress_explosion_on_quagsire_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(real_boom)["chosen_move_id"],
            "move_explosion",
        )
        real_boom["position_snapshot"]["opponent_active"]["revealed_moves"] = [
            "Surf",
            "Protect",
        ]
        real_boom["public_opponent_model"]["immediate_punish"] = (
            "Protect is publicly revealed, so Explosion can be blanked while "
            "Forretress faints and the route trade fails."
        )
        self.assertEqual(
            choose_benchmark_policy_move(real_boom)["chosen_move_id"],
            "switch_snorlax",
        )

        resttalk = deepcopy(
            benchmarks["external_gsc_vaporeon_vs_restdtalk_snorlax_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(resttalk)["chosen_move_id"],
            "move_surf",
        )
        resttalk["position_snapshot"]["opponent_active"]["revealed_moves"] = [
            "Curse",
            "Double-Edge",
        ]
        resttalk["position_snapshot"]["mechanics"][
            "sleep_talk_rest_branch"
        ] = False
        resttalk["position_snapshot"]["mechanics"][
            "setup_changes_ko_math"
        ] = True
        resttalk["public_opponent_model"]["immediate_punish"] = (
            "Snorlax is asleep without public Sleep Talk or RestTalk evidence, "
            "so Growth can use the sleep window to change the Surf conversion math."
        )
        self.assertEqual(
            choose_benchmark_policy_move(resttalk)["chosen_move_id"],
            "move_growth",
        )

        late_spin = deepcopy(benchmarks["external_gsc_golem_late_rapid_spin_001"])
        self.assertEqual(
            choose_benchmark_policy_move(late_spin)["chosen_move_id"],
            "move_rapid_spin",
        )
        late_spin["position_snapshot"]["field"]["boss_side_spikes"] = "none"
        late_spin["position_snapshot"]["mechanics"]["own_hazards_present"] = False
        late_spin["public_opponent_model"]["immediate_punish"] = (
            "There are no own-side Spikes to remove, so Rapid Spin becomes "
            "low-value and Golem should pressure the Resting Snorlax directly."
        )
        self.assertEqual(
            choose_benchmark_policy_move(late_spin)["chosen_move_id"],
            "move_earthquake",
        )

        fast_dark = deepcopy(
            benchmarks["fixture_will_slowbro_vs_houndoom_fast_dark_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(fast_dark)["chosen_move_id"],
            "switch_houndoom",
        )
        fast_dark["position_snapshot"]["boss_bench"] = [
            "Forretress",
            "Starmie",
            "Alakazam",
            "Xatu",
        ]
        self.assertEqual(
            choose_benchmark_policy_move(fast_dark)["chosen_move_id"],
            "move_surf",
        )

        fire_pressure = deepcopy(
            benchmarks["fixture_koga_ariados_vs_typhlosion_fire_spikes_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(fire_pressure)["chosen_move_id"],
            "switch_tentacruel",
        )
        fire_pressure["position_snapshot"]["boss_bench"] = [
            "Muk",
            "Nidoking",
            "Umbreon",
            "Crobat",
        ]
        self.assertEqual(
            choose_benchmark_policy_move(fire_pressure)["chosen_move_id"],
            "switch_umbreon",
        )

        safe_setup = deepcopy(
            benchmarks["fixture_bugsy_scyther_vs_geodude_safe_swords_dance_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(safe_setup)["chosen_move_id"],
            "move_swords_dance",
        )
        safe_setup["position_snapshot"]["boss_active"]["hp"] = "70%"
        safe_setup["position_snapshot"]["mechanics"][
            "setup_survives_worst_plausible_branch"
        ] = False
        safe_setup["position_snapshot"]["damage_bands"][
            "opponent_rock_throw_vs_boss_active"
        ]["ko_at_current_hp"] = "guaranteed"
        safe_setup["public_opponent_model"]["immediate_punish"] = (
            "Geodude's plausible Rock Throw now KOs after the setup turn, "
            "so Swords Dance loses the boosted route before it can convert."
        )
        self.assertEqual(
            choose_benchmark_policy_move(safe_setup)["chosen_move_id"],
            "move_wing_attack",
        )

        psychic_pivot = deepcopy(
            benchmarks["fixture_chuck_poliwrath_vs_alakazam_psychic_pivot_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(psychic_pivot)["chosen_move_id"],
            "switch_umbreon",
        )
        psychic_pivot["position_snapshot"]["boss_bench"] = [
            "Sudowoodo",
            "Hitmontop",
            "Hitmonlee",
        ]
        self.assertEqual(
            choose_benchmark_policy_move(psychic_pivot)["chosen_move_id"],
            "move_hypnosis",
        )

        morty_sleep = deepcopy(
            benchmarks["fixture_morty_haunter_vs_noctowl_sleep_line_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(morty_sleep)["chosen_move_id"],
            "move_hypnosis",
        )
        morty_sleep["position_snapshot"]["field"]["sleep_clause"] = "occupied"
        self.assertEqual(
            choose_benchmark_policy_move(morty_sleep)["chosen_move_id"],
            "move_night_shade",
        )

        scout_probe = deepcopy(
            benchmarks["fixture_falkner_pidgeotto_vs_geodude_scout_probe_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(scout_probe)["chosen_move_id"],
            "move_sand_attack",
        )
        scout_probe["position_snapshot"]["mechanics"]["public_probe_needed"] = False
        scout_probe["public_opponent_model"]["immediate_punish"] = (
            "Geodude has no meaningful public Rock-risk branch in this mutation, "
            "so Sand Attack no longer buys enough safety to beat direct Gust progress."
        )
        self.assertEqual(
            choose_benchmark_policy_move(scout_probe)["chosen_move_id"],
            "move_gust",
        )

        fire_pivot = deepcopy(
            benchmarks["fixture_pryce_cloyster_vs_quilava_fire_pivot_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(fire_pivot)["chosen_move_id"],
            "switch_slowking",
        )
        fire_pivot["position_snapshot"]["boss_active"]["hp"] = "88%"
        fire_pivot["position_snapshot"]["mechanics"][
            "active_faints_before_progress"
        ] = False
        fire_pivot["position_snapshot"]["mechanics"][
            "active_survives_public_punish"
        ] = True
        fire_pivot["position_snapshot"]["damage_bands"][
            "opponent_flame_wheel_vs_boss_active"
        ]["ko_at_current_hp"] = "never"
        fire_pivot["public_opponent_model"]["immediate_punish"] = (
            "Cloyster now survives the public Flame Wheel branch, so Surf can "
            "punish Quilava without spending the future Explosion/Spikes resource "
            "or needing the Slowking pivot first."
        )
        self.assertEqual(
            choose_benchmark_policy_move(fire_pivot)["chosen_move_id"],
            "move_surf",
        )

        fire_setup = deepcopy(
            benchmarks["fixture_bugsy_scyther_vs_quilava_fire_setup_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(fire_setup)["chosen_move_id"],
            "move_swords_dance",
        )
        fire_setup["position_snapshot"]["boss_active"]["hp"] = "45%"
        fire_setup["position_snapshot"]["mechanics"][
            "setup_survives_worst_plausible_branch"
        ] = False
        fire_setup["position_snapshot"]["damage_bands"][
            "opponent_ember_vs_boss_active"
        ]["ko_at_current_hp"] = "guaranteed"
        fire_setup["public_opponent_model"]["immediate_punish"] = (
            "Quilava's revealed Ember now removes Scyther after a setup turn, "
            "so Swords Dance loses the boosted route before it converts and "
            "Wing Attack is the best forced progress."
        )
        self.assertEqual(
            choose_benchmark_policy_move(fire_setup)["chosen_move_id"],
            "move_wing_attack",
        )

        rollout_lock = deepcopy(
            benchmarks["fixture_whitney_miltank_vs_geodude_rollout_lock_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(rollout_lock)["chosen_move_id"],
            "move_body_slam",
        )
        rollout_lock["position_snapshot"]["opponent_active"]["status"] = "par"
        rollout_lock["position_snapshot"]["mechanics"]["lock_move_safe"] = True
        rollout_lock["position_snapshot"]["mechanics"][
            "lock_after_status_or_safe_state"
        ] = True
        rollout_lock["public_opponent_model"]["immediate_punish"] = (
            "Geodude is now paralyzed and Miltank remains healthy, so the taught "
            "pressure line can switch from Body Slam setup pressure to Rollout "
            "lock conversion."
        )
        self.assertEqual(
            choose_benchmark_policy_move(rollout_lock)["chosen_move_id"],
            "move_rollout",
        )

        toxic_clock = deepcopy(
            benchmarks["fixture_karen_crobat_vs_dragonite_toxic_clock_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(toxic_clock)["chosen_move_id"],
            "move_toxic",
        )
        toxic_clock["position_snapshot"]["boss_active"]["hp"] = "38%"
        toxic_clock["position_snapshot"]["mechanics"][
            "status_clock_survives_punish"
        ] = False
        toxic_clock["position_snapshot"]["damage_bands"][
            "opponent_outrage_vs_boss_active"
        ]["ko_at_current_hp"] = "guaranteed"
        toxic_clock["public_opponent_model"]["immediate_punish"] = (
            "Dragonite's revealed Outrage now removes Crobat after the status "
            "attempt, so Karen should preserve the status pivot and use "
            "Tyranitar as the anti-Dragon route."
        )
        self.assertEqual(
            choose_benchmark_policy_move(toxic_clock)["chosen_move_id"],
            "switch_tyranitar",
        )

        immediate_ko = deepcopy(
            benchmarks["fixture_koga_crobat_vs_alakazam_immediate_ko_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(immediate_ko)["chosen_move_id"],
            "move_wing_attack",
        )
        immediate_ko["position_snapshot"]["opponent_active"]["hp"] = "84%"
        immediate_ko["position_snapshot"]["mechanics"]["direct_ko_available"] = False
        immediate_ko["position_snapshot"]["damage_bands"][
            "boss_wing_attack_vs_opponent_active"
        ]["ko_at_current_hp"] = "never"
        immediate_ko["public_opponent_model"]["immediate_punish"] = (
            "Wing Attack no longer removes Alakazam before Psychic or Recover "
            "pressure, so Koga should preserve Crobat and use Umbreon as the "
            "clean public answer."
        )
        self.assertEqual(
            choose_benchmark_policy_move(immediate_ko)["chosen_move_id"],
            "switch_umbreon",
        )

        weak_setup = deepcopy(
            benchmarks["fixture_jasmine_skarmory_vs_machoke_focus_energy_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(weak_setup)["chosen_move_id"],
            "move_toxic",
        )
        weak_setup["position_snapshot"]["opponent_active"]["revealed_moves"] = [
            "Attack-boosting setup",
            "Karate Chop",
        ]
        weak_setup["position_snapshot"]["mechanics"]["weak_setup_signal"] = False
        weak_setup["position_snapshot"]["mechanics"][
            "phazing_required_for_boost"
        ] = True
        weak_setup["public_opponent_model"]["immediate_punish"] = (
            "Machoke now has a real attack-boost route rather than only "
            "Focus Energy, so Whirlwind should deny the boost before Toxic or "
            "Steel Wing can convert."
        )
        self.assertEqual(
            choose_benchmark_policy_move(weak_setup)["chosen_move_id"],
            "move_whirlwind",
        )

        perish_route = deepcopy(
            benchmarks["fixture_morty_misdreavus_vs_typhlosion_perish_route_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(perish_route)["chosen_move_id"],
            "move_perish_song",
        )
        perish_route["position_snapshot"]["boss_active"]["hp"] = "38%"
        perish_route["position_snapshot"]["mechanics"][
            "perish_route_survives_punish"
        ] = False
        perish_route["position_snapshot"]["damage_bands"][
            "opponent_flame_wheel_vs_boss_active"
        ]["ko_at_current_hp"] = "guaranteed"
        perish_route["public_opponent_model"]["immediate_punish"] = (
            "Typhlosion's revealed Flame Wheel now removes Misdreavus before "
            "Perish Song can start, so Morty should preserve through Gengar "
            "instead of trying to create the clock."
        )
        self.assertEqual(
            choose_benchmark_policy_move(perish_route)["chosen_move_id"],
            "switch_gengar",
        )

        encore_route = deepcopy(
            benchmarks["fixture_whitney_clefairy_vs_bayleef_encore_reflect_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(encore_route)["chosen_move_id"],
            "move_encore",
        )
        encore_route["position_snapshot"]["field"]["player_last_move"] = "Razor Leaf"
        encore_route["position_snapshot"]["mechanics"]["encore_trap_live"] = False
        encore_route["public_opponent_model"]["immediate_punish"] = (
            "Bayleef no longer has a visible low-value Reflect last move to trap, "
            "so Encore becomes speculative and Clefairy should use one Double "
            "Team setup turn while the public hit is survivable."
        )
        self.assertEqual(
            choose_benchmark_policy_move(encore_route)["chosen_move_id"],
            "move_double_team",
        )

        speed_control = deepcopy(
            benchmarks["fixture_jasmine_magneton_vs_quilava_speed_control_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(speed_control)["chosen_move_id"],
            "move_thunder_wave",
        )
        speed_control["position_snapshot"]["opponent_active"]["hp"] = "24%"
        speed_control["position_snapshot"]["mechanics"]["direct_ko_available"] = True
        speed_control["position_snapshot"]["damage_bands"][
            "boss_thunderbolt_vs_opponent_active"
        ]["ko_at_current_hp"] = "guaranteed"
        speed_control["public_opponent_model"]["immediate_punish"] = (
            "Quilava is now low enough that Thunderbolt removes the active "
            "threat before speed-control status needs to buy future turns."
        )
        self.assertEqual(
            choose_benchmark_policy_move(speed_control)["chosen_move_id"],
            "move_thunderbolt",
        )

        recover_tempo = deepcopy(
            benchmarks["fixture_misty_starmie_vs_meganium_recover_tempo_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(recover_tempo)["chosen_move_id"],
            "move_psychic",
        )
        recover_tempo["position_snapshot"]["opponent_active"]["status"] = "sleep"
        recover_tempo["position_snapshot"]["mechanics"][
            "recovery_window_live"
        ] = True
        recover_tempo["position_snapshot"]["mechanics"][
            "tempo_attack_changes_route"
        ] = False
        recover_tempo["public_opponent_model"]["immediate_punish"] = (
            "Meganium is asleep this turn and Psychic no longer changes the "
            "Lapras cleanup band, so Recover preserves Starmie before the next "
            "re-score."
        )
        self.assertEqual(
            choose_benchmark_policy_move(recover_tempo)["chosen_move_id"],
            "move_recover",
        )

        hidden_ice = deepcopy(
            benchmarks["fixture_clair_dragonair_vs_suicune_hidden_ice_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(hidden_ice)["chosen_move_id"],
            "switch_kingdra",
        )
        hidden_ice["position_snapshot"]["opponent_active"]["public_priors"] = [
            "Rest plausible",
            "Suicune likely pivots out",
        ]
        hidden_ice["position_snapshot"]["mechanics"][
            "hidden_coverage_punish_plausible"
        ] = False
        hidden_ice["public_opponent_model"]["immediate_punish"] = (
            "Suicune no longer has a plausible public Ice punish into "
            "Dragonair, so Thunder can claim direct pressure instead of "
            "pivoting first."
        )
        self.assertEqual(
            choose_benchmark_policy_move(hidden_ice)["chosen_move_id"],
            "move_thunder",
        )

        bugsy_clock = deepcopy(
            benchmarks["fixture_bugsy_ariados_vs_pidgey_status_clock_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(bugsy_clock)["chosen_move_id"],
            "move_toxic",
        )
        bugsy_clock["position_snapshot"]["opponent_active"]["status"] = "tox"
        bugsy_clock["position_snapshot"]["mechanics"][
            "status_clock_survives_punish"
        ] = False
        bugsy_clock["public_opponent_model"]["immediate_punish"] = (
            "Pidgey is already toxic, so repeating Toxic no longer creates "
            "progress; Ariados can preserve its HP and bring Scyther in after "
            "the clock exists."
        )
        self.assertEqual(
            choose_benchmark_policy_move(bugsy_clock)["chosen_move_id"],
            "switch_scyther",
        )

        sacrifice_trade = deepcopy(
            benchmarks["fixture_morty_gengar_vs_kadabra_destiny_bond_001"]
        )
        self.assertEqual(
            choose_benchmark_policy_move(sacrifice_trade)["chosen_move_id"],
            "move_shadow_ball",
        )
        sacrifice_trade["position_snapshot"]["opponent_active"]["hp"] = "91%"
        sacrifice_trade["position_snapshot"]["mechanics"][
            "direct_ko_available"
        ] = False
        sacrifice_trade["position_snapshot"]["mechanics"][
            "sacrifice_trade_forced"
        ] = True
        sacrifice_trade["position_snapshot"]["damage_bands"][
            "boss_shadow_ball_vs_opponent_active"
        ]["ko_at_current_hp"] = "never"
        sacrifice_trade["public_opponent_model"]["immediate_punish"] = (
            "Kadabra is now outside Shadow Ball removal range and can KO "
            "Gengar after surviving, so Destiny Bond becomes the forced route "
            "trade instead of a wasteful sacrifice."
        )
        self.assertEqual(
            choose_benchmark_policy_move(sacrifice_trade)["chosen_move_id"],
            "move_destiny_bond",
        )

    def test_mutation_report_covers_answer_flip_boundaries(self) -> None:
        report = build_benchmark_mutation_report(load_benchmarks())

        self.assertEqual(report["mutation_count"], 36)
        self.assertEqual(report["pass_count"], 36)
        self.assertEqual(report["policy_flip_count"], 36)
        self.assertTrue(report["all_mutations_pass"])
        self.assertTrue(report["all_mutations_flip"])
        mutation_ids = {row["mutation_id"] for row in report["mutations"]}
        self.assertIn("mut_sleep_clause_occupied_blocks_sleep_001", mutation_ids)
        self.assertIn("mut_long_battle_sleep_clause_blocks_rescore_001", mutation_ids)
        self.assertIn("mut_spikes_layer_2_to_max_001", mutation_ids)
        self.assertIn("mut_explosion_blocked_by_protect_001", mutation_ids)
        self.assertIn("mut_long_battle_rest_becomes_forced_001", mutation_ids)
        self.assertIn("mut_spinblock_damage_survival_to_ko_001", mutation_ids)
        self.assertIn("mut_phazing_order_faster_to_slower_001", mutation_ids)
        self.assertIn("mut_final_phaze_pp_setup_pressure_001", mutation_ids)
        self.assertIn("mut_sleep_window_target_awake_001", mutation_ids)
        self.assertIn("mut_opening_double_switch_to_direct_pressure_001", mutation_ids)
        self.assertIn("mut_external_boom_blocked_by_protect_001", mutation_ids)
        self.assertIn("mut_restdtalk_branch_absent_setup_window_001", mutation_ids)
        self.assertIn("mut_late_spin_no_hazards_attack_now_001", mutation_ids)
        self.assertIn("mut_fast_dark_pivot_unavailable_attack_now_001", mutation_ids)
        self.assertIn(
            "mut_fire_preservation_primary_pivot_unavailable_001", mutation_ids
        )
        self.assertIn(
            "mut_safe_setup_window_removed_by_ko_range_001", mutation_ids
        )
        self.assertIn(
            "mut_psychic_pivot_unavailable_sleep_fallback_001", mutation_ids
        )
        self.assertIn("mut_morty_sleep_clause_blocks_hypnosis_001", mutation_ids)
        self.assertIn("mut_falkner_probe_unneeded_attack_now_001", mutation_ids)
        self.assertIn("mut_pryce_cloyster_survives_attack_now_001", mutation_ids)
        self.assertIn("mut_bugsy_fire_setup_window_removed_001", mutation_ids)
        self.assertIn("mut_whitney_rollout_after_status_001", mutation_ids)
        self.assertIn("mut_karen_toxic_clock_no_survival_001", mutation_ids)
        self.assertIn("mut_koga_ko_removed_preserve_umbreon_001", mutation_ids)
        self.assertIn("mut_jasmine_real_boost_requires_whirlwind_001", mutation_ids)
        self.assertIn("mut_morty_perish_route_cannot_survive_001", mutation_ids)
        self.assertIn("mut_whitney_encore_trap_absent_double_team_001", mutation_ids)
        self.assertIn("mut_jasmine_speed_control_to_direct_ko_001", mutation_ids)
        self.assertIn("mut_misty_recovery_window_opens_001", mutation_ids)
        self.assertIn("mut_clair_hidden_ice_absent_attack_now_001", mutation_ids)
        self.assertIn("mut_bugsy_status_clock_already_started_001", mutation_ids)
        self.assertIn(
            "mut_morty_direct_removal_absent_destiny_bond_001", mutation_ids
        )
        for row in report["mutations"]:
            self.assertNotEqual(
                row["base_chosen_move_id"],
                row["mutated_chosen_move_id"],
            )
            self.assertFalse(row["validation_errors"])

    def test_write_mutation_report_writes_markdown_and_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "mutations.md"
            json_out_path = Path(tmpdir) / "mutations.json"

            report = write_benchmark_mutation_report(
                out_path=out_path,
                json_out_path=json_out_path,
            )

            self.assertTrue(report["all_mutations_pass"])
            self.assertIn(
                "State-Transition Mutation Report",
                out_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                '"mutation_count": 36',
                json_out_path.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
