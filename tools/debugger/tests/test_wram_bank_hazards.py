from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from tools.debugger.wram_bank_hazards import build_wram_bank_hazard_report


class WramBankHazardTests(unittest.TestCase):
    def test_wram_bank_hazard_report_flags_helper_call_and_cross_bank_pop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "engine" / "battle" / "ai" / "bad.asm"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "BadCall::",
                        "\tpush af",
                        "\tld a, 2",
                        "\tcall SetWRAMBank",
                        "\tpop af",
                        "\tret",
                        "",
                        "BadInline::",
                        "\tpush af",
                        "\tboss_ai_set_wram_bank 2",
                        "\tpop af",
                        "\tboss_ai_set_wram_bank 1",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_wram_bank_hazard_report(
                source_files=("engine/battle/ai/bad.asm",),
                root=root,
            )

        finding_types = {finding["type"] for finding in report["findings"]}

        self.assertTrue(report["valid"])
        self.assertFalse(report["passed"])
        self.assertIn("set_wram_bank_call", finding_types)
        self.assertIn("stack_bank_mismatch", finding_types)

    def test_wram_bank_hazard_report_accepts_current_observation_log_idiom(self) -> None:
        report = build_wram_bank_hazard_report(
            source_files=("engine/battle/ai/observation_log.asm",),
        )

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
