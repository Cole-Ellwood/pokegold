from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.debugger.clobber_chain import build_clobber_chain_report, clobbers_for_instruction


class ClobberChainTests(unittest.TestCase):
    def test_banked_call_abi_clobbers_a_and_hl_not_flags(self) -> None:
        clobbers = clobbers_for_instruction("farcall", ["Target"])

        self.assertIn("a", clobbers)
        self.assertIn("h", clobbers)
        self.assertIn("l", clobbers)
        self.assertNotIn("flags", clobbers)

    def test_report_walks_transitive_call_targets(self) -> None:
        root = self._root_with_file(
            "engine/unit.asm",
            """
Root:
\tld d, a
\tcall Child
\tret
Child:
\tld c, a
\tfarcall Grandchild
\tret
Grandchild:
\tld b, a
\tret
""",
        )

        report = build_clobber_chain_report(function="Root", root=root)

        self.assertTrue(report["valid"])
        self.assertEqual(report["direct_clobbers"], ["d"])
        self.assertIn("c", report["transitive_clobbers"])
        self.assertIn("b", report["transitive_clobbers"])
        self.assertIn("a", report["transitive_clobbers"])
        self.assertIn("h", report["transitive_clobbers"])
        self.assertIn("l", report["transitive_clobbers"])
        self.assertIn(["Root", "Child"], report["clobber_chains"]["c"])
        self.assertIn(["Root", "Child", "Grandchild"], report["clobber_chains"]["b"])
        self.assertEqual(report["farcall_targets"], ["Grandchild"])
        self.assertEqual(report["farcall_abi_clobbers"][0]["callee"], "Grandchild")

    def test_register_query_expands_pairs(self) -> None:
        root = self._root_with_file(
            "engine/unit.asm",
            """
Root:
\tcall Child
\tret
Child:
\tld c, a
\tret
""",
        )

        report = build_clobber_chain_report(function="Root", register="bc", root=root)

        self.assertTrue(report["query_clobbered"])
        self.assertEqual(report["query_register_tokens"], ["b", "c"])
        self.assertEqual(report["query_clobber_chains"]["c"], [["Root", "Child"]])

    def test_push_pop_window_masks_child_clobbers(self) -> None:
        root = self._root_with_file(
            "engine/unit.asm",
            """
Root:
\tpush bc
\tcall Child
\tpop bc
\tret
Child:
\tld c, a
\tret
""",
        )

        report = build_clobber_chain_report(function="Root", register="c", root=root)

        self.assertFalse(report["query_clobbered"])
        self.assertNotIn("c", report["transitive_clobbers"])

    def test_post_pop_write_remains_visible_clobber(self) -> None:
        root = self._root_with_file(
            "engine/unit.asm",
            """
Root:
\tpush bc
\tcall Child
\tpop bc
\tld c, a
\tret
Child:
\tld c, a
\tret
""",
        )

        report = build_clobber_chain_report(function="Root", register="c", root=root)

        self.assertTrue(report["query_clobbered"])
        self.assertEqual(report["query_clobber_chains"]["c"], [["Root"]])

    def test_called_local_helper_is_masked_by_parent_save_window(self) -> None:
        root = self._root_with_file(
            "engine/unit.asm",
            """
Root:
\tpush de
\tcall .Helper
\tpop de
\tret
.Helper:
\tld d, a
\tjr .done
.done
\tld e, a
\tret
""",
        )

        report = build_clobber_chain_report(function="Root", register="de", root=root)
        helper_report = build_clobber_chain_report(function="Root.Helper", root=root)

        self.assertFalse(report["query_clobbered"])
        self.assertNotIn("d", report["transitive_clobbers"])
        self.assertNotIn("e", report["transitive_clobbers"])
        self.assertEqual(helper_report["direct_clobbers"], ["d", "e"])

    def _root_with_file(self, relative_path: str, text: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.strip() + "\n", encoding="utf-8")
        return root


if __name__ == "__main__":
    unittest.main()
