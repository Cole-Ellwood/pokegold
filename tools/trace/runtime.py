from __future__ import annotations

import hashlib
import logging
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Symbol:
    bank: int
    address: int


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(resolved)


def sha256_file(path: Path) -> str:
    if not path.exists():
        fail(f"missing file for SHA256: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def parse_symbols(path: Path) -> dict[str, Symbol]:
    if not path.exists():
        fail(f"missing symbol file: {path}")
    out: dict[str, Symbol] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = raw.split()
        if len(parts) != 2 or ":" not in parts[0]:
            continue
        bank_s, addr_s = parts[0].split(":", 1)
        try:
            out[parts[1]] = Symbol(int(bank_s, 16), int(addr_s, 16))
        except ValueError:
            continue
    return out


def read_byte(pyboy, symbol: Symbol) -> int:
    if 0xD000 <= symbol.address <= 0xDFFF and symbol.bank:
        try:
            return int(pyboy.memory[symbol.bank, symbol.address])
        except Exception:
            old_bank = int(pyboy.memory[0xFF70])
            pyboy.memory[0xFF70] = symbol.bank
            try:
                return int(pyboy.memory[symbol.address])
            finally:
                pyboy.memory[0xFF70] = old_bank
    return int(pyboy.memory[symbol.address])


def read_addr(pyboy, bank: int, address: int) -> int:
    return read_byte(pyboy, Symbol(bank, address))


def read_range(pyboy, symbol: Symbol, size: int) -> list[int]:
    return [
        read_byte(pyboy, Symbol(symbol.bank, symbol.address + offset))
        for offset in range(size)
    ]


def read_word(pyboy, symbol: Symbol) -> int:
    return (read_byte(pyboy, symbol) << 8) | read_addr(
        pyboy,
        symbol.bank,
        symbol.address + 1,
    )


def load_pyboy(import_error_message: str):
    local_pydeps = ROOT / ".local" / "pydeps"
    if local_pydeps.exists() and str(local_pydeps) not in sys.path:
        sys.path.insert(0, str(local_pydeps))
    warnings.filterwarnings("ignore", message="Using SDL2 binaries.*")
    try:
        from pyboy import PyBoy  # type: ignore
    except Exception as exc:
        fail(f"{import_error_message}: {exc}")
    return PyBoy


def open_pyboy(rom: Path, import_error_message: str):
    if not rom.exists():
        fail(f"missing ROM: {rom}")

    logging.disable(logging.WARNING)
    PyBoy = load_pyboy(import_error_message)
    try:
        return PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    except TypeError:
        return PyBoy(str(rom), window="null", sound=False)


def disable_realtime(pyboy) -> None:
    set_speed = getattr(pyboy, "set_emulation_speed", None)
    if set_speed is not None:
        set_speed(0)
