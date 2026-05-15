from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.rom_scenarios import (
    evaluate_batch,
    evaluate_scenario,
    format_batch_report,
    load_scenario_batch,
)
from tools.boss_ai_preference.data import PreferenceDataError


def scenario(
    scenario_id: str,
    *,
    moves: list[dict] | None = None,
    expectation: dict | None = None,
) -> dict:
    return {
        "id": scenario_id,
        "tier": "late",
        "moves": moves
        or [
            {"id": "a", "name": "A"},
            {"id": "b", "name": "B"},
            {"id": "c", "name": "C"},
        ],
        "expectation": expectation or {},
    }


class RomBatchTests(unittest.TestCase):
    def test_matching_expected_best_is_pass(self) -> None:
        verdict = evaluate_scenario(
            scenario("pass", expectation={"best_action_ids": ["a"]})
        )

        self.assertEqual(verdict.verdict, "pass")
        self.assertEqual(verdict.severity, 0)

    def test_acceptable_top_is_reviewable(self) -> None:
        verdict = evaluate_scenario(
            scenario(
                "acceptable",
                expectation={
                    "best_action_ids": ["b"],
                    "acceptable_action_ids": ["a"],
                },
            )
        )

        self.assertEqual(verdict.verdict, "acceptable_top")
        self.assertGreater(verdict.severity, 0)

    def test_catastrophic_roll_ranks_above_best_never_rolled(self) -> None:
        report = evaluate_batch(
            [
                scenario(
                    "catastrophic",
                    expectation={
                        "best_action_ids": ["a"],
                        "catastrophic_action_ids": ["b"],
                    },
                ),
                scenario(
                    "never",
                    expectation={
                        "best_action_ids": ["c"],
                        "acceptable_action_ids": ["a"],
                    },
                ),
            ]
        )

        verdicts = report["verdicts"]
        self.assertEqual(verdicts[0]["scenario_id"], "catastrophic")
        self.assertEqual(verdicts[0]["verdict"], "catastrophic_roll")

    def test_expected_best_in_slot_three_can_be_never_rolled(self) -> None:
        verdict = evaluate_scenario(
            scenario("slot3", expectation={"best_action_ids": ["c"]})
        )

        self.assertEqual(verdict.verdict, "best_never_rolled")
        self.assertEqual(verdict.zero_probability_best_action_ids, ["c"])

    def test_all_moves_blocked_is_unready(self) -> None:
        verdict = evaluate_scenario(
            scenario(
                "blocked",
                moves=[
                    {"id": "a", "name": "A", "blocked": True},
                    {"id": "b", "name": "B", "blocked": True},
                ],
                expectation={"best_action_ids": ["a"]},
            )
        )

        self.assertEqual(verdict.verdict, "no_rom_choice")

    def test_missing_expectation_is_nonfatal(self) -> None:
        verdict = evaluate_scenario(scenario("missing"))

        self.assertEqual(verdict.verdict, "needs_expectation")
        self.assertEqual(verdict.severity, 0)

    def test_unknown_expected_action_raises(self) -> None:
        with self.assertRaisesRegex(PreferenceDataError, "unknown action"):
            evaluate_scenario(
                scenario("unknown", expectation={"best_action_ids": ["missing"]})
            )

    def test_jsonl_batch_and_external_expectations_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenarios_path = Path(tmp) / "scenarios.jsonl"
            expectations_path = Path(tmp) / "expectations.json"
            scenarios_path.write_text(
                json.dumps(
                    {
                        "id": "external",
                        "tier": "late",
                        "moves": [{"id": "a", "name": "A"}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            expectations_path.write_text(
                json.dumps(
                    {
                        "expectations": [
                            {
                                "scenario_id": "external",
                                "expect": {"best_action_ids": ["a"]},
                                "policy_tags": ["batch"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            loaded = load_scenario_batch(scenarios_path, expectations_path)

        self.assertEqual(loaded[0]["expectation"]["best_action_ids"], ["a"])
        self.assertEqual(loaded[0]["expectation"]["policy_tags"], ["batch"])

    def test_batch_report_has_throughput_metrics(self) -> None:
        report = evaluate_batch(
            [scenario("pass", expectation={"best_action_ids": ["a"]})]
        )

        self.assertEqual(report["scenario_count"], 1)
        self.assertGreater(report["scenarios_per_minute"], 0)

    def test_report_keeps_mastery_note_context(self) -> None:
        report = evaluate_batch(
            [
                scenario(
                    "context",
                    expectation={
                        "best_action_ids": ["c"],
                        "policy_tags": ["hazard_loop"],
                        "condition_tags": ["spinner_active"],
                        "lesson_type": "sequence_policy",
                        "evidence_refs": [
                            "docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md"
                        ],
                        "why": "preserve the spiker unless the spin branch is priced",
                        "answer_changing_information": [
                            "Starmie attacks instead of spins"
                        ],
                    },
                )
            ]
        )
        item = report["verdicts"][0]
        text = format_batch_report(report, limit=1)

        self.assertEqual(
            item["evidence_refs"][0],
            "docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md",
        )
        self.assertIn(
            "refs=docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md",
            text,
        )
        self.assertIn("policy: preserve the spiker", text)
        self.assertIn("changes answer if: Starmie attacks instead of spins", text)

    def test_cli_writes_json_and_failure_flag_controls_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenarios_path = Path(tmp) / "scenarios.json"
            json_out = Path(tmp) / "report.json"
            scenarios_path.write_text(
                json.dumps(
                    {
                        "scenarios": [
                            scenario("cli", expectation={"best_action_ids": ["c"]})
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with redirect_stdout(io.StringIO()):
                pass_code = debugger_main(
                    [
                        "batch-simulate",
                        "--scenarios",
                        str(scenarios_path),
                        "--json-out",
                        str(json_out),
                        "--quiet",
                    ]
                )
            with redirect_stdout(io.StringIO()):
                fail_code = debugger_main(
                    [
                        "batch-simulate",
                        "--scenarios",
                        str(scenarios_path),
                        "--fail-on-reviewable-mismatch",
                        "--quiet",
                    ]
                )

            report = json.loads(json_out.read_text(encoding="utf-8"))

        self.assertEqual(pass_code, 0)
        self.assertEqual(fail_code, 1)
        self.assertEqual(report["scenario_count"], 1)


if __name__ == "__main__":
    unittest.main()
