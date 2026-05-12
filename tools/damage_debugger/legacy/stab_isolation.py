"""Test BattleCommand_Stab in isolation with controlled inputs.

Set up the smallest WRAM seed Stab needs (types, hBattleTurn,
wCurDamage, wTypeMatchup, etc.), call Stab, read wCurDamage.

Pidgey (NORMAL/FLYING) Tackle (NORMAL move) vs Cyndaquil (FIRE):
- Vanilla STAB: ×1.5 (matches one of attacker's types)
- Type effectiveness: 1.0× (NORMAL hits FIRE neutrally)
- Type-passive Normal STAB: dual-type Normal contribution = 1
  -> mult ×31/30 in addition to vanilla ×1.5
- Net STAB: ×1.55

Setting wCurDamage = 3 and calling Stab:
  Vanilla path: 3 × 1.5 = 4 (after STAB applied)
  Then type-eff loop runs (NORMAL has type matchups);
  Then TypePassive_ApplyDamageModifiers_Far applies ×31/30:
    4 × 31/30 = 4 (integer)
  Expected final: ~4

If Stab returns ~18 (5x), bug is somewhere in Stab/type-passive chain.
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
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "stab_iso.log"


def parse_sym(p: Path) -> dict[str, tuple[int, int]]:
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
    if s is None:
        return False
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


def read_be_u16(pyboy, addr, bank=0):
    if 0xD000 <= addr <= 0xDFFF and bank:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = bank
        try:
            hi = int(pyboy.memory[addr])
            lo = int(pyboy.memory[addr+1])
        finally: pyboy.memory[0xFF70] = old
    else:
        hi = int(pyboy.memory[addr])
        lo = int(pyboy.memory[addr+1])
    return (hi << 8) | lo


def call_function(pyboy, name, syms, log, budget=1200):
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

    # Seed minimal state for Stab:
    # Pidgey (enemy attacker) Normal/Flying, Tackle (Normal move)
    # Cyndaquil (player defender) Fire/Fire
    write_byte(pyboy, "wBattleMonType1", syms, 0x14)   # FIRE
    write_byte(pyboy, "wBattleMonType2", syms, 0x14)
    write_byte(pyboy, "wEnemyMonType1", syms, 0x00)    # NORMAL
    write_byte(pyboy, "wEnemyMonType2", syms, 0x02)    # FLYING
    # Move struct (since Pidgey is enemy, wEnemyMoveStruct)
    move_sym = syms.get("wEnemyMoveStruct")
    if move_sym:
        b, a = move_sym
        for offset, val in [(0, 0x21), (1, 0x00), (2, 40), (3, 0x00), (4, 0xFF), (5, 35), (6, 0)]:
            if 0xD000 <= a + offset <= 0xDFFF and b:
                old = int(pyboy.memory[0xFF70])
                pyboy.memory[0xFF70] = b
                try: pyboy.memory[a+offset] = val
                finally: pyboy.memory[0xFF70] = old
            else:
                pyboy.memory[a+offset] = val
    # Initial state for the formula
    write_be_u16(pyboy, "wCurDamage", syms, 3)         # the correct base
    write_byte(pyboy, "wCriticalHit", syms, 0)
    write_byte(pyboy, "wTypeMatchup", syms, 0x10)      # neutral
    write_byte(pyboy, "wTypeModifier", syms, 0)
    write_byte(pyboy, "wAttackMissed", syms, 0)
    write_byte(pyboy, "wIsConfusionDamage", syms, 0)
    # HP/Max for type-passive HP-based branches (Fire low-HP, Ice >half-HP)
    write_be_u16(pyboy, "wBattleMonHP", syms, 18)
    write_be_u16(pyboy, "wBattleMonMaxHP", syms, 18)
    write_be_u16(pyboy, "wEnemyMonHP", syms, 12)
    write_be_u16(pyboy, "wEnemyMonMaxHP", syms, 12)
    # Status
    write_byte(pyboy, "wBattleMonStatus", syms, 0)
    write_byte(pyboy, "wEnemyMonStatus", syms, 0)
    # Items (none)
    write_byte(pyboy, "wBattleMonItem", syms, 0)
    write_byte(pyboy, "wEnemyMonItem", syms, 0)
    # Weather
    write_byte(pyboy, "wBattleWeather", syms, 0)
    # Badges
    write_byte(pyboy, "wJohtoBadges", syms, 0)
    write_byte(pyboy, "wKantoBadges", syms, 0)
    # hBattleTurn = 1 (enemy turn)
    write_byte(pyboy, "hBattleTurn", syms, 1)

    log(f"WRAM seeded; calling BattleCommand_Stab with wCurDamage=3")

    # Hook stab body to capture intermediate states
    stab_sym = syms["BattleCommand_Stab"]
    hits = []
    def cb(_ctx):
        rf = pyboy.register_file
        cd = read_be_u16(pyboy, syms["wCurDamage"][1], syms["wCurDamage"][0])
        hits.append({"PC": int(rf.PC), "cur_damage": cd})

    # Hook the .end and .stab points to see what happens
    points = ["BattleCommand_Stab", "BattleCommand_Stab.stab",
              "BattleCommand_Stab.SkipStab", "BattleCommand_Stab.GotMatchup",
              "BattleCommand_Stab.end", "BattleCommand_Stab.not_immune"]
    installed = []
    for name in points:
        s = syms.get(name)
        if s is None: continue
        pyboy.hook_register(s[0], s[1], cb, None)
        installed.append((s, name))

    ticks, ok = call_function(pyboy, "BattleCommand_Stab", syms, log, budget=2400)
    log(f"  ticks={ticks} returned={ok}")

    cd_after = read_be_u16(pyboy, syms["wCurDamage"][1], syms["wCurDamage"][0])
    log(f"\nwCurDamage AFTER Stab: {cd_after} (started at 3)")
    log(f"\nIntermediate hits ({len(hits)}):")
    for h in hits:
        # Match PC to label
        for s, name in installed:
            if h["PC"] == s[1]:
                log(f"  {name:40s}: cur_damage={h['cur_damage']}")
                break

    if cd_after == 3:
        log("\n=> Stab didn't apply STAB (no STAB matched)")
    elif cd_after in (4, 5):
        log("\n=> Stab applied correctly (~1.5×, possibly +type-passive ×31/30)")
    elif cd_after >= 12:
        log(f"\n=> Stab returned bug-shaped damage ({cd_after}, ratio {cd_after/3:.1f}×)")
        log("    *** BUG REPRODUCED IN ISOLATION — narrow down by inspecting hits ***")
    else:
        log(f"\n=> Unexpected wCurDamage={cd_after}")

    pyboy.stop(save=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
