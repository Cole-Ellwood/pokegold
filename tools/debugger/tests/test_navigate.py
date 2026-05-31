from __future__ import annotations

import unittest

from tools.debugger import state_predicate
from tools.debugger.navigate import (
    ROOT,
    build_observed,
    format_search_input_log,
    parse_event_constants,
    parse_pokemon_names,
    parse_trainer_class_names,
    predicate_targets_battle_state,
    predicate_targets_event_state,
)
from tools.debugger.runtime_state import load_map_catalog


class NavigateObservationTests(unittest.TestCase):
    def test_live_constant_parsers_resolve_morty_and_gengar(self) -> None:
        trainer_classes = parse_trainer_class_names()
        species = parse_pokemon_names()

        self.assertEqual(trainer_classes[4], "MORTY")
        self.assertEqual(species[0x10], "PIDGEY")
        self.assertEqual(species[0x5E], "GENGAR")

    def test_boss_battle_observation_satisfies_predicate_language(self) -> None:
        catalog = load_map_catalog(root=ROOT, labels={})
        observed = build_observed(
            catalog,
            24,
            7,
            battle_mode=2,
            trainer_class=4,
            trainer_id=1,
            trainer_class_name="MORTY",
            boss="MORTY",
            enemy_species=0x5E,
            enemy_active="GENGAR",
            player_turns_taken=3,
        )

        predicate = state_predicate.parse(
            "battle(boss=MORTY) and trainer_class=MORTY and trainer_id=1 "
            "and turn==3 and enemy_active=GENGAR"
        )
        result = state_predicate.evaluate(predicate, observed)

        self.assertTrue(result.satisfied, result.unmet)
        self.assertEqual(observed["_trainer_class"], 4)
        self.assertEqual(observed["_trainer_id"], 1)
        self.assertEqual(observed["trainer_class"], "MORTY")
        self.assertEqual(observed["trainer_id"], 1)
        self.assertEqual(observed["boss"], "MORTY")
        self.assertEqual(observed["enemy_active"], "GENGAR")
        self.assertTrue(observed["trainer_battle"])

    def test_route_waypoint_observation_satisfies_coordinate_predicate(self) -> None:
        catalog = load_map_catalog(root=ROOT, labels={})
        observed = build_observed(catalog, 5, 9, x=7, y=33, battle_mode=0, facing="UP")

        predicate = state_predicate.parse("map=ROUTE_46 and x=7 and y=33 and facing=UP")
        result = state_predicate.evaluate(predicate, observed)

        self.assertTrue(result.satisfied, result.unmet)
        self.assertEqual(observed["map"], "ROUTE_46")
        self.assertEqual(observed["x"], 7)
        self.assertEqual(observed["y"], 33)
        self.assertEqual(observed["facing"], "UP")

    def test_script_state_observation_satisfies_script_predicates(self) -> None:
        catalog = load_map_catalog(root=ROOT, labels={})
        observed = build_observed(catalog, 26, 10, x=3, y=6, script_mode=2, script_running=0xFF)

        active = state_predicate.parse("map=MR_POKEMONS_HOUSE and script_active")
        done = state_predicate.parse("map=MR_POKEMONS_HOUSE and script_mode=0 and script_running=0")

        self.assertTrue(state_predicate.evaluate(active, observed).satisfied)
        self.assertFalse(state_predicate.evaluate(done, observed).satisfied)
        self.assertEqual(observed["script_mode"], 2)
        self.assertEqual(observed["script_running"], 0xFF)

    def test_event_flag_observation_satisfies_event_predicates(self) -> None:
        catalog = load_map_catalog(root=ROOT, labels={})
        observed = build_observed(
            catalog,
            24,
            5,
            x=4,
            y=8,
            script_mode=0,
            script_running=0,
            event_flags={"EVENT_GAVE_MYSTERY_EGG_TO_ELM": True},
        )

        predicate = state_predicate.parse(
            "event=EVENT_GAVE_MYSTERY_EGG_TO_ELM and map=ELMS_LAB and script_mode=0"
        )

        self.assertTrue(state_predicate.evaluate(predicate, observed).satisfied)
        self.assertTrue(observed["event:EVENT_GAVE_MYSTERY_EGG_TO_ELM"])
        event_constants = parse_event_constants()
        self.assertEqual(event_constants["EVENT_GAVE_MYSTERY_EGG_TO_ELM"], 31)
        self.assertEqual(event_constants["EVENT_BEAT_SWIMMERF_ELAINE"], 1000)

    def test_battle_target_detection_keeps_battle_predicates_from_normalizing_away(self) -> None:
        self.assertTrue(predicate_targets_battle_state(state_predicate.parse("trainer_battle")))
        self.assertTrue(predicate_targets_battle_state(state_predicate.parse("trainer_class=RIVAL1")))
        self.assertTrue(predicate_targets_battle_state(state_predicate.parse("battle(boss=FALKNER) and turn=1")))
        self.assertFalse(
            predicate_targets_battle_state(
                state_predicate.parse("map=CHERRYGROVE_CITY and script_mode=0 and script_running=0")
            )
        )

    def test_event_target_detection_adds_interaction_actions(self) -> None:
        self.assertTrue(predicate_targets_event_state(state_predicate.parse("event=EVENT_GAVE_MYSTERY_EGG_TO_ELM")))
        self.assertFalse(predicate_targets_event_state(state_predicate.parse("map=ELMS_LAB")))

    def test_search_input_log_formatter_preserves_button_timing(self) -> None:
        text = format_search_input_log(
            {
                "predicate": "map==ROUTE_46",
                "checkpoint": "route29_first_wild",
                "input_events": [
                    {"kind": "button", "button": "LEFT", "hold_frames": 16, "total_frames": 100},
                    {"kind": "wait", "frames": 12},
                ],
            }
        )

        self.assertIn("LEFT 16\nWAIT 84", text)
        self.assertIn("WAIT 12", text)


if __name__ == "__main__":
    unittest.main()
