from __future__ import annotations

import re
from typing import Any

from tools.boss_ai_debugger.scorer import inspect_fixture

from .damage_estimates import attach_damage_estimates
from .features import (
    LOCK_MOVES,
    RECOVERY_MOVES,
    SACRIFICE_MOVES,
    SETUP_MOVES,
    SLEEP_MOVES,
    SPEED_CONTROL_MOVES,
    STATUS_MOVES,
)
from .rollouts import DEFAULT_ROLLOUT_MODE, normalize_rollout_mode, project_plan
from .threat_availability import attach_incoming_threats


DEFAULT_PLAN_HORIZON = 3
MAX_PLAN_HORIZON = 5


def slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return text or "plan"


def phase_for_fixture(fixture: dict[str, Any]) -> str:
    turn = fixture.get("turn")
    if isinstance(turn, bool):
        turn = None
    try:
        turn_number = int(turn)
    except (TypeError, ValueError):
        turn_number = 1
    if turn_number <= 2:
        return "early"
    if turn_number <= 8:
        return "mid"
    return "late"


def enrich_fixture_for_plans(fixture: dict[str, Any]) -> dict[str, Any]:
    return attach_incoming_threats(attach_damage_estimates([fixture]))[0]


def action_name(action: dict[str, Any] | None) -> str:
    if not action:
        return "unknown action"
    return str(action.get("name") or action.get("id") or "unknown action")


def action_id(action: dict[str, Any] | None) -> str:
    return str(action.get("id") or "") if action else ""


def action_name_key(action: dict[str, Any]) -> str:
    return action_name(action).strip().lower()


def action_kind(action: dict[str, Any] | None) -> str:
    return str(action.get("kind") or "") if action else ""


def is_switch_action(action: dict[str, Any]) -> bool:
    return action_kind(action) == "switch" or action_id(action).startswith("switch_")


def is_damage_action(action: dict[str, Any]) -> bool:
    return action_kind(action) == "move" and isinstance(action.get("damage_estimate"), dict)


def is_setup_action(action: dict[str, Any]) -> bool:
    return action_name_key(action) in SETUP_MOVES


def is_status_action(action: dict[str, Any]) -> bool:
    return action_name_key(action) in STATUS_MOVES


def is_sleep_action(action: dict[str, Any]) -> bool:
    return action_name_key(action) in SLEEP_MOVES


def is_speed_control_action(action: dict[str, Any]) -> bool:
    return action_name_key(action) in SPEED_CONTROL_MOVES


def is_sacrifice_action(action: dict[str, Any]) -> bool:
    return action_name_key(action) in SACRIFICE_MOVES


def is_lock_action(action: dict[str, Any]) -> bool:
    return action_name_key(action) in LOCK_MOVES


def is_recovery_action(action: dict[str, Any]) -> bool:
    return action_name_key(action) in RECOVERY_MOVES


def damage_sort_key(action: dict[str, Any]) -> tuple[float, float, str]:
    estimate = action.get("damage_estimate") if isinstance(action.get("damage_estimate"), dict) else {}
    high = estimate.get("high_percent", 0)
    low = estimate.get("low_percent", 0)
    high_value = float(high) if isinstance(high, (int, float)) else 0.0
    low_value = float(low) if isinstance(low, (int, float)) else 0.0
    return (high_value, low_value, action_name(action))


def action_by_id(fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(action.get("id")): action
        for action in fixture.get("actions", [])
        if isinstance(action, dict) and action.get("id")
    }


def scored_actions(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    actions = action_by_id(fixture)
    try:
        inspection = inspect_fixture(fixture)
    except Exception:
        return list(actions.values())
    rows: list[dict[str, Any]] = []
    for row in inspection.get("actions", []):
        action = actions.get(str(row.get("action_id")))
        if action is None:
            continue
        merged = dict(action)
        merged["current_scorer_score"] = row.get("score")
        rows.append(merged)
    return rows or list(actions.values())


def first_matching(actions: list[dict[str, Any]], predicate: Any) -> dict[str, Any] | None:
    for action in actions:
        if predicate(action):
            return action
    return None


def best_damage_action(actions: list[dict[str, Any]]) -> dict[str, Any] | None:
    damaging = [action for action in actions if is_damage_action(action)]
    if not damaging:
        damaging = [
            action
            for action in actions
            if action_kind(action) == "move"
            and not (is_setup_action(action) or is_status_action(action) or is_recovery_action(action))
        ]
    if not damaging:
        return None
    return sorted(damaging, key=damage_sort_key, reverse=True)[0]


def plan_identifier(fixture: dict[str, Any], shape: str, action_ids: list[str]) -> str:
    body = "_".join([shape, *[slug(action_id) for action_id in action_ids if action_id]])
    return f"plan_{slug(fixture['id'])}_{body}"[:160]


def plan_step(turn: int, action: dict[str, Any], **extra: Any) -> dict[str, Any]:
    row = {
        "turn": turn,
        "action_id": action_id(action),
        "label": action_name(action),
    }
    row.update(extra)
    return row


def make_plan(
    fixture: dict[str, Any],
    *,
    shape: str,
    label: str,
    goal: str,
    steps: list[dict[str, Any]],
    rationale: str,
    priority: int,
    stop_conditions: list[str],
    branch_rules: list[dict[str, str]] | None = None,
    initiation_conditions: list[str] | None = None,
    horizon: int = DEFAULT_PLAN_HORIZON,
    rollout_mode: str = DEFAULT_ROLLOUT_MODE,
) -> dict[str, Any]:
    action_ids = [
        str(step.get("action_id"))
        for step in steps
        if isinstance(step, dict) and step.get("action_id")
    ]
    plan = {
        "id": plan_identifier(fixture, shape, action_ids),
        "kind": "plan",
        "shape": shape,
        "phase": phase_for_fixture(fixture),
        "label": label,
        "goal": goal,
        "horizon": max(1, min(MAX_PLAN_HORIZON, int(horizon))),
        "initiation_conditions": initiation_conditions or [],
        "steps": steps,
        "branch_rules": branch_rules or [{"if": "target_switches", "then": "re_score"}],
        "stop_conditions": stop_conditions or ["plan_goal_reached", "boss_faints"],
        "rationale": rationale,
        "source_action_ids": action_ids,
        "priority": priority,
        "public_info_constraints": [
            "boss_actions_only",
            "player_hidden_moves_not_facts",
        ],
    }
    plan.update(project_plan(fixture, plan, rollout_mode=rollout_mode))
    return plan


def direct_attack_plan(
    fixture: dict[str, Any],
    action: dict[str, Any],
    *,
    rollout_mode: str,
) -> dict[str, Any]:
    label = f"{action_name(action)} now"
    return make_plan(
        fixture,
        shape="attack_now",
        label=label,
        goal="Cash immediate damage before the player gets another response.",
        steps=[
            plan_step(1, action),
            plan_step(2, action, repeat_until=["target_switches", "target_in_ko_range"]),
        ],
        rationale=str(action.get("explanation") or "Direct pressure is the clean baseline."),
        priority=12,
        stop_conditions=["target_switches", "target_faints", "boss_hp_below_30"],
        branch_rules=[
            {"if": "target_switches", "then": "re_score"},
            {"if": "target_in_ko_range", "then": "take_ko"},
        ],
        rollout_mode=rollout_mode,
    )


def setup_then_attack_plan(
    fixture: dict[str, Any],
    setup: dict[str, Any],
    attack: dict[str, Any],
    *,
    rollout_mode: str,
) -> dict[str, Any]:
    return make_plan(
        fixture,
        shape="setup_once_then_attack",
        label=f"{action_name(setup)}, then {action_name(attack)}",
        goal="Spend one turn improving the damage race, then cash pressure.",
        steps=[plan_step(1, setup), plan_step(2, attack, repeat_until=["target_in_ko_range"])],
        rationale="Setup is only useful if the next attack changes the race or forces a switch.",
        priority=10,
        stop_conditions=["boss_hp_below_35", "target_switches", "setup_no_longer_changes_ko_math"],
        branch_rules=[
            {"if": "player_reveals_stronger_punish", "then": "attack_now_or_switch"},
            {"if": "target_switches", "then": "re_score"},
        ],
        initiation_conditions=["boss_faster_or_survives_one_hit", "setup_changes_ko_math"],
        rollout_mode=rollout_mode,
    )


def sleep_setup_then_attack_plan(
    fixture: dict[str, Any],
    sleep: dict[str, Any],
    setup: dict[str, Any],
    attack: dict[str, Any],
    *,
    rollout_mode: str,
) -> dict[str, Any]:
    return make_plan(
        fixture,
        shape="sleep_then_setup_then_attack",
        label=f"{action_name(sleep)}, then {action_name(setup)}, then {action_name(attack)}",
        goal="Use sleep to create the setup turn, then cash the boosted attack.",
        steps=[
            plan_step(1, sleep),
            plan_step(2, setup),
            plan_step(3, attack, repeat_until=["target_in_ko_range", "target_wakes"]),
        ],
        rationale=(
            "Sleep-first setup is a bounded route: setup is only part of the "
            "line while sleep still makes the board safe enough to spend the turn."
        ),
        priority=11,
        stop_conditions=[
            "status_misses",
            "target_wakes",
            "target_switches",
            "sleep_clause_occupied",
            "setup_no_longer_changes_ko_math",
            "boss_hp_below_35",
        ],
        branch_rules=[
            {"if": "status_misses", "then": "re_score"},
            {"if": "target_wakes", "then": "re_score_or_reapply_sleep_if_clause_free"},
            {"if": "target_switches", "then": "re_score"},
            {"if": "sleep_clause_occupied", "then": "skip_sleep_move"},
        ],
        initiation_conditions=[
            "sleep_clause_free",
            "target_not_statused",
            "setup_changes_ko_math",
        ],
        horizon=5,
        rollout_mode=rollout_mode,
    )


def status_then_attack_plan(
    fixture: dict[str, Any],
    status: dict[str, Any],
    attack: dict[str, Any],
    *,
    rollout_mode: str,
) -> dict[str, Any]:
    shape = "status_once_then_attack"
    if is_speed_control_action(status):
        shape = "speed_control_then_attack"
    return make_plan(
        fixture,
        shape=shape,
        label=f"{action_name(status)}, then {action_name(attack)}",
        goal="Apply one useful control move, then stop giving up damage.",
        steps=[plan_step(1, status), plan_step(2, attack, repeat_until=["target_switches"])],
        rationale="Control moves teach better when they are bounded by a clear stop rule.",
        priority=9,
        stop_conditions=["status_landed", "target_already_neutralized", "target_switches"],
        branch_rules=[
            {"if": "status_landed", "then": "do_not_repeat_control"},
            {"if": "sleep_clause_occupied", "then": "skip_sleep_move"},
        ],
        initiation_conditions=["target_not_statused"],
        rollout_mode=rollout_mode,
    )


def scout_then_commit_plan(
    fixture: dict[str, Any],
    scout: dict[str, Any],
    attack: dict[str, Any],
    *,
    rollout_mode: str,
) -> dict[str, Any]:
    return make_plan(
        fixture,
        shape="scout_probe_then_commit",
        label=f"Probe with {action_name(scout)}, then commit",
        goal="Spend one turn reducing public uncertainty before committing the ace.",
        steps=[plan_step(1, scout), plan_step(2, attack)],
        rationale="A probe line can be correct when hidden coverage or speed is the real boundary.",
        priority=8,
        stop_conditions=["threat_revealed", "boss_hp_below_40", "target_switches"],
        branch_rules=[
            {"if": "hidden_threat_revealed", "then": "preserve_or_switch"},
            {"if": "no_punish_revealed", "then": "commit_to_damage"},
        ],
        initiation_conditions=["hidden_coverage_or_speed_boundary"],
        rollout_mode=rollout_mode,
    )


def switch_plan(
    fixture: dict[str, Any],
    switch: dict[str, Any],
    attack: dict[str, Any] | None,
    *,
    rollout_mode: str,
) -> dict[str, Any]:
    followup = attack or switch
    return make_plan(
        fixture,
        shape="switch_preserve_then_rescore",
        label=f"{action_name(switch)}, then re-score",
        goal="Preserve a useful boss Pokemon and create a cleaner matchup.",
        steps=[plan_step(1, switch), plan_step(2, followup, actor="boss_next_mon")],
        rationale="Switching is useful when preservation value beats immediate tempo loss.",
        priority=7,
        stop_conditions=["switch_in_bad_fit", "boss_last_mon", "plan_goal_reached"],
        branch_rules=[
            {"if": "player_punishes_switch", "then": "avoid_repeat_switch"},
            {"if": "new_matchup_is_clean", "then": "attack"},
        ],
        initiation_conditions=["preserve_ace_or_clean_switch_value"],
        rollout_mode=rollout_mode,
    )


def sacrifice_plan(
    fixture: dict[str, Any],
    sacrifice: dict[str, Any],
    attack: dict[str, Any] | None,
    *,
    rollout_mode: str,
) -> dict[str, Any]:
    followup = attack or sacrifice
    return make_plan(
        fixture,
        shape="sacrifice_trade_for_clean_switch",
        label=f"{action_name(sacrifice)} for a clean switch",
        goal="Trade a low-value or doomed mon for a cleaner next position.",
        steps=[
            plan_step(1, sacrifice),
            plan_step(2, followup, actor="boss_next_mon"),
        ],
        rationale="Sacrifice lines should be close-call mixups, not a deterministic default.",
        priority=8,
        stop_conditions=["sacrifice_no_longer_profitable", "boss_has_no_clean_followup"],
        branch_rules=[
            {"if": "target_survives_trade", "then": "re_score"},
            {"if": "near_tie", "then": "preserve_variety"},
        ],
        initiation_conditions=["clean_switch_value", "late_game_resource_trade"],
        rollout_mode=rollout_mode,
    )


def lock_or_recovery_plan(
    fixture: dict[str, Any],
    action: dict[str, Any],
    attack: dict[str, Any],
    *,
    rollout_mode: str,
) -> dict[str, Any]:
    if is_lock_action(action):
        shape = "commit_lock_only_if_safe"
        goal = "Commit to a ramp or lock only when the public punish cannot exploit it."
        stops = ["target_resists_lock_move", "target_can_switch", "boss_hp_below_40"]
    else:
        shape = "recover_until_safe"
        goal = "Recover only when it prevents a real KO race loss."
        stops = ["not_outdamaging_player", "boss_hp_high_enough", "target_can_setup"]
    return make_plan(
        fixture,
        shape=shape,
        label=f"{action_name(action)}, then {action_name(attack)}",
        goal=goal,
        steps=[plan_step(1, action), plan_step(2, attack)],
        rationale=str(action.get("public_tradeoff") or action.get("explanation") or goal),
        priority=6,
        stop_conditions=stops,
        rollout_mode=rollout_mode,
    )


def pressure_recover_lock_plan(
    fixture: dict[str, Any],
    attack: dict[str, Any],
    recovery: dict[str, Any],
    lock: dict[str, Any],
    *,
    rollout_mode: str,
) -> dict[str, Any]:
    return make_plan(
        fixture,
        shape="pressure_recover_then_lock",
        label=(
            f"{action_name(attack)} pressure, heal when needed, "
            f"then consider {action_name(lock)}"
        ),
        goal=(
            "Use safe pressure first, preserve the ace near the danger threshold, "
            "and only commit to the lock once the board is safer."
        ),
        steps=[
            plan_step(1, attack, repeat_until=["target_statused", "target_in_ko_range"]),
            plan_step(2, attack, repeat_until=["boss_hp_near_recovery_threshold"]),
            plan_step(3, recovery, condition="boss_hp_near_recovery_threshold"),
            plan_step(4, lock, condition="target_statused_or_cannot_punish"),
        ],
        rationale=(
            "The demonstrated line does not open with recovery or lock-in. It "
            "uses pressure to fish for paralysis or range, heals only when the "
            "damage race demands it, then revisits the risky lock."
        ),
        priority=13,
        stop_conditions=[
            "target_switches",
            "boss_hp_below_35",
            "target_can_punish_lock",
            "lock_no_longer_changes_ko_math",
        ],
        branch_rules=[
            {"if": "target_statused", "then": "consider_lock_or_continue_pressure"},
            {"if": "boss_hp_near_recovery_threshold", "then": "recover_once"},
            {"if": "target_reveals_stronger_punish", "then": "abandon_lock_and_re_score"},
        ],
        initiation_conditions=[
            "lock_is_resisted_or_punishable_now",
            "safe_attack_has_status_or_range_value",
            "recovery_preserves_ace_after_chip",
        ],
        horizon=5,
        rollout_mode=rollout_mode,
    )


def dedupe_plans(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, tuple[str, ...]]] = set()
    output: list[dict[str, Any]] = []
    for plan in plans:
        key = (plan["shape"], tuple(plan.get("source_action_ids", [])[:2]))
        if key in seen:
            continue
        seen.add(key)
        output.append(plan)
    output.sort(key=lambda item: (-int(item.get("priority", 0)), item["id"]))
    return output


def generate_plan_cards(
    fixture: dict[str, Any],
    *,
    rollout_mode: str = DEFAULT_ROLLOUT_MODE,
    max_cards: int = 4,
) -> list[dict[str, Any]]:
    mode = normalize_rollout_mode(rollout_mode)
    enriched = enrich_fixture_for_plans(fixture)
    actions = scored_actions(enriched)
    if not actions:
        return []

    damage = best_damage_action(actions)
    plans: list[dict[str, Any]] = []
    if damage is not None:
        plans.append(direct_attack_plan(enriched, damage, rollout_mode=mode))

    setup = first_matching(actions, is_setup_action)
    status = first_matching(actions, is_status_action)
    fixture_tags = {str(tag) for tag in enriched.get("tags", [])}
    if (
        setup is not None
        and status is not None
        and damage is not None
        and action_id(setup) != action_id(damage)
        and action_id(status) != action_id(damage)
        and is_sleep_action(status)
        and {"sleep", "setup"} <= fixture_tags
    ):
        plans.append(
            sleep_setup_then_attack_plan(
                enriched,
                status,
                setup,
                damage,
                rollout_mode=mode,
            )
        )

    if setup is not None and damage is not None and action_id(setup) != action_id(damage):
        plans.append(setup_then_attack_plan(enriched, setup, damage, rollout_mode=mode))

    if status is not None and damage is not None and action_id(status) != action_id(damage):
        plans.append(status_then_attack_plan(enriched, status, damage, rollout_mode=mode))

    switch = first_matching(actions, is_switch_action)
    if switch is not None:
        plans.append(switch_plan(enriched, switch, damage, rollout_mode=mode))

    sacrifice = first_matching(actions, is_sacrifice_action)
    if sacrifice is not None:
        plans.append(sacrifice_plan(enriched, sacrifice, damage, rollout_mode=mode))

    utility = first_matching(
        actions,
        lambda action: (
            action_id(action) != action_id(damage)
            and not is_switch_action(action)
            and (
                "sand" in action_name_key(action)
                or "probe" in str(action.get("explanation", "")).lower()
                or "scout" in str(action.get("explanation", "")).lower()
            )
        ),
    )
    if utility is not None and damage is not None and (
        "hidden_coverage" in fixture_tags or "prediction" in fixture_tags or "ace_preservation" in fixture_tags
    ):
        plans.append(scout_then_commit_plan(enriched, utility, damage, rollout_mode=mode))

    lock_or_recovery = first_matching(actions, lambda action: is_lock_action(action) or is_recovery_action(action))
    if lock_or_recovery is not None and damage is not None and action_id(lock_or_recovery) != action_id(damage):
        plans.append(lock_or_recovery_plan(enriched, lock_or_recovery, damage, rollout_mode=mode))

    lock_action = first_matching(actions, is_lock_action)
    recovery_action = first_matching(actions, is_recovery_action)
    if (
        damage is not None
        and lock_action is not None
        and recovery_action is not None
        and {"ace_preservation", "setup_lock"} <= fixture_tags
    ):
        plans.append(
            pressure_recover_lock_plan(
                enriched,
                damage,
                recovery_action,
                lock_action,
                rollout_mode=mode,
            )
        )

    output = dedupe_plans(plans)
    for index, plan in enumerate(output, start=1):
        plan["card_index"] = index
    return output[:max(1, min(4, max_cards))]


def generated_plan_ids_by_fixture(
    fixtures: list[dict[str, Any]],
    *,
    rollout_mode: str = DEFAULT_ROLLOUT_MODE,
) -> dict[str, set[str]]:
    return {
        fixture["id"]: {plan["id"] for plan in generate_plan_cards(fixture, rollout_mode=rollout_mode)}
        for fixture in fixtures
    }
