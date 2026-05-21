from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tools.debugger.bisect import (
    BisectError,
    _maybe_first_bad,
    _preflight_clean_tree,
    _resolve_commit,
    run_bisect,
)


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _make_synthetic_repo(
    base: Path,
    *,
    flip_at_index: int = 3,
    total_commits: int = 5,
) -> tuple[Path, list[str]]:
    """Create a temp git repo with N commits.

    A ``marker.txt`` file holds ``good`` for commits before
    ``flip_at_index`` and ``broken`` for commits at and after it. The
    bisect should identify ``commits[flip_at_index]`` as the first bad
    commit when the scenario reads marker.txt and exits nonzero on
    ``broken``.
    """

    repo = base / "synth_repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Bisect Test")
    # Disable signing to avoid GPG prompts in CI/local.
    _git(repo, "config", "commit.gpgsign", "false")
    # Make sure HEAD doesn't pick up the user's global default branch
    # name surprises.
    _git(repo, "checkout", "-b", "main")
    commits: list[str] = []
    for idx in range(total_commits):
        # marker.txt carries the bug signal; seq.txt makes every commit
        # non-empty so git accepts them even when marker is unchanged.
        marker = repo / "marker.txt"
        marker.write_text("broken" if idx >= flip_at_index else "good")
        (repo / "seq.txt").write_text(str(idx))
        _git(repo, "add", "marker.txt", "seq.txt")
        _git(repo, "commit", "-m", f"commit-{idx}", "--quiet")
        commits.append(_git(repo, "rev-parse", "HEAD").strip())
    return repo, commits


class ParseFirstBadTests(unittest.TestCase):
    def test_parse_extracts_sha_from_bisect_terminal_message(self) -> None:
        sample = (
            "abc1234567890abcdefabcdefabcdef1234567890 is the first bad commit\n"
            "commit abc1234567890abcdefabcdefabcdef1234567890\n"
            "Author: x <x@x>\n"
        )
        self.assertEqual(
            _maybe_first_bad(sample),
            "abc1234567890abcdefabcdefabcdef1234567890",
        )

    def test_parse_returns_none_when_not_terminal(self) -> None:
        sample = "Bisecting: 12 revisions left to test after this (roughly 4 steps)"
        self.assertIsNone(_maybe_first_bad(sample))


class PreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.commits = _make_synthetic_repo(Path(self.tmp.name))

    def test_clean_tree_passes(self) -> None:
        _preflight_clean_tree(self.repo)

    def test_tracked_modification_blocks(self) -> None:
        (self.repo / "marker.txt").write_text("dirty edit")
        with self.assertRaises(BisectError) as cm:
            _preflight_clean_tree(self.repo)
        self.assertIn("tracked changes", str(cm.exception))

    def test_untracked_does_not_block(self) -> None:
        # Untracked files don't break bisect since git switches branches
        # cleanly past them.
        (self.repo / "untracked.txt").write_text("ignored")
        _preflight_clean_tree(self.repo)

    def test_resolve_commit_succeeds_for_real_sha(self) -> None:
        sha = _resolve_commit(self.repo, self.commits[2])
        self.assertEqual(sha, self.commits[2])

    def test_resolve_commit_succeeds_for_head(self) -> None:
        sha = _resolve_commit(self.repo, "HEAD")
        self.assertEqual(sha, self.commits[-1])

    def test_resolve_commit_raises_on_unknown_ref(self) -> None:
        with self.assertRaises(BisectError):
            _resolve_commit(self.repo, "does-not-exist-xyz")


class BisectRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo, self.commits = _make_synthetic_repo(Path(self.tmp.name))
        # The scenario reads marker.txt; "good" exits 0, anything else
        # exits 1. Quote-safe argv (no shell).
        self.scenario = [
            sys.executable,
            "-c",
            "import pathlib,sys; "
            "sys.exit(0 if pathlib.Path('marker.txt').read_text()=='good' else 1)",
        ]

    def test_bisect_finds_injected_bad_commit(self) -> None:
        # Lived smoke: synthetic regression at commits[3].
        result = run_bisect(
            good_ref=self.commits[0],
            bad_ref=self.commits[4],
            scenario_argv=self.scenario,
            repo=self.repo,
        )
        self.assertEqual(result.first_bad_commit, self.commits[3])
        self.assertEqual(result.good_sha, self.commits[0])
        self.assertEqual(result.bad_sha, self.commits[4])
        self.assertGreater(result.steps, 0)
        # Bisect must have reset cleanly (no leftover BISECT_LOG).
        self.assertFalse((self.repo / ".git" / "BISECT_LOG").exists())

    def test_bisect_resets_state_even_when_good_equals_bad(self) -> None:
        with self.assertRaises(BisectError) as cm:
            run_bisect(
                good_ref=self.commits[2],
                bad_ref=self.commits[2],
                scenario_argv=self.scenario,
                repo=self.repo,
            )
        self.assertIn("same commit", str(cm.exception))
        self.assertFalse((self.repo / ".git" / "BISECT_LOG").exists())

    def test_bisect_refuses_dirty_tree(self) -> None:
        (self.repo / "marker.txt").write_text("dirty edit")
        with self.assertRaises(BisectError) as cm:
            run_bisect(
                good_ref=self.commits[0],
                bad_ref=self.commits[4],
                scenario_argv=self.scenario,
                repo=self.repo,
            )
        self.assertIn("tracked changes", str(cm.exception))
        self.assertFalse((self.repo / ".git" / "BISECT_LOG").exists())

    def test_bisect_refuses_unresolvable_good(self) -> None:
        with self.assertRaises(BisectError):
            run_bisect(
                good_ref="nope-not-a-real-ref",
                bad_ref=self.commits[4],
                scenario_argv=self.scenario,
                repo=self.repo,
            )
        self.assertFalse((self.repo / ".git" / "BISECT_LOG").exists())

    def test_bisect_refuses_unresolvable_bad(self) -> None:
        with self.assertRaises(BisectError):
            run_bisect(
                good_ref=self.commits[0],
                bad_ref="nope-not-a-real-ref",
                scenario_argv=self.scenario,
                repo=self.repo,
            )
        self.assertFalse((self.repo / ".git" / "BISECT_LOG").exists())

    def test_bisect_resets_when_scenario_command_missing(self) -> None:
        with self.assertRaises(BisectError) as cm:
            run_bisect(
                good_ref=self.commits[0],
                bad_ref=self.commits[4],
                scenario_argv=["definitely-not-a-real-executable-xyz"],
                repo=self.repo,
            )
        self.assertIn("scenario command not found", str(cm.exception))
        self.assertFalse((self.repo / ".git" / "BISECT_LOG").exists())

    def test_bisect_rejects_empty_scenario(self) -> None:
        with self.assertRaises(BisectError):
            run_bisect(
                good_ref=self.commits[0],
                bad_ref=self.commits[4],
                scenario_argv=[],
                repo=self.repo,
            )


if __name__ == "__main__":
    unittest.main()
