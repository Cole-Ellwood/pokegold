"""Load each boss save state on pokegold_trace.gbc, hook BattleCommand_DamageCalc,
tick aggressively until the AI's chosen move resolves into damage calc.

Goal: capture b/c/d/e at the moment of damage so we can localize the bug.
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
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "boss_drive.log"
STATE_FACTORY = ROOT / ".local" / "tmp" / "boss_state_factory"


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
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
    def log(msg: str):
        sys.stdout.write(msg + "\n"); sys.stdout.flush()
        log_fh.write(msg + "\n"); log_fh.flush()

    rom = ROOT / "pokegold_trace.gbc"
    sym = ROOT / "pokegold_trace.sym"
    if not rom.exists() or not sym.exists():
        log(f"missing rom/sym: {rom} {sym}"); return 1
    syms = parse_sym(sym)
    dc = syms.get("BattleCommand_DamageCalc")
    if dc is None:
        log("no BattleCommand_DamageCalc"); return 1
    log(f"DamageCalc @ ${dc[0]:02x}:{dc[1]:04x}")

    states = sorted(STATE_FACTORY.glob("*_chosen_frame_*.state"))
    log(f"found {len(states)} boss states")

    summary = []
    for state_path in states[:5]:  # limit to first 5 to bound time
        log(f"\n=== {state_path.name} ===")
        pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
        pyboy.set_emulation_speed(0)
        with open(state_path, "rb") as f:
            pyboy.load_state(f)

        hits = []
        def make_hook(s_pyboy):
            def cb(_ctx):
                rf = s_pyboy.register_file
                snap = {
                    "A": int(rf.A), "B": int(rf.B), "C": int(rf.C),
                    "D": int(rf.D), "E": int(rf.E),
                    "HL": int(rf.HL), "SP": int(rf.SP),
                    "PC": int(rf.PC),
                }
                hits.append(snap)
                if len(hits) <= 3:
                    log(f"  HIT #{len(hits)}: d={snap['D']} (0x{snap['D']:02x}) "
                        f"e={snap['E']} b={snap['B']} c={snap['C']}")
            return cb
        pyboy.hook_register(dc[0], dc[1], make_hook(pyboy), None)

        # Tick aggressively. Each batch is 1000 frames; up to 50 batches = 50k frames
        # = ~14 minutes of GB time. Headless this is ~5 sec real time.
        t0 = time.time()
        for batch in range(50):
            pyboy.tick(1000, False, False)
            if hits:
                break
        log(f"  total ticks: {(batch+1)*1000}, hits: {len(hits)}, t={time.time()-t0:.1f}s")
        if hits:
            for i, h in enumerate(hits[:5]):
                log(f"    #{i+1}: d={h['D']:3d} e={h['E']:3d} b={h['B']:3d} c={h['C']:3d}  hl=0x{h['HL']:04x}")
            from collections import Counter
            c = Counter(h["D"] for h in hits)
            log(f"  d-distribution: {dict(c)}")
            if 208 in c:
                log("  *** d=208 SEEN — UPSTREAM CLOBBER ***")
            summary.append((state_path.name, hits[0]["D"], len(hits)))
        else:
            summary.append((state_path.name, None, 0))

        pyboy.stop(save=False)

    log(f"\n=== SUMMARY ===")
    for name, d_val, n in summary:
        log(f"  {name}: first_d={d_val} hits={n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
