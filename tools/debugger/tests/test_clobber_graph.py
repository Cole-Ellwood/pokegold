from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.debugger.clobber_graph import (
    FARCALL_ABI_CLOBBERS,
    HOMECALL_ABI_CLOBBERS,
    build_call_graph_report,
    build_static_call_graph,
    iter_asm_source_files,
)


class ClobberGraphTests(unittest.TestCase):
    def test_resolves_local_label_call_targets(self) -> None:
        root = self._root_with_file(
            "unit.asm",
            """
Parent:
\tcall .Helper
\tcall .NoColon
\tret
.Helper:
\tret
.NoColon
\tret
Other::
\tcall Parent
\tret
""",
        )

        graph = build_static_call_graph(root=root, source_files=["unit.asm"])

        self.assertIn("Parent", graph.blocks)
        self.assertIn("Parent.Helper", graph.blocks)
        self.assertIn("Other", graph.blocks)
        edges = {(edge.caller, edge.callee, edge.call_type) for edge in graph.edges}
        self.assertIn(("Parent", "Parent.Helper", "call"), edges)
        self.assertIn(("Parent", "Parent.NoColon", "call"), edges)
        self.assertIn(("Other", "Parent", "call"), edges)

    def test_detects_conditional_call_and_tail_jump_edges(self) -> None:
        root = self._root_with_file(
            "unit.asm",
            """
Brancher:
\tcall z, Target
\tjp nc, TailTarget
\tret
Target:
\tret
TailTarget:
\tret
""",
        )

        graph = build_static_call_graph(root=root, source_files=["unit.asm"])

        by_type = {(edge.call_type, edge.callee): edge for edge in graph.edges}
        self.assertEqual(by_type[("call", "Target")].condition, "z")
        self.assertEqual(by_type[("jump", "TailTarget")].condition, "nc")

    def test_marks_banked_call_macro_edges_with_abi_clobbers(self) -> None:
        root = self._root_with_file(
            "unit.asm",
            """
Banked:
\tfarcall FarTarget
\tcallfar OtherTarget
\tcallba LegacyFarTarget
\tcallab LegacyCallTarget
\thomecall HomeTarget
\tret
""",
        )

        graph = build_static_call_graph(root=root, source_files=["unit.asm"])

        far_edges = [edge for edge in graph.edges if edge.call_type == "farcall"]
        self.assertEqual(
            [edge.callee for edge in far_edges],
            ["FarTarget", "OtherTarget", "LegacyFarTarget", "LegacyCallTarget"],
        )
        self.assertTrue(all(edge.abi_clobbers == FARCALL_ABI_CLOBBERS for edge in far_edges))
        self.assertTrue(all("target exit c" in edge.notes[0] for edge in far_edges))
        home_edge = next(edge for edge in graph.edges if edge.call_type == "homecall")
        self.assertEqual(home_edge.callee, "HomeTarget")
        self.assertEqual(home_edge.abi_clobbers, HOMECALL_ABI_CLOBBERS)
        self.assertIn("original ROM bank", home_edge.notes[0])

    def test_flags_indirect_and_rst_dispatch_edges(self) -> None:
        root = self._root_with_file(
            "unit.asm",
            """
Dispatch:
\trst FarCall
\trst JumpTable
\tjp hl
\tjp [hl]
\trst Bankswitch
\tret
""",
        )

        graph = build_static_call_graph(root=root, source_files=["unit.asm"])

        unresolved_types = [edge.call_type for edge in graph.unresolved_edges()]
        self.assertEqual(
            unresolved_types,
            ["rst_farcall", "rst_jumptable", "indirect_jump", "indirect_jump"],
        )
        direct_rst = next(edge for edge in graph.edges if edge.call_type == "rst")
        self.assertEqual(direct_rst.callee, "Bankswitch")

    def test_report_includes_direct_edges_and_reachable_chains(self) -> None:
        root = self._root_with_file(
            "unit.asm",
            """
Root:
\tcall Child
\tret
Child:
\tfarcall Grandchild
\tret
Grandchild:
\tret
""",
        )

        report = build_call_graph_report(function="Root", root=root, source_files=["unit.asm"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["edge_count"], 2)
        self.assertEqual(report["direct_edges"][0]["callee"], "Child")
        self.assertIn(["Root", "Child", "Grandchild"], report["reachable_chains"])

    def test_default_source_iterator_ignores_generated_artifact_dirs(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        for relative_path in (
            "engine/battle/core.asm",
            ".claude/tmp/generated.asm",
            ".local/tmp/generated.asm",
            "audit/run/generated.asm",
            "tools/generated.asm",
        ):
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Label:\n\tret\n", encoding="utf-8")

        paths = {path.relative_to(root).as_posix() for path in iter_asm_source_files(root=root)}

        self.assertEqual(paths, {"engine/battle/core.asm"})

    def test_section_directive_ends_previous_block(self) -> None:
        root = self._root_with_file(
            "unit.asm",
            """
First:
\tret

SECTION "rst18", ROM0[$0018]
\trst $38

Second:
\tret
""",
        )

        graph = build_static_call_graph(root=root, source_files=["unit.asm"])

        self.assertEqual([line.code for line in graph.blocks["First"].lines], ["ret"])
        self.assertEqual(graph.edges_from("First"), ())

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
