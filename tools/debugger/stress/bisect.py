"""Git bisect with scenario criterion.

``python -m tools.debugger bisect --scenario X --good <commit> --bad HEAD``

Automates ``git bisect`` using a debugger scenario as the pass/fail
criterion.  Finds the exact commit where a scenario's output changed.
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class BisectResult:
    """Result of a bisect run."""
    found_commit: str = ""
    commit_message: str = ""
    good_commit: str = ""
    bad_commit: str = ""
    steps: int = 0
    duration_s: float = 0.0
    error: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.found_commit) and not self.error

    def summary(self) -> str:
        if self.error:
            return f"Bisect failed: {self.error}"
        return (
            f"Found regression in {self.steps} steps ({self.duration_s:.1f}s)\n"
            f"  commit: {self.found_commit}\n"
            f"  message: {self.commit_message}\n"
            f"  range: {self.good_commit}..{self.bad_commit}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "found_commit": self.found_commit,
            "commit_message": self.commit_message,
            "good_commit": self.good_commit,
            "bad_commit": self.bad_commit,
            "steps": self.steps,
            "duration_s": self.duration_s,
            "error": self.error,
        }


def _run_git(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=60,
        )
        return proc.returncode, proc.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return 1, str(e)


def _get_commit_message(commit: str, cwd: Path) -> str:
    rc, msg = _run_git(["log", "--format=%s", "-1", commit], cwd)
    return msg if rc == 0 else ""


ScenarioTestFunc = Callable[[Path, str], bool]


def bisect_scenario(
    project_root: Path,
    good_commit: str,
    bad_commit: str,
    test_fn: ScenarioTestFunc,
    *,
    build_cmd: str | None = None,
) -> BisectResult:
    """Run git bisect using test_fn as the criterion.

    Args:
        project_root: Repo root.
        good_commit: Known-good commit hash.
        bad_commit: Known-bad commit hash (usually HEAD).
        test_fn: Called with (project_root, current_commit) → True if good.
        build_cmd: Optional build command to run at each step.
    """
    result = BisectResult(good_commit=good_commit, bad_commit=bad_commit)
    start = time.monotonic()

    rc, _ = _run_git(["bisect", "start"], project_root)
    if rc != 0:
        result.error = "git bisect start failed"
        return result

    rc, _ = _run_git(["bisect", "bad", bad_commit], project_root)
    if rc != 0:
        _run_git(["bisect", "reset"], project_root)
        result.error = f"git bisect bad {bad_commit} failed"
        return result

    rc, output = _run_git(["bisect", "good", good_commit], project_root)
    if rc != 0:
        _run_git(["bisect", "reset"], project_root)
        result.error = f"git bisect good {good_commit} failed"
        return result

    max_steps = 50
    for step in range(max_steps):
        result.steps = step + 1

        rc, current = _run_git(["rev-parse", "HEAD"], project_root)
        if rc != 0:
            result.error = "Could not get current HEAD"
            break

        if build_cmd:
            proc = subprocess.run(
                build_cmd, shell=True, cwd=str(project_root),
                capture_output=True, timeout=120,
            )
            if proc.returncode != 0:
                _run_git(["bisect", "skip"], project_root)
                continue

        try:
            is_good = test_fn(project_root, current)
        except Exception as e:
            _run_git(["bisect", "skip"], project_root)
            continue

        verdict = "good" if is_good else "bad"
        rc, output = _run_git(["bisect", verdict], project_root)

        if "is the first bad commit" in output or rc == 0 and not output:
            rc2, found = _run_git(["bisect", "visualize", "--oneline", "-1"], project_root)
            if rc2 != 0:
                found = current
            result.found_commit = current
            result.commit_message = _get_commit_message(current, project_root)
            break

        if "already" in output.lower():
            result.found_commit = current
            result.commit_message = _get_commit_message(current, project_root)
            break

    _run_git(["bisect", "reset"], project_root)
    result.duration_s = time.monotonic() - start
    return result


__all__ = ["BisectResult", "ScenarioTestFunc", "bisect_scenario"]
