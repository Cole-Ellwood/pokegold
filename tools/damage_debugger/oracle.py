"""Python oracle for the Gen 2 damage formula as it lives in this hack.

Mirrors `BattleCommand_DamageCalc` (engine/battle/effect_commands.asm:2790)
+ `.CriticalMultiplier` (line 3013) + `BattleCommand_Stab` (line 1223),
plus the late-gen item mods in
`engine/battle/late_gen_held_items.asm`.

Why we need this: hand-picked `expected_low/high` ranges in
`clobber_smoke.SCENARIOS` are honest today (verified by paper math in
the Pass 1 BUG_CHECK) but won't scale to fuzzing. With a Python oracle
the harness can predict exact damage for any input and Hypothesis can
generate inputs without us hand-curating ranges.

The oracle deliberately mirrors the asm's integer-flooring division
order, NOT a textbook Gen 2 formula -- the asm path is the ground
truth. Cross-verify any "the formula is X" assumption against
`engine/battle/effect_commands.asm` before changing this file.

Scope: damage chain only (DamageCalc + Stab + late-gen item-stat
mods + crit + type matchup). Excluded for now and tracked as TODOs:
- DamageVariation (final 0.85-1.0 random multiplier) -- predict a
  range instead of a point until we wire RNG seeding.
- HandleLateGenAfterHitEffects_Far (Rocky Helmet, Life Orb, Shell
  Bell) -- second damage chain after the hit lands.
- TypeBoostItems (e.g. Charcoal +10% FIRE) -- ApplyLateGenDamageMultipliers
  consumes them, but no current scenario exercises one. Add when
  needed by Tier 2.3.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Type IDs (constants/type_constants.asm).
NORMAL = 0x00
FIGHTING = 0x01
FLYING = 0x02
POISON = 0x03
GROUND = 0x04
ROCK = 0x05
BUG = 0x07
GHOST = 0x08
STEEL = 0x09
FIRE = 0x14
WATER = 0x15
GRASS = 0x16
ELECTRIC = 0x17
PSYCHIC_TYPE = 0x18
ICE = 0x19
DRAGON = 0x1A
DARK = 0x1B

PHYSICAL_MAX = 0x09  # Inclusive: NORMAL..STEEL.

# Effectiveness encoding from constants/battle_constants.asm.
SUPER_EFFECTIVE = 20
EFFECTIVE = 10
NOT_VERY_EFFECTIVE = 5
NO_EFFECT = 0

# Item IDs that participate in the damage-chain stat mods.
HELD_NONE = 0x00
HELD_CHOICE_BAND = 0x74
HELD_CHOICE_SPECS = 0x81
HELD_ASSAULT_VEST = 0x89
HELD_EVOLITE = 0x93

# Mirrors data/types/type_matchups.asm. Multiplier is the "*=" column
# in 5/10/20 encoding (NO_EFFECT, NOT_VERY, SUPER). Default 10 when
# unlisted (matches the asm, where the loop iterates and only applies
# matchups it finds).
_TYPE_MATCHUPS: dict[tuple[int, int], int] = {
    (NORMAL, ROCK): NOT_VERY_EFFECTIVE,
    (NORMAL, STEEL): NOT_VERY_EFFECTIVE,
    (NORMAL, GHOST): NO_EFFECT,
    (NORMAL, PSYCHIC_TYPE): NOT_VERY_EFFECTIVE,  # Hack's tweak; keeps doc accurate
    (FIRE, FIRE): NOT_VERY_EFFECTIVE,
    (FIRE, WATER): NOT_VERY_EFFECTIVE,
    (FIRE, GRASS): SUPER_EFFECTIVE,
    (FIRE, ICE): SUPER_EFFECTIVE,
    (FIRE, BUG): SUPER_EFFECTIVE,
    (FIRE, ROCK): NOT_VERY_EFFECTIVE,
    (FIRE, DRAGON): NOT_VERY_EFFECTIVE,
    (FIRE, STEEL): SUPER_EFFECTIVE,
    (WATER, FIRE): SUPER_EFFECTIVE,
    (WATER, WATER): NOT_VERY_EFFECTIVE,
    (WATER, GRASS): NOT_VERY_EFFECTIVE,
    (WATER, GROUND): SUPER_EFFECTIVE,
    (WATER, ROCK): SUPER_EFFECTIVE,
    (WATER, DRAGON): NOT_VERY_EFFECTIVE,
    (WATER, ICE): NOT_VERY_EFFECTIVE,
    (ELECTRIC, WATER): SUPER_EFFECTIVE,
    (ELECTRIC, ELECTRIC): NOT_VERY_EFFECTIVE,
    (ELECTRIC, GRASS): NOT_VERY_EFFECTIVE,
    (ELECTRIC, GROUND): NO_EFFECT,
    (ELECTRIC, FLYING): SUPER_EFFECTIVE,
    (ELECTRIC, DRAGON): NOT_VERY_EFFECTIVE,
    (GRASS, FIRE): NOT_VERY_EFFECTIVE,
    (GRASS, WATER): SUPER_EFFECTIVE,
    (GRASS, GRASS): NOT_VERY_EFFECTIVE,
    (GRASS, POISON): NOT_VERY_EFFECTIVE,
    (GRASS, GROUND): SUPER_EFFECTIVE,
    (GRASS, BUG): NOT_VERY_EFFECTIVE,
    (GRASS, ROCK): SUPER_EFFECTIVE,
    (GRASS, DRAGON): NOT_VERY_EFFECTIVE,
    (GRASS, STEEL): NOT_VERY_EFFECTIVE,
    (ICE, WATER): NOT_VERY_EFFECTIVE,
    (ICE, GRASS): SUPER_EFFECTIVE,
    (ICE, ICE): NOT_VERY_EFFECTIVE,
    (ICE, GROUND): SUPER_EFFECTIVE,
    (ICE, FLYING): SUPER_EFFECTIVE,
    (ICE, DRAGON): SUPER_EFFECTIVE,
    (ICE, STEEL): NOT_VERY_EFFECTIVE,
    (ICE, FIRE): NOT_VERY_EFFECTIVE,
    (FIGHTING, NORMAL): SUPER_EFFECTIVE,
    (FIGHTING, ICE): SUPER_EFFECTIVE,
    (FIGHTING, GHOST): NO_EFFECT,
    (FIGHTING, FLYING): NOT_VERY_EFFECTIVE,
    (FIGHTING, PSYCHIC_TYPE): NOT_VERY_EFFECTIVE,
    (FIGHTING, ROCK): SUPER_EFFECTIVE,
    (FIGHTING, DARK): SUPER_EFFECTIVE,
    (FIGHTING, STEEL): SUPER_EFFECTIVE,
    (POISON, GRASS): SUPER_EFFECTIVE,
    (POISON, POISON): NOT_VERY_EFFECTIVE,
    (POISON, GROUND): NOT_VERY_EFFECTIVE,
    (POISON, ROCK): NOT_VERY_EFFECTIVE,
    (POISON, GHOST): NOT_VERY_EFFECTIVE,
    (POISON, STEEL): NO_EFFECT,
    (POISON, NORMAL): SUPER_EFFECTIVE,
    (GROUND, ELECTRIC): SUPER_EFFECTIVE,
    (GROUND, GRASS): NOT_VERY_EFFECTIVE,
    (GROUND, POISON): SUPER_EFFECTIVE,
    (GROUND, FLYING): NO_EFFECT,
    (GROUND, BUG): NOT_VERY_EFFECTIVE,
    (GROUND, ROCK): SUPER_EFFECTIVE,
    (GROUND, STEEL): SUPER_EFFECTIVE,
    (GROUND, GHOST): NO_EFFECT,
    (FLYING, ELECTRIC): NOT_VERY_EFFECTIVE,
    (FLYING, GRASS): SUPER_EFFECTIVE,
    (FLYING, FIGHTING): SUPER_EFFECTIVE,
    (FLYING, BUG): SUPER_EFFECTIVE,
    (FLYING, ROCK): NOT_VERY_EFFECTIVE,
    (FLYING, STEEL): NOT_VERY_EFFECTIVE,
    (PSYCHIC_TYPE, FIGHTING): SUPER_EFFECTIVE,
    (PSYCHIC_TYPE, PSYCHIC_TYPE): NOT_VERY_EFFECTIVE,
    (PSYCHIC_TYPE, DARK): NO_EFFECT,
    (PSYCHIC_TYPE, STEEL): NOT_VERY_EFFECTIVE,
    (BUG, FIRE): NOT_VERY_EFFECTIVE,
    (BUG, GRASS): SUPER_EFFECTIVE,
    (BUG, FIGHTING): NOT_VERY_EFFECTIVE,
    (BUG, POISON): NOT_VERY_EFFECTIVE,
    (BUG, FLYING): NOT_VERY_EFFECTIVE,
    (BUG, PSYCHIC_TYPE): SUPER_EFFECTIVE,
    (BUG, GHOST): NOT_VERY_EFFECTIVE,
    (BUG, DARK): SUPER_EFFECTIVE,
    (BUG, STEEL): NOT_VERY_EFFECTIVE,
    (ROCK, FIRE): SUPER_EFFECTIVE,
    (ROCK, ICE): SUPER_EFFECTIVE,
    (ROCK, FIGHTING): NOT_VERY_EFFECTIVE,
    (ROCK, GROUND): NOT_VERY_EFFECTIVE,
    (ROCK, FLYING): SUPER_EFFECTIVE,
    (ROCK, BUG): SUPER_EFFECTIVE,
    (ROCK, STEEL): NOT_VERY_EFFECTIVE,
    (ROCK, PSYCHIC_TYPE): NOT_VERY_EFFECTIVE,
    (GHOST, NORMAL): NO_EFFECT,
    (GHOST, PSYCHIC_TYPE): SUPER_EFFECTIVE,
    (GHOST, DARK): NOT_VERY_EFFECTIVE,
    (GHOST, STEEL): NO_EFFECT,
    (GHOST, GHOST): SUPER_EFFECTIVE,
    (GHOST, FIGHTING): SUPER_EFFECTIVE,
    (DRAGON, DRAGON): SUPER_EFFECTIVE,
    (DRAGON, STEEL): NOT_VERY_EFFECTIVE,
    (DARK, FIGHTING): NOT_VERY_EFFECTIVE,
    (DARK, PSYCHIC_TYPE): SUPER_EFFECTIVE,
    (DARK, GHOST): SUPER_EFFECTIVE,
    (DARK, DARK): NOT_VERY_EFFECTIVE,
    (STEEL, FIRE): NOT_VERY_EFFECTIVE,
    (STEEL, WATER): NOT_VERY_EFFECTIVE,
    (STEEL, ICE): SUPER_EFFECTIVE,
    (STEEL, ROCK): SUPER_EFFECTIVE,
    (STEEL, STEEL): NOT_VERY_EFFECTIVE,
    (STEEL, FIGHTING): NOT_VERY_EFFECTIVE,
}


def matchup(move_type: int, defender_type: int) -> int:
    """Single-axis matchup multiplier. Defaults to EFFECTIVE (10) when
    the (att, def) pair isn't in the table -- mirrors the asm loop, which
    leaves wTypeMatchup unmodified at its initial 0x10 if no rows match."""
    return _TYPE_MATCHUPS.get((move_type, defender_type), EFFECTIVE)


@dataclass
class BattleInputs:
    attacker_level: int
    move_bp: int
    move_type: int
    is_physical: bool

    attacker_atk: int        # Atk in physical category, SpAtk in special
    defender_def: int        # Def in physical category, SpDef in special

    attacker_types: tuple[int, int]
    defender_types: tuple[int, int]

    user_item: int = HELD_NONE
    opponent_item: int = HELD_NONE
    can_evolve_attacker: bool = False
    can_evolve_defender: bool = False

    is_critical: bool = False

    # When the move's effect is one of the "skip damage" specials (Self-
    # destruct halving def is the only one we model today), wire it here.
    is_selfdestruct: bool = False


def _apply_user_item_stat_mod(inp: BattleInputs, atk: int) -> int:
    """ApplyChoiceBandBoost / ApplyChoiceSpecsBoost in late_gen_held_items.asm."""
    if inp.is_physical and inp.user_item == HELD_CHOICE_BAND:
        return atk * 3 // 2
    if not inp.is_physical and inp.user_item == HELD_CHOICE_SPECS:
        return atk * 3 // 2
    return atk


def _apply_opponent_item_stat_mod(inp: BattleInputs, deff: int) -> int:
    """ApplyAssaultVestBoostToDefense / ApplyEvioliteDefenseBoost /
    ApplyEvioliteSpDefBoost. Eviolite hooks the .SpeciesCanEvolve check;
    we pass that as a boolean rather than enumerating evo data."""
    if not inp.is_physical and inp.opponent_item == HELD_ASSAULT_VEST:
        deff = deff * 3 // 2
    if inp.opponent_item == HELD_EVOLITE and inp.can_evolve_defender:
        deff = deff * 3 // 2
    return deff


def _stab(inp: BattleInputs, dmg: int) -> int:
    """3/2 if the move's type matches either of the attacker's types."""
    if inp.move_type in inp.attacker_types:
        return dmg + dmg // 2
    return dmg


def _type_matchup(inp: BattleInputs, dmg: int) -> int:
    """Loop over defender types; multiply / 10 each row that matches.
    Mirrors the BattleCommand_Stab matchup loop's behavior on a 16-bit
    wCurDamage with the integer-floor + clamp-to-1 quirks."""
    for d_type in inp.defender_types:
        # Skip the second iteration if defender's type1 == type2 (the asm
        # loop iterates the matchup table once and matches by row, not by
        # defender's type slot, but since we walk per defender slot we
        # need to dedupe).
        if d_type == inp.defender_types[0] and d_type != inp.defender_types[1]:
            continue
    # Iterate the table by row (correct mirror of the asm loop):
    for (att, deff), mult in _TYPE_MATCHUPS.items():
        if att != inp.move_type:
            continue
        if deff != inp.defender_types[0] and deff != inp.defender_types[1]:
            continue
        if mult == NO_EFFECT:
            # Multiplier is 0; product is 0. Asm path: jr z .ok skips
            # the divide and writes hMultiplicand[1,2] back, which still
            # holds wCurDamage's bytes -- so the value is UNCHANGED. The
            # wAttackMissed flag is set; that signal is the marker, not
            # wCurDamage. We mirror exactly.
            return dmg
        product = dmg * mult
        quot = product // 10
        if quot == 0 and product != 0:
            # Asm "ld a, 1; ldh [hMultiplicand + 2], a" floor-clamp.
            quot = 1
        dmg = quot
    return dmg


def predict_damage(inp: BattleInputs) -> int:
    """Mirror BattleCommand_DamageCalc + .CriticalMultiplier + BattleCommand_Stab.

    Returns wCurDamage as it would appear after the three-phase chain
    that `clobber_smoke` reads: DamageStats -> DamageCalc -> Stab.
    """
    atk = _apply_user_item_stat_mod(inp, inp.attacker_atk)
    deff = _apply_opponent_item_stat_mod(inp, inp.defender_def)

    if inp.is_selfdestruct:
        deff = max(1, deff // 2)

    if inp.move_bp == 0:
        return 0

    # Level term: floor(2*L / 5) + 2.
    q = (2 * inp.attacker_level) // 5 + 2
    q = q * inp.move_bp
    q = q * atk
    q = q // max(1, deff)  # asm has a min-1 clamp on def
    q = q // 50

    # Crit doubles the pre-additive quotient.
    if inp.is_critical:
        q *= 2
        if q > 0xFFFF:
            q = 0xFFFF

    # wCurDamage += q + 2 (with cap at MAX_DAMAGE = 999, MIN_DAMAGE = 2).
    dmg = q + 2
    DAMAGE_CAP = 997
    if dmg > DAMAGE_CAP:
        dmg = DAMAGE_CAP
    dmg = min(999, dmg + 0)  # clamp at 999 after the +MIN_DAMAGE step

    # STAB: 3/2 if move type matches attacker.
    dmg = _stab(inp, dmg)

    # Type matchup loop: multiply / 10 per matching row.
    dmg = _type_matchup(inp, dmg)

    return dmg


# ---------------------------------------------------------------------------
# Self-test: predict the 8 clobber_smoke scenarios and assert centers match.
# ---------------------------------------------------------------------------

PIDGEY_TYPES = (NORMAL, FLYING)
CYNDAQUIL_TYPES = (FIRE, FIRE)


def _self_test() -> list[tuple[str, int, int]]:
    """Returns (scenario_name, expected_from_paper_math, oracle_predicted).
    Expected centers come from the Pass 1 BUG_CHECK paper-math table.
    """
    cases: list[tuple[str, int, BattleInputs]] = []

    # physical_no_items: Pidgey lvl 2 atk 6 Tackle vs Cyndaquil def 9.
    cases.append((
        "physical_no_items", 4,
        BattleInputs(
            attacker_level=2, move_bp=40, move_type=NORMAL, is_physical=True,
            attacker_atk=6, defender_def=9,
            attacker_types=PIDGEY_TYPES, defender_types=CYNDAQUIL_TYPES,
        ),
    ))

    # physical_critical: same + crit.
    cases.append((
        "physical_critical", 6,
        BattleInputs(
            attacker_level=2, move_bp=40, move_type=NORMAL, is_physical=True,
            attacker_atk=6, defender_def=9,
            attacker_types=PIDGEY_TYPES, defender_types=CYNDAQUIL_TYPES,
            is_critical=True,
        ),
    ))

    # physical_choice_band: Pidgey atk 6 -> Choice Band -> 9 (still Q=1).
    cases.append((
        "physical_choice_band", 4,
        BattleInputs(
            attacker_level=2, move_bp=40, move_type=NORMAL, is_physical=True,
            attacker_atk=6, defender_def=9,
            attacker_types=PIDGEY_TYPES, defender_types=CYNDAQUIL_TYPES,
            user_item=HELD_CHOICE_BAND,
        ),
    ))

    # physical_eviolite_def: Cyndaquil def 9 -> Eviolite -> 13.
    cases.append((
        "physical_eviolite_def", 3,
        BattleInputs(
            attacker_level=2, move_bp=40, move_type=NORMAL, is_physical=True,
            attacker_atk=6, defender_def=9,
            attacker_types=PIDGEY_TYPES, defender_types=CYNDAQUIL_TYPES,
            opponent_item=HELD_EVOLITE, can_evolve_defender=True,
        ),
    ))

    # special_no_items: Cyndaquil lvl 5 spatk 11 Ember vs Pidgey spdef 5.
    cases.append((
        "special_no_items", 13,
        BattleInputs(
            attacker_level=5, move_bp=40, move_type=FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=CYNDAQUIL_TYPES, defender_types=PIDGEY_TYPES,
        ),
    ))

    cases.append((
        "special_choice_specs", 18,
        BattleInputs(
            attacker_level=5, move_bp=40, move_type=FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=CYNDAQUIL_TYPES, defender_types=PIDGEY_TYPES,
            user_item=HELD_CHOICE_SPECS,
        ),
    ))

    cases.append((
        "special_assault_vest", 10,
        BattleInputs(
            attacker_level=5, move_bp=40, move_type=FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=CYNDAQUIL_TYPES, defender_types=PIDGEY_TYPES,
            opponent_item=HELD_ASSAULT_VEST,
        ),
    ))

    cases.append((
        "special_eviolite_spd", 10,
        BattleInputs(
            attacker_level=5, move_bp=40, move_type=FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=CYNDAQUIL_TYPES, defender_types=PIDGEY_TYPES,
            opponent_item=HELD_EVOLITE, can_evolve_defender=True,
        ),
    ))

    return [(name, expected, predict_damage(inp)) for name, expected, inp in cases]


if __name__ == "__main__":
    fails = 0
    for name, expected, got in _self_test():
        status = "ok" if got == expected else "FAIL"
        print(f"{name:<28s} expected={expected:>3d} oracle={got:>3d}  {status}")
        if got != expected:
            fails += 1
    if fails:
        print(f"\n{fails} oracle prediction(s) disagree with paper math; fix oracle.")
        raise SystemExit(1)
    print(f"\nall {len(_self_test())} oracle predictions match paper math")
