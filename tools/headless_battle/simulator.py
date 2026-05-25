from __future__ import annotations

import copy
import json
import random
import re
from dataclasses import dataclass, replace as dataclass_replace
from pathlib import Path
from typing import Any, Literal

from tools.boss_ai_debugger import rom_scenarios
from tools.boss_ai_preference.data import PreferenceDataError
from tools.damage_debugger import oracle
from tools.damage_debugger import tables


REPORT_KIND = "headless_battle_turn_simulation"
SCHEMA_VERSION = 1
RngMode = Literal["fixed", "sample", "exhaustive"]
TURN_ORDER_AFFECTING_ITEMS = frozenset(
    tables.resolve_item(name) for name in ("QUICK_CLAW", "CHOICE_SCARF")
)
DAMAGE_VARIATION_MIN_MULTIPLIER = (85 * 255 // 100) + 1
DAMAGE_VARIATION_MAX_MULTIPLIER = 100 * 255 // 100
WILD_RANDOM_MOVE_SLOT_COUNT = 4
PARTY_LENGTH = 6
EFFECTIVE_FACTOR = 10
STAT_STAGE_MIN = -6
STAT_STAGE_MAX = 6
MAX_MODIFIED_BATTLE_STAT = 999
STAT_STAGE_KEYS = ("attack", "defense", "speed", "sp_attack", "sp_defense")
STAT_STAGE_ALIASES = {
    "attack": "attack",
    "atk": "attack",
    "defense": "defense",
    "def": "defense",
    "speed": "speed",
    "spd": "speed",
    "spe": "speed",
    "sp_attack": "sp_attack",
    "special_attack": "sp_attack",
    "spatk": "sp_attack",
    "spa": "sp_attack",
    "s_atk": "sp_attack",
    "sp_defense": "sp_defense",
    "special_defense": "sp_defense",
    "spdef": "sp_defense",
    "spd_def": "sp_defense",
    "s_def": "sp_defense",
}
STAT_STAGE_MULTIPLIERS = {
    -6: (25, 100),
    -5: (28, 100),
    -4: (33, 100),
    -3: (40, 100),
    -2: (50, 100),
    -1: (66, 100),
    0: (1, 1),
    1: (15, 10),
    2: (2, 1),
    3: (25, 10),
    4: (3, 1),
    5: (35, 10),
    6: (4, 1),
}
SELF_STAT_STAGE_EFFECTS = {
    "EFFECT_ATTACK_UP": (("attack", 1),),
    "EFFECT_DEFENSE_UP": (("defense", 1),),
    "EFFECT_SPEED_UP": (("speed", 1),),
    "EFFECT_SP_ATK_UP": (("sp_attack", 1),),
    "EFFECT_SP_DEF_UP": (("sp_defense", 1),),
    "EFFECT_ATTACK_UP_2": (("attack", 2),),
    "EFFECT_DEFENSE_UP_2": (("defense", 2),),
    "EFFECT_SPEED_UP_2": (("speed", 2),),
    "EFFECT_SP_ATK_UP_2": (("sp_attack", 2),),
    "EFFECT_SP_DEF_UP_2": (("sp_defense", 2),),
    "EFFECT_DEFENSE_CURL": (("defense", 1),),
}
OPPONENT_STAT_STAGE_EFFECTS = {
    "EFFECT_ATTACK_DOWN": (("attack", -1),),
    "EFFECT_DEFENSE_DOWN": (("defense", -1),),
    "EFFECT_SPEED_DOWN": (("speed", -1),),
    "EFFECT_SP_ATK_DOWN": (("sp_attack", -1),),
    "EFFECT_SP_DEF_DOWN": (("sp_defense", -1),),
    "EFFECT_ATTACK_DOWN_2": (("attack", -2),),
    "EFFECT_DEFENSE_DOWN_2": (("defense", -2),),
    "EFFECT_SPEED_DOWN_2": (("speed", -2),),
    "EFFECT_SP_ATK_DOWN_2": (("sp_attack", -2),),
    "EFFECT_SP_DEF_DOWN_2": (("sp_defense", -2),),
}
POISON_STATUS_EFFECTS = {
    "EFFECT_POISON": "poison",
    "EFFECT_TOXIC": "toxic",
}
PARALYSIS_STATUS_EFFECTS = {"EFFECT_PARALYZE": "paralyze"}
SELF_HEALING_MOVE_NAMES = frozenset({"RECOVER", "SOFTBOILED", "MILK_DRINK"})
FULL_PARALYSIS_THRESHOLD = 25 * 255 // 100
TYPE_FACTOR_CONSTANTS = {
    "NO_EFFECT": 0,
    "NOT_VERY_EFFECTIVE": 5,
    "EFFECTIVE": 10,
    "MORE_EFFECTIVE": 15,
    "SUPER_EFFECTIVE": 20,
}
CRITICAL_HIT_THRESHOLDS = (256 // 15, 256 // 8, 256 // 4, 256 // 3, 256 // 2, 256 // 2, 256 // 2)
ITEM_LUCKY_PUNCH = tables.resolve_item("LUCKY_PUNCH")
ITEM_STICK = tables.resolve_item("STICK")
ITEM_SCOPE_LENS = tables.resolve_item("SCOPE_LENS")
ITEM_LIFE_ORB = tables.resolve_item("LIFE_ORB")
ITEM_ROCKY_HELMET = tables.resolve_item("ROCKY_HELMET")
ITEM_SHELL_BELL = tables.resolve_item("SHELL_BELL")
ITEM_POTION = tables.resolve_item("POTION")
ITEM_SUPER_POTION = tables.resolve_item("SUPER_POTION")
ITEM_HYPER_POTION = tables.resolve_item("HYPER_POTION")
ITEM_MAX_POTION = tables.resolve_item("MAX_POTION")
ITEM_FULL_RESTORE = tables.resolve_item("FULL_RESTORE")
ITEM_PSNCUREBERRY = tables.resolve_item("PSNCUREBERRY")
ITEM_PRZCUREBERRY = tables.resolve_item("PRZCUREBERRY")
LIFE_ORB_RECOIL_DENOMINATOR = 10
ROCKY_HELMET_DENOMINATOR = 6
SHELL_BELL_DENOMINATOR = 8
ACTIVE_HP_RESTORE_ITEMS = {
    ITEM_POTION: 20,
    ITEM_SUPER_POTION: 50,
    ITEM_HYPER_POTION: 200,
}
FULL_HP_RESTORE_ITEMS = frozenset({ITEM_MAX_POTION, ITEM_FULL_RESTORE})
HIGH_CRIT_MOVES = {
    line.strip().removeprefix("db ").strip()
    for line in (tables.ROOT / "data/moves/critical_hit_moves.asm").read_text(encoding="utf-8").splitlines()
    if line.strip().startswith("db ") and "-1" not in line
}
_MOVE_IDS_BY_NAME: dict[str, int] | None = None
_CONTACT_FLAGS_BY_MOVE_ID: dict[int, bool] | None = None
_TYPE_CHART_BY_NAME: dict[tuple[str, str], int] | None = None


class SimulationInputError(Exception):
    """User-facing scenario error."""


@dataclass(frozen=True)
class MoveState:
    name: str
    effect: str
    move_type: int
    move_type_name: str
    bp: int
    priority: int = 1
    accuracy: int = 255
    pp: int = 0
    contact: bool = False
    move_id: int | None = None


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
    attack_stage: int = 0
    defense_stage: int = 0
    speed_stage: int = 0
    sp_attack_stage: int = 0
    sp_defense_stage: int = 0
    item: int = oracle.HELD_NONE
    can_evolve: bool = False
    focus_energy: bool = False
    status: str = "none"
    toxic_count: int = 0
    moves: tuple[MoveState, ...] = ()


@dataclass(frozen=True)
class BattleState:
    player: PokemonState
    enemy: PokemonState
    player_bench: tuple[PokemonState, ...] = ()
    enemy_bench: tuple[PokemonState, ...] = ()
    weather: int = oracle.WEATHER_NONE
    turn: int = 1


@dataclass(frozen=True)
class ActionState:
    kind: str
    move_index: int | None = None
    switch_index: int | None = None
    item: int | None = None
    selector: dict[str, Any] | None = None
    fallback: ActionState | None = None


@dataclass(frozen=True)
class RngConfig:
    mode: RngMode
    values: tuple[int, ...] = ()
    samples: int = 1
    seed: int | None = None
    speed_tie_default: int = 0
    critical_default: int = 255
    default: int = 255
    accuracy_default: int = 0
    max_outcomes: int = 2048


class RuntimeRng:
    def __init__(self, config: RngConfig, *, generator: random.Random | None = None) -> None:
        self.config = config
        self.generator = generator
        self.offset = 0

    def next_byte(self, *, purpose: str) -> int:
        if self.config.mode == "sample":
            if self.generator is None:
                raise AssertionError("sample RNG requires a generator")
            return self.generator.randrange(256)
        if self.config.values:
            if self.offset >= len(self.config.values):
                raise SimulationInputError(f"rng.values exhausted while resolving {purpose}")
            value = self.config.values[self.offset]
            self.offset += 1
            return value
        if purpose == "speed tie":
            return self.config.speed_tie_default
        if purpose == "critical":
            return self.config.critical_default
        if purpose == "accuracy":
            return self.config.accuracy_default
        return self.config.default


def simulate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    state = parse_state(payload.get("state", {}))
    action_plan = parse_action_plan(payload)
    rng = parse_rng(payload.get("rng", {"mode": "fixed", "values": []}))
    outcomes = simulate_samples(state, action_plan, rng)
    report = {
        "kind": REPORT_KIND,
        "schema_version": SCHEMA_VERSION,
        "turn_count": len(action_plan),
        "outcome_count": len(outcomes),
        "rng": rng_to_json(rng),
        "coverage": coverage_report(),
        "summary": summarize(outcomes),
        "outcomes": outcomes,
    }
    return report


def simulate_samples(
    state: BattleState,
    action_plan: tuple[dict[str, ActionState], ...],
    rng: RngConfig,
) -> list[dict[str, Any]]:
    if rng.mode == "sample":
        generator = random.Random(rng.seed)
        outcomes = []
        for index in range(rng.samples):
            stream = RuntimeRng(rng, generator=generator)
            branches = simulate_battle(state, action_plan, rng, stream=stream)
            if len(branches) != 1:
                raise AssertionError("sample mode should not create exhaustive branches")
            branch = branches[0]
            branch["sample_index"] = index
            outcomes.append(branch_to_outcome(branch, index))
        return outcomes
    stream = None if rng.mode == "exhaustive" else RuntimeRng(rng)
    return [
        branch_to_outcome(branch, index)
        for index, branch in enumerate(simulate_battle(state, action_plan, rng, stream=stream))
    ]


def simulate_battle(
    state: BattleState,
    action_plan: tuple[dict[str, ActionState], ...],
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    branches = [initial_branch(state)]
    for actions in action_plan:
        next_branches: list[dict[str, Any]] = []
        for branch in branches:
            branch_state: BattleState = branch["state"]
            if battle_is_over(branch_state):
                next_branches.append(branch)
                continue
            if branch_state.player.hp <= 0 or branch_state.enemy.hp <= 0:
                next_branches.extend(apply_forced_replacements(branch, actions, rng, stream=stream))
                continue
            next_branches.extend(simulate_turn(branch, actions, rng, stream=stream))
        if len(next_branches) > rng.max_outcomes:
            raise SimulationInputError(
                f"rng.max_outcomes exceeded while branching ({len(next_branches)} > {rng.max_outcomes})"
            )
        branches = next_branches
    return branches


def initial_branch(state: BattleState) -> dict[str, Any]:
    return {
        "state": state,
        "turn_order": [],
        "turn_orders": [],
        "events": [],
        "proof_notes": [],
        "rng_consumed": [],
        "turns_simulated": 0,
    }


def simulate_turn(
    branch: dict[str, Any],
    actions: dict[str, ActionState],
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    branches: list[dict[str, Any]] = []
    for resolved_branch in resolve_pre_turn_actions(branch, actions, rng, stream=stream):
        state: BattleState = resolved_branch["state"]
        resolved_actions: dict[str, ActionState] = resolved_branch["actions"]
        for order_result in turn_order_results(state, resolved_actions, rng, stream=stream):
            working = clone_branch(resolved_branch)
            working["actions"] = resolved_actions
            order = order_result["order"]
            working["turn_order"] = order
            row = {"turn": state.turn, "order": order}
            if order_result["reason"] in {"speed_tie", "modified_speed"}:
                row["turn_order_check"] = order_result
            working["turn_orders"].append(row)
            working["rng_consumed"].extend(order_result["raw_values"])
            branches.append(working)
    if not branches:
        return []
    max_order_len = max(len(item["turn_order"]) for item in branches)
    for order_index in range(max_order_len):
        next_branches: list[dict[str, Any]] = []
        for branch in branches:
            if order_index >= len(branch["turn_order"]):
                next_branches.append(branch)
                continue
            side = branch["turn_order"][order_index]
            branch_state: BattleState = branch["state"]
            if branch_state.player.hp <= 0 or branch_state.enemy.hp <= 0:
                next_branches.append(branch)
                continue
            branch_actions: dict[str, ActionState] = branch["actions"]
            action = branch_actions[side]
            if action.kind == "boss_ai_selector":
                updated = clone_branch(branch)
                updated["events"].append(run_boss_ai_selector(branch_state, side, action))
                next_branches.append(updated)
                continue
            if action.kind == "switch":
                next_branches.append(apply_switch_action(branch, side, action, event_type="switch"))
                continue
            if action.kind == "replace":
                next_branches.append(apply_switch_action(branch, side, action, event_type="replacement"))
                continue
            if action.kind == "item":
                item_branch = apply_item_action(branch, side, action)
                next_branches.append(apply_post_action_residual(item_branch, side))
                continue
            if action.kind == "auto_replace":
                raise SimulationInputError(f"{side} auto_replace action requires a fainted active Pokemon")
            if action.kind != "move":
                updated = clone_branch(branch)
                updated["events"].append(
                    {
                        "turn": branch_state.turn,
                        "actor": side,
                        "type": "unsupported_noop",
                        "reason": f"unsupported action kind {action.kind!r}",
                        "proof_status": "out_of_scope",
                    }
                )
                next_branches.append(updated)
                continue
            moved_branches = apply_move(branch, side, action, rng, stream=stream)
            for moved_branch in moved_branches:
                next_branches.append(apply_post_action_residual(moved_branch, side))
        if len(next_branches) > rng.max_outcomes:
            raise SimulationInputError(
                f"rng.max_outcomes exceeded while branching ({len(next_branches)} > {rng.max_outcomes})"
            )
        branches = next_branches
    completed = []
    for branch in branches:
        updated = clone_branch(branch)
        updated.pop("actions", None)
        updated["turns_simulated"] += 1
        if updated["state"].player.hp > 0 and updated["state"].enemy.hp > 0:
            updated["state"] = advance_turn(updated["state"])
        completed.append(updated)
    return completed


def resolve_pre_turn_actions(
    branch: dict[str, Any],
    actions: dict[str, ActionState],
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    branches: list[tuple[dict[str, Any], dict[str, ActionState]]] = [
        (clone_branch(branch), dict(actions))
    ]
    for side in ("player", "enemy"):
        next_branches: list[tuple[dict[str, Any], dict[str, ActionState]]] = []
        for working, action_map in branches:
            action = action_map[side]
            if action.kind == "auto_replace_or":
                fallback = action.fallback
                if fallback is None:
                    raise AssertionError("auto_replace_or action missing fallback")
                updated_actions = dict(action_map)
                updated_actions[side] = (
                    ActionState(kind="auto_replace")
                    if get_side(working["state"], side).hp <= 0
                    else fallback
                )
                next_branches.append((working, updated_actions))
                continue
            if action.kind == "boss_ai_selector_move":
                selections = boss_ai_selector_move_results(working["state"], side, action, rng, stream=stream)
            elif action.kind == "wild_random_move":
                selections = wild_random_move_results(working["state"], side, rng, stream=stream)
            else:
                next_branches.append((working, action_map))
                continue
            for selection in selections:
                updated = clone_branch(working)
                updated["events"].append(selection["event"])
                updated["rng_consumed"].extend(selection["raw_values"])
                updated_actions = dict(action_map)
                updated_actions[side] = ActionState(kind="move", move_index=selection["move_index"])
                next_branches.append((updated, updated_actions))
        branches = next_branches
        if len(branches) > rng.max_outcomes:
            raise SimulationInputError(
                f"rng.max_outcomes exceeded while resolving pre-turn actions ({len(branches)} > {rng.max_outcomes})"
            )
    resolved = []
    for working, action_map in branches:
        working["actions"] = action_map
        resolved.append(working)
    return resolved


def turn_order_results(
    state: BattleState,
    actions: dict[str, ActionState],
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    player_action = actions["player"]
    enemy_action = actions["enemy"]
    if player_action.kind == "item" and enemy_action.kind == "item":
        raise SimulationInputError("simultaneous explicit item actions are out of scope")
    non_move_first_actions = {"switch", "replace", "item"}
    if player_action.kind in non_move_first_actions or enemy_action.kind in non_move_first_actions:
        if player_action.kind in non_move_first_actions:
            return [turn_order_result(["player", "enemy"], reason=f"selected_{player_action.kind}")]
        return [turn_order_result(["enemy", "player"], reason=f"selected_{enemy_action.kind}")]
    if player_action.kind != "move" or enemy_action.kind != "move":
        return [turn_order_result(["player", "enemy"], reason="non_move_action")]
    player_move = selected_move(state.player, player_action)
    enemy_move = selected_move(state.enemy, enemy_action)
    if player_move.priority != enemy_move.priority:
        order = ["player", "enemy"] if player_move.priority > enemy_move.priority else ["enemy", "player"]
        return [turn_order_result(order, reason="move_priority")]
    for pokemon in (state.player, state.enemy):
        if pokemon.item in TURN_ORDER_AFFECTING_ITEMS:
            raise SimulationInputError(
                f"{pokemon.side} item {tables.display_item(pokemon.item)} modifies turn order and is out of scope"
            )
    player_speed = effective_speed(state.player)
    enemy_speed = effective_speed(state.enemy)
    if player_speed != enemy_speed:
        order = ["player", "enemy"] if player_speed > enemy_speed else ["enemy", "player"]
        result = turn_order_result(order, reason="modified_speed")
        result["effective_speeds"] = {"player": player_speed, "enemy": enemy_speed}
        return [result]
    return speed_tie_results(rng, stream=stream)


def turn_order_result(order: list[str], *, reason: str) -> dict[str, Any]:
    return {
        "order": order,
        "reason": reason,
        "threshold": None,
        "raw_values": [],
        "raw_range": None,
    }


def speed_tie_results(rng: RngConfig, *, stream: RuntimeRng | None) -> list[dict[str, Any]]:
    threshold = 128
    if rng.mode == "exhaustive":
        return [
            {
                "order": ["player", "enemy"],
                "reason": "speed_tie",
                "threshold": threshold,
                "raw_values": [],
                "raw_range": [0, threshold - 1],
            },
            {
                "order": ["enemy", "player"],
                "reason": "speed_tie",
                "threshold": threshold,
                "raw_values": [],
                "raw_range": [threshold, 255],
            },
        ]
    if stream is None:
        raise AssertionError("fixed/sample speed tie requires an RNG stream")
    raw = stream.next_byte(purpose="speed tie")
    order = ["player", "enemy"] if raw < threshold else ["enemy", "player"]
    return [
        {
            "order": order,
            "reason": "speed_tie",
            "threshold": threshold,
            "raw_values": [raw],
            "raw_range": None,
        }
    ]


def effective_speed(pokemon: PokemonState) -> int:
    speed = apply_stat_stage(pokemon.speed, pokemon.speed_stage)
    if pokemon.status == "paralyze":
        speed = apply_paralysis_speed_modifiers(pokemon, speed)
    return speed


def apply_paralysis_speed_modifiers(pokemon: PokemonState, speed: int) -> int:
    electric = type_contribution("ELECTRIC", pokemon.type_names)
    if electric == 2:
        speed = apply_stat_fraction(speed, 21, 20)
    elif electric == 1:
        speed = apply_stat_fraction(speed, 41, 40)

    fighting = type_contribution("FIGHTING", pokemon.type_names)
    if fighting == 2:
        return apply_stat_fraction(speed, 1, 2)
    if fighting == 1:
        return apply_stat_fraction(speed, 3, 8)
    return apply_stat_fraction(speed, 1, 4)


def type_contribution(type_name: str, type_names: tuple[str, str]) -> int:
    if type_names[0] == type_names[1]:
        return 2 if type_names[0] == type_name else 0
    return 1 if type_name in type_names else 0


def full_paralysis_results(
    pokemon: PokemonState,
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]] | None:
    if pokemon.status != "paralyze":
        return None
    threshold = full_paralysis_threshold(pokemon)
    if rng.mode == "exhaustive":
        return [
            {
                "fully_paralyzed": True,
                "threshold": threshold,
                "raw_values": [],
                "raw_range": [0, threshold - 1],
                "reason": "raw_below_threshold",
            },
            {
                "fully_paralyzed": False,
                "threshold": threshold,
                "raw_values": [],
                "raw_range": [threshold, 255],
                "reason": "raw_at_or_above_threshold",
            },
        ]
    if stream is None:
        raise AssertionError("fixed/sample full paralysis requires an RNG stream")
    raw = stream.next_byte(purpose="full paralysis")
    return [
        {
            "fully_paralyzed": raw < threshold,
            "threshold": threshold,
            "raw_values": [raw],
            "raw_range": None,
            "reason": "raw_below_threshold" if raw < threshold else "raw_at_or_above_threshold",
        }
    ]


def full_paralysis_threshold(pokemon: PokemonState) -> int:
    fighting = type_contribution("FIGHTING", pokemon.type_names)
    if fighting == 2:
        return 15 * 255 // 100
    if fighting == 1:
        return 20 * 255 // 100
    return FULL_PARALYSIS_THRESHOLD


def apply_move(
    branch: dict[str, Any],
    side: str,
    action: ActionState,
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    state: BattleState = branch["state"]
    attacker = get_side(state, side)
    move = selected_move(attacker, action)
    if move.pp <= 0:
        raise SimulationInputError(f"{side} move {move.name} has no PP; Struggle is out of scope")
    paralysis_checks = full_paralysis_results(attacker, rng, stream=stream)
    if paralysis_checks is not None:
        branches = []
        for paralysis_check in paralysis_checks:
            updated = clone_branch(branch)
            updated["rng_consumed"].extend(paralysis_check["raw_values"])
            if paralysis_check["fully_paralyzed"]:
                updated["events"].append(
                    {
                        "turn": state.turn,
                        "actor": side,
                        "move": move.name,
                        "type": "fully_paralyzed",
                        "paralysis_check": paralysis_check,
                        "pp_before": move.pp,
                        "pp_after": move.pp,
                        "proof_status": "source_mirrored_baseline_full_paralysis",
                    }
                )
                branches.append(updated)
                continue
            branches.extend(apply_move_after_action_check(updated, side, action, rng, stream=stream))
        return branches

    return apply_move_after_action_check(branch, side, action, rng, stream=stream)


def apply_move_after_action_check(
    branch: dict[str, Any],
    side: str,
    action: ActionState,
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    state: BattleState = branch["state"]
    attacker = get_side(state, side)
    move = selected_move(attacker, action)
    pp_before = move.pp
    branch = consume_move_pp(branch, side, action.move_index)
    state = branch["state"]
    attacker = get_side(state, side)
    move = selected_move(attacker, action)
    pp_after = move.pp
    target_side = "enemy" if side == "player" else "player"
    target = get_side(state, target_side)
    if move.bp <= 0:
        poison_status_branches = apply_poison_status_move(
            branch,
            side,
            target_side,
            move,
            pp_before,
            pp_after,
            rng,
            stream=stream,
        )
        if poison_status_branches is not None:
            return poison_status_branches
        paralysis_status_branches = apply_paralysis_status_move(
            branch,
            side,
            target_side,
            move,
            pp_before,
            pp_after,
            rng,
            stream=stream,
        )
        if paralysis_status_branches is not None:
            return paralysis_status_branches
        self_heal_branch = apply_self_heal_move(branch, side, move, pp_before, pp_after)
        if self_heal_branch is not None:
            return [self_heal_branch]
        stat_stage_branches = apply_stat_stage_only_move(
            branch,
            side,
            move,
            pp_before,
            pp_after,
            rng,
            stream=stream,
        )
        if stat_stage_branches is not None:
            return stat_stage_branches
        updated = clone_branch(branch)
        updated["events"].append(
            {
                "turn": state.turn,
                "actor": side,
                "move": move.name,
                "type": "unsupported_noop",
                "reason": "bp=0 move effect is out of scope for this simulator slice",
                "pp_before": pp_before,
                "pp_after": pp_after,
                "proof_status": "out_of_scope",
            }
        )
        return [updated]
    branches = []
    for critical_check in critical_results(attacker, move, rng, stream=stream):
        pre_variation_damage = predict_pre_variation_damage(
            state,
            attacker,
            target,
            move,
            is_critical=critical_check["critical"],
        )
        for variation in damage_variation_results(pre_variation_damage, rng, stream=stream):
            for hit_check in accuracy_results(state, move, rng, stream=stream):
                if not hit_check["hit"]:
                    updated = clone_branch(branch)
                    updated["rng_consumed"].extend(critical_check["raw_values"])
                    updated["rng_consumed"].extend(variation["raw_values"])
                    updated["rng_consumed"].extend(hit_check["raw_values"])
                    updated["events"].append(
                        {
                            "turn": state.turn,
                            "actor": side,
                            "target": target_side,
                            "move": move.name,
                            "type": "miss",
                            "critical_check": critical_check,
                            "pre_variation_damage": pre_variation_damage,
                            "damage_variation": {
                                "applied": variation["applied"],
                                "multiplier": variation["multiplier"],
                                "raw_values": variation["raw_values"],
                            },
                            "accuracy_check": hit_check,
                            "pp_before": pp_before,
                            "pp_after": pp_after,
                            "proof_status": "source_mirrored_basic_critical_variation_accuracy",
                        }
                    )
                    branches.append(updated)
                    continue
                damage = variation["damage"]
                hp_after = max(0, target.hp - damage)
                updated_target = replace_hp(target, hp_after)
                updated_state = replace_side(state, target_side, updated_target)
                updated = clone_branch(branch)
                updated["state"] = updated_state
                updated["rng_consumed"].extend(critical_check["raw_values"])
                updated["rng_consumed"].extend(variation["raw_values"])
                updated["rng_consumed"].extend(hit_check["raw_values"])
                updated["events"].append(
                    {
                        "turn": state.turn,
                        "actor": side,
                        "target": target_side,
                        "move": move.name,
                        "type": "damage",
                        "damage": damage,
                        "pre_variation_damage": pre_variation_damage,
                        "target_hp_before": target.hp,
                        "target_hp_after": hp_after,
                        "critical_check": critical_check,
                        "accuracy_check": hit_check,
                        "pp_before": pp_before,
                        "pp_after": pp_after,
                        "damage_variation": {
                            "applied": variation["applied"],
                            "multiplier": variation["multiplier"],
                            "raw_values": variation["raw_values"],
                        },
                        "proof_status": "delegated_pre_variation_damage_plus_source_mirrored_critical_variation_accuracy",
                    }
                )
                updated = apply_after_hit_effects(
                    updated,
                    side,
                    target_side,
                    move,
                    damage,
                )
                branches.append(updated)
    return branches


def apply_poison_status_move(
    branch: dict[str, Any],
    side: str,
    target_side: str,
    move: MoveState,
    pp_before: int,
    pp_after: int,
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]] | None:
    status = POISON_STATUS_EFFECTS.get(move.effect)
    if status is None:
        return None
    out = []
    for hit_check in accuracy_results(branch["state"], move, rng, stream=stream):
        if not hit_check["hit"]:
            updated = clone_branch(branch)
            updated["rng_consumed"].extend(hit_check["raw_values"])
            updated["events"].append(
                {
                    "turn": branch["state"].turn,
                    "actor": side,
                    "target": target_side,
                    "move": move.name,
                    "type": "miss",
                    "accuracy_check": hit_check,
                    "pp_before": pp_before,
                    "pp_after": pp_after,
                    "proof_status": "source_mirrored_poison_status_move_accuracy",
                }
            )
            out.append(updated)
            continue
        out.append(
            apply_poison_status_change(
                branch,
                side,
                target_side,
                move,
                status,
                hit_check,
                pp_before,
                pp_after,
            )
        )
    return out


def apply_poison_status_change(
    branch: dict[str, Any],
    side: str,
    target_side: str,
    move: MoveState,
    status: str,
    hit_check: dict[str, Any],
    pp_before: int,
    pp_after: int,
) -> dict[str, Any]:
    state: BattleState = branch["state"]
    target = get_side(state, target_side)
    blocked_reason = poison_status_blocked_reason(target, move)
    updated = clone_branch(branch)
    updated["rng_consumed"].extend(hit_check["raw_values"])
    if blocked_reason is None:
        updated_target = replace_hp(target, target.hp, status=status, toxic_count=0)
        updated["state"] = replace_side(state, target_side, updated_target)
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": side,
            "target": target_side,
            "move": move.name,
            "type": "status_apply" if blocked_reason is None else "status_no_effect",
            "status": status,
            "status_before": target.status,
            "status_after": status if blocked_reason is None else target.status,
            "toxic_count_before": target.toxic_count,
            "toxic_count_after": 0 if blocked_reason is None else target.toxic_count,
            "blocked_reason": blocked_reason,
            "accuracy_check": hit_check,
            "pp_before": pp_before,
            "pp_after": pp_after,
            "proof_status": (
                "source_mirrored_selected_poison_status_move"
                if blocked_reason is None
                else (
                    "out_of_scope"
                    if blocked_reason == "held_status_healing_item_out_of_scope"
                    else "source_mirrored_selected_poison_status_no_effect"
                )
            ),
        }
    )
    return updated


def poison_status_blocked_reason(target: PokemonState, move: MoveState) -> str | None:
    if type_effectiveness_factor(move.move_type_name, target.type_names) == 0:
        return "type_immunity"
    if "POISON" in target.type_names:
        return "poison_type"
    if target.status in {"poison", "toxic"}:
        return "already_poisoned"
    if target.status != "none":
        return "already_statused"
    if target.item == ITEM_PSNCUREBERRY:
        return "held_status_healing_item_out_of_scope"
    return None


def apply_paralysis_status_move(
    branch: dict[str, Any],
    side: str,
    target_side: str,
    move: MoveState,
    pp_before: int,
    pp_after: int,
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]] | None:
    status = PARALYSIS_STATUS_EFFECTS.get(move.effect)
    if status is None:
        return None
    out = []
    for hit_check in accuracy_results(branch["state"], move, rng, stream=stream):
        if not hit_check["hit"]:
            updated = clone_branch(branch)
            updated["rng_consumed"].extend(hit_check["raw_values"])
            updated["events"].append(
                {
                    "turn": branch["state"].turn,
                    "actor": side,
                    "target": target_side,
                    "move": move.name,
                    "type": "miss",
                    "accuracy_check": hit_check,
                    "pp_before": pp_before,
                    "pp_after": pp_after,
                    "proof_status": "source_mirrored_paralysis_status_move_accuracy",
                }
            )
            out.append(updated)
            continue
        out.append(
            apply_paralysis_status_change(
                branch,
                side,
                target_side,
                move,
                status,
                hit_check,
                pp_before,
                pp_after,
            )
        )
    return out


def apply_paralysis_status_change(
    branch: dict[str, Any],
    side: str,
    target_side: str,
    move: MoveState,
    status: str,
    hit_check: dict[str, Any],
    pp_before: int,
    pp_after: int,
) -> dict[str, Any]:
    state: BattleState = branch["state"]
    target = get_side(state, target_side)
    blocked_reason = paralysis_status_blocked_reason(target, move)
    updated = clone_branch(branch)
    updated["rng_consumed"].extend(hit_check["raw_values"])
    if blocked_reason is None:
        updated_target = replace_hp(target, target.hp, status=status)
        updated["state"] = replace_side(state, target_side, updated_target)
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": side,
            "target": target_side,
            "move": move.name,
            "type": "status_apply" if blocked_reason is None else "status_no_effect",
            "status": status,
            "status_before": target.status,
            "status_after": status if blocked_reason is None else target.status,
            "blocked_reason": blocked_reason,
            "accuracy_check": hit_check,
            "pp_before": pp_before,
            "pp_after": pp_after,
            "proof_status": (
                "source_mirrored_selected_paralysis_status_move"
                if blocked_reason is None
                else (
                    "out_of_scope"
                    if blocked_reason == "held_status_healing_item_out_of_scope"
                    else "source_mirrored_selected_paralysis_status_no_effect"
                )
            ),
        }
    )
    return updated


def paralysis_status_blocked_reason(target: PokemonState, move: MoveState) -> str | None:
    if type_effectiveness_factor(move.move_type_name, target.type_names) == 0:
        return "type_immunity"
    if target.status == "paralyze":
        return "already_paralyzed"
    if target.status != "none":
        return "already_statused"
    if target.item == ITEM_PRZCUREBERRY:
        return "held_status_healing_item_out_of_scope"
    return None


def apply_self_heal_move(
    branch: dict[str, Any],
    side: str,
    move: MoveState,
    pp_before: int,
    pp_after: int,
) -> dict[str, Any] | None:
    if move.effect != "EFFECT_HEAL" or move.name not in SELF_HEALING_MOVE_NAMES:
        return None
    state: BattleState = branch["state"]
    actor = get_side(state, side)
    raw_heal = fraction_max_hp(actor.max_hp, 2)
    hp_after = min(actor.max_hp, actor.hp + raw_heal)
    actual_heal = hp_after - actor.hp
    updated = clone_branch(branch)
    if actual_heal > 0:
        updated["state"] = replace_side(state, side, replace_hp(actor, hp_after))
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": side,
            "target": side,
            "move": move.name,
            "type": "self_heal" if actual_heal > 0 else "self_heal_no_effect",
            "raw_heal": raw_heal,
            "heal": actual_heal,
            "hp_before": actor.hp,
            "hp_after": hp_after,
            "blocked_reason": None if actual_heal > 0 else "hp_full",
            "pp_before": pp_before,
            "pp_after": pp_after,
            "proof_status": "source_mirrored_selected_self_heal_move",
        }
    )
    return updated


def apply_stat_stage_only_move(
    branch: dict[str, Any],
    side: str,
    move: MoveState,
    pp_before: int,
    pp_after: int,
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]] | None:
    effect = stat_stage_only_effect(move)
    if effect is None:
        return None
    target_side = side if effect["target"] == "self" else ("enemy" if side == "player" else "player")
    checks = (
        accuracy_results(branch["state"], move, rng, stream=stream)
        if effect["target"] == "opponent"
        else [{"hit": True, "threshold": None, "raw_values": [], "raw_range": None, "reason": "self_stat_move"}]
    )
    out = []
    for hit_check in checks:
        if not hit_check["hit"]:
            updated = clone_branch(branch)
            updated["rng_consumed"].extend(hit_check["raw_values"])
            updated["events"].append(
                {
                    "turn": branch["state"].turn,
                    "actor": side,
                    "target": target_side,
                    "move": move.name,
                    "type": "miss",
                    "accuracy_check": hit_check,
                    "pp_before": pp_before,
                    "pp_after": pp_after,
                    "proof_status": "source_mirrored_stat_stage_move_accuracy",
                }
            )
            out.append(updated)
            continue
        out.append(
            apply_stat_stage_changes(
                branch,
                side,
                target_side,
                move,
                effect["changes"],
                hit_check,
                pp_before,
                pp_after,
            )
        )
    return out


def stat_stage_only_effect(move: MoveState) -> dict[str, Any] | None:
    if move.effect in SELF_STAT_STAGE_EFFECTS:
        return {"target": "self", "changes": SELF_STAT_STAGE_EFFECTS[move.effect]}
    if move.effect in OPPONENT_STAT_STAGE_EFFECTS:
        return {"target": "opponent", "changes": OPPONENT_STAT_STAGE_EFFECTS[move.effect]}
    return None


def apply_stat_stage_changes(
    branch: dict[str, Any],
    side: str,
    target_side: str,
    move: MoveState,
    changes: tuple[tuple[str, int], ...],
    hit_check: dict[str, Any],
    pp_before: int,
    pp_after: int,
) -> dict[str, Any]:
    state: BattleState = branch["state"]
    target = get_side(state, target_side)
    updated_target = target
    applied = []
    blocked = []
    for stat, delta in changes:
        before = stat_stage(updated_target, stat)
        after = max(STAT_STAGE_MIN, min(STAT_STAGE_MAX, before + delta))
        row = {
            "stat": stat,
            "stage_before": before,
            "stage_after": after,
            "delta_requested": delta,
            "delta_applied": after - before,
        }
        if after == before:
            blocked.append(row)
        else:
            applied.append(row)
            updated_target = replace_stat_stage(updated_target, stat, after)
    updated = clone_branch(branch)
    if applied:
        updated["state"] = replace_side(state, target_side, updated_target)
    event_type = "stat_stage_change" if applied else "stat_stage_no_effect"
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": side,
            "target": target_side,
            "move": move.name,
            "type": event_type,
            "changes": applied,
            "blocked_changes": blocked,
            "accuracy_check": hit_check,
            "pp_before": pp_before,
            "pp_after": pp_after,
            "proof_status": "source_mirrored_selected_stat_stage_only_move",
        }
    )
    return updated


def apply_after_hit_effects(
    branch: dict[str, Any],
    side: str,
    target_side: str,
    move: MoveState,
    damage: int,
) -> dict[str, Any]:
    if damage <= 0:
        return branch
    updated = clone_branch(branch)
    updated = apply_rocky_helmet(updated, side, target_side, move)
    if get_side(updated["state"], side).hp <= 0:
        return updated
    updated = apply_shell_bell(updated, side, damage)
    if get_side(updated["state"], side).hp <= 0:
        return updated
    return apply_life_orb_recoil(updated, side)


def apply_rocky_helmet(
    branch: dict[str, Any],
    side: str,
    target_side: str,
    move: MoveState,
) -> dict[str, Any]:
    state: BattleState = branch["state"]
    target = get_side(state, target_side)
    if target.item != ITEM_ROCKY_HELMET or not move.contact:
        return branch
    actor = get_side(state, side)
    damage = fraction_max_hp(actor.max_hp, ROCKY_HELMET_DENOMINATOR)
    hp_after = max(0, actor.hp - damage)
    updated = clone_branch(branch)
    updated["state"] = replace_side(state, side, replace_hp(actor, hp_after))
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": side,
            "target": side,
            "type": "after_hit_recoil",
            "source_item": "ROCKY_HELMET",
            "holder": target_side,
            "damage": damage,
            "hp_before": actor.hp,
            "hp_after": hp_after,
            "proof_status": "byte_smoke_supported_after_hit_item_effect",
        }
    )
    return updated


def apply_shell_bell(branch: dict[str, Any], side: str, damage_done: int) -> dict[str, Any]:
    state: BattleState = branch["state"]
    actor = get_side(state, side)
    if actor.item != ITEM_SHELL_BELL or actor.hp <= 0:
        return branch
    heal = max(1, damage_done // SHELL_BELL_DENOMINATOR)
    hp_after = min(actor.max_hp, actor.hp + heal)
    actual_heal = hp_after - actor.hp
    updated = clone_branch(branch)
    updated["state"] = replace_side(state, side, replace_hp(actor, hp_after))
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": side,
            "target": side,
            "type": "after_hit_heal",
            "source_item": "SHELL_BELL",
            "heal": actual_heal,
            "raw_heal": heal,
            "hp_before": actor.hp,
            "hp_after": hp_after,
            "proof_status": "byte_smoke_supported_after_hit_item_effect",
        }
    )
    return updated


def apply_life_orb_recoil(branch: dict[str, Any], side: str) -> dict[str, Any]:
    state: BattleState = branch["state"]
    actor = get_side(state, side)
    if actor.item != ITEM_LIFE_ORB or actor.hp <= 0:
        return branch
    damage = fraction_max_hp(actor.max_hp, LIFE_ORB_RECOIL_DENOMINATOR)
    hp_after = max(0, actor.hp - damage)
    updated = clone_branch(branch)
    updated["state"] = replace_side(state, side, replace_hp(actor, hp_after))
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": side,
            "target": side,
            "type": "after_hit_recoil",
            "source_item": "LIFE_ORB",
            "holder": side,
            "damage": damage,
            "hp_before": actor.hp,
            "hp_after": hp_after,
            "proof_status": "byte_smoke_supported_after_hit_item_effect",
        }
    )
    return updated


def apply_forced_replacements(
    branch: dict[str, Any],
    actions: dict[str, ActionState],
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    branches = [clone_branch(branch)]
    for side in ("player", "enemy"):
        next_branches: list[dict[str, Any]] = []
        for working in branches:
            active = get_side(working["state"], side)
            if active.hp > 0:
                next_branches.append(working)
                continue
            action = actions[side]
            if action.kind == "replace":
                next_branches.append(apply_switch_action(working, side, action, event_type="replacement"))
            elif action.kind in {"auto_replace", "auto_replace_or"}:
                next_branches.extend(apply_auto_replace_action(working, side, rng, stream=stream))
            else:
                next_branches.append(working)
        branches = next_branches
    completed = []
    for working in branches:
        state_after: BattleState = working["state"]
        if state_after.player.hp > 0 and state_after.enemy.hp > 0:
            working = clone_branch(working)
            working["state"] = advance_turn(state_after)
        completed.append(working)
    return completed


def apply_auto_replace_action(
    branch: dict[str, Any],
    side: str,
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    if side != "enemy":
        raise SimulationInputError("player auto_replace is out of scope; use an explicit replace action")
    state: BattleState = branch["state"]
    active = get_side(state, side)
    if active.hp > 0:
        raise SimulationInputError(f"{side} auto_replace action requires a fainted active Pokemon")
    choices = auto_replacement_choice_results(state, side, rng, stream=stream)
    out = []
    for choice in choices:
        updated = clone_branch(branch)
        updated["events"].append(choice["event"])
        updated["rng_consumed"].extend(choice["raw_values"])
        action = ActionState(kind="replace", switch_index=choice["bench_index"])
        out.append(apply_switch_action(updated, side, action, event_type="replacement"))
    return out


def auto_replacement_choice_results(
    state: BattleState,
    side: str,
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    bench = get_bench(state, side)
    legal = [index for index, pokemon in enumerate(bench) if pokemon.hp > 0 and index < PARTY_LENGTH]
    if not legal:
        raise SimulationInputError(f"{side} auto_replace has no non-fainted bench Pokemon")
    opponent = get_side(state, "player" if side == "enemy" else "enemy")
    evaluations = [
        auto_replacement_candidate_evaluation(index, pokemon, opponent)
        for index, pokemon in enumerate(bench)
        if index < PARTY_LENGTH
    ]
    enemy_pressure = [
        row for row in evaluations
        if row["legal"] and row["candidate_has_super_effective_move"] and not row["opponent_has_super_effective_type"]
    ]
    if enemy_pressure:
        return [
            auto_replacement_choice(
                state,
                side,
                enemy_pressure[0]["bench_index"],
                "candidate_super_effective_move",
                evaluations,
                raw_values=[],
            )
        ]
    acceptable = [
        row for row in evaluations
        if row["legal"] and not row["player_discouraged"]
    ]
    if acceptable:
        return [
            auto_replacement_choice(
                state,
                side,
                acceptable[0]["bench_index"],
                "not_player_discouraged",
                evaluations,
                raw_values=[],
            )
        ]
    return random_auto_replacement_choices(state, side, legal, evaluations, rng, stream=stream)


def auto_replacement_candidate_evaluation(
    bench_index: int,
    candidate: PokemonState,
    opponent: PokemonState,
) -> dict[str, Any]:
    candidate_has_super_effective_move = any(
        type_effectiveness_factor(move.move_type_name, opponent.type_names) > EFFECTIVE_FACTOR
        for move in candidate.moves
        if move.name != "NO_MOVE"
    )
    opponent_has_super_effective_type = any(
        type_effectiveness_factor(type_name, candidate.type_names) > EFFECTIVE_FACTOR
        for type_name in unique_type_names(opponent.type_names)
    )
    player_discouraged = opponent_has_super_effective_type and not candidate_has_super_effective_move
    return {
        "bench_index": bench_index,
        "name": candidate.name,
        "legal": candidate.hp > 0,
        "candidate_has_super_effective_move": candidate_has_super_effective_move,
        "opponent_has_super_effective_type": opponent_has_super_effective_type,
        "player_discouraged": player_discouraged,
    }


def random_auto_replacement_choices(
    state: BattleState,
    side: str,
    legal: list[int],
    evaluations: list[dict[str, Any]],
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    if rng.mode == "exhaustive":
        return [
            auto_replacement_choice(
                state,
                side,
                bench_index,
                "random_fallback",
                evaluations,
                raw_values=[],
                raw_low_bits=bench_index,
            )
            for bench_index in legal
        ]
    if stream is None:
        raise AssertionError("fixed/sample auto replacement choice requires an RNG stream")
    raw_values = []
    while True:
        raw = stream.next_byte(purpose="auto replacement choice")
        raw_values.append(raw)
        bench_index = raw & 7
        if bench_index in legal:
            return [
                auto_replacement_choice(
                    state,
                    side,
                    bench_index,
                    "random_fallback",
                    evaluations,
                    raw_values=raw_values,
                    raw_low_bits=bench_index,
                )
            ]


def auto_replacement_choice(
    state: BattleState,
    side: str,
    bench_index: int,
    reason: str,
    evaluations: list[dict[str, Any]],
    *,
    raw_values: list[int],
    raw_low_bits: int | None = None,
) -> dict[str, Any]:
    incoming = get_bench(state, side)[bench_index]
    event = {
        "turn": state.turn,
        "actor": side,
        "type": "auto_replacement_choice",
        "selected_bench_index": bench_index,
        "selected": incoming.name,
        "reason": reason,
        "candidate_evaluations": evaluations,
        "raw_values": raw_values,
        "raw_low_bits": raw_low_bits,
        "proof_status": "source_mirrored_basic_trainer_replacement_choice",
    }
    return {"bench_index": bench_index, "event": event, "raw_values": raw_values}


def apply_switch_action(
    branch: dict[str, Any],
    side: str,
    action: ActionState,
    *,
    event_type: str,
) -> dict[str, Any]:
    if action.switch_index is None:
        raise SimulationInputError(f"{side} {event_type} action requires bench_index")
    state: BattleState = branch["state"]
    active = get_side(state, side)
    if event_type == "switch" and active.hp <= 0:
        raise SimulationInputError(f"{side} cannot use a selected switch action after fainting; use replace")
    if event_type == "replacement" and active.hp > 0:
        raise SimulationInputError(f"{side} replacement action requires a fainted active Pokemon")
    bench = get_bench(state, side)
    if action.switch_index >= len(bench):
        raise SimulationInputError(f"{side} bench_index out of range")
    incoming = reset_stat_stages(bench[action.switch_index])
    if incoming.hp <= 0:
        raise SimulationInputError(f"{side} cannot switch to fainted bench Pokemon {incoming.name}")
    outgoing = reset_stat_stages(active)
    updated_bench = tuple(
        outgoing if index == action.switch_index else pokemon
        for index, pokemon in enumerate(bench)
    )
    updated_state = replace_side_and_bench(state, side, incoming, updated_bench)
    updated = clone_branch(branch)
    updated["state"] = updated_state
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": side,
            "type": event_type,
            "from": active.name,
            "to": incoming.name,
            "bench_index": action.switch_index,
            "proof_status": (
                "source_mirrored_selected_switch_no_entry_effects"
                if event_type == "switch"
                else "source_mirrored_selected_replacement_no_entry_effects"
            ),
        }
    )
    return updated


def apply_item_action(branch: dict[str, Any], side: str, action: ActionState) -> dict[str, Any]:
    if action.item is None:
        raise SimulationInputError(f"{side} item action requires item")
    item = action.item
    state: BattleState = branch["state"]
    actor = get_side(state, side)
    if actor.hp <= 0:
        raise SimulationInputError(f"{side} cannot use {tables.display_item(item)} on a fainted active Pokemon")
    if item in ACTIVE_HP_RESTORE_ITEMS:
        hp_restore = ACTIVE_HP_RESTORE_ITEMS[item]
        hp_after = min(actor.max_hp, actor.hp + hp_restore)
        status_after = actor.status
        toxic_count_after = actor.toxic_count
    elif item in FULL_HP_RESTORE_ITEMS:
        hp_restore = actor.max_hp
        hp_after = actor.max_hp
        status_after = "none" if item == ITEM_FULL_RESTORE else actor.status
        toxic_count_after = 0 if item == ITEM_FULL_RESTORE else actor.toxic_count
    else:
        supported = ", ".join(
            tables.display_item(supported_item)
            for supported_item in (
                ITEM_POTION,
                ITEM_SUPER_POTION,
                ITEM_HYPER_POTION,
                ITEM_MAX_POTION,
                ITEM_FULL_RESTORE,
            )
        )
        raise SimulationInputError(
            f"{side} item {tables.display_item(item)} is out of scope; supported active HP items: {supported}"
        )
    if hp_after == actor.hp and status_after == actor.status and toxic_count_after == actor.toxic_count:
        raise SimulationInputError(f"{side} item {tables.display_item(item)} has no effect")
    updated_actor = replace_hp(
        actor,
        hp_after,
        status=status_after,
        toxic_count=toxic_count_after,
    )
    updated = clone_branch(branch)
    updated["state"] = replace_side(state, side, updated_actor)
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": side,
            "type": "item_restore",
            "item": tables.display_item(item),
            "item_id": item,
            "hp_restore_amount": hp_restore,
            "hp_before": actor.hp,
            "hp_after": hp_after,
            "heal": hp_after - actor.hp,
            "status_before": actor.status,
            "status_after": status_after,
            "toxic_count_before": actor.toxic_count,
            "toxic_count_after": toxic_count_after,
            "proof_status": "source_mirrored_explicit_active_item_effect_no_inventory",
        }
    )
    return updated


def apply_post_action_residual(branch: dict[str, Any], side: str) -> dict[str, Any]:
    state: BattleState = branch["state"]
    actor = get_side(state, side)
    target = get_side(state, "enemy" if side == "player" else "player")
    if actor.hp <= 0 or target.hp <= 0:
        return branch
    residual = residual_status_damage(actor)
    if residual is None:
        return branch
    damage = residual["damage"]
    hp_after = max(0, actor.hp - damage)
    updated_actor = replace_hp(actor, hp_after, toxic_count=residual["toxic_count_after"])
    updated = clone_branch(branch)
    updated["state"] = replace_side(state, side, updated_actor)
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": side,
            "type": "residual_damage",
            "status": residual["status"],
            "damage": damage,
            "hp_before": actor.hp,
            "hp_after": hp_after,
            "toxic_count_before": residual["toxic_count_before"],
            "toxic_count_after": residual["toxic_count_after"],
            "proof_status": "source_mirrored_basic_status_residual",
        }
    )
    return updated


def battle_is_over(state: BattleState) -> bool:
    return side_is_defeated(state, "player") or side_is_defeated(state, "enemy")


def side_is_defeated(state: BattleState, side: str) -> bool:
    active = get_side(state, side)
    if active.hp > 0:
        return False
    return not any(pokemon.hp > 0 for pokemon in get_bench(state, side))


def residual_status_damage(pokemon: PokemonState) -> dict[str, Any] | None:
    if pokemon.status in {"poison", "burn"}:
        return {
            "status": pokemon.status,
            "damage": fraction_max_hp(pokemon.max_hp, 8),
            "toxic_count_before": pokemon.toxic_count,
            "toxic_count_after": pokemon.toxic_count,
        }
    if pokemon.status == "toxic":
        toxic_count_after = pokemon.toxic_count + 1
        return {
            "status": pokemon.status,
            "damage": fraction_max_hp(pokemon.max_hp, 16) * toxic_count_after,
            "toxic_count_before": pokemon.toxic_count,
            "toxic_count_after": toxic_count_after,
        }
    return None


def fraction_max_hp(max_hp: int, denominator: int) -> int:
    return max(1, max_hp // denominator)


def critical_results(
    attacker: PokemonState,
    move: MoveState,
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    threshold = critical_threshold(attacker, move)
    if rng.mode == "exhaustive":
        out = []
        if threshold > 0:
            out.append(
                {
                    "critical": True,
                    "threshold": threshold,
                    "raw_values": [],
                    "raw_range": [0, threshold - 1],
                    "level": critical_level(attacker, move),
                    "reason": "raw_below_threshold",
                }
            )
        if threshold < 256:
            out.append(
                {
                    "critical": False,
                    "threshold": threshold,
                    "raw_values": [],
                    "raw_range": [threshold, 255],
                    "level": critical_level(attacker, move),
                    "reason": "raw_at_or_above_threshold",
                }
            )
        return out
    if stream is None:
        raise AssertionError("fixed/sample critical hit check requires an RNG stream")
    raw = stream.next_byte(purpose="critical")
    level = critical_level(attacker, move)
    return [
        {
            "critical": raw < threshold,
            "threshold": threshold,
            "raw_values": [raw],
            "raw_range": None,
            "level": level,
            "reason": "raw_below_threshold" if raw < threshold else "raw_at_or_above_threshold",
        }
    ]


def critical_threshold(attacker: PokemonState, move: MoveState) -> int:
    return CRITICAL_HIT_THRESHOLDS[min(critical_level(attacker, move), len(CRITICAL_HIT_THRESHOLDS) - 1)]


def critical_level(attacker: PokemonState, move: MoveState) -> int:
    if attacker.name == "CHANSEY" and attacker.item == ITEM_LUCKY_PUNCH:
        return 2
    elif attacker.name == "FARFETCH_D" and attacker.item == ITEM_STICK:
        return 2
    level = 0
    if attacker.focus_energy:
        level += 1
    if move.name in HIGH_CRIT_MOVES:
        level += 2
    if attacker.item == ITEM_SCOPE_LENS:
        level += 1
    return level


def accuracy_results(
    state: BattleState,
    move: MoveState,
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    threshold = effective_accuracy_threshold(state, move)
    if threshold is None:
        return [
            {
                "hit": True,
                "threshold": None,
                "raw_values": [],
                "raw_range": None,
                "reason": "always_hit",
            }
        ]
    if rng.mode == "exhaustive":
        out = []
        if threshold > 0:
            out.append(
                {
                    "hit": True,
                    "threshold": threshold,
                    "raw_values": [],
                    "raw_range": [0, threshold - 1],
                    "reason": "raw_below_threshold",
                }
            )
        if threshold < 256:
            out.append(
                {
                    "hit": False,
                    "threshold": threshold,
                    "raw_values": [],
                    "raw_range": [threshold, 255],
                    "reason": "raw_at_or_above_threshold",
                }
            )
        return out
    if stream is None:
        raise AssertionError("fixed/sample accuracy requires an RNG stream")
    raw = stream.next_byte(purpose="accuracy")
    return [
        {
            "hit": raw < threshold,
            "threshold": threshold,
            "raw_values": [raw],
            "raw_range": None,
            "reason": "raw_below_threshold" if raw < threshold else "raw_at_or_above_threshold",
        }
    ]


def effective_accuracy_threshold(state: BattleState, move: MoveState) -> int | None:
    if move.effect == "EFFECT_ALWAYS_HIT" or move.accuracy == 255:
        return None
    if move.effect == "EFFECT_THUNDER" and state.weather == oracle.WEATHER_RAIN:
        return None
    return move.accuracy


def damage_variation_results(
    damage: int,
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    if damage < 2:
        return [{"damage": damage, "applied": False, "multiplier": None, "raw_values": []}]
    if rng.mode == "exhaustive":
        return [
            {
                "damage": damage * multiplier // DAMAGE_VARIATION_MAX_MULTIPLIER,
                "applied": True,
                "multiplier": multiplier,
                "raw_values": [rotate_left_byte(multiplier)],
            }
            for multiplier in range(DAMAGE_VARIATION_MIN_MULTIPLIER, DAMAGE_VARIATION_MAX_MULTIPLIER + 1)
        ]
    if stream is None:
        raise AssertionError("fixed/sample damage variation requires an RNG stream")
    raw_values = []
    while True:
        raw = stream.next_byte(purpose="damage variation")
        raw_values.append(raw)
        multiplier = rotate_right_byte(raw)
        if multiplier >= DAMAGE_VARIATION_MIN_MULTIPLIER:
            return [
                {
                    "damage": damage * multiplier // DAMAGE_VARIATION_MAX_MULTIPLIER,
                    "applied": True,
                    "multiplier": multiplier,
                    "raw_values": raw_values,
                }
            ]


def rotate_right_byte(value: int) -> int:
    return ((value >> 1) | ((value & 1) << 7)) & 0xFF


def rotate_left_byte(value: int) -> int:
    return (((value << 1) & 0xFF) | (value >> 7)) & 0xFF


def predict_pre_variation_damage(
    state: BattleState,
    attacker: PokemonState,
    target: PokemonState,
    move: MoveState,
    *,
    is_critical: bool = False,
) -> int:
    is_physical = tables.is_physical_type(move.move_type)
    attacker_stage_key = "attack" if is_physical else "sp_attack"
    target_stage_key = "defense" if is_physical else "sp_defense"
    attacker_base_stat = attacker.attack if is_physical else attacker.sp_attack
    target_base_stat = target.defense if is_physical else target.sp_defense
    attacker_stage = stat_stage(attacker, attacker_stage_key)
    target_stage = stat_stage(target, target_stage_key)
    use_modified_stats = not is_critical or attacker_stage > target_stage
    inputs = oracle.BattleInputs(
        attacker_level=attacker.level,
        move_bp=move.bp,
        move_type=move.move_type,
        is_physical=is_physical,
        attacker_atk=(
            apply_stat_stage(attacker_base_stat, attacker_stage)
            if use_modified_stats
            else attacker_base_stat
        ),
        defender_def=(
            apply_stat_stage(target_base_stat, target_stage)
            if use_modified_stats
            else target_base_stat
        ),
        attacker_types=attacker.types,
        defender_types=target.types,
        user_item=attacker.item,
        opponent_item=target.item,
        can_evolve_attacker=attacker.can_evolve,
        can_evolve_defender=target.can_evolve,
        is_critical=is_critical,
        weather=state.weather,
        battle_turn=0 if attacker.side == "player" else 1,
    )
    return oracle.predict_damage(inputs)


def stat_stage(pokemon: PokemonState, key: str) -> int:
    if key == "attack":
        return pokemon.attack_stage
    if key == "defense":
        return pokemon.defense_stage
    if key == "speed":
        return pokemon.speed_stage
    if key == "sp_attack":
        return pokemon.sp_attack_stage
    if key == "sp_defense":
        return pokemon.sp_defense_stage
    raise AssertionError(f"unknown stat stage key {key!r}")


def stat_stages_to_json(pokemon: PokemonState) -> dict[str, int]:
    return {key: stat_stage(pokemon, key) for key in STAT_STAGE_KEYS}


def apply_stat_stage(value: int, stage: int) -> int:
    numerator, denominator = STAT_STAGE_MULTIPLIERS[stage]
    return max(1, min(MAX_MODIFIED_BATTLE_STAT, value * numerator // denominator))


def apply_stat_fraction(value: int, numerator: int, denominator: int) -> int:
    return max(1, min(MAX_MODIFIED_BATTLE_STAT, value * numerator // denominator))


def run_boss_ai_selector(state: BattleState, side: str, action: ActionState) -> dict[str, Any]:
    result = boss_ai_selector_result(state, side, action)
    return {
        "turn": state.turn,
        "actor": side,
        "type": "boss_ai_select_move",
        "selector": result,
        "proof_status": "source_mirrored_existing_selector_oracle",
    }


def boss_ai_selector_move_results(
    state: BattleState,
    side: str,
    action: ActionState,
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    result = boss_ai_selector_result(state, side, action)
    if not result.get("ready"):
        raise SimulationInputError(f"boss_ai_selector_move has no selectable move: {result.get('reason')}")
    best_index = int(result["best_slot_index"])
    second_index = result.get("second_slot_index")
    threshold = result.get("best_roll_threshold")
    if second_index is None or threshold is None:
        return [
            selector_choice_result(
                state,
                side,
                result,
                best_index,
                {
                    "threshold": None,
                    "raw_values": [],
                    "raw_range": None,
                    "reason": "only_selectable_move",
                },
            )
        ]
    threshold = int(threshold)
    if rng.mode == "exhaustive":
        choices = []
        if threshold > 0:
            choices.append(
                selector_choice_result(
                    state,
                    side,
                    result,
                    best_index,
                    {
                        "threshold": threshold,
                        "raw_values": [],
                        "raw_range": [0, threshold - 1],
                        "reason": "raw_below_threshold_choose_best",
                    },
                )
            )
        if threshold < 256:
            choices.append(
                selector_choice_result(
                    state,
                    side,
                    result,
                    int(second_index),
                    {
                        "threshold": threshold,
                        "raw_values": [],
                        "raw_range": [threshold, 255],
                        "reason": "raw_at_or_above_threshold_choose_second",
                    },
                )
            )
        return choices
    if stream is None:
        raise AssertionError("fixed/sample Boss AI selector requires an RNG stream")
    raw = stream.next_byte(purpose="boss ai selector")
    selected_index = best_index if raw < threshold else int(second_index)
    reason = "raw_below_threshold_choose_best" if raw < threshold else "raw_at_or_above_threshold_choose_second"
    return [
        selector_choice_result(
            state,
            side,
            result,
            selected_index,
            {
                "threshold": threshold,
                "raw_values": [raw],
                "raw_range": None,
                "reason": reason,
            },
        )
    ]


def selector_choice_result(
    state: BattleState,
    side: str,
    selector_result: dict[str, Any],
    selected_slot_index: int,
    selector_check: dict[str, Any],
) -> dict[str, Any]:
    actor = get_side(state, side)
    if selected_slot_index < 0 or selected_slot_index >= len(actor.moves):
        raise SimulationInputError(
            f"boss_ai_selector_move selected slot {selected_slot_index} but {side} has {len(actor.moves)} moves"
        )
    selected_move = actor.moves[selected_slot_index]
    selected_slot = selector_slot(selector_result, selected_slot_index)
    selected_move_id = int(selected_slot["move_id"])
    if selected_move.move_id is not None and selected_move.move_id != selected_move_id:
        raise SimulationInputError(
            "boss_ai_selector_move selected move id "
            f"{selected_move_id} for slot {selected_slot_index}, but state.{side}.moves[{selected_slot_index}] "
            f"is {selected_move.name} ({selected_move.move_id})"
        )
    return {
        "move_index": selected_slot_index,
        "raw_values": selector_check["raw_values"],
        "event": {
            "turn": state.turn,
            "actor": side,
            "type": "boss_ai_select_move",
            "selected_slot_index": selected_slot_index,
            "selected_move_id": selected_move_id,
            "selected_move": selected_move.name,
            "selector": selector_result,
            "selector_check": selector_check,
            "proof_status": "source_mirrored_existing_selector_oracle_executed_move",
        },
    }


def selector_slot(selector_result: dict[str, Any], slot_index: int) -> dict[str, Any]:
    for slot in selector_result.get("slots", []):
        if int(slot.get("slot_index", -1)) == slot_index:
            return slot
    raise SimulationInputError(f"boss_ai_selector_move selected unknown slot {slot_index}")


def boss_ai_selector_result(state: BattleState, side: str, action: ActionState) -> dict[str, Any]:
    assert action.selector is not None
    selector = action.selector
    actor = get_side(state, side)
    move_names = {move.move_id: move.name for move in actor.moves if move.move_id is not None}
    try:
        return rom_scenarios.select_from_score_bytes(
            scenario_id=str(selector.get("scenario_id", "headless_boss_ai_selector")),
            tier=selector.get("tier", "late"),
            move_ids=[int(value) for value in selector["move_ids"]],
            scores=[int(value) for value in selector["scores"]],
            move_names=move_names,
        )
    except (KeyError, PreferenceDataError, ValueError) as exc:
        raise SimulationInputError(f"invalid {action.kind} action: {exc}") from exc


def wild_random_move_results(
    state: BattleState,
    side: str,
    rng: RngConfig,
    *,
    stream: RuntimeRng | None,
) -> list[dict[str, Any]]:
    actor = get_side(state, side)
    legal_slots = wild_random_legal_slots(actor)
    if not legal_slots:
        raise SimulationInputError(f"{side} has no usable random move; Struggle is out of scope")
    if rng.mode == "exhaustive":
        return [
            wild_random_choice_result(
                state,
                side,
                slot,
                {
                    "raw_values": [],
                    "raw_low_bits": [slot],
                    "reason": "exhaustive_legal_slot",
                },
            )
            for slot in legal_slots
        ]
    if stream is None:
        raise AssertionError("fixed/sample wild random move requires an RNG stream")
    raw_values = []
    while True:
        raw = stream.next_byte(purpose="wild random move")
        raw_values.append(raw)
        slot = raw & (WILD_RANDOM_MOVE_SLOT_COUNT - 1)
        if slot in legal_slots:
            return [
                wild_random_choice_result(
                    state,
                    side,
                    slot,
                    {
                        "raw_values": raw_values,
                        "raw_low_bits": [value & (WILD_RANDOM_MOVE_SLOT_COUNT - 1) for value in raw_values],
                        "reason": "first_legal_slot_after_rejections",
                    },
                )
            ]


def wild_random_legal_slots(actor: PokemonState) -> list[int]:
    legal = []
    for slot in range(WILD_RANDOM_MOVE_SLOT_COUNT):
        if slot >= len(actor.moves):
            continue
        move = actor.moves[slot]
        if move.move_id == 0:
            break
        if move.pp <= 0:
            continue
        legal.append(slot)
    return legal


def wild_random_choice_result(
    state: BattleState,
    side: str,
    selected_slot_index: int,
    selector_check: dict[str, Any],
) -> dict[str, Any]:
    actor = get_side(state, side)
    move = actor.moves[selected_slot_index]
    return {
        "move_index": selected_slot_index,
        "raw_values": selector_check["raw_values"],
        "event": {
            "turn": state.turn,
            "actor": side,
            "type": "wild_random_move",
            "selected_slot_index": selected_slot_index,
            "selected_move_id": move.move_id,
            "selected_move": move.name,
            "selector_check": selector_check,
            "proof_status": "source_mirrored_wild_random_move_choice",
        },
    }


def parse_state(raw: Any) -> BattleState:
    if not isinstance(raw, dict):
        raise SimulationInputError("state must be an object")
    player_raw = raw.get("player")
    enemy_raw = raw.get("enemy")
    player = parse_pokemon(player_raw, "player")
    enemy = parse_pokemon(enemy_raw, "enemy")
    return BattleState(
        player=player,
        enemy=enemy,
        player_bench=parse_bench(raw.get("player_bench", side_bench_raw(player_raw)), "player"),
        enemy_bench=parse_bench(raw.get("enemy_bench", side_bench_raw(enemy_raw)), "enemy"),
        weather=parse_weather(raw.get("weather", "none")),
        turn=parse_positive_int(raw.get("turn", 1), "state.turn"),
    )


def side_bench_raw(raw: Any) -> Any:
    if isinstance(raw, dict):
        return raw.get("bench", [])
    return []


def parse_bench(raw: Any, side: str) -> tuple[PokemonState, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise SimulationInputError(f"state.{side}_bench must be a list")
    return tuple(parse_pokemon(item, side) for item in raw)


def parse_pokemon(raw: Any, side: str) -> PokemonState:
    if not isinstance(raw, dict):
        raise SimulationInputError(f"state.{side} must be an object")
    species = source_species_row(raw.get("species"), f"state.{side}.species")
    level = parse_positive_int(raw.get("level", 5), f"state.{side}.level")
    if species is not None:
        type_names, type_ids = parse_type_pair(
            raw.get("types", [species.type_a, species.type_b]),
            f"state.{side}.types",
        )
        iv = parse_non_negative_int(raw.get("iv", tables.TRAINER_IV_STATEEXP[0]), f"state.{side}.iv")
        statexp = parse_non_negative_int(
            raw.get("statexp_term", tables.TRAINER_IV_STATEEXP[1]),
            f"state.{side}.statexp_term",
        )
        max_hp = parse_positive_int(
            raw.get("max_hp", tables.compute_hp(species.hp, level, iv, statexp)),
            f"state.{side}.max_hp",
        )
        defaults = {
            "attack": tables.compute_stat(species.atk, level, iv, statexp, is_hp=False),
            "defense": tables.compute_stat(species.def_, level, iv, statexp, is_hp=False),
            "speed": tables.compute_stat(species.spe, level, iv, statexp, is_hp=False),
            "sp_attack": tables.compute_stat(species.sat, level, iv, statexp, is_hp=False),
            "sp_defense": tables.compute_stat(species.sdf, level, iv, statexp, is_hp=False),
        }
        can_evolve = tables.load_can_evolve().get(species.species, False)
        name = species.species
    else:
        type_names, type_ids = parse_type_pair(raw.get("types", ["NORMAL", "NORMAL"]), f"state.{side}.types")
        max_hp = parse_positive_int(raw.get("max_hp", 20), f"state.{side}.max_hp")
        defaults = {"attack": 10, "defense": 10, "speed": 10, "sp_attack": 10, "sp_defense": 10}
        can_evolve = False
        name = str(raw.get("name", side)).upper()
    stats = raw.get("stats", {})
    if not isinstance(stats, dict):
        raise SimulationInputError(f"state.{side}.stats must be an object")
    hp = parse_non_negative_int(raw.get("hp", max_hp), f"state.{side}.hp")
    if hp > max_hp:
        raise SimulationInputError(f"state.{side}.hp cannot exceed max_hp")
    moves_raw = raw.get("moves", [])
    if not isinstance(moves_raw, list) or not moves_raw:
        raise SimulationInputError(f"state.{side}.moves must be a non-empty list")
    stat_stages = parse_stat_stages(raw.get("stat_stages", raw.get("stages", {})), f"state.{side}.stat_stages")
    return PokemonState(
        side=side,
        name=name,
        level=level,
        hp=hp,
        max_hp=max_hp,
        types=type_ids,
        type_names=type_names,
        attack=parse_positive_int(stats.get("attack", defaults["attack"]), f"state.{side}.stats.attack"),
        defense=parse_positive_int(stats.get("defense", defaults["defense"]), f"state.{side}.stats.defense"),
        speed=parse_positive_int(stats.get("speed", defaults["speed"]), f"state.{side}.stats.speed"),
        sp_attack=parse_positive_int(
            stats.get("sp_attack", stats.get("special_attack", defaults["sp_attack"])),
            f"state.{side}.stats.sp_attack",
        ),
        sp_defense=parse_positive_int(
            stats.get("sp_defense", stats.get("special_defense", defaults["sp_defense"])),
            f"state.{side}.stats.sp_defense",
        ),
        attack_stage=stat_stages["attack"],
        defense_stage=stat_stages["defense"],
        speed_stage=stat_stages["speed"],
        sp_attack_stage=stat_stages["sp_attack"],
        sp_defense_stage=stat_stages["sp_defense"],
        item=parse_item(raw.get("item", 0)),
        can_evolve=bool(raw.get("can_evolve", can_evolve)),
        focus_energy=bool(raw.get("focus_energy", False)),
        status=parse_status(raw.get("status", "none"), f"state.{side}.status"),
        toxic_count=parse_non_negative_int(raw.get("toxic_count", 0), f"state.{side}.toxic_count"),
        moves=tuple(parse_move(move, f"state.{side}.moves[{index}]") for index, move in enumerate(moves_raw)),
    )


def parse_move(raw: Any, path: str) -> MoveState:
    if isinstance(raw, str):
        raw = {"name": raw}
    if not isinstance(raw, dict):
        raise SimulationInputError(f"{path} must be an object or move name")
    name = str(raw.get("name", "TACKLE")).upper()
    row = None
    try:
        row = tables.load_moves()[tables.resolve_move(name)]
    except tables.InputError:
        row = None
    default_move_id = move_id_for_name(row.name) if row is not None else None
    move_id = parse_optional_byte(raw.get("move_id", default_move_id), f"{path}.move_id")
    type_name = raw.get("type", row.type_name if row is not None else "NORMAL")
    move_type_name, move_type = parse_type(type_name, f"{path}.type")
    return MoveState(
        name=name,
        effect=str(raw.get("effect", row.effect if row is not None else "EFFECT_NORMAL_HIT")),
        move_type=move_type,
        move_type_name=move_type_name,
        bp=parse_non_negative_int(raw.get("bp", row.bp if row is not None else 40), f"{path}.bp"),
        priority=parse_int(raw.get("priority", 1), f"{path}.priority"),
        accuracy=parse_accuracy(raw, row, f"{path}.accuracy"),
        pp=parse_byte(raw.get("pp", row.pp if row is not None else 35), f"{path}.pp"),
        contact=parse_bool(raw.get("contact", is_contact_move_id(move_id)), f"{path}.contact"),
        move_id=move_id,
    )


def move_id_for_name(name: str) -> int | None:
    global _MOVE_IDS_BY_NAME
    if _MOVE_IDS_BY_NAME is None:
        _MOVE_IDS_BY_NAME = tables.parse_const_values(tables.ROOT / "constants/move_constants.asm")
    return _MOVE_IDS_BY_NAME.get(name)


def is_contact_move_id(move_id: int | None) -> bool:
    if move_id is None:
        return False
    return contact_flags_by_move_id().get(move_id, False)


def contact_flags_by_move_id() -> dict[int, bool]:
    global _CONTACT_FLAGS_BY_MOVE_ID
    if _CONTACT_FLAGS_BY_MOVE_ID is not None:
        return _CONTACT_FLAGS_BY_MOVE_ID
    flags: dict[int, bool] = {}
    move_id = 1
    for raw in (tables.ROOT / "data/moves/contact_flags.asm").read_text(encoding="utf-8").splitlines():
        code = raw.split(";", 1)[0].strip()
        if code == "db TRUE":
            flags[move_id] = True
            move_id += 1
        elif code == "db FALSE":
            flags[move_id] = False
            move_id += 1
    _CONTACT_FLAGS_BY_MOVE_ID = flags
    return flags


def type_effectiveness_factor(attack_type: str, defender_types: tuple[str, str]) -> int:
    factor = EFFECTIVE_FACTOR
    for defender_type in unique_type_names(defender_types):
        factor = factor * source_type_chart().get((attack_type, defender_type), EFFECTIVE_FACTOR) // EFFECTIVE_FACTOR
    return factor


def unique_type_names(type_names: tuple[str, str]) -> tuple[str, ...]:
    if type_names[0] == type_names[1]:
        return (type_names[0],)
    return type_names


def source_type_chart() -> dict[tuple[str, str], int]:
    global _TYPE_CHART_BY_NAME
    if _TYPE_CHART_BY_NAME is not None:
        return _TYPE_CHART_BY_NAME
    chart: dict[tuple[str, str], int] = {}
    pattern = re.compile(r"db\s+([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)\s*,\s*([A-Z0-9_]+)")
    for raw in (tables.ROOT / "data/types/type_matchups.asm").read_text(encoding="utf-8").splitlines():
        code = raw.split(";", 1)[0].strip()
        if code == "db -1":
            break
        if not code or code == "db -2":
            continue
        match = pattern.fullmatch(code)
        if match is None:
            continue
        attack_type, defender_type, factor_name = match.groups()
        chart[(attack_type, defender_type)] = TYPE_FACTOR_CONSTANTS[factor_name]
    _TYPE_CHART_BY_NAME = chart
    return chart


def parse_accuracy(raw: dict[str, Any], row: tables.MoveRow | None, path: str) -> int:
    if "accuracy" in raw:
        return parse_byte(raw["accuracy"], path)
    if "accuracy_percent" in raw:
        return accuracy_percent_to_byte(parse_percentage(raw["accuracy_percent"], f"{path}_percent"))
    if row is not None:
        return accuracy_percent_to_byte(row.accuracy)
    return 255


def accuracy_percent_to_byte(percent: int) -> int:
    return percent * 0xFF // 100


def parse_actions(raw: Any) -> dict[str, ActionState]:
    if not isinstance(raw, dict):
        raise SimulationInputError("actions must be an object")
    return {
        "player": parse_action(raw.get("player", {"type": "move", "move": 0}), "actions.player"),
        "enemy": parse_action(raw.get("enemy", {"type": "move", "move": 0}), "actions.enemy"),
    }


def parse_action_plan(payload: dict[str, Any]) -> tuple[dict[str, ActionState], ...]:
    repeat = payload.get("repeat")
    if repeat is not None:
        if isinstance(repeat, int):
            max_turns = parse_positive_int(repeat, "repeat")
            repeat_actions = payload.get("actions", {})
        elif isinstance(repeat, dict):
            max_turns = parse_positive_int(repeat.get("max_turns", repeat.get("turns", 1)), "repeat.max_turns")
            repeat_actions = repeat.get("actions", payload.get("actions", {}))
        else:
            raise SimulationInputError("repeat must be an integer or object")
        return tuple(parse_actions(repeat_actions) for _ in range(max_turns))
    if "max_turns" in payload:
        max_turns = parse_positive_int(payload["max_turns"], "max_turns")
        return tuple(parse_actions(payload.get("actions", {})) for _ in range(max_turns))
    turns = payload.get("turns")
    if turns is None:
        return (parse_actions(payload.get("actions", {})),)
    if not isinstance(turns, list) or not turns:
        raise SimulationInputError("turns must be a non-empty list when provided")
    return tuple(parse_turn_actions(raw_turn, index) for index, raw_turn in enumerate(turns))


def parse_turn_actions(raw: Any, index: int) -> dict[str, ActionState]:
    if not isinstance(raw, dict):
        raise SimulationInputError(f"turns[{index}] must be an object")
    actions = raw.get("actions", raw)
    if not isinstance(actions, dict):
        raise SimulationInputError(f"turns[{index}].actions must be an object")
    return {
        "player": parse_action(actions.get("player", {"type": "move", "move": 0}), f"turns[{index}].player"),
        "enemy": parse_action(actions.get("enemy", {"type": "move", "move": 0}), f"turns[{index}].enemy"),
    }


def parse_action(raw: Any, path: str) -> ActionState:
    if isinstance(raw, int):
        return ActionState(kind="move", move_index=raw)
    if not isinstance(raw, dict):
        raise SimulationInputError(f"{path} must be an object")
    kind = str(raw.get("type", "move"))
    if kind == "move":
        return ActionState(kind="move", move_index=parse_non_negative_int(raw.get("move", 0), f"{path}.move"))
    if kind in {"switch", "replace"}:
        switch_index = raw.get("bench_index", raw.get("bench"))
        if switch_index is None:
            raise SimulationInputError(f"{path}.bench_index is required for {kind} actions")
        return ActionState(kind=kind, switch_index=parse_non_negative_int(switch_index, f"{path}.bench_index"))
    if kind == "item":
        if str(raw.get("target", "active")).lower() not in {"active", "self"}:
            raise SimulationInputError(f"{path}.target only supports active item targets")
        item = raw.get("item", raw.get("name"))
        if item is None:
            raise SimulationInputError(f"{path}.item is required for item actions")
        return ActionState(kind=kind, item=parse_item(item))
    if kind == "auto_replace":
        return ActionState(kind=kind)
    if kind == "auto_replace_or":
        fallback = raw.get("action", raw.get("fallback"))
        if fallback is None:
            raise SimulationInputError(f"{path}.action is required for auto_replace_or actions")
        return ActionState(kind=kind, fallback=parse_action(fallback, f"{path}.action"))
    if kind == "boss_ai_selector":
        if raw.get("execute") is True:
            return ActionState(kind="boss_ai_selector_move", selector=raw)
        return ActionState(kind=kind, selector=raw)
    if kind == "boss_ai_selector_move":
        return ActionState(kind=kind, selector=raw)
    if kind == "wild_random_move":
        return ActionState(kind=kind)
    return ActionState(kind=kind)


def parse_rng(raw: Any) -> RngConfig:
    if not isinstance(raw, dict):
        raise SimulationInputError("rng must be an object")
    mode = str(raw.get("mode", "fixed")).lower()
    if mode not in {"fixed", "sample", "exhaustive"}:
        raise SimulationInputError("rng.mode must be fixed, sample, or exhaustive")
    values = raw.get("values", [])
    if not isinstance(values, list):
        raise SimulationInputError("rng.values must be a list")
    seed = raw.get("seed")
    return RngConfig(
        mode=mode,  # type: ignore[arg-type]
        values=tuple(parse_byte(value, f"rng.values[{index}]") for index, value in enumerate(values)),
        samples=parse_positive_int(raw.get("samples", 1), "rng.samples"),
        seed=None if seed is None else parse_int(seed, "rng.seed"),
        speed_tie_default=parse_byte(raw.get("speed_tie_default", 0), "rng.speed_tie_default"),
        critical_default=parse_byte(raw.get("critical_default", 255), "rng.critical_default"),
        default=parse_byte(raw.get("default", 255), "rng.default"),
        accuracy_default=parse_byte(raw.get("accuracy_default", 0), "rng.accuracy_default"),
        max_outcomes=parse_positive_int(raw.get("max_outcomes", 2048), "rng.max_outcomes"),
    )


def parse_stat_stages(raw: Any, path: str) -> dict[str, int]:
    stages = {key: 0 for key in STAT_STAGE_KEYS}
    if raw in (None, ""):
        return stages
    if not isinstance(raw, dict):
        raise SimulationInputError(f"{path} must be an object")
    for raw_name, raw_stage in raw.items():
        key = str(raw_name).strip().lower()
        if key in {"accuracy", "acc", "evasion", "eva", "evade"}:
            raise SimulationInputError(f"{path}.{raw_name} is out of scope; accuracy/evasion stages use a separate ROM table")
        try:
            canonical = STAT_STAGE_ALIASES[key]
        except KeyError as exc:
            known = ", ".join(STAT_STAGE_KEYS)
            raise SimulationInputError(f"{path}.{raw_name} is unknown; supported stat stages: {known}") from exc
        stages[canonical] = parse_stat_stage(raw_stage, f"{path}.{raw_name}")
    return stages


def parse_stat_stage(raw: Any, path: str) -> int:
    stage = parse_int(raw, path)
    if stage < STAT_STAGE_MIN or stage > STAT_STAGE_MAX:
        raise SimulationInputError(f"{path} must be between -6 and +6")
    return stage


def selected_move(pokemon: PokemonState, action: ActionState) -> MoveState:
    if action.move_index is None or action.move_index >= len(pokemon.moves):
        raise SimulationInputError(f"{pokemon.side} move index out of range")
    return pokemon.moves[action.move_index]


def consume_move_pp(branch: dict[str, Any], side: str, move_index: int | None) -> dict[str, Any]:
    if move_index is None:
        raise SimulationInputError(f"{side} move index out of range")
    state: BattleState = branch["state"]
    pokemon = get_side(state, side)
    if move_index >= len(pokemon.moves):
        raise SimulationInputError(f"{side} move index out of range")
    move = pokemon.moves[move_index]
    updated_move = replace_move_pp(move, move.pp - 1)
    updated_pokemon = replace_move(pokemon, move_index, updated_move)
    updated = clone_branch(branch)
    updated["state"] = replace_side(state, side, updated_pokemon)
    return updated


def get_side(state: BattleState, side: str) -> PokemonState:
    return state.player if side == "player" else state.enemy


def replace_side(state: BattleState, side: str, pokemon: PokemonState) -> BattleState:
    if side == "player":
        return BattleState(
            player=pokemon,
            enemy=state.enemy,
            player_bench=state.player_bench,
            enemy_bench=state.enemy_bench,
            weather=state.weather,
            turn=state.turn,
        )
    return BattleState(
        player=state.player,
        enemy=pokemon,
        player_bench=state.player_bench,
        enemy_bench=state.enemy_bench,
        weather=state.weather,
        turn=state.turn,
    )


def advance_turn(state: BattleState) -> BattleState:
    return BattleState(
        player=state.player,
        enemy=state.enemy,
        player_bench=state.player_bench,
        enemy_bench=state.enemy_bench,
        weather=state.weather,
        turn=state.turn + 1,
    )


def get_bench(state: BattleState, side: str) -> tuple[PokemonState, ...]:
    return state.player_bench if side == "player" else state.enemy_bench


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
            player_bench=bench,
            enemy_bench=state.enemy_bench,
            weather=state.weather,
            turn=state.turn,
        )
    return BattleState(
        player=state.player,
        enemy=pokemon,
        player_bench=state.player_bench,
        enemy_bench=bench,
        weather=state.weather,
        turn=state.turn,
    )


def replace_hp(
    pokemon: PokemonState,
    hp: int,
    *,
    status: str | None = None,
    toxic_count: int | None = None,
) -> PokemonState:
    return PokemonState(
        side=pokemon.side,
        name=pokemon.name,
        level=pokemon.level,
        hp=hp,
        max_hp=pokemon.max_hp,
        types=pokemon.types,
        type_names=pokemon.type_names,
        attack=pokemon.attack,
        defense=pokemon.defense,
        speed=pokemon.speed,
        sp_attack=pokemon.sp_attack,
        sp_defense=pokemon.sp_defense,
        attack_stage=pokemon.attack_stage,
        defense_stage=pokemon.defense_stage,
        speed_stage=pokemon.speed_stage,
        sp_attack_stage=pokemon.sp_attack_stage,
        sp_defense_stage=pokemon.sp_defense_stage,
        item=pokemon.item,
        can_evolve=pokemon.can_evolve,
        focus_energy=pokemon.focus_energy,
        status=pokemon.status if status is None else status,
        toxic_count=pokemon.toxic_count if toxic_count is None else toxic_count,
        moves=pokemon.moves,
    )


def reset_stat_stages(pokemon: PokemonState) -> PokemonState:
    return dataclass_replace(
        pokemon,
        attack_stage=0,
        defense_stage=0,
        speed_stage=0,
        sp_attack_stage=0,
        sp_defense_stage=0,
    )


def replace_stat_stage(pokemon: PokemonState, key: str, stage: int) -> PokemonState:
    field_name = f"{key}_stage"
    if not hasattr(pokemon, field_name):
        raise AssertionError(f"unknown stat stage key {key!r}")
    return dataclass_replace(pokemon, **{field_name: stage})


def replace_move(pokemon: PokemonState, move_index: int, move: MoveState) -> PokemonState:
    moves = tuple(move if index == move_index else item for index, item in enumerate(pokemon.moves))
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
        attack_stage=pokemon.attack_stage,
        defense_stage=pokemon.defense_stage,
        speed_stage=pokemon.speed_stage,
        sp_attack_stage=pokemon.sp_attack_stage,
        sp_defense_stage=pokemon.sp_defense_stage,
        item=pokemon.item,
        can_evolve=pokemon.can_evolve,
        focus_energy=pokemon.focus_energy,
        status=pokemon.status,
        toxic_count=pokemon.toxic_count,
        moves=moves,
    )


def replace_move_pp(move: MoveState, pp: int) -> MoveState:
    return MoveState(
        name=move.name,
        effect=move.effect,
        move_type=move.move_type,
        move_type_name=move.move_type_name,
        bp=move.bp,
        priority=move.priority,
        accuracy=move.accuracy,
        pp=pp,
        contact=move.contact,
        move_id=move.move_id,
    )


def clone_branch(branch: dict[str, Any]) -> dict[str, Any]:
    cloned = {
        "state": branch["state"],
        "turn_order": list(branch["turn_order"]),
        "turn_orders": copy.deepcopy(branch["turn_orders"]),
        "events": copy.deepcopy(branch["events"]),
        "proof_notes": copy.deepcopy(branch["proof_notes"]),
        "rng_consumed": list(branch["rng_consumed"]),
        "turns_simulated": branch["turns_simulated"],
    }
    if "actions" in branch:
        cloned["actions"] = branch["actions"]
    return cloned


def branch_to_outcome(branch: dict[str, Any], index: int) -> dict[str, Any]:
    state = branch["state"]
    data = {
        "outcome_id": str(index),
        "turn_order": branch["turn_order"],
        "turn_orders": branch["turn_orders"],
        "turns_simulated": branch["turns_simulated"],
        "events": branch["events"],
        "state": state_to_json(state),
        "battle_over": battle_is_over(state),
        "rng_consumed": list(branch["rng_consumed"]),
    }
    if "sample_index" in branch:
        data["sample_index"] = branch["sample_index"]
    return data


def state_to_json(state: BattleState) -> dict[str, Any]:
    return {
        "turn": state.turn,
        "weather": state.weather,
        "player": pokemon_to_json(state.player),
        "enemy": pokemon_to_json(state.enemy),
        "player_bench": [pokemon_to_json(pokemon) for pokemon in state.player_bench],
        "enemy_bench": [pokemon_to_json(pokemon) for pokemon in state.enemy_bench],
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
        "focus_energy": pokemon.focus_energy,
        "status": pokemon.status,
        "toxic_count": pokemon.toxic_count,
        "stats": {
            "attack": pokemon.attack,
            "defense": pokemon.defense,
            "speed": pokemon.speed,
            "sp_attack": pokemon.sp_attack,
            "sp_defense": pokemon.sp_defense,
        },
        "stat_stages": stat_stages_to_json(pokemon),
        "moves": [move_to_json(move) for move in pokemon.moves],
    }


def move_to_json(move: MoveState) -> dict[str, Any]:
    return {
        "name": move.name,
        "effect": move.effect,
        "type": move.move_type_name,
        "bp": move.bp,
        "priority": move.priority,
        "accuracy": move.accuracy,
        "pp": move.pp,
        "contact": move.contact,
        "move_id": move.move_id,
    }


def coverage_report() -> dict[str, Any]:
    return {
        "byte_proven": [
            {
                "id": "damage_core_pre_variation",
                "source": "tools.damage_debugger.oracle.predict_damage + tools.damage_debugger.clobber_smoke",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "This first slice delegates pre-variation damage to the existing ROM-backed damage oracle/smoke surface.",
            }
        ],
        "source_mirrored_pending_differential": [
            {
                "id": "damage_variation_rng_branching",
                "source": "engine/battle/effect_commands.asm:BattleCommand_DamageVariation",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "0/1 damage skips variation; otherwise RNG bytes are rotated right, rejected below 217, and accepted multipliers 217..255 scale damage over 255. Fixed/sample/exhaustive modes are implemented for this mechanic only.",
            },
            {
                "id": "basic_move_accuracy_rng",
                "source": "engine/battle/effect_commands.asm:BattleCommand_CheckHit",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Move accuracy bytes, always-hit moves, and Thunder-in-rain bypass are mirrored. Fixed/sample/exhaustive modes branch hit/miss for the basic raw-byte threshold check. Accuracy/evasion stat stages, BrightPowder, Protect, Fly/Dig, Lock-On, X Accuracy, and passive bonuses are not in this slice.",
            },
            {
                "id": "basic_critical_hit_rng",
                "source": "engine/battle/effect_commands.asm:BattleCommand_Critical",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Critical-hit level and raw-byte threshold are mirrored for normal damaging moves, including Focus Energy, high-critical moves, Lucky Punch, Stick, and Scope Lens. Fixed/sample/exhaustive modes branch critical/non-critical before damage variation and accuracy, matching the NormalHit command order.",
            },
            {
                "id": "basic_status_residual",
                "source": "engine/battle/core.asm:ResidualDamage",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Initial poison, burn, and toxic residual damage is mirrored after a selected move when both active Pokemon remain alive. Status application outside selected poison/paralysis moves, sleep, freeze, Leech Seed, Nightmare, Curse, weather, Leftovers, and item/status cures outside the explicit active Full Restore subset remain out of scope.",
            },
            {
                "id": "basic_pp_decrement",
                "source": "engine/battle/effect_commands.asm:BattleCommand_DoTurn",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Selected and executable-selector moves decrement PP once before their supported effect handling. Zero-PP selected moves are rejected because Struggle and full move-legality selection are not implemented.",
            },
            {
                "id": "supported_after_hit_item_effects",
                "source": "engine/battle/late_gen_held_items.asm:HandleLateGenAfterHitEffects_Far + tools.damage_debugger.clobber_smoke",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Rocky Helmet contact recoil, Shell Bell healing, and Life Orb recoil are mirrored after successful damaging hits. The damage debugger smoke byte-proves these isolated handler effects; the headless path applies the same HP fractions and item order for the supported subset.",
            },
            {
                "id": "explicit_active_hp_restore_items",
                "source": "engine/items/item_effects.asm:RestoreHPEffect + FullRestoreEffect; data/items/heal_hp.asm",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Explicit item actions for active Potion, Super Potion, Hyper Potion, Max Potion, and Full Restore mirror source HP amounts, max-HP caps, Full Restore's supported status/toxic cure, turn consumption, and actor residual after the item. Bag inventory, bench targeting, revives, PP restore, X items, player trainer-battle Pack availability, and automatic trainer item dispatch remain out of scope.",
            },
            {
                "id": "selected_turn_order_priority_speed",
                "source": "engine/battle/core.asm:DetermineMoveOrder",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Priority, unequal modified-speed ordering, the non-link equal-speed tie RNG threshold, and selected switch/item non-move ordering are mirrored for selected turns. Speed stages use data/battle/stat_multipliers.asm. Baseline paralysis speed uses the source 1/4 speed rule. Quick Claw, Choice Scarf, link-battle inversion, and type-passive speed modifiers are not in this slice.",
            },
            {
                "id": "explicit_stat_stage_state",
                "source": "data/battle/stat_multipliers.asm + engine/battle/effect_commands.asm:CalcBattleStats + engine/battle/core.asm:DetermineMoveOrder",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Scenario-supplied active attack/defense/speed/sp_attack/sp_defense stages in the -6..+6 user-facing range use the ROM percentage table for damage stats and turn-order speed; switch/replacement resets stages. Critical-hit stat handling mirrors CheckDamageStatsCritical's rule: use modified stats only when the attacker's offensive stage is higher than the defender's matching defensive stage. Stage-changing move effects outside the selected single-stat BP=0 subset, accuracy/evasion stages, Baton Pass/Psych Up, badge boosts, status speed, and passive stat modifiers remain out of scope.",
            },
            {
                "id": "selected_stat_stage_only_moves",
                "source": "data/moves/effects.asm AttackUp/DefenseUp/SpeedUp/SpecialAttackUp/SpecialDefenseUp and matching Down/Up2/Down2 scripts + engine/battle/effect_commands.asm:RaiseStat/LowerStat",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Selected BP=0 single-stat stage moves for attack/defense/speed/sp_attack/sp_defense consume PP, run checkhit for opponent-lowering moves, mutate stages by one or two with -6..+6 caps, and report no-effect cap/floor cases. Accuracy/evasion stage moves, damaging secondary stat effects, multi-stat chain moves, Substitute/Mist blockers, and text/animation side effects remain out of scope.",
            },
            {
                "id": "selected_self_heal_moves",
                "source": "engine/battle/effect_commands.asm:BattleCommand_Heal + data/moves/effects.asm:Heal",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Recover, Softboiled, and Milk Drink consume PP, restore half max HP with max-HP cap, report full-HP no-effect cases, and preserve post-action residual. Rest branches through the same command but adds full HP restoration, sleep/status handling, and stat recalculation, so Rest remains out of scope until sleep/status move effects are modeled.",
            },
            {
                "id": "selected_poison_status_moves",
                "source": "data/moves/effects.asm:Toxic/DoPoison + engine/battle/effect_commands.asm:BattleCommand_Poison",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "PoisonPowder, Poison Gas, and Toxic consume PP, run the basic accuracy check, apply poison/toxic to healthy non-Poison non-immune targets, initialize toxic_count at 0, and report no-effect cases for Poison-type targets, type immunity, and already-statused targets. Safeguard, Substitute, held status-healing item consumption, damaging poison secondary effects, and text/animation side effects remain out of scope.",
            },
            {
                "id": "selected_paralysis_status_moves",
                "source": "data/moves/effects.asm:DoParalyze + engine/battle/effect_commands.asm:BattleCommand_Paralyze + type_passive_damage_mods.asm:TypePassive_GetUserParalysisFailThreshold_Far",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Thunder Wave, Stun Spore, and Glare consume PP after the full-paralysis gate, run the basic accuracy check, apply paralysis to healthy non-immune targets, reduce future turn-order speed with ApplyPrzEffectOnSpeed's Electric/Fighting type-passive paralysis modifiers, and branch full-paralysis action denial with TypePassive_GetUserParalysisFailThreshold_Far's Fighting thresholds before PP decrement. Type immunity and already-statused targets report no effect. Safeguard, Substitute, held prevent/cure items, non-paralyzed Electric speed passives, and damaging paralysis secondary effects remain out of scope.",
            },
            {
                "id": "multi_turn_selected_action_progression",
                "source": "tools.headless_battle.simulator.simulate_battle",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "A turns[] list carries HP/RNG state forward across selected-action turns, supports caller-selected switch actions, caller-supplied replacement actions after a KO, and explicit enemy auto_replace actions. Automatic action choice is still out of scope.",
            },
            {
                "id": "repeat_plan_auto_replace_or",
                "source": "tools.headless_battle.simulator.parse_action_plan + simulate_battle",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "repeat/max_turns can reuse one action map until battle-over or the turn cap. auto_replace_or lets a side use a normal fallback action while alive and explicit auto_replace after fainting, so simple text battles no longer require hand-writing every replacement step.",
            },
            {
                "id": "selected_switch_and_replacement",
                "source": "engine/battle/core.asm:TryPlayerSwitch, PlayerSwitch, DoubleSwitch, EnemySwitch",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Caller-selected switch actions swap the active Pokemon with a bench slot before the opponent's move, replace actions can continue a planned battle after a KO, and both entry paths reset stat stages. Pursuit, Spikes, switch-in effects, and forced prompts remain out of scope.",
            },
            {
                "id": "auto_replacement_choice_basic_type_chart",
                "source": "engine/battle/core.asm:FindMonInOTPartyToSwitchIntoBattle + data/types/type_matchups.asm",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Enemy auto_replace actions choose from living bench Pokemon using the source-shaped trainer replacement preference: prefer candidates with a super-effective move, otherwise avoid candidates the player's public types hit super-effectively, otherwise use BattleRandom-style low-three-bit rejection. Dragon's Majesty, Air Balloon, Foresight/identified state, trainer party loading, player prompt flow, and switch-in effects remain out of scope.",
            },
            {
                "id": "boss_ai_selector_from_post_score_bytes",
                "source": "tools.boss_ai_debugger.rom_scenarios.select_from_score_bytes",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Report-only Boss AI selector actions consume already-known post-score bytes. Live score generation is out of scope.",
            },
            {
                "id": "boss_ai_selector_move_execution",
                "source": "engine/battle/ai/boss_policy_move.asm:BossAI_SelectMove + tools.boss_ai_debugger.rom_scenarios.select_from_score_bytes",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Executable Boss AI selector actions branch fixed/sample/exhaustive RNG over already-known final score bytes, validate the selected slot/move id when available, and then run the chosen move through the existing selected-turn path. Score generation and switch confidence remain out of scope.",
            },
            {
                "id": "wild_random_move_choice",
                "source": "engine/battle/core.asm enemy wild move selection loop",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "wild_random_move actions mirror the four-slot wild enemy random move loop for non-empty, nonzero-PP moves. Fixed/sample modes consume raw bytes until a legal slot is selected; exhaustive mode branches one outcome per legal slot. Disabled moves, locks, and Struggle remain out of scope.",
            },
        ],
        "out_of_scope": [
            "automatic full battle flow, trainer/Boss automatic action choice without caller-supplied final Boss AI score bytes, forced switch prompts, implicit replacement without an auto_replace action, automatic trainer item turns, player trainer-battle Pack availability, and item inventory accounting",
            "Pursuit-on-switch, Spikes/switch-in entry effects, switch-triggered abilities/passives, and switch memory side effects",
            "RNG-consuming mechanics outside speed ties/Boss AI selector choice/wild random move choice/auto-replace fallback/critical hits/accuracy/damage variation, Quick Claw/Choice Scarf turn-order effects",
            "accuracy/evasion stat-stage move effects, damaging secondary stat effects, multi-stat chain moves, BrightPowder, Protect, Fly/Dig, Lock-On, X Accuracy, Baton Pass/Psych Up, Substitute/Mist blockers, badge boosts, status speed modifiers, passive stat/speed/accuracy bonuses, and passive accuracy bonuses",
            "sleep, freeze, burn application, Safeguard/Substitute, held status prevent/cure item consumption, non-paralyzed Electric speed passives, volatile effects, weather/time healing, Rest, drain moves, Heal Bell, unsupported item recovery/cures, Air Balloon pop, Substitute-blocked contact, Focus Punch break, after-hit text/script effects outside supported HP mutations, Struggle, PP Up bit packing, Mimic/Transform PP routing, and full PP legality selection",
            "Boss AI live score generation and switch candidate/confidence generation",
            "graphics, text scripts, animations, EXP, and party writes",
        ],
    }


def summarize(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    event_counts: dict[str, int] = {}
    for outcome in outcomes:
        for event in outcome["events"]:
            event_counts[event["type"]] = event_counts.get(event["type"], 0) + 1
    return {"event_counts": event_counts}


def format_text(report: dict[str, Any]) -> str:
    lines = [
        f"Headless battle simulation: turns={report['turn_count']} outcomes={report['outcome_count']} rng={report['rng']['mode']}",
        "Coverage:",
    ]
    for row in report["coverage"]["byte_proven"]:
        lines.append(f"  byte-proven: {row['id']} via {row['gate']}")
    for row in report["coverage"]["source_mirrored_pending_differential"]:
        lines.append(f"  source-mirrored: {row['id']} via {row['source']}")
    lines.append("")
    for outcome in report["outcomes"]:
        state = outcome["state"]
        if outcome.get("turn_orders"):
            order = "; ".join(
                f"{row['turn']}:{','.join(row['order'])}"
                for row in outcome["turn_orders"]
            )
        else:
            order = ",".join(outcome["turn_order"])
        lines.append(
            f"Outcome {outcome['outcome_id']}: order={order} "
            f"player_hp={state['player']['hp']}/{state['player']['max_hp']} "
            f"enemy_hp={state['enemy']['hp']}/{state['enemy']['max_hp']}"
        )
        for event in outcome["events"]:
            if event["type"] == "damage":
                variation = event.get("damage_variation", {})
                suffix = ""
                if variation.get("applied"):
                    suffix = f" (pre={event['pre_variation_damage']} mult={variation['multiplier']})"
                if event.get("critical_check", {}).get("critical"):
                    suffix += " critical"
                lines.append(
                    f"  turn {event['turn']} {event['actor']} {event['move']} -> "
                    f"{event['target']} {event['damage']} damage{suffix}"
                )
            elif event["type"] == "boss_ai_select_move" and "selected_move" in event:
                lines.append(
                    f"  turn {event['turn']} {event['actor']} boss_ai_select_move -> "
                    f"{event['selected_move']} slot={event['selected_slot_index']}"
                )
            elif event["type"] == "wild_random_move":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} wild_random_move -> "
                    f"{event['selected_move']} slot={event['selected_slot_index']}"
                )
            elif event["type"] == "after_hit_recoil":
                lines.append(
                    f"  turn {event['turn']} {event['source_item']} recoil -> "
                    f"{event['target']} {event['damage']} damage"
                )
            elif event["type"] == "after_hit_heal":
                lines.append(
                    f"  turn {event['turn']} {event['source_item']} heal -> "
                    f"{event['actor']} {event['heal']} hp"
                )
            elif event["type"] == "item_restore":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} {event['item']} -> "
                    f"+{event['heal']} hp"
                )
            elif event["type"] == "self_heal":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} {event['move']} -> "
                    f"+{event['heal']} hp"
                )
            elif event["type"] == "status_apply":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} {event['move']} -> "
                    f"{event['target']} {event['status']}"
                )
            elif event["type"] == "status_no_effect":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} {event['move']} -> "
                    f"no effect ({event['blocked_reason']})"
                )
            elif event["type"] == "residual_damage":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} {event['status']} residual -> "
                    f"{event['damage']} damage"
                )
            elif event["type"] == "fully_paralyzed":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} fully paralyzed -> "
                    f"{event['move']} skipped"
                )
            elif event["type"] == "stat_stage_change":
                changes = ", ".join(
                    f"{row['stat']} {row['stage_before']}->{row['stage_after']}"
                    for row in event["changes"]
                )
                lines.append(
                    f"  turn {event['turn']} {event['actor']} {event['move']} -> "
                    f"{event['target']} {changes}"
                )
            elif event["type"] == "auto_replacement_choice":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} auto_replace -> "
                    f"{event['selected']} bench={event['selected_bench_index']} reason={event['reason']}"
                )
            else:
                lines.append(f"  turn {event.get('turn')} {event.get('actor', '')} {event['type']}")
    return "\n".join(lines)


def scenario_template() -> dict[str, Any]:
    return {
        "rng": {"mode": "fixed", "values": []},
        "state": {
            "weather": "none",
            "turn": 1,
            "player": {
                "species": "PIDGEY",
                "level": 2,
                "hp": 16,
                "max_hp": 16,
                "stats": {"attack": 6, "defense": 7, "speed": 10, "sp_attack": 6, "sp_defense": 7},
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
            },
            "enemy": {
                "species": "CYNDAQUIL",
                "level": 5,
                "hp": 18,
                "max_hp": 18,
                "stats": {"attack": 10, "defense": 9, "speed": 9, "sp_attack": 11, "sp_defense": 10},
                "moves": [{"name": "TACKLE", "type": "NORMAL", "bp": 40}],
            },
        },
        "actions": {"player": {"type": "move", "move": 0}, "enemy": {"type": "move", "move": 0}},
    }


def run_self_test() -> None:
    report = simulate_payload(scenario_template())
    if report["kind"] != REPORT_KIND:
        raise AssertionError(report)
    outcome = report["outcomes"][0]
    if outcome["turn_order"] != ["player", "enemy"]:
        raise AssertionError(report)
    if not any(event["type"] == "damage" for event in outcome["events"]):
        raise AssertionError(report)
    selector_payload = scenario_template()
    selector_payload["actions"]["enemy"] = {
        "type": "boss_ai_selector",
        "scenario_id": "self_test_selector",
        "tier": "late",
        "move_ids": [33, 52, 0, 0],
        "scores": [20, 30, 80, 80],
    }
    selector = simulate_payload(selector_payload)["outcomes"][0]["events"][1]
    if selector["type"] != "boss_ai_select_move" or not selector["selector"]["ready"]:
        raise AssertionError(selector)
    selector_move_payload = scenario_template()
    selector_move_payload["state"]["player"]["moves"][0]["bp"] = 0
    selector_move_payload["state"]["enemy"]["moves"] = [
        {"name": "TACKLE", "type": "NORMAL", "bp": 0},
        {"name": "EMBER", "type": "FIRE", "bp": 40},
    ]
    selector_move_payload["actions"]["enemy"] = {
        "type": "boss_ai_selector_move",
        "scenario_id": "self_test_selector_move",
        "tier": "late",
        "move_ids": [33, 52, 0, 0],
        "scores": [20, 21, 80, 80],
    }
    selector_move_payload["rng"] = {"mode": "fixed", "values": [200, 255, 255]}
    selector_move = simulate_payload(selector_move_payload)["outcomes"][0]["events"]
    if selector_move[0]["selected_slot_index"] != 1 or selector_move[-1].get("move") != "EMBER":
        raise AssertionError(selector_move)


def load_payload(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SimulationInputError(f"could not read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SimulationInputError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SimulationInputError("scenario file must contain an object")
    return data


def parse_type_pair(raw: Any, path: str) -> tuple[tuple[str, str], tuple[int, int]]:
    if not isinstance(raw, list) or len(raw) not in {1, 2}:
        raise SimulationInputError(f"{path} must contain one or two type names")
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
    return name, tables.load_type_constants()[name]


def source_species_row(raw: Any, path: str) -> tables.BaseStatsRow | None:
    if raw in (None, ""):
        return None
    if not isinstance(raw, str):
        raise SimulationInputError(f"{path} must be a species name")
    key = tables.resolve_name(raw, tables.load_base_stats(), "species")
    return tables.load_base_stats()[key]


def parse_weather(raw: Any) -> int:
    if isinstance(raw, int):
        return raw
    if not isinstance(raw, str):
        raise SimulationInputError("weather must be a string or int")
    if raw.lower() in {"none", "clear"}:
        return oracle.WEATHER_NONE
    return tables.weather_to_int(raw)


def parse_item(raw: Any) -> int:
    if raw in (None, "", 0, "0", "none", "NONE", "NO_ITEM"):
        return oracle.HELD_NONE
    if isinstance(raw, int):
        return raw
    if not isinstance(raw, str):
        raise SimulationInputError("item must be an int or item constant")
    return tables.resolve_item(raw)


def parse_status(raw: Any, path: str) -> str:
    if not isinstance(raw, str):
        raise SimulationInputError(f"{path} must be a status string")
    normalized = raw.strip().lower()
    aliases = {
        "": "none",
        "none": "none",
        "ok": "none",
        "healthy": "none",
        "psn": "poison",
        "poison": "poison",
        "poisoned": "poison",
        "tox": "toxic",
        "toxic": "toxic",
        "badly_poisoned": "toxic",
        "brn": "burn",
        "burn": "burn",
        "burned": "burn",
        "par": "paralyze",
        "prz": "paralyze",
        "paralyze": "paralyze",
        "paralyzed": "paralyze",
        "paralysis": "paralyze",
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        raise SimulationInputError(
            f"{path} must be none, poison, toxic, burn, or paralyze; other status mechanics are out of scope"
        ) from exc


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


def parse_percentage(raw: Any, path: str) -> int:
    value = parse_int(raw, path)
    if value < 0 or value > 100:
        raise SimulationInputError(f"{path} must be in percent range 0..100")
    return value


def parse_optional_byte(raw: Any, path: str) -> int | None:
    if raw is None:
        return None
    return parse_byte(raw, path)


def parse_bool(raw: Any, path: str) -> bool:
    if not isinstance(raw, bool):
        raise SimulationInputError(f"{path} must be a boolean")
    return raw


def rng_to_json(rng: RngConfig) -> dict[str, Any]:
    data: dict[str, Any] = {"mode": rng.mode}
    if rng.values:
        data["values"] = list(rng.values)
    if rng.speed_tie_default != 0:
        data["speed_tie_default"] = rng.speed_tie_default
    if rng.critical_default != 255:
        data["critical_default"] = rng.critical_default
    if rng.default != 255:
        data["default"] = rng.default
    if rng.accuracy_default != 0:
        data["accuracy_default"] = rng.accuracy_default
    if rng.mode == "sample":
        data["samples"] = rng.samples
        data["seed"] = rng.seed
    if rng.mode == "exhaustive":
        data["max_outcomes"] = rng.max_outcomes
    return data
