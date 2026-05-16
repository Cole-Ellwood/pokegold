"""Fixture-aware multi-turn route projection for trajectory plans.

Companion to ``tools/boss_ai_debugger/route_eval.py``: that module evaluates
``rom_scenarios``-shape inputs; this one operates directly on the preference
fixture corpus and the plan cards generated from it. Together they cover both
sides of the multi-turn review surface.

The trajectory regression's iter-8 cumulative tiebreaker silently treats every
plan step as if the actor is the still-active boss mon. That works for
"same-active" sequences (Sleep Powder then Quiver Dance vs Sleep Powder then
attack) but mis-grades cross-mon sequences. A self-KO move (Explosion,
Self-Destruct, Memento, Healing Wish, Lunar Dance) terminates the active mon;
a switch action moves a new mon into the active slot. Subsequent ``actor=None``
/ ``actor="boss"`` steps in those plans are structurally invalid (the named
mon cannot act on the post-trade turn), yet the static cumulative happily
double-counts them. The brock_golem_vs_vaporeon_explosion_question case
exposes the bug: both same-first-move explosion plans cumulate the same way,
but only one ("sacrifice_trade_for_clean_switch") explicitly continues via
``boss_next_mon``; the other ("attack_now") double-uses the now-dead mon and
wins the static cumulative anyway.

This module gives the verifier a structural-validity check it can call on
each plan, and a small route_value adjustment that flips obviously invalid
post-self-KO/post-switch sequences below their valid counterparts. It does
not try to be a full battle simulator; it just refuses to award credit for
plan steps the simulator would never have a chance to run.
"""

from __future__ import annotations

from typing import Any

# Action IDs that end the current active boss mon's turn permanently this
# battle. After one of these, only an ``actor="boss_next_mon"`` follow-up
# can act for the boss side.
SELF_KO_ACTION_IDS = frozenset(
    {
        "move_explosion",
        "move_self_destruct",
        "move_selfdestruct",
        "move_memento",
        "move_healing_wish",
        "move_lunar_dance",
    }
)

# Action ID prefixes that swap a new mon into the active slot. After one of
# these, only an ``actor="boss_next_mon"`` follow-up can act for the boss side.
SWITCH_ACTION_PREFIXES = ("switch_", "swap_", "send_")

# Penalty applied to a plan's route_value per structurally invalid post-step.
# Sized to dominate the largest legitimate per-action score (max ~80) so a
# single invalid continuation always loses to a valid one of the same length.
STRUCTURAL_INVALID_PENALTY = 90

# Bonus awarded to plans whose self-KO or switch first step is followed by a
# ``boss_next_mon`` continuation, which is the structurally honest way to
# spell out a trade or pivot. Smaller than the invalid penalty so it never
# overpowers an otherwise-better legitimate same-mon plan; tuned to be just
# enough to break a same-first-move + same-cumulative tie.
STRUCTURAL_CONTINUATION_BONUS = 6


def _action_kind(action: dict[str, Any]) -> str:
    """Return the action's ``kind`` field if present, else infer from the id."""

    kind = action.get("kind")
    if kind:
        return str(kind)
    action_id = str(action.get("id", ""))
    if action_id.startswith(SWITCH_ACTION_PREFIXES):
        return "switch"
    return "move"


def is_self_ko_action(action: dict[str, Any]) -> bool:
    """True when the action ends the active mon's life this battle."""

    action_id = str(action.get("id", ""))
    if action_id in SELF_KO_ACTION_IDS:
        return True
    name = str(action.get("name", "")).lower()
    return name in {"explosion", "self-destruct", "selfdestruct", "self destruct", "memento", "healing wish", "lunar dance"}


def is_switch_action(action: dict[str, Any]) -> bool:
    """True when the action swaps the active boss mon."""

    if _action_kind(action) == "switch":
        return True
    action_id = str(action.get("id", ""))
    return action_id.startswith(SWITCH_ACTION_PREFIXES)


def _action_lookup(fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build an action_id -> action map from the fixture."""

    return {str(a["id"]): a for a in fixture.get("actions", []) if "id" in a}


def project_plan_route(fixture: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    """Project structural validity and route_value adjustment for a single plan.

    Returns a dict with:
      - ``structural_valid``: bool, False if the plan has an action after the
        active mon has been removed (self-KO or switch) without using
        ``actor="boss_next_mon"`` to acknowledge the swap.
      - ``invalid_post_steps``: list of (index, action_id, reason) tuples.
      - ``honest_continuation``: bool, True when a self-KO/switch first step is
        followed by an ``actor="boss_next_mon"`` continuation step.
      - ``route_value_delta``: int, penalty + bonus adjustment to layer on top
        of cumulative scoring. Negative when the plan is structurally invalid.
      - ``factors``: sorted list of multi-turn factors observed
        (``self_ko_trade``, ``switch_pivot``, ``honest_continuation``).
    """

    actions = _action_lookup(fixture)
    steps = plan.get("steps", []) or []
    factors: set[str] = set()
    invalid_post_steps: list[tuple[int, str, str]] = []
    honest_continuation = False

    # Find the first boss-actor step (actor in {None, "boss"}). Anything after
    # it that is not ``boss_next_mon`` is invalid IFF the first boss step
    # terminates the current mon.
    boss_terminator_seen = False
    boss_terminator_kind: str | None = None
    for index, step in enumerate(steps):
        action_id = step.get("action_id")
        if not action_id:
            continue
        action = actions.get(str(action_id))
        actor = step.get("actor")
        if actor in (None, "boss"):
            if boss_terminator_seen:
                # Earlier step in this plan removed the active mon. This step
                # is supposed to act with the same mon — that is impossible.
                invalid_post_steps.append(
                    (
                        index,
                        str(action_id),
                        f"prior {boss_terminator_kind} terminated active mon; same-actor step is impossible",
                    )
                )
                continue
            if action is not None and is_self_ko_action(action):
                boss_terminator_seen = True
                boss_terminator_kind = "self_ko"
                factors.add("self_ko_trade")
            elif action is not None and is_switch_action(action):
                boss_terminator_seen = True
                boss_terminator_kind = "switch_pivot"
                factors.add("switch_pivot")
        elif actor == "boss_next_mon":
            if boss_terminator_seen:
                honest_continuation = True
                factors.add("honest_continuation")
            # boss_next_mon after no terminator is a labeling oddity, not a
            # structural invalidity (the plan just hands tempo over). Tracked
            # as a factor but neither rewarded nor penalised here.

    route_value_delta = 0
    if invalid_post_steps:
        route_value_delta -= STRUCTURAL_INVALID_PENALTY * len(invalid_post_steps)
    if honest_continuation:
        route_value_delta += STRUCTURAL_CONTINUATION_BONUS

    return {
        "structural_valid": not invalid_post_steps,
        "invalid_post_steps": invalid_post_steps,
        "honest_continuation": honest_continuation,
        "route_value_delta": route_value_delta,
        "factors": sorted(factors),
    }
