#!/usr/bin/env python3
"""Audit post-patch Boss AI behavior invariants."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOSS_FILES = (
    ROOT / "engine" / "battle" / "ai" / "boss_platform.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_policy_move.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_policy_switch.asm",
    ROOT / "engine" / "battle" / "ai" / "boss_thunks.asm",
)
BOSS_TRACE_TOPMOVES = ROOT / "engine" / "battle" / "ai" / "boss_trace_topmoves.asm"
ITEMS = ROOT / "engine" / "battle" / "ai" / "items.asm"
SWITCH = ROOT / "engine" / "battle" / "ai" / "switch.asm"
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


def load_boss_source() -> str:
    return "\n".join(load(path) for path in BOSS_FILES)


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


def require_not_contains(block: str, needle: str, context: str) -> None:
    if needle in block:
        fail(f"{context}: must not contain `{needle}`")


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
            "push hl",
            "call BossAI_MoveTaintsFourMoveReveal",
            "pop hl",
            "call BossAI_AddRevealedMoveToSpeciesMask",
        ],
        "record revealed move path",
    )

    compute_mask = top_block(boss, "BossAI_ComputePlayerPlausibleTypeMask")
    require_order(
        compute_mask,
        [
            "call BossAI_AddPublicSTABThreatsToMask",
            "call BossAI_AddRevealedDamagingTypesToMask",
            "call BossAI_PlayerActiveFourMoveSaturated",
            "jr c, .done",
            "call BossAI_AddSpeciesAndPreEvolutionMovesToMask",
        ],
        "four-revealed-move saturation hook",
    )

    saturation = top_block(boss, "BossAI_PlayerActiveFourMoveSaturated")
    require_order(
        saturation,
        [
            "ld a, [wPlayerSubStatus5]",
            "bit SUBSTATUS_TRANSFORMED, a",
            "call BossAI_ActiveSpeciesRevealTainted",
            "ld hl, wPlayerUsedMoves",
            "ld c, NUM_MOVES",
            "call BossAI_MoveTaintsFourMoveReveal",
            "scf",
            "ret",
        ],
        "four-revealed-move saturation guards",
    )

    taint_move = top_block(boss, "BossAI_MoveTaintsFourMoveReveal")
    for needle in (
        "cp STRUGGLE",
        "cp EFFECT_MIRROR_MOVE",
        "cp EFFECT_TRANSFORM",
        "cp EFFECT_MIMIC",
        "cp EFFECT_METRONOME",
        "cp EFFECT_SKETCH",
        "cp EFFECT_SLEEP_TALK",
    ):
        require_contains(taint_move, needle, "four-move saturation unsafe move filter")

    active_taint = top_block(boss, "BossAI_ActiveSpeciesRevealTainted")
    require_order(
        active_taint,
        [
            "call BossAI_GetActiveSpeciesSeenIndex",
            "call BossAI_SeenPlayerSpeciesBitFromC",
            "ld hl, wBossAIRevealedMovesBitmapSpare",
            "and [hl]",
        ],
        "four-move saturation taint mask read",
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

    record_species = top_block(boss, "BossAI_RecordPlayerSpecies")
    require_order(
        record_species,
        [
            "wBattleMonSpecies",
            "wBossAISeenPlayerSpeciesCount",
            "wBossAISeenPlayerSpecies",
            "call BossAI_SetSeenPlayerAliveBit",
        ],
        "seen species alive mark on public send-out",
    )

    record_faint = top_block(boss, "BossAI_RecordPlayerFaint")
    require_order(
        record_faint,
        [
            "wBattleMonSpecies",
            "wBossAISeenPlayerSpeciesCount",
            "wBossAISeenPlayerSpecies",
            "call BossAI_ClearSeenPlayerAliveBit",
        ],
        "seen species alive clear on public faint",
    )

    seen_score = top_block(boss, "BossAI_SeenBenchThreatScore")
    require_order(
        seen_score,
        [
            "ld a, [wCurSpecies]",
            "push af",
            "ld a, [wBossAISeenPlayerAliveMask]",
            "ld [wBossAITemp5], a",
            "ld a, [wBossAITemp5]",
            "bit 0, a",
            "ld a, [wBattleMonSpecies]",
            "cp e",
            "ld [wCurSpecies], a",
            "call GetBaseData",
            "push hl",
            "call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem",
            "pop hl",
            ".next",
            "ld a, [wBossAITemp5]",
            "srl a",
            "ld [wBossAITemp5], a",
            ".restore_return",
            "ld b, a",
            "pop af",
            "ld [wCurSpecies], a",
            "push bc",
            "call GetBaseData",
            "pop bc",
            "ld a, b",
            "ret",
        ],
        "seen bench threat score base-data and pointer restoration",
    )

    species_moves = top_block(boss, "BossAI_AddSpeciesAndPreEvolutionMovesToMask")
    require_order(
        species_moves,
        [
            "ld [wBossAITemp4], a",
            "ld a, [wCurSpecies]",
            "push af",
            "ld a, [wCurPartySpecies]",
            "ld [wBossAITemp5], a",
            "ld a, [wBossAITemp4]",
            "ld [wCurPartySpecies], a",
            ".restore",
            "ld a, [wBossAITemp5]",
            "ld [wCurPartySpecies], a",
            "pop af",
            "ld [wCurSpecies], a",
            "call nz, GetBaseData",
            "ret",
        ],
        "plausible species move scan base-data restoration",
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
        "wBossAISeenPlayerAliveMask:: db ; bit per seen species slot, set while publicly not fainted",
        "WRAM seen species alive mask",
    )
    require_contains(
        wram,
        "wBossAIRevealedMovesBitmapSpare:: ds 3",
        "WRAM revealed mask spare",
    )


def audit_public_threat_keeps_species_fallback(boss: str) -> None:
    # The public symbol is now a thin per-tick cache wrapper; the real scan logic
    # lives in the *Uncached helper. Behavior asserted here is unchanged.
    public_threat = top_block(boss, "BossAI_PlayerHasPublicThreatVsEnemyUncached")
    require_order(
        public_threat,
        [
            "call BossAI_HasRevealedSuperEffectiveMove",
            "jr c, .yes",
            "ld hl, wPlayerUsedMoves",
            "jr z, .public_type_fallback",
            ".used_move_loop",
            "jr z, .public_type_fallback",
            "dec d",
            "jr nz, .used_move_loop",
            "jr .public_type_fallback",
            ".no",
            "and a",
            "ret",
            ".yes_pop_hl",
            "pop hl",
            ".yes",
            "scf",
            "ret",
            ".public_type_fallback",
            "ld a, [wBattleMonType1]",
            "call BossAI_PlayerThreatTypeSuperEffectiveVsEnemy",
            "ld a, [wBattleMonType2]",
            "call BossAI_PlayerThreatTypeSuperEffectiveVsEnemy",
        ],
        "public threat wrapper keeps active species typing after revealed-move scan",
    )
    hit_helper = top_block(boss, "BossAI_PlayerThreatTypeHitsEnemy")
    require_order(
        hit_helper,
        [
            "ld a, c",
            "call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem",
            "ld a, [wTypeMatchup]",
            "and a",
            "jr z, .no",
            "ld a, c",
            "call BossAI_EnemyKnownItemNullifiesThreatType",
            "jr c, .no",
            "scf",
            "ret",
        ],
        "public threat type helper preserves no-item matchup plus known nullifier semantics",
    )
    super_helper = top_block(boss, "BossAI_PlayerThreatTypeSuperEffectiveVsEnemy")
    require_order(
        super_helper,
        [
            "call BossAI_PlayerThreatTypeHitsEnemy",
            "jr nc, .no",
            "ld a, [wTypeMatchup]",
            "cp EFFECTIVE + 1",
            "jr c, .no",
            "scf",
            "ret",
        ],
        "super-effective public threat helper keeps the current severity threshold",
    )


def audit_switch_loop(boss: str) -> None:
    switch_entry = top_block(boss, "BossAI_SwitchOrTryItem")
    require_order(
        switch_entry,
        [
            "call BossAI_SelectPlanIfNeeded",
            "call BossAI_ComputePlayerPlausibleTypeMask",
            "call BossAI_TryMortyHakiOracle",
            "ret nz",
            "call BossAI_EnemyPerishEscapeUrgent",
            "jr c, .check_switch",
            "call BossAI_HasAnyKOMove",
        ],
        "perish escape can override KO stay gate",
    )

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
    require_order(
        block,
        [
            "call AICheckEnemyQuarterHP",
            "jr nc, .no_penalty",
            "call BossAI_ShouldRespectPotentialPlayerRevenge",
            "jr c, .no_penalty",
        ],
        "switch loop narrow emergency exception",
    )
    if "call BossAI_IsImminentKOPrevention" in block:
        fail("switch loop exception must not use broad imminent-KO predicate")
    for call in (
        "call BossAI_EnemyPerishEscapeUrgent",
        "call BossAI_IsImmunityPivotOpportunity",
        "call BossAI_AceTimingHook",
    ):
        require_contains(block, call, "switch loop emergency exceptions")

    perish = top_block(boss, "BossAI_EnemyPerishEscapeUrgent")
    require_order(
        perish,
        [
            "ld a, [wEnemySubStatus1]",
            "bit SUBSTATUS_PERISH, a",
            "ld a, [wEnemyPerishCount]",
            "cp 3",
            "jr nc, .no",
            "and a",
            "jr z, .no",
            "scf",
        ],
        "perish escape uses public own perish counter only",
    )

    confidence = top_block(boss, "BossAI_ComputeSwitchConfidence")
    require_order(
        confidence,
        [
            "call BossAI_AceTimingHook",
            ".no_ace_bonus",
            "call BossAI_EnemyPerishEscapeUrgent",
            "jr nc, .no_perish_bonus",
            "ld a, [wBossAISwitchConfidence]",
            "add 40",
            "cp 100",
            "ld a, 99",
            ".store_perish_bonus",
            "ld [wBossAISwitchConfidence], a",
            ".no_perish_bonus",
            "call BossAI_PredictPlayerSwitch",
        ],
        "perish escape adds strong switch confidence before player switch prediction",
    )


def audit_haki_quarantine(boss: str) -> None:
    turn = top_block(boss, "BossAI_IncrementTurnsElapsed")
    require_order(
        turn,
        [
            "ld a, [wBossAITier]",
            "ret z",
            "call BossAI_UpdateHakiAceWindow",
            "ld hl, wBossAITurnsElapsed",
        ],
        "Haki first-turn window is updated once per battle turn",
    )

    window = top_block(boss, "BossAI_UpdateHakiAceWindow")
    require_order(
        window,
        [
            "ld hl, wBossAIRevealedMovesBitmapSpare + 1",
            "res BOSSAI_HAKI_ELIGIBLE_F, [hl]",
            "bit BOSSAI_HAKI_SPENT_F, [hl]",
            "bit BOSSAI_HAKI_ACE_SEEN_F, [hl]",
            "cp MORTY",
            "cp MORTY1",
            "cp GENGAR",
            "set BOSSAI_HAKI_ACE_SEEN_F, [hl]",
            "set BOSSAI_HAKI_ELIGIBLE_F, [hl]",
        ],
        "Morty Haki first-turn state is trainer and ace gated",
    )

    oracle = top_block(boss, "BossAI_TryMortyHakiOracle")
    require_order(
        oracle,
        [
            "ld hl, wBossAIRevealedMovesBitmapSpare + 1",
            "bit BOSSAI_HAKI_SPENT_F, [hl]",
            "bit BOSSAI_HAKI_ELIGIBLE_F, [hl]",
            "ld a, [wEnemyGoesFirst]",
            "ld a, [wBattlePlayerAction]",
            "call .FindDestinyBondSlot",
            "call .PlayerSelectedStrongSuperEffectiveAttack",
            "ld [wCurEnemyMoveNum], a",
            "ld a, DESTINY_BOND",
            "ld [wCurEnemyMove], a",
            "callfar EnforceEnemyHeldMoveRestrictions_Far",
            "callfar UpdateMoveData",
            "call BossAI_UpdateRepeatTracker",
            "set BOSSAI_HAKI_SPENT_F, [hl]",
        ],
        "Morty Haki oracle is post-input, one-shot, and refreshes move data",
    )
    for needle in (
        "ld a, [wCurPlayerMove]",
        "call BossAI_PlayerThreatTypeSuperEffectiveVsEnemy",
        "or 1 << BOSSAI_HAKI_TRACE_FIRED_F",
        "ld [wBossAITraceChosenMove], a",
    ):
        require_contains(oracle, needle, "Morty Haki quarantine trace/input boundary")


def audit_revenge_denial_uses_public_seen_species(boss: str) -> None:
    revenge = top_block(boss, "BossAI_ShouldRespectPotentialPlayerRevenge")
    require_order(
        revenge,
        [
            "call BossAI_PublicEnemyFaster",
            "jr nc, .check_threat",
            "call BossAI_PlayerHasRevealedPriorityThreat",
            "jr c, .yes",
            "jr .check_seen_revenge",
            "call BossAI_GetPrimaryThreatType",
            "jr nc, .check_seen_revenge",
            "call BossAI_GetTypeThreatSeverityVsEnemyMon",
            "jr c, .check_seen_revenge",
            ".check_seen_revenge",
            "call .KnownSeenRevengeThreat",
            ".KnownSeenRevengeThreat",
            "wBossAITier",
            "AI_TIER_MID",
            "call BossAI_SeenBenchThreatScore",
            "cp 20",
            "cp 10",
            "call AICheckEnemyHalfHP",
        ],
        "revenge denial uses public active and seen-species threats",
    )


def audit_revealed_priority_pressure(boss: str) -> None:
    # Cache wrapper is at the public symbol; scan logic lives in the *Uncached.
    helper = top_block(boss, "BossAI_PlayerHasRevealedPriorityThreatUncached")
    require_order(
        helper,
        [
            "ld hl, wPlayerUsedMoves",
            "ld hl, Moves + MOVE_EFFECT",
            "call BossAI_GetMoveAttr",
            "cp EFFECT_PRIORITY_HIT",
            "ld hl, Moves + MOVE_POWER",
            "call BossAI_GetMoveAttr",
            "ld hl, Moves + MOVE_TYPE",
            "call BossAI_GetMoveAttr",
            "call BossAI_PlayerThreatTypeHitsEnemy",
            "call AICheckEnemyQuarterHP",
            "call AICheckEnemyHalfHP",
            "cp 80",
            "cp EFFECTIVE + 1",
        ],
        "revealed priority threat uses only public used moves and coarse HP bands",
    )

    pressure = local_block(boss, ".EnemyUnderPressure", ".HasKOLine")
    require_order(
        pressure,
        [
            "call AICheckEnemyQuarterHP",
            "call BossAI_PlayerHasRevealedPriorityThreat",
            "jr c, .pressure_yes",
            "call BossAI_PlayerHasPublicThreatVsEnemy",
        ],
        "move scoring pressure treats revealed priority as speed-breaking pressure",
    )

    projection = local_block(
        top_block(boss, "BossAI_ApplyMultiTurnProjection"),
        ".IsUnderPressure",
        ".pressure_yes",
    )
    require_order(
        projection,
        [
            "call AICheckEnemyQuarterHP",
            "call BossAI_PlayerHasRevealedPriorityThreat",
            "jr c, .pressure_yes",
            "call BossAI_PlayerHasPublicThreatVsEnemy",
        ],
        "lookahead pressure treats revealed priority as speed-breaking pressure",
    )

    compute = top_block(boss, "BossAI_ComputeSwitchCandidateRisk")
    require_order(
        compute,
        [
            "push bc",
            "call GetBaseData",
            "pop de",
            "ld b, 0",
            "call .ApplyRevealedPrioritySwitchInRisk",
            "ld a, [wBattleMonType1]",
        ],
        "switch candidate risk checks revealed priority before active STAB risk",
    )
    switch_priority = local_block(
        compute,
        ".ApplyRevealedPrioritySwitchInRisk",
        ".CandidateAtHalfHP",
    )
    require_order(
        switch_priority,
        [
            "call .CandidateAtHalfHP",
            "ret c",
            "ld hl, wPlayerUsedMoves",
            "ld hl, Moves + MOVE_EFFECT",
            "call BossAI_GetMoveAttr",
            "cp EFFECT_PRIORITY_HIT",
            "ld hl, Moves + MOVE_POWER",
            "call BossAI_GetMoveAttr",
            "ld hl, Moves + MOVE_TYPE",
            "call BossAI_GetMoveAttr",
            "call BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem",
            "cp EFFECTIVE",
            "add 3",
        ],
        "switch candidate revealed priority risk uses active revealed moves and candidate base typing",
    )
    candidate_hp = local_block(compute, ".CandidateAtHalfHP", ".AddTypeRisk")
    require_order(
        candidate_hp,
        [
            "ld hl, wOTPartyMon1HP",
            "ld bc, PARTYMON_STRUCT_LENGTH",
            "call AddNTimes",
            "sla c",
            "rl b",
            "sbc b",
        ],
        "switch candidate revealed priority risk uses own candidate coarse HP",
    )


def audit_revealed_protect_commitment_risk(boss: str) -> None:
    score = top_block(boss, "BossAI_ApplyMoveModel")
    require_order(
        score,
        [
            "call .ApplyChoiceFirstLockRegret",
            "call .ApplyRevealedProtectCommitmentRisk",
            "call BossAI_ApplyScoutMoveBias",
        ],
        "revealed Protect commitment risk runs before scout/repeat cleanup",
    )

    protect_risk = local_block(
        boss,
        ".ApplyRevealedProtectCommitmentRisk",
        ".PlayerHasRevealedProtect",
    )
    require_order(
        protect_risk,
        [
            "call .PlayerHasRevealedProtect",
            "ret nc",
            "ld a, [wEnemyMoveStruct + MOVE_EFFECT]",
            "cp EFFECT_SELFDESTRUCT",
            "jr z, .protect_hard_punish",
            "cp EFFECT_HYPER_BEAM",
            "ret nz",
            "ld a, 4",
            "jp BossAI_DiscourageScoreHL",
            ".protect_hard_punish",
            "ld a, 10",
            "jp BossAI_DiscourageScoreHL",
        ],
        "revealed Protect commitment risk discourages only high-commitment effects",
    )

    protect_scan = local_block(
        boss,
        ".PlayerHasRevealedProtect",
        ".ApplyRevealedRecoveryDenialBias",
    )
    require_order(
        protect_scan,
        [
            "ld a, EFFECT_PROTECT",
            "jp .PlayerHasRevealedEffectA",
        ],
        "revealed Protect scan uses shared exact visible player move effect helper",
    )


def audit_revealed_recovery_denial_bias(boss: str) -> None:
    score = top_block(boss, "BossAI_ApplyMoveModel")
    require_order(
        score,
        [
            "call .ApplyRevealedProtectCommitmentRisk",
            "call .ApplyRevealedRecoveryDenialBias",
            "call .ApplyLastMoveEncoreTrapBias",
            "call BossAI_ApplyScoutMoveBias",
        ],
        "revealed recovery denial runs before scout/repeat cleanup",
    )

    recovery_bias = local_block(
        boss,
        ".ApplyRevealedRecoveryDenialBias",
        ".PlayerHasRevealedRecovery",
    )
    require_order(
        recovery_bias,
        [
            "ld a, [wBossAITier]",
            "cp AI_TIER_MID",
            "ret c",
            "call .PlayerHasRevealedRecovery",
            "ret nc",
            "call AICheckPlayerMaxHP",
            "ret c",
            "call .HasKOLine",
            "ret c",
            "cp EFFECT_TOXIC",
            "jr z, .recovery_status",
            "cp EFFECT_LEECH_SEED",
            "jr z, .recovery_status",
            "cp EFFECT_FORCE_SWITCH",
            "ret nz",
            "call .UtilityMoveWouldFailPublicly",
            "ld a, 3",
            "jp BossAI_EncourageScoreHL",
            ".recovery_status",
            "call .StatusMoveWouldFailPublicly",
            "ld a, 4",
            "jp BossAI_EncourageScoreHL",
        ],
        "revealed recovery denial uses public recovery, current HP, and legal denial moves",
    )

    recovery_scan = local_block(
        boss,
        ".PlayerHasRevealedRecovery",
        ".CandidateMoveMatchupVsBaseTypes",
    )
    require_order(
        recovery_scan,
        [
            "ld hl, wPlayerUsedMoves",
            "ld hl, Moves + MOVE_EFFECT",
            "call BossAI_GetMoveAttr",
            "cp EFFECT_HEAL",
            "cp EFFECT_MORNING_SUN",
            "cp EFFECT_SYNTHESIS",
            "cp EFFECT_MOONLIGHT",
        ],
        "revealed recovery scan uses exact visible recovery effects",
    )


def audit_last_move_encore_trap_bias(boss: str) -> None:
    score = top_block(boss, "BossAI_ApplyMoveModel")
    require_order(
        score,
        [
            "call .ApplyRevealedRecoveryDenialBias",
            "call .ApplyRevealedFastEncoreAvoidance",
            "call .ApplyLastMoveEncoreTrapBias",
            "call BossAI_ApplyScoutMoveBias",
        ],
        "Encore reveal memory runs before scout/repeat cleanup",
    )

    revealed_encore = local_block(
        boss,
        ".ApplyRevealedFastEncoreAvoidance",
        ".EncorePunishableCommitmentMove",
    )
    require_order(
        revealed_encore,
        [
            "ld a, [wBossAITier]",
            "cp AI_TIER_MID",
            "ret c",
            "ld a, [wPlayerSubStatus5]",
            "bit SUBSTATUS_ENCORED, a",
            "ret nz",
            "call .EncorePunishableCommitmentMove",
            "ret nc",
            "ld a, EFFECT_ENCORE",
            "call .PlayerHasRevealedEffectA",
            "ret nc",
            "call BossAI_PublicEnemyFaster",
            "ret c",
            "ld a, 5",
            "jp BossAI_DiscourageScoreHL",
        ],
        "revealed fast Encore avoidance uses public reveal and speed gates",
    )

    encore_commitment = local_block(
        boss,
        ".EncorePunishableCommitmentMove",
        ".ApplyLastMoveEncoreTrapBias",
    )
    require_order(
        encore_commitment,
        [
            "call BossAI_IsCurrentEnemySetupMove",
            "ret c",
            "cp EFFECT_PROTECT",
            "cp EFFECT_SUBSTITUTE",
            "cp EFFECT_HEAL",
            "cp EFFECT_MORNING_SUN",
            "cp EFFECT_SYNTHESIS",
            "cp EFFECT_MOONLIGHT",
            "scf",
        ],
        "revealed fast Encore avoidance targets punishable commitment moves",
    )

    encore_bias = local_block(
        boss,
        ".ApplyLastMoveEncoreTrapBias",
        ".LastPlayerMoveIsEncoreTrap",
    )
    require_order(
        encore_bias,
        [
            "ld a, [wBossAITier]",
            "cp AI_TIER_MID",
            "ret c",
            "ld a, [wEnemyMoveStruct + MOVE_EFFECT]",
            "cp EFFECT_ENCORE",
            "ret nz",
            "ld a, [wPlayerSubStatus5]",
            "bit SUBSTATUS_ENCORED, a",
            "ret nz",
            "call .UtilityMoveWouldFailPublicly",
            "ret c",
            "call BossAI_PublicEnemyFaster",
            "ret nc",
            "call .LastPlayerMoveIsEncoreTrap",
            "ret nc",
            "ld a, 6",
            "jp BossAI_EncourageScoreHL",
        ],
        "last-move Encore trap uses tier, public fail, and public speed gates",
    )

    encore_scan = local_block(
        boss,
        ".LastPlayerMoveIsEncoreTrap",
        ".CandidateMoveMatchupVsBaseTypes",
    )
    require_order(
        encore_scan,
        [
            "ld a, [wLastPlayerMove]",
            "and a",
            "ret z",
            "cp STRUGGLE",
            "ret z",
            "cp ENCORE",
            "ret z",
            "cp MIRROR_MOVE",
            "ret z",
            "push hl",
            "ld hl, Moves + MOVE_EFFECT",
            "call BossAI_GetMoveAttr",
            "pop hl",
            "cp EFFECT_PROTECT",
            "cp EFFECT_HEAL",
            "cp EFFECT_MORNING_SUN",
            "cp EFFECT_SYNTHESIS",
            "cp EFFECT_MOONLIGHT",
        ],
        "last-move Encore trap scans only the public previous move effect",
    )


def audit_revealed_selfdestruct_protect_bias(boss: str) -> None:
    score = top_block(boss, "BossAI_ApplyMoveModel")
    require_order(
        score,
        [
            "call .ApplyLastMoveEncoreTrapBias",
            "call .ApplyRevealedSelfdestructProtectBias",
            "call BossAI_ApplyScoutMoveBias",
        ],
        "revealed Selfdestruct Protect bias runs before scout/repeat cleanup",
    )

    protect_bias = local_block(
        boss,
        ".ApplyRevealedSelfdestructProtectBias",
        ".PlayerHasRevealedSelfdestruct",
    )
    require_order(
        protect_bias,
        [
            "ld a, [wBossAITier]",
            "cp AI_TIER_MID",
            "ret c",
            "ld a, [wEnemyMoveStruct + MOVE_EFFECT]",
            "cp EFFECT_PROTECT",
            "ret nz",
            "call .UtilityMoveWouldFailPublicly",
            "ret c",
            "call AICheckPlayerHalfHP",
            "ret c",
            "push hl",
            "call BossAI_HasAnyKOMove",
            "pop hl",
            "ret c",
            "call .PlayerHasRevealedSelfdestruct",
            "ret nc",
            "ld a, 5",
            "jp BossAI_EncourageScoreHL",
        ],
        "revealed Selfdestruct Protect bias gates",
    )

    selfdestruct_scan = local_block(
        boss,
        ".PlayerHasRevealedSelfdestruct",
        ".CandidateMoveMatchupVsBaseTypes",
    )
    require_order(
        selfdestruct_scan,
        [
            "ld a, EFFECT_SELFDESTRUCT",
            "jp .PlayerHasRevealedEffectA",
        ],
        "revealed Selfdestruct scan uses shared exact visible move effect helper",
    )


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

    spikes_l2 = local_block(boss, ".spikes_layer2", ".spikes_layer3")
    require_order(
        spikes_l2,
        [
            "ld a, EFFECT_RAPID_SPIN",
            "call .PlayerHasRevealedEffectA",
            "call .ApplyRevealedRapidSpinSpikesRisk",
            "ret c",
            "call .ApplySpikesLayer2UnrevealedSpinRisk",
            "call BossAI_PredictPlayerSwitch",
        ],
        "layer-two Spikes applies public Spin risk before switch projection",
    )

    spikes_l3 = local_block(boss, ".spikes_layer3", ".spikes_l3_danger")
    require_order(
        spikes_l3,
        [
            "ld a, EFFECT_RAPID_SPIN",
            "call .PlayerHasRevealedEffectA",
            "call .ApplyRevealedRapidSpinSpikesRisk",
            "ret c",
            "call .ApplySpikesLayer3UnrevealedSpinRisk",
            "call .EncourageByTierWeight",
        ],
        "layer-three Spikes applies public Spin risk before third-layer reward",
    )

    revealed_spin = local_block(
        boss,
        ".ApplyRevealedRapidSpinSpikesRisk",
        ".ApplySpikesLayer2UnrevealedSpinRisk",
    )
    require_order(
        revealed_spin,
        [
            "call .EnemyActiveBlocksRapidSpin",
            "ld a, EFFECT_FORESIGHT",
            "call .PlayerHasRevealedEffectA",
            "call .BossHasAvailableReserveGhost",
            "call .DiscourageByTierWeight",
            "scf",
            "ret",
        ],
        "revealed Rapid Spin risk respects Ghost/Foresight before hard penalty",
    )

    active_spinblock = local_block(
        boss,
        ".EnemyActiveBlocksRapidSpin",
        ".BossHasAvailableReserveGhost",
    )
    require_order(
        active_spinblock,
        [
            "call BossAI_EnemyIsGhostType",
            "ld a, [wEnemySubStatus1]",
            "bit SUBSTATUS_IDENTIFIED, a",
        ],
        "active Ghost spinblock uses public identified state",
    )

    reserve_spinblock = local_block(
        boss,
        ".BossHasAvailableReserveGhost",
        ".RestoreBossSpeciesBaseData",
    )
    require_order(
        reserve_spinblock,
        [
            "ld a, [wOTPartyCount]",
            "ld de, wOTPartySpecies",
            "ld hl, wOTPartyMon1HP",
            "call .PartyMonAtLeastQuarterHP",
            "call GetBaseData",
            "ld a, [wBaseType1]",
            "cp GHOST",
            "ld a, [wBaseType2]",
            "cp GHOST",
        ],
        "reserve Ghost spinblock uses only boss-owned party state",
    )
    require_not_contains(
        reserve_spinblock,
        "wParty",
        "reserve Ghost spinblock must not read player party data",
    )

    bench_spin = local_block(
        boss,
        ".PlayerHasSeenBenchRevealedRapidSpin",
        ".PlayerActiveLikelyCanRapidSpin",
    )
    require_order(
        bench_spin,
        [
            "ld a, [wBossAISeenPlayerSpeciesCount]",
            "ld a, [wBossAISeenPlayerAliveMask]",
            "ld hl, wBossAISeenPlayerSpecies",
            "ld hl, wBossAISpeciesUsedMoves",
            "cp EFFECT_RAPID_SPIN",
        ],
        "bench Rapid Spin risk uses public seen/alive revealed-move memory",
    )
    require_not_contains(
        bench_spin,
        "wParty",
        "bench Rapid Spin risk must not read hidden player party data",
    )

    active_spin_prior = local_block(
        boss,
        ".PlayerActiveLikelyCanRapidSpin",
        ".SpeciesLevelUpHasRapidSpin",
    )
    require_order(
        active_spin_prior,
        [
            "call BossAI_PlayerActiveFourMoveSaturated",
            "ld a, [wBattleMonSpecies]",
            "call GetBaseData",
            "call .SpeciesLevelUpHasRapidSpin",
            "callfar GetPreEvolution",
        ],
        "active Rapid Spin prior uses public species/level and saturation",
    )
    for hidden_source in ("EggMovePointers", "wParty", "wBattleMonMoves"):
        require_not_contains(
            active_spin_prior,
            hidden_source,
            "active Rapid Spin prior excludes hidden or egg-move sources",
        )

    species_spin = local_block(boss, ".SpeciesLevelUpHasRapidSpin", ".ApplyRoleBias")
    require_order(
        species_spin,
        [
            "ld hl, EvosAttacksPointers",
            "ld a, [wBattleMonLevel]",
            "cp RAPID_SPIN",
        ],
        "Rapid Spin prior walks only level-up data through current public level",
    )
    require_not_contains(
        species_spin,
        "EggMovePointers",
        "Rapid Spin likely prior must exclude egg moves",
    )

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
    require_order(
        status,
        [
            ".StatusMoveWouldFailPublicly",
            "call .DarkShieldBlocksStatusEffect",
            "ret c",
        ],
        "full Dark shield status fail gate",
    )
    for effect in (
        "EFFECT_SLEEP",
        "EFFECT_TOXIC",
        "EFFECT_POISON",
        "EFFECT_PARALYZE",
        "EFFECT_CONFUSE",
        "EFFECT_LEECH_SEED",
    ):
        require_contains(status, effect, "full Dark shield status effects")
    require_order(
        status,
        [
            ".dark_shield_candidate",
            "ld a, [wPlayerDarkShieldConsumed]",
            "jr nz, .dark_shield_no",
            "ld a, [wBattleMonType1]",
            "cp DARK",
            "ld a, [wBattleMonType2]",
            "cp DARK",
            "scf",
        ],
        "full Dark shield public state check",
    )

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
    require_order(
        utility,
        [
            ".UtilityMoveWouldFailPublicly",
            "call .DarkShieldBlocksUtilityEffect",
            "ret c",
        ],
        "full Dark shield utility fail gate",
    )
    for effect in (
        "EFFECT_LIGHT_SCREEN",
        "EFFECT_REFLECT",
        "EFFECT_SAFEGUARD",
        "EFFECT_SUBSTITUTE",
        "EFFECT_PROTECT",
        "EFFECT_DISABLE",
        "EFFECT_ENCORE",
        "EFFECT_MEAN_LOOK",
        "EFFECT_DREAM_EATER",
        "EFFECT_NIGHTMARE",
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
        "SCREENS_SAFEGUARD",
        "wEnemySubStatus4",
        "wPlayerSubStatus4",
        "wPlayerSubStatus5",
        "wPlayerDisableCount",
        "wLastPlayerCounterMove",
        "wLastPlayerMove",
        "SUBSTATUS_SUBSTITUTE",
        "SUBSTATUS_ENCORED",
        "SUBSTATUS_CANT_RUN",
        "AICheckEnemyQuarterHP",
        "AICheckEnemyMaxHP",
    ):
        require_contains(utility, public_state, "utility public fail states")
    safeguard = local_block(utility, ".check_safeguard", ".check_substitute")
    require_order(
        safeguard,
        [
            "ld a, [wEnemyScreens]",
            "bit SCREENS_SAFEGUARD, a",
            "jp nz, .status_fail",
        ],
        "Safeguard public already-active fail gate",
    )
    disable = local_block(utility, ".check_disable", ".check_encore")
    require_order(
        disable,
        [
            "ld a, [wPlayerDisableCount]",
            "and a",
            "jp nz, .status_fail",
            "ld a, [wLastPlayerCounterMove]",
            "and a",
            "jp z, .status_fail",
            "cp STRUGGLE",
            "jp z, .status_fail",
        ],
        "Disable public existing-disable and last-counter fail gate",
    )
    encore = local_block(utility, ".check_encore", ".check_mean_look")
    require_order(
        encore,
        [
            "ld a, [wPlayerSubStatus5]",
            "bit SUBSTATUS_ENCORED, a",
            "jp nz, .status_fail",
            "ld a, [wLastPlayerMove]",
            "and a",
            "jp z, .status_fail",
            "cp STRUGGLE",
            "jp z, .status_fail",
            "cp ENCORE",
            "jp z, .status_fail",
            "cp MIRROR_MOVE",
            "jp z, .status_fail",
        ],
        "Encore public existing-encore and last-move fail gate",
    )
    mean_look = local_block(utility, ".check_mean_look", ".check_dream_eater")
    require_order(
        mean_look,
        [
            "ld a, [wPlayerSubStatus5]",
            "bit SUBSTATUS_CANT_RUN, a",
            "jp nz, .status_fail",
        ],
        "Mean Look public already-trapped fail gate",
    )
    dream_eater = local_block(utility, ".check_dream_eater", ".check_rain_dance")
    require_order(
        dream_eater,
        [
            "ld a, [wPlayerSubStatus4]",
            "bit SUBSTATUS_SUBSTITUTE, a",
            "jp nz, .status_fail",
            "ld a, [wBattleMonStatus]",
            "and SLP_MASK",
            "jp z, .status_fail",
        ],
        "Dream Eater public Substitute and sleep fail gate",
    )
    nightmare = local_block(utility, ".check_nightmare", ".check_rain_dance")
    require_order(
        nightmare,
        [
            "ld a, [wPlayerSubStatus4]",
            "bit SUBSTATUS_SUBSTITUTE, a",
            "jp nz, .status_fail",
            "ld a, [wBattleMonStatus]",
            "and SLP_MASK",
            "jp z, .status_fail",
            "ld a, [wPlayerSubStatus1]",
            "bit SUBSTATUS_NIGHTMARE, a",
            "jp nz, .status_fail",
        ],
        "Nightmare public Substitute, sleep, and duplicate fail gate",
    )
    for effect in (
        "EFFECT_DISABLE",
        "EFFECT_ENCORE",
        "EFFECT_SPITE",
        "EFFECT_ATTRACT",
        "EFFECT_MEAN_LOOK",
        "EFFECT_NIGHTMARE",
        "EFFECT_FORCE_SWITCH",
        "EFFECT_ATTACK_DOWN",
        "EFFECT_EVASION_DOWN",
        "EFFECT_ATTACK_DOWN_2",
        "EFFECT_EVASION_DOWN_2",
    ):
        require_contains(utility, effect, "full Dark shield utility effects")

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
    move_model = top_block(boss, "BossAI_ApplyMoveModel")
    require_order(
        move_model,
        [
            "call .ApplyBatonPassBias",
            "call .ApplyRevealedAntiSetupAvoidance",
            "call .ApplyRampMoveBias",
        ],
        "revealed anti-setup avoidance hook",
    )

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

    anti_setup = local_block(boss, ".ApplyRevealedAntiSetupAvoidance", ".IsBoostSetupMove")
    require_order(
        anti_setup,
        [
            "wBossAITier",
            "AI_TIER_MID",
            "call .IsBoostSetupMove",
            "call .HasKOLine",
            "call .PlayerHasRevealedAntiSetup",
            "jp BossAI_DiscourageScoreHL",
        ],
        "revealed anti-setup avoidance gates",
    )

    boost_setup = local_block(boss, ".IsBoostSetupMove", ".PlayerHasRevealedAntiSetup")
    for effect in (
        "EFFECT_DRAGON_DANCE",
        "EFFECT_CALM_MIND",
        "EFFECT_QUIVER_DANCE",
        "EFFECT_CURSE",
        "EFFECT_ATTACK_UP",
        "EFFECT_EVASION_UP",
        "EFFECT_ATTACK_UP_2",
        "EFFECT_EVASION_UP_2",
    ):
        require_contains(boost_setup, effect, "boost-only setup classifier")
    require_not_contains(boost_setup, "EFFECT_RAIN_DANCE", "boost-only setup classifier")
    require_not_contains(boost_setup, "EFFECT_SUNNY_DAY", "boost-only setup classifier")

    plan_setup = top_block(boss, "BossAI_IsSetupEffect")
    require_order(
        plan_setup,
        [
            "EFFECT_DRAGON_DANCE",
            "EFFECT_CALM_MIND",
            "EFFECT_QUIVER_DANCE",
            "EFFECT_RAIN_DANCE",
            "EFFECT_SUNNY_DAY",
            "EFFECT_ATTACK_UP",
        ],
        "shared setup classifier includes weather setup effects",
    )

    current_setup = top_block(boss, "BossAI_IsCurrentEnemySetupMove")
    require_order(
        current_setup,
        [
            "wEnemyMoveStruct + MOVE_EFFECT",
            "EFFECT_CURSE",
            "jp BossAI_IsSetupEffect",
            "call BossAI_EnemyIsGhostType",
            "jr c, .no",
        ],
        "current setup classifier handles non-Ghost Curse without poisoning shared helper",
    )

    revealed_anti_setup = local_block(boss, ".PlayerHasRevealedAntiSetup", ".ApplyRampMoveBias")
    require_order(
        revealed_anti_setup,
        [
            "ld a, EFFECT_RESET_STATS",
            "call .PlayerHasRevealedEffectA",
            "ret c",
            "ld a, EFFECT_FORCE_SWITCH",
            "jp .PlayerHasRevealedEffectA",
        ],
        "revealed anti-setup wrapper checks exact public denial effects",
    )

    shared_revealed_scan = local_block(boss, ".PlayerHasRevealedEffectA", ".ApplyRampMoveBias")
    require_order(
        shared_revealed_scan,
        [
            "ld [wBossAITemp], a",
            "push hl",
            "push bc",
            "ld hl, wPlayerUsedMoves",
            "ld hl, Moves + MOVE_EFFECT",
            "call BossAI_GetMoveAttr",
            "ld b, a",
            "ld a, [wBossAITemp]",
            "cp b",
            "scf",
        ],
        "shared revealed-effect scan uses exact visible player move effects",
    )

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

    projection = top_block(boss, "BossAI_ApplyMultiTurnProjection")
    require_order(
        projection,
        [
            "call BossAI_PredictPlayerSwitch",
            "cp 50",
            "cp EFFECT_SPIKES",
            "jr z, .switch_candidate",
            "call BossAI_IsCurrentEnemySetupMove",
            "jr nc, .check_accuracy",
            ".switch_candidate",
            "call .IsUnderPressure",
            "jr c, .check_accuracy",
            ".switch_bonus",
            "call .GetProjectionDepth",
            "call .AddUpsideByA",
        ],
        "Spikes/setup projection overread floor",
    )


def audit_poison_contact_risk(boss: str) -> None:
    move_model = top_block(boss, "BossAI_ApplyMoveModel")
    require_order(
        move_model,
        [
            "call .ApplyChargeMoveBias",
            "call .ApplyPoisonContactRiskBias",
            "call BossAI_ApplyScoutMoveBias",
        ],
        "Poison contact retaliation risk hook",
    )

    poison = local_block(boss, ".ApplyPoisonContactRiskBias", ".EnemyHasBoostToPass")
    require_order(
        poison,
        [
            ".ApplyPoisonContactRiskBias",
            "ld a, [wEnemyMoveStruct + MOVE_POWER]",
            "call .EnemyMoveMakesContact",
            "call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem",
            "ld a, [wTypeMatchup]",
            "call .HasKOLine",
            "ret c",
            "call .EnemyCanBePoisonedByRetaliation",
            "call .PlayerPoisonTypeContribution",
            "jp BossAI_DiscourageScoreHL",
        ],
        "Poison contact risk must be damaging/contact/non-KO/public",
    )
    for public_state in (
        "wEnemyMoveStruct + MOVE_ANIM",
        "MoveContactFlags",
        "BANK(MoveContactFlags)",
        "wEnemyMonStatus",
        "wEnemyMonType1",
        "wEnemyMonType2",
        "wEnemyScreens",
        "SCREENS_SAFEGUARD",
        "wBattleMonType1",
        "wBattleMonType2",
        "POISON",
        "STEEL",
    ):
        require_contains(poison, public_state, "Poison contact public state")
    require_order(
        poison,
        [
            "cp 2",
            "jr z, .full_poison_contact_risk",
            "ld a, 2",
            "jp BossAI_DiscourageScoreHL",
            ".full_poison_contact_risk",
            "ld a, 4",
            "jp BossAI_DiscourageScoreHL",
        ],
        "Poison contact half/full risk scale",
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


def audit_switch_candidate_state_restoration(boss: str) -> None:
    immunity = top_block(boss, "BossAI_IsImmunityPivotOpportunity")
    require_order(
        immunity,
        [
            "ld a, [wCurSpecies]",
            "push af",
            "ld [wCurSpecies], a",
            "call GetBaseData",
            "pop af",
            "ld [wCurSpecies], a",
            "call nz, GetBaseData",
            "scf",
            "ret",
            ".not_immune",
            "pop af",
            "ld [wCurSpecies], a",
            "call nz, GetBaseData",
            "and a",
            "ret",
            ".no",
            "pop af",
            "pop af",
            "ld [wCurSpecies], a",
            "call nz, GetBaseData",
            "and a",
            "ret",
        ],
        "immunity pivot candidate base-data restoration",
    )

    compute = top_block(boss, "BossAI_ComputeSwitchCandidateRisk")
    require_order(
        compute,
        [
            "ld a, [wCurSpecies]",
            "push af",
            "ld [wCurSpecies], a",
            "call GetBaseData",
            ".done",
            "jr c, .restore_return",
            "jr .restore_return",
            ".hard_risk",
            "ld a, 99",
            ".restore_return",
            "ld b, a",
            "pop af",
            "ld [wCurSpecies], a",
            "push bc",
            "call GetBaseData",
            "pop bc",
            "ld a, b",
            "ret",
        ],
        "switch candidate risk base-data restoration",
    )


def audit_item_and_passive_reasoning(boss: str) -> None:
    move_model = top_block(boss, "BossAI_ApplyMoveModel")
    require_order(
        move_model,
        [
            "call .HeldItemMoveBlocked",
            "ret c",
            "call .ApplyPoisonContactRiskBias",
            "call .ApplyDarkShieldChanceBias",
            "call .ApplyLifeOrbRecoilBias",
            "call .ApplyDestinyBondTradeBias",
            "call .ApplyRevealedDestinyBondAvoidance",
            "call .ApplyCounterCoatTradeBias",
            "call .ApplyChoiceFirstLockRegret",
            "call BossAI_CurrentEnemyMoveAccuracyRisky",
        ],
        "Boss AI known item/passive move hooks",
    )
    scored_power = top_block(boss, "BossAI_CurrentEnemyMoveScoredPower")
    require_order(
        scored_power,
        [
            "EFFECT_SOLARBEAM",
            "jr z, .solar_power",
            "EFFECT_REVERSAL",
            "jr z, .reversal_power",
            ".solar_power",
            "WEATHER_SUN",
            "SUBSTATUS_CHARGED",
            ".reversal_power",
            "call AICheckEnemyQuarterHP",
            "jr nc, .reversal_high",
            "call AICheckEnemyHalfHP",
            "jr nc, .reversal_mid",
            ".reversal_high",
            "ld a, 100",
            ".reversal_mid",
            "ld a, 70",
            ".raw_power",
            "wEnemyMoveStruct + MOVE_POWER",
        ],
        "Reversal/Flail public HP-band scored power",
    )
    held = local_block(move_model, ".HeldItemMoveBlocked", ".held_item_legal")
    for needle in (
        "call BossAI_EnemyChoiceLockedMove",
        "wEnemyMoveStruct + MOVE_ANIM",
        "call BossAI_SetScoreHL",
        "HELD_ASSAULT_VEST",
        "call .AssaultVestBlocksCurrentMove",
    ):
        require_contains(held, needle, "held item legality model")
    choice_lock = top_block(boss, "BossAI_EnemyChoiceLockedMove")
    for needle in (
        "wEnemyChoiceLockedMove",
        "call BossAI_GetEnemyHeldEffect",
        "call BossAI_IsChoiceHeldEffect",
    ):
        require_contains(choice_lock, needle, "Choice locked move model")
    require_contains(
        top_block(boss, "BossAI_GetEnemyHeldEffect"),
        "callfar GetItemHeldEffect",
        "enemy held-effect lookup",
    )

    pressure = top_block(boss, "BossAI_ApplyEnemyHeldItemPressure")
    require_contains(
        pressure,
        "call BossAI_GetEnemyHeldEffect",
        "known offensive item pressure uses held effects",
    )
    for item in (
        "HELD_LIFE_ORB",
        "HELD_CHOICE_BAND",
        "HELD_CHOICE_SPECS",
        "HELD_EXPERT_BELT",
        "HELD_MUSCLE_BAND",
        "HELD_WISE_GLASSES",
        "HELD_METRONOME",
    ):
        require_contains(pressure, item, "known offensive item pressure")

    passive = top_block(boss, "BossAI_ApplyPlayerDefensivePassivePressure")
    for type_name in ("PSYCHIC_TYPE", "GROUND", "BUG", "WATER", "ICE"):
        require_contains(passive, type_name, "public defensive passive pressure")
    require_contains(
        top_block(boss, "BossAI_ApplyEnemyOffensivePassivePressure"),
        "BossAI_EnemyBelowOneThirdHP",
        "Fire passive low HP model",
    )

    speed = top_block(boss, "BossAI_PublicEnemyFaster")
    require_contains(speed, "HELD_CHOICE_SCARF", "Choice Scarf public speed model")
    require_contains(
        speed,
        "call BossAI_GetEnemyHeldEffect",
        "Choice Scarf public speed model uses held effect",
    )

    threat = top_block(boss, "BossAI_AdjustThreatSeverityForEnemyKnownDefense")
    require_contains(
        threat,
        "call BossAI_EnemyKnownItemNullifiesThreatType",
        "known defensive item nullifier hook",
    )
    require_contains(
        threat,
        "call BossAI_GetEnemyHeldEffect",
        "known defensive item threat model uses held effects",
    )
    for item in ("HELD_ASSAULT_VEST", "HELD_EVOLITE"):
        require_contains(threat, item, "known defensive item threat model")
    nullifier = top_block(boss, "BossAI_EnemyKnownItemNullifiesThreatType")
    require_contains(nullifier, "HELD_AIR_BALLOON", "Air Balloon threat nullifier")
    require_contains(
        nullifier,
        "call BossAI_GetEnemyHeldEffect",
        "Air Balloon threat nullifier uses held effect",
    )

    destiny = local_block(move_model, ".ApplyDestinyBondTradeBias", ".ApplyRevealedDestinyBondAvoidance")
    require_order(
        destiny,
        [
            "EFFECT_DESTINY_BOND",
            "wBossAITier",
            "AI_TIER_MID",
            "call AICheckEnemyQuarterHP",
            "call .HasKOLine",
            "call BossAI_PlayerHasPublicThreatVsEnemy",
            "call BossAI_PublicEnemyFaster",
            "call .EncourageByTierWeight",
            "jp BossAI_EncourageScoreHL",
        ],
        "Destiny Bond public trade-window gates",
    )

    destiny_avoid = local_block(
        move_model,
        ".ApplyRevealedDestinyBondAvoidance",
        ".ApplyCounterCoatTradeBias",
    )
    require_order(
        destiny_avoid,
        [
            "ld a, [wBossAITier]",
            "cp AI_TIER_MID",
            "ret c",
            "wEnemyMoveStruct + MOVE_POWER",
            "call .HasKOLine",
            "ret nc",
            "call AICheckPlayerQuarterHP",
            "ret c",
            "ld a, EFFECT_DESTINY_BOND",
            "call .PlayerHasRevealedEffectA",
            "ret nc",
            "call BossAI_PublicEnemyFaster",
            "ret c",
            "ld a, 7",
            "jp BossAI_DiscourageScoreHL",
        ],
        "revealed Destiny Bond KO avoidance gates",
    )

    countercoat = local_block(move_model, ".ApplyCounterCoatTradeBias", ".PlayerHasRevealedCounterCoatCategory")
    require_order(
        countercoat,
        [
            "EFFECT_COUNTER",
            "EFFECT_MIRROR_COAT",
            "wBossAITier",
            "AI_TIER_MID",
            "call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem",
            "wTypeMatchup",
            "call .HasKOLine",
            "call BossAI_PublicEnemyFaster",
            "call BossAI_PlayerHasPublicThreatVsEnemy",
            "call .PlayerHasRevealedCounterCoatCategory",
            "call .EncourageByTierWeight",
            "jp BossAI_EncourageScoreHL",
        ],
        "Counter/Mirror Coat public trade-window gates",
    )

    countercoat_seen = local_block(move_model, ".PlayerHasRevealedCounterCoatCategory", ".ApplyRevealedCounterCoatAvoidance")
    for needle in (
        "wPlayerUsedMoves",
        "Moves + MOVE_POWER",
        "call BossAI_GetMoveAttr",
        "call BossAI_GetMoveByte",
        "cp SPECIAL",
        "scf",
    ):
        require_contains(countercoat_seen, needle, "Counter/Mirror Coat revealed-category scan")

    require_order(
        move_model,
        [
            "call .ApplyCounterCoatTradeBias",
            "call .ApplyRevealedCounterCoatAvoidance",
            "call .ApplyChoiceFirstLockRegret",
        ],
        "revealed Counter/Mirror Coat avoidance hook",
    )

    countercoat_avoid = local_block(
        move_model,
        ".ApplyRevealedCounterCoatAvoidance",
        ".PlayerHasRevealedCounterCoatTrap",
    )
    require_order(
        countercoat_avoid,
        [
            "wBossAITier",
            "AI_TIER_MID",
            "wEnemyMoveStruct + MOVE_POWER",
            "call .HasKOLine",
            "call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem",
            "wTypeMatchup",
            "call BossAI_CurrentEnemyMoveCategory",
            "cp SPECIAL",
            "call .PlayerHasRevealedCounterCoatTrap",
            "jp BossAI_DiscourageScoreHL",
        ],
        "revealed Counter/Mirror Coat avoidance gates",
    )

    countercoat_trap = local_block(
        move_model,
        ".PlayerHasRevealedCounterCoatTrap",
        ".ApplyChoiceFirstLockRegret",
    )
    require_order(
        countercoat_trap,
        [
            "ld a, b",
            "and a",
            "ld a, EFFECT_COUNTER",
            "jr z, .counter_coat_trap_scan",
            "ld a, EFFECT_MIRROR_COAT",
            ".counter_coat_trap_scan",
            "jp .PlayerHasRevealedEffectA",
        ],
        "revealed Counter/Mirror Coat trap scan uses shared public effect helper",
    )

    choice_commit = local_block(move_model, ".ApplyChoiceFirstLockRegret", ".SeenSpeciesChoiceLockRisk")
    require_order(
        choice_commit,
        [
            "wEnemyMoveStruct + MOVE_POWER",
            "wEnemyChoiceLockedMove",
            "call BossAI_GetEnemyHeldEffect",
            "call BossAI_IsChoiceHeldEffect",
            "call .HasKOLine",
            "ret c",
            "call .EnemyUnderPressure",
            "ret c",
            "call BossAI_PredictPlayerSwitch",
            "cp 60",
            "call .SeenSpeciesChoiceLockRisk",
        ],
        "Choice first-lock commitment gates",
    )
    require_contains(
        choice_commit,
        "jp BossAI_DiscourageScoreHL",
        "Choice first-lock commitment penalty",
    )

    choice_seen = local_block(move_model, ".SeenSpeciesChoiceLockRisk", ".CandidateMoveMatchupVsBaseTypes")
    for needle in (
        "wBossAISeenPlayerSpeciesCount",
        "wBossAISeenPlayerSpecies",
        "call GetBaseData",
        "call .CandidateMoveMatchupVsBaseTypes",
        "cp EFFECTIVE",
        "ld e, 2",
    ):
        require_contains(choice_seen, needle, "Choice first-lock public seen-species risk")
    choice_matchup = local_block(move_model, ".CandidateMoveMatchupVsBaseTypes", ".EnemyMoveMakesContact")
    require_order(
        choice_matchup,
        [
            "ldh a, [hBattleTurn]",
            "ld a, 1",
            "ldh [hBattleTurn], a",
            "ld a, [wEnemyMoveStruct + MOVE_TYPE]",
            "ld hl, wBaseType1",
            "call BossAI_CheckTypeMatchupNoItem",
            "ld a, [wTypeMatchup]",
        ],
        "Choice first-lock matchup uses candidate type against seen species",
    )


def audit_baton_pass_requires_living_bench(boss: str) -> None:
    move_model = top_block(boss, "BossAI_ApplyMoveModel")
    baton = local_block(move_model, ".ApplyBatonPassBias", ".ApplyRampMoveBias")
    require_order(
        baton,
        [
            "cp EFFECT_BATON_PASS",
            "push hl",
            "call BossAI_FindFirstAliveSwitchCandidate",
            "pop hl",
            "jr nc, .baton_bad",
            "call .EnemyHasBoostToPass",
            "jr c, .baton_good",
            ".baton_bad",
            "call BossAI_DiscourageScoreHL",
            ".baton_good",
            "call .EncourageByTierWeight",
        ],
        "Baton Pass bias requires a living bench and preserves score pointer",
    )


def audit_trace_top_moves_preserves_pointer(boss: str) -> None:
    # BossAI_TraceTopMoves was lifted to its own SECTION/file so the bank can
    # hold the per-tick cache wrappers; read its source file directly.
    trace_source = BOSS_TRACE_TOPMOVES.read_text(encoding="utf-8")
    trace = top_block(trace_source, "BossAI_TraceTopMoves")
    require_order(
        trace,
        [
            "ld de, wEnemyMonMoves",
            "push de",
            "call .InsertCandidate",
            "pop de",
            "inc de",
        ],
        "BossAI trace top-move pointer preservation",
    )


def audit_move_model_trace_snapshots(boss: str, wram: str) -> None:
    move_model = top_block(boss, "BossAI_ApplyMoveModel")
    require_order(
        move_model,
        [
            "call BossAI_ComputePlayerPlausibleTypeMask",
            "call .ClearMoveModelTrace",
            "ld hl, wEnemyAIMoveScores",
            "ld de, wEnemyMonMoves",
            "call .TracePreModelScore",
            "ld a, [hl]",
            "cp 80",
            "jr nc, .scored",
            "call .ScoreMove",
            ".scored",
            "call .TracePostModelScore",
        ],
        "move-model trace snapshots bracket policy scoring",
    )
    for label in (".TracePreModelScore", ".TracePostModelScore"):
        helper = local_block(move_model, label, ".ScoreMove" if label == ".TracePostModelScore" else ".TracePostModelScore")
        require_order(
            helper,
            [
                "push af",
                "push bc",
                "push de",
                "push hl",
                "ld d, [hl]",
                "ld a, NUM_MOVES",
                "sub c",
                "ld c, a",
                "ld b, 0",
                "add hl, bc",
                "ld [hl], d",
                "pop hl",
                "pop de",
                "pop bc",
                "pop af",
                "ret",
            ],
            f"{label} preserves score-loop registers",
        )
    require_contains(
        wram,
        "wBossAITracePreModelScores:: ds NUM_MOVES",
        "trace pre-model score snapshot reserve",
    )
    require_contains(
        wram,
        "wBossAITracePostModelScores:: ds NUM_MOVES",
        "trace post-model score snapshot reserve",
    )


def audit_boss_move_attr_bank_safety(boss: str) -> None:
    require_not_contains(boss, "call GetMoveAttr", "Boss AI cross-bank move attr reads")
    require_not_contains(boss, "call GetMoveByte", "Boss AI cross-bank move byte reads")
    helper = top_block(boss, "BossAI_GetMoveAttr")
    require_order(
        helper,
        [
            "ld bc, MOVE_LENGTH",
            "call AddNTimes",
            "call BossAI_GetMoveByte",
        ],
        "Boss AI local move attr helper",
    )
    byte_helper = top_block(boss, "BossAI_GetMoveByte")
    require_order(
        byte_helper,
        [
            "ld a, BANK(Moves)",
            "jp GetFarByte",
        ],
        "Boss AI local move byte helper",
    )


def audit_public_threat_scan_preserves_source_pointers(boss: str) -> None:
    level_moves = local_block(
        top_block(boss, "BossAI_AddSpeciesLevelUpMovesToMask"),
        ".move_loop",
        ".skip_move",
    )
    require_order(
        level_moves,
        [
            "call GetFarByte",
            "push hl",
            "call BossAI_AddMoveIdToPlausibleMask",
            "pop hl",
            "inc hl",
            "jr .move_loop",
        ],
        "Boss AI level-up plausible move source pointer preservation",
    )

    likely_moves = local_block(
        top_block(boss, "BossAI_AddSpeciesLevelUpMovesToLikelyMask"),
        ".move_loop",
        ".skip_move",
    )
    require_order(
        likely_moves,
        [
            "call GetFarByte",
            "push hl",
            "call BossAI_AddMoveIdToLikelyMask",
            "pop hl",
            "inc hl",
            "jr .move_loop",
        ],
        "Boss AI level-up likely move source pointer preservation",
    )

    egg_moves = top_block(boss, "BossAI_AddSpeciesEggMovesToMask")
    require_order(
        egg_moves,
        [
            "call GetFarByte",
            "cp -1",
            "ret z",
            "push hl",
            "call BossAI_AddMoveIdToPlausibleMask",
            "pop hl",
            "inc hl",
            "jr .loop",
        ],
        "Boss AI egg move source pointer preservation",
    )


def audit_type_matchup_scan_preserves_table_cursor(boss: str) -> None:
    matchup = local_block(
        top_block(boss, "BossAI_CheckTypeMatchupNoItem"),
        ".yup",
        ".end",
    )
    require_order(
        matchup,
        [
            ".yup",
            "push hl",
            "call GetFarByte",
            "inc hl",
            "call BossAI_ApplyDragonsMajestyNoItem",
            "call Multiply",
            "call Divide",
            "pop hl",
            "jr .types_loop",
        ],
        "Boss AI type-matchup scan table cursor preservation",
    )


def audit_type_threat_severity_preserves_list_cursor(boss: str) -> None:
    severity = top_block(boss, "BossAI_GetTypeThreatSeverityVsEnemyMon")
    require_order(
        severity,
        [
            "push hl",
            "call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem",
            "pop hl",
            ".adjust",
            "ld b, a",
            "push hl",
            "call BossAI_AdjustThreatSeverityForEnemyKnownDefense",
            "pop hl",
            "ret",
        ],
        "Boss AI type-threat severity list cursor preservation",
    )


def audit_legacy_switch_state_restoration(items: str, switch: str) -> None:
    wrapper = top_block(items, "AI_CheckAbleToSwitchPreserveCurSpecies")
    require_order(
        wrapper,
        [
            "ld a, [wCurSpecies]",
            "push af",
            "callfar CheckAbleToSwitch",
            "pop af",
            "ld [wCurSpecies], a",
            "call nz, GetBaseData",
            "ret",
        ],
        "legacy switch entrypoint base-data restoration",
    )

    for label in ("SwitchOften", "SwitchRarely", "SwitchSometimes"):
        require_contains(
            top_block(items, label),
            "call AI_CheckAbleToSwitchPreserveCurSpecies",
            "legacy switch callers restore base data",
        )

    require_order(
        top_block(switch, "FindEnemyMonsThatResistPlayer"),
        [
            "push bc",
            "ld hl, wOTPartySpecies",
            "ld [wCurSpecies], a",
            "call GetBaseData",
            ".done",
            "pop bc",
            "and c",
            "ld c, a",
            "ret",
        ],
        "legacy resist switch scan uses real party species",
    )

    require_order(
        top_block(switch, "FindEnemyMonsWithASuperEffectiveMove"),
        [
            "ld d, 0",
            "ld e, 0",
            ".loop",
            "ld a, b",
            "and c",
            "jr z, .next",
            "ld e, 0",
            "push hl",
            "push bc",
        ],
        "legacy super-effective switch scan resets per-candidate result",
    )


def audit_no_battle_core_boss_labels(core: str, boss: str) -> None:
    if 'SECTION "Battle Core"' in boss or 'BANK("Battle Core")' in boss:
        fail("Boss AI split source must not define or bank into Battle Core")
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
        "GENGAR,     SPELL_TAG, SHADOW_BALL, THUNDERBOLT, DESTINY_BOND, PSYCHIC_M",
        "MAGNETON,   MAGNET, SPIKES, THUNDERBOLT, THUNDER_WAVE, SWIFT",
        "STEELIX,    METAL_COAT, EARTHQUAKE, IRON_TAIL, ROCK_SLIDE, ROAR",
        "SKARMORY,   ROCKY_HELMET, SPIKES, STEEL_WING, TOXIC, WHIRLWIND",
        "GLIGAR,     QUICK_CLAW, SPIKES, EARTHQUAKE, WING_ATTACK, TOXIC",
        "TENTACRUEL, MYSTIC_WATER, RAPID_SPIN, SURF, SLUDGE_BOMB, HAZE",
        "GYARADOS,   LEFTOVERS, DRAGON_DANCE, OUTRAGE, HYDRO_PUMP, HYPER_BEAM",
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
    boss = load_boss_source()
    items = load(ITEMS)
    switch = load(SWITCH)
    wram = load(WRAM)
    parties = load(PARTIES)
    tiers = load(AI_TIERS)
    constants = load(CONSTANTS)
    core = load(CORE)

    audit_revealed_coverage(boss, wram)
    audit_public_threat_keeps_species_fallback(boss)
    audit_switch_loop(boss)
    audit_haki_quarantine(boss)
    audit_revenge_denial_uses_public_seen_species(boss)
    audit_revealed_priority_pressure(boss)
    audit_revealed_protect_commitment_risk(boss)
    audit_revealed_recovery_denial_bias(boss)
    audit_last_move_encore_trap_bias(boss)
    audit_revealed_selfdestruct_protect_bias(boss)
    audit_spikes_and_status(boss)
    audit_setup_and_phazing(boss)
    audit_poison_contact_risk(boss)
    audit_champion_hyper_beam(boss)
    audit_immunity_tiebreak(boss)
    audit_switch_candidate_state_restoration(boss)
    audit_item_and_passive_reasoning(boss)
    audit_baton_pass_requires_living_bench(boss)
    audit_trace_top_moves_preserves_pointer(boss)
    audit_move_model_trace_snapshots(boss, wram)
    audit_boss_move_attr_bank_safety(boss)
    audit_public_threat_scan_preserves_source_pointers(boss)
    audit_type_matchup_scan_preserves_table_cursor(boss)
    audit_type_threat_severity_preserves_list_cursor(boss)
    audit_legacy_switch_state_restoration(items, switch)
    audit_no_battle_core_boss_labels(core, boss)
    audit_priority_trainers(parties, tiers)
    audit_constants(constants)

    print("Boss AI trace invariant audit passed.")
    print("Checked invariants:")
    for name in (
        "per-species revealed coverage",
        "four-revealed-move saturation guards",
        "public threat fallback after revealed-move scan",
        "source-weighted plausible threat confidence",
        "plausible threat source and seen-bench restoration",
        "public perish-count escape switching",
        "A->B->A loop penalty target check",
        "Morty Haki oracle quarantine",
        "public seen-species revenge denial",
        "revealed priority pressure",
        "revealed Protect commitment risk",
        "revealed recovery denial bias",
        "revealed fast Encore avoidance",
        "last-move Encore trap bias",
        "revealed Selfdestruct Protect bias",
        "first-turn Spikes pressure gate",
        "public Rapid Spin risk before extra Spikes",
        "Ghost/Foresight spinblock adjustment",
        "bench revealed Rapid Spin public-memory risk",
        "active species Rapid Spin level-up prior",
        "public status fail gates",
        "public utility fail gates",
        "Disable/Encore public lock fail gates",
        "Mean Look public already-trapped fail gate",
        "Dream Eater public Substitute fail gate",
        "Nightmare public fail gates",
        "Imperial Scales pressure discount",
        "public +2 setup denial",
        "revealed anti-setup avoidance",
        "shared weather setup planning",
        "current non-Ghost Curse setup planning",
        "Spikes/setup projection overread floor",
        "Poison contact retaliation risk",
        "Spikes plus phazing pressure response",
        "Champion non-KO Hyper Beam discouragement",
        "primary-threat immunity pivot tie-break",
        "switch candidate base-data restoration",
        "Destiny Bond public trade-window bias",
        "revealed Destiny Bond KO avoidance",
        "Counter/Mirror Coat public trade-window bias",
        "revealed Counter/Mirror Coat avoidance",
        "Choice first-lock public counterplay risk",
        "Reversal/Flail public HP-band pressure",
        "known item and passive tactical reasoning",
        "Baton Pass living-bench gate",
        "trace top-move pointer preservation",
        "move-model trace score snapshots",
        "Boss AI bank-safe move attr reads",
        "public threat scan source pointer preservation",
        "type-matchup scan table cursor preservation",
        "type-threat severity list cursor preservation",
        "legacy switch base-data restoration",
        "no Battle Core BossAI labels",
    ):
        print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
