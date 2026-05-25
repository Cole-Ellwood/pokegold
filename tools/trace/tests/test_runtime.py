from __future__ import annotations

import hashlib
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from tools.trace import runtime
from tools.trace.runtime import (
    Symbol,
    display_path,
    fail,
    parse_symbols,
    read_addr,
    read_byte,
    read_range,
    read_word,
    sha256_file,
)


class FakeMemory:
    """Minimal stand-in for PyBoy's memory; supports flat addr indexing,
    (bank, addr) indexing for the WRAMX range, and the $FF70 SVBK shadow."""

    def __init__(self, flat: dict[int, int] | None = None,
                 banked: dict[tuple[int, int], int] | None = None,
                 *, raise_on_banked: bool = False) -> None:
        self._flat: dict[int, int] = dict(flat or {})
        self._banked: dict[tuple[int, int], int] = dict(banked or {})
        self._raise_on_banked = raise_on_banked

    def __getitem__(self, key):
        if isinstance(key, tuple):
            if self._raise_on_banked:
                raise RuntimeError("banked access disabled")
            return self._banked.get(key, 0)
        return self._flat.get(int(key), 0)

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            self._banked[key] = int(value) & 0xFF
        else:
            self._flat[int(key)] = int(value) & 0xFF


class FakePyBoy:
    def __init__(self, memory: FakeMemory) -> None:
        self.memory = memory


class SymbolDataclassTests(unittest.TestCase):
    def test_symbol_is_frozen_and_hashable(self) -> None:
        a = Symbol(1, 0xD200)
        b = Symbol(1, 0xD200)
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        with self.assertRaises(Exception):
            a.bank = 2  # type: ignore[misc]

    def test_symbols_with_different_banks_or_addresses_differ(self) -> None:
        self.assertNotEqual(Symbol(1, 0xD200), Symbol(2, 0xD200))
        self.assertNotEqual(Symbol(1, 0xD200), Symbol(1, 0xD201))


class FailExitTests(unittest.TestCase):
    def test_fail_prints_error_and_raises_systemexit(self) -> None:
        stderr_buffer = io.StringIO()
        with redirect_stderr(stderr_buffer):
            with self.assertRaises(SystemExit) as ctx:
                fail("boom")
        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("ERROR: boom", stderr_buffer.getvalue())


class DisplayPathTests(unittest.TestCase):
    def test_path_inside_repo_returns_forward_slash_relative(self) -> None:
        inside = runtime.ROOT / "tools" / "trace" / "runtime.py"
        self.assertEqual(display_path(inside), "tools/trace/runtime.py")

    def test_path_outside_repo_returns_absolute_string(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            outside = Path(tempdir) / "x.bin"
            outside.write_bytes(b"")
            result = display_path(outside)
            self.assertEqual(result, str(outside.resolve()))


class Sha256FileTests(unittest.TestCase):
    def test_known_content_matches_hashlib(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            target = Path(tempdir) / "blob.bin"
            payload = b"trace ROM contents"
            target.write_bytes(payload)
            expected = hashlib.sha256(payload).hexdigest().upper()
            self.assertEqual(sha256_file(target), expected)

    def test_missing_file_fails(self) -> None:
        stderr_buffer = io.StringIO()
        with redirect_stderr(stderr_buffer):
            with self.assertRaises(SystemExit):
                sha256_file(Path("does-not-exist.bin"))
        self.assertIn("missing file for SHA256", stderr_buffer.getvalue())


class ParseSymbolsTests(unittest.TestCase):
    def test_parses_typical_symfile_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            sym = Path(tempdir) / "x.sym"
            sym.write_text(
                "; comment header\n"
                "00:0150 EntryPoint\n"
                "01:d200 wExampleField\n"
                "02:dffa wWramxField\n"
                "garbage line with no colon\n"
                "01:notahex wBogus\n",
                encoding="utf-8",
            )
            out = parse_symbols(sym)
        self.assertEqual(out["EntryPoint"], Symbol(0, 0x0150))
        self.assertEqual(out["wExampleField"], Symbol(1, 0xD200))
        self.assertEqual(out["wWramxField"], Symbol(2, 0xDFFA))
        self.assertNotIn("wBogus", out)

    def test_missing_symbol_file_fails(self) -> None:
        stderr_buffer = io.StringIO()
        with redirect_stderr(stderr_buffer):
            with self.assertRaises(SystemExit):
                parse_symbols(Path("missing.sym"))
        self.assertIn("missing symbol file", stderr_buffer.getvalue())


class ReadByteTests(unittest.TestCase):
    def test_flat_address_reads_from_memory_dict(self) -> None:
        pyboy = FakePyBoy(FakeMemory(flat={0xFF44: 0x91}))
        self.assertEqual(read_byte(pyboy, Symbol(0, 0xFF44)), 0x91)

    def test_wramx_address_with_bank_uses_banked_index(self) -> None:
        pyboy = FakePyBoy(FakeMemory(banked={(2, 0xD400): 0x42}))
        self.assertEqual(read_byte(pyboy, Symbol(2, 0xD400)), 0x42)

    def test_wramx_address_falls_back_to_svbk_when_banked_raises(self) -> None:
        memory = FakeMemory(
            flat={0xFF70: 1, 0xD400: 0x77},
            raise_on_banked=True,
        )
        pyboy = FakePyBoy(memory)
        self.assertEqual(read_byte(pyboy, Symbol(2, 0xD400)), 0x77)
        # SVBK shadow restored to the original bank.
        self.assertEqual(memory[0xFF70], 1)

    def test_wramx_address_with_bank_zero_skips_bank_path(self) -> None:
        # bank=0 is treated as "no banking metadata"; use flat memory.
        pyboy = FakePyBoy(FakeMemory(flat={0xD400: 0x99}))
        self.assertEqual(read_byte(pyboy, Symbol(0, 0xD400)), 0x99)


class ReadAddrAndRangeTests(unittest.TestCase):
    def test_read_addr_matches_read_byte(self) -> None:
        pyboy = FakePyBoy(FakeMemory(flat={0xC123: 0x88}))
        self.assertEqual(read_addr(pyboy, 0, 0xC123), 0x88)

    def test_read_range_returns_contiguous_bytes(self) -> None:
        pyboy = FakePyBoy(
            FakeMemory(flat={0xC100: 1, 0xC101: 2, 0xC102: 3, 0xC103: 4})
        )
        self.assertEqual(
            read_range(pyboy, Symbol(0, 0xC100), 4),
            [1, 2, 3, 4],
        )

    def test_read_range_size_zero_returns_empty_list(self) -> None:
        pyboy = FakePyBoy(FakeMemory())
        self.assertEqual(read_range(pyboy, Symbol(0, 0xC100), 0), [])

    def test_read_word_is_big_endian(self) -> None:
        # Per the runtime helper: high byte at offset+0, low byte at offset+1.
        # See macros/ram.asm for the runtime-populated big-endian convention.
        pyboy = FakePyBoy(FakeMemory(flat={0xC100: 0x12, 0xC101: 0x34}))
        self.assertEqual(read_word(pyboy, Symbol(0, 0xC100)), 0x1234)


if __name__ == "__main__":
    unittest.main()
