"""Tactical scoring biases and switch-loop policy for the Boss AI.

These audits enforce tactical move-scoring invariants: switch-loop A->B->A
penalty narrow emergency exceptions; Spikes pressure and Rapid Spin risk
chains; public status / utility fail gates and Curse / Pain Split hard
gates; setup punish and phazing bias; revealed anti-setup avoidance;
Poison contact retaliation risk; primary-threat immunity tie-break;
known item / passive reasoning (held effects, Reversal HP bands, Choice
locks); and Baton Pass living-bench gate.

File-size justification (>700 hand-written lines per CLAUDE.md): each
`audit_*` here corresponds to a single named invariant in the runner's
"Checked invariants:" output; the body is mostly declarative
`require_order(..., [list of asm needles])` policy strings rather than
branching logic, with `audit_spikes_and_status` and
`audit_item_and_passive_reasoning` being intrinsically large policy
bundles. Further subdividing would either rename the public invariants
(changing audit-doc references and `bug_hunt_triage.py` diagnostics) or
add a sub-runner with no reduction in reader load.

Extracted from `check_boss_ai_trace_invariants.py` per
`audit/non_debugger_code_review_2026-05-26.md` §2 item #8.
"""

from __future__ import annotations

import re

from _common import fail
from _trace_helpers import (
    first_add_value,
    local_block,
    require_contains,
    require_not_contains,
    require_order,
    top_block,
)


def audit_switch_loop(boss: str) -> None:
    switch_entry = top_block(boss, "BossAI_SwitchOrTryItem")
    require_order(
        switch_entry,
        [
            "call BossAI_SelectPlanIfNeeded",
            "call BossAI_ComputePlayerPlausibleTypeMask",
            "call BossAI_OracleHakiRead",
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

    dispatch = top_block(boss, "BossAI_SwitchOrTryItem")
    require_order(
        dispatch,
        [
            "call BossAI_RefineSwitchCandidateForPlausibleRisk",
            "call BossAI_GetPrimaryThreatType",
            "jr nc, .candidate_answers_threat",
            "call BossAI_IsImmunityPivotOpportunity",
            "jr c, .candidate_answers_threat",
            "xor a",
            "ld [wEnemySwitchMonParam], a",
            "jp AI_TryItem",
            ".candidate_answers_threat",
            "ld a, [wEnemySwitchMonParam]",
            "and a",
            "jp z, AI_TryItem",
            "push af",
            "call BossAI_ComputeSwitchConfidence",
        ],
        "switch target must answer public primary threat before confidence roll",
    )

    answer = top_block(boss, "BossAI_IsImmunityPivotOpportunity")
    require_order(
        answer,
        [
            "call BossAI_GetPrimaryThreatType",
            "ret nc",
            "ld [wBossAITemp], a",
            "ld a, [wEnemySwitchMonParam]",
            "and $f",
            "ld hl, wOTPartySpecies",
            "call GetBaseData",
            "ld a, [wBossAITemp]",
            "call BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem",
            "ld a, [wTypeMatchup]",
            "cp EFFECTIVE",
            "jr nc, .not_immune",
        ],
        "switch target answer gate must require resistance/immunity to primary threat",
    )

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
            "ld a, 10",
            "call BossAI_DiscourageScoreHL",
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

    species_spin = local_block(boss, ".SpeciesLevelUpHasRapidSpin", ".EncourageByTierWeight")
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
            "call .HeldItemMoveBlocked",
            "ret c",
            "call .DamagingMoveBlockedByTypeImmunity",
            "ret c",
            "call .GhostCurseBlockedPublicly",
            "ret c",
            "call .PainSplitBlockedPublicly",
            "ret c",
            "ld a, [wEnemyMoveStruct + MOVE_POWER]",
        ],
        "Ghost Curse and Pain Split hard-block before scoring biases",
    )
    require_order(
        move_model,
        [
            "call .UtilityMoveWouldFailPublicly",
            "jr nc, .skip_utility_fail",
            "ld a, 24",
            "call BossAI_DiscourageScoreHL",
            "call .StatusMoveWouldFailPublicly",
            "jr nc, .status_ok",
            "ld a, 80",
            "call BossAI_SetScoreHL",
            ".status_ok",
            "ld c, 4",
            "call .EncourageByTierWeight",
        ],
        "public status fail blocking before generic encouragement",
    )

    utility = local_block(boss, ".UtilityMoveWouldFailPublicly", ".early_stat_drop_discipline")
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
    curse = local_block(boss, ".GhostCurseBlockedPublicly", ".PainSplitBlockedPublicly")
    require_order(
        curse,
        [
            "ld a, [wEnemyMoveStruct + MOVE_EFFECT]",
            "cp EFFECT_CURSE",
            "jr nz, .ghost_curse_ok",
            "call BossAI_EnemyIsGhostType",
            "jr nc, .ghost_curse_ok",
            "ld a, [wPlayerSubStatus4]",
            "bit SUBSTATUS_SUBSTITUTE, a",
            "jr nz, .ghost_curse_block",
            "ld a, [wPlayerSubStatus1]",
            "bit SUBSTATUS_CURSE, a",
            "jr nz, .ghost_curse_block",
            ".ghost_curse_check_self_ko",
            "call AICheckEnemyHalfHP_HL",
            "jr c, .ghost_curse_ok",
            "call .PlayerCantActThisTurnPublicly",
            "jr c, .ghost_curse_block",
            "call .EnemyUnderPressure",
            "jr c, .ghost_curse_ok",
            ".ghost_curse_block",
            "ld a, 80",
            "call BossAI_SetScoreHL",
            "scf",
        ],
        "Ghost Curse public duplicate and self-KO hard fail gate",
    )
    pain_split = local_block(boss, ".PainSplitBlockedPublicly", ".early_stat_drop_discipline")
    require_order(
        pain_split,
        [
            ".PainSplitBlockedPublicly",
            "ld a, [wEnemyMoveStruct + MOVE_EFFECT]",
            "cp EFFECT_PAIN_SPLIT",
            "jr nz, .pain_split_ok",
            "call BossAI_HasAnyKOMove",
            "jr c, .pain_split_block",
            "call .PainSplitHasLargePositiveGap",
            "jr c, .pain_split_ok",
            ".pain_split_block",
            "ld a, 80",
            "call BossAI_SetScoreHL",
            "scf",
        ],
        "Pain Split public value hard gate",
    )
    pain_split_gap = local_block(boss, ".PainSplitHasLargePositiveGap", ".PlayerCantActThisTurnPublicly")
    require_order(
        pain_split_gap,
        [
            ".PainSplitHasLargePositiveGap",
            "ld hl, wEnemyMonHP",
            "sla c",
            "rl b",
            "ld hl, wBattleMonHP + 1",
            "cp c",
            "sbc b",
            "jr c, .pain_split_gap_no",
            "scf",
        ],
        "Pain Split requires player HP at least twice enemy HP",
    )
    player_cant_act = local_block(boss, ".PlayerCantActThisTurnPublicly", ".early_stat_drop_discipline")
    require_order(
        player_cant_act,
        [
            ".PlayerCantActThisTurnPublicly",
            "ld a, [wBattleMonStatus]",
            "and SLP_MASK",
            "jr nz, .player_cant_act",
            "ld a, [wBattleMonStatus]",
            "bit FRZ, a",
            "jr nz, .player_cant_act",
            ".player_cant_act",
            "scf",
        ],
        "Ghost Curse self-KO gate treats sleeping/frozen player as no immediate pressure",
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
            "call .ApplyCounterCoatTradeBias",
            "call .ApplyRevealedEffectMatrixBias",
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

    # BossAI_PublicEnemyFaster is now a thin per-tick cache wrapper around
    # BossAI_PublicEnemyFasterUncached (same pattern as
    # BossAI_PlayerHasPublicThreatVsEnemy / *Uncached at line 357). Inspect
    # the Uncached body for the Choice Scarf model.
    speed = top_block(boss, "BossAI_PublicEnemyFasterUncached")
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

    destiny = local_block(move_model, ".ApplyDestinyBondTradeBias", ".ApplyCounterCoatTradeBias")
    require_order(
        destiny,
        [
            "EFFECT_DESTINY_BOND",
            "wBossAITier",
            "AI_TIER_MID",
            "call AICheckEnemyQuarterHP",
            # Use BossAI_HasAnyKOMove (whole-moveset scan), not .HasKOLine which
            # only checks the currently-scored move's KO pressure — DB has
            # MOVE_POWER = 0 so .HasKOLine always reports "no KO".
            "call BossAI_HasAnyKOMove",
            "call BossAI_PlayerHasPublicThreatVsEnemy",
            "call BossAI_PublicEnemyFaster",
            "call .EncourageByTierWeight",
            "jp BossAI_EncourageScoreHL",
        ],
        "Destiny Bond public trade-window gates",
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

    countercoat_seen = local_block(move_model, ".PlayerHasRevealedCounterCoatCategory", ".ApplyChoiceFirstLockRegret")
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
            "call .ApplyRevealedEffectMatrixBias",
            "call .ApplyChoiceFirstLockRegret",
        ],
        "revealed Counter/Mirror Coat avoidance hook routes through matrix",
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
