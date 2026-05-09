"""Regression probe for DamageCalc's nonzero-wCurDamage accumulation path.

M1 roadmap item. The audit flagged an endian-looking quirk in
BattleCommand_DamageCalc's cap/add block: it adds the high byte of incoming
`wCurDamage` to `hQuotient+3` before adding the full incoming damage. That
bug is fixed; this probe now guards the fixed ROM against two models:

- buggy-old-asm: `initial + quotient + high(initial) + MIN_DAMAGE`
- intended:      `initial + quotient + MIN_DAMAGE`

The command exits 0 only when the high-byte extra-add is absent.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from .boot_cache import BootStateCache
from .clobber_smoke import parse_sym, write_be_u16
from .fuzz import _seed_inputs
from .oracle import (
    BattleInputs,
    FIRE,
    NORMAL,
    predict_damagecalc_only,
)
from .paths import find_rom, find_sym
from .safe_call import call_function_safe, read_be_u16_banked


PROBE_INPUT = BattleInputs(
    attacker_level=50,
    move_bp=60,
    move_type=NORMAL,
    is_physical=True,
    attacker_atk=80,
    defender_def=70,
    attacker_types=(NORMAL, NORMAL),
    defender_types=(FIRE, FIRE),
)


@dataclass(frozen=True)
class CapAddResult:
    initial: int
    rom: int
    buggy_old_asm: int
    intended: int

    @property
    def classification(self) -> str:
        if self.rom == self.buggy_old_asm == self.intended:
            return "both"
        if self.rom == self.buggy_old_asm:
            return "buggy-old-asm"
        if self.rom == self.intended:
            return "intended"
        return "unknown"


def run_case(cache: BootStateCache, syms: dict, initial_cur_damage: int) -> CapAddResult:
    pyboy = cache.restore()
    _seed_inputs(pyboy, syms, PROBE_INPUT)
    call_function_safe(pyboy, syms, "BattleCommand_DamageStats")
    write_be_u16(pyboy, "wCurDamage", syms, initial_cur_damage)
    call_function_safe(pyboy, syms, "BattleCommand_DamageCalc")
    cd = syms["wCurDamage"]
    rom = read_be_u16_banked(pyboy, cd[1], cd[0])
    return CapAddResult(
        initial=initial_cur_damage,
        rom=rom,
        buggy_old_asm=predict_damagecalc_only(
            PROBE_INPUT,
            initial_cur_damage=initial_cur_damage,
            emulate_cap_add_endian_bug=True,
        ),
        intended=predict_damagecalc_only(
            PROBE_INPUT,
            initial_cur_damage=initial_cur_damage,
            emulate_cap_add_endian_bug=False,
        ),
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    rom = find_rom("pokegold_debug")
    sym = find_sym("pokegold_debug")
    syms = parse_sym(sym)
    cache = BootStateCache(rom)
    cache.prime()
    try:
        results = [run_case(cache, syms, initial) for initial in (0x0000, 0x00FF, 0x0100)]
    finally:
        cache.stop()

    print("cap-add probe: BattleCommand_DamageCalc with incoming wCurDamage")
    print(f"{'initial':>8s} {'ROM':>6s} {'buggy':>8s} {'intended':>9s}  classification")
    unknown = False
    high_byte_bug_present = False
    for result in results:
        print(
            f"${result.initial:04x} {result.rom:>6d} "
            f"{result.buggy_old_asm:>8d} {result.intended:>9d}  {result.classification}"
        )
        unknown = unknown or result.classification == "unknown"
        if result.initial >= 0x0100 and result.classification == "buggy-old-asm":
            high_byte_bug_present = True

    if unknown:
        print("\ncap-add probe: FAIL -- ROM matched neither model")
        return 1
    if high_byte_bug_present:
        print("\ncap-add probe: FAIL -- high byte is still added twice for incoming damage >= 256")
        return 1
    else:
        print("\ncap-add probe: PASS -- no high-byte extra-add observed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
