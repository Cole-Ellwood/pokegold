from __future__ import annotations

import unittest

from tools.boss_ai_debugger.rom_switch_materialize import (
    scenario_condition_tags,
)
from tools.headless_battle.rom_switch_scenario_export import (
    DEFENSIVE_SACK_HP_THRESHOLD,
    ACTIVE_PRESSURE_HP_THRESHOLD,
    headless_to_switch_sack_scenario,
)
from tools.headless_battle.simulator import SimulationInputError


def fixture_state(**overrides):
    state = {
        "weather": "none",
        "weather_count": 0,
        "turn": 1,
        "player": {
            "species": "STARMIE",
            "level": 50,
            "types": ["GROUND", "GROUND"],
            "hp": 80,
            "max_hp": 100,
            "stats": {
                "attack": 70,
                "defense": 80,
                "speed": 100,
                "sp_attack": 90,
                "sp_defense": 80,
            },
            "moves": [{"name": "SURF"}],
        },
        "enemy": {
            "species": "QWILFISH",
            "level": 50,
            "types": ["POISON", "WATER"],
            "hp": 80,
            "max_hp": 100,
            "stats": {
                "attack": 70,
                "defense": 75,
                "speed": 85,
                "sp_attack": 55,
                "sp_defense": 55,
            },
            "moves": [{"name": "POISON_STING"}],
            "bench": [
                {
                    "name": "GENGAR",
                    "level": 50,
                    "types": ["GHOST", "POISON"],
                    "hp": 80,
                    "max_hp": 100,
                    "stats": {
                        "attack": 65,
                        "defense": 60,
                        "speed": 110,
                        "sp_attack": 130,
                        "sp_defense": 75,
                    },
                    "moves": [{"name": "LICK"}],
                },
            ],
        },
    }
    for path, value in overrides.items():
        parts = path.split(".")
        target = state
        for key in parts[:-1]:
            target = target[key]
        target[parts[-1]] = value
    return state


class RomSwitchScenarioExportTests(unittest.TestCase):
    def test_canonical_board_emits_minimum_tag_set(self) -> None:
        scenario = headless_to_switch_sack_scenario(
            fixture_state(), scenario_id="canonical", tier="mid"
        )
        self.assertEqual(scenario["family"], "switch_sack")
        self.assertEqual(scenario["tier"], "mid")
        self.assertEqual(scenario["id"], "canonical")
        tags = scenario_condition_tags(scenario)
        self.assertEqual(tags, {"switch_sack"})
        self.assertEqual(scenario["policy_case"], "exported_headless_board")

    def test_low_enemy_hp_triggers_defensive_sack_owner_tag(self) -> None:
        state = fixture_state()
        state["enemy"]["hp"] = DEFENSIVE_SACK_HP_THRESHOLD
        scenario = headless_to_switch_sack_scenario(state)
        self.assertIn("defensive_sack_owner", scenario_condition_tags(scenario))

    def test_low_player_hp_triggers_active_pressure_converts_tag(self) -> None:
        state = fixture_state()
        state["player"]["hp"] = ACTIVE_PRESSURE_HP_THRESHOLD
        scenario = headless_to_switch_sack_scenario(state)
        self.assertIn("active_pressure_converts", scenario_condition_tags(scenario))

    def test_extra_tags_pass_through(self) -> None:
        scenario = headless_to_switch_sack_scenario(
            fixture_state(),
            extra_tags=["wincon_preservation", "support_job_completed"],
        )
        tags = scenario_condition_tags(scenario)
        self.assertIn("wincon_preservation", tags)
        self.assertIn("support_job_completed", tags)
        self.assertIn("switch_sack", tags)

    def test_custom_policy_case(self) -> None:
        scenario = headless_to_switch_sack_scenario(
            fixture_state(), policy_case="preserve_wincon_over_comfort_damage"
        )
        self.assertEqual(scenario["policy_case"], "preserve_wincon_over_comfort_damage")

    def test_rejects_wrong_player_species(self) -> None:
        state = fixture_state()
        state["player"]["species"] = "CYNDAQUIL"
        with self.assertRaisesRegex(SimulationInputError, "player.name='CYNDAQUIL'"):
            headless_to_switch_sack_scenario(state)

    def test_rejects_wrong_enemy_types(self) -> None:
        state = fixture_state()
        state["enemy"]["types"] = ["POISON", "POISON"]
        with self.assertRaisesRegex(SimulationInputError, "enemy.types"):
            headless_to_switch_sack_scenario(state)

    def test_rejects_missing_enemy_bench(self) -> None:
        state = fixture_state()
        state["enemy"]["bench"] = []
        with self.assertRaisesRegex(SimulationInputError, "enemy bench is empty"):
            headless_to_switch_sack_scenario(state)

    def test_rejects_wrong_enemy_bench_species(self) -> None:
        state = fixture_state()
        state["enemy"]["bench"][0]["name"] = "DRAGONITE"
        with self.assertRaisesRegex(SimulationInputError, "bench\\[0\\]='DRAGONITE'"):
            headless_to_switch_sack_scenario(state)

    def test_rejects_status_on_player(self) -> None:
        state = fixture_state()
        state["player"]["status"] = "burn"
        with self.assertRaisesRegex(SimulationInputError, "player.status='burn'"):
            headless_to_switch_sack_scenario(state)

    def test_rejects_weather(self) -> None:
        state = fixture_state(weather="rain", weather_count=5)
        with self.assertRaisesRegex(SimulationInputError, "weather"):
            headless_to_switch_sack_scenario(state)

    def test_rejects_spikes(self) -> None:
        state = fixture_state()
        state["player_spikes"] = 1
        with self.assertRaisesRegex(SimulationInputError, "spikes"):
            headless_to_switch_sack_scenario(state)

    def test_rejects_substitute(self) -> None:
        state = fixture_state()
        state["enemy"]["substitute"] = True
        state["enemy"]["substitute_hp"] = 25
        with self.assertRaisesRegex(SimulationInputError, "Substitute"):
            headless_to_switch_sack_scenario(state)

    def test_rejects_stat_stages(self) -> None:
        state = fixture_state()
        state["player"]["stat_stages"] = {"attack": 1}
        with self.assertRaisesRegex(SimulationInputError, "stat_stages"):
            headless_to_switch_sack_scenario(state)

    def test_rejects_invalid_tier(self) -> None:
        with self.assertRaisesRegex(SimulationInputError, "tier"):
            headless_to_switch_sack_scenario(fixture_state(), tier="ultra")

    def test_accept_overrides_emits_overrides_for_arbitrary_species(self) -> None:
        state = fixture_state()
        state["player"]["species"] = "CYNDAQUIL"
        state["player"]["types"] = ["FIRE", "FIRE"]
        state["enemy"]["species"] = "HAUNTER"
        state["enemy"]["types"] = ["GHOST", "POISON"]
        state["enemy"]["hp"] = 60
        state["enemy"]["max_hp"] = 90
        state["enemy"]["bench"][0]["name"] = "DRAGONITE"
        state["enemy"]["bench"][0]["types"] = ["DRAGON", "FLYING"]
        state["enemy"]["bench"][0]["hp"] = 75
        state["enemy"]["bench"][0]["max_hp"] = 120

        scenario = headless_to_switch_sack_scenario(
            state, accept_overrides=True, tier="late"
        )

        self.assertEqual(scenario["family"], "switch_sack")
        self.assertEqual(scenario["tier"], "late")
        self.assertEqual(scenario["exporter"]["fixture_domain"], "parameterized_overrides")
        overrides = scenario["overrides"]
        # Species ids are looked up via parse_species_order; spot-check by name->id.
        from tools.boss_ai_debugger.role_packages import parse_species_order
        order = parse_species_order()
        cyndaquil_id = order.index("CYNDAQUIL") + 1
        haunter_id = order.index("HAUNTER") + 1
        dragonite_id = order.index("DRAGONITE") + 1
        self.assertEqual(overrides["player_species"], cyndaquil_id)
        self.assertEqual(overrides["enemy_species"], haunter_id)
        self.assertEqual(overrides["enemy_bench_species"], dragonite_id)
        self.assertEqual(overrides["enemy_hp"], 60)
        self.assertEqual(overrides["enemy_max_hp"], 90)
        self.assertEqual(overrides["enemy_bench_hp"], 75)
        self.assertEqual(overrides["enemy_bench_max_hp"], 120)

    def test_accept_overrides_now_accepts_sleep_status_with_turns(self) -> None:
        state = fixture_state()
        state["player"]["status"] = "sleep"
        state["player"]["sleep_turns"] = 3
        scenario = headless_to_switch_sack_scenario(state, accept_overrides=True)
        # Sleep packs the counter into status byte bits 0-2.
        self.assertEqual(scenario["overrides"]["player_status"], 3)

    def test_accept_overrides_now_accepts_toxic_status_and_emits_sub5_bit(self) -> None:
        state = fixture_state()
        state["enemy"]["status"] = "toxic"
        state["enemy"]["toxic_count"] = 2
        scenario = headless_to_switch_sack_scenario(state, accept_overrides=True)
        # Toxic shares the poison primary-status byte.
        self.assertEqual(scenario["overrides"]["enemy_status"], 1 << 3)
        # SUBSTATUS_TOXIC bit on sub5 distinguishes toxic from regular poison.
        self.assertEqual(scenario["overrides"]["enemy_sub5"], 1)
        # No player_sub5 should be emitted when not toxic.
        self.assertNotIn("player_sub5", scenario["overrides"])

    def test_accept_overrides_now_accepts_burn_status(self) -> None:
        state = fixture_state()
        state["player"]["status"] = "burn"
        scenario = headless_to_switch_sack_scenario(state, accept_overrides=True)
        # 1 << BRN = 16
        self.assertEqual(scenario["overrides"]["player_status"], 16)
        self.assertEqual(scenario["overrides"]["enemy_status"], 0)

    def test_accept_overrides_now_accepts_paralyze_and_poison(self) -> None:
        state = fixture_state()
        state["player"]["status"] = "paralyze"
        state["enemy"]["status"] = "poison"
        scenario = headless_to_switch_sack_scenario(state, accept_overrides=True)
        self.assertEqual(scenario["overrides"]["player_status"], 1 << 6)
        self.assertEqual(scenario["overrides"]["enemy_status"], 1 << 3)

    def test_accept_overrides_now_accepts_weather(self) -> None:
        state = fixture_state(weather="rain", weather_count=5)
        scenario = headless_to_switch_sack_scenario(state, accept_overrides=True)
        self.assertIn("weather", scenario["overrides"])
        self.assertGreater(scenario["overrides"]["weather"], 0)
        self.assertEqual(scenario["overrides"]["weather_count"], 5)

    def test_accept_overrides_still_rejects_spikes(self) -> None:
        state = fixture_state()
        state["enemy_spikes"] = 2
        with self.assertRaisesRegex(SimulationInputError, "slice C-spikes"):
            headless_to_switch_sack_scenario(state, accept_overrides=True)

    def test_accept_overrides_now_accepts_held_items(self) -> None:
        state = fixture_state()
        state["player"]["item"] = 17  # arbitrary item id
        state["enemy"]["item"] = 32
        scenario = headless_to_switch_sack_scenario(state, accept_overrides=True)
        self.assertEqual(scenario["overrides"]["player_item"], 17)
        self.assertEqual(scenario["overrides"]["enemy_item"], 32)

    def test_accept_overrides_now_accepts_nonzero_stat_stages(self) -> None:
        state = fixture_state()
        # Dragon-Dance-style player setup: +1 Atk, +1 Spe.
        state["player"]["stat_stages"] = {"attack": 1, "speed": 1}
        # Calm-Mind-style enemy: +2 SpA, +2 SpD.
        state["enemy"]["stat_stages"] = {"sp_attack": 2, "sp_defense": 2}
        scenario = headless_to_switch_sack_scenario(state, accept_overrides=True)
        self.assertEqual(
            scenario["overrides"]["player_stat_stages"], [1, 0, 1, 0, 0]
        )
        self.assertEqual(
            scenario["overrides"]["enemy_stat_stages"], [0, 0, 0, 2, 2]
        )

    def test_accept_overrides_skips_stat_stages_when_all_zero(self) -> None:
        state = fixture_state()
        scenario = headless_to_switch_sack_scenario(state, accept_overrides=True)
        # All-zero stages must NOT emit the override key so the base save
        # state's existing wPlayer/EnemyStatLevels survive untouched.
        self.assertNotIn("player_stat_stages", scenario["overrides"])
        self.assertNotIn("enemy_stat_stages", scenario["overrides"])

    def test_accept_overrides_emits_safeguard_screens_bit(self) -> None:
        state = fixture_state()
        state["player_safeguard"] = True
        scenario = headless_to_switch_sack_scenario(state, accept_overrides=True)
        # SCREENS_SAFEGUARD is bit 2 -> 1<<2 = 4
        self.assertEqual(scenario["overrides"]["player_screens"], 4)
        self.assertNotIn("enemy_screens", scenario["overrides"])

    def test_accept_overrides_still_rejects_empty_enemy_bench(self) -> None:
        state = fixture_state()
        state["enemy"]["bench"] = []
        with self.assertRaisesRegex(SimulationInputError, "enemy bench is empty"):
            headless_to_switch_sack_scenario(state, accept_overrides=True)

    def test_accept_overrides_round_trips_into_materialization_patches(self) -> None:
        # End-to-end: the headless-emitted overrides should be consumed by
        # switch_materialization_patches and yield matching WRAM patches.
        from tools.boss_ai_debugger.rom_switch_materialize import (
            switch_materialization_patches,
        )

        state = fixture_state()
        state["player"]["species"] = "CYNDAQUIL"
        state["player"]["types"] = ["FIRE", "FIRE"]
        state["enemy"]["species"] = "HAUNTER"
        state["enemy"]["types"] = ["GHOST", "POISON"]
        state["enemy"]["hp"] = 60
        state["enemy"]["bench"][0]["name"] = "DRAGONITE"
        state["enemy"]["bench"][0]["types"] = ["DRAGON", "FLYING"]
        scenario = headless_to_switch_sack_scenario(state, accept_overrides=True)
        patches = {
            (p.symbol_name, p.offset): p.value
            for p in switch_materialization_patches(scenario)
        }
        from tools.boss_ai_debugger.role_packages import parse_species_order
        order = parse_species_order()
        self.assertEqual(patches[("wBattleMonSpecies", 0)], order.index("CYNDAQUIL") + 1)
        self.assertEqual(patches[("wEnemyMonSpecies", 0)], order.index("HAUNTER") + 1)
        self.assertEqual(patches[("wOTPartyMon2Species", 0)], order.index("DRAGONITE") + 1)
        self.assertEqual(patches[("wEnemyMonHP", 1)], 60)


if __name__ == "__main__":
    unittest.main()
