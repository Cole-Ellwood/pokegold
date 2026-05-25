from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.headless_battle.batch_switch import (
    SUMMARY_TEMPLATE,
    build_parser,
    format_batch_switch_table,
    main,
    run_batch_switch_materialize,
    summarize_batch_switch,
)


def _verdict(
    scenario_id: str,
    *,
    status: str = "pass",
    confidence: int | None = 0x40,
    observation_status: str = "switch_proposal_observed",
    observed_switch_path: bool = True,
    proposed_switch: bool = True,
    actual_switch: bool = False,
    switch_roll: dict | None = None,
    reason: str | None = None,
) -> dict:
    verdict: dict = {
        "scenario_id": scenario_id,
        "status": status,
        "family": "switch_sack",
        "expected_switch": True,
    }
    if status == "pass":
        verdict["rom_policy"] = {"verdict": "pass", "severity": 0, "reason": ""}
    verdict["rom"] = {
        "switch_confidence": confidence if confidence is not None else 0,
        "observation_status": observation_status,
        "observed_switch_path": observed_switch_path,
        "proposed_switch": proposed_switch,
        "actual_switch": actual_switch,
    }
    if switch_roll is None:
        switch_roll = {
            "available": True,
            "confidence": confidence,
            "switch_probability": 0.55,
            "probability_exact": True,
            "proof_status": "source_mirrored_final_switch_roll_from_observed_confidence",
        }
    verdict["switch_roll"] = switch_roll
    if reason is not None:
        verdict["reason"] = reason
    return verdict


def _report(verdicts: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "source": "test",
        "kind": "rom_switch_materialization",
        "base_route": "shared_switch_loop",
        "base_state": "stub.state",
        "base_state_field": "save_state",
        "scenario_count": len(verdicts),
        "checked_count": sum(1 for v in verdicts if v["status"] == "pass"),
        "skipped_count": sum(1 for v in verdicts if v["status"] == "skipped"),
        "error_count": sum(1 for v in verdicts if v["status"] == "error"),
        "policy_disagreement_count": 0,
        "elapsed_seconds": 0.5,
        "materializations_per_minute": 120.0,
        "known_limits": ["test limit one", "test limit two"],
        "verdicts": verdicts,
    }


class SummarizeBatchSwitchTests(unittest.TestCase):
    def test_counts_observed_switches_probability_exact_and_errors(self) -> None:
        report = _report(
            [
                _verdict("a"),  # observed + exact
                _verdict(
                    "b",
                    observation_status="no_decision_observed",
                    observed_switch_path=False,
                    switch_roll={
                        "available": False,
                        "confidence": 0,
                        "reason": "no_switch_dispatch_observation",
                        "proof_status": "no_final_switch_roll_observed",
                    },
                ),  # neither
                _verdict(
                    "c",
                    switch_roll={
                        "available": True,
                        "confidence": 0x40,
                        "switch_probability": 0.5,
                        "probability_exact": False,
                        "proof_status": "source_mirrored_final_switch_roll_from_observed_confidence",
                    },
                ),  # observed but ranged
                _verdict(
                    "d",
                    status="error",
                    reason="no observation",
                    observed_switch_path=False,
                    switch_roll={"available": False, "reason": "no_switch_dispatch_observation"},
                ),  # error
            ]
        )

        summary = summarize_batch_switch(report)
        self.assertEqual(summary["scenario_count"], 4)
        self.assertEqual(summary["observed_switches"], 2)  # a + c
        self.assertEqual(summary["probability_exact_count"], 1)  # only a
        self.assertEqual(summary["error_count"], 1)  # d
        self.assertEqual(summary["skipped_count"], 0)

    def test_counts_skipped_separately_from_errors(self) -> None:
        report = _report(
            [
                _verdict(
                    "skipped",
                    status="skipped",
                    reason="unsupported scenario family",
                    observed_switch_path=False,
                    switch_roll={"available": False, "reason": "n/a"},
                ),
            ]
        )

        summary = summarize_batch_switch(report)
        self.assertEqual(summary["skipped_count"], 1)
        self.assertEqual(summary["error_count"], 0)

    def test_summary_template_matches_spec_text(self) -> None:
        text = SUMMARY_TEMPLATE.format(scenarios=5, observed=3, exact=2, errors=1)
        self.assertEqual(
            text,
            "Summary: 5 scenarios, 3 observed switches, 2 probability_exact, errors=1",
        )


class FormatBatchSwitchTableTests(unittest.TestCase):
    def test_table_contains_column_headers_and_summary_line(self) -> None:
        report = _report([_verdict("only")])
        text = format_batch_switch_table(report)
        self.assertIn("scenario_id", text)
        self.assertIn("confidence", text)
        self.assertIn("switch_prob", text)
        self.assertIn("exact", text)
        self.assertIn("proof_status", text)
        self.assertIn("observation_status", text)
        self.assertIn("1 scenarios", text)
        self.assertIn("observed switches", text)
        self.assertIn("probability_exact", text)
        self.assertIn("errors=0", text)

    def test_table_renders_each_verdict_row(self) -> None:
        report = _report(
            [
                _verdict("morty_haunter_shadow_ball"),
                _verdict(
                    "morty_gengar_full_hp",
                    observation_status="no_decision_observed",
                    observed_switch_path=False,
                    proposed_switch=False,
                    switch_roll={
                        "available": False,
                        "confidence": 0,
                        "reason": "no_switch_dispatch_observation",
                        "proof_status": "no_final_switch_roll_observed",
                    },
                ),
            ]
        )
        text = format_batch_switch_table(report)
        self.assertIn("morty_haunter_shadow_ball", text)
        self.assertIn("morty_gengar_full_hp", text)
        # Per-row hex confidence; probability with one-decimal percent.
        self.assertIn("0x40", text)
        self.assertIn("55.0%", text)
        # Unavailable switch_roll renders as n/a(reason) and exact=-
        self.assertIn("n/a(no_switch_dispatch_observation)", text)

    def test_table_truncates_beyond_display_limit(self) -> None:
        report = _report([_verdict(f"row_{i}") for i in range(5)])
        text = format_batch_switch_table(report, limit=2)
        self.assertIn("row_0", text)
        self.assertIn("row_1", text)
        self.assertNotIn("row_2", text)
        self.assertIn("3 more rows truncated", text)

    def test_table_renders_error_status_with_reason(self) -> None:
        report = _report(
            [
                _verdict(
                    "err",
                    status="error",
                    reason="no observation within watch_frames",
                    confidence=None,
                    observation_status="no_decision_observed",
                    observed_switch_path=False,
                    proposed_switch=False,
                    switch_roll={"available": False, "reason": "no_switch_dispatch_observation"},
                ),
            ]
        )
        text = format_batch_switch_table(report)
        self.assertIn("ERROR:", text)
        self.assertIn("no observation within watch_frames", text)

    def test_table_renders_skipped_status_with_reason(self) -> None:
        report = _report(
            [
                _verdict(
                    "skipped",
                    status="skipped",
                    reason="unsupported scenario family",
                    confidence=None,
                    observation_status="no_decision_observed",
                    observed_switch_path=False,
                    proposed_switch=False,
                    switch_roll={"available": False, "reason": "n/a"},
                ),
            ]
        )
        text = format_batch_switch_table(report)
        self.assertIn("SKIPPED:", text)
        self.assertIn("unsupported scenario family", text)
        # Skipped count is shown as a parenthetical after the summary.
        self.assertIn("1 scenarios skipped", text)


class RunBatchSwitchMaterializeTests(unittest.TestCase):
    def test_wraps_report_with_summary_and_kind_tag(self) -> None:
        fake_report = _report([_verdict("only")])
        with patch(
            "tools.headless_battle.batch_switch.run_rom_switch_materialization_from_path",
            return_value=fake_report,
        ) as mocked:
            result = run_batch_switch_materialize(
                Path("ignored.jsonl"),
                limit=4,
                base_route="shared_switch_loop",
            )
        mocked.assert_called_once()
        call_kwargs = mocked.call_args.kwargs
        self.assertEqual(call_kwargs["limit"], 4)
        self.assertEqual(call_kwargs["base_route"], "shared_switch_loop")
        self.assertEqual(result["kind"], "headless_battle_batch_switch_materialize")
        self.assertIn("summary", result)
        self.assertEqual(result["summary"]["scenario_count"], 1)

    def test_zero_limit_passes_through_to_materializer_unchanged(self) -> None:
        fake_report = _report([])
        with patch(
            "tools.headless_battle.batch_switch.run_rom_switch_materialization_from_path",
            return_value=fake_report,
        ) as mocked:
            run_batch_switch_materialize(Path("ignored.jsonl"), limit=0)
        # limit=0 means "no cap" both at the runner boundary and at the
        # materializer (which interprets limit > 0 as the cap).
        self.assertEqual(mocked.call_args.kwargs["limit"], 0)


class CliMainTests(unittest.TestCase):
    def test_text_mode_prints_table_and_summary(self) -> None:
        fake_report = _report([_verdict("only")])
        with patch(
            "tools.headless_battle.batch_switch.run_rom_switch_materialization_from_path",
            return_value=fake_report,
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(["--scenarios", "ignored.jsonl"])
        self.assertEqual(code, 0)
        text = buf.getvalue()
        self.assertIn("Headless battle batch switch-materialize", text)
        self.assertIn("Summary:", text)
        self.assertIn("scenario_id", text)

    def test_json_mode_outputs_full_report_including_summary(self) -> None:
        fake_report = _report([_verdict("only"), _verdict("two")])
        with patch(
            "tools.headless_battle.batch_switch.run_rom_switch_materialization_from_path",
            return_value=fake_report,
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(["--scenarios", "ignored.jsonl", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["summary"]["scenario_count"], 2)
        self.assertEqual(data["kind"], "headless_battle_batch_switch_materialize")

    def test_json_out_writes_full_report_to_disk(self) -> None:
        fake_report = _report([_verdict("only")])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.json"
            with patch(
                "tools.headless_battle.batch_switch.run_rom_switch_materialization_from_path",
                return_value=fake_report,
            ):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = main(
                        [
                            "--scenarios",
                            "ignored.jsonl",
                            "--json-out",
                            str(out),
                        ]
                    )
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["summary"]["scenario_count"], 1)

    def test_fail_on_error_exits_nonzero_when_errors_present(self) -> None:
        fake_report = _report(
            [
                _verdict("ok"),
                _verdict(
                    "err",
                    status="error",
                    reason="something",
                    observed_switch_path=False,
                    switch_roll={"available": False, "reason": "x"},
                ),
            ]
        )
        with patch(
            "tools.headless_battle.batch_switch.run_rom_switch_materialization_from_path",
            return_value=fake_report,
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(
                    [
                        "--scenarios",
                        "ignored.jsonl",
                        "--fail-on-error",
                    ]
                )
        self.assertEqual(code, 1)

    def test_fail_on_error_returns_zero_when_only_skipped(self) -> None:
        fake_report = _report(
            [
                _verdict(
                    "skipped",
                    status="skipped",
                    reason="unsupported scenario family",
                    observed_switch_path=False,
                    switch_roll={"available": False, "reason": "n/a"},
                ),
            ]
        )
        with patch(
            "tools.headless_battle.batch_switch.run_rom_switch_materialization_from_path",
            return_value=fake_report,
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(
                    [
                        "--scenarios",
                        "ignored.jsonl",
                        "--fail-on-error",
                    ]
                )
        # Skipped is informational, not an error.
        self.assertEqual(code, 0)


class CliParserTests(unittest.TestCase):
    def test_parser_requires_scenarios(self) -> None:
        with self.assertRaises(SystemExit):
            build_parser().parse_args([])

    def test_parser_defaults_match_documented_workflow(self) -> None:
        args = build_parser().parse_args(["--scenarios", "p.jsonl"])
        self.assertEqual(args.limit, 0)
        self.assertFalse(args.json)
        self.assertEqual(args.json_out, "")
        self.assertEqual(args.display_limit, 50)
        self.assertFalse(args.fail_on_error)


if __name__ == "__main__":
    unittest.main()
