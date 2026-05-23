from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "install_debugger_hooks.py"


def _load_installer():
    spec = importlib.util.spec_from_file_location("install_debugger_hooks", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(
    *args: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*args],
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    proc = _run("git", *args, cwd=repo, env=env)
    if proc.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout


def _init_repo(repo: Path) -> None:
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "debugger-hooks-test@example.invalid")
    _git(repo, "config", "user.name", "Debugger Hooks Test")
    (repo / "file.txt").write_text("one\n", encoding="utf-8")
    _git(repo, "add", "file.txt")
    _git(repo, "commit", "-m", "initial")


def _hook_path(repo: Path) -> Path:
    return repo / ".git" / "hooks" / "post-commit"


class InstallDebuggerHooksTests(unittest.TestCase):
    def test_dry_run_install_reports_target_without_writing(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)

            proc = _run(
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(repo),
                "--dry-run",
                "--install",
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("would create post-commit", proc.stdout)
            self.assertFalse(_hook_path(repo).exists())

    def test_auto_watch_post_commit_hook_install_uninstall_round_trip(self) -> None:
        installer = _load_installer()
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)

            install = installer.install_hook(repo)
            hook = Path(install["hook_path"])

            self.assertTrue(hook.exists())
            self.assertIn(installer.HOOK_BEGIN, hook.read_text(encoding="utf-8"))

            uninstall = installer.uninstall_hook(repo)

            self.assertEqual(uninstall["action"], "remove-file")
            self.assertFalse(hook.exists())

    def test_install_debugger_hooks_preserves_existing_hook_on_uninstall(self) -> None:
        installer = _load_installer()
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            hook = _hook_path(repo)
            hook.write_text("#!/bin/sh\necho existing\n", encoding="utf-8")

            installer.install_hook(repo)
            installer.uninstall_hook(repo)

            self.assertEqual(hook.read_text(encoding="utf-8"), "#!/bin/sh\necho existing\n")

    def test_install_debugger_hooks_hook_exits_zero_when_auto_watch_missing(self) -> None:
        installer = _load_installer()
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            package = repo / "tools" / "debugger"
            package.mkdir(parents=True)
            (repo / "tools" / "__init__.py").write_text("", encoding="utf-8")
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "__main__.py").write_text(
                "from . import auto_watch\nraise SystemExit(auto_watch.main())\n",
                encoding="utf-8",
            )
            _git(repo, "add", "tools")
            _git(repo, "commit", "-m", "add debugger package without auto-watch")
            installer.install_hook(repo)

            (repo / "file.txt").write_text("two\n", encoding="utf-8")
            _git(repo, "add", "file.txt")
            env = {**os.environ, "PYTHON": sys.executable}
            proc = _run(
                "git",
                "commit",
                "-m",
                "trigger missing auto-watch",
                cwd=repo,
                env=env,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertNotIn("ImportError", proc.stderr)
            findings = repo / "audit" / "auto_watch_findings.jsonl"
            rows = [
                json.loads(line)
                for line in findings.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(rows[-1]["status"], "watcher_unavailable")
            self.assertEqual(rows[-1]["trigger"], "commit")
            self.assertEqual(
                rows[-1]["commit_hash"], _git(repo, "rev-parse", "HEAD").strip()
            )
            self.assertEqual(rows[-1]["trigger_id"], rows[-1]["commit_hash"])
            self.assertEqual(rows[-1]["bug_class"], "watcher_unavailable")
            self.assertEqual(rows[-1]["detector"], "post_commit_hook")
            self.assertEqual(rows[-1]["evidence"]["exit_code"], 1)
            self.assertEqual(rows[-1]["evidence_atoms"][0]["exit_code"], 1)
            self.assertIn("auto-watch", rows[-1]["command_replay"])


if __name__ == "__main__":
    unittest.main()
