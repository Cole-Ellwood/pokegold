"""Multi-scenario clobber regression harness.

Runs damage-path scenarios and checks that wCurDamage matches an expected
range. The point isn't precision — it's catching CLOBBER-CLASS bugs (§3.13,
§3.14), which manifest as 5-10x damage spikes when a register carrying
defender def, move BP, or attacker atk gets overwritten mid-chain. The
c-clobber that shipped May 2026 turned wCurDamage from 4 into 16 — exactly
the kind of jump these range checks catch.

Usage:
    python -m tools.damage_debugger.clobber_smoke

Exit code: 0 if every scenario lands inside [expected_low, expected_high];
nonzero otherwise. On FAIL, the failing scenario's register snapshot at
each instrumented entry/exit (`ALGDS_far_entry`, `ALGDS_far_done`,
`Truncate_done`, etc.) is dumped to the log so the clobber's location can
be read off the trace instead of bisected.

Coverage today:
    physical_no_items          — no-op item branches (the clobber's path).
    physical_critical          — same chain + wCriticalHit=1.
    physical_choice_band       — Choice Band on attacker → atk * 3/2.
    physical_eviolite_def      — Eviolite on defender (can-evolve) → def * 3/2.
    special_no_items           — special branch through ALGDS.
    special_choice_specs       — Choice Specs on attacker → spatk * 3/2.
    special_assault_vest       — Assault Vest on defender → spdef * 3/2.
    special_eviolite_spd       — Eviolite on defender → spdef * 3/2.
    item damage multipliers    — TypeBoostItems, Muscle Band, Wise Glasses,
                                 Expert Belt, Metronome, Life Orb.
    type-effectiveness         — super-effective, resisted, immune rows.
    damage variation           — final 0.85-1.0 random multiplier range.
    late-gen after-hit effects — Rocky Helmet, Shell Bell, Life Orb HP effects.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .paths import find_rom, find_sym
from .safe_call import call_function_safe, read_be_u16_banked, write_byte_banked
from .symbols import Symbol, SymbolTable

LOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "audit"
    / "damage_debugger"
    / "clobber_smoke.log"
)


# Item IDs used by item-present scenarios. Item IDs live in
# constants/item_constants.asm and are listed in HEX in the comments
# (CHOICE_BAND ; 74 means 0x74, not decimal 74).
CHOICE_BAND_ID = 0x74
CHOICE_SPECS_ID = 0x81
ASSAULT_VEST_ID = 0x89
EVOLITE_ID = 0x93
LIFE_ORB_ID = 0x46
BLACKBELT_ID = 0x62
EXPERT_BELT_ID = 0x8D
MUSCLE_BAND_ID = 0x8E
WISE_GLASSES_ID = 0x91
SHELL_BELL_ID = 0x95
ROCKY_HELMET_ID = 0x99
METRONOME_ITEM_ID = 0x9A

NORMAL_TYPE = 0x00
BUG_TYPE = 0x07
FIGHTING_TYPE = 0x01
GHOST_TYPE = 0x08
FIRE_TYPE = 0x14
WATER_TYPE = 0x15
GRASS_TYPE = 0x16

WEATHER_RAIN = 1
WEATHER_SUN = 2
VOLCANOBADGE_MASK = 1 << 6

DEFAULT_CHAIN = (
    "BattleCommand_DamageStats",
    "BattleCommand_DamageCalc",
    "BattleCommand_Stab",
)

PostCheck = Callable[[object, dict], tuple[bool, str]]


@dataclass
class Scenario:
    name: str
    seed: Callable
    expected_low: int
    expected_high: int
    note: str = ""
    chain: tuple[str, ...] = DEFAULT_CHAIN
    post_check: PostCheck | None = None
    call_budget: int = 4800
    allow_nonreturn: bool = False
    # When True, an out-of-range damage is rendered as XFAIL (known-failure)
    # rather than FAIL, and does NOT influence the harness exit code. Use for
    # scenarios that surface a discovered-but-not-yet-fixed bug. Once the bug
    # ships a fix, drop the flag so an actual passing scenario is required.
    xfail: bool = False
    xfail_reason: str = ""


# Hooks fired during scenario execution; captured snapshots are emitted on
# FAIL so a clobber's location is obvious rather than bisected. These are
# the same key entry/exit points trace_chain.py uses for focused debugging.
HOOK_TARGETS: list[tuple[str, str]] = [
    ("BattleCommand_DamageStats", "DStats_entry"),
    ("EnemyAttackDamage", "EnemyAtkDmg_entry"),
    ("EnemyAttackDamage.done", "EnemyAtkDmg_done"),
    ("PlayerAttackDamage", "PlayerAtkDmg_entry"),
    ("PlayerAttackDamage.done", "PlayerAtkDmg_done"),
    ("ApplyLateGenDamageStatsItemMods", "ALGDS_thunk_entry"),
    ("ApplyLateGenDamageStatsItemMods_Far", "ALGDS_far_entry"),
    ("ApplyLateGenDamageStatsItemMods_Far.done", "ALGDS_far_done"),
    ("ApplyLateGenDamageStatsItemMods_Far.ApplyChoiceBandBoost", "ALGDS_choice_band"),
    ("ApplyLateGenDamageStatsItemMods_Far.ApplyChoiceSpecsBoost", "ALGDS_choice_specs"),
    ("ApplyLateGenDamageStatsItemMods_Far.ApplyAssaultVestBoostToDefense", "ALGDS_assault_vest"),
    ("ApplyLateGenDamageStatsItemMods_Far.ApplyEvioliteDefenseBoost", "ALGDS_eviolite_def"),
    ("ApplyLateGenDamageStatsItemMods_Far.ApplyEvioliteSpDefBoost", "ALGDS_eviolite_spd"),
    ("DittoMetalPowder_Far", "DMP_entry"),
    ("TypePassive_GetEffectiveMoveCategory_Far", "TPCat_entry"),
    ("TypePassive_GetEffectiveMoveCategory_Far.done", "TPCat_done"),
    ("TruncateHL_BC", "Truncate_entry"),
    ("TruncateHL_BC.done", "Truncate_done"),
    ("CheckDamageStatsCritical_Far", "CDSC_far_entry"),
    ("BattleCommand_Stab", "Stab_entry"),
    ("BattleCommand_Stab.end", "TypeMatchup_done"),
    ("BattleCommand_DamageVariation", "DVariation_entry"),
    ("BattleCommand_DamageVariation.loop", "DVariation_loop"),
    ("HandleLateGenAfterHitEffects_Far", "AfterHit_entry"),
    ("HandleLateGenAfterHitEffects_Far.MaybeApplyRockyHelmetRecoil", "AfterHit_rocky"),
    ("HandleLateGenAfterHitEffects_Far.MaybeApplyShellBellHeal", "AfterHit_shell"),
    ("HandleLateGenAfterHitEffects_Far.MaybeApplyLifeOrbRecoil", "AfterHit_life"),
    ("HandleLateGenAfterHitEffects_Far.done", "AfterHit_done"),
]


def parse_sym(p: Path) -> dict:
    return SymbolTable.load(p).as_legacy_dict()


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
        "wCurEnemyMove", "wCurPlayerMove", "wLinkMode",
        "wPlayerMetronomeCount", "wEnemyMetronomeCount",
        "wPlayerSubStatus1", "wPlayerSubStatus2", "wPlayerSubStatus3",
        "wPlayerSubStatus4", "wPlayerSubStatus5",
        "wEnemySubStatus1", "wEnemySubStatus2", "wEnemySubStatus3",
        "wEnemySubStatus4", "wEnemySubStatus5",
    ):
        write_byte(pyboy, byte_field, syms, 0)
    write_byte(pyboy, "wTypeMatchup", syms, 0x10)
    write_be_u16(pyboy, "wCurDamage", syms, 0)
    for stage in ("Atk", "Def", "Spd", "SAtk", "SDef"):
        write_byte(pyboy, f"wPlayer{stage}Level", syms, 7)
        write_byte(pyboy, f"wEnemy{stage}Level", syms, 7)


def _read_be_u16(pyboy, name, syms) -> int | None:
    s = syms.get(name)
    if s is None:
        return None
    return read_be_u16_banked(pyboy, s[1], s[0])


def _expect_u16s(expected: dict[str, int]) -> PostCheck:
    def check(pyboy, syms) -> tuple[bool, str]:
        mismatches: list[str] = []
        seen: list[str] = []
        for name, want in expected.items():
            got = _read_be_u16(pyboy, name, syms)
            seen.append(f"{name}={got}")
            if got != want:
                mismatches.append(f"{name}: expected {want}, got {got}")
        if mismatches:
            return False, "; ".join(mismatches)
        return True, ", ".join(seen)
    return check


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


def _seed_cyndaquil_attacks_pidgey_with_ember(pyboy, syms):
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


def seed_physical_no_items(pyboy, syms):
    _seed_pidgey_attacks_cyndaquil_with_tackle(pyboy, syms)


def seed_physical_critical(pyboy, syms):
    _seed_pidgey_attacks_cyndaquil_with_tackle(pyboy, syms)
    write_byte(pyboy, "wCriticalHit", syms, 1)


def seed_physical_choice_band(pyboy, syms):
    """Pidgey Tackle vs Cyndaquil with Choice Band on attacker → atk * 3/2."""
    _seed_pidgey_attacks_cyndaquil_with_tackle(pyboy, syms)
    # Attacker is Enemy (Pidgey); Choice Band hooks via _CheckUserItemEquals.
    write_byte(pyboy, "wEnemyMonItem", syms, CHOICE_BAND_ID)


def seed_physical_eviolite_def(pyboy, syms):
    """Pidgey Tackle vs Cyndaquil with Eviolite on defender → def * 3/2.

    Cyndaquil (155) evolves into Quilava → .SpeciesCanEvolve is true."""
    _seed_pidgey_attacks_cyndaquil_with_tackle(pyboy, syms)
    # Defender is Player (Cyndaquil); Eviolite hooks via _CheckOpponentItemEquals.
    write_byte(pyboy, "wBattleMonItem", syms, EVOLITE_ID)


def seed_special_no_items(pyboy, syms):
    """Cyndaquil lvl 5 attacks Pidgey lvl 2 with Ember (FIRE special, BP 40)."""
    _seed_cyndaquil_attacks_pidgey_with_ember(pyboy, syms)


def seed_special_choice_specs(pyboy, syms):
    """Cyndaquil Ember vs Pidgey with Choice Specs on attacker → spatk * 3/2."""
    _seed_cyndaquil_attacks_pidgey_with_ember(pyboy, syms)
    write_byte(pyboy, "wBattleMonItem", syms, CHOICE_SPECS_ID)


def seed_special_assault_vest(pyboy, syms):
    """Cyndaquil Ember vs Pidgey with Assault Vest on defender → spdef * 3/2."""
    _seed_cyndaquil_attacks_pidgey_with_ember(pyboy, syms)
    write_byte(pyboy, "wEnemyMonItem", syms, ASSAULT_VEST_ID)


def seed_special_eviolite_spd(pyboy, syms):
    """Cyndaquil Ember vs Pidgey with Eviolite on defender → spdef * 3/2.

    Pidgey (16) evolves into Pidgeotto → .SpeciesCanEvolve is true."""
    _seed_cyndaquil_attacks_pidgey_with_ember(pyboy, syms)
    write_byte(pyboy, "wEnemyMonItem", syms, EVOLITE_ID)


def seed_special_sun_fire(pyboy, syms):
    """Cyndaquil Ember vs Pidgey under sun -> weather 1.5x before STAB."""
    _seed_cyndaquil_attacks_pidgey_with_ember(pyboy, syms)
    write_byte(pyboy, "wBattleWeather", syms, WEATHER_SUN)


def seed_special_rain_fire(pyboy, syms):
    """Cyndaquil Ember vs Pidgey under rain -> weather 0.5x before STAB."""
    _seed_cyndaquil_attacks_pidgey_with_ember(pyboy, syms)
    write_byte(pyboy, "wBattleWeather", syms, WEATHER_RAIN)


def seed_special_fire_badge(pyboy, syms):
    """Cyndaquil Ember vs Pidgey with VolcanoBadge -> damage + damage/8 before STAB."""
    _seed_cyndaquil_attacks_pidgey_with_ember(pyboy, syms)
    write_byte(pyboy, "wKantoBadges", syms, VOLCANOBADGE_MASK)


def seed_special_fire_low_hp(pyboy, syms):
    """Full-FIRE attacker below one-third HP -> Fire passive boosts damage 6/5."""
    _seed_cyndaquil_attacks_pidgey_with_ember(pyboy, syms)
    write_be_u16(pyboy, "wBattleMonHP", syms, 1)
    write_be_u16(pyboy, "wBattleMonMaxHP", syms, 10)


def _seed_player_item_multiplier_case(
    pyboy,
    syms,
    *,
    item_id: int,
    move_type: int,
    is_physical: bool,
    defender_type1: int = NORMAL_TYPE,
    defender_type2: int = NORMAL_TYPE,
    metronome_count: int = 0,
):
    """Player-side level-50 neutral seed for DamageCalc item multipliers."""
    _seed_cyndaquil_lvl5(pyboy, syms, slot="Battle")
    _seed_pidgey_lvl2(pyboy, syms, slot="Enemy")
    _zero_meta(pyboy, syms)

    write_byte(pyboy, "wBattleMonLevel", syms, 50)
    write_byte(pyboy, "wBattleMonType1", syms, WATER_TYPE)
    write_byte(pyboy, "wBattleMonType2", syms, WATER_TYPE)
    write_byte(pyboy, "wBattleMonItem", syms, item_id)
    write_byte(pyboy, "wEnemyMonType1", syms, defender_type1)
    write_byte(pyboy, "wEnemyMonType2", syms, defender_type2)
    write_byte(pyboy, "wPlayerMetronomeCount", syms, metronome_count)

    if is_physical:
        write_be_u16(pyboy, "wBattleMonAttack", syms, 90)
        write_be_u16(pyboy, "wPlayerAttack", syms, 90)
        write_be_u16(pyboy, "wEnemyMonDefense", syms, 70)
        write_be_u16(pyboy, "wEnemyDefense", syms, 70)
    else:
        write_be_u16(pyboy, "wBattleMonSpclAtk", syms, 90)
        write_be_u16(pyboy, "wPlayerSpAtk", syms, 90)
        write_be_u16(pyboy, "wEnemyMonSpclDef", syms, 70)
        write_be_u16(pyboy, "wEnemySpDef", syms, 70)

    pm = syms["wPlayerMoveStruct"]
    for offset, val in [(0, 0x21), (1, 0x00), (2, 60), (3, move_type), (4, 0xFF), (5, 25), (6, 0)]:
        write_byte_banked(pyboy, pm[1] + offset, val, pm[0])
    write_byte(pyboy, "wCurPlayerMove", syms, 0x21)
    write_byte(pyboy, "hBattleTurn", syms, 0)


def seed_physical_type_boost_item(pyboy, syms):
    """Black Belt on a neutral FIGHTING move -> quotient * 120/100."""
    _seed_player_item_multiplier_case(
        pyboy, syms, item_id=BLACKBELT_ID, move_type=FIGHTING_TYPE,
        is_physical=True, defender_type1=FIRE_TYPE, defender_type2=WATER_TYPE,
    )


def seed_physical_muscle_band(pyboy, syms):
    """Muscle Band on a neutral physical move -> quotient * 11/10."""
    _seed_player_item_multiplier_case(
        pyboy, syms, item_id=MUSCLE_BAND_ID, move_type=FIGHTING_TYPE,
        is_physical=True, defender_type1=FIRE_TYPE, defender_type2=WATER_TYPE,
    )


def seed_special_wise_glasses(pyboy, syms):
    """Wise Glasses on a neutral special move -> quotient * 11/10."""
    _seed_player_item_multiplier_case(
        pyboy, syms, item_id=WISE_GLASSES_ID, move_type=FIRE_TYPE, is_physical=False,
    )


def seed_special_expert_belt(pyboy, syms):
    """Expert Belt on a super-effective special move -> quotient * 6/5."""
    _seed_player_item_multiplier_case(
        pyboy, syms, item_id=EXPERT_BELT_ID, move_type=FIRE_TYPE,
        is_physical=False, defender_type1=GRASS_TYPE, defender_type2=NORMAL_TYPE,
    )


def seed_special_metronome_item(pyboy, syms):
    """Metronome item count 3 -> quotient * 16/10."""
    _seed_player_item_multiplier_case(
        pyboy, syms, item_id=METRONOME_ITEM_ID, move_type=FIRE_TYPE,
        is_physical=False, metronome_count=3,
    )


def seed_special_life_orb_damage(pyboy, syms):
    """Life Orb on the main damage chain -> quotient * 13/10."""
    _seed_player_item_multiplier_case(
        pyboy, syms, item_id=LIFE_ORB_ID, move_type=FIRE_TYPE, is_physical=False,
    )


def seed_special_super_effective(pyboy, syms):
    """Cyndaquil Ember vs a GRASS/BUG defender -> two FIRE super-effective rows."""
    _seed_cyndaquil_attacks_pidgey_with_ember(pyboy, syms)
    write_byte(pyboy, "wEnemyMonType1", syms, GRASS_TYPE)
    write_byte(pyboy, "wEnemyMonType2", syms, BUG_TYPE)


def seed_special_not_very_effective(pyboy, syms):
    """Cyndaquil Ember vs a WATER/FIRE defender -> two resisted FIRE rows."""
    _seed_cyndaquil_attacks_pidgey_with_ember(pyboy, syms)
    write_byte(pyboy, "wEnemyMonType1", syms, WATER_TYPE)
    write_byte(pyboy, "wEnemyMonType2", syms, FIRE_TYPE)


def seed_physical_immune(pyboy, syms):
    """Pidgey Tackle vs a GHOST/GHOST defender -> NORMAL immunity zeros damage."""
    _seed_pidgey_attacks_cyndaquil_with_tackle(pyboy, syms)
    write_byte(pyboy, "wBattleMonType1", syms, GHOST_TYPE)
    write_byte(pyboy, "wBattleMonType2", syms, GHOST_TYPE)


def _seed_player_tackle_afterhit_base(pyboy, syms, *, cur_damage: int = 16):
    """Player-side contact hit state for isolated after-hit effect checks."""
    _seed_cyndaquil_attacks_pidgey_with_ember(pyboy, syms)
    pm = syms["wPlayerMoveStruct"]
    # Tackle is a contact move; the handler checks the move id through
    # BATTLE_VARS_MOVE_ANIM, not the attacker's type.
    for offset, val in [(0, 0x21), (1, 0x00), (2, 40), (3, NORMAL_TYPE), (4, 0xFF), (5, 35), (6, 0)]:
        write_byte_banked(pyboy, pm[1] + offset, val, pm[0])
    write_byte(pyboy, "wCurPlayerMove", syms, 0x21)
    write_byte(pyboy, "hBattleTurn", syms, 0)
    write_be_u16(pyboy, "wCurDamage", syms, cur_damage)
    write_be_u16(pyboy, "wBattleMonHP", syms, 30)
    write_be_u16(pyboy, "wBattleMonMaxHP", syms, 30)
    write_be_u16(pyboy, "wEnemyMonHP", syms, 30)
    write_be_u16(pyboy, "wEnemyMonMaxHP", syms, 30)


def seed_afterhit_rocky_helmet(pyboy, syms):
    """Opponent Rocky Helmet recoils the player by maxHP/6 after contact."""
    _seed_player_tackle_afterhit_base(pyboy, syms)
    write_byte(pyboy, "wEnemyMonItem", syms, ROCKY_HELMET_ID)


def seed_afterhit_shell_bell(pyboy, syms):
    """Player Shell Bell heals max(1, wCurDamage/8) after a damaging hit."""
    _seed_player_tackle_afterhit_base(pyboy, syms)
    write_be_u16(pyboy, "wBattleMonHP", syms, 10)
    write_byte(pyboy, "wBattleMonItem", syms, SHELL_BELL_ID)


def seed_afterhit_life_orb(pyboy, syms):
    """Player Life Orb recoils the user by maxHP/10 after a damaging hit."""
    _seed_player_tackle_afterhit_base(pyboy, syms)
    write_byte(pyboy, "wBattleMonItem", syms, LIFE_ORB_ID)


# Ranges are loose enough to absorb DamageVariation-free integer noise but
# tight enough that a 4-10x clobber-class regression always trips them.
#
# Note on physical_choice_band: at lvl 2 vs lvl 5 the Gen 2 damage formula's
# integer floor masks the +50% atk boost (atk=6 vs atk=9 both round to dmg
# 4 post-STAB). The range stays tight (3-7) so a clobber escalating into
# the ~16-24 zone still trips. Special-side scenarios use bigger stats and
# show the boost explicitly.
#
# Note on the two Eviolite-on-evolvable scenarios: discovered as XFAIL when
# this expansion landed -- `.SpeciesCanEvolve` clobbered `bc` and `hl`
# without push/pop, propagating ~3x and ~25x damage spikes through
# TruncateHL_BC. Fixed by push/pop bc/hl at the call site (engine/battle/
# late_gen_held_items.asm:81 and :92), same shape as the AG-08 c-clobber
# fix (sec 3.14).
SCENARIOS = [
    Scenario(
        "physical_no_items", seed_physical_no_items, 3, 5,
        "Pidgey Tackle vs Cyndaquil. The exact path the c-clobber bug shipped on.",
    ),
    Scenario(
        "physical_critical", seed_physical_critical, 5, 8,
        "Same + wCriticalHit=1 -> pre-Stab quotient * 2.",
    ),
    Scenario(
        "physical_choice_band", seed_physical_choice_band, 3, 7,
        "Choice Band on attacker -> atk * 3/2 (formula floor masks visible delta at this level).",
    ),
    Scenario(
        "physical_eviolite_def", seed_physical_eviolite_def, 2, 5,
        "Eviolite on defender (Cyndaquil can evolve) -> def * 3/2 -> ~3.",
    ),
    Scenario(
        "special_no_items", seed_special_no_items, 11, 16,
        "Cyndaquil Ember vs Pidgey. Routes through ALGDS Special branch.",
    ),
    Scenario(
        "special_choice_specs", seed_special_choice_specs, 16, 24,
        "Choice Specs on attacker -> spatk * 3/2 -> ~19.",
    ),
    Scenario(
        "special_assault_vest", seed_special_assault_vest, 6, 12,
        "Assault Vest on defender -> spdef * 3/2 -> ~9.",
    ),
    Scenario(
        "special_eviolite_spd", seed_special_eviolite_spd, 6, 12,
        "Eviolite on defender (Pidgey can evolve) -> spdef * 3/2 -> ~9.",
    ),
    Scenario(
        "special_sun_fire", seed_special_sun_fire, 17, 22,
        "Sun boosts FIRE damage 1.5x before STAB.",
    ),
    Scenario(
        "special_rain_fire", seed_special_rain_fire, 5, 8,
        "Rain halves FIRE damage before STAB.",
    ),
    Scenario(
        "special_fire_badge", seed_special_fire_badge, 13, 17,
        "VolcanoBadge adds damage/8 before STAB on player FIRE move.",
    ),
    Scenario(
        "special_fire_low_hp", seed_special_fire_low_hp, 15, 15,
        "Full-FIRE attacker below one-third HP gets the type-passive 6/5 damage boost.",
    ),
    Scenario(
        "physical_type_boost_item", seed_physical_type_boost_item, 40, 42,
        "Black Belt boosts matching FIGHTING damage quotient by 120/100.",
    ),
    Scenario(
        "physical_muscle_band", seed_physical_muscle_band, 37, 39,
        "Muscle Band boosts physical damage quotient by 11/10.",
    ),
    Scenario(
        "special_wise_glasses", seed_special_wise_glasses, 37, 39,
        "Wise Glasses boosts special damage quotient by 11/10.",
    ),
    Scenario(
        "special_expert_belt", seed_special_expert_belt, 81, 83,
        "Expert Belt boosts super-effective damage quotient by 6/5 before matchup.",
    ),
    Scenario(
        "special_metronome_item", seed_special_metronome_item, 53, 55,
        "Metronome item count 3 boosts damage quotient by 16/10.",
    ),
    Scenario(
        "special_life_orb_damage", seed_special_life_orb_damage, 43, 45,
        "Life Orb boosts main damage quotient by 13/10.",
    ),
    Scenario(
        "special_super_effective", seed_special_super_effective, 50, 54,
        "FIRE vs GRASS/BUG runs two super-effective type rows -> 52.",
    ),
    Scenario(
        "special_not_very_effective", seed_special_not_very_effective, 1, 3,
        "FIRE vs WATER/FIRE runs two resisted type rows plus WATER special resist -> 2.",
    ),
    Scenario(
        "physical_immune", seed_physical_immune, 0, 0,
        "NORMAL Tackle into GHOST/GHOST must zero wCurDamage.",
    ),
    Scenario(
        "special_super_effective_variation", seed_special_super_effective, 44, 52,
        "Same super-effective FIRE case after DamageVariation; final RNG multiplier stays 0.85-1.0.",
        chain=DEFAULT_CHAIN + ("BattleCommand_DamageVariation",),
    ),
    Scenario(
        "afterhit_rocky_helmet", seed_afterhit_rocky_helmet, 16, 16,
        "Isolated after-hit handler: contact into Rocky Helmet subtracts player maxHP/6.",
        chain=("HandleLateGenAfterHitEffects_Far",),
        post_check=_expect_u16s({"wBattleMonHP": 25, "wEnemyMonHP": 30}),
        call_budget=500,
        allow_nonreturn=True,
    ),
    Scenario(
        "afterhit_shell_bell", seed_afterhit_shell_bell, 16, 16,
        "Isolated after-hit handler: Shell Bell heals player by wCurDamage/8.",
        chain=("HandleLateGenAfterHitEffects_Far",),
        post_check=_expect_u16s({"wBattleMonHP": 12, "wEnemyMonHP": 30}),
        call_budget=500,
        allow_nonreturn=True,
    ),
    Scenario(
        "afterhit_life_orb", seed_afterhit_life_orb, 16, 16,
        "Isolated after-hit handler: Life Orb subtracts player maxHP/10.",
        chain=("HandleLateGenAfterHitEffects_Far",),
        post_check=_expect_u16s({"wBattleMonHP": 27, "wEnemyMonHP": 30}),
        call_budget=500,
        allow_nonreturn=True,
    ),
]


@dataclass
class HookSnapshot:
    label: str
    seq: int
    bank: int
    pc: int
    a: int
    f: int
    b: int
    c: int
    d: int
    e: int
    h: int
    l: int
    sp: int


def _install_hooks(pyboy, syms: dict, snapshots: list[HookSnapshot]) -> list[tuple[int, int]]:
    """Install entry/exit hooks at the targets in HOOK_TARGETS that exist in
    the sym table. Returns the (bank, addr) pairs that were registered, so
    the caller can deregister them when the scenario finishes (the shared-
    PyBoy boot-cache pattern needs hooks scoped to the scenario)."""
    installed: list[tuple[int, int]] = []
    seq_counter = [0]

    def _make_cb(label: str, bank: int):
        def cb(_):
            rf = pyboy.register_file
            seq_counter[0] += 1
            snapshots.append(HookSnapshot(
                label=label,
                seq=seq_counter[0],
                bank=bank,
                pc=int(rf.PC),
                a=int(rf.A), f=int(rf.F),
                b=int(rf.B), c=int(rf.C),
                d=int(rf.D), e=int(rf.E),
                h=int(rf.H) if hasattr(rf, "H") else (int(rf.HL) >> 8) & 0xFF,
                l=int(rf.L) if hasattr(rf, "L") else int(rf.HL) & 0xFF,
                sp=int(rf.SP),
            ))
        return cb

    for sym_name, label in HOOK_TARGETS:
        s = syms.get(sym_name)
        if s is None:
            continue
        pyboy.hook_register(s[0], s[1], _make_cb(label, s[0]), None)
        installed.append((s[0], s[1]))
    return installed


def _deregister_hooks(pyboy, hooks: list[tuple[int, int]]) -> None:
    for bank, addr in hooks:
        try:
            pyboy.hook_deregister(bank, addr)
        except Exception:
            # PyBoy's hook table is a flat dict per (bank, addr); if a
            # deregister fails because it was already cleared (unlikely
            # given paired register/deregister), swallow rather than
            # cascade -- the next scenario re-registers regardless.
            pass


def _read_byte(pyboy, name, syms):
    s = syms.get(name)
    if s is None:
        return None
    addr, bank = s[1], s[0]
    if 0xD000 <= addr <= 0xDFFF and bank:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = bank
        try:
            return int(pyboy.memory[addr])
        finally:
            pyboy.memory[0xFF70] = old
    return int(pyboy.memory[addr])


def run_scenario(
    scenario: Scenario,
    syms: dict,
    cache: BootStateCache,
) -> tuple[int, list[HookSnapshot], dict, list[str]]:
    """Run one scenario against the cache's shared PyBoy.

    `cache.restore(pyboy)` rewinds to the post-boot snapshot in ~10ms
    instead of booting + ticking 240 frames per scenario (~1s). Hooks
    are scoped to this scenario only -- registered now, deregistered
    after the damage read so the next scenario starts hook-clean.
    """
    pyboy = cache.restore()

    snapshots: list[HookSnapshot] = []
    hooks = _install_hooks(pyboy, syms, snapshots)

    try:
        scenario.seed(pyboy, syms)

        # Capture seed-state for diagnostics: post-seed byte values that
        # determine which item branches fire. Rendered only on FAIL.
        seed_state = {
            "wBattleMonItem": _read_byte(pyboy, "wBattleMonItem", syms),
            "wEnemyMonItem": _read_byte(pyboy, "wEnemyMonItem", syms),
            "wBattleMonSpecies": _read_byte(pyboy, "wBattleMonSpecies", syms),
            "wEnemyMonSpecies": _read_byte(pyboy, "wEnemyMonSpecies", syms),
            "hBattleTurn": _read_byte(pyboy, "hBattleTurn", syms),
            "wCriticalHit": _read_byte(pyboy, "wCriticalHit", syms),
        }

        check_failures: list[str] = []
        cd_sym = syms["wCurDamage"]
        for fn in scenario.chain:
            ticks, returned, post_pc = call_function_safe(pyboy, syms, fn, budget=scenario.call_budget)
            if not returned:
                seed_state[f"{fn}.post_pc"] = f"${post_pc:04x}"
                if not scenario.allow_nonreturn:
                    check_failures.append(
                        f"{fn} did not reach the HRAM sentinel within {ticks} ticks"
                    )

        damage = read_be_u16_banked(pyboy, cd_sym[1], cd_sym[0])
        if scenario.post_check is not None:
            ok, detail = scenario.post_check(pyboy, syms)
            seed_state["post_check"] = detail
            if not ok:
                check_failures.append(detail)
    finally:
        _deregister_hooks(pyboy, hooks)
    return damage, snapshots, seed_state, check_failures


def _format_snapshot(s: HookSnapshot, symbols: SymbolTable | None = None) -> str:
    pc = f"${s.bank:02x}:{s.pc:04x}"
    if symbols is not None:
        pc = f"{pc} ({symbols.render(s.bank, s.pc)})"
    return (
        f"  #{s.seq:3d} {s.label:24s} PC={pc} "
        f"A={s.a:02x} F={s.f:02x} "
        f"BC={s.b:02x}{s.c:02x} DE={s.d:02x}{s.e:02x} "
        f"HL={s.h:02x}{s.l:02x} SP=${s.sp:04x}"
    )


def _format_bc(s: HookSnapshot) -> str:
    return f"{s.b:02x}{s.c:02x}"


def _diagnose_clobber_footprints(snapshots: list[HookSnapshot]) -> list[str]:
    """Turn hook snapshots into fix-region hints for known clobber footprints."""
    diagnoses: list[str] = []

    for i, snap in enumerate(snapshots):
        if snap.label != "ALGDS_far_entry":
            continue
        entry = snap
        tpcat_done_index = None
        for j in range(i + 1, len(snapshots)):
            candidate = snapshots[j]
            if candidate.label == "TPCat_done":
                tpcat_done_index = j
                continue
            if candidate.label in {"ALGDS_far_done", "DMP_entry", "Truncate_entry", "Stab_entry"}:
                break
            if tpcat_done_index is None:
                continue
            if not candidate.label.startswith("ALGDS_"):
                continue
            if candidate.c == entry.c:
                break
            diagnoses.append(
                "Likely AG-08 c-mirror clobber: "
                f"ApplyLateGenDamageStatsItemMods_Far entered with BC={_format_bc(entry)} "
                f"(load-bearing C={entry.c:02x}) but resumed at {candidate.label} "
                f"after TypePassive_GetEffectiveMoveCategory_Far with BC={_format_bc(candidate)}. "
                "Fix region: engine/battle/late_gen_held_items.asm; preserve bc around "
                "the in-bank TypePassive_GetEffectiveMoveCategory_Far calls in "
                "ApplyLateGenDamageStatsItemMods_Far and DittoMetalPowder_Far before "
                "the value reaches TruncateHL_BC."
            )
            break
        if diagnoses:
            break

    return diagnoses


def _self_test() -> int:
    table = SymbolTable([
        Symbol(bank=1, address=0x4000, name="Fixture"),
        Symbol(bank=1, address=0x4002, name="Fixture.next"),
    ])
    legacy = table.as_legacy_dict()
    assert legacy["Fixture"] == (1, 0x4000)
    snap = HookSnapshot(
        label="FixtureHook",
        seq=1,
        bank=1,
        pc=0x4003,
        a=1,
        f=0,
        b=2,
        c=3,
        d=4,
        e=5,
        h=0xC0,
        l=0xAF,
        sp=0xDFFE,
    )
    rendered = _format_snapshot(snap, symbols=table)
    assert "Fixture.next+0x1" in rendered
    assert "PC=$01:4003" in rendered

    diagnosis = _diagnose_clobber_footprints([
        HookSnapshot(
            label="ALGDS_far_entry",
            seq=1,
            bank=0x11,
            pc=0x4AE1,
            a=0,
            f=0,
            b=0,
            c=9,
            d=0,
            e=0,
            h=0,
            l=0,
            sp=0xDFDF,
        ),
        HookSnapshot(
            label="TPCat_done",
            seq=2,
            bank=0x11,
            pc=0x52A8,
            a=0x21,
            f=0,
            b=0,
            c=9,
            d=0,
            e=0,
            h=0,
            l=0,
            sp=0xDFD3,
        ),
        HookSnapshot(
            label="ALGDS_choice_band",
            seq=3,
            bank=0x11,
            pc=0x4AFE,
            a=0,
            f=0,
            b=0,
            c=0,
            d=0,
            e=0,
            h=0,
            l=0,
            sp=0xDFD9,
        ),
    ])
    assert len(diagnosis) == 1
    assert "engine/battle/late_gen_held_items.asm" in diagnosis[0]
    assert "ApplyLateGenDamageStatsItemMods_Far" in diagnosis[0]
    assert "DittoMetalPowder_Far" in diagnosis[0]

    no_diagnosis = _diagnose_clobber_footprints([
        HookSnapshot("ALGDS_far_entry", 1, 0x11, 0x4AE1, 0, 0, 0, 9, 0, 0, 0, 0, 0),
        HookSnapshot("TPCat_done", 2, 0x11, 0x52A8, 0, 0, 0, 9, 0, 0, 0, 0, 0),
        HookSnapshot("ALGDS_choice_band", 3, 0x11, 0x4AFE, 0, 0, 0, 9, 0, 0, 0, 0, 0),
    ])
    assert no_diagnosis == []

    print("clobber_smoke self-test: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv == ["--self-test"]:
        return _self_test()
    if argv:
        print("usage: python -m tools.damage_debugger.clobber_smoke [--self-test]", file=sys.stderr)
        return 2

    # Windows native Python defaults stdout to cp1252; any non-ASCII glyph in
    # a Scenario.note (em-dash, arrow, section symbol) crashes mid-print and
    # leaves a partial log. Force UTF-8 so future scenario authors don't have
    # to police their notes character-by-character.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(LOG_PATH, "w", encoding="utf-8", buffering=1)

    def log(msg: str = ""):
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()
        fh.write(msg + "\n")
        fh.flush()

    # find_rom/find_sym walk up from this file to find the ROM/sym pair --
    # works inside .claude/worktrees/* and at the project root. If a worktree
    # never built its own pokegold_debug.gbc, the search silently falls back
    # to an ancestor (the main repo). Printing the absolute path makes that
    # fallback visible -- otherwise a stale upstream ROM looks like a real
    # regression. Saw this in the 2026-05-05 harness bug-check pass.
    rom = find_rom("pokegold_debug")
    sym = find_sym("pokegold_debug")
    symbol_table = SymbolTable.load(sym)
    syms = symbol_table.as_legacy_dict()

    name_width = max(26, *(len(sc.name) for sc in SCENARIOS))
    log(f"clobber_smoke: running {len(SCENARIOS)} scenarios against {rom}")
    log(f"{'scenario':<{name_width}s} {'damage':>7s} {'expected':>10s}  result  notes")
    log("-" * 110)

    # Boot ONE PyBoy, snapshot it, then load_state per scenario instead of
    # constructing a new emulator each time. Drops 8-scenario wall-clock
    # from ~10s to ~1s and unblocks the Hypothesis fuzz workload (Tier 2.2)
    # which needs hundreds of restores per second.
    from .boot_cache import BootStateCache

    cache = BootStateCache(rom)
    cache.prime()

    failures: list[tuple[Scenario, int, list[HookSnapshot], dict, list[str]]] = []
    xfailures: list[tuple[Scenario, int, list[HookSnapshot], dict, list[str]]] = []
    xpasses: list[tuple[Scenario, int]] = []
    try:
        for sc in SCENARIOS:
            damage, snapshots, seed_state, check_failures = run_scenario(sc, syms, cache)
            ok = sc.expected_low <= damage <= sc.expected_high and not check_failures
            if ok and sc.xfail:
                result = "XPASS"
                xpasses.append((sc, damage))
            elif ok:
                result = "PASS"
            elif sc.xfail:
                result = "XFAIL"
                xfailures.append((sc, damage, snapshots, seed_state, check_failures))
            else:
                result = "FAIL"
                failures.append((sc, damage, snapshots, seed_state, check_failures))
            log(
                f"{sc.name:<{name_width}s} {damage:>7d} "
                f"{f'{sc.expected_low}-{sc.expected_high}':>10s}  {result:>5s}  {sc.note}"
            )
    finally:
        cache.stop()

    log()

    # XPASS = scenario tagged xfail but actually passing. The bug got fixed
    # and the tag is stale.
    if xpasses:
        log(f"XPASS: {len(xpasses)} scenario(s) tagged xfail are now passing.")
        log("       Drop the xfail flag in SCENARIOS so a real regression would FAIL.")
        for sc, damage in xpasses:
            log(f"  - {sc.name} (damage={damage}, range {sc.expected_low}-{sc.expected_high})")
            if sc.xfail_reason:
                log(f"      tagged because: {sc.xfail_reason}")
        log()

    if xfailures:
        log(f"XFAIL: {len(xfailures)} scenario(s) failed as expected (known bug).")
        for sc, damage, _snaps, _seed, check_failures in xfailures:
            log(f"  - {sc.name}: damage={damage} (expected {sc.expected_low}-{sc.expected_high})")
            log(f"      reason: {sc.xfail_reason}")
            for failure in check_failures:
                log(f"      self-check: {failure}")
        log()

    if failures:
        log(f"FAIL: {len(failures)} scenario(s) produced unexpected damage.")
        log("      A clobber-class regression likely escaped function-level audits.")
        log("      See docs/asm_authoring_guide.md sec 3.14 for the recurrence pattern.")
        log()
        _emit_diagnostic_traces(failures, log, prefix="FAIL", symbols=symbol_table)
        return 1

    if xfailures:
        # All non-xfail scenarios passed; emit traces for the xfail ones so the
        # user has the diagnostic handy when picking up the underlying fix.
        _emit_diagnostic_traces(xfailures, log, prefix="XFAIL", symbols=symbol_table)
        non_xfail = len(SCENARIOS) - len(xfailures)
        log(f"PASS: all {non_xfail} non-xfail scenarios within expected ranges.")
        log(f"      ({len(xfailures)} xfail above remain known-bug; not blocking.)")
    else:
        log(f"PASS: all {len(SCENARIOS)} scenarios within expected damage ranges.")
        log("      No clobber-class regression detected on the covered paths.")
    return 0


def _emit_diagnostic_traces(
    items,
    log,
    *,
    prefix: str,
    symbols: SymbolTable | None = None,
) -> None:
    for sc, damage, snapshots, seed_state, check_failures in items:
        log(f"=== diagnostic trace for {prefix} scenario: {sc.name} (damage={damage}) ===")
        log(f"    expected {sc.expected_low}-{sc.expected_high}; {sc.note}")
        log(f"    seed: " + ", ".join(
            f"{k}={v}" for k, v in seed_state.items() if v is not None
        ))
        if check_failures:
            log("    debugger self-check failures:")
            for failure in check_failures:
                log(f"      - {failure}")
        if not snapshots:
            log("    (no hook snapshots -- symbols missing from sym table)")
            continue
        diagnoses = _diagnose_clobber_footprints(snapshots)
        if diagnoses:
            log("    likely clobber diagnosis:")
            for diagnosis in diagnoses:
                log(f"      - {diagnosis}")
        log(f"    {len(snapshots)} hook hits along the chain:")
        for snap in snapshots:
            log(_format_snapshot(snap, symbols=symbols))
        log()
    log("Reading the trace:")
    log("  - DStats_entry            : caller hands off bc/de/hl into the chain")
    log("  - ALGDS_far_entry/.done   : item-mod chain enter/exit (bc/de must round-trip)")
    log("  - TPCat_entry/.done       : the AG-08 c-mirror site")
    log("  - Truncate_entry/.done    : if c flips between ALGDS_far_done and Truncate_done,")
    log("                              that's the sec 3.14 c-clobber footprint")
    log("  - TypeMatchup_done        : post-type-effectiveness boundary inside Stab")
    log("  - DVariation_*            : final 0.85-1.0 random multiplier path")
    log("  - AfterHit_*              : Rocky Helmet / Shell Bell / Life Orb side effects")
    log("  - EnemyAtkDmg_done        : final c value just before ConfusionDamageCalc")
    log()


if __name__ == "__main__":
    sys.exit(main())
