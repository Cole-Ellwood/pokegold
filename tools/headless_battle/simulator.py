from __future__ import annotations

import copy
import json
from dataclasses import dataclass
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


class SimulationInputError(Exception):
    """User-facing scenario error."""


@dataclass(frozen=True)
class MoveState:
    name: str
    move_type: int
    move_type_name: str
    bp: int
    priority: int = 1
    accuracy: int = 255
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
    item: int = oracle.HELD_NONE
    can_evolve: bool = False
    moves: tuple[MoveState, ...] = ()


@dataclass(frozen=True)
class BattleState:
    player: PokemonState
    enemy: PokemonState
    weather: int = oracle.WEATHER_NONE
    turn: int = 1


@dataclass(frozen=True)
class ActionState:
    kind: str
    move_index: int | None = None
    selector: dict[str, Any] | None = None


@dataclass(frozen=True)
class RngConfig:
    mode: RngMode
    values: tuple[int, ...] = ()
    samples: int = 1
    seed: int | None = None


def simulate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    state = parse_state(payload.get("state", {}))
    actions = parse_actions(payload.get("actions", {}))
    rng = parse_rng(payload.get("rng", {"mode": "fixed", "values": []}))
    validate_supported_rng(rng)
    outcomes = simulate_samples(state, actions, rng)
    report = {
        "kind": REPORT_KIND,
        "schema_version": SCHEMA_VERSION,
        "turn_count": 1,
        "outcome_count": len(outcomes),
        "rng": rng_to_json(rng),
        "coverage": coverage_report(),
        "summary": summarize(outcomes),
        "outcomes": outcomes,
    }
    return report


def simulate_samples(
    state: BattleState,
    actions: dict[str, ActionState],
    rng: RngConfig,
) -> list[dict[str, Any]]:
    return [branch_to_outcome(simulate_turn(state, actions), 0)]


def simulate_turn(state: BattleState, actions: dict[str, ActionState]) -> dict[str, Any]:
    order = turn_order(state, actions)
    branch: dict[str, Any] = {
        "state": state,
        "turn_order": order,
        "events": [],
        "proof_notes": [],
    }
    for side in order:
        action = actions[side]
        if action.kind == "boss_ai_selector":
            branch["events"].append(run_boss_ai_selector(state, side, action))
            continue
        if action.kind != "move":
            branch["events"].append(
                {
                    "turn": state.turn,
                    "actor": side,
                    "type": "unsupported_noop",
                    "reason": f"unsupported action kind {action.kind!r}",
                    "proof_status": "out_of_scope",
                }
            )
            continue
        branch = apply_move(branch, side, action)
        if branch["state"].player.hp <= 0 or branch["state"].enemy.hp <= 0:
            break
    return branch


def turn_order(state: BattleState, actions: dict[str, ActionState]) -> list[str]:
    player_action = actions["player"]
    enemy_action = actions["enemy"]
    if player_action.kind != "move" or enemy_action.kind != "move":
        return ["player", "enemy"]
    player_move = selected_move(state.player, player_action)
    enemy_move = selected_move(state.enemy, enemy_action)
    if player_move.priority != enemy_move.priority:
        return ["player", "enemy"] if player_move.priority > enemy_move.priority else ["enemy", "player"]
    for pokemon in (state.player, state.enemy):
        if pokemon.item in TURN_ORDER_AFFECTING_ITEMS:
            raise SimulationInputError(
                f"{pokemon.side} item {tables.display_item(pokemon.item)} modifies turn order and is out of scope"
            )
    if state.player.speed != state.enemy.speed:
        return ["player", "enemy"] if state.player.speed > state.enemy.speed else ["enemy", "player"]
    raise SimulationInputError("equal-speed turn order requires RNG speed-tie logic and is out of scope")


def apply_move(branch: dict[str, Any], side: str, action: ActionState) -> dict[str, Any]:
    state: BattleState = branch["state"]
    attacker = get_side(state, side)
    target_side = "enemy" if side == "player" else "player"
    target = get_side(state, target_side)
    move = selected_move(attacker, action)
    if move.bp <= 0:
        updated = clone_branch(branch)
        updated["events"].append(
            {
                "turn": state.turn,
                "actor": side,
                "move": move.name,
                "type": "unsupported_noop",
                "reason": "first slice only mutates HP for damaging moves with bp > 0",
                "proof_status": "out_of_scope",
            }
        )
        return updated
    damage = predict_pre_variation_damage(state, attacker, target, move)
    hp_after = max(0, target.hp - damage)
    updated_target = replace_hp(target, hp_after)
    updated_state = replace_side(state, target_side, updated_target)
    updated = clone_branch(branch)
    updated["state"] = updated_state
    updated["events"].append(
        {
            "turn": state.turn,
            "actor": side,
            "target": target_side,
            "move": move.name,
            "type": "damage",
            "damage": damage,
            "target_hp_before": target.hp,
            "target_hp_after": hp_after,
            "proof_status": "delegated_damage_oracle_pre_variation",
        }
    )
    return updated


def predict_pre_variation_damage(
    state: BattleState,
    attacker: PokemonState,
    target: PokemonState,
    move: MoveState,
) -> int:
    is_physical = tables.is_physical_type(move.move_type)
    inputs = oracle.BattleInputs(
        attacker_level=attacker.level,
        move_bp=move.bp,
        move_type=move.move_type,
        is_physical=is_physical,
        attacker_atk=attacker.attack if is_physical else attacker.sp_attack,
        defender_def=target.defense if is_physical else target.sp_defense,
        attacker_types=attacker.types,
        defender_types=target.types,
        user_item=attacker.item,
        opponent_item=target.item,
        can_evolve_attacker=attacker.can_evolve,
        can_evolve_defender=target.can_evolve,
        weather=state.weather,
        battle_turn=0 if attacker.side == "player" else 1,
    )
    return oracle.predict_damage(inputs)


def run_boss_ai_selector(state: BattleState, side: str, action: ActionState) -> dict[str, Any]:
    assert action.selector is not None
    selector = action.selector
    try:
        result = rom_scenarios.select_from_score_bytes(
            scenario_id=str(selector.get("scenario_id", "headless_boss_ai_selector")),
            tier=selector.get("tier", "late"),
            move_ids=[int(value) for value in selector["move_ids"]],
            scores=[int(value) for value in selector["scores"]],
        )
    except (KeyError, PreferenceDataError, ValueError) as exc:
        raise SimulationInputError(f"invalid boss_ai_selector action: {exc}") from exc
    return {
        "turn": state.turn,
        "actor": side,
        "type": "boss_ai_select_move",
        "selector": result,
        "proof_status": "source_mirrored_existing_selector_oracle",
    }


def parse_state(raw: Any) -> BattleState:
    if not isinstance(raw, dict):
        raise SimulationInputError("state must be an object")
    return BattleState(
        player=parse_pokemon(raw.get("player"), "player"),
        enemy=parse_pokemon(raw.get("enemy"), "enemy"),
        weather=parse_weather(raw.get("weather", "none")),
        turn=parse_positive_int(raw.get("turn", 1), "state.turn"),
    )


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
        item=parse_item(raw.get("item", 0)),
        can_evolve=bool(raw.get("can_evolve", can_evolve)),
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
    type_name = raw.get("type", row.type_name if row is not None else "NORMAL")
    move_type_name, move_type = parse_type(type_name, f"{path}.type")
    return MoveState(
        name=name,
        move_type=move_type,
        move_type_name=move_type_name,
        bp=parse_non_negative_int(raw.get("bp", row.bp if row is not None else 40), f"{path}.bp"),
        priority=parse_int(raw.get("priority", 1), f"{path}.priority"),
        accuracy=parse_byte(raw.get("accuracy", 255), f"{path}.accuracy"),
        move_id=parse_optional_byte(raw.get("move_id"), f"{path}.move_id"),
    )


def parse_actions(raw: Any) -> dict[str, ActionState]:
    if not isinstance(raw, dict):
        raise SimulationInputError("actions must be an object")
    return {
        "player": parse_action(raw.get("player", {"type": "move", "move": 0}), "actions.player"),
        "enemy": parse_action(raw.get("enemy", {"type": "move", "move": 0}), "actions.enemy"),
    }


def parse_action(raw: Any, path: str) -> ActionState:
    if isinstance(raw, int):
        return ActionState(kind="move", move_index=raw)
    if not isinstance(raw, dict):
        raise SimulationInputError(f"{path} must be an object")
    kind = str(raw.get("type", "move"))
    if kind == "move":
        return ActionState(kind="move", move_index=parse_non_negative_int(raw.get("move", 0), f"{path}.move"))
    if kind == "boss_ai_selector":
        return ActionState(kind=kind, selector=raw)
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
    )


def validate_supported_rng(rng: RngConfig) -> None:
    if rng.mode != "fixed":
        raise SimulationInputError(
            "rng.mode sample/exhaustive is planned, but this first slice only supports fixed deterministic turns"
        )
    if rng.values:
        raise SimulationInputError(
            "rng.values are not consumed until an RNG-consuming mechanic is implemented and proven"
        )


def selected_move(pokemon: PokemonState, action: ActionState) -> MoveState:
    if action.move_index is None or action.move_index >= len(pokemon.moves):
        raise SimulationInputError(f"{pokemon.side} move index out of range")
    return pokemon.moves[action.move_index]


def get_side(state: BattleState, side: str) -> PokemonState:
    return state.player if side == "player" else state.enemy


def replace_side(state: BattleState, side: str, pokemon: PokemonState) -> BattleState:
    if side == "player":
        return BattleState(player=pokemon, enemy=state.enemy, weather=state.weather, turn=state.turn)
    return BattleState(player=state.player, enemy=pokemon, weather=state.weather, turn=state.turn)


def replace_hp(pokemon: PokemonState, hp: int) -> PokemonState:
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
        item=pokemon.item,
        can_evolve=pokemon.can_evolve,
        moves=pokemon.moves,
    )


def clone_branch(branch: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": branch["state"],
        "turn_order": list(branch["turn_order"]),
        "events": copy.deepcopy(branch["events"]),
        "proof_notes": copy.deepcopy(branch["proof_notes"]),
    }


def branch_to_outcome(branch: dict[str, Any], index: int) -> dict[str, Any]:
    state = branch["state"]
    data = {
        "outcome_id": str(index),
        "turn_order": branch["turn_order"],
        "events": branch["events"],
        "state": state_to_json(state),
        "battle_over": state.player.hp <= 0 or state.enemy.hp <= 0,
    }
    if "sample_index" in branch:
        data["sample_index"] = branch["sample_index"]
        data["sample_seed_byte"] = branch["sample_seed_byte"]
    return data


def state_to_json(state: BattleState) -> dict[str, Any]:
    return {
        "turn": state.turn,
        "weather": state.weather,
        "player": pokemon_to_json(state.player),
        "enemy": pokemon_to_json(state.enemy),
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
        "stats": {
            "attack": pokemon.attack,
            "defense": pokemon.defense,
            "speed": pokemon.speed,
            "sp_attack": pokemon.sp_attack,
            "sp_defense": pokemon.sp_defense,
        },
        "moves": [move_to_json(move) for move in pokemon.moves],
    }


def move_to_json(move: MoveState) -> dict[str, Any]:
    return {
        "name": move.name,
        "type": move.move_type_name,
        "bp": move.bp,
        "priority": move.priority,
        "accuracy": move.accuracy,
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
                "id": "selected_turn_order_priority_speed",
                "source": "engine/battle/core.asm:DetermineMoveOrder",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Priority and unequal raw-speed ordering are mirrored for move-vs-move selected turns. Quick Claw, Choice Scarf, speed ties, switches, and status speed are not in this first slice.",
            },
            {
                "id": "boss_ai_selector_from_post_score_bytes",
                "source": "tools.boss_ai_debugger.rom_scenarios.select_from_score_bytes",
                "gate": "python tools/audit/check_headless_battle_simulator.py",
                "notes": "Boss AI selector actions consume already-known post-score bytes. Live score generation is out of scope.",
            },
        ],
        "out_of_scope": [
            "automatic full battle flow, switch actions, forced switch prompts, items as actions, and trainer item turns",
            "sample/exhaustive RNG, consumed fixed RNG bytes, speed ties, Quick Claw/Choice Scarf turn-order effects",
            "damage variation, critical hits, accuracy misses, status effects, volatile effects, between-turn effects, and after-hit effects",
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
        lines.append(
            f"Outcome {outcome['outcome_id']}: order={','.join(outcome['turn_order'])} "
            f"player_hp={state['player']['hp']}/{state['player']['max_hp']} "
            f"enemy_hp={state['enemy']['hp']}/{state['enemy']['max_hp']}"
        )
        for event in outcome["events"]:
            if event["type"] == "damage":
                lines.append(
                    f"  turn {event['turn']} {event['actor']} {event['move']} -> "
                    f"{event['target']} {event['damage']} damage"
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


def rng_to_json(rng: RngConfig) -> dict[str, Any]:
    data: dict[str, Any] = {"mode": rng.mode}
    if rng.values:
        data["values"] = list(rng.values)
    if rng.mode == "sample":
        data["samples"] = rng.samples
        data["seed"] = rng.seed
    return data
