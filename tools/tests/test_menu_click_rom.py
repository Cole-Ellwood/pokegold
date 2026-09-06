"""ROM-backed regression for menu input sound flags and AF preservation."""
from __future__ import annotations

import unittest
from pathlib import Path

from tools.damage_debugger.emulator import DebugSession


ROOT = Path(__file__).resolve().parents[2]


class MenuClickRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import pyboy  # noqa: F401
        except ImportError as exc:
            raise unittest.SkipTest(f"PyBoy unavailable: {exc}") from exc

    def check_variant(self, variant):
        for suffix in (".gbc", ".sym"):
            artifact = ROOT / f"{variant}{suffix}"
            if not artifact.is_file():
                self.skipTest(f"Build artifact unavailable: {artifact.name}")
        with DebugSession.open(variant) as session:
            # Never silently test a ROM found in a parent checkout.
            self.assertEqual(session.rom_path.parent, ROOT)
            self.assertEqual(session.sym_path.parent, ROOT)
            session.tick(600)
            emulator = session.pyboy
            registers = emulator.register_file
            hits = []
            sound = session.symbols["PlayClickSFX"]
            session.hook_register(sound.bank, sound.address, lambda _: hits.append(True))
            # Include unrelated flags and non-A/B input to pin the two masks.
            for flags in (0, 8, 0xF7, 0xFF):
                for buttons in (0, 1, 2, 3, 0x10):
                    with self.subTest(variant=variant, flags=flags, buttons=buttons):
                        emulator.memory[0xFFFF] = 0
                        emulator.memory[0xFF0F] = 0
                        emulator.memory[0xFF40] = 0
                        # Return into a stable HRAM loop after this one call.
                        emulator.memory[0xFFFD] = 0x18
                        emulator.memory[0xFFFE] = 0xFE
                        emulator.memory[0xDFF0] = 0xFD
                        emulator.memory[0xDFF1] = 0xFF
                        emulator.memory[session.symbols["wMenuFlags"].address] = flags
                        registers.SP = 0xDFF0
                        registers.A = buttons
                        registers.F = 0xB0
                        registers.PC = session.symbols["MenuClickSound"].address
                        hits.clear()
                        emulator.tick(2, False, False)
                        expected = int(bool(buttons & 3) and not flags & 8)
                        self.assertEqual(registers.PC, 0xFFFD)
                        self.assertEqual(len(hits), expected)
                        self.assertEqual(registers.A, buttons)
                        self.assertEqual(registers.F, 0xB0)
            # DebugSession closes PyBoy with save=False on context exit.

    def test_gold(self):
        self.check_variant("pokegold")

    def test_silver(self):
        self.check_variant("pokesilver")

    def test_debug_gold(self):
        self.check_variant("pokegold_debug")


if __name__ == "__main__":
    unittest.main()
