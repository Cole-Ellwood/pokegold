"""Delta-debugging for BattleInputs.

Tier 3.4. Given a failing scenario, try setting each field to a
"neutral default" and keep the simplification if the failure still
reproduces. Output: the minimal subset of fields that drives the
divergence.

Why on top of Hypothesis (which shrinks too): Hypothesis shrinks
within its strategy space, but it can't tell us "this attacker_level
of 8 is significant -- the bug needs lvl >= 5" or "this Choice Band
is irrelevant -- you can drop it." ddmin runs the failure predicate
against simplified candidates and keeps the smallest one that still
fails. Useful when:

  - A bug repro was hand-coded, not Hypothesis-shrunken.
  - You want a "story" form of the inputs ("the bug needs FIRE move +
    attacker_below_third_hp; everything else is irrelevant").
  - You want to verify a fuzz-shrunken example actually requires
    every field Hypothesis preserved.

Usage:

    from tools.damage_debugger.minimize import minimize, divergence_predicate
    from tools.damage_debugger.find import _known_bugs

    inp = _known_bugs()['hp_d_clobber'][1]
    minimal, story = minimize(inp, divergence_predicate)
    print(story)

Or via CLI:

    python -m tools.damage_debugger.minimize --bug hp_d_clobber

Algorithm: single-axis ddmin. We don't bother with full Zeller subset
minimization because BattleInputs has ~15 fields and per-axis
reduction converges in O(N) checks (15-25 PyBoy runs at ~50ms each).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, fields, replace
from typing import Callable

from .boot_cache import BootStateCache
from .clobber_smoke import parse_sym
from .fuzz import _seed_inputs
from .oracle import (
    BattleInputs,
    HELD_NONE,
    NORMAL,
    predict_damage,
)
from .paths import find_rom, find_sym
from .safe_call import call_function_safe, read_be_u16_banked


# Neutral defaults to try as simplifications. A field's value gets
# replaced with the default; if the test still fails, the simplification
# sticks. Order matters only for output readability -- we reduce the
# "least likely to matter" fields first.
DEFAULTS = BattleInputs(
    attacker_level=1,
    move_bp=10,
    move_type=NORMAL,
    is_physical=True,
    attacker_atk=5,
    defender_def=5,
    attacker_types=(NORMAL, NORMAL),
    defender_types=(NORMAL, NORMAL),
    user_item=HELD_NONE,
    opponent_item=HELD_NONE,
    can_evolve_attacker=False,
    can_evolve_defender=False,
    is_critical=False,
    is_selfdestruct=False,
    attacker_below_third_hp=False,
    opponent_has_status=False,
    opponent_above_half_hp=False,
)


def divergence_predicate(
    cache: BootStateCache,
    syms: dict,
    *,
    pristine: bool = True,
) -> Callable[[BattleInputs], bool]:
    """Build a predicate that returns True if `inp` diverges from oracle.

    `pristine=True` is the default for known-bug repros: the oracle
    models the as-INTENDED behavior, so the predicate fires when the
    ROM's bug-bearing path produces a different value. Pass
    `pristine=False` when minimizing a fresh fuzz-found divergence
    (fuzz scores the bug-mirroring oracle, so a true ROM regression
    is what's left).
    """
    def predicate(inp: BattleInputs) -> bool:
        pyboy = cache.restore()
        _seed_inputs(pyboy, syms, inp)
        cd = syms["wCurDamage"]
        for fn in ("BattleCommand_DamageStats", "BattleCommand_DamageCalc",
                   "BattleCommand_Stab"):
            call_function_safe(pyboy, syms, fn)
        rom_damage = read_be_u16_banked(pyboy, cd[1], cd[0])
        oracle_damage = predict_damage(inp, pristine=pristine)
        return rom_damage != oracle_damage
    return predicate


# `is_physical` and `move_type` are tightly coupled in the asm: the
# move's category is derived from its type via
# TypePassive_GetEffectiveMoveCategory_Far. Reducing one without the
# other (e.g. move_type=NORMAL with is_physical=False) creates a stat
# mismatch between the seed (writes to wBattleMonSpclAtk) and the ROM
# (reads wBattleMonAttack because NORMAL is physical). Skip both during
# minimization -- the bug repro should preserve the move kind it was
# discovered on.
COUPLED_FIELDS = frozenset({"is_physical", "move_type"})


def minimize(
    initial: BattleInputs,
    predicate: Callable[[BattleInputs], bool],
    defaults: BattleInputs = DEFAULTS,
) -> tuple[BattleInputs, list[str]]:
    """Single-axis ddmin: try replacing each field with its default; keep
    the simplification if `predicate` still fires on the result.

    Returns `(minimized_inputs, story)` where `story` is a list of
    diff lines suitable for printing. Fields in `COUPLED_FIELDS` are
    not touched -- the bug story keeps the move kind (physical/special
    + type) it was found with.
    """
    if not predicate(initial):
        return initial, ["initial inputs do not satisfy predicate; nothing to minimize"]

    current = initial
    reduced_fields: list[str] = []
    preserved_fields: list[str] = []
    for f in fields(BattleInputs):
        if f.name in COUPLED_FIELDS:
            continue
        candidate = replace(current, **{f.name: getattr(defaults, f.name)})
        if candidate == current:
            continue
        if predicate(candidate):
            current = candidate
            reduced_fields.append(f.name)
        else:
            preserved_fields.append(f.name)

    story: list[str] = []
    story.append(f"minimize: {len(reduced_fields)} field(s) reducible to defaults:")
    for name in reduced_fields:
        was = getattr(initial, name)
        now = getattr(current, name)
        story.append(f"  - {name}: {was!r}  ->  {now!r}")
    if preserved_fields:
        story.append(f"minimize: {len(preserved_fields)} field(s) load-bearing for the bug:")
        for name in preserved_fields:
            val = getattr(current, name)
            story.append(f"  * {name} = {val!r}")
    if not preserved_fields:
        story.append("  (every field could be defaulted -- the bug fires on a default scenario; "
                     "the predicate may be too lax)")
    return current, story


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Minimize a BattleInputs to its load-bearing axes")
    parser.add_argument("--bug", default=None,
                        help="Known-bug name to minimize (try: hp_d_clobber)")
    parser.add_argument("--no-pristine", action="store_true",
                        help="Score against bug-mirroring oracle (use when minimizing "
                        "a freshly-found fuzz divergence; default models AS-INTENDED)")
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.bug is None:
        parser.error("specify --bug <name>")
    from .find import _known_bugs
    bugs = _known_bugs()
    if args.bug not in bugs:
        print(f"unknown bug {args.bug!r}; known: {list(bugs)}", file=sys.stderr)
        return 2
    _, inp, _seed = bugs[args.bug]

    rom = find_rom("pokegold_debug")
    sym = find_sym("pokegold_debug")
    syms = parse_sym(sym)
    cache = BootStateCache(rom)
    cache.prime()

    predicate = divergence_predicate(cache, syms, pristine=not args.no_pristine)
    minimal, story = minimize(inp, predicate)

    print(f"original: {inp}\n")
    print(f"minimal:  {minimal}\n")
    for line in story:
        print(line)

    cache.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
