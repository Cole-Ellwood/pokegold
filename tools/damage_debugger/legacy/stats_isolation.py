"""Test BattleCommand_DamageStats in isolation.

DamageStats is the function that fills b/c/d/e (the args DamageCalc
expects). It reads:
- wEnemyMoveStructPower (=40 for Tackle)
- wEnemyMonAttack (=6 for lvl 2 Pidgey)
- wBattleMonDefense (=9 for lvl 5 Cyndaquil)
- wEnemyMonLevel (=2)
And after running should leave:
- b = 6 (attacker's atk truncated)
- c = 9 (defender's def truncated)
- d = 40 (move BP)
- e = 2 (attacker's level)

If d != 40 after this call, we've found the BP-clobber site.
If b/c are wrong, that's a stat-stage / item-mod / Ditto bug.
"""

from __future__ import annotations

LEGACY_EXIT = (
    "tools.damage_debugger.legacy scripts are pruned one-shot drivers; "
    "use active tools.damage_debugger modules instead."
)
raise SystemExit(LEGACY_EXIT)

import sys
from pathlib import Path

from pyboy import PyBoy

ROOT = Path("C:/Users/lolno/Downloads/pokemon gold hack")
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "stats_iso.log"


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
    if s is None: return
    if 0xD000 <= s[1] <= 0xDFFF and s[0]:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = s[0]
        try: pyboy.memory[s[1]] = value & 0xFF
        finally: pyboy.memory[0xFF70] = old
    else:
        pyboy.memory[s[1]] = value & 0xFF


def write_be_u16(pyboy, name, syms, value):
    s = syms.get(name)
    if s is None: return
    hi, lo = (value >> 8) & 0xFF, value & 0xFF
    if 0xD000 <= s[1] <= 0xDFFF and s[0]:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = s[0]
        try:
            pyboy.memory[s[1]] = hi
            pyboy.memory[s[1]+1] = lo
        finally: pyboy.memory[0xFF70] = old
    else:
        pyboy.memory[s[1]] = hi
        pyboy.memory[s[1]+1] = lo


def call_function(pyboy, name, syms, budget=2400):
    s = syms[name]
    rf = pyboy.register_file
    sentinel = 0x0008
    sp = int(rf.SP)
    new_sp = (sp - 2) & 0xFFFF
    pyboy.memory[new_sp] = sentinel & 0xFF
    pyboy.memory[new_sp + 1] = (sentinel >> 8) & 0xFF
    rf.SP = new_sp
    rf.PC = s[1]
    if syms.get("hROMBank"):
        pyboy.memory[syms["hROMBank"][1]] = s[0]
    pyboy.memory[0x2000] = s[0]
    returned = [False]
    def cb(_): returned[0] = True
    pyboy.hook_register(0, sentinel, cb, None)
    ticked = 0
    while ticked < budget and not returned[0]:
        pyboy.tick(2, False, False)
        ticked += 2
    pyboy.hook_deregister(0, sentinel)
    return ticked, returned[0]


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    def log(msg):
        sys.stdout.write(msg + "\n"); sys.stdout.flush()
        fh.write(msg + "\n"); fh.flush()

    rom = ROOT / "pokegold_trace.gbc"
    sym = ROOT / "pokegold_trace.sym"
    syms = parse_sym(sym)

    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    pyboy.set_emulation_speed(0)
    pyboy.tick(240, False, False)

    # === SEED for "lvl 2 Pidgey Tackle vs lvl 5 Cyndaquil" ===
    write_byte(pyboy, "wEnemyMonSpecies", syms, 16)            # PIDGEY
    write_byte(pyboy, "wEnemyMonLevel", syms, 2)
    write_byte(pyboy, "wEnemyMonType1", syms, 0x00)            # NORMAL
    write_byte(pyboy, "wEnemyMonType2", syms, 0x02)            # FLYING
    write_byte(pyboy, "wEnemyMonItem", syms, 0)
    write_be_u16(pyboy, "wEnemyMonHP", syms, 12)
    write_be_u16(pyboy, "wEnemyMonAttack", syms, 6)            # lvl 2 Pidgey atk
    write_be_u16(pyboy, "wEnemyMonDefense", syms, 6)
    write_be_u16(pyboy, "wEnemyMonSpeed", syms, 7)
    write_be_u16(pyboy, "wEnemyMonSpclAtk", syms, 5)
    write_be_u16(pyboy, "wEnemyMonSpclDef", syms, 5)
    write_be_u16(pyboy, "wEnemyAttack", syms, 6)
    write_be_u16(pyboy, "wEnemyDefense", syms, 6)
    write_be_u16(pyboy, "wEnemySpAtk", syms, 5)
    write_be_u16(pyboy, "wEnemySpDef", syms, 5)
    write_byte(pyboy, "wEnemyAtkLevel", syms, 7)
    write_byte(pyboy, "wEnemyDefLevel", syms, 7)
    write_byte(pyboy, "wEnemySpdLevel", syms, 7)
    write_byte(pyboy, "wEnemySAtkLevel", syms, 7)
    write_byte(pyboy, "wEnemySDefLevel", syms, 7)

    write_byte(pyboy, "wBattleMonSpecies", syms, 155)          # CYNDAQUIL
    write_byte(pyboy, "wBattleMonLevel", syms, 5)
    write_byte(pyboy, "wBattleMonType1", syms, 0x14)
    write_byte(pyboy, "wBattleMonType2", syms, 0x14)
    write_byte(pyboy, "wBattleMonItem", syms, 0)
    write_be_u16(pyboy, "wBattleMonHP", syms, 18)
    write_be_u16(pyboy, "wBattleMonMaxHP", syms, 18)
    write_be_u16(pyboy, "wBattleMonAttack", syms, 10)
    write_be_u16(pyboy, "wBattleMonDefense", syms, 9)          # lvl 5 Cyndaquil def
    write_be_u16(pyboy, "wBattleMonSpeed", syms, 11)
    write_be_u16(pyboy, "wBattleMonSpclAtk", syms, 11)
    write_be_u16(pyboy, "wBattleMonSpclDef", syms, 10)
    write_be_u16(pyboy, "wPlayerAttack", syms, 10)
    write_be_u16(pyboy, "wPlayerDefense", syms, 9)
    write_be_u16(pyboy, "wPlayerSpAtk", syms, 11)
    write_be_u16(pyboy, "wPlayerSpDef", syms, 10)
    write_byte(pyboy, "wPlayerAtkLevel", syms, 7)
    write_byte(pyboy, "wPlayerDefLevel", syms, 7)
    write_byte(pyboy, "wPlayerSpdLevel", syms, 7)
    write_byte(pyboy, "wPlayerSAtkLevel", syms, 7)
    write_byte(pyboy, "wPlayerSDefLevel", syms, 7)

    # Tackle in wEnemyMoveStruct (since Pidgey attacks)
    move_sym = syms.get("wEnemyMoveStruct")
    b, a = move_sym
    for offset, val in [(0, 0x21), (1, 0x00), (2, 40), (3, 0x00), (4, 0xFF), (5, 35), (6, 0)]:
        if 0xD000 <= a + offset <= 0xDFFF and b:
            old = int(pyboy.memory[0xFF70])
            pyboy.memory[0xFF70] = b
            try: pyboy.memory[a+offset] = val
            finally: pyboy.memory[0xFF70] = old
        else:
            pyboy.memory[a+offset] = val

    # Battle state
    write_byte(pyboy, "wCriticalHit", syms, 0)
    write_byte(pyboy, "wEnemyScreens", syms, 0)
    write_byte(pyboy, "wPlayerScreens", syms, 0)
    write_byte(pyboy, "wIsConfusionDamage", syms, 0)
    write_byte(pyboy, "hBattleTurn", syms, 1)                 # enemy turn

    log("WRAM seeded; calling BattleCommand_DamageStats")
    log(f"  inputs: wEnemyMoveStructPower=40 wEnemyMonAttack=6 wBattleMonDefense=9 wEnemyMonLevel=2")
    log(f"  expected after: b=6 (atk truncated), c=9 (def truncated), d=40 (BP), e=2 (lvl)")

    ticks, ok = call_function(pyboy, "BattleCommand_DamageStats", syms)
    if not ok:
        log(f"FAIL: did not return within {ticks} ticks")
        pyboy.stop(save=False)
        return 1

    rf = pyboy.register_file
    log(f"\nAFTER DamageStats: b={int(rf.B):3d} c={int(rf.C):3d} d={int(rf.D):3d} e={int(rf.E):3d}  "
        f"hl={int(rf.HL):04x}  ticks={ticks}")

    expected = (6, 9, 40, 2)
    actual = (int(rf.B), int(rf.C), int(rf.D), int(rf.E))
    log(f"expected: b={expected[0]} c={expected[1]} d={expected[2]} e={expected[3]}")
    if actual == expected:
        log("\n*** MATCH — DamageStats correct in isolation ***")
        log("    Bug is somewhere else (between DamageStats and DamageCalc dispatch?)")
    else:
        deltas = [(name, expected[i], actual[i])
                  for i, name in enumerate("bcde")
                  if actual[i] != expected[i]]
        log(f"\n*** MISMATCH: {deltas} ***")
        for name, exp, act in deltas:
            if name == "d":
                log(f"    d corrupted from {exp} to {act} (0x{act:02x}). Likely the BP-clobber bug.")
                if act == 0xD0:
                    log(f"    >>> d=$D0 = HIGH(wEnemyMonItem) — UNFIXED de-clobber")
                elif act == 2:
                    log(f"    >>> d=2 = boost helper *_DEN leaked")
                elif act > 100:
                    log(f"    >>> d={act} = some upstream HIGH() byte")

    pyboy.stop(save=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
