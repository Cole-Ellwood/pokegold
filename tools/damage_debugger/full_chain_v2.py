"""Full chain (DamageStats + DamageCalc + Stab) with safe-sentinel call.

Skip Critical (which farcalls GetUserItem and hangs cold-boot). Run the
core damage path on Pidgey-Tackle-vs-Cyndaquil and read final wCurDamage.

Expected: 3 (no STAB) -> Stab applies 1.5x for monotype attacker (but
Pidgey is dual Normal/Flying, so STAB applies for Normal-type Tackle;
Tackle's type matches Pidgey's type1=Normal). With type-passive
\\u00d731/30 dual mod, end result ~4.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pyboy import PyBoy

from .safe_call import call_function_safe, read_be_u16_banked, write_byte_banked

ROOT = Path("C:/Users/lolno/Downloads/pokemon gold hack")
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "full_chain_v2.log"


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
    write_byte_banked(pyboy, s[1], value, s[0])


def write_be_u16(pyboy, name, syms, value):
    s = syms.get(name)
    if s is None: return
    hi, lo = (value >> 8) & 0xFF, value & 0xFF
    write_byte_banked(pyboy, s[1], hi, s[0])
    write_byte_banked(pyboy, s[1] + 1, lo, s[0])


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    def log(msg):
        sys.stdout.write(msg + "\n"); sys.stdout.flush()
        fh.write(msg + "\n"); fh.flush()

    rom = ROOT / "pokegold_debug.gbc"
    sym = ROOT / "pokegold_debug.sym"
    syms = parse_sym(sym)

    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    pyboy.set_emulation_speed(0)
    pyboy.tick(240, False, False)

    # Pidgey lvl 2 attacker, Tackle, vs Cyndaquil lvl 5 defender, no items
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
    write_byte(pyboy, "wBattleMonItem", syms, 0)
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
    b_, a_ = move_sym
    for offset, val in [(0, 0x21), (1, 0x00), (2, 40), (3, 0x00), (4, 0xFF), (5, 35), (6, 0)]:
        write_byte_banked(pyboy, a_+offset, val, b_)

    write_byte(pyboy, "wCriticalHit", syms, 0)
    write_byte(pyboy, "wEnemyScreens", syms, 0)
    write_byte(pyboy, "wPlayerScreens", syms, 0)
    write_byte(pyboy, "wIsConfusionDamage", syms, 0)
    write_byte(pyboy, "wTypeMatchup", syms, 0x10)
    write_byte(pyboy, "wTypeModifier", syms, 0)
    write_byte(pyboy, "wAttackMissed", syms, 0)
    write_byte(pyboy, "wEffectFailed", syms, 0)
    write_be_u16(pyboy, "wCurDamage", syms, 0)
    write_byte(pyboy, "wBattleMonStatus", syms, 0)
    write_byte(pyboy, "wEnemyMonStatus", syms, 0)
    write_byte(pyboy, "wBattleWeather", syms, 0)
    write_byte(pyboy, "wJohtoBadges", syms, 0)
    write_byte(pyboy, "wKantoBadges", syms, 0)
    write_byte(pyboy, "wCurEnemyMove", syms, 0x21)
    write_byte(pyboy, "wCurPlayerMove", syms, 0)
    write_byte(pyboy, "hBattleTurn", syms, 1)

    log(f"Pidgey-Tackle-vs-Cyndaquil; calling chain")
    log(f"{'function':<32s} {'ticks':>6s} {'ret':>4s} {'cd_after':>8s}")

    cd_sym = syms["wCurDamage"]
    chain = ["BattleCommand_DamageStats", "BattleCommand_DamageCalc",
             "BattleCommand_Stab"]
    for fn in chain:
        ticks, returned, post_pc = call_function_safe(pyboy, syms, fn)
        cd = read_be_u16_banked(pyboy, cd_sym[1], cd_sym[0])
        log(f"{fn:<32s} {ticks:>6d} {returned!s:>4s} {cd:>8d}  (PC=${post_pc:04x})")

    final_cd = read_be_u16_banked(pyboy, cd_sym[1], cd_sym[0])
    log(f"\nFINAL wCurDamage = {final_cd}")
    log(f"Expected (no STAB):                       3")
    log(f"Expected (vanilla 1.5x STAB):             4")
    log(f"Expected (1.5x + type-passive 31/30):    ~4")
    log(f"User reported (the bug):                 18")
    if final_cd == 3 or final_cd == 4 or final_cd == 5:
        log(f"\n*** OK — chain produces expected damage. Bug NOT in this path.")
        log(f"    Bug must be elsewhere — possibly DamageVariation, ApplyDamage,")
        log(f"    or a pre-DamageStats command (Critical, DoTurn).")
    elif final_cd > 12:
        log(f"\n*** BUG REPRODUCED IN SYNTH ({final_cd}, expected ~3-4) ***")

    pyboy.stop(save=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
