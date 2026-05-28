#!/usr/bin/env python3
"""Warn (or fail) loudly when the current branch is behind canonical master on
gameplay-critical paths.

Why this exists: the repo is developed by many parallel sessions, each on its
own per-session worktree branch. Those branches go stale versus master and get
built and playtested unknowingly, so already-fixed bugs resurface as phantom
"regressions". Nothing else surfaces that staleness -- a stale branch still
builds, and every other audit only checks a branch's *internal* consistency,
not its currency versus master. This is the missing tripwire.

Modes:
  (default)   print a loud banner if behind master on critical paths; exit 0.
  --strict    exit 1 when behind on critical paths. Use in the release-smoke
              floor and for unattended autonomous loops, which must hard-stop
              rather than silently proceed. (env BRANCH_CURRENCY_STRICT=1 too.)

Base ref resolution, first that exists: --base REF, env BRANCH_CURRENCY_BASE,
local `master`, `origin/master`. Local master is authoritative in this repo
(origin is not kept current). Needs no build artifact, so it runs pre-build.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Paths whose absence from a build would change in-game behavior. Drift here is
# what turns a stale playtest into a misleading one; drift in tools/ or docs/
# does not. (engine/battle/ covers engine/battle/ai/; ram/ covers wram.asm.)
CRITICAL_PATHS = (
    "engine/battle/",
    "data/trainers/",
    "data/pokemon/",
    "data/moves/",
    "ram/",
)
MAX_LISTED = 15


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def ref_exists(ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet", ref],
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )


def resolve_base(explicit: str | None) -> str | None:
    candidates = (explicit, os.environ.get("BRANCH_CURRENCY_BASE"), "master", "origin/master")
    for ref in candidates:
        if ref and ref_exists(ref):
            return ref
    return None


def count(rev_range: str, *paths: str) -> int:
    out = git("rev-list", "--count", "--no-merges", rev_range, "--", *paths)
    return int(out) if out.isdigit() else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Warn/fail when the branch is behind canonical master on gameplay paths."
    )
    parser.add_argument("--base", help="canonical ref to compare against (default: master)")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when behind on critical paths (release-smoke floor / autonomous loops)",
    )
    args = parser.parse_args(argv)
    strict = args.strict or os.environ.get("BRANCH_CURRENCY_STRICT") == "1"

    base = resolve_base(args.base)
    if base is None:
        print("branch-currency: no canonical ref (master / origin/master) found; skipping.")
        return 0

    head = git("rev-parse", "--abbrev-ref", "HEAD")
    base_sha = git("rev-parse", "--short", base)

    behind = int(git("rev-list", "--count", f"HEAD..{base}") or 0)
    if behind == 0:
        print(f"branch-currency: '{head}' is current with {base} ({base_sha}).")
        return 0

    critical = [line for line in git(
        "log", "--oneline", "--no-merges", f"HEAD..{base}", "--", *CRITICAL_PATHS
    ).splitlines() if line.strip()]

    if not critical:
        print(
            f"branch-currency: '{head}' is {behind} commits behind {base}, but none touch "
            "gameplay-critical paths -- OK to build/playtest."
        )
        return 0

    buckets = [f"{path} {n}" for path in CRITICAL_PATHS if (n := count(f'HEAD..{base}', path))]
    out = sys.stderr if strict else sys.stdout
    bar = "=" * 72
    print(bar, file=out)
    print(f"!! STALE BRANCH -- '{head}' is {behind} commits behind {base} ({base_sha}) !!", file=out)
    print(f"   {len(critical)} of those commits touch GAMEPLAY-CRITICAL paths. A ROM built", file=out)
    print('   here may be MISSING fixes that already exist on master, so "regressions"', file=out)
    print("   you see in playtest may be phantom. Rebase onto master before trusting", file=out)
    print("   a playtest or reporting a bug.", file=out)
    print(f"   behind on: {'   '.join(buckets)}", file=out)
    print("   missing gameplay commits (newest first):", file=out)
    for line in critical[:MAX_LISTED]:
        print(f"     {line}", file=out)
    if len(critical) > MAX_LISTED:
        print(f"     ... and {len(critical) - MAX_LISTED} more", file=out)
    print("   intentional? run without --strict / unset BRANCH_CURRENCY_STRICT.", file=out)
    print(bar, file=out)

    return 1 if strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
