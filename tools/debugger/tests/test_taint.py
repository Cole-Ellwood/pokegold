from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tools.debugger.__main__ import main as debugger_main
from tools.debugger.taint import build_taint_report


class TaintTests(unittest.TestCase):
    def test_taint_traces_register_loads_to_memory_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine" / "battle").mkdir(parents=True)
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:D141 wCurDamage",
                        "01:D142 wBattleMonAttack",
                        "01:D144 wPlayerMovePower",
                        "01:4000 BattleCommand_DamageCalc",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\nwBattleMonAttack:: ds 2\nwPlayerMovePower:: ds 1\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "effect_commands.asm").write_text(
                "\n".join(
                    [
                        "BattleCommand_DamageCalc:",
                        "\tld a, [wBattleMonAttack]",
                        "\tadd a, [wPlayerMovePower]",
                        "\tld [wCurDamage], a",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_taint_report(
                symbols_path="test.sym",
                symbols=("wCurDamage",),
                source_files=("engine/battle/effect_commands.asm",),
                root=root,
            )

        target = report["targets"][0]
        contributors = {item["symbol"] for item in target["contributors"]}
        relations = {item["relation"] for item in target["contributors"]}

        self.assertTrue(report["valid"])
        self.assertEqual(report["sink_count"], 1)
        self.assertIn("wBattleMonAttack", contributors)
        self.assertIn("wPlayerMovePower", contributors)
        self.assertIn("memory_load", relations)
        self.assertIn("value_transform", relations)
        self.assertIn("tools.debugger taint --symbol wBattleMonAttack", "\n".join(report["commands"]))

    def test_taint_resolves_same_routine_indirect_hl_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine" / "battle" / "ai").mkdir(parents=True)
            (root / "test.sym").write_text(
                "\n".join(
                    [
                        "01:D0D3 wEnemyAIMoveScores",
                        "01:D0E0 wBossAIRole",
                        "01:4000 BossAI_Test",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wEnemyAIMoveScores:: ds 4\nwBossAIRole:: ds 1\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle" / "ai" / "boss.asm").write_text(
                "\n".join(
                    [
                        "BossAI_Test:",
                        "\tld hl, wEnemyAIMoveScores",
                        "\tld a, [wBossAIRole]",
                        "\tld [hl], a",
                        "\tret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_taint_report(
                symbols_path="test.sym",
                symbols=("wEnemyAIMoveScores",),
                source_files=("engine/battle/ai/boss.asm",),
                root=root,
            )

        target = report["targets"][0]
        contributors = {item["symbol"]: item for item in target["contributors"]}

        self.assertTrue(report["valid"])
        self.assertEqual(target["sinks"][0]["access"], "indirect_write")
        self.assertEqual(target["sinks"][0]["pointer_register"], "hl")
        self.assertIn("wBossAIRole", contributors)
        self.assertEqual(contributors["wBossAIRole"]["relation"], "memory_load")

    def test_cli_taint_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ram").mkdir()
            (root / "engine").mkdir()
            symbols = root / "test.sym"
            symbols.write_text(
                "01:D141 wCurDamage\n01:D142 wBattleMonAttack\n01:4000 BattleCommand_Test\n",
                encoding="utf-8",
            )
            (root / "ram" / "wram.asm").write_text(
                "wCurDamage:: ds 2\nwBattleMonAttack:: ds 2\n",
                encoding="utf-8",
            )
            (root / "engine" / "battle.asm").write_text(
                "BattleCommand_Test:\n\tld a, [wBattleMonAttack]\n\tld [wCurDamage], a\n",
                encoding="utf-8",
            )
            out = root / "taint.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "taint",
                        "--symbols",
                        str(symbols),
                        "--symbol",
                        "wCurDamage",
                        "--source-file",
                        str(root / "engine" / "battle.asm"),
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_taint_report")
        self.assertEqual(data["sink_count"], 1)
