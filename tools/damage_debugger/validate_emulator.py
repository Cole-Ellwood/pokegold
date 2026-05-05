"""M2: validate the PyBoy SM83 core via Blargg cpu_instrs.gb.

Drop the public-domain ``cpu_instrs.gb`` (or per-subtest ROMs like
``01-special.gb``) into ``tools/damage_debugger/blargg/`` and run::

    python -m tools.damage_debugger.validate_emulator

Blargg ROMs print PASS/FAIL via the link-cable serial port ($FF01/$FF02).
We hook the serial-control register, accumulate a transcript, and look
for the literal substring "Passed". A subtest that prints "Failed" or
hangs past the cycle budget fails the harness.

Without a Blargg ROM the harness exits with status 2 (DEFERRED, not
failure) so the loop can proceed past M2; the risk noted in
research.md caveat 1 is then accepted with eyes open and the
divergence detector at M8 is the practical fallback.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .emulator import _load_pyboy_class

BLARGG_DIR = Path(__file__).resolve().parent / "blargg"
TARGETS = (
    "cpu_instrs.gb",
    "01-special.gb",
    "02-interrupts.gb",
    "03-op sp,hl.gb",
    "04-op r,imm.gb",
    "05-op rp.gb",
    "06-ld r,r.gb",
    "07-jr,jp,call,ret,rst.gb",
    "08-misc instrs.gb",
    "09-op r,r.gb",
    "10-bit ops.gb",
    "11-op a,(hl).gb",
)
CYCLE_BUDGET = 60_000_000  # ~14s of GB time at 4.19 MHz
TICKS_PER_BATCH = 1024


def find_blargg_roms() -> list[Path]:
    if not BLARGG_DIR.exists():
        return []
    return [p for p in (BLARGG_DIR / name for name in TARGETS) if p.exists()]


def run_one(rom: Path, *, verbose: bool = False) -> tuple[bool, str]:
    PyBoy = _load_pyboy_class()
    try:
        pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    except TypeError:
        pyboy = PyBoy(str(rom), window="null", sound=False)
    set_speed = getattr(pyboy, "set_emulation_speed", None)
    if set_speed is not None:
        set_speed(0)

    transcript: list[int] = []

    # Blargg writes a byte to $FF01, then writes $81 to $FF02 to "send."
    # Hook the SC ($FF02) write at the BIOS handler is too hardware-specific;
    # the simpler approach is to poll $FF01 between batches. Even simpler:
    # hook a write breakpoint by replacing the write with a watcher tick.
    # PyBoy's API is per-PC, not per-MMIO, so we poll.
    last_sc = 0
    elapsed = 0
    try:
        while elapsed < CYCLE_BUDGET:
            pyboy.tick(TICKS_PER_BATCH, False)
            elapsed += TICKS_PER_BATCH * 70224  # cycles per frame approx
            sc = int(pyboy.memory[0xFF02])
            if sc & 0x80 and sc != last_sc:
                ch = int(pyboy.memory[0xFF01])
                transcript.append(ch)
                pyboy.memory[0xFF02] = sc & 0x7F
            last_sc = sc
            text = bytes(transcript).decode("ascii", errors="replace")
            if "Passed" in text or "Failed" in text:
                break
            if verbose and len(transcript) and len(transcript) % 32 == 0:
                print(f"  ... {text[-64:]!r}", file=sys.stderr)
    finally:
        stop = getattr(pyboy, "stop", None)
        if stop is not None:
            try:
                stop(save=False)
            except TypeError:
                stop()

    text = bytes(transcript).decode("ascii", errors="replace")
    return ("Passed" in text and "Failed" not in text), text


def main() -> int:
    roms = find_blargg_roms()
    if not roms:
        print("DEFERRED: no Blargg ROMs found.")
        print(f"  Looked in: {BLARGG_DIR}")
        print("  Drop cpu_instrs.gb (or per-subtest .gb files) there and re-run.")
        print("  PyBoy 2.7.0's SM83 core is widely used and accepted as-is for v1;")
        print("  the M8 divergence detector serves as the practical fallback if a")
        print("  PyBoy arithmetic bug ever surfaces.")
        return 2

    overall_pass = True
    for rom in roms:
        print(f"[blargg] {rom.name}")
        ok, transcript = run_one(rom, verbose=False)
        status = "PASS" if ok else "FAIL"
        print(f"  {status}: {transcript.strip()!r}")
        if not ok:
            overall_pass = False
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
