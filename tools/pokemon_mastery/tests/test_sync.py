"""Hermetic tests for the loop's git sync hygiene (A3).

Each test builds a throwaway git repo in tmp_path, points sync.ROOT at it, and
stubs the integrity gate (sync.run_gate) so nothing shells out to the real
verifiers or the network. They exercise the refusal paths (the whole value of
the feature is refusing unsafe operations) plus the happy fast-forward.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools.pokemon_mastery import sync


def g(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    g(path, "init", "-b", "master")
    g(path, "config", "user.email", "t@t")
    g(path, "config", "user.name", "tester")
    return path


def commit(path: Path, fname: str, content: str, msg: str) -> str:
    (path / fname).write_text(content, encoding="utf-8")
    g(path, "add", fname)
    g(path, "commit", "-m", msg)
    return g(path, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Path:
    r = init_repo(tmp_path / "repo")
    monkeypatch.setattr(sync, "ROOT", r)
    return r


@pytest.fixture
def green_gate(monkeypatch):
    """Default: integrity gate passes, so tests focus on git correctness."""
    monkeypatch.setattr(sync, "run_gate", lambda: [])


# --- sync-preflight -------------------------------------------------------

def test_preflight_refuses_detached_head(repo, green_gate):
    commit(repo, "f", "v0", "c0")
    g(repo, "checkout", "--detach")
    assert sync.sync_preflight(do_fetch=False) == 1


def test_preflight_refuses_dirty_tree(repo, green_gate):
    commit(repo, "f", "v0", "c0")
    g(repo, "checkout", "-b", "work")
    (repo / "f").write_text("dirty", encoding="utf-8")  # uncommitted tracked change
    assert sync.sync_preflight(do_fetch=False) == 1


def test_preflight_on_master_skips_rebase_and_passes(repo, green_gate):
    commit(repo, "f", "v0", "c0")  # already on master
    assert sync.sync_preflight(do_fetch=False) == 0


def test_preflight_rebases_behind_branch_onto_master(repo, green_gate):
    commit(repo, "f", "v0", "c0")
    g(repo, "checkout", "-b", "work")
    commit(repo, "w", "w1", "work1")        # work ahead by 1
    g(repo, "checkout", "master")
    commit(repo, "m", "m1", "master1")       # master ahead by 1 (diverged, no conflict)
    g(repo, "checkout", "work")
    assert sync.sync_preflight(do_fetch=False) == 0
    # master is now an ancestor of work, and work's own change survived the rebase.
    assert sync.is_ancestor("master", "HEAD")
    assert (repo / "w").read_text(encoding="utf-8") == "w1"
    assert (repo / "m").read_text(encoding="utf-8") == "m1"


def test_preflight_aborts_and_refuses_on_conflict(repo, green_gate):
    commit(repo, "f", "base", "c0")
    g(repo, "checkout", "-b", "work")
    work_head = commit(repo, "f", "work-side", "work-edit")
    g(repo, "checkout", "master")
    commit(repo, "f", "master-side", "master-edit")  # conflicts with work's edit
    g(repo, "checkout", "work")
    assert sync.sync_preflight(do_fetch=False) == 1
    # Rebase was aborted: branch unchanged, no rebase state left behind.
    assert g(repo, "rev-parse", "HEAD") == work_head
    assert (repo / "f").read_text(encoding="utf-8") == "work-side"
    assert not (repo / ".git" / "rebase-merge").exists()
    assert not (repo / ".git" / "rebase-apply").exists()


def test_preflight_refuses_on_red_gate(repo, monkeypatch):
    commit(repo, "f", "v0", "c0")
    monkeypatch.setattr(sync, "run_gate", lambda: [("verify_loop_state.py", "boom")])
    assert sync.sync_preflight(do_fetch=False) == 1


# --- land -----------------------------------------------------------------

def test_land_noop_on_integration_line_itself(repo, green_gate):
    commit(repo, "f", "v0", "c0")  # on master
    assert sync.land(into="master") == 0


def test_land_noop_when_target_equals_head(repo, green_gate):
    commit(repo, "f", "v0", "c0")
    g(repo, "checkout", "-b", "work")  # work == master
    assert sync.land(into="master") == 0
    assert g(repo, "rev-parse", "master") == g(repo, "rev-parse", "work")


def test_land_fast_forwards_safe_target(repo, green_gate):
    commit(repo, "f", "v0", "c0")
    g(repo, "checkout", "-b", "work")
    commit(repo, "w1", "a", "work1")
    head = commit(repo, "w2", "b", "work2")
    assert sync.land(into="master") == 0
    assert g(repo, "rev-parse", "master") == head  # master fast-forwarded to HEAD


def test_land_refuses_non_fast_forward(repo, green_gate):
    commit(repo, "f", "v0", "c0")
    g(repo, "checkout", "-b", "work")
    commit(repo, "w", "w1", "work1")
    g(repo, "checkout", "master")
    master_head = commit(repo, "m", "m1", "master1")  # master diverged from work
    g(repo, "checkout", "work")
    assert sync.land(into="master") == 1
    assert g(repo, "rev-parse", "master") == master_head  # untouched


def test_land_refuses_dirty_tree(repo, green_gate):
    commit(repo, "f", "v0", "c0")
    g(repo, "checkout", "-b", "work")
    base_master = g(repo, "rev-parse", "master")
    commit(repo, "w", "w1", "work1")
    (repo / "f").write_text("dirty", encoding="utf-8")
    assert sync.land(into="master") == 1
    assert g(repo, "rev-parse", "master") == base_master


def test_land_refuses_when_target_checked_out_elsewhere(repo, green_gate, tmp_path):
    commit(repo, "f", "v0", "c0")
    g(repo, "checkout", "-b", "work")
    base_master = g(repo, "rev-parse", "master")
    commit(repo, "w", "w1", "work1")  # work is a clean FF over master...
    g(repo, "worktree", "add", str(tmp_path / "wt_master"), "master")  # ...but master is live elsewhere
    assert sync.land(into="master") == 1
    assert g(repo, "rev-parse", "master") == base_master  # not desynced


def test_land_refuses_on_red_gate(repo, monkeypatch):
    commit(repo, "f", "v0", "c0")
    g(repo, "checkout", "-b", "work")
    base_master = g(repo, "rev-parse", "master")
    commit(repo, "w", "w1", "work1")
    monkeypatch.setattr(sync, "run_gate", lambda: [("verify_regression_battery.py", "boom")])
    assert sync.land(into="master") == 1
    assert g(repo, "rev-parse", "master") == base_master  # gate runs before update-ref


def test_land_refuses_missing_target_branch(repo, green_gate):
    commit(repo, "f", "v0", "c0")
    g(repo, "checkout", "-b", "work")
    assert sync.land(into="nonexistent") == 1
