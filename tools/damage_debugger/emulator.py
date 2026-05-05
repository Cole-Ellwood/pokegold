"""DebugSession: thin PyBoy wrapper for step-debugging Pokemon Gold/Silver.

Patterns adapted from tools/trace/boss_ai_trace_capture.py.
"""

from __future__ import annotations

import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator

from .paths import find_rom, find_sym
from .symbols import Symbol, SymbolTable


def _load_pyboy_class():
    warnings.filterwarnings("ignore", message="Using SDL2 binaries.*")
    try:
        from pyboy import PyBoy  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            f"PyBoy import failed: {exc}. Install via `python -m pip install pyboy`."
        )
    return PyBoy


class DebugSession:
    """Headless PyBoy session loaded with a pokegold ROM and its .sym table.

    Usage:
        with DebugSession.open("pokegold_debug") as sess:
            sess.tick(60)
            print(sess.regs.PC, sess.cur_bank)
    """

    def __init__(self, pyboy: Any, symbols: SymbolTable, rom_path: Path, sym_path: Path):
        self.pyboy = pyboy
        self.symbols = symbols
        self.rom_path = rom_path
        self.sym_path = sym_path

    @classmethod
    def open(cls, variant: str = "pokegold_debug") -> "DebugSession":
        rom_path = find_rom(variant)
        sym_path = find_sym(variant)
        PyBoy = _load_pyboy_class()
        try:
            pyboy = PyBoy(
                str(rom_path),
                window="null",
                sound=False,
                log_level="ERROR",
                symbols=str(sym_path),
            )
        except TypeError:
            pyboy = PyBoy(str(rom_path), window="null", sound=False)
        set_speed = getattr(pyboy, "set_emulation_speed", None)
        if set_speed is not None:
            set_speed(0)
        symbols = SymbolTable.load(sym_path)
        return cls(pyboy, symbols, rom_path, sym_path)

    def __enter__(self) -> "DebugSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        stop = getattr(self.pyboy, "stop", None)
        if stop is not None:
            try:
                stop(save=False)
            except TypeError:
                stop()

    # --- Frame advance ---
    def tick(self, frames: int = 1, render: bool = False) -> None:
        self.pyboy.tick(frames, render)

    # --- Registers ---
    @property
    def regs(self):
        return self.pyboy.register_file

    def regs_snapshot(self) -> dict[str, int]:
        rf = self.pyboy.register_file
        f = int(rf.F)
        return {
            "A": int(rf.A), "F": f,
            "B": int(rf.B), "C": int(rf.C),
            "D": int(rf.D), "E": int(rf.E),
            "HL": int(rf.HL),
            "SP": int(rf.SP),
            "PC": int(rf.PC),
            "Z": (f >> 7) & 1,
            "N": (f >> 6) & 1,
            "H": (f >> 5) & 1,
            "Cf": (f >> 4) & 1,
        }

    # --- Memory ---
    @property
    def mem(self):
        return self.pyboy.memory

    @property
    def cur_bank(self) -> int:
        # hROMBank shadow at $FFB8 in this codebase (verify via sym).
        sym = self.symbols.get("hROMBank")
        if sym is not None:
            return int(self.pyboy.memory[sym.address])
        return int(self.pyboy.memory[0xFFB8])

    def read_bytes(self, bank: int | None, addr: int, size: int) -> list[int]:
        if bank is None or addr < 0x4000:
            return [int(self.pyboy.memory[addr + i]) for i in range(size)]
        return [int(self.pyboy.memory[bank, addr + i]) for i in range(size)]

    def read_u16_le(self, addr: int) -> int:
        return int(self.pyboy.memory[addr]) | (int(self.pyboy.memory[addr + 1]) << 8)

    def read_u16_be(self, addr: int) -> int:
        return (int(self.pyboy.memory[addr]) << 8) | int(self.pyboy.memory[addr + 1])

    # --- Symbol/PC rendering ---
    def render_pc(self) -> str:
        rf = self.pyboy.register_file
        pc = int(rf.PC)
        bank = self.cur_bank if pc >= 0x4000 else 0
        return f"${bank:02x}:{pc:04x} ({self.symbols.render(bank, pc)})"

    def lookup(self, name: str) -> Symbol:
        return self.symbols[name]

    # --- Hooks ---
    def hook_register(self, bank: int | None, addr_or_name: int | str, callback: Callable, ctx=None) -> None:
        if isinstance(addr_or_name, str):
            sym = self.symbols[addr_or_name]
            bank, addr = sym.bank, sym.address
        else:
            addr = addr_or_name
        self.pyboy.hook_register(bank, addr, callback, ctx)

    def hook_deregister(self, bank: int | None, addr_or_name: int | str) -> None:
        if isinstance(addr_or_name, str):
            sym = self.symbols[addr_or_name]
            bank, addr = sym.bank, sym.address
        else:
            addr = addr_or_name
        self.pyboy.hook_deregister(bank, addr)

    @contextmanager
    def hooked(self, bank: int | None, addr_or_name: int | str, callback: Callable, ctx=None) -> Iterator[None]:
        self.hook_register(bank, addr_or_name, callback, ctx)
        try:
            yield
        finally:
            try:
                self.hook_deregister(bank, addr_or_name)
            except Exception:
                pass

    # --- Save state ---
    def save_state(self, path: Path) -> None:
        with open(path, "wb") as fh:
            self.pyboy.save_state(fh)

    def load_state(self, path: Path) -> None:
        with open(path, "rb") as fh:
            self.pyboy.load_state(fh)
