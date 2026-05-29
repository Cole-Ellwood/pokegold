"""Tests for tools/debugger/auto_watch.py (P19 first slice).

Covers the finding-row schema, the append-only JSONL writer, the
register_flow detector against synthetic broken/fixed asm, and the
``--self-test`` CLI subprocess exit code.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.debugger import auto_watch


REPO_ROOT = Path(__file__).resolve().parents[3]


class AutoWatchFindingTests(unittest.TestCase):
    def test_finding_serializes_required_fields(self) -> None:
        finding = auto_watch.AutoWatchFinding(
            trigger="self-test",
            trigger_id="t1",
            bug_class="ag_nn_register_clobber",
            detector="register_flow",
        )
        row = finding.as_dict()
        for field_name in (
            "schema_version",
            "kind",
            "ts",
            "trigger",
            "trigger_id",
            "bug_class",
            "detector",
            "status",
            "severity",
        ):
            self.assertIn(field_name, row)
        self.assertEqual(row["schema_version"], auto_watch.SCHEMA_VERSION)
        self.assertEqual(row["kind"], auto_watch.KIND)
        # Default status/severity are present even when not set.
        self.assertEqual(row["status"], "detected")
        self.assertEqual(row["severity"], "medium")

    def test_finding_omits_empty_optionals(self) -> None:
        finding = auto_watch.AutoWatchFinding(
            trigger="self-test",
            trigger_id="t1",
            bug_class="ag_nn_register_clobber",
            detector="register_flow",
        )
        row = finding.as_dict()
        # Empty evidence / files / symbols / llm_next_step are omitted.
        self.assertNotIn("evidence", row)
        self.assertNotIn("files", row)
        self.assertNotIn("symbols", row)
        self.assertNotIn("llm_next_step", row)
        # commit_hash / proposal_id only auto-mirror for matching trigger.
        self.assertNotIn("commit_hash", row)
        self.assertNotIn("proposal_id", row)
        self.assertNotIn("evidence_atoms", row)
        self.assertNotIn("command_replay", row)

    def test_finding_commit_trigger_auto_mirrors_commit_hash(self) -> None:
        finding = auto_watch.AutoWatchFinding(
            trigger="commit",
            trigger_id="abc1234",
            bug_class="release_smoke_regression",
            detector="release_smoke",
        )
        row = finding.as_dict()
        self.assertEqual(row["commit_hash"], "abc1234")
        self.assertNotIn("proposal_id", row)

    def test_finding_rom_edit_trigger_auto_mirrors_proposal_id(self) -> None:
        finding = auto_watch.AutoWatchFinding(
            trigger="rom-edit-propose",
            trigger_id="prop-42",
            bug_class="clobber_smoke_regression",
            detector="clobber_smoke",
        )
        row = finding.as_dict()
        self.assertEqual(row["proposal_id"], "prop-42")
        self.assertNotIn("commit_hash", row)

    def test_finding_explicit_commit_hash_overrides_mirror(self) -> None:
        finding = auto_watch.AutoWatchFinding(
            trigger="commit",
            trigger_id="self-test-1",
            commit_hash="def5678",
            bug_class="release_smoke_regression",
            detector="release_smoke",
        )
        row = finding.as_dict()
        self.assertEqual(row["commit_hash"], "def5678")
        self.assertEqual(row["trigger_id"], "self-test-1")

    def test_finding_includes_evidence_atoms_and_command_replay(self) -> None:
        finding = auto_watch.AutoWatchFinding(
            trigger="self-test",
            trigger_id="t1",
            bug_class="ag_nn_register_clobber",
            detector="register_flow",
            evidence_atoms=(
                {"kind": "register_flow_clobber", "symbol": "X", "flagged_writes": ["c"]},
            ),
            command_replay="python -m tools.debugger clobbers --symbol X",
        )
        row = finding.as_dict()
        self.assertIn("evidence_atoms", row)
        self.assertEqual(row["evidence_atoms"][0]["symbol"], "X")
        self.assertEqual(
            row["command_replay"], "python -m tools.debugger clobbers --symbol X"
        )

    def test_finding_command_replay_falls_back_to_evidence_command(self) -> None:
        finding = auto_watch.AutoWatchFinding(
            trigger="self-test",
            trigger_id="t1",
            bug_class="ag_nn_register_clobber",
            detector="register_flow",
            evidence_command="python -m tools.debugger clobbers --symbol Y",
        )
        row = finding.as_dict()
        self.assertEqual(
            row["command_replay"], "python -m tools.debugger clobbers --symbol Y"
        )

    def test_finding_includes_evidence_when_supplied(self) -> None:
        finding = auto_watch.AutoWatchFinding(
            trigger="self-test",
            trigger_id="t1",
            bug_class="ag_nn_register_clobber",
            detector="register_flow",
            evidence_command="python -m tools.debugger clobbers --symbol X",
            evidence_exit_code=0,
            evidence_summary="clobber set includes c",
        )
        row = finding.as_dict()
        self.assertIn("evidence", row)
        evidence = row["evidence"]
        self.assertEqual(evidence["command"],
                         "python -m tools.debugger clobbers --symbol X")
        self.assertEqual(evidence["exit_code"], 0)
        self.assertEqual(evidence["summary"], "clobber set includes c")


class ValidateFindingTests(unittest.TestCase):
    def test_rejects_missing_required_field(self) -> None:
        bad = {"trigger": "self-test"}
        errors = auto_watch.validate_finding(bad)
        # trigger_id, bug_class, detector, status all missing.
        self.assertTrue(any("trigger_id" in e for e in errors))
        self.assertTrue(any("bug_class" in e for e in errors))
        self.assertTrue(any("detector" in e for e in errors))
        self.assertTrue(any("status" in e for e in errors))

    def test_rejects_bad_trigger(self) -> None:
        bad = {
            "trigger": "not-a-trigger",
            "trigger_id": "x",
            "bug_class": "ag_nn_register_clobber",
            "detector": "register_flow",
            "status": "detected",
        }
        errors = auto_watch.validate_finding(bad)
        self.assertTrue(any("trigger" in e and "not in" in e for e in errors))

    def test_rejects_bad_status(self) -> None:
        bad = {
            "trigger": "self-test",
            "trigger_id": "x",
            "bug_class": "ag_nn_register_clobber",
            "detector": "register_flow",
            "status": "made-up-status",
        }
        errors = auto_watch.validate_finding(bad)
        self.assertTrue(
            any("status" in e and "not in" in e for e in errors)
        )

    def test_rejects_bad_severity(self) -> None:
        bad = {
            "trigger": "self-test",
            "trigger_id": "x",
            "bug_class": "ag_nn_register_clobber",
            "detector": "register_flow",
            "status": "detected",
            "severity": "catastrophic",
        }
        errors = auto_watch.validate_finding(bad)
        self.assertTrue(any("severity" in e for e in errors))

    def test_accepts_valid_row(self) -> None:
        good = {
            "trigger": "self-test",
            "trigger_id": "x",
            "bug_class": "ag_nn_register_clobber",
            "detector": "register_flow",
            "status": "detected",
            "severity": "medium",
        }
        self.assertEqual(auto_watch.validate_finding(good), [])

    def test_accepts_hook_emitted_watcher_unavailable_row(self) -> None:
        """The post-commit hook in scripts/install_debugger_hooks.py emits
        a row in the both-shapes shape (roadmap fields + auto_watch fields)
        when auto-watch is missing. Verify that exact shape passes
        validate_finding so the JSONL stays single-schema across writers.
        """
        hook_row = {
            "schema_version": 1,
            "kind": "auto_watch_finding",
            "status": "watcher_unavailable",
            "trigger": "commit",
            "trigger_id": "abc1234567",
            "commit_hash": "abc1234567",
            "ts": "2026-05-23T01:30:00Z",
            "bug_class": "watcher_unavailable",
            "detector": "post_commit_hook",
            "severity": "low",
            "evidence": {
                "command": "python -m tools.debugger auto-watch --on commit --commit-hash abc1234567",
                "exit_code": 1,
                "summary": "ModuleNotFoundError: No module named 'tools.debugger.auto_watch'",
            },
            "evidence_atoms": [
                {
                    "kind": "command_exit",
                    "command": "python -m tools.debugger auto-watch --on commit --commit-hash abc1234567",
                    "exit_code": 1,
                    "stderr_tail": "ModuleNotFoundError",
                }
            ],
            "command_replay": "python -m tools.debugger auto-watch --on commit --commit-hash abc1234567",
            "llm_next_step": "Repair or finish tools.debugger auto-watch; post-commit hook is detect-and-report and exited 0.",
        }
        self.assertEqual(auto_watch.validate_finding(hook_row), [])


class AppendFindingTests(unittest.TestCase):
    def test_append_writes_one_jsonl_row(self) -> None:
        finding = auto_watch.AutoWatchFinding(
            trigger="self-test",
            trigger_id="t1",
            bug_class="ag_nn_register_clobber",
            detector="register_flow",
        )
        with TemporaryDirectory() as td:
            store = Path(td) / "findings.jsonl"
            written = auto_watch.append_finding(finding, store_path=store)
            self.assertEqual(written, store)
            text = store.read_text(encoding="utf-8")
            self.assertEqual(text.count("\n"), 1)
            row = json.loads(text.strip())
            self.assertEqual(row["trigger"], "self-test")

    def test_append_is_append_only_across_calls(self) -> None:
        f1 = auto_watch.AutoWatchFinding(
            trigger="self-test",
            trigger_id="t1",
            bug_class="ag_nn_register_clobber",
            detector="register_flow",
        )
        f2 = auto_watch.AutoWatchFinding(
            trigger="self-test",
            trigger_id="t2",
            bug_class="ag_nn_register_clobber",
            detector="register_flow",
        )
        with TemporaryDirectory() as td:
            store = Path(td) / "findings.jsonl"
            auto_watch.append_finding(f1, store_path=store)
            auto_watch.append_finding(f2, store_path=store)
            rows = store.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(rows), 2)
            self.assertEqual(json.loads(rows[0])["trigger_id"], "t1")
            self.assertEqual(json.loads(rows[1])["trigger_id"], "t2")

    def test_append_creates_parent_directory(self) -> None:
        finding = auto_watch.AutoWatchFinding(
            trigger="self-test",
            trigger_id="t1",
            bug_class="ag_nn_register_clobber",
            detector="register_flow",
        )
        with TemporaryDirectory() as td:
            store = Path(td) / "nested" / "dir" / "findings.jsonl"
            auto_watch.append_finding(finding, store_path=store)
            self.assertTrue(store.exists())


class RegisterFlowDetectorTests(unittest.TestCase):
    def test_detector_emits_finding_for_synth_broken(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / "engine").mkdir()
            (root / "engine" / "synth_broken.asm").write_text(
                auto_watch._SYNTH_BROKEN_ASM, encoding="utf-8"
            )
            finding = auto_watch.run_register_flow_detector(
                "TestStubBroken", root=root
            )
        self.assertIsNotNone(finding)
        assert finding is not None
        self.assertEqual(finding.status, "detected")
        self.assertEqual(finding.bug_class, "ag_nn_register_clobber")
        self.assertEqual(finding.detector, "register_flow")
        self.assertIn("TestStubBroken", finding.symbols)
        # Roadmap §3 P19 Findings-file contract: detector findings carry
        # evidence_atoms (§4.2) and command_replay.
        row = finding.as_dict()
        self.assertIn("evidence_atoms", row)
        self.assertEqual(row["evidence_atoms"][0]["symbol"], "TestStubBroken")
        self.assertIn("c", row["evidence_atoms"][0]["flagged_writes"])
        self.assertIn("command_replay", row)
        self.assertIn("clobbers --symbol TestStubBroken", row["command_replay"])

    def test_detector_no_finding_for_synth_fixed(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / "engine").mkdir()
            (root / "engine" / "synth_fixed.asm").write_text(
                auto_watch._SYNTH_FIXED_ASM, encoding="utf-8"
            )
            finding = auto_watch.run_register_flow_detector(
                "TestStubFixed", root=root
            )
        self.assertIsNone(finding)


class SelfTestCommandTests(unittest.TestCase):
    def test_self_test_exit_zero(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "tools.debugger.auto_watch", "--self-test"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"auto_watch --self-test failed: stdout={result.stdout!r} "
            f"stderr={result.stderr!r}",
        )
        self.assertIn(
            "auto-watch synthetic regression detected", result.stdout
        )
        self.assertIn("auto-watch self-test PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
