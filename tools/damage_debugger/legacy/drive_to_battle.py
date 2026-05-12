"""Boot the probe ROM, navigate Title→Continue, walk to grass, fight.

Output:
- Per-DamageCalc-entry snapshot (b/c/d/e regs)
- Final wCurDamage value
- A save_state at the moment of the first DamageCalc hit, for fast re-runs

This is the operational live-capture: drives input headlessly until a
damage event fires, then captures.
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
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "drive_to_battle.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
STATE_OUT = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "first_damagecalc.state"


def parse_sym(path: Path) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.split(";", 1)[0].strip()
        parts = s.split()
        if len(parts) < 2 or ":" not in parts[0]:
            continue
        try:
            bank_s, addr_s = parts[0].split(":", 1)
            out[parts[1]] = (int(bank_s, 16), int(addr_s, 16))
        except ValueError:
            continue
    return out


def read_wram(pyboy, addr: int, bank: int = 1) -> int:
    if 0xD000 <= addr <= 0xDFFF and bank:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = bank
        try:
            return int(pyboy.memory[addr])
        finally:
            pyboy.memory[0xFF70] = old
    return int(pyboy.memory[addr])


class Logger:
    def __init__(self, path: Path):
        self.fh = open(path, "w", encoding="utf-8", buffering=1)

    def __call__(self, msg: str):
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()
        self.fh.write(msg + "\n")
        self.fh.flush()


def main(rom_name: str = "pokegold-probe-d-at-damagecalc.gbc",
         sym_name: str = "pokegold.sym",
         max_drive_frames: int = 200_000) -> int:
    log = Logger(LOG_PATH)
    rom_path = ROOT / rom_name
    sav_path = rom_path.with_suffix(".sav")
    sym_path = ROOT / sym_name

    log(f"rom: {rom_path.name}")
    log(f"sav: {sav_path.name} (exists={sav_path.exists()})")
    log(f"sym: {sym_path.name}")

    syms = parse_sym(sym_path)
    if "BattleCommand_DamageCalc" not in syms:
        log("FAIL: missing BattleCommand_DamageCalc")
        return 1
    dc_bank, dc_addr = syms["BattleCommand_DamageCalc"]
    cd_bank, cd_addr = syms["wCurDamage"]
    log(f"DamageCalc @ ${dc_bank:02x}:{dc_addr:04x}")

    ram_fh = open(sav_path, "rb") if sav_path.exists() else None
    pyboy = PyBoy(str(rom_path), window="null", sound=False, log_level="ERROR",
                  ram_file=ram_fh)
    pyboy.set_emulation_speed(0)

    hits = []
    def on_entry(_ctx):
        rf = pyboy.register_file
        snap = {
            "A": int(rf.A), "B": int(rf.B), "C": int(rf.C),
            "D": int(rf.D), "E": int(rf.E), "HL": int(rf.HL),
            "SP": int(rf.SP), "PC": int(rf.PC),
        }
        hits.append(snap)
        log(f"  *** HIT #{len(hits)}: d={snap['D']} (0x{snap['D']:02x}) "
            f"e={snap['E']} b={snap['B']} c={snap['C']} hl={snap['HL']:04x}")
        # Save state at first hit so subsequent runs can resume.
        if len(hits) == 1:
            with open(STATE_OUT, "wb") as fh:
                pyboy.save_state(fh)
            log(f"     state saved -> {STATE_OUT}")

    pyboy.hook_register(dc_bank, dc_addr, on_entry, None)

    log("=== boot to title (3000 frames) ===")
    pyboy.tick(3000, False, False)
    log(f"  PC=${int(pyboy.register_file.PC):04x}")

    log("=== title sequence: start, a (Continue) ===")
    for action in [("start", 6, 90), ("a", 6, 240)]:
        btn, hold, wait = action
        pyboy.button(btn, hold)
        pyboy.tick(wait, False, False)
        log(f"  pressed {btn}; PC=${int(pyboy.register_file.PC):04x}")
    party_cnt = read_wram(pyboy, 0xDA22, 1)
    log(f"  wPartyCount after Continue: {party_cnt}")

    if party_cnt == 0:
        log("  Continue did not load — try alt menu navigation")
        # Maybe it landed on "New Game"; press down once then A.
        pyboy.button("down", 6)
        pyboy.tick(60, False, False)
        pyboy.button("a", 6)
        pyboy.tick(180, False, False)
        party_cnt = read_wram(pyboy, 0xDA22, 1)
        log(f"  wPartyCount after alt: {party_cnt}")

    log("=== drive to encounter: walk + A spam ===")
    t0 = time.time()
    walk_pattern = [
        ("a", 4, 30), ("b", 4, 30),  # close any dialog
        ("down", 6, 30), ("down", 6, 30), ("down", 6, 30),
        ("right", 6, 30), ("right", 6, 30),
        ("up", 6, 30), ("left", 6, 30),
    ]
    drive_round = 0
    while time.time() - t0 < 60 and not hits:
        for btn, hold, wait in walk_pattern:
            if hits: break
            pyboy.button(btn, hold)
            pyboy.tick(wait, False, False)
        # Periodic A presses to advance any encountered dialog
        for _ in range(5):
            if hits: break
            pyboy.button("a", 4)
            pyboy.tick(30, False, False)
        drive_round += 1
        if drive_round % 10 == 0:
            mg = read_wram(pyboy, 0xDA00, 1)  # wMapGroup
            mn = read_wram(pyboy, 0xDA01, 1)  # wMapNumber
            x  = read_wram(pyboy, 0xDA03, 1)
            y  = read_wram(pyboy, 0xDA02, 1)
            bm = read_wram(pyboy, 0xD116, 1)  # wBattleMode
            log(f"  round {drive_round} t={time.time()-t0:.1f}s "
                f"map={mg}.{mn} x={x} y={y} battle_mode={bm} hits={len(hits)}")

    log(f"\n=== summary ({time.time()-t0:.1f}s drive) ===")
    log(f"hits: {len(hits)}")
    for i, h in enumerate(hits[:10]):
        log(f"  #{i+1}: d={h['D']:3d} (0x{h['D']:02x})  e={h['E']:3d}  "
            f"b={h['B']:3d}  c={h['C']:3d}  hl=0x{h['HL']:04x}  pc=0x{h['PC']:04x}")
    if hits:
        from collections import Counter
        c = Counter(h["D"] for h in hits)
        log(f"d-value distribution: {dict(c)}")
        # Read final wCurDamage
        cd = (read_wram(pyboy, cd_addr, cd_bank) << 8) | read_wram(pyboy, cd_addr+1, cd_bank)
        log(f"final wCurDamage: {cd}")
    pyboy.stop(save=False)
    if ram_fh: ram_fh.close()
    return 0 if hits else 2


if __name__ == "__main__":
    sys.exit(main())
