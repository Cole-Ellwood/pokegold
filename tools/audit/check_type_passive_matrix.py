#!/usr/bin/env python3
"""ROM-backed audit: every type passive, at mono (full) and dual (half) strength.

Companion to check_grass_regrowth_rom.py, same reasoning: the mono/dual split in
every passive is selected by a small integer (1=dual, 2=mono) that travels from a
contribution helper to a `cp 2`. When that integer gets clobbered en route, the
mono branch becomes unreachable and every mon silently gets the weaker dual rate.
Two shipped instances of exactly that:

  - Grass regrowth: contribution parked in d across a call that returns d -> max
    HP. Every Grass mon healed at the dual /64 rate. (check_grass_regrowth_rom.py)
  - ApplyPrzEffectOnSpeed_Far: the Electric section overwrites d (the types
    pointer high byte) with its denominator, so the Fighting check that follows
    read types out of ROM0. Paralyzed Raichu/Electabuzz (Electric/Fighting in
    this hack) got the vanilla 1/4 Speed penalty instead of half-Fighting 3/8.

Neither was visible to a Python reimplementation of the intended formula, so this
drives the real routines: seed a synthetic battle state, jump to the passive, read
the number back out, compare against docs/mechanics_changes_from_base.md 1.3.

Every passive is checked at BOTH strengths, and the two strengths are required to
produce DIFFERENT numbers -- that difference is what the clobber class destroys.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Type constants (constants/type_constants.asm)
NORMAL, FIGHTING, FLYING, POISON, GROUND, ROCK = 0, 1, 2, 3, 4, 5
BUG, GHOST, STEEL = 7, 8, 9
FIRE, WATER, GRASS, ELECTRIC, PSYCHIC_TYPE, ICE, DRAGON, DARK = 20, 21, 22, 23, 24, 25, 26, 27

STAB_DAMAGE = 0x80          # const_def 7; shift_const STAB_DAMAGE
EFFECTIVE, SUPER_EFFECTIVE = 10, 20
PSN_BIT, BRN_BIT, PAR_BIT = 1 << 3, 1 << 4, 1 << 6
MOVE_ANIM, MOVE_TYPE = 0, 3

BOOT_FRAMES = 600
RUN_BUDGET = 4800
BASE_DAMAGE = 200

# Return-detection trap: 2 free HRAM bytes just below IE at $FFFF, holding
# `jr -2`. Do NOT use $0008 as a sentinel -- that is the FarCall RST vector the
# battle engine invokes constantly, so a hook there fires spuriously mid-routine
# (see tools/damage_debugger/safe_call.py, which exists for this reason). With
# the HRAM trap the CPU spins in place after the function returns, leaving
# registers and battle RAM frozen at their post-return values.
SENTINEL_ADDR = 0xFFFD


def pct(n: int) -> int:
    """`N percent` == `N * $ff / 100` (macros/data.asm)."""
    return n * 0xFF // 100


def frac(value: int, num: int, den: int, min_one: bool = True) -> int:
    out = value * num // den
    return max(1, out) if min_one else out


# --- Damage modifiers, all through TypePassive_ApplyDamageModifiers_Far ---
# Baseline arms nothing: FLYING is inert on both sides in this routine (user side
# checks NORMAL/FIRE/GHOST, defender side checks DRAGON/GROUND/ROCK/BUG/WATER/ICE).
DMG_BASELINE = dict(
    user_types=(FLYING, FLYING), foe_types=(FLYING, FLYING),
    type_modifier=0, move_type=NORMAL, critical=0, matchup=EFFECTIVE,
    user_hp=100, user_max=100, foe_hp=100, foe_max=100, foe_status=0,
)

DMG_CASES = [
    # (label, doc rate half, doc rate full, overrides for half, overrides for full)
    ("Normal STAB enhancer", (31, 30), (16, 15),
     dict(type_modifier=STAB_DAMAGE, move_type=NORMAL, user_types=(NORMAL, FLYING)),
     dict(type_modifier=STAB_DAMAGE, move_type=NORMAL, user_types=(NORMAL, NORMAL))),
    ("Fire attacker below 1/3 HP", (11, 10), (6, 5),
     dict(move_type=FIRE, user_hp=10, user_types=(FIRE, FLYING)),
     dict(move_type=FIRE, user_hp=10, user_types=(FIRE, FIRE))),
    ("Ghost attacker vs statused foe", (21, 20), (11, 10),
     dict(foe_status=PSN_BIT, user_types=(GHOST, FLYING)),
     dict(foe_status=PSN_BIT, user_types=(GHOST, GHOST))),
    ("Imperial Scales (Dragon defender)", (2, 3), (1, 2),
     dict(matchup=EFFECTIVE, foe_types=(DRAGON, FLYING)),
     dict(matchup=EFFECTIVE, foe_types=(DRAGON, DRAGON))),
    ("Ground defender, super-effective hit", (19, 20), (9, 10),
     dict(matchup=SUPER_EFFECTIVE, foe_types=(GROUND, FLYING)),
     dict(matchup=SUPER_EFFECTIVE, foe_types=(GROUND, GROUND))),
    ("Rock defender, critical hit", (19, 20), (9, 10),
     dict(critical=1, foe_types=(ROCK, FLYING)),
     dict(critical=1, foe_types=(ROCK, ROCK))),
    ("Bug defender vs physical", (19, 20), (9, 10),
     dict(move_type=NORMAL, foe_types=(BUG, FLYING)),
     dict(move_type=NORMAL, foe_types=(BUG, BUG))),
    ("Water defender vs special", (39, 40), (19, 20),
     dict(move_type=WATER, foe_types=(WATER, FLYING)),
     dict(move_type=WATER, foe_types=(WATER, WATER))),
    ("Ice defender above half HP", (39, 40), (19, 20),
     dict(foe_hp=100, foe_types=(ICE, FLYING)),
     dict(foe_hp=100, foe_types=(ICE, ICE))),
]


def skip(reason: str) -> int:
    print(f"SKIP: type passive matrix audit ({reason})")
    return 0


class Harness:
    """Seeds synthetic battle state and invokes a passive on the real ROM."""

    def __init__(self, sess):
        self.sess = sess
        self.pb = sess.pyboy
        self.syms = sess.symbols
        from tools.damage_debugger.safe_call import write_byte_banked
        self._wb = write_byte_banked
        # Baseline snapshot taken after boot. Every case restores it first, so
        # cases cannot contaminate each other: once a routine returns to the
        # sentinel the ROM keeps executing from $0008 (the RST FarCall vector)
        # with synthetic state, and that wild execution must not leak forward.
        self._baseline = io.BytesIO()
        self.pb.save_state(self._baseline)

    def reset(self):
        self._baseline.seek(0)
        self.pb.load_state(self._baseline)

    def wr(self, name, value, off=0):
        s = self.syms[name]
        self._wb(self.pb, s.address + off, value, s.bank)

    def wr_be16(self, name, value):
        self.wr(name, (value >> 8) & 0xFF, 0)
        self.wr(name, value & 0xFF, 1)

    def rd_be16(self, name):
        s = self.syms[name]
        old = int(self.pb.memory[0xFF70])
        if 0xD000 <= s.address <= 0xDFFF and s.bank:
            self.pb.memory[0xFF70] = s.bank
        try:
            return (int(self.pb.memory[s.address]) << 8) | int(self.pb.memory[s.address + 1])
        finally:
            self.pb.memory[0xFF70] = old

    def invoke(self, func_name, regs_in=None):
        """Jump to func_name and run until it returns into the HRAM trap.

        Returns the exit register file, or None if the routine never returned.
        Battle RAM is safe to read afterwards: the CPU is parked in the trap
        loop, not executing further ROM.
        """
        entry = self.syms[func_name]
        rf = self.pb.register_file
        # Mask all interrupts: we hijack PC/SP, so a VBlank arriving mid-routine
        # hands control to the real game loop and never returns here.
        self.pb.memory[0xFFFF] = 0x00
        self.pb.memory[0xFF0F] = 0x00
        self.pb.memory[SENTINEL_ADDR] = 0x18      # jr
        self.pb.memory[SENTINEL_ADDR + 1] = 0xFE  # -2
        new_sp = (int(rf.SP) - 2) & 0xFFFF
        self.pb.memory[new_sp] = SENTINEL_ADDR & 0xFF
        self.pb.memory[new_sp + 1] = SENTINEL_ADDR >> 8
        rf.SP = new_sp
        for reg, val in (regs_in or {}).items():
            setattr(rf, reg, val)
        self.wr("hROMBank", entry.bank)
        self.pb.memory[0x2000] = entry.bank
        rf.PC = entry.address

        ticked = 0
        while ticked < RUN_BUDGET:
            self.pb.tick(2, False, False)
            ticked += 2
            if int(rf.PC) in (SENTINEL_ADDR, SENTINEL_ADDR + 2):
                return {"A": int(rf.A), "B": int(rf.B), "C": int(rf.C),
                        "BC": (int(rf.B) << 8) | int(rf.C)}
        return None

    # --- per-group drivers ---

    def damage_mod(self, cfg):
        c = dict(DMG_BASELINE)
        c.update(cfg)
        self.reset()
        self.wr("hBattleTurn", 0)
        self.wr("wBattleMonType1", c["user_types"][0])
        self.wr("wBattleMonType1", c["user_types"][1], 1)
        self.wr("wEnemyMonType1", c["foe_types"][0])
        self.wr("wEnemyMonType1", c["foe_types"][1], 1)
        self.wr("wTypeModifier", c["type_modifier"])
        self.wr("wTypeMatchup", c["matchup"])
        self.wr("wCriticalHit", c["critical"])
        self.wr("wEnemyMonStatus", c["foe_status"])
        self.wr("wBattleMonStatus", 0)
        self.wr_be16("wBattleMonHP", c["user_hp"])
        self.wr_be16("wBattleMonMaxHP", c["user_max"])
        self.wr_be16("wEnemyMonHP", c["foe_hp"])
        self.wr_be16("wEnemyMonMaxHP", c["foe_max"])
        for struct in ("wPlayerMoveStruct", "wEnemyMoveStruct"):
            self.wr(struct, 1, MOVE_ANIM)          # not OUTRAGE
            self.wr(struct, c["move_type"], MOVE_TYPE)
        self.wr_be16("wCurDamage", BASE_DAMAGE)
        if self.invoke("TypePassive_ApplyDamageModifiers_Far") is None:
            return None
        return self.rd_be16("wCurDamage")

    def przz_speed(self, types, status, speed=100):
        # NOTE: this routine documents an INVERTED hBattleTurn convention
        # (nonzero = player), unlike the rest of the battle engine.
        self.reset()
        self.wr("hBattleTurn", 1)
        self.wr("wBattleMonType1", types[0])
        self.wr("wBattleMonType1", types[1], 1)
        self.wr("wBattleMonStatus", status)
        self.wr_be16("wBattleMonSpeed", speed)
        if self.invoke("ApplyPrzEffectOnSpeed_Far") is None:
            return None
        return self.rd_be16("wBattleMonSpeed")

    def burn_attack(self, types, atk=100):
        self.reset()
        self.wr("hBattleTurn", 1)
        self.wr("wBattleMonType1", types[0])
        self.wr("wBattleMonType1", types[1], 1)
        self.wr("wBattleMonStatus", BRN_BIT)
        self.wr_be16("wBattleMonAttack", atk)
        if self.invoke("ApplyBrnEffectOnAttack_Far") is None:
            return None
        return self.rd_be16("wBattleMonAttack")

    def flying_accuracy(self, types, acc=100):
        self.reset()
        self.wr("hBattleTurn", 0)
        self.wr("wBattleMonType1", types[0])
        self.wr("wBattleMonType1", types[1], 1)
        out = self.invoke("TypePassive_ApplyFlyingAccuracyBonusToB_Far", {"B": acc})
        return None if out is None else out["B"]

    def przz_fail_threshold(self, types):
        self.reset()
        self.wr("hBattleTurn", 0)
        self.wr("wBattleMonType1", types[0])
        self.wr("wBattleMonType1", types[1], 1)
        out = self.invoke("TypePassive_GetUserParalysisFailThreshold_Far")
        return None if out is None else out["A"]

    def steel_recoil(self, types, recoil=40):
        self.reset()
        self.wr("hBattleTurn", 0)
        self.wr("wBattleMonType1", types[0])
        self.wr("wBattleMonType1", types[1], 1)
        out = self.invoke("TypePassive_AdjustRecoilBCForSteel_Far",
                          {"B": recoil >> 8, "C": recoil & 0xFF})
        return None if out is None else out["BC"]


def main() -> int:
    try:
        from tools.damage_debugger.emulator import DebugSession
    except Exception as exc:  # pragma: no cover - environment guard
        return skip(f"debugger harness unavailable: {exc}")
    try:
        sess_cm = DebugSession.open("pokegold")
    except Exception as exc:
        return skip(f"pokegold ROM/symbols unavailable: {exc}")

    rows: list[tuple[str, str, str, int | None, int, str]] = []
    failures: list[str] = []

    def check(group, label, strength, got, want, note=""):
        if got is None:
            status = "FAIL(no-return)"
            failures.append(f"{group} / {label} [{strength}]: routine never returned")
        elif got != want:
            status = "FAIL"
            failures.append(
                f"{group} / {label} [{strength}]: got {got}, documented rate gives {want}"
                + (f" ({note})" if note else "")
            )
        else:
            status = "OK"
        rows.append((group, f"{label} [{strength}]", status, got, want, note))

    with sess_cm as sess:
        needed = ["TypePassive_ApplyDamageModifiers_Far", "ApplyPrzEffectOnSpeed_Far",
                  "ApplyBrnEffectOnAttack_Far",
                  "TypePassive_ApplyFlyingAccuracyBonusToB_Far",
                  "TypePassive_GetUserParalysisFailThreshold_Far",
                  "TypePassive_AdjustRecoilBCForSteel_Far"]
        for n in needed:
            if sess.symbols.get(n) is None:
                return skip(f"symbol {n} missing from pokegold.sym")
        sess.tick(BOOT_FRAMES)
        h = Harness(sess)

        # --- control: nothing armed, damage must pass through untouched ---
        check("damage", "baseline, no passive armed", "control",
              h.damage_mod({}), BASE_DAMAGE)

        # --- 9 damage modifiers x {dual, mono} ---
        for label, half, full, half_cfg, full_cfg in DMG_CASES:
            got_h = h.damage_mod(half_cfg)
            got_f = h.damage_mod(full_cfg)
            check("damage", label, f"dual {half[0]}/{half[1]}", got_h,
                  frac(BASE_DAMAGE, *half))
            check("damage", label, f"mono {full[0]}/{full[1]}", got_f,
                  frac(BASE_DAMAGE, *full))
            if got_h is not None and got_h == got_f:
                failures.append(
                    f"damage / {label}: dual and mono both produced {got_h} -- the "
                    "mono branch is unreachable (the clobber signature)"
                )

        # --- Electric Speed passive ---
        check("speed", "Electric Speed", "mono 21/20",
              h.przz_speed((ELECTRIC, ELECTRIC), 0), frac(100, 21, 20))
        check("speed", "Electric Speed", "dual 41/40",
              h.przz_speed((ELECTRIC, FLYING), 0), frac(100, 41, 40))
        check("speed", "Electric Speed", "absent",
              h.przz_speed((FLYING, FLYING), 0), 100)

        # --- paralysis Speed penalty, tuned by Fighting ---
        check("speed", "Paralysis penalty", "no Fighting 1/4",
              h.przz_speed((FLYING, FLYING), PAR_BIT), frac(100, 1, 4))
        check("speed", "Paralysis penalty", "dual Fighting 3/8",
              h.przz_speed((FIGHTING, FLYING), PAR_BIT), frac(100, 3, 8))
        check("speed", "Paralysis penalty", "mono Fighting 1/2",
              h.przz_speed((FIGHTING, FIGHTING), PAR_BIT), frac(100, 1, 2))
        # Regression guard for the shipped d-clobber: Electric AND Fighting.
        # Electric half first (100 -> 102), then Fighting half (102 * 3/8 = 38).
        # Pre-fix this read types out of ROM0 and fell back to 1/4 -> 25.
        check("speed", "Paralysis, Electric/Fighting (Raichu, Electabuzz)",
              "dual Elec + dual Fight",
              h.przz_speed((ELECTRIC, FIGHTING), PAR_BIT),
              frac(frac(100, 41, 40), 3, 8),
              note="pre-fix gave 25 (baseline 1/4) via a ROM0 garbage type read")

        # --- burn Attack penalty, tuned by Fighting ---
        check("attack", "Burn penalty", "no Fighting 1/2",
              h.burn_attack((FLYING, FLYING)), frac(100, 1, 2))
        check("attack", "Burn penalty", "dual Fighting 5/8",
              h.burn_attack((FIGHTING, FLYING)), frac(100, 5, 8))
        check("attack", "Burn penalty", "mono Fighting 3/4",
              h.burn_attack((FIGHTING, FIGHTING)), frac(100, 3, 4))

        # --- Flying accuracy bonus ---
        check("accuracy", "Flying accuracy", "mono 27/25",
              h.flying_accuracy((FLYING, FLYING)), frac(100, 27, 25))
        check("accuracy", "Flying accuracy", "dual 26/25",
              h.flying_accuracy((FLYING, NORMAL)), frac(100, 26, 25))
        check("accuracy", "Flying accuracy", "absent",
              h.flying_accuracy((NORMAL, NORMAL)), 100)

        # --- full-paralysis fail chance, tuned by Fighting ---
        check("status", "Full-paralysis fail chance", "no Fighting 25%",
              h.przz_fail_threshold((FLYING, FLYING)), pct(25))
        check("status", "Full-paralysis fail chance", "dual Fighting 20%",
              h.przz_fail_threshold((FIGHTING, FLYING)), pct(20))
        check("status", "Full-paralysis fail chance", "mono Fighting 15%",
              h.przz_fail_threshold((FIGHTING, FIGHTING)), pct(15))

        # --- Steel recoil mitigation ---
        check("recoil", "Steel recoil mitigation", "absent (full recoil)",
              h.steel_recoil((FLYING, FLYING)), 40)
        check("recoil", "Steel recoil mitigation", "dual (halved)",
              h.steel_recoil((STEEL, FLYING)), 20)
        check("recoil", "Steel recoil mitigation", "mono (zeroed)",
              h.steel_recoil((STEEL, STEEL)), 0)

    gw = max(len(r[0]) for r in rows)
    lw = max(len(r[1]) for r in rows)
    print(f"{'group'.ljust(gw)}  {'case'.ljust(lw)}  got  want  status")
    print("-" * (gw + lw + 22))
    for group, label, status, got, want, _note in rows:
        got_s = "--" if got is None else str(got)
        print(f"{group.ljust(gw)}  {label.ljust(lw)}  {got_s:>3}  {want:>4}  {status}")
    print()

    if failures:
        print(f"FAIL: {len(failures)} type-passive rate mismatch(es).")
        for f in failures:
            print(f"  - {f}")
        print()
        print("Source: engine/battle/type_passive_damage_mods.asm")
        print("Docs:   docs/mechanics_changes_from_base.md 1.3")
        return 1

    ok = sum(1 for r in rows if r[2] == "OK")
    print(f"PASS: all {ok} type-passive cases match the documented rates")
    print("      mono and dual branches are reachable and distinct for every passive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
