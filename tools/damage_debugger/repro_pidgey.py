"""Synth the exact bug reproduction scenario from the investigation doc:
- Lvl 2 wild Pidgey (attacker)
- Lvl 5 Cyndaquil (defender)
- Tackle (BP 40, NORMAL type)
- Expected damage ~3-4

If synth produces ~3, the inner DamageCalc formula is correct and the
bug is wholly upstream (in something that mutates b/c/d/e or wCurDamage
between damagestats and damagecalc, or in a post-damagecalc command).

If synth produces ~18, the bug is INSIDE DamageCalc body itself.
"""

from __future__ import annotations

import sys
from pathlib import Path

from tools.damage_debugger.synth import SynthBattle, SynthMon, SynthMove, run_synth

TYPE_NORMAL = 0x00
TYPE_FIRE = 0x14

# Pokemon Gen 2 base stats (verify):
# Pidgey:    NORMAL/FLYING, base atk=45, def=40, spe=56, spa=35, spd=35, hp=40
# Cyndaquil: FIRE,         base atk=52, def=43, spe=65, spa=60, spd=50, hp=39

# Computed stats (no IVs/EVs as a worst-case approx for fresh new game wild):
# stat = floor((2*base) * level / 100) + 5  (no IV/EV)
# HP   = floor((2*base) * level / 100) + level + 10

def computed(base: int, level: int) -> int:
    return ((2 * base) * level) // 100 + 5


def main() -> int:
    pidgey = SynthMon(
        species=16,            # PIDGEY in Gen 2 dex
        level=2,
        type1=0x00,            # NORMAL
        type2=0x02,            # FLYING
        attack=computed(45, 2),    # ~6
        defense=computed(40, 2),
        speed=computed(56, 2),
        spatk=computed(35, 2),
        spdef=computed(35, 2),
        max_hp=((2*40)*2)//100 + 2 + 10,
        cur_hp=((2*40)*2)//100 + 2 + 10,
    )
    cyndaquil = SynthMon(
        species=155,           # CYNDAQUIL
        level=5,
        type1=0x14,            # FIRE
        type2=0x14,
        attack=computed(52, 5),
        defense=computed(43, 5),    # ~9-10
        speed=computed(65, 5),
        spatk=computed(60, 5),
        spdef=computed(50, 5),
        max_hp=((2*39)*5)//100 + 5 + 10,
        cur_hp=((2*39)*5)//100 + 5 + 10,
    )
    tackle = SynthMove(
        move_id=0x21,          # TACKLE
        effect=0x00,           # EFFECT_NORMAL_HIT
        power=40,
        type=TYPE_NORMAL,
        accuracy=0xFF,
        pp=35,
    )

    print(f"pidgey:    lvl={pidgey.level} atk={pidgey.attack} def={pidgey.defense} type1={pidgey.type1:#04x} type2={pidgey.type2:#04x}")
    print(f"cyndaquil: lvl={cyndaquil.level} atk={cyndaquil.attack} def={cyndaquil.defense} hp={cyndaquil.cur_hp}/{cyndaquil.max_hp}")
    print(f"move:      tackle BP={tackle.power} type=NORMAL")

    # Pidgey is the enemy/attacker.
    battle = SynthBattle(
        name="repro_pidgey_tackle_cyndaquil",
        player=cyndaquil,
        enemy=pidgey,
        move=tackle,
        is_player_turn=False,  # enemy attacks
    )

    print("\n--- running synth (DamageCalc only, controlled inputs) ---")
    res = run_synth(battle)
    print(f"per_step       : {res['per_step']}")
    print(f"trace frames   : {res['trace_frames']}")
    print(f"first/last PC  : {res['first_pc']:04x} / {res['last_pc']:04x}" if res['first_pc'] else "(no trace)")
    print(f"final cur_dmg  : {res['cur_damage']}")

    # Hand-computed Gen 2 formula:
    # base = ((2*L/5+2) * Atk * Power / Def) / 50 + 2
    L, A, P, D = pidgey.level, pidgey.attack, tackle.power, cyndaquil.defense
    inner = (2 * L) // 5 + 2
    base = ((inner * A * P) // D) // 50 + 2
    print(f"\nhand-computed: L={L} A={A} P={P} D={D}")
    print(f"  inner = (2*{L})/5+2 = {inner}")
    print(f"  base = ({inner}*{A}*{P}/{D})/50+2 = {base}")
    print(f"  expected ~{base} (no STAB, no item, no crit, no type-eff)")

    if res["cur_damage"] == base:
        print(f"\n*** SYNTH MATCHES ORACLE: {base} ***")
        print("  -> DamageCalc inner formula is correct in isolation.")
        print("  -> Bug is in upstream (DamageStats sets wrong b/c/d/e) or")
        print("     post-DamageCalc commands (Stab/etc multiply wrong).")
    elif res["cur_damage"] > base * 4:
        print(f"\n*** SYNTH ALSO BUGGY: live={res['cur_damage']} vs oracle={base} ratio={res['cur_damage']/base:.1f}x ***")
        print("  -> Bug is INSIDE DamageCalc body (the inner formula).")
    else:
        print(f"\n*** UNEXPECTED: live={res['cur_damage']} vs oracle={base} ***")

    return 0


if __name__ == "__main__":
    sys.exit(main())
