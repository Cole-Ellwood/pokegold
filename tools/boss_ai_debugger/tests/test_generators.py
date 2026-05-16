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

    def test_active_revealed_spin_prefers_live_damage_over_extra_spikes(self) -> None:
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

        self.assertEqual(result["best_action_id"], "move_sludge_bomb")
        self.assertEqual(result["probabilities"]["move_spikes"], 0.0)

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

    def test_capped_spikes_does_not_roll_failed_fourth_click(self) -> None:
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
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
