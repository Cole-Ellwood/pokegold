from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Sequence

from .handoff_log import (
    DEFAULT_STORE,
    ROOT,
    HandoffRow,
    is_mutual_verified,
    load_rows,
)
from .workflow import command_is_runnable, execute_step


PASS = "pass"
FAIL = "fail"

RELEASE_SMOKE_GATE_NAME = "release_smoke"
SAVE_FORMAT_GATE_NAME = "save_format_version"
RELEASE_SMOKE_COMMAND = "python tools/audit/check_release_smoke.py"
SAVE_FORMAT_COMMAND = "python tools/audit/check_save_format_version.py"
DEFAULT_VERIFY_COMMANDS = (RELEASE_SMOKE_COMMAND,)
DEFAULT_BUILD_COMMAND = (
    "bash -lc \"make -j4 PYTHON=python3 "
    "RGBASM=rgbds-1.0.1/rgbasm.exe "
    "RGBLINK=rgbds-1.0.1/rgblink.exe "
    "RGBFIX=rgbds-1.0.1/rgbfix.exe "
    "RGBGFX=rgbds-1.0.1/rgbgfx.exe "
    "pokegold.gbc pokesilver.gbc\""
)
ROM_EDIT_WORKTREE_DIR = Path(".local") / "tmp" / "rom_edit_worktrees"
PROTECTED_BRANCHES = frozenset(
    {
        "main",
        "master",
        "origin/main",
        "origin/master",
        "refs/heads/main",
        "refs/heads/master",
    }
)


@dataclass(frozen=True)
class GateSpec:
    name: str
    command: str

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "command": self.command}


@dataclass(frozen=True)
class GateResult:
    name: str
    status: str
    command: str = ""
    detail: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "status": self.status,
            "command": self.command,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class RomEditWorktree:
    path: str
    branch: str
    slug: str
    base_head: str

    def as_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "branch": self.branch,
            "slug": self.slug,
            "base_head": self.base_head,
        }


class RomEditWorktreeError(RuntimeError):
    pass


def touches_ram(changed_files: Sequence[str]) -> bool:
    return any(_normalize_repo_path(path).startswith("ram/") for path in changed_files)


def required_green_gate_stack(changed_files: Sequence[str]) -> tuple[GateSpec, ...]:
    gates = [GateSpec(RELEASE_SMOKE_GATE_NAME, RELEASE_SMOKE_COMMAND)]
    if touches_ram(changed_files):
        gates.insert(0, GateSpec(SAVE_FORMAT_GATE_NAME, SAVE_FORMAT_COMMAND))
    return tuple(gates)


def decide_auto_apply(
    *,
    changed_files: Sequence[str],
    gate_results: Sequence[GateResult | Mapping[str, Any]],
    handoff_phase: str,
    handoff_rows: Sequence[dict[str, Any]] | None = None,
    handoff_store: Path = DEFAULT_STORE,
    root: Path = ROOT,
    target_branch: str = "",
    merge_target: str = "",
    push_remote: bool = False,
) -> dict[str, Any]:
    """Return the P12 full-autonomy auto-apply decision without applying edits."""

    normalized_results = tuple(_normalize_gate_result(result) for result in gate_results)
    required_gates = required_green_gate_stack(changed_files)
    blocking_reasons = _gate_blocking_reasons(required_gates, normalized_results)

    if push_remote:
        blocking_reasons.append("auto-apply refuses remote push")
    if not target_branch.strip():
        blocking_reasons.append("auto-apply requires explicit target branch")
    if _is_protected_branch(target_branch):
        blocking_reasons.append(
            f"auto-apply refuses protected target branch {target_branch!r}"
        )
    if _is_protected_branch(merge_target):
        blocking_reasons.append(
            f"auto-apply refuses auto-merge to protected branch {merge_target!r}"
        )

    rows = (
        list(handoff_rows)
        if handoff_rows is not None
        else load_rows(_resolve_store(handoff_store, root))
    )
    handoff_mutual_verified, handoff_reasons = is_mutual_verified(rows, handoff_phase)
    if not handoff_mutual_verified:
        blocking_reasons.append(
            "handoff phase is not mutual-verified: " + "; ".join(handoff_reasons)
        )

    return {
        "kind": "rom_edit_auto_apply_decision",
        "allowed": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
        "changed_files": tuple(changed_files),
        "required_gates": tuple(gate.as_dict() for gate in required_gates),
        "gate_results": tuple(result.as_dict() for result in normalized_results),
        "handoff_phase": handoff_phase,
        "handoff_mutual_verified": handoff_mutual_verified,
        "handoff_reasons": tuple(handoff_reasons),
        "target_branch": target_branch,
        "merge_target": merge_target,
        "push_remote": push_remote,
        "requires_mutual_verified": True,
    }


def default_worktree_base(root: Path = ROOT) -> Path:
    return root / ROM_EDIT_WORKTREE_DIR


def create_rom_edit_worktree(
    *,
    root: Path = ROOT,
    base_dir: Path | None = None,
    changed_files: Sequence[str] = (),
    slug: str = "",
    branch_prefix: str = "rom-edit",
) -> RomEditWorktree:
    repo_root = root.resolve()
    target_base = _resolve_worktree_base(repo_root, base_dir)
    target_base.mkdir(parents=True, exist_ok=True)
    base_head = _git_stdout(["rev-parse", "HEAD"], cwd=repo_root)
    final_slug = slug or _make_worktree_slug(base_head, changed_files)
    worktree_path = (target_base / final_slug).resolve()
    if worktree_path.exists():
        raise RomEditWorktreeError(f"worktree path already exists: {worktree_path}")
    branch = f"{branch_prefix}/{final_slug}"
    _git_stdout(
        ["worktree", "add", "-b", branch, str(worktree_path), base_head],
        cwd=repo_root,
    )
    return RomEditWorktree(
        path=str(worktree_path),
        branch=branch,
        slug=final_slug,
        base_head=base_head,
    )


def remove_rom_edit_worktree(
    worktree_path: str | Path,
    *,
    root: Path = ROOT,
    base_dir: Path | None = None,
    force: bool = True,
) -> dict[str, str]:
    repo_root = root.resolve()
    target_base = _resolve_worktree_base(repo_root, base_dir)
    target = Path(worktree_path).resolve()
    if not _is_relative_to(target, target_base):
        raise RomEditWorktreeError(
            f"refusing to remove worktree outside rom-edit base: {target}"
        )
    branch = _git_stdout(["branch", "--show-current"], cwd=target)
    args = ["worktree", "remove"]
    if force:
        args.append("--force")
    args.append(str(target))
    _git_stdout(args, cwd=repo_root)
    removed_branch = ""
    if branch.startswith("rom-edit/"):
        _git_stdout(["branch", "-D", branch], cwd=repo_root)
        removed_branch = branch
    return {"removed": str(target), "removed_branch": removed_branch}


def apply_unified_patch_to_worktree(
    worktree_path: str | Path,
    patch_text: str,
    *,
    root: Path = ROOT,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    repo_root = root.resolve()
    target_base = _resolve_worktree_base(repo_root, base_dir)
    target = Path(worktree_path).resolve()
    if not _is_relative_to(target, target_base):
        raise RomEditWorktreeError(
            f"refusing to patch worktree outside rom-edit base: {target}"
        )
    if not patch_text.strip():
        raise RomEditWorktreeError("refusing to apply an empty patch")
    _git_stdout(["apply", "--check", "-"], cwd=target, input_text=patch_text)
    _git_stdout(["apply", "-"], cwd=target, input_text=patch_text)
    changed_files = tuple(
        line
        for line in _git_stdout(["diff", "--name-only"], cwd=target).splitlines()
        if line
    )
    return {
        "patch_applied": True,
        "worktree_path": str(target),
        "changed_files": changed_files,
        "diff": _git_stdout(["diff", "--"], cwd=target, strip_output=False),
    }


def propose_rom_edit(
    *,
    file_path: str,
    patch_text: str,
    root: Path = ROOT,
    slug: str = "",
) -> dict[str, Any]:
    normalized_file = _normalize_repo_path(file_path)
    worktree = create_rom_edit_worktree(
        root=root,
        changed_files=(normalized_file,),
        slug=slug,
    )
    try:
        applied = apply_unified_patch_to_worktree(
            worktree.path,
            patch_text,
            root=root,
        )
        if tuple(applied["changed_files"]) != (normalized_file,):
            raise RomEditWorktreeError(
                "patch changed files do not match declared --file: "
                f"declared={normalized_file!r} observed={applied['changed_files']!r}"
            )
    except Exception:
        remove_rom_edit_worktree(worktree.path, root=root)
        raise
    return {
        "kind": "rom_edit_proposal",
        "status": "proposed",
        "declared_file": normalized_file,
        "worktree": worktree.as_dict(),
        "changed_files": applied["changed_files"],
        "diff": applied["diff"],
    }


def verify_rom_edit_worktree(
    worktree_path: str | Path,
    *,
    commands: Sequence[str] = DEFAULT_VERIFY_COMMANDS,
    root: Path = ROOT,
    base_dir: Path | None = None,
    timeout_seconds: int = 600,
) -> dict[str, Any]:
    repo_root = root.resolve()
    target_base = _resolve_worktree_base(repo_root, base_dir)
    target = Path(worktree_path).resolve()
    if not _is_relative_to(target, target_base):
        raise RomEditWorktreeError(
            f"refusing to verify worktree outside rom-edit base: {target}"
        )
    steps = []
    for index, command in enumerate(commands, start=1):
        step = {
            "id": f"verify:{index}",
            "command": command,
            "runnable": command_is_runnable(command),
            "status": "pending",
            "returncode": None,
            "elapsed_seconds": 0.0,
            "stdout_tail": [],
            "stderr_tail": [],
        }
        execute_step(step, root=target, timeout_seconds=timeout_seconds)
        steps.append(step)
    failed = [step for step in steps if step["status"] != "passed"]
    return {
        "kind": "rom_edit_verify_report",
        "worktree_path": str(target),
        "status": "failed" if failed else "passed",
        "passed": not failed,
        "step_count": len(steps),
        "failed_count": len(failed),
        "steps": steps,
    }


def build_rom_edit_worktree(
    worktree_path: str | Path,
    *,
    command: str = DEFAULT_BUILD_COMMAND,
    root: Path = ROOT,
    base_dir: Path | None = None,
    timeout_seconds: int = 900,
) -> dict[str, Any]:
    report = verify_rom_edit_worktree(
        worktree_path,
        commands=(command,),
        root=root,
        base_dir=base_dir,
        timeout_seconds=timeout_seconds,
    )
    report["kind"] = "rom_edit_build_report"
    report["build_command"] = command
    return report


def apply_rom_edit_to_main(
    worktree_path: str | Path,
    *,
    changed_files: Sequence[str],
    gate_results: Sequence[GateResult | Mapping[str, Any]],
    handoff_phase: str,
    target_branch: str,
    root: Path = ROOT,
    base_dir: Path | None = None,
    handoff_rows: Sequence[dict[str, Any]] | None = None,
    handoff_store: Path = DEFAULT_STORE,
    merge_target: str = "",
    push_remote: bool = False,
) -> dict[str, Any]:
    repo_root = root.resolve()
    target_base = _resolve_worktree_base(repo_root, base_dir)
    target = Path(worktree_path).resolve()
    if not _is_relative_to(target, target_base):
        raise RomEditWorktreeError(
            f"refusing to apply worktree outside rom-edit base: {target}"
        )
    decision = decide_auto_apply(
        changed_files=tuple(changed_files),
        gate_results=tuple(gate_results),
        handoff_phase=handoff_phase,
        handoff_rows=handoff_rows,
        handoff_store=handoff_store,
        root=repo_root,
        target_branch=target_branch,
        merge_target=merge_target,
        push_remote=push_remote,
    )
    blocking_reasons = list(decision["blocking_reasons"])
    current_branch = _git_stdout(["branch", "--show-current"], cwd=repo_root)
    if current_branch != target_branch:
        blocking_reasons.append(
            f"target branch mismatch: current={current_branch!r} target={target_branch!r}"
        )
    tracked_dirty = _git_stdout(
        ["status", "--porcelain", "--untracked-files=no"],
        cwd=repo_root,
    )
    if tracked_dirty:
        blocking_reasons.append("target checkout has tracked dirty changes")
    diff = _git_stdout(["diff", "--binary", "--"], cwd=target, strip_output=False)
    if not diff.strip():
        blocking_reasons.append("rom-edit worktree has no diff to apply")

    if blocking_reasons:
        return {
            "kind": "rom_edit_apply_to_main_report",
            "status": "refused",
            "applied": False,
            "worktree_path": str(target),
            "changed_files": tuple(changed_files),
            "target_branch": target_branch,
            "current_branch": current_branch,
            "blocking_reasons": tuple(blocking_reasons),
            "decision": decision,
        }

    _git_stdout(["apply", "--check", "-"], cwd=repo_root, input_text=diff)
    _git_stdout(["apply", "-"], cwd=repo_root, input_text=diff)
    return {
        "kind": "rom_edit_apply_to_main_report",
        "status": "applied",
        "applied": True,
        "worktree_path": str(target),
        "changed_files": tuple(changed_files),
        "target_branch": target_branch,
        "current_branch": current_branch,
        "blocking_reasons": (),
        "decision": decision,
    }


def run_self_test() -> dict[str, Any]:
    """Exercise the rom-edit propose/verify/apply loop in a temp git repo."""

    phase = "P12_rom_edit_selftest_candidate"
    with TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        _git_stdout(["init", "--quiet"], cwd=repo)
        _git_stdout(
            ["config", "user.email", "rom-edit-selftest@example.invalid"],
            cwd=repo,
        )
        _git_stdout(["config", "user.name", "Rom Edit Selftest"], cwd=repo)
        (repo / "file.txt").write_text("one\n", encoding="utf-8")
        _git_stdout(["add", "file.txt"], cwd=repo)
        _git_stdout(["commit", "-m", "initial", "--quiet"], cwd=repo)
        _git_stdout(["checkout", "-b", "feature", "--quiet"], cwd=repo)

        proposal = propose_rom_edit(
            file_path="file.txt",
            patch_text=_selftest_patch("two"),
            root=repo,
            slug="selftest",
        )
        worktree_path = proposal["worktree"]["path"]
        try:
            verify_report = verify_rom_edit_worktree(
                worktree_path,
                commands=(
                    "python -c \"from pathlib import Path; "
                    "raise SystemExit(0 if Path('file.txt').read_text(encoding='utf-8') == 'two\\n' else 1)\"",
                ),
                root=repo,
                timeout_seconds=30,
            )
            if verify_report["passed"]:
                apply_report = apply_rom_edit_to_main(
                    worktree_path,
                    changed_files=("file.txt",),
                    gate_results=(
                        GateResult(name=RELEASE_SMOKE_GATE_NAME, status=PASS),
                    ),
                    handoff_phase=phase,
                    handoff_rows=_selftest_handoff_rows(phase),
                    root=repo,
                    target_branch="feature",
                )
            else:
                apply_report = {"status": "skipped", "applied": False}
            root_text = (repo / "file.txt").read_text(encoding="utf-8")
        finally:
            remove_rom_edit_worktree(worktree_path, root=repo)

        return {
            "kind": "rom_edit_self_test",
            "passed": (
                proposal["status"] == "proposed"
                and verify_report["passed"]
                and apply_report["applied"]
                and root_text == "two\n"
            ),
            "proposal_status": proposal["status"],
            "verify_status": verify_report["status"],
            "apply_status": apply_report["status"],
            "changed_files": proposal["changed_files"],
        }


def format_decision(decision: Mapping[str, Any]) -> str:
    status = "ALLOWED" if decision.get("allowed") else "REFUSED"
    lines = [f"rom-edit auto-apply: {status}"]
    lines.append(f"handoff_phase: {decision.get('handoff_phase')}")
    lines.append(
        f"handoff_mutual_verified: {decision.get('handoff_mutual_verified')}"
    )
    lines.append(f"target_branch: {decision.get('target_branch')}")
    if decision.get("merge_target"):
        lines.append(f"merge_target: {decision.get('merge_target')}")
    if decision.get("push_remote"):
        lines.append("push_remote: True")
    blocking = decision.get("blocking_reasons") or ()
    if blocking:
        lines.append("blocking_reasons:")
        for reason in blocking:
            lines.append(f"  - {reason}")
    else:
        lines.append("blocking_reasons: none")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "self_test", False):
        return cmd_self_test(args)
    if not hasattr(args, "func"):
        parser.error("the following arguments are required: command")
    try:
        return int(args.func(args))
    except RomEditWorktreeError as exc:
        print(f"rom-edit: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger rom-edit",
        description="ROM edit proposal/apply safety tooling.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run a temp-repo propose/verify/apply-to-main smoke test",
    )
    sub = parser.add_subparsers(dest="command")

    gate = sub.add_parser(
        "gate",
        help="Evaluate the non-destructive P12 auto-apply gate decision.",
    )
    gate.add_argument(
        "--changed-file",
        action="append",
        dest="changed_files",
        required=True,
        help="Repo-relative path changed by the rom-edit candidate.",
    )
    gate.add_argument(
        "--gate",
        action="append",
        default=[],
        type=_parse_gate_arg,
        metavar="NAME=STATUS",
        help="Observed green-gate result, for example release_smoke=pass.",
    )
    gate.add_argument("--handoff-phase", required=True)
    gate.add_argument("--handoff-store", default="")
    gate.add_argument("--target-branch", required=True)
    gate.add_argument("--merge-target", default="")
    gate.add_argument("--push-remote", action="store_true")
    gate.add_argument("--json", action="store_true")
    gate.set_defaults(func=cmd_gate)

    propose = sub.add_parser(
        "propose",
        help="Create a rom-edit worktree and apply a unified patch.",
    )
    propose.add_argument("--file", required=True, dest="file_path")
    propose.add_argument("--change", default="", help="Unified diff text to apply.")
    propose.add_argument(
        "--patch-file",
        default="",
        help="Path to a file containing unified diff text.",
    )
    propose.add_argument("--root", default=str(ROOT))
    propose.add_argument("--slug", default="")
    propose.add_argument("--json", action="store_true")
    propose.set_defaults(func=cmd_propose)

    verify = sub.add_parser(
        "verify",
        help="Run verification commands inside a rom-edit worktree.",
    )
    verify.add_argument("--worktree-path", required=True)
    verify.add_argument(
        "--command",
        action="append",
        dest="commands",
        default=[],
        help="Command to execute inside the worktree. Repeat for multiple commands.",
    )
    verify.add_argument("--root", default=str(ROOT))
    verify.add_argument("--timeout-seconds", type=int, default=600)
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(func=cmd_verify)

    build = sub.add_parser(
        "build",
        help="Run the ROM build command inside a rom-edit worktree.",
    )
    build.add_argument("--worktree-path", required=True)
    build.add_argument("--command", default=DEFAULT_BUILD_COMMAND)
    build.add_argument("--root", default=str(ROOT))
    build.add_argument("--timeout-seconds", type=int, default=900)
    build.add_argument("--json", action="store_true")
    build.set_defaults(func=cmd_build)

    apply = sub.add_parser(
        "apply-to-main",
        help="Apply a verified rom-edit worktree diff back to the target checkout.",
    )
    apply.add_argument("--worktree-path", required=True)
    apply.add_argument(
        "--changed-file",
        action="append",
        dest="changed_files",
        required=True,
        help="Repo-relative file expected in the worktree diff.",
    )
    apply.add_argument(
        "--gate",
        action="append",
        default=[],
        type=_parse_gate_arg,
        metavar="NAME=STATUS",
        help="Observed green-gate result, for example release_smoke=pass.",
    )
    apply.add_argument("--handoff-phase", required=True)
    apply.add_argument("--handoff-store", default="")
    apply.add_argument("--root", default=str(ROOT))
    apply.add_argument("--target-branch", required=True)
    apply.add_argument("--merge-target", default="")
    apply.add_argument("--push-remote", action="store_true")
    apply.add_argument("--json", action="store_true")
    apply.set_defaults(func=cmd_apply_to_main)
    return parser


def cmd_gate(args: argparse.Namespace) -> int:
    decision = decide_auto_apply(
        changed_files=tuple(args.changed_files),
        gate_results=tuple(args.gate),
        handoff_phase=args.handoff_phase,
        handoff_store=Path(args.handoff_store) if args.handoff_store else DEFAULT_STORE,
        target_branch=args.target_branch,
        merge_target=args.merge_target,
        push_remote=args.push_remote,
    )
    if args.json:
        print(json.dumps(decision, indent=2))
    else:
        print(format_decision(decision))
    return 0 if decision["allowed"] else 1


def cmd_self_test(args: argparse.Namespace) -> int:
    report = run_self_test()
    status = "passed" if report["passed"] else "failed"
    print(f"rom-edit self-test: {status}")
    return 0 if report["passed"] else 1


def cmd_propose(args: argparse.Namespace) -> int:
    patch_text = _patch_text_from_args(args.change, args.patch_file)
    proposal = propose_rom_edit(
        file_path=args.file_path,
        patch_text=patch_text,
        root=Path(args.root),
        slug=args.slug,
    )
    if args.json:
        print(json.dumps(proposal, indent=2))
    else:
        print(f"rom-edit proposal: {proposal['status']}")
        print(f"worktree: {proposal['worktree']['path']}")
        print(f"changed_files: {', '.join(proposal['changed_files'])}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    report = verify_rom_edit_worktree(
        args.worktree_path,
        commands=tuple(args.commands) or DEFAULT_VERIFY_COMMANDS,
        root=Path(args.root),
        timeout_seconds=args.timeout_seconds,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"rom-edit verify: {report['status']}")
        for step in report["steps"]:
            print(f"  {step['status']}: {step['command']}")
            if step.get("failure_summary"):
                print(f"    {step['failure_summary']}")
    return 0 if report["passed"] else 1


def cmd_build(args: argparse.Namespace) -> int:
    report = build_rom_edit_worktree(
        args.worktree_path,
        command=args.command,
        root=Path(args.root),
        timeout_seconds=args.timeout_seconds,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"rom-edit build: {report['status']}")
        for step in report["steps"]:
            print(f"  {step['status']}: {step['command']}")
            if step.get("failure_summary"):
                print(f"    {step['failure_summary']}")
    return 0 if report["passed"] else 1


def cmd_apply_to_main(args: argparse.Namespace) -> int:
    report = apply_rom_edit_to_main(
        args.worktree_path,
        changed_files=tuple(args.changed_files),
        gate_results=tuple(args.gate),
        handoff_phase=args.handoff_phase,
        handoff_store=Path(args.handoff_store) if args.handoff_store else DEFAULT_STORE,
        root=Path(args.root),
        target_branch=args.target_branch,
        merge_target=args.merge_target,
        push_remote=args.push_remote,
    )
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"rom-edit apply-to-main: {report['status']}")
        for reason in report["blocking_reasons"]:
            print(f"  - {reason}")
    return 0 if report["applied"] else 1


def _parse_gate_arg(text: str) -> GateResult:
    if "=" not in text:
        raise argparse.ArgumentTypeError("gate result must be NAME=STATUS")
    name, status = text.split("=", 1)
    if not name or not status:
        raise argparse.ArgumentTypeError("gate result must be NAME=STATUS")
    return GateResult(name=name, status=status)


def _patch_text_from_args(change: str, patch_file: str) -> str:
    if bool(change) == bool(patch_file):
        raise RomEditWorktreeError("provide exactly one of --change or --patch-file")
    if patch_file:
        return Path(patch_file).read_text(encoding="utf-8")
    return change


def _selftest_patch(new_text: str) -> str:
    return (
        "diff --git a/file.txt b/file.txt\n"
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1 +1 @@\n"
        "-one\n"
        f"+{new_text}\n"
    )


def _selftest_handoff_rows(phase: str) -> list[dict[str, Any]]:
    rows = (
        HandoffRow(
            phase=phase,
            event="ack_start",
            status="in_progress",
            model="codex",
            primary="codex",
            confidence="repo-proven",
            claim="rom-edit selftest candidate started.",
        ),
        HandoffRow(
            phase=phase,
            event="slice_update",
            status="ready_for_review",
            model="codex",
            primary="codex",
            confidence="repo-proven",
            claim="rom-edit selftest candidate ready for review.",
        ),
        HandoffRow(
            phase=phase,
            event="slice_review",
            status="slice_accepted",
            model="claude",
            primary="codex",
            reviewer="claude",
            confidence="repo-proven",
            claim="rom-edit selftest candidate accepted.",
        ),
    )
    return [{**row.as_dict(), "_line": index + 1} for index, row in enumerate(rows)]


def _gate_blocking_reasons(
    required_gates: Sequence[GateSpec],
    gate_results: Sequence[GateResult],
) -> list[str]:
    reasons: list[str] = []
    result_by_name = {result.name: result for result in gate_results}
    for gate in required_gates:
        result = result_by_name.get(gate.name)
        if result is None:
            reasons.append(
                f"required green-gate audit {gate.name!r} has no result"
            )
            continue
        if result.status != PASS:
            detail = f": {result.detail}" if result.detail else ""
            reasons.append(
                f"required green-gate audit {gate.name!r} did not pass"
                f" (status={result.status!r}){detail}"
            )
    return reasons


def _normalize_gate_result(result: GateResult | Mapping[str, Any]) -> GateResult:
    if isinstance(result, GateResult):
        return result
    return GateResult(
        name=str(result.get("name", "")),
        status=str(result.get("status", "")),
        command=str(result.get("command", "")),
        detail=str(result.get("detail", "")),
    )


def _normalize_repo_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _is_protected_branch(branch: str) -> bool:
    return branch.strip() in PROTECTED_BRANCHES


def _resolve_store(store: Path, root: Path) -> Path:
    return store if store.is_absolute() else root / store


def _resolve_worktree_base(root: Path, base_dir: Path | None) -> Path:
    default_base = default_worktree_base(root).resolve()
    target_base = (base_dir or default_base).resolve()
    if target_base != default_base and not _is_relative_to(target_base, default_base):
        raise RomEditWorktreeError(
            f"worktree base must stay under {default_base}: {target_base}"
        )
    return target_base


def _make_worktree_slug(base_head: str, changed_files: Sequence[str]) -> str:
    payload = "\n".join([base_head, *sorted(changed_files), str(time.time_ns())])
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def _git_stdout(
    args: Sequence[str],
    *,
    cwd: Path,
    input_text: str | None = None,
    strip_output: bool = True,
) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        shell=False,
        text=True,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RomEditWorktreeError(
            f"git {' '.join(args)} failed with code {completed.returncode}: {detail}"
        )
    return completed.stdout.strip() if strip_output else completed.stdout


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
