from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.coverage import build_coverage_report


class CoverageTests(unittest.TestCase):
    def test_coverage_marks_direct_and_indirect_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text(
                "01:D141 wCurDamage\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld [wCurDamage], a\n\tret\n",
                encoding="utf-8",
            )
            trace = root / "trace.json"
            trace.write_text(
                json.dumps(
                    {
                        "covered_rule_ids": ["damage.test"],
                        "events": [
                            {
                                "source": {
                                    "full_symbol": "BattleCommand_Test",
                                    "source_file": "engine/battle.asm",
                                    "rule_id": "damage.test",
                                }
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_coverage_report(
                traces=("trace.json",),
                symbols=("BattleCommand_Test", "wCurDamage"),
                rules=("damage.test",),
                changed_files=("engine/battle.asm",),
                symbols_path="test.sym",
                root=root,
            )

        by_id = {target["id"]: target for target in report["targets"]}
        self.assertTrue(report["valid"])
        self.assertEqual(by_id["BattleCommand_Test"]["status"], "covered")
        self.assertEqual(by_id["engine/battle.asm"]["status"], "covered")
        self.assertEqual(by_id["wCurDamage"]["status"], "indirect")
        self.assertEqual(by_id["damage.test"]["status"], "covered")
        self.assertGreaterEqual(report["covered_rule_count"], 1)

    def test_coverage_uses_content_rom_mirror_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content_report = root / "content.json"
            content_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_mirror",
                        "rom_mirrors": [
                            {
                                "type": "incbin_table_rom_bytes",
                                "status": "passed",
                                "title": "Footprints ROM bytes match",
                                "source_file": "gfx/footprints.asm",
                                "related_files": ["gfx/footprints.asm", "gfx/footprints/bulbasaur.1bpp"],
                                "related_symbols": ["Footprints"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_coverage_report(reports=("content.json",), root=root)

        by_id = {target["id"]: target for target in report["targets"]}
        self.assertTrue(report["valid"])
        self.assertEqual(by_id["Footprints"]["status"], "covered")
        self.assertEqual(by_id["gfx/footprints.asm"]["status"], "covered")
        self.assertIn("Footprints", by_id["gfx/footprints.asm"]["related_symbols"])

    def test_cli_coverage_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text("01:4000 BattleCommand_Test\n", encoding="utf-8")
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tret\n",
                encoding="utf-8",
            )
            trace = root / "trace.json"
            trace.write_text(
                json.dumps({"full_symbol": "BattleCommand_Test"}),
                encoding="utf-8",
            )
            out = root / "coverage.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "coverage",
                        "--trace",
                        str(trace),
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "BattleCommand_Test",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_coverage_report")
        self.assertEqual(data["covered_target_count"], 1)
