"""Git-bisect harness for the unified debugger.

Drives ``git bisect`` against a scenario command and reports the first
commit where the scenario flips from good (exit 0) to bad (exit
nonzero). The scenario command is passed as trailing argv so Windows
quoting doesn't have to round-trip through a shell string.

V0 contract
-----------

CLI:

    python -m tools.debugger.bisect --good <commit> --bad <commit> -- <argv...>

Pre-flight (all must pass before ``git bisect start``):

- Working tree clean (``git status --porcelain`` is empty).
- ``--good`` resolves via ``git rev-parse --verify <c>^{commit}``.
- ``--bad`` resolves the same way.
- The two commits differ.

If any pre-flight fails, the repo never enters bisect state.

Loop:

- ``git bisect start``
- ``git bisect bad <bad_sha>``
- ``git bisect good <good_sha>``
- Until bisect terminates: run the scenario subprocess; mark good if
  exit 0, bad if exit nonzero. Exit code 125 is reserved by
  ``git bisect run`` for "cannot test this commit, skip" — V0 deliberately
  fails closed on 125 with a best-effort ``git bisect reset`` rather
  than marking the commit bad. False first-bad is worse than
  "unsupported in V0." ``skip`` and ``abort`` verdicts proper are
  deferred to V1.
- Best-effort ``git bisect reset`` runs in ``finally``. If the reset
  call itself errors (corrupted refs, missing HEAD, etc.) a warning
  prints to stderr; we do not raise from ``finally`` because we don't
  want a failed cleanup to mask the load-bearing bisect verdict. If
  you see the warning, run ``git bisect reset`` manually.

Returns the first bad commit's full SHA on success.

V1 candidates (deferred)
------------------------

- ``--expect "stdout contains X"`` criterion.
- ``--skip-on-exit 125`` so the scenario can signal "indeterminate".
- ``--stash-changes`` to preserve uncommitted work instead of refusing.
- ``--scenario "shell string"`` form for non-Windows users.

CLI wiring into the top-level ``python -m tools.debugger`` is held
pending a Codex sync on ``__main__.py`` (per the collision-risk list
in ``docs/omni_debugger_v2.md``). For now the module is callable via
``python -m tools.debugger.bisect``.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .catalog import ROOT


class BisectError(RuntimeError):
    """Raised on any pre-flight or invariant violation."""


@dataclass(frozen=True)
class BisectResult:
    first_bad_commit: str
    steps: int
    good_ref: str
    bad_ref: str
    good_sha: str
    bad_sha: str


_FIRST_BAD_RE = re.compile(
    r"^([0-9a-f]{4,})\s+is the first bad commit",
    re.IGNORECASE | re.MULTILINE,
)


def _run(
    cmd: Sequence[str],
    *,
    cwd: Path,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess:
    """Run a subprocess with consistent kwargs.

    ``check=True`` raises CalledProcessError on nonzero exit. The
    scenario invocation passes ``check=False`` because nonzero is the
    "bad" signal, not an error.
    """

    return subprocess.run(
        list(cmd),
        cwd=str(cwd),
        check=check,
        capture_output=capture,
        text=True,
    )


def _git(cwd: Path, *args: str, check: bool = True) -> str:
    """Run ``git <args>`` in ``cwd`` and return its stdout."""

    result = _run(["git", *args], cwd=cwd, check=check)
    if check and result.returncode != 0:  # defensive — _run(check=True) already raised
        raise BisectError(
            f"git {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout


def _preflight_clean_tree(repo: Path) -> None:
    out = _git(repo, "status", "--porcelain")
    dirty = [line for line in out.splitlines() if line.strip()]
    # Untracked files (?? prefix) don't block bisect — git switches branches
    # cleanly with untracked files in place. Tracked-modified, staged adds,
    # and other index changes do block.
    tracked = [line for line in dirty if not line.startswith("??")]
    if tracked:
        sample = ", ".join(line[3:] for line in tracked[:5])
        more = f" (+{len(tracked) - 5} more)" if len(tracked) > 5 else ""
        raise BisectError(
            f"working tree has tracked changes; refusing to bisect "
            f"(commit, stash, or restore first). Touched: {sample}{more}"
        )


def _resolve_commit(repo: Path, ref: str) -> str:
    """Return the full SHA for a ref, or raise if it doesn't resolve."""

    try:
        out = _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    except subprocess.CalledProcessError as exc:
        raise BisectError(
            f"ref {ref!r} did not resolve to a commit: "
            f"{(exc.stderr or '').strip() or exc}"
        ) from exc
    sha = out.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise BisectError(f"ref {ref!r} resolved to unexpected output: {sha!r}")
    return sha


def _bisect_active(repo: Path) -> bool:
    """Detect whether the repo is currently in bisect state."""

    return (repo / ".git" / "BISECT_LOG").exists()


def run_bisect(
    *,
    good_ref: str,
    bad_ref: str,
    scenario_argv: Sequence[str],
    repo: Path | None = None,
    max_steps: int = 60,
) -> BisectResult:
    """Drive ``git bisect`` and return the first bad commit.

    Pre-flight: clean tree, both refs resolve, refs differ. Runs the
    scenario at each midpoint; exit 0 → good, nonzero → bad. Always
    runs ``git bisect reset`` in ``finally``.
    """

    if not scenario_argv:
        raise BisectError("scenario argv must not be empty")
    work = (repo if repo is not None else Path.cwd()).resolve()
    if not (work / ".git").exists():
        raise BisectError(f"not a git repo: {work}")
    if _bisect_active(work):
        raise BisectError(
            "repo is already in a bisect state — run `git bisect reset` first"
        )

    _preflight_clean_tree(work)
    good_sha = _resolve_commit(work, good_ref)
    bad_sha = _resolve_commit(work, bad_ref)
    if good_sha == bad_sha:
        raise BisectError(
            f"--good and --bad resolve to the same commit ({good_sha[:8]}); "
            "give two distinct endpoints"
        )

    started = False
    try:
        _git(work, "bisect", "start")
        started = True
        _git(work, "bisect", "bad", bad_sha)
        # `bisect good` is the call that picks the midpoint and prints
        # either "Bisecting: N revisions left..." or the terminal "first
        # bad commit" message when there's only one step between good
        # and bad.
        bisect_msg = _git(work, "bisect", "good", good_sha)
        first_bad = _maybe_first_bad(bisect_msg)
        steps = 0
        while first_bad is None:
            steps += 1
            if steps > max_steps:
                raise BisectError(
                    f"bisect did not terminate in {max_steps} steps "
                    f"(scenario may not be deterministic)"
                )
            verdict_argv = list(scenario_argv)
            try:
                proc = _run(verdict_argv, cwd=work, check=False)
            except FileNotFoundError as exc:
                raise BisectError(
                    f"scenario command not found: {verdict_argv[0]!r}"
                ) from exc
            # Exit code 125 is reserved by `git bisect run` for "cannot
            # test this commit, skip." V0 deliberately does not support
            # skip — failing closed here is decision-useful: a false
            # first-bad sends the user chasing a non-bug, which is worse
            # than "your scenario hit an indeterminate exit code, fix
            # the scenario or wait for V1 skip support."
            if proc.returncode == 125:
                raise BisectError(
                    "scenario exited 125 — `git bisect run` reserves this for "
                    "'cannot test this commit'. V0 does not support skip; "
                    "either fix the scenario to return deterministically "
                    "(0=good, nonzero!=125=bad), or wait for V1 skip support. "
                    f"Last argv: {verdict_argv!r}"
                )
            mark = "good" if proc.returncode == 0 else "bad"
            next_msg = _git(work, "bisect", mark)
            first_bad = _maybe_first_bad(next_msg)
        return BisectResult(
            first_bad_commit=first_bad,
            steps=steps,
            good_ref=good_ref,
            bad_ref=bad_ref,
            good_sha=good_sha,
            bad_sha=bad_sha,
        )
    finally:
        if started:
            # Best-effort reset. We do not raise from finally — a
            # cleanup failure should not mask the load-bearing bisect
            # verdict (or original exception). When reset fails, surface
            # it on stderr with the recovery command so a future session
            # sees the broken state immediately.
            try:
                _git(work, "bisect", "reset")
            except (subprocess.CalledProcessError, BisectError) as cleanup_exc:
                print(
                    f"warning: `git bisect reset` failed in {work}: "
                    f"{cleanup_exc}. Run `git bisect reset` manually before "
                    f"resuming work in this checkout.",
                    file=sys.stderr,
                )


def _maybe_first_bad(bisect_output: str) -> str | None:
    """Parse the bisect output and return the first-bad SHA if present."""

    match = _FIRST_BAD_RE.search(bisect_output)
    if not match:
        return None
    return match.group(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.bisect",
        description=(
            "Run git bisect against a scenario command. Pass the scenario "
            "as trailing argv after `--` so platform shell quoting is "
            "out of the way. Refuses to start on a dirty tracked tree "
            "or on unresolvable refs."
        ),
    )
    parser.add_argument(
        "--good",
        required=True,
        help="known-good commit ref (must resolve)",
    )
    parser.add_argument(
        "--bad",
        required=True,
        help="known-bad commit ref (must resolve)",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="path to the git repo (default: cwd; falls back to the unified-debugger repo root)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=60,
        help="hard ceiling on bisect iterations (default 60, ~2^60 commits)",
    )
    parser.add_argument(
        "scenario",
        nargs=argparse.REMAINDER,
        help=(
            "scenario argv after `--`; nonzero exit means BAD, exit 0 means GOOD"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    scenario = list(args.scenario or [])
    if scenario and scenario[0] == "--":
        scenario = scenario[1:]
    if not scenario:
        parser.error("scenario argv required after `--`")
    repo = args.repo if args.repo is not None else ROOT
    try:
        result = run_bisect(
            good_ref=args.good,
            bad_ref=args.bad,
            scenario_argv=scenario,
            repo=repo,
            max_steps=args.max_steps,
        )
    except BisectError as exc:
        print(f"bisect failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"first bad commit: {result.first_bad_commit}\n"
        f"  good ref: {result.good_ref} ({result.good_sha[:12]})\n"
        f"  bad ref:  {result.bad_ref} ({result.bad_sha[:12]})\n"
        f"  steps:    {result.steps}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
