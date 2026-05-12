"""Live capture against pokegold-probe-d-at-damagecalc.gbc.

The probe ROM (commit 08c02370 on branch claude/probe-d-damagecalc-2026-05-04)
replaced BattleCommand_DamageCalc's body with:

    BattleCommand_DamageCalc:
        xor a
        ld [wCurDamage], a
        ld a, d
        ld [wCurDamage + 1], a
        ld a, 1
        and a
        ret

So at the moment damagecalc would normally fire, wCurDamage gets the
value of register d (the move's BP arg).

If d == 40 (Tackle's BP), the upstream d-pass is correct → bug is in
the inner damage formula.
If d == 208 (=$D0=HIGH(wEnemyMonItem)), the d-clobber is upstream →
need to find which function corrupted d.

This script:
1. Loads the probe ROM with its companion .sav (battery save)
2. Hooks BattleCommand_DamageCalc on entry
3. Drives the game with periodic A presses to advance through whatever
   dialog / menus the save state lands in
4. Captures every entry hit and the final wCurDamage
"""

from __future__ import annotations

LEGACY_EXIT = (
    "tools.damage_debugger.legacy scripts are pruned one-shot drivers; "
    "use active tools.damage_debugger modules instead."
)
raise SystemExit(LEGACY_EXIT)

import os
import sys
import time
from pathlib import Path

from pyboy import PyBoy

ROOT = Path("C:/Users/lolno/Downloads/pokemon gold hack")
PROBE_ROM = ROOT / "pokegold-probe-d-at-damagecalc.gbc"
PROBE_SYM = ROOT / "pokegold.sym"  # probe doesn't have its own sym; main syms are close
PROBE_SAV = ROOT / "pokegold-probe-d-at-damagecalc.sav"

LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "live_probe.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def log(msg: str, fh=None) -> None:
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()
    if fh:
        fh.write(msg + "\n")
        fh.flush()


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


def main() -> int:
    log_fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    log(f"probe ROM: {PROBE_ROM}", log_fh)
    log(f"sym:       {PROBE_SYM}", log_fh)
    log(f"sav:       {PROBE_SAV}", log_fh)

    if not PROBE_ROM.exists():
        log("FAIL: probe ROM missing", log_fh)
        return 1
    if not PROBE_SYM.exists():
        log("FAIL: sym missing", log_fh)
        return 1

    syms = parse_sym(PROBE_SYM)
    dc = syms.get("BattleCommand_DamageCalc")
    if dc is None:
        log("FAIL: BattleCommand_DamageCalc not in sym", log_fh)
        return 1
    log(f"DamageCalc at ${dc[0]:02x}:{dc[1]:04x}", log_fh)

    # PyBoy auto-loads <rom-stem>.sav next to the ROM, so the .sav with
    # matching name will load automatically.
    pyboy = PyBoy(str(PROBE_ROM), window="null", sound=False, log_level="ERROR")
    set_speed = getattr(pyboy, "set_emulation_speed", None)
    if set_speed is not None:
        set_speed(0)

    # Hook DamageCalc entry to capture d (move BP) which the probe writes
    # to wCurDamage+1. We snapshot wCurDamage AFTER the function returns
    # because the probe explicitly writes there.
    hits: list[dict] = []
    cur_damage_sym = syms.get("wCurDamage")
    if cur_damage_sym is None:
        log("FAIL: wCurDamage not in sym", log_fh)
        return 1
    cd_bank, cd_addr = cur_damage_sym

    def on_entry(_ctx):
        rf = pyboy.register_file
        # Snapshot incoming registers — these are the args.
        snap = {
            "A": int(rf.A), "B": int(rf.B), "C": int(rf.C),
            "D": int(rf.D), "E": int(rf.E),
            "HL": int(rf.HL), "SP": int(rf.SP),
        }
        hits.append(snap)
        log(f"  HIT #{len(hits)}: A={snap['A']:02x} BC={snap['B']:02x}{snap['C']:02x} "
            f"DE={snap['D']:02x}{snap['E']:02x} HL={snap['HL']:04x} SP={snap['SP']:04x} "
            f"  (d={snap['D']} as decimal = supposed move BP)", log_fh)

    pyboy.hook_register(dc[0], dc[1], on_entry, None)

    log("=== boot phase: 1800 frames ===", log_fh)
    t0 = time.time()
    pyboy.tick(1800, False, False)
    log(f"boot done in {time.time()-t0:.1f}s", log_fh)

    log("=== drive phase: alternate A/down/right + tick ===", log_fh)
    t0 = time.time()
    BUTTONS = ["a", "a", "a", "down", "down", "right", "a", "down", "a"]
    pre_drive_hits = len(hits)
    for round_no in range(60):  # 60 rounds * ~9 button presses = 540 button events
        for btn in BUTTONS:
            try:
                pyboy.button(btn, delay=8)
            except TypeError:
                pyboy.button(btn, 8)
            pyboy.tick(40, False, False)
        if (round_no + 1) % 10 == 0:
            elapsed = time.time() - t0
            log(f"  round {round_no+1}/60 t={elapsed:.1f}s hits_so_far={len(hits)}", log_fh)
        # If we've already captured many hits, that's enough.
        if len(hits) > 5:
            log(f"  early-stop: captured {len(hits)} hits", log_fh)
            break
    log(f"drive done in {time.time()-t0:.1f}s, total hits={len(hits)}", log_fh)

    if hits:
        log("\n=== summary of DamageCalc entry hits ===", log_fh)
        for i, h in enumerate(hits[:20]):
            log(f"  #{i+1}: d={h['D']:3d} ({h['D']:02x}h)  e={h['E']:3d}  "
                f"b={h['B']:3d}  c={h['C']:3d}  hl={h['HL']:04x}", log_fh)
        # Check for d=208 (=$D0) hint
        d_values = [h["D"] for h in hits]
        from collections import Counter
        c = Counter(d_values)
        log(f"\n  d-value frequency: {dict(c.most_common(10))}", log_fh)
        if 208 in c:
            log(f"  *** d=208 ($D0) seen — likely upstream d-clobber ***", log_fh)
        if 40 in c:
            log(f"  *** d=40 (Tackle BP) seen — d is correct upstream ***", log_fh)
    else:
        log("NO DamageCalc hits during the drive — battery save did not lead to a battle", log_fh)

    pyboy.stop(save=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
