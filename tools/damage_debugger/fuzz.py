"""Hypothesis-driven property test for the damage chain.

Uses the Tier 2.1 Python oracle as ground truth. Generates random
`BattleInputs` (level, BP, atk, def, types, items, crit), seeds them
into the ROM via the same WRAM writes the hand-coded scenarios use,
runs `BattleCommand_DamageStats` -> `DamageCalc` -> `Stab`, and asserts
the on-ROM `wCurDamage` matches `oracle.predict_damage(inputs)`.

When a counterexample fires, Hypothesis auto-shrinks to a minimal repro.
The Tier 3.4 ddmin minimizer can shrink the result further across axes
Hypothesis won't (e.g., alternative attacker types that still trigger).

Why: hand-coded scenarios cover the paths we know about. Fuzz catches
the ones we don't -- e.g., Eviolite's `bc/hl` clobber (commit 2ad4ca2c)
would have surfaced organically through Hypothesis if we'd had this
when the AG-08 fix landed.

Run modes:

    python -m tools.damage_debugger.fuzz                 # 200 examples
    python -m tools.damage_debugger.fuzz --max=1000      # extended

Eviolite-axis coverage is deferred to a v2 pass: triggering Eviolite
requires `.SpeciesCanEvolve` which reads from the live EvosAttacks
table, so we'd need a curated species list to fuzz across. The hand-
coded `physical_eviolite_def` / `special_eviolite_spd` scenarios in
`clobber_smoke` cover that axis at fixed stats today.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict, replace
from pathlib import Path

from hypothesis import HealthCheck, given, settings, strategies as st
from hypothesis.errors import Unsatisfiable

from .boot_cache import BootStateCache
from .clobber_smoke import (
    _read_byte,
    parse_sym,
    write_be_u16,
    write_byte,
)
from .oracle import (
    BattleInputs,
    DARK,
    DRAGON,
    ELECTRIC,
    FIGHTING,
    FIRE,
    FLYING,
    GHOST,
    GRASS,
    GROUND,
    HELD_ASSAULT_VEST,
    HELD_CHOICE_BAND,
    HELD_CHOICE_SPECS,
    HELD_NONE,
    ICE,
    NORMAL,
    PHYSICAL_MAX,
    POISON,
    PSYCHIC_TYPE,
    ROCK,
    STEEL,
    WATER,
    BUG,
    predict_damage,
)
from .paths import find_rom, find_sym
from .safe_call import call_function_safe, read_be_u16_banked, write_byte_banked


ALL_TYPES = (
    NORMAL, FIGHTING, FLYING, POISON, GROUND, ROCK, BUG, GHOST, STEEL,
    FIRE, WATER, GRASS, ELECTRIC, PSYCHIC_TYPE, ICE, DRAGON, DARK,
)
PHYSICAL_TYPES = tuple(t for t in ALL_TYPES if t <= PHYSICAL_MAX)
SPECIAL_TYPES = tuple(t for t in ALL_TYPES if t > PHYSICAL_MAX)


# --- Hypothesis strategies ---------------------------------------------------

@st.composite
def battle_inputs_strategy(draw) -> BattleInputs:
    is_physical = draw(st.booleans())
    move_type = draw(
        st.sampled_from(PHYSICAL_TYPES) if is_physical
        else st.sampled_from(SPECIAL_TYPES)
    )
    attacker_t1 = draw(st.sampled_from(ALL_TYPES))
    attacker_t2 = draw(st.sampled_from(ALL_TYPES))
    defender_t1 = draw(st.sampled_from(ALL_TYPES))
    defender_t2 = draw(st.sampled_from(ALL_TYPES))

    # Items: only Choice Band/Specs and Assault Vest are species-agnostic.
    # Eviolite needs a curated species list (.SpeciesCanEvolve check) --
    # the hand-coded scenarios cover that axis at fixed stats; deferred for
    # the fuzz harness until we generate (species, can_evolve) pairs.
    if is_physical:
        user_item = draw(st.sampled_from([HELD_NONE, HELD_CHOICE_BAND]))
    else:
        user_item = draw(st.sampled_from([HELD_NONE, HELD_CHOICE_SPECS]))
    opponent_item = (
        draw(st.sampled_from([HELD_NONE, HELD_ASSAULT_VEST])) if not is_physical
        else HELD_NONE
    )

    return BattleInputs(
        attacker_level=draw(st.integers(min_value=1, max_value=100)),
        # BP > 0 -- DamageCalc returns early on 0. Cap at 120 to avoid
        # multi-hit / Selfdestruct / Variable-power moves' weird paths.
        move_bp=draw(st.integers(min_value=10, max_value=120)),
        move_type=move_type,
        is_physical=is_physical,
        # Stat range: realistic computed stats (level-scaled).
        attacker_atk=draw(st.integers(min_value=5, max_value=400)),
        defender_def=draw(st.integers(min_value=5, max_value=400)),
        attacker_types=(attacker_t1, attacker_t2),
        defender_types=(defender_t1, defender_t2),
        user_item=user_item,
        opponent_item=opponent_item,
        is_critical=draw(st.booleans()),
        # Type-passive flags (oracle Branches 2/3/9). The fuzz seed
        # pins ROM HP/status to match these so oracle and ROM agree on
        # which branches fire.
        attacker_below_third_hp=draw(st.booleans()),
        opponent_has_status=draw(st.booleans()),
        opponent_above_half_hp=draw(st.booleans()),
    )


# --- ROM seeding -------------------------------------------------------------

def _seed_inputs(pyboy, syms, inp: BattleInputs) -> None:
    """Write `inp` into the ROM's battle state.

    Convention: player turn (hBattleTurn=0). Battle slot = attacker,
    Enemy slot = defender. Mirrors the writes in
    `_seed_cyndaquil_attacks_pidgey_with_ember` from clobber_smoke.py
    but parameterized.
    """
    # Zero meta.
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

    # Attacker = Battle slot.
    # Species 155 (Cyndaquil) is a sane default; we override types directly
    # so species choice doesn't drive the matchup.
    write_byte(pyboy, "wBattleMonSpecies", syms, 155)
    write_byte(pyboy, "wBattleMonLevel", syms, inp.attacker_level)
    write_byte(pyboy, "wBattleMonType1", syms, inp.attacker_types[0])
    write_byte(pyboy, "wBattleMonType2", syms, inp.attacker_types[1])
    write_byte(pyboy, "wBattleMonItem", syms, inp.user_item)

    # Stats: Battle slot drives the BattleCommand_DamageStats reads via
    # wPlayer* mirrors. Write both the "computed at start of battle"
    # mirrors AND the species mon block to be safe.
    if inp.is_physical:
        write_be_u16(pyboy, "wBattleMonAttack", syms, inp.attacker_atk)
        write_be_u16(pyboy, "wPlayerAttack", syms, inp.attacker_atk)
    else:
        write_be_u16(pyboy, "wBattleMonSpclAtk", syms, inp.attacker_atk)
        write_be_u16(pyboy, "wPlayerSpAtk", syms, inp.attacker_atk)
    # Other stats: zero-ish defaults (don't matter for damage on the chosen axis).
    for slot in ("wBattleMonDefense", "wBattleMonSpclDef", "wBattleMonSpeed"):
        write_be_u16(pyboy, slot, syms, max(5, inp.attacker_atk // 2))
    for slot in ("wPlayerDefense", "wPlayerSpDef", "wPlayerSpeed"):
        write_be_u16(pyboy, slot, syms, max(5, inp.attacker_atk // 2))

    # Defender = Enemy slot. Species 16 (Pidgey) by default; types overridden.
    write_byte(pyboy, "wEnemyMonSpecies", syms, 16)
    write_byte(pyboy, "wEnemyMonLevel", syms, inp.attacker_level)  # not strictly
    write_byte(pyboy, "wEnemyMonType1", syms, inp.defender_types[0])
    write_byte(pyboy, "wEnemyMonType2", syms, inp.defender_types[1])
    write_byte(pyboy, "wEnemyMonItem", syms, inp.opponent_item)

    if inp.is_physical:
        write_be_u16(pyboy, "wEnemyMonDefense", syms, inp.defender_def)
        write_be_u16(pyboy, "wEnemyDefense", syms, inp.defender_def)
    else:
        write_be_u16(pyboy, "wEnemyMonSpclDef", syms, inp.defender_def)
        write_be_u16(pyboy, "wEnemySpDef", syms, inp.defender_def)
    for slot in ("wEnemyMonAttack", "wEnemyMonSpclAtk", "wEnemyMonSpeed"):
        write_be_u16(pyboy, slot, syms, max(5, inp.defender_def // 2))
    for slot in ("wEnemyAttack", "wEnemySpAtk", "wEnemySpeed"):
        write_be_u16(pyboy, slot, syms, max(5, inp.defender_def // 2))

    # HP / status fields drive TypePassive Branches 2/3/9 -- pin them
    # to match the BattleInputs flags so ROM and oracle agree on which
    # branches fire. Convention:
    #   attacker_below_third_hp: HP=1, MaxHP=10  (1 < 10/3)
    #   not below third         : HP=10, MaxHP=10 (full)
    #   opponent_above_half_hp  : HP=10, MaxHP=10
    #   not above half          : HP=0,  MaxHP=10
    if inp.attacker_below_third_hp:
        write_be_u16(pyboy, "wBattleMonHP", syms, 1)
        write_be_u16(pyboy, "wBattleMonMaxHP", syms, 10)
    else:
        write_be_u16(pyboy, "wBattleMonHP", syms, 10)
        write_be_u16(pyboy, "wBattleMonMaxHP", syms, 10)
    if inp.opponent_above_half_hp:
        write_be_u16(pyboy, "wEnemyMonHP", syms, 10)
        write_be_u16(pyboy, "wEnemyMonMaxHP", syms, 10)
    else:
        write_be_u16(pyboy, "wEnemyMonHP", syms, 0)
        write_be_u16(pyboy, "wEnemyMonMaxHP", syms, 10)
    # opponent_has_status: any nonzero byte triggers the GHOST branch.
    write_byte(pyboy, "wEnemyMonStatus", syms, 0x40 if inp.opponent_has_status else 0)

    # Move struct. Effect 0x00 = NORMAL_HIT (no special branch). Accuracy
    # 0xFF for "always hit at the seed level"; we never simulate the miss
    # path. PP doesn't matter for damage.
    pm = syms["wPlayerMoveStruct"]
    move_id = 0x21  # arbitrary stable ID -- not used in the path
    for offset, val in [
        (0, move_id),
        (1, 0x00),         # effect = NORMAL_HIT
        (2, inp.move_bp),
        (3, inp.move_type),
        (4, 0xFF),         # accuracy
        (5, 25),           # pp
        (6, 0),            # effect chance
    ]:
        write_byte_banked(pyboy, pm[1] + offset, val, pm[0])
    write_byte(pyboy, "wCurPlayerMove", syms, move_id)
    write_byte(pyboy, "hBattleTurn", syms, 0)
    if inp.is_critical:
        write_byte(pyboy, "wCriticalHit", syms, 1)


def _run_one(pyboy, syms, inp: BattleInputs) -> int:
    _seed_inputs(pyboy, syms, inp)
    cd_sym = syms["wCurDamage"]
    for fn in ("BattleCommand_DamageStats", "BattleCommand_DamageCalc", "BattleCommand_Stab"):
        call_function_safe(pyboy, syms, fn)
    return read_be_u16_banked(pyboy, cd_sym[1], cd_sym[0])


# --- Test entrypoint ---------------------------------------------------------

# Module-level shared cache so each Hypothesis example re-uses the same
# booted PyBoy via load_state instead of paying boot cost per example.
_CACHE: BootStateCache | None = None
_SYMS: dict | None = None


def _ensure_cache():
    global _CACHE, _SYMS
    if _CACHE is None:
        rom = find_rom("pokegold_debug")
        sym = find_sym("pokegold_debug")
        _SYMS = parse_sym(sym)
        _CACHE = BootStateCache(rom)
        _CACHE.prime()
    return _CACHE, _SYMS


def check_one(inp: BattleInputs, *, tolerance: int = 1) -> tuple[int, int, bool]:
    """Run inp against ROM + oracle. Returns (rom_damage, oracle_damage, ok)."""
    cache, syms = _ensure_cache()
    pyboy = cache.restore()
    rom_damage = _run_one(pyboy, syms, inp)
    oracle_damage = predict_damage(inp)
    ok = abs(rom_damage - oracle_damage) <= tolerance
    return rom_damage, oracle_damage, ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Damage-chain property test")
    parser.add_argument("--max-examples", "--max", type=int, default=200,
                        help="Hypothesis example budget (default 200)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Hypothesis seed for reproducibility")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--tolerance", type=int, default=1,
                        help="Allowed |rom - oracle| (default 1, for rounding edges)")
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print(f"fuzz: priming boot cache...", flush=True)
    _ensure_cache()
    print(f"fuzz: running up to {args.max_examples} examples", flush=True)

    failures: list[tuple[BattleInputs, int, int]] = []

    @settings(
        max_examples=args.max_examples,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
        derandomize=args.seed is None,
    )
    @given(battle_inputs_strategy())
    def _check(inp: BattleInputs):
        rom_damage, oracle_damage, ok = check_one(inp, tolerance=args.tolerance)
        if not ok:
            failures.append((inp, rom_damage, oracle_damage))
            assert False, (
                f"divergence: rom={rom_damage} oracle={oracle_damage}\n"
                f"inputs={inp}"
            )

    try:
        _check()
        print(f"\nfuzz: PASS -- no divergence in {args.max_examples} examples", flush=True)
        return 0
    except AssertionError as e:
        print(f"\nfuzz: FAIL -- counterexample found", flush=True)
        if failures:
            inp, rom, oracle = failures[-1]
            print(f"  rom_damage    = {rom}")
            print(f"  oracle_damage = {oracle}")
            print(f"  inputs        = {inp}")
        # Hypothesis will print its shrunken form; surface that too.
        print(f"\nHypothesis details:\n{e}", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
