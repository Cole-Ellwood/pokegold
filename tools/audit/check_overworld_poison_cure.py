#!/usr/bin/env python3
"""Runtime audit for overworld poison's 1-HP cure boundary."""

from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pyboy import PyBoy  # type: ignore  # noqa: E402

from tools.damage_debugger.safe_call import (  # noqa: E402
    call_function_safe,
    read_be_u16_banked,
    read_byte_banked,
    write_byte_banked,
)


PSN_MASK = 1 << 3
SAFE_STACK = 0xDFF0


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_sym(path: Path) -> dict[str, tuple[int, int]]:
    if not path.exists():
        fail(f"missing symbol file: {path}")
    out: dict[str, tuple[int, int]] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = raw.split()
        if len(parts) != 2 or ":" not in parts[0]:
            continue
        bank_text, address_text = parts[0].split(":", 1)
        try:
            out[parts[1]] = (int(bank_text, 16), int(address_text, 16))
        except ValueError:
            continue
    return out


def require_symbol(symbols: dict[str, tuple[int, int]], name: str) -> tuple[int, int]:
    if name not in symbols:
        fail(f"missing symbol: {name}")
    return symbols[name]


def write_byte(pyboy: PyBoy, symbols: dict[str, tuple[int, int]], name: str, value: int) -> None:
    bank, address = require_symbol(symbols, name)
    write_byte_banked(pyboy, address, value, bank)


def write_u16_be(pyboy: PyBoy, symbols: dict[str, tuple[int, int]], name: str, value: int) -> None:
    bank, address = require_symbol(symbols, name)
    write_byte_banked(pyboy, address, (value >> 8) & 0xFF, bank)
    write_byte_banked(pyboy, address + 1, value & 0xFF, bank)


def read_byte(pyboy: PyBoy, symbols: dict[str, tuple[int, int]], name: str) -> int:
    bank, address = require_symbol(symbols, name)
    return read_byte_banked(pyboy, address, bank)


def read_u16_be(pyboy: PyBoy, symbols: dict[str, tuple[int, int]], name: str) -> int:
    bank, address = require_symbol(symbols, name)
    return read_be_u16_banked(pyboy, address, bank)


def run_case(symbols: dict[str, tuple[int, int]], start_hp: int, expected_hp: int, expected_status: int) -> None:
    pyboy = PyBoy(str(ROOT / "pokegold.gbc"), window="null", sound=False, log_level="ERROR")
    try:
        disable_realtime(pyboy)
        pyboy.tick(60, False, False)
        pyboy.register_file.SP = SAFE_STACK

        write_byte(pyboy, symbols, "wCurPartyMon", 0)
        write_byte(pyboy, symbols, "wPartyMon1Status", PSN_MASK)
        write_u16_be(pyboy, symbols, "wPartyMon1HP", start_hp)

        ticks, returned, pc = call_function_safe(
            pyboy,
            symbols,
            "DoPoisonStep.DamageMonIfPoisoned",
            budget=20_000,
        )
        if not returned:
            fail(f"start HP {start_hp}: poison damage helper did not return; pc=${pc:04x}, ticks={ticks}")

        actual_hp = read_u16_be(pyboy, symbols, "wPartyMon1HP")
        actual_status = read_byte(pyboy, symbols, "wPartyMon1Status")
        actual_flag = int(pyboy.register_file.C)
        carry_set = bool(int(pyboy.register_file.F) & 0x10)

        if actual_hp != expected_hp:
            fail(f"start HP {start_hp}: expected HP {expected_hp}, got {actual_hp}")
        if actual_status != expected_status:
            fail(f"start HP {start_hp}: expected status ${expected_status:02x}, got ${actual_status:02x}")
        if actual_flag != 1 or not carry_set:
            fail(f"start HP {start_hp}: expected poison-damage return flag %%01 with carry")
    finally:
        pyboy.stop(save=False)


def disable_realtime(pyboy: PyBoy) -> None:
    set_speed = getattr(pyboy, "set_emulation_speed", None)
    if set_speed is not None:
        set_speed(0)


def main() -> int:
    warnings.filterwarnings("ignore", message="Using SDL2 binaries.*")
    logging.disable(logging.WARNING)

    if not (ROOT / "pokegold.gbc").exists():
        fail("missing built ROM: pokegold.gbc")
    symbols = parse_sym(ROOT / "pokegold.sym")

    run_case(symbols, start_hp=1, expected_hp=1, expected_status=0)
    run_case(symbols, start_hp=2, expected_hp=1, expected_status=0)
    run_case(symbols, start_hp=3, expected_hp=2, expected_status=PSN_MASK)

    print("Overworld poison cure runtime audit passed.")
    print("Verified 1 HP cures without fainting, 2 HP ticks to cured 1 HP, and 3 HP remains poisoned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
