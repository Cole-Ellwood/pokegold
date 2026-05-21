from __future__ import annotations

import hashlib
import json
import random
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError


PUBLIC_POLICY_FAMILIES = (
    "switch_sack",
    "setup_heal",
    "prediction_mix",
    "support_handoff",
    "cashout_board_delta",
)
FAMILIES = (
    "selector_edges",
    "spikes_spin",
    "score_rule_probe",
    "mastery_policy",
    *PUBLIC_POLICY_FAMILIES,
    "all",
)
ALL_FAMILY_SEQUENCE = (
    "selector_edges",
    "mastery_policy",
    "spikes_spin",
    "mastery_policy",
    "switch_sack",
    "mastery_policy",
    "setup_heal",
    "mastery_policy",
    "prediction_mix",
    "support_handoff",
    "cashout_board_delta",
)
DEFAULT_GENERATOR_VERSION = "boss-ai-debugger-generator-v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRACE_ROM = ROOT / "pokegold_trace.gbc"
DEFAULT_TRACE_SYMBOLS = ROOT / "pokegold_trace.sym"
AI_TIER_MID = 2
AI_TIER_LATE = 3
ROM_TIER_WEIGHTS = {
    "mid": {
        "setup": 2,
        "status": 1,
        "role": 1,
        "risk": 2,
    },
    "late": {
        "setup": 2,
        "status": 2,
        "role": 3,
        "risk": 1,
    },
}


def probe_delta(rule: str, delta: int) -> dict[str, int | str]:
    return {"rule": rule, "delta": delta}


def probe_set_score(rule: str, score: int) -> dict[str, int | str]:
    return {"rule": rule, "set_score": score}


def probe_patch(symbol: str, value: int, offset: int = 0) -> dict[str, int | str]:
    return {"symbol": symbol, "offset": offset, "value": value}


PROBE_CLEAR_PLAYER_USED_MOVES = [
    probe_patch("wPlayerUsedMoves", 0, 0),
    probe_patch("wPlayerUsedMoves", 0, 1),
    probe_patch("wPlayerUsedMoves", 0, 2),
    probe_patch("wPlayerUsedMoves", 0, 3),
]

PROBE_SLEEP_UNCERTAIN_PATCHES = [
    probe_patch("wBattleMonStatus", 2),
    probe_patch("wCurBattleMon", 0),
    probe_patch("wBossAIPlayerSleepDeniedMon", 1),
    probe_patch("wBossAIPlayerSleepDeniedCount", 2),
    probe_patch("wBattleMonHP", 0, 0),
    probe_patch("wBattleMonHP", 80, 1),
]

SCORE_RULE_PROBE_CASES = [
    {
        "case_id": "sleep_wake_uncertain",
        "notes": [
            "generated score-rule probe: slower boss prices uncertain wake timing",
        ],
        "moves": [
            {
                "id": "move_dream_eater",
                "name": "Dream Eater",
                "move_id": 0x8A,
                "deltas": [
                    probe_delta("move.apply_move_model.apply_damage_pressure_bias", 2),
                    probe_delta("move.apply_move_model.apply_sleep_wake_risk_bias", 2),
                ],
                "lookahead_delta": 18,
            },
            {
                "id": "move_nightmare",
                "name": "Nightmare",
                "move_id": 0xAB,
                "deltas": [
                    probe_delta("move.apply_move_model.apply_sleep_wake_risk_bias", 2),
                ],
                "lookahead_delta": 18,
            },
            {
                "id": "move_recover",
                "name": "Recover",
                "move_id": 0x69,
                "deltas": [
                    probe_delta(
                        "move.apply_move_model.apply_recovery_timing_discipline",
                        6,
                    ),
                ],
                "lookahead_delta": 18,
            },
            {
                "id": "move_spikes",
                "name": "Spikes",
                "move_id": 0xBF,
                "deltas": [
                    probe_delta("move.apply_move_model.enemy_under_pressure", -3),
                    probe_delta("move.apply_move_model.apply_role_bias", -3),
                ],
                "lookahead_delta": 18,
            },
        ],
        "expectation": {
            "best_action_ids": ["move_spikes"],
            "acceptable_action_ids": ["move_nightmare"],
            "condition_tags": ["sleep_probe_uncertain"],
            "lesson_type": "score_rule_probe",
            "confidence": "high",
            "why": "Uncertain public wake timing makes sleep-dependent moves risky without hiding the sleep counter.",
        },
        "materialization_patches": [
            *PROBE_SLEEP_UNCERTAIN_PATCHES,
            *PROBE_CLEAR_PLAYER_USED_MOVES,
        ],
    },
    {
        "case_id": "focus_revealed_damage",
        "notes": [
            "generated score-rule probe: revealed damage breaks Focus Punch",
        ],
        "moves": [
            {
                "id": "move_focus_punch",
                "name": "Focus Punch",
                "move_id": 0x86,
                "deltas": [
                    probe_delta("move.apply_move_model.apply_damage_pressure_bias", 2),
                    probe_delta("move.apply_move_model.apply_sleep_wake_risk_bias", 2),
                    probe_delta(
                        "move.apply_move_model.player_has_revealed_damaging_hit_vs_enemy",
                        14,
                    ),
                ],
                "lookahead_delta": 18,
            },
            {
                "id": "move_nightmare",
                "name": "Nightmare",
                "move_id": 0xAB,
                "deltas": [
                    probe_delta("move.apply_move_model.apply_sleep_wake_risk_bias", 2),
                ],
                "lookahead_delta": 18,
            },
            {
                "id": "move_recover",
                "name": "Recover",
                "move_id": 0x69,
                "deltas": [
                    probe_delta("move.apply_move_model.enemy_under_pressure", -4),
                    probe_delta(
                        "move.apply_move_model.apply_recovery_timing_discipline",
                        6,
                    ),
                ],
                "lookahead_delta": 18,
            },
            {
                "id": "move_spikes",
                "name": "Spikes",
                "move_id": 0xBF,
                "deltas": [
                    probe_delta("move.apply_move_model.enemy_under_pressure", -2),
                    probe_delta("move.apply_move_model.apply_role_bias", -3),
                ],
                "lookahead_delta": 18,
            },
        ],
        "expectation": {
            "best_action_ids": ["move_spikes"],
            "acceptable_action_ids": ["move_focus_punch"],
            "condition_tags": ["focus_revealed_damage_probe"],
            "lesson_type": "score_rule_probe",
            "confidence": "high",
            "why": "A public revealed damaging hit can break Focus Punch when sleep is not guaranteed.",
        },
        "materialization_patches": [
            *PROBE_SLEEP_UNCERTAIN_PATCHES,
            probe_patch("wPlayerUsedMoves", 0x39, 0),
            probe_patch("wPlayerUsedMoves", 0, 1),
            probe_patch("wPlayerUsedMoves", 0, 2),
            probe_patch("wPlayerUsedMoves", 0, 3),
        ],
    },
    {
        "case_id": "high_pressure_ko",
        "notes": [
            "generated score-rule probe: KO-pressure move enters the high-pressure gate",
        ],
        "moves": [
            {
                "id": "move_sludge_bomb",
                "name": "Sludge Bomb",
                "move_id": 0xBC,
                "deltas": [
                    probe_delta("move.apply_move_model", -7),
                    probe_delta("move.apply_move_model.apply_damage_pressure_bias", -4),
                    probe_delta("move.apply_move_model.apply_role_bias", -3),
                ],
                "lookahead_delta": 18,
            },
            {
                "id": "move_nightmare",
                "name": "Nightmare",
                "move_id": 0xAB,
                "deltas": [
                    probe_set_score(
                        "move.apply_move_model.utility_move_would_fail_publicly",
                        80,
                    ),
                ],
                "lookahead_delta": 18,
            },
            {
                "id": "move_recover",
                "name": "Recover",
                "move_id": 0x69,
                "deltas": [
                    probe_delta(
                        "move.apply_move_model.apply_recovery_timing_discipline",
                        6,
                    ),
                ],
                "lookahead_delta": 18,
            },
            {
                "id": "move_spikes",
                "name": "Spikes",
                "move_id": 0xBF,
                "deltas": [
                    probe_delta("move.apply_move_model.enemy_under_pressure", -3),
                    probe_delta("move.apply_move_model.apply_role_bias", -3),
                ],
                "lookahead_delta": 18,
            },
        ],
        "expectation": {
            "best_action_ids": ["move_sludge_bomb"],
            "acceptable_action_ids": ["move_recover"],
            "condition_tags": ["high_pressure_ko_probe"],
            "lesson_type": "score_rule_probe",
            "confidence": "high",
            "why": "A public KO-pressure damage move executes the high-pressure gate and remains top.",
        },
        "materialization_patches": [
            probe_patch("wBattleMonStatus", 0),
            probe_patch("wBattleMonHP", 0, 0),
            probe_patch("wBattleMonHP", 20, 1),
            *PROBE_CLEAR_PLAYER_USED_MOVES,
        ],
    },
]

POLICY_CARD_REFS = {
    "active_pressure_before_status": (
        "docs/pokemon_mastery/policy_cards/active_pressure_before_status.md"
    ),
    "branch_action_after_naming": (
        "docs/pokemon_mastery/policy_cards/branch_action_after_naming.md"
    ),
    "cashout_boundary": "docs/pokemon_mastery/policy_cards/cashout_boundary.md",
    "hazard_loop_spin_window": (
        "docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md"
    ),
    "hidden_role_voluntary_entry": (
        "docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md"
    ),
    "romhack_mechanics_firewall": (
        "docs/pokemon_mastery/policy_cards/romhack_mechanics_firewall.md"
    ),
    "sleep_absorber_and_set_ambiguity": (
        "docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md"
    ),
    "support_handoff_after_job": (
        "docs/pokemon_mastery/policy_cards/support_handoff_after_job.md"
    ),
}

MASTERY_POLICY_CASES = [
    {
        "card_id": "active_pressure_before_status",
        "tiers": ("mid", "late"),
        "notes": [
            "generated mastery case: active pressure is already making route progress",
        ],
        "moves": [
            {
                "id": "move_active_pressure",
                "name": "Active Pressure",
                "deltas": [{"rule": "named active route pressure", "delta": -6}],
                "lookahead_delta": -1,
            },
            {
                "id": "move_status_script",
                "name": "Status Script",
                "deltas": [{"rule": "status exists but route is already active", "delta": -1}],
            },
            {
                "id": "move_pivot_out",
                "name": "Pivot Out",
                "deltas": [{"rule": "unpriced handoff", "delta": 1}],
            },
            {
                "id": "move_self_ko",
                "name": "Self-KO",
                "deltas": [{"rule": "premature cashout", "delta": 3}],
            },
        ],
        "expectation": {
            "best_action_ids": ["move_active_pressure"],
            "acceptable_action_ids": ["move_status_script"],
            "bad_action_ids": ["move_self_ko"],
            "policy_tags": ["active_pressure", "status_timing"],
            "condition_tags": ["active_pressure_before_status"],
            "lesson_type": "policy_card",
            "confidence": "medium",
            "why": "Price the direct pressure line before status or cash-out when it already advances a named route.",
            "answer_changing_information": [
                "whether status stops a route that damage cannot",
                "whether the support piece has no future entry or job",
            ],
        },
    },
    {
        "card_id": "branch_action_after_naming",
        "tiers": ("mid", "late"),
        "notes": [
            "generated mastery case: the likely receiver is named before choosing",
        ],
        "moves": [
            {
                "id": "move_receiver_coverage",
                "name": "Receiver Coverage",
                "deltas": [{"rule": "beats named receiver branch", "delta": -7}],
                "lookahead_delta": -1,
            },
            {
                "id": "move_counter_handoff",
                "name": "Counter-Handoff",
                "deltas": [{"rule": "owns next board", "delta": -3}],
            },
            {
                "id": "move_active_damage",
                "name": "Active Damage",
                "deltas": [{"rule": "only beats current active", "delta": -1}],
            },
            {
                "id": "move_generic_status",
                "name": "Generic Status",
                "deltas": [{"rule": "absorber branch unpriced", "delta": 2}],
            },
        ],
        "expectation": {
            "best_action_ids": ["move_receiver_coverage"],
            "acceptable_action_ids": ["move_counter_handoff"],
            "bad_action_ids": ["move_generic_status"],
            "policy_tags": ["branch_action", "receiver_pricing"],
            "condition_tags": ["named_receiver_branch"],
            "lesson_type": "policy_card",
            "confidence": "medium",
            "why": "After naming the likely branch, choose the action that beats that branch rather than the visible active alone.",
            "answer_changing_information": [
                "which receiver or absorber is likely",
                "whether the active move also changes the receiver board",
            ],
        },
    },
    {
        "card_id": "cashout_boundary",
        "tiers": ("mid", "late"),
        "notes": [
            "generated mastery case: a one-time trade has a named converter",
        ],
        "moves": [
            {
                "id": "move_cashout_converter",
                "name": "Cash Out Into Converter",
                "deltas": [{"rule": "named route trade", "delta": -8}],
                "lookahead_delta": -1,
            },
            {
                "id": "move_preserve_job",
                "name": "Preserve Support Job",
                "deltas": [{"rule": "support job mostly delivered", "delta": -2}],
            },
            {
                "id": "move_safe_status",
                "name": "Safe Status",
                "deltas": [{"rule": "misses converter window", "delta": 1}],
            },
            {
                "id": "move_chip_damage",
                "name": "Chip Damage",
                "deltas": [{"rule": "no converter named", "delta": 2}],
            },
        ],
        "expectation": {
            "best_action_ids": ["move_cashout_converter"],
            "acceptable_action_ids": ["move_preserve_job"],
            "bad_action_ids": ["move_chip_damage"],
            "policy_tags": ["cashout", "route_converter"],
            "condition_tags": ["one_time_trade_named_converter"],
            "lesson_type": "policy_card",
            "confidence": "medium",
            "why": "Cash out only when the target and post-trade converter are named and slow play can lose the window.",
            "answer_changing_information": [
                "whether the support job remains route-defining",
                "whether a revealed absorber or immunity blanks the trade",
            ],
        },
    },
    {
        "card_id": "hazard_loop_spin_window",
        "tiers": ("mid", "late"),
        "notes": [
            "generated mastery case: hazard progress is only real if Spin is priced",
        ],
        "moves": [
            {
                "id": "move_punish_spin",
                "name": "Punish Spin",
                "deltas": [{"rule": "keeps hazard route intact", "delta": -7}],
                "lookahead_delta": -1,
            },
            {
                "id": "move_attack_spinner",
                "name": "Attack Spinner",
                "deltas": [{"rule": "live damage into spinner", "delta": -3}],
            },
            {
                "id": "move_set_extra_spikes",
                "name": "Set Extra Spikes",
                "deltas": [{"rule": "free spin window", "delta": 4}],
            },
            {
                "id": "move_passive_handoff",
                "name": "Passive Handoff",
                "deltas": [{"rule": "spin route unresolved", "delta": 2}],
            },
        ],
        "expectation": {
            "best_action_ids": ["move_punish_spin"],
            "acceptable_action_ids": ["move_attack_spinner"],
            "bad_action_ids": ["move_set_extra_spikes"],
            "policy_tags": ["hazard_retention", "rapid_spin", "spikes"],
            "condition_tags": ["spin_window_priced"],
            "lesson_type": "policy_card",
            "confidence": "medium",
            "why": "Hazard progress is not stable if the opponent can remove it without paying a route-relevant cost.",
            "answer_changing_information": [
                "whether the spinner has an entry path",
                "whether a spinblocker is already active or safely available",
            ],
        },
    },
    {
        "card_id": "hidden_role_voluntary_entry",
        "tiers": ("early", "mid", "late"),
        "notes": [
            "generated mastery case: voluntary entry signals a role before species memory does",
        ],
        "moves": [
            {
                "id": "move_respect_lure",
                "name": "Respect Lure",
                "deltas": [{"rule": "revealed-role public evidence", "delta": -6}],
                "lookahead_delta": -1,
            },
            {
                "id": "move_scout_switch",
                "name": "Scout Switch",
                "deltas": [{"rule": "covers strong prior if wrong", "delta": -2}],
            },
            {
                "id": "move_species_template",
                "name": "Species Template",
                "deltas": [{"rule": "ignores voluntary entry", "delta": 3}],
            },
            {
                "id": "move_possible_only_read",
                "name": "Possible-Only Read",
                "deltas": [{"rule": "unrevealed move promoted to fact", "delta": 4}],
            },
        ],
        "expectation": {
            "best_action_ids": ["move_respect_lure"],
            "acceptable_action_ids": ["move_scout_switch"],
            "bad_action_ids": ["move_possible_only_read"],
            "policy_tags": ["hidden_role", "public_info_gate"],
            "condition_tags": ["voluntary_entry_role_signal"],
            "lesson_type": "policy_card",
            "confidence": "medium",
            "why": "Treat a voluntary bad-looking entry or set reveal as evidence, while keeping unrevealed moves at prior strength.",
            "answer_changing_information": [
                "which move or entry detail is public",
                "whether the standard role still explains the entry",
            ],
        },
    },
    {
        "card_id": "romhack_mechanics_firewall",
        "tiers": ("mid", "late"),
        "notes": [
            "generated mastery case: local mechanics evidence outranks imported vanilla knowledge",
        ],
        "moves": [
            {
                "id": "move_local_verified_line",
                "name": "Local Verified Line",
                "deltas": [{"rule": "runtime-verified local mechanic", "delta": -5}],
                "lookahead_delta": -1,
            },
            {
                "id": "move_neutral_route",
                "name": "Neutral Route",
                "deltas": [{"rule": "mechanic not decision-relevant", "delta": -1}],
            },
            {
                "id": "move_vanilla_assumption",
                "name": "Vanilla Assumption",
                "deltas": [{"rule": "unverified imported mechanic", "delta": 4}],
            },
            {
                "id": "move_haki_generalization",
                "name": "Haki Generalization",
                "deltas": [{"rule": "quarantined exception generalized", "delta": 5}],
            },
        ],
        "expectation": {
            "best_action_ids": ["move_local_verified_line"],
            "acceptable_action_ids": ["move_neutral_route"],
            "bad_action_ids": ["move_haki_generalization"],
            "policy_tags": ["romhack_mechanics", "no_cheat_boundary"],
            "condition_tags": ["local_mechanics_firewall"],
            "lesson_type": "policy_card",
            "confidence": "medium",
            "why": "Use local evidence for romhack mechanics and keep Haki/oracle exceptions quarantined from ordinary boss AI.",
            "answer_changing_information": [
                "local fixture or trace status for the mechanic",
                "whether the mechanic is decision-relevant",
            ],
        },
    },
    {
        "card_id": "sleep_absorber_and_set_ambiguity",
        "tiers": ("mid", "late"),
        "notes": [
            "generated mastery case: sleep state changes the route instead of starting a script",
        ],
        "moves": [
            {
                "id": "move_preserve_sleep_absorber",
                "name": "Preserve Sleep Absorber",
                "deltas": [{"rule": "keeps sleep-clause route value", "delta": -6}],
                "lookahead_delta": -1,
            },
            {
                "id": "move_active_absorber_job",
                "name": "Active Absorber Job",
                "deltas": [{"rule": "staying has a named job", "delta": -2}],
            },
            {
                "id": "move_burn_wake_turns",
                "name": "Burn Wake Turns",
                "deltas": [{"rule": "no active job named", "delta": 4}],
            },
            {
                "id": "move_status_sleeping_target",
                "name": "Status Sleeping Target",
                "deltas": [{"rule": "timing branch unresolved", "delta": 3}],
            },
        ],
        "expectation": {
            "best_action_ids": ["move_preserve_sleep_absorber"],
            "acceptable_action_ids": ["move_active_absorber_job"],
            "bad_action_ids": ["move_burn_wake_turns"],
            "policy_tags": ["sleep_absorber", "set_ambiguity"],
            "condition_tags": ["sleep_clause_value_preserved"],
            "lesson_type": "policy_card",
            "confidence": "medium",
            "why": "A sleeping Pokemon is route state; preserve it unless staying has a named active job.",
            "answer_changing_information": [
                "whether staying burns turns toward a useful job",
                "whether a revealed set changes the absorber map",
            ],
        },
    },
    {
        "card_id": "support_handoff_after_job",
        "tiers": ("mid", "late"),
        "notes": [
            "generated mastery case: support success must be converted on the next board",
        ],
        "moves": [
            {
                "id": "move_handoff_converter",
                "name": "Handoff Converter",
                "deltas": [{"rule": "names next board converter", "delta": -6}],
                "lookahead_delta": -1,
            },
            {
                "id": "move_cover_worst_branch",
                "name": "Cover Worst Branch",
                "deltas": [{"rule": "stops immediate reset branch", "delta": -2}],
            },
            {
                "id": "move_repeat_support",
                "name": "Repeat Support",
                "deltas": [{"rule": "support job already done", "delta": 4}],
            },
            {
                "id": "move_generic_damage",
                "name": "Generic Damage",
                "deltas": [{"rule": "converter unnamed", "delta": 2}],
            },
        ],
        "expectation": {
            "best_action_ids": ["move_handoff_converter"],
            "acceptable_action_ids": ["move_cover_worst_branch"],
            "bad_action_ids": ["move_repeat_support"],
            "policy_tags": ["support_handoff", "route_converter"],
            "condition_tags": ["support_job_completed"],
            "lesson_type": "policy_card",
            "confidence": "medium",
            "why": "After support lands, name the next board, converter, counter-pivot, and the resource needed for the handoff.",
            "answer_changing_information": [
                "whether the converter has an entry path",
                "whether the opponent can immediately reset with Spin, Rest, setup, or phaze",
            ],
        },
    },
]

PUBLIC_POLICY_CASES = {
    "switch_sack": [
        {
            "case_id": "preserve_wincon_over_comfort_damage",
            "tiers": ("mid", "late"),
            "notes": [
                "generated switch/sack case: current active can chip, but the route owner must be preserved",
            ],
            "moves": [
                {
                    "id": "move_comfort_damage",
                    "name": "Comfort Damage",
                    "kind": "move",
                    "deltas": [{"rule": "current active chip overvalued", "delta": -7}],
                    "lookahead_delta": -1,
                },
                {
                    "id": "move_preserve_wincon_switch",
                    "name": "Switch Preserve Wincon",
                    "kind": "switch",
                    "deltas": [{"rule": "safe entry to named owner", "delta": -2}],
                },
                {
                    "id": "move_support_status",
                    "name": "Support Status",
                    "kind": "move",
                    "deltas": [{"rule": "script without converter", "delta": 1}],
                },
                {
                    "id": "move_panic_cashout",
                    "name": "Panic Explosion",
                    "kind": "move",
                    "deltas": [{"rule": "spends preserved route piece", "delta": 5}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_preserve_wincon_switch"],
                "acceptable_action_ids": ["move_comfort_damage"],
                "bad_action_ids": ["move_panic_cashout"],
                "policy_tags": ["switching", "ace_preservation", "route_owner"],
                "condition_tags": [
                    "named_next_board_owner",
                    "safe_entry_available",
                    "ace_preservation",
                    "public_threat_to_active",
                ],
                "lesson_type": "weight_hint",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/heuristic_core/name_next_board_owner.md",
                    "docs/pokemon_mastery/heuristic_core/spend_or_save_piece.md",
                ],
                "why": "When the active can leave and a preserved owner owns the next board, rank the switch above comfortable chip.",
                "answer_changing_information": [
                    "whether the switch target enters safely",
                    "whether active damage also changes the receiver board",
                ],
            },
        },
        {
            "case_id": "defensive_sack_for_safe_entry",
            "tiers": ("mid", "late"),
            "notes": [
                "generated switch/sack case: a low-value sack creates safer entry than exposing the wincon",
            ],
            "moves": [
                {
                    "id": "move_switch_wincon_raw",
                    "name": "Raw Switch To Wincon",
                    "kind": "switch",
                    "deltas": [{"rule": "named wincon bias", "delta": -5}],
                },
                {
                    "id": "move_defensive_sack",
                    "name": "Defensive Sack For Safe Entry",
                    "kind": "switch",
                    "deltas": [{"rule": "sack preserves higher-value owner", "delta": -2}],
                    "lookahead_delta": -1,
                },
                {
                    "id": "move_last_chip",
                    "name": "Last Chip",
                    "kind": "move",
                    "deltas": [{"rule": "low piece attacks without handoff", "delta": 2}],
                },
                {
                    "id": "move_repeat_support",
                    "name": "Repeat Support",
                    "kind": "move",
                    "deltas": [{"rule": "support job already delivered", "delta": 4}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_defensive_sack"],
                "acceptable_action_ids": ["move_switch_wincon_raw"],
                "bad_action_ids": ["move_repeat_support"],
                "policy_tags": ["switching", "defensive_sack", "safe_entry"],
                "condition_tags": [
                    "defensive_sack_owner",
                    "safe_entry_available",
                    "wincon_preservation",
                    "support_job_completed",
                ],
                "lesson_type": "weight_hint",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/policy_cards/cashout_boundary.md",
                    "docs/pokemon_mastery/heuristic_core/spend_or_save_piece.md",
                ],
                "why": "A sack can be the positive move when it preserves the higher-value owner and creates clean entry.",
                "answer_changing_information": [
                    "whether the wincon takes route-losing damage on raw entry",
                    "whether the sack still has a future route job",
                ],
            },
        },
        {
            "case_id": "stay_when_current_move_converts",
            "tiers": ("early", "mid", "late"),
            "notes": [
                "generated switch/sack case: switching is tempting, but active pressure already converts",
            ],
            "moves": [
                {
                    "id": "move_route_damage",
                    "name": "Route Damage",
                    "kind": "move",
                    "deltas": [{"rule": "current pressure converts", "delta": -9}],
                },
                {
                    "id": "move_safe_switch",
                    "name": "Safe Switch",
                    "kind": "switch",
                    "deltas": [{"rule": "safe but gives up active conversion", "delta": -2}],
                },
                {
                    "id": "move_status_script",
                    "name": "Status Script",
                    "kind": "move",
                    "deltas": [{"rule": "script after converter", "delta": 2}],
                },
                {
                    "id": "move_cashout",
                    "name": "Explosion Cashout",
                    "kind": "move",
                    "deltas": [{"rule": "no named converter", "delta": 5}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_route_damage"],
                "acceptable_action_ids": ["move_safe_switch"],
                "bad_action_ids": ["move_cashout"],
                "policy_tags": ["active_pressure", "switching", "converter"],
                "condition_tags": ["active_pressure_converts", "named_current_owner"],
                "lesson_type": "hard_rule",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/policy_cards/active_pressure_before_status.md",
                    "docs/pokemon_mastery/heuristic_core/converter_before_script.md",
                ],
                "why": "Do not switch or cash out when the current active move is already the converter.",
                "answer_changing_information": [
                    "whether the active move fails into the named receiver",
                    "whether the active is removed before converting",
                ],
            },
        },
    ],
    "setup_heal": [
        {
            "case_id": "setup_once_in_real_window",
            "tiers": ("mid", "late"),
            "notes": [
                "generated setup/heal case: one boost is route-changing because the receiver cannot reset it",
            ],
            "moves": [
                {
                    "id": "move_safe_setup",
                    "name": "Curse Setup Window",
                    "kind": "move",
                    "deltas": [{"rule": "setup identity", "delta": -3}],
                    "lookahead_delta": -3,
                },
                {
                    "id": "move_neutral_hit",
                    "name": "Neutral Hit",
                    "kind": "move",
                    "deltas": [{"rule": "visible chip", "delta": -4}],
                },
                {
                    "id": "move_switch_out",
                    "name": "Switch Out",
                    "kind": "switch",
                    "deltas": [{"rule": "gives up setup board", "delta": 3}],
                },
                {
                    "id": "move_recover",
                    "name": "Recover",
                    "kind": "move",
                    "deltas": [{"rule": "healing before route exists", "delta": 4}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_safe_setup"],
                "acceptable_action_ids": ["move_neutral_hit"],
                "bad_action_ids": ["move_recover"],
                "policy_tags": ["setup", "receiver_pricing", "route_converter"],
                "condition_tags": [
                    "setup_window",
                    "named_receiver_branch",
                    "reset_loop_denied",
                    "worst_case_guarded",
                ],
                "lesson_type": "weight_hint",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/policy_cards/branch_action_after_naming.md",
                    "docs/pokemon_mastery/heuristic_core/reset_loop_denial.md",
                ],
                "why": "Setup is positive only when it changes the named receiver board before reset or phaze can erase it.",
                "answer_changing_information": [
                    "whether the receiver can phaze, Haze, recover, or KO",
                    "whether one boost changes the next damage threshold",
                ],
            },
        },
        {
            "case_id": "stop_setup_when_attack_converts",
            "tiers": ("mid", "late"),
            "notes": [
                "generated setup/heal case: more setup is a loop once an attack already converts",
            ],
            "moves": [
                {
                    "id": "move_more_setup",
                    "name": "More Curse",
                    "kind": "move",
                    "deltas": [{"rule": "setup identity overvalued", "delta": -5}],
                },
                {
                    "id": "move_cashout_attack",
                    "name": "Cashout Attack",
                    "kind": "move",
                    "deltas": [{"rule": "attack converts boosted route", "delta": -3}],
                    "lookahead_delta": -2,
                },
                {
                    "id": "move_recover_loop",
                    "name": "Recover Loop",
                    "kind": "move",
                    "deltas": [{"rule": "preserves but misses timer", "delta": 2}],
                },
                {
                    "id": "move_handoff",
                    "name": "Handoff",
                    "kind": "switch",
                    "deltas": [{"rule": "unneeded handoff", "delta": 3}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_cashout_attack"],
                "acceptable_action_ids": ["move_recover_loop"],
                "bad_action_ids": ["move_more_setup"],
                "policy_tags": ["setup", "cashout", "reset_loop_denial"],
                "condition_tags": [
                    "setup_already_bankrolled",
                    "active_pressure_converts",
                    "timer_pressure",
                ],
                "lesson_type": "hard_rule",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/policy_cards/branch_action_after_naming.md",
                    "docs/pokemon_mastery/heuristic_core/converter_before_script.md",
                ],
                "why": "Once the boosted route already converts, another setup turn is worse than cashing out the attack.",
                "answer_changing_information": [
                    "whether the attack misses the required range",
                    "whether healing is required before the route is lost",
                ],
            },
        },
        {
            "case_id": "heal_only_when_it_preserves_route",
            "tiers": ("mid", "late"),
            "notes": [
                "generated setup/heal case: recovery is a route-preservation move, not a panic button",
            ],
            "moves": [
                {
                    "id": "move_recover_route",
                    "name": "Recover Route",
                    "kind": "move",
                    "deltas": [{"rule": "recovery preserves named owner", "delta": -6}],
                },
                {
                    "id": "move_weak_attack",
                    "name": "Weak Attack",
                    "kind": "move",
                    "deltas": [{"rule": "does not cross threshold", "delta": -2}],
                },
                {
                    "id": "move_status",
                    "name": "Toxic",
                    "kind": "move",
                    "deltas": [{"rule": "status into reset loop", "delta": 3}],
                },
                {
                    "id": "move_switch",
                    "name": "Switch Handoff",
                    "kind": "switch",
                    "deltas": [{"rule": "handoff loses preserved route", "delta": 4}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_recover_route"],
                "acceptable_action_ids": ["move_weak_attack"],
                "bad_action_ids": ["move_status"],
                "policy_tags": ["healing", "recovery", "route_preservation"],
                "condition_tags": [
                    "recovery_preserves_route",
                    "no_immediate_pressure",
                    "named_current_owner",
                ],
                "lesson_type": "weight_hint",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/worked_examples/misty_starmie_meganium_recover_tempo.md",
                    "docs/pokemon_mastery/heuristic_core/spend_or_save_piece.md",
                ],
                "why": "Heal when the restored HP keeps the named route alive; otherwise rank conversion first.",
                "answer_changing_information": [
                    "whether the next hit removes the route through recovery",
                    "whether the attack crosses a decisive threshold now",
                ],
            },
        },
    ],
    "prediction_mix": [
        {
            "case_id": "coverage_into_named_receiver",
            "tiers": ("mid", "late"),
            "notes": [
                "generated prediction case: the receiver branch is public enough to punish",
            ],
            "moves": [
                {
                    "id": "move_obvious_stab",
                    "name": "Obvious Active STAB",
                    "kind": "move",
                    "deltas": [{"rule": "beats visible active only", "delta": -6}],
                },
                {
                    "id": "move_receiver_coverage",
                    "name": "Prediction Receiver Coverage",
                    "kind": "move",
                    "deltas": [{"rule": "branch coverage underweighted", "delta": -2}],
                    "lookahead_delta": -2,
                },
                {
                    "id": "move_counter_handoff",
                    "name": "Counter Handoff",
                    "kind": "switch",
                    "deltas": [{"rule": "owns next board if branch occurs", "delta": -1}],
                },
                {
                    "id": "move_status_script",
                    "name": "Status Script",
                    "kind": "move",
                    "deltas": [{"rule": "absorber branch unpriced", "delta": 4}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_receiver_coverage"],
                "acceptable_action_ids": ["move_counter_handoff", "move_obvious_stab"],
                "bad_action_ids": ["move_status_script"],
                "policy_tags": ["prediction", "branch_action", "receiver_pricing"],
                "condition_tags": [
                    "named_receiver_branch",
                    "prediction_branch_supported",
                    "worst_case_guarded",
                    "prediction_ev_positive",
                ],
                "lesson_type": "weight_hint",
                "confidence": "medium",
                "min_best_probability": 0.55,
                "evidence_refs": [
                    "docs/pokemon_mastery/policy_cards/branch_action_after_naming.md",
                    "docs/pokemon_mastery/heuristic_core/branch_punish_ranking.md",
                ],
                "why": "Prediction is correct when public receiver probability and payoff beat the obvious line with bounded downside.",
                "answer_changing_information": [
                    "whether the receiver branch is actually public-supported",
                    "how much the coverage loses if the active stays in",
                ],
            },
        },
        {
            "case_id": "reject_reckless_prediction",
            "tiers": ("mid", "late"),
            "notes": [
                "generated prediction case: the flashy read loses too much if wrong",
            ],
            "moves": [
                {
                    "id": "move_safe_active_ko",
                    "name": "Safe Active KO",
                    "kind": "move",
                    "deltas": [{"rule": "visible KO", "delta": -6}],
                },
                {
                    "id": "move_reckless_prediction",
                    "name": "Reckless Prediction Coverage",
                    "kind": "move",
                    "deltas": [{"rule": "speculative branch payoff", "delta": -7}],
                    "lookahead_delta": 2,
                },
                {
                    "id": "move_safe_handoff",
                    "name": "Safe Handoff",
                    "kind": "switch",
                    "deltas": [{"rule": "covers worst branch modestly", "delta": -1}],
                },
                {
                    "id": "move_repeat_setup",
                    "name": "Repeat Setup",
                    "kind": "move",
                    "deltas": [{"rule": "greedy into live punishment", "delta": 5}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_safe_active_ko"],
                "acceptable_action_ids": ["move_safe_handoff"],
                "bad_action_ids": ["move_reckless_prediction", "move_repeat_setup"],
                "policy_tags": ["prediction", "risk_control", "active_pressure"],
                "condition_tags": [
                    "prediction_branch_possible_only",
                    "worst_case_unguarded",
                    "active_pressure_converts",
                ],
                "lesson_type": "hard_rule",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/policy_cards/branch_action_after_naming.md",
                    "docs/pokemon_mastery/heuristic_core/public_info_tiers.md",
                ],
                "why": "Do not make a high-downside read top when the active conversion is already public and safe.",
                "answer_changing_information": [
                    "whether the branch has moved from possible-only to strong-prior",
                    "whether missing the prediction still preserves the route",
                ],
            },
        },
        {
            "case_id": "near_tie_mix_surface",
            "tiers": ("late",),
            "notes": [
                "generated prediction case: two public lines are close enough to mix without forcing determinism",
            ],
            "moves": [
                {
                    "id": "move_safe_default",
                    "name": "Safe Default",
                    "kind": "move",
                    "deltas": [{"rule": "safe default line", "delta": -4}],
                },
                {
                    "id": "move_low_risk_prediction",
                    "name": "Low Risk Prediction Branch",
                    "kind": "move",
                    "deltas": [{"rule": "bounded branch punish", "delta": -3}],
                },
                {
                    "id": "move_counter_switch",
                    "name": "Counter Switch",
                    "kind": "switch",
                    "deltas": [{"rule": "acceptable if receiver branch occurs", "delta": -2}],
                },
                {
                    "id": "move_all_in_read",
                    "name": "All In Read",
                    "kind": "move",
                    "deltas": [{"rule": "unbounded read", "delta": 6}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_safe_default", "move_low_risk_prediction"],
                "acceptable_action_ids": ["move_counter_switch"],
                "bad_action_ids": ["move_all_in_read"],
                "policy_tags": ["prediction", "mixed_strategy", "risk_control"],
                "condition_tags": [
                    "prediction_branch_supported",
                    "worst_case_guarded",
                    "near_tie_mix",
                ],
                "lesson_type": "weight_hint",
                "confidence": "medium",
                "min_best_probability": 0.50,
                "evidence_refs": [
                    "docs/pokemon_mastery/workspace/quick_tests/branch_action_mixed_probe_001_2026-05-14.md",
                    "docs/pokemon_mastery/heuristic_core/branch_punish_ranking.md",
                ],
                "why": "When the default and low-risk branch punish are close, preserve both as rollable instead of enforcing a single obvious move.",
                "answer_changing_information": [
                    "whether one line becomes clearly dominant",
                    "whether the branch punish becomes unbounded if wrong",
                ],
            },
        },
    ],
    "support_handoff": [
        {
            "case_id": "handoff_after_support_lands",
            "tiers": ("mid", "late"),
            "notes": [
                "generated support case: support already landed, so repeating it misses the conversion",
            ],
            "moves": [
                {
                    "id": "move_repeat_support",
                    "name": "Repeat Support",
                    "kind": "move",
                    "deltas": [{"rule": "support identity overvalued", "delta": -5}],
                },
                {
                    "id": "move_handoff_converter",
                    "name": "Handoff Converter",
                    "kind": "switch",
                    "deltas": [{"rule": "names next-board converter", "delta": -2}],
                    "lookahead_delta": -2,
                },
                {
                    "id": "move_cover_reset",
                    "name": "Cover Reset Branch",
                    "kind": "move",
                    "deltas": [{"rule": "denies immediate reset branch", "delta": -1}],
                },
                {
                    "id": "move_generic_damage",
                    "name": "Generic Damage",
                    "kind": "move",
                    "deltas": [{"rule": "converter unnamed", "delta": 3}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_handoff_converter"],
                "acceptable_action_ids": ["move_cover_reset"],
                "bad_action_ids": ["move_repeat_support"],
                "policy_tags": ["support_handoff", "route_converter", "reset_loop_denial"],
                "condition_tags": [
                    "support_job_completed",
                    "named_next_board_owner",
                    "reset_loop_live",
                ],
                "lesson_type": "weight_hint",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/policy_cards/support_handoff_after_job.md",
                    "docs/pokemon_mastery/heuristic_core/name_next_board_owner.md",
                ],
                "why": "After support succeeds, convert or cover the reset branch instead of repeating the support move.",
                "answer_changing_information": [
                    "whether the converter has a safe entry path",
                    "whether the reset branch must be covered immediately",
                ],
            },
        },
        {
            "case_id": "status_absorber_branch_punish",
            "tiers": ("mid", "late"),
            "notes": [
                "generated support case: status is bad into a named absorber unless it hits the branch target",
            ],
            "moves": [
                {
                    "id": "move_generic_status",
                    "name": "Generic Toxic",
                    "kind": "move",
                    "deltas": [{"rule": "status identity overvalued", "delta": -6}],
                },
                {
                    "id": "move_absorber_coverage",
                    "name": "Absorber Coverage",
                    "kind": "move",
                    "deltas": [{"rule": "hits named absorber", "delta": -2}],
                    "lookahead_delta": -1,
                },
                {
                    "id": "move_counter_handoff",
                    "name": "Counter Handoff",
                    "kind": "switch",
                    "deltas": [{"rule": "owns absorber board", "delta": -1}],
                },
                {
                    "id": "move_passive_reset",
                    "name": "Passive Reset",
                    "kind": "move",
                    "deltas": [{"rule": "hands back reset loop", "delta": 4}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_absorber_coverage"],
                "acceptable_action_ids": ["move_counter_handoff"],
                "bad_action_ids": ["move_generic_status", "move_passive_reset"],
                "policy_tags": ["status_timing", "branch_action", "receiver_pricing"],
                "condition_tags": [
                    "status_absorber_named",
                    "named_receiver_branch",
                    "branch_punish_available",
                ],
                "lesson_type": "hard_rule",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/policy_cards/branch_action_after_naming.md",
                    "docs/pokemon_mastery/policy_cards/active_pressure_before_status.md",
                ],
                "why": "When a status absorber is named, rank the coverage or handoff that beats it before generic status.",
                "answer_changing_information": [
                    "whether the status move hits the incoming branch",
                    "whether coverage also affects the visible active",
                ],
            },
        },
        {
            "case_id": "phaze_loop_over_generic_chip",
            "tiers": ("mid", "late"),
            "notes": [
                "generated support case: public phazing plus hazards can be the converter",
            ],
            "moves": [
                {
                    "id": "move_generic_chip",
                    "name": "Generic Chip",
                    "kind": "move",
                    "deltas": [{"rule": "visible chip overvalued", "delta": -5}],
                },
                {
                    "id": "move_roar_loop",
                    "name": "Roar Phaze Loop",
                    "kind": "move",
                    "deltas": [{"rule": "phaze loop underweighted", "delta": -2}],
                    "lookahead_delta": -2,
                },
                {
                    "id": "move_spikes_reset",
                    "name": "Spikes Reset",
                    "kind": "move",
                    "deltas": [{"rule": "hazard reset acceptable", "delta": -1}],
                },
                {
                    "id": "move_switch_away",
                    "name": "Switch Away",
                    "kind": "switch",
                    "deltas": [{"rule": "abandons phaze loop", "delta": 4}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_roar_loop"],
                "acceptable_action_ids": ["move_spikes_reset"],
                "bad_action_ids": ["move_switch_away"],
                "policy_tags": ["phazing", "hazard_retention", "reset_loop_denial"],
                "condition_tags": [
                    "spikes_layers_2",
                    "phaze_loop_live",
                    "reset_loop_denied",
                    "named_current_owner",
                ],
                "lesson_type": "weight_hint",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md",
                    "docs/pokemon_mastery/heuristic_core/reset_loop_denial.md",
                ],
                "why": "When hazards and public phazing own the route, keep the phaze loop above generic chip or retreat.",
                "answer_changing_information": [
                    "whether the opponent has a live Spin, Recover, or phaze counter-loop",
                    "whether chip forces an immediate irreversible threshold",
                ],
            },
        },
    ],
    "cashout_board_delta": [
        {
            "case_id": "reversible_before_irreversible",
            "tiers": ("mid", "late"),
            "notes": [
                "generated newest-mastery case: a reversible branch-covering move preserves the one-shot converter",
            ],
            "moves": [
                {
                    "id": "move_boom_now",
                    "name": "Explosion Now",
                    "kind": "move",
                    "deltas": [{"rule": "one-shot converter overvalued", "delta": -7}],
                },
                {
                    "id": "move_reversible_branch_cover",
                    "name": "Earthquake Branch Cover",
                    "kind": "move",
                    "deltas": [{"rule": "covers active and named branch", "delta": -2}],
                    "lookahead_delta": -2,
                },
                {
                    "id": "move_counter_handoff",
                    "name": "Counter Handoff",
                    "kind": "switch",
                    "deltas": [{"rule": "preserves converter for next forced choice", "delta": -1}],
                },
                {
                    "id": "move_status_script",
                    "name": "Status Script",
                    "kind": "move",
                    "deltas": [{"rule": "script misses branch", "delta": 3}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_reversible_branch_cover"],
                "acceptable_action_ids": ["move_counter_handoff"],
                "bad_action_ids": ["move_boom_now", "move_status_script"],
                "policy_tags": [
                    "cashout",
                    "reversible_before_irreversible",
                    "branch_action",
                    "risk_control",
                ],
                "condition_tags": [
                    "reversible_line_covers_active_and_branch",
                    "irreversible_converter_preserved",
                    "delay_does_not_reset_target",
                ],
                "lesson_type": "hard_rule",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/reviews/training_method_review_004_2026-05-15.md",
                    "docs/pokemon_mastery/heuristic_core/spend_or_save_piece.md",
                    "docs/pokemon_mastery/policy_cards/cashout_boundary.md",
                ],
                "why": "Prefer the reversible line when it covers the active target and named branch while preserving the irreversible converter.",
                "answer_changing_information": [
                    "whether delay lets the target reset, escape, or remove the user",
                    "whether the reversible line still covers the named branch",
                ],
            },
        },
        {
            "case_id": "resisted_explosion_free_owner",
            "tiers": ("mid", "late"),
            "notes": [
                "generated newest-mastery case: Explosion into a resist is positive when chip and denial create the next owner",
            ],
            "moves": [
                {
                    "id": "move_earthquake_active",
                    "name": "Earthquake Active",
                    "kind": "move",
                    "deltas": [{"rule": "active damage overvalued", "delta": -5}],
                },
                {
                    "id": "move_explosion_board_delta",
                    "name": "Explosion Board Delta",
                    "kind": "move",
                    "deltas": [{"rule": "resisted trade creates free owner", "delta": -2}],
                    "lookahead_delta": -4,
                },
                {
                    "id": "move_preserve_piece",
                    "name": "Preserve Piece",
                    "kind": "switch",
                    "deltas": [{"rule": "preserve but gives reset turn", "delta": 1}],
                },
                {
                    "id": "move_generic_status",
                    "name": "Generic Status",
                    "kind": "move",
                    "deltas": [{"rule": "misses conversion window", "delta": 4}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_explosion_board_delta"],
                "acceptable_action_ids": ["move_earthquake_active"],
                "bad_action_ids": ["move_generic_status"],
                "policy_tags": [
                    "cashout",
                    "resisted_explosion_board_delta",
                    "route_converter",
                ],
                "condition_tags": [
                    "resisted_explosion_free_owner",
                    "post_trade_owner_named",
                    "active_damage_misses_receiver",
                ],
                "lesson_type": "weight_hint",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/workspace/quick_tests/resisted_explosion_board_delta_drill_001_2026-05-15.md",
                    "docs/pokemon_mastery/policy_cards/cashout_boundary.md",
                ],
                "why": "A resisted self-KO can be correct when it denies the receiver's action and gives the named owner a free board.",
                "answer_changing_information": [
                    "whether the resisted target survives outside the next owner's range",
                    "whether preserving the user gives the target a reset turn",
                ],
            },
        },
        {
            "case_id": "explosion_into_ghost_branch",
            "tiers": ("mid", "late"),
            "notes": [
                "generated newest-mastery case: revealed Ghost branch makes unguarded cash-out bad",
            ],
            "moves": [
                {
                    "id": "move_explosion_read",
                    "name": "Explosion Read",
                    "kind": "move",
                    "deltas": [
                        {"rule": "cashout overvalued into immunity branch", "delta": -8},
                        {
                            "rule": "move.apply_move_model.self_ko_seen_ghost_branch",
                            "delta": 8,
                        },
                    ],
                },
                {
                    "id": "move_earthquake_branch_cover",
                    "name": "Earthquake Branch Cover",
                    "kind": "move",
                    "deltas": [{"rule": "hits active and Ghost branch", "delta": -2}],
                    "lookahead_delta": -2,
                },
                {
                    "id": "move_preserve_handoff",
                    "name": "Preserve Handoff",
                    "kind": "switch",
                    "deltas": [{"rule": "preserves one-shot converter", "delta": -1}],
                },
                {
                    "id": "move_soft_status",
                    "name": "Soft Status",
                    "kind": "move",
                    "deltas": [{"rule": "does not beat immunity branch", "delta": 3}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_earthquake_branch_cover"],
                "acceptable_action_ids": ["move_preserve_handoff"],
                "bad_action_ids": ["move_explosion_read"],
                "policy_tags": [
                    "cashout",
                    "reversible_before_irreversible",
                    "branch_action",
                    "public_info_gate",
                ],
                "condition_tags": [
                    "revealed_ghost_absorber",
                    "cashout_immunity_guard",
                    "reversible_line_covers_active_and_branch",
                ],
                "lesson_type": "hard_rule",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/workspace/quick_tests/resisted_explosion_board_delta_drill_001_2026-05-15.md",
                    "docs/pokemon_mastery/policy_cards/cashout_boundary.md",
                ],
                "why": "Do not make Explosion top when a revealed immunity branch can enter and a reversible line covers more public branches.",
                "answer_changing_information": [
                    "whether the Ghost branch is actually revealed or only possible",
                    "whether slow play lets the active target reset",
                ],
            },
        },
        {
            "case_id": "sleep_plus_cashout_package",
            "tiers": ("mid", "late"),
            "notes": [
                "generated newest-mastery case: sleep plus self-KO is one public role package",
            ],
            "moves": [
                {
                    "id": "move_valuable_damage",
                    "name": "Valuable Owner Damage",
                    "kind": "move",
                    "deltas": [{"rule": "damage ignores sleep-cashout package", "delta": -6}],
                },
                {
                    "id": "move_low_value_guard",
                    "name": "Low Value Guard",
                    "kind": "switch",
                    "deltas": [{"rule": "absorbs sleep plus cashout package", "delta": -2}],
                    "lookahead_delta": -2,
                },
                {
                    "id": "move_status_back",
                    "name": "Status Back",
                    "kind": "move",
                    "deltas": [{"rule": "status into sleep package", "delta": 3}],
                },
                {
                    "id": "move_setup_greed",
                    "name": "Setup Greed",
                    "kind": "move",
                    "deltas": [{"rule": "gives self-KO target", "delta": 5}],
                },
            ],
            "expectation": {
                "best_action_ids": ["move_low_value_guard"],
                "acceptable_action_ids": ["move_valuable_damage"],
                "bad_action_ids": ["move_setup_greed"],
                "policy_tags": [
                    "role_package_ledger",
                    "sleep_plus_cashout_package",
                    "switch_sack",
                    "cashout",
                ],
                "condition_tags": [
                    "sleep_move_revealed",
                    "self_ko_strong_prior",
                    "low_value_absorber_available",
                ],
                "lesson_type": "hard_rule",
                "confidence": "medium",
                "evidence_refs": [
                    "docs/pokemon_mastery/heuristic_core/role_package_ledger.md",
                    "docs/pokemon_mastery/policy_cards/cashout_boundary.md",
                ],
                "why": "Once sleep plus cash-out is public or strong-prior, answer the package with a lower-value guard before exposing the key owner.",
                "answer_changing_information": [
                    "whether self-KO has been disproved by four revealed moves",
                    "whether the low-value guard still has an undelivered route job",
                ],
            },
        },
    ],
}


def generate_scenarios(
    *,
    family: str,
    count: int,
    seed: int,
) -> list[dict[str, Any]]:
    if count < 0:
        raise PreferenceDataError("count must be non-negative")
    if family not in FAMILIES:
        raise PreferenceDataError(f"unknown generator family {family!r}")
    rng = random.Random(seed)
    if family == "all":
        families = ALL_FAMILY_SEQUENCE
        family_counts = {name: 0 for name in FAMILIES if name != "all"}
        scenarios: list[dict[str, Any]] = []
        for index in range(count):
            chosen = families[index % len(families)]
            child_index = family_counts[chosen]
            family_counts[chosen] = child_index + 1
            scenarios.append(stamp_scenario(generate_one(chosen, child_index, rng, seed)))
        return scenarios
    return [stamp_scenario(generate_one(family, index, rng, seed)) for index in range(count)]


def generate_one(
    family: str,
    index: int,
    rng: random.Random,
    seed: int,
) -> dict[str, Any]:
    if family == "selector_edges":
        return selector_edge_scenario(index, rng, seed)
    if family == "spikes_spin":
        return spikes_spin_scenario(index, rng, seed)
    if family == "score_rule_probe":
        return score_rule_probe_scenario(index, rng, seed)
    if family == "mastery_policy":
        return mastery_policy_scenario(index, rng, seed)
    if family in PUBLIC_POLICY_CASES:
        return public_policy_scenario(family, index, rng, seed)
    raise PreferenceDataError(f"unknown generator family {family!r}")


def selector_edge_scenario(index: int, rng: random.Random, seed: int) -> dict[str, Any]:
    tier = rng.choice(["early", "mid", "late"])
    shape = rng.choice(["all_equal", "blocked_best", "third_tied", "wide_gap"])
    moves = [
        {"id": "slot1", "name": "Slot 1"},
        {"id": "slot2", "name": "Slot 2"},
        {"id": "slot3", "name": "Slot 3"},
        {"id": "slot4", "name": "Slot 4"},
    ]
    expectation: dict[str, Any]
    if shape == "all_equal":
        expectation = {
            "best_action_ids": ["slot1"],
            "acceptable_action_ids": ["slot2"],
            "bad_action_ids": ["slot3", "slot4"],
            "policy_tags": ["selector_surface"],
            "condition_tags": ["equal_scores", "best_second_only"],
            "confidence": "high",
            "why": "Equal scores should roll only the first best and first second slot.",
        }
    elif shape == "blocked_best":
        moves[0]["blocked"] = True
        moves[1]["deltas"] = [{"rule": "live move", "delta": -1}]
        expectation = {
            "best_action_ids": ["slot2"],
            "bad_action_ids": ["slot1"],
            "policy_tags": ["selector_surface"],
            "condition_tags": ["blocked_score_ignored"],
            "confidence": "high",
            "why": "Scores at 80 or higher must have zero selector probability.",
        }
    elif shape == "third_tied":
        moves[0]["deltas"] = [{"rule": "small encourage", "delta": -1}]
        moves[3]["deltas"] = [{"rule": "small discourage", "delta": 1}]
        expectation = {
            "best_action_ids": ["slot1"],
            "acceptable_action_ids": ["slot2"],
            "bad_action_ids": ["slot3", "slot4"],
            "policy_tags": ["selector_surface"],
            "condition_tags": ["third_slot_tied_second"],
            "confidence": "high",
            "why": "The selector only rolls between best and the first second-best slot.",
        }
    else:
        moves[0]["deltas"] = [{"rule": "large encourage", "delta": -8}]
        moves[1]["deltas"] = [{"rule": "small encourage", "delta": -1}]
        expectation = {
            "best_action_ids": ["slot1"],
            "acceptable_action_ids": ["slot2"],
            "policy_tags": ["selector_surface"],
            "condition_tags": ["wide_gap"],
            "confidence": "high",
            "min_best_probability": 0.85,
            "why": "Large score gaps should make the best move strongly favored.",
        }
    return {
        "id": f"generated_selector_edges_{seed}_{index:05d}_{shape}",
        "generator": DEFAULT_GENERATOR_VERSION,
        "family": "selector_edges",
        "seed": seed,
        "case_index": index,
        "tier": tier,
        "notes": [f"generated selector edge case: {shape}"],
        "moves": moves,
        "expectation": expectation,
    }


def score_rule_probe_scenario(index: int, rng: random.Random, seed: int) -> dict[str, Any]:
    case = SCORE_RULE_PROBE_CASES[index % len(SCORE_RULE_PROBE_CASES)]
    scenario = deepcopy(case)
    scenario["id"] = (
        f"generated_score_rule_probe_{seed}_{index:05d}_{case['case_id']}"
    )
    scenario["family"] = "score_rule_probe"
    scenario["tier"] = "late"
    return scenario


def spikes_spin_scenario(index: int, rng: random.Random, seed: int) -> dict[str, Any]:
    tier = rng.choice(["mid", "late"])
    layers = rng.choice([0, 1, 2, 3])
    active_revealed_spin = rng.choice([False, True])
    active_ghost = rng.choice([False, True])
    foresighted = rng.choice([False, True]) if active_ghost else False
    reserve_ghost = rng.choice([False, True])
    bench_revealed_spin = rng.choice([False, True])
    active_species_prior = rng.choice([False, True])
    immediate_pressure = active_species_prior and not active_ghost

    condition_tags = [f"spikes_layers_{layers}"]
    if active_revealed_spin:
        condition_tags.append("active_revealed_rapid_spin")
    if active_ghost:
        condition_tags.append("active_ghost_spinblock")
    if foresighted:
        condition_tags.append("foresight_identified_ghost")
    if reserve_ghost:
        condition_tags.append("reserve_ghost_available")
    if bench_revealed_spin:
        condition_tags.append("bench_revealed_rapid_spin")
    if active_species_prior:
        condition_tags.append("active_species_spin_prior")
    if immediate_pressure:
        condition_tags.append("immediate_pressure")

    rom_deltas = materialized_spikes_spin_rom_deltas(
        tier=tier,
        layers=layers,
        active_revealed_spin=active_revealed_spin,
        active_ghost=active_ghost,
        foresighted=foresighted,
        reserve_ghost=reserve_ghost,
        bench_revealed_spin=bench_revealed_spin,
        active_species_prior=active_species_prior,
    )
    active_spinblock = active_ghost and not foresighted
    spinblock_available = active_spinblock or reserve_ghost
    active_spin_risk = active_revealed_spin and layers in {1, 2} and not active_spinblock
    bench_spin_risk = (
        bench_revealed_spin
        and layers == 2
        and not spinblock_available
    )

    moves = [
        {
            "id": "move_spikes",
            "name": "Spikes",
            "deltas": rom_deltas["spikes"],
            "lookahead_delta": rom_deltas["lookahead"]["spikes"],
        },
        {
            "id": "move_sludge_bomb",
            "name": "Sludge Bomb",
            "deltas": rom_deltas["sludge_bomb"],
            "lookahead_delta": rom_deltas["lookahead"]["sludge_bomb"],
        },
        {
            "id": "move_surf",
            "name": "Surf",
            "deltas": rom_deltas["surf"],
            "lookahead_delta": rom_deltas["lookahead"]["surf"],
        },
        {
            "id": "move_explosion",
            "name": "Explosion",
            "deltas": rom_deltas["explosion"],
            "lookahead_delta": rom_deltas["lookahead"]["explosion"],
        },
    ]

    if layers == 3:
        best = ["move_sludge_bomb"]
        bad = ["move_spikes"]
        why = "A fourth local Spikes click fails after the stack is already capped."
        lesson_type = "hard_rule"
    elif active_spin_risk or bench_spin_risk:
        best = ["move_sludge_bomb"]
        bad = ["move_spikes"]
        why = "Public Rapid Spin pressure threatens to erase the stack before another layer pays off."
        lesson_type = "hard_rule"
    elif immediate_pressure and layers > 0:
        best = ["move_sludge_bomb"]
        bad = ["move_spikes"]
        why = "Immediate pressure can make another hazard turn too slow."
        lesson_type = "weight_hint"
    else:
        best = ["move_spikes"]
        bad = []
        why = "When spin risk is absent or spinblocked, another useful Spikes layer can be the route-progress move."
        lesson_type = "weight_hint"

    return {
        "id": f"generated_spikes_spin_{seed}_{index:05d}",
        "generator": DEFAULT_GENERATOR_VERSION,
        "family": "spikes_spin",
        "seed": seed,
        "case_index": index,
        "tier": tier,
        "notes": [
            "generated Spikes/Rapid Spin boundary case",
            f"layers={layers} active_revealed_spin={active_revealed_spin} active_ghost={active_ghost}",
        ],
        "moves": moves,
        "expectation": {
            "best_action_ids": best,
            "acceptable_action_ids": ["move_explosion"] if active_revealed_spin else [],
            "bad_action_ids": bad,
            "policy_tags": ["hazard_retention", "rapid_spin", "spikes"],
            "condition_tags": condition_tags,
            "lesson_type": lesson_type,
            "confidence": "medium",
            "evidence_refs": [
                "docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md",
                "docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md",
            ],
            "why": why,
            "answer_changing_information": [
                "Rapid Spin revealed status",
                "active or reserve Ghost spinblock state",
                "whether immediate damage pressure makes the hazard turn too slow",
            ],
        },
    }


def spikes_layer_delta(layers: int) -> int:
    if layers == 0:
        return -4
    if layers == 1:
        return -7
    if layers == 2:
        return -12
    return 20


def materialized_spikes_spin_rom_deltas(
    *,
    tier: str,
    layers: int,
    active_revealed_spin: bool,
    active_ghost: bool,
    foresighted: bool,
    reserve_ghost: bool,
    bench_revealed_spin: bool,
    active_species_prior: bool,
) -> dict[str, Any]:
    weights = ROM_TIER_WEIGHTS[tier]
    role = weights["role"]
    status = weights["status"]
    risk = weights["risk"]
    active_spinblock = active_ghost and not foresighted
    spinblock_available = active_spinblock or reserve_ghost
    revealed_spin_counts = active_revealed_spin and not active_spinblock

    spikes: list[dict[str, int]] = []
    lookahead = materialized_spikes_spin_lookahead(
        layers=layers,
        active_revealed_spin=active_revealed_spin,
        active_species_prior=active_species_prior,
    )
    if layers == 0:
        if revealed_spin_counts:
            if reserve_ghost:
                add_rom_delta(
                    spikes,
                    "move.apply_move_model.apply_revealed_rapid_spin_spikes_risk",
                    8,
                )
            else:
                add_rom_delta(
                    spikes,
                    "move.apply_move_model.apply_revealed_rapid_spin_spikes_risk",
                    20,
                )
        add_rom_delta(spikes, "move.apply_move_model.enemy_under_pressure", -status)
    elif layers == 1:
        if revealed_spin_counts:
            if reserve_ghost:
                add_rom_delta(
                    spikes,
                    "move.apply_move_model.apply_revealed_rapid_spin_spikes_risk",
                    8,
                )
            else:
                add_rom_delta(
                    spikes,
                    "move.apply_move_model.boss_has_available_reserve_ghost",
                    20,
                )
    elif layers == 2:
        returned = False
        if revealed_spin_counts:
            if reserve_ghost:
                add_rom_delta(
                    spikes,
                    "move.apply_move_model.apply_revealed_rapid_spin_spikes_risk",
                    8,
                )
            else:
                add_rom_delta(
                    spikes,
                    "move.apply_move_model.boss_has_available_reserve_ghost",
                    20,
                )
                returned = True
        if not returned:
            if not spinblock_available and bench_revealed_spin:
                add_rom_delta(
                    spikes,
                    "move.apply_move_model.apply_spikes_layer3_unrevealed_spin_risk",
                    6,
                )
            elif not spinblock_available and (active_species_prior or tier == "late"):
                add_rom_delta(
                    spikes,
                    "move.apply_move_model.apply_spikes_layer3_unrevealed_spin_risk",
                    1,
                )
            add_rom_delta(
                spikes,
                "move.apply_move_model.apply_spikes_layer3_unrevealed_spin_risk",
                -role,
            )
    else:
        add_rom_set_score(
            spikes,
            "move.apply_move_model.apply_spikes_layer_bias",
            80,
        )
        return {
            "spikes": spikes,
            "sludge_bomb": materialized_sludge_bomb_deltas(
                role=role,
                active_species_prior=active_species_prior,
                active_ghost=active_ghost,
            ),
            "surf": materialized_surf_deltas(
                tier=tier,
                active_species_prior=active_species_prior,
                active_ghost=active_ghost,
            ),
            "explosion": materialized_explosion_deltas(
                risk=risk,
                active_species_prior=active_species_prior,
            ),
            "lookahead": lookahead,
        }

    add_rom_delta(spikes, "move.apply_move_model.apply_role_bias", -role)
    sludge_bomb = materialized_sludge_bomb_deltas(
        role=role,
        active_species_prior=active_species_prior,
        active_ghost=active_ghost,
    )
    surf = materialized_surf_deltas(
        tier=tier,
        active_species_prior=active_species_prior,
        active_ghost=active_ghost,
    )
    explosion = materialized_explosion_deltas(
        risk=risk,
        active_species_prior=active_species_prior,
    )
    return {
        "spikes": spikes,
        "sludge_bomb": sludge_bomb,
        "surf": surf,
        "explosion": explosion,
        "lookahead": lookahead,
    }


def materialized_sludge_bomb_deltas(
    *,
    role: int,
    active_species_prior: bool,
    active_ghost: bool,
) -> list[dict[str, int]]:
    deltas: list[dict[str, int]] = []
    if not active_species_prior:
        add_rom_set_score(
            deltas,
            "move.apply_move_model.apply_damage_pressure_bias",
            80,
        )
        return deltas
    if active_ghost:
        add_rom_delta(deltas, "move.apply_move_model.apply_damage_pressure_bias", 2)
    add_rom_delta(deltas, "move.apply_move_model.apply_role_bias", -role)
    return deltas


def materialized_surf_deltas(
    *,
    tier: str,
    active_species_prior: bool,
    active_ghost: bool,
) -> list[dict[str, int]]:
    deltas: list[dict[str, int]] = []
    if not active_species_prior:
        add_rom_set_score(
            deltas,
            "move.apply_move_model.apply_damage_pressure_bias",
            80,
        )
        return deltas
    pressure_delta = -2 if tier == "mid" else -4
    add_rom_delta(deltas, "move.apply_move_model.enemy_under_pressure", pressure_delta)
    if not active_ghost:
        add_rom_set_score(
            deltas,
            "move.apply_move_model.apply_damage_pressure_bias",
            80,
        )
    return deltas


def materialized_explosion_deltas(
    *,
    risk: int,
    active_species_prior: bool,
) -> list[dict[str, int]]:
    deltas: list[dict[str, int]] = []
    damage_delta = 2 if active_species_prior else -3
    add_rom_delta(deltas, "move.apply_move_model.apply_damage_pressure_bias", damage_delta)
    add_rom_delta(
        deltas,
        "move.apply_move_model.apply_self_kotrade_discipline",
        16,
    )
    add_rom_delta(deltas, "move.current_enemy_move_accuracy_risky", risk)
    return deltas


def materialized_spikes_spin_lookahead(
    *,
    layers: int,
    active_revealed_spin: bool,
    active_species_prior: bool,
) -> dict[str, int]:
    spikes = 0
    explosion = 0
    if layers == 2 and not active_revealed_spin:
        spikes = 3
    elif active_revealed_spin and active_species_prior:
        spikes = 18
    elif active_revealed_spin:
        spikes = 4
        explosion = 4
    return {
        "spikes": spikes,
        "sludge_bomb": 18,
        "surf": 18,
        "explosion": explosion,
    }


def add_rom_delta(events: list[dict[str, int]], rule: str, delta: int) -> None:
    if delta:
        events.append({"rule": rule, "delta": delta})


def add_rom_set_score(events: list[dict[str, int]], rule: str, score: int) -> None:
    events.append({"rule": rule, "set_score": score})


def mastery_policy_scenario(index: int, rng: random.Random, seed: int) -> dict[str, Any]:
    case = MASTERY_POLICY_CASES[index % len(MASTERY_POLICY_CASES)]
    card_id = str(case["card_id"])
    expectation = deepcopy(case["expectation"])
    expectation["evidence_refs"] = [POLICY_CARD_REFS[card_id]]
    condition_tags = list(expectation.get("condition_tags", []))
    if card_id not in condition_tags:
        condition_tags.append(card_id)
    expectation["condition_tags"] = condition_tags

    return {
        "id": f"generated_mastery_policy_{seed}_{index:05d}_{card_id}",
        "generator": DEFAULT_GENERATOR_VERSION,
        "family": "mastery_policy",
        "policy_card": card_id,
        "seed": seed,
        "case_index": index,
        "tier": rng.choice(list(case["tiers"])),
        "notes": deepcopy(case["notes"]),
        "moves": deepcopy(case["moves"]),
        "expectation": expectation,
    }


def public_policy_scenario(
    family: str,
    index: int,
    rng: random.Random,
    seed: int,
) -> dict[str, Any]:
    cases = PUBLIC_POLICY_CASES[family]
    case = cases[index % len(cases)]
    case_id = str(case["case_id"])
    expectation = deepcopy(case["expectation"])
    condition_tags = list(expectation.get("condition_tags", []))
    if family not in condition_tags:
        condition_tags.append(family)
    if case_id not in condition_tags:
        condition_tags.append(case_id)
    expectation["condition_tags"] = condition_tags

    return {
        "id": f"generated_{family}_{seed}_{index:05d}_{case_id}",
        "generator": DEFAULT_GENERATOR_VERSION,
        "family": family,
        "policy_case": case_id,
        "seed": seed,
        "case_index": index,
        "tier": rng.choice(list(case["tiers"])),
        "notes": deepcopy(case["notes"]),
        "moves": deepcopy(case["moves"]),
        "expectation": expectation,
    }


def write_jsonl(scenarios: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(scenario, sort_keys=True) for scenario in scenarios)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8", newline="\n")


def stamp_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    stamped = dict(scenario)
    stamped["generator_source"] = "tools.boss_ai_debugger.generators"
    stamped["rom"] = display_path(DEFAULT_TRACE_ROM)
    stamped["rom_sha256"] = sha256_file_cached(str(DEFAULT_TRACE_ROM))
    stamped["symbols"] = display_path(DEFAULT_TRACE_SYMBOLS)
    stamped["symbols_sha256"] = sha256_file_cached(str(DEFAULT_TRACE_SYMBOLS))
    stamped["state_hash"] = scenario_hash(stamped)
    return stamped


def scenario_hash(scenario: dict[str, Any]) -> str:
    canonical = {
        key: value
        for key, value in scenario.items()
        if key not in {"state_hash", "scenario_hash"}
    }
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


@lru_cache(maxsize=None)
def sha256_file_cached(path_text: str) -> str:
    path = Path(path_text)
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("/", "\\")
    except ValueError:
        return str(path)


def format_generate_report(
    *,
    family: str,
    count: int,
    seed: int,
    out: Path | None,
) -> str:
    target = str(out) if out is not None else "stdout"
    return (
        "Boss AI scenario generation complete: "
        f"family={family} count={count} seed={seed} out={target}"
    )
