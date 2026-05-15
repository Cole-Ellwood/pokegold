from __future__ import annotations

import hashlib
import json
import random
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError


FAMILIES = ("selector_edges", "spikes_spin", "mastery_policy", "all")
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
        families = ("selector_edges", "spikes_spin", "mastery_policy")
        scenarios: list[dict[str, Any]] = []
        for index in range(count):
            chosen = families[index % len(families)]
            scenarios.append(stamp_scenario(generate_one(chosen, index, rng, seed)))
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
    if family == "mastery_policy":
        return mastery_policy_scenario(index, rng, seed)
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


def spikes_spin_scenario(index: int, rng: random.Random, seed: int) -> dict[str, Any]:
    tier = rng.choice(["mid", "late"])
    layers = rng.choice([0, 1, 2, 3])
    active_revealed_spin = rng.choice([False, True])
    active_ghost = rng.choice([False, True])
    foresighted = rng.choice([False, True]) if active_ghost else False
    reserve_ghost = rng.choice([False, True])
    bench_revealed_spin = rng.choice([False, True])
    active_species_prior = rng.choice([False, True])
    immediate_pressure = rng.choice([False, True])

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

    moves = [
        {
            "id": "move_spikes",
            "name": "Spikes",
            "deltas": rom_deltas["spikes"],
            "lookahead_delta": 18,
        },
        {
            "id": "move_sludge_bomb",
            "name": "Sludge Bomb",
            "deltas": rom_deltas["sludge_bomb"],
            "lookahead_delta": 18,
        },
        {
            "id": "move_surf",
            "name": "Surf",
            "deltas": rom_deltas["surf"],
            "lookahead_delta": 18,
        },
        {
            "id": "move_explosion",
            "name": "Explosion",
            "deltas": rom_deltas["explosion"],
        },
    ]

    if layers == 3:
        best = ["move_sludge_bomb"]
        bad = ["move_spikes"]
        why = "A fourth local Spikes click fails after the stack is already capped."
        lesson_type = "hard_rule"
    elif active_revealed_spin and layers in {1, 2} and not (active_ghost and not foresighted):
        best = ["move_sludge_bomb"]
        bad = ["move_spikes"]
        why = "Public Rapid Spin on the active Pokemon threatens to erase the stack before another layer pays off."
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
) -> dict[str, int]:
    weights = ROM_TIER_WEIGHTS[tier]
    role = weights["role"]
    status = weights["status"]
    setup = weights["setup"]
    risk = weights["risk"]
    pressure = active_species_prior and not active_ghost
    active_spinblock = active_ghost and not foresighted
    spinblock_available = active_ghost or reserve_ghost
    revealed_spin_counts = active_revealed_spin and not active_ghost

    spikes: list[dict[str, int]] = []
    if layers == 0:
        add_rom_delta(
            spikes,
            "move.apply_move_model.enemy_under_pressure",
            -(status if pressure else role),
        )
    elif layers == 1:
        if pressure:
            add_rom_delta(spikes, "move.apply_move_model.enemy_under_pressure", role)
        else:
            returned = False
            if revealed_spin_counts and not active_spinblock:
                if reserve_ghost:
                    add_rom_delta(
                        spikes,
                        "move.apply_move_model.apply_revealed_rapid_spin_spikes_risk",
                        1,
                    )
                else:
                    add_rom_delta(
                        spikes,
                        "move.apply_move_model.boss_has_available_reserve_ghost",
                        role,
                    )
                    returned = True
            if not returned:
                if not spinblock_available and (
                    bench_revealed_spin or active_species_prior
                ):
                    add_rom_delta(
                        spikes,
                        "move.apply_move_model.apply_spikes_layer2_unrevealed_spin_risk",
                        1,
                    )
                add_rom_delta(
                    spikes,
                    "move.apply_move_model.apply_spikes_layer2_unrevealed_spin_risk",
                    status,
                )
    elif layers == 2:
        if pressure:
            add_rom_delta(spikes, "move.apply_move_model.enemy_under_pressure", setup)
        else:
            returned = False
            if revealed_spin_counts and not active_spinblock:
                if reserve_ghost:
                    add_rom_delta(
                        spikes,
                        "move.apply_move_model.apply_revealed_rapid_spin_spikes_risk",
                        1,
                    )
                else:
                    add_rom_delta(
                        spikes,
                        "move.apply_move_model.boss_has_available_reserve_ghost",
                        role,
                    )
                    returned = True
            if not returned:
                if not spinblock_available and (
                    bench_revealed_spin
                    or active_species_prior
                    or tier == "late"
                ):
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
        add_rom_delta(spikes, "move.apply_move_model.apply_spikes_layer_bias", role)

    add_rom_delta(spikes, "move.apply_move_model.apply_role_bias", -role)
    return {
        "spikes": spikes,
        "sludge_bomb": [
            {"rule": "move.apply_move_model.apply_role_bias", "delta": -role}
        ],
        "surf": [],
        "explosion": [
            {
                "rule": "move.apply_move_model.apply_self_kotrade_discipline",
                "delta": 6,
            },
            {"rule": "move.current_enemy_move_accuracy_risky", "delta": risk},
        ],
    }


def add_rom_delta(events: list[dict[str, int]], rule: str, delta: int) -> None:
    if delta:
        events.append({"rule": rule, "delta": delta})


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
