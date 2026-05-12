"""Synthesize the FULL move chain (DamageStats -> DamageCalc -> Stab)
with manually-populated WRAM. Pidgey lvl 2 vs Cyndaquil lvl 5 with
Tackle, no items, no crit -- the user's exact bug repro scenario.

Expected damage: ~3 (vanilla formula) -> ~4 with STAB ×1.55 type-passive
Bug observation: ~18 in live game

If the synth chain produces ~18, we have the bug reproduced in
controlled environment and can narrow further.
If the synth chain produces ~3-4, the bug is in something MY synth
isn't seeing -- likely move struct loading (wPlayerMoveStructPower)
or wEnemyMonAttack stat generation.
"""

from __future__ import annotations

LEGACY_EXIT = (
    "tools.damage_debugger.legacy scripts are pruned one-shot drivers; "
    "use active tools.damage_debugger modules instead."
)
raise SystemExit(LEGACY_EXIT)

import sys
import time
from pathlib import Path

from pyboy import PyBoy

ROOT = Path("C:/Users/lolno/Downloads/pokemon gold hack")
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "full_chain.log"


def parse_sym(p: Path) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.split(";", 1)[0].strip()
        parts = s.split()
        if len(parts) < 2 or ":" not in parts[0]: continue
        try:
            b, a = parts[0].split(":", 1)
            out[parts[1]] = (int(b, 16), int(a, 16))
        except ValueError: continue
    return out


def setup_logger():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    def log(msg):
        sys.stdout.write(msg + "\n"); sys.stdout.flush()
        fh.write(msg + "\n"); fh.flush()
    return log


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


def write_be_u16(pyboy, name, syms, value):
    s = syms.get(name)
    if s is None: return False
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
    return True


def read_byte(pyboy, addr, bank=0):
    if 0xD000 <= addr <= 0xDFFF and bank:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = bank
        try: return int(pyboy.memory[addr])
        finally: pyboy.memory[0xFF70] = old
    return int(pyboy.memory[addr])


def call_function(pyboy, name, syms, log):
    s = syms[name]
    rf = pyboy.register_file
    sentinel = 0x0008
    sp = int(rf.SP)
    new_sp = (sp - 2) & 0xFFFF
    pyboy.memory[new_sp] = sentinel & 0xFF
    pyboy.memory[new_sp + 1] = (sentinel >> 8) & 0xFF
    rf.SP = new_sp
    rf.PC = s[1]
    rom_bank_sym = syms.get("hROMBank")
    if rom_bank_sym:
        pyboy.memory[rom_bank_sym[1]] = s[0]
    pyboy.memory[0x2000] = s[0]

    returned = [False]
    def cb(_): returned[0] = True
    pyboy.hook_register(0, sentinel, cb, None)
    ticked = 0
    while ticked < 1200 and not returned[0]:
        pyboy.tick(2, False, False)
        ticked += 2
    pyboy.hook_deregister(0, sentinel)
    if not returned[0]:
        log(f"  WARN: {name} did not return within {ticked} ticks")
    return ticked


def main() -> int:
    log = setup_logger()
    rom = ROOT / "pokegold_trace.gbc"
    sym = ROOT / "pokegold_trace.sym"
    syms = parse_sym(sym)
    log(f"rom: {rom.name}")

    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    pyboy.set_emulation_speed(0)
    pyboy.tick(240, False, False)
    log(f"booted; PC=${int(pyboy.register_file.PC):04x}")

    # Populate the WRAM the chain reads. WRAMX symbols at $D... are bank 1.
    PIDGEY_LVL = 2
    PIDGEY_ATK = ((2 * 45) * PIDGEY_LVL) // 100 + 5
    PIDGEY_DEF = ((2 * 40) * PIDGEY_LVL) // 100 + 5
    PIDGEY_SPE = ((2 * 56) * PIDGEY_LVL) // 100 + 5
    PIDGEY_SPA = ((2 * 35) * PIDGEY_LVL) // 100 + 5
    PIDGEY_SPD = ((2 * 35) * PIDGEY_LVL) // 100 + 5
    PIDGEY_HP = ((2 * 40) * PIDGEY_LVL) // 100 + PIDGEY_LVL + 10

    CYND_LVL = 5
    CYND_ATK = ((2 * 52) * CYND_LVL) // 100 + 5
    CYND_DEF = ((2 * 43) * CYND_LVL) // 100 + 5
    CYND_SPE = ((2 * 65) * CYND_LVL) // 100 + 5
    CYND_SPA = ((2 * 60) * CYND_LVL) // 100 + 5
    CYND_SPD = ((2 * 50) * CYND_LVL) // 100 + 5
    CYND_HP = ((2 * 39) * CYND_LVL) // 100 + CYND_LVL + 10

    log(f"Pidgey:    lvl={PIDGEY_LVL} atk={PIDGEY_ATK} def={PIDGEY_DEF}")
    log(f"Cyndaquil: lvl={CYND_LVL} atk={CYND_ATK} def={CYND_DEF}")

    # === ATTACKER (enemy = Pidgey) ===
    write_byte(pyboy, "wEnemyMonSpecies", syms, 16)             # PIDGEY
    write_byte(pyboy, "wEnemyMonLevel", syms, PIDGEY_LVL)
    write_byte(pyboy, "wEnemyMonType1", syms, 0x00)             # NORMAL
    write_byte(pyboy, "wEnemyMonType2", syms, 0x02)             # FLYING
    write_byte(pyboy, "wEnemyMonItem", syms, 0)                 # no item
    write_be_u16(pyboy, "wEnemyMonHP", syms, PIDGEY_HP)
    write_be_u16(pyboy, "wEnemyMonAttack", syms, PIDGEY_ATK)
    write_be_u16(pyboy, "wEnemyMonDefense", syms, PIDGEY_DEF)
    write_be_u16(pyboy, "wEnemyMonSpeed", syms, PIDGEY_SPE)
    write_be_u16(pyboy, "wEnemyMonSpclAtk", syms, PIDGEY_SPA)
    write_be_u16(pyboy, "wEnemyMonSpclDef", syms, PIDGEY_SPD)
    # Working stats (some functions read wEnemyAttack/Defense which is the
    # un-stage-modified copy)
    write_be_u16(pyboy, "wEnemyAttack", syms, PIDGEY_ATK)
    write_be_u16(pyboy, "wEnemyDefense", syms, PIDGEY_DEF)
    write_be_u16(pyboy, "wEnemySpAtk", syms, PIDGEY_SPA)
    write_be_u16(pyboy, "wEnemySpDef", syms, PIDGEY_SPD)
    write_byte(pyboy, "wEnemyAtkLevel", syms, 7)  # +0 stage
    write_byte(pyboy, "wEnemyDefLevel", syms, 7)
    write_byte(pyboy, "wEnemySpdLevel", syms, 7)
    write_byte(pyboy, "wEnemySAtkLevel", syms, 7)
    write_byte(pyboy, "wEnemySDefLevel", syms, 7)

    # === DEFENDER (player = Cyndaquil) ===
    write_byte(pyboy, "wBattleMonSpecies", syms, 155)           # CYNDAQUIL
    write_byte(pyboy, "wBattleMonLevel", syms, CYND_LVL)
    write_byte(pyboy, "wBattleMonType1", syms, 0x14)            # FIRE
    write_byte(pyboy, "wBattleMonType2", syms, 0x14)            # FIRE
    write_byte(pyboy, "wBattleMonItem", syms, 0)
    write_be_u16(pyboy, "wBattleMonHP", syms, CYND_HP)
    write_be_u16(pyboy, "wBattleMonAttack", syms, CYND_ATK)
    write_be_u16(pyboy, "wBattleMonDefense", syms, CYND_DEF)
    write_be_u16(pyboy, "wBattleMonSpeed", syms, CYND_SPE)
    write_be_u16(pyboy, "wBattleMonSpclAtk", syms, CYND_SPA)
    write_be_u16(pyboy, "wBattleMonSpclDef", syms, CYND_SPD)
    write_be_u16(pyboy, "wPlayerAttack", syms, CYND_ATK)
    write_be_u16(pyboy, "wPlayerDefense", syms, CYND_DEF)
    write_be_u16(pyboy, "wPlayerSpAtk", syms, CYND_SPA)
    write_be_u16(pyboy, "wPlayerSpDef", syms, CYND_SPD)
    write_byte(pyboy, "wPlayerAtkLevel", syms, 7)
    write_byte(pyboy, "wPlayerDefLevel", syms, 7)
    write_byte(pyboy, "wPlayerSpdLevel", syms, 7)
    write_byte(pyboy, "wPlayerSAtkLevel", syms, 7)
    write_byte(pyboy, "wPlayerSDefLevel", syms, 7)

    # === MOVE STRUCT (Tackle in wEnemyMoveStruct since Pidgey attacks) ===
    move_sym = syms.get("wEnemyMoveStruct")
    if move_sym:
        # struct: anim, effect, power, type, accuracy, pp, crit_chance
        b, a = move_sym
        for offset, val in [(0, 0x21), (1, 0x00), (2, 40), (3, 0x00), (4, 0xFF), (5, 35), (6, 0)]:
            if 0xD000 <= a + offset <= 0xDFFF and b:
                old = int(pyboy.memory[0xFF70])
                pyboy.memory[0xFF70] = b
                try: pyboy.memory[a + offset] = val
                finally: pyboy.memory[0xFF70] = old
            else:
                pyboy.memory[a + offset] = val

    # Also wPlayerMoveStruct (zeroed)
    p_move = syms.get("wPlayerMoveStruct")
    if p_move:
        b, a = p_move
        for offset in range(7):
            if 0xD000 <= a + offset <= 0xDFFF and b:
                old = int(pyboy.memory[0xFF70])
                pyboy.memory[0xFF70] = b
                try: pyboy.memory[a + offset] = 0
                finally: pyboy.memory[0xFF70] = old
            else:
                pyboy.memory[a + offset] = 0

    # === BATTLE STATE ===
    write_byte(pyboy, "wBattleMode", syms, 1)         # WILD_BATTLE
    write_byte(pyboy, "wCriticalHit", syms, 0)
    write_byte(pyboy, "wTypeMatchup", syms, 0x10)     # neutral 1.0×
    write_byte(pyboy, "wIsConfusionDamage", syms, 0)
    write_byte(pyboy, "wEffectFailed", syms, 0)
    write_byte(pyboy, "wAttackMissed", syms, 0)
    write_byte(pyboy, "wTypeModifier", syms, 0x00)
    write_byte(pyboy, "wCurEnemyMove", syms, 0x21)    # TACKLE
    write_byte(pyboy, "wCurPlayerMove", syms, 0)
    write_be_u16(pyboy, "wCurDamage", syms, 0)
    # Screens
    write_byte(pyboy, "wPlayerScreens", syms, 0)
    write_byte(pyboy, "wEnemyScreens", syms, 0)

    # === BATTLE TURN: enemy attacks (turn 1 = enemy) ===
    write_byte(pyboy, "hBattleTurn", syms, 1)         # 1 = enemy turn

    log("\nWRAM populated. Calling chain...")
    chain = ["BattleCommand_Critical", "BattleCommand_DamageStats",
             "BattleCommand_DamageCalc", "BattleCommand_Stab"]
    for name in chain:
        if name not in syms:
            log(f"  SKIP {name} (not in sym)"); continue
        ticks = call_function(pyboy, name, syms, log)
        cd_sym = syms["wCurDamage"]
        cd_hi = read_byte(pyboy, cd_sym[1], cd_sym[0])
        cd_lo = read_byte(pyboy, cd_sym[1]+1, cd_sym[0])
        cd_word = (cd_hi << 8) | cd_lo
        log(f"  after {name:32s}: ticks={ticks:4d} wCurDamage={cd_word}")

    log("\n=== final ===")
    cd_sym = syms["wCurDamage"]
    cd_word = (read_byte(pyboy, cd_sym[1], cd_sym[0]) << 8) | read_byte(pyboy, cd_sym[1]+1, cd_sym[0])
    log(f"wCurDamage = {cd_word}")
    expected_no_stab = 3
    expected_stab_dual = (3 * 31) // 30  # ~3
    log(f"expected vanilla: ~3")
    log(f"expected with type-passive STAB (dual Normal): ~3-4")
    log(f"expected with bug (5x): ~15-18")
    if cd_word > 12:
        log(f"\n*** BUG REPRODUCED IN SYNTH (live={cd_word}, expected ~3) ***")
        log(f"*** Now we can step through the chain to localize ***")
    elif cd_word in (3, 4, 5):
        log(f"\nSYNTH OK ({cd_word}). Chain is correct in this controlled environment.")
        log(f"  -> Bug must be in something my WRAM seed didn't capture.")
        log(f"  -> Likely candidates: real move struct loading from Moves table,")
        log(f"     real wild Pokémon stat generation, or data the game sets in")
        log(f"     other WRAM cells that affect the chain.")

    pyboy.stop(save=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
