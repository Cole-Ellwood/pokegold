#!/usr/bin/env python3
"""ROM-backed audit: Grass type-passive regrowth heals at the documented rate.

Why this exists as a ROM check and not a formula mirror
------------------------------------------------------
`python -m tools.debugger grass-regrowth` mirrors the intended formula in
Python. That mirror was green for months while the ROM was wrong, because the
bug was a register clobber, not a formula error: `.do_it` fetched the GRASS type
contribution into `d`, then called TypePassive_GetUserHPPointers_Far, which
returns `de` -> max HP and destroyed it. `d` became $CB/$D1 (the pointer's high
byte), `cp 2` never matched, and every Grass mon -- mono or dual -- healed at
the dual-type /64 rate. A level 17 Bayleef (max HP 54) healed 1 HP per turn
instead of 2, which reads on screen as "Grass regrowth is not working."

The same clobber survived an earlier targeted fix: GetMaxHP was given a
push/pop de precisely to protect this value (see engine/battle/core.asm
GetMaxHP), but `d` was already dead before GetMaxHP was ever reached, so the
mono branch stayed unreachable. A formula mirror cannot see any of that.

So this audit drives the real ROM: it seeds a synthetic between-turns state,
jumps to HandleTypePassiveRegrowth_Far, and asserts the actual HP delta against
the documented table, on both the mono and dual branch, across every cutoff
band. It also asserts `d` at the denominator pick is a type code (1 or 2) and
never a pointer high byte -- the direct signature of the clobber.

Documented rates (docs/mechanics_changes_from_base.md 1.3):
  full/mono Grass = max(1, floor((maxHP + 16) / 32))
  half/dual Grass = max(1, floor((maxHP + 32) / 64))
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

NORMAL, POISON, GRASS = 0, 3, 22
SENTINEL = 0x0008
BOOT_FRAMES = 600
RUN_BUDGET = 400

# (label, type1, type2, max_hp) -- expected heal is derived, not hardcoded.
CASES = [
    ("mono maxHP 40  (below first cutoff)", GRASS, GRASS, 40),
    ("mono maxHP 48  (first cutoff edge)", GRASS, GRASS, 48),
    ("mono maxHP 54  (L17 Bayleef)", GRASS, GRASS, 54),
    ("mono maxHP 79  (band top)", GRASS, GRASS, 79),
    ("mono maxHP 80  (band edge)", GRASS, GRASS, 80),
    ("mono maxHP 112 (fourth band)", GRASS, GRASS, 112),
    ("dual maxHP 54  (Grass/Poison)", GRASS, POISON, 54),
    ("dual maxHP 95  (band top)", GRASS, POISON, 95),
    ("dual maxHP 96  (band edge)", GRASS, POISON, 96),
]

REQUIRED_SYMBOLS = (
    "HandleTypePassiveRegrowth_Far",
    "HandleTypePassiveRegrowth_Far.shift",
)


def expected_heal(max_hp: int, mono: bool) -> int:
    if mono:
        return max(1, (max_hp + 16) // 32)
    return max(1, (max_hp + 32) // 64)


def skip(reason: str) -> int:
    print(f"SKIP: grass regrowth ROM audit ({reason})")
    return 0


def run_case(DebugSession, write_byte_banked, t1, t2, max_hp):
    """Boot a fresh session, seed the state, run the routine once.

    A fresh session per case is deliberate: the routine ends in
    StdBattleTextbox, which leaves synthetic UI state behind, and a reused
    session spins on the next case instead of returning.

    Returns (healed, d_at_denominator_pick, returned_cleanly) or a skip reason.
    """
    with DebugSession.open("pokegold") as sess:
        pb = sess.pyboy
        syms = sess.symbols
        for name in REQUIRED_SYMBOLS:
            if syms.get(name) is None:
                return f"symbol {name} missing from pokegold.sym"

        sess.tick(BOOT_FRAMES)

        def wr(sym_name, value, off=0):
            s = syms[sym_name]
            write_byte_banked(pb, s.address + off, value, s.bank)

        def wr_be16(sym_name, value):
            wr(sym_name, (value >> 8) & 0xFF, 0)
            wr(sym_name, value & 0xFF, 1)

        def rd_be16(sym_name):
            s = syms[sym_name]
            old = int(pb.memory[0xFF70])
            if 0xD000 <= s.address <= 0xDFFF and s.bank:
                pb.memory[0xFF70] = s.bank
            try:
                return (int(pb.memory[s.address]) << 8) | int(pb.memory[s.address + 1])
            finally:
                pb.memory[0xFF70] = old

        cur_hp = max_hp - 10

        # Player side under test.
        wr("wBattleMonType1", t1)
        wr("wBattleMonType1", t2, 1)          # wBattleMonType2 is +1
        wr("wBattleMonStatus", 0)
        wr_be16("wBattleMonMaxHP", max_hp)
        wr_be16("wBattleMonHP", cur_hp)
        # Enemy side pure Normal so its pass exits at the type gate.
        wr("wEnemyMonType1", NORMAL)
        wr("wEnemyMonType1", NORMAL, 1)
        wr("wEnemyMonStatus", 0)
        wr_be16("wEnemyMonMaxHP", 100)
        wr_be16("wEnemyMonHP", 100)
        wr("hSerialConnectionStatus", 0)
        wr("hBattleTurn", 0)

        captured = {}
        shift_sym = syms["HandleTypePassiveRegrowth_Far.shift"]
        sess.hook_register(
            shift_sym.bank, shift_sym.address,
            lambda _c: captured.setdefault("d", int(pb.register_file.D)), None,
        )

        entry = syms["HandleTypePassiveRegrowth_Far"]
        rf = pb.register_file
        new_sp = (int(rf.SP) - 2) & 0xFFFF
        pb.memory[new_sp] = SENTINEL & 0xFF
        pb.memory[new_sp + 1] = SENTINEL >> 8
        rf.SP = new_sp
        wr("hROMBank", entry.bank)
        pb.memory[0x2000] = entry.bank
        rf.PC = entry.address

        returned = [False]
        sess.hook_register(0x00, SENTINEL,
                           lambda _c: returned.__setitem__(0, True), None)
        ticked = 0
        while ticked < RUN_BUDGET and not returned[0]:
            sess.tick(2, False)
            ticked += 2

        return (rd_be16("wBattleMonHP") - cur_hp, captured.get("d"), returned[0])


def main() -> int:
    try:
        from tools.damage_debugger.emulator import DebugSession
        from tools.damage_debugger.safe_call import write_byte_banked
    except Exception as exc:  # pragma: no cover - environment guard
        return skip(f"debugger harness unavailable: {exc}")

    failures: list[str] = []
    rows: list[tuple[str, int, int, int, str]] = []

    for label, t1, t2, max_hp in CASES:
        mono = (t1 == t2)
        try:
            result = run_case(DebugSession, write_byte_banked, t1, t2, max_hp)
        except Exception as exc:
            return skip(f"pokegold ROM/symbols unavailable: {exc}")
        if isinstance(result, str):
            return skip(result)
        healed, d_val, returned = result
        want = expected_heal(max_hp, mono)

        status = "OK"
        if not returned:
            status = "FAIL(no-return)"
            failures.append(f"{label}: routine did not return in {RUN_BUDGET} frames")
        elif d_val is None:
            status = "FAIL(no-denom)"
            failures.append(f"{label}: never reached the denominator pick")
        elif d_val not in (1, 2):
            status = f"FAIL(d={d_val})"
            failures.append(
                f"{label}: d at denominator pick = {d_val} (0x{d_val:02X}), expected "
                "type code 1=dual or 2=mono. This is the register-clobber signature: "
                "d is holding a pointer high byte."
            )
        elif d_val != (2 if mono else 1):
            status = f"FAIL(d={d_val})"
            failures.append(
                f"{label}: d={d_val} but this case is "
                f"{'mono' if mono else 'dual'} (expected {2 if mono else 1})"
            )
        elif healed != want:
            status = "FAIL(heal)"
            failures.append(f"{label}: healed {healed} HP, documented rate is {want} HP")
        rows.append((label, max_hp, want, healed, status))

    width = max(len(r[0]) for r in rows)
    print(f"{'case'.ljust(width)}  maxHP  want  got  status")
    print("-" * (width + 26))
    for label, max_hp, want, got, status in rows:
        print(f"{label.ljust(width)}  {max_hp:5d}  {want:4d}  {got:3d}  {status}")
    print()

    if failures:
        print("FAIL: Grass regrowth does not match the documented rate.")
        for f in failures:
            print(f"  - {f}")
        print()
        print("Source: engine/battle/type_passive_damage_mods.asm "
              "HandleTypePassiveRegrowth_Far.do_it")
        print("Docs:   docs/mechanics_changes_from_base.md 1.3")
        return 1

    print(f"PASS: all {len(rows)} Grass regrowth cases heal at the documented rate")
    print("      (mono /32 and dual /64 branches both reachable and correct)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
