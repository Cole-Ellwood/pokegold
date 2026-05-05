"""Boot ROM with battery save, drive Title-Screen→Continue, save state at
post-load.

Approach: copy the boss factory's exact button-input pattern (180-frame
waits in BOOT phase). Capture state when wPartyCount > 0 (game loaded).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from pyboy import PyBoy

ROOT = Path("C:/Users/lolno/Downloads/pokemon gold hack")
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "boot_continue.log"
STATE_OUT = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "post_continue.state"


def parse_sym(p):
    out = {}
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.split(";", 1)[0].strip()
        parts = s.split()
        if len(parts) < 2 or ":" not in parts[0]: continue
        try:
            b, a = parts[0].split(":", 1)
            out[parts[1]] = (int(b, 16), int(a, 16))
        except ValueError: continue
    return out


def read_byte(pyboy, addr, bank=0):
    if 0xD000 <= addr <= 0xDFFF and bank:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = bank
        try: return int(pyboy.memory[addr])
        finally: pyboy.memory[0xFF70] = old
    return int(pyboy.memory[addr])


def main(rom_name: str = "pokegold_debug.gbc",
         sym_name: str = "pokegold_debug.sym") -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    def log(msg):
        sys.stdout.write(msg + "\n"); sys.stdout.flush()
        fh.write(msg + "\n"); fh.flush()

    rom = ROOT / rom_name
    sav = rom.with_suffix(".sav")
    sym = ROOT / sym_name
    log(f"rom: {rom.name} (exists={rom.exists()})")
    log(f"sav: {sav.name} (exists={sav.exists()})")

    syms = parse_sym(sym)
    party_count_sym = syms.get("wPartyCount")
    party_mon1_lvl_sym = syms.get("wPartyMon1Level")
    map_group_sym = syms.get("wMapGroup")
    map_num_sym = syms.get("wMapNumber")

    ram_fh = open(sav, "rb") if sav.exists() else None
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR",
                  ram_file=ram_fh)
    pyboy.set_emulation_speed(0)

    log("Phase 1: boot 1800 frames")
    pyboy.tick(1800, False, False)
    pc = int(pyboy.register_file.PC)
    log(f"  PC=${pc:04x}")

    log("Phase 2: title-screen sequence (start, a, a, a) with 180-frame wait")
    for btn in ("start", "a", "a", "a"):
        pyboy.button(btn, 8)
        pyboy.tick(180, False, False)
        pc = int(pyboy.register_file.PC)
        if party_count_sym:
            pc_val = read_byte(pyboy, party_count_sym[1], party_count_sym[0])
            log(f"  after {btn}: PC=${pc:04x} wPartyCount={pc_val}")
        else:
            log(f"  after {btn}: PC=${pc:04x}")

    log("Phase 3: post-load A spam (clear dialogs)")
    last_party_count = 0
    for round_no in range(40):
        pyboy.button("a", 8)
        pyboy.tick(45, False, False)
        if party_count_sym:
            pc_val = read_byte(pyboy, party_count_sym[1], party_count_sym[0])
            if pc_val != last_party_count:
                log(f"  round {round_no}: wPartyCount={pc_val} (changed!)")
                last_party_count = pc_val
            if pc_val > 0 and pc_val < 7:
                # Loaded successfully; check if we're stable at overworld
                if map_group_sym and map_num_sym:
                    mg = read_byte(pyboy, map_group_sym[1], map_group_sym[0])
                    mn = read_byte(pyboy, map_num_sym[1], map_num_sym[0])
                    if mg > 0 and mn > 0 and mg < 30 and mn < 60:
                        log(f"  player at map={mg}.{mn}, party_count={pc_val}; saving state")
                        with open(STATE_OUT, "wb") as state_fh:
                            pyboy.save_state(state_fh)
                        log(f"  state saved -> {STATE_OUT}")
                        break

    # Final state inspection
    if party_count_sym:
        pc_val = read_byte(pyboy, party_count_sym[1], party_count_sym[0])
        log(f"\nfinal wPartyCount = {pc_val}")
    if party_mon1_lvl_sym:
        pml = read_byte(pyboy, party_mon1_lvl_sym[1], party_mon1_lvl_sym[0])
        log(f"final wPartyMon1Level = {pml}")
    if map_group_sym:
        mg = read_byte(pyboy, map_group_sym[1], map_group_sym[0])
        mn = read_byte(pyboy, map_num_sym[1], map_num_sym[0])
        log(f"final map = {mg}.{mn}")

    pyboy.stop(save=False)
    if ram_fh: ram_fh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
