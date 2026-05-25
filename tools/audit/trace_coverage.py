"""Information-reveal and no-cheat coverage invariants for the Boss AI.

These audits enforce the "boss wins without cheating" rule: revealed-move
masks must be the source of truth for plausible-type reasoning; the four-
move saturation gate must use exact public effects; the Uniform Haki
oracle must be tier-gated, one-shot, ace-gated, and quarantined from
ordinary policy; revenge-denial must use public seen-species threats only;
revealed effect-matrix dispatch must read only public effects; per-class
role bias is forbidden; and the switch threshold depends only on tier.

File-size justification (>700 hand-written lines per CLAUDE.md): each
`audit_*` here corresponds to a single named invariant in the runner's
"Checked invariants:" output; the body is mostly declarative
`require_order(..., [list of asm needles])` policy strings rather than
branching logic. Further subdividing would either rename the public
invariants (changing audit-doc references and `bug_hunt_triage.py`
diagnostics) or add a sub-runner with no reduction in reader load.

Extracted from `check_boss_ai_trace_invariants.py` per
`audit/non_debugger_code_review_2026-05-26.md` §2 item #8.
"""

from __future__ import annotations

from _common import load
from _trace_helpers import (
    ROOT,
    local_block,
    require_contains,
    require_not_contains,
    require_order,
    top_block,
)


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
            "call BossAI_HakiTrainerEligible",
            "ret nc",
            "call BossAI_CurrentEnemyIsAce",
            "ret nc",
            "set BOSSAI_HAKI_ACE_SEEN_F, [hl]",
            "set BOSSAI_HAKI_ELIGIBLE_F, [hl]",
        ],
        "Uniform Haki first-turn state is trainer-gated and ace-gated",
    )
    gate = top_block(boss, "BossAI_HakiTrainerEligible")
    require_order(
        gate,
        [
            "ld a, [wBossAITier]",
            "cp AI_TIER_EARLY",
            "ld a, [wTrainerClass]",
            "ld hl, BossAIHakiExcludedClasses",
            "scf",
            "ret",
        ],
        "Uniform Haki trainer gate uses tier plus excluded-class table",
    )
    ace = top_block(boss, "BossAI_CurrentEnemyIsAce")
    require_order(
        ace,
        [
            "ld a, [wOTPartyCount]",
            "ld hl, wOTPartyMon1Level",
            "ld bc, PARTYMON_STRUCT_LENGTH",
            "ld a, [wCurOTMon]",
            "cp e",
            "scf",
            "ret",
        ],
        "Uniform Haki ace gate picks the current highest-level trainer party slot",
    )

    oracle = top_block(boss, "BossAI_OracleHakiRead")
    require_order(
        oracle,
        [
            "call BossAI_HakiReadyCommon",
            "ld a, [wEnemyGoesFirst]",
            "ld a, [wBattlePlayerAction]",
            "ld a, [wCurPlayerMove]",
            "call BossAI_HakiFindImmunitySwitch",
            "jp c, BossAI_CommitHakiOracleSwitch",
            "call BossAI_ChooseBestOracleMove",
            "jp BossAI_CommitHakiOracleChoice",
        ],
        "Uniform Haki enemy-first oracle reads committed move, pivots on immunity or jumps to shared move commit",
    )

    after_player = top_block(boss, "BossAI_OracleHakiAfterPlayerAction")
    require_order(
        after_player,
        [
            "ld a, [wBossAITier]",
            "ret z",
            "call BossAI_HakiReadyCommon",
            "ld a, [wBattlePlayerAction]",
            "cp BATTLEPLAYERACTION_SWITCH",
            "ld a, [wCurPlayerMove]",
            "call BossAI_RebuildHakiMoveScores",
            "call BossAI_ChooseBestOracleMove",
            "jp BossAI_CommitHakiOracleChoice",
        ],
        "Uniform Haki player-first hook reads committed move or switch-in before enemy action",
    )
    for needle in (
        ".switch_read",
        "call BossAI_RebuildHakiMoveScores",
    ):
        require_contains(after_player, needle, "Uniform Haki switch-in oracle path")

    reserve = top_block(boss, "BossAI_HakiReserveAceAction")
    require_order(
        reserve,
        [
            "ld a, [wEnemyGoesFirst]",
            "call BossAI_HakiReadyCommon",
            "ld a, [wBattlePlayerAction]",
            "ld a, 1",
            "ret",
        ],
        "Uniform Haki reserves the ace action from ordinary switch/item policy",
    )

    common = top_block(boss, "BossAI_HakiReadyCommon")
    require_order(
        common,
        [
            "ld a, [wBossAITier]",
            "ld hl, wBossAIRevealedMovesBitmapSpare + 1",
            "bit BOSSAI_HAKI_SPENT_F, [hl]",
            "bit BOSSAI_HAKI_ELIGIBLE_F, [hl]",
            "ld a, [wEnemySubStatus5]",
            "callfar CheckEnemyLockedIn",
            "scf",
            "ret",
        ],
        "Uniform Haki shared ready gate is tier-gated, one-shot, and lock-safe",
    )

    rebuild = top_block(boss, "BossAI_RebuildHakiMoveScores")
    require_order(
        rebuild,
        [
            "ld a, 20",
            "ld hl, wEnemyAIMoveScores",
            "ld a, [wEnemyDisabledMove]",
            "ld de, wEnemyMonPP",
            "call BossAI_ApplyMoveModel",
            "call BossAI_ApplyLookaheadToTopMoveCandidates",
        ],
        "Uniform Haki rebuilds move scores after a public switch-in/player action",
    )

    commit = top_block(boss, "BossAI_CommitHakiOracleChoice")
    require_order(
        commit,
        [
            "callfar EnforceEnemyHeldMoveRestrictions_Far",
            "callfar UpdateMoveData",
            "call BossAI_UpdateRepeatTracker",
            "call BossAI_MarkScoutedIfScoutMove",
            "call BossAI_QueueHakiTaunt",
            "set BOSSAI_HAKI_SPENT_F, [hl]",
        ],
        "Uniform Haki shared commit queues taunt, spends Haki, and refreshes move data",
    )
    for needle in (
        "ld a, [wCurPlayerMove]",
        "or 1 << BOSSAI_HAKI_TRACE_FIRED_F",
        "ld [wBossAITraceChosenMove], a",
    ):
        haystack = oracle + "\n" + after_player + "\n" + commit
        require_contains(haystack, needle, "Uniform Haki quarantine trace/input boundary")

    pivot = top_block(boss, "BossAI_HakiFindImmunitySwitch")
    require_order(
        pivot,
        [
            "ld a, [wCurPlayerMove]",
            "ld hl, Moves + MOVE_TYPE",
            "call BossAI_GetMoveAttr",
            "ld a, [wEnemyMonSpecies]",
            "call BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem",
            "ld a, [wTypeMatchup]",
            "jr z, .none",
            "ld a, [wOTPartyCount]",
            "ld hl, wOTPartyMon1HP",
            "ld hl, wOTPartySpecies",
            "call BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem",
            "jr z, .found",
        ],
        "Uniform Haki defensive pivot reads locked move type and walks the bench for an immunity",
    )

    switch_commit = top_block(boss, "BossAI_CommitHakiOracleSwitch")
    require_order(
        switch_commit,
        [
            "ld a, [wBossAITemp]",
            "ld [wEnemySwitchMonIndex], a",
            "call BossAI_QueueHakiTaunt",
            "set BOSSAI_HAKI_SPENT_F, [hl]",
            "jp AI_TrySwitch",
        ],
        "Uniform Haki switch commit queues taunt, spends Haki, and tail-calls AI_TrySwitch",
    )


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


def audit_revealed_effect_matrix_bias(boss: str) -> None:
    score = top_block(boss, "BossAI_ApplyMoveModel")
    require_order(
        score,
        [
            "call .ApplyCounterCoatTradeBias",
            "call .ApplyRevealedEffectMatrixBias",
            "call .ApplyChoiceFirstLockRegret",
            "call .ApplySelfKOTradeDiscipline",
            "call BossAI_ApplyScoutMoveBias",
        ],
        "revealed-effect matrix runs before scout/repeat cleanup",
    )

    matrix = local_block(boss, ".ApplyRevealedEffectMatrixBias", ".CandidateMoveMatchupVsBaseTypes")
    require_order(
        matrix,
        [
            "ld hl, BossAIRevealedEffectMatrix",
            "ld [wBossAITemp], a",
            "ld [wBossAITemp2], a",
            "ld [wBossAITemp3], a",
            "call .MatrixCandidateMatchesA",
            "call .MatrixRevealedKeyMatchesA",
            "call .MatrixApplyRuleA",
        ],
        "revealed-effect matrix dispatch reads table rows into scratch and applies matching rules",
    )
    require_order(
        matrix,
        [
            ".MatrixCandidateMatchesA",
            "BOSS_AI_REM_GROUP_STATUS_DENIAL",
            "BOSS_AI_REM_GROUP_COMMITMENT",
            "BOSS_AI_REM_GROUP_SLEEP_PREEMPT",
            "BOSS_AI_REM_GROUP_DAMAGING",
            "BOSS_AI_REM_GROUP_PHYSICAL_DAMAGE",
            "BOSS_AI_REM_GROUP_SPECIAL_DAMAGE",
            "wEnemyMoveStruct + MOVE_EFFECT",
            "wEnemyMoveStruct + MOVE_POWER",
            "call BossAI_CurrentEnemyMoveCategory",
        ],
        "matrix candidate keys are current boss move effect/category only",
    )
    require_order(
        matrix,
        [
            ".MatrixRevealedKeyMatchesA",
            "BOSS_AI_REM_GROUP_RECOVERY",
            "jp z, .PlayerHasRevealedRecovery",
            "BOSS_AI_REM_GROUP_LAST_MOVE_ENCORE_TRAP",
            "jp z, .LastPlayerMoveIsEncoreTrap",
            "jp .PlayerHasRevealedEffectA",
        ],
        "matrix revealed keys use exact public revealed effects or public last move",
    )
    require_order(
        matrix,
        [
            ".MatrixRecoveryStatusDenial",
            "call .MatrixRequireMidTier",
            "call AICheckPlayerMaxHP_HL",
            "call .HasKOLine",
            "call .StatusMoveWouldFailPublicly",
            "jp .MatrixEncourageScore",
            ".MatrixRecoveryUtilityDenial",
            "call .UtilityMoveWouldFailPublicly",
        ],
        "matrix recovery denial keeps public tier/HP/KO/fail gates",
    )
    require_order(
        matrix,
        [
            ".MatrixFastEncoreAvoidance",
            "wPlayerSubStatus5",
            "SUBSTATUS_ENCORED",
            "call BossAI_PublicEnemyFaster",
            "jr .MatrixDiscourageScore",
            ".MatrixLastMoveEncoreTrap",
            "call .UtilityMoveWouldFailPublicly",
            "call BossAI_PublicEnemyFaster",
            "jr .MatrixEncourageScore",
        ],
        "matrix Encore rows keep public lock/speed/fail gates",
    )
    require_order(
        matrix,
        [
            ".MatrixSelfdestructProtect",
            "call .UtilityMoveWouldFailPublicly",
            "call AICheckPlayerHalfHP_HL",
            "call BossAI_HasAnyKOMove",
            "jr .MatrixEncourageScore",
            ".MatrixSleepPreempt",
            "wEnemyMonStatus",
            "SLP_MASK",
            "call BossAI_PublicEnemyFaster",
        ],
        "matrix self-KO and sleep-preempt rows keep public gates",
    )
    require_order(
        matrix,
        [
            ".MatrixDestinyBondAvoidance",
            "call BossAI_HasAnyKOMove",
            "call AICheckPlayerQuarterHP_HL",
            "call BossAI_PublicEnemyFaster",
            "jr .MatrixDiscourageScore",
            ".MatrixCounterCoatAvoidance",
            "call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem",
            "wTypeMatchup",
        ],
        "matrix Destiny Bond and Counter/Mirror Coat avoidance keep public gates",
    )
    require_order(
        matrix,
        [
            ".MatrixLoadScorePtrHL",
            "wBossAIScorePtr",
            "wBossAIScorePtr + 1",
        ],
        "matrix score updates reload the score pointer instead of depending on row-pointer hl",
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

    encore_commitment = local_block(
        boss,
        ".EncorePunishableCommitmentMove",
        ".LastPlayerMoveIsEncoreTrap",
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

    matrix_data = load(ROOT / "data" / "boss_ai" / "revealed_effect_matrix.asm")
    required_rows = (
        "db EFFECT_PROTECT, EFFECT_SELFDESTRUCT, BOSS_AI_REM_RULE_DISCOURAGE, 10",
        "db EFFECT_PROTECT, EFFECT_HYPER_BEAM, BOSS_AI_REM_RULE_DISCOURAGE, 4",
        "db BOSS_AI_REM_GROUP_RECOVERY, BOSS_AI_REM_GROUP_STATUS_DENIAL, BOSS_AI_REM_RULE_RECOVERY_STATUS_DENIAL, 4",
        "db BOSS_AI_REM_GROUP_RECOVERY, EFFECT_FORCE_SWITCH, BOSS_AI_REM_RULE_RECOVERY_UTILITY_DENIAL, 3",
        "db EFFECT_ENCORE, BOSS_AI_REM_GROUP_COMMITMENT, BOSS_AI_REM_RULE_FAST_ENCORE_AVOIDANCE, 5",
        "db BOSS_AI_REM_GROUP_LAST_MOVE_ENCORE_TRAP, EFFECT_ENCORE, BOSS_AI_REM_RULE_LAST_MOVE_ENCORE_TRAP, 6",
        "db EFFECT_SELFDESTRUCT, EFFECT_PROTECT, BOSS_AI_REM_RULE_SELFDESTRUCT_PROTECT, 5",
        "db EFFECT_SLEEP, BOSS_AI_REM_GROUP_SLEEP_PREEMPT, BOSS_AI_REM_RULE_SLEEP_PREEMPT, 5",
        "db EFFECT_DESTINY_BOND, BOSS_AI_REM_GROUP_DAMAGING, BOSS_AI_REM_RULE_DESTINY_BOND_AVOIDANCE, 7",
        "db EFFECT_COUNTER, BOSS_AI_REM_GROUP_PHYSICAL_DAMAGE, BOSS_AI_REM_RULE_COUNTERCOAT_AVOIDANCE, 5",
        "db EFFECT_MIRROR_COAT, BOSS_AI_REM_GROUP_SPECIAL_DAMAGE, BOSS_AI_REM_RULE_COUNTERCOAT_AVOIDANCE, 5",
    )
    for row in required_rows:
        require_contains(matrix_data, row, "revealed-effect matrix row coverage")


def audit_revealed_protect_commitment_risk(boss: str) -> None:
    audit_revealed_effect_matrix_bias(boss)


def audit_revealed_recovery_denial_bias(boss: str) -> None:
    audit_revealed_effect_matrix_bias(boss)


def audit_last_move_encore_trap_bias(boss: str) -> None:
    audit_revealed_effect_matrix_bias(boss)


def audit_revealed_selfdestruct_protect_bias(boss: str) -> None:
    audit_revealed_effect_matrix_bias(boss)


def audit_tier_only_switch_threshold(boss: str) -> None:
    block = top_block(boss, "BossAI_GetSwitchThreshold")
    require_order(
        block,
        [
            "ld a, [wBossAITier]",
            "cp AI_TIER_LATE",
            "ld a, AI_SWITCH_THRESHOLD_LATE",
            "jr z, .base_done",
            "ld a, [wBossAITier]",
            "cp AI_TIER_MID",
            "ld a, AI_SWITCH_THRESHOLD_MID",
            "jr z, .base_done",
            "ld a, AI_SWITCH_THRESHOLD_EARLY",
            ".base_done",
            "ret",
        ],
        "switch threshold must depend only on boss tier",
    )
    for needle in ("wTrainerClass", "ApplyClassSwitchThresholdMod"):
        require_not_contains(block, needle, "switch threshold must not use per-class bias")


def audit_no_per_class_role_bias(boss: str) -> None:
    for needle in (
        "call .ApplyRoleBias",
        ".ApplyRoleBias",
        ".EncourageIfType",
        ".EncourageIfEffectInArray",
        "RoleEffects:",
    ):
        require_not_contains(boss, needle, "per-class role bias must be removed")
