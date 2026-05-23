"""Tests for tools/debugger/speedup_harness.py (P21 scaffold slice).

Covers schema validation, missing-baseline-evidence refusal, the
null-time / null-ratio gate (only allowed when status='scaffold_incomplete'),
the scaffold ``--self-test`` exit code + status line, and the
deliberate non-emission of the pgoal v5 acceptance regex.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.debugger import speedup_harness


REPO_ROOT = Path(__file__).resolve().parents[3]
SCENARIOS_PATH = REPO_ROOT / "audit" / "lived_bug_scenarios.jsonl"
PGOAL_V5_REGEX = re.compile(r"scenarios=[6-9]|scenarios=1[0-9]")


def _good_record() -> dict:
    return {
        "id": "test_scaffold_scenario",
        "bug_class": "ag_nn_register_clobber",
        "baseline_commands": ["git bisect", "hand-trace"],
        "baseline_time_estimate_seconds": 3600,
        "masterpiece_commands": ["python -m tools.debugger clobbers --symbol X"],
        "masterpiece_time_actual_seconds": None,
        "ratio": None,
        "evidence_atoms": [
            {"kind": "commit", "sha": "deadbeef", "description": "test"}
        ],
        "status": "scaffold_incomplete",
    }


class ValidateScenarioTests(unittest.TestCase):
    def test_accepts_valid_scaffold_record(self) -> None:
        self.assertEqual(speedup_harness.validate_scenario(_good_record()), [])

    def test_rejects_missing_required_field(self) -> None:
        bad = _good_record()
        del bad["bug_class"]
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(any("bug_class" in e for e in errors))

    def test_rejects_missing_evidence_atoms(self) -> None:
        bad = _good_record()
        bad["evidence_atoms"] = []
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(any("evidence_atoms" in e for e in errors))

    def test_rejects_empty_baseline_commands(self) -> None:
        bad = _good_record()
        bad["baseline_commands"] = []
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(any("baseline_commands" in e for e in errors))

    def test_rejects_empty_masterpiece_commands(self) -> None:
        bad = _good_record()
        bad["masterpiece_commands"] = []
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(any("masterpiece_commands" in e for e in errors))

    def test_rejects_bad_status(self) -> None:
        bad = _good_record()
        bad["status"] = "wishful_thinking"
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(any("status" in e for e in errors))

    def test_rejects_null_masterpiece_time_when_measured(self) -> None:
        bad = _good_record()
        bad["status"] = "measured"
        bad["ratio"] = 12.5
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(
            any("masterpiece_time_actual_seconds" in e for e in errors)
        )

    def test_rejects_null_ratio_when_measured(self) -> None:
        bad = _good_record()
        bad["status"] = "measured"
        bad["masterpiece_time_actual_seconds"] = 30.0
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(any("ratio" in e for e in errors))

    def test_rejects_nonnull_masterpiece_time_in_scaffold(self) -> None:
        bad = _good_record()
        bad["masterpiece_time_actual_seconds"] = 30.0
        errors = speedup_harness.validate_scenario(bad)
        self.assertTrue(
            any("scaffold_incomplete" in e and "masterpiece_time_actual_seconds" in e
                for e in errors)
        )

    def test_accepts_fully_measured_record(self) -> None:
        good = _good_record()
        good["status"] = "measured"
        good["masterpiece_time_actual_seconds"] = 30.0
        good["ratio"] = 120.0
        self.assertEqual(speedup_harness.validate_scenario(good), [])

    def test_rejects_bug_class_not_in_catalog(self) -> None:
        """Codex P21-review finding [P1]: validator must cross-check
        bug_class against the P20 catalog so taxonomy drift doesn't slip
        through (the value_came_from_where mislabel was caught manually;
        this gate should catch the next instance automatically)."""
        bad = _good_record()
        bad["bug_class"] = "not_in_the_p20_catalog"
        errors = speedup_harness.validate_scenario(
            bad,
            known_bug_classes={"ag_nn_register_clobber", "value_came_from_where"},
        )
        self.assertTrue(
            any("bug_class" in e and "catalog" in e for e in errors),
            f"expected bug_class catalog-mismatch error, got: {errors}",
        )

    def test_skips_catalog_check_when_known_set_empty(self) -> None:
        """The cross-check is opt-out via known_bug_classes=set() so the
        validator stays useful in environments where the catalog isn't
        readable. Empty set means 'skip', not 'reject everything'."""
        good = _good_record()
        good["bug_class"] = "anything_at_all"
        errors = speedup_harness.validate_scenario(
            good, known_bug_classes=set()
        )
        self.assertEqual(errors, [])

    def test_rejects_empty_dict_evidence_atom(self) -> None:
        """Codex P21-review finding [P1]: evidence_atoms=[{}] passed the
        old gate. Each atom must be a non-empty dict."""
        bad = _good_record()
        bad["evidence_atoms"] = [{}]
        errors = speedup_harness.validate_scenario(
            bad, known_bug_classes=set()
        )
        self.assertTrue(
            any("evidence_atoms[0]" in e for e in errors),
            f"expected empty-dict evidence_atom error, got: {errors}",
        )

    def test_rejects_non_dict_evidence_atom(self) -> None:
        bad = _good_record()
        bad["evidence_atoms"] = ["a string instead of a dict"]
        errors = speedup_harness.validate_scenario(
            bad, known_bug_classes=set()
        )
        self.assertTrue(any("evidence_atoms[0]" in e for e in errors))

    def test_rejects_non_numeric_baseline_time(self) -> None:
        """Codex P21-review finding [P1]: baseline_time_estimate_seconds=
        'not-a-number' passed the old gate. Must be int or float."""
        bad = _good_record()
        bad["baseline_time_estimate_seconds"] = "not-a-number"
        errors = speedup_harness.validate_scenario(
            bad, known_bug_classes=set()
        )
        self.assertTrue(
            any("baseline_time_estimate_seconds" in e and "number" in e
                for e in errors),
            f"expected numeric-baseline error, got: {errors}",
        )

    def test_rejects_bool_baseline_time(self) -> None:
        """Python edge case: bool is a subclass of int, but True/False
        aren't meaningful baseline times. Must be a real number."""
        bad = _good_record()
        bad["baseline_time_estimate_seconds"] = True
        errors = speedup_harness.validate_scenario(
            bad, known_bug_classes=set()
        )
        self.assertTrue(
            any("baseline_time_estimate_seconds" in e for e in errors)
        )

    def test_codex_probe_record_now_rejected(self) -> None:
        """The exact probe Codex ran during P21 review (bug_class=
        'not_in_catalog', baseline_time_estimate_seconds='not-a-number',
        evidence_atoms=[{}]) must now fail validation."""
        probe = _good_record()
        probe["bug_class"] = "not_in_catalog"
        probe["baseline_time_estimate_seconds"] = "not-a-number"
        probe["evidence_atoms"] = [{}]
        errors = speedup_harness.validate_scenario(
            probe,
            known_bug_classes={"ag_nn_register_clobber"},
        )
        # All three Codex-named issues should now be flagged.
        self.assertTrue(any("bug_class" in e and "catalog" in e for e in errors))
        self.assertTrue(
            any("baseline_time_estimate_seconds" in e and "number" in e
                for e in errors)
        )
        self.assertTrue(any("evidence_atoms[0]" in e for e in errors))


class LoadScenariosTests(unittest.TestCase):
    def test_load_real_scenarios_file(self) -> None:
        records, errors = speedup_harness.load_scenarios(SCENARIOS_PATH)
        self.assertEqual(
            errors,
            [],
            f"audit/lived_bug_scenarios.jsonl has validation errors: {errors}",
        )
        self.assertGreaterEqual(
            len(records),
            speedup_harness.MIN_SCENARIOS,
            f"need >= {speedup_harness.MIN_SCENARIOS} scenarios, got {len(records)}",
        )

    def test_load_real_scenarios_includes_must_have_ids(self) -> None:
        records, _ = speedup_harness.load_scenarios(SCENARIOS_PATH)
        ids = {r["id"] for r in records}
        self.assertIn("ag_nn_5x_damage_44ca3b29", ids)
        self.assertIn("wild_floor_no_op_13a6e3a3", ids)
        self.assertIn("rival_1_softlock_farcall_hl", ids)

    def test_load_returns_errors_for_missing_file(self) -> None:
        with TemporaryDirectory() as td:
            records, errors = speedup_harness.load_scenarios(
                Path(td) / "missing.jsonl"
            )
        self.assertEqual(records, [])
        self.assertTrue(any("not found" in e for e in errors))


class ScenarioDataclassTests(unittest.TestCase):
    def test_from_dict_and_back(self) -> None:
        original = _good_record()
        scenario = speedup_harness.Scenario.from_dict(original)
        round_tripped = scenario.as_dict()
        self.assertEqual(round_tripped["id"], original["id"])
        self.assertEqual(round_tripped["bug_class"], original["bug_class"])
        self.assertEqual(round_tripped["status"], original["status"])
        self.assertIsNone(round_tripped["masterpiece_time_actual_seconds"])
        self.assertIsNone(round_tripped["ratio"])


class RenderMarkdownTests(unittest.TestCase):
    def test_renders_table_with_null_indicator(self) -> None:
        records, _ = speedup_harness.load_scenarios(SCENARIOS_PATH)
        table = speedup_harness.render_markdown_table(records)
        self.assertIn("| id |", table)
        # Null masterpiece-time and null ratio render as em-dash; the
        # scaffold slice shouldn't have any non-null measurements yet.
        self.assertIn("—", table)


class SelfTestCommandTests(unittest.TestCase):
    def test_self_test_exits_zero(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "tools.debugger.speedup_harness",
             "--self-test"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"--self-test failed: stdout={result.stdout!r} "
            f"stderr={result.stderr!r}",
        )

    def test_self_test_output_does_not_match_pgoal_v5_regex(self) -> None:
        """Codex's explicit constraint: scaffold output must NOT match the
        pgoal v5 acceptance regex `scenarios=[6-9]|scenarios=1[0-9]`.
        The scaffold slice must keep pgoal v5 red so it does not falsely
        close before the acceptance slice measures real ratios."""
        result = subprocess.run(
            [sys.executable, "-m", "tools.debugger.speedup_harness",
             "--self-test"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIsNone(
            PGOAL_V5_REGEX.search(result.stdout),
            f"scaffold output MUST NOT match pgoal v5 regex but did: "
            f"{result.stdout!r}",
        )
        # Sanity: the honest scaffold status line IS present.
        self.assertIn(
            "speedup-report scaffold:", result.stdout
        )
        self.assertIn(
            "ratios pending acceptance slice", result.stdout
        )

    def test_self_test_fails_on_missing_evidence_atom(self) -> None:
        """Refusal gate: a scenarios file with a record missing
        evidence_atoms fails validation, --self-test exits 1."""
        with TemporaryDirectory() as td:
            bad_path = Path(td) / "bad.jsonl"
            bad_record = _good_record()
            bad_record["evidence_atoms"] = []
            bad_path.write_text(
                json.dumps(bad_record) + "\n", encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, "-m", "tools.debugger.speedup_harness",
                 "--self-test", "--scenarios", str(bad_path)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence_atoms", result.stderr)

    def test_self_test_fails_on_too_few_scenarios(self) -> None:
        """Floor gate: fewer than MIN_SCENARIOS valid records fails."""
        with TemporaryDirectory() as td:
            short_path = Path(td) / "short.jsonl"
            record = _good_record()
            short_path.write_text(
                json.dumps(record) + "\n", encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, "-m", "tools.debugger.speedup_harness",
                 "--self-test", "--scenarios", str(short_path)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("minimum", result.stderr)


class PgoalV5StaysRedTests(unittest.TestCase):
    """Explicit guard: the unified front door must NOT have a speedup-report
    passthrough yet. This is the negative check Codex named in their ack."""

    def test_unified_front_door_does_not_dispatch_speedup_report(self) -> None:
        from tools.debugger.__main__ import V2_PASSTHROUGH_MODULES

        self.assertNotIn(
            "speedup-report",
            V2_PASSTHROUGH_MODULES,
            "Pgoal v5 acceptance gate must stay red for the scaffold slice; "
            "wiring speedup-report through __main__ belongs to the acceptance "
            "slice (P21_speedup_harness_acceptance_slice).",
        )


if __name__ == "__main__":
    unittest.main()
