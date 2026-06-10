from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.generators import (
    POLICY_CARD_REFS,
    PUBLIC_POLICY_FAMILIES,
    generate_scenarios,
    generate_scenarios_compact,
    materialized_spikes_spin_rom_deltas,
)
from tools.boss_ai_debugger.rom_scenarios import evaluate_batch, select_move
from tools.boss_ai_debugger.state_schema import validate_scenario_file


class GeneratorTests(unittest.TestCase):
    def test_spikes_spin_generation_is_deterministic(self) -> None:
        first = generate_scenarios(family="spikes_spin", count=5, seed=7)
        second = generate_scenarios(family="spikes_spin", count=5, seed=7)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 5)
        self.assertEqual(first[0]["family"], "spikes_spin")
        self.assertRegex(first[0]["state_hash"], r"^[0-9A-F]{64}$")
        self.assertIn("rom_sha256", first[0])
        self.assertIn("symbols_sha256", first[0])
        self.assertRegex(first[0]["class_id"], r"^csc_[0-9A-F]{20}$")
        self.assertEqual(first[0]["class_id"], first[0]["canonical_state_class"]["class_id"])
        self.assertTrue(first[0]["canonical_state_class"]["valid"])

    def test_generated_scenarios_validate_and_batch_evaluate(self) -> None:
        scenarios = generate_scenarios(family="all", count=20, seed=11)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "generated.jsonl"
            path.write_text(
                "\n".join(__import__("json").dumps(row) for row in scenarios) + "\n",
                encoding="utf-8",
            )
            validation = validate_scenario_file(path)

        report = evaluate_batch(scenarios)

        self.assertTrue(validation["valid"])
        self.assertEqual(report["scenario_count"], 20)
        self.assertGreater(report["scenarios_per_minute"], 0)

    def test_compact_generation_matches_rendered_generation_without_stamp_fields(self) -> None:
        compact = generate_scenarios_compact(family="all", count=80, seed=23)
        rendered = generate_scenarios(family="all", count=80, seed=23)
        stamp_keys = {
            "generator_source",
            "rom",
            "rom_sha256",
            "symbols",
            "symbols_sha256",
            "map",
            "map_sha256",
            "rule_map_sha256",
            "source_tree_sha256",
            "dirty_diff_hash",
            "state_hash",
            "canonical_state_class",
            "class_id",
            "class_fingerprint",
        }

        stripped = [
            {key: value for key, value in scenario.items() if key not in stamp_keys}
            for scenario in rendered
        ]

        self.assertEqual(compact, stripped)

    def test_mastery_policy_generation_covers_policy_cards(self) -> None:
        scenarios = generate_scenarios(
            family="mastery_policy",
            count=len(POLICY_CARD_REFS),
            seed=13,
        )

        refs = {
            scenario["expectation"]["evidence_refs"][0]
            for scenario in scenarios
        }
        report = evaluate_batch(scenarios)

        self.assertEqual(refs, set(POLICY_CARD_REFS.values()))
        self.assertEqual(report["scenario_count"], len(POLICY_CARD_REFS))
        self.assertEqual(report["reviewable_count"], 0)

    def test_policy_status_placeholders_carry_public_state_tags(self) -> None:
        mastery = generate_scenarios(family="mastery_policy", count=8, seed=13)
        branch_tags = set(mastery[1]["expectation"]["condition_tags"])
        cashout_tags = set(mastery[2]["expectation"]["condition_tags"])
        hazard_tags = set(mastery[3]["expectation"]["condition_tags"])
        sleep_tags = set(mastery[6]["expectation"]["condition_tags"])
        support_tags = set(mastery[7]["expectation"]["condition_tags"])
        setup = generate_scenarios(family="setup_heal", count=3, seed=13)[2]
        prediction = generate_scenarios(family="prediction_mix", count=1, seed=13)[0]

        self.assertIn("status_absorber_named", branch_tags)
        self.assertIn("resisted_explosion_free_owner", cashout_tags)
        self.assertIn("spikes_layers_1", hazard_tags)
        self.assertIn("active_revealed_rapid_spin", hazard_tags)
        self.assertIn("active_target_already_statused", sleep_tags)
        self.assertIn("active_target_already_statused", support_tags)
        self.assertIn(
            "active_target_already_statused",
            setup["expectation"]["condition_tags"],
        )
        self.assertIn(
            "status_absorber_named",
            prediction["expectation"]["condition_tags"],
        )

    def test_public_policy_families_generate_reviewable_cases(self) -> None:
        for family in PUBLIC_POLICY_FAMILIES:
            with self.subTest(family=family):
                scenarios = generate_scenarios(family=family, count=6, seed=17)

                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / f"{family}.jsonl"
                    path.write_text(
                        "\n".join(__import__("json").dumps(row) for row in scenarios)
                        + "\n",
                        encoding="utf-8",
                    )
                    validation = validate_scenario_file(path)
                report = evaluate_batch(scenarios)

                self.assertTrue(validation["valid"])
                self.assertEqual({scenario["family"] for scenario in scenarios}, {family})
                self.assertGreater(report["reviewable_count"], 0)

    def test_all_generation_includes_broad_public_policy_families(self) -> None:
        scenarios = generate_scenarios(family="all", count=60, seed=19)
        families = {scenario["family"] for scenario in scenarios}

        for family in PUBLIC_POLICY_FAMILIES:
            self.assertIn(family, families)

    def test_cashout_board_delta_generation_covers_newest_mastery_cases(self) -> None:
        scenarios = generate_scenarios(family="cashout_board_delta", count=4, seed=23)
        case_ids = {scenario["policy_case"] for scenario in scenarios}
        tags = {
            tag
            for scenario in scenarios
            for tag in scenario["expectation"]["policy_tags"]
        }
        condition_tags_by_case = {
            scenario["policy_case"]: set(scenario["expectation"]["condition_tags"])
            for scenario in scenarios
        }

        self.assertEqual(
            case_ids,
            {
                "reversible_before_irreversible",
                "resisted_explosion_free_owner",
                "explosion_into_ghost_branch",
                "sleep_plus_cashout_package",
            },
        )
        self.assertIn("reversible_before_irreversible", tags)
        self.assertIn("resisted_explosion_board_delta", tags)
        self.assertIn("role_package_ledger", tags)
        self.assertIn(
            "active_target_already_statused",
            condition_tags_by_case["reversible_before_irreversible"],
        )
        self.assertIn(
            "active_target_already_statused",
            condition_tags_by_case["explosion_into_ghost_branch"],
        )

    def test_support_handoff_generation_includes_phaze_setup_boundary(self) -> None:
        scenarios = generate_scenarios(family="support_handoff", count=4, seed=1)
        scenario = find_scenario(
            scenarios,
            "generated_support_handoff_1_00003_phaze_loop_over_setup_greed_boundary",
        )

        self.assertEqual(scenario["tier"], "late")
        self.assertEqual(
            [move["id"] for move in scenario["moves"]],
            [
                "move_setup_greed",
                "move_roar_loop",
                "move_spikes_reset",
                "move_switch_away",
            ],
        )
        self.assertIn("phaze_loop_live", scenario["expectation"]["condition_tags"])
        self.assertEqual(select_move(scenario)["best_action_id"], "move_roar_loop")

    def test_support_handoff_generation_includes_public_read_probe_cases(self) -> None:
        scenarios = generate_scenarios(family="support_handoff", count=9, seed=1)
        cases = {scenario["policy_case"]: scenario for scenario in scenarios}

        self.assertIn("public_read_poison_full_probe", cases)
        self.assertIn("public_read_poison_half_probe", cases)
        self.assertIn("public_read_physical_choice_probe", cases)
        self.assertIn("public_read_ramp_resisted_probe", cases)
        self.assertIn("public_read_repeated_switch_probe", cases)
        self.assertIn(
            "player_full_poison_type",
            cases["public_read_poison_full_probe"]["expectation"]["condition_tags"],
        )
        self.assertIn(
            "choice_immune_seen_species",
            cases["public_read_physical_choice_probe"]["expectation"]["condition_tags"],
        )
        self.assertIn(
            "player_fire_ramp_probe",
            cases["public_read_ramp_resisted_probe"]["expectation"]["condition_tags"],
        )

    def test_switch_sack_defensive_sack_is_stay_action(self) -> None:
        scenario = find_scenario(
            generate_scenarios(family="switch_sack", count=3, seed=1),
            "generated_switch_sack_1_00001_defensive_sack_for_safe_entry",
        )
        move_by_id = {move["id"]: move for move in scenario["moves"]}

        self.assertEqual(scenario["tier"], "late")
        self.assertEqual(move_by_id["move_defensive_sack"]["kind"], "move")
        self.assertEqual(scenario["expectation"]["best_action_ids"], ["move_defensive_sack"])

    def test_active_revealed_spin_with_reserve_ghost_keeps_third_spikes_live(self) -> None:
        scenario = spikes_spin_score_scenario(
            tier="mid",
            layers=2,
            active_revealed_spin=True,
            active_ghost=True,
            foresighted=True,
            reserve_ghost=True,
            bench_revealed_spin=True,
            active_species_prior=True,
        )

        result = select_move(scenario)

        self.assertEqual(result["best_action_id"], "move_spikes")
        self.assertGreater(
            result["probabilities"]["move_spikes"],
            result["probabilities"]["move_sludge_bomb"],
        )
        self.assertEqual(result["probabilities"]["move_surf"], 0.0)

    def test_generated_reserve_ghost_softens_revealed_spin_risk(self) -> None:
        scenarios = generate_scenarios(family="all", count=128, seed=5312026)
        scenario = find_scenario(scenarios, "generated_spikes_spin_5312026_00010")

        self.assertEqual(scenario["id"], "generated_spikes_spin_5312026_00010")
        self.assertIn(
            "active_revealed_rapid_spin",
            scenario["expectation"]["condition_tags"],
        )
        self.assertIn(
            "reserve_ghost_available",
            scenario["expectation"]["condition_tags"],
        )
        self.assertIn("move_spikes", scenario["expectation"]["best_action_ids"])
        self.assertNotIn(
            "move_spikes",
            scenario["expectation"].get("bad_action_ids", []),
        )

    def test_soft_spin_risk_uses_materialized_score_best(self) -> None:
        scenarios = generate_scenarios(family="all", count=128, seed=5312026)
        scenario = find_scenario(scenarios, "generated_spikes_spin_5312026_00006")

        self.assertEqual(scenario["id"], "generated_spikes_spin_5312026_00006")
        self.assertIn(
            "active_revealed_rapid_spin",
            scenario["expectation"]["condition_tags"],
        )
        self.assertIn(
            "reserve_ghost_available",
            scenario["expectation"]["condition_tags"],
        )
        self.assertIn(
            "active_species_spin_prior",
            scenario["expectation"]["condition_tags"],
        )
        self.assertEqual(
            scenario["expectation"]["best_action_ids"],
            ["move_sludge_bomb"],
        )
        self.assertNotIn(
            "move_spikes",
            scenario["expectation"].get("bad_action_ids", []),
        )

    def test_no_spin_second_layer_keeps_spikes_live(self) -> None:
        scenario = spikes_spin_score_scenario(
            tier="late",
            layers=1,
            active_revealed_spin=False,
            active_ghost=False,
            foresighted=False,
            reserve_ghost=False,
            bench_revealed_spin=True,
            active_species_prior=False,
        )

        result = select_move(scenario)

        self.assertEqual(result["best_action_id"], "move_spikes")

    def test_revealed_bench_spinner_is_soft_third_layer_risk(self) -> None:
        scenario = find_scenario(
            generate_scenarios(family="spikes_spin", count=113, seed=20260531),
            "generated_spikes_spin_20260531_00112",
        )

        self.assertNotIn(
            "active_revealed_rapid_spin",
            scenario["expectation"]["condition_tags"],
        )
        self.assertIn(
            "bench_revealed_rapid_spin",
            scenario["expectation"]["condition_tags"],
        )
        self.assertIn("move_spikes", scenario["expectation"]["best_action_ids"])
        self.assertNotIn(
            "move_spikes",
            scenario["expectation"].get("bad_action_ids", []),
        )

    def test_active_species_spin_prior_does_not_create_immediate_pressure(self) -> None:
        scenario = spikes_spin_score_scenario(
            tier="late",
            layers=1,
            active_revealed_spin=False,
            active_ghost=False,
            foresighted=False,
            reserve_ghost=True,
            bench_revealed_spin=False,
            active_species_prior=True,
        )

        result = select_move(scenario)

        self.assertEqual(scenario["moves"][0]["deltas"], [])
        self.assertEqual(result["best_action_id"], "move_spikes")

    def test_capped_spikes_prefers_sludge_bomb_when_active_species_prior_is_live(self) -> None:
        scenario = spikes_spin_score_scenario(
            tier="late",
            layers=3,
            active_revealed_spin=True,
            active_ghost=False,
            foresighted=False,
            reserve_ghost=True,
            bench_revealed_spin=True,
            active_species_prior=True,
        )

        result = select_move(scenario)

        self.assertEqual(result["best_action_id"], "move_sludge_bomb")
        self.assertEqual(result["probabilities"]["move_spikes"], 0.0)
        self.assertTrue(result["moves"][0]["blocked"])

    def test_capped_spikes_active_species_prior_prefers_sludge_when_ghost_is_identified(self) -> None:
        scenario = spikes_spin_score_scenario(
            tier="mid",
            layers=3,
            active_revealed_spin=True,
            active_ghost=True,
            foresighted=True,
            reserve_ghost=False,
            bench_revealed_spin=False,
            active_species_prior=True,
        )

        result = select_move(scenario)

        self.assertEqual(result["best_action_id"], "move_sludge_bomb")
        self.assertEqual(result["probabilities"]["move_spikes"], 0.0)
        self.assertGreater(
            result["probabilities"]["move_sludge_bomb"],
            result["probabilities"]["move_surf"],
        )
        self.assertTrue(result["moves"][0]["blocked"])

    def test_cli_generate_writes_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "scenarios.jsonl"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "generate",
                        "--family",
                        "selector_edges",
                        "--count",
                        "3",
                        "--seed",
                        "3",
                        "--out",
                        str(out),
                    ]
                )

            rows = [line for line in out.read_text(encoding="utf-8").splitlines() if line]

        self.assertEqual(code, 0)
        self.assertEqual(len(rows), 3)
        self.assertIn("scenario generation complete", stdout.getvalue())


def spikes_spin_score_scenario(**kwargs: Any) -> dict[str, Any]:
    deltas = materialized_spikes_spin_rom_deltas(**kwargs)
    return {
        "id": "targeted_spikes_spin_score_case",
        "tier": kwargs["tier"],
        "moves": [
            {
                "id": "move_spikes",
                "name": "Spikes",
                "deltas": deltas["spikes"],
                "blocked": kwargs["layers"] >= 3,
                "lookahead_delta": 18,
            },
            {
                "id": "move_sludge_bomb",
                "name": "Sludge Bomb",
                "deltas": deltas["sludge_bomb"],
                "lookahead_delta": 18,
            },
            {
                "id": "move_surf",
                "name": "Surf",
                "deltas": deltas["surf"],
                "lookahead_delta": 18,
            },
            {
                "id": "move_explosion",
                "name": "Explosion",
                "deltas": deltas["explosion"],
                "lookahead_delta": 18,
            },
        ],
    }


def find_scenario(scenarios: list[dict[str, Any]], scenario_id: str) -> dict[str, Any]:
    for scenario in scenarios:
        if scenario["id"] == scenario_id:
            return scenario
    raise AssertionError(f"missing scenario {scenario_id}")


if __name__ == "__main__":
    unittest.main()
