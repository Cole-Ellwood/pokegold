"""Load a boss state and continuously press A (boss factory pattern) until
BattleCommand_DamageCalc fires. The boss state captures the AI's chosen
move; pressing A advances through dialogs and animations."""

from __future__ import annotations

import sys
import time
from pathlib import Path

from pyboy import PyBoy

ROOT = Path("C:/Users/lolno/Downloads/pokemon gold hack")
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "boss_drive_v2.log"
STATES = ROOT / ".local" / "tmp" / "boss_state_factory"


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


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    def log(msg: str):
        sys.stdout.write(msg + "\n"); sys.stdout.flush()
        log_fh.write(msg + "\n"); log_fh.flush()

    rom = ROOT / "pokegold_trace.gbc"
    sym = ROOT / "pokegold_trace.sym"
    syms = parse_sym(sym)
    dc = syms["BattleCommand_DamageCalc"]
    ds_sym = syms.get("BattleCommand_DamageStats")
    log(f"DamageCalc @ ${dc[0]:02x}:{dc[1]:04x}")
    log(f"DamageStats @ ${ds_sym[0]:02x}:{ds_sym[1]:04x}" if ds_sym else "DamageStats: missing")

    state_files = sorted(STATES.glob("*_chosen_frame_*.state"))
    log(f"states: {len(state_files)}")

    # Try just the falkner state (early-game low complexity).
    target_state = None
    for s in state_files:
        if "falkner" in s.name:
            target_state = s; break
    if target_state is None:
        target_state = state_files[0]
    log(f"using: {target_state.name}")

    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    pyboy.set_emulation_speed(0)
    with open(target_state, "rb") as f:
        pyboy.load_state(f)

    hits_dc = []
    hits_ds = []
    def make_cb(label, store):
        def cb(_ctx):
            rf = pyboy.register_file
            snap = {
                "label": label,
                "A": int(rf.A), "B": int(rf.B), "C": int(rf.C),
                "D": int(rf.D), "E": int(rf.E),
                "HL": int(rf.HL), "PC": int(rf.PC),
            }
            store.append(snap)
            if len(store) <= 3:
                log(f"  {label} HIT #{len(store)}: d={snap['D']}(0x{snap['D']:02x}) "
                    f"e={snap['E']} b={snap['B']} c={snap['C']}")
        return cb

    pyboy.hook_register(dc[0], dc[1], make_cb("DC", hits_dc), None)
    if ds_sym:
        pyboy.hook_register(ds_sym[0], ds_sym[1], make_cb("DS", hits_ds), None)

    log("=== driving with A presses (45-frame wait, boss factory pattern) ===")
    t0 = time.time()
    a_presses = 0
    MAX_A = 300
    while a_presses < MAX_A and not (hits_dc or hits_ds):
        pyboy.button("a", delay=8)
        pyboy.tick(45, False, False)
        a_presses += 1
        if a_presses % 50 == 0:
            log(f"  ...{a_presses} presses, t={time.time()-t0:.1f}s, dc_hits={len(hits_dc)} ds_hits={len(hits_ds)}")
    log(f"final: {a_presses} A presses, t={time.time()-t0:.1f}s")
    log(f"DamageCalc hits: {len(hits_dc)}")
    log(f"DamageStats hits: {len(hits_ds)}")
    if hits_dc or hits_ds:
        log("\nFIRST 10 hits:")
        for h in (hits_dc + hits_ds)[:10]:
            log(f"  {h['label']}: d={h['D']}(0x{h['D']:02x}) e={h['E']} b={h['B']} c={h['C']} hl=0x{h['HL']:04x}")
    pyboy.stop(save=False)
    return 0 if (hits_dc or hits_ds) else 2


if __name__ == "__main__":
    sys.exit(main())
