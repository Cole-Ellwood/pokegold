from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.headless_battle.switch_expectations import (
    ScenarioComparison,
    SwitchExpectation,
    SwitchExpectationError,
    build_parser,
    compare_batch_against_expectations,
    compare_verdict_to_expectation,
    format_violation_report,
    load_switch_expectations,
    main,
    parse_switch_expectations,
)


def _verdict(
    scenario_id: str,
    *,
    status: str = "pass",
    proposed_switch: bool = True,
    confidence: int = 0x40,
    observation_status: str = "switch_proposal_observed",
    observed_switch_path: bool = True,
    switch_probability: float | None = 0.55,
    probability_exact: bool = True,
    switch_roll_available: bool = True,
    switch_roll_reason: str | None = None,
    reason: str | None = None,
) -> dict:
    rom = {
        "switch_confidence": confidence,
        "observation_status": observation_status,
        "observed_switch_path": observed_switch_path,
        "proposed_switch": proposed_switch,
        "actual_switch": False,
    }
    if switch_roll_available:
        switch_roll = {
            "available": True,
            "confidence": confidence,
            "switch_probability": switch_probability,
            "probability_exact": probability_exact,
            "proof_status": "source_mirrored_final_switch_roll_from_observed_confidence",
        }
    else:
        switch_roll = {
            "available": False,
            "confidence": 0,
            "reason": switch_roll_reason or "no_switch_dispatch_observation",
            "proof_status": "no_final_switch_roll_observed",
        }
    verdict: dict = {
        "scenario_id": scenario_id,
        "status": status,
        "family": "switch_sack",
        "rom": rom,
        "switch_roll": switch_roll,
    }
    if reason is not None:
        verdict["reason"] = reason
    return verdict


def _batch_report(verdicts: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "kind": "headless_battle_batch_switch_materialize",
        "base_route": "shared_switch_loop",
        "base_state": "stub.state",
        "materializations_per_minute": 60.0,
        "summary": {
            "scenario_count": len(verdicts),
            "observed_switches": sum(
                1
                for v in verdicts
                if (v.get("rom") or {}).get("observed_switch_path")
            ),
            "probability_exact_count": sum(
                1
                for v in verdicts
                if (v.get("switch_roll") or {}).get("probability_exact")
            ),
            "error_count": sum(1 for v in verdicts if v["status"] == "error"),
            "skipped_count": 0,
        },
        "verdicts": verdicts,
        "known_limits": ["test limit"],
    }


class ParseSwitchExpectationsTests(unittest.TestCase):
    def test_parse_envelope_with_full_row(self) -> None:
        data = {
            "schema_version": 1,
            "expectations": [
                {
                    "scenario_id": "a",
                    "expected": {
                        "action": "stay",
                        "switch_probability_max": 0.10,
                    },
                    "rationale": "switch loses tempo",
                },
            ],
        }
        result = parse_switch_expectations(data)
        self.assertEqual(set(result), {"a"})
        exp = result["a"]
        self.assertEqual(exp.action, "stay")
        self.assertEqual(exp.switch_probability_max, 0.10)
        self.assertEqual(exp.rationale, "switch loses tempo")
        self.assertIsNone(exp.switch_probability_min)

    def test_parse_flat_list_shape(self) -> None:
        data = [
            {"scenario_id": "a", "expected": {"action": "switch"}},
            {"scenario_id": "b", "expected": {"action": "stay"}},
        ]
        result = parse_switch_expectations(data)
        self.assertEqual(set(result), {"a", "b"})

    def test_parse_single_row_shape(self) -> None:
        row = {"scenario_id": "solo", "expected": {"action": "switch"}}
        result = parse_switch_expectations(row)
        self.assertEqual(set(result), {"solo"})

    def test_parse_rejects_invalid_action(self) -> None:
        with self.assertRaisesRegex(SwitchExpectationError, "action must be one of"):
            parse_switch_expectations(
                [{"scenario_id": "a", "expected": {"action": "maybe"}}]
            )

    def test_parse_rejects_invalid_probability_bound(self) -> None:
        with self.assertRaisesRegex(SwitchExpectationError, "must be between 0 and 1"):
            parse_switch_expectations(
                [
                    {
                        "scenario_id": "a",
                        "expected": {"action": "stay", "switch_probability_max": 1.5},
                    }
                ]
            )

    def test_parse_rejects_min_greater_than_max(self) -> None:
        with self.assertRaisesRegex(SwitchExpectationError, "must not exceed"):
            parse_switch_expectations(
                [
                    {
                        "scenario_id": "a",
                        "expected": {
                            "action": "switch",
                            "switch_probability_min": 0.8,
                            "switch_probability_max": 0.5,
                        },
                    }
                ]
            )

    def test_parse_rejects_duplicate_scenario_id(self) -> None:
        with self.assertRaisesRegex(SwitchExpectationError, "duplicate"):
            parse_switch_expectations(
                [
                    {"scenario_id": "a", "expected": {"action": "stay"}},
                    {"scenario_id": "a", "expected": {"action": "switch"}},
                ]
            )

    def test_parse_rejects_bool_for_bounds(self) -> None:
        with self.assertRaisesRegex(SwitchExpectationError, "must be a number"):
            parse_switch_expectations(
                [
                    {
                        "scenario_id": "a",
                        "expected": {"action": "stay", "switch_probability_max": True},
                    }
                ]
            )

    def test_parse_rejects_top_level_string(self) -> None:
        with self.assertRaisesRegex(SwitchExpectationError, "must be a list of rows"):
            parse_switch_expectations("not a dict")

    def test_load_switch_expectations_from_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expectations.json"
            path.write_text(
                json.dumps(
                    {
                        "expectations": [
                            {
                                "scenario_id": "a",
                                "expected": {"action": "stay"},
                                "rationale": "",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = load_switch_expectations(path)
        self.assertEqual(set(result), {"a"})


class CompareVerdictToExpectationTests(unittest.TestCase):
    def _exp(
        self,
        action: str,
        *,
        prob_max: float | None = None,
        prob_min: float | None = None,
        rationale: str = "",
    ) -> SwitchExpectation:
        return SwitchExpectation(
            scenario_id="x",
            action=action,
            switch_probability_max=prob_max,
            switch_probability_min=prob_min,
            rationale=rationale,
        )

    def test_matching_action_with_no_bounds_passes(self) -> None:
        result = compare_verdict_to_expectation(
            _verdict("x", proposed_switch=True),
            self._exp("switch"),
        )
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.observed_action, "switch")
        self.assertEqual(result.expected_action, "switch")
        self.assertEqual(result.reason, "")

    def test_action_mismatch_fails(self) -> None:
        result = compare_verdict_to_expectation(
            _verdict("x", proposed_switch=True),
            self._exp("stay"),
        )
        self.assertEqual(result.status, "fail")
        self.assertIn("expected action='stay'", result.reason)
        self.assertIn("observed='switch'", result.reason)

    def test_action_match_but_probability_above_max_fails(self) -> None:
        result = compare_verdict_to_expectation(
            _verdict("x", proposed_switch=True, switch_probability=0.65),
            self._exp("switch", prob_max=0.40),
        )
        self.assertEqual(result.status, "fail")
        self.assertIn("switch_probability=0.6500", result.reason)
        self.assertIn("switch_probability_max=0.4000", result.reason)

    def test_action_match_but_probability_below_min_fails(self) -> None:
        result = compare_verdict_to_expectation(
            _verdict("x", proposed_switch=True, switch_probability=0.05),
            self._exp("switch", prob_min=0.20),
        )
        self.assertEqual(result.status, "fail")
        self.assertIn("switch_probability_min=0.2000", result.reason)

    def test_unavailable_switch_roll_with_bound_fails(self) -> None:
        result = compare_verdict_to_expectation(
            _verdict(
                "x",
                proposed_switch=False,
                observed_switch_path=False,
                observation_status="no_decision_observed",
                switch_roll_available=False,
                switch_roll_reason="no_switch_dispatch_observation",
            ),
            self._exp("stay", prob_max=0.10),
        )
        self.assertEqual(result.status, "fail")
        self.assertIn("switch_roll_unavailable_for_bound_check", result.reason)

    def test_unavailable_switch_roll_without_bound_still_passes_when_action_matches(self) -> None:
        result = compare_verdict_to_expectation(
            _verdict(
                "x",
                proposed_switch=False,
                observed_switch_path=False,
                observation_status="no_decision_observed",
                switch_roll_available=False,
                switch_roll_reason="no_switch_dispatch_observation",
            ),
            self._exp("stay"),
        )
        # No bound; ROM observation shows "stay" (no proposed switch) which
        # matches the expectation.
        self.assertEqual(result.status, "pass")

    def test_error_verdict_status_is_error(self) -> None:
        result = compare_verdict_to_expectation(
            _verdict(
                "x",
                status="error",
                reason="no observation within watch_frames",
                proposed_switch=False,
                observed_switch_path=False,
                switch_roll_available=False,
            ),
            self._exp("stay"),
        )
        self.assertEqual(result.status, "error")
        self.assertEqual(result.reason, "no observation within watch_frames")
        self.assertIsNone(result.observed_action)


class CompareBatchAgainstExpectationsTests(unittest.TestCase):
    def test_summary_counts_all_categories(self) -> None:
        report = _batch_report(
            [
                _verdict("pass_id"),
                _verdict(
                    "fail_action",
                    proposed_switch=False,
                    observation_status="chosen_move_observed_without_switch_proposal",
                ),
                _verdict(
                    "fail_bound",
                    proposed_switch=True,
                    switch_probability=0.99,
                ),
                _verdict(
                    "error_id",
                    status="error",
                    reason="x",
                    observed_switch_path=False,
                    switch_roll_available=False,
                ),
                _verdict("unscoped"),  # no matching expectation
            ]
        )
        expectations = parse_switch_expectations(
            [
                {"scenario_id": "pass_id", "expected": {"action": "switch"}},
                {"scenario_id": "fail_action", "expected": {"action": "switch"}},
                {
                    "scenario_id": "fail_bound",
                    "expected": {"action": "switch", "switch_probability_max": 0.5},
                },
                {"scenario_id": "error_id", "expected": {"action": "stay"}},
                {"scenario_id": "missing_id", "expected": {"action": "switch"}},
            ]
        )
        comparison = compare_batch_against_expectations(report, expectations)
        self.assertEqual(comparison["summary"]["pass"], 1)
        self.assertEqual(comparison["summary"]["fail"], 2)
        self.assertEqual(comparison["summary"]["error"], 1)
        self.assertEqual(comparison["summary"]["no_expectation"], 1)
        # missing_id is in expectations but no verdict ran for it.
        self.assertEqual(comparison["summary"]["missing_scenario_ids"], ["missing_id"])
        self.assertEqual(
            comparison["kind"], "headless_battle_switch_expectations_comparison"
        )

    def test_no_expectation_status_for_unscoped_scenarios(self) -> None:
        report = _batch_report([_verdict("orphan")])
        comparison = compare_batch_against_expectations(report, {})
        self.assertEqual(comparison["summary"]["no_expectation"], 1)
        self.assertEqual(comparison["comparisons"][0]["status"], "no_expectation")


class FormatViolationReportTests(unittest.TestCase):
    def test_report_lists_violations_with_reasons(self) -> None:
        report = _batch_report(
            [
                _verdict("fail_id", proposed_switch=False),
                _verdict("ok_id"),
            ]
        )
        expectations = parse_switch_expectations(
            [
                {"scenario_id": "fail_id", "expected": {"action": "switch"},
                 "rationale": "Haunter must switch to Gengar"},
                {"scenario_id": "ok_id", "expected": {"action": "switch"}},
            ]
        )
        comparison = compare_batch_against_expectations(report, expectations)
        text = format_violation_report(comparison)
        self.assertIn("pass=1", text)
        self.assertIn("fail=1", text)
        self.assertIn("Violations (1)", text)
        self.assertIn("fail_id", text)
        self.assertIn("expected=switch observed=stay", text)
        self.assertIn("rationale: Haunter must switch to Gengar", text)

    def test_report_calls_out_missing_scenarios(self) -> None:
        report = _batch_report([_verdict("present")])
        expectations = parse_switch_expectations(
            [
                {"scenario_id": "present", "expected": {"action": "switch"}},
                {"scenario_id": "missing", "expected": {"action": "stay"}},
            ]
        )
        comparison = compare_batch_against_expectations(report, expectations)
        text = format_violation_report(comparison)
        self.assertIn("Expectations with no matching scenario (1):", text)
        self.assertIn("- missing", text)

    def test_report_calls_out_no_expectation_section(self) -> None:
        report = _batch_report([_verdict("orphan")])
        comparison = compare_batch_against_expectations(report, {})
        text = format_violation_report(comparison)
        self.assertIn("Scenarios with no expectation (1; informational", text)
        self.assertIn("- orphan", text)


class CliMainTests(unittest.TestCase):
    def _fake_batch_report(self) -> dict:
        return _batch_report(
            [
                _verdict("pass_id"),
                _verdict("fail_id", proposed_switch=False),
            ]
        )

    def _write_expectations(self, dir_path: Path) -> Path:
        out = dir_path / "expectations.json"
        out.write_text(
            json.dumps(
                {
                    "expectations": [
                        {"scenario_id": "pass_id", "expected": {"action": "switch"}},
                        {
                            "scenario_id": "fail_id",
                            "expected": {"action": "switch"},
                            "rationale": "demo",
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        return out

    def test_cli_prints_violation_report_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            expectations_path = self._write_expectations(Path(tmp))
            scenarios_path = Path(tmp) / "scenarios.jsonl"
            scenarios_path.write_text("[]", encoding="utf-8")
            with patch(
                "tools.headless_battle.switch_expectations.run_batch_switch_materialize",
                return_value=self._fake_batch_report(),
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = main(
                        [
                            "--scenarios",
                            str(scenarios_path),
                            "--expectations",
                            str(expectations_path),
                        ]
                    )
            text = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("Headless battle switch-expectations comparison", text)
        self.assertIn("pass=1", text)
        self.assertIn("fail=1", text)
        self.assertIn("Violations (1)", text)
        self.assertIn("fail_id", text)

    def test_cli_writes_json_out(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            expectations_path = self._write_expectations(tmp_path)
            scenarios_path = tmp_path / "scenarios.jsonl"
            scenarios_path.write_text("[]", encoding="utf-8")
            json_out = tmp_path / "comparison.json"
            with patch(
                "tools.headless_battle.switch_expectations.run_batch_switch_materialize",
                return_value=self._fake_batch_report(),
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = main(
                        [
                            "--scenarios",
                            str(scenarios_path),
                            "--expectations",
                            str(expectations_path),
                            "--json-out",
                            str(json_out),
                        ]
                    )
            data = json.loads(json_out.read_text(encoding="utf-8"))
        self.assertEqual(code, 0)
        self.assertEqual(data["summary"]["pass"], 1)
        self.assertEqual(data["summary"]["fail"], 1)
        self.assertEqual(
            data["kind"], "headless_battle_switch_expectations_comparison"
        )

    def test_cli_fail_on_violation_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            expectations_path = self._write_expectations(tmp_path)
            scenarios_path = tmp_path / "scenarios.jsonl"
            scenarios_path.write_text("[]", encoding="utf-8")
            with patch(
                "tools.headless_battle.switch_expectations.run_batch_switch_materialize",
                return_value=self._fake_batch_report(),
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = main(
                        [
                            "--scenarios",
                            str(scenarios_path),
                            "--expectations",
                            str(expectations_path),
                            "--fail-on-violation",
                        ]
                    )
        self.assertEqual(code, 1)

    def test_cli_fail_on_violation_returns_zero_when_all_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            expectations_path = tmp_path / "expectations.json"
            expectations_path.write_text(
                json.dumps(
                    [
                        {"scenario_id": "pass_id", "expected": {"action": "switch"}},
                    ]
                ),
                encoding="utf-8",
            )
            scenarios_path = tmp_path / "scenarios.jsonl"
            scenarios_path.write_text("[]", encoding="utf-8")
            with patch(
                "tools.headless_battle.switch_expectations.run_batch_switch_materialize",
                return_value=_batch_report([_verdict("pass_id")]),
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = main(
                        [
                            "--scenarios",
                            str(scenarios_path),
                            "--expectations",
                            str(expectations_path),
                            "--fail-on-violation",
                        ]
                    )
        self.assertEqual(code, 0)

    def test_cli_batch_json_out_writes_underlying_batch_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            expectations_path = self._write_expectations(tmp_path)
            scenarios_path = tmp_path / "scenarios.jsonl"
            scenarios_path.write_text("[]", encoding="utf-8")
            batch_out = tmp_path / "batch.json"
            with patch(
                "tools.headless_battle.switch_expectations.run_batch_switch_materialize",
                return_value=self._fake_batch_report(),
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = main(
                        [
                            "--scenarios",
                            str(scenarios_path),
                            "--expectations",
                            str(expectations_path),
                            "--batch-json-out",
                            str(batch_out),
                        ]
                    )
            self.assertEqual(code, 0)
            data = json.loads(batch_out.read_text(encoding="utf-8"))
        self.assertEqual(data["kind"], "headless_battle_batch_switch_materialize")
        self.assertEqual(len(data["verdicts"]), 2)


class CliParserTests(unittest.TestCase):
    def test_requires_scenarios_and_expectations(self) -> None:
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["--scenarios", "s.jsonl"])
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["--expectations", "e.json"])

    def test_parser_defaults(self) -> None:
        args = build_parser().parse_args(
            ["--scenarios", "s.jsonl", "--expectations", "e.json"]
        )
        self.assertEqual(args.limit, 0)
        self.assertFalse(args.json)
        self.assertEqual(args.json_out, "")
        self.assertEqual(args.batch_json_out, "")
        self.assertFalse(args.fail_on_violation)


if __name__ == "__main__":
    unittest.main()
