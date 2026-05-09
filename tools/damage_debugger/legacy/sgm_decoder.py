"""Parse VBA .sgm save states to extract wCurDamage from the probe ROM.

The probe ROM (08c02370) replaced BattleCommand_DamageCalc body with code
that writes the value of register d (the move's BP arg) to wCurDamage+1.

If the bug is upstream of DamageCalc, d will be wrong (e.g. 208=$D0 from
HIGH(wEnemyMonItem)). The .sgm files debug1.sgm (turn 1 start) and
debug2.sgm (turn 2 start) capture WRAM at those moments — wCurDamage in
debug2.sgm shows what d was during turn 1's attack.

Per the investigation doc, three party-signature occurrences exist in
the .sgm; we anchor on each and dump nearby memory to find which is the
live WRAM.
"""

from __future__ import annotations

import gzip
import sys
from pathlib import Path
from typing import Iterable

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


def find_signatures(data: bytes, sig: bytes) -> list[int]:
    out = []
    i = 0
    while True:
        j = data.find(sig, i)
        if j < 0: break
        out.append(j)
        i = j + 1
    return out


def hexdump(data: bytes, start: int = 0, count: int = 64) -> str:
    out_lines = []
    for off in range(0, count, 16):
        if off + start >= len(data): break
        chunk = data[start + off: start + off + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join((chr(b) if 0x20 <= b < 0x7F else ".") for b in chunk)
        out_lines.append(f"  {start+off:06x}  {hex_part:<48}  {ascii_part}")
    return "\n".join(out_lines)


def score_wram_liveness(data: bytes, base: int) -> tuple[int, str]:
    """Score how 'live' a region is. Higher = more likely real WRAM."""
    region = data[base : base + 0x1000]
    if len(region) < 0x1000:
        return -1, "truncated"
    # Liveness signals: variety of byte values, presence of typical WRAM patterns.
    unique_bytes = len(set(region))
    zero_count = region.count(0)
    # Repetitive 39 00 39 00 pattern = NOT WRAM
    pattern_3900 = sum(1 for i in range(0, len(region) - 1, 2) if region[i] == 0x39 and region[i+1] == 0)
    score = unique_bytes - (pattern_3900 // 4) - max(0, zero_count - 0x800)
    return score, f"unique={unique_bytes} zeros={zero_count} 39_00_pattern={pattern_3900}"


def main() -> int:
    syms = parse_sym(ROOT / "pokegold.sym")
    cur_damage = syms["wCurDamage"]
    party_count = syms["wPartyCount"]
    party_species = syms["wPartyMon1Species"]
    print(f"wCurDamage @ ${cur_damage[0]:02x}:{cur_damage[1]:04x}")
    print(f"wPartyCount @ ${party_count[0]:02x}:{party_count[1]:04x}")
    print(f"wPartyMon1Species @ ${party_species[0]:02x}:{party_species[1]:04x}")
    print()

    # The investigation doc gives the party signature (wPartyCount=5 + species
    # ids). We try multiple plausible signatures depending on what was in the
    # user's party at probe time.
    candidate_sigs = [
        # From the doc, exact byte sequence
        bytes([0x05, 0x4a, 0x9c, 0x60, 0xa7, 0xa3, 0xff]),
        # Other plausible party sigs (just count + species)
    ]

    for sgm_name in ["debug1.sgm", "debug2.sgm"]:
        path = ROOT / sgm_name
        if not path.exists():
            print(f"missing: {path}")
            continue
        with gzip.open(path, "rb") as f:
            data = f.read()
        print(f"=== {sgm_name} ({len(data)} bytes decompressed) ===")

        all_positions: list[tuple[int, str]] = []
        for sig in candidate_sigs:
            positions = find_signatures(data, sig)
            print(f"  signature {sig.hex()}: {len(positions)} hits {[hex(p) for p in positions]}")
            for p in positions:
                all_positions.append((p, sig.hex()))

        if not all_positions:
            # Fall back: search for wPartyCount value alone (between 1-6).
            # Too many false positives; instead search for the cur_damage offset
            # within candidate WRAM bases.
            print("  no party sig hits; trying alternative anchors")
            continue

        for pos, sig in all_positions:
            # wPartyCount is at $DA22 -> file offset = pos. So $D000 base = pos - $A22
            base = pos - 0xA22
            if base < 0:
                continue
            score, info = score_wram_liveness(data, base)
            print(f"  pos=0x{pos:05x} (sig={sig}) -> base=0x{base:05x} -> {info} score={score}")
            if True:  # always probe; let the value tell us
                # Read wCurDamage at base + (cur_damage_addr - 0xD000) = base + ($D141 - $D000) = base + 0x141
                cd_off = base + (cur_damage[1] - 0xD000)
                if cd_off + 1 < len(data):
                    hi = data[cd_off]
                    lo = data[cd_off + 1]
                    cd_word = (hi << 8) | lo
                    print(f"    => wCurDamage[hi,lo] = [0x{hi:02x}, 0x{lo:02x}]  word={cd_word}")
                    # The probe writes d to wCurDamage+1 (low byte). hi should be 0.
                    print(f"       d (low byte) = {lo}")
                    if lo == 40:
                        print(f"       *** d=40 (Tackle BP) — d is CORRECT upstream ***")
                    elif lo == 208:
                        print(f"       *** d=208 ($D0) — UPSTREAM d-CLOBBER ***")
                    elif lo == 210:
                        print(f"       *** d=210 ($D2) — different upstream clobber ***")
                    elif lo == 2:
                        print(f"       *** d=2 — boost helper *_DEN leaked, wrapper fix incomplete ***")
                    else:
                        print(f"       *** d=$%02x (%d) — unknown clobber, narrow it ***" % (lo, lo))
                # Also dump nearby region
                print("    " + hexdump(data, max(0, cd_off - 16), 48).replace("\n", "\n    "))

                # Verify the candidate WRAM by reading other known symbols
                interesting = [
                    "wPartyMon1Species", "wPartyMon1Level",
                    "wEnemyMonSpecies", "wEnemyMonLevel", "wEnemyMonHP",
                    "wEnemyMonAttack", "wEnemyMonDefense", "wEnemyMonSpeed",
                    "wEnemyMonSpclAtk", "wEnemyMonSpclDef",
                    "wEnemyMonItem", "wEnemyMonType1", "wEnemyMonType2",
                    "wEnemyMoveStructPower", "wPlayerMoveStructPower",
                    "wBattleMode", "wCurOTMon", "wMapNumber", "wMapGroup",
                    "wXCoord", "wYCoord", "hBattleTurn",
                    "wPlayerName",
                    "wBattleMonSpecies", "wBattleMonLevel", "wBattleMonHP", "wBattleMonMaxHP",
                    "wBattleMonAttack", "wBattleMonDefense", "wBattleMonSpeed",
                    "wBattleMonSpclAtk", "wBattleMonSpclDef",
                    "wBattleMonType1", "wBattleMonType2",
                    "wPlayerAttack", "wPlayerDefense", "wEnemyAttack", "wEnemyDefense",
                    "wCurEnemyMove", "wCurPlayerMove", "wCurDamage",
                    "wPlayerAtkLevel", "wPlayerDefLevel", "wEnemyAtkLevel", "wEnemyDefLevel",
                    "wCriticalHit", "wTypeMatchup",
                ]
                for name in interesting:
                    s = syms.get(name)
                    if s is None: continue
                    if s[1] < 0xC000 or s[1] >= 0xE000: continue
                    off = base + (s[1] - 0xD000)
                    if off < 0 or off >= len(data): continue
                    if name == "wPlayerName":
                        bs = data[off:off+8]
                        print(f"    {name:<24}: {bs.hex()} ({bs})")
                    elif name in ("wPartyMon1HP", "wEnemyMonHP", "wCurDamage",
                                  "wEnemyMonAttack", "wEnemyMonDefense",
                                  "wBattleMonAttack", "wBattleMonDefense"):
                        v = (data[off] << 8) | data[off+1]
                        print(f"    {name:<24}: {v}  ({data[off]:02x} {data[off+1]:02x})")
                    else:
                        v = data[off]
                        print(f"    {name:<24}: {v}  (0x{v:02x})")
                print()
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
