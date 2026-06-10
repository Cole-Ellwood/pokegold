from __future__ import annotations

import json
from argparse import Namespace
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError
from tools.trace import boss_ai_trace_capture as capture
from tools.trace import runtime as trace_runtime

from .canonical_classes import build_rom_contribution_trace_class, canonical_class_fields
from .rule_map import build_rule_map


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROM_CONTRIBUTION_TRACE_PATH = (
    ROOT / "audit" / "boss_ai_debugger" / "rom_contribution_trace_smoke.json"
)
DEFAULT_ROM_CONTRIBUTION_TRACE_PROBE_PATH = (
    ROOT / "audit" / "boss_ai_debugger" / "rom_contribution_trace_spikes_spin_probe.json"
)
DEFAULT_ROM_CONTRIBUTION_TRACE_DIR = ROOT / "audit" / "boss_ai_debugger"
DEFAULT_ROM_CONTRIBUTION_TRACE_GLOB = "rom_contribution_trace_*.json"
DEFAULT_ROM_CONTRIBUTION_TRACE_SOURCES = (
    (DEFAULT_ROM_CONTRIBUTION_TRACE_DIR, DEFAULT_ROM_CONTRIBUTION_TRACE_GLOB),
    (
        ROOT
        / "audit"
        / "boss_ai_debugger"
        / "god_level_benchmark"
        / "artifacts"
        / "changed_ai_rom_contribution_routes",
        "*.json",
    ),
)

MAX_REPLAY_POLL_CHUNK_FRAMES = 45
PARTY_LENGTH = 6
PARTYMON_STRUCT_LENGTH = 48

PUBLIC_INPUT_SNAPSHOT_WIDTHS = {
    "wPlayerScreens": 1,
    "wEnemyScreens": 1,
    "wPlayerUsedMoves": 4,
    "wEnemyMonType1": 1,
    "wEnemyMonType2": 1,
    "wEnemySubStatus1": 1,
    "wOTPartyCount": 1,
    "wOTPartySpecies": PARTY_LENGTH + 1,
    "wBossAITier": 1,
    "wBossAISeenPlayerSpeciesCount": 1,
    "wBossAISeenPlayerSpecies": PARTY_LENGTH,
    "wBossAISeenPlayerAliveMask": 1,
    "wBossAISpeciesUsedMoves": PARTY_LENGTH * 4,
    "wBattleMonSpecies": 1,
    "wBattleMonItem": 1,
    "wBattleMonHP": 2,
    "wBattleMonMaxHP": 2,
    "wEnemyMonMoves": 4,
    "wBattleMonLevel": 1,
    "wPlayerSubStatus1": 1,
    "wPlayerSubStatus4": 1,
    "wBattleMonType1": 1,
    "wBattleMonType2": 1,
    "wBattleWeather": 1,
    "wEnemyMoveStructAnimation": 1,
    "wEnemyMoveStructEffect": 1,
    "wEnemyMoveStructPower": 1,
    "wEnemyMoveStructType": 1,
    "wEnemyMoveStructAccuracy": 1,
    "wEnemySubStatus3": 1,
    "wEnemySubStatus4": 1,
    "wEnemyMonHP": 2,
    "wEnemyMonMaxHP": 2,
    "wEnemyMonStatus": 1,
    "wEnemyMonSpecies": 1,
    "wTempEnemyMonSpecies": 1,
    "wEnemyMonLevel": 1,
    "wEnemyMonItem": 1,
    "wEnemyAtkLevel": 1,
    "wEnemySAtkLevel": 1,
    "wEnemyMetronomeCount": 1,
    "wEnemyChoiceLockedMove": 1,
    "wEnemySleepClauseSlot": 1,
    "wPlayerDisableCount": 1,
    "wPlayerStatLevels": 7,
    "wPlayerDefLevel": 1,
    "wPlayerSDefLevel": 1,
    "wBattleMonStatus": 1,
    "wEnemyStatLevels": 7,
    "wBossAISwitchCooldown": 1,
    "wBossAITurnsElapsed": 1,
    "wBossAIPlayerSwitchCount": 1,
    "wBossAIPlanId": 1,
    "wBossAIPlanPhase": 1,
    "wBossAIPlanConfidence": 1,
    "wBossAIWinconMonIdx": 1,
    "wBossAIPublicThreatCache": 1,
    "wBossAIRevealedPriorityCache": 1,
    "wBossAIPrimaryThreatCache": 1,
    "wBossAIPublicEnemyFasterCache": 1,
    "wBossAILookaheadDepthCache": 1,
    "wBossAIPlausibleTypeMaskCache": 4,
    "wBossAILikelyTypeMaskCache": 4,
    "wBossAIRevealedMovesBitmap": PARTY_LENGTH * 4,
    "wBossAITemp": 1,
    "wBossAITemp2": 1,
    "wBossAITemp3": 1,
    "wBossAITemp4": 1,
    "wBossAITemp5": 1,
    "wTypeMatchup": 1,
    "wCurOTMon": 1,
    "wCurSpecies": 1,
    "wCurPartySpecies": 1,
    "wPlayerDarkShieldConsumed": 1,
    "wOTPartyMon1Status": PARTY_LENGTH,
    "wLastPlayerCounterMove": 1,
    "wLastPlayerMove": 1,
}

STATIC_PUBLIC_TABLE_SYMBOLS = {
    "AdaptiveLeadMap": "AdaptiveLeadMap",
    "BaseData": "BaseData",
    "EvosAttacks": "EvosAttacksPointers",
    "Moves + MOVE_EFFECT": "Moves",
    "Moves + MOVE_POWER": "Moves",
    "Moves + MOVE_TYPE": "Moves",
    "MoveContactFlags": "MoveContactFlags",
    "StatLevelMultipliers": "StatLevelMultipliers",
    "TypeBoostItems": "TypeBoostItems",
}

REGISTER_PUBLIC_INPUTS = {
    "register:A": "A",
    "register:B": "B",
    "register:C": "C",
    "register:D": "D",
    "register:E": "E",
}

SCORE_HELPERS = {
    "BossAI_ApplyMoveModel.EncourageScoreByA": "encourage_tier_weight",
    "BossAI_ApplyMoveModel.DiscourageScoreByA": "discourage_tier_weight",
    "BossAI_SetScoreHL": "set_score",
    "BossAI_EncourageScoreHL": "encourage_score",
    "BossAI_DiscourageScoreHL": "discourage_score",
    "BossAI_ApplySignedDeltaToScore": "apply_signed_lookahead_delta",
}

POINTER_FROM_WRAM_SCORE_PTR = {
    "BossAI_SetScoreHL",
    "BossAI_EncourageScoreHL",
    "BossAI_DiscourageScoreHL",
}

CONTROL_HOOKS = {
    "MaybePickAdaptiveEnemyLead": "adaptive_lead_start",
    "BossAI_ApplyMoveModel.ScoreMove": "candidate_start",
    # The post-model trace recorder lives in the floating "Boss AI Trace"
    # section (engine/battle/ai/boss_trace_topmoves.asm) and is farcalled once
    # per move candidate, scored or not — same firing semantics as the old
    # inline BossAI_ApplyMoveModel.TracePostModelScore local label.
    "BossAI_TraceRecordPostModelScore": "candidate_end",
    "BossAI_SelectMove.first_pass": "selector_start",
}

SWITCH_DECISION_FIELDS = (
    "wBossAITraceSwitchConfidence",
    "wEnemySwitchMonParam",
    "wEnemySwitchMonIndex",
)

DIRECT_SCORE_WRITE_RULE_IDS = {
    "ko_band_oracle.apply_damage_dominance_bias",
}

PREDICATE_BRANCH_HOOKS = {
    "MaybePickAdaptiveEnemyLead.enabled": {
        "predicate_id": "adaptive_lead_trainer_match",
        "outcome": "enabled",
        "parent_symbol": "MaybePickAdaptiveEnemyLead.ShouldUseAdaptiveLeadForTrainer",
        "legal_inputs": (
            "wOtherTrainerClass",
            "wOtherTrainerID",
            "AdaptiveLeadMap",
        ),
    },
    "MaybePickAdaptiveEnemyLead.loop": {
        "predicate_id": "adaptive_lead_trainer_match",
        "outcome": "disabled",
        "parent_symbol": "MaybePickAdaptiveEnemyLead.ShouldUseAdaptiveLeadForTrainer",
        "legal_inputs": (
            "wOtherTrainerClass",
            "wOtherTrainerID",
            "AdaptiveLeadMap",
        ),
        "condition": "hl_points_to_zero_byte",
    },
    "MaybePickAdaptiveEnemyLead.first_found": {
        "predicate_id": "adaptive_lead_first_alive_party_mon",
        "outcome": "found",
        "parent_symbol": "MaybePickAdaptiveEnemyLead.FindFirstAliveOTMon",
        "legal_inputs": ("wOTPartyCount", "wOTPartyMon1HP"),
    },
    "MaybePickAdaptiveEnemyLead.next_found": {
        "predicate_id": "adaptive_lead_next_alive_party_mon",
        "outcome": "found",
        "parent_symbol": "MaybePickAdaptiveEnemyLead.FindNextAliveOTMon",
        "legal_inputs": ("wOTPartyCount", "wOTPartyMon1HP"),
    },
    "MaybePickAdaptiveEnemyLead.none_found": {
        "predicate_id": "adaptive_lead_alive_party_mon",
        "outcome": "not_found",
        "parent_symbol": "$active_frame",
        "legal_inputs": ("wOTPartyCount", "wOTPartyMon1HP"),
    },
    "BossAI_ShouldRespectPotentialPlayerRevenge.seen_yes": {
        "predicate_id": "known_seen_revenge_threat",
        "outcome": "seen_revenge_threat",
        "parent_symbol": "BossAI_ShouldRespectPotentialPlayerRevenge.KnownSeenRevengeThreat",
        "legal_inputs": (
            "wBossAITier",
            "wBossAISeenPlayerSpeciesCount",
            "wBossAISeenPlayerSpecies",
            "wBossAISeenPlayerAliveMask",
            "wBattleMonSpecies",
            "wBattleMonType1",
            "wBattleMonType2",
            "wBossAISpeciesUsedMoves",
        ),
    },
    "BossAI_SwitchCandidateLowHPBlock.at_quarter": {
        "predicate_id": "switch_candidate_low_hp",
        "outcome": "at_or_below_quarter",
        "parent_symbol": "BossAI_SwitchCandidateLowHPBlock",
        "legal_inputs": ("wEnemySwitchMonParam", "wOTPartyMon1HP"),
    },
    "BossAI_CandidateImmuneToPlayerSTAB.immune_yes": {
        "predicate_id": "candidate_immune_to_player_stab",
        "outcome": "immune",
        "parent_symbol": "BossAI_CandidateImmuneToPlayerSTAB",
        "legal_inputs": (
            "wEnemySwitchMonParam",
            "wOTPartySpecies",
            "wBattleMonType1",
            "wBattleMonType2",
            "BaseData",
        ),
    },
    "BossAI_ApplyMoveModel.PlayerHasRevealedEffectA": {
        "predicate_id": "player_revealed_effect_scan",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasRevealedEffectA",
        "legal_inputs": ("wPlayerUsedMoves", "Moves + MOVE_EFFECT"),
    },
    "BossAI_HasRevealedSuperEffectiveMove": {
        "predicate_id": "revealed_super_effective_move",
        "outcome": "entered",
        "parent_symbol": "BossAI_HasRevealedSuperEffectiveMove",
        "legal_inputs": (
            "wBattleMonSpecies",
            "wBossAISeenPlayerSpecies",
            "wBossAISpeciesUsedMoves",
            "wEnemyMonType1",
            "wEnemyMonType2",
        ),
    },
    "BossAI_PlayerHasRevealedPriorityThreat": {
        "predicate_id": "revealed_priority_threat",
        "outcome": "entered",
        "parent_symbol": "BossAI_PlayerHasRevealedPriorityThreat",
        "legal_inputs": (
            "wPlayerUsedMoves",
            "Moves + MOVE_EFFECT",
            "wEnemyMonType1",
            "wEnemyMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.ApplyRapidSpinBias": {
        "predicate_id": "rapid_spin_bias_public_gate",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyRapidSpinBias",
        "legal_inputs": ("wEnemyScreens", "Moves + MOVE_EFFECT"),
    },
    "BossAI_ApplyMoveModel.ApplyRevealedAntiSetupAvoidance": {
        "predicate_id": "revealed_anti_setup_avoidance",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyRevealedAntiSetupAvoidance",
        "legal_inputs": ("wBossAITier", "wPlayerUsedMoves", "Moves + MOVE_EFFECT"),
    },
    "BossAI_ApplyMoveModel.ApplyRevealedEffectMatrixBias": {
        "predicate_id": "revealed_effect_matrix_bias",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyRevealedEffectMatrixBias",
        "legal_inputs": ("wBossAITier", "wPlayerUsedMoves", "Moves + MOVE_EFFECT"),
    },
    "BossAI_ApplyMoveModel.spikes_layer1": {
        "predicate_id": "spikes_existing_layer_count",
        "outcome": "zero_existing_layers",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayerBias",
        "legal_inputs": ("wPlayerScreens",),
    },
    "BossAI_ApplyMoveModel.spikes_layer2": {
        "predicate_id": "spikes_existing_layer_count",
        "outcome": "one_existing_layer",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayerBias",
        "legal_inputs": ("wPlayerScreens",),
    },
    "BossAI_ApplyMoveModel.spikes_layer3": {
        "predicate_id": "spikes_existing_layer_count",
        "outcome": "two_existing_layers",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayerBias",
        "legal_inputs": ("wPlayerScreens",),
    },
    "BossAI_ApplyMoveModel.spikes_l2_no_revealed_spin": {
        "predicate_id": "active_revealed_rapid_spin",
        "outcome": "not_revealed_for_layer2",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayerBias",
        "legal_inputs": ("wPlayerUsedMoves",),
    },
    "BossAI_ApplyMoveModel.spikes_l3_no_revealed_spin": {
        "predicate_id": "active_revealed_rapid_spin",
        "outcome": "not_revealed_for_layer3",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayerBias",
        "legal_inputs": ("wPlayerUsedMoves",),
    },
    "BossAI_ApplyMoveModel.revealed_spin_not_blocked": {
        "predicate_id": "revealed_rapid_spin_active_spinblock",
        "outcome": "not_blocked",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyRevealedRapidSpinSpikesRisk",
        "legal_inputs": (
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemySubStatus1",
        ),
    },
    "BossAI_ApplyMoveModel.revealed_spin_soft": {
        "predicate_id": "revealed_rapid_spin_spikes_risk",
        "outcome": "softened_by_spinblock_context",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyRevealedRapidSpinSpikesRisk",
        "legal_inputs": (
            "wPlayerUsedMoves",
            "wEnemySubStatus1",
            "wOTPartySpecies",
            "wOTPartyMon1HP",
        ),
    },
    "BossAI_ApplyMoveModel.spikes_l2_soft_spin_risk": {
        "predicate_id": "layer2_unrevealed_spin_risk",
        "outcome": "soft_penalty",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayer2UnrevealedSpinRisk",
        "legal_inputs": (
            "wBossAISeenPlayerSpecies",
            "wBossAISpeciesUsedMoves",
            "wBattleMonSpecies",
            "wBattleMonLevel",
            "EvosAttacks",
        ),
    },
    "BossAI_ApplyMoveModel.spikes_l3_soft_spin_risk": {
        "predicate_id": "layer3_unrevealed_spin_risk",
        "outcome": "active_species_prior_or_late_game",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayer3UnrevealedSpinRisk",
        "legal_inputs": (
            "wBattleMonSpecies",
            "wBattleMonLevel",
            "wBossAITier",
            "EvosAttacks",
        ),
    },
    "BossAI_ApplyMoveModel.spikes_l3_bench_spin_risk": {
        "predicate_id": "layer3_seen_bench_revealed_spin",
        "outcome": "bench_spinner_seen_alive",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayer3UnrevealedSpinRisk",
        "legal_inputs": (
            "wBossAISeenPlayerSpecies",
            "wBossAISeenPlayerAliveMask",
            "wBossAISpeciesUsedMoves",
        ),
    },
    "BossAI_ApplyMoveModel.enemy_not_spinblocking": {
        "predicate_id": "enemy_active_spinblock",
        "outcome": "not_spinblocking",
        "parent_symbol": "BossAI_ApplyMoveModel.EnemyActiveBlocksRapidSpin",
        "legal_inputs": (
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemySubStatus1",
        ),
    },
    "BossAI_ApplyMoveModel.reserve_ghost_yes_pop": {
        "predicate_id": "boss_reserve_spinblock",
        "outcome": "available",
        "parent_symbol": "BossAI_ApplyMoveModel.BossHasAvailableReserveGhost",
        "legal_inputs": (
            "wOTPartySpecies",
            "wOTPartyMon1HP",
            "BaseData",
        ),
    },
    "BossAI_ApplyMoveModel.reserve_ghost_no": {
        "predicate_id": "boss_reserve_spinblock",
        "outcome": "unavailable",
        "parent_symbol": "BossAI_ApplyMoveModel.BossHasAvailableReserveGhost",
        "legal_inputs": (
            "wOTPartyCount",
            "wOTPartySpecies",
            "wOTPartyMon1HP",
            "BaseData",
        ),
    },
    "BossAI_ApplyMoveModel.bench_spin_yes_pop": {
        "predicate_id": "seen_bench_revealed_rapid_spin",
        "outcome": "found",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasSeenBenchRevealedRapidSpin",
        "legal_inputs": (
            "wBossAISeenPlayerSpecies",
            "wBossAISeenPlayerAliveMask",
            "wBossAISpeciesUsedMoves",
        ),
    },
    "BossAI_ApplyMoveModel.bench_spin_no": {
        "predicate_id": "seen_bench_revealed_rapid_spin",
        "outcome": "not_found",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasSeenBenchRevealedRapidSpin",
        "legal_inputs": (
            "wBossAISeenPlayerSpecies",
            "wBossAISeenPlayerAliveMask",
            "wBossAISpeciesUsedMoves",
        ),
    },
    "BossAI_ApplyMoveModel.active_spin_yes": {
        "predicate_id": "active_species_levelup_rapid_spin_prior",
        "outcome": "can_learn",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerActiveLikelyCanRapidSpin",
        "legal_inputs": (
            "wBattleMonSpecies",
            "wBattleMonLevel",
            "EvosAttacks",
        ),
    },
    "BossAI_ApplyMoveModel.active_spin_no": {
        "predicate_id": "active_species_levelup_rapid_spin_prior",
        "outcome": "cannot_infer",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerActiveLikelyCanRapidSpin",
        "legal_inputs": (
            "wBattleMonSpecies",
            "wBattleMonLevel",
            "EvosAttacks",
        ),
    },
    "BossAI_ApplyMoveModel.species_spin_yes": {
        "predicate_id": "species_levelup_rapid_spin",
        "outcome": "available_by_level",
        "parent_symbol": "BossAI_ApplyMoveModel.SpeciesLevelUpHasRapidSpin",
        "legal_inputs": (
            "wBattleMonLevel",
            "EvosAttacks",
        ),
    },
    "BossAI_ApplyMoveModel.species_spin_no": {
        "predicate_id": "species_levelup_rapid_spin",
        "outcome": "not_available_by_level",
        "parent_symbol": "BossAI_ApplyMoveModel.SpeciesLevelUpHasRapidSpin",
        "legal_inputs": (
            "wBattleMonLevel",
            "EvosAttacks",
        ),
    },
    "BossAI_EnemyIsGhostType.yes": {
        "predicate_id": "enemy_is_ghost_type",
        "outcome": "ghost_type_present",
        "parent_symbol": "BossAI_EnemyIsGhostType",
        "legal_inputs": ("wEnemyMonType1", "wEnemyMonType2"),
    },
    "BossAI_ApplyMoveModel.player_cant_act": {
        "predicate_id": "player_cant_act_this_turn_publicly",
        "outcome": "status_prevents_action",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerCantActThisTurnPublicly",
        "legal_inputs": ("wBattleMonStatus",),
    },
    "BossAI_ApplyMoveModel.status_ok": {
        "predicate_id": "status_move_would_fail_publicly",
        "outcome": "not_publicly_failed",
        "parent_symbol": "BossAI_ApplyMoveModel.StatusMoveWouldFailPublicly",
        "legal_inputs": (
            "wBattleMonStatus",
            "wPlayerSubStatus1",
            "wPlayerSubStatus4",
            "wPlayerScreens",
            "wBattleMonType1",
            "wBattleMonType2",
            "wEnemyMonType1",
            "wEnemyMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.status_fail": {
        "predicate_id": "utility_or_status_public_fail",
        "outcome": "public_failure",
        "parent_symbol": "$active_frame",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wEnemyScreens",
            "wEnemySubStatus4",
            "wPlayerDisableCount",
            "wPlayerSubStatus1",
            "wPlayerSubStatus4",
            "wPlayerSubStatus5",
            "wPlayerScreens",
            "wBattleMonStatus",
            "wBattleWeather",
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.status_type_fail": {
        "predicate_id": "status_move_type_immunity",
        "outcome": "type_immunity",
        "parent_symbol": "BossAI_ApplyMoveModel.EnemyStatusMoveTypeMissesPlayer",
        "legal_inputs": (
            "wEnemyMoveStructType",
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.UtilityMoveWouldFailPublicly": {
        "predicate_id": "utility_move_would_fail_publicly",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.UtilityMoveWouldFailPublicly",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wEnemyScreens",
            "wEnemySubStatus4",
            "wPlayerDisableCount",
            "wPlayerSubStatus1",
            "wPlayerSubStatus4",
            "wPlayerSubStatus5",
            "wPlayerScreens",
            "wBattleMonStatus",
            "wBattleWeather",
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.skip_utility_fail": {
        "predicate_id": "utility_move_would_fail_publicly",
        "outcome": "not_publicly_failed",
        "parent_symbol": "BossAI_ApplyMoveModel.UtilityMoveWouldFailPublicly",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wEnemyScreens",
            "wEnemySubStatus4",
            "wEnemyMonHP",
            "wEnemyMonMaxHP",
            "wPlayerDarkShieldConsumed",
            "wPlayerDisableCount",
            "wPlayerSubStatus1",
            "wPlayerSubStatus4",
            "wPlayerSubStatus5",
            "wPlayerScreens",
            "wBattleMonStatus",
            "wBattleWeather",
            "wBattleMonType1",
            "wBattleMonType2",
            "wLastPlayerCounterMove",
            "wLastPlayerMove",
            "wEnemySleepClauseSlot",
        ),
    },
    "BossAI_ApplyMoveModel.PlayerCantActThisTurnPublicly": {
        "predicate_id": "player_cant_act_this_turn_publicly",
        "outcome": "not_status_prevents_action",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerCantActThisTurnPublicly",
        "legal_inputs": ("wBattleMonStatus",),
        "condition": "battle_mon_can_act",
    },
    "BossAI_ApplyMoveModel.EnemyHasBoostToPass": {
        "predicate_id": "enemy_boost_to_pass",
        "outcome": "no_boost_to_pass",
        "parent_symbol": "BossAI_ApplyMoveModel.EnemyHasBoostToPass",
        "legal_inputs": ("wEnemyStatLevels",),
        "condition": "enemy_has_no_boost_to_pass",
    },
    "BossAI_ApplyMoveModel.setup_punish": {
        "predicate_id": "setup_punish_bias",
        "outcome": "setup_punish_move",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySetupPunishBias",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wPlayerStatLevels",
        ),
    },
    "BossAI_ApplyMoveModel.discourage_recovery": {
        "predicate_id": "recovery_timing_discipline",
        "outcome": "recovery_too_slow",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyRecoveryTimingDiscipline",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wEnemyMonHP",
            "wEnemyMonMaxHP",
        ),
    },
    "BossAI_ApplyMoveModel.yes_recovery": {
        "predicate_id": "current_enemy_recovery_move",
        "outcome": "recovery_move",
        "parent_symbol": "BossAI_ApplyMoveModel.IsCurrentEnemyRecoveryMove",
        "legal_inputs": ("wEnemyMoveStructEffect",),
    },
    "BossAI_ApplyMoveModel.phaze_good": {
        "predicate_id": "phazing_plan_bias",
        "outcome": "phaze_good",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyPhazingPlanBias",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wPlayerScreens",
            "wPlayerStatLevels",
        ),
    },
    "BossAI_ApplyMoveModel.baton_bad": {
        "predicate_id": "baton_pass_bias",
        "outcome": "bad_pass_context",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyBatonPassBias",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wEnemyStatLevels",
            "wOTPartyCount",
            "wOTPartyMon1HP",
        ),
    },
    "BossAI_ApplyMoveModel.baton_good": {
        "predicate_id": "baton_pass_bias",
        "outcome": "boost_pass_available",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyBatonPassBias",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wEnemyStatLevels",
            "wOTPartyCount",
            "wOTPartyMon1HP",
        ),
    },
    "BossAI_ApplyMoveModel.boost_setup_yes": {
        "predicate_id": "boost_setup_move",
        "outcome": "boost_setup_move",
        "parent_symbol": "BossAI_ApplyMoveModel.IsBoostSetupMove",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wEnemyMonType1",
            "wEnemyMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.ApplySetupDisciplineBias": {
        "predicate_id": "setup_discipline_bias",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySetupDisciplineBias",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wEnemyStatLevels",
            "wEnemyMonType1",
            "wEnemyMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.setup_has_value": {
        "predicate_id": "setup_boost_has_further_value",
        "outcome": "has_value",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySetupDisciplineBias",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wEnemyStatLevels",
            "wEnemyMonType1",
            "wEnemyMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.ApplyStatusHardAnswerDiscipline": {
        "predicate_id": "status_hard_answer_discipline",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyStatusHardAnswerDiscipline",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wEnemyMoveStructPower",
            "wEnemyMoveStructType",
            "wBattleMonHP",
            "wBattleMonMaxHP",
        ),
    },
    "BossAI_ApplyMoveModel.hsmdm_yes": {
        "predicate_id": "strong_matchup_damaging_move",
        "outcome": "found",
        "parent_symbol": "BossAI_ApplyMoveModel.HasStrongMatchupDamagingMove",
        "legal_inputs": (
            "wEnemyMoveStructAnimation",
            "wEnemyMonMoves",
            "wBattleMonType1",
            "wBattleMonType2",
            "Moves + MOVE_POWER",
            "Moves + MOVE_TYPE",
        ),
    },
    "BossAI_ApplyMoveModel.PlayerHasRevealedAntiSetup": {
        "predicate_id": "revealed_anti_setup_scan",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasRevealedAntiSetup",
        "legal_inputs": (
            "wPlayerUsedMoves",
            "Moves + MOVE_EFFECT",
        ),
    },
    "BossAI_ApplyMoveModel.ApplyRampMoveBias": {
        "predicate_id": "ramp_move_bias",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyRampMoveBias",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wEnemyMoveStructType",
            "wEnemyMoveStructPower",
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.ramp_move": {
        "predicate_id": "ramp_move_candidate",
        "outcome": "rollout_or_fury_cutter",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyRampMoveBias",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wEnemyMoveStructType",
            "wEnemyMoveStructPower",
        ),
    },
    "BossAI_ApplyMoveModel.ramp_resisted": {
        "predicate_id": "ramp_move_matchup",
        "outcome": "resisted",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyRampMoveBias",
        "legal_inputs": (
            "wEnemyMoveStructType",
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.ramp_risky": {
        "predicate_id": "ramp_move_pressure",
        "outcome": "enemy_under_pressure",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyRampMoveBias",
        "legal_inputs": (
            "wEnemyMonHP",
            "wEnemyMonMaxHP",
            "wPlayerUsedMoves",
            "Moves + MOVE_EFFECT",
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.ApplyChargeMoveBias": {
        "predicate_id": "charge_move_bias",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyChargeMoveBias",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wBattleWeather",
            "wEnemySubStatus3",
        ),
    },
    "BossAI_ApplyMoveModel.ApplyPoisonContactRiskBias": {
        "predicate_id": "poison_contact_risk_bias",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyPoisonContactRiskBias",
        "legal_inputs": (
            "wEnemyMoveStructAnimation",
            "wEnemyMoveStructPower",
            "wEnemyMoveStructType",
            "wEnemyMonStatus",
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemyScreens",
            "wBattleMonType1",
            "wBattleMonType2",
            "MoveContactFlags",
        ),
    },
    "BossAI_ApplyMoveModel.full_poison_contact_risk": {
        "predicate_id": "poison_contact_risk",
        "outcome": "full_poison_contact_risk",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyPoisonContactRiskBias",
        "legal_inputs": (
            "wEnemyMoveStructAnimation",
            "wEnemyMoveStructPower",
            "wEnemyMoveStructType",
            "wEnemyMonStatus",
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemyScreens",
            "wBattleMonType1",
            "wBattleMonType2",
            "MoveContactFlags",
        ),
    },
    "BossAI_ApplyMoveModel.ApplyDarkShieldChanceBias": {
        "predicate_id": "dark_shield_chance_bias",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyDarkShieldChanceBias",
        "legal_inputs": (
            "wEnemyMoveStructEffect",
            "wEnemyMoveStructPower",
            "wPlayerDarkShieldConsumed",
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.ApplyLifeOrbRecoilBias": {
        "predicate_id": "life_orb_recoil_bias",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyLifeOrbRecoilBias",
        "legal_inputs": (
            "wEnemyMoveStructPower",
            "wEnemyMoveStructType",
            "wEnemyMonHP",
            "wEnemyMonMaxHP",
            "TypeBoostItems",
        ),
    },
    "BossAI_ApplyMoveModel.ApplyDestinyBondTradeBias": {
        "predicate_id": "destiny_bond_trade_bias",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyDestinyBondTradeBias",
        "legal_inputs": (
            "wBossAITier",
            "wEnemyMoveStructEffect",
            "wEnemyMonHP",
            "wEnemyMonMaxHP",
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.PlayerHasRevealedCounterCoatCategory": {
        "predicate_id": "revealed_counter_coat_category",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasRevealedCounterCoatCategory",
        "legal_inputs": (
            "register:B",
            "wPlayerUsedMoves",
            "Moves + MOVE_POWER",
            "Moves + MOVE_TYPE",
        ),
    },
    "BossAI_ApplyMoveModel.counter_coat_yes": {
        "predicate_id": "revealed_counter_coat_category",
        "outcome": "found",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasRevealedCounterCoatCategory",
        "legal_inputs": (
            "register:B",
            "wPlayerUsedMoves",
            "Moves + MOVE_POWER",
            "Moves + MOVE_TYPE",
        ),
    },
    "BossAI_ApplyMoveModel.ApplyChoiceFirstLockRegret": {
        "predicate_id": "choice_first_lock_regret",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyChoiceFirstLockRegret",
        "legal_inputs": (
            "wEnemyMoveStructPower",
            "wEnemyMoveStructType",
            "wEnemyChoiceLockedMove",
            "wBossAISeenPlayerSpeciesCount",
            "wBossAISeenPlayerSpecies",
            "BaseData",
        ),
    },
    "BossAI_ApplyMoveModel.choice_immune_risk": {
        "predicate_id": "choice_lock_risk",
        "outcome": "immune_risk",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplyChoiceFirstLockRegret",
        "legal_inputs": (
            "wEnemyMoveStructPower",
            "wEnemyMoveStructType",
            "wBossAISeenPlayerSpeciesCount",
            "wBossAISeenPlayerSpecies",
            "BaseData",
        ),
    },
    "BossAI_ApplyMoveModel.PlayerHasRevealedRecovery": {
        "predicate_id": "revealed_recovery_scan",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasRevealedRecovery",
        "legal_inputs": (
            "wPlayerUsedMoves",
            "Moves + MOVE_EFFECT",
        ),
    },
    "BossAI_ApplyMoveModel.recovery_yes_pop": {
        "predicate_id": "revealed_recovery",
        "outcome": "found",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasRevealedRecovery",
        "legal_inputs": (
            "wPlayerUsedMoves",
            "Moves + MOVE_EFFECT",
        ),
    },
    "BossAI_ApplyMoveModel.EnemyMoveMakesContact": {
        "predicate_id": "enemy_move_contact_scan",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.EnemyMoveMakesContact",
        "legal_inputs": (
            "wEnemyMoveStructAnimation",
            "MoveContactFlags",
        ),
    },
    "BossAI_ApplyMoveModel.no_contact": {
        "predicate_id": "enemy_move_contact",
        "outcome": "no_contact",
        "parent_symbol": "BossAI_ApplyMoveModel.EnemyMoveMakesContact",
        "legal_inputs": (
            "wEnemyMoveStructAnimation",
            "MoveContactFlags",
        ),
    },
    "BossAI_ApplyMoveModel.EnemyCanBePoisonedByRetaliation": {
        "predicate_id": "enemy_poison_retaliation_vulnerability",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.EnemyCanBePoisonedByRetaliation",
        "legal_inputs": (
            "wEnemyMonStatus",
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemyScreens",
        ),
    },
    "BossAI_ApplyMoveModel.poison_retaliation_safe": {
        "predicate_id": "enemy_poison_retaliation_vulnerability",
        "outcome": "not_vulnerable",
        "parent_symbol": "BossAI_ApplyMoveModel.EnemyCanBePoisonedByRetaliation",
        "legal_inputs": (
            "wEnemyMonStatus",
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemyScreens",
        ),
    },
    "BossAI_ApplyMoveModel.PlayerPoisonTypeContribution": {
        "predicate_id": "player_poison_type_contribution",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerPoisonTypeContribution",
        "legal_inputs": (
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.half_poison_type": {
        "predicate_id": "player_poison_type_contribution",
        "outcome": "half_poison_type",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerPoisonTypeContribution",
        "legal_inputs": (
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.full_poison_type": {
        "predicate_id": "player_poison_type_contribution",
        "outcome": "full_poison_type",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerPoisonTypeContribution",
        "legal_inputs": (
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.PlayerHasMajorSetupBoost": {
        "predicate_id": "player_major_setup_boost",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasMajorSetupBoost",
        "legal_inputs": ("wPlayerStatLevels",),
    },
    "BossAI_ApplyMoveModel.setup_seen": {
        "predicate_id": "player_major_setup_boost",
        "outcome": "major_setup_boost",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasMajorSetupBoost",
        "legal_inputs": ("wPlayerStatLevels",),
    },
    "BossAI_ApplyMoveModel.PlayerHasRepeatedSwitchPressure": {
        "predicate_id": "player_repeated_switch_pressure",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasRepeatedSwitchPressure",
        "legal_inputs": (
            "wBossAITurnsElapsed",
            "wBossAIPlayerSwitchCount",
        ),
    },
    "BossAI_ApplyMoveModel.no_switch_pressure": {
        "predicate_id": "player_repeated_switch_pressure",
        "outcome": "no_repeated_switch_pressure",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasRepeatedSwitchPressure",
        "legal_inputs": (
            "wBossAITurnsElapsed",
            "wBossAIPlayerSwitchCount",
        ),
    },
    "BossAI_ApplyMoveModel.BossHasSpinblockAvailable": {
        "predicate_id": "boss_spinblock_available",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.BossHasSpinblockAvailable",
        "legal_inputs": (
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemySubStatus1",
            "wOTPartyCount",
            "wOTPartySpecies",
            "wOTPartyMon1HP",
            "BaseData",
        ),
    },
    "BossAI_ApplyMoveModel.PlayerHasSeenAliveBenchGhost": {
        "predicate_id": "player_seen_alive_bench_ghost",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasSeenAliveBenchGhost",
        "legal_inputs": (
            "wBossAISeenPlayerSpecies",
            "wBossAISeenPlayerAliveMask",
            "wBattleMonSpecies",
            "BaseData",
        ),
    },
    "BossAI_ApplyMoveModel.bench_ghost_yes_pop": {
        "predicate_id": "player_seen_alive_bench_ghost",
        "outcome": "found",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerHasSeenAliveBenchGhost",
        "legal_inputs": (
            "wBossAISeenPlayerSpecies",
            "wBossAISeenPlayerAliveMask",
            "wBattleMonSpecies",
            "BaseData",
        ),
    },
    "BossAI_ApplyMoveModel.HasKOLine": {
        "predicate_id": "current_move_ko_line",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.HasKOLine",
        "legal_inputs": (
            "wEnemyMoveStructPower",
            "wEnemyMoveStructType",
            "wBattleMonHP",
            "wBattleMonMaxHP",
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.hasko_no": {
        "predicate_id": "current_move_ko_line",
        "outcome": "no_ko_line",
        "parent_symbol": "BossAI_ApplyMoveModel.HasKOLine",
        "legal_inputs": (
            "wEnemyMoveStructPower",
            "wEnemyMoveStructType",
            "wBattleMonHP",
            "wBattleMonMaxHP",
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.PlayerPublicThreatCategory": {
        "predicate_id": "player_public_threat_category",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerPublicThreatCategory",
        "legal_inputs": (
            "wBattleMonType1",
            "wBattleMonType2",
            "wEnemyMonType1",
            "wEnemyMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.public_threat_physical": {
        "predicate_id": "player_public_threat_category",
        "outcome": "physical_threat",
        "parent_symbol": "BossAI_ApplyMoveModel.PlayerPublicThreatCategory",
        "legal_inputs": (
            "wBattleMonType1",
            "wBattleMonType2",
            "wEnemyMonType1",
            "wEnemyMonType2",
        ),
    },
    "BossAI_PlayerHasPublicThreatVsEnemyUncached": {
        "predicate_id": "player_public_threat_vs_enemy_uncached",
        "outcome": "entered",
        "parent_symbol": "BossAI_PlayerHasPublicThreatVsEnemyUncached",
        "legal_inputs": (
            "wPlayerUsedMoves",
            "wBattleMonSpecies",
            "wBattleMonType1",
            "wBattleMonType2",
            "wBossAISeenPlayerSpeciesCount",
            "wBossAISeenPlayerSpecies",
            "wBossAIRevealedMovesBitmap",
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemyMonItem",
            "Moves + MOVE_POWER",
            "Moves + MOVE_TYPE",
        ),
    },
    "BossAI_PlayerHasRevealedPriorityThreatUncached": {
        "predicate_id": "revealed_priority_threat_uncached",
        "outcome": "entered",
        "parent_symbol": "BossAI_PlayerHasRevealedPriorityThreatUncached",
        "legal_inputs": (
            "wPlayerUsedMoves",
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemyMonItem",
            "wEnemyMonHP",
            "wEnemyMonMaxHP",
            "Moves + MOVE_EFFECT",
            "Moves + MOVE_POWER",
            "Moves + MOVE_TYPE",
        ),
    },
    "BossAI_ScaleMovePowerByBaseStatRatio.ApplyStatStagesToScored": {
        "predicate_id": "stat_stage_scaled_power",
        "outcome": "applied",
        "parent_symbol": "BossAI_ScaleMovePowerByBaseStatRatio.ApplyStatStagesToScored",
        "legal_inputs": (
            "register:A",
            "wEnemyMoveStructType",
            "wEnemyAtkLevel",
            "wEnemySAtkLevel",
            "wPlayerDefLevel",
            "wPlayerSDefLevel",
            "StatLevelMultipliers",
        ),
    },
    "BossAI_ApplyEnemyKnownPressureModifiers": {
        "predicate_id": "enemy_known_pressure_modifiers",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyEnemyKnownPressureModifiers",
        "legal_inputs": (
            "register:B",
            "wEnemyMoveStructType",
            "wTypeMatchup",
            "wEnemyMonItem",
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wBattleMonType1",
            "wBattleMonType2",
            "wEnemyMonHP",
            "wEnemyMonMaxHP",
            "wBattleMonHP",
            "wBattleMonMaxHP",
            "wEnemyMetronomeCount",
            "wBattleMonStatus",
            "TypeBoostItems",
        ),
    },
    "BossAI_PublicEnemyFasterUncached": {
        "predicate_id": "public_enemy_faster_uncached",
        "outcome": "entered",
        "parent_symbol": "BossAI_PublicEnemyFasterUncached",
        "legal_inputs": (
            "wBattleMonSpecies",
            "wEnemyMonSpecies",
            "wTempEnemyMonSpecies",
            "wEnemyMonItem",
            "wCurSpecies",
            "BaseData",
        ),
    },
    "BossAI_PublicEnemyFasterUncached.enemy_faster": {
        "predicate_id": "public_enemy_faster_uncached",
        "outcome": "enemy_faster",
        "parent_symbol": "BossAI_PublicEnemyFasterUncached",
        "legal_inputs": (
            "wBattleMonSpecies",
            "wEnemyMonSpecies",
            "wTempEnemyMonSpecies",
            "wEnemyMonItem",
            "wCurSpecies",
            "BaseData",
        ),
    },
    "BossAI_PublicEnemyFasterUncached.enemy_not_faster": {
        "predicate_id": "public_enemy_faster_uncached",
        "outcome": "not_enemy_faster",
        "parent_symbol": "BossAI_PublicEnemyFasterUncached",
        "legal_inputs": (
            "wBattleMonSpecies",
            "wEnemyMonSpecies",
            "wTempEnemyMonSpecies",
            "wEnemyMonItem",
            "wCurSpecies",
            "BaseData",
        ),
    },
    "BossAI_SeenBenchThreatScore": {
        "predicate_id": "seen_bench_threat_score",
        "outcome": "entered",
        "parent_symbol": "BossAI_SeenBenchThreatScore",
        "legal_inputs": (
            "wBossAISeenPlayerSpeciesCount",
            "wBossAISeenPlayerSpecies",
            "wBossAISeenPlayerAliveMask",
            "wBattleMonSpecies",
            "wCurSpecies",
            "wEnemyMonType1",
            "wEnemyMonType2",
            "BaseData",
        ),
    },
    "BossAI_SeenBenchThreatScore.favorable": {
        "predicate_id": "seen_bench_threat_score",
        "outcome": "favorable_bench_threat",
        "parent_symbol": "BossAI_SeenBenchThreatScore",
        "legal_inputs": (
            "wBossAISeenPlayerSpeciesCount",
            "wBossAISeenPlayerSpecies",
            "wBossAISeenPlayerAliveMask",
            "wBattleMonSpecies",
            "wCurSpecies",
            "wEnemyMonType1",
            "wEnemyMonType2",
            "BaseData",
        ),
    },
    "BossAI_SelectPlanIfNeeded.IsWinconCompromised": {
        "predicate_id": "wincon_compromised",
        "outcome": "entered",
        "parent_symbol": "BossAI_SelectPlanIfNeeded.IsWinconCompromised",
        "legal_inputs": (
            "wBossAIWinconMonIdx",
            "wOTPartyCount",
            "wOTPartyMon1Status",
            "wOTPartyMon1HP",
        ),
    },
    "BossAI_PlayerHasRevealedEffectA_Coach": {
        "predicate_id": "coach_revealed_effect_scan",
        "outcome": "entered",
        "parent_symbol": "BossAI_PlayerHasRevealedEffectA_Coach",
        "legal_inputs": (
            "register:A",
            "wPlayerUsedMoves",
            "Moves + MOVE_EFFECT",
        ),
    },
    "BossAI_AddPublicSTABThreatsToMask": {
        "predicate_id": "public_stab_threat_mask",
        "outcome": "entered",
        "parent_symbol": "BossAI_AddPublicSTABThreatsToMask",
        "legal_inputs": (
            "wBattleMonType1",
            "wBattleMonType2",
            "wBossAIPlausibleTypeMaskCache",
            "wBossAILikelyTypeMaskCache",
        ),
    },
    "BossAI_AddRevealedDamagingTypesToMask": {
        "predicate_id": "revealed_damaging_type_mask",
        "outcome": "entered",
        "parent_symbol": "BossAI_AddRevealedDamagingTypesToMask",
        "legal_inputs": (
            "wBattleMonSpecies",
            "wBossAISeenPlayerSpeciesCount",
            "wBossAISeenPlayerSpecies",
            "wBossAIRevealedMovesBitmap",
            "wBossAIPlausibleTypeMaskCache",
            "wBossAILikelyTypeMaskCache",
            "Moves + MOVE_POWER",
            "Moves + MOVE_TYPE",
        ),
    },
    "BossAI_LoadPublicThreatSourceSpecies": {
        "predicate_id": "public_threat_source_species",
        "outcome": "loaded",
        "parent_symbol": "BossAI_LoadPublicThreatSourceSpecies",
        "legal_inputs": (
            "wCurPartySpecies",
            "BaseData",
        ),
    },
    "BossAI_ApplyMultiTurnProjection.IsUnderPressure": {
        "predicate_id": "multi_turn_projection_pressure",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyMultiTurnProjection.IsUnderPressure",
        "legal_inputs": (
            "wEnemyMonHP",
            "wEnemyMonMaxHP",
            "wBossAIRevealedPriorityCache",
            "wBossAIPublicThreatCache",
            "wPlayerUsedMoves",
            "Moves + MOVE_EFFECT",
            "wBattleMonType1",
            "wBattleMonType2",
        ),
    },
    "BossAI_GetRevealedMoveThreatTypeAndSeverity": {
        "predicate_id": "revealed_move_threat_type_and_severity",
        "outcome": "entered",
        "parent_symbol": "BossAI_GetRevealedMoveThreatTypeAndSeverity",
        "legal_inputs": (
            "register:A",
            "wPlayerUsedMoves",
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemyMonItem",
            "wBossAIPlausibleTypeMaskCache",
            "wBossAILikelyTypeMaskCache",
            "Moves + MOVE_EFFECT",
            "Moves + MOVE_POWER",
            "Moves + MOVE_TYPE",
        ),
    },
    "BossAI_AdjustThreatSeverityForEnemyKnownDefense": {
        "predicate_id": "enemy_known_defense_threat_adjustment",
        "outcome": "entered",
        "parent_symbol": "BossAI_AdjustThreatSeverityForEnemyKnownDefense",
        "legal_inputs": (
            "register:B",
            "register:C",
            "wEnemyMoveStructType",
            "wTypeMatchup",
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemyMonItem",
            "wEnemyMonSpecies",
            "BaseData",
        ),
    },
    "BossAI_EnemyKnownItemNullifiesThreatType": {
        "predicate_id": "enemy_known_item_nullifies_threat_type",
        "outcome": "entered",
        "parent_symbol": "BossAI_EnemyKnownItemNullifiesThreatType",
        "legal_inputs": (
            "register:A",
            "wEnemyMoveStructType",
            "wEnemyMonSpecies",
            "wEnemyMonItem",
            "TypeBoostItems",
        ),
    },
    "BossAI_ApplyDamageDominanceBias.CurrentMoveDamageRank": {
        "predicate_id": "ko_band_current_move_damage_rank",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyDamageDominanceBias.CurrentMoveDamageRank",
        "legal_inputs": (
            "wEnemyMoveStructPower",
            "wEnemyMoveStructType",
            "wEnemyMoveStructEffect",
            "wTypeMatchup",
            "wBossAITemp",
            "wBossAITemp5",
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemyMonSpecies",
            "wBattleMonSpecies",
            "BaseData",
        ),
    },
    "BossAI_ApplyDamageDominanceBias.ApplySTABToRank": {
        "predicate_id": "ko_band_apply_stab_to_rank",
        "outcome": "entered",
        "parent_symbol": "BossAI_ApplyDamageDominanceBias.ApplySTABToRank",
        "legal_inputs": (
            "register:A",
            "register:C",
            "wEnemyMoveStructType",
            "wBossAITemp4",
            "wEnemyMonMoves",
            "wEnemyMonType1",
            "wEnemyMonType2",
        ),
    },
    "BossAI_ApplyMoveModel.ApplySpikesLayer3UnrevealedSpinRisk": {
        "predicate_id": "layer3_unrevealed_spin_risk",
        "outcome": "no_unrevealed_spin_risk",
        "parent_symbol": "BossAI_ApplyMoveModel.ApplySpikesLayer3UnrevealedSpinRisk",
        "legal_inputs": (
            "wEnemyMonType1",
            "wEnemyMonType2",
            "wEnemySubStatus1",
        ),
        "condition": "enemy_active_spinblock_available",
    },
    "BossAI_DecaySwitchCooldown": {
        "predicate_id": "switch_cooldown_decay",
        "outcome": "no_cooldown_to_decay",
        "parent_symbol": "BossAI_DecaySwitchCooldown",
        "legal_inputs": ("wBossAISwitchCooldown",),
        "condition": "symbol_zero:wBossAISwitchCooldown",
    },
}

PUBLIC_READ_PROBE_HOOKS = {
    name: {
        "probe_id": spec["predicate_id"],
        "outcome": spec["outcome"],
        "parent_symbol": spec["parent_symbol"],
        "legal_inputs": spec["legal_inputs"],
        "condition": spec.get("condition", ""),
    }
    for name, spec in PREDICATE_BRANCH_HOOKS.items()
}


@dataclass(frozen=True)
class HookTarget:
    kind: str
    full_symbol: str
    operation: str
    bank: int
    address: int
    predicate_id: str = ""
    outcome: str = ""
    parent_symbol: str = ""
    legal_inputs: tuple[str, ...] = ()
    condition: str = ""
    patches: tuple[MemoryPatch, ...] = ()


@dataclass(frozen=True)
class MemoryPatch:
    symbol_name: str
    offset: int
    value: int


@dataclass(frozen=True)
class DelayedMemoryPatch:
    hook_symbol: str
    patch: MemoryPatch


@dataclass(frozen=True)
class RuleFrame:
    sp: int
    full_symbol: str
    rule: dict[str, Any]


@dataclass(frozen=True)
class PendingScore:
    helper_symbol: str
    operation: str
    amount: int
    pointer: int
    before: int
    candidate: dict[str, Any]
    source: dict[str, Any]


class SymbolIndex:
    def __init__(
        self,
        symbols: dict[str, capture.Symbol],
        rule_map: dict[str, Any],
    ) -> None:
        self.symbols = symbols
        self.rule_by_full_symbol = build_rule_lookup(rule_map)
        self.symbols_by_bank: dict[int, list[tuple[int, str]]] = {}
        self.rules_by_bank: dict[int, list[tuple[int, str]]] = {}
        for name, symbol in symbols.items():
            self.symbols_by_bank.setdefault(symbol.bank, []).append(
                (symbol.address, name)
            )
        for items in self.symbols_by_bank.values():
            items.sort()
        for name in self.rule_by_full_symbol:
            symbol = symbols.get(name)
            if symbol is None:
                continue
            self.rules_by_bank.setdefault(symbol.bank, []).append(
                (symbol.address, name)
            )
        for items in self.rules_by_bank.values():
            items.sort()

    def hook_targets(
        self,
        delayed_memory_patches: list[DelayedMemoryPatch] | None = None,
    ) -> list[HookTarget]:
        targets: list[HookTarget] = []
        names: dict[str, tuple[str, str]] = {}
        for name in self.rule_by_full_symbol:
            if not is_executable_hook_label(name):
                continue
            names[name] = ("rule", "")
        for name, operation in SCORE_HELPERS.items():
            names[name] = ("score_helper", operation)
        for name, operation in CONTROL_HOOKS.items():
            names[name] = ("control", operation)

        for name, (kind, operation) in names.items():
            symbol = self.symbols.get(name)
            if symbol is None:
                continue
            targets.append(
                HookTarget(
                    kind=kind,
                    full_symbol=name,
                    operation=operation,
                    bank=symbol.bank,
                    address=symbol.address,
                )
            )
        for name, spec in PREDICATE_BRANCH_HOOKS.items():
            symbol = self.symbols.get(name)
            if symbol is None:
                continue
            targets.append(
                HookTarget(
                    kind="predicate_branch",
                    full_symbol=name,
                    operation=str(spec["outcome"]),
                    bank=symbol.bank,
                    address=symbol.address,
                    predicate_id=str(spec["predicate_id"]),
                    outcome=str(spec["outcome"]),
                    parent_symbol=str(spec["parent_symbol"]),
                    legal_inputs=tuple(str(item) for item in spec["legal_inputs"]),
                    condition=str(spec.get("condition", "")),
                )
            )
        for name, spec in PUBLIC_READ_PROBE_HOOKS.items():
            symbol = self.symbols.get(name)
            if symbol is None:
                continue
            targets.append(
                HookTarget(
                    kind="public_read_probe",
                    full_symbol=name,
                    operation=str(spec["outcome"]),
                    bank=symbol.bank,
                    address=symbol.address,
                    predicate_id=str(spec["probe_id"]),
                    outcome=str(spec["outcome"]),
                    parent_symbol=str(spec["parent_symbol"]),
                    legal_inputs=tuple(str(item) for item in spec["legal_inputs"]),
                    condition=str(spec.get("condition", "")),
                )
            )
        for delayed in delayed_memory_patches or []:
            symbol = self.symbols.get(delayed.hook_symbol)
            if symbol is None:
                raise PreferenceDataError(
                    f"unknown delayed patch hook symbol: {delayed.hook_symbol}"
                )
            targets.append(
                HookTarget(
                    kind="memory_patch",
                    full_symbol=delayed.hook_symbol,
                    operation="apply_memory_patch",
                    bank=symbol.bank,
                    address=symbol.address,
                    patches=(delayed.patch,),
                )
            )
        return targets

    def nearest_symbol(self, bank: int, address: int) -> str:
        return nearest_name(self.symbols_by_bank.get(bank, []), address)

    def nearest_rule_symbol(self, bank: int, address: int) -> str:
        return nearest_name(self.rules_by_bank.get(bank, []), address)

    def rule_for(self, full_symbol: str) -> dict[str, Any] | None:
        return self.rule_by_full_symbol.get(full_symbol)


class RomContributionTracer:
    def __init__(
        self,
        pyboy: Any,
        symbols: dict[str, capture.Symbol],
        symbol_index: SymbolIndex,
        move_names: dict[int, str],
        memory_patches: list[MemoryPatch] | None = None,
    ) -> None:
        self.pyboy = pyboy
        self.symbols = symbols
        self.symbol_index = symbol_index
        self.move_names = move_names
        self.memory_patches = memory_patches or []
        self.score_start_patches_applied = False
        self.frames: list[RuleFrame] = []
        self.pending: PendingScore | None = None
        self.events: list[dict[str, Any]] = []
        self.rule_entries: list[dict[str, Any]] = []
        self.predicate_branch_entries: list[dict[str, Any]] = []
        self.public_read_probe_entries: list[dict[str, Any]] = []
        self.delayed_patch_entries: list[dict[str, Any]] = []
        self.selector_entry_scores: list[int] = []
        self.candidate_start_scores: list[int] | None = None
        self.candidate_start_event_index = 0
        self.candidate_start_rule_entry_index = 0

    def reset(self, *, memory_patches: list[MemoryPatch] | None = None) -> None:
        self.memory_patches = memory_patches or []
        self.score_start_patches_applied = False
        self.frames.clear()
        self.pending = None
        self.events.clear()
        self.rule_entries.clear()
        self.predicate_branch_entries.clear()
        self.public_read_probe_entries.clear()
        self.delayed_patch_entries.clear()
        self.selector_entry_scores = []
        self.candidate_start_scores = None
        self.candidate_start_event_index = 0
        self.candidate_start_rule_entry_index = 0

    def handle_hook(self, targets: list[HookTarget]) -> None:
        for target in sorted(targets, key=hook_order):
            if target.kind == "rule":
                self.handle_rule(target)
            elif target.kind == "score_helper":
                self.handle_score_helper(target)
            elif target.kind == "control":
                self.handle_control(target)
            elif target.kind == "predicate_branch":
                self.handle_predicate_branch(target)
            elif target.kind == "public_read_probe":
                self.handle_public_read_probe(target)
            elif target.kind == "memory_patch":
                self.handle_memory_patch(target)

    def handle_rule(self, target: HookTarget) -> None:
        self.close_pending(trigger=target.full_symbol)
        sp = int(self.pyboy.register_file.SP)
        self.pop_returned_frames(sp)
        rule = self.symbol_index.rule_for(target.full_symbol)
        if rule is None:
            return
        frame = RuleFrame(sp=sp, full_symbol=target.full_symbol, rule=rule)
        if self.frames and self.frames[-1].sp == sp:
            self.frames[-1] = frame
        else:
            self.frames.append(frame)
        self.rule_entries.append(
            {
                "index": len(self.rule_entries) + 1,
                "event_type": "rule_enter",
                "sp": f"{sp:04x}",
                "candidate": self.active_score_candidate(),
                "move_struct": self.current_move_struct(),
                "public_input_snapshot": self.public_input_snapshot_for_rule(rule),
                "source": self.source_for_rule_entry(target, rule),
            }
        )

    def handle_score_helper(self, target: HookTarget) -> None:
        self.close_pending(trigger=target.full_symbol)
        sp = int(self.pyboy.register_file.SP)
        self.pop_returned_frames(sp)
        rule = self.symbol_index.rule_for(target.full_symbol)
        if rule is not None:
            self.rule_entries.append(
                {
                    "index": len(self.rule_entries) + 1,
                    "event_type": "rule_enter",
                    "sp": f"{sp:04x}",
                    "candidate": self.active_score_candidate(),
                    "move_struct": self.current_move_struct(),
                    "public_input_snapshot": self.public_input_snapshot_for_rule(rule),
                    "source": self.source_for_rule_entry(target, rule),
                }
            )
        pointer = self.score_pointer_for_helper(target)
        before = self.read_addr(pointer)
        amount = int(self.pyboy.register_file.A) & 0xFF
        self.pending = PendingScore(
            helper_symbol=target.full_symbol,
            operation=target.operation,
            amount=amount,
            pointer=pointer,
            before=before,
            candidate=self.candidate_for_score_pointer(pointer),
            source=self.source_for_score_helper(target),
        )

    def handle_predicate_branch(self, target: HookTarget) -> None:
        self.close_pending(trigger=target.full_symbol)
        if not self.predicate_branch_condition_matches(target):
            return
        sp = int(self.pyboy.register_file.SP)
        self.pop_returned_frames(sp)
        parent_symbol = self.resolved_predicate_parent_symbol(target)
        self.predicate_branch_entries.append(
            {
                "index": len(self.predicate_branch_entries) + 1,
                "event_type": "predicate_branch",
                "sp": f"{sp:04x}",
                "candidate": self.active_score_candidate(),
                "move_struct": self.current_move_struct(),
                "predicate": {
                    "predicate_id": target.predicate_id,
                    "outcome": target.outcome,
                    "branch_symbol": target.full_symbol,
                    "parent_symbol": parent_symbol,
                    "legal_inputs": list(target.legal_inputs),
                },
                "public_input_snapshot": self.public_input_snapshot(
                    target.legal_inputs
                ),
                "source": self.source_for_predicate_branch(target),
            }
        )

    def predicate_branch_condition_matches(self, target: HookTarget) -> bool:
        if not target.condition:
            return True
        if target.condition == "hl_points_to_zero_byte":
            try:
                hl = int(self.pyboy.register_file.HL) & 0xFFFF
                value = trace_runtime.read_byte(
                    self.pyboy,
                    capture.Symbol(target.bank, hl),
                )
            except Exception:
                return False
            return value == 0
        if target.condition.startswith("symbol_zero:"):
            symbol_name = target.condition.split(":", 1)[1]
            return self.read_public_symbol_byte(symbol_name) == 0
        if target.condition == "battle_mon_can_act":
            status = self.read_public_symbol_byte("wBattleMonStatus")
            return status is not None and status & 0x27 == 0
        if target.condition == "enemy_has_no_boost_to_pass":
            values = self.read_public_symbol_range("wEnemyStatLevels", 7)
            return values is not None and all(value <= 7 for value in values)
        if target.condition == "enemy_active_spinblock_available":
            type1 = self.read_public_symbol_byte("wEnemyMonType1")
            type2 = self.read_public_symbol_byte("wEnemyMonType2")
            substatus = self.read_public_symbol_byte("wEnemySubStatus1")
            if type1 is None or type2 is None or substatus is None:
                return False
            return (type1 == 8 or type2 == 8) and substatus & 0x08 == 0
        return False

    def read_public_symbol_byte(self, symbol_name: str) -> int | None:
        values = self.read_public_symbol_range(symbol_name, 1)
        return values[0] if values else None

    def read_public_symbol_range(self, symbol_name: str, width: int) -> list[int] | None:
        symbol = self.symbols.get(symbol_name)
        if symbol is None:
            return None
        try:
            return [self.read_symbol_offset(symbol, offset) for offset in range(width)]
        except Exception:
            return None

    def resolved_predicate_parent_symbol(self, target: HookTarget) -> str:
        if target.parent_symbol != "$active_frame":
            return target.parent_symbol
        frame = self.active_frame()
        return frame.full_symbol if frame is not None else ""

    def handle_public_read_probe(self, target: HookTarget) -> None:
        self.close_pending(trigger=target.full_symbol)
        if not self.predicate_branch_condition_matches(target):
            return
        sp = int(self.pyboy.register_file.SP)
        self.pop_returned_frames(sp)
        parent_symbol = self.resolved_predicate_parent_symbol(target)
        self.public_read_probe_entries.append(
            {
                "index": len(self.public_read_probe_entries) + 1,
                "event_type": "public_read_probe",
                "sp": f"{sp:04x}",
                "candidate": self.active_score_candidate(),
                "move_struct": self.current_move_struct(),
                "probe": {
                    "probe_id": target.predicate_id,
                    "outcome": target.outcome,
                    "probe_symbol": target.full_symbol,
                    "parent_symbol": parent_symbol,
                    "legal_inputs": list(target.legal_inputs),
                },
                "public_input_snapshot": self.public_input_snapshot(
                    target.legal_inputs
                ),
                "source": self.source_for_public_read_probe(target),
            }
        )

    def score_pointer_for_helper(self, target: HookTarget) -> int:
        if target.full_symbol in POINTER_FROM_WRAM_SCORE_PTR:
            symbol = self.symbols["wBossAIScorePtr"]
            high = trace_runtime.read_byte(self.pyboy, symbol)
            low = trace_runtime.read_byte(
                self.pyboy,
                capture.Symbol(symbol.bank, symbol.address + 1),
            )
            return (high << 8) | low
        return int(self.pyboy.register_file.HL)

    def handle_control(self, target: HookTarget) -> None:
        self.close_pending(trigger=target.full_symbol)
        if target.operation == "candidate_start":
            if not self.score_start_patches_applied:
                apply_memory_patches(self.pyboy, self.symbols, self.memory_patches)
                self.score_start_patches_applied = True
            self.frames.clear()
            self.candidate_start_scores = self.current_score_bytes()
            self.candidate_start_event_index = len(self.events)
            self.candidate_start_rule_entry_index = len(self.rule_entries)
        elif target.operation == "adaptive_lead_start":
            apply_memory_patches(self.pyboy, self.symbols, self.memory_patches)
        elif target.operation == "candidate_end":
            self.record_direct_score_writes(trigger=target.full_symbol)
        elif target.operation == "selector_start":
            self.selector_entry_scores = self.current_score_bytes()

    def handle_memory_patch(self, target: HookTarget) -> None:
        self.close_pending(trigger=target.full_symbol)
        apply_memory_patches(self.pyboy, self.symbols, list(target.patches))
        self.delayed_patch_entries.append(
            {
                "index": len(self.delayed_patch_entries) + 1,
                "event_type": "delayed_memory_patch",
                "hook_symbol": target.full_symbol,
                "memory_patches": memory_patches_to_json(list(target.patches)),
            }
        )

    def current_score_bytes(self) -> list[int]:
        symbol = self.symbols.get("wEnemyAIMoveScores")
        if symbol is None:
            return []
        try:
            return [
                self.read_symbol_offset(symbol, offset)
                for offset in range(4)
            ]
        except Exception:
            return []

    def close_pending(self, *, trigger: str) -> None:
        pending = self.pending
        if pending is None:
            return
        self.pending = None
        after = self.read_addr(pending.pointer)
        delta = after - pending.before
        self.events.append(
            {
                "index": len(self.events) + 1,
                "event_type": "score_delta",
                "helper_symbol": pending.helper_symbol,
                "operation": pending.operation,
                "amount_register_a": pending.amount,
                "score_pointer": f"{pending.pointer:04x}",
                "score_before": pending.before,
                "score_after": after,
                "delta": delta,
                "changed": delta != 0,
                "candidate": pending.candidate,
                "public_input_snapshot": self.public_input_snapshot_for_source(pending.source),
                "source": pending.source,
                "closed_by": trigger,
            }
        )

    def record_direct_score_writes(self, *, trigger: str) -> None:
        before_scores = self.candidate_start_scores
        if not before_scores:
            return
        after_scores = self.current_score_bytes()
        if len(before_scores) != len(after_scores):
            return
        helper_deltas = [0] * len(after_scores)
        for event in self.events[self.candidate_start_event_index:]:
            candidate = event.get("candidate", {})
            if not isinstance(candidate, dict):
                continue
            try:
                slot_index = int(candidate.get("slot_index", -1))
                delta = int(event.get("delta", 0))
            except (TypeError, ValueError):
                continue
            if 0 <= slot_index < len(helper_deltas):
                helper_deltas[slot_index] += delta
        for slot_index, (before, after) in enumerate(zip(before_scores, after_scores)):
            residual = (after - before) - helper_deltas[slot_index]
            if residual == 0:
                continue
            source = self.source_for_direct_score_write(slot_index=slot_index)
            self.events.append(
                {
                    "index": len(self.events) + 1,
                    "event_type": "score_delta",
                    "helper_symbol": "",
                    "operation": "direct_score_write",
                    "amount_register_a": 0,
                    "score_pointer": f"{self.score_pointer_for_slot(slot_index):04x}",
                    "score_before": after - residual,
                    "score_after": after,
                    "delta": residual,
                    "changed": True,
                    "candidate": self.candidate_for_slot(slot_index),
                    "public_input_snapshot": self.public_input_snapshot_for_source(source),
                    "source": source,
                    "closed_by": trigger,
                }
            )
        self.candidate_start_scores = None
        self.candidate_start_event_index = len(self.events)
        self.candidate_start_rule_entry_index = len(self.rule_entries)

    def score_pointer_for_slot(self, slot_index: int) -> int:
        base = self.symbols["wEnemyAIMoveScores"]
        return base.address + slot_index

    def candidate_for_slot(self, slot_index: int) -> dict[str, Any]:
        return self.candidate_for_score_pointer(self.score_pointer_for_slot(slot_index))

    def source_for_direct_score_write(self, *, slot_index: int) -> dict[str, Any]:
        direct_source = self.direct_write_source_from_rule_entries(slot_index)
        if direct_source is not None:
            return direct_source
        frame = self.active_frame()
        rule = frame.rule if frame is not None else None
        return {
            "rule_id": rule.get("rule_id", "") if rule else "",
            "source_label": rule.get("source_label", "") if rule else "",
            "full_symbol": frame.full_symbol if frame is not None else "",
            "classification": rule.get("classification", "") if rule else "",
            "public_reads": rule.get("public_reads", []) if rule else [],
            "static_public_read_hints": rule.get("public_reads", []) if rule else [],
            "attribution": "candidate score snapshot residual",
        }

    def direct_write_source_from_rule_entries(
        self,
        slot_index: int,
    ) -> dict[str, Any] | None:
        for entry in reversed(self.rule_entries[self.candidate_start_rule_entry_index:]):
            candidate = entry.get("candidate", {})
            source = entry.get("source", {})
            if not isinstance(candidate, dict) or not isinstance(source, dict):
                continue
            try:
                entry_slot = int(candidate.get("slot_index", -1))
            except (TypeError, ValueError):
                continue
            rule_id = str(source.get("rule_id", ""))
            if entry_slot == slot_index and rule_id in DIRECT_SCORE_WRITE_RULE_IDS:
                result = dict(source)
                result["attribution"] = "candidate score snapshot residual"
                return result
        return None

    def pop_returned_frames(self, sp: int) -> None:
        while self.frames and self.frames[-1].sp < sp:
            self.frames.pop()

    def active_frame(self) -> RuleFrame | None:
        if not self.frames:
            return None
        return self.frames[-1]

    def source_for_score_helper(self, target: HookTarget) -> dict[str, Any]:
        frame = self.active_frame()
        return_address = self.stack_return_address()
        callsite_symbol = self.symbol_index.nearest_symbol(
            target.bank,
            return_address,
        )
        callsite_rule_symbol = self.symbol_index.nearest_rule_symbol(
            target.bank,
            return_address,
        )
        callsite_rule = self.symbol_index.rule_for(callsite_rule_symbol)
        rule = frame.rule if frame is not None else callsite_rule
        full_symbol = frame.full_symbol if frame is not None else callsite_rule_symbol
        return {
            "rule_id": rule.get("rule_id", "") if rule else "",
            "source_label": rule.get("source_label", "") if rule else "",
            "full_symbol": full_symbol,
            "classification": rule.get("classification", "") if rule else "",
            "public_reads": rule.get("public_reads", []) if rule else [],
            "static_public_read_hints": rule.get("public_reads", []) if rule else [],
            "callsite_symbol": callsite_symbol,
            "callsite_rule_symbol": callsite_rule_symbol,
            "return_address": f"{return_address:04x}",
            "hook_bank": f"{target.bank:02x}",
        }

    def source_for_rule_entry(
        self,
        target: HookTarget,
        rule: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "rule_id": rule.get("rule_id", ""),
            "source_label": rule.get("source_label", ""),
            "full_symbol": target.full_symbol,
            "classification": rule.get("classification", ""),
            "public_reads": rule.get("public_reads", []),
            "static_public_read_hints": rule.get("public_reads", []),
            "hook_bank": f"{target.bank:02x}",
            "hook_address": f"{target.address:04x}",
        }

    def source_for_predicate_branch(self, target: HookTarget) -> dict[str, Any]:
        parent_symbol = self.resolved_predicate_parent_symbol(target)
        rule = self.symbol_index.rule_for(parent_symbol)
        return {
            "rule_id": rule.get("rule_id", "") if rule else "",
            "source_label": rule.get("source_label", "") if rule else "",
            "full_symbol": parent_symbol,
            "branch_symbol": target.full_symbol,
            "classification": rule.get("classification", "") if rule else "",
            "public_reads": rule.get("public_reads", []) if rule else [],
            "static_public_read_hints": rule.get("public_reads", []) if rule else [],
            "dynamic_branch_legal_inputs": list(target.legal_inputs),
            "hook_bank": f"{target.bank:02x}",
            "hook_address": f"{target.address:04x}",
        }

    def source_for_public_read_probe(self, target: HookTarget) -> dict[str, Any]:
        parent_symbol = self.resolved_predicate_parent_symbol(target)
        rule = self.symbol_index.rule_for(parent_symbol)
        return {
            "rule_id": rule.get("rule_id", "") if rule else "",
            "source_label": rule.get("source_label", "") if rule else "",
            "full_symbol": parent_symbol,
            "probe_symbol": target.full_symbol,
            "classification": rule.get("classification", "") if rule else "",
            "public_reads": rule.get("public_reads", []) if rule else [],
            "static_public_read_hints": rule.get("public_reads", []) if rule else [],
            "dynamic_probe_legal_inputs": list(target.legal_inputs),
            "hook_bank": f"{target.bank:02x}",
            "hook_address": f"{target.address:04x}",
        }

    def active_score_candidate(self) -> dict[str, Any]:
        if "wBossAIScorePtr" not in self.symbols:
            return unknown_candidate()
        try:
            symbol = self.symbols["wBossAIScorePtr"]
            high = trace_runtime.read_byte(self.pyboy, symbol)
            low = trace_runtime.read_byte(
                self.pyboy,
                capture.Symbol(symbol.bank, symbol.address + 1),
            )
        except Exception:
            return unknown_candidate()
        return self.candidate_for_score_pointer((high << 8) | low)

    def candidate_for_score_pointer(self, pointer: int) -> dict[str, Any]:
        base = self.symbols["wEnemyAIMoveScores"]
        offset = pointer - base.address
        if 0 <= offset < 4:
            move_symbol = self.symbols["wEnemyMonMoves"]
            move_id = self.read_symbol_offset(move_symbol, offset)
            return {
                "kind": "move",
                "slot_index": offset,
                "slot": offset + 1,
                "move_id": move_id,
                "move_name": self.move_names.get(move_id, f"#{move_id:02x}"),
            }
        return {
            **unknown_candidate(),
            "score_pointer": f"{pointer:04x}",
        }

    def current_move_struct(self) -> dict[str, int]:
        symbol_names = {
            "animation": "wEnemyMoveStructAnimation",
            "effect": "wEnemyMoveStructEffect",
            "power": "wEnemyMoveStructPower",
            "type": "wEnemyMoveStructType",
            "accuracy": "wEnemyMoveStructAccuracy",
            "pp": "wEnemyMoveStructPP",
            "effect_chance": "wEnemyMoveStructEffectChance",
        }
        values: dict[str, int] = {}
        for key, name in symbol_names.items():
            symbol = self.symbols.get(name)
            if symbol is None:
                continue
            try:
                values[key] = int(trace_runtime.read_byte(self.pyboy, symbol))
            except Exception:
                continue
        return values

    def public_input_snapshot_for_rule(self, rule: dict[str, Any]) -> dict[str, Any]:
        reads = rule.get("public_reads", [])
        if not isinstance(reads, (list, tuple)):
            return {}
        names = tuple(str(item) for item in reads if str(item))
        return self.public_input_snapshot(names) if names else {}

    def public_input_snapshot_for_source(self, source: dict[str, Any]) -> dict[str, Any]:
        reads = source.get("public_reads", [])
        if not isinstance(reads, (list, tuple)):
            return {}
        names = tuple(str(item) for item in reads if str(item))
        return self.public_input_snapshot(names) if names else {}

    def public_input_snapshot(self, names: tuple[str, ...]) -> dict[str, Any]:
        return {name: self.snapshot_public_input(name) for name in names}

    def snapshot_public_input(self, name: str) -> dict[str, Any]:
        register_name = REGISTER_PUBLIC_INPUTS.get(name)
        if register_name is not None:
            return self.register_snapshot(name, register_name)

        if name == "wOTPartyMon1HP":
            return self.party_hp_snapshot(name)
        if name == "wOTPartyMon1Status":
            return self.party_status_snapshot(name)

        static_symbol_name = STATIC_PUBLIC_TABLE_SYMBOLS.get(name)
        if static_symbol_name is not None:
            return self.static_table_snapshot(name, static_symbol_name)

        symbol = self.symbols.get(name)
        if symbol is None:
            return {
                "available": False,
                "reason": "symbol not found",
            }
        width = PUBLIC_INPUT_SNAPSHOT_WIDTHS.get(name, 1)
        try:
            values = [
                self.read_symbol_offset(symbol, offset)
                for offset in range(width)
            ]
        except Exception as exc:
            return {
                "available": False,
                "symbol": name,
                "bank": f"{symbol.bank:02x}",
                "address": f"{symbol.address:04x}",
                "width": width,
                "reason": f"read failed: {exc}",
            }
        return {
            "available": True,
            "kind": "byte_range",
            "symbol": name,
            "bank": f"{symbol.bank:02x}",
            "address": f"{symbol.address:04x}",
            "width": width,
            "values": values,
        }

    def register_snapshot(self, input_name: str, register_name: str) -> dict[str, Any]:
        try:
            value = int(getattr(self.pyboy.register_file, register_name)) & 0xFF
        except Exception as exc:
            return {
                "available": False,
                "kind": "cpu_register",
                "input": input_name,
                "register": register_name,
                "reason": f"read failed: {exc}",
            }
        return {
            "available": True,
            "kind": "cpu_register",
            "input": input_name,
            "register": register_name,
            "value": value,
        }

    def party_hp_snapshot(self, name: str) -> dict[str, Any]:
        symbol = self.symbols.get(name)
        if symbol is None:
            return {
                "available": False,
                "reason": "symbol not found",
            }
        slots = []
        try:
            for slot_index in range(PARTY_LENGTH):
                address = symbol.address + (slot_index * PARTYMON_STRUCT_LENGTH)
                values = [
                    self.read_symbol_offset(
                        capture.Symbol(symbol.bank, address),
                        offset,
                    )
                    for offset in range(4)
                ]
                slots.append(
                    {
                        "slot_index": slot_index,
                        "address": f"{address:04x}",
                        "values": values,
                    }
                )
        except Exception as exc:
            return {
                "available": False,
                "symbol": name,
                "bank": f"{symbol.bank:02x}",
                "address": f"{symbol.address:04x}",
                "reason": f"read failed: {exc}",
            }
        return {
            "available": True,
            "kind": "party_hp_slots",
            "symbol": name,
            "bank": f"{symbol.bank:02x}",
            "address": f"{symbol.address:04x}",
            "slot_count": len(slots),
            "slot_width": 4,
            "stride": PARTYMON_STRUCT_LENGTH,
            "slots": slots,
        }

    def party_status_snapshot(self, name: str) -> dict[str, Any]:
        symbol = self.symbols.get(name)
        if symbol is None:
            return {
                "available": False,
                "kind": "party_status_slots",
                "symbol": name,
                "reason": "symbol not found",
            }
        slots: list[dict[str, Any]] = []
        for slot_index in range(PARTY_LENGTH):
            try:
                value = self.read_symbol_offset(
                    symbol,
                    slot_index * PARTYMON_STRUCT_LENGTH,
                )
            except Exception as exc:
                slots.append(
                    {
                        "slot_index": slot_index,
                        "available": False,
                        "reason": f"read failed: {exc}",
                    }
                )
                continue
            slots.append(
                {
                    "slot_index": slot_index,
                    "status": value,
                }
            )
        return {
            "available": True,
            "kind": "party_status_slots",
            "symbol": name,
            "bank": f"{symbol.bank:02x}",
            "address": f"{symbol.address:04x}",
            "slot_count": len(slots),
            "stride": PARTYMON_STRUCT_LENGTH,
            "slots": slots,
        }

    def static_table_snapshot(
        self,
        input_name: str,
        symbol_name: str,
    ) -> dict[str, Any]:
        symbol = self.symbols.get(symbol_name)
        if symbol is None:
            return {
                "available": False,
                "kind": "static_table_reference",
                "symbol": symbol_name,
                "reason": "symbol not found",
            }
        return {
            "available": True,
            "kind": "static_table_reference",
            "input": input_name,
            "symbol": symbol_name,
            "bank": f"{symbol.bank:02x}",
            "address": f"{symbol.address:04x}",
            "values": [],
            "note": "static ROM table reference; branch-specific table bytes are not sampled",
        }

    def stack_return_address(self) -> int:
        sp = int(self.pyboy.register_file.SP)
        low = int(self.pyboy.memory[sp])
        high = int(self.pyboy.memory[(sp + 1) & 0xFFFF])
        return low | (high << 8)

    def read_symbol_offset(self, symbol: capture.Symbol, offset: int) -> int:
        return int(
            trace_runtime.read_byte(
                self.pyboy,
                capture.Symbol(symbol.bank, symbol.address + offset),
            )
        )

    def read_addr(self, address: int) -> int:
        bank = self.symbols["wEnemyAIMoveScores"].bank if 0xD000 <= address <= 0xDFFF else 0
        return int(trace_runtime.read_byte(self.pyboy, capture.Symbol(bank, address)))


class RomContributionTraceSession:
    def __init__(
        self,
        *,
        rom: Path = capture.DEFAULT_ROM,
        symbols_path: Path = capture.DEFAULT_SYMBOLS,
        delayed_memory_patches: list[DelayedMemoryPatch] | None = None,
    ) -> None:
        self.rom = rom
        self.symbols_path = symbols_path
        self.delayed_memory_patches = delayed_memory_patches or []
        self.symbols = capture.parse_symbols(symbols_path)
        capture.require_symbols(self.symbols)
        require_hook_symbols(self.symbols)
        self.symbol_index = SymbolIndex(self.symbols, build_rule_map())
        self.move_names = capture.parse_move_names(capture.MOVE_CONSTANTS)
        pyboy_class = trace_runtime.load_pyboy(
            "PyBoy is required for ROM contribution tracing"
        )
        self.pyboy = pyboy_class(str(rom), window="null", sound=False, log_level="ERROR")
        trace_runtime.disable_realtime(self.pyboy)
        self.tracer = RomContributionTracer(
            self.pyboy,
            self.symbols,
            self.symbol_index,
            self.move_names,
        )
        register_hooks(
            self.pyboy,
            self.symbol_index.hook_targets(self.delayed_memory_patches),
            self.tracer,
        )
        self.basis = capture.build_trace_basis_metadata(
            SimpleTraceArgs(rom=rom, symbols=symbols_path)
        )

    def __enter__(self) -> "RomContributionTraceSession":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        self.pyboy.stop(save=False)

    def run(
        self,
        *,
        save_state: Path,
        button: str = "a",
        button_delay: int = 8,
        watch_frames: int = 60,
        button_presses: int = 1,
        button_interval_frames: int = 0,
        metadata: dict[str, str] | None = None,
        memory_patches: list[MemoryPatch] | None = None,
        finish_on: str = "choice",
    ) -> dict[str, Any]:
        if not save_state.exists():
            raise PreferenceDataError(f"missing save-state: {save_state}")
        if finish_on not in {"choice", "switch"}:
            raise PreferenceDataError("finish_on must be 'choice' or 'switch'")

        patches = memory_patches or []
        self.tracer.reset(memory_patches=patches)
        with save_state.open("rb") as fh:
            self.pyboy.load_state(fh)
        apply_memory_patches(self.pyboy, self.symbols, patches)
        switch_observation: dict[str, Any] | None = None
        if finish_on == "switch":
            clear_switch_decision_fields(self.pyboy, self.symbols)
            final_values, presses_issued, observed_frame = drive_replay_to_switch_observation(
                self.pyboy,
                self.symbols,
                button=button,
                button_delay=button_delay,
                button_presses=button_presses,
                button_interval_frames=button_interval_frames,
                watch_frames=watch_frames,
            )
            if final_values is not None:
                switch_observation = switch_observation_from_values(
                    final_values,
                    frame=observed_frame,
                )
        else:
            clear_chosen_move(self.pyboy, self.symbols)
            final_values, presses_issued = drive_replay_to_choice(
                self.pyboy,
                self.symbols,
                button=button,
                button_delay=button_delay,
                button_presses=button_presses,
                button_interval_frames=button_interval_frames,
                watch_frames=watch_frames,
            )
        self.tracer.close_pending(trigger="replay_end")
        if final_values is None:
            if finish_on == "switch":
                raise PreferenceDataError(
                    no_switch_observation_error(
                        save_state=save_state,
                        watch_frames=watch_frames,
                        button=button,
                        button_delay=button_delay,
                        button_presses=button_presses,
                        button_interval_frames=button_interval_frames,
                        presses_issued=presses_issued,
                        metadata=metadata,
                        memory_patches=patches,
                    )
                )
            else:
                raise PreferenceDataError(
                    no_choice_error(
                        save_state=save_state,
                        watch_frames=watch_frames,
                        button=button,
                        button_delay=button_delay,
                        button_presses=button_presses,
                        button_interval_frames=button_interval_frames,
                        presses_issued=presses_issued,
                        metadata=metadata,
                        memory_patches=patches,
                    )
                )

        basis = dict(self.basis)
        if metadata:
            basis.update(metadata)
        return build_report(
            save_state=save_state,
            basis=basis,
            values=final_values,
            events=self.tracer.events,
            rule_entries=self.tracer.rule_entries,
            predicate_branch_entries=self.tracer.predicate_branch_entries,
            public_read_probe_entries=self.tracer.public_read_probe_entries,
            delayed_patch_entries=self.tracer.delayed_patch_entries,
            selector_entry_scores=self.tracer.selector_entry_scores,
            move_names=self.move_names,
            memory_patches=patches,
            delayed_memory_patches=self.delayed_memory_patches,
            decision_surface=(
                "switch_dispatch" if finish_on == "switch" else "rom_contribution_trace"
            ),
            switch_observation=switch_observation,
        )


def run_rom_contribution_trace(
    *,
    save_state: Path,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    button: str = "a",
    button_delay: int = 8,
    watch_frames: int = 60,
    button_presses: int = 1,
    button_interval_frames: int = 0,
    metadata: dict[str, str] | None = None,
    memory_patches: list[MemoryPatch] | None = None,
    delayed_memory_patches: list[DelayedMemoryPatch] | None = None,
    finish_on: str = "choice",
) -> dict[str, Any]:
    with RomContributionTraceSession(
        rom=rom,
        symbols_path=symbols_path,
        delayed_memory_patches=delayed_memory_patches,
    ) as session:
        return session.run(
            save_state=save_state,
            button=button,
            button_delay=button_delay,
            watch_frames=watch_frames,
            button_presses=button_presses,
            button_interval_frames=button_interval_frames,
            metadata=metadata,
            memory_patches=memory_patches,
            finish_on=finish_on,
        )


def run_rom_contribution_trace_for_route(
    *,
    boss_id: str,
    rom: Path = capture.DEFAULT_ROM,
    symbols_path: Path = capture.DEFAULT_SYMBOLS,
    battery_save: Path | None = None,
    out_dir: Path | None = None,
    input_wait_frames: int = 0,
    max_a_presses: int = 0,
    metadata: dict[str, str] | None = None,
    memory_patches: list[MemoryPatch] | None = None,
    delayed_memory_patches: list[DelayedMemoryPatch] | None = None,
) -> dict[str, Any]:
    from tools.trace import boss_ai_state_factory as factory

    if boss_id not in factory.ROUTES:
        known = ", ".join(sorted(factory.ROUTES))
        raise PreferenceDataError(f"unknown boss route {boss_id!r}; known: {known}")
    route = factory.ROUTES[boss_id]
    battery = battery_save if battery_save is not None else factory.DEFAULT_BATTERY_SAVE
    output = out_dir if out_dir is not None else factory.DEFAULT_OUT_DIR
    args = Namespace(
        rom=rom,
        battery_save=battery,
        out_dir=output,
        input_wait_frames=input_wait_frames,
        max_a_presses=max_a_presses,
        log_every=20,
    )

    symbols = capture.parse_symbols(symbols_path)
    capture.require_symbols(symbols)
    factory.require_symbols(symbols, [route])
    require_hook_symbols(symbols)
    event_constants = factory.parse_simple_consts(factory.EVENT_FLAGS)
    map_constants = factory.parse_map_consts(factory.MAP_CONSTANTS)
    trainer_constants = factory.parse_trainer_consts(factory.TRAINER_CONSTANTS)
    trainer_constant = factory.expected_trainer(route, trainer_constants)

    symbol_index = SymbolIndex(symbols, build_rule_map())
    move_names = capture.parse_move_names(capture.MOVE_CONSTANTS)
    work_rom = factory.prepare_work_rom(args)
    pyboy = factory.open_pyboy(work_rom)
    tracer = RomContributionTracer(
        pyboy,
        symbols,
        symbol_index,
        move_names,
        memory_patches=memory_patches,
    )
    log: list[str] = [
        f"ROUTE {route.capture_id}",
        "MODE contribution_trace",
        f"ROM_SOURCE {capture.display_path(rom)}",
        f"ROM_WORK {capture.display_path(work_rom)}",
        f"BATTERY_SAVE {capture.display_path(battery)}",
    ]
    try:
        register_hooks(pyboy, symbol_index.hook_targets(delayed_memory_patches), tracer)
        frame = factory.boot_continue(pyboy, symbols, log)
        frame = factory.setup_route_entry(
            pyboy,
            route,
            symbols,
            event_constants,
            map_constants,
            output,
            log,
            frame,
        )
        apply_memory_patches(pyboy, symbols, memory_patches or [])
        values, frame = drive_route_until_choice(
            pyboy,
            route,
            trainer_constant,
            symbols,
            args,
            log,
            frame,
        )
        tracer.close_pending(trigger="route_replay_end")
        basis = capture.build_trace_basis_metadata(
            SimpleTraceArgs(rom=rom, symbols=symbols_path)
        )
        if metadata:
            basis.update(metadata)
        report = build_report(
            save_state=work_rom,
            save_state_label=f"route:{route.capture_id}",
            basis=basis,
            values=values,
            events=tracer.events,
            rule_entries=tracer.rule_entries,
            predicate_branch_entries=tracer.predicate_branch_entries,
            public_read_probe_entries=tracer.public_read_probe_entries,
            delayed_patch_entries=tracer.delayed_patch_entries,
            selector_entry_scores=tracer.selector_entry_scores,
            move_names=move_names,
            memory_patches=memory_patches or [],
            delayed_memory_patches=delayed_memory_patches or [],
        )
        report["boss_route"] = route.capture_id
        report["frame"] = frame
        report["work_rom"] = capture.display_path(work_rom)
        return report
    finally:
        pyboy.stop(save=False)


def drive_route_until_choice(
    pyboy: Any,
    route: Any,
    trainer_constant: Any,
    symbols: dict[str, capture.Symbol],
    args: Namespace,
    log: list[str],
    frame: int,
) -> tuple[dict[str, list[int]], int]:
    from tools.trace import boss_ai_state_factory as factory

    input_wait_frames = (
        route.input_wait_frames
        if args.input_wait_frames == 0
        else args.input_wait_frames
    )
    for button_name in route.prime_buttons:
        factory.press(pyboy, button_name, input_wait_frames)
        frame += input_wait_frames
        log.append(factory.watch_line(pyboy, symbols, frame, f"PRIME_{button_name.upper()}"))

    max_presses = args.max_a_presses or route.max_a_presses
    for step in range(max_presses):
        factory.press(pyboy, "a", input_wait_frames)
        frame += input_wait_frames
        values = capture.read_trace_values(pyboy, symbols)
        chosen = values["wBossAITraceChosenMove"][0]
        if step % args.log_every == 0 or chosen:
            log.append(factory.watch_line(pyboy, symbols, frame, f"DRIVE_A_{step + 1:03d}"))
        if not chosen:
            continue
        trainer_class = factory.read_one(pyboy, symbols, "wOtherTrainerClass")
        trainer_id = factory.read_one(pyboy, symbols, "wOtherTrainerID")
        if (
            trainer_class != trainer_constant.class_id
            or trainer_id != trainer_constant.trainer_id
        ):
            raise PreferenceDataError(
                f"{route.capture_id}: got chosen move for trainer "
                f"{trainer_class:02x}:{trainer_id:02x}, expected "
                f"{trainer_constant.class_id:02x}:{trainer_constant.trainer_id:02x}"
            )
        return values, frame

    raise PreferenceDataError(
        f"{route.capture_id}: no chosen move observed within {max_presses} A presses"
    )


def register_hooks(
    pyboy: Any,
    targets: list[HookTarget],
    tracer: RomContributionTracer,
) -> None:
    targets_by_address: dict[tuple[int, int], list[HookTarget]] = {}
    for target in targets:
        targets_by_address.setdefault((target.bank, target.address), []).append(target)
    for (bank, address), grouped in targets_by_address.items():
        pyboy.hook_register(bank, address, hook_callback, (tracer, grouped))


def hook_callback(context: tuple[RomContributionTracer, list[HookTarget]]) -> None:
    tracer, targets = context
    tracer.handle_hook(targets)


def hook_order(target: HookTarget) -> int:
    return {
        "memory_patch": -1,
        "control": 0,
        "rule": 1,
        "predicate_branch": 2,
        "public_read_probe": 3,
        "score_helper": 4,
    }[target.kind]


def clear_chosen_move(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
) -> None:
    clear_decision_fields(pyboy, symbols, ("wBossAITraceChosenMove",))


def clear_switch_decision_fields(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
) -> None:
    clear_decision_fields(
        pyboy,
        symbols,
        ("wBossAITraceChosenMove", *SWITCH_DECISION_FIELDS),
    )


def clear_decision_fields(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
    names: tuple[str, ...],
) -> None:
    for name in names:
        symbol = symbols.get(name)
        if symbol is None:
            continue
        if 0xD000 <= symbol.address <= 0xDFFF and symbol.bank:
            try:
                pyboy.memory[symbol.bank, symbol.address] = 0
                continue
            except Exception:
                pass
        pyboy.memory[symbol.address] = 0


def drive_replay_to_choice(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
    *,
    button: str,
    button_delay: int,
    button_presses: int,
    button_interval_frames: int,
    watch_frames: int,
) -> tuple[dict[str, list[int]] | None, int]:
    if watch_frames <= 0:
        raise PreferenceDataError("watch_frames must be positive")
    if button_presses < 0:
        raise PreferenceDataError("button_presses must be non-negative")
    if button_interval_frames < 0:
        raise PreferenceDataError("button_interval_frames must be non-negative")
    if button_presses > 1 and button_interval_frames == 0:
        raise PreferenceDataError(
            "button_interval_frames is required when button_presses is greater than 1"
        )

    presses_issued = 0
    frame = 0
    last_values: dict[str, list[int]] | None = None
    while frame <= watch_frames:
        if should_issue_replay_button(
            frame=frame,
            button=button,
            button_presses=button_presses,
            button_interval_frames=button_interval_frames,
            presses_issued=presses_issued,
        ):
            pyboy.button(button, delay=button_delay)
            presses_issued += 1
        values = capture.read_trace_values(pyboy, symbols)
        if values["wBossAITraceChosenMove"][0] != 0:
            return values, presses_issued
        tick_count = replay_tick_count(
            frame=frame,
            watch_frames=watch_frames,
            button=button,
            button_presses=button_presses,
            button_interval_frames=button_interval_frames,
            presses_issued=presses_issued,
        )
        pyboy.tick(tick_count, False, False)
        frame += tick_count
    return None, presses_issued


def drive_replay_to_switch_observation(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
    *,
    button: str,
    button_delay: int,
    button_presses: int,
    button_interval_frames: int,
    watch_frames: int,
) -> tuple[dict[str, list[int]] | None, int, int]:
    if watch_frames <= 0:
        raise PreferenceDataError("watch_frames must be positive")
    if button_presses < 0:
        raise PreferenceDataError("button_presses must be non-negative")
    if button_presses > 1 and button_interval_frames == 0:
        raise PreferenceDataError(
            "button_interval_frames is required when button_presses is greater than 1"
        )

    presses_issued = 0
    frame = 0
    while frame <= watch_frames:
        if should_issue_replay_button(
            frame=frame,
            button=button,
            button_presses=button_presses,
            button_interval_frames=button_interval_frames,
            presses_issued=presses_issued,
        ):
            pyboy.button(button, delay=button_delay)
            presses_issued += 1
        values = capture.read_trace_values(pyboy, symbols)
        last_values = values
        if switch_decision_observed(values):
            return values, presses_issued, frame
        tick_count = 1
        pyboy.tick(tick_count, False, False)
        frame += tick_count
    return last_values, presses_issued, watch_frames


def switch_decision_observed(values: dict[str, list[int]]) -> bool:
    return any(
        int(values.get(name, [0])[0]) != 0
        for name in (
            "wBossAITraceChosenMove",
            "wBossAITraceSwitchConfidence",
            "wEnemySwitchMonIndex",
        )
    )


def switch_observation_from_values(
    values: dict[str, list[int]],
    *,
    frame: int,
) -> dict[str, Any]:
    confidence = int(values.get("wBossAITraceSwitchConfidence", [0])[0])
    param = int(values.get("wEnemySwitchMonParam", [0])[0])
    index = int(values.get("wEnemySwitchMonIndex", [0])[0])
    chosen = int(values.get("wBossAITraceChosenMove", [0])[0])
    if index:
        status = "actual_switch_observed"
    elif param:
        status = "switch_proposal_observed"
    elif confidence:
        status = "switch_confidence_observed"
    else:
        status = "no_switch_observation"
    return {
        "frame": frame,
        "status": status,
        "switch_confidence": confidence,
        "switch_param": param,
        "switch_index": index,
        "chosen_move": chosen,
    }


def no_choice_error(
    *,
    save_state: Path,
    watch_frames: int,
    button: str,
    button_delay: int,
    button_presses: int,
    button_interval_frames: int,
    presses_issued: int,
    metadata: dict[str, str] | None,
    memory_patches: list[MemoryPatch],
) -> str:
    parts = [
        f"no boss move choice observed within {watch_frames} frames",
        f"save_state={trace_runtime.display_path(save_state)}",
        (
            f"replay=button:{button or '<none>'} delay:{button_delay} "
            f"presses:{presses_issued}/{button_presses} interval:{button_interval_frames}"
        ),
        f"memory_patches={len(memory_patches)}",
    ]
    if metadata:
        metadata_text = " ".join(
            f"{key}={value}" for key, value in sorted(metadata.items()) if value
        )
        if metadata_text:
            parts.append(f"metadata={metadata_text}")
    parts.append(
        "diagnostic: this usually means the base state is stale, already past the choice window, or needs different manifest replay controls"
    )
    return "; ".join(parts)


def no_switch_observation_error(
    *,
    save_state: Path,
    watch_frames: int,
    button: str,
    button_delay: int,
    button_presses: int,
    button_interval_frames: int,
    presses_issued: int,
    metadata: dict[str, str] | None,
    memory_patches: list[MemoryPatch],
) -> str:
    parts = [
        f"no boss switch observation within {watch_frames} frames",
        f"save_state={trace_runtime.display_path(save_state)}",
        (
            f"replay=button:{button or '<none>'} delay:{button_delay} "
            f"presses:{presses_issued}/{button_presses} interval:{button_interval_frames}"
        ),
        f"memory_patches={len(memory_patches)}",
    ]
    if metadata:
        metadata_text = " ".join(
            f"{key}={value}" for key, value in sorted(metadata.items()) if value
        )
        if metadata_text:
            parts.append(f"metadata={metadata_text}")
    parts.append(
        "diagnostic: switch-dispatch traces finalize only after switch confidence, proposal, or index bytes change"
    )
    return "; ".join(parts)


def replay_tick_count(
    *,
    frame: int,
    watch_frames: int,
    button: str,
    button_presses: int,
    button_interval_frames: int,
    presses_issued: int,
) -> int:
    remaining = watch_frames - frame
    if remaining <= 0:
        return 1

    next_frame = frame + min(remaining, MAX_REPLAY_POLL_CHUNK_FRAMES)
    next_button = next_replay_button_frame(
        frame=frame,
        button=button,
        button_presses=button_presses,
        button_interval_frames=button_interval_frames,
        presses_issued=presses_issued,
    )
    if next_button is not None:
        next_frame = min(next_frame, next_button)
    return max(1, next_frame - frame)


def next_replay_button_frame(
    *,
    frame: int,
    button: str,
    button_presses: int,
    button_interval_frames: int,
    presses_issued: int,
) -> int | None:
    if not button or presses_issued >= button_presses:
        return None
    if button_interval_frames == 0:
        return None
    next_frame = button_interval_frames * presses_issued
    while next_frame <= frame and presses_issued < button_presses:
        presses_issued += 1
        next_frame = button_interval_frames * presses_issued
    if presses_issued >= button_presses:
        return None
    return next_frame


def should_issue_replay_button(
    *,
    frame: int,
    button: str,
    button_presses: int,
    button_interval_frames: int,
    presses_issued: int,
) -> bool:
    if not button or presses_issued >= button_presses:
        return False
    if button_interval_frames == 0:
        return frame == 0
    return frame % button_interval_frames == 0


def parse_memory_patch(text: str) -> MemoryPatch:
    lhs, sep, rhs = text.partition("=")
    if sep != "=" or not lhs or not rhs:
        raise PreferenceDataError(
            f"memory patch must look like SYMBOL=VALUE or SYMBOL+OFFSET=VALUE: {text}"
        )
    symbol_name, offset = parse_patch_location(lhs)
    value = int(rhs, 0)
    if not 0 <= value <= 0xFF:
        raise PreferenceDataError(f"memory patch value must be a byte: {text}")
    return MemoryPatch(symbol_name=symbol_name, offset=offset, value=value)


def parse_delayed_memory_patch(text: str) -> DelayedMemoryPatch:
    hook_symbol, sep, patch_text = text.partition(":")
    if sep != ":" or not hook_symbol or not patch_text:
        raise PreferenceDataError(
            "delayed memory patch must look like HOOK_SYMBOL:SYMBOL=VALUE "
            f"or HOOK_SYMBOL:SYMBOL+OFFSET=VALUE: {text}"
        )
    return DelayedMemoryPatch(
        hook_symbol=hook_symbol,
        patch=parse_memory_patch(patch_text),
    )


def parse_patch_location(text: str) -> tuple[str, int]:
    symbol_name, plus, offset_text = text.partition("+")
    if not symbol_name:
        raise PreferenceDataError(f"memory patch symbol is empty: {text}")
    offset = int(offset_text, 0) if plus else 0
    if offset < 0:
        raise PreferenceDataError(f"memory patch offset must be non-negative: {text}")
    return symbol_name, offset


def apply_memory_patches(
    pyboy: Any,
    symbols: dict[str, capture.Symbol],
    patches: list[MemoryPatch],
) -> None:
    for patch in patches:
        symbol = symbols.get(patch.symbol_name)
        if symbol is None:
            raise PreferenceDataError(f"unknown memory patch symbol: {patch.symbol_name}")
        write_symbol_offset(pyboy, symbol, patch.offset, patch.value)


def write_symbol_offset(
    pyboy: Any,
    symbol: capture.Symbol,
    offset: int,
    value: int,
) -> None:
    address = symbol.address + offset
    value &= 0xFF
    if 0xD000 <= address <= 0xDFFF and symbol.bank:
        try:
            pyboy.memory[symbol.bank, address] = value
            return
        except Exception:
            old_bank = int(pyboy.memory[0xFF70])
            pyboy.memory[0xFF70] = symbol.bank
            try:
                pyboy.memory[address] = value
            finally:
                pyboy.memory[0xFF70] = old_bank
            return
    pyboy.memory[address] = value


def memory_patches_to_json(patches: list[MemoryPatch]) -> list[dict[str, Any]]:
    return [
        {
            "symbol_name": patch.symbol_name,
            "offset": patch.offset,
            "value": patch.value,
        }
        for patch in patches
    ]


def delayed_memory_patches_to_json(
    patches: list[DelayedMemoryPatch],
) -> list[dict[str, Any]]:
    return [
        {
            "hook_symbol": delayed.hook_symbol,
            "patch": memory_patches_to_json([delayed.patch])[0],
        }
        for delayed in patches
    ]


def build_report(
    *,
    save_state: Path,
    save_state_label: str | None = None,
    basis: dict[str, str],
    values: dict[str, list[int]],
    events: list[dict[str, Any]],
    rule_entries: list[dict[str, Any]],
    predicate_branch_entries: list[dict[str, Any]],
    public_read_probe_entries: list[dict[str, Any]],
    delayed_patch_entries: list[dict[str, Any]],
    selector_entry_scores: list[int],
    move_names: dict[int, str],
    memory_patches: list[MemoryPatch],
    delayed_memory_patches: list[DelayedMemoryPatch],
    decision_surface: str = "rom_contribution_trace",
    switch_observation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    changed = [event for event in events if event["changed"]]
    executed_rule_ids = sorted(
        rule_ids_from_events(rule_entries)
        | rule_ids_from_events(predicate_branch_entries)
        | rule_ids_from_events(public_read_probe_entries)
        | rule_ids_from_events(events)
    )
    report = {
        "schema_version": 1,
        "source": "trace_rom_pyboy_hooks",
        "decision_surface": decision_surface,
        "save_state": save_state_label or trace_runtime.display_path(save_state),
        "trace_basis": basis,
        "chosen": {
            "move_id": values["wBossAITraceChosenMove"][0],
            "move_name": move_names.get(
                values["wBossAITraceChosenMove"][0],
                f"#{values['wBossAITraceChosenMove'][0]:02x}",
            ),
            "slot_index": values["wCurEnemyMoveNum"][0],
        },
        "memory_patches": memory_patches_to_json(memory_patches),
        "delayed_memory_patches": delayed_memory_patches_to_json(delayed_memory_patches),
        "move_ids": values["wEnemyMonMoves"],
        "move_scores": values["wEnemyAIMoveScores"],
        "pre_model_scores": values["wBossAITracePreModelScores"],
        "post_model_scores": values["wBossAITracePostModelScores"],
        "selector_entry_scores": list(selector_entry_scores),
        "rule_entry_count": len(rule_entries),
        "executed_rule_count": len(executed_rule_ids),
        "executed_rule_ids": executed_rule_ids,
        "rule_entries": deepcopy(rule_entries),
        "predicate_branch_entry_count": len(predicate_branch_entries),
        "predicate_branch_entries": deepcopy(predicate_branch_entries),
        "public_read_probe_entry_count": len(public_read_probe_entries),
        "public_read_probe_entries": deepcopy(public_read_probe_entries),
        "delayed_patch_entry_count": len(delayed_patch_entries),
        "delayed_patch_entries": deepcopy(delayed_patch_entries),
        "event_count": len(events),
        "changed_event_count": len(changed),
        "events": deepcopy(events),
        "known_limits": [
            "Trace events are captured by PyBoy execution hooks, not by an in-ROM WRAM ring buffer.",
            "Score events record score helper deltas plus candidate-start/end residual direct score writes, while rule entries record dynamic rule-label execution.",
            "Predicate branch entries record selected executable public-info branch labels and configured outcomes.",
            "Public-read probe entries record legal-input snapshots at configured executable labels; they are not CPU memory-read watchpoints.",
        ],
    }
    if switch_observation is not None:
        report["switch_observation"] = switch_observation
        report["known_limits"].append(
            "Switch-dispatch contribution traces finalize on observed switch WRAM fields, not on a chosen move."
        )
    return stamp_rom_contribution_trace_class(report)


def stamp_rom_contribution_trace_class(report: dict[str, Any]) -> dict[str, Any]:
    canonical = build_rom_contribution_trace_class(report)
    report.update(canonical_class_fields(canonical))
    return report


def format_rom_contribution_trace(report: dict[str, Any], *, limit: int = 80) -> str:
    chosen = report["chosen"]
    lines = [
        "Boss AI ROM contribution trace",
        (
            f"source={report['source']} surface={report.get('decision_surface', 'rom_contribution_trace')} "
            f"save_state={report['save_state']} "
            f"events={report['event_count']} changed={report['changed_event_count']} "
            f"rule_entries={report.get('rule_entry_count', 0)} "
            f"predicate_branches={report.get('predicate_branch_entry_count', 0)} "
            f"public_read_probes={report.get('public_read_probe_entry_count', 0)}"
        ),
        (
            f"chosen={chosen['move_name']}#{chosen['move_id']} "
            f"slot={chosen['slot_index']}"
        ),
        (
            "scores: "
            f"pre={csv(report['pre_model_scores'])} "
            f"post={csv(report['post_model_scores'])} "
            f"final={csv(report['move_scores'])}"
        ),
    ]
    switch_observation = report.get("switch_observation")
    if isinstance(switch_observation, dict):
        lines.append(
            "switch: "
            f"status={switch_observation.get('status', '')} "
            f"confidence={switch_observation.get('switch_confidence', 0)} "
            f"param={switch_observation.get('switch_param', 0)} "
            f"index={switch_observation.get('switch_index', 0)} "
            f"frame={switch_observation.get('frame', 0)}"
        )
    lines.extend(["", f"First {limit} score events:"])
    for event in report["events"][:limit]:
        candidate = event["candidate"]
        source = event["source"]
        change = "*" if event["changed"] else " "
        lines.append(
            f"  {change} {event['index']:03d} "
            f"slot={candidate['slot_index']} {candidate['move_name']} "
            f"{event['operation']} a={event['amount_register_a']} "
            f"{event['score_before']}->{event['score_after']} "
            f"delta={event['delta']:+d}"
        )
        lines.append(
            "      "
            f"{source.get('rule_id') or source.get('full_symbol')} "
            f"callsite={source.get('callsite_symbol', '')}"
        )
    if len(report["events"]) > limit:
        lines.append(f"  ... {len(report['events']) - limit} more")
    probe_entries = report.get("public_read_probe_entries", [])
    if probe_entries:
        lines.append("")
        lines.append(f"First {min(limit, len(probe_entries))} public-read probes:")
        for entry in probe_entries[:limit]:
            probe = entry.get("probe", {})
            candidate = entry.get("candidate", {})
            lines.append(
                f"  {entry['index']:03d} "
                f"slot={candidate.get('slot_index', -1)} "
                f"{probe.get('probe_id', '')}={probe.get('outcome', '')}"
            )
        if len(probe_entries) > limit:
            lines.append(f"  ... {len(probe_entries) - limit} more")
    rule_entries = report.get("rule_entries", [])
    if rule_entries:
        lines.append("")
        lines.append(f"First {min(limit, len(rule_entries))} rule entries:")
        for entry in rule_entries[:limit]:
            source = entry.get("source", {})
            candidate = entry.get("candidate", {})
            move_struct = entry.get("move_struct", {})
            effect = move_struct.get("effect", "?") if isinstance(move_struct, dict) else "?"
            lines.append(
                f"  {entry['index']:03d} "
                f"slot={candidate.get('slot_index', -1)} "
                f"effect={effect} "
                f"{source.get('rule_id') or source.get('full_symbol', '')}"
            )
        if len(rule_entries) > limit:
            lines.append(f"  ... {len(rule_entries) - limit} more")
    predicate_entries = report.get("predicate_branch_entries", [])
    if predicate_entries:
        lines.append("")
        lines.append(f"First {min(limit, len(predicate_entries))} predicate branches:")
        for entry in predicate_entries[:limit]:
            predicate = entry.get("predicate", {})
            candidate = entry.get("candidate", {})
            lines.append(
                f"  {entry['index']:03d} "
                f"slot={candidate.get('slot_index', -1)} "
                f"{predicate.get('predicate_id', '')}="
                f"{predicate.get('outcome', '')}"
            )
        if len(predicate_entries) > limit:
            lines.append(f"  ... {len(predicate_entries) - limit} more")
    lines.append("")
    lines.append("Known limits:")
    for limit_text in report["known_limits"]:
        lines.append(f"  - {limit_text}")
    return "\n".join(lines)


def write_rom_contribution_trace_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_rom_contribution_trace(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PreferenceDataError(f"missing ROM contribution trace: {path}") from exc
    if not isinstance(data, dict):
        raise PreferenceDataError(f"ROM contribution trace is not an object: {path}")
    if data.get("source") != "trace_rom_pyboy_hooks":
        raise PreferenceDataError(f"unsupported ROM contribution trace source: {path}")
    if not data.get("class_id") or not isinstance(data.get("canonical_state_class"), dict):
        stamp_rom_contribution_trace_class(data)
    return data


def summarize_rom_contribution_trace(
    report: dict[str, Any],
    *,
    artifact_path: Path | None = None,
) -> dict[str, Any]:
    events = [event for event in report.get("events", []) if isinstance(event, dict)]
    rule_entries = [
        event for event in report.get("rule_entries", []) if isinstance(event, dict)
    ]
    predicate_branch_entries = [
        event
        for event in report.get("predicate_branch_entries", [])
        if isinstance(event, dict)
    ]
    public_read_probe_entries = [
        event
        for event in report.get("public_read_probe_entries", [])
        if isinstance(event, dict)
    ]
    changed_events = [event for event in events if event.get("changed")]
    covered_rule_ids = sorted(rule_ids_from_events(events))
    changed_rule_ids = sorted(rule_ids_from_events(changed_events))
    executed_rule_ids = sorted(
        rule_ids_from_events(rule_entries)
        | rule_ids_from_events(predicate_branch_entries)
        | rule_ids_from_events(public_read_probe_entries)
        | set(covered_rule_ids)
    )
    operation_counts = count_event_values(events, "operation")
    changed_operation_counts = count_event_values(changed_events, "operation")
    classification_counts = count_source_values(events, "classification")
    changed_classification_counts = count_source_values(changed_events, "classification")
    executed_classification_counts = count_source_values(
        [*rule_entries, *predicate_branch_entries, *public_read_probe_entries, *events],
        "classification",
    )
    predicate_counts = count_predicate_values(predicate_branch_entries, "predicate_id")
    predicate_outcome_counts = count_predicate_outcomes(predicate_branch_entries)
    predicate_snapshot_count = count_predicate_public_input_snapshots(
        predicate_branch_entries
    )
    public_probe_counts = count_probe_values(public_read_probe_entries, "probe_id")
    public_probe_outcome_counts = count_probe_outcomes(public_read_probe_entries)
    public_probe_snapshot_count = count_public_input_snapshots(
        public_read_probe_entries
    )
    result = {
        "available": True,
        "source": report.get("source", ""),
        "save_state": report.get("save_state", ""),
        "boss_route": report.get("boss_route", ""),
        "artifact": relative_artifact_path(artifact_path) if artifact_path else "",
        "trace_rom_sha256": report.get("trace_basis", {}).get("trace_rom_sha256", ""),
        "trace_symbols_sha256": report.get("trace_basis", {}).get(
            "trace_symbols_sha256",
            "",
        ),
        "event_count": int(report.get("event_count", len(events))),
        "changed_event_count": int(report.get("changed_event_count", len(changed_events))),
        "rule_entry_count": int(report.get("rule_entry_count", len(rule_entries))),
        "predicate_branch_entry_count": int(
            report.get("predicate_branch_entry_count", len(predicate_branch_entries))
        ),
        "predicate_public_input_snapshot_count": predicate_snapshot_count,
        "public_read_probe_entry_count": int(
            report.get("public_read_probe_entry_count", len(public_read_probe_entries))
        ),
        "public_read_probe_snapshot_count": public_probe_snapshot_count,
        "executed_rule_count": len(executed_rule_ids),
        "covered_rule_count": len(covered_rule_ids),
        "changed_rule_count": len(changed_rule_ids),
        "executed_rule_ids": executed_rule_ids,
        "covered_rule_ids": covered_rule_ids,
        "changed_rule_ids": changed_rule_ids,
        "operation_counts": operation_counts,
        "changed_operation_counts": changed_operation_counts,
        "executed_classification_counts": executed_classification_counts,
        "classification_counts": classification_counts,
        "changed_classification_counts": changed_classification_counts,
        "predicate_counts": predicate_counts,
        "predicate_outcome_counts": predicate_outcome_counts,
        "public_read_probe_counts": public_probe_counts,
        "public_read_probe_outcome_counts": public_probe_outcome_counts,
        "unmapped_event_count": count_unmapped_events(events),
        "unmapped_rule_entry_count": count_unmapped_events(rule_entries),
        "unmapped_predicate_branch_entry_count": count_unmapped_events(
            predicate_branch_entries
        ),
        "unmapped_public_read_probe_entry_count": count_unmapped_events(
            public_read_probe_entries
        ),
        "changed_unmapped_event_count": count_unmapped_events(changed_events),
        "candidate_count": len(candidate_keys(events)),
        "changed_candidate_count": len(candidate_keys(changed_events)),
        "chosen": report.get("chosen", {}),
        "known_limits": report.get("known_limits", []),
    }
    canonical = report.get("canonical_state_class")
    if not isinstance(canonical, dict):
        canonical = build_rom_contribution_trace_class(report)
    result.update(
        {
            "class_id": canonical.get("class_id", ""),
            "class_fingerprint": canonical.get("class_fingerprint", ""),
            "canonical_state_class_valid": canonical.get("valid", False),
            "canonical_state_class_errors": canonical.get("validation_errors", []),
        }
    )
    return result


def summarize_rom_contribution_trace_paths(paths: list[Path]) -> dict[str, Any]:
    loaded = [
        summarize_rom_contribution_trace(
            load_rom_contribution_trace(path),
            artifact_path=path,
        )
        for path in paths
    ]
    return summarize_rom_contribution_trace_summaries(loaded)


def summarize_rom_contribution_trace_reports(
    reports: list[dict[str, Any]],
) -> dict[str, Any]:
    return summarize_rom_contribution_trace_summaries(
        [summarize_rom_contribution_trace(report) for report in reports]
    )


def summarize_rom_contribution_trace_summaries(
    loaded: list[dict[str, Any]],
) -> dict[str, Any]:
    if not loaded:
        return {
            "available": False,
            "artifact_count": 0,
            "event_count": 0,
            "changed_event_count": 0,
            "rule_entry_count": 0,
            "predicate_branch_entry_count": 0,
            "predicate_public_input_snapshot_count": 0,
            "public_read_probe_entry_count": 0,
            "public_read_probe_snapshot_count": 0,
            "executed_rule_count": 0,
            "covered_rule_count": 0,
            "changed_rule_count": 0,
            "class_id_count": 0,
            "executed_rule_ids": [],
            "covered_rule_ids": [],
            "changed_rule_ids": [],
            "operation_counts": {},
            "changed_operation_counts": {},
            "executed_classification_counts": {},
            "classification_counts": {},
            "changed_classification_counts": {},
            "predicate_counts": {},
            "predicate_outcome_counts": {},
            "public_read_probe_counts": {},
            "public_read_probe_outcome_counts": {},
            "unmapped_event_count": 0,
            "unmapped_rule_entry_count": 0,
            "unmapped_predicate_branch_entry_count": 0,
            "unmapped_public_read_probe_entry_count": 0,
            "changed_unmapped_event_count": 0,
            "candidate_count": 0,
            "changed_candidate_count": 0,
            "artifacts": [],
        }

    covered_rule_ids = sorted(
        {
            rule_id
            for summary in loaded
            for rule_id in summary["covered_rule_ids"]
        }
    )
    changed_rule_ids = sorted(
        {
            rule_id
            for summary in loaded
            for rule_id in summary["changed_rule_ids"]
        }
    )
    executed_rule_ids = sorted(
        {
            rule_id
            for summary in loaded
            for rule_id in summary["executed_rule_ids"]
        }
    )
    return {
        "available": True,
        "artifact_count": len(loaded),
        "event_count": sum(int(summary["event_count"]) for summary in loaded),
        "changed_event_count": sum(
            int(summary["changed_event_count"]) for summary in loaded
        ),
        "rule_entry_count": sum(int(summary["rule_entry_count"]) for summary in loaded),
        "predicate_branch_entry_count": sum(
            int(summary["predicate_branch_entry_count"]) for summary in loaded
        ),
        "predicate_public_input_snapshot_count": sum(
            int(summary["predicate_public_input_snapshot_count"])
            for summary in loaded
        ),
        "public_read_probe_entry_count": sum(
            int(summary["public_read_probe_entry_count"]) for summary in loaded
        ),
        "public_read_probe_snapshot_count": sum(
            int(summary["public_read_probe_snapshot_count"]) for summary in loaded
        ),
        "executed_rule_count": len(executed_rule_ids),
        "covered_rule_count": len(covered_rule_ids),
        "changed_rule_count": len(changed_rule_ids),
        "class_id_count": sum(1 for summary in loaded if summary.get("class_id")),
        "executed_rule_ids": executed_rule_ids,
        "covered_rule_ids": covered_rule_ids,
        "changed_rule_ids": changed_rule_ids,
        "operation_counts": merge_counts(
            summary["operation_counts"] for summary in loaded
        ),
        "changed_operation_counts": merge_counts(
            summary["changed_operation_counts"] for summary in loaded
        ),
        "executed_classification_counts": merge_counts(
            summary["executed_classification_counts"] for summary in loaded
        ),
        "classification_counts": merge_counts(
            summary["classification_counts"] for summary in loaded
        ),
        "changed_classification_counts": merge_counts(
            summary["changed_classification_counts"] for summary in loaded
        ),
        "predicate_counts": merge_counts(
            summary["predicate_counts"] for summary in loaded
        ),
        "predicate_outcome_counts": merge_counts(
            summary["predicate_outcome_counts"] for summary in loaded
        ),
        "public_read_probe_counts": merge_counts(
            summary["public_read_probe_counts"] for summary in loaded
        ),
        "public_read_probe_outcome_counts": merge_counts(
            summary["public_read_probe_outcome_counts"] for summary in loaded
        ),
        "unmapped_event_count": sum(
            int(summary["unmapped_event_count"]) for summary in loaded
        ),
        "unmapped_rule_entry_count": sum(
            int(summary["unmapped_rule_entry_count"]) for summary in loaded
        ),
        "unmapped_predicate_branch_entry_count": sum(
            int(summary["unmapped_predicate_branch_entry_count"])
            for summary in loaded
        ),
        "unmapped_public_read_probe_entry_count": sum(
            int(summary["unmapped_public_read_probe_entry_count"])
            for summary in loaded
        ),
        "changed_unmapped_event_count": sum(
            int(summary["changed_unmapped_event_count"]) for summary in loaded
        ),
        "candidate_count": sum(int(summary["candidate_count"]) for summary in loaded),
        "changed_candidate_count": sum(
            int(summary["changed_candidate_count"]) for summary in loaded
        ),
        "artifacts": loaded,
    }


def resolve_rom_contribution_trace_paths(paths: list[Path] | None) -> list[Path]:
    if paths is not None:
        return paths
    discovered: list[Path] = []
    for directory, pattern in DEFAULT_ROM_CONTRIBUTION_TRACE_SOURCES:
        discovered.extend(sorted(directory.glob(pattern)))

    resolved: list[Path] = []
    seen: set[Path] = set()
    for path in discovered:
        key = path.resolve()
        if key in seen:
            continue
        seen.add(key)
        resolved.append(path)
    return resolved


def expected_public_read_probe_outcomes() -> list[str]:
    return sorted(
        f"{spec['probe_id']}:{spec['outcome']}"
        for spec in PUBLIC_READ_PROBE_HOOKS.values()
    )


def require_hook_symbols(symbols: dict[str, capture.Symbol]) -> None:
    missing = [
        name
        for name in [*SCORE_HELPERS, *CONTROL_HOOKS]
        if name not in symbols
    ]
    if missing:
        raise PreferenceDataError("missing hook symbols: " + ", ".join(missing))


def build_rule_lookup(rule_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for rule in rule_map["rules"]:
        full_symbol = full_symbol_for_rule(rule)
        if not full_symbol:
            continue
        out[full_symbol] = rule
    return out


def full_symbol_for_rule(rule: dict[str, Any]) -> str:
    label = str(rule["source_label"])
    if label.startswith("."):
        if not isinstance(rule.get("parent_label"), str):
            return ""
        return f"{rule['parent_label']}{label}"
    return label


def is_executable_hook_label(full_symbol: str) -> bool:
    label = full_symbol.rsplit(".", 1)[-1]
    if label.startswith("BossAI") and not label.startswith("BossAI_"):
        return False
    return True


def nearest_name(items: list[tuple[int, str]], address: int) -> str:
    name = ""
    for item_address, item_name in items:
        if item_address > address:
            break
        name = item_name
    return name


def csv(values: list[int]) -> str:
    return ",".join(str(value) for value in values)


def rule_ids_from_events(events: list[dict[str, Any]]) -> set[str]:
    rule_ids = set()
    for event in events:
        source = event.get("source", {})
        if not isinstance(source, dict):
            continue
        rule_id = str(source.get("rule_id", ""))
        if rule_id:
            rule_ids.add(rule_id)
    return rule_ids


def candidate_keys(events: list[dict[str, Any]]) -> set[tuple[str, int, int]]:
    keys = set()
    for event in events:
        candidate = event.get("candidate", {})
        if not isinstance(candidate, dict):
            continue
        keys.add(
            (
                str(candidate.get("kind", "")),
                int(candidate.get("slot_index", -1)),
                int(candidate.get("move_id", 0)),
            )
        )
    return keys


def unknown_candidate() -> dict[str, Any]:
    return {
        "kind": "unknown_score_pointer",
        "slot_index": -1,
        "slot": 0,
        "move_id": 0,
        "move_name": "",
    }


def count_event_values(events: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        value = str(event.get(key, ""))
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def count_source_values(events: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        source = event.get("source", {})
        if not isinstance(source, dict):
            continue
        value = str(source.get(key, ""))
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def count_predicate_values(events: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        predicate = event.get("predicate", {})
        if not isinstance(predicate, dict):
            continue
        value = str(predicate.get(key, ""))
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def count_predicate_outcomes(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        predicate = event.get("predicate", {})
        if not isinstance(predicate, dict):
            continue
        predicate_id = str(predicate.get("predicate_id", ""))
        outcome = str(predicate.get("outcome", ""))
        if not predicate_id or not outcome:
            continue
        key = f"{predicate_id}:{outcome}"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def count_predicate_public_input_snapshots(events: list[dict[str, Any]]) -> int:
    return count_public_input_snapshots(events)


def count_public_input_snapshots(events: list[dict[str, Any]]) -> int:
    count = 0
    for event in events:
        snapshot = event.get("public_input_snapshot")
        if isinstance(snapshot, dict) and snapshot:
            count += 1
    return count


def count_probe_values(events: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        probe = event.get("probe", {})
        if not isinstance(probe, dict):
            continue
        value = str(probe.get(key, ""))
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def count_probe_outcomes(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        probe = event.get("probe", {})
        if not isinstance(probe, dict):
            continue
        probe_id = str(probe.get("probe_id", ""))
        outcome = str(probe.get("outcome", ""))
        if not probe_id or not outcome:
            continue
        key = f"{probe_id}:{outcome}"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def count_unmapped_events(events: list[dict[str, Any]]) -> int:
    count = 0
    for event in events:
        if not rule_ids_from_events([event]):
            count += 1
    return count


def merge_counts(items: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for key, value in item.items():
            counts[key] = counts.get(key, 0) + int(value)
    return dict(sorted(counts.items()))


def relative_artifact_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)


@dataclass(frozen=True)
class SimpleTraceArgs:
    rom: Path
    symbols: Path
