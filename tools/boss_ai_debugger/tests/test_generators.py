from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.generators import POLICY_CARD_REFS, generate_scenarios
from tools.boss_ai_debugger.rom_scenarios import evaluate_batch
from tools.boss_ai_debugger.state_schema import validate_scenario_file


class GeneratorTests(unittest.TestCase):
    def test_spikes_spin_generation_is_deterministic(self) -> None:
        first = generate_scenarios(family="spikes_spin", count=5, seed=7)
        second = generate_scenarios(family="spikes_spin", count=5, seed=7)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 5)
        self.assertEqual(first[0]["family"], "spikes_spin")

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


if __name__ == "__main__":
    unittest.main()
