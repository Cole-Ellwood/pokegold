"""Multi-scenario clobber regression harness.

Runs several damage-path scenarios and checks that wCurDamage matches an
expected range. The point isn't precision — it's catching CLOBBER-CLASS
bugs (§3.14, §3.13), which manifest as 5-10x damage spikes when a
register carrying defender def, move BP, or attacker atk gets overwritten
mid-chain. The c-clobber that shipped May 2026 turned wCurDamage from 4
into 16 — exactly the kind of jump these range checks catch.

Usage:
    python -m tools.damage_debugger.clobber_smoke

Exit code: 0 if every scenario lands inside [expected_low, expected_high];
nonzero otherwise.

Coverage today:
    physical_no_items   — ALGDS_Far -> ApplyChoiceBandBoost (no-op),
                          -> ApplyEvioliteDefenseBoost (no-op).
                          The exact path that just shipped the c-clobber.
    physical_critical   — Same chain + wCriticalHit=1 hits .CriticalMultiplier.
    special_no_items    — ALGDS_Far -> ApplyChoiceSpecsBoost (no-op),
                          -> ApplyAssaultVestBoostToDefense (no-op),
                          -> ApplyEvioliteSpDefBoost (no-op).

Uncovered (any could ship a clobber undetected — extend this file):
    Items present (Choice Band, Eviolite, Assault Vest, Choice Specs).
      Need item-id setup + species-can-evolve check for Eviolite.
    Type-effective (super-effective / not-very-effective).
    DamageVariation (final 0.85-1.0 random multiplier).
    HandleLateGenAfterHitEffects_Far (Rocky Helmet, Life Orb).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from pyboy import PyBoy

from .safe_call import call_function_safe, read_be_u16_banked, write_byte_banked

ROOT = Path("C:/Users/lolno/Downloads/pokemon gold hack")
LOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "audit"
    / "damage_debugger"
    / "clobber_smoke.log"
)


@dataclass
class Scenario:
    name: str
    seed: Callable
    expected_low: int
    expected_high: int
    note: str = ""


def parse_sym(p: Path) -> dict:
    out = {}
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.split(";", 1)[0].strip()
        parts = s.split()
        if len(parts) < 2 or ":" not in parts[0]:
            continue
        try:
            b, a = parts[0].split(":", 1)
            out[parts[1]] = (int(b, 16), int(a, 16))
        except ValueError:
            continue
    return out


def write_byte(pyboy, name, syms, value):
    s = syms.get(name)
    if s is not None:
        write_byte_banked(pyboy, s[1], value, s[0])


def write_be_u16(pyboy, name, syms, value):
    s = syms.get(name)
    if s is not None:
        hi, lo = (value >> 8) & 0xFF, value & 0xFF
        write_byte_banked(pyboy, s[1], hi, s[0])
        write_byte_banked(pyboy, s[1] + 1, lo, s[0])


def _seed_pidgey_lvl2(pyboy, syms, *, slot: str):
    """Pidgey lvl 2 stats into the named slot ('Battle' for player, 'Enemy' for enemy)."""
    write_byte(pyboy, f"w{slot}MonSpecies", syms, 16)
    write_byte(pyboy, f"w{slot}MonLevel", syms, 2)
    write_byte(pyboy, f"w{slot}MonType1", syms, 0x00)  # NORMAL
    write_byte(pyboy, f"w{slot}MonType2", syms, 0x02)  # FLYING
    write_byte(pyboy, f"w{slot}MonItem", syms, 0)
    write_be_u16(pyboy, f"w{slot}MonAttack", syms, 6)
    write_be_u16(pyboy, f"w{slot}MonDefense", syms, 6)
    write_be_u16(pyboy, f"w{slot}MonSpeed", syms, 7)
    write_be_u16(pyboy, f"w{slot}MonSpclAtk", syms, 5)
    write_be_u16(pyboy, f"w{slot}MonSpclDef", syms, 5)


def _seed_cyndaquil_lvl5(pyboy, syms, *, slot: str):
    write_byte(pyboy, f"w{slot}MonSpecies", syms, 155)
    write_byte(pyboy, f"w{slot}MonLevel", syms, 5)
    write_byte(pyboy, f"w{slot}MonType1", syms, 0x14)  # FIRE
    write_byte(pyboy, f"w{slot}MonType2", syms, 0x14)
    write_byte(pyboy, f"w{slot}MonItem", syms, 0)
    write_be_u16(pyboy, f"w{slot}MonAttack", syms, 10)
    write_be_u16(pyboy, f"w{slot}MonDefense", syms, 9)
    write_be_u16(pyboy, f"w{slot}MonSpeed", syms, 11)
    write_be_u16(pyboy, f"w{slot}MonSpclAtk", syms, 11)
    write_be_u16(pyboy, f"w{slot}MonSpclDef", syms, 10)


def _zero_meta(pyboy, syms):
    for byte_field in (
        "wCriticalHit", "wTypeModifier", "wAttackMissed", "wIsConfusionDamage",
        "wEffectFailed", "wEnemyScreens", "wPlayerScreens", "wBattleMonStatus",
        "wEnemyMonStatus", "wBattleWeather", "wJohtoBadges", "wKantoBadges",
        "wCurEnemyMove", "wCurPlayerMove",
    ):
        write_byte(pyboy, byte_field, syms, 0)
    write_byte(pyboy, "wTypeMatchup", syms, 0x10)
    write_be_u16(pyboy, "wCurDamage", syms, 0)
    for stage in ("Atk", "Def", "Spd", "SAtk", "SDef"):
        write_byte(pyboy, f"wPlayer{stage}Level", syms, 7)
        write_byte(pyboy, f"wEnemy{stage}Level", syms, 7)


def _seed_pidgey_attacks_cyndaquil_with_tackle(pyboy, syms):
    _seed_pidgey_lvl2(pyboy, syms, slot="Enemy")
    _seed_cyndaquil_lvl5(pyboy, syms, slot="Battle")
    write_be_u16(pyboy, "wEnemyAttack", syms, 6)
    write_be_u16(pyboy, "wEnemyDefense", syms, 6)
    write_be_u16(pyboy, "wEnemySpAtk", syms, 5)
    write_be_u16(pyboy, "wEnemySpDef", syms, 5)
    write_be_u16(pyboy, "wPlayerAttack", syms, 10)
    write_be_u16(pyboy, "wPlayerDefense", syms, 9)
    write_be_u16(pyboy, "wPlayerSpAtk", syms, 11)
    write_be_u16(pyboy, "wPlayerSpDef", syms, 10)
    _zero_meta(pyboy, syms)
    em = syms["wEnemyMoveStruct"]
    # Tackle: id=0x21, effect=0x00 (NORMAL_HIT), bp=40, type=0x00 (NORMAL)
    for offset, val in [(0, 0x21), (1, 0x00), (2, 40), (3, 0x00), (4, 0xFF), (5, 35), (6, 0)]:
        write_byte_banked(pyboy, em[1] + offset, val, em[0])
    write_byte(pyboy, "wCurEnemyMove", syms, 0x21)
    write_byte(pyboy, "hBattleTurn", syms, 1)  # Enemy turn


def seed_physical_no_items(pyboy, syms):
    _seed_pidgey_attacks_cyndaquil_with_tackle(pyboy, syms)


def seed_physical_critical(pyboy, syms):
    _seed_pidgey_attacks_cyndaquil_with_tackle(pyboy, syms)
    write_byte(pyboy, "wCriticalHit", syms, 1)


def seed_special_no_items(pyboy, syms):
    """Cyndaquil lvl 5 attacks Pidgey lvl 2 with Ember (FIRE special, BP 40)."""
    _seed_cyndaquil_lvl5(pyboy, syms, slot="Battle")
    _seed_pidgey_lvl2(pyboy, syms, slot="Enemy")
    write_be_u16(pyboy, "wPlayerAttack", syms, 10)
    write_be_u16(pyboy, "wPlayerDefense", syms, 9)
    write_be_u16(pyboy, "wPlayerSpAtk", syms, 11)
    write_be_u16(pyboy, "wPlayerSpDef", syms, 10)
    write_be_u16(pyboy, "wEnemyAttack", syms, 6)
    write_be_u16(pyboy, "wEnemyDefense", syms, 6)
    write_be_u16(pyboy, "wEnemySpAtk", syms, 5)
    write_be_u16(pyboy, "wEnemySpDef", syms, 5)
    _zero_meta(pyboy, syms)
    pm = syms["wPlayerMoveStruct"]
    # Ember: id=0x34, effect=0x4A (BURN_SIDE_EFFECT), bp=40, type=0x14 (FIRE)
    for offset, val in [(0, 0x34), (1, 0x4A), (2, 40), (3, 0x14), (4, 0xFF), (5, 25), (6, 0)]:
        write_byte_banked(pyboy, pm[1] + offset, val, pm[0])
    write_byte(pyboy, "wCurPlayerMove", syms, 0x34)
    write_byte(pyboy, "hBattleTurn", syms, 0)  # Player turn


SCENARIOS = [
    Scenario(
        "physical_no_items", seed_physical_no_items, 3, 5,
        "Pidgey Tackle vs Cyndaquil. The exact path the c-clobber bug shipped on.",
    ),
    Scenario(
        "physical_critical", seed_physical_critical, 5, 8,
        "Same + wCriticalHit=1 → .CriticalMultiplier doubles the pre-+2 quotient (1*2+2=4 → Stab x1.5 = 6).",
    ),
    Scenario(
        "special_no_items", seed_special_no_items, 11, 16,
        "Cyndaquil Ember vs Pidgey. Routes through ALGDS Special branch.",
    ),
]


def run_scenario(scenario: Scenario, syms: dict, rom_path: Path) -> int:
    pyboy = PyBoy(str(rom_path), window="null", sound=False, log_level="ERROR")
    pyboy.set_emulation_speed(0)
    pyboy.tick(240, False, False)

    scenario.seed(pyboy, syms)

    cd_sym = syms["wCurDamage"]
    for fn in ("BattleCommand_DamageStats", "BattleCommand_DamageCalc", "BattleCommand_Stab"):
        call_function_safe(pyboy, syms, fn)

    damage = read_be_u16_banked(pyboy, cd_sym[1], cd_sym[0])
    pyboy.stop(save=False)
    return damage


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)

    def log(msg: str = ""):
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()
        fh.write(msg + "\n")
        fh.flush()

    rom = ROOT / "pokegold_debug.gbc"
    sym = ROOT / "pokegold_debug.sym"
    syms = parse_sym(sym)

    log(f"clobber_smoke: running {len(SCENARIOS)} scenarios against {rom.name}")
    log(f"{'scenario':<22s} {'damage':>7s} {'expected':>10s}  result  notes")
    log("-" * 110)

    failures = []
    for sc in SCENARIOS:
        damage = run_scenario(sc, syms, rom)
        ok = sc.expected_low <= damage <= sc.expected_high
        result = "PASS" if ok else "FAIL"
        log(
            f"{sc.name:<22s} {damage:>7d} "
            f"{f'{sc.expected_low}-{sc.expected_high}':>10s}  {result:>4s}  {sc.note}"
        )
        if not ok:
            failures.append((sc, damage))

    log()
    if failures:
        log(f"FAIL: {len(failures)}/{len(SCENARIOS)} scenario(s) produced unexpected damage.")
        log("      A clobber-class regression likely escaped function-level audits.")
        log("      See docs/asm_authoring_guide.md §3.14 for the recurrence pattern.")
        return 1

    log(f"PASS: all {len(SCENARIOS)} scenarios within expected damage ranges.")
    log("      No clobber-class regression detected on the covered paths.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
