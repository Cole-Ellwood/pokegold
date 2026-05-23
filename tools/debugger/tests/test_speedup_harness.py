"""Tests for tools/debugger/speedup_harness.py (P21 acceptance slice)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.debugger import speedup_harness
from tools.debugger.evidence import evidence_atom


REPO_ROOT = Path(__file__).resolve().parents[3]
SCENARIOS_PATH = REPO_ROOT / "audit" / "lived_bug_scenarios.jsonl"
REPORT_PATH = REPO_ROOT / "docs" / "debugger_speedup_2026-05-22.md"
PGOAL_V5_REGEX = re.compile(r"scenarios=[6-9]|scenarios=1[0-9]")


def _baseline_atom(scenario_id: str = "test_scenario") -> dict:
    return evidence_atom(
        claim_type="speedup.baseline_time_estimate",
        origin="baseline_history",
        observation_type="commit_or_handoff_citation",
        proof_status="planned_only",
        source_report="test fixture",
        source_kind="unit_test",
        scope={"scenario_id": scenario_id, "bug_class": "ag_nn_register_clobber"},
        subjects={"commands": ["manual historical trace"]},
        precision={"time_seconds": "estimate"},
        validation={"note": "fixture"},
        detail={"baseline_time_estimate_seconds": 120.0},
    )


def _scaffold_record(scenario_id: str = "test_scenario", command: str = "python -c \"print('ok')\"") -> dict:
    return {
        "id": scenario_id,
        "bug_class": "ag_nn_register_clobber",
        "baseline_commands": ["git bisect", "hand-trace"],
        "baseline_time_estimate_seconds": 120.0,
        "baseline_source": "test fixture",
        "masterpiece_commands": [command],
        "masterpiece_time_actual_seconds": None,
        "ratio": None,
        "evidence_atoms": [_baseline_atom(scenario_id)],
        "status": "scaffold_incomplete",
    }


def _measured_record() -> dict:
    scenario = speedup_harness.Scenario(1, _scaffold_record())

    def runner(command: str) -> speedup_harness.CommandResult:
        return speedup_harness.CommandResult(command, 0, 2.0, "ok", "")

    return speedup_harness.measure_scenario(scenario, runner=runner)


class ValidateScenarioTests(unittest.TestCase):
    def test_accepts_valid_scaffold_record(self) -> None:
        self.assertEqual(
            speedup_harness.validate_scenario(
                _scaffold_record(),
                known_bug_classes={"ag_nn_register_clobber"},
            ),
            [],
        )

    def test_accepts_fully_measured_record(self) -> None:
        self.assertEqual(
            speedup_harness.validate_scenario(
                _measured_record(),
                known_bug_classes={"ag_nn_register_clobber"},
                require_measured=True,
            ),
            [],
        )

    def test_rejects_missing_required_field(self) -> None:
        bad = _scaffold_record()
        del bad["bug_class"]
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(any("bug_class" in error for error in errors))

    def test_rejects_missing_evidence_atoms(self) -> None:
        bad = _scaffold_record()
        bad["evidence_atoms"] = []
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(any("evidence_atoms" in error for error in errors))

    def test_rejects_empty_baseline_commands(self) -> None:
        bad = _scaffold_record()
        bad["baseline_commands"] = []
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(any("baseline_commands" in error for error in errors))

    def test_rejects_empty_masterpiece_commands(self) -> None:
        bad = _scaffold_record()
        bad["masterpiece_commands"] = []
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(any("masterpiece_commands" in error for error in errors))

    def test_rejects_bad_status(self) -> None:
        bad = _scaffold_record()
        bad["status"] = "wishful_thinking"
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(any("status" in error for error in errors))

    def test_rejects_missing_masterpiece_time_when_measured(self) -> None:
        bad = _scaffold_record()
        bad["status"] = "measured"
        bad["ratio"] = 12.5
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(any("masterpiece_time_actual_seconds" in error for error in errors))

    def test_rejects_missing_ratio_when_measured(self) -> None:
        bad = _scaffold_record()
        bad["status"] = "measured"
        bad["masterpiece_time_actual_seconds"] = 30.0
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(any("ratio" in error for error in errors))

    def test_rejects_measured_record_without_ratio_atom(self) -> None:
        bad = _measured_record()
        bad["evidence_atoms"] = [
            atom for atom in bad["evidence_atoms"] if atom.get("claim_type") != "speedup.ratio"
        ]
        errors = speedup_harness.validate_scenario(bad, require_measured=True)
        self.assertTrue(any("speedup.ratio" in error for error in errors))

    def test_rejects_bug_class_not_in_catalog(self) -> None:
        bad = _scaffold_record()
        bad["bug_class"] = "not_in_the_p20_catalog"
        errors = speedup_harness.validate_scenario(
            bad,
            known_bug_classes={"ag_nn_register_clobber", "value_came_from_where"},
        )
        self.assertTrue(any("bug_class" in error and "catalog" in error for error in errors))

    def test_skips_catalog_check_when_known_set_empty(self) -> None:
        good = _scaffold_record()
        good["bug_class"] = "anything_at_all"
        errors = speedup_harness.validate_scenario(good, known_bug_classes=set())
        self.assertEqual(errors, [])

    def test_rejects_empty_dict_evidence_atom(self) -> None:
        bad = _scaffold_record()
        bad["evidence_atoms"] = [{}]
        errors = speedup_harness.validate_scenario(bad, known_bug_classes=set())
        self.assertTrue(any("evidence_atoms[0]" in error for error in errors))

    def test_rejects_non_dict_evidence_atom(self) -> None:
        bad = _scaffold_record()
        bad["evidence_atoms"] = ["a string instead of a dict"]
        errors = speedup_harness.validate_scenario(bad, known_bug_classes=set())
        self.assertTrue(any("evidence_atoms[0]" in error for error in errors))

    def test_rejects_non_numeric_baseline_time(self) -> None:
        bad = _scaffold_record()
        bad["baseline_time_estimate_seconds"] = "not-a-number"
        errors = speedup_harness.validate_scenario(bad, known_bug_classes=set())
        self.assertTrue(any("baseline_time_estimate_seconds" in error and "number" in error for error in errors))

    def test_rejects_bool_baseline_time(self) -> None:
        bad = _scaffold_record()
        bad["baseline_time_estimate_seconds"] = True
        errors = speedup_harness.validate_scenario(bad, known_bug_classes=set())
        self.assertTrue(any("baseline_time_estimate_seconds" in error for error in errors))

    def test_codex_probe_record_now_rejected(self) -> None:
        probe = _scaffold_record()
        probe["bug_class"] = "not_in_catalog"
        probe["baseline_time_estimate_seconds"] = "not-a-number"
        probe["evidence_atoms"] = [{}]
        errors = speedup_harness.validate_scenario(
            probe,
            known_bug_classes={"ag_nn_register_clobber"},
        )
        self.assertTrue(any("bug_class" in error and "catalog" in error for error in errors))
        self.assertTrue(any("baseline_time_estimate_seconds" in error and "number" in error for error in errors))
        self.assertTrue(any("evidence_atoms[0]" in error for error in errors))


class LoadScenariosTests(unittest.TestCase):
    def test_load_real_scenarios_file(self) -> None:
        records = speedup_harness.load_scenarios(SCENARIOS_PATH)
        self.assertGreaterEqual(len(records), speedup_harness.MIN_SCENARIOS)

    def test_load_real_scenarios_includes_must_have_ids(self) -> None:
        records = speedup_harness.load_scenarios(SCENARIOS_PATH)
        ids = {scenario.id for scenario in records}
        self.assertIn("ag_nn_5x_damage_44ca3b29", ids)
        self.assertIn("wild_floor_no_op_13a6e3a3", ids)
        self.assertIn("rival_1_softlock_farcall_hl", ids)

    def test_load_returns_error_for_missing_file(self) -> None:
        with TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                speedup_harness.load_scenarios(Path(td) / "missing.jsonl")

    def test_stored_scenarios_are_measured_after_acceptance_slice(self) -> None:
        records = speedup_harness.load_scenarios(SCENARIOS_PATH, require_measured=True)
        self.assertGreaterEqual(len(records), speedup_harness.MIN_SCENARIOS)


class MeasureAndReportTests(unittest.TestCase):
    def test_measure_scenario_adds_ratio_and_evidence_atoms(self) -> None:
        measured = _measured_record()
        self.assertEqual(measured["status"], "measured")
        self.assertEqual(measured["masterpiece_time_actual_seconds"], 2.0)
        self.assertEqual(measured["ratio"], 60.0)
        claims = {atom.get("claim_type") for atom in measured["evidence_atoms"]}
        self.assertIn("speedup.baseline_time_estimate", claims)
        self.assertIn("speedup.masterpiece_replay", claims)
        self.assertIn("speedup.ratio", claims)

    def test_speedup_harness_replays_ag_nn_lived_bug(self) -> None:
        scenarios = speedup_harness.load_scenarios(SCENARIOS_PATH)
        scenario = next(item for item in scenarios if item.id == "ag_nn_5x_damage_44ca3b29")
        measured = speedup_harness.measure_scenario(scenario, timeout_seconds=120.0)
        self.assertEqual(measured["status"], "measured")
        self.assertGreater(measured["ratio"], 0)
        self.assertTrue(
            any(atom.get("claim_type") == "speedup.masterpiece_replay" for atom in measured["evidence_atoms"])
        )

    def test_speedup_harness_ratios_are_evidence_backed(self) -> None:
        records = speedup_harness.load_scenarios(SCENARIOS_PATH, require_measured=True)
        for scenario in records:
            row = scenario.record
            self.assertIsInstance(row["ratio"], (int, float))
            claims = {atom.get("claim_type") for atom in row["evidence_atoms"]}
            origins = {atom.get("origin") for atom in row["evidence_atoms"]}
            self.assertIn("speedup.ratio", claims, row["id"])
            self.assertIn("baseline_history", origins, row["id"])
            self.assertIn("masterpiece_replay", origins, row["id"])

    def test_speedup_harness_refuses_to_emit_unverifiable_baseline(self) -> None:
        with TemporaryDirectory() as td:
            path = Path(td) / "scenarios.jsonl"
            records = [
                _scaffold_record(f"scenario_{index}", command=("bad-command" if index == 0 else "ok-command"))
                for index in range(speedup_harness.MIN_SCENARIOS)
            ]
            path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

            def runner(command: str) -> speedup_harness.CommandResult:
                if command == "bad-command":
                    return speedup_harness.CommandResult(command, 7, 0.1, "", "boom")
                return speedup_harness.CommandResult(command, 0, 0.1, "ok", "")

            report = speedup_harness.build_speedup_report(path, runner=runner)

        self.assertFalse(report["ready"])
        self.assertEqual(report["measured_count"], speedup_harness.MIN_SCENARIOS - 1)
        self.assertTrue(any("exit=7" in error for error in report["errors"]))

    def test_render_markdown_table_reports_per_scenario_ratios(self) -> None:
        report = speedup_harness.build_speedup_report(SCENARIOS_PATH, refresh=False)
        table = speedup_harness.render_markdown_table(report)
        self.assertIn("| Scenario | Bug class |", table)
        self.assertIn("speedup.ratio", table)
        self.assertIn("does not emit an aggregate speedup claim", table)

    def test_filter_query_scenarios(self) -> None:
        report = speedup_harness.build_speedup_report(SCENARIOS_PATH, filter_tier="QUERY", refresh=False)
        self.assertTrue(report["ready"])
        self.assertGreaterEqual(report["measured_count"], 1)
        tiers = speedup_harness.load_bug_class_tiers()
        self.assertTrue(all(tiers[row["bug_class"]] == "QUERY" for row in report["scenarios"]))


class CommandTests(unittest.TestCase):
    def test_top_level_self_test_exits_zero_and_matches_pgoal_regex(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "tools.debugger", "speedup-report", "--self-test"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"--self-test failed: stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        self.assertRegex(result.stdout, PGOAL_V5_REGEX)

    def test_json_output_with_no_refresh(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "tools.debugger", "speedup-report", "--json", "--no-refresh"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ready"])
        self.assertGreaterEqual(payload["measured_count"], speedup_harness.MIN_SCENARIOS)

    def test_self_test_fails_on_missing_evidence_atom(self) -> None:
        with TemporaryDirectory() as td:
            bad_path = Path(td) / "bad.jsonl"
            bad_record = _scaffold_record()
            bad_record["evidence_atoms"] = []
            bad_path.write_text(json.dumps(bad_record) + "\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tools.debugger.speedup_harness",
                    "--self-test",
                    "--scenarios",
                    str(bad_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence_atoms", result.stderr)

    def test_self_test_fails_on_too_few_scenarios(self) -> None:
        with TemporaryDirectory() as td:
            short_path = Path(td) / "short.jsonl"
            short_path.write_text(json.dumps(_scaffold_record()) + "\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tools.debugger.speedup_harness",
                    "--self-test",
                    "--scenarios",
                    str(short_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required=6", result.stderr)

    def test_unified_front_door_dispatches_speedup_report(self) -> None:
        from tools.debugger.__main__ import V2_PASSTHROUGH_MODULES

        self.assertEqual(V2_PASSTHROUGH_MODULES["speedup-report"], "tools.debugger.speedup_harness")

    def test_committed_markdown_report_exists(self) -> None:
        text = REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("# Debugger Speedup Report - 2026-05-22", text)
        self.assertIn("ag_nn_5x_damage_44ca3b29", text)


if __name__ == "__main__":
    unittest.main()
