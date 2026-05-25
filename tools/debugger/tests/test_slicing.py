from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.slicing import build_slice_report


class SliceTests(unittest.TestCase):
    def test_slice_maps_symbol_to_static_reference_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text(
                "01:D141 wCurDamage\n01:4000 BattleCommand_Test\n01:4010 Helper\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "\n".join(
                    [
                        "BattleCommand_Test:",
                        "\tld [wCurDamage], a",
                        "\tjr .done",
                        "\tcall Helper",
                        "\tret",
                        ".done",
                        "\tret",
                        "Helper:",
                        "\tld a, [wCurDamage]",
                        "\tret",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_slice_report(
                symbols_path="test.sym",
                symbols=("wCurDamage", "BattleCommand_Test"),
                root=root,
            )

        self.assertTrue(report["valid"])
        target = report["targets"][0]
        self.assertTrue(target["found"])
        self.assertEqual(target["definition"]["path"], "ram/wram.asm")
        accesses = {edge["access"] for edge in target["incoming"]}
        sources = {edge["source"] for edge in target["incoming"]}
        self.assertIn("write", accesses)
        self.assertIn("read", accesses)
        self.assertIn("BattleCommand_Test", sources)
        self.assertIn("Helper", sources)
        routine = report["targets"][1]
        self.assertIn(
            "BattleCommand_Test.done",
            {edge["target"] for edge in routine["outgoing"]},
        )

    def test_slice_ignores_rgbds_control_directives_as_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            (root / "test.sym").write_text(
                "01:D0D3 wEnemyAIMoveScores\n01:4000 BossAI_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wEnemyAIMoveScores:: ds 4\n",
                encoding="utf-8",
            )
            (root / "engine" / "ai.asm").write_text(
                "\n".join(
                    [
                        "IF DEF(_DEBUG)",
                        "ENDC",
                        "\tdw wEnemyAIMoveScores",
                        "BossAI_Test:",
                        "\tld hl, wEnemyAIMoveScores",
                        "\tret",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_slice_report(
                symbols_path="test.sym",
                symbols=("wEnemyAIMoveScores",),
                root=root,
            )

        incoming_sources = {edge["source"] for edge in report["targets"][0]["incoming"]}

        self.assertTrue(report["valid"])
        self.assertNotIn("ENDC", incoming_sources)
        self.assertIn("BossAI_Test", incoming_sources)

    def test_cli_slice_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            symbols = root / "test.sym"
            symbols.write_text("01:D141 wCurDamage\n", encoding="utf-8")
            (root / "ram" / "wram.asm").write_text("wCurDamage:: ds 2\n", encoding="utf-8")
            out = root / "slice.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "slice",
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "wCurDamage",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_causal_slice")
        self.assertTrue(data["valid"])
