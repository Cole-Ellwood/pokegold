from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.debugger.handoff_log import HandoffRow, append_row
from tools.debugger.rom_edit import (
    FAIL,
    PASS,
    RELEASE_SMOKE_GATE_NAME,
    SAVE_FORMAT_GATE_NAME,
    GateResult,
    RomEditWorktreeError,
    apply_unified_patch_to_worktree,
    create_rom_edit_worktree,
    decide_auto_apply,
    default_worktree_base,
    remove_rom_edit_worktree,
    required_green_gate_stack,
    touches_ram,
)


PHASE = "P12_rom_edit_apply_candidate"
ROOT = Path(__file__).resolve().parents[3]


def _ack_start() -> HandoffRow:
    return HandoffRow(
        phase=PHASE,
        event="ack_start",
        status="in_progress",
        model="codex",
        primary="codex",
        confidence="repo-proven",
        claim="Codex starts a rom-edit candidate.",
    )


def _slice_update() -> HandoffRow:
    return HandoffRow(
        phase=PHASE,
        event="slice_update",
        status="ready_for_review",
        model="codex",
        primary="codex",
        confidence="repo-proven",
        claim="Rom-edit candidate green gates are ready for review.",
    )


def _slice_review() -> HandoffRow:
    return HandoffRow(
        phase=PHASE,
        event="slice_review",
        status="slice_accepted",
        model="claude",
        primary="codex",
        reviewer="claude",
        confidence="repo-proven",
        claim="Claude reviewed the rom-edit candidate and accepted it.",
    )


def _rows(*rows: HandoffRow) -> list[dict[str, object]]:
    return [{**row.as_dict(), "_line": idx + 1} for idx, row in enumerate(rows)]


def _passing_results(changed_files: tuple[str, ...]) -> tuple[GateResult, ...]:
    return tuple(
        GateResult(name=gate.name, command=gate.command, status=PASS)
        for gate in required_green_gate_stack(changed_files)
    )


def _write_store(root: Path, *rows: HandoffRow) -> Path:
    store = root / "handoff.jsonl"
    for row in rows:
        append_row(row, store=store)
    return store


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed: {proc.stderr or proc.stdout}"
        )
    return proc.stdout


def _init_repo(repo: Path) -> None:
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "rom-edit-test@example.invalid")
    _git(repo, "config", "user.name", "Rom Edit Test")
    (repo / "file.txt").write_text("one\n", encoding="utf-8")
    _git(repo, "add", "file.txt")
    _git(repo, "commit", "-m", "initial")


def _file_txt_patch(new_text: str) -> str:
    return (
        "diff --git a/file.txt b/file.txt\n"
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1 +1 @@\n"
        "-one\n"
        f"+{new_text}\n"
    )


class RomEditAutoApplyGateTests(unittest.TestCase):
    def test_ram_path_detection_accepts_windows_and_posix_paths(self) -> None:
        self.assertTrue(touches_ram(("ram/wram.asm",)))
        self.assertTrue(touches_ram(("ram\\sram.asm",)))
        self.assertFalse(touches_ram(("engine/battle/core.asm",)))

    def test_ram_gate_stack_includes_save_format_before_release_smoke(self) -> None:
        gates = required_green_gate_stack(("ram/wram.asm",))
        self.assertEqual(
            [gate.name for gate in gates],
            [SAVE_FORMAT_GATE_NAME, RELEASE_SMOKE_GATE_NAME],
        )

    def test_non_ram_gate_stack_requires_release_smoke_only(self) -> None:
        gates = required_green_gate_stack(("engine/battle/core.asm",))
        self.assertEqual([gate.name for gate in gates], [RELEASE_SMOKE_GATE_NAME])

    def test_allows_green_mutual_verified_non_protected_branch(self) -> None:
        changed = ("engine/battle/core.asm",)
        decision = decide_auto_apply(
            changed_files=changed,
            gate_results=_passing_results(changed),
            handoff_phase=PHASE,
            handoff_rows=_rows(_ack_start(), _slice_update(), _slice_review()),
            target_branch="codex/cleanup-gsc-rebalance-split",
        )

        self.assertTrue(decision["allowed"], decision)
        self.assertEqual(decision["blocking_reasons"], [])
        self.assertTrue(decision["handoff_mutual_verified"])

    def test_refuses_single_signed_candidate(self) -> None:
        changed = ("engine/battle/core.asm",)
        decision = decide_auto_apply(
            changed_files=changed,
            gate_results=_passing_results(changed),
            handoff_phase=PHASE,
            handoff_rows=_rows(_ack_start(), _slice_update()),
            target_branch="codex/cleanup-gsc-rebalance-split",
        )

        self.assertFalse(decision["allowed"])
        self.assertTrue(
            any("not mutual-verified" in reason for reason in decision["blocking_reasons"]),
            decision,
        )

    def test_refuses_ram_edit_when_save_format_gate_missing(self) -> None:
        changed = ("ram/wram.asm",)
        decision = decide_auto_apply(
            changed_files=changed,
            gate_results=(GateResult(name=RELEASE_SMOKE_GATE_NAME, status=PASS),),
            handoff_phase=PHASE,
            handoff_rows=_rows(_ack_start(), _slice_update(), _slice_review()),
            target_branch="codex/cleanup-gsc-rebalance-split",
        )

        self.assertFalse(decision["allowed"])
        self.assertTrue(
            any(SAVE_FORMAT_GATE_NAME in reason for reason in decision["blocking_reasons"]),
            decision,
        )


class RomEditWorktreeLifecycleTests(unittest.TestCase):
    def test_create_and_remove_worktree_roundtrip_in_temp_repo(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)

            worktree = create_rom_edit_worktree(
                root=repo,
                changed_files=("file.txt",),
                slug="roundtrip",
            )

            worktree_path = Path(worktree.path)
            self.assertTrue(worktree_path.is_dir())
            self.assertEqual(
                worktree_path.parent,
                default_worktree_base(repo.resolve()).resolve(),
            )
            self.assertEqual(
                (worktree_path / "file.txt").read_text(encoding="utf-8"),
                "one\n",
            )
            self.assertIn("roundtrip", _git(repo, "worktree", "list"))

            removed = remove_rom_edit_worktree(worktree.path, root=repo)

            self.assertEqual(removed["removed"], str(worktree_path))
            self.assertEqual(removed["removed_branch"], "rom-edit/roundtrip")
            self.assertFalse(worktree_path.exists())
            self.assertNotIn("rom-edit/roundtrip", _git(repo, "branch", "--list"))

    def test_create_refuses_existing_target_path(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            existing = default_worktree_base(repo.resolve()) / "dupe"
            existing.mkdir(parents=True)

            with self.assertRaisesRegex(RomEditWorktreeError, "already exists"):
                create_rom_edit_worktree(root=repo, slug="dupe")

    def test_remove_refuses_path_outside_rom_edit_base(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)

            with self.assertRaisesRegex(RomEditWorktreeError, "outside rom-edit base"):
                remove_rom_edit_worktree(repo, root=repo)

    def test_create_refuses_worktree_base_outside_local_tmp_boundary(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)

            with self.assertRaisesRegex(RomEditWorktreeError, "worktree base"):
                create_rom_edit_worktree(
                    root=repo,
                    base_dir=Path(tmp) / "external-worktrees",
                    slug="outside",
                )


class RomEditPatchApplyTests(unittest.TestCase):
    def test_apply_unified_patch_changes_worktree_not_main_checkout(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            worktree = create_rom_edit_worktree(root=repo, slug="patch-core")
            patch = _file_txt_patch("two")

            result = apply_unified_patch_to_worktree(
                worktree.path,
                patch,
                root=repo,
            )

            self.assertTrue(result["patch_applied"])
            self.assertEqual(result["changed_files"], ("file.txt",))
            self.assertIn("+two", result["diff"])
            self.assertEqual(
                (Path(worktree.path) / "file.txt").read_text(encoding="utf-8"),
                "two\n",
            )
            self.assertEqual((repo / "file.txt").read_text(encoding="utf-8"), "one\n")

    def test_apply_unified_patch_refuses_empty_patch(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            worktree = create_rom_edit_worktree(root=repo, slug="empty-patch")

            with self.assertRaisesRegex(RomEditWorktreeError, "empty patch"):
                apply_unified_patch_to_worktree(worktree.path, "\n", root=repo)

            self.assertEqual(
                (Path(worktree.path) / "file.txt").read_text(encoding="utf-8"),
                "one\n",
            )

    def test_apply_unified_patch_refuses_path_outside_rom_edit_base(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)

            with self.assertRaisesRegex(RomEditWorktreeError, "outside rom-edit base"):
                apply_unified_patch_to_worktree(repo, "not a patch", root=repo)


class RomEditProposeCliTests(unittest.TestCase):
    def test_propose_cli_creates_worktree_and_applies_patch(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            proc = subprocess.run(
                [
                    "python",
                    "-m",
                    "tools.debugger",
                    "rom-edit",
                    "propose",
                    "--root",
                    str(repo),
                    "--file",
                    "file.txt",
                    "--change",
                    _file_txt_patch("three"),
                    "--slug",
                    "cli-propose",
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            proposal = json.loads(proc.stdout)
            worktree_path = Path(proposal["worktree"]["path"])
            self.assertEqual(proposal["changed_files"], ["file.txt"])
            self.assertEqual(
                (worktree_path / "file.txt").read_text(encoding="utf-8"),
                "three\n",
            )
            self.assertEqual((repo / "file.txt").read_text(encoding="utf-8"), "one\n")

            remove_rom_edit_worktree(worktree_path, root=repo)

    def test_propose_cli_cleans_up_failed_patch(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            proc = subprocess.run(
                [
                    "python",
                    "-m",
                    "tools.debugger",
                    "rom-edit",
                    "propose",
                    "--root",
                    str(repo),
                    "--file",
                    "file.txt",
                    "--change",
                    "not a patch",
                    "--slug",
                    "bad-proposal",
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(proc.returncode, 1, proc.stdout)
            self.assertIn("git apply --check", proc.stderr)
            self.assertFalse(
                (default_worktree_base(repo.resolve()) / "bad-proposal").exists()
            )

    def test_refuses_red_save_format_audit_for_ram_edit(self) -> None:
        changed = ("ram/wram.asm",)
        decision = decide_auto_apply(
            changed_files=changed,
            gate_results=(
                GateResult(
                    name=SAVE_FORMAT_GATE_NAME,
                    status=FAIL,
                    detail="save layout changed without bumping SAVE_FORMAT_VERSION",
                ),
                GateResult(name=RELEASE_SMOKE_GATE_NAME, status=PASS),
            ),
            handoff_phase=PHASE,
            handoff_rows=_rows(_ack_start(), _slice_update(), _slice_review()),
            target_branch="codex/cleanup-gsc-rebalance-split",
        )

        self.assertFalse(decision["allowed"])
        self.assertTrue(
            any("SAVE_FORMAT_VERSION" in reason for reason in decision["blocking_reasons"]),
            decision,
        )

    def test_refuses_remote_push(self) -> None:
        changed = ("engine/battle/core.asm",)
        decision = decide_auto_apply(
            changed_files=changed,
            gate_results=_passing_results(changed),
            handoff_phase=PHASE,
            handoff_rows=_rows(_ack_start(), _slice_update(), _slice_review()),
            target_branch="codex/cleanup-gsc-rebalance-split",
            push_remote=True,
        )

        self.assertFalse(decision["allowed"])
        self.assertIn("auto-apply refuses remote push", decision["blocking_reasons"])

    def test_refuses_unknown_target_branch(self) -> None:
        changed = ("engine/battle/core.asm",)
        decision = decide_auto_apply(
            changed_files=changed,
            gate_results=_passing_results(changed),
            handoff_phase=PHASE,
            handoff_rows=_rows(_ack_start(), _slice_update(), _slice_review()),
        )

        self.assertFalse(decision["allowed"])
        self.assertIn(
            "auto-apply requires explicit target branch",
            decision["blocking_reasons"],
        )

    def test_refuses_master_target_branch(self) -> None:
        changed = ("engine/battle/core.asm",)
        decision = decide_auto_apply(
            changed_files=changed,
            gate_results=_passing_results(changed),
            handoff_phase=PHASE,
            handoff_rows=_rows(_ack_start(), _slice_update(), _slice_review()),
            target_branch="master",
        )

        self.assertFalse(decision["allowed"])
        self.assertTrue(
            any("protected target branch" in reason for reason in decision["blocking_reasons"]),
            decision,
        )

    def test_refuses_master_merge_target(self) -> None:
        changed = ("engine/battle/core.asm",)
        decision = decide_auto_apply(
            changed_files=changed,
            gate_results=_passing_results(changed),
            handoff_phase=PHASE,
            handoff_rows=_rows(_ack_start(), _slice_update(), _slice_review()),
            target_branch="codex/cleanup-gsc-rebalance-split",
            merge_target="master",
        )

        self.assertFalse(decision["allowed"])
        self.assertTrue(
            any("auto-merge" in reason for reason in decision["blocking_reasons"]),
            decision,
        )

    def test_front_door_gate_cli_allows_green_mutual_candidate(self) -> None:
        with TemporaryDirectory() as tmp:
            store = _write_store(
                Path(tmp),
                _ack_start(),
                _slice_update(),
                _slice_review(),
            )
            proc = subprocess.run(
                [
                    "python",
                    "-m",
                    "tools.debugger",
                    "rom-edit",
                    "gate",
                    "--changed-file",
                    "engine/battle/core.asm",
                    "--gate",
                    "release_smoke=pass",
                    "--handoff-phase",
                    PHASE,
                    "--handoff-store",
                    str(store),
                    "--target-branch",
                    "codex/cleanup-gsc-rebalance-split",
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        decision = json.loads(proc.stdout)
        self.assertTrue(decision["allowed"], decision)
        self.assertTrue(decision["handoff_mutual_verified"], decision)

    def test_front_door_gate_cli_refuses_red_save_format_audit(self) -> None:
        with TemporaryDirectory() as tmp:
            store = _write_store(
                Path(tmp),
                _ack_start(),
                _slice_update(),
                _slice_review(),
            )
            proc = subprocess.run(
                [
                    "python",
                    "-m",
                    "tools.debugger",
                    "rom-edit",
                    "gate",
                    "--changed-file",
                    "ram/wram.asm",
                    "--gate",
                    "save_format_version=fail",
                    "--gate",
                    "release_smoke=pass",
                    "--handoff-phase",
                    PHASE,
                    "--handoff-store",
                    str(store),
                    "--target-branch",
                    "codex/cleanup-gsc-rebalance-split",
                    "--json",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(proc.returncode, 1, proc.stdout)
        decision = json.loads(proc.stdout)
        self.assertFalse(decision["allowed"], decision)
        self.assertTrue(
            any(SAVE_FORMAT_GATE_NAME in reason for reason in decision["blocking_reasons"]),
            decision,
        )


if __name__ == "__main__":
    unittest.main()
