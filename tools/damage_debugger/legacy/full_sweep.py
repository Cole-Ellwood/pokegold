"""Sweep variants through DamageStats -> DamageCalc -> Stab (skip
Critical which requires WRAM context I can't easily seed cold-boot).

For each variant, computes the expected damage in Python (oracle) and
compares to the live emulator result. A divergence = the mechanic
exposed by that variant is buggy.
"""

from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from pyboy import PyBoy

ROOT = Path("C:/Users/lolno/Downloads/pokemon gold hack")
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "full_sweep.log"


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


@dataclass
class Variant:
    name: str
    pidgey_atk: int = 6      # Pidgey lvl 2 base atk
    cynd_def: int = 9         # Cyndaquil lvl 5 base def
    pidgey_lvl: int = 2
    bp: int = 40              # Tackle BP
    enemy_item: int = 0
    player_item: int = 0
    pidgey_t1: int = 0x00     # NORMAL
    pidgey_t2: int = 0x02     # FLYING
    cynd_t1: int = 0x14       # FIRE
    cynd_t2: int = 0x14
    move_type: int = 0x00     # Tackle = NORMAL
    enemy_atk_stage: int = 7
    enemy_def_stage: int = 7
    player_atk_stage: int = 7
    player_def_stage: int = 7
    crit: int = 0
    expected: int = 3         # Oracle prediction


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


def seed_wram(pyboy, syms, v: Variant):
    """Set up WRAM for the variant scenario."""
    # Enemy (Pidgey)
    write_byte(pyboy, "wEnemyMonSpecies", syms, 16)
    write_byte(pyboy, "wEnemyMonLevel", syms, v.pidgey_lvl)
    write_byte(pyboy, "wEnemyMonType1", syms, v.pidgey_t1)
    write_byte(pyboy, "wEnemyMonType2", syms, v.pidgey_t2)
    write_byte(pyboy, "wEnemyMonItem", syms, v.enemy_item)
    write_be_u16(pyboy, "wEnemyMonHP", syms, 12)
    write_be_u16(pyboy, "wEnemyMonAttack", syms, v.pidgey_atk)
    write_be_u16(pyboy, "wEnemyMonDefense", syms, 6)
    write_be_u16(pyboy, "wEnemyMonSpeed", syms, 7)
    write_be_u16(pyboy, "wEnemyMonSpclAtk", syms, 5)
    write_be_u16(pyboy, "wEnemyMonSpclDef", syms, 5)
    write_be_u16(pyboy, "wEnemyAttack", syms, v.pidgey_atk)
    write_be_u16(pyboy, "wEnemyDefense", syms, 6)
    write_be_u16(pyboy, "wEnemySpAtk", syms, 5)
    write_be_u16(pyboy, "wEnemySpDef", syms, 5)
    write_byte(pyboy, "wEnemyAtkLevel", syms, v.enemy_atk_stage)
    write_byte(pyboy, "wEnemyDefLevel", syms, v.enemy_def_stage)
    write_byte(pyboy, "wEnemySpdLevel", syms, 7)
    write_byte(pyboy, "wEnemySAtkLevel", syms, 7)
    write_byte(pyboy, "wEnemySDefLevel", syms, 7)

    # Player (Cyndaquil)
    write_byte(pyboy, "wBattleMonSpecies", syms, 155)
    write_byte(pyboy, "wBattleMonLevel", syms, 5)
    write_byte(pyboy, "wBattleMonType1", syms, v.cynd_t1)
    write_byte(pyboy, "wBattleMonType2", syms, v.cynd_t2)
    write_byte(pyboy, "wBattleMonItem", syms, v.player_item)
    write_be_u16(pyboy, "wBattleMonHP", syms, 18)
    write_be_u16(pyboy, "wBattleMonMaxHP", syms, 18)
    write_be_u16(pyboy, "wBattleMonAttack", syms, 10)
    write_be_u16(pyboy, "wBattleMonDefense", syms, v.cynd_def)
    write_be_u16(pyboy, "wBattleMonSpeed", syms, 11)
    write_be_u16(pyboy, "wBattleMonSpclAtk", syms, 11)
    write_be_u16(pyboy, "wBattleMonSpclDef", syms, 10)
    write_be_u16(pyboy, "wPlayerAttack", syms, 10)
    write_be_u16(pyboy, "wPlayerDefense", syms, v.cynd_def)
    write_be_u16(pyboy, "wPlayerSpAtk", syms, 11)
    write_be_u16(pyboy, "wPlayerSpDef", syms, 10)
    write_byte(pyboy, "wPlayerAtkLevel", syms, v.player_atk_stage)
    write_byte(pyboy, "wPlayerDefLevel", syms, v.player_def_stage)
    write_byte(pyboy, "wPlayerSpdLevel", syms, 7)
    write_byte(pyboy, "wPlayerSAtkLevel", syms, 7)
    write_byte(pyboy, "wPlayerSDefLevel", syms, 7)

    # Tackle in wEnemyMoveStruct (since Pidgey attacks)
    move_sym = syms.get("wEnemyMoveStruct")
    if move_sym:
        b, a = move_sym
        for offset, val in [(0, 0x21), (1, 0x00), (2, v.bp), (3, v.move_type),
                            (4, 0xFF), (5, 35), (6, 0)]:
            if 0xD000 <= a + offset <= 0xDFFF and b:
                old = int(pyboy.memory[0xFF70])
                pyboy.memory[0xFF70] = b
                try: pyboy.memory[a+offset] = val
                finally: pyboy.memory[0xFF70] = old
            else:
                pyboy.memory[a+offset] = val

    # Battle state
    write_byte(pyboy, "wBattleMode", syms, 1)
    write_byte(pyboy, "wCriticalHit", syms, v.crit)
    write_byte(pyboy, "wTypeMatchup", syms, 0x10)
    write_byte(pyboy, "wIsConfusionDamage", syms, 0)
    write_byte(pyboy, "wEffectFailed", syms, 0)
    write_byte(pyboy, "wAttackMissed", syms, 0)
    write_byte(pyboy, "wTypeModifier", syms, 0)
    write_byte(pyboy, "wCurEnemyMove", syms, 0x21)
    write_byte(pyboy, "wCurPlayerMove", syms, 0)
    write_be_u16(pyboy, "wCurDamage", syms, 0)
    write_byte(pyboy, "wPlayerScreens", syms, 0)
    write_byte(pyboy, "wEnemyScreens", syms, 0)
    write_byte(pyboy, "wBattleWeather", syms, 0)
    write_byte(pyboy, "wJohtoBadges", syms, 0)
    write_byte(pyboy, "wKantoBadges", syms, 0)
    write_byte(pyboy, "wBattleMonStatus", syms, 0)
    write_byte(pyboy, "wEnemyMonStatus", syms, 0)
    write_byte(pyboy, "hBattleTurn", syms, 1)         # enemy turn


def run_variant(rom: Path, sym: Path, syms: dict, v: Variant) -> dict:
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    pyboy.set_emulation_speed(0)
    pyboy.tick(240, False, False)
    seed_wram(pyboy, syms, v)
    cd_after = {}
    chain = ["BattleCommand_DamageStats", "BattleCommand_DamageCalc",
             "BattleCommand_Stab"]
    for fn in chain:
        ticks, ok = call_function(pyboy, fn, syms, budget=2400)
        cd_sym = syms["wCurDamage"]
        cd = read_be_u16(pyboy, cd_sym[1], cd_sym[0])
        cd_after[fn] = (cd, ticks, ok)
    pyboy.stop(save=False)
    return cd_after


def python_oracle(v: Variant) -> int:
    """Compute expected damage. Pidgey is the attacker (enemy turn)."""
    L = v.pidgey_lvl
    eff_atk = v.pidgey_atk
    eff_def = v.cynd_def
    inner = (2 * L) // 5 + 2
    base = ((inner * eff_atk * v.bp) // eff_def) // 50 + 2
    # STAB: move_type matches attacker's type1 or type2
    if v.move_type == v.pidgey_t1 or v.move_type == v.pidgey_t2:
        base = (base * 3) // 2
    return base


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    def log(msg):
        sys.stdout.write(msg + "\n"); sys.stdout.flush()
        fh.write(msg + "\n"); fh.flush()

    rom = ROOT / "pokegold_trace.gbc"
    sym = ROOT / "pokegold_trace.sym"
    syms = parse_sym(sym)

    variants = [
        Variant(name="baseline_pidgey_tackle"),
        Variant(name="muscle_band_pidgey", enemy_item=0x8E),     # MUSCLE_BAND
        Variant(name="life_orb_pidgey", enemy_item=0x46),
        Variant(name="choice_band_pidgey", enemy_item=0x74),
        Variant(name="cyn_eviolite", player_item=0x93),         # EVOLITE on Cyndaquil
        Variant(name="cyn_assault_vest", player_item=0x89),
        Variant(name="stab_normal_dual",  move_type=0x00, pidgey_t1=0x00, pidgey_t2=0x02),  # NORMAL/FLYING dual
        Variant(name="stab_normal_mono",  move_type=0x00, pidgey_t1=0x00, pidgey_t2=0x00),  # mono Normal (16/15)
        Variant(name="cyndaquil_atk_minus_2", player_atk_stage=5),
        Variant(name="pidgey_atk_plus_2", enemy_atk_stage=9),
        Variant(name="critical_hit", crit=1),
    ]

    log(f"variant{'':30s} {'Stats':>5s} {'Calc':>5s} {'Stab':>5s} {'Oracle':>6s}  notes")
    log("-" * 100)
    for v in variants:
        try:
            res = run_variant(rom, sym, syms, v)
            ds = res["BattleCommand_DamageStats"][0]
            dc = res["BattleCommand_DamageCalc"][0]
            stab = res["BattleCommand_Stab"][0]
            oracle = python_oracle(v)
            divergent = "***" if abs(stab - oracle) > 1 else "   "
            log(f"{divergent} {v.name:32s} {ds:>5d} {dc:>5d} {stab:>5d} {oracle:>6d}")
        except Exception as e:
            log(f"!!! {v.name:32s} ERROR {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
