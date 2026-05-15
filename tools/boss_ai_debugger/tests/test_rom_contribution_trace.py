from __future__ import annotations

import unittest

from tools.boss_ai_debugger.rom_contribution_trace import (
    HookTarget,
    RomContributionTracer,
    RuleFrame,
    format_rom_contribution_trace,
)
from tools.trace.runtime import Symbol


class FakeRegisters:
    A = 0
    HL = 0
    SP = 0xFF00


class FakeMemory:
    def __init__(self) -> None:
        self.values: dict[tuple[int, int], int] = {}

    def __getitem__(self, key):
        if isinstance(key, tuple):
            bank, address = key
        else:
            bank, address = 0, key
        return self.values.get((bank, address), self.values.get((0, address), 0))

    def __setitem__(self, key, value: int) -> None:
        if isinstance(key, tuple):
            bank, address = key
        else:
            bank, address = 0, key
        self.values[(bank, address)] = value & 0xFF


class FakePyBoy:
    def __init__(self) -> None:
        self.register_file = FakeRegisters()
        self.memory = FakeMemory()


class FakeSymbolIndex:
    rule = {
        "rule_id": "move.apply_test_bias",
        "source_label": ".ApplyTestBias",
        "classification": "public_info",
        "public_reads": ["wPlayerUsedMoves"],
    }

    def nearest_symbol(self, bank: int, address: int) -> str:
        return "BossAI_ApplyMoveModel.test_callsite"

    def nearest_rule_symbol(self, bank: int, address: int) -> str:
        return "BossAI_ApplyMoveModel.ApplyTestBias"

    def rule_for(self, full_symbol: str):
        return self.rule


class RomContributionTraceTests(unittest.TestCase):
    def test_score_helper_event_uses_score_pointer_candidate_and_active_rule(self) -> None:
        pyboy = FakePyBoy()
        pyboy.memory[1, 0xD0D3] = 20
        pyboy.memory[1, 0xD100] = 57
        pyboy.memory[1, 0xD768] = 0xD0
        pyboy.memory[1, 0xD769] = 0xD3
        pyboy.memory[0xFF00] = 0x34
        pyboy.memory[0xFF01] = 0x56
        pyboy.register_file.A = 5
        pyboy.register_file.HL = 0xC000
        pyboy.register_file.SP = 0xFF00
        tracer = RomContributionTracer(
            pyboy,
            {
                "wEnemyAIMoveScores": Symbol(1, 0xD0D3),
                "wEnemyMonMoves": Symbol(1, 0xD100),
                "wBossAIScorePtr": Symbol(1, 0xD768),
            },
            FakeSymbolIndex(),
            {57: "SURF"},
        )
        tracer.frames.append(
            RuleFrame(
                sp=0xFEF0,
                full_symbol="BossAI_ApplyMoveModel.ApplyTestBias",
                rule=FakeSymbolIndex.rule,
            )
        )

        tracer.handle_score_helper(
            HookTarget(
                kind="score_helper",
                full_symbol="BossAI_EncourageScoreHL",
                operation="encourage_score",
                bank=0x0E,
                address=0x6983,
            )
        )
        pyboy.memory[1, 0xD0D3] = 15
        tracer.close_pending(trigger="unit_test")

        self.assertEqual(len(tracer.events), 1)
        event = tracer.events[0]
        self.assertEqual(event["candidate"]["slot_index"], 0)
        self.assertEqual(event["candidate"]["move_name"], "SURF")
        self.assertEqual(event["source"]["rule_id"], "move.apply_test_bias")
        self.assertEqual(event["score_before"], 20)
        self.assertEqual(event["score_after"], 15)
        self.assertEqual(event["delta"], -5)

    def test_format_marks_changed_events(self) -> None:
        text = format_rom_contribution_trace(
            {
                "source": "trace_rom_pyboy_hooks",
                "save_state": "route:unit",
                "event_count": 1,
                "changed_event_count": 1,
                "chosen": {"move_name": "SURF", "move_id": 57, "slot_index": 0},
                "pre_model_scores": [20, 20, 20, 20],
                "post_model_scores": [20, 20, 20, 20],
                "move_scores": [15, 20, 20, 20],
                "events": [
                    {
                        "index": 1,
                        "changed": True,
                        "candidate": {"slot_index": 0, "move_name": "SURF"},
                        "operation": "encourage_score",
                        "amount_register_a": 5,
                        "score_before": 20,
                        "score_after": 15,
                        "delta": -5,
                        "source": {
                            "rule_id": "move.apply_test_bias",
                            "callsite_symbol": "BossAI_ApplyMoveModel.test_callsite",
                        },
                    }
                ],
                "known_limits": ["unit limit"],
            }
        )

        self.assertIn("* 001 slot=0 SURF encourage_score a=5 20->15 delta=-5", text)
        self.assertIn("move.apply_test_bias", text)


if __name__ == "__main__":
    unittest.main()
