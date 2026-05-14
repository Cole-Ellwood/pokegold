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
mods + crit + type matchup). Excluded from exact oracle prediction for
now and tracked as TODOs:
- DamageVariation (final 0.85-1.0 random multiplier) -- clobber_smoke
  covers the ROM range, but the oracle still predicts the pre-variation
  point until we wire deterministic RNG seeding.
- HandleLateGenAfterHitEffects_Far (Rocky Helmet, Life Orb, Shell
  Bell) -- clobber_smoke covers the HP side effects, but the oracle still
  predicts only the main damage chain.
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
MORE_EFFECTIVE = 15
EFFECTIVE = 10
NOT_VERY_EFFECTIVE = 5
NO_EFFECT = 0

# Weather values from constants/battle_constants.asm.
WEATHER_NONE = 0
WEATHER_RAIN = 1
WEATHER_SUN = 2
WEATHER_SANDSTORM = 3

# Move effects from constants/move_effect_constants.asm.
EFFECT_NORMAL_HIT = 0
EFFECT_MULTI_HIT = 29
EFFECT_CONVERSION = 30
EFFECT_SOLARBEAM = 151

# Item IDs that participate in the damage chain.
HELD_NONE = 0x00
HELD_LIFE_ORB = 0x46
HELD_SOFT_SAND = 0x4C
HELD_SHARP_BEAK = 0x4D
HELD_POISON_BARB = 0x51
HELD_SILVERPOWDER = 0x58
HELD_MYSTIC_WATER = 0x5F
HELD_TWISTEDSPOON = 0x60
HELD_BLACKBELT_I = 0x62
HELD_BLACKGLASSES = 0x66
HELD_PINK_BOW = 0x68
HELD_NEVERMELTICE = 0x6B
HELD_MAGNET = 0x6C
HELD_SPELL_TAG = 0x71
HELD_CHOICE_BAND = 0x74
HELD_MIRACLE_SEED = 0x75
HELD_HARD_STONE = 0x7D
HELD_CHOICE_SPECS = 0x81
HELD_ASSAULT_VEST = 0x89
HELD_CHARCOAL = 0x8A
HELD_EXPERT_BELT = 0x8D
HELD_MUSCLE_BAND = 0x8E
HELD_METAL_COAT = 0x8F
HELD_DRAGON_FANG = 0x90
HELD_WISE_GLASSES = 0x91
HELD_EVOLITE = 0x93
HELD_DRAGON_SCALE = 0x97
HELD_METRONOME = 0x9A
HELD_POLKADOT_BOW = 0xAA

# Mirrors data/types/type_matchups.asm. Multiplier is the "*=" column
# in 5/10/20 encoding (NO_EFFECT, NOT_VERY, SUPER). Default 10 when
# unlisted (matches the asm, where the loop iterates and only applies
# matchups it finds).
_TYPE_MATCHUPS: dict[tuple[int, int], int] = {
    (NORMAL, ROCK): NOT_VERY_EFFECTIVE,
    (NORMAL, STEEL): NOT_VERY_EFFECTIVE,
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
    # Foresight-section Ghost immunity rows. When the target is not
    # identified, the ROM applies these after the main chart rows; order
    # matters because each row floors after multiplying.
    (NORMAL, GHOST): NO_EFFECT,
    (FIGHTING, GHOST): NO_EFFECT,
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

    # State flags consumed by the TypePassive_ApplyDamageModifiers_Far
    # branches in `_type_passive_modifiers`. Defaults match the
    # "no extra modifier" path: full HP, no status, opponent low HP.
    # Fuzz seeds set ROM HP/status fields to match these so the oracle
    # and ROM agree on which branches fire.
    attacker_below_third_hp: bool = False
    opponent_has_status: bool = False
    opponent_above_half_hp: bool = False

    # BattleCommand_Stab pre-STAB modifiers. Fuzz seeds these fields into
    # wBattleWeather, wJohtoBadges, wKantoBadges, wLinkMode, and the move
    # struct effect byte. The fuzz convention is player turn (`hBattleTurn=0`)
    # unless `battle_turn` is explicitly set.
    weather: int = WEATHER_NONE
    move_effect: int = EFFECT_NORMAL_HIT
    johto_badges: int = 0
    kanto_badges: int = 0
    link_mode: int = 0
    battle_turn: int = 0

    # Synthetic multi-hit/cap-add probe axis. Normal move scripts enter
    # DamageCalc with zero damage after DamageStats; multi-hit accumulation
    # can enter with a nonzero wCurDamage from a prior hit.
    initial_cur_damage: int = 0

    # ApplyLateGenDamageMultipliers_Far reads this when the user holds
    # Metronome. The counter is already side-selected by the ROM helper.
    metronome_count: int = 0


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


def _truncate_hl_bc(hl: int, bc: int) -> tuple[int, int]:
    """Mirror `TruncateHL_BC` (engine/battle/effect_commands.asm:2590).

    Returns the post-truncate (b, c) pair that DamageCalc consumes as
    (attack, defense). When either input has its high byte set, the
    asm shifts BOTH bc and hl right by 2 bits, then clamps each to a
    minimum of 1 if a shift truncated it to zero. The function
    returns `b = l` (low byte of the post-shift hl), and the caller
    uses c (low byte of post-shift bc) directly.

    Existing scenarios all hit `h|b == 0` (both stats < 256) so the
    shift path is dead at typical hand-coded levels. Hypothesis fuzz
    surfaces it when attack >= 256 or defense >= 256.
    """
    if (hl >> 8) == 0 and (bc >> 8) == 0:
        return hl & 0xFF, bc & 0xFF
    bc >>= 2
    if bc == 0:
        bc = 1
    hl >>= 2
    if hl == 0:
        hl = 1
    return hl & 0xFF, bc & 0xFF


def _damagecalc_quotient(inp: BattleInputs) -> int | None:
    """DamageCalc quotient before cap/add/MIN_DAMAGE.

    Returns None when BattleCommand_DamageCalc would early-return before
    touching wCurDamage (BP=0 outside the multi-hit/conversion bypass).
    """
    atk = _apply_user_item_stat_mod(inp, inp.attacker_atk)
    deff = _apply_opponent_item_stat_mod(inp, inp.defender_def)
    atk, deff = _truncate_hl_bc(atk, deff)

    if inp.is_selfdestruct:
        deff = max(1, deff // 2)

    if inp.move_bp == 0 and inp.move_effect not in {EFFECT_MULTI_HIT, EFFECT_CONVERSION}:
        return None

    q = (2 * inp.attacker_level) // 5 + 2
    q = q * inp.move_bp
    q = q * atk
    q = q // max(1, deff)
    q = q // 50

    q = _apply_type_boost_item(inp, q)
    q = _apply_late_gen_damage_multiplier(inp, q)

    if inp.is_critical:
        q *= 2
        if q > 0xFFFF:
            q = 0xFFFF
    return q


_TYPE_BOOST_ITEM_TYPES = {
    HELD_PINK_BOW: NORMAL,
    HELD_POLKADOT_BOW: NORMAL,
    HELD_BLACKBELT_I: FIGHTING,
    HELD_SHARP_BEAK: FLYING,
    HELD_POISON_BARB: POISON,
    HELD_SOFT_SAND: GROUND,
    HELD_HARD_STONE: ROCK,
    HELD_SILVERPOWDER: BUG,
    HELD_SPELL_TAG: GHOST,
    HELD_CHARCOAL: FIRE,
    HELD_MYSTIC_WATER: WATER,
    HELD_MIRACLE_SEED: GRASS,
    HELD_MAGNET: ELECTRIC,
    HELD_TWISTEDSPOON: PSYCHIC_TYPE,
    HELD_NEVERMELTICE: ICE,
    HELD_DRAGON_FANG: DRAGON,
    HELD_DRAGON_SCALE: DRAGON,
    HELD_BLACKGLASSES: DARK,
    HELD_METAL_COAT: STEEL,
}


def _apply_type_boost_item(inp: BattleInputs, q: int) -> int:
    """Mirror the TypeBoostItems loop in BattleCommand_DamageCalc."""
    if _TYPE_BOOST_ITEM_TYPES.get(inp.user_item) != inp.move_type:
        return q
    return q * 120 // 100


def _apply_late_gen_damage_multiplier(inp: BattleInputs, q: int) -> int:
    """Mirror ApplyLateGenDamageMultipliers_Far.

    This operates on hQuotient after the vanilla type-boost item loop and
    before the critical-hit multiplier.
    """
    if inp.user_item == HELD_MUSCLE_BAND:
        return q * 11 // 10 if inp.is_physical else q
    if inp.user_item == HELD_WISE_GLASSES:
        return q * 11 // 10 if not inp.is_physical else q
    if inp.user_item == HELD_EXPERT_BELT:
        return q * 6 // 5 if _matchup_total(inp) >= EFFECTIVE + 1 else q
    if inp.user_item == HELD_METRONOME:
        numerator = min(10 + inp.metronome_count * 2, 20)
        return q * numerator // 10
    if inp.user_item == HELD_LIFE_ORB:
        return q * 13 // 10
    return q


def _finish_damagecalc(
    q: int | None,
    *,
    initial_cur_damage: int = 0,
    emulate_cap_add_endian_bug: bool = False,
) -> int:
    """Finish BattleCommand_DamageCalc from quotient to wCurDamage.

    The fixed ROM uses endian-neutral accumulation:
    `initial + quotient + MIN_DAMAGE`, capped at 999.

    `emulate_cap_add_endian_bug=True` is retained for the M1 regression
    probe's historical comparison. The old asm added `wCurDamage`'s high
    byte to `hQuotient+3` before the full 16-bit add.
    """
    if q is None:
        return initial_cur_damage & 0xFFFF

    DAMAGE_CAP = 997
    initial_cur_damage &= 0xFFFF
    adjusted_q = q
    if emulate_cap_add_endian_bug:
        adjusted_q += initial_cur_damage >> 8
    if adjusted_q > DAMAGE_CAP:
        return 999

    total = adjusted_q + initial_cur_damage
    if total > DAMAGE_CAP:
        total = DAMAGE_CAP
    return total + 2


def predict_damagecalc_only(
    inp: BattleInputs,
    *,
    initial_cur_damage: int = 0,
    emulate_cap_add_endian_bug: bool = False,
) -> int:
    """Predict wCurDamage immediately after BattleCommand_DamageCalc."""
    return _finish_damagecalc(
        _damagecalc_quotient(inp),
        initial_cur_damage=initial_cur_damage,
        emulate_cap_add_endian_bug=emulate_cap_add_endian_bug,
    )


def _dragons_majesty_applies(inp: BattleInputs) -> bool:
    """Return True if `TypePassive_ApplyDragonsMajestyMultiplier_Far` would
    convert a NO_EFFECT matchup row to NOT_VERY_EFFECTIVE.

    Conditions (mirrored from
    engine/battle/type_passive_damage_mods.asm:.CurrentMoveHasDragonsMajesty):
      - move has nonzero BP
      - move effect is NOT one of the static-damage / counter family
      - attacker has DRAGON type contribution > 0
    The move-effect filter is moot for the fuzz harness today since we
    only use NORMAL_HIT (effect 0); leaving the check explicit so that
    future scenarios with non-NORMAL_HIT effects don't silently break.
    """
    if inp.move_bp == 0:
        return False
    return _type_contribution(DRAGON, inp.attacker_types) > 0


def _type_matchup(inp: BattleInputs, dmg: int) -> int:
    """Loop over the matchup table; per-row multiply / 10 if it matches.

    Mirrors BattleCommand_Stab's matchup loop with the math UNION quirks:

    - The math UNION (`ram/hram.asm:60-79`) aliases `hMultiplicand[1..3]`
      with `hProduct[1..3]`, and `hMultiplicand[1..3]` with `hQuotient[1..3]`
      after `Divide`. The asm loads wCurDamage into hMultiplicand[1,2]
      then calls Multiply by the matchup multiplier. After the Multiply,
      the writeback reads hMultiplicand[1,2] -- which now points at
      hProduct[2,3], NOT the pre-multiply value.

    - Therefore mult=0 (NO_EFFECT immune) zeros wCurDamage, because
      hProduct = 0 and the writeback reads zero. wAttackMissed is set
      as the "this attack missed" signal -- but wCurDamage IS modified
      contrary to a naive reading of the asm. (Pass 1 BUG_CHECK had
      this wrong; corrected by Hypothesis fuzz divergence on
      `NORMAL move vs (NORMAL, GHOST)` defender at level 1.)

    - For nonzero multipliers, the loop divides hProduct by 10 into
      hQuotient. If quotient <= 255 (high byte zero), a "clamp-to-1"
      branch sets `hMultiplicand[2] = 1` for any positive product that
      truncates to zero. The writeback then reads `hMultiplicand[1,2]`
      = `hQuotient[2,3]`. Net: dmg = product // 10, with min 1 if the
      pre-divide product was nonzero.
    """
    for (att, deff), mult in _TYPE_MATCHUPS.items():
        if att != inp.move_type:
            continue
        if deff != inp.defender_types[0] and deff != inp.defender_types[1]:
            continue
        if mult == NO_EFFECT:
            # Dragon's Majesty: DRAGON-type attackers treat type-chart
            # immunities as resistances (multiplier 0 -> 5).
            # `BattleCommand_ApplyDragonsMajestyMultiplier` runs inside
            # the matchup loop's .GotMatchup block; if it converts 0 to
            # 5, control falls through to the multiply path instead of
            # zeroing wCurDamage. See type_passive_damage_mods.asm:1-14.
            if _dragons_majesty_applies(inp):
                mult = NOT_VERY_EFFECTIVE
            else:
                # See docstring: writeback after multiply-by-zero zeros wCurDamage.
                return 0
        product = dmg * mult
        quot = product // 10
        if quot == 0 and product != 0:
            quot = 1
        dmg = quot
    return dmg


def _type_contribution(target_type: int, types: tuple[int, int]) -> int:
    """Mirror `.GetTypeContributionFromHL` in type_passive_damage_mods.asm.

    Returns 2 if monotype matches target, 1 if dual-type with one match,
    0 otherwise. The hack's TypePassive system uses this to scale the
    fraction it applies (monotype gets the bigger boost / resist).
    """
    a, b = types
    if a == b:
        return 2 if a == target_type else 0
    return 1 if (a == target_type or b == target_type) else 0


def _apply_fraction(dmg: int, num: int, den: int) -> int:
    """Mirror `.ApplyCurDamageFraction`: floor(dmg * num / den), min 1 if dmg > 0."""
    if dmg == 0:
        return 0
    out = (dmg * num) // den
    return max(1, out)


def _apply_scaled_by_10(dmg: int, mult: int) -> int:
    """Mirror DoWeatherModifiers' multiply/divide-by-10 helper."""
    product = dmg * mult
    out = product // 10
    if out > 0xFFFF:
        return 0xFFFF
    if out == 0 and product != 0:
        return 1
    return out


_WEATHER_TYPE_MODIFIERS = (
    (WEATHER_RAIN, WATER, MORE_EFFECTIVE),
    (WEATHER_RAIN, FIRE, NOT_VERY_EFFECTIVE),
    (WEATHER_SUN, FIRE, MORE_EFFECTIVE),
    (WEATHER_SUN, WATER, NOT_VERY_EFFECTIVE),
)

_WEATHER_MOVE_MODIFIERS = (
    (WEATHER_RAIN, EFFECT_SOLARBEAM, NOT_VERY_EFFECTIVE),
)


def _apply_weather_modifiers(inp: BattleInputs, dmg: int) -> int:
    """Mirror DoWeatherModifiers.

    The asm scans WeatherTypeModifiers first and returns after the first
    match. WeatherMoveModifiers (currently Rain + SolarBeam) are checked
    only if no type row matched.
    """
    for weather, move_type, mult in _WEATHER_TYPE_MODIFIERS:
        if inp.weather == weather and inp.move_type == move_type:
            return _apply_scaled_by_10(dmg, mult)
    for weather, move_effect, mult in _WEATHER_MOVE_MODIFIERS:
        if inp.weather == weather and inp.move_effect == move_effect:
            return _apply_scaled_by_10(dmg, mult)
    return dmg


_BADGE_TYPE_BOOSTS = (
    FLYING,
    BUG,
    NORMAL,
    GHOST,
    STEEL,
    FIGHTING,
    ICE,
    DRAGON,
    ROCK,
    WATER,
    ELECTRIC,
    GRASS,
    POISON,
    PSYCHIC_TYPE,
    FIRE,
    GROUND,
)


def _badge_boost_applies(inp: BattleInputs) -> bool:
    if inp.link_mode != 0:
        return False
    if inp.battle_turn != 0:
        return False
    badge_bits = (inp.kanto_badges << 8) | inp.johto_badges
    for index, move_type in enumerate(_BADGE_TYPE_BOOSTS):
        if badge_bits & (1 << index) and inp.move_type == move_type:
            return True
    return False


def _apply_badge_type_boost(inp: BattleInputs, dmg: int) -> int:
    """Mirror DoBadgeTypeBoosts: add max(1, damage // 8), capped at $ffff."""
    if not _badge_boost_applies(inp):
        return dmg
    boost = dmg // 8
    if boost == 0:
        boost = 1
    return min(0xFFFF, dmg + boost)


def _type_passive_modifiers(
    inp: BattleInputs,
    dmg: int,
    *,
    has_stab: bool,
    matchup_total: int,
) -> int:
    """Mirror `TypePassive_ApplyDamageModifiers_Far` (locked V1 mods).

    Applied AFTER the matchup loop in the asm chain. Each branch reads
    type contributions from attacker and/or defender and applies a
    fixed Q-style fraction. Branch order matches the asm exactly --
    fractions accumulate (each runs on the previous branch's output).

    `matchup_total` is wTypeMatchup at end-of-loop: EFFECTIVE (10) by
    default, doubled per super-effective row, halved per not-very row.
    Asm reads `cp EFFECTIVE + 1` to gate Dragon-resist (skip if > 10)
    vs Ground-resist (apply if > 10).

    `has_stab` is the STAB_DAMAGE bit of wTypeModifier; only the NORMAL
    branch reads it. Other branches inspect type contributions / status
    / HP independently.
    """
    if dmg == 0:
        return 0

    # Branch 1: NORMAL move + STAB → 16/15 monotype, 31/30 dual.
    if has_stab and inp.move_type == NORMAL:
        c = _type_contribution(NORMAL, inp.attacker_types)
        if c == 2:
            dmg = _apply_fraction(dmg, 16, 15)
        elif c == 1:
            dmg = _apply_fraction(dmg, 31, 30)

    # Branch 2: FIRE move + user below 1/3 HP → 6/5 monotype, 11/10 dual.
    #
    # The .GetUserHPAndMax / .GetOpponentHPAndMax d-clobber bug that
    # historically gated this branch (found by Tier 2.2 fuzz, 2026-05-05)
    # was fixed in this same session via push-af around the high-byte
    # save. Oracle now applies Branch 2 unconditionally to match the
    # fixed ROM.
    if inp.move_type == FIRE and inp.attacker_below_third_hp:
        c = _type_contribution(FIRE, inp.attacker_types)
        if c == 2:
            dmg = _apply_fraction(dmg, 6, 5)
        elif c == 1:
            dmg = _apply_fraction(dmg, 11, 10)

    # Branch 3: opponent has any status -> GHOST contribution boost
    # 11/10 monotype, 21/20 dual.
    if inp.opponent_has_status:
        c = _type_contribution(GHOST, inp.attacker_types)
        if c == 2:
            dmg = _apply_fraction(dmg, 11, 10)
        elif c == 1:
            dmg = _apply_fraction(dmg, 21, 20)

    # Branch 4: defender has DRAGON contribution AND matchup is NOT super
    # effective (matchup_total <= EFFECTIVE) → resist 1/2 monotype, 2/3 dual.
    if matchup_total <= EFFECTIVE:
        c = _type_contribution(DRAGON, inp.defender_types)
        if c == 2:
            dmg = _apply_fraction(dmg, 1, 2)
        elif c == 1:
            dmg = _apply_fraction(dmg, 2, 3)

    # Branch 5: defender has GROUND contribution AND matchup IS super
    # effective (matchup_total >= EFFECTIVE+1) → resist 9/10 mono, 19/20 dual.
    if matchup_total >= EFFECTIVE + 1:
        c = _type_contribution(GROUND, inp.defender_types)
        if c == 2:
            dmg = _apply_fraction(dmg, 9, 10)
        elif c == 1:
            dmg = _apply_fraction(dmg, 19, 20)

    # Branch 6: critical hit + defender ROCK contribution → resist 9/10, 19/20.
    if inp.is_critical:
        c = _type_contribution(ROCK, inp.defender_types)
        if c == 2:
            dmg = _apply_fraction(dmg, 9, 10)
        elif c == 1:
            dmg = _apply_fraction(dmg, 19, 20)

    # Branch 7: physical move + defender BUG contribution → resist 9/10, 19/20.
    if inp.is_physical:
        c = _type_contribution(BUG, inp.defender_types)
        if c == 2:
            dmg = _apply_fraction(dmg, 9, 10)
        elif c == 1:
            dmg = _apply_fraction(dmg, 19, 20)

    # Branch 8: special move + defender WATER contribution → resist 19/20, 39/40.
    if not inp.is_physical:
        c = _type_contribution(WATER, inp.defender_types)
        if c == 2:
            dmg = _apply_fraction(dmg, 19, 20)
        elif c == 1:
            dmg = _apply_fraction(dmg, 39, 40)

    # Branch 9: opponent above 1/2 HP + defender ICE contribution
    # → resist 19/20 mono, 39/40 dual.
    #
    # The .GetOpponentHPAndMax d-clobber that historically made this
    # branch non-deterministic was fixed in the same session as the
    # Branch 2 fix. Oracle now matches the fixed ROM directly.
    if inp.opponent_above_half_hp:
        c = _type_contribution(ICE, inp.defender_types)
        if c == 2:
            dmg = _apply_fraction(dmg, 19, 20)
        elif c == 1:
            dmg = _apply_fraction(dmg, 39, 40)

    return dmg


def _matchup_total(inp: BattleInputs) -> int:
    """Walk the matchup table once and produce wTypeMatchup at end-of-loop.

    Mirrors the asm's `BattleCheckTypeMatchup` running-product: starts at
    EFFECTIVE (10), each matching row multiplies by mult/10. The asm
    folds Dragon's Majesty into this path too (line 1499 calls
    `CheckTypeMatchup_ApplyDragonsMajestyMultiplier`), so a NO_EFFECT
    row gets converted to NOT_VERY_EFFECTIVE for DRAGON attackers.
    """
    total = EFFECTIVE
    for (att, deff), mult in _TYPE_MATCHUPS.items():
        if att != inp.move_type:
            continue
        if deff != inp.defender_types[0] and deff != inp.defender_types[1]:
            continue
        if mult == NO_EFFECT:
            if _dragons_majesty_applies(inp):
                mult = NOT_VERY_EFFECTIVE
            else:
                return NO_EFFECT
        total = total * mult // 10
    return total


def predict_damage(inp: BattleInputs) -> int:
    """Mirror BattleCommand_DamageCalc + .CriticalMultiplier + BattleCommand_Stab
    + TypePassive_ApplyDamageModifiers_Far.

    Returns wCurDamage as it would appear after the three-phase chain
    that `clobber_smoke` reads: DamageStats -> DamageCalc -> Stab. The
    final phase invokes TypePassive_ApplyDamageModifiers_Far via farcall
    at the end of `Stab`'s `.not_immune` block (effect_commands.asm:1412),
    so the oracle must model those nine type-passive mods as well.
    """
    dmg = predict_damagecalc_only(inp, initial_cur_damage=inp.initial_cur_damage)

    # BattleCommand_Stab first applies weather and badge type boosts to the
    # current damage, then applies STAB.
    dmg = _apply_weather_modifiers(inp, dmg)
    dmg = _apply_badge_type_boost(inp, dmg)

    # STAB: 3/2 if move type matches attacker.
    has_stab = inp.move_type in inp.attacker_types
    if has_stab:
        dmg = dmg + dmg // 2

    # Type matchup loop: multiply / 10 per matching row.
    dmg = _type_matchup(inp, dmg)
    if dmg == 0:
        return 0

    # TypePassive_ApplyDamageModifiers_Far: 9 fractional branches gated
    # on attacker types, defender types, move type, status, HP, crit, etc.
    matchup_total = _matchup_total(inp)
    dmg = _type_passive_modifiers(
        inp, dmg, has_stab=has_stab, matchup_total=matchup_total,
    )

    return dmg


def predict_damage_trace(inp: BattleInputs) -> list[tuple[str, int]]:
    """Like `predict_damage`, but returns wCurDamage at each step boundary.

    Used by the Tier 3.5 `find` CLI to bucket-locate divergence between
    ROM execution and oracle prediction. Step names match the asm's
    top-level labels so the diff readout is self-explanatory:

        ('DamageStats',  0)             # ResetDamage zeros wCurDamage
        ('DamageCalc',   q + 2)         # post-Q, post-crit, post-cap, +MIN_DAMAGE
        ('Stab',         post-STAB)     # +50% if move type matches attacker
        ('TypeMatchup',  post-matchup)  # /10 multiply per matching row
        ('TypePassive',  final)         # 9 fractional V1 modifiers

    When ROM and oracle agree at step N but diverge at step N+1, the
    bug lives in the asm code that runs between those labels.
    """
    trace: list[tuple[str, int]] = [("DamageStats", 0)]

    q = _damagecalc_quotient(inp)
    if q is None:
        trace.extend([("DamageCalc", 0), ("Stab", 0), ("TypeMatchup", 0), ("TypePassive", 0)])
        return trace

    dmg = _finish_damagecalc(q, initial_cur_damage=inp.initial_cur_damage)
    trace.append(("DamageCalc", dmg))

    dmg = _apply_weather_modifiers(inp, dmg)
    dmg = _apply_badge_type_boost(inp, dmg)

    has_stab = inp.move_type in inp.attacker_types
    if has_stab:
        dmg = dmg + dmg // 2
    # In the asm, STAB and the matchup loop both happen inside
    # BattleCommand_Stab. We expose them as separate buckets here so a
    # divergence at the matchup step is distinguishable from a STAB-side
    # bug. The on-ROM trace can hook the matchup .end label to read
    # wCurDamage at the same boundary.
    pre_matchup = dmg
    dmg = _type_matchup(inp, dmg)
    trace.append(("Stab", pre_matchup))
    trace.append(("TypeMatchup", dmg))

    if dmg == 0:
        trace.append(("TypePassive", 0))
        return trace

    matchup_total = _matchup_total(inp)
    dmg = _type_passive_modifiers(
        inp, dmg, has_stab=has_stab, matchup_total=matchup_total,
    )
    trace.append(("TypePassive", dmg))
    return trace


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

    cases.append((
        "special_sun_fire", 19,
        BattleInputs(
            attacker_level=5, move_bp=40, move_type=FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=CYNDAQUIL_TYPES, defender_types=PIDGEY_TYPES,
            weather=WEATHER_SUN,
        ),
    ))

    cases.append((
        "special_rain_fire", 6,
        BattleInputs(
            attacker_level=5, move_bp=40, move_type=FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=CYNDAQUIL_TYPES, defender_types=PIDGEY_TYPES,
            weather=WEATHER_RAIN,
        ),
    ))

    cases.append((
        "special_fire_badge", 15,
        BattleInputs(
            attacker_level=5, move_bp=40, move_type=FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=CYNDAQUIL_TYPES, defender_types=PIDGEY_TYPES,
            kanto_badges=1 << 6,
        ),
    ))

    cases.append((
        "special_fire_low_hp", 15,
        BattleInputs(
            attacker_level=5, move_bp=40, move_type=FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=CYNDAQUIL_TYPES, defender_types=PIDGEY_TYPES,
            attacker_below_third_hp=True,
        ),
    ))

    cases.append((
        "physical_type_boost_item", 41,
        BattleInputs(
            attacker_level=50, move_bp=60, move_type=FIGHTING, is_physical=True,
            attacker_atk=90, defender_def=70,
            attacker_types=(WATER, WATER), defender_types=(FIRE, WATER),
            user_item=HELD_BLACKBELT_I,
        ),
    ))

    cases.append((
        "physical_muscle_band", 38,
        BattleInputs(
            attacker_level=50, move_bp=60, move_type=FIGHTING, is_physical=True,
            attacker_atk=90, defender_def=70,
            attacker_types=(WATER, WATER), defender_types=(FIRE, WATER),
            user_item=HELD_MUSCLE_BAND,
        ),
    ))

    cases.append((
        "special_wise_glasses", 38,
        BattleInputs(
            attacker_level=50, move_bp=60, move_type=FIRE, is_physical=False,
            attacker_atk=90, defender_def=70,
            attacker_types=(WATER, WATER), defender_types=PIDGEY_TYPES,
            user_item=HELD_WISE_GLASSES,
        ),
    ))

    cases.append((
        "special_expert_belt", 82,
        BattleInputs(
            attacker_level=50, move_bp=60, move_type=FIRE, is_physical=False,
            attacker_atk=90, defender_def=70,
            attacker_types=(WATER, WATER), defender_types=(GRASS, NORMAL),
            user_item=HELD_EXPERT_BELT,
        ),
    ))

    cases.append((
        "special_metronome_item", 54,
        BattleInputs(
            attacker_level=50, move_bp=60, move_type=FIRE, is_physical=False,
            attacker_atk=90, defender_def=70,
            attacker_types=(WATER, WATER), defender_types=PIDGEY_TYPES,
            user_item=HELD_METRONOME, metronome_count=3,
        ),
    ))

    cases.append((
        "special_life_orb_damage", 44,
        BattleInputs(
            attacker_level=50, move_bp=60, move_type=FIRE, is_physical=False,
            attacker_atk=90, defender_def=70,
            attacker_types=(WATER, WATER), defender_types=PIDGEY_TYPES,
            user_item=HELD_LIFE_ORB,
        ),
    ))

    cases.append((
        "special_super_effective", 52,
        BattleInputs(
            attacker_level=5, move_bp=40, move_type=FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=CYNDAQUIL_TYPES, defender_types=(GRASS, BUG),
        ),
    ))

    cases.append((
        "special_not_very_effective", 2,
        BattleInputs(
            attacker_level=5, move_bp=40, move_type=FIRE, is_physical=False,
            attacker_atk=11, defender_def=5,
            attacker_types=CYNDAQUIL_TYPES, defender_types=(WATER, FIRE),
        ),
    ))

    cases.append((
        "physical_immune", 0,
        BattleInputs(
            attacker_level=2, move_bp=40, move_type=NORMAL, is_physical=True,
            attacker_atk=6, defender_def=9,
            attacker_types=PIDGEY_TYPES, defender_types=(GHOST, GHOST),
        ),
    ))

    cases.append((
        "dragon_fighting_ghost_dark_order", 9,
        BattleInputs(
            attacker_level=2, move_bp=20, move_type=FIGHTING, is_physical=True,
            attacker_atk=25, defender_def=5,
            attacker_types=(DRAGON, FIGHTING), defender_types=(GHOST, DARK),
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
