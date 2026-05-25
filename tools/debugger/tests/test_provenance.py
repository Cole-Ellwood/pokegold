from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.provenance import build_provenance_report


class ProvenanceTests(unittest.TestCase):
    def test_provenance_maps_symbols_to_source_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text(
                "01:4000 BattleCommand_Test\n02:5abc wCurDamage\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld hl, wCurDamage\n\tret\n",
                encoding="utf-8",
            )

            report = build_provenance_report(
                symbols_path="test.sym",
                symbols=("wCurDamage", "BattleCommand_Test"),
                source_files=("engine/battle.asm",),
                root=root,
            )

        self.assertTrue(report["valid"])
        by_query = {item["query"]: item for item in report["symbols"]}
        self.assertEqual(by_query["wCurDamage"]["address"]["bank_address"], "02:5ABC")
        self.assertGreaterEqual(by_query["wCurDamage"]["source_hit_count"], 2)
        self.assertEqual(by_query["wCurDamage"]["source_hits"][0]["kind"], "definition")
        self.assertEqual(report["source_files"][0]["symbols_matched_count"], 1)

    def test_cli_provenance_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            symbols = root / "test.sym"
            symbols.write_text("01:4000 LabelOne\n", encoding="utf-8")
            out = root / "provenance.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "provenance",
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "LabelOne",
                        "--json-out",
                        str(out),
                    ]
                )

            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "unified_debugger_provenance_report")
            self.assertTrue(data["valid"])
