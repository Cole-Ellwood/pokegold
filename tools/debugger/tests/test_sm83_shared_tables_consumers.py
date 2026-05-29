from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.audit.check_sm83_shared_tables_consumers import (
    MIGRATION_INTENT_MARKER,
    scan_sm83_shared_tables_consumers,
)
from tools.debugger.catalog import ROOT


class Sm83SharedTablesConsumerAuditTests(unittest.TestCase):
    def test_live_repo_matches_shrinking_allowlist(self) -> None:
        report = scan_sm83_shared_tables_consumers(root=ROOT)
        self.assertTrue(report["ok"], report)

    def test_allowlist_hit_at_correct_count_untouched_passes(self) -> None:
        with self._repo("return INDEX_REG[opcode & 0x07]") as root:
            key = ("tools/debugger/effect_trace.py", "decode", "register_index")

            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={key: {"count": 1}},
                touched_allowlist_keys=set(),
                commit_message="",
            )

        self.assertTrue(report["ok"], report)

    def test_new_unallowlisted_site_fails(self) -> None:
        with self._repo("return INDEX_REG[opcode & 0x07]") as root:
            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={},
                touched_allowlist_keys=set(),
                commit_message="",
            )

        self.assertFalse(report["ok"])
        self.assertEqual(report["issues"][0]["dispatch_family"], "register_index")
        self.assertIn("not in the shrinking allowlist", report["issues"][0]["message"])

    def test_rejects_module_scope_shared_table_shadow_assignment(self) -> None:
        with self._repo(
            "INDEX_REG = {0: 'b'}\n"
            "def decode(opcode):\n"
            "    return opcode\n",
            full_text=True,
        ) as root:
            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={},
                touched_allowlist_keys=set(),
                commit_message="",
            )

        self.assertFalse(report["ok"])
        self.assertEqual(report["issues"][0]["function"], "<module>")
        self.assertEqual(report["issues"][0]["name"], "INDEX_REG")
        self.assertIn("must not be rebound", report["issues"][0]["message"])

    def test_local_shared_table_name_assignment_is_not_a_module_shadow(self) -> None:
        with self._repo(
            "def decode(opcode):\n"
            "    INDEX_REG = {0: 'b'}\n"
            "    return opcode\n",
            full_text=True,
        ) as root:
            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={},
                touched_allowlist_keys=set(),
                commit_message="",
            )

        self.assertTrue(report["ok"], report)

    def test_allows_shared_table_alias_import_from_sm83_model(self) -> None:
        with self._repo(
            "from .sm83_model import REGISTER_INDEX_TARGETS as INDEX_REG\n"
            "\n"
            "def decode(opcode):\n"
            "    return opcode\n",
            full_text=True,
        ) as root:
            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={},
                touched_allowlist_keys=set(),
                commit_message="",
            )

        self.assertTrue(report["ok"], report)

    def test_rejects_shared_table_alias_import_from_other_module(self) -> None:
        with self._repo(
            "from .other_model import REGISTER_INDEX_TARGETS as INDEX_REG\n"
            "\n"
            "def decode(opcode):\n"
            "    return opcode\n",
            full_text=True,
        ) as root:
            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={},
                touched_allowlist_keys=set(),
                commit_message="",
            )

        self.assertFalse(report["ok"])
        self.assertEqual(report["issues"][0]["function"], "<module>")
        self.assertEqual(report["issues"][0]["name"], "INDEX_REG")
        self.assertIn("must not be rebound", report["issues"][0]["message"])

    def test_rejects_module_scope_shared_table_attribute_store(self) -> None:
        with self._repo(
            "import tools.debugger.sm83_model as model\n"
            "model.REGISTER_INDEX_TARGETS = {0: 'b'}\n"
            "\n"
            "def decode(opcode):\n"
            "    return opcode\n",
            full_text=True,
        ) as root:
            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={},
                touched_allowlist_keys=set(),
                commit_message="",
            )

        self.assertFalse(report["ok"])
        self.assertEqual(report["issues"][0]["function"], "<module>")
        self.assertEqual(report["issues"][0]["name"], "REGISTER_INDEX_TARGETS")
        self.assertIn("must not be rebound", report["issues"][0]["message"])

    def test_count_up_fails_even_with_marker(self) -> None:
        with self._repo("return INDEX_REG[opcode & 0x07], INDEX_REG[(opcode >> 3) & 0x07]") as root:
            key = ("tools/debugger/effect_trace.py", "decode", "register_index")

            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={key: {"count": 1}},
                touched_allowlist_keys={key},
                commit_message=MIGRATION_INTENT_MARKER,
            )

        self.assertFalse(report["ok"])
        self.assertEqual(report["issues"][0]["observed_count"], 2)
        self.assertIn("increased", report["issues"][0]["message"])

    def test_count_down_passes_without_marker(self) -> None:
        with self._repo("return INDEX_REG[opcode & 0x07]") as root:
            key = ("tools/debugger/effect_trace.py", "decode", "register_index")

            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={key: {"count": 2}},
                touched_allowlist_keys={key},
                commit_message="",
            )

        self.assertTrue(report["ok"], report)
        self.assertEqual(report["migrations"][0]["observed_count"], 1)

    def test_stable_touched_without_marker_fails(self) -> None:
        with self._repo("return INDEX_REG[opcode & 0x07]") as root:
            key = ("tools/debugger/effect_trace.py", "decode", "register_index")

            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={key: {"count": 1}},
                touched_allowlist_keys={key},
                commit_message="",
            )

        self.assertFalse(report["ok"])
        self.assertIn("stayed stable in a touched function", report["issues"][0]["message"])

    def test_stable_touched_with_marker_passes(self) -> None:
        with self._repo("return INDEX_REG[opcode & 0x07]") as root:
            key = ("tools/debugger/effect_trace.py", "decode", "register_index")

            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={key: {"count": 1}},
                touched_allowlist_keys={key},
                commit_message=f"refactor decode\n\n{MIGRATION_INTENT_MARKER}\n",
            )

        self.assertTrue(report["ok"], report)

    def test_count_to_zero_passes_so_entry_can_be_removed(self) -> None:
        with self._repo("return opcode") as root:
            key = ("tools/debugger/effect_trace.py", "decode", "register_index")

            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={key: {"count": 1}},
                touched_allowlist_keys={key},
                commit_message="",
            )

        self.assertTrue(report["ok"], report)
        self.assertEqual(report["migrations"][0]["observed_count"], 0)

    def test_attribute_dispatch_site_is_counted_once(self) -> None:
        with self._repo(
            "import tools.debugger.sm83_model as model\n"
            "def decode(opcode):\n"
            "    return model.REGISTER_INDEX_TARGETS[opcode & 0x07]\n",
            full_text=True,
        ) as root:
            key = ("tools/debugger/effect_trace.py", "decode", "register_index")

            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={key: {"count": 1}},
                touched_allowlist_keys=set(),
                commit_message="",
            )

        self.assertTrue(report["ok"], report)

    def test_call_dispatch_site_is_counted_once(self) -> None:
        with self._repo("return INDEX_REG(opcode)") as root:
            key = ("tools/debugger/effect_trace.py", "decode", "register_index")

            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={key: {"count": 1}},
                touched_allowlist_keys=set(),
                commit_message="",
            )

        self.assertTrue(report["ok"], report)

    def test_renamed_only_noop_keeps_live_repo_stable(self) -> None:
        report = scan_sm83_shared_tables_consumers(
            root=ROOT,
            touched_allowlist_keys=set(),
            commit_message="",
        )
        self.assertTrue(report["ok"], report)

    def test_git_diff_marks_allowlisted_function_touched(self) -> None:
        with self._repo("return INDEX_REG[opcode & 0x07]") as root:
            self._git(root, "init")
            self._git(root, "config", "user.email", "codex@example.invalid")
            self._git(root, "config", "user.name", "Codex")
            self._git(root, "add", "tools/debugger/effect_trace.py", "tools/debugger/sm83_model.py")
            self._git(root, "commit", "-m", "base")
            (root / "tools" / "debugger" / "effect_trace.py").write_text(
                "from .sm83_model import REGISTER_INDEX_TARGETS as INDEX_REG\n"
                "\n"
                "def decode(opcode):\n"
                "    # touched without burning down the shared-table dispatch\n"
                "    return INDEX_REG[opcode & 0x07]\n",
                encoding="utf-8",
            )
            key = ("tools/debugger/effect_trace.py", "decode", "register_index")

            report = scan_sm83_shared_tables_consumers(
                root=root,
                allowlist={key: {"count": 1}},
                commit_message="",
            )

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["touched_allowlist_keys"],
            [{"path": key[0], "function": key[1], "dispatch_family": key[2]}],
        )

    def _git(self, root: Path, *args: str) -> None:
        try:
            completed = subprocess.run(
                ["git", *args],
                cwd=root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
            )
        except OSError as exc:
            self.skipTest(f"git unavailable: {exc}")
        if completed.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {completed.stderr}")

    def _repo(self, body: str, *, full_text: bool = False):
        return _RepoFixture(body, full_text=full_text)


class _RepoFixture:
    def __init__(self, body: str, *, full_text: bool) -> None:
        self.body = body
        self.full_text = full_text
        self.temp = TemporaryDirectory()

    def __enter__(self) -> Path:
        root = Path(self.temp.__enter__())
        debugger_root = root / "tools" / "debugger"
        debugger_root.mkdir(parents=True)
        (debugger_root / "sm83_model.py").write_text(
            "REGISTER_INDEX_TARGETS = {0: 'b'}\n",
            encoding="utf-8",
        )
        text = self.body if self.full_text else _consumer_text(self.body)
        (debugger_root / "effect_trace.py").write_text(text, encoding="utf-8")
        return root

    def __exit__(self, exc_type, exc, tb) -> None:
        self.temp.__exit__(exc_type, exc, tb)


def _consumer_text(body: str) -> str:
    return (
        "from .sm83_model import REGISTER_INDEX_TARGETS as INDEX_REG\n"
        "\n"
        "def decode(opcode):\n"
        f"    {body}\n"
    )


if __name__ == "__main__":
    unittest.main()
