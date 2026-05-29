#!/usr/bin/env python3
"""Install local git hooks for the unified debugger."""

from __future__ import annotations

import argparse
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
HOOK_BEGIN = "# BEGIN pokemon-gold-debugger-auto-watch"
HOOK_END = "# END pokemon-gold-debugger-auto-watch"
HOOK_NAME = "post-commit"


class HookInstallError(RuntimeError):
    pass


def managed_hook_block() -> str:
    return f"""\
{HOOK_BEGIN}
# Detect-and-report only. This hook must never block commits.
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -n "$REPO_ROOT" ]; then
    COMMIT_HASH=$(git rev-parse HEAD 2>/dev/null)
    PYTHON_BIN="${{PYTHON:-python}}"
    cd "$REPO_ROOT" 2>/dev/null || exit 0
    AUTO_WATCH_OUTPUT=$("$PYTHON_BIN" -m tools.debugger auto-watch --on commit --commit-hash "$COMMIT_HASH" 2>&1)
    AUTO_WATCH_STATUS=$?
    if [ "$AUTO_WATCH_STATUS" -ne 0 ]; then
        AUTO_WATCH_OUTPUT="$AUTO_WATCH_OUTPUT" "$PYTHON_BIN" - "$REPO_ROOT" "$COMMIT_HASH" "$AUTO_WATCH_STATUS" <<'PY' >/dev/null 2>&1 || true
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1])
commit_hash = sys.argv[2]
exit_code = int(sys.argv[3])
command = "python -m tools.debugger auto-watch --on commit --commit-hash " + commit_hash
output = os.environ.get("AUTO_WATCH_OUTPUT", "")
row = {{
    "schema_version": 1,
    "kind": "auto_watch_finding",
    "status": "watcher_unavailable",
    "trigger": "commit",
    "trigger_id": commit_hash,
    "commit_hash": commit_hash,
    "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "bug_class": "watcher_unavailable",
    "detector": "post_commit_hook",
    "severity": "low",
    "evidence": {{
        "command": command,
        "exit_code": exit_code,
        "summary": output[-2000:],
    }},
    "evidence_atoms": [
        {{
            "kind": "command_exit",
            "command": command,
            "exit_code": exit_code,
            "stderr_tail": output[-2000:],
        }}
    ],
    "command_replay": command,
    "llm_next_step": "Repair or finish tools.debugger auto-watch; post-commit hook is detect-and-report and exited 0.",
}}
target = root / "audit" / "auto_watch_findings.jsonl"
target.parent.mkdir(parents=True, exist_ok=True)
with target.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(row, separators=(",", ":")) + "\\n")
PY
    fi
fi
exit 0
{HOOK_END}
"""


def resolve_hook_path(repo_root: Path) -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--git-path", f"hooks/{HOOK_NAME}"],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise HookInstallError(
            f"cannot resolve git hook path for {repo_root}: {proc.stderr.strip() or proc.stdout.strip()}"
        )
    hook_path = Path(proc.stdout.strip())
    if not hook_path.is_absolute():
        hook_path = repo_root / hook_path
    return hook_path


def hook_has_managed_block(text: str) -> bool:
    return HOOK_BEGIN in text and HOOK_END in text


def install_text(existing: str) -> str:
    block = managed_hook_block().rstrip() + "\n"
    if hook_has_managed_block(existing):
        return _replace_managed_block(existing, block)
    prefix = existing
    if not prefix:
        prefix = "#!/bin/sh\n"
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    if prefix.strip():
        prefix += "\n"
    return prefix + block


def uninstall_text(existing: str) -> str:
    if not hook_has_managed_block(existing):
        return existing
    updated = _replace_managed_block(existing, "")
    if _is_empty_hook(updated):
        return ""
    return updated if updated.endswith("\n") else updated + "\n"


def install_hook(repo_root: Path = ROOT, *, dry_run: bool = False) -> dict[str, str | bool]:
    hook_path = resolve_hook_path(repo_root)
    existing = hook_path.read_text(encoding="utf-8") if hook_path.exists() else ""
    updated = install_text(existing)
    action = (
        "replace"
        if hook_has_managed_block(existing)
        else "create"
        if not existing
        else "append"
    )
    if not dry_run:
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text(updated, encoding="utf-8", newline="\n")
        _make_executable(hook_path)
    return {
        "action": action,
        "dry_run": dry_run,
        "hook_path": str(hook_path),
        "changed": updated != existing,
    }


def uninstall_hook(repo_root: Path = ROOT, *, dry_run: bool = False) -> dict[str, str | bool]:
    hook_path = resolve_hook_path(repo_root)
    existing = hook_path.read_text(encoding="utf-8") if hook_path.exists() else ""
    if not hook_has_managed_block(existing):
        return {
            "action": "noop",
            "dry_run": dry_run,
            "hook_path": str(hook_path),
            "changed": False,
        }
    updated = uninstall_text(existing)
    action = "remove-file" if not updated.strip() else "remove-block"
    if not dry_run:
        if action == "remove-file":
            hook_path.unlink()
        else:
            hook_path.write_text(updated, encoding="utf-8", newline="\n")
            _make_executable(hook_path)
    return {
        "action": action,
        "dry_run": dry_run,
        "hook_path": str(hook_path),
        "changed": True,
    }


def _replace_managed_block(existing: str, replacement: str) -> str:
    pattern = re.compile(
        rf"\n?{re.escape(HOOK_BEGIN)}.*?{re.escape(HOOK_END)}\n?",
        re.DOTALL,
    )
    updated = pattern.sub(("\n" + replacement) if replacement else "\n", existing)
    return updated.strip() + ("\n" if replacement else "")


def _is_empty_hook(text: str) -> bool:
    meaningful = [
        line
        for line in text.splitlines()
        if line.strip() and not line.startswith("#!")
    ]
    return not meaningful


def _make_executable(path: Path) -> None:
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        # Windows git can still run shebang hooks without a meaningful chmod bit.
        pass


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/install_debugger_hooks.py",
        description="Install or uninstall local debugger git hooks.",
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--install", action="store_true", help=f"install the {HOOK_NAME} hook"
    )
    action.add_argument(
        "--uninstall",
        action="store_true",
        help=f"remove the managed {HOOK_NAME} hook block",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print the planned action without writing"
    )
    parser.add_argument(
        "--repo-root",
        default=str(ROOT),
        help="repo root to modify; defaults to this checkout",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    try:
        result = (
            install_hook(repo_root, dry_run=args.dry_run)
            if args.install
            else uninstall_hook(repo_root, dry_run=args.dry_run)
        )
    except HookInstallError as exc:
        print(f"install_debugger_hooks: {exc}", file=sys.stderr)
        return 1

    prefix = "would " if args.dry_run else ""
    print(f"{prefix}{result['action']} {HOOK_NAME}: {result['hook_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
