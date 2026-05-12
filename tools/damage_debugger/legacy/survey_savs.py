"""Survey all *.sav files: load each, drive through Continue, read map +
party. Identify which save ends in a battle-accessible location."""

from __future__ import annotations

LEGACY_EXIT = (
    "tools.damage_debugger.legacy scripts are pruned one-shot drivers; "
    "use active tools.damage_debugger modules instead."
)
raise SystemExit(LEGACY_EXIT)

import sys
import shutil
from pathlib import Path

from pyboy import PyBoy

ROOT = Path("C:/Users/lolno/Downloads/pokemon gold hack")
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "sav_survey.log"


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


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    def log(msg):
        sys.stdout.write(msg + "\n"); sys.stdout.flush()
        fh.write(msg + "\n"); fh.flush()

    rom = ROOT / "pokegold.gbc"
    sym = ROOT / "pokegold.sym"
    syms = parse_sym(sym)
    party_cnt = syms["wPartyCount"]
    pml = syms["wPartyMon1Level"]
    pms = syms["wPartyMon1Species"]
    map_g = syms["wMapGroup"]
    map_n = syms["wMapNumber"]
    x_sym = syms["wXCoord"]
    y_sym = syms["wYCoord"]

    sav_files = sorted(ROOT.glob("*.sav"))
    log(f"surveying {len(sav_files)} .sav files")

    # Use a temp .sav swap so PyBoy auto-loads each one
    debug_sav = rom.with_suffix(".sav")
    backup = debug_sav.with_suffix(".sav.bak_survey")
    if debug_sav.exists() and not backup.exists():
        shutil.copy(debug_sav, backup)
        log(f"backed up {debug_sav.name} -> {backup.name}")

    results = []
    for sav in sav_files:
        if "bak" in sav.name: continue
        # Copy this sav over debug_sav so PyBoy auto-loads it
        shutil.copy(sav, debug_sav)

        try:
            pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
            pyboy.set_emulation_speed(0)
            pyboy.tick(1800, False, False)
            for btn in ("start", "a", "a", "a"):
                pyboy.button(btn, 8)
                pyboy.tick(180, False, False)
            # A few more A presses
            for _ in range(8):
                pyboy.button("a", 8)
                pyboy.tick(45, False, False)
            pc = read_byte(pyboy, party_cnt[1], party_cnt[0])
            mg = read_byte(pyboy, map_g[1], map_g[0])
            mn = read_byte(pyboy, map_n[1], map_n[0])
            x = read_byte(pyboy, x_sym[1], x_sym[0])
            y = read_byte(pyboy, y_sym[1], y_sym[0])
            lvl = read_byte(pyboy, pml[1], pml[0])
            sp = read_byte(pyboy, pms[1], pms[0])
            log(f"  {sav.name:<50s}: party={pc} map={mg}.{mn} pos=({x},{y}) starter=#{sp} lvl={lvl}")
            results.append({"sav": sav.name, "party": pc, "map": (mg, mn),
                            "pos": (x, y), "starter": sp, "level": lvl})
            pyboy.stop(save=False)
        except Exception as e:
            log(f"  {sav.name}: ERROR {e}")

    # Restore debug_sav
    if backup.exists():
        shutil.copy(backup, debug_sav)
        log(f"restored {debug_sav.name} from backup")

    log("\n=== Most promising for wild encounter (route grass) ===")
    # Map groups with wild grass: typical Johto routes
    wild_groups = {1, 2, 3, 4, 6, 8, 9, 10, 11, 12, 13, 14, 24, 25, 26}
    for r in results:
        mg, mn = r["map"]
        if r["party"] > 0 and mg in wild_groups:
            log(f"  {r['sav']}: map={mg}.{mn} party={r['party']} starter#{r['starter']} lvl{r['level']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
