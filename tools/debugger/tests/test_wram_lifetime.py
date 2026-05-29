from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.debugger.wram_lifetime import build_wram_lifetime_report


WATCH_SYMBOLS = (
    "wSeenTrainerBank",
    "wScriptAfterPointer",
    "wRunningTrainerBattleScript",
)


class WramLifetimeTests(unittest.TestCase):
    def test_trainer_union_lifetime_is_protected_when_backup_wraps_barrier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_lifetime_fixture(root, protected=True)

            report = build_wram_lifetime_report(symbols=WATCH_SYMBOLS, root=root)

        self.assertTrue(report["valid"])
        self.assertTrue(report["passed"])
        self.assertEqual(report["findings"][0]["id"], "volatile_trainer_union_protected")
        self.assertEqual(report["findings"][0]["severity"], 3)
        self.assertIn("wMenuItemsList", report["findings"][0]["overlap_labels"])

    def test_trainer_union_lifetime_fails_when_barrier_is_unprotected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_lifetime_fixture(root, protected=False)

            report = build_wram_lifetime_report(symbols=WATCH_SYMBOLS, root=root)

        self.assertTrue(report["valid"])
        self.assertFalse(report["passed"])
        self.assertEqual(report["findings"][0]["id"], "volatile_trainer_union_unprotected")
        self.assertEqual(report["findings"][0]["severity"], 1)


def write_lifetime_fixture(root: Path, *, protected: bool) -> None:
    (root / "ram").mkdir(parents=True)
    (root / "engine" / "overworld").mkdir(parents=True)
    (root / "pokegold.sym").write_text(
        "\n".join(
            [
                "00:cf29 wSeenTrainerBank",
                "00:cf36 wScriptAfterPointer",
                "00:cf38 wRunningTrainerBattleScript",
                "00:cf39 wTempTrainerEnd",
                "01:d049 wTrainerBattleContextBackup",
                "01:d059 wTrainerBattleContextBackupActive",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "ram" / "wram.asm").write_text(
        "\n".join(
            [
                "UNION",
                "wSeenTrainerBank:: db",
                "wSeenTrainerDistance:: db",
                "wSeenTrainerDirection:: db",
                "wTempTrainer:: db",
                "wTempTrainerEventFlag:: dw",
                "wTempTrainerClass:: db",
                "wTempTrainerID:: db",
                "wSeenTextPointer:: dw",
                "wWinTextPointer:: dw",
                "wLossTextPointer:: dw",
                "wScriptAfterPointer:: dw",
                "wRunningTrainerBattleScript:: db",
                "wTempTrainerEnd::",
                "NEXTU",
                "wMenuItemsList:: ds 16",
                "wMenuItemsListEnd::",
                "ENDU",
                "wTrainerBattleContextBackup:: ds wTempTrainerEnd - wSeenTrainerBank",
                "wTrainerBattleContextBackupActive:: db",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if protected:
        body = [
            "Script_startbattle:",
            "\txor a",
            "\tld [wTrainerBattleContextBackupActive], a",
            "\tcall nz, .SaveTrainerContext",
            "\tpredef StartBattle",
            "\tld a, [wTrainerBattleContextBackupActive]",
            "\tcall nz, .RestoreTrainerContext",
            "\tret",
            ".SaveTrainerContext:",
            "\tld de, wTrainerBattleContextBackup",
            "\tret",
            ".RestoreTrainerContext:",
            "\tld hl, wTrainerBattleContextBackup",
            "\tret",
            "Script_after:",
            "\tret",
        ]
    else:
        body = [
            "Script_startbattle:",
            "\tpredef StartBattle",
            "\tret",
            "Script_after:",
            "\tret",
        ]
    (root / "engine" / "overworld" / "scripting.asm").write_text(
        "\n".join(body) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
