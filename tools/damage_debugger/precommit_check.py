"""Claude PreToolUse guard for damage-chain clobber smoke.

This is not a Git hook. It is wired from `.claude/settings.json` as a
PreToolUse command hook, so it runs before Claude executes a shell command.
If the command is not `git commit`, it exits 0. If the pending commit touches
damage-chain ABI-sensitive asm files, it runs `clobber_smoke` and blocks the
tool call on failure.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


TARGET_PATHS = frozenset({
    "engine/battle/effect_commands.asm",
    "engine/battle/late_gen_held_items.asm",
    "engine/battle/type_passive_damage_mods.asm",
    "home/farcall.asm",
})

DEFAULT_SMOKE_COMMAND = [
    sys.executable,
    "-m",
    "tools.damage_debugger.clobber_smoke",
]


def _norm(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def _split_command(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=os.name != "nt")
    except ValueError:
        return command.split()


def is_git_commit_command(command: str) -> bool:
    tokens = _split_command(command)
    for index, token in enumerate(tokens):
        if Path(token).name.lower() not in {"git", "git.exe"}:
            continue
        j = index + 1
        while j < len(tokens):
            current = tokens[j]
            if current == "-C" and j + 1 < len(tokens):
                j += 2
                continue
            if current == "-c" and j + 1 < len(tokens):
                j += 2
                continue
            if current.startswith("--git-dir=") or current.startswith("--work-tree="):
                j += 1
                continue
            if current.startswith("-"):
                j += 1
                continue
            return current == "commit"
    return False


def command_requests_all_tracked(command: str) -> bool:
    tokens = _split_command(command)
    if "commit" not in tokens:
        return False
    for token in tokens[tokens.index("commit") + 1:]:
        if token == "--":
            return False
        if token == "--all":
            return True
        if token.startswith("--"):
            continue
        if token.startswith("-") and "a" in token[1:]:
            return True
    return False


def extract_command_from_event(stdin_text: str, explicit_command: str | None) -> str:
    if explicit_command is not None:
        return explicit_command
    if not stdin_text.strip():
        return ""
    try:
        event = json.loads(stdin_text)
    except json.JSONDecodeError:
        return ""
    tool_input = event.get("tool_input")
    if isinstance(tool_input, dict) and isinstance(tool_input.get("command"), str):
        return tool_input["command"]
    if isinstance(event.get("command"), str):
        return event["command"]
    return ""


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def changed_paths_for_pending_commit(repo: Path, command: str) -> set[str]:
    paths: set[str] = set()

    staged = _git(repo, "diff", "--cached", "--name-only")
    if staged.returncode != 0:
        raise RuntimeError(staged.stderr.strip() or "git diff --cached failed")
    paths.update(_norm(line) for line in staged.stdout.splitlines() if line.strip())

    if command_requests_all_tracked(command):
        tracked = _git(repo, "diff", "--name-only")
        if tracked.returncode != 0:
            raise RuntimeError(tracked.stderr.strip() or "git diff --name-only failed")
        paths.update(_norm(line) for line in tracked.stdout.splitlines() if line.strip())

    # Best-effort support for `git commit path/to/file`: Git can commit a
    # tracked pathspec without it appearing in the index before the command.
    for target in TARGET_PATHS:
        if target in _norm(command):
            paths.add(target)

    return paths


def target_paths_touched(paths: set[str]) -> set[str]:
    return TARGET_PATHS.intersection(paths)


def run_smoke(repo: Path, smoke_command: list[str]) -> int:
    proc = subprocess.run(smoke_command, cwd=repo)
    return proc.returncode


def should_run_for_command(repo: Path, command: str) -> tuple[bool, set[str]]:
    if not is_git_commit_command(command):
        return False, set()
    touched = target_paths_touched(changed_paths_for_pending_commit(repo, command))
    return bool(touched), touched


def run_hook(
    *,
    repo: Path,
    command: str,
    smoke_command: list[str],
    dry_run: bool = False,
) -> int:
    should_run, touched = should_run_for_command(repo, command)
    if not should_run:
        print("damage precommit: skip (not a git commit touching damage-chain asm)")
        return 0

    print("damage precommit: running clobber_smoke before commit")
    for path in sorted(touched):
        print(f"  touched: {path}")
    if dry_run:
        print("damage precommit: dry run, smoke command not executed")
        return 0
    rc = run_smoke(repo, smoke_command)
    if rc == 0:
        print("damage precommit: clobber_smoke PASS")
    else:
        print(f"damage precommit: clobber_smoke FAIL (exit {rc})", file=sys.stderr)
    return rc


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="damage-precommit-") as tmp:
        repo = Path(tmp)
        subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "damage precommit test"], cwd=repo, check=True)

        _write(repo / "README.md", "base\n")
        for target in TARGET_PATHS:
            _write(repo / target, "base\n")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "base"], cwd=repo, check=True, stdout=subprocess.DEVNULL)

        calls_file = repo / "smoke_calls.txt"
        smoke_ok = [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                f"Path({str(calls_file)!r}).write_text('ran', encoding='utf-8')"
            ),
        ]
        smoke_fail = [sys.executable, "-c", "raise SystemExit(7)"]

        assert run_hook(
            repo=repo,
            command="git status",
            smoke_command=smoke_ok,
        ) == 0
        assert not calls_file.exists(), "non-commit command ran smoke"

        _write(repo / "README.md", "changed\n")
        subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
        assert run_hook(
            repo=repo,
            command='git commit -m "docs"',
            smoke_command=smoke_ok,
        ) == 0
        assert not calls_file.exists(), "untouched target path ran smoke"
        subprocess.run(["git", "commit", "-m", "docs"], cwd=repo, check=True, stdout=subprocess.DEVNULL)

        _write(repo / "engine/battle/effect_commands.asm", "all tracked\n")
        assert run_hook(
            repo=repo,
            command='git commit -am "damage all tracked"',
            smoke_command=smoke_ok,
        ) == 0
        assert calls_file.read_text(encoding="utf-8") == "ran", "git commit -am target did not run smoke"
        calls_file.unlink()

        _write(repo / "engine/battle/late_gen_held_items.asm", "changed\n")
        subprocess.run(["git", "add", "engine/battle/late_gen_held_items.asm"], cwd=repo, check=True)
        assert run_hook(
            repo=repo,
            command='git commit -m "damage"',
            smoke_command=smoke_ok,
        ) == 0
        assert calls_file.read_text(encoding="utf-8") == "ran", "touched target did not run smoke"

        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            failed_rc = run_hook(
                repo=repo,
                command='git commit -m "damage"',
                smoke_command=smoke_fail,
            )
        assert failed_rc == 7, "touched target smoke failure did not propagate"
        print("damage precommit: expected smoke failure propagated")

    print("damage precommit: self-test PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Claude git-commit clobber_smoke gate")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--command", default=None, help="Command to inspect; defaults to Claude hook stdin")
    parser.add_argument("--smoke-command", nargs=argparse.REMAINDER, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    stdin_text = ""
    if not sys.stdin.isatty():
        stdin_text = sys.stdin.read()
    command = extract_command_from_event(stdin_text, args.command)
    smoke_command = args.smoke_command if args.smoke_command else DEFAULT_SMOKE_COMMAND
    return run_hook(
        repo=args.repo.resolve(),
        command=command,
        smoke_command=smoke_command,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
