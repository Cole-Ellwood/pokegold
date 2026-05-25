from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools.boss_ai_debugger.generators import generate_scenarios
from tools.boss_ai_debugger.rom_switch_materialize import (
    PreferenceDataError,
    format_rom_switch_materialization,
    scenario_expects_switch,
    source_base_switch_threshold,
    switch_materialization_patches,
    switch_observation_status,
    switch_roll_frequency,
    switch_verdict_from_report,
    switch_materialization_state_field,
    validate_manifest_hash,
    validate_switch_materialization_base,
)


class RomSwitchMaterializeTests(unittest.TestCase):
    def test_switch_sack_expectation_detects_switch_best_action(self) -> None:
        scenario = generate_scenarios(family="switch_sack", count=1, seed=1)[0]

        self.assertTrue(scenario_expects_switch(scenario))

    def test_switch_materialization_uses_public_state_patches(self) -> None:
        scenario = generate_scenarios(family="switch_sack", count=1, seed=1)[0]
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in switch_materialization_patches(scenario)
        }

        self.assertEqual(patches[("wOTPartyCount", 0)], 2)
        self.assertEqual(patches[("wPlayerUsedMoves", 0)], 0x59)
        self.assertEqual(patches[("wEnemySwitchMonParam", 0)], 0)

    def test_switch_materialization_backward_compat_without_overrides(self) -> None:
        # No-overrides scenario must produce the same patches as before slice B.
        scenario = {
            "family": "switch_sack",
            "tier": "mid",
            "expectation": {"condition_tags": ["switch_sack", "defensive_sack_owner"]},
        }
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in switch_materialization_patches(scenario)
        }

        # Hardcoded fixture defaults are still in place.
        self.assertEqual(patches[("wBattleMonSpecies", 0)], 0x79)  # STARMIE
        self.assertEqual(patches[("wEnemyMonSpecies", 0)], 0xD3)  # QWILFISH
        self.assertEqual(patches[("wOTPartyMon2Species", 0)], 0x5E)  # GENGAR
        self.assertEqual(patches[("wBattleMonType1", 0)], 0x04)  # GROUND
        self.assertEqual(patches[("wEnemyMonType1", 0)], 0x03)  # POISON
        self.assertEqual(patches[("wEnemyMonType2", 0)], 0x14)  # WATER
        # defensive_sack_owner tag still drives enemy HP to 22.
        self.assertEqual(patches[("wEnemyMonHP", 0)], 0)
        self.assertEqual(patches[("wEnemyMonHP", 1)], 22)
        self.assertEqual(patches[("wEnemyMonMaxHP", 1)], 100)
        # player HP defaults to 80 when active_pressure_converts is not in tags.
        self.assertEqual(patches[("wBattleMonHP", 1)], 80)
        # Status defaults remain 0 (no status) for backward compat.
        self.assertEqual(patches[("wBattleMonStatus", 0)], 0)
        self.assertEqual(patches[("wEnemyMonStatus", 0)], 0)

    def test_switch_materialization_overrides_replace_defaults(self) -> None:
        scenario = {
            "family": "switch_sack",
            "tier": "late",
            "expectation": {"condition_tags": ["switch_sack"]},
            "overrides": {
                "player_species": "MUK",
                "player_type1": "POISON",
                "player_type2": "POISON",
                "player_hp": 55,
                "player_max_hp": 130,
                "enemy_species": "PIKACHU",
                "enemy_type1": "ELECTRIC",
                "enemy_type2": "ELECTRIC",
                "enemy_hp": 40,
                "enemy_max_hp": 90,
                "enemy_bench_species": "TENTACRUEL",
                "enemy_bench_hp": 70,
                "enemy_bench_max_hp": 120,
            },
        }
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in switch_materialization_patches(scenario)
        }

        self.assertEqual(patches[("wBattleMonSpecies", 0)], 0x59)  # MUK
        self.assertEqual(patches[("wBattleMonType1", 0)], 0x03)  # POISON
        self.assertEqual(patches[("wBattleMonType2", 0)], 0x03)
        self.assertEqual(patches[("wBattleMonHP", 1)], 55)
        self.assertEqual(patches[("wBattleMonMaxHP", 1)], 130)
        self.assertEqual(patches[("wEnemyMonSpecies", 0)], 0x19)  # PIKACHU
        self.assertEqual(patches[("wEnemyMonType1", 0)], 0x17)  # ELECTRIC
        self.assertEqual(patches[("wEnemyMonHP", 1)], 40)
        self.assertEqual(patches[("wEnemyMonMaxHP", 1)], 90)
        self.assertEqual(patches[("wOTPartyMon2Species", 0)], 0x49)  # TENTACRUEL
        self.assertEqual(patches[("wOTPartyMon2HP", 1)], 70)
        self.assertEqual(patches[("wOTPartyMon2MaxHP", 1)], 120)
        # Override HP wins over tag-derived HP defaults.

    def test_switch_materialization_accepts_integer_overrides(self) -> None:
        scenario = {
            "family": "switch_sack",
            "tier": "late",
            "expectation": {"condition_tags": ["switch_sack"]},
            "overrides": {
                "player_species": 0x93,  # an arbitrary species id not in the small SPECIES dict
                "enemy_species": 0x5D,  # likewise
                "enemy_bench_species": 0x5E,  # GENGAR by id
            },
        }
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in switch_materialization_patches(scenario)
        }
        self.assertEqual(patches[("wBattleMonSpecies", 0)], 0x93)
        self.assertEqual(patches[("wEnemyMonSpecies", 0)], 0x5D)
        self.assertEqual(patches[("wOTPartyMon2Species", 0)], 0x5E)

    def test_switch_materialization_status_overrides_apply(self) -> None:
        scenario = {
            "family": "switch_sack",
            "tier": "late",
            "expectation": {"condition_tags": ["switch_sack"]},
            "overrides": {"player_status": 16, "enemy_status": 8},  # burn / poison
        }
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in switch_materialization_patches(scenario)
        }
        self.assertEqual(patches[("wBattleMonStatus", 0)], 16)
        self.assertEqual(patches[("wEnemyMonStatus", 0)], 8)

    def test_switch_materialization_environment_overrides_apply_when_present(self) -> None:
        scenario = {
            "family": "switch_sack",
            "tier": "late",
            "expectation": {"condition_tags": ["switch_sack"]},
            "overrides": {
                "weather": 1,  # rain
                "weather_count": 5,
                "player_item": 17,
                "enemy_item": 32,
                "player_screens": 4,  # safeguard bit
            },
        }
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in switch_materialization_patches(scenario)
        }
        self.assertEqual(patches[("wBattleWeather", 0)], 1)
        self.assertEqual(patches[("wWeatherCount", 0)], 5)
        self.assertEqual(patches[("wBattleMonItem", 0)], 17)
        # enemy_item override should win over the default NO_ITEM patch.
        self.assertEqual(patches[("wEnemyMonItem", 0)], 32)
        self.assertEqual(patches[("wPlayerScreens", 0)], 4)
        # No override for enemy_screens; no patch should be emitted for it.

    def test_switch_materialization_sub5_overrides_apply_when_present(self) -> None:
        scenario = {
            "family": "switch_sack",
            "tier": "late",
            "expectation": {"condition_tags": ["switch_sack"]},
            "overrides": {"player_sub5": 1, "enemy_sub5": 1},
        }
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in switch_materialization_patches(scenario)
        }
        self.assertEqual(patches[("wPlayerSubStatus5", 0)], 1)
        self.assertEqual(patches[("wEnemySubStatus5", 0)], 1)

    def test_switch_materialization_stat_stages_override_applies(self) -> None:
        scenario = {
            "family": "switch_sack",
            "tier": "late",
            "expectation": {"condition_tags": ["switch_sack"]},
            "overrides": {
                # +2 Atk, +0 Def, +1 Spd, +0 SAtk, +0 SDef (Dragon Dance look)
                "player_stat_stages": [2, 0, 1, 0, 0],
                # -1 Atk, +0, +0, -2 SAtk, +0 (intimidate + nasty plot drop look)
                "enemy_stat_stages": [-1, 0, 0, -2, 0],
            },
        }
        patches = {
            (patch.symbol_name, patch.offset): patch.value
            for patch in switch_materialization_patches(scenario)
        }
        # base-7 encoding: user +0 -> byte 7, +2 -> 9, +1 -> 8, -1 -> 6, -2 -> 5
        self.assertEqual(patches[("wPlayerAtkLevel", 0)], 9)
        self.assertEqual(patches[("wPlayerDefLevel", 0)], 7)
        self.assertEqual(patches[("wPlayerSpdLevel", 0)], 8)
        self.assertEqual(patches[("wPlayerSAtkLevel", 0)], 7)
        self.assertEqual(patches[("wPlayerSDefLevel", 0)], 7)
        self.assertEqual(patches[("wEnemyAtkLevel", 0)], 6)
        self.assertEqual(patches[("wEnemyDefLevel", 0)], 7)
        self.assertEqual(patches[("wEnemySpdLevel", 0)], 7)
        self.assertEqual(patches[("wEnemySAtkLevel", 0)], 5)
        self.assertEqual(patches[("wEnemySDefLevel", 0)], 7)

    def test_switch_materialization_skips_stat_stages_when_absent(self) -> None:
        scenario = {
            "family": "switch_sack",
            "tier": "late",
            "expectation": {"condition_tags": ["switch_sack"]},
        }
        symbols = {
            patch.symbol_name
            for patch in switch_materialization_patches(scenario)
        }
        # No stat-stage override means no patch -- the base save state's
        # existing wPlayer/EnemyStatLevels survive untouched.
        for symbol in (
            "wPlayerAtkLevel",
            "wPlayerDefLevel",
            "wPlayerSpdLevel",
            "wPlayerSAtkLevel",
            "wPlayerSDefLevel",
            "wEnemyAtkLevel",
            "wEnemyDefLevel",
            "wEnemySpdLevel",
            "wEnemySAtkLevel",
            "wEnemySDefLevel",
        ):
            self.assertNotIn(symbol, symbols)

    def test_switch_materialization_rejects_stat_stages_wrong_length(self) -> None:
        scenario = {
            "family": "switch_sack",
            "tier": "late",
            "expectation": {"condition_tags": ["switch_sack"]},
            "overrides": {"player_stat_stages": [1, 2, 3]},
        }
        with self.assertRaisesRegex(PreferenceDataError, "5-element list"):
            switch_materialization_patches(scenario)

    def test_switch_materialization_rejects_stat_stages_out_of_range(self) -> None:
        scenario = {
            "family": "switch_sack",
            "tier": "late",
            "expectation": {"condition_tags": ["switch_sack"]},
            "overrides": {"player_stat_stages": [0, 0, 7, 0, 0]},
        }
        with self.assertRaisesRegex(PreferenceDataError, "out of range"):
            switch_materialization_patches(scenario)

    def test_switch_materialization_rejects_stat_stages_non_int(self) -> None:
        scenario = {
            "family": "switch_sack",
            "tier": "late",
            "expectation": {"condition_tags": ["switch_sack"]},
            "overrides": {"player_stat_stages": [0, "two", 0, 0, 0]},
        }
        with self.assertRaisesRegex(PreferenceDataError, "must be an integer"):
            switch_materialization_patches(scenario)

    def test_switch_materialization_skips_sub5_when_absent(self) -> None:
        scenario = {
            "family": "switch_sack",
            "tier": "late",
            "expectation": {"condition_tags": ["switch_sack"]},
        }
        symbols = {
            patch.symbol_name
            for patch in switch_materialization_patches(scenario)
        }
        self.assertNotIn("wPlayerSubStatus5", symbols)
        self.assertNotIn("wEnemySubStatus5", symbols)

    def test_switch_materialization_skips_environment_patches_when_absent(self) -> None:
        scenario = {
            "family": "switch_sack",
            "tier": "late",
            "expectation": {"condition_tags": ["switch_sack"]},
        }
        symbols = {
            patch.symbol_name
            for patch in switch_materialization_patches(scenario)
        }
        # When no environment overrides are provided, slice C-environment must
        # not emit those patches so the base save state's existing values are
        # preserved (preserves backward-compat with trace ROM bytes).
        self.assertNotIn("wBattleWeather", symbols)
        self.assertNotIn("wWeatherCount", symbols)
        self.assertNotIn("wBattleMonItem", symbols)
        self.assertNotIn("wPlayerScreens", symbols)
        self.assertNotIn("wEnemyScreens", symbols)
        # wEnemyMonItem IS always patched (legacy default = NO_ITEM).
        self.assertIn("wEnemyMonItem", symbols)

    def test_switch_materialization_rejects_non_object_overrides(self) -> None:
        scenario = {
            "family": "switch_sack",
            "tier": "late",
            "expectation": {"condition_tags": ["switch_sack"]},
            "overrides": "not a dict",
        }
        with self.assertRaisesRegex(PreferenceDataError, "overrides must be an object"):
            switch_materialization_patches(scenario)

    def test_switch_verdict_flags_unwanted_switch(self) -> None:
        scenario = generate_scenarios(family="switch_sack", count=3, seed=2)[2]

        verdict = switch_verdict_from_report(
            scenario,
            {
                "proposed_switch": True,
                "switch_confidence": 90,
                "switch_param": 0x21,
            },
        )

        self.assertFalse(verdict["expected_switch"])
        self.assertEqual(verdict["rom_policy"]["verdict"], "mismatch")

    def test_source_base_switch_threshold_uses_shared_jasmine_class_mod(self) -> None:
        scenario = {"tier": "mid"}

        threshold = source_base_switch_threshold(scenario, base_route="shared_switch_loop")

        self.assertEqual(threshold["tier"], "mid")
        self.assertEqual(threshold["trainer_class"], "JASMINE")
        self.assertEqual(threshold["class_threshold_mod"], 4)
        self.assertEqual(threshold["threshold"], 74)

    def test_switch_roll_frequency_uses_explicit_threshold_for_exact_rate(self) -> None:
        scenario = generate_scenarios(family="switch_sack", count=1, seed=1)[0]

        roll = switch_roll_frequency(
            scenario,
            {"switch_confidence": 90},
            switch_threshold=70,
        )

        self.assertTrue(roll["threshold_exact"])
        self.assertTrue(roll["probability_exact"])
        self.assertEqual(roll["assumed_effective_threshold"], 70)
        self.assertEqual(roll["switch_chance_threshold"], 230)
        self.assertEqual(roll["switch_probability"], 230 / 256)

    def test_switch_roll_frequency_reports_untraced_bias_range(self) -> None:
        scenario = {"tier": "mid"}

        roll = switch_roll_frequency(
            scenario,
            {"switch_confidence": 90},
            base_route="shared_switch_loop",
        )

        self.assertFalse(roll["threshold_exact"])
        self.assertFalse(roll["probability_exact"])
        self.assertEqual(roll["base_threshold"], 74)
        self.assertEqual(roll["possible_effective_thresholds"], [74, 82, 84, 92])
        self.assertEqual(
            [item["switch_chance_threshold"] for item in roll["possible_switch_probabilities"]],
            [192, 141, 141, 0],
        )

    def test_switch_roll_frequency_is_unavailable_without_switch_observation(self) -> None:
        scenario = {"tier": "mid"}

        roll = switch_roll_frequency(
            scenario,
            {
                "switch_confidence": 0,
                "observed_switch_path": False,
                "observation_status": "no_decision_observed",
            },
        )

        self.assertFalse(roll["available"])
        self.assertEqual(roll["reason"], "no_switch_dispatch_observation")
        self.assertEqual(roll["proof_status"], "no_final_switch_roll_observed")

    def test_switch_verdict_marks_no_decision_observation_as_error(self) -> None:
        scenario = generate_scenarios(family="switch_sack", count=1, seed=1)[0]

        verdict = switch_verdict_from_report(
            scenario,
            {
                "observed_decision": False,
                "observed_switch_path": False,
                "observation_status": "no_decision_observed",
                "switch_confidence": 0,
            },
        )

        self.assertEqual(verdict["status"], "error")
        self.assertEqual(
            verdict["reason"],
            "no switch materialization decision observed within watch_frames",
        )
        self.assertFalse(verdict["switch_roll"]["available"])

    def test_switch_observation_status_distinguishes_timeout_from_proposal(self) -> None:
        self.assertEqual(
            switch_observation_status(
                switch_confidence=0,
                switch_param=0,
                switch_index=0,
                chosen_move=0,
            ),
            "no_decision_observed",
        )
        self.assertEqual(
            switch_observation_status(
                switch_confidence=0x30,
                switch_param=0x21,
                switch_index=0,
                chosen_move=0,
            ),
            "switch_proposal_observed",
        )

    def test_manifest_prefers_switch_materialization_state_when_present(self) -> None:
        self.assertEqual(
            switch_materialization_state_field(
                {
                    "save_state": "post_dispatch.state",
                    "switch_materialization_state": "pre_dispatch.state",
                }
            ),
            "switch_materialization_state",
        )
        self.assertEqual(
            switch_materialization_state_field({"save_state": "post_dispatch.state"}),
            "save_state",
        )

    def test_switch_base_validation_rejects_post_dispatch_snapshot(self) -> None:
        values = {
            "wBossAITraceSwitchConfidence": [99],
            "wEnemySwitchMonParam": [0x31],
            "wEnemySwitchMonIndex": [2],
            "wBossAITraceChosenMove": [0],
        }

        with self.assertRaisesRegex(
            PreferenceDataError,
            "already inside or past BossAI_SwitchOrTryItem",
        ):
            validate_switch_materialization_base(values)

    def test_manifest_hash_validation_rejects_mismatched_trace_basis(self) -> None:
        with TemporaryDirectory() as tmp:
            rom = Path(tmp) / "pokegold_trace.gbc"
            rom.write_bytes(b"current-rom")
            data = {"trace_rom_sha256": "0" * 64}

            with self.assertRaisesRegex(
                PreferenceDataError,
                "trace_rom hash mismatch",
            ):
                validate_manifest_hash(
                    data,
                    manifest_key="trace_rom_sha256",
                    actual_path=rom,
                    label="trace_rom",
                )

    def test_manifest_hash_validation_accepts_matching_trace_basis(self) -> None:
        with TemporaryDirectory() as tmp:
            rom = Path(tmp) / "pokegold_trace.gbc"
            rom.write_bytes(b"current-rom")
            with patch(
                "tools.boss_ai_debugger.rom_switch_materialize.capture.sha256_file",
                return_value="A" * 64,
            ):
                validate_manifest_hash(
                    {"trace_rom_sha256": "a" * 64},
                    manifest_key="trace_rom_sha256",
                    actual_path=rom,
                    label="trace_rom",
                )

    def test_manifest_hash_validation_prefers_switch_materialization_basis(self) -> None:
        with TemporaryDirectory() as tmp:
            rom = Path(tmp) / "pokegold_trace.gbc"
            rom.write_bytes(b"current-rom")
            with patch(
                "tools.boss_ai_debugger.rom_switch_materialize.capture.sha256_file",
                return_value="B" * 64,
            ):
                validate_manifest_hash(
                    {
                        "switch_materialization_trace_rom_sha256": "b" * 64,
                    },
                    manifest_fallback={"trace_rom_sha256": "0" * 64},
                    manifest_key="switch_materialization_trace_rom_sha256",
                    fallback_key="trace_rom_sha256",
                    actual_path=rom,
                    label="trace_rom",
                )

    def test_format_switch_materialization_prints_error_reason(self) -> None:
        report = {
            "scenario_count": 1,
            "checked_count": 0,
            "skipped_count": 1,
            "error_count": 1,
            "policy_disagreement_count": 0,
            "base_route": "shared_switch_loop",
            "base_state": "post_dispatch.state",
            "base_state_field": "save_state",
            "materializations_per_minute": 0.0,
            "known_limits": [],
            "verdicts": [
                {
                    "scenario_id": "unit",
                    "status": "error",
                    "expected_switch": True,
                    "reason": "stale post-dispatch state",
                    "rom": {},
                    "switch_roll": {"available": False, "reason": "no_switch_dispatch_observation"},
                }
            ],
        }

        text = format_rom_switch_materialization(report)

        self.assertIn("status=error", text)
        self.assertIn("reason=stale post-dispatch state", text)


if __name__ == "__main__":
    unittest.main()
