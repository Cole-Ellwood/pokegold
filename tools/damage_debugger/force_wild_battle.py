"""From post_continue.state, force a wild Pidgey lvl-2 battle by
calling StartBattle directly with WRAM seeded for wild encounter.

StartBattle reads:
- wPartyCount > 0 (have a Pokemon)
- wOtherTrainerClass == 0 (wild)
- wTempWildMonSpecies (the wild mon)
- wCurPartyLevel (level for stat compute)
- wTimeOfDayPal (palette setup)

After invoking, the engine runs through battle intro, AI move pick,
DoBattle. Our hook on BattleCommand_DamageCalc fires when damage is
computed. We then capture register state.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from pyboy import PyBoy

ROOT = Path("C:/Users/lolno/Downloads/pokemon gold hack")
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "force_wild_battle.log"
STATE_IN = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "post_continue.state"


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


def write_byte(pyboy, name, syms, value):
    s = syms.get(name)
    if s is None: return False
    if 0xD000 <= s[1] <= 0xDFFF and s[0]:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = s[0]
        try: pyboy.memory[s[1]] = value & 0xFF
        finally: pyboy.memory[0xFF70] = old
    else:
        pyboy.memory[s[1]] = value & 0xFF
    return True


def read_byte(pyboy, addr, bank=0):
    if 0xD000 <= addr <= 0xDFFF and bank:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = bank
        try: return int(pyboy.memory[addr])
        finally: pyboy.memory[0xFF70] = old
    return int(pyboy.memory[addr])


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
        log(f"FAIL: {STATE_IN} missing")
        return 1

    ram_fh = open(sav, "rb") if sav.exists() else None
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR",
                  ram_file=ram_fh)
    pyboy.set_emulation_speed(0)
    with open(STATE_IN, "rb") as f:
        pyboy.load_state(f)
    log(f"loaded {STATE_IN.name}")

    # Hook DamageCalc + DamageStats
    dc = syms["BattleCommand_DamageCalc"]
    ds = syms.get("BattleCommand_DamageStats")
    log(f"DamageCalc @ ${dc[0]:02x}:{dc[1]:04x}")

    hits_dc = []
    def cb_dc(_):
        rf = pyboy.register_file
        snap = {"A": int(rf.A), "B": int(rf.B), "C": int(rf.C),
                "D": int(rf.D), "E": int(rf.E), "HL": int(rf.HL),
                "PC": int(rf.PC)}
        hits_dc.append(snap)
        log(f"  *** DamageCalc HIT #{len(hits_dc)}: d={snap['D']}(0x{snap['D']:02x}) "
            f"e={snap['E']} b={snap['B']} c={snap['C']}")
    pyboy.hook_register(dc[0], dc[1], cb_dc, None)

    # Seed the WRAM for a wild Pidgey lvl 2 battle
    log("seeding WRAM: wild Pidgey lvl 2 (PIDGEY=16)")
    write_byte(pyboy, "wOtherTrainerClass", syms, 0)
    write_byte(pyboy, "wTempWildMonSpecies", syms, 16)  # PIDGEY
    write_byte(pyboy, "wCurPartyLevel", syms, 2)
    write_byte(pyboy, "wBattleType", syms, 0)            # BATTLETYPE_NORMAL
    write_byte(pyboy, "wBattleMode", syms, 1)            # WILD_BATTLE

    # Push sentinel return + set PC = StartBattle
    sb = syms["StartBattle"]
    rf = pyboy.register_file
    sentinel = 0x0008
    sp = int(rf.SP)
    new_sp = (sp - 2) & 0xFFFF
    pyboy.memory[new_sp] = sentinel & 0xFF
    pyboy.memory[new_sp + 1] = (sentinel >> 8) & 0xFF
    rf.SP = new_sp
    rf.PC = sb[1]
    pyboy.memory[syms["hROMBank"][1]] = sb[0]
    pyboy.memory[0x2000] = sb[0]

    log(f"calling StartBattle @ ${sb[0]:02x}:{sb[1]:04x}")

    t0 = time.time()
    BUDGET = 60000  # plenty for a battle to complete
    ticked = 0
    while ticked < BUDGET and len(hits_dc) < 3:
        pyboy.tick(180, False, False)
        ticked += 180
        # Press A periodically to advance battle dialogs
        pyboy.button("a", 6)
        if ticked % 1800 == 0:
            log(f"  t={time.time()-t0:.1f}s ticked={ticked} hits={len(hits_dc)} "
                f"PC=${int(pyboy.register_file.PC):04x}")

    log(f"\n=== final t={time.time()-t0:.1f}s ticked={ticked} ===")
    log(f"DamageCalc hits: {len(hits_dc)}")
    if hits_dc:
        for i, h in enumerate(hits_dc[:10]):
            log(f"  #{i+1}: d={h['D']:3d}(0x{h['D']:02x}) e={h['E']:3d} b={h['B']:3d} c={h['C']:3d}")
        # Compute oracle damage with the captured inputs
        h = hits_dc[0]
        if h['B'] > 0 and h['C'] > 0 and h['D'] > 0 and h['E'] > 0:
            inner = (2 * h['E']) // 5 + 2
            oracle = ((inner * h['B'] * h['D']) // h['C']) // 50 + 2
            log(f"\nOracle base (no STAB/type/crit/random): {oracle}")
            log(f"  Pidgey-Tackle-vs-Cyndaquil expected: 3")
            if oracle != 3:
                log(f"  ANOMALY: inputs differ from expected. d/b/c/e are wrong.")

    pyboy.stop(save=False)
    if ram_fh: ram_fh.close()
    return 0 if hits_dc else 2


if __name__ == "__main__":
    sys.exit(main())
