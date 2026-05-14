from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.boss_ai_preference.expert_play_research import (
    build_expert_play_research_report,
    validate_expert_play_research_report,
    write_expert_play_research_report,
)


class ExpertPlayResearchTests(unittest.TestCase):
    def test_report_contains_source_backed_policy_hooks(self) -> None:
        report = build_expert_play_research_report()

        self.assertFalse(validate_expert_play_research_report(report))
        self.assertGreaterEqual(report["principle_count"], 8)
        ids = {row["id"] for row in report["principles"]}
        self.assertIn("gsc_foresight_over_one_turn_prediction", ids)
        self.assertIn("gsc_bad_matchup_switching_preserves_future_routes", ids)
        self.assertIn("gsc_spikes_need_conversion_support", ids)
        self.assertIn("gsc_sleep_is_temporary_and_resttalk_aware", ids)
        self.assertIn("gsc_opening_moves_are_information_and_resource_bids", ids)
        self.assertIn("gsc_tournament_replays_are_real_state_corpus", ids)
        self.assertIn("gsc_spikes_offense_uses_direct_pressure_and_booms", ids)
        self.assertIn("gsc_damage_thresholds_not_type_slogans", ids)
        self.assertIn("gsc_spikes_are_not_free_passivity", ids)
        self.assertIn("gsc_setup_requires_opening_and_route", ids)
        self.assertIn("gsc_toxic_clock_needs_survivable_transition", ids)
        self.assertIn("risk_reward_direct_removal_beats_slow_clock", ids)
        self.assertIn("gsc_phazing_needs_live_setup_route", ids)
        self.assertIn("gsc_perish_song_is_forced_clock_route", ids)
        self.assertIn("risk_reward_utility_needs_public_branch", ids)
        self.assertIn("prediction_requires_public_information", ids)
        self.assertIn(
            "vanilla_gsc_opening_electric_double_switch_spikes_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "external_gsc_forretress_explosion_on_quagsire_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "external_gsc_vaporeon_vs_restdtalk_snorlax_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "external_gsc_golem_late_rapid_spin_001",
            report["benchmark_hooks"],
        )
        self.assertIn("romhack_spinblock_damage_context_001", report["benchmark_hooks"])
        self.assertIn(
            "vanilla_gsc_phazing_timing_mirror_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "vanilla_gsc_pp_phaze_loop_save_final_whirlwind_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "external_gsc_sleeping_lax_curse_window_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "romhack_defensive_answer_preservation_pryce_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_will_slowbro_vs_houndoom_fast_dark_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_koga_ariados_vs_typhlosion_fire_spikes_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_bugsy_scyther_vs_geodude_safe_swords_dance_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_bugsy_scyther_vs_quilava_fire_setup_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_chuck_poliwrath_vs_alakazam_psychic_pivot_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_morty_haunter_vs_noctowl_sleep_line_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_pryce_cloyster_vs_quilava_fire_pivot_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_whitney_miltank_vs_geodude_rollout_lock_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_karen_crobat_vs_dragonite_toxic_clock_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_koga_crobat_vs_alakazam_immediate_ko_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_jasmine_skarmory_vs_machoke_focus_energy_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_morty_misdreavus_vs_typhlosion_perish_route_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_whitney_clefairy_vs_bayleef_encore_reflect_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_jasmine_magneton_vs_quilava_speed_control_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_misty_starmie_vs_meganium_recover_tempo_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_clair_dragonair_vs_suicune_hidden_ice_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_bugsy_ariados_vs_pidgey_status_clock_001",
            report["benchmark_hooks"],
        )
        self.assertIn(
            "fixture_morty_gengar_vs_kadabra_destiny_bond_001",
            report["benchmark_hooks"],
        )

    def test_validator_rejects_non_smogon_source(self) -> None:
        report = build_expert_play_research_report()
        report["principles"][0] = {
            **report["principles"][0],
            "source": "https://example.com/not-smogon",
        }

        errors = validate_expert_play_research_report(report)

        self.assertTrue(any("source must be a Smogon URL" in error for error in errors))

    def test_write_report_writes_markdown_and_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "expert.md"
            json_out_path = Path(tmpdir) / "expert.json"

            report = write_expert_play_research_report(
                out_path=out_path,
                json_out_path=json_out_path,
            )

            self.assertGreaterEqual(report["principle_count"], 6)
            self.assertIn(
                "Expert Play Research",
                out_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                '"principle_count"',
                json_out_path.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
