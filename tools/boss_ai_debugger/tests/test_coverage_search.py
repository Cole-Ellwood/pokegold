from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.coverage_search import mutate_scenario, run_coverage_guided_search
from tools.boss_ai_debugger.generators import generate_scenarios, write_jsonl
from tools.boss_ai_debugger.state_schema import validate_scenario_file


class CoverageSearchTests(unittest.TestCase):
    def test_coverage_search_mutates_public_scenarios(self) -> None:
        seeds = generate_scenarios(family="all", count=4, seed=3)

        result = run_coverage_guided_search(
            seed_scenarios=seeds,
            rounds=1,
            per_seed=2,
            seed=9,
            generated_count=2,
            keep=5,
        )

        self.assertGreater(result["report"]["candidate_count"], len(seeds))
        self.assertLessEqual(len(result["scenarios"]), 5)
        self.assertIn("coverage_guided", result["report"]["candidate_policy_tag_counts"])
        for scenario in result["scenarios"]:
            if "coverage_search" in scenario:
                self.assertTrue(scenario["coverage_search"]["public_info_only"])

    def test_newest_mastery_mutations_add_public_policy_tags(self) -> None:
        seed = generate_scenarios(family="cashout_board_delta", count=1, seed=12)[0]

        resisted = mutate_scenario(
            seed,
            mutation="price_resisted_explosion_board_delta",
            round_index=0,
            mutation_index=0,
            seed=12,
        )
        reversible = mutate_scenario(
            seed,
            mutation="prefer_reversible_before_irreversible",
            round_index=0,
            mutation_index=1,
            seed=12,
        )

        self.assertIn(
            "resisted_explosion_board_delta",
            resisted["expectation"]["policy_tags"],
        )
        self.assertIn(
            "coverage_resisted_explosion_free_owner",
            resisted["expectation"]["condition_tags"],
        )
        self.assertIn(
            "reversible_before_irreversible",
            reversible["expectation"]["policy_tags"],
        )
        self.assertTrue(resisted["coverage_search"]["public_info_only"])

    def test_cli_coverage_search_writes_selected_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            seed_path = Path(tmp) / "seeds.jsonl"
            out = Path(tmp) / "selected.jsonl"
            report = Path(tmp) / "report.json"
            write_jsonl(generate_scenarios(family="all", count=4, seed=4), seed_path)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                code = debugger_main(
                    [
                        "coverage-search",
                        "--scenarios",
                        str(seed_path),
                        "--rounds",
                        "1",
                        "--per-seed",
                        "2",
                        "--generated-count",
                        "2",
                        "--keep",
                        "5",
                        "--out",
                        str(out),
                        "--json-out",
                        str(report),
                    ]
                )
            validation = validate_scenario_file(out)

            self.assertEqual(code, 0)
            self.assertTrue(validation["valid"])
            self.assertTrue(report.exists())
            self.assertIn("Boss AI coverage-guided search", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
