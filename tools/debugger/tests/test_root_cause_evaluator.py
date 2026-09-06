from __future__ import annotations

import copy
import unittest
from unittest.mock import Mock

from tools.audit.root_cause_evaluator import score_diagnosis
from tools.debugger.evidence import evidence_atom


class RootCauseEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.basis = {
            "rom_sha256": "A" * 64,
            "symbols_sha256": "B" * 64,
            "source_tree_sha256": "C" * 64,
            "backend": "pyboy-test",
            "state_basis": {
                "initial_state_sha256": "D" * 64,
                "input_log_sha256": "E" * 64,
                "rng": {"seed": 0},
            },
        }
        self.location = {
            "source_file": "engine/unit.asm", "source_symbol": "Caller",
            "source_line": 12,
        }
        self.report = {
            **copy.deepcopy(self.basis),
            "proof_status": "complete",
            "repro_command": "python replay.py recording.json",
            "known_limits": ["unit fixture"],
            "evidence_atoms": [evidence_atom(
                claim_type="diagnosis.root_cause", origin="investigate",
                observation_type="controlled_runtime_comparison",
                proof_status="instruction_observed", precision=self.location,
                detail={
                    "invariant": "d remains the type contribution until consumed",
                    "causal_chain": [
                        {"trace": "broken.jsonl", "seq": 4},
                        {"trace": "broken.jsonl", "seq": 8},
                    ],
                    "reproducer": "minimal.json",
                    "regression": "regression.json",
                    "scope": "recorded state and inputs",
                    "uncertainty": "no claim outside the fixture",
                },
            )],
        }
        self.checks = {
            "failure_reproduced": True,
            "causal_chain_replayed": True,
            "alternatives_rejected": True,
            "minimized_reproducer_replayed": True,
            "regression_failed_broken": True,
            "regression_passed_control": True,
        }
        self.verify = Mock(return_value=self.checks)

    def score(self, report=None, *, causes=None, assistance=()):
        return score_diagnosis(
            self.report if report is None else report,
            expected_basis=self.basis,
            accepted_causes=[self.location] if causes is None else causes,
            verify_replay=self.verify,
            assistance_events=assistance,
        )

    def test_accepted_cause_requires_independent_replay(self):
        result = self.score()
        self.assertTrue(result["solved"])
        self.assertTrue(result["autonomous"])
        self.assertFalse(result["false_proven_claim"])
        self.verify.assert_called_once_with(self.report)

    def test_correct_file_wrong_instruction_is_rejected_before_replay(self):
        self.report["evidence_atoms"][0]["precision"]["source_line"] = 19
        result = self.score()
        self.assertFalse(result["solved"])
        self.assertTrue(result["false_proven_claim"])
        self.assertIn("cause_location_mismatch", result["problems"])
        self.verify.assert_not_called()

    def test_stale_or_missing_identity_is_rejected_before_replay(self):
        for key in self.basis:
            for mutation in ("different", "missing"):
                with self.subTest(key=key, mutation=mutation):
                    report = copy.deepcopy(self.report)
                    if mutation == "missing":
                        del report[key]
                    else:
                        report[key] = "stale"
                    self.assertFalse(self.score(report)["solved"])
        self.verify.assert_not_called()

    def test_missing_named_evidence_is_rejected_before_replay(self):
        for key in ("invariant", "causal_chain", "reproducer", "regression",
                    "scope", "uncertainty"):
            with self.subTest(key=key):
                report = copy.deepcopy(self.report)
                del report["evidence_atoms"][0]["detail"][key]
                self.assertFalse(self.score(report)["solved"])
        self.verify.assert_not_called()

    def test_packet_success_and_markers_are_not_root_cause_proof(self):
        result = self.score({"passed": True, "valid": True,
                             "stdout": "root cause proven; predicate satisfied"})
        self.assertFalse(result["solved"])
        self.assertFalse(result["false_proven_claim"])
        self.verify.assert_not_called()

    def test_unexecuted_root_cause_claim_is_rejected(self):
        atom = self.report["evidence_atoms"][0]
        for status in ("planned_only", "mirror_passed", None):
            with self.subTest(status=status):
                atom["proof_status"] = status
                result = self.score()
                self.assertFalse(result["solved"])
                self.assertTrue(result["false_proven_claim"])
        self.verify.assert_not_called()

    def test_report_cannot_self_certify_replay_or_suppress_a_failed_check(self):
        self.report["validation"] = dict(self.checks)
        for key in self.checks:
            for value in (False, None, "true", 1):
                with self.subTest(key=key, value=value):
                    checks = dict(self.checks)
                    checks[key] = value
                    self.verify.return_value = checks
                    result = self.score()
                    self.assertFalse(result["solved"])
                    self.assertIn(key, result["problems"])

    def test_no_claim_on_unconfirmed_report_is_not_a_failed_bug_diagnosis(self):
        result = self.score({"passed": True, "evidence_atoms": []}, causes=[])
        self.assertTrue(result["control_passed"])
        self.assertFalse(result["solved"])
        self.assertFalse(result["false_proven_claim"])
        self.verify.assert_not_called()

    def test_invented_cause_for_unconfirmed_report_is_rejected(self):
        result = self.score(causes=[])
        self.assertFalse(result["control_passed"])
        self.assertTrue(result["false_proven_claim"])
        self.verify.assert_not_called()

    def test_assisted_correct_diagnosis_does_not_count_as_autonomous(self):
        result = self.score(assistance=("operator supplied suspect symbol",))
        self.assertTrue(result["solved"])
        self.assertFalse(result["autonomous"])

    def test_replay_error_fails_closed(self):
        self.verify.side_effect = RuntimeError("recording cannot be replayed")
        result = self.score()
        self.assertFalse(result["solved"])
        self.assertTrue(result["false_proven_claim"])
        self.assertIn("recording cannot be replayed", " ".join(result["problems"]))


if __name__ == "__main__":
    unittest.main()
