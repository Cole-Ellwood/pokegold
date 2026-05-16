from __future__ import annotations

import io
import json
import tempfile
import unittest
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.regression import evaluate_corpus, format_json, format_summary
from tools.boss_ai_debugger.scorer import score_action
from tools.boss_ai_preference.data import (
    PreferenceDataError,
    load_fixtures,
    load_preferences,
)
from tools.boss_ai_preference.features import extract_action_features


def tiny_fixture() -> dict:
    return {
        "id": "synthetic_fixture",
        "leader": "Tester",
        "state": {},
        "actions": [
            {
                "id": "move_crunch",
                "kind": "move",
                "name": "Crunch",
                "explanation": "coverage move",
                "public_tradeoff": "punish visible pressure",
            },
            {
                "id": "move_tackle",
                "kind": "move",
                "name": "Tackle",
                "explanation": "plain move",
                "public_tradeoff": "neutral",
            },
        ],
    }


def tie_fixture() -> dict:
    return {
        "id": "tie_fixture",
        "leader": "Tester",
        "state": {},
        "actions": [
            {
                "id": "move_tackle",
                "kind": "move",
                "name": "Tackle",
                "explanation": "plain move",
                "public_tradeoff": "neutral",
            },
            {
                "id": "move_scratch",
                "kind": "move",
                "name": "Scratch",
                "explanation": "plain move",
                "public_tradeoff": "neutral",
            },
        ],
    }


def pairwise_label(
    choice: str,
    *,
    fixture_id: str = "synthetic_fixture",
    action_a_id: str = "move_crunch",
    action_b_id: str = "move_tackle",
) -> dict:
    preferred_action_id = None
    if choice == "a_better":
        preferred_action_id = action_a_id
    elif choice == "b_better":
        preferred_action_id = action_b_id
    return {
        "fixture_id": fixture_id,
        "state_version": 1,
        "action_a_id": action_a_id,
        "action_b_id": action_b_id,
        "choice": choice,
        "preferred_action_id": preferred_action_id,
        "reason_tags": [],
        "action_tags": {action_a_id: [], action_b_id: []},
        "note": "unit test label",
        "created_at": "2026-05-09T00:00:00+00:00",
        "tool_version": "boss-ai-preference-v0",
    }


class RegressionTests(unittest.TestCase):
    def test_existing_fixture_file_loads_realistic_corpus(self) -> None:
        fixtures = load_fixtures()
        labels = load_preferences(fixtures=fixtures)

        result = evaluate_corpus(fixtures, labels, threshold=0.80)

        expected_strict = sum(
            1 for label in labels if label["choice"] in {"a_better", "b_better"}
        )
        expected_skipped = Counter(
            label["choice"]
            for label in labels
            if label["choice"] not in {"a_better", "b_better"}
        )
        self.assertGreaterEqual(len(labels), 10)
        self.assertEqual(result.strict_label_count, expected_strict)
        self.assertEqual(result.skipped, dict(sorted(expected_skipped.items())))

    def test_lock_risk_only_applies_to_actual_lock_moves(self) -> None:
        fixture = {
            "id": "lock_text_fixture",
            "leader": "Tester",
            "state": {},
            "actions": [
                {
                    "id": "move_body_slam",
                    "kind": "move",
                    "name": "Body Slam",
                    "explanation": "Keeps pressure without locking into a bad sequence.",
                    "public_tradeoff": "Safe damage.",
                },
                {
                    "id": "move_rollout",
                    "kind": "move",
                    "name": "Rollout",
                    "explanation": "Actual ramp lock move.",
                    "public_tradeoff": "Risky lock.",
                },
            ],
        }

        body_slam = score_action(fixture, fixture["actions"][0])
        rollout = score_action(fixture, fixture["actions"][1])

        self.assertNotIn(
            "lock_risk",
            {contribution["rule"] for contribution in body_slam["contributions"]},
        )
        self.assertIn(
            "lock_risk",
            {contribution["rule"] for contribution in rollout["contributions"]},
        )

    def test_setup_prose_does_not_make_setup_a_coverage_move(self) -> None:
        fixture = {
            "id": "setup_text_fixture",
            "leader": "Tester",
            "state": {},
            "actions": [
                {
                    "id": "move_swords_dance",
                    "kind": "move",
                    "name": "Swords Dance",
                    "explanation": "Can set up if the player cannot punish.",
                    "public_tradeoff": "A real setup opportunity.",
                }
            ],
        }

        scored = score_action(fixture, fixture["actions"][0])
        rules = {contribution["rule"] for contribution in scored["contributions"]}

        self.assertIn("setup_window", rules)
        self.assertNotIn("coverage", rules)

    def test_quiver_dance_is_scored_as_setup_not_damage_coverage(self) -> None:
        fixture = {
            "id": "quiver_setup_fixture",
            "leader": "Tester",
            "state": {},
            "actions": [
                {
                    "id": "move_quiver_dance",
                    "kind": "move",
                    "name": "Quiver Dance",
                    "explanation": "Attempts to snowball through speed and special pressure.",
                    "public_tradeoff": "Greedy if the target has Ice coverage.",
                }
            ],
        }

        scored = score_action(fixture, fixture["actions"][0])
        rules = {contribution["rule"] for contribution in scored["contributions"]}
        features = extract_action_features(fixture, fixture["actions"][0])["features"]

        self.assertIn("setup_identity", rules)
        self.assertIn("setup_risk", rules)
        self.assertNotIn("coverage", rules)
        self.assertIn("move_class_setup", features)

    def test_public_psychic_into_dark_is_penalized(self) -> None:
        fixture = {
            "id": "psychic_dark_fixture",
            "leader": "Tester",
            "tags": ["choice_lock", "coverage"],
            "state": {
                "public_notes": [
                    "Psychic may fail into Dark typing.",
                ]
            },
            "actions": [
                {
                    "id": "move_psychic",
                    "kind": "move",
                    "name": "Psychic",
                    "explanation": "Highest identity move but bad into a public Dark type.",
                    "public_tradeoff": "Too robotic if chosen blindly.",
                },
                {
                    "id": "move_thunderpunch",
                    "kind": "move",
                    "name": "ThunderPunch",
                    "explanation": "Neutral coverage without locking into a failed Psychic.",
                    "public_tradeoff": "Readable adaptation.",
                },
            ],
        }

        psychic = score_action(fixture, fixture["actions"][0])
        thunderpunch = score_action(fixture, fixture["actions"][1])
        rules = {contribution["rule"] for contribution in psychic["contributions"]}
        features = extract_action_features(fixture, fixture["actions"][0])["features"]

        self.assertLess(psychic["score"], thunderpunch["score"])
        self.assertIn("public_type_immunity_risk", rules)
        self.assertIn("public_type_immunity_risk", features)

    def test_setup_into_public_sleep_window_can_beat_immediate_damage(self) -> None:
        fixture = {
            "id": "sleeping_target_setup_fixture",
            "leader": "Tester",
            "tags": ["sleep", "setup"],
            "state": {
                "player": {
                    "active": {
                        "species": "Snorlax",
                        "hp": "87%",
                        "status": "sleep",
                    }
                }
            },
            "actions": [
                {
                    "id": "move_curse",
                    "kind": "move",
                    "name": "Curse",
                    "explanation": "Uses the sleep window to change KO math.",
                    "public_tradeoff": "Wake timing still matters.",
                },
                {
                    "id": "move_earthquake",
                    "kind": "move",
                    "name": "Earthquake",
                    "explanation": "Immediate damage into the sleeping target.",
                    "public_tradeoff": "May fail to convert before wake.",
                },
            ],
        }

        curse = score_action(fixture, fixture["actions"][0])
        earthquake = score_action(fixture, fixture["actions"][1])
        rules = {contribution["rule"] for contribution in curse["contributions"]}
        features = extract_action_features(fixture, fixture["actions"][0])["features"]

        self.assertGreater(curse["score"], earthquake["score"])
        self.assertIn("sleeping_target_setup_window", rules)
        self.assertIn("setup_into_sleep_window", features)

    def test_sleep_first_can_enable_setup_line(self) -> None:
        fixture = {
            "id": "sleep_first_setup_fixture",
            "leader": "Tester",
            "tags": ["sleep", "setup"],
            "state": {
                "player": {
                    "active": {
                        "species": "Snorlax",
                        "hp": "84%",
                        "status": "none",
                    }
                }
            },
            "actions": [
                {
                    "id": "move_sleep_powder",
                    "kind": "move",
                    "name": "Sleep Powder",
                    "explanation": "Controls the target before setup.",
                    "public_tradeoff": "Miss risk exists.",
                },
                {
                    "id": "move_swords_dance",
                    "kind": "move",
                    "name": "Swords Dance",
                    "explanation": "Attempts raw setup.",
                    "public_tradeoff": "Greedy if the target can hit back.",
                },
            ],
        }

        sleep_powder = score_action(fixture, fixture["actions"][0])
        swords_dance = score_action(fixture, fixture["actions"][1])
        rules = {
            contribution["rule"] for contribution in sleep_powder["contributions"]
        }
        features = extract_action_features(fixture, fixture["actions"][0])["features"]

        self.assertGreater(sleep_powder["score"], swords_dance["score"])
        self.assertIn("sleep_enables_setup_line", rules)
        self.assertIn("sleep_enables_setup_line", features)

    def test_rest_and_sleep_talk_state_gates_are_scored(self) -> None:
        fixture = {
            "id": "rest_state_fixture",
            "leader": "Tester",
            "state": {
                "boss": {
                    "active": {
                        "species": "Snorlax",
                        "hp": "100%",
                        "status": "par",
                    }
                }
            },
            "actions": [
                {
                    "id": "move_rest",
                    "kind": "move",
                    "name": "Rest",
                    "explanation": "Tries to cure status at full HP.",
                    "public_tradeoff": "Local mechanics make this fail.",
                },
                {
                    "id": "move_sleep_talk",
                    "kind": "move",
                    "name": "Sleep Talk",
                    "explanation": "Only works while asleep.",
                    "public_tradeoff": "The user is awake.",
                },
            ],
        }

        rest = score_action(fixture, fixture["actions"][0])
        sleep_talk = score_action(fixture, fixture["actions"][1])
        rest_rules = {contribution["rule"] for contribution in rest["contributions"]}
        sleep_talk_rules = {
            contribution["rule"] for contribution in sleep_talk["contributions"]
        }
        rest_features = extract_action_features(fixture, fixture["actions"][0])["features"]
        sleep_talk_features = extract_action_features(fixture, fixture["actions"][1])[
            "features"
        ]

        self.assertIn("full_hp_rest_fails", rest_rules)
        self.assertIn("awake_sleep_talk_fails", sleep_talk_rules)
        self.assertIn("rest_at_full_hp", rest_features)
        self.assertIn("sleep_talk_while_awake", sleep_talk_features)

    def test_spikes_layer_delta_is_scored_from_fixture_state(self) -> None:
        fixture = {
            "id": "spikes_layer_fixture",
            "leader": "Tester",
            "tags": ["hazards", "romhack_delta"],
            "state": {
                "field": {
                    "hazards": {
                        "player_side_spikes_layers": 2,
                    }
                }
            },
            "actions": [
                {
                    "id": "move_spikes",
                    "kind": "move",
                    "name": "Spikes",
                    "explanation": "Places the third local Spikes layer.",
                    "public_tradeoff": "Converts future grounded switches.",
                },
                {
                    "id": "move_sludge_bomb",
                    "kind": "move",
                    "name": "Sludge Bomb",
                    "explanation": "Direct STAB chip.",
                    "public_tradeoff": "Does not change the hazard economy.",
                },
            ],
        }

        spikes = score_action(fixture, fixture["actions"][0])
        sludge_bomb = score_action(fixture, fixture["actions"][1])
        rules = {contribution["rule"] for contribution in spikes["contributions"]}
        features = extract_action_features(fixture, fixture["actions"][0])["features"]

        self.assertGreater(spikes["score"], sludge_bomb["score"])
        self.assertIn("third_spikes_layer_pressure", rules)
        self.assertIn("spikes_third_layer_available", features)
        self.assertIn("move_class_hazard", features)

    def test_spikes_already_maxed_is_scored_as_failed_redundancy(self) -> None:
        fixture = {
            "id": "spikes_maxed_fixture",
            "leader": "Tester",
            "tags": ["hazards", "romhack_delta"],
            "state": {
                "field": {
                    "hazards": {
                        "player_side_spikes_layers": 3,
                    }
                }
            },
            "actions": [
                {
                    "id": "move_spikes",
                    "kind": "move",
                    "name": "Spikes",
                    "explanation": "Attempts a fourth local Spikes layer.",
                    "public_tradeoff": "Fails once three layers are already set.",
                },
                {
                    "id": "move_sludge_bomb",
                    "kind": "move",
                    "name": "Sludge Bomb",
                    "explanation": "Direct STAB chip.",
                    "public_tradeoff": "At least advances the board.",
                },
            ],
        }

        spikes = score_action(fixture, fixture["actions"][0])
        sludge_bomb = score_action(fixture, fixture["actions"][1])
        rules = {contribution["rule"] for contribution in spikes["contributions"]}
        features = extract_action_features(fixture, fixture["actions"][0])["features"]

        self.assertLess(spikes["score"], sludge_bomb["score"])
        self.assertIn("spikes_already_maxed", rules)
        self.assertIn("spikes_already_maxed", features)

    def test_revealed_spinner_penalizes_extra_spikes_layers(self) -> None:
        for player_layers in (1, 2):
            with self.subTest(player_layers=player_layers):
                fixture = {
                    "id": "revealed_spinner_fixture",
                    "leader": "Tester",
                    "tags": ["hazards", "romhack_delta"],
                    "state": {
                        "player": {
                            "active": {
                                "species": "Starmie",
                                "revealed_moves": ["Surf", "Rapid Spin"],
                            }
                        },
                        "field": {
                            "hazards": {
                                "player_side_spikes_layers": player_layers,
                            }
                        },
                    },
                    "actions": [
                        {
                            "id": "move_spikes",
                            "kind": "move",
                            "name": "Spikes",
                            "explanation": "Stacks another local Spikes layer.",
                            "public_tradeoff": "The active spinner has already revealed Rapid Spin.",
                        },
                        {
                            "id": "move_sludge_bomb",
                            "kind": "move",
                            "name": "Sludge Bomb",
                            "explanation": "Direct STAB chip into the active spinner.",
                            "public_tradeoff": "Keeps tempo instead of stacking into revealed removal.",
                        },
                    ],
                }

                spikes = score_action(fixture, fixture["actions"][0])
                sludge_bomb = score_action(fixture, fixture["actions"][1])
                rules = {contribution["rule"] for contribution in spikes["contributions"]}
                features = extract_action_features(fixture, fixture["actions"][0])["features"]

                self.assertLess(spikes["score"], sludge_bomb["score"])
                self.assertIn("active_revealed_spinner_hazard_retention", rules)
                self.assertIn("active_revealed_spinner_hazard_retention", features)

    def test_spinner_capable_without_revealed_spin_keeps_spikes_pressure(self) -> None:
        fixture = {
            "id": "unrevealed_spinner_fixture",
            "leader": "Tester",
            "tags": ["hazards", "romhack_delta"],
            "state": {
                "player": {
                    "active": {
                        "species": "Starmie",
                        "revealed_moves": ["Surf", "Recover"],
                    }
                },
                "field": {
                    "hazards": {
                        "player_side_spikes_layers": 2,
                    }
                },
            },
            "actions": [
                {
                    "id": "move_spikes",
                    "kind": "move",
                    "name": "Spikes",
                    "explanation": "Places the third local Spikes layer.",
                    "public_tradeoff": "Rapid Spin has not been revealed by the active Pokemon.",
                },
                {
                    "id": "move_sludge_bomb",
                    "kind": "move",
                    "name": "Sludge Bomb",
                    "explanation": "Direct STAB chip.",
                    "public_tradeoff": "Does not change the hazard economy.",
                },
            ],
        }

        spikes = score_action(fixture, fixture["actions"][0])
        sludge_bomb = score_action(fixture, fixture["actions"][1])
        rules = {contribution["rule"] for contribution in spikes["contributions"]}
        features = extract_action_features(fixture, fixture["actions"][0])["features"]

        self.assertGreater(spikes["score"], sludge_bomb["score"])
        self.assertNotIn("active_revealed_spinner_hazard_retention", rules)
        self.assertNotIn("active_revealed_spinner_hazard_retention", features)

    def test_damage_estimate_can_mark_confirmed_ko(self) -> None:
        fixture = {
            "id": "ko_fixture",
            "leader": "Tester",
            "state": {},
            "actions": [
                {
                    "id": "move_wing_attack",
                    "kind": "move",
                    "name": "Wing Attack",
                    "explanation": "Immediate damage.",
                    "public_tradeoff": "Clean tempo.",
                    "damage_estimate": {
                        "low_percent": 95,
                        "high_percent": 112,
                        "target_hp": "51%",
                    },
                }
            ],
        }

        scored = score_action(fixture, fixture["actions"][0])

        self.assertIn(
            "ko_confirmed",
            {contribution["rule"] for contribution in scored["contributions"]},
        )

    def test_strict_pair_passes_when_scorer_matches_label(self) -> None:
        result = evaluate_corpus([tiny_fixture()], [pairwise_label("a_better")], 0.80)

        self.assertEqual(result.strict_agreement_count, 1)
        self.assertTrue(result.passed)
        self.assertEqual(result.disagreements, [])

    def test_strict_pair_fails_when_scorer_disagrees(self) -> None:
        result = evaluate_corpus([tiny_fixture()], [pairwise_label("b_better")], 0.80)

        self.assertEqual(result.strict_agreement_count, 0)
        self.assertFalse(result.passed)
        self.assertEqual(len(result.disagreements), 1)
        self.assertEqual(result.disagreements[0].scorer_choice, "a_better")
        self.assertIn("move_tackle > move_crunch", format_summary(result))

    def test_score_tie_counts_as_disagreement(self) -> None:
        label = pairwise_label(
            "a_better",
            fixture_id="tie_fixture",
            action_a_id="move_tackle",
            action_b_id="move_scratch",
        )

        result = evaluate_corpus([tie_fixture()], [label], 0.80)

        self.assertEqual(result.strict_label_count, 1)
        self.assertEqual(result.strict_agreement_count, 0)
        self.assertEqual(result.disagreements[0].scorer_choice, "tie")

    def test_non_strict_choices_are_skipped(self) -> None:
        result = evaluate_corpus([tiny_fixture()], [pairwise_label("both_good")], 0.80)

        self.assertEqual(result.strict_label_count, 0)
        self.assertEqual(result.skipped, {"both_good": 1})
        self.assertEqual(result.disagreements, [])

    def test_missing_fixture_or_action_raises_schema_error(self) -> None:
        with self.assertRaisesRegex(PreferenceDataError, "unknown fixture_id"):
            evaluate_corpus(
                [tiny_fixture()],
                [pairwise_label("a_better", fixture_id="missing_fixture")],
                0.80,
            )

        with self.assertRaisesRegex(PreferenceDataError, "action_id 'missing_action'"):
            evaluate_corpus(
                [tiny_fixture()],
                [pairwise_label("a_better", action_b_id="missing_action")],
                0.80,
            )

    def test_json_report_shape(self) -> None:
        result = evaluate_corpus([tiny_fixture()], [pairwise_label("b_better")], 0.80)

        report = format_json(result)

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["threshold"], 0.80)
        self.assertEqual(report["strict_label_count"], 1)
        self.assertEqual(report["strict_agreement_count"], 0)
        self.assertEqual(report["agreement_rate"], 0.0)
        self.assertEqual(report["disagreements"][0]["label_choice"], "b_better")

    def test_cli_exit_code_tracks_threshold_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixtures_path = Path(tmp) / "fixtures.json"
            labels_path = Path(tmp) / "labels.jsonl"
            fixtures_path.write_text(
                json.dumps({"schema_version": 1, "fixtures": [tiny_fixture()]}),
                encoding="utf-8",
            )

            labels_path.write_text(
                json.dumps(pairwise_label("a_better"), sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                pass_code = debugger_main(
                    [
                        "regress",
                        "--fixtures",
                        str(fixtures_path),
                        "--labels",
                        str(labels_path),
                        "--threshold",
                        "0.80",
                        "--quiet",
                    ]
                )
            self.assertEqual(pass_code, 0)

            labels_path.write_text(
                json.dumps(pairwise_label("b_better"), sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                fail_code = debugger_main(
                    [
                        "regress",
                        "--fixtures",
                        str(fixtures_path),
                        "--labels",
                        str(labels_path),
                        "--threshold",
                        "0.80",
                        "--quiet",
                    ]
                )
            self.assertEqual(fail_code, 1)

    def test_public_notes_chip_qualifier_penalises_switch_actions(self) -> None:
        fixture = {
            "id": "chip_qualifier_fixture",
            "leader": "Tester",
            "tags": ["switching"],
            "state": {
                "public_notes": [
                    "Revealed Flame Wheel is chip, not a reason to panic-switch.",
                ],
            },
            "actions": [
                {
                    "id": "move_rock_slide",
                    "kind": "move",
                    "name": "Rock Slide",
                    "explanation": "Super-effective hit into the active threat.",
                    "public_tradeoff": "Coverage tempo.",
                },
                {
                    "id": "switch_skarmory",
                    "kind": "switch",
                    "name": "Switch to Skarmory",
                    "explanation": "Preserves the ace.",
                    "public_tradeoff": "Defensive pivot.",
                },
            ],
        }
        switch = score_action(fixture, fixture["actions"][1])
        rules = {c["rule"] for c in switch["contributions"]}
        self.assertIn("public_notes_chip_qualifier", rules)
        chip_contribution = next(
            c for c in switch["contributions"] if c["rule"] == "public_notes_chip_qualifier"
        )
        self.assertEqual(chip_contribution["delta"], -6)

    def test_public_notes_chip_qualifier_does_not_fire_on_unrelated_fixture(self) -> None:
        fixture = {
            "id": "no_chip_qualifier_fixture",
            "leader": "Tester",
            "tags": ["switching"],
            "state": {
                "public_notes": [
                    "Player has revealed Choice Specs lock; coverage might exist.",
                ],
            },
            "actions": [
                {
                    "id": "switch_skarmory",
                    "kind": "switch",
                    "name": "Switch to Skarmory",
                    "explanation": "Preserves the ace.",
                    "public_tradeoff": "Defensive pivot.",
                },
            ],
        }
        switch = score_action(fixture, fixture["actions"][0])
        rules = {c["rule"] for c in switch["contributions"]}
        self.assertNotIn("public_notes_chip_qualifier", rules)

    def test_public_notes_chip_qualifier_does_not_fire_on_move_actions(self) -> None:
        fixture = {
            "id": "chip_qualifier_move_fixture",
            "leader": "Tester",
            "tags": ["switching"],
            "state": {
                "public_notes": [
                    "Revealed Flame Wheel is chip, not a reason to panic-switch.",
                ],
            },
            "actions": [
                {
                    "id": "move_rock_slide",
                    "kind": "move",
                    "name": "Rock Slide",
                    "explanation": "Super-effective hit into the active threat.",
                    "public_tradeoff": "Coverage tempo.",
                },
            ],
        }
        move = score_action(fixture, fixture["actions"][0])
        rules = {c["rule"] for c in move["contributions"]}
        self.assertNotIn("public_notes_chip_qualifier", rules)


if __name__ == "__main__":
    unittest.main()
