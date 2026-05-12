"""Sweep DamageStats only with various items. After DamageStats:
  - b should = attacker's truncated atk
  - c should = defender's truncated def
  - d should = move BP (Tackle = 40, never changes)
  - e should = attacker's level

If `d != 40` for any item variant, the bug is in DamageStats path
(specifically the ApplyLateGenDamageStatsItemMods chain).
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
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "stats_item_sweep.log"


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


SENTINEL_ADDR = 0xFFFD


def call_function(pyboy, name, syms, budget=4800):
    s = syms[name]
    rf = pyboy.register_file
    # Install jr-loop trap: 0x18 0xFE = jr -2 (infinite self-loop)
    pyboy.memory[SENTINEL_ADDR] = 0x18
    pyboy.memory[SENTINEL_ADDR + 1] = 0xFE
    sp = int(rf.SP)
    new_sp = (sp - 2) & 0xFFFF
    pyboy.memory[new_sp] = SENTINEL_ADDR & 0xFF
    pyboy.memory[new_sp + 1] = (SENTINEL_ADDR >> 8) & 0xFF
    rf.SP = new_sp
    rf.PC = s[1]
    if syms.get("hROMBank"):
        pyboy.memory[syms["hROMBank"][1]] = s[0]
    pyboy.memory[0x2000] = s[0]
    ticked = 0
    while ticked < budget:
        pyboy.tick(2, False, False)
        ticked += 2
        pc = int(rf.PC)
        if pc == SENTINEL_ADDR or pc == SENTINEL_ADDR + 2:
            return ticked, True
    return ticked, False


def seed_minimal(pyboy, syms, enemy_item: int = 0, player_item: int = 0):
    """Same WRAM seed as stats_isolation.py (which works)."""
    write_byte(pyboy, "wEnemyMonSpecies", syms, 16)
    write_byte(pyboy, "wEnemyMonLevel", syms, 2)
    write_byte(pyboy, "wEnemyMonType1", syms, 0x00)
    write_byte(pyboy, "wEnemyMonType2", syms, 0x02)
    write_byte(pyboy, "wEnemyMonItem", syms, enemy_item)
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
    write_byte(pyboy, "wBattleMonItem", syms, player_item)
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

    write_byte(pyboy, "wCriticalHit", syms, 0)
    write_byte(pyboy, "wEnemyScreens", syms, 0)
    write_byte(pyboy, "wPlayerScreens", syms, 0)
    write_byte(pyboy, "wIsConfusionDamage", syms, 0)
    write_byte(pyboy, "hBattleTurn", syms, 1)


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    def log(msg):
        sys.stdout.write(msg + "\n"); sys.stdout.flush()
        fh.write(msg + "\n"); fh.flush()

    rom = ROOT / "pokegold_debug.gbc"
    sym = ROOT / "pokegold_debug.sym"
    syms = parse_sym(sym)

    # Item variants — both attacker and defender slots
    variants = [
        ("baseline_no_item", 0, 0),
        ("attacker_muscle_band", 0x8E, 0),
        ("attacker_life_orb", 0x46, 0),
        ("attacker_choice_band", 0x74, 0),
        ("attacker_metronome", 0x9A, 0),
        ("attacker_expert_belt", 0x8D, 0),
        ("defender_eviolite", 0, 0x93),
        ("defender_assault_vest", 0, 0x89),
    ]

    log(f"{'variant':<30s} {'b':>4s} {'c':>4s} {'d':>4s} {'e':>4s}  notes")
    log("-" * 80)

    for name, e_item, p_item in variants:
        pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
        pyboy.set_emulation_speed(0)
        pyboy.tick(240, False, False)
        seed_minimal(pyboy, syms, enemy_item=e_item, player_item=p_item)

        ticks, ok = call_function(pyboy, "BattleCommand_DamageStats", syms)
        if not ok:
            log(f"!!! {name:<30s} HUNG after {ticks} ticks")
            pyboy.stop(save=False)
            continue
        rf = pyboy.register_file
        b = int(rf.B); c = int(rf.C); d = int(rf.D); e = int(rf.E)
        flag = "***" if d != 40 else "   "
        log(f"{flag} {name:<30s} {b:>4d} {c:>4d} {d:>4d} {e:>4d}  e_item=0x{e_item:02x} p_item=0x{p_item:02x}")
        pyboy.stop(save=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
