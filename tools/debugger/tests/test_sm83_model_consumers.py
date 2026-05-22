from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.audit.check_sm83_model_consumers import scan_sm83_model_consumers
from tools.debugger.catalog import ROOT


class Sm83ModelConsumerAuditTests(unittest.TestCase):
    def test_live_repo_has_no_duplicated_shared_opcode_tables(self) -> None:
        report = scan_sm83_model_consumers(root=ROOT)
        self.assertTrue(report["ok"], report)

    def test_rejects_consumer_local_opcode_table(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            debugger_root = root / "tools" / "debugger"
            debugger_root.mkdir(parents=True)
            (debugger_root / "sm83_model.py").write_text(
                "REGISTER_INDEX_TARGETS = {0: 'b'}\n",
                encoding="utf-8",
            )
            (debugger_root / "effect_trace.py").write_text(
                "INDEX_REG = {0: 'b', 1: 'c'}\n",
                encoding="utf-8",
            )

            report = scan_sm83_model_consumers(root=root)

        self.assertFalse(report["ok"])
        self.assertEqual(report["issues"][0]["name"], "INDEX_REG")

    def test_accepts_consumer_importing_shared_table(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            debugger_root = root / "tools" / "debugger"
            debugger_root.mkdir(parents=True)
            (debugger_root / "sm83_model.py").write_text(
                "REGISTER_INDEX_TARGETS = {0: 'b'}\n",
                encoding="utf-8",
            )
            (debugger_root / "effect_trace.py").write_text(
                "from .sm83_model import REGISTER_INDEX_TARGETS as INDEX_REG\n",
                encoding="utf-8",
            )

            report = scan_sm83_model_consumers(root=root)

        self.assertTrue(report["ok"], report)


if __name__ == "__main__":
    unittest.main()
