from __future__ import annotations

import unittest

from tools.trace.boss_ai_trace_state_probe import party_summary, read_symbol_big_endian_word
from tools.trace.runtime import Symbol


class TraceStateProbeTests(unittest.TestCase):
    def test_pokemon_hp_words_are_read_big_endian(self) -> None:
        class FakeMemory:
            def __init__(self) -> None:
                self.values = {
                    (1, 0xD100): 0x00,
                    (1, 0xD101): 0x1A,
                }

            def __getitem__(self, key):
                return self.values[key]

        class FakePyBoy:
            def __init__(self) -> None:
                self.memory = FakeMemory()

        symbols = {"wBattleMonHP": Symbol(1, 0xD100)}

        self.assertEqual(
            read_symbol_big_endian_word(FakePyBoy(), symbols, "wBattleMonHP"),
            26,
        )

    def test_party_summary_uses_big_endian_hp_words(self) -> None:
        class FakeMemory:
            def __init__(self) -> None:
                self.values = {
                    (1, 0xD000): 0x01,  # wPartyCount
                    (1, 0xD001): 0x19,  # wPartyMon1Species
                    (1, 0xD002): 0x20,  # wPartyMon1Level
                    (1, 0xD003): 0x01,  # wPartyMon1HP high
                    (1, 0xD004): 0x2C,  # wPartyMon1HP low
                    (1, 0xD005): 0x01,  # wPartyMon1MaxHP high
                    (1, 0xD006): 0x90,  # wPartyMon1MaxHP low
                }

            def __getitem__(self, key):
                return self.values[key]

        class FakePyBoy:
            def __init__(self) -> None:
                self.memory = FakeMemory()

        symbols = {
            "wPartyCount": Symbol(1, 0xD000),
            "wPartyMon1Species": Symbol(1, 0xD001),
            "wPartyMon1Level": Symbol(1, 0xD002),
            "wPartyMon1HP": Symbol(1, 0xD003),
            "wPartyMon1MaxHP": Symbol(1, 0xD005),
        }

        summary = party_summary(FakePyBoy(), symbols, battle_mode=0)

        self.assertEqual(summary["hp"], 300)
        self.assertEqual(summary["max_hp"], 400)

    def test_battle_summary_uses_big_endian_hp_words(self) -> None:
        class FakeMemory:
            def __init__(self) -> None:
                self.values = {
                    (1, 0xD0FF): 0x01,  # wPartyCount
                    (1, 0xD100): 0x02,  # wBattleMonSpecies
                    (1, 0xD101): 0x2A,  # wBattleMonLevel
                    (1, 0xD102): 0x01,  # wBattleMonHP high
                    (1, 0xD103): 0x2C,  # wBattleMonHP low
                    (1, 0xD104): 0x01,  # wBattleMonMaxHP high
                    (1, 0xD105): 0x90,  # wBattleMonMaxHP low
                }

            def __getitem__(self, key):
                return self.values[key]

        class FakePyBoy:
            def __init__(self) -> None:
                self.memory = FakeMemory()

        symbols = {
            "wPartyCount": Symbol(1, 0xD0FF),
            "wBattleMonSpecies": Symbol(1, 0xD100),
            "wBattleMonLevel": Symbol(1, 0xD101),
            "wBattleMonHP": Symbol(1, 0xD102),
            "wBattleMonMaxHP": Symbol(1, 0xD104),
        }

        summary = party_summary(FakePyBoy(), symbols, battle_mode=1)

        self.assertEqual(summary["hp"], 300)
        self.assertEqual(summary["max_hp"], 400)


if __name__ == "__main__":
    unittest.main()
