from __future__ import annotations

import unittest
from tools.debugger.proof_runner import build_proof_campaign, build_proof_card, command_record


class ProofRunnerTests(unittest.TestCase):
    def test_proof_card_executes_safe_fast_unified_command(self) -> None:
        report = build_proof_card(
            symptom="How much does grass regrowth heal at 300 hp?",
            execute=True,
            timeout_seconds=30,
        )

        self.assertEqual(report["kind"], "unified_debugger_proof_card")
        self.assertEqual(report["proof_depth"], "executed")
        self.assertTrue(report["passed"])
        self.assertIn("grass-regrowth", report["chosen_command"])

    def test_proof_campaign_classifies_routes_and_executes_case(self) -> None:
        report = build_proof_campaign(
            cases=(
                {
                    "id": "grass",
                    "command": "python -m tools.debugger grass-regrowth --max-total-hp 300",
                    "expected_exit_codes": [0],
                },
            ),
            include_all_routes=True,
            execute=True,
            timeout_seconds=30,
        )

        self.assertEqual(report["kind"], "unified_debugger_proof_campaign")
        self.assertTrue(report["valid"])
        self.assertGreaterEqual(report["route_row_count"], 35)
        self.assertGreaterEqual(report["blocked_reason_counts"]["placeholder_input"], 1)
        self.assertEqual(report["executed_unique_command_count"], 1)

    def test_proof_campaign_rejects_execute_all_routes_without_suite(self) -> None:
        report = build_proof_campaign(
            cases=(),
            include_all_routes=True,
            execute=True,
            timeout_seconds=30,
        )

        self.assertFalse(report["valid"])
        self.assertIn("--execute with --all-routes requires --suite", report["validation_errors"][0])
        self.assertEqual(report["executed_unique_command_count"], 0)

    def test_proof_campaign_rejects_command_limit_truncation(self) -> None:
        report = build_proof_campaign(
            cases=(
                {
                    "id": "grass",
                    "command": "python -m tools.debugger grass-regrowth --max-total-hp 300",
                },
                {
                    "id": "mirror",
                    "command": "python -m tools.debugger content-mirror --source-file maps\\NewBarkTown.asm",
                },
            ),
            execute=True,
            max_commands=1,
            timeout_seconds=30,
        )

        self.assertFalse(report["valid"])
        self.assertEqual(report["status_counts"]["not_run_limit"], 1)

    def test_proof_campaign_enforces_expected_disposition(self) -> None:
        report = build_proof_campaign(
            cases=(
                {
                    "id": "wrong_expectation",
                    "command": "python -m tools.debugger grass-regrowth --max-total-hp 300",
                    "expected_exit_codes": [0],
                    "expected_disposition": "discrepancy_found",
                },
            ),
            execute=True,
            timeout_seconds=30,
        )

        self.assertFalse(report["valid"])
        self.assertEqual(report["status_counts"]["passed"], 1)
        self.assertEqual(len(report["expectation_errors"]), 1)

    def test_proof_command_records_block_reasons(self) -> None:
        placeholder = command_record("python -m tools.debugger triage --symptom <symptom>")
        shell = command_record("python tools\\audit\\check_release_smoke.py & git status")

        self.assertFalse(placeholder["safe"])
        self.assertEqual(placeholder["blocked_reason"], "placeholder_input")
        self.assertFalse(shell["safe"])
        self.assertEqual(shell["blocked_reason"], "shell_metacharacter")
