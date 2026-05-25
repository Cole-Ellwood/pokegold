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


if __name__ == "__main__":
    unittest.main()
