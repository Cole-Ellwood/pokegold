"""M1 acceptance test: load pokegold_debug.gbc, advance 60 frames, print PC + bank."""

from __future__ import annotations

LEGACY_EXIT = (
    "tools.damage_debugger.legacy scripts are pruned one-shot drivers; "
    "use active tools.damage_debugger modules instead."
)
raise SystemExit(LEGACY_EXIT)

import sys
import time

from .emulator import DebugSession


def main() -> int:
    t0 = time.time()
    with DebugSession.open("pokegold_debug") as sess:
        load_t = time.time() - t0
        sess.tick(60)
        tick_t = time.time() - t0 - load_t
        regs = sess.regs_snapshot()
        bank = sess.cur_bank
        print(f"ROM:    {sess.rom_path}")
        print(f"SYM:    {sess.sym_path}")
        print(f"Load:   {load_t*1000:.1f} ms")
        print(f"60-tick:{tick_t*1000:.1f} ms")
        print(f"PC:     ${bank:02x}:{regs['PC']:04x} ({sess.symbols.render(bank, regs['PC'])})")
        print(f"Bank:   ${bank:02x}")
        print(f"Regs:   A={regs['A']:02x} F={regs['F']:02x} BC={regs['B']:02x}{regs['C']:02x} "
              f"DE={regs['D']:02x}{regs['E']:02x} HL={regs['HL']:04x} SP={regs['SP']:04x}")
    total = time.time() - t0
    print(f"Total:  {total*1000:.1f} ms")
    if total > 5.0:
        print("WARN: M1 acceptance threshold (<5s) exceeded.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
