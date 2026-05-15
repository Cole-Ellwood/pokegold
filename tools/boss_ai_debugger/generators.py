from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from tools.boss_ai_preference.data import PreferenceDataError


FAMILIES = ("selector_edges", "spikes_spin", "all")
DEFAULT_GENERATOR_VERSION = "boss-ai-debugger-generator-v1"


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
        families = ("selector_edges", "spikes_spin")
        scenarios: list[dict[str, Any]] = []
        for index in range(count):
            chosen = families[index % len(families)]
            scenarios.append(generate_one(chosen, index, rng, seed))
        return scenarios
    return [generate_one(family, index, rng, seed) for index in range(count)]


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

    spikes_delta = spikes_layer_delta(layers)
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

    risk_delta = 0
    if layers in {1, 2}:
        if active_revealed_spin:
            risk_delta += 18
            if active_ghost and not foresighted:
                risk_delta -= 12
            elif reserve_ghost:
                risk_delta -= 6
        elif bench_revealed_spin:
            risk_delta += 9
        elif active_species_prior:
            risk_delta += 4
    if immediate_pressure:
        risk_delta += 8

    spike_deltas = [{"rule": "spikes_layer_value", "delta": spikes_delta}]
    if risk_delta:
        spike_deltas.append({"rule": "public_spin_or_tempo_risk", "delta": risk_delta})

    moves = [
        {
            "id": "move_spikes",
            "name": "Spikes",
            "deltas": spike_deltas,
            "lookahead_delta": -1 if layers < 3 and risk_delta <= 4 else 1,
        },
        {
            "id": "move_sludge_bomb",
            "name": "Sludge Bomb",
            "deltas": [{"rule": "live_damage", "delta": -3}],
        },
        {
            "id": "move_surf",
            "name": "Surf",
            "deltas": [{"rule": "coverage_chip", "delta": -1}],
        },
        {
            "id": "move_explosion",
            "name": "Explosion",
            "deltas": [{"rule": "route_trade", "delta": -2 if active_revealed_spin else 1}],
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


def write_jsonl(scenarios: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(scenario, sort_keys=True) for scenario in scenarios)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8", newline="\n")


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
