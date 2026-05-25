from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from tools.debugger.wram_ownership import build_wram_ownership_report


class WramOwnershipTests(unittest.TestCase):
    def test_wram_ownership_reports_union_cotenants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "ram" / "wram.asm").write_text(
                "\n".join(
                    [
                        "UNION",
                        "wSeenTrainerBank:: db",
                        "wScriptAfterPointer:: dw",
                        "NEXTU",
                        "wMenuItemsList:: ds 16",
                        "ENDU",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_wram_ownership_report(
                symbols=("wSeenTrainerBank",),
                root=root,
            )

        owner = report["ownership"][0]
        self.assertTrue(report["valid"])
        self.assertEqual(owner["status"], "union_member")
        self.assertEqual(owner["same_arm_labels"], ["wSeenTrainerBank", "wScriptAfterPointer"])
        self.assertEqual(owner["other_union_arms"][0]["labels"], ["wMenuItemsList"])
        self.assertEqual(owner["risk"], "high")
