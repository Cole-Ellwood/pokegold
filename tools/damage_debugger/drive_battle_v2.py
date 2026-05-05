"""From the post_continue.state, drive into a battle and capture
DamageCalc register state.

Strategy: load post-Continue state. Press A, then directional keys, then
A to advance through dialog. The user's save is in a Trainer House
where pressing A on the right NPC triggers a battle.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from pyboy import PyBoy

ROOT = Path("C:/Users/lolno/Downloads/pokemon gold hack")
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "drive_battle_v2.log"
STATE_IN = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "post_continue.state"
DAMAGE_STATE_OUT = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "first_damage.state"


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


def read_be_u16(pyboy, addr, bank=0):
    if 0xD000 <= addr <= 0xDFFF and bank:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = bank
        try:
            hi = int(pyboy.memory[addr]); lo = int(pyboy.memory[addr+1])
        finally: pyboy.memory[0xFF70] = old
    else:
        hi = int(pyboy.memory[addr]); lo = int(pyboy.memory[addr+1])
    return (hi << 8) | lo


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    def log(msg):
        sys.stdout.write(msg + "\n"); sys.stdout.flush()
        fh.write(msg + "\n"); fh.flush()

    rom = ROOT / "pokegold_debug.gbc"
    sym = ROOT / "pokegold_debug.sym"
    syms = parse_sym(sym)
    sav = rom.with_suffix(".sav")

    if not STATE_IN.exists():
        log(f"FAIL: post_continue state missing at {STATE_IN}")
        log("  Run boot_continue.py first")
        return 1

    ram_fh = open(sav, "rb") if sav.exists() else None
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR",
                  ram_file=ram_fh)
    pyboy.set_emulation_speed(0)
    with open(STATE_IN, "rb") as state_fh:
        pyboy.load_state(state_fh)
    log(f"loaded {STATE_IN.name}")

    # Read initial state
    party_count = read_byte(pyboy, syms["wPartyCount"][1], syms["wPartyCount"][0])
    map_group = read_byte(pyboy, syms["wMapGroup"][1], syms["wMapGroup"][0])
    map_num = read_byte(pyboy, syms["wMapNumber"][1], syms["wMapNumber"][0])
    x = read_byte(pyboy, syms["wXCoord"][1], syms["wXCoord"][0])
    y = read_byte(pyboy, syms["wYCoord"][1], syms["wYCoord"][0])
    log(f"start: party={party_count} map={map_group}.{map_num} pos=({x},{y})")

    # Hook DamageCalc to capture
    dc = syms["BattleCommand_DamageCalc"]
    ds = syms.get("BattleCommand_DamageStats")
    log(f"DamageCalc @ ${dc[0]:02x}:{dc[1]:04x}")

    hits_dc = []
    hits_ds = []
    state_saved = [False]

    def cb_dc(_):
        rf = pyboy.register_file
        snap = {"label": "DC",
                "A": int(rf.A), "B": int(rf.B), "C": int(rf.C),
                "D": int(rf.D), "E": int(rf.E),
                "HL": int(rf.HL), "PC": int(rf.PC)}
        hits_dc.append(snap)
        log(f"  *** DamageCalc HIT #{len(hits_dc)}: d={snap['D']}(0x{snap['D']:02x}) "
            f"e={snap['E']} b={snap['B']} c={snap['C']} hl=0x{snap['HL']:04x}")
        if not state_saved[0]:
            state_saved[0] = True
            with open(DAMAGE_STATE_OUT, "wb") as fh:
                pyboy.save_state(fh)
            log(f"  state saved -> {DAMAGE_STATE_OUT}")
            # Read battle context too
            for name in ("wEnemyMonSpecies", "wEnemyMonLevel",
                         "wEnemyMoveStructPower", "wPlayerMoveStructPower",
                         "wCurEnemyMove", "wCurPlayerMove"):
                s = syms.get(name)
                if s:
                    log(f"    {name} = {read_byte(pyboy, s[1], s[0])}")
            for name in ("wEnemyMonAttack", "wEnemyMonDefense",
                         "wBattleMonAttack", "wBattleMonDefense"):
                s = syms.get(name)
                if s:
                    log(f"    {name} = {read_be_u16(pyboy, s[1], s[0])}")

    def cb_ds(_):
        rf = pyboy.register_file
        snap = {"label": "DS", "PC": int(rf.PC)}
        hits_ds.append(snap)

    pyboy.hook_register(dc[0], dc[1], cb_dc, None)
    if ds:
        pyboy.hook_register(ds[0], ds[1], cb_ds, None)

    # Aggressive drive: lots of A presses, occasional movement
    log("\nPhase 1: A spam to advance through dialog (300 presses)")
    t0 = time.time()
    drive = ["a"] * 60 + ["down"] * 4 + ["right"] * 4 + ["a"] * 50
    for round_no in range(8):
        for btn in drive:
            if hits_dc: break
            pyboy.button(btn, 6)
            pyboy.tick(45, False, False)
        if hits_dc: break
        x = read_byte(pyboy, syms["wXCoord"][1], syms["wXCoord"][0])
        y = read_byte(pyboy, syms["wYCoord"][1], syms["wYCoord"][0])
        bm = read_byte(pyboy, syms["wBattleMode"][1], syms["wBattleMode"][0])
        log(f"  round {round_no+1}: t={time.time()-t0:.1f}s pos=({x},{y}) battle_mode={bm} ds_hits={len(hits_ds)}")

    log(f"\n=== summary t={time.time()-t0:.1f}s ===")
    log(f"DamageCalc hits: {len(hits_dc)}")
    log(f"DamageStats hits: {len(hits_ds)}")
    if hits_dc:
        from collections import Counter
        c = Counter(h["D"] for h in hits_dc)
        log(f"\nd-distribution: {dict(c)}")
        for h in hits_dc[:10]:
            log(f"  d={h['D']:3d} (0x{h['D']:02x}) e={h['E']:3d} b={h['B']:3d} c={h['C']:3d}")
        # Compute damage with these inputs (max-roll, no STAB, neutral)
        h = hits_dc[0]
        if h['B'] and h['C'] and h['D'] and h['E']:
            inner = (2 * h['E']) // 5 + 2
            dmg = ((inner * h['B'] * h['D']) // h['C']) // 50 + 2
            log(f"\noracle base damage with d/b/c/e: {dmg}")

    pyboy.stop(save=False)
    if ram_fh: ram_fh.close()
    return 0 if hits_dc else 2


if __name__ == "__main__":
    sys.exit(main())
