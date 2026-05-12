"""Inspect what state pokegold-probe-d-at-damagecalc.sav loads into."""

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
    rom = ROOT / "pokegold-probe-d-at-damagecalc.gbc"
    sym = ROOT / "pokegold.sym"
    syms = parse_sym(sym)

    pyboy = PyBoy(str(rom), window="null", sound=False, log_level="ERROR")
    pyboy.set_emulation_speed(0)

    print(f"loaded {rom.name}")
    print(f"cart type: {pyboy.cartridge_title!r}")
    print(f"sav exists: {(rom.with_suffix('.sav')).exists()} size={(rom.with_suffix('.sav')).stat().st_size if (rom.with_suffix('.sav')).exists() else 'n/a'}")
    pyboy.tick(1800, False, False)
    print(f"after 1800 ticks PC=${int(pyboy.register_file.PC):04x}")
    # Also try reading via SVBK bank-switch trick
    old_svbk = int(pyboy.memory[0xFF70])
    print(f"SVBK={old_svbk}")
    for bank in (1, 2, 3, 4, 5, 6, 7):
        pyboy.memory[0xFF70] = bank
        v = int(pyboy.memory[0xDA00])
        print(f"  via SVBK={bank}: $DA00 = {v}")
    pyboy.memory[0xFF70] = old_svbk

    keys = ["wMapGroup", "wMapNumber", "wPlayerState", "wXCoord", "wYCoord",
            "wPartyCount", "wBattleMode", "wPlayerDirection",
            "wPartyMon1Species", "wPartyMon1Level", "wPartyMon1HP",
            "wPartyMon1Move1", "wPlayerName"]
    for k in keys:
        s = syms.get(k)
        if s is None:
            print(f"  {k}: missing in sym")
            continue
        b, a = s
        try:
            v = int(pyboy.memory[a]) if a < 0x8000 else int(pyboy.memory[b, a])
        except Exception as e:
            v = f"ERR({e})"
        print(f"  {k:<24} ${b:02x}:{a:04x} = {v}")

    # Also try sending a few inputs and see if anything moves
    print("\n--- sending inputs and watching wXCoord/wYCoord ---")
    s_x = syms.get("wXCoord")
    s_y = syms.get("wYCoord")
    if s_x and s_y:
        for cmd, hold in [("a", 4), ("a", 4), ("start", 4), ("a", 4),
                          ("b", 4), ("b", 4),
                          ("down", 8), ("down", 8), ("right", 8),
                          ("a", 4), ("a", 4)]:
            pyboy.button(cmd, hold)
            pyboy.tick(60, False, False)
            x = int(pyboy.memory[s_x[1]])
            y = int(pyboy.memory[s_y[1]])
            print(f"  after {cmd:6s}: x={x} y={y} PC=${int(pyboy.register_file.PC):04x}")

    pyboy.stop(save=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
