#!/usr/bin/env python3
"""Git sync hygiene for the Pokemon Mastery loop -- the A3 fix for the
divergence generator described in docs/divergence_remediation_plan.md.

Why this exists: every autonomous loop session ran on its own per-session
`claude/<name>` branch and was told "never commit to master". Iterations
therefore stranded on branches that drifted ever further behind master, and a
fresh session on such a branch would build/playtest a ROM missing already-landed
fixes and see phantom "regressions". `loop_runner.py` had zero git awareness, so
nothing pulled the work back together.

These two operations converge loop work onto ONE shared integration line
(master, by default) instead of scattering it:

  sync-preflight  Run BEFORE an iteration. Rebases the working branch onto the
                  canonical base (local `master`) so the iteration starts
                  current, then runs the integrity gate. Refuses -- cleanly,
                  leaving the branch untouched -- if the tree is dirty, the
                  rebase conflicts, or the gate is red.

  land            Run AFTER the iteration's commits pass. Fast-forwards the
                  shared integration line to HEAD. FF-only and worktree-safe:
                  it refuses rather than rewrite history or desync a branch
                  that is checked out in another worktree.

The integrity gate is deliberately NOT the full pgoal verify.txt. That file
also lists the loop's *aspirational* gates (verify_progress_gate,
verify_case_breadth) which stay red until the loop has finished training -- so
gating `land` on them would make it never succeed. The gate here is the
per-iteration SAFETY subset only:

  * unit tests still pass,
  * library schema valid + no tier contamination (verify_loop_state),
  * regression battery 100% green (a hard loop invariant per constraints.txt),
  * the branch is current with master (the A2 currency tripwire).

Reached as `loop_runner.py sync-preflight` / `loop_runner.py land`; the CLI
surface lives there, the logic lives here.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FETCH_TIMEOUT_SECONDS = 60


def _land_gate() -> list[list[str]]:
    """The per-iteration safety gate (see module docstring for why this is a
    subset of verify.txt). Built lazily so it always uses the live
    sys.executable rather than freezing one at import time."""
    py = sys.executable
    return [
        [py, "-m", "pytest", "tools/pokemon_mastery/", "-q"],
        [py, "tools/pokemon_mastery/verify_loop_state.py"],
        [py, "tools/pokemon_mastery/verify_regression_battery.py"],
        [py, "tools/audit/check_branch_currency.py", "--strict"],
    ]


def git(*args: str, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def ref_exists(ref: str) -> bool:
    return git("rev-parse", "--verify", "--quiet", ref).returncode == 0


def current_branch() -> str | None:
    """Short branch name, or None when HEAD is detached."""
    proc = git("symbolic-ref", "--quiet", "--short", "HEAD")
    return proc.stdout.strip() if proc.returncode == 0 else None


def head_sha() -> str:
    return git("rev-parse", "HEAD").stdout.strip()


def tracked_dirty() -> str:
    """Uncommitted *tracked* changes, the porcelain lines. Untracked files are
    ignored: they don't block a rebase and don't change what `land` advances.
    An iteration's data changes must be committed before either op runs."""
    return git("status", "--porcelain", "--untracked-files=no").stdout.strip()


def resolve_base(explicit: str | None) -> str | None:
    """First base ref that exists: --base, env, local master, origin/master.
    Local master is canonical in this repo (origin is not kept current), so it
    is preferred over origin/master. Mirrors check_branch_currency.py (kept
    local so tests can resolve against a monkeypatched sync.ROOT)."""
    for ref in (explicit, os.environ.get("BRANCH_CURRENCY_BASE"), "master", "origin/master"):
        if ref and ref_exists(ref):
            return ref
    return None


def is_ancestor(maybe_ancestor: str, descendant: str) -> bool:
    return git("merge-base", "--is-ancestor", maybe_ancestor, descendant).returncode == 0


def worktree_branch_paths() -> dict[str, str]:
    """Map of short branch name -> worktree path for every checked-out branch.
    Used to refuse advancing a branch that is live in another worktree."""
    out = git("worktree", "list", "--porcelain").stdout
    paths: dict[str, str] = {}
    path: str | None = None
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line.startswith("branch ") and path is not None:
            name = line[len("branch "):].split("refs/heads/", 1)[-1]
            paths[name] = path
    return paths


def run_gate() -> list[tuple[str, str]]:
    """Run the integrity gate; return (command, output-tail) for each failure."""
    failures: list[tuple[str, str]] = []
    for cmd in _land_gate():
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if proc.returncode != 0:
            tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-15:])
            failures.append((" ".join(cmd[1:]), tail))
    return failures


def _report_gate(failures: list[tuple[str, str]]) -> None:
    for cmd, tail in failures:
        print(f"  FAILED: {cmd}", file=sys.stderr)
        for line in tail.splitlines():
            print(f"    | {line}", file=sys.stderr)


def _refuse(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def sync_preflight(base: str | None = None, do_fetch: bool = True) -> int:
    """Rebase the working branch onto canonical master and gate it. Returns a
    process exit code: 0 = current + green, safe to run the iteration; nonzero
    = refused (branch left in a safe, unchanged state)."""
    branch = current_branch()
    if branch is None:
        return _refuse(
            "sync-preflight REFUSED: HEAD is detached. Check out the loop's "
            "working branch before syncing."
        )
    target = resolve_base(base)
    if target is None:
        return _refuse(
            "sync-preflight REFUSED: no canonical base (master / origin/master) found."
        )

    dirty = tracked_dirty()
    if dirty:
        return _refuse(
            "sync-preflight REFUSED: uncommitted tracked changes present:\n"
            f"{dirty}\n"
            "  Commit the iteration (or snapshot via "
            "`python tools/audit/check_uncommitted_work.py --snapshot`) first."
        )

    if do_fetch:
        try:
            fetch = git("fetch", "--quiet", timeout=FETCH_TIMEOUT_SECONDS)
            if fetch.returncode != 0:
                print(
                    "sync-preflight: `git fetch` failed (non-fatal; local master is "
                    f"canonical here):\n  {fetch.stderr.strip()}",
                    file=sys.stderr,
                )
        except subprocess.TimeoutExpired:
            print(
                "sync-preflight: `git fetch` timed out (non-fatal; rebasing onto "
                "local master).",
                file=sys.stderr,
            )

    if branch != target:
        rebase = git("rebase", target)
        if rebase.returncode != 0:
            git("rebase", "--abort")
            return _refuse(
                f"sync-preflight REFUSED: rebase onto {target} hit conflicts "
                "(aborted; branch unchanged). Resolve the overlap manually, then "
                "retry.\n" + (rebase.stdout + rebase.stderr).strip()
            )

    failures = run_gate()
    if failures:
        _report_gate(failures)
        return _refuse(
            "sync-preflight REFUSED: integrity gate is red after rebase. Fix the "
            "above before running the iteration."
        )

    where = "is the integration line" if branch == target else f"rebased onto {target}"
    print(f"sync-preflight OK: '{branch}' {where}; integrity gate green. Safe to run the iteration.")
    return 0


def land(into: str = "master") -> int:
    """Fast-forward the shared integration line `into` to HEAD. Returns a
    process exit code: 0 = landed (or already landed); nonzero = refused."""
    branch = current_branch()
    if branch is None:
        return _refuse(
            "land REFUSED: HEAD is detached. Check out the loop's working branch first."
        )
    if not ref_exists(f"refs/heads/{into}"):
        return _refuse(f"land REFUSED: no local branch '{into}' to land into.")
    if branch == into:
        print(f"land: already on the integration line '{into}'; nothing to land.")
        return 0

    dirty = tracked_dirty()
    if dirty:
        return _refuse(
            "land REFUSED: uncommitted tracked changes present -- commit the "
            f"iteration before landing:\n{dirty}"
        )

    head = head_sha()
    target_sha = git("rev-parse", into).stdout.strip()
    if head == target_sha:
        print(f"land: '{into}' is already at HEAD ({head[:9]}); nothing to land.")
        return 0
    if not is_ancestor(into, head):
        return _refuse(
            f"land REFUSED: not a fast-forward -- '{into}' has commits not in "
            f"'{branch}'. Run `loop_runner.py sync-preflight` first to rebase onto it."
        )

    checked_out = worktree_branch_paths()
    if into in checked_out:
        return _refuse(
            f"land REFUSED: '{into}' is checked out at {checked_out[into]}; "
            "advancing it here would desync that worktree. Land from there, or "
            "land into a branch that isn't checked out."
        )

    failures = run_gate()
    if failures:
        _report_gate(failures)
        return _refuse(
            f"land REFUSED: integrity gate is red -- not advancing '{into}' to a "
            "broken state."
        )

    update = git("update-ref", f"refs/heads/{into}", head, target_sha)
    if update.returncode != 0:
        return _refuse(
            f"land REFUSED: update-ref failed (did '{into}' move under us?):\n"
            + update.stderr.strip()
        )

    n = git("rev-list", "--count", f"{target_sha}..{head}").stdout.strip()
    print(
        f"landed: '{into}' {target_sha[:9]} -> {head[:9]} "
        f"({n} commit{'s' if n != '1' else ''}, fast-forward) from '{branch}'."
    )
    return 0
