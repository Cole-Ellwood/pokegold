"""Load each boss save state and read mid-battle WRAM directly.

Boss states are captured at the AI's first move-decision moment of a
trainer battle. By that point the engine has populated wEnemyMon*
(boss's lead Pokemon) and wBattleMon* (player's lead). The values
should match the canonical computed-stat formula for that level.

If the values are 5x inflated (e.g., Falkner's Pidgeotto lvl 9 with
base atk 60 should have atk = (2*60*9)/100+5 = 15-16, but we see ~80),
the bug is in stat generation / load. If they're sane, the bug is
during damage execution itself."""

from __future__ import annotations

LEGACY_EXIT = (
    "tools.damage_debugger.legacy scripts are pruned one-shot drivers; "
    "use active tools.damage_debugger modules instead."
)
raise SystemExit(LEGACY_EXIT)

import sys
from pathlib import Path

from pyboy import PyBoy

ROOT = Path("C:/Users/lolno/Downloads/pokemon gold hack")
LOG_PATH = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger" / "boss_state_inspect.log"
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


def read_be_u16(pyboy, addr, bank=0):
    if 0xD000 <= addr <= 0xDFFF and bank:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = bank
        try:
            hi = int(pyboy.memory[addr])
            lo = int(pyboy.memory[addr+1])
        finally:
            pyboy.memory[0xFF70] = old
    else:
        hi = int(pyboy.memory[addr])
        lo = int(pyboy.memory[addr+1])
    return (hi << 8) | lo


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

    rom = ROOT / "pokegold_trace.gbc"
    sym = ROOT / "pokegold_trace.sym"
    syms = parse_sym(sym)

    state_files = sorted(STATES.glob("*_chosen_frame_*.state"))
    log(f"inspecting {len(state_files)} boss states")
    log(f"="*80)

    fields = [
        ("u8", "wEnemyMonSpecies"),
        ("u8", "wEnemyMonLevel"),
        ("u16be", "wEnemyMonHP"),
        ("u16be", "wEnemyMonMaxHP"),
        ("u16be", "wEnemyMonAttack"),
        ("u16be", "wEnemyMonDefense"),
        ("u16be", "wEnemyMonSpeed"),
        ("u16be", "wEnemyMonSpclAtk"),
        ("u16be", "wEnemyMonSpclDef"),
        ("u8", "wEnemyMonItem"),
        ("u8", "wEnemyMonType1"),
        ("u8", "wEnemyMonType2"),
        ("u8", "wBattleMonSpecies"),
        ("u8", "wBattleMonLevel"),
        ("u16be", "wBattleMonHP"),
        ("u16be", "wBattleMonAttack"),
        ("u16be", "wBattleMonDefense"),
        ("u16be", "wBattleMonSpeed"),
        ("u8", "wEnemyMoveStructPower"),
        ("u8", "wEnemyMoveStructType"),
        ("u8", "wEnemyMoveStructAnimation"),
        ("u8", "wPlayerMoveStructPower"),
        ("u8", "wCurEnemyMove"),
        ("u8", "wCurPlayerMove"),
        ("u8", "wBattleMode"),
        ("u8", "hBattleTurn"),
        ("u8", "wEnemyAtkLevel"),
        ("u8", "wEnemyDefLevel"),
        ("u8", "wPlayerAtkLevel"),
        ("u8", "wPlayerDefLevel"),
    ]

    for state_path in state_files:
        boss = state_path.name.split("_chosen")[0]
        log(f"\n[{boss}] {state_path.name}")
        pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
        pyboy.set_emulation_speed(0)
        with open(state_path, "rb") as f:
            pyboy.load_state(f)
        for kind, name in fields:
            s = syms.get(name)
            if s is None:
                continue
            if kind == "u8":
                v = read_byte(pyboy, s[1], s[0])
                log(f"  {name:<30s}: {v:5d}  (0x{v:02x})")
            else:
                v = read_be_u16(pyboy, s[1], s[0])
                log(f"  {name:<30s}: {v:5d}  (0x{v:04x})")
        pyboy.stop(save=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
