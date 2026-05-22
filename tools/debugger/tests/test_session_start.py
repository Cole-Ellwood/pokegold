from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.debugger.catalog import ROOT
from tools.debugger.session_start import (
    RECOMMENDED_COMMANDS,
    SessionStartReport,
    WorkingTreeSummary,
    _active_probe_summary,
    _format_text,
    _truncate,
    build_session_start_report,
    main,
)
from tools.debugger.probe import declare_probe
from tools.debugger.selftest import CheckResult, SelftestReport


class TruncateTests(unittest.TestCase):
    def test_short_text_unchanged(self) -> None:
        self.assertEqual(_truncate("short", 10), "short")

    def test_long_text_truncated_with_ellipsis(self) -> None:
        result = _truncate("hello world this is long", 12)
        self.assertEqual(len(result), 12)
        self.assertTrue(result.endswith("..."))


class WorkingTreeSummaryTests(unittest.TestCase):
    def test_jsonable_round_trips(self) -> None:
        tree = WorkingTreeSummary(tracked_modified=2, tracked_added=1, tracked_deleted=0, untracked=5)
        encoded = json.dumps(tree.to_jsonable(), sort_keys=True)
        decoded = json.loads(encoded)
        self.assertEqual(decoded["tracked_modified"], 2)
        self.assertEqual(decoded["untracked"], 5)


class ReportFormatTests(unittest.TestCase):
    def _sample(self, *, selftest_ok: bool = True, fails: list[str] | None = None) -> SessionStartReport:
        return SessionStartReport(
            selftest_ok=selftest_ok,
            selftest_components_failed=fails or [],
            selftest_summary_line="selftest PASS (13/13 components healthy)" if selftest_ok else "selftest FAIL (12/13 components healthy)",
            active_probe_count=2,
            probe_store="audit/probes.jsonl",
            open_hypotheses=[
                {
                    "id": "h_test_x",
                    "symptom": "physical damage 5x too high",
                    "claim": "AG-NN clobber suspected",
                    "confidence": "repo-proven",
                    "citation_stale": False,
                },
            ],
            open_hypothesis_count=1,
            stale_citation_count=0,
            latest_commits=[
                "abc1234 commit-a",
                "def5678 commit-b",
                "fed8765 commit-c",
            ],
            working_tree=WorkingTreeSummary(tracked_modified=1, tracked_added=0, tracked_deleted=0, untracked=42),
            git_branch="codex/main",
        )

    def test_passing_selftest_text_has_no_fail_block(self) -> None:
        text = _format_text(self._sample())
        self.assertIn("selftest PASS", text)
        self.assertNotIn("FAIL:", text)
        self.assertIn("codex/main", text)

    def test_failing_selftest_text_names_failing_component_and_next_command(self) -> None:
        text = _format_text(self._sample(selftest_ok=False, fails=["coverage"]))
        self.assertIn("selftest FAIL", text)
        self.assertIn("FAIL: coverage", text)
        self.assertIn("python -m tools.debugger.selftest", text)

    def test_open_hypothesis_is_rendered_with_confidence_and_symptom(self) -> None:
        text = _format_text(self._sample())
        self.assertIn("h_test_x", text)
        self.assertIn("repo-proven", text)
        self.assertIn("physical damage 5x too high", text)

    def test_active_probe_count_is_rendered(self) -> None:
        text = _format_text(self._sample())
        self.assertIn("active probes: 2", text)
        self.assertIn("audit/probes.jsonl", text)

    def test_recommended_commands_block_present(self) -> None:
        text = _format_text(self._sample())
        for cmd in RECOMMENDED_COMMANDS:
            self.assertIn(cmd, text)

    def test_working_tree_summary_inlines_without_path_dump(self) -> None:
        text = _format_text(self._sample())
        self.assertIn("untracked=42", text)
        # Path-dump anti-pattern: a real path string would never appear
        # in the summary form.
        self.assertNotIn(".local/", text)
        self.assertNotIn("audit/boss_ai_debugger/runs", text)


class JsonOutputTests(unittest.TestCase):
    def test_to_jsonable_round_trips(self) -> None:
        report = SessionStartReport(
            selftest_ok=True,
            selftest_components_failed=[],
            selftest_summary_line="selftest PASS (1/1)",
            active_probe_count=0,
            probe_store="audit/probes.jsonl",
            open_hypotheses=[],
            open_hypothesis_count=0,
            stale_citation_count=0,
            latest_commits=["abc commit"],
            working_tree=WorkingTreeSummary(0, 0, 0, 1),
            git_branch="main",
        )
        encoded = json.dumps(report.to_jsonable(), sort_keys=True)
        decoded = json.loads(encoded)
        self.assertTrue(decoded["selftest_ok"])
        self.assertEqual(decoded["git_branch"], "main")
        self.assertEqual(decoded["active_probe_count"], 0)
        self.assertEqual(decoded["working_tree"]["untracked"], 1)


class ExitCodeTests(unittest.TestCase):
    def test_main_exits_zero_when_selftest_passes(self) -> None:
        captured = io.StringIO()
        with redirect_stdout(captured):
            rc = main([])
        self.assertEqual(rc, 0)

    def test_main_exits_nonzero_when_selftest_fails(self) -> None:
        # Mock the builder to force a failure path. The real selftest
        # runs against the live catalog (slow); this test only cares
        # about the exit-code contract.
        with patch("tools.debugger.session_start.build_session_start_report") as builder:
            builder.return_value = SessionStartReport(
                selftest_ok=False,
                selftest_components_failed=["capability_audit"],
                selftest_summary_line="selftest FAIL (0/1 components healthy)",
                active_probe_count=0,
                probe_store="audit/probes.jsonl",
                open_hypotheses=[],
                open_hypothesis_count=0,
                stale_citation_count=0,
                latest_commits=[],
                working_tree=WorkingTreeSummary(0, 0, 0, 0),
                git_branch="main",
            )
            captured = io.StringIO()
            with redirect_stdout(captured):
                rc = main([])
            self.assertEqual(rc, 1)

    def test_main_json_emits_valid_json(self) -> None:
        captured = io.StringIO()
        with redirect_stdout(captured):
            rc = main(["--json"])
        self.assertEqual(rc, 0)
        payload = json.loads(captured.getvalue())
        self.assertIn("selftest_ok", payload)
        self.assertIn("selftest_summary_line", payload)
        self.assertIn("working_tree", payload)


class IntegrationTests(unittest.TestCase):
    """Pairing rule #5 — real workflow test. Run the actual builder
    against the live repo and assert the contract: selftest passes on
    this branch, the report has all fields populated, and the working
    tree summary is integers (not path dumps)."""

    def test_real_session_start_against_live_repo(self) -> None:
        report = build_session_start_report()
        self.assertTrue(
            report.selftest_ok,
            f"selftest failed: {report.selftest_components_failed}",
        )
        # All structural fields populated.
        self.assertIsInstance(report.latest_commits, list)
        self.assertIsInstance(report.active_probe_count, int)
        self.assertIsInstance(report.working_tree.untracked, int)
        # Branch should be readable.
        self.assertTrue(len(report.git_branch) > 0)

    def test_probe_summary_counts_active_deduped_probes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            declare_probe(name="damage_calc_entry", pc="01:5A00", root=root)
            declare_probe(name="damage_calc_entry", pc="02:4100", root=root)
            declare_probe(name="boss_ai_choose", pc="02:4100", root=root)

            count, store = _active_probe_summary(root)

        self.assertEqual(count, 2)
        self.assertTrue(store.endswith("audit\\probes.jsonl") or store.endswith("audit/probes.jsonl"))


if __name__ == "__main__":
    unittest.main()
