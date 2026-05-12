"""Trace key function entries/exits during DamageStats with Eviolite-on-defender
to pinpoint where d gets clobbered from 40 to 127.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pyboy import PyBoy

from .paths import find_rom, find_sym

LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "trace_chain.log"


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


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    def log(msg):
        sys.stdout.write(msg + "\n"); sys.stdout.flush()
        fh.write(msg + "\n"); fh.flush()

    rom = find_rom()
    sym = find_sym()
    syms = parse_sym(sym)

    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    pyboy.set_emulation_speed(0)
    pyboy.tick(240, False, False)

    # Seed for Eviolite-on-defender
    write_byte(pyboy, "wEnemyMonSpecies", syms, 16)
    write_byte(pyboy, "wEnemyMonLevel", syms, 2)
    write_byte(pyboy, "wEnemyMonType1", syms, 0x00)
    write_byte(pyboy, "wEnemyMonType2", syms, 0x02)
    write_byte(pyboy, "wEnemyMonItem", syms, 0)
    write_be_u16(pyboy, "wEnemyMonHP", syms, 12)
    write_be_u16(pyboy, "wEnemyMonAttack", syms, 6)
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

    write_byte(pyboy, "wBattleMonSpecies", syms, 155)
    write_byte(pyboy, "wBattleMonLevel", syms, 5)
    write_byte(pyboy, "wBattleMonType1", syms, 0x14)
    write_byte(pyboy, "wBattleMonType2", syms, 0x14)
    write_byte(pyboy, "wBattleMonItem", syms, 0)  # baseline: no item
    write_be_u16(pyboy, "wBattleMonHP", syms, 18)
    write_be_u16(pyboy, "wBattleMonMaxHP", syms, 18)
    write_be_u16(pyboy, "wBattleMonAttack", syms, 10)
    write_be_u16(pyboy, "wBattleMonDefense", syms, 9)
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

    move_sym = syms["wEnemyMoveStruct"]
    b, a = move_sym
    for offset, val in [(0, 0x21), (1, 0x00), (2, 40), (3, 0x00), (4, 0xFF), (5, 35), (6, 0)]:
        if 0xD000 <= a + offset <= 0xDFFF and b:
            old = int(pyboy.memory[0xFF70])
            pyboy.memory[0xFF70] = b
            try: pyboy.memory[a+offset] = val
            finally: pyboy.memory[0xFF70] = old
        else:
            pyboy.memory[a+offset] = val

    write_byte(pyboy, "wCriticalHit", syms, 0)
    write_byte(pyboy, "wEnemyScreens", syms, 0)
    write_byte(pyboy, "wPlayerScreens", syms, 0)
    write_byte(pyboy, "wIsConfusionDamage", syms, 0)
    write_byte(pyboy, "hBattleTurn", syms, 1)

    # Hook key functions on the path
    targets = [
        ("BattleCommand_DamageStats", "DStats_entry"),
        ("EnemyAttackDamage", "EnemyAtkDmg_entry"),
        ("ApplyLateGenDamageStatsItemMods", "ALGDS_thunk_entry"),
        ("ApplyLateGenDamageStatsItemMods_Far", "ALGDS_far_entry"),
        ("ApplyLateGenDamageStatsItemMods_Far.done", "ALGDS_far_done"),
        ("ApplyLateGenDamageStatsItemMods_Far.ApplyEvioliteDefenseBoost", "ALGDS_eviolite"),
        ("DittoMetalPowder_Far", "DMP_entry"),
        ("TruncateHL_BC", "Truncate_entry"),
        ("TruncateHL_BC.done", "Truncate_done"),
        ("CheckDamageStatsCritical", "CDSC_entry"),
        ("CheckDamageStatsCritical_Far", "CDSC_far_entry"),
    ]

    seq = [0]
    def make_cb(label):
        def cb(_):
            rf = pyboy.register_file
            seq[0] += 1
            log(f"  #{seq[0]:3d} {label:32s}: A={int(rf.A):02x} F={int(rf.F):02x} "
                f"BC={int(rf.B):02x}{int(rf.C):02x} DE={int(rf.D):02x}{int(rf.E):02x} "
                f"HL={int(rf.HL):04x} SP={int(rf.SP):04x}")
        return cb

    log("BASELINE no-items scenario; hooks installed:")
    for sym_name, label in targets:
        s = syms.get(sym_name)
        if s is None:
            log(f"  SKIP (sym missing): {sym_name}")
            continue
        pyboy.hook_register(s[0], s[1], make_cb(label), None)
        log(f"  HOOK ${s[0]:02x}:{s[1]:04x}  {sym_name}  -> {label}")

    log("\n=== calling BattleCommand_DamageStats ===")
    sb = syms["BattleCommand_DamageStats"]
    rf = pyboy.register_file
    sp = int(rf.SP)
    new_sp = (sp - 2) & 0xFFFF
    # Use safe jr-loop sentinel
    sentinel_addr = 0xFFFD
    pyboy.memory[sentinel_addr] = 0x18
    pyboy.memory[sentinel_addr + 1] = 0xFE
    pyboy.memory[new_sp] = sentinel_addr & 0xFF
    pyboy.memory[new_sp + 1] = (sentinel_addr >> 8) & 0xFF
    rf.SP = new_sp
    rf.PC = sb[1]
    pyboy.memory[syms["hROMBank"][1]] = sb[0]
    pyboy.memory[0x2000] = sb[0]
    ticked = 0
    returned = [False]
    while ticked < 4800:
        pyboy.tick(2, False, False)
        ticked += 2
        pc_now = int(pyboy.register_file.PC)
        if pc_now == sentinel_addr or pc_now == sentinel_addr + 2:
            returned[0] = True
            break
    log(f"\nDamageStats returned in {ticked} ticks: returned={returned[0]}")
    rf = pyboy.register_file
    log(f"FINAL: A={int(rf.A):02x} BC={int(rf.B):02x}{int(rf.C):02x} "
        f"DE={int(rf.D):02x}{int(rf.E):02x} HL={int(rf.HL):04x}")
    pyboy.stop(save=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
