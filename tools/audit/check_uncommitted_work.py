#!/usr/bin/env python3
"""Tripwire for uncommitted work -- the gap that nearly lost the 2026-05-27
Magikarp pass (~2,900 lines sitting uncommitted across worktrees).

Branch-currency (check_branch_currency.py) only sees commits *behind* master;
it is blind to a *dirty* worktree. Uncommitted work -- especially new untracked
files -- is invisible to every build and audit and is the easiest work to lose
to a worktree wipe, a bad checkout, or a crash. This makes it visible and, at
session end, preserves it.

Significance: a worktree carries real work when changed lines >=
UNCOMMITTED_WORK_MIN_LINES (default 25) OR changed files >=
UNCOMMITTED_WORK_MIN_FILES (default 4), counting tracked modifications AND
untracked (non-ignored) files. Build outputs are .gitignored, so they never
count.

Modes:
  (default)   print a banner to stdout when significant; exit 0.
  --strict    exit 1 when significant (unattended autonomous loops must stop
              and commit rather than pile up unprotected work).
  --hook      emit a SessionStart hook JSON envelope when significant; exit 0.
  --snapshot  when significant, preserve the exact worktree state (tracked +
              untracked) as a commit under refs/wip-snapshots/<branch>-<ts>
              WITHOUT touching the working tree, the index, or the branch.
              For a SessionEnd hook, so nothing accumulates unprotected.

Recover a snapshot:
  git for-each-ref refs/wip-snapshots/        # list
  git show --stat <ref>                       # inspect
  git checkout <ref> -- .                     # restore into the worktree
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
DEFAULT_MIN_LINES = 25
DEFAULT_MIN_FILES = 4


def git(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        env={**os.environ, **env} if env else None,
    )


def head_base() -> str:
    """HEAD's commit sha, or the empty-tree sha on an unborn branch."""
    proc = git("rev-parse", "--verify", "--quiet", "HEAD")
    return proc.stdout.strip() if proc.returncode == 0 else EMPTY_TREE


@contextlib.contextmanager
def temp_index():
    """A throwaway git index, so staging never touches the real index."""
    fd, path = tempfile.mkstemp(prefix="uncommitted-snap-", suffix=".index")
    os.close(fd)
    os.unlink(path)  # let git create a fresh index at this path
    try:
        yield {"GIT_INDEX_FILE": path}
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(path)


def stage_all(base: str, env: dict[str, str]) -> None:
    """Seed the (temp) index from base, then stage every worktree change,
    including untracked files. .gitignored build outputs are excluded."""
    git("read-tree", base, env=env)
    git("add", "--all", env=env)


def measure(base: str) -> tuple[int, int]:
    """(changed_files, changed_lines) of the worktree vs base, via a throwaway
    index, counting tracked modifications and untracked (non-ignored) files."""
    with temp_index() as env:
        stage_all(base, env)
        numstat = git("diff", "--cached", "--numstat", base, env=env).stdout
    files = lines = 0
    for row in numstat.splitlines():
        cols = row.split("\t")
        if len(cols) < 3:
            continue
        files += 1
        added, deleted = cols[0], cols[1]  # "-" for binary files
        if added.isdigit():
            lines += int(added)
        if deleted.isdigit():
            lines += int(deleted)
    return files, lines


def is_significant(files: int, lines: int) -> bool:
    min_lines = int(os.environ.get("UNCOMMITTED_WORK_MIN_LINES", DEFAULT_MIN_LINES))
    min_files = int(os.environ.get("UNCOMMITTED_WORK_MIN_FILES", DEFAULT_MIN_FILES))
    return lines >= min_lines or files >= min_files


def branch_name() -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "detached"


def banner(files: int, lines: int) -> list[str]:
    bar = "=" * 72
    return [
        bar,
        f"!! UNCOMMITTED WORK -- {files} files / {lines} lines not committed on "
        f"'{branch_name()}' !!",
        "   This is invisible to branch-currency and every build/audit, and is the",
        "   easiest work to lose (worktree wipe, bad checkout, crash). Commit it.",
        "   At session end it is auto-snapshotted to refs/wip-snapshots/; recover:",
        "     git for-each-ref refs/wip-snapshots/",
        "     git checkout <snapshot-sha> -- .",
        bar,
    ]


def snapshot(base: str, files: int, lines: int) -> tuple[str, str]:
    """Preserve the worktree state as a commit under refs/wip-snapshots/.

    Builds the commit from a throwaway index, so the working tree, the real
    index, and the branch HEAD are all left untouched -- this only adds a ref.
    """
    branch = branch_name()
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", branch).strip("-") or "detached"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    ref = f"refs/wip-snapshots/{slug}-{stamp}"
    message = (
        f"wip-snapshot: {files} files / {lines} lines uncommitted on {branch} "
        f"at {stamp}\n\nAuto-preserved by check_uncommitted_work.py --snapshot. "
        "Not finished work; triage and land or delete deliberately."
    )
    # commit-tree needs an identity; supply one so it can't fail on missing
    # git config in an automated hook.
    ident = {
        "GIT_AUTHOR_NAME": "wip-snapshot",
        "GIT_AUTHOR_EMAIL": "wip-snapshot@local",
        "GIT_COMMITTER_NAME": "wip-snapshot",
        "GIT_COMMITTER_EMAIL": "wip-snapshot@local",
    }
    with temp_index() as env:
        stage_all(base, env)
        tree = git("write-tree", env=env).stdout.strip()
        parents = [] if base == EMPTY_TREE else ["-p", base]
        commit = git(
            "commit-tree", tree, *parents, "-m", message, env={**env, **ident}
        ).stdout.strip()
    git("update-ref", ref, commit)
    return ref, commit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Warn about / snapshot significant uncommitted worktree changes."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when significant uncommitted work exists (autonomous loops)",
    )
    parser.add_argument(
        "--hook",
        action="store_true",
        help="emit a SessionStart hook JSON envelope when significant; exit 0",
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="preserve significant uncommitted work to refs/wip-snapshots/ (SessionEnd)",
    )
    args = parser.parse_args(argv)

    base = head_base()
    files, lines = measure(base)
    significant = is_significant(files, lines)

    if args.hook:
        if significant:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": "\n".join(banner(files, lines)),
                }
            }))
        return 0

    if args.snapshot:
        if not significant:
            print(f"uncommitted-work: {files} files / {lines} lines (below threshold); nothing to snapshot.")
            return 0
        ref, commit = snapshot(base, files, lines)
        print(f"uncommitted-work: snapshotted {files} files / {lines} lines to {ref}")
        print(f"  commit:  {commit}")
        print(f"  preview: git diff HEAD {commit}")
        print(f"  restore: git checkout {commit} -- .")
        return 0

    stream = sys.stderr if args.strict else sys.stdout
    if significant:
        print("\n".join(banner(files, lines)), file=stream)
    else:
        print(f"uncommitted-work: {files} files / {lines} lines (below threshold); OK.", file=stream)
    return 1 if (args.strict and significant) else 0


if __name__ == "__main__":
    raise SystemExit(main())
