#!/usr/bin/env python3
"""Audit post-patch Boss AI behavior invariants."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOSS = ROOT / "engine" / "battle" / "ai" / "boss.asm"
WRAM = ROOT / "ram" / "wram.asm"
PARTIES = ROOT / "data" / "trainers" / "parties.asm"
AI_TIERS = ROOT / "data" / "trainers" / "ai_tiers.asm"
CONSTANTS = ROOT / "constants" / "battle_constants.asm"
CORE = ROOT / "engine" / "battle" / "core.asm"

TOP_LABEL_RE = re.compile(r"^[A-Za-z0-9_]+:{1,2}\s*(?:;.*)?$")
ADD_RE = re.compile(r"\badd\s+(\d+)\b")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def strip_comment(line: str) -> str:
    if ";" in line:
        return line.split(";", 1)[0]
    return line


def load(path: Path) -> str:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8", errors="replace")


def code_lines(text: str) -> list[str]:
    return [strip_comment(line).rstrip() for line in text.splitlines()]


def top_block(text: str, label: str) -> str:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() in {f"{label}:", f"{label}::"}:
            start = i
            break
    if start is None:
        fail(f"missing label: {label}")

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if TOP_LABEL_RE.match(strip_comment(lines[i]).strip()):
            end = i
            break
    return "\n".join(lines[start:end])


def local_block(text: str, label: str, end_label: str) -> str:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        stripped = strip_comment(line).strip()
        if stripped in {label, f"{label}:"}:
            start = i
            break
    if start is None:
        fail(f"missing local label: {label}")

    end = None
    for i in range(start + 1, len(lines)):
        stripped = strip_comment(lines[i]).strip()
        if stripped in {end_label, f"{end_label}:"}:
            end = i
            break
    if end is None:
        fail(f"missing local block end {end_label} after {label}")
    return "\n".join(lines[start:end])


def require_contains(block: str, needle: str, context: str) -> None:
    if needle not in block:
        fail(f"{context}: missing `{needle}`")


def require_order(block: str, needles: list[str], context: str) -> None:
    pos = -1
    for needle in needles:
        nxt = block.find(needle, pos + 1)
        if nxt < 0:
            fail(f"{context}: missing `{needle}` in required order")
        pos = nxt


def first_add_value(block: str, context: str) -> int:
    match = ADD_RE.search(block)
    if not match:
        fail(f"{context}: missing add immediate")
    return int(match.group(1))


def audit_revealed_coverage(boss: str, wram: str) -> None:
    record = top_block(boss, "BossAI_RecordRevealedPlayerMove")
    require_order(
        record,
        [
            "call BossAI_GetActiveSpeciesRevealedMaskPointer",
            "call BossAI_AddRevealedMoveToSpeciesMask",
        ],
        "record revealed move path",
    )

    has_revealed = top_block(boss, "BossAI_HasRevealedSuperEffectiveMove")
    require_order(
        has_revealed,
        [
            "call BossAI_GetActiveSpeciesRevealedMaskPointer",
            "call BossAI_TestRevealedSpeciesMaskBit",
        ],
        "revealed super-effective read path",
    )

    add_revealed = top_block(boss, "BossAI_AddRevealedDamagingTypesToMask")
    require_order(
        add_revealed,
        [
            "call BossAI_GetActiveSpeciesRevealedMaskPointer",
            "ld de, wBossAIPlausibleTypeMaskCache",
            "ld b, 4",
            "or [hl]",
            "ld de, wBossAILikelyTypeMaskCache",
            "ld b, 4",
            "or [hl]",
        ],
        "revealed damaging type mask copy",
    )

    compute_plausible = top_block(boss, "BossAI_ComputePlayerPlausibleTypeMask")
    require_order(
        compute_plausible,
        [
            "call BossAI_ClearPlausibleMask",
            "call BossAI_AddPublicSTABThreatsToMask",
            "call BossAI_AddRevealedDamagingTypesToMask",
            "call BossAI_AddSpeciesAndPreEvolutionMovesToMask",
        ],
        "public threat mask source ordering",
    )

    stab = top_block(boss, "BossAI_AddPublicSTABThreatsToMask")
    require_contains(
        stab,
        "call BossAI_SetPlausibleAndLikelyMaskBit",
        "STAB likely/plausible threat source",
    )

    compute_risk = top_block(boss, "BossAI_ComputeSwitchCandidateRisk")
    require_order(
        compute_risk,
        [
            "call BossAI_GetTierPlausibleRiskWeight",
            "call BossAI_TestLikelyMaskBit",
            "call BossAI_GetSpeculativePlausibleRiskWeight",
            "call BossAI_TestPlausibleMaskBit",
            "call BossAI_TestLikelyMaskBit",
        ],
        "source-weighted plausible switch risk",
    )

    require_contains(
        wram,
        "wBossAISeenPlayerSpecies:: ds PARTY_LENGTH",
        "WRAM active species registry",
    )
    require_contains(
        wram,
        "wBossAIRevealedMovesBitmap:: ds PARTY_LENGTH * 4 ; six 4-byte per-seen-species revealed type masks",
        "WRAM per-species revealed mask reserve",
    )
    require_contains(
        wram,
        "wBossAILikelyTypeMaskCache:: ds 4",
        "WRAM likely type mask cache",
    )
    require_contains(
        wram,
        "wBossAIRevealedMovesBitmapSpare:: ds 4",
        "WRAM revealed mask spare",
    )


def audit_switch_loop(boss: str) -> None:
    block = top_block(boss, "BossAI_NeedsLoopPenalty")
    require_order(
        block,
        [
            "ld a, [wEnemySwitchMonParam]",
            "and $f",
            "inc a",
            "ld b, a",
            "ld a, [wBossAILastSwitchedOut]",
            "cp b",
            "jr z, .check_exceptions",
        ],
        "switch loop proposed-target check",
    )
    for call in (
        "call BossAI_IsImminentKOPrevention",
        "call BossAI_IsImmunityPivotOpportunity",
        "call BossAI_AceTimingHook",
    ):
        require_contains(block, call, "switch loop emergency exceptions")


def audit_spikes_and_status(boss: str) -> None:
    spikes = local_block(boss, ".spikes_layer1", ".spikes_layer2")
    require_order(
        spikes,
        [
            "call .EnemyUnderPressure",
            "jr c, .spikes_l1_baseline",
            "ld a, [wBossAITurnsElapsed]",
            "cp 2",
            "jr c, .spikes_l1_high",
        ],
        "first-layer Spikes pressure and first-turn gate",
    )
    if re.search(r"ld a, \[wBossAITurnsElapsed\]\s*\n\s*and a", spikes):
        fail("first-layer Spikes reverted to turn-zero-only check")

    status = local_block(
        boss,
        ".StatusMoveWouldFailPublicly",
        ".ApplySetupPunishBias",
    )
    for effect in (
        "EFFECT_LEECH_SEED",
        "EFFECT_PARALYZE",
        "EFFECT_CONFUSE",
        "EFFECT_POISON",
        "EFFECT_TOXIC",
        "EFFECT_SLEEP",
    ):
        require_contains(status, effect, "status public fail gates")
    for public_state in (
        "wBattleMonStatus",
        "wPlayerSubStatus3",
        "SUBSTATUS_CONFUSED",
        "wPlayerSubStatus4",
        "SUBSTATUS_SUBSTITUTE",
        "SUBSTATUS_LEECH_SEED",
        "SCREENS_SAFEGUARD",
        "POISON",
        "STEEL",
        "GRASS",
    ):
        require_contains(status, public_state, "status public fail states")
    for type_gate in (
        ".EnemyStatusMoveTypeMissesPlayer",
        "wEnemyMoveStruct + MOVE_TYPE",
        "TypeMatchups",
        "SUBSTATUS_IDENTIFIED",
    ):
        require_contains(status, type_gate, "status type-immunity fail gate")

    move_model = top_block(boss, "BossAI_ApplyMoveModel")
    require_order(
        move_model,
        [
            "call .UtilityMoveWouldFailPublicly",
            "jr nc, .skip_utility_fail",
            "ld a, 24",
            "call BossAI_DiscourageScoreHL",
            "call .StatusMoveWouldFailPublicly",
            "jr nc, .status_ok",
            "ld a, 24",
            "call BossAI_DiscourageScoreHL",
            ".status_ok",
            "ld c, 4",
            "call .EncourageByTierWeight",
        ],
        "public fail discouragement before generic encouragement",
    )

    utility = local_block(boss, ".UtilityMoveWouldFailPublicly", ".check_primary_status")
    for effect in (
        "EFFECT_LIGHT_SCREEN",
        "EFFECT_REFLECT",
        "EFFECT_SUBSTITUTE",
        "EFFECT_PROTECT",
        "EFFECT_HEAL",
        "EFFECT_MORNING_SUN",
        "EFFECT_SYNTHESIS",
        "EFFECT_MOONLIGHT",
    ):
        require_contains(utility, effect, "utility public fail gates")
    for public_state in (
        "wEnemyScreens",
        "SCREENS_LIGHT_SCREEN",
        "SCREENS_REFLECT",
        "wEnemySubStatus4",
        "SUBSTATUS_SUBSTITUTE",
        "AICheckEnemyQuarterHP",
        "AICheckEnemyMaxHP",
    ):
        require_contains(utility, public_state, "utility public fail states")

    imperial = local_block(boss, ".imperial_scales", ".cap")
    require_order(
        imperial,
        [
            "ld a, [wTypeMatchup]",
            "cp EFFECTIVE + 1",
            "ld a, [wBattleMonType1]",
            "cp DRAGON",
            "ld a, [wBattleMonType2]",
            "cp DRAGON",
            "dec b",
        ],
        "Imperial Scales pressure discount",
    )


def audit_setup_and_phazing(boss: str) -> None:
    setup = local_block(boss, ".ApplySetupPunishBias", ".ApplyPhazingPlanBias")
    require_order(
        setup,
        [
            "call .PlayerHasMajorSetupBoost",
            "ret nc",
            "call .HasKOLine",
            "ret c",
        ],
        "setup punish public setup and KO guard",
    )
    for effect in ("EFFECT_FORCE_SWITCH", "EFFECT_RESET_STATS", "EFFECT_ENCORE"):
        require_contains(setup, effect, "setup punish denial effects")
    require_order(setup, ["ld a, 8", "jp BossAI_EncourageScoreHL"], "setup punish bias")

    major = local_block(boss, ".PlayerHasMajorSetupBoost", ".ApplySpikesLayerBias")
    for stat in (
        "wPlayerStatLevels + ATTACK",
        "wPlayerStatLevels + SP_ATTACK",
        "wPlayerStatLevels + SPEED",
        "wPlayerStatLevels + EVASION",
    ):
        require_contains(major, stat, "public +2 setup stat check")
    if major.count("cp BASE_STAT_LEVEL + 2") < 4:
        fail("public +2 setup check must cover four public stat lanes")

    phazing = local_block(boss, ".ApplyPhazingPlanBias", ".PlayerHasMajorSetupBoost")
    require_order(
        phazing,
        [
            "cp EFFECT_FORCE_SWITCH",
            "call .HasKOLine",
            "ret c",
            "ld a, [wPlayerScreens]",
            "and SCREENS_SPIKES_MASK",
            "ret z",
            "call .PlayerHasMajorSetupBoost",
            "jr c, .phaze_good",
            "call .PlayerHasRepeatedSwitchPressure",
            "ret nc",
            ".phaze_good",
            "ld a, 8",
            "jp BossAI_EncourageScoreHL",
        ],
        "Spikes plus phazing setup/switch pressure gate",
    )


def audit_champion_hyper_beam(boss: str) -> None:
    champion = local_block(boss, ".champion", ".EncourageIfType")
    require_order(
        champion,
        [
            "cp EFFECT_HYPER_BEAM",
            "ret nz",
            "call .HasKOLine",
            "ret c",
            "ld c, 5",
            "call .DiscourageByTierWeight",
        ],
        "Champion non-KO Hyper Beam discouragement",
    )


def audit_immunity_tiebreak(boss: str) -> None:
    refine = top_block(boss, "BossAI_RefineSwitchCandidateForPlausibleRisk")
    done = local_block(refine, ".done", "ld a, [wEnemySwitchMonParam]")
    replacement_margin = first_add_value(done, "switch candidate replacement margin")

    compute = top_block(boss, "BossAI_ComputeSwitchCandidateRisk")
    require_contains(
        compute,
        "call .ApplyPrimaryThreatImmunityTieBreak",
        "switch candidate risk immunity tie-break call",
    )
    tiebreak = local_block(compute, ".ApplyPrimaryThreatImmunityTieBreak", ".restore_no_penalty")
    require_order(
        tiebreak,
        [
            "call BossAI_GetPrimaryThreatType",
            "jr nc, .restore_no_penalty",
            "call BossAI_CheckTypeMatchupNoItem",
            "ld a, [wTypeMatchup]",
            "and a",
            "jr z, .restore_no_penalty",
        ],
        "public primary-threat non-immunity check",
    )
    tiebreak_adjustment = first_add_value(tiebreak, "primary-threat immunity tie-break")
    if tiebreak_adjustment <= replacement_margin:
        fail(
            "primary-threat non-immunity adjustment must exceed switch "
            f"replacement margin ({tiebreak_adjustment} <= {replacement_margin})"
        )


def audit_no_battle_core_boss_labels(core: str, boss: str) -> None:
    if 'SECTION "Battle Core"' in boss or 'BANK("Battle Core")' in boss:
        fail("boss.asm must not define or bank into Battle Core")
    for line in code_lines(core):
        stripped = line.strip()
        if TOP_LABEL_RE.match(stripped) and stripped.startswith("BossAI_"):
            fail("Battle Core must not define BossAI labels")


def audit_priority_trainers(parties: str, tiers: str) -> None:
    for entry in (
        "db MORTY, MORTY1, AI_TIER_MID",
        "db JASMINE, JASMINE1, AI_TIER_MID",
        "db CLAIR, CLAIR1, AI_TIER_LATE",
        "db KOGA, KOGA1, AI_TIER_LATE",
        "db CHAMPION, LANCE, AI_TIER_LATE",
    ):
        require_contains(tiers, entry, "priority boss AI tier")

    for move in (
        "GENGAR,     SPELL_TAG, SHADOW_BALL, THUNDERBOLT, DESTINY_BOND, SPIKES",
        "MAGNETON,   MAGNET, SPIKES, THUNDERBOLT, THUNDER_WAVE, SUPERSONIC",
        "STEELIX,    METAL_COAT, EARTHQUAKE, IRON_TAIL, ROCK_SLIDE, ROAR",
        "VAPOREON,   MYSTIC_WATER, SURF, ICE_BEAM, HAZE, ACID_ARMOR",
        "GLIGAR,     QUICK_CLAW, SPIKES, EARTHQUAKE, WING_ATTACK, TOXIC",
        "TENTACRUEL, MYSTIC_WATER, RAPID_SPIN, SURF, SLUDGE_BOMB, HAZE",
        "GYARADOS,   LEFTOVERS, RAIN_DANCE, OUTRAGE, SURF, HYPER_BEAM",
    ):
        require_contains(parties, move, "priority boss scenario move")


def audit_constants(constants: str) -> None:
    for constant in (
        "DEF BOSS_AI_SWITCH_CANDIDATE_CAP EQU 4",
        "DEF BOSS_AI_PLAUSIBLE_HP_RISK_BIT EQU 31",
        "DEF BOSS_AI_PLAUSIBLE_MIN_POWER EQU 45",
    ):
        require_contains(constants, constant, "Boss AI behavior constants")


def main() -> int:
    boss = load(BOSS)
    wram = load(WRAM)
    parties = load(PARTIES)
    tiers = load(AI_TIERS)
    constants = load(CONSTANTS)
    core = load(CORE)

    audit_revealed_coverage(boss, wram)
    audit_switch_loop(boss)
    audit_spikes_and_status(boss)
    audit_setup_and_phazing(boss)
    audit_champion_hyper_beam(boss)
    audit_immunity_tiebreak(boss)
    audit_no_battle_core_boss_labels(core, boss)
    audit_priority_trainers(parties, tiers)
    audit_constants(constants)

    print("Boss AI trace invariant audit passed.")
    print("Checked invariants:")
    for name in (
        "per-species revealed coverage",
        "source-weighted plausible threat confidence",
        "A->B->A loop penalty target check",
        "first-turn Spikes pressure gate",
        "public status fail gates",
        "public utility fail gates",
        "Imperial Scales pressure discount",
        "public +2 setup denial",
        "Spikes plus phazing pressure response",
        "Champion non-KO Hyper Beam discouragement",
        "primary-threat immunity pivot tie-break",
        "no Battle Core BossAI labels",
    ):
        print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
