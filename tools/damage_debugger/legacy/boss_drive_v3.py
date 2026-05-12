"""Load boss state, drive A heavily with state monitoring.

Probe wBattleMode/wBattlePlayerAction/wBossAITraceChosenMove etc each
batch to understand what state the engine is in.
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
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "boss_drive_v3.log"
DAMAGE_OUT = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "boss_first_damage.state"
STATES = ROOT / ".local" / "tmp" / "boss_state_factory"


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

    rom = ROOT / "pokegold_trace.gbc"
    sym = ROOT / "pokegold_trace.sym"
    syms = parse_sym(sym)
    sav = rom.with_suffix(".sav")

    state_path = STATES / "falkner_chosen_frame_4655.state"
    if not state_path.exists():
        log(f"FAIL: missing {state_path}")
        return 1

    ram_fh = open(sav, "rb") if sav.exists() else None
    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR",
                  ram_file=ram_fh)
    pyboy.set_emulation_speed(0)
    with open(state_path, "rb") as f:
        pyboy.load_state(f)
    log(f"loaded {state_path.name}")

    # Inspect initial state
    for name in ("wBattleMode", "wBattlePlayerAction", "wEnemyMonSpecies",
                 "wEnemyMonLevel", "wCurEnemyMove", "wCurPlayerMove",
                 "wPlayerAction", "wEnemyAction"):
        s = syms.get(name)
        if s is not None:
            v = read_byte(pyboy, s[1], s[0])
            log(f"  init {name} = {v}  (0x{v:02x})")

    # Hook DamageCalc + DamageStats
    dc = syms["BattleCommand_DamageCalc"]
    ds = syms.get("BattleCommand_DamageStats")
    do_move = syms.get("DoMove")
    do_player_turn = syms.get("DoPlayerTurn")
    do_enemy_turn = syms.get("DoEnemyTurn")

    hits_dc, hits_ds, hits_dm, hits_pt, hits_et = [], [], [], [], []

    def make_cb(store, label, save_state_too=False):
        def cb(_):
            rf = pyboy.register_file
            store.append({"label": label,
                          "A": int(rf.A), "B": int(rf.B), "C": int(rf.C),
                          "D": int(rf.D), "E": int(rf.E),
                          "HL": int(rf.HL), "PC": int(rf.PC)})
            if save_state_too and len(store) == 1:
                with open(DAMAGE_OUT, "wb") as fh:
                    pyboy.save_state(fh)
            if len(store) <= 3:
                snap = store[-1]
                log(f"  *** {label} HIT #{len(store)}: d={snap['D']}(0x{snap['D']:02x}) "
                    f"e={snap['E']} b={snap['B']} c={snap['C']}")
        return cb

    pyboy.hook_register(dc[0], dc[1], make_cb(hits_dc, "DC", save_state_too=True), None)
    if ds:
        pyboy.hook_register(ds[0], ds[1], make_cb(hits_ds, "DS"), None)
    if do_move:
        pyboy.hook_register(do_move[0], do_move[1], make_cb(hits_dm, "DoMove"), None)
    if do_player_turn:
        pyboy.hook_register(do_player_turn[0], do_player_turn[1], make_cb(hits_pt, "PT"), None)
    if do_enemy_turn:
        pyboy.hook_register(do_enemy_turn[0], do_enemy_turn[1], make_cb(hits_et, "ET"), None)

    # Aggressive drive
    log("\n=== driving 1000 A presses with state monitoring ===")
    t0 = time.time()
    last_state = None
    for round_no in range(1000):
        pyboy.button("a", 8)
        pyboy.tick(45, False, False)
        if hits_dc:
            log(f"  damage hit at round {round_no} t={time.time()-t0:.1f}s")
            break
        if round_no % 50 == 0:
            bm = read_byte(pyboy, syms["wBattleMode"][1], syms["wBattleMode"][0])
            cur_em = read_byte(pyboy, syms["wCurEnemyMove"][1], syms["wCurEnemyMove"][0])
            cur_pm = read_byte(pyboy, syms["wCurPlayerMove"][1], syms["wCurPlayerMove"][0])
            ds_n = len(hits_ds)
            dm_n = len(hits_dm)
            pt_n = len(hits_pt)
            et_n = len(hits_et)
            line = f"  round {round_no:4d} t={time.time()-t0:.1f}s bm={bm} curEM={cur_em} curPM={cur_pm} DS={ds_n} DM={dm_n} PT={pt_n} ET={et_n}"
            if line != last_state:
                log(line)
                last_state = line
    log(f"\n=== summary t={time.time()-t0:.1f}s ===")
    log(f"DamageCalc={len(hits_dc)} DamageStats={len(hits_ds)} DoMove={len(hits_dm)} "
        f"PlayerTurn={len(hits_pt)} EnemyTurn={len(hits_et)}")
    if hits_dc:
        for i, h in enumerate(hits_dc[:5]):
            log(f"  DC #{i+1}: d={h['D']}(0x{h['D']:02x}) e={h['E']} b={h['B']} c={h['C']}")

    pyboy.stop(save=False)
    if ram_fh: ram_fh.close()
    return 0 if hits_dc else 2


if __name__ == "__main__":
    sys.exit(main())
