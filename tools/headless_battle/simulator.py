from __future__ import annotations

import copy
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

from tools.boss_ai_debugger import rom_scenarios
from tools.boss_ai_preference.data import PreferenceDataError
from tools.damage_debugger import oracle
from tools.damage_debugger import tables


def parse_equ_values(path: Path) -> dict[str, int]:
    values: dict[str, int] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split(";", 1)[0].strip()
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "DEF" and parts[2] == "EQU":
            try:
                values[parts[1]] = parse_asm_int(parts[3])
            except ValueError:
                continue
    return values


def parse_asm_int(token: str) -> int:
    token = token.strip()
    if token.startswith("$"):
        return int(token[1:], 16)
    return int(token, 0)


SCHEMA_VERSION = 1
REPORT_KIND = "headless_battle_turn_simulation"
PERCENT_100 = 255
DAMAGE_VARIATION_MIN = (85 * PERCENT_100 // 100) + 1
DAMAGE_VARIATION_OUTCOME_COUNT = PERCENT_100 - DAMAGE_VARIATION_MIN + 1
SPEED_TIE_THRESHOLD = (50 * PERCENT_100 // 100) + 1
QUICK_CLAW_ITEM = tables.resolve_item("QUICK_CLAW")
CHOICE_SCARF_ITEM = tables.resolve_item("CHOICE_SCARF")
LEFTOVERS_ITEM = tables.resolve_item("LEFTOVERS")
ROCKY_HELMET_ITEM = tables.resolve_item("ROCKY_HELMET")
SHELL_BELL_ITEM = tables.resolve_item("SHELL_BELL")
LIFE_ORB_ITEM = tables.resolve_item("LIFE_ORB")
BRIGHTPOWDER_ITEM = tables.resolve_item("BRIGHTPOWDER")
SCOPE_LENS_ITEM = tables.resolve_item("SCOPE_LENS")
LUCKY_PUNCH_ITEM = tables.resolve_item("LUCKY_PUNCH")
STICK_ITEM = tables.resolve_item("STICK")
QUICK_CLAW_THRESHOLD = 60
BRIGHTPOWDER_MISS_CHANCE = 20
ROCKY_HELMET_DENOMINATOR = 6
SHELL_BELL_DENOMINATOR = 8
LIFE_ORB_DENOMINATOR = 10
STATUS_NONE = "none"
STATUS_POISON = "poison"
STATUS_BURN = "burn"
STATUS_TOXIC = "toxic"
STATUS_PARALYSIS = "paralysis"
STATUS_SLEEP = "sleep"
STATUS_FREEZE = "freeze"
STATUS_ALIASES = {
    "": STATUS_NONE,
    "none": STATUS_NONE,
    "no_status": STATUS_NONE,
    "ok": STATUS_NONE,
    "poison": STATUS_POISON,
    "psn": STATUS_POISON,
    "burn": STATUS_BURN,
    "brn": STATUS_BURN,
    "toxic": STATUS_TOXIC,
    "bad_poison": STATUS_TOXIC,
    "badly_poisoned": STATUS_TOXIC,
    "par": STATUS_PARALYSIS,
    "paralysis": STATUS_PARALYSIS,
    "paralyzed": STATUS_PARALYSIS,
    "slp": STATUS_SLEEP,
    "sleep": STATUS_SLEEP,
    "asleep": STATUS_SLEEP,
    "frz": STATUS_FREEZE,
    "freeze": STATUS_FREEZE,
    "frozen": STATUS_FREEZE,
}
BASE_PRIORITY = 1
PRIORITY_HIT_PRIORITY = 2
MIN_STAT_LEVEL = 1
NEUTRAL_STAT_LEVEL = 7
MAX_STAT_LEVEL = 13
FLYING_TARGET_HIT_MOVES = ("GUST", "WHIRLWIND", "THUNDER", "TWISTER")
UNDERGROUND_TARGET_HIT_MOVES = ("EARTHQUAKE", "FISSURE", "MAGNITUDE")
DIG_TARGET_HIT_MOVES = UNDERGROUND_TARGET_HIT_MOVES
HIGH_CRITICAL_HIT_MOVES = (
    "KARATE_CHOP",
    "RAZOR_WIND",
    "RAZOR_LEAF",
    "CRABHAMMER",
    "SLASH",
    "AEROBLAST",
    "CROSS_CHOP",
)
SLEEP_BYPASS_MOVES = ("SNORE", "SLEEP_TALK")
FREEZE_BYPASS_MOVES = ("FLAME_WHEEL", "SACRED_FIRE")
CRITICAL_HIT_CHANCES = (17, 32, 64, 85, 128, 128, 128)
BATTLE_EQU_CONSTANTS = parse_equ_values(tables.ROOT / "constants/battle_constants.asm")
AI_SWITCH_THRESHOLD_EARLY = BATTLE_EQU_CONSTANTS["AI_SWITCH_THRESHOLD_EARLY"]
AI_SWITCH_THRESHOLD_MID = BATTLE_EQU_CONSTANTS["AI_SWITCH_THRESHOLD_MID"]
AI_SWITCH_THRESHOLD_LATE = BATTLE_EQU_CONSTANTS["AI_SWITCH_THRESHOLD_LATE"]
AI_SWITCH_ANTI_LOOP_PENALTY = BATTLE_EQU_CONSTANTS["AI_SWITCH_ANTI_LOOP_PENALTY"]
BOSS_AI_SWITCH_ROLL_HIGH = 230
BOSS_AI_SWITCH_ROLL_MID = 192
BOSS_AI_SWITCH_ROLL_LOW = 141
PARALYSIS_FAIL_BASELINE = 25 * PERCENT_100 // 100
PARALYSIS_FAIL_FIGHTING_HALF = 20 * PERCENT_100 // 100
PARALYSIS_FAIL_FIGHTING_FULL = 15 * PERCENT_100 // 100
ELECTRIC_SPEED_HALF = (41, 40)
ELECTRIC_SPEED_FULL = (21, 20)
PARALYSIS_SPEED_BASELINE = (1, 4)
PARALYSIS_SPEED_FIGHTING_HALF = (3, 8)
PARALYSIS_SPEED_FIGHTING_FULL = (1, 2)
TIER_SWITCH_THRESHOLDS = {
    "early": AI_SWITCH_THRESHOLD_EARLY,
    "mid": AI_SWITCH_THRESHOLD_MID,
    "late": AI_SWITCH_THRESHOLD_LATE,
}
CLASS_SWITCH_THRESHOLD_DELTAS = {
    "CHAMPION": -10,
    "KOGA": -8,
    "CLAIR": -6,
    "KAREN": -4,
    "BRUNO": -4,
    "JASMINE": 4,
    "CHUCK": 2,
}
ACCURACY_LEVEL_MULTIPLIERS = (
    (33, 100),
    (36, 100),
    (43, 100),
    (50, 100),
    (60, 100),
    (75, 100),
    (1, 1),
    (133, 100),
    (166, 100),
    (2, 1),
    (233, 100),
    (133, 50),
    (3, 1),
)
RngMode = Literal["fixed", "sample", "exhaustive"]
ActionKind = Literal["move", "switch", "wait", "boss_ai_selector", "boss_ai_switch_policy"]
_MOVE_IDS: dict[str, int] | None = None
_MOVE_CONTACT_FLAGS: dict[str, bool] | None = None


class SimulationInputError(Exception):
    """User-facing scenario error."""


@dataclass(frozen=True)
class MoveState:
    name: str
    move_type: int
    move_type_name: str
    bp: int
    move_id: int | None = None
    priority: int = 0
    accuracy: int = PERCENT_100
    effect: str = "normal_hit"
    contact: bool = False


@dataclass(frozen=True)
class PokemonState:
    side: str
    name: str
    level: int
    hp: int
    max_hp: int
    types: tuple[int, int]
    type_names: tuple[str, str]
    attack: int
    defense: int
    speed: int
    sp_attack: int
    sp_defense: int
    item: int = oracle.HELD_NONE
    status: str = STATUS_NONE
    sleep_turns: int = 0
    toxic_count: int = 0
    can_evolve: bool = False
    accuracy_level: int = NEUTRAL_STAT_LEVEL
    evasion_level: int = NEUTRAL_STAT_LEVEL
    protect: bool = False
    x_accuracy: bool = False
    lock_on: bool = False
    flying: bool = False
    underground: bool = False
    focus_energy: bool = False
    flinched: bool = False
    moves: tuple[MoveState, ...] = ()


@dataclass(frozen=True)
class ActionState:
    kind: ActionKind
    move_index: int | None = None
    bench_index: int | None = None
    boss_ai_selector: BossAiSelectorState | None = None
    boss_ai_switch_policy: BossAiSwitchPolicyState | None = None


@dataclass(frozen=True)
class BossAiSelectorState:
    scenario_id: str
    tier: int | str
    move_ids: tuple[int, ...]
    scores: tuple[int, ...]
    move_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class BossAiSwitchPolicyState:
    scenario_id: str
    candidate_bench: int
    confidence: int
    tier: int | str
    trainer_class: str = ""
    threshold: int | None = None
    anti_loop: bool = False
    sack_bias: bool = False
    wincon_risk: bool = False
    fallback_move_index: int = 0


@dataclass(frozen=True)
class BattleState:
    player: PokemonState
    enemy: PokemonState
    weather: int = oracle.WEATHER_NONE
    turn: int = 1
    player_bench: tuple[PokemonState, ...] = ()
    enemy_bench: tuple[PokemonState, ...] = ()


@dataclass(frozen=True)
class RngConfig:
    mode: RngMode
    values: tuple[int, ...] = ()
    seed: int | None = None
    samples: int = 1


@dataclass
class RngStream:
    config: RngConfig
    index: int = 0
    sample_rng: random.Random | None = None

    def next_byte(self, source: str) -> tuple[int, dict[str, Any]]:
        if self.config.mode == "fixed":
            if self.index >= len(self.config.values):
                raise SimulationInputError(
                    f"fixed RNG exhausted while reading {source}; "
                    f"provide more rng.values bytes"
                )
            value = self.config.values[self.index]
            self.index += 1
        elif self.config.mode == "sample":
            if self.sample_rng is None:
                self.sample_rng = random.Random(self.config.seed)
            value = self.sample_rng.randrange(256)
        else:
            raise SimulationInputError("exhaustive RNG must not request a concrete byte")
        return value, {"source": source, "raw": value}


def simulate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rng = parse_rng(payload.get("rng", {}))
    state = parse_state(payload.get("state"))
    turns = parse_turns(payload, state)
    outcomes = simulate_samples(state, turns, rng)
    return {
        "kind": REPORT_KIND,
        "schema_version": SCHEMA_VERSION,
        "valid": True,
        "turn_count": len(turns),
        "rng": rng_to_json(rng),
        "coverage": coverage_report(),
        "outcome_count": len(outcomes),
        "summary": summarize_outcomes(outcomes),
        "outcomes": outcomes,
    }


def simulate_samples(
    state: BattleState,
    turns: list[dict[str, ActionState]],
    rng: RngConfig,
) -> list[dict[str, Any]]:
    if rng.mode != "sample" or rng.samples == 1:
        return simulate_sequence(state, turns, rng)
    outcomes: list[dict[str, Any]] = []
    for sample_index in range(rng.samples):
        sample_seed = None if rng.seed is None else rng.seed + sample_index
        sample_rng = RngConfig(mode="sample", seed=sample_seed, samples=1)
        for outcome in simulate_sequence(state, turns, sample_rng):
            item = copy.deepcopy(outcome)
            item["sample_index"] = sample_index
            item["outcome_id"] = f"sample{sample_index}.{item['outcome_id']}"
            outcomes.append(item)
    return outcomes


def simulate_turn(
    state: BattleState,
    actions: dict[str, ActionState],
    rng: RngConfig,
) -> list[dict[str, Any]]:
    return simulate_sequence(state, [actions], rng)


def simulate_sequence(
    state: BattleState,
    turns: list[dict[str, ActionState]],
    rng: RngConfig,
) -> list[dict[str, Any]]:
    rng_stream = RngStream(rng) if rng.mode != "exhaustive" else None
    branches = [
        {
            "state": state,
            "events": [],
            "rng_trace": [],
            "turn_order": [],
            "turns": [],
            "branch_path": [],
        }
    ]
    for actions in turns:
        for branch in branches:
            forced_sides = forced_switch_prompt_sides(branch["state"])
            if forced_sides and not is_forced_switch_plan(forced_sides, actions):
                rendered = ", ".join(forced_sides)
                raise SimulationInputError(
                    "forced post-KO switch prompts are out of scope for this slice; "
                    f"state has fainted active Pokemon with living bench on: {rendered}; "
                    "use a forced switch phase with the forced side switching and the other side waiting"
                )
        if all(battle_is_over(branch["state"]) for branch in branches):
            branches = [append_battle_over_once(branch) for branch in branches]
            break
        next_branches: list[dict[str, Any]] = []
        for branch in branches:
            if battle_is_over(branch["state"]):
                next_branches.append(append_battle_over_once(branch))
                continue
            next_branches.extend(simulate_turn_branches(branch, actions, rng, rng_stream))
        branches = next_branches

    return [branch_to_outcome(branch, index) for index, branch in enumerate(branches)]


def simulate_turn_branches(
    source_branch: dict[str, Any],
    actions: dict[str, ActionState],
    rng: RngConfig,
    rng_stream: RngStream | None,
) -> list[dict[str, Any]]:
    state: BattleState = source_branch["state"]
    turn_branches: list[dict[str, Any]] = []
    for resolved in resolve_boss_ai_action_branches(source_branch, actions, rng, rng_stream):
        resolved_state: BattleState = resolved["state"]
        resolved_actions: dict[str, ActionState] = resolved["actions"]
        order_options = turn_order_options(resolved_state, resolved_actions, rng, rng_stream)
        for option_index, option in enumerate(order_options):
            branches = [
                start_turn_branch(resolved, option, resolved_state, resolved_actions, option_index)
            ]
            for actor in option["turn_order"]:
                next_branches = []
                for active_branch in branches:
                    for action_branch in apply_action_branch(active_branch, actor, resolved_actions[actor], rng, rng_stream):
                        next_branches.append(
                            apply_post_action_residual_status(
                                action_branch,
                                actor,
                                enabled=turn_order_reason(option) != "forced_switch_phase",
                            )
                        )
                branches = next_branches
            for completed_branch in branches:
                with_between_turns = apply_between_turn_leftovers(completed_branch)
                with_between_turns["state"] = advance_turn(with_between_turns["state"])
                turn_branches.append(with_between_turns)
    return turn_branches


def resolve_boss_ai_action_branches(
    source_branch: dict[str, Any],
    actions: dict[str, ActionState],
    rng: RngConfig,
    rng_stream: RngStream | None,
) -> list[dict[str, Any]]:
    state: BattleState = source_branch["state"]
    for side in ("player", "enemy"):
        action = actions[side]
        if action.kind == "boss_ai_selector":
            resolved_branches: list[dict[str, Any]] = []
            for option in boss_ai_selector_options(state, side, action, rng, rng_stream):
                resolved = clone_branch(source_branch)
                resolved["rng_trace"].extend(with_turn(option["rng_trace"], state.turn))
                resolved["branch_path"].extend(with_turn(option["branch_path"], state.turn))
                resolved["events"].append(
                    {
                        "turn": state.turn,
                        "actor": side,
                        "type": "boss_ai_select_move",
                        "move_index": option["move_index"],
                        "move": option["move_name"],
                        "selected_slot_index": option["selected_slot_index"],
                        "selected_move_id": option["selected_move_id"],
                        "selector": option["selector"],
                        "proof_status": "source_mirrored_boss_ai_selector_from_post_score_bytes",
                    }
                )
                next_actions = dict(actions)
                next_actions[side] = ActionState(kind="move", move_index=option["move_index"])
                resolved["actions"] = next_actions
                resolved_branches.extend(resolve_boss_ai_action_branches(resolved, next_actions, rng, rng_stream))
            return resolved_branches
        if action.kind == "boss_ai_switch_policy":
            resolved_branches = []
            for option in boss_ai_switch_policy_options(state, side, action, rng, rng_stream):
                resolved = clone_branch(source_branch)
                resolved["rng_trace"].extend(with_turn(option["rng_trace"], state.turn))
                resolved["branch_path"].extend(with_turn(option["branch_path"], state.turn))
                resolved["events"].append(
                    {
                        "turn": state.turn,
                        "actor": side,
                        "type": "boss_ai_switch_policy",
                        "scenario_id": option["scenario_id"],
                        "candidate_bench": option["candidate_bench"],
                        "candidate": option["candidate_name"],
                        "confidence": option["confidence"],
                        "threshold": option["threshold"],
                        "margin": option["margin"],
                        "roll_threshold": option["roll_threshold"],
                        "decision": option["decision"],
                        "reason": option["reason"],
                        "proof_status": "source_mirrored_boss_ai_switch_policy_from_final_confidence",
                    }
                )
                next_actions = dict(actions)
                if option["decision"] == "switch":
                    next_actions[side] = ActionState(kind="switch", bench_index=option["candidate_bench"])
                else:
                    next_actions[side] = ActionState(kind="move", move_index=option["fallback_move_index"])
                resolved["actions"] = next_actions
                resolved_branches.extend(resolve_boss_ai_action_branches(resolved, next_actions, rng, rng_stream))
            return resolved_branches
        if action.kind != "boss_ai_selector":
            continue

    resolved = clone_branch(source_branch)
    resolved["actions"] = actions
    return [resolved]


def boss_ai_selector_options(
    state: BattleState,
    side: str,
    action: ActionState,
    rng: RngConfig,
    rng_stream: RngStream | None,
) -> list[dict[str, Any]]:
    selector = action.boss_ai_selector
    if selector is None:
        raise SimulationInputError(f"actions.{side}.boss_ai_selector is required")
    pokemon = get_side(state, side)
    validate_selector_move_ids(pokemon, selector, side)
    try:
        result = rom_scenarios.select_from_score_bytes(
            scenario_id=selector.scenario_id,
            tier=selector.tier,
            move_ids=list(selector.move_ids),
            scores=list(selector.scores),
            move_names={
                move_id: name
                for move_id, name in zip(selector.move_ids, selector.move_names)
                if move_id != 0 and name
            } or None,
        )
    except PreferenceDataError as exc:
        raise SimulationInputError(f"actions.{side}.boss_ai_selector invalid: {exc}") from exc
    if not result.get("ready", False):
        raise SimulationInputError(
            f"actions.{side}.boss_ai_selector is not ready: {result.get('reason', 'unknown')}"
        )

    threshold = result.get("best_roll_threshold")
    best_slot = int(result["best_slot_index"])
    second_slot = result.get("second_slot_index")
    if threshold is None or second_slot is None:
        return [boss_ai_selector_option(pokemon, result, best_slot, [], "only_legal_selector_move")]

    threshold = int(threshold)
    second_slot = int(second_slot)
    if rng.mode == "exhaustive":
        return [
            boss_ai_selector_option(
                pokemon,
                result,
                best_slot,
                [
                    {
                        "source": "boss_ai_selector",
                        "raw_range": [0, threshold - 1],
                        "raw_count": threshold,
                        "domain_count": 256,
                        "threshold": threshold,
                        "branch": "best",
                    }
                ],
                "boss_ai_selector_best",
            ),
            boss_ai_selector_option(
                pokemon,
                result,
                second_slot,
                [
                    {
                        "source": "boss_ai_selector",
                        "raw_range": [threshold, 255],
                        "raw_count": 256 - threshold,
                        "domain_count": 256,
                        "threshold": threshold,
                        "branch": "second",
                    }
                ],
                "boss_ai_selector_second",
            ),
        ]
    assert rng_stream is not None
    raw, trace = rng_stream.next_byte("boss_ai_selector")
    chose_best = raw < threshold
    selected_slot = best_slot if chose_best else second_slot
    trace["threshold"] = threshold
    trace["branch"] = "best" if chose_best else "second"
    return [
        boss_ai_selector_option(
            pokemon,
            result,
            selected_slot,
            [trace],
            trace["branch"],
        )
    ]


def boss_ai_selector_option(
    pokemon: PokemonState,
    selector: dict[str, Any],
    selected_slot: int,
    rng_trace: list[dict[str, Any]],
    branch: str,
) -> dict[str, Any]:
    if selected_slot < 0 or selected_slot >= len(pokemon.moves):
        raise SimulationInputError(
            f"boss_ai_selector selected slot {selected_slot}, but {pokemon.name} has "
            f"{len(pokemon.moves)} move(s)"
        )
    move = pokemon.moves[selected_slot]
    selected_move_id = selector_move_id(selector, selected_slot)
    return {
        "move_index": selected_slot,
        "move_name": move.name,
        "selected_slot_index": selected_slot,
        "selected_move_id": selected_move_id,
        "selector": selector,
        "rng_trace": rng_trace,
        "branch_path": [
            {
                "source": "boss_ai_selector",
                "scenario_id": selector["scenario_id"],
                "branch": branch,
                "slot_index": selected_slot,
                "move": move.name,
            }
        ],
    }


def selector_move_id(selector: dict[str, Any], selected_slot: int) -> int | None:
    for slot in selector.get("slots", []):
        if int(slot["slot_index"]) == selected_slot:
            return int(slot["move_id"])
    return None


def validate_selector_move_ids(
    pokemon: PokemonState,
    selector: BossAiSelectorState,
    side: str,
) -> None:
    if len(selector.move_ids) != 4 or len(selector.scores) != 4:
        raise SimulationInputError(f"actions.{side}.boss_ai_selector needs four move_ids and four scores")
    for index, move in enumerate(pokemon.moves):
        if index >= len(selector.move_ids):
            break
        expected = selector.move_ids[index]
        if expected == 0:
            break
        if move.move_id is not None and move.move_id != expected:
            raise SimulationInputError(
                f"actions.{side}.boss_ai_selector move_ids[{index}]={expected} "
                f"does not match state.{side}.moves[{index}].move_id={move.move_id}"
            )


def boss_ai_switch_policy_options(
    state: BattleState,
    side: str,
    action: ActionState,
    rng: RngConfig,
    rng_stream: RngStream | None,
) -> list[dict[str, Any]]:
    policy = action.boss_ai_switch_policy
    if policy is None:
        raise SimulationInputError(f"actions.{side}.boss_ai_switch_policy is required")
    bench = get_bench(state, side)
    if policy.candidate_bench >= len(bench):
        raise SimulationInputError(
            f"actions.{side}.boss_ai_switch_policy.candidate_bench "
            f"index {policy.candidate_bench} out of range"
        )
    candidate = bench[policy.candidate_bench]
    if candidate.hp <= 0:
        raise SimulationInputError(f"actions.{side}.boss_ai_switch_policy cannot target a fainted Pokemon")
    active = get_side(state, side)
    if policy.fallback_move_index >= len(active.moves):
        raise SimulationInputError(
            f"actions.{side}.boss_ai_switch_policy.fallback_move index "
            f"{policy.fallback_move_index} out of range"
        )

    threshold = boss_ai_switch_threshold(policy)
    confidence = policy.confidence
    if confidence < threshold:
        return [
            boss_ai_switch_policy_option(
                policy,
                candidate,
                threshold=threshold,
                decision="stay",
                reason="confidence_below_threshold",
                roll_threshold=None,
                rng_trace=[],
            )
        ]

    margin = confidence - threshold
    roll_threshold = boss_ai_switch_roll_threshold(margin)
    if rng.mode == "exhaustive":
        return [
            boss_ai_switch_policy_option(
                policy,
                candidate,
                threshold=threshold,
                decision="switch",
                reason="roll_succeeded",
                roll_threshold=roll_threshold,
                rng_trace=[
                    {
                        "source": "boss_ai_switch_roll",
                        "raw_range": [0, roll_threshold - 1],
                        "raw_count": roll_threshold,
                        "domain_count": 256,
                        "threshold": roll_threshold,
                        "decision": "switch",
                    }
                ],
            ),
            boss_ai_switch_policy_option(
                policy,
                candidate,
                threshold=threshold,
                decision="stay",
                reason="roll_failed",
                roll_threshold=roll_threshold,
                rng_trace=[
                    {
                        "source": "boss_ai_switch_roll",
                        "raw_range": [roll_threshold, 255],
                        "raw_count": 256 - roll_threshold,
                        "domain_count": 256,
                        "threshold": roll_threshold,
                        "decision": "stay",
                    }
                ],
            ),
        ]
    assert rng_stream is not None
    raw, trace = rng_stream.next_byte("boss_ai_switch_roll")
    decision = "switch" if raw < roll_threshold else "stay"
    trace["threshold"] = roll_threshold
    trace["decision"] = decision
    return [
        boss_ai_switch_policy_option(
            policy,
            candidate,
            threshold=threshold,
            decision=decision,
            reason="roll_succeeded" if decision == "switch" else "roll_failed",
            roll_threshold=roll_threshold,
            rng_trace=[trace],
        )
    ]


def boss_ai_switch_policy_option(
    policy: BossAiSwitchPolicyState,
    candidate: PokemonState,
    *,
    threshold: int,
    decision: str,
    reason: str,
    roll_threshold: int | None,
    rng_trace: list[dict[str, Any]],
) -> dict[str, Any]:
    margin = policy.confidence - threshold
    return {
        "scenario_id": policy.scenario_id,
        "candidate_bench": policy.candidate_bench,
        "candidate_name": candidate.name,
        "fallback_move_index": policy.fallback_move_index,
        "confidence": policy.confidence,
        "threshold": threshold,
        "margin": margin,
        "roll_threshold": roll_threshold,
        "decision": decision,
        "reason": reason,
        "rng_trace": rng_trace,
        "branch_path": [
            {
                "source": "boss_ai_switch_policy",
                "scenario_id": policy.scenario_id,
                "candidate_bench": policy.candidate_bench,
                "candidate": candidate.name,
                "confidence": policy.confidence,
                "threshold": threshold,
                "margin": margin,
                "roll_threshold": roll_threshold,
                "decision": decision,
                "reason": reason,
            }
        ],
    }


def boss_ai_switch_threshold(policy: BossAiSwitchPolicyState) -> int:
    if policy.threshold is not None:
        threshold = policy.threshold
    else:
        tier_name = normalize_boss_ai_tier(policy.tier)
        threshold = TIER_SWITCH_THRESHOLDS[tier_name]
        class_name = policy.trainer_class.upper()
        delta = CLASS_SWITCH_THRESHOLD_DELTAS.get(class_name, 0)
        if delta < 0:
            threshold = max(0, threshold + delta)
        elif delta > 0:
            threshold = min(95, threshold + delta)
    if policy.anti_loop:
        threshold += AI_SWITCH_ANTI_LOOP_PENALTY
    if policy.sack_bias:
        threshold += 8
    if policy.wincon_risk:
        threshold += 10
    return min(255, threshold)


def boss_ai_switch_roll_threshold(margin: int) -> int:
    if margin >= 20:
        return BOSS_AI_SWITCH_ROLL_HIGH
    if margin >= 10:
        return BOSS_AI_SWITCH_ROLL_MID
    return BOSS_AI_SWITCH_ROLL_LOW


def normalize_boss_ai_tier(raw: int | str) -> str:
    if isinstance(raw, str):
        text = raw.lower()
        if text in TIER_SWITCH_THRESHOLDS:
            return text
        raise SimulationInputError(f"boss AI tier must be early, mid, or late; got {raw!r}")
    if raw == 1:
        return "early"
    if raw == 2:
        return "mid"
    if raw == 3:
        return "late"
    raise SimulationInputError(f"boss AI tier must be 1, 2, 3, early, mid, or late; got {raw!r}")


def start_turn_branch(
    branch: dict[str, Any],
    option: dict[str, Any],
    state: BattleState,
    actions: dict[str, ActionState],
    option_index: int,
) -> dict[str, Any]:
    started = clone_branch(branch)
    turn = state.turn
    started["rng_trace"].extend(with_turn(option["rng_trace"], turn))
    started["branch_path"].extend(with_turn(option["branch_path"], turn))
    started["turn_order"] = list(option["turn_order"])
    started["turns"].append(
        {
            "turn": turn,
            "option_index": option_index,
            "turn_order": list(option["turn_order"]),
            "actions": action_summary(state, actions),
        }
    )
    return started


def turn_order_options(
    state: BattleState,
    actions: dict[str, ActionState],
    rng: RngConfig,
    rng_stream: RngStream | None,
) -> list[dict[str, Any]]:
    player_action = actions["player"]
    enemy_action = actions["enemy"]
    forced_sides = forced_switch_prompt_sides(state)
    if forced_sides:
        if not is_forced_switch_plan(forced_sides, actions):
            rendered = ", ".join(forced_sides)
            raise SimulationInputError(
                "forced post-KO switch prompts are out of scope for this slice; "
                f"state has fainted active Pokemon with living bench on: {rendered}; "
                "use a forced switch phase with the forced side switching and the other side waiting"
            )
        return [order_option(forced_sides, "forced_switch_phase", [])]
    if player_action.kind == "wait" or enemy_action.kind == "wait":
        raise SimulationInputError("wait actions are only valid during forced switch phases")
    if player_action.kind == "switch" or enemy_action.kind == "switch":
        order = []
        if player_action.kind == "switch":
            order.append("player")
        if enemy_action.kind == "switch":
            order.append("enemy")
        if player_action.kind != "switch":
            order.append("player")
        if enemy_action.kind != "switch":
            order.append("enemy")
        reason = "double_switch_player_first" if player_action.kind == enemy_action.kind else "switch_before_move"
        return [order_option(order, reason, [])]

    player_move = selected_move(state.player, player_action, "actions.player")
    enemy_move = selected_move(state.enemy, enemy_action, "actions.enemy")
    if player_move.priority != enemy_move.priority:
        first = "player" if player_move.priority > enemy_move.priority else "enemy"
        return [order_option([first, other_side(first)], "priority", [])]
    quick_claw = quick_claw_options(state, rng, rng_stream)
    if quick_claw:
        return quick_claw
    return speed_order_options(state, rng, rng_stream, [], [])


def quick_claw_options(
    state: BattleState,
    rng: RngConfig,
    rng_stream: RngStream | None,
) -> list[dict[str, Any]]:
    player_has = state.player.item == QUICK_CLAW_ITEM
    enemy_has = state.enemy.item == QUICK_CLAW_ITEM
    if not player_has and not enemy_has:
        return []
    if player_has and not enemy_has:
        return one_quick_claw_options(state, "player", rng, rng_stream)
    if enemy_has and not player_has:
        return one_quick_claw_options(state, "enemy", rng, rng_stream)
    return both_quick_claw_options(state, rng, rng_stream)


def one_quick_claw_options(
    state: BattleState,
    side: str,
    rng: RngConfig,
    rng_stream: RngStream | None,
) -> list[dict[str, Any]]:
    if rng.mode == "exhaustive":
        success = order_option(
            [side, other_side(side)],
            "quick_claw",
            [
                {
                    "source": "quick_claw",
                    "side": side,
                    "raw_range": [0, QUICK_CLAW_THRESHOLD - 1],
                    "raw_count": QUICK_CLAW_THRESHOLD,
                    "domain_count": 256,
                    "threshold": QUICK_CLAW_THRESHOLD,
                    "activated": True,
                }
            ],
        )
        failure_trace = [
            {
                "source": "quick_claw",
                "side": side,
                "raw_range": [QUICK_CLAW_THRESHOLD, 255],
                "raw_count": 256 - QUICK_CLAW_THRESHOLD,
                "domain_count": 256,
                "threshold": QUICK_CLAW_THRESHOLD,
                "activated": False,
            }
        ]
        failure_path = [{"source": "quick_claw", "side": side, "activated": False}]
        return [success, *speed_order_options(state, rng, None, failure_trace, failure_path)]

    assert rng_stream is not None
    raw, trace = rng_stream.next_byte("quick_claw")
    activated = raw < QUICK_CLAW_THRESHOLD
    trace["side"] = side
    trace["threshold"] = QUICK_CLAW_THRESHOLD
    trace["activated"] = activated
    if activated:
        return [order_option([side, other_side(side)], "quick_claw", [trace])]
    return speed_order_options(
        state,
        rng,
        rng_stream,
        [trace],
        [{"source": "quick_claw", "side": side, "activated": False}],
    )


def both_quick_claw_options(
    state: BattleState,
    rng: RngConfig,
    rng_stream: RngStream | None,
) -> list[dict[str, Any]]:
    if rng.mode == "exhaustive":
        enemy_success = order_option(
            ["enemy", "player"],
            "quick_claw",
            [
                {
                    "source": "quick_claw",
                    "side": "enemy",
                    "raw_range": [0, QUICK_CLAW_THRESHOLD - 1],
                    "raw_count": QUICK_CLAW_THRESHOLD,
                    "domain_count": 256,
                    "threshold": QUICK_CLAW_THRESHOLD,
                    "activated": True,
                }
            ],
        )
        enemy_fail = [
            {
                "source": "quick_claw",
                "side": "enemy",
                "raw_range": [QUICK_CLAW_THRESHOLD, 255],
                "raw_count": 256 - QUICK_CLAW_THRESHOLD,
                "domain_count": 256,
                "threshold": QUICK_CLAW_THRESHOLD,
                "activated": False,
            }
        ]
        player_success = order_option(
            ["player", "enemy"],
            "quick_claw",
            [
                *enemy_fail,
                {
                    "source": "quick_claw",
                    "side": "player",
                    "raw_range": [0, QUICK_CLAW_THRESHOLD - 1],
                    "raw_count": QUICK_CLAW_THRESHOLD,
                    "domain_count": 256,
                    "threshold": QUICK_CLAW_THRESHOLD,
                    "activated": True,
                },
            ],
        )
        both_fail_trace = [
            *enemy_fail,
            {
                "source": "quick_claw",
                "side": "player",
                "raw_range": [QUICK_CLAW_THRESHOLD, 255],
                "raw_count": 256 - QUICK_CLAW_THRESHOLD,
                "domain_count": 256,
                "threshold": QUICK_CLAW_THRESHOLD,
                "activated": False,
            },
        ]
        both_fail_path = [
            {"source": "quick_claw", "side": "enemy", "activated": False},
            {"source": "quick_claw", "side": "player", "activated": False},
        ]
        return [enemy_success, player_success, *speed_order_options(state, rng, None, both_fail_trace, both_fail_path)]

    assert rng_stream is not None
    enemy_raw, enemy_trace = rng_stream.next_byte("quick_claw")
    enemy_activated = enemy_raw < QUICK_CLAW_THRESHOLD
    enemy_trace["side"] = "enemy"
    enemy_trace["threshold"] = QUICK_CLAW_THRESHOLD
    enemy_trace["activated"] = enemy_activated
    if enemy_activated:
        return [order_option(["enemy", "player"], "quick_claw", [enemy_trace])]

    player_raw, player_trace = rng_stream.next_byte("quick_claw")
    player_activated = player_raw < QUICK_CLAW_THRESHOLD
    player_trace["side"] = "player"
    player_trace["threshold"] = QUICK_CLAW_THRESHOLD
    player_trace["activated"] = player_activated
    if player_activated:
        return [order_option(["player", "enemy"], "quick_claw", [enemy_trace, player_trace])]
    return speed_order_options(
        state,
        rng,
        rng_stream,
        [enemy_trace, player_trace],
        [
            {"source": "quick_claw", "side": "enemy", "activated": False},
            {"source": "quick_claw", "side": "player", "activated": False},
        ],
    )


def speed_order_options(
    state: BattleState,
    rng: RngConfig,
    rng_stream: RngStream | None,
    prefix_trace: list[dict[str, Any]],
    prefix_path: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    player_speed = turn_order_speed(state.player)
    enemy_speed = turn_order_speed(state.enemy)
    if player_speed != enemy_speed:
        first = "player" if player_speed >= enemy_speed else "enemy"
        return [
            order_option(
                [first, other_side(first)],
                "speed",
                prefix_trace,
                prefix_path,
            )
        ]
    if rng.mode == "exhaustive":
        return [
            order_option(
                ["player", "enemy"],
                "speed_tie",
                [
                    *prefix_trace,
                    {"source": "speed_tie", "raw_range": [0, SPEED_TIE_THRESHOLD - 1], "raw_count": SPEED_TIE_THRESHOLD, "domain_count": 256, "branch": "player"},
                ],
                prefix_path,
            ),
            order_option(
                ["enemy", "player"],
                "speed_tie",
                [
                    *prefix_trace,
                    {"source": "speed_tie", "raw_range": [SPEED_TIE_THRESHOLD, 255], "raw_count": 256 - SPEED_TIE_THRESHOLD, "domain_count": 256, "branch": "enemy"},
                ],
                prefix_path,
            ),
        ]
    assert rng_stream is not None
    raw, trace = rng_stream.next_byte("speed_tie")
    first = "player" if raw < SPEED_TIE_THRESHOLD else "enemy"
    trace["threshold"] = SPEED_TIE_THRESHOLD
    trace["winner"] = first
    return [order_option([first, other_side(first)], "speed_tie", [*prefix_trace, trace], prefix_path)]


def order_option(
    order: list[str],
    reason: str,
    rng_trace: list[dict[str, Any]],
    prefix_path: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "turn_order": order,
        "branch_path": [
            *(prefix_path or []),
            {"source": "turn_order", "reason": reason, "order": order},
        ],
        "rng_trace": rng_trace,
    }


def turn_order_reason(option: dict[str, Any]) -> str:
    for item in option["branch_path"]:
        if item.get("source") == "turn_order":
            return str(item["reason"])
    raise SimulationInputError("turn order option missing reason")


def apply_action_branch(
    branch: dict[str, Any],
    actor: str,
    action: ActionState,
    rng: RngConfig,
    rng_stream: RngStream | None,
) -> list[dict[str, Any]]:
    state: BattleState = branch["state"]
    if action.kind == "switch":
        return [apply_switch_branch(branch, actor, action)]
    attacker = get_side(state, actor)
    defender_side = other_side(actor)
    defender = get_side(state, defender_side)
    move = selected_move(attacker, action, f"actions.{actor}")
    if attacker.hp <= 0:
        skipped = clone_branch(branch)
        skipped["events"].append(
            {"turn": state.turn, "actor": actor, "type": "skip", "reason": "user_fainted"}
        )
        return [skipped]
    if defender.hp <= 0:
        skipped = clone_branch(branch)
        skipped["events"].append(
            {"turn": state.turn, "actor": actor, "type": "skip", "reason": "target_already_fainted"}
        )
        return [skipped]
    if attacker.status == STATUS_SLEEP:
        branches: list[dict[str, Any]] = []
        for result in sleep_turn_options(attacker, move):
            checked = clone_branch(branch)
            checked["state"] = replace_side(
                state,
                actor,
                replace_status(attacker, result["status_after"], result["sleep_turns_after"]),
            )
            checked["events"].append(
                {
                    "turn": state.turn,
                    "actor": actor,
                    "type": result["event_type"],
                    "status": STATUS_SLEEP,
                    "reason": result["reason"],
                    "sleep_turns_before": attacker.sleep_turns,
                    "sleep_turns_after": result["sleep_turns_after"],
                    "proof_status": "source_mirrored_sleep_checkturn_control_flow_byte_proven_text_path_and_status_decrement",
                }
            )
            if result["blocked"]:
                branches.append(checked)
                continue
            branches.extend(apply_move_after_turn_check(checked, actor, action, rng, rng_stream))
        return branches
    if attacker.status == STATUS_FREEZE:
        result = freeze_turn_result(attacker, move)
        checked = clone_branch(branch)
        checked["state"] = replace_side(
            state,
            actor,
            replace_status(attacker, result["status_after"], attacker.sleep_turns),
        )
        if result["blocked"]:
            checked["events"].append(
                {
                    "turn": state.turn,
                    "actor": actor,
                    "type": result["event_type"],
                    "status": STATUS_FREEZE,
                    "reason": result["reason"],
                    "proof_status": "source_mirrored_freeze_turn_blocking_byte_proven_checkturn_text_path",
                }
            )
            return [checked]
        if result["reason"] != "not_frozen":
            checked["events"].append(
                {
                    "turn": state.turn,
                    "actor": actor,
                    "type": result["event_type"],
                    "status": STATUS_FREEZE,
                    "reason": result["reason"],
                    "proof_status": "source_mirrored_freeze_checkturn_bypass_byte_proven_return_path",
                }
            )
        branch = checked
        state = branch["state"]
        attacker = get_side(state, actor)
    if attacker.flinched:
        result = flinch_turn_result(attacker)
        checked = clone_branch(branch)
        checked["state"] = replace_side(
            state,
            actor,
            replace_volatile(attacker, flinched=result["flinched_after"]),
        )
        checked["events"].append(
            {
                "turn": state.turn,
                "actor": actor,
                "type": result["event_type"],
                "volatile": "flinched",
                "reason": result["reason"],
                "flinched_after": result["flinched_after"],
                "proof_status": "source_mirrored_flinch_turn_blocking_byte_proven_checkturn_text_path",
            }
        )
        return [checked]
    if attacker.status != STATUS_PARALYSIS:
        return apply_move_after_turn_check(branch, actor, action, rng, rng_stream)
    turn_check_branches = []
    for blocked, trace, path in paralysis_turn_options(attacker, rng, rng_stream):
        checked = clone_branch(branch)
        checked["rng_trace"].extend(with_turn(trace, state.turn))
        checked["branch_path"].extend(with_turn(path, state.turn))
        if blocked:
            checked["events"].append(
                {
                    "turn": state.turn,
                    "actor": actor,
                    "type": "turn_blocked",
                    "status": STATUS_PARALYSIS,
                    "reason": "fully_paralyzed",
                    "threshold": paralysis_fail_threshold(attacker),
                    "proof_status": "source_mirrored_paralysis_turn_blocking_byte_proven_checkturn_text_path",
                }
            )
            turn_check_branches.append(checked)
        else:
            turn_check_branches.append(checked)
    branches: list[dict[str, Any]] = []
    for checked in turn_check_branches:
        if checked["events"] and checked["events"][-1].get("type") == "turn_blocked":
            branches.append(checked)
            continue
        branches.extend(apply_move_after_turn_check(checked, actor, action, rng, rng_stream))
    return branches


def apply_move_after_turn_check(
    branch: dict[str, Any],
    actor: str,
    action: ActionState,
    rng: RngConfig,
    rng_stream: RngStream | None,
) -> list[dict[str, Any]]:
    state: BattleState = branch["state"]
    attacker = get_side(state, actor)
    defender_side = other_side(actor)
    defender = get_side(state, defender_side)
    move = selected_move(attacker, action, f"actions.{actor}")
    if move.bp <= 0 or move.effect not in {"normal_hit", "always_hit", "thunder", "gust", "earthquake"}:
        noop = clone_branch(branch)
        noop["events"].append(
            {
                "turn": state.turn,
                "actor": actor,
                "type": "unsupported_noop",
                "move": move.name,
                "proof_status": "out_of_scope",
                "reason": "this slice only mutates HP for normal, always-hit, Thunder, Gust, and Earthquake damaging moves",
            }
        )
        return [noop]
    branches = []
    for is_critical, critical_trace, critical_branch in critical_options(move, attacker, rng, rng_stream):
        critical_source = clone_branch(branch)
        critical_source["rng_trace"].extend(with_turn(critical_trace, state.turn))
        critical_source["branch_path"].extend(with_turn(critical_branch, state.turn))
        critical_state = critical_source["state"]
        critical_attacker = get_side(critical_state, actor)
        critical_defender = get_side(critical_state, defender_side)
        inp = battle_inputs_for(
            critical_attacker,
            critical_defender,
            move,
            critical_state,
            actor,
            is_critical=is_critical,
        )
        pre_variation = oracle.predict_damage(inp)
        trace = oracle.predict_damage_trace(inp)
        critical_level = move_critical_level(move, critical_attacker)
        critical_threshold = CRITICAL_HIT_CHANCES[min(critical_level, len(CRITICAL_HIT_CHANCES) - 1)]
        for damage, variation_trace, variation_branch in damage_variation_options(pre_variation, rng, rng_stream):
            varied_branch = clone_branch(critical_source)
            varied_branch["rng_trace"].extend(with_turn(variation_trace, state.turn))
            varied_branch["branch_path"].extend(with_turn(variation_branch, state.turn))
            varied_state = varied_branch["state"]
            current_attacker = get_side(varied_state, actor)
            current_defender = get_side(varied_state, defender_side)
            hit_check = move_hit_check(move, current_attacker, current_defender, varied_state)
            effect_damage, damage_effect = apply_post_variation_damage_effect(damage, move, current_defender)
            if hit_check["forced_miss_reason"] is not None:
                blocked = clone_branch(varied_branch)
                if hit_check["clear_target_lock_on"]:
                    blocked["state"] = replace_side(
                        blocked["state"],
                        defender_side,
                        replace_volatile(get_side(blocked["state"], defender_side), lock_on=False),
                    )
                proof_status = (
                    "source_mirrored_protect_blocks_before_accuracy"
                    if hit_check["forced_miss_reason"] == "target_protected"
                    else "byte_proven_supported_damage_move_accuracy_modifiers_overrides_semivulnerable_weather_and_sure_hit"
                )
                blocked["events"].append(
                    miss_event(
                        state,
                        actor,
                        defender_side,
                        move,
                        current_attacker,
                        current_defender,
                        hit_check,
                        proof_status=proof_status,
                        reason=hit_check["forced_miss_reason"],
                        critical_hit=is_critical,
                        critical_level=critical_level,
                        critical_threshold=critical_threshold,
                        pre_variation_damage=pre_variation,
                        post_variation_damage=damage,
                        damage_effect=damage_effect,
                    )
                )
                branches.append(blocked)
                continue
            effective_accuracy = hit_check["threshold"]
            for did_hit, accuracy_trace, accuracy_branch in accuracy_options(
                move.accuracy,
                rng,
                rng_stream,
                threshold_override=effective_accuracy,
                accuracy_level=current_attacker.accuracy_level,
                evasion_level=current_defender.evasion_level,
            ):
                action_branch = clone_branch(varied_branch)
                if hit_check["clear_target_lock_on"]:
                    target = get_side(action_branch["state"], defender_side)
                    action_branch["state"] = replace_side(
                        action_branch["state"],
                        defender_side,
                        replace_volatile(target, lock_on=False),
                    )
                action_branch["rng_trace"].extend(with_turn(accuracy_trace, state.turn))
                action_branch["branch_path"].extend(with_turn(accuracy_branch, state.turn))
                if not did_hit:
                    action_branch["events"].append(
                        miss_event(
                            state,
                            actor,
                            defender_side,
                            move,
                            current_attacker,
                            current_defender,
                            hit_check,
                            proof_status="byte_proven_supported_damage_move_accuracy_modifiers_overrides_semivulnerable_weather_and_sure_hit",
                            critical_hit=is_critical,
                            critical_level=critical_level,
                            critical_threshold=critical_threshold,
                            pre_variation_damage=pre_variation,
                            post_variation_damage=damage,
                            damage_effect=damage_effect,
                        )
                    )
                    branches.append(action_branch)
                    continue

                current_state = action_branch["state"]
                target = get_side(current_state, defender_side)
                actual_damage = min(effect_damage, target.hp)
                updated_defender = replace_hp(target, target.hp - actual_damage)
                action_branch["state"] = replace_side(current_state, defender_side, updated_defender)
                action_branch["events"].append(
                    {
                        "turn": state.turn,
                        "actor": actor,
                        "target": defender_side,
                        "type": "damage",
                        "move": move.name,
                        "accuracy": move.accuracy,
                        "effective_accuracy": effective_accuracy,
                        "accuracy_level": current_attacker.accuracy_level,
                        "target_evasion_level": current_defender.evasion_level,
                        "accuracy_override": hit_check["override"],
                        "critical_hit": is_critical,
                        "critical_level": critical_level,
                        "critical_threshold": critical_threshold,
                        "pre_variation_damage": pre_variation,
                        "post_variation_damage": damage,
                        "damage_effect": damage_effect,
                        "damage": actual_damage,
                        "target_hp_before": target.hp,
                        "target_hp_after": updated_defender.hp,
                        "target_fainted": updated_defender.hp == 0,
                        "damage_trace": [{"step": step, "damage": value} for step, value in trace],
                        "proof_status": "byte_proven_supported_damage_accuracy_modifiers_overrides_semivulnerable_weather_sure_hit_damage_core_and_variation_source_mirrored_turn_sequence",
                    }
                )
                branches.append(apply_after_hit_effects(action_branch, actor, move, effect_damage))
    return branches


def miss_event(
    state: BattleState,
    actor: str,
    defender_side: str,
    move: MoveState,
    attacker: PokemonState,
    defender: PokemonState,
    hit_check: dict[str, Any],
    *,
    proof_status: str,
    reason: str | None = None,
    critical_hit: bool | None = None,
    critical_level: int | None = None,
    critical_threshold: int | None = None,
    pre_variation_damage: int | None = None,
    post_variation_damage: int | None = None,
    damage_effect: str | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "turn": state.turn,
        "actor": actor,
        "target": defender_side,
        "type": "miss",
        "move": move.name,
        "accuracy": move.accuracy,
        "effective_accuracy": hit_check["threshold"],
        "accuracy_level": attacker.accuracy_level,
        "target_evasion_level": defender.evasion_level,
        "accuracy_override": hit_check["override"],
        "target_lock_on_cleared": hit_check["clear_target_lock_on"],
        "critical_hit": critical_hit,
        "critical_level": critical_level,
        "critical_threshold": critical_threshold,
        "pre_variation_damage": pre_variation_damage,
        "post_variation_damage": post_variation_damage,
        "damage_effect": damage_effect,
        "proof_status": proof_status,
    }
    if reason is not None:
        event["reason"] = reason
    return event


def apply_after_hit_effects(
    branch: dict[str, Any],
    actor: str,
    move: MoveState,
    cur_damage: int,
) -> dict[str, Any]:
    if cur_damage <= 0:
        return branch
    updated = branch
    defender_side = other_side(actor)
    defender = get_side(updated["state"], defender_side)
    if move.contact and defender.item == ROCKY_HELMET_ITEM:
        updated = apply_after_hit_recoil(
            updated,
            target_side=actor,
            item_name="ROCKY_HELMET",
            denominator=ROCKY_HELMET_DENOMINATOR,
            reason="contact_with_opponent_rocky_helmet",
        )
    if get_side(updated["state"], actor).hp <= 0:
        return updated
    attacker = get_side(updated["state"], actor)
    if attacker.item == SHELL_BELL_ITEM:
        updated = apply_after_hit_heal(
            updated,
            target_side=actor,
            item_name="SHELL_BELL",
            amount=max(1, cur_damage // SHELL_BELL_DENOMINATOR),
            reason="user_shell_bell_after_damage",
        )
    if get_side(updated["state"], actor).hp <= 0:
        return updated
    attacker = get_side(updated["state"], actor)
    if attacker.item == LIFE_ORB_ITEM:
        updated = apply_after_hit_recoil(
            updated,
            target_side=actor,
            item_name="LIFE_ORB",
            denominator=LIFE_ORB_DENOMINATOR,
            reason="user_life_orb_after_damage",
        )
    return updated


def apply_after_hit_recoil(
    branch: dict[str, Any],
    *,
    target_side: str,
    item_name: str,
    denominator: int,
    reason: str,
) -> dict[str, Any]:
    state: BattleState = branch["state"]
    target = get_side(state, target_side)
    recoil = max(1, target.max_hp // denominator)
    hp_after = max(0, target.hp - recoil)
    updated = clone_branch(branch)
    updated["state"] = replace_side(state, target_side, replace_hp(target, hp_after))
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": target_side,
            "type": "after_hit_recoil",
            "item": item_name,
            "reason": reason,
            "damage": target.hp - hp_after,
            "hp_before": target.hp,
            "hp_after": hp_after,
            "fainted": hp_after == 0,
            "proof_status": "byte_proven_after_hit_rocky_shell_life_orb",
        }
    )
    return updated


def apply_after_hit_heal(
    branch: dict[str, Any],
    *,
    target_side: str,
    item_name: str,
    amount: int,
    reason: str,
) -> dict[str, Any]:
    state: BattleState = branch["state"]
    target = get_side(state, target_side)
    hp_after = min(target.max_hp, target.hp + amount)
    if hp_after == target.hp:
        return branch
    updated = clone_branch(branch)
    updated["state"] = replace_side(state, target_side, replace_hp(target, hp_after))
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": target_side,
            "type": "after_hit_heal",
            "item": item_name,
            "reason": reason,
            "healed": hp_after - target.hp,
            "hp_before": target.hp,
            "hp_after": hp_after,
            "proof_status": "byte_proven_after_hit_rocky_shell_life_orb",
        }
    )
    return updated


def apply_post_action_residual_status(
    branch: dict[str, Any],
    side: str,
    *,
    enabled: bool,
) -> dict[str, Any]:
    if not enabled:
        return branch
    state: BattleState = branch["state"]
    pokemon = get_side(state, side)
    opponent = get_side(state, other_side(side))
    if pokemon.hp <= 0 or opponent.hp <= 0:
        return branch
    result = residual_status_damage_result(
        pokemon.status,
        hp=pokemon.hp,
        max_hp=pokemon.max_hp,
        toxic_count=pokemon.toxic_count,
    )
    if result is None:
        return branch

    updated_pokemon = replace_hp_and_toxic_count(
        pokemon,
        result["hp_after"],
        result["toxic_count_after"],
    )
    updated = clone_branch(branch)
    updated["state"] = replace_side(state, side, updated_pokemon)
    event = {
        "turn": state.turn,
        "actor": side,
        "type": "residual_status_damage",
        "status": result["status"],
        "damage": result["damage"],
        "raw_damage": result["raw_damage"],
        "hp_before": pokemon.hp,
        "hp_after": result["hp_after"],
        "fainted": result["hp_after"] == 0,
        "proof_status": "source_mirrored_residual_status_control_flow_byte_proven_hp_mutation",
    }
    if result["status"] == STATUS_TOXIC:
        event["toxic_count_before"] = pokemon.toxic_count
        event["toxic_count_after"] = result["toxic_count_after"]
        event["toxic_damage_unit"] = result["damage_unit"]
        event["toxic_multiplier"] = result["toxic_multiplier"]
    updated["events"].append(event)
    return updated


def residual_status_damage_result(
    status: str,
    *,
    hp: int,
    max_hp: int,
    toxic_count: int = 0,
) -> dict[str, Any] | None:
    if hp <= 0 or status in {STATUS_NONE, STATUS_PARALYSIS, STATUS_SLEEP, STATUS_FREEZE}:
        return None
    if status in {STATUS_POISON, STATUS_BURN}:
        raw_damage = eighth_max_hp_damage(max_hp)
        hp_after = max(0, hp - raw_damage)
        return {
            "status": status,
            "damage": hp - hp_after,
            "raw_damage": raw_damage,
            "damage_unit": raw_damage,
            "hp_after": hp_after,
            "toxic_count_after": toxic_count,
            "toxic_multiplier": None,
        }
    if status == STATUS_TOXIC:
        next_count = (toxic_count + 1) & 0xFF
        multiplier = next_count if next_count else 256
        damage_unit = sixteenth_max_hp_damage(max_hp)
        raw_damage = damage_unit * multiplier
        hp_after = max(0, hp - raw_damage)
        return {
            "status": status,
            "damage": hp - hp_after,
            "raw_damage": raw_damage,
            "damage_unit": damage_unit,
            "hp_after": hp_after,
            "toxic_count_after": next_count,
            "toxic_multiplier": multiplier,
        }
    raise SimulationInputError(f"unsupported status {status!r}")


def eighth_max_hp_damage(max_hp: int) -> int:
    quarter = max_hp // 4
    low_byte = quarter & 0xFF
    return max(1, low_byte // 2)


def sixteenth_max_hp_damage(max_hp: int) -> int:
    quarter = max_hp // 4
    low_byte = quarter & 0xFF
    return max(1, low_byte // 4)


def apply_between_turn_leftovers(branch: dict[str, Any]) -> dict[str, Any]:
    if battle_is_over(branch["state"]) or forced_switch_prompt_sides(branch["state"]):
        return branch
    updated = branch
    for side in ("player", "enemy"):
        updated = apply_leftovers_for_side(updated, side)
    return updated


def apply_leftovers_for_side(branch: dict[str, Any], side: str) -> dict[str, Any]:
    state: BattleState = branch["state"]
    pokemon = get_side(state, side)
    if pokemon.item != LEFTOVERS_ITEM or pokemon.hp <= 0 or pokemon.hp >= pokemon.max_hp:
        return branch
    result = leftovers_heal_result(pokemon.hp, pokemon.max_hp)
    updated_pokemon = replace_hp(pokemon, result["hp_after"])
    updated = clone_branch(branch)
    updated["state"] = replace_side(state, side, updated_pokemon)
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": side,
            "type": "between_turn_heal",
            "item": "LEFTOVERS",
            "healed": result["healed"],
            "raw_heal": result["raw_heal"],
            "hp_before": pokemon.hp,
            "hp_after": result["hp_after"],
            "proof_status": "source_mirrored_leftovers_turn_timing_byte_proven_hp_mutation",
        }
    )
    return updated


def leftovers_heal_result(hp: int, max_hp: int) -> dict[str, int]:
    raw_heal = sixteenth_max_hp_damage(max_hp)
    hp_after = min(max_hp, hp + raw_heal)
    return {
        "raw_heal": raw_heal,
        "healed": hp_after - hp,
        "hp_after": hp_after,
    }


def apply_switch_branch(
    branch: dict[str, Any],
    actor: str,
    action: ActionState,
) -> dict[str, Any]:
    state: BattleState = branch["state"]
    active = get_side(state, actor)
    bench = get_bench(state, actor)
    if action.bench_index is None:
        raise SimulationInputError(f"actions.{actor}.bench is required for switch actions")
    if action.bench_index >= len(bench):
        raise SimulationInputError(
            f"actions.{actor}.bench index {action.bench_index} out of range"
        )
    target = bench[action.bench_index]
    if target.hp <= 0:
        raise SimulationInputError(f"actions.{actor}.bench cannot switch to a fainted Pokemon")

    updated_bench = list(bench)
    updated_bench[action.bench_index] = active
    switched = clone_branch(branch)
    switched["state"] = replace_side_and_bench(
        state,
        actor,
        target,
        tuple(updated_bench),
    )
    switched["events"].append(
        {
            "turn": state.turn,
            "actor": actor,
            "type": "switch",
            "from": active.name,
            "to": target.name,
            "bench_index": action.bench_index,
            "target_hp": target.hp,
            "proof_status": "source_mirrored_selected_switch_action",
        }
    )
    return switched


def accuracy_options(
    accuracy: int,
    rng: RngConfig,
    rng_stream: RngStream | None,
    *,
    threshold_override: int | None = None,
    accuracy_level: int = NEUTRAL_STAT_LEVEL,
    evasion_level: int = NEUTRAL_STAT_LEVEL,
    always_hit: bool = False,
) -> list[tuple[bool, list[dict[str, Any]], list[dict[str, Any]]]]:
    threshold = (
        parse_threshold_override(threshold_override)
        if threshold_override is not None
        else effective_accuracy_threshold(accuracy, accuracy_level, evasion_level, always_hit)
    )
    if threshold == PERCENT_100:
        return [(True, [], [])]
    if rng.mode == "exhaustive":
        branches = []
        if threshold > 0:
            branches.append(
                (
                    True,
                    [{"source": "accuracy", "raw_range": [0, threshold - 1], "raw_count": threshold, "domain_count": 256, "threshold": threshold, "hit": True}],
                    [
                        {
                            "source": "accuracy",
                            "threshold": threshold,
                            "hit": True,
                            "accuracy_level": accuracy_level,
                            "evasion_level": evasion_level,
                        }
                    ],
                )
            )
        if threshold < 256:
            branches.append(
                (
                    False,
                    [{"source": "accuracy", "raw_range": [threshold, 255], "raw_count": 256 - threshold, "domain_count": 256, "threshold": threshold, "hit": False}],
                    [
                        {
                            "source": "accuracy",
                            "threshold": threshold,
                            "hit": False,
                            "accuracy_level": accuracy_level,
                            "evasion_level": evasion_level,
                        }
                    ],
                )
            )
        return branches
    assert rng_stream is not None
    raw, trace = rng_stream.next_byte("accuracy")
    hit = raw < threshold
    trace["threshold"] = threshold
    trace["hit"] = hit
    return [
        (
            hit,
            [trace],
            [
                {
                    "source": "accuracy",
                    "threshold": threshold,
                    "hit": hit,
                    "accuracy_level": accuracy_level,
                    "evasion_level": evasion_level,
                }
            ],
        )
    ]


def paralysis_turn_options(
    pokemon: PokemonState,
    rng: RngConfig,
    rng_stream: RngStream | None,
) -> list[tuple[bool, list[dict[str, Any]], list[dict[str, Any]]]]:
    threshold = paralysis_fail_threshold(pokemon)
    if rng.mode == "exhaustive":
        branches = []
        if threshold > 0:
            branches.append(
                (
                    True,
                    [
                        {
                            "source": "paralysis",
                            "raw_range": [0, threshold - 1],
                            "raw_count": threshold,
                            "domain_count": 256,
                            "threshold": threshold,
                            "blocked": True,
                        }
                    ],
                    [{"source": "paralysis", "threshold": threshold, "blocked": True}],
                )
            )
        if threshold < 256:
            branches.append(
                (
                    False,
                    [
                        {
                            "source": "paralysis",
                            "raw_range": [threshold, 255],
                            "raw_count": 256 - threshold,
                            "domain_count": 256,
                            "threshold": threshold,
                            "blocked": False,
                        }
                    ],
                    [{"source": "paralysis", "threshold": threshold, "blocked": False}],
                )
            )
        return branches

    assert rng_stream is not None
    raw, trace = rng_stream.next_byte("paralysis")
    blocked = raw < threshold
    trace["threshold"] = threshold
    trace["blocked"] = blocked
    return [
        (
            blocked,
            [trace],
            [{"source": "paralysis", "threshold": threshold, "blocked": blocked}],
        )
    ]


def sleep_turn_options(pokemon: PokemonState, move: MoveState) -> list[dict[str, Any]]:
    next_turns = max(0, pokemon.sleep_turns - 1)
    if next_turns == 0:
        return [
            {
                "blocked": False,
                "event_type": "status_woke_up",
                "reason": "woke_up",
                "status_after": STATUS_NONE,
                "sleep_turns_after": 0,
            }
        ]
    blocked = not move_matches_any(move, SLEEP_BYPASS_MOVES)
    return [
        {
            "blocked": blocked,
            "event_type": "turn_blocked" if blocked else "status_check",
            "reason": "fast_asleep" if blocked else "sleep_bypass_move",
            "status_after": STATUS_SLEEP,
            "sleep_turns_after": next_turns,
        }
    ]


def freeze_turn_result(pokemon: PokemonState, move: MoveState) -> dict[str, Any]:
    if pokemon.status != STATUS_FREEZE:
        return {
            "blocked": False,
            "event_type": "status_check",
            "reason": "not_frozen",
            "status_after": pokemon.status,
        }
    if move_matches_any(move, FREEZE_BYPASS_MOVES):
        return {
            "blocked": False,
            "event_type": "status_check",
            "reason": "thaw_move_bypasses_freeze",
            "status_after": STATUS_FREEZE,
        }
    return {
        "blocked": True,
        "event_type": "turn_blocked",
        "reason": "frozen_solid",
        "status_after": STATUS_FREEZE,
    }


def flinch_turn_result(pokemon: PokemonState) -> dict[str, Any]:
    return {
        "blocked": pokemon.flinched,
        "event_type": "turn_blocked" if pokemon.flinched else "status_check",
        "reason": "flinched" if pokemon.flinched else "not_flinched",
        "flinched_after": False,
    }


def paralysis_fail_threshold(pokemon: PokemonState) -> int:
    contribution = type_contribution(oracle.FIGHTING, pokemon.types)
    if contribution == 2:
        return PARALYSIS_FAIL_FIGHTING_FULL
    if contribution == 1:
        return PARALYSIS_FAIL_FIGHTING_HALF
    return PARALYSIS_FAIL_BASELINE


def type_contribution(target_type: int, types: tuple[int, int]) -> int:
    first, second = types
    if first == second:
        return 2 if first == target_type else 0
    return 1 if target_type in types else 0


def critical_options(
    move: MoveState,
    attacker: PokemonState,
    rng: RngConfig,
    rng_stream: RngStream | None,
) -> list[tuple[bool, list[dict[str, Any]], list[dict[str, Any]]]]:
    level = move_critical_level(move, attacker)
    threshold = CRITICAL_HIT_CHANCES[min(level, len(CRITICAL_HIT_CHANCES) - 1)]
    if rng.mode == "exhaustive":
        return [
            (
                True,
                [{"source": "critical_hit", "raw_range": [0, threshold - 1], "raw_count": threshold, "domain_count": 256, "threshold": threshold, "critical": True, "critical_level": level}],
                [{"source": "critical_hit", "threshold": threshold, "critical": True, "critical_level": level}],
            ),
            (
                False,
                [{"source": "critical_hit", "raw_range": [threshold, 255], "raw_count": 256 - threshold, "domain_count": 256, "threshold": threshold, "critical": False, "critical_level": level}],
                [{"source": "critical_hit", "threshold": threshold, "critical": False, "critical_level": level}],
            ),
        ]
    assert rng_stream is not None
    raw, trace = rng_stream.next_byte("critical_hit")
    is_critical = raw < threshold
    trace["threshold"] = threshold
    trace["critical"] = is_critical
    trace["critical_level"] = level
    return [
        (
            is_critical,
            [trace],
            [{"source": "critical_hit", "threshold": threshold, "critical": is_critical, "critical_level": level}],
        )
    ]


def move_critical_level(move: MoveState, attacker: PokemonState) -> int:
    level = 0
    if attacker.name == "CHANSEY" and attacker.item == LUCKY_PUNCH_ITEM:
        level += 2
    elif attacker.name == "FARFETCH_D" and attacker.item == STICK_ITEM:
        level += 2
    if attacker.focus_energy:
        level += 1
    if move_matches_any(move, HIGH_CRITICAL_HIT_MOVES):
        level += 2
    if attacker.item == SCOPE_LENS_ITEM:
        level += 1
    return min(level, len(CRITICAL_HIT_CHANCES) - 1)


def parse_threshold_override(raw: int) -> int:
    if raw < 0 or raw > PERCENT_100:
        raise SimulationInputError(f"accuracy threshold override must be between 0 and {PERCENT_100}")
    return raw


def move_hit_check(
    move: MoveState,
    attacker: PokemonState,
    defender: PokemonState,
    state: BattleState,
) -> dict[str, Any]:
    if defender.protect:
        return {
            "threshold": 0,
            "override": "protect",
            "forced_miss_reason": "target_protected",
            "clear_target_lock_on": False,
        }
    if defender.lock_on:
        if not (defender.flying and move_matches_any(move, DIG_TARGET_HIT_MOVES)):
            return {
                "threshold": PERCENT_100,
                "override": "lock_on",
                "forced_miss_reason": None,
                "clear_target_lock_on": True,
            }
        clear_lock_on = True
    else:
        clear_lock_on = False
    if defender.flying and not move_matches_any(move, FLYING_TARGET_HIT_MOVES):
        return {
            "threshold": 0,
            "override": "semi_invulnerable",
            "forced_miss_reason": "target_flying",
            "clear_target_lock_on": clear_lock_on,
        }
    if defender.underground and not move_matches_any(move, UNDERGROUND_TARGET_HIT_MOVES):
        return {
            "threshold": 0,
            "override": "semi_invulnerable",
            "forced_miss_reason": "target_underground",
            "clear_target_lock_on": clear_lock_on,
        }
    if move.effect == "thunder" and state.weather == oracle.WEATHER_RAIN:
        return {
            "threshold": PERCENT_100,
            "override": "thunder_rain",
            "forced_miss_reason": None,
            "clear_target_lock_on": clear_lock_on,
        }
    if attacker.x_accuracy:
        return {
            "threshold": PERCENT_100,
            "override": "x_accuracy",
            "forced_miss_reason": None,
            "clear_target_lock_on": clear_lock_on,
        }
    threshold = move_accuracy_threshold(move, attacker, defender)
    override = "always_hit" if move.effect == "always_hit" else None
    if override is None and defender.item == BRIGHTPOWDER_ITEM:
        threshold = max(0, threshold - BRIGHTPOWDER_MISS_CHANCE)
        override = "brightpowder"
    return {
        "threshold": threshold,
        "override": override,
        "forced_miss_reason": None,
        "clear_target_lock_on": clear_lock_on,
    }


def move_accuracy_threshold(move: MoveState, attacker: PokemonState, defender: PokemonState) -> int:
    return effective_accuracy_threshold(
        move.accuracy,
        attacker.accuracy_level,
        defender.evasion_level,
        move.effect == "always_hit",
    )


def move_matches_any(move: MoveState, move_names: tuple[str, ...]) -> bool:
    if move.name in move_names:
        return True
    if move.move_id is None:
        return False
    return any(move.move_id == move_id_for_name(name) for name in move_names)


def effective_accuracy_threshold(
    accuracy: int,
    accuracy_level: int = NEUTRAL_STAT_LEVEL,
    evasion_level: int = NEUTRAL_STAT_LEVEL,
    always_hit: bool = False,
) -> int:
    if always_hit:
        return PERCENT_100
    for level, path in (
        (accuracy_level, "accuracy_level"),
        (evasion_level, "evasion_level"),
    ):
        if level < MIN_STAT_LEVEL or level > MAX_STAT_LEVEL:
            raise SimulationInputError(f"{path} must be between {MIN_STAT_LEVEL} and {MAX_STAT_LEVEL}")
    result = max(1, accuracy)
    for level in (accuracy_level, MAX_STAT_LEVEL + 1 - evasion_level):
        numerator, denominator = ACCURACY_LEVEL_MULTIPLIERS[level - 1]
        result = result * numerator // denominator
        if result == 0:
            result = 1
    return min(PERCENT_100, result)


def damage_variation_options(
    damage: int,
    rng: RngConfig,
    rng_stream: RngStream | None,
) -> list[tuple[int, list[dict[str, Any]], list[dict[str, Any]]]]:
    if damage < 2:
        return [(damage, [], [{"source": "damage_variation", "reason": "damage_less_than_2"}])]
    if rng.mode == "exhaustive":
        return [
            (
                damage * multiplier // PERCENT_100,
                [
                    {
                        "source": "damage_variation",
                        "multiplier": multiplier,
                        "raw": None,
                        "raw_count": 1,
                        "domain_count": DAMAGE_VARIATION_OUTCOME_COUNT,
                    }
                ],
                [{"source": "damage_variation", "multiplier": multiplier}],
            )
            for multiplier in range(DAMAGE_VARIATION_MIN, PERCENT_100 + 1)
        ]
    assert rng_stream is not None
    traces = []
    while True:
        raw, trace = rng_stream.next_byte("damage_variation")
        multiplier = rotate_right_carry(raw)
        trace["rotated"] = multiplier
        trace["accepted"] = multiplier >= DAMAGE_VARIATION_MIN
        traces.append(trace)
        if multiplier >= DAMAGE_VARIATION_MIN:
            return [
                (
                    damage * multiplier // PERCENT_100,
                    traces,
                    [{"source": "damage_variation", "multiplier": multiplier}],
                )
            ]


def apply_post_variation_damage_effect(
    damage: int,
    move: MoveState,
    defender: PokemonState,
) -> tuple[int, str | None]:
    if move.effect == "gust" and defender.flying:
        return double_damage(damage), "double_flying_damage"
    if move.effect == "earthquake" and defender.underground:
        return double_damage(damage), "double_underground_damage"
    return damage, None


def double_damage(damage: int) -> int:
    doubled = damage * 2
    return min(doubled, 0xFFFF)


def battle_inputs_for(
    attacker: PokemonState,
    defender: PokemonState,
    move: MoveState,
    state: BattleState,
    actor: str,
    *,
    is_critical: bool = False,
) -> oracle.BattleInputs:
    is_physical = tables.is_physical_type(move.move_type)
    return oracle.BattleInputs(
        attacker_level=attacker.level,
        move_bp=move.bp,
        move_type=move.move_type,
        is_physical=is_physical,
        attacker_atk=attacker.attack if is_physical else attacker.sp_attack,
        defender_def=defender.defense if is_physical else defender.sp_defense,
        attacker_types=attacker.types,
        defender_types=defender.types,
        user_item=attacker.item,
        opponent_item=defender.item,
        can_evolve_attacker=attacker.can_evolve,
        can_evolve_defender=defender.can_evolve,
        is_critical=is_critical,
        weather=state.weather,
        battle_turn=0 if actor == "player" else 1,
    )


def parse_rng(raw: Any) -> RngConfig:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise SimulationInputError("rng must be an object")
    mode = str(raw.get("mode", "fixed")).lower()
    if mode not in {"fixed", "sample", "exhaustive"}:
        raise SimulationInputError("rng.mode must be fixed, sample, or exhaustive")
    values = tuple(parse_byte(value, "rng.values") for value in raw.get("values", ()))
    seed = raw.get("seed")
    if seed is not None and not isinstance(seed, int):
        raise SimulationInputError("rng.seed must be an integer")
    samples = raw.get("samples", 1)
    if not isinstance(samples, int) or samples < 1:
        raise SimulationInputError("rng.samples must be a positive integer")
    if mode == "fixed":
        if seed is not None:
            raise SimulationInputError("rng.seed is only valid for sample mode")
        if "samples" in raw and samples != 1:
            raise SimulationInputError("rng.samples is only valid for sample mode")
    elif mode == "sample":
        if values:
            raise SimulationInputError("rng.values is only valid for fixed mode")
    elif mode == "exhaustive":
        if values:
            raise SimulationInputError("rng.values is only valid for fixed mode")
        if seed is not None:
            raise SimulationInputError("rng.seed is only valid for sample mode")
        if "samples" in raw and samples != 1:
            raise SimulationInputError("rng.samples is only valid for sample mode")
    return RngConfig(mode=mode, values=values, seed=seed, samples=samples)


def parse_state(raw: Any) -> BattleState:
    if not isinstance(raw, dict):
        raise SimulationInputError("state must be an object")
    player, player_bench = parse_side("player", raw.get("player"))
    enemy, enemy_bench = parse_side("enemy", raw.get("enemy"))
    return BattleState(
        player=player,
        enemy=enemy,
        weather=parse_weather(raw.get("weather", "none")),
        turn=parse_positive_int(raw.get("turn", 1), "state.turn"),
        player_bench=player_bench,
        enemy_bench=enemy_bench,
    )


def parse_turns(payload: dict[str, Any], state: BattleState) -> list[dict[str, ActionState]]:
    if "turns" not in payload:
        return [parse_actions(payload.get("actions"), "actions")]
    raw_turns = payload["turns"]
    if not isinstance(raw_turns, list) or not raw_turns:
        raise SimulationInputError("turns must be a non-empty list")
    turns = []
    for index, raw_turn in enumerate(raw_turns):
        path = f"turns[{index}]"
        if not isinstance(raw_turn, dict):
            raise SimulationInputError(f"{path} must be an object")
        turns.append(parse_actions(raw_turn.get("actions"), f"{path}.actions"))
    return turns


def parse_side(side: str, raw: Any) -> tuple[PokemonState, tuple[PokemonState, ...]]:
    active = parse_pokemon(side, raw, f"state.{side}")
    bench_raw = raw.get("bench", []) if isinstance(raw, dict) else []
    if not isinstance(bench_raw, list):
        raise SimulationInputError(f"state.{side}.bench must be a list")
    bench = tuple(
        parse_pokemon(side, item, f"state.{side}.bench[{index}]")
        for index, item in enumerate(bench_raw)
    )
    return active, bench


def parse_pokemon(side: str, raw: Any, path: str | None = None) -> PokemonState:
    base_path = path or f"state.{side}"
    if not isinstance(raw, dict):
        raise SimulationInputError(f"{base_path} must be an object")
    stats = raw.get("stats", {})
    if not isinstance(stats, dict):
        raise SimulationInputError(f"{base_path}.stats must be an object")
    stages = raw.get("stages", {})
    if not isinstance(stages, dict):
        raise SimulationInputError(f"{base_path}.stages must be an object")
    volatile = raw.get("volatile", {})
    if not isinstance(volatile, dict):
        raise SimulationInputError(f"{base_path}.volatile must be an object")
    level = parse_positive_int(raw.get("level"), f"{base_path}.level")
    species_row = source_species_row(raw.get("species"), f"{base_path}.species")
    if species_row is None:
        type_names, type_ids = parse_type_pair(raw.get("types"), f"{base_path}.types")
        max_hp = parse_positive_int(raw.get("max_hp"), f"{base_path}.max_hp")
        attack = parse_positive_int(stats.get("attack"), f"{base_path}.stats.attack")
        defense = parse_positive_int(stats.get("defense"), f"{base_path}.stats.defense")
        speed = parse_positive_int(stats.get("speed"), f"{base_path}.stats.speed")
        sp_attack = parse_positive_int(
            stats.get("sp_attack", stats.get("special_attack")),
            f"{base_path}.stats.sp_attack",
        )
        sp_defense = parse_positive_int(
            stats.get("sp_defense", stats.get("special_defense")),
            f"{base_path}.stats.sp_defense",
        )
        can_evolve = bool(raw.get("can_evolve", False))
    else:
        type_names, type_ids = parse_type_pair(
            raw.get("types", [species_row.type_a, species_row.type_b]),
            f"{base_path}.types",
        )
        iv, statexp_term = parse_stat_profile(raw, base_path)
        max_hp = parse_positive_int(
            raw.get("max_hp", tables.compute_hp(species_row.hp, level, iv, statexp_term)),
            f"{base_path}.max_hp",
        )
        attack = parse_stat_override(
            stats, "attack", None, species_row.atk, level, iv, statexp_term, f"{base_path}.stats.attack"
        )
        defense = parse_stat_override(
            stats, "defense", None, species_row.def_, level, iv, statexp_term, f"{base_path}.stats.defense"
        )
        speed = parse_stat_override(
            stats, "speed", None, species_row.spe, level, iv, statexp_term, f"{base_path}.stats.speed"
        )
        sp_attack = parse_stat_override(
            stats,
            "sp_attack",
            "special_attack",
            species_row.sat,
            level,
            iv,
            statexp_term,
            f"{base_path}.stats.sp_attack",
        )
        sp_defense = parse_stat_override(
            stats,
            "sp_defense",
            "special_defense",
            species_row.sdf,
            level,
            iv,
            statexp_term,
            f"{base_path}.stats.sp_defense",
        )
        can_evolve = bool(
            raw.get("can_evolve", tables.load_can_evolve().get(species_row.species, False))
        )
    hp = parse_non_negative_int(raw.get("hp", max_hp), f"{base_path}.hp")
    if hp > max_hp:
        raise SimulationInputError(f"{base_path}.hp cannot exceed max_hp")
    moves_raw = raw.get("moves", ())
    if not isinstance(moves_raw, list) or not moves_raw:
        raise SimulationInputError(f"{base_path}.moves must be a non-empty list")
    status = parse_status(raw.get("status", STATUS_NONE), f"{base_path}.status")
    sleep_turns = parse_sleep_turns(raw.get("sleep_turns"), status, f"{base_path}.sleep_turns")
    return PokemonState(
        side=side,
        name=str(
            raw.get("name", species_row.species if species_row is not None else side)
        ).upper(),
        level=level,
        hp=hp,
        max_hp=max_hp,
        types=type_ids,
        type_names=type_names,
        attack=attack,
        defense=defense,
        speed=speed,
        sp_attack=sp_attack,
        sp_defense=sp_defense,
        item=parse_item(raw.get("item", 0)),
        status=status,
        sleep_turns=sleep_turns,
        toxic_count=parse_byte(raw.get("toxic_count", 0), f"{base_path}.toxic_count"),
        can_evolve=can_evolve,
        accuracy_level=parse_stage_modifier(stages.get("accuracy", 0), f"{base_path}.stages.accuracy"),
        evasion_level=parse_stage_modifier(stages.get("evasion", 0), f"{base_path}.stages.evasion"),
        protect=parse_bool(volatile.get("protect", False), f"{base_path}.volatile.protect"),
        x_accuracy=parse_bool(volatile.get("x_accuracy", False), f"{base_path}.volatile.x_accuracy"),
        lock_on=parse_bool(volatile.get("lock_on", False), f"{base_path}.volatile.lock_on"),
        flying=parse_bool(volatile.get("flying", False), f"{base_path}.volatile.flying"),
        underground=parse_bool(volatile.get("underground", False), f"{base_path}.volatile.underground"),
        focus_energy=parse_bool(volatile.get("focus_energy", False), f"{base_path}.volatile.focus_energy"),
        flinched=parse_bool(volatile.get("flinched", False), f"{base_path}.volatile.flinched"),
        moves=tuple(
            parse_move(move, f"{base_path}.moves[{index}]")
            for index, move in enumerate(moves_raw)
        ),
    )


def parse_move(raw: Any, path: str) -> MoveState:
    if isinstance(raw, str):
        return parse_source_move(raw, {}, path)
    if not isinstance(raw, dict):
        raise SimulationInputError(f"{path} must be an object")
    if isinstance(raw.get("name"), str):
        source_overrides = dict(raw)
        if {"type", "bp", "accuracy"}.issubset(raw) and "effect" not in raw:
            source_overrides["effect"] = "normal_hit"
        source_move = parse_source_move(str(raw["name"]), source_overrides, path)
        if any(
            key not in raw
            for key in ("type", "bp", "accuracy", "move_id", "priority", "effect")
        ):
            return source_move
    type_name, type_id = parse_type(raw.get("type"), f"{path}.type")
    return MoveState(
        name=str(raw.get("name", "MOVE")).upper(),
        move_type=type_id,
        move_type_name=type_name,
        bp=parse_non_negative_int(raw.get("bp"), f"{path}.bp"),
        move_id=parse_optional_byte(raw.get("move_id"), f"{path}.move_id"),
        priority=parse_int(raw.get("priority", 0), f"{path}.priority"),
        accuracy=parse_byte(raw.get("accuracy", PERCENT_100), f"{path}.accuracy"),
        effect=str(raw.get("effect", "normal_hit")),
        contact=parse_bool(raw.get("contact", False), f"{path}.contact"),
    )


def source_species_row(raw: Any, path: str) -> tables.BaseStatsRow | None:
    if raw in (None, ""):
        return None
    if not isinstance(raw, str):
        raise SimulationInputError(f"{path} must be a species name")
    key = tables.resolve_name(raw, tables.load_base_stats(), "species")
    return tables.load_base_stats()[key]


def parse_stat_profile(raw: dict[str, Any], path: str) -> tuple[int, int]:
    if "iv" in raw or "statexp_term" in raw:
        iv = parse_non_negative_int(
            raw.get("iv", tables.TRAINER_IV_STATEEXP[0]),
            f"{path}.iv",
        )
        statexp_term = parse_non_negative_int(
            raw.get("statexp_term", tables.TRAINER_IV_STATEEXP[1]),
            f"{path}.statexp_term",
        )
        return iv, statexp_term
    profile = str(raw.get("profile", raw.get("grind", "trainer"))).lower()
    if profile == "trainer":
        return tables.TRAINER_IV_STATEEXP
    if profile in tables.GRINDS:
        return tables.GRINDS[profile]
    known = ", ".join(["trainer", *sorted(tables.GRINDS)])
    raise SimulationInputError(f"{path}.profile must be one of: {known}")


def parse_stat_override(
    stats: dict[str, Any],
    key: str,
    alias: str | None,
    base: int,
    level: int,
    iv: int,
    statexp_term: int,
    path: str,
) -> int:
    raw = stats.get(key)
    if raw is None and alias is not None:
        raw = stats.get(alias)
    if raw is not None:
        return parse_positive_int(raw, path)
    return tables.compute_stat(base, level, iv, statexp_term, is_hp=False)


def parse_source_move(name: str, overrides: dict[str, Any], path: str) -> MoveState:
    move_key = tables.resolve_move(name)
    row = tables.load_moves()[move_key]
    type_name, type_id = parse_type(overrides.get("type", row.type_name), f"{path}.type")
    return MoveState(
        name=str(overrides.get("name", move_key)).upper(),
        move_type=type_id,
        move_type_name=type_name,
        bp=parse_non_negative_int(overrides.get("bp", row.bp), f"{path}.bp"),
        move_id=parse_optional_byte(
            overrides.get("move_id", move_id_for_name(move_key)),
            f"{path}.move_id",
        ),
        priority=parse_int(
            overrides.get("priority", source_move_priority(row.effect)),
            f"{path}.priority",
        ),
        accuracy=parse_byte(
            overrides.get("accuracy", percent_accuracy_to_byte(row.accuracy)),
            f"{path}.accuracy",
        ),
        effect=str(overrides.get("effect", simulator_effect(row.effect))),
        contact=parse_bool(
            overrides.get("contact", source_move_contact(move_key)),
            f"{path}.contact",
        ),
    )


def move_id_for_name(move_key: str) -> int:
    global _MOVE_IDS
    if _MOVE_IDS is None:
        _MOVE_IDS = tables.parse_const_values(tables.ROOT / "constants/move_constants.asm")
    return _MOVE_IDS[move_key]


def source_move_contact(move_key: str) -> bool:
    global _MOVE_CONTACT_FLAGS
    if _MOVE_CONTACT_FLAGS is None:
        _MOVE_CONTACT_FLAGS = load_move_contact_flags()
    return _MOVE_CONTACT_FLAGS.get(move_key, False)


def load_move_contact_flags() -> dict[str, bool]:
    move_ids = tables.parse_const_values(tables.ROOT / "constants/move_constants.asm")
    by_id = {move_id: move_name for move_name, move_id in move_ids.items()}
    flags: dict[str, bool] = {}
    for line in (tables.ROOT / "data/moves/contact_flags.asm").read_text(encoding="utf-8").splitlines():
        if ";" not in line or "db" not in line:
            continue
        raw_flag, raw_comment = line.split(";", 1)
        flag_text = raw_flag.split("db", 1)[1].strip().upper()
        if flag_text not in {"TRUE", "FALSE"}:
            continue
        move_name = raw_comment.strip().split()[0]
        if move_name not in move_ids:
            continue
        flags[by_id[move_ids[move_name]]] = flag_text == "TRUE"
    return flags


def source_move_priority(effect: str) -> int:
    if effect == "EFFECT_PRIORITY_HIT":
        return PRIORITY_HIT_PRIORITY
    return BASE_PRIORITY


def simulator_effect(effect: str) -> str:
    if effect in {"EFFECT_NORMAL_HIT", "EFFECT_PRIORITY_HIT"}:
        return "normal_hit"
    if effect == "EFFECT_ALWAYS_HIT":
        return "always_hit"
    return effect.removeprefix("EFFECT_").lower()


def percent_accuracy_to_byte(value: int) -> int:
    return value * PERCENT_100 // 100


def parse_stage_modifier(raw: Any, path: str) -> int:
    value = parse_int(raw, path)
    if value < -6 or value > 6:
        raise SimulationInputError(f"{path} must be between -6 and 6")
    return value + NEUTRAL_STAT_LEVEL


def parse_bool(raw: Any, path: str) -> bool:
    if isinstance(raw, bool):
        return raw
    raise SimulationInputError(f"{path} must be true or false")


def parse_actions(raw: Any, path: str = "actions") -> dict[str, ActionState]:
    if not isinstance(raw, dict):
        raise SimulationInputError(f"{path} must be an object")
    return {
        "player": parse_action(raw.get("player"), f"{path}.player"),
        "enemy": parse_action(raw.get("enemy"), f"{path}.enemy"),
    }


def parse_action(raw: Any, path: str) -> ActionState:
    if isinstance(raw, int):
        return ActionState(kind="move", move_index=parse_non_negative_int(raw, f"{path}.move"))
    elif isinstance(raw, dict):
        action_type = str(raw.get("type", "move")).lower()
        if action_type == "move":
            return ActionState(kind="move", move_index=parse_non_negative_int(raw.get("move"), f"{path}.move"))
        if action_type == "switch":
            return ActionState(kind="switch", bench_index=parse_non_negative_int(raw.get("bench"), f"{path}.bench"))
        if action_type == "wait":
            return ActionState(kind="wait")
        if action_type == "boss_ai_selector":
            return ActionState(
                kind="boss_ai_selector",
                boss_ai_selector=parse_boss_ai_selector(raw, path),
            )
        if action_type == "boss_ai_switch_policy":
            return ActionState(
                kind="boss_ai_switch_policy",
                boss_ai_switch_policy=parse_boss_ai_switch_policy(raw, path),
            )
        raise SimulationInputError(f"{path}.type must be move, switch, wait, boss_ai_selector, or boss_ai_switch_policy")
    raise SimulationInputError(f"{path} must be a move index or object")


def parse_boss_ai_selector(raw: dict[str, Any], path: str) -> BossAiSelectorState:
    move_ids = raw.get("move_ids")
    scores = raw.get("scores")
    if not isinstance(move_ids, list) or len(move_ids) != 4:
        raise SimulationInputError(f"{path}.move_ids must contain four move ids")
    if not isinstance(scores, list) or len(scores) != 4:
        raise SimulationInputError(f"{path}.scores must contain four score bytes")
    raw_move_names = raw.get("move_names", [])
    if raw_move_names and (not isinstance(raw_move_names, list) or len(raw_move_names) != 4):
        raise SimulationInputError(f"{path}.move_names must contain four names when present")
    return BossAiSelectorState(
        scenario_id=str(raw.get("scenario_id", "headless_boss_ai_selector")),
        tier=raw.get("tier", "late"),
        move_ids=tuple(parse_byte(value, f"{path}.move_ids[{index}]") for index, value in enumerate(move_ids)),
        scores=tuple(parse_byte(value, f"{path}.scores[{index}]") for index, value in enumerate(scores)),
        move_names=tuple(str(value).upper() for value in raw_move_names),
    )


def parse_boss_ai_switch_policy(raw: dict[str, Any], path: str) -> BossAiSwitchPolicyState:
    threshold = raw.get("threshold")
    return BossAiSwitchPolicyState(
        scenario_id=str(raw.get("scenario_id", "headless_boss_ai_switch_policy")),
        candidate_bench=parse_non_negative_int(raw.get("candidate_bench"), f"{path}.candidate_bench"),
        confidence=parse_byte(raw.get("confidence"), f"{path}.confidence"),
        tier=raw.get("tier", "late"),
        trainer_class=str(raw.get("trainer_class", "")),
        threshold=None if threshold is None else parse_byte(threshold, f"{path}.threshold"),
        anti_loop=parse_bool(raw.get("anti_loop", False), f"{path}.anti_loop"),
        sack_bias=parse_bool(raw.get("sack_bias", False), f"{path}.sack_bias"),
        wincon_risk=parse_bool(raw.get("wincon_risk", False), f"{path}.wincon_risk"),
        fallback_move_index=parse_non_negative_int(raw.get("fallback_move", 0), f"{path}.fallback_move"),
    )


def parse_type_pair(raw: Any, path: str) -> tuple[tuple[str, str], tuple[int, int]]:
    if not isinstance(raw, list) or not raw:
        raise SimulationInputError(f"{path} must be a non-empty list")
    if len(raw) > 2:
        raise SimulationInputError(f"{path} must contain one or two types")
    first_name, first_id = parse_type(raw[0], f"{path}[0]")
    if len(raw) == 1:
        return (first_name, first_name), (first_id, first_id)
    second_name, second_id = parse_type(raw[1], f"{path}[1]")
    return (first_name, second_name), (first_id, second_id)


def parse_type(raw: Any, path: str) -> tuple[str, int]:
    if isinstance(raw, int):
        for name, value in tables.load_type_constants().items():
            if value == raw and value in tables.ALL_DAMAGE_TYPE_VALUES:
                return name, value
        raise SimulationInputError(f"{path} unknown damage type id {raw}")
    if not isinstance(raw, str):
        raise SimulationInputError(f"{path} must be a type name or id")
    name = tables.resolve_type_name(raw)
    value = tables.load_type_constants()[name]
    if value not in tables.ALL_DAMAGE_TYPE_VALUES:
        raise SimulationInputError(f"{path} must be a damage type, got {raw!r}")
    return name, value


def parse_weather(raw: Any) -> int:
    if isinstance(raw, int):
        return raw
    if not isinstance(raw, str):
        raise SimulationInputError("state.weather must be a string or int")
    key = raw.strip().lower()
    if key in {"none", "clear", "weather_none"}:
        return oracle.WEATHER_NONE
    return tables.weather_to_int(key)


def parse_item(raw: Any) -> int:
    if raw in (None, "", 0, "0", "none", "NONE", "NO_ITEM", "HELD_NONE"):
        return oracle.HELD_NONE
    if isinstance(raw, int):
        return raw
    if not isinstance(raw, str):
        raise SimulationInputError("item must be an integer or item constant")
    return tables.resolve_item(raw)


def parse_status(raw: Any, path: str) -> str:
    if not isinstance(raw, str):
        raise SimulationInputError(f"{path} must be a status string")
    key = raw.strip().lower()
    if key not in STATUS_ALIASES:
        known = ", ".join(sorted(k for k in STATUS_ALIASES if k))
        raise SimulationInputError(
            f"{path} must be one of the currently modeled statuses: {known}"
        )
    return STATUS_ALIASES[key]


def parse_sleep_turns(raw: Any, status: str, path: str) -> int:
    if raw is None:
        return 1 if status == STATUS_SLEEP else 0
    value = parse_byte(raw, path)
    if status == STATUS_SLEEP:
        if value < 1 or value > 7:
            raise SimulationInputError(f"{path} must be between 1 and 7 for sleep")
        return value
    if value != 0:
        raise SimulationInputError(f"{path} must be 0 unless status is sleep")
    return 0


def parse_int(raw: Any, path: str) -> int:
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise SimulationInputError(f"{path} must be an integer")
    return raw


def parse_positive_int(raw: Any, path: str) -> int:
    value = parse_int(raw, path)
    if value <= 0:
        raise SimulationInputError(f"{path} must be positive")
    return value


def parse_non_negative_int(raw: Any, path: str) -> int:
    value = parse_int(raw, path)
    if value < 0:
        raise SimulationInputError(f"{path} must be non-negative")
    return value


def parse_byte(raw: Any, path: str) -> int:
    value = parse_int(raw, path)
    if value < 0 or value > 255:
        raise SimulationInputError(f"{path} must be in byte range 0..255")
    return value


def parse_optional_byte(raw: Any, path: str) -> int | None:
    if raw is None:
        return None
    return parse_byte(raw, path)


def rotate_right_carry(value: int) -> int:
    return ((value & 1) << 7) | (value >> 1)


def other_side(side: str) -> str:
    return "enemy" if side == "player" else "player"


def turn_order_speed(pokemon: PokemonState) -> int:
    speed = status_adjusted_speed(pokemon)
    if pokemon.item == CHOICE_SCARF_ITEM:
        return speed * 3 // 2
    return speed


def status_adjusted_speed(pokemon: PokemonState) -> int:
    speed = pokemon.speed
    electric_contribution = type_contribution(oracle.ELECTRIC, pokemon.types)
    if electric_contribution == 2:
        speed = apply_stat_fraction(speed, *ELECTRIC_SPEED_FULL)
    elif electric_contribution == 1:
        speed = apply_stat_fraction(speed, *ELECTRIC_SPEED_HALF)
    if pokemon.status != STATUS_PARALYSIS:
        return speed
    fighting_contribution = type_contribution(oracle.FIGHTING, pokemon.types)
    if fighting_contribution == 2:
        return apply_stat_fraction(speed, *PARALYSIS_SPEED_FIGHTING_FULL)
    if fighting_contribution == 1:
        return apply_stat_fraction(speed, *PARALYSIS_SPEED_FIGHTING_HALF)
    return apply_stat_fraction(speed, *PARALYSIS_SPEED_BASELINE)


def apply_stat_fraction(value: int, numerator: int, denominator: int) -> int:
    return max(1, value * numerator // denominator)


def get_side(state: BattleState, side: str) -> PokemonState:
    return state.player if side == "player" else state.enemy


def get_bench(state: BattleState, side: str) -> tuple[PokemonState, ...]:
    return state.player_bench if side == "player" else state.enemy_bench


def replace_side(state: BattleState, side: str, pokemon: PokemonState) -> BattleState:
    if side == "player":
        return BattleState(
            player=pokemon,
            enemy=state.enemy,
            weather=state.weather,
            turn=state.turn,
            player_bench=state.player_bench,
            enemy_bench=state.enemy_bench,
        )
    return BattleState(
        player=state.player,
        enemy=pokemon,
        weather=state.weather,
        turn=state.turn,
        player_bench=state.player_bench,
        enemy_bench=state.enemy_bench,
    )


def replace_side_and_bench(
    state: BattleState,
    side: str,
    pokemon: PokemonState,
    bench: tuple[PokemonState, ...],
) -> BattleState:
    if side == "player":
        return BattleState(
            player=pokemon,
            enemy=state.enemy,
            weather=state.weather,
            turn=state.turn,
            player_bench=bench,
            enemy_bench=state.enemy_bench,
        )
    return BattleState(
        player=state.player,
        enemy=pokemon,
        weather=state.weather,
        turn=state.turn,
        player_bench=state.player_bench,
        enemy_bench=bench,
    )


def advance_turn(state: BattleState) -> BattleState:
    return BattleState(
        player=state.player,
        enemy=state.enemy,
        weather=state.weather,
        turn=state.turn + 1,
        player_bench=state.player_bench,
        enemy_bench=state.enemy_bench,
    )


def battle_is_over(state: BattleState) -> bool:
    return not side_has_living(state, "player") or not side_has_living(state, "enemy")


def side_has_living(state: BattleState, side: str) -> bool:
    active = get_side(state, side)
    return active.hp > 0 or any(mon.hp > 0 for mon in get_bench(state, side))


def forced_switch_prompt_sides(state: BattleState) -> list[str]:
    sides = []
    for side in ("player", "enemy"):
        if get_side(state, side).hp <= 0 and any(mon.hp > 0 for mon in get_bench(state, side)):
            sides.append(side)
    return sides


def is_forced_switch_plan(forced_sides: list[str], actions: dict[str, ActionState]) -> bool:
    forced = set(forced_sides)
    for side in ("player", "enemy"):
        action = actions[side]
        if side in forced:
            if action.kind != "switch":
                return False
        elif action.kind != "wait":
            return False
    return True


def battle_over_reason(state: BattleState) -> str:
    player_living = side_has_living(state, "player")
    enemy_living = side_has_living(state, "enemy")
    if not player_living and not enemy_living:
        return "both_sides_fainted"
    if not player_living:
        return "player_fainted"
    if not enemy_living:
        return "enemy_fainted"
    return "not_over"


def append_battle_over_once(branch: dict[str, Any]) -> dict[str, Any]:
    stopped = clone_branch(branch)
    if stopped["events"] and stopped["events"][-1].get("type") == "battle_over":
        return stopped
    stopped["events"].append(
        {
            "turn": stopped["state"].turn,
            "type": "battle_over",
            "reason": battle_over_reason(stopped["state"]),
        }
    )
    return stopped


def replace_hp(pokemon: PokemonState, hp: int) -> PokemonState:
    return PokemonState(
        side=pokemon.side,
        name=pokemon.name,
        level=pokemon.level,
        hp=max(0, hp),
        max_hp=pokemon.max_hp,
        types=pokemon.types,
        type_names=pokemon.type_names,
        attack=pokemon.attack,
        defense=pokemon.defense,
        speed=pokemon.speed,
        sp_attack=pokemon.sp_attack,
        sp_defense=pokemon.sp_defense,
        item=pokemon.item,
        status=pokemon.status,
        sleep_turns=pokemon.sleep_turns,
        toxic_count=pokemon.toxic_count,
        can_evolve=pokemon.can_evolve,
        accuracy_level=pokemon.accuracy_level,
        evasion_level=pokemon.evasion_level,
        protect=pokemon.protect,
        x_accuracy=pokemon.x_accuracy,
        lock_on=pokemon.lock_on,
        flying=pokemon.flying,
        underground=pokemon.underground,
        focus_energy=pokemon.focus_energy,
        flinched=pokemon.flinched,
        moves=pokemon.moves,
    )


def replace_hp_and_toxic_count(pokemon: PokemonState, hp: int, toxic_count: int) -> PokemonState:
    return PokemonState(
        side=pokemon.side,
        name=pokemon.name,
        level=pokemon.level,
        hp=max(0, hp),
        max_hp=pokemon.max_hp,
        types=pokemon.types,
        type_names=pokemon.type_names,
        attack=pokemon.attack,
        defense=pokemon.defense,
        speed=pokemon.speed,
        sp_attack=pokemon.sp_attack,
        sp_defense=pokemon.sp_defense,
        item=pokemon.item,
        status=pokemon.status,
        sleep_turns=pokemon.sleep_turns,
        toxic_count=toxic_count,
        can_evolve=pokemon.can_evolve,
        accuracy_level=pokemon.accuracy_level,
        evasion_level=pokemon.evasion_level,
        protect=pokemon.protect,
        x_accuracy=pokemon.x_accuracy,
        lock_on=pokemon.lock_on,
        flying=pokemon.flying,
        underground=pokemon.underground,
        focus_energy=pokemon.focus_energy,
        flinched=pokemon.flinched,
        moves=pokemon.moves,
    )


def replace_status(pokemon: PokemonState, status: str, sleep_turns: int = 0) -> PokemonState:
    return PokemonState(
        side=pokemon.side,
        name=pokemon.name,
        level=pokemon.level,
        hp=pokemon.hp,
        max_hp=pokemon.max_hp,
        types=pokemon.types,
        type_names=pokemon.type_names,
        attack=pokemon.attack,
        defense=pokemon.defense,
        speed=pokemon.speed,
        sp_attack=pokemon.sp_attack,
        sp_defense=pokemon.sp_defense,
        item=pokemon.item,
        status=status,
        sleep_turns=sleep_turns,
        toxic_count=pokemon.toxic_count,
        can_evolve=pokemon.can_evolve,
        accuracy_level=pokemon.accuracy_level,
        evasion_level=pokemon.evasion_level,
        protect=pokemon.protect,
        x_accuracy=pokemon.x_accuracy,
        lock_on=pokemon.lock_on,
        flying=pokemon.flying,
        underground=pokemon.underground,
        focus_energy=pokemon.focus_energy,
        flinched=pokemon.flinched,
        moves=pokemon.moves,
    )


def replace_volatile(
    pokemon: PokemonState,
    *,
    protect: bool | None = None,
    x_accuracy: bool | None = None,
    lock_on: bool | None = None,
    flying: bool | None = None,
    underground: bool | None = None,
    focus_energy: bool | None = None,
    flinched: bool | None = None,
) -> PokemonState:
    return PokemonState(
        side=pokemon.side,
        name=pokemon.name,
        level=pokemon.level,
        hp=pokemon.hp,
        max_hp=pokemon.max_hp,
        types=pokemon.types,
        type_names=pokemon.type_names,
        attack=pokemon.attack,
        defense=pokemon.defense,
        speed=pokemon.speed,
        sp_attack=pokemon.sp_attack,
        sp_defense=pokemon.sp_defense,
        item=pokemon.item,
        status=pokemon.status,
        sleep_turns=pokemon.sleep_turns,
        toxic_count=pokemon.toxic_count,
        can_evolve=pokemon.can_evolve,
        accuracy_level=pokemon.accuracy_level,
        evasion_level=pokemon.evasion_level,
        protect=pokemon.protect if protect is None else protect,
        x_accuracy=pokemon.x_accuracy if x_accuracy is None else x_accuracy,
        lock_on=pokemon.lock_on if lock_on is None else lock_on,
        flying=pokemon.flying if flying is None else flying,
        underground=pokemon.underground if underground is None else underground,
        focus_energy=pokemon.focus_energy if focus_energy is None else focus_energy,
        flinched=pokemon.flinched if flinched is None else flinched,
        moves=pokemon.moves,
    )


def selected_move(pokemon: PokemonState, action: ActionState, path: str) -> MoveState:
    if action.kind != "move" or action.move_index is None:
        raise SimulationInputError(f"{path}.type must resolve to move")
    if action.move_index >= len(pokemon.moves):
        raise SimulationInputError(f"{path}.move index {action.move_index} out of range")
    return pokemon.moves[action.move_index]


def clone_branch(branch: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": branch["state"],
        "events": copy.deepcopy(branch["events"]),
        "rng_trace": copy.deepcopy(branch["rng_trace"]),
        "turn_order": list(branch["turn_order"]),
        "turns": copy.deepcopy(branch["turns"]),
        "branch_path": copy.deepcopy(branch["branch_path"]),
    }


def branch_to_outcome(branch: dict[str, Any], index: int) -> dict[str, Any]:
    turn_order = branch["turn_order"] if len(branch["turns"]) == 1 else None
    forced_sides = forced_switch_prompt_sides(branch["state"])
    rng_weight = rng_weight_from_trace(branch["rng_trace"])
    return {
        "outcome_id": str(index),
        "turn_order": turn_order,
        "last_turn_order": branch["turn_order"],
        "turns": branch["turns"],
        "branch_path": branch["branch_path"],
        "rng_trace": branch["rng_trace"],
        "rng_weight": rng_weight,
        "events": branch["events"],
        "state": state_to_json(branch["state"]),
        "battle_over": battle_is_over(branch["state"]),
        "battle_over_reason": battle_over_reason(branch["state"]),
        "requires_forced_switch": bool(forced_sides),
        "forced_switch_sides": forced_sides,
    }


def rng_weight_from_trace(trace: list[dict[str, Any]]) -> dict[str, Any] | None:
    numerator = 1
    denominator = 1
    has_exhaustive_choice = False
    for item in trace:
        if "raw_count" not in item:
            continue
        has_exhaustive_choice = True
        numerator *= int(item["raw_count"])
        denominator *= int(item.get("domain_count", 256))
    if not has_exhaustive_choice:
        return None
    divisor = math.gcd(numerator, denominator)
    return {
        "numerator": numerator,
        "denominator": denominator,
        "probability": numerator / denominator,
        "reduced": [numerator // divisor, denominator // divisor],
    }


def summarize_outcomes(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    weight_basis = "rng_weight" if any(outcome.get("rng_weight") for outcome in outcomes) else "outcome_count"
    weights = [outcome_weight(outcome) for outcome in outcomes]
    total_weight = sum(weights)
    return {
        "weight_basis": weight_basis,
        "total_weight": total_weight,
        "event_type_rates": event_type_rates(outcomes, weights, total_weight),
        "turn_order_rates": turn_order_rates(outcomes, weights, total_weight),
        "boss_ai_selector_rates": boss_ai_selector_rates(outcomes, weights, total_weight),
        "boss_ai_switch_policy_rates": boss_ai_switch_policy_rates(outcomes, weights, total_weight),
        "requires_forced_switch_rate": rate_from_weight(
            sum(weight for outcome, weight in zip(outcomes, weights) if outcome["requires_forced_switch"]),
            total_weight,
        ),
        "battle_over_rate": rate_from_weight(
            sum(weight for outcome, weight in zip(outcomes, weights) if outcome["battle_over"]),
            total_weight,
        ),
    }


def outcome_weight(outcome: dict[str, Any]) -> float:
    weight = outcome.get("rng_weight")
    if isinstance(weight, dict):
        return float(weight["probability"])
    return 1.0


def event_type_rates(
    outcomes: list[dict[str, Any]],
    weights: list[float],
    total_weight: float,
) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for outcome, weight in zip(outcomes, weights):
        for event_type in {str(event["type"]) for event in outcome["events"]}:
            bucket = buckets.setdefault(event_type, {"outcome_count": 0, "weight": 0.0, "rate": 0.0})
            bucket["outcome_count"] += 1
            bucket["weight"] += weight
    for bucket in buckets.values():
        bucket["rate"] = rate_from_weight(float(bucket["weight"]), total_weight)
    return dict(sorted(buckets.items()))


def turn_order_rates(
    outcomes: list[dict[str, Any]],
    weights: list[float],
    total_weight: float,
) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for outcome, weight in zip(outcomes, weights):
        order = outcome.get("turn_order") or outcome.get("last_turn_order") or []
        key = ",".join(order) if order else "none"
        bucket = buckets.setdefault(key, {"outcome_count": 0, "weight": 0.0, "rate": 0.0})
        bucket["outcome_count"] += 1
        bucket["weight"] += weight
    for bucket in buckets.values():
        bucket["rate"] = rate_from_weight(float(bucket["weight"]), total_weight)
    return dict(sorted(buckets.items()))


def boss_ai_selector_rates(
    outcomes: list[dict[str, Any]],
    weights: list[float],
    total_weight: float,
) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for outcome, weight in zip(outcomes, weights):
        seen = set()
        for event in outcome["events"]:
            if event["type"] != "boss_ai_select_move":
                continue
            key = f"{event['actor']}:{event['move_index']}:{event['move']}"
            if key in seen:
                continue
            seen.add(key)
            bucket = buckets.setdefault(key, {"outcome_count": 0, "weight": 0.0, "rate": 0.0})
            bucket["outcome_count"] += 1
            bucket["weight"] += weight
    for bucket in buckets.values():
        bucket["rate"] = rate_from_weight(float(bucket["weight"]), total_weight)
    return dict(sorted(buckets.items()))


def boss_ai_switch_policy_rates(
    outcomes: list[dict[str, Any]],
    weights: list[float],
    total_weight: float,
) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for outcome, weight in zip(outcomes, weights):
        seen = set()
        for event in outcome["events"]:
            if event["type"] != "boss_ai_switch_policy":
                continue
            key = f"{event['actor']}:{event['decision']}:{event['candidate']}"
            if key in seen:
                continue
            seen.add(key)
            bucket = buckets.setdefault(key, {"outcome_count": 0, "weight": 0.0, "rate": 0.0})
            bucket["outcome_count"] += 1
            bucket["weight"] += weight
    for bucket in buckets.values():
        bucket["rate"] = rate_from_weight(float(bucket["weight"]), total_weight)
    return dict(sorted(buckets.items()))


def rate_from_weight(weight: float, total_weight: float) -> float:
    if total_weight == 0:
        return 0.0
    return weight / total_weight


def with_turn(items: list[dict[str, Any]], turn: int) -> list[dict[str, Any]]:
    stamped = []
    for item in items:
        next_item = dict(item)
        next_item.setdefault("turn", turn)
        stamped.append(next_item)
    return stamped


def action_summary(state: BattleState, actions: dict[str, ActionState]) -> dict[str, Any]:
    return {
        "player": describe_action(state, "player", actions["player"]),
        "enemy": describe_action(state, "enemy", actions["enemy"]),
    }


def describe_action(state: BattleState, side: str, action: ActionState) -> dict[str, Any]:
    if action.kind == "move":
        move = selected_move(get_side(state, side), action, f"actions.{side}")
        return {
            "type": "move",
            "move_index": action.move_index,
            "move": move.name,
        }
    if action.kind == "wait":
        return {
            "type": "wait",
        }
    if action.bench_index is None:
        raise SimulationInputError(f"actions.{side}.bench is required for switch actions")
    bench = get_bench(state, side)
    if action.bench_index >= len(bench):
        raise SimulationInputError(f"actions.{side}.bench index {action.bench_index} out of range")
    return {
        "type": "switch",
        "bench_index": action.bench_index,
        "target": bench[action.bench_index].name,
    }


def state_to_json(state: BattleState) -> dict[str, Any]:
    player = pokemon_to_json(state.player)
    enemy = pokemon_to_json(state.enemy)
    if state.player_bench:
        player["bench"] = [pokemon_to_json(mon) for mon in state.player_bench]
    if state.enemy_bench:
        enemy["bench"] = [pokemon_to_json(mon) for mon in state.enemy_bench]
    return {
        "turn": state.turn,
        "weather": state.weather,
        "player": player,
        "enemy": enemy,
    }


def pokemon_to_json(pokemon: PokemonState) -> dict[str, Any]:
    return {
        "side": pokemon.side,
        "name": pokemon.name,
        "level": pokemon.level,
        "hp": pokemon.hp,
        "max_hp": pokemon.max_hp,
        "types": list(pokemon.type_names),
        "item": pokemon.item,
        "status": pokemon.status,
        "sleep_turns": pokemon.sleep_turns,
        "toxic_count": pokemon.toxic_count,
        "can_evolve": pokemon.can_evolve,
        "stats": {
            "attack": pokemon.attack,
            "defense": pokemon.defense,
            "speed": pokemon.speed,
            "sp_attack": pokemon.sp_attack,
            "sp_defense": pokemon.sp_defense,
        },
        "stages": {
            "accuracy": pokemon.accuracy_level - NEUTRAL_STAT_LEVEL,
            "evasion": pokemon.evasion_level - NEUTRAL_STAT_LEVEL,
        },
        "volatile": {
            "protect": pokemon.protect,
            "x_accuracy": pokemon.x_accuracy,
            "lock_on": pokemon.lock_on,
            "flying": pokemon.flying,
            "underground": pokemon.underground,
            "focus_energy": pokemon.focus_energy,
            "flinched": pokemon.flinched,
        },
        "moves": [move_to_json(move) for move in pokemon.moves],
    }


def move_to_json(move: MoveState) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": move.name,
        "type": move.move_type_name,
        "bp": move.bp,
        "priority": move.priority,
        "accuracy": move.accuracy,
        "effect": move.effect,
        "contact": move.contact,
    }
    if move.move_id is not None:
        data["move_id"] = move.move_id
    return data


def rng_to_json(rng: RngConfig) -> dict[str, Any]:
    data: dict[str, Any] = {"mode": rng.mode}
    if rng.values:
        data["values"] = list(rng.values)
    if rng.seed is not None:
        data["seed"] = rng.seed
    if rng.mode == "sample":
        data["samples"] = rng.samples
    if rng.mode == "exhaustive":
        data["exhaustive_kind"] = "distinct_outcome_classes"
    return data


def coverage_report() -> dict[str, Any]:
    return {
        "byte_proven": [
            {
                "id": "damage_core_pre_variation",
                "source": "tools.damage_debugger.oracle.predict_damage",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit runs clobber_smoke against the ROM damage chain; broader oracle fuzz remains python -m tools.damage_debugger.fuzz --self-check-workers=2.",
            },
            {
                "id": "damage_variation",
                "source": "engine/battle/effect_commands.asm:BattleCommand_DamageVariation",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit injects deterministic link-battle RNG bytes into wLinkBattleRNs and compares ROM wCurDamage plus consumed RNG count against the Python simulator.",
            },
            {
                "id": "critical_hit_chance",
                "source": "engine/battle/effect_commands.asm:BattleCommand_Critical",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit injects deterministic link-battle RNG bytes and compares ROM wCriticalHit plus consumed RNG count against the Python simulator for base odds, high-critical moves, Focus Energy, Scope Lens, Lucky Punch, Stick, capped critical level, and zero-power no-RNG behavior.",
            },
            {
                "id": "turn_order_priority_speed_default_role",
                "source": "engine/battle/core.asm:DetermineMoveOrder",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit compares ROM carry-flag order and consumed RNG count against the Python simulator for no-held-item non-link priority/speed cases and default-role speed ties.",
            },
            {
                "id": "turn_order_quick_claw_choice_scarf_default_role",
                "source": "engine/battle/core.asm:DetermineMoveOrder",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit compares ROM carry-flag order and consumed RNG count against the Python simulator for Choice Scarf speed, one-sided Quick Claw activation/fallback, and both-Quick-Claw default-role roll order.",
            },
            {
                "id": "supported_damage_move_accuracy_modifiers_overrides_semivulnerable_weather_and_sure_hit",
                "source": "engine/battle/effect_commands.asm:BattleCommand_CheckHit",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit compares ROM wAttackMissed and consumed RNG count against the Python simulator for supported damaging moves, including accuracy/evasion stages, BrightPowder, X Accuracy, Lock-On, semi-invulnerable flying/underground targets, Thunder-in-rain, source-table sure-hit effects, and the ROM's minimum 1/256 hit chance.",
            },
            {
                "id": "after_hit_rocky_shell_life_orb",
                "source": "engine/battle/late_gen_held_items.asm:HandleLateGenAfterHitEffects_Far",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit compares ROM user/target HP after Rocky Helmet, Shell Bell, and Life Orb after-hit item effects against the Python simulator.",
            },
            {
                "id": "post_variation_double_flying_underground_damage",
                "source": "engine/battle/effect_commands.asm:BattleCommand_DoubleFlyingDamage and BattleCommand_DoubleUndergroundDamage",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit compares ROM wCurDamage after the post-variation double-damage commands used by Gust and Earthquake against the Python simulator, including the ROM's $ffff cap.",
            },
            {
                "id": "residual_status_hp_mutation",
                "source": "engine/battle/core.asm:ResidualDamage.check_toxic and SubtractHP",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit enters the post-text residual path and compares ROM HP/toxic counter mutation against the Python simulator for poison, burn, badly poisoned, minimum-chip, and fainting cases. The full ResidualDamage entry still includes text/animation handling outside this headless proof.",
            },
            {
                "id": "leftovers_hp_mutation",
                "source": "engine/battle/core.asm:HandleLeftovers.do_it",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit calls the ROM Leftovers handler for player and enemy sides and compares active HP mutation against the Python simulator for heal, full-HP no-op, no-item no-op, and minimum-heal cases. The handler reaches text/animation code after mutation, so the proof only claims HP mutation.",
            },
            {
                "id": "paralysis_checkturn_text_path",
                "source": "engine/battle/effect_commands.asm:BattleCommand_CheckTurn and engine/battle/type_passive_damage_mods.asm:TypePassive_GetUserParalysisFailThreshold_Far",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit injects deterministic link-battle RNG, hooks StdBattleTextbox, and compares the ROM FullyParalyzedText path plus consumed RNG count against the Python simulator across baseline, half-Fighting, full-Fighting, player, and enemy cases.",
            },
            {
                "id": "status_speed_recalculation",
                "source": "engine/battle/type_passive_damage_mods.asm:ApplyPrzEffectOnSpeed_Far",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit calls ApplyPrzEffectOnSpeed_Far and compares the ROM speed stat mutation against the Python simulator for normal, Electric passive, baseline paralysis, Fighting-passive paralysis, and combined Electric/Fighting cases.",
            },
            {
                "id": "sleep_checkturn_text_path",
                "source": "engine/battle/effect_commands.asm:BattleCommand_CheckTurn",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit hooks StdBattleTextbox/FarPlayBattleAnimation and compares ROM FastAsleep/WokeUp paths plus sleep status-byte decrement against the Python simulator for player/enemy fast-asleep and wake-up cases.",
            },
            {
                "id": "freeze_checkturn_text_path",
                "source": "engine/battle/effect_commands.asm:BattleCommand_CheckTurn",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit hooks StdBattleTextbox and compares the ROM FrozenSolidText path plus Flame Wheel / Sacred Fire CheckTurn bypass return path against the Python simulator for player/enemy cases. Move-script defrost status clearing remains a separate unimplemented command surface.",
            },
            {
                "id": "flinch_checkturn_text_path",
                "source": "engine/battle/effect_commands.asm:BattleCommand_CheckTurn",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit hooks StdBattleTextbox and compares the ROM FlinchedText path plus one-turn flinch substatus clearing against the Python simulator for player/enemy cases.",
            }
        ],
        "source_mirrored_pending_differential": [
            {
                "id": "selected_turn_sequence",
                "source": "engine/battle/core.asm:BattleTurn",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Supported damaging moves mirror the source move-script order for implemented critical/damage/check-hit surfaces: critical-hit chance, damage variation, and supported post-variation damage effects run before BattleCommand_CheckHit, then HP is applied only on hit. Full script interpretation is still out of scope.",
            },
            {
                "id": "selected_switch_actions",
                "source": "engine/battle/core.asm:BattleTurn selected switch ordering",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
            },
            {
                "id": "explicit_forced_switch_phases",
                "source": "engine/battle/core.asm post-KO send-out flow",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
            },
            {
                "id": "boss_ai_selector_from_post_score_bytes",
                "source": "tools.boss_ai_debugger.rom_scenarios.select_from_score_bytes",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The headless audit directly calls ROM BossAI_SelectMove.first_pass for deterministic no-roll selector edges. Stochastic best-vs-second selector branches are source-mirrored through the existing selector oracle until seeded selector RNG has a direct differential.",
            },
            {
                "id": "boss_ai_switch_policy_from_final_confidence",
                "source": "engine/battle/ai/boss_policy_switch.asm:BossAI_SwitchOrTryItem final confidence threshold and switch roll",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The simulator mirrors the final switch threshold and roll once a candidate and confidence are supplied: tier/class threshold, anti-loop/sack/wincon threshold deltas, and the ROM's 90/75/55 percent switch-roll bands. It does not yet generate the switch candidate or confidence from live battle state.",
            },
            {
                "id": "protect_blocks_before_accuracy",
                "source": "engine/battle/effect_commands.asm:BattleCommand_CheckHit.Protect",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The simulator mirrors Protect's position before Lock-On and accuracy. The direct ROM proof is pending because the isolated Protect path enters text/delay handling under call_function_safe.",
            },
            {
                "id": "residual_status_turn_timing",
                "source": "engine/battle/core.asm:Battle_PlayerFirst and Battle_EnemyFirst",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The simulator applies poison, burn, and toxic residual damage after each selected non-forced action phase when neither active Pokemon has already fainted. Leech Seed, Nightmare, Curse, weather, wrap, perish song, and other between-turn effects remain separate out-of-scope surfaces.",
            },
            {
                "id": "leftovers_between_turn_timing",
                "source": "engine/battle/core.asm:HandleBetweenTurnEffects and HandleLeftovers",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The simulator applies Leftovers after selected actions and residual status effects when no forced switch prompt is pending. Other between-turn effects still need separate implementation and proof.",
            },
            {
                "id": "paralysis_turn_blocking_timing",
                "source": "engine/battle/effect_commands.asm:DoPlayerTurn and DoEnemyTurn",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The simulator applies the supported paralysis CheckTurn block before move execution. Status infliction and other CheckTurn blockers such as confusion, infatuation, disabled moves, and recharge remain separate surfaces.",
            },
            {
                "id": "turn_order_status_adjusted_speed_inputs",
                "source": "engine/battle/core.asm:DetermineMoveOrder and engine/battle/type_passive_damage_mods.asm:ApplyPrzEffectOnSpeed_Far",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The simulator feeds status-adjusted speed into the existing selected-turn order mirror before Choice Scarf, matching the ROM split where ApplyPrzEffectOnSpeed_Far mutates active speed before DetermineMoveOrder reads it. The speed mutator and base turn-order routine are byte-proven separately.",
            },
            {
                "id": "sleep_turn_counter_timing",
                "source": "engine/battle/effect_commands.asm:BattleCommand_CheckTurn",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The simulator decrements sleep before supported move execution, blocks while still asleep, and clears status when the counter reaches zero. Sleep Talk/Snore bypass behavior is source-mirrored only; sleep infliction and Sleep Clause slot bookkeeping remain out of scope.",
            },
            {
                "id": "freeze_turn_blocking_timing",
                "source": "engine/battle/effect_commands.asm:BattleCommand_CheckTurn",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The simulator applies the supported frozen-solid CheckTurn block after sleep and before flinch/paralysis. Flame Wheel / Sacred Fire CheckTurn bypass is modeled, but their later defrost move-script command is not yet implemented.",
            },
            {
                "id": "flinch_turn_blocking_timing",
                "source": "engine/battle/effect_commands.asm:BattleCommand_CheckTurn",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "The simulator applies the one-turn flinch CheckTurn block after sleep/freeze and before paralysis, and clears the flinch flag when it blocks.",
            },
        ],
        "out_of_scope": [
            "automatic volatile-state lifetimes and source move damage-effect commands beyond normal, always-hit, Thunder, Gust, and Earthquake HP mutation",
            "status infliction, freeze infliction, defrost move-script status clearing, Sleep Clause slot bookkeeping, and volatile state beyond supported poison/burn/toxic residual HP mutation plus paralysis/sleep/freeze/flinch move blocking",
            "held-item turn-order effects beyond Quick Claw and Choice Scarf",
            "held-item after-hit/between-turn effects beyond Rocky Helmet, Shell Bell, Life Orb, and Leftovers",
            "automatic forced-switch selection, shift/set prompts, trapping/Pursuit/phazing switch effects, items used as actions, flee/forfeit, and trainer item turns",
            "Boss AI score-model generation from live battle state and Boss AI switch candidate/confidence generation",
            "multi-hit, substitute, counter/mirror coat, trapping, charge/recharge, and forced moves",
            "full battle start/end scripts, EXP, text boxes, animations, and party writes",
        ],
    }


def format_text(report: dict[str, Any]) -> str:
    lines = [
        f"Headless battle simulation: turns={report['turn_count']} outcomes={report['outcome_count']} rng={report['rng']['mode']}",
        "Coverage:",
    ]
    for row in report["coverage"]["byte_proven"]:
        lines.append(f"  byte-proven: {row['id']} via {row['gate']}")
    for row in report["coverage"]["source_mirrored_pending_differential"]:
        lines.append(f"  source-mirrored: {row['id']} via {row['source']}")
    summary = report.get("summary", {})
    if summary:
        lines.append("")
        lines.append(f"Summary: weight_basis={summary['weight_basis']}")
        event_rates = summary.get("event_type_rates", {})
        if event_rates:
            lines.append(
                "  event rates: "
                + ", ".join(f"{name}={row['rate']:.6g}" for name, row in event_rates.items())
            )
        selector_rates = summary.get("boss_ai_selector_rates", {})
        if selector_rates:
            lines.append(
                "  selector rates: "
                + ", ".join(f"{name}={row['rate']:.6g}" for name, row in selector_rates.items())
            )
        switch_policy_rates = summary.get("boss_ai_switch_policy_rates", {})
        if switch_policy_rates:
            lines.append(
                "  switch-policy rates: "
                + ", ".join(f"{name}={row['rate']:.6g}" for name, row in switch_policy_rates.items())
            )
        if summary.get("requires_forced_switch_rate"):
            lines.append(f"  forced-switch-required={summary['requires_forced_switch_rate']:.6g}")
    lines.append("")
    for outcome in report["outcomes"]:
        player = outcome["state"]["player"]
        enemy = outcome["state"]["enemy"]
        if outcome["turn_order"] is None:
            order_text = "per-turn"
        else:
            order_text = ",".join(outcome["turn_order"])
        weight_text = format_rng_weight(outcome.get("rng_weight"))
        lines.append(
            f"Outcome {outcome['outcome_id']}: order={order_text}{weight_text} "
            f"player_hp={player['hp']}/{player['max_hp']} enemy_hp={enemy['hp']}/{enemy['max_hp']}"
        )
        if outcome["turn_order"] is None:
            for turn in outcome["turns"]:
                lines.append(f"  turn {turn['turn']} order={','.join(turn['turn_order'])}")
        for event in outcome["events"]:
            if event["type"] == "damage":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} {event['move']} -> {event['target']} "
                    f"{event['damage']} damage ({event['target_hp_before']}->{event['target_hp_after']})"
                )
            elif event["type"] == "miss":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} {event['move']} -> {event['target']} missed"
                )
            elif event["type"] == "switch":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} switched "
                    f"{event['from']} -> {event['to']}"
                )
            elif event["type"] == "boss_ai_switch_policy":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} switch-policy "
                    f"confidence={event['confidence']} threshold={event['threshold']} "
                    f"decision={event['decision']} target={event['candidate']}"
                )
            elif event["type"] == "residual_status_damage":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} {event['status']} residual "
                    f"{event['damage']} damage ({event['hp_before']}->{event['hp_after']})"
                )
            elif event["type"] == "between_turn_heal":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} {event['item']} "
                    f"healed {event['healed']} ({event['hp_before']}->{event['hp_after']})"
                )
            elif event["type"] == "turn_blocked":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} could not move: {event['reason']}"
                )
            else:
                actor = f"{event.get('actor')} " if event.get("actor") else ""
                lines.append(f"  turn {event.get('turn')} {actor}{event['type']}: {event.get('reason', '')}")
    return "\n".join(lines)


def format_rng_weight(weight: dict[str, Any] | None) -> str:
    if not weight:
        return ""
    reduced = weight["reduced"]
    return f" p={weight['probability']:.6g} ({reduced[0]}/{reduced[1]})"


def load_payload(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SimulationInputError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SimulationInputError("scenario file must contain a JSON object")
    return data


def run_self_test() -> None:
    payload = {
        "rng": {"mode": "fixed", "values": [255, 255]},
        "state": {
            "player": {
                "name": "PIDGEY",
                "level": 2,
                "hp": 16,
                "max_hp": 16,
                "types": ["NORMAL", "FLYING"],
                "stats": {"attack": 6, "defense": 7, "speed": 10, "sp_attack": 6, "sp_defense": 7},
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
            },
            "enemy": {
                "name": "CYNDAQUIL",
                "level": 5,
                "hp": 18,
                "max_hp": 18,
                "types": ["FIRE"],
                "stats": {"attack": 10, "defense": 9, "speed": 9, "sp_attack": 11, "sp_defense": 10},
                "moves": [{"name": "LEER", "type": "NORMAL", "bp": 0}],
            },
        },
        "actions": {"player": {"move": 0}, "enemy": {"move": 0}},
    }
    fixed = simulate_payload(payload)
    if fixed["outcome_count"] != 1:
        raise AssertionError(f"expected one fixed outcome, got {fixed['outcome_count']}")
    event = fixed["outcomes"][0]["events"][0]
    if event["pre_variation_damage"] != 4 or event["damage"] != 4:
        raise AssertionError(f"expected max-roll 4 damage from oracle-backed Tackle, got {event}")
    exhaustive_payload = copy.deepcopy(payload)
    exhaustive_payload["rng"] = {"mode": "exhaustive"}
    exhaustive = simulate_payload(exhaustive_payload)
    damages = sorted({outcome["events"][0]["damage"] for outcome in exhaustive["outcomes"]})
    if exhaustive["outcome_count"] != 78 or damages != [3, 4, 5, 6]:
        raise AssertionError(
            f"expected 78 critical-plus-damage-variation branches with damage 3/4/5/6, got "
            f"{exhaustive['outcome_count']} branches and {damages}"
        )
    if not fixed["coverage"]["byte_proven"] or not fixed["coverage"]["out_of_scope"]:
        raise AssertionError("expected proof coverage labels in report")
    two_turn_payload = copy.deepcopy(payload)
    two_turn_payload["rng"] = {"mode": "fixed", "values": [255, 255, 255, 255]}
    two_turn_payload["turns"] = [
        {"actions": {"player": {"move": 0}, "enemy": {"move": 0}}},
        {"actions": {"player": {"move": 0}, "enemy": {"move": 0}}},
    ]
    two_turn_payload.pop("actions")
    two_turn = simulate_payload(two_turn_payload)
    if two_turn["turn_count"] != 2 or two_turn["outcomes"][0]["state"]["enemy"]["hp"] != 10:
        raise AssertionError(f"expected two selected turns to reduce enemy HP to 10, got {two_turn}")
    switch_payload = copy.deepcopy(payload)
    switch_payload["state"]["player"]["bench"] = [
        {
            "name": "RATTATA",
            "level": 5,
            "hp": 20,
            "max_hp": 20,
            "types": ["NORMAL"],
            "stats": {"attack": 11, "defense": 9, "speed": 12, "sp_attack": 8, "sp_defense": 8},
            "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40, "accuracy": 255}],
        }
    ]
    switch_payload["state"]["enemy"]["moves"][0] = {"name": "TACKLE", "type": "NORMAL", "bp": 40, "accuracy": 255}
    switch_payload["actions"] = {"player": {"type": "switch", "bench": 0}, "enemy": {"type": "move", "move": 0}}
    switch_result = simulate_payload(switch_payload)
    switch_events = switch_result["outcomes"][0]["events"]
    if [event["type"] for event in switch_events] != ["switch", "damage"]:
        raise AssertionError(f"expected selected switch before enemy damage, got {switch_result}")
    switch_policy_payload = copy.deepcopy(payload)
    switch_policy_payload["state"]["player"]["moves"][0]["bp"] = 0
    switch_policy_payload["state"]["enemy"]["bench"] = [
        {
            "name": "TOTODILE",
            "level": 5,
            "hp": 21,
            "max_hp": 21,
            "types": ["WATER"],
            "stats": {"attack": 12, "defense": 11, "speed": 9, "sp_attack": 9, "sp_defense": 10},
            "moves": [{"name": "SCRATCH", "type": "NORMAL", "bp": 40, "accuracy": 255}],
        }
    ]
    switch_policy_payload["rng"] = {"mode": "fixed", "values": [229]}
    switch_policy_payload["actions"] = {
        "player": {"type": "move", "move": 0},
        "enemy": {
            "type": "boss_ai_switch_policy",
            "candidate_bench": 0,
            "confidence": 80,
            "tier": "late",
            "fallback_move": 0,
        },
    }
    switch_policy_result = simulate_payload(switch_policy_payload)
    switch_policy_event = switch_policy_result["outcomes"][0]["events"][0]
    if switch_policy_event["decision"] != "switch":
        raise AssertionError(f"expected final switch-policy roll to switch, got {switch_policy_result}")
    forced_payload = copy.deepcopy(payload)
    forced_payload["state"]["enemy"]["hp"] = 4
    forced_payload["state"]["enemy"]["bench"] = [
        {
            "name": "TOTODILE",
            "level": 5,
            "hp": 21,
            "max_hp": 21,
            "types": ["WATER"],
            "stats": {"attack": 12, "defense": 11, "speed": 9, "sp_attack": 9, "sp_defense": 10},
            "moves": [{"name": "SCRATCH", "type": "NORMAL", "bp": 40, "accuracy": 255}],
        }
    ]
    forced_payload["rng"] = {"mode": "fixed", "values": [255, 255]}
    forced_payload["turns"] = [
        {"actions": {"player": {"move": 0}, "enemy": {"move": 0}}},
        {"actions": {"player": {"type": "wait"}, "enemy": {"type": "switch", "bench": 0}}},
    ]
    forced_payload.pop("actions")
    forced_result = simulate_payload(forced_payload)
    if forced_result["outcomes"][0]["state"]["enemy"]["name"] != "TOTODILE":
        raise AssertionError(f"expected explicit forced switch phase to send in TOTODILE, got {forced_result}")
    selector_payload = copy.deepcopy(payload)
    selector_payload["state"]["enemy"]["moves"] = [
        {"name": "TACKLE", "move_id": 33, "type": "NORMAL", "bp": 40, "accuracy": 255},
        {"name": "EMBER", "move_id": 52, "type": "FIRE", "bp": 40, "accuracy": 255},
    ]
    selector_payload["rng"] = {"mode": "fixed", "values": [255, 255, 255, 255, 255]}
    selector_payload["actions"] = {
        "player": {"type": "move", "move": 0},
        "enemy": {
            "type": "boss_ai_selector",
            "scenario_id": "self_test_selector",
            "tier": "late",
            "move_ids": [33, 52, 0, 0],
            "scores": [20, 20, 80, 80],
        },
    }
    selector_result = simulate_payload(selector_payload)
    selector_event = selector_result["outcomes"][0]["events"][0]
    if selector_event["type"] != "boss_ai_select_move" or selector_event["selected_slot_index"] != 1:
        raise AssertionError(f"expected fixed selector RNG to choose second slot, got {selector_result}")
    residual_payload = copy.deepcopy(payload)
    residual_payload["state"]["player"]["status"] = "toxic"
    residual_payload["state"]["player"]["toxic_count"] = 2
    residual_result = simulate_payload(residual_payload)
    residual_events = residual_result["outcomes"][0]["events"]
    residual_event = next(
        event for event in residual_events if event["type"] == "residual_status_damage"
    )
    if residual_event["damage"] != 3 or residual_event["toxic_count_after"] != 3:
        raise AssertionError(f"expected toxic residual to advance count and deal 3, got {residual_result}")
    leftovers_payload = copy.deepcopy(payload)
    leftovers_payload["state"]["player"]["hp"] = 8
    leftovers_payload["state"]["player"]["item"] = "LEFTOVERS"
    leftovers_result = simulate_payload(leftovers_payload)
    leftovers_event = next(
        event for event in leftovers_result["outcomes"][0]["events"]
        if event["type"] == "between_turn_heal"
    )
    if leftovers_event["healed"] != 1:
        raise AssertionError(f"expected Leftovers to heal 1, got {leftovers_result}")
    paralysis_payload = copy.deepcopy(payload)
    paralysis_payload["state"]["player"]["status"] = "paralysis"
    paralysis_payload["rng"] = {"mode": "fixed", "values": [0]}
    paralysis_result = simulate_payload(paralysis_payload)
    if paralysis_result["outcomes"][0]["events"][0]["type"] != "turn_blocked":
        raise AssertionError(f"expected paralysis to block the move, got {paralysis_result}")
    sleep_payload = copy.deepcopy(payload)
    sleep_payload["state"]["player"]["status"] = "sleep"
    sleep_payload["state"]["player"]["sleep_turns"] = 2
    sleep_result = simulate_payload(sleep_payload)
    if sleep_result["outcomes"][0]["state"]["player"]["sleep_turns"] != 1:
        raise AssertionError(f"expected sleep to decrement to 1, got {sleep_result}")
    freeze_payload = copy.deepcopy(payload)
    freeze_payload["state"]["player"]["status"] = "freeze"
    freeze_result = simulate_payload(freeze_payload)
    if freeze_result["outcomes"][0]["events"][0].get("reason") != "frozen_solid":
        raise AssertionError(f"expected freeze to block the move, got {freeze_result}")
    flinch_payload = copy.deepcopy(payload)
    flinch_payload["state"]["player"]["volatile"] = {"flinched": True}
    flinch_result = simulate_payload(flinch_payload)
    if flinch_result["outcomes"][0]["state"]["player"]["volatile"]["flinched"]:
        raise AssertionError(f"expected flinch to clear after blocking, got {flinch_result}")


def scenario_template() -> dict[str, Any]:
    return {
        "rng": {"mode": "fixed", "values": [255, 255]},
        "state": {
            "weather": "none",
            "turn": 1,
            "player": {
                "name": "PIDGEY",
                "level": 2,
                "hp": 16,
                "max_hp": 16,
                "types": ["NORMAL", "FLYING"],
                "stats": {"attack": 6, "defense": 7, "speed": 10, "sp_attack": 6, "sp_defense": 7},
                "stages": {"accuracy": 0, "evasion": 0},
                "volatile": {
                    "protect": False,
                    "x_accuracy": False,
                    "lock_on": False,
                    "flying": False,
                    "underground": False,
                    "focus_energy": False,
                    "flinched": False,
                },
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40, "accuracy": 255}],
            },
            "enemy": {
                "name": "CYNDAQUIL",
                "level": 5,
                "hp": 18,
                "max_hp": 18,
                "types": ["FIRE"],
                "stats": {"attack": 10, "defense": 9, "speed": 9, "sp_attack": 11, "sp_defense": 10},
                "stages": {"accuracy": 0, "evasion": 0},
                "volatile": {
                    "protect": False,
                    "x_accuracy": False,
                    "lock_on": False,
                    "flying": False,
                    "underground": False,
                    "focus_energy": False,
                    "flinched": False,
                },
                "moves": [{"name": "LEER", "type": "NORMAL", "bp": 0, "accuracy": 255}],
            },
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def iter_compact_outcomes(report: dict[str, Any], limit: int) -> Iterable[dict[str, Any]]:
    for outcome in report["outcomes"][:limit]:
        yield outcome
