"""Exhaustive EXP-curve prover for CalcExpAtLevel refactors.

CalcExpAtLevel's entire input domain is (growth rate 0-5) x (level 1-100)
= 600 cases. That makes "the refactor didn't change the EXP curve"
*provable* by exhaustive sweep instead of spot-checks: dump all 600
outputs from the ROM before the change, dump again after, and require
exact equality. This is the TD-013 verification floor replacement for
SHA1 match, which a restructuring refactor cannot satisfy by definition.

Modes:
    # dump a ROM's full curve to JSON
    python -m tools.damage_debugger.exp_curve_prover --dump out.json [--rom pokegold]

    # compare two dumps (exit 1 on any difference)
    python -m tools.damage_debugger.exp_curve_prover --compare old.json new.json

    # validate a dump against the closed-form growth formula (harness
    # self-check: catches a broken sweep, not a broken ROM)
    python -m tools.damage_debugger.exp_curve_prover --check-formula dump.json

Captured per case: hProduct+0..3 (the output all callers read), post-call
d (loop-counter contract: CalcLevel increments d across repeated calls)
and e (callers may rely on it surviving the call). Interrupts are
disabled (IE=0) around each call so an old-vs-new instruction-count
difference cannot shift interrupt timing into the math HRAM.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .boot_cache import BootStateCache
from .paths import find_rom, find_sym
from .safe_call import call_function_safe, write_byte_banked
from .symbols import SymbolTable

RATES = 6
LEVELS = range(1, 101)
E_CANARY = 0x5A

# data/growth_rates.asm, in GROWTH_* constant order:
# (cubic_num, cubic_den, quad_coef, linear_coef, const_term)
GROWTH_COEFS = [
    (1, 1, 0, 0, 0),        # Medium Fast
    (3, 4, 10, 0, 30),      # Slightly Fast
    (3, 4, 20, 0, 70),      # Slightly Slow
    (6, 5, -15, 100, 140),  # Medium Slow
    (4, 5, 0, 0, 0),        # Fast
    (5, 4, 0, 0, 0),        # Slow
]


def closed_form(rate: int, level: int) -> int:
    """(a/b)*n^3 + c*n^2 + d*n - e, floor-divided cubic, mod 2^24."""
    if level == 1:
        return 0
    a, b, c, d, e = GROWTH_COEFS[rate]
    n = level
    total = (a * n**3) // b + c * n * n + d * n - e
    return total & 0xFFFFFF


def sweep(rom_variant: str) -> dict:
    rom_path = find_rom(rom_variant)
    syms = SymbolTable.load(find_sym(rom_variant)).as_legacy_dict()
    for needed in ("CalcExpAtLevel", "wBaseGrowthRate", "hProduct"):
        if needed not in syms:
            raise SystemExit(f"symbol {needed} missing from {rom_variant}.sym")

    cache = BootStateCache(rom_path)
    pyboy = cache.prime()
    rate_sym = syms["wBaseGrowthRate"]
    hproduct = syms["hProduct"][1]

    cases: dict[str, dict] = {}
    try:
        for rate in range(RATES):
            for level in LEVELS:
                cache.restore(pyboy)
                pyboy.memory[0xFFFF] = 0  # IE=0: no interrupts mid-call
                write_byte_banked(pyboy, rate_sym[1], rate, rate_sym[0])
                rf = pyboy.register_file
                rf.D = level
                rf.E = E_CANARY
                ticks, returned, post_pc = call_function_safe(
                    pyboy, syms, "CalcExpAtLevel"
                )
                if not returned:
                    raise SystemExit(
                        f"rate={rate} level={level}: did not return "
                        f"(pc={post_pc:#06x} after {ticks} ticks)"
                    )
                b = [int(pyboy.memory[hproduct + i]) for i in range(4)]
                cases[f"{rate}:{level}"] = {
                    "bytes": b,
                    "exp": (b[1] << 16) | (b[2] << 8) | b[3],
                    "d": int(rf.D),
                    "e": int(rf.E),
                }
    finally:
        cache.stop()
    return {"rom": rom_path.name, "cases": cases}


def cmd_dump(args) -> int:
    dump = sweep(args.rom)
    out = Path(args.dump)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dump, indent=1), encoding="utf-8")
    n = len(dump["cases"])
    print(f"dumped {n} cases from {dump['rom']} -> {out}")
    return 0


def cmd_compare(args) -> int:
    a = json.loads(Path(args.compare[0]).read_text(encoding="utf-8"))
    b = json.loads(Path(args.compare[1]).read_text(encoding="utf-8"))
    keys_a, keys_b = set(a["cases"]), set(b["cases"])
    if keys_a != keys_b:
        print(f"FAIL: case sets differ (only-in-a: {keys_a - keys_b}, "
              f"only-in-b: {keys_b - keys_a})")
        return 1
    bad = 0
    for key in sorted(keys_a, key=lambda k: (int(k.split(':')[0]), int(k.split(':')[1]))):
        ca, cb = a["cases"][key], b["cases"][key]
        if ca != cb:
            bad += 1
            print(f"MISMATCH {key}: {ca} != {cb}")
    if bad:
        print(f"FAIL: {bad}/{len(keys_a)} cases differ between "
              f"{args.compare[0]} and {args.compare[1]}")
        return 1
    print(f"PASS: all {len(keys_a)} cases identical "
          f"({a['rom']} vs {b['rom']}: exp bytes, d, e)")
    return 0


def cmd_check_formula(args) -> int:
    dump = json.loads(Path(args.check_formula).read_text(encoding="utf-8"))
    bad = 0
    for key, case in dump["cases"].items():
        rate, level = (int(x) for x in key.split(":"))
        want = closed_form(rate, level)
        if case["exp"] != want:
            bad += 1
            print(f"MISMATCH {key}: rom={case['exp']} formula={want}")
        if case["d"] != level:
            bad += 1
            print(f"MISMATCH {key}: post-call d={case['d']}, want {level}")
        if case["e"] != E_CANARY:
            bad += 1
            print(f"MISMATCH {key}: post-call e={case['e']:#04x}, "
                  f"want {E_CANARY:#04x}")
    if bad:
        print(f"FAIL: {bad} deviation(s) from the closed-form model")
        return 1
    print(f"PASS: all {len(dump['cases'])} cases match the closed-form "
          f"growth formula; d and e preserved")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--rom", default="pokegold", help="ROM variant name (default: pokegold)")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dump", metavar="OUT_JSON")
    mode.add_argument("--compare", nargs=2, metavar=("OLD_JSON", "NEW_JSON"))
    mode.add_argument("--check-formula", metavar="DUMP_JSON")
    args = p.parse_args()
    if args.dump:
        return cmd_dump(args)
    if args.compare:
        return cmd_compare(args)
    return cmd_check_formula(args)


if __name__ == "__main__":
    sys.exit(main())
